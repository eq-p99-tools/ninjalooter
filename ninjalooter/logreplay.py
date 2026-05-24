import datetime
import re
from dataclasses import dataclass

import dateutil.parser

from ninjalooter import config, logger, logparse, message_handlers, models, utils

# This is the app logger, not related to EQ logs
LOG = logger.getLogger(__name__)

MATCH_START_AUCTION_DKP = re.compile(
    config.TIMESTAMP + r"(?P<name>\w+) .*?, '"
    r"~?\[(?P<item>.*?)\](?P<classes> \(.*?\))? - BID IN /\w+"
    r"(, MIN (?P<min_dkp>\d+) DKP)?\. "
    r"You MUST include the item name in your bid! "
    r"(Currently: `(?P<player>\w+)` with (?P<bid>\d+) DKP - )?Closing in "
    r"(?P<time_remaining>.*?)(\.|!).*'"
)
MATCH_END_AUCTION_DKP = re.compile(
    config.TIMESTAMP + r"(?P<name>\w+) .*?, '"
    r"~?Gratss (?P<player>\w+) on \[(?P<item>.*?)] \((?P<number>\d+) DKP\)!.*'"
)
MATCH_START_AUCTION_RANDOM = re.compile(
    config.TIMESTAMP + r"(?P<name>\w+) .*?, '"
    r"~?\[(?P<item>.*?)\](?P<classes> \(.*?\))? ROLL (?P<number>\d+) NOW!.*'"
)
MATCH_END_AUCTION_RANDOM = re.compile(
    config.TIMESTAMP + r"(?P<name>\w+) .*?, '"
    r"~?Gratss (?P<player>\w+) on \[(?P<item>.*?)] with "
    r"(?P<number>\d+) / (?P<target>\d+)!.*'"
)
SELF_MESSAGE_MATCHERS = {
    MATCH_START_AUCTION_DKP: message_handlers.handle_auc_start,
    MATCH_START_AUCTION_RANDOM: message_handlers.handle_auc_start,
    MATCH_END_AUCTION_DKP: message_handlers.handle_auc_end,
    MATCH_END_AUCTION_RANDOM: message_handlers.handle_auc_end,
}


def replay_logs(replay_lines, progress_callback=None):
    """Replay a log file, parsing all lines.

    Args:
        replay_lines: List of log lines to replay.
        progress_callback: Optional callable(current, total) -> bool.
                          Returns False to cancel.
    """
    old_charname = config.PLAYER_NAME
    total_picked_lines = len(replay_lines)
    last_rand_player = None
    for idx, line in enumerate(replay_lines):
        if progress_callback:
            if not progress_callback(idx, total_picked_lines):
                LOG.debug("User cancelled log replay.")
                break

        current_line = line.strip()
        if last_rand_player:
            current_line = current_line + last_rand_player
            last_rand_player = None
        result = None
        for matcher, match_func in SELF_MESSAGE_MATCHERS.items():
            match = matcher.match(current_line)
            if match:
                try:
                    result = match_func(match, skip_store=True)
                except Exception:
                    LOG.exception("Failed to parse SELF line: %s", current_line)
        if result:
            LOG.debug("Handled SELF line: %s", current_line)
            continue

        for matcher, match_func in logparse.LOG_MATCHERS.items():
            match = matcher.match(current_line)
            if match:
                try:
                    result = match_func(match, skip_store=True)
                except Exception:
                    LOG.exception("Failed to parse line: %s", current_line)
                    break
                if matcher == config.MATCH_RAND1:
                    last_rand_player = result
        if result:
            LOG.debug("Handled line: %s", current_line)
    LOG.info("Finished log replay!")
    config.PLAYER_NAME = old_charname
    utils.store_state()


# ──────────────────────────────────────────────────────────────────────────────
# Attendance-only replay
# ──────────────────────────────────────────────────────────────────────────────

ATTENDANCE_MATCHERS = {
    config.MATCH_START_WHO: message_handlers.handle_start_who,
    config.MATCH_WHO: message_handlers.handle_who,
    config.MATCH_END_WHO: message_handlers.handle_end_who,
    config.MATCH_RAIDTICK: message_handlers.handle_raidtick,
    config.MATCH_CREDITT: message_handlers.handle_creditt,
    config.MATCH_GRATSS: message_handlers.handle_gratss,
}


@dataclass
class ScanResult:
    total_whos: int
    raidtick_whos: int
    creditt_count: int = 0
    gratss_count: int = 0


def _iter_lines_in_range(lines, start_time, end_time):
    """Yield lines whose timestamps fall within [start_time, end_time]."""
    start_idx = utils.find_timestamp(lines, start_time)
    if start_idx is None:
        return
    for line in lines[start_idx:]:
        ts = utils.get_timestamp(line)
        if ts and ts > end_time:
            return
        yield line


def scan_attendance(lines, start_time, end_time):
    """Quick count of /who snapshots, raid ticks, creditts, and gratss in a time range.

    Does NOT mutate any global state.
    """
    total_whos = 0
    raidtick_whos = 0
    creditt_count = 0
    gratss_count = 0
    last_raidtick = datetime.datetime.fromtimestamp(0)
    in_who = False

    for line in _iter_lines_in_range(lines, start_time, end_time):
        stripped = line.strip()

        match = config.MATCH_RAIDTICK.match(stripped)
        if match:
            tick_time = match.group("time")
            last_raidtick = dateutil.parser.parse(tick_time)
            continue

        if config.MATCH_CREDITT.match(stripped):
            creditt_count += 1
            continue

        if config.MATCH_GRATSS.match(stripped):
            gratss_count += 1
            continue

        if config.MATCH_START_WHO.match(stripped):
            in_who = True
            continue

        if in_who:
            end_match = config.MATCH_END_WHO.match(stripped)
            if end_match:
                in_who = False
                total_whos += 1
                who_time = dateutil.parser.parse(end_match.group("time"))
                if (who_time - last_raidtick) <= datetime.timedelta(seconds=3):
                    raidtick_whos += 1

    return ScanResult(
        total_whos=total_whos,
        raidtick_whos=raidtick_whos,
        creditt_count=creditt_count,
        gratss_count=gratss_count,
    )


def replay_attendance(lines, start_time, end_time, progress_callback=None):
    """Parse only attendance data (/who + raidtick) from lines in a time range.

    Appends WhoLog entries to config.ATTENDANCE_LOGS and persists state once.

    Args:
        lines: Full list of log file lines.
        start_time: Start of time range (inclusive).
        end_time: End of time range (inclusive).
        progress_callback: Optional callable(current, total) -> bool.
                          Returns False to cancel.
    """
    old_raidtick = config.LAST_RAIDTICK
    config.LAST_RAIDTICK = datetime.datetime.fromtimestamp(0)

    start_idx = utils.find_timestamp(lines, start_time)
    if start_idx is None:
        LOG.info("No lines found in time range for attendance replay.")
        config.LAST_RAIDTICK = old_raidtick
        return

    subset = []
    for line in lines[start_idx:]:
        ts = utils.get_timestamp(line)
        if ts and ts > end_time:
            break
        subset.append(line)

    total = len(subset)
    for idx, line in enumerate(subset):
        if progress_callback:
            if not progress_callback(idx, total):
                LOG.debug("User cancelled attendance replay.")
                break

        stripped = line.strip()
        for matcher, handler in ATTENDANCE_MATCHERS.items():
            match = matcher.match(stripped)
            if match:
                try:
                    handler(match, skip_store=True)
                except Exception:
                    LOG.exception("Failed to parse attendance line: %s", stripped)
                break

    LOG.info("Finished attendance replay!")
    config.LAST_RAIDTICK = old_raidtick
    utils.store_state()


# ──────────────────────────────────────────────────────────────────────────────
# Full replay (attendance + auctions)
# ──────────────────────────────────────────────────────────────────────────────

ALL_DROP_MATCHERS = [
    config.MATCH_DROP_SAY,
    config.MATCH_DROP_OOC,
    config.MATCH_DROP_AUC,
    config.MATCH_DROP_SHOUT,
    config.MATCH_DROP_GU,
]

ALL_BID_MATCHERS = [
    config.MATCH_BID_SAY,
    config.MATCH_BID_OOC,
    config.MATCH_BID_AUC,
    config.MATCH_BID_SHOUT,
    config.MATCH_BID_GU,
    config.MATCH_BID_TELL,
]


def _build_full_matchers():
    """Build matcher dict for full replay using all channels."""
    matchers = {}
    matchers[config.MATCH_START_WHO] = message_handlers.handle_start_who
    matchers[config.MATCH_WHO] = message_handlers.handle_who
    matchers[config.MATCH_END_WHO] = message_handlers.handle_end_who
    matchers[config.MATCH_RAND1] = message_handlers.handle_rand1
    matchers[config.MATCH_RAND2] = message_handlers.handle_rand2
    matchers[config.MATCH_KILL] = message_handlers.handle_kill
    matchers[config.MATCH_RAIDTICK] = message_handlers.handle_raidtick
    matchers[config.MATCH_CREDITT] = message_handlers.handle_creditt
    matchers[config.MATCH_GRATSS] = message_handlers.handle_gratss
    for matcher in ALL_BID_MATCHERS:
        matchers[matcher] = message_handlers.handle_bid
    for matcher in ALL_DROP_MATCHERS:
        matchers[matcher] = message_handlers.handle_drop
    return matchers


def _replay_handle_auc_start(match, skip_store=True):
    """Wrapper that synthesizes a pending item if needed."""
    result = message_handlers.handle_auc_start(match, skip_store=skip_store)
    if not result:
        item_name = match.group("item")
        timestamp = match.group("time")
        synthetic = models.ItemDrop(item_name, "(replay)", timestamp)
        config.PENDING_AUCTIONS.append(synthetic)
        result = message_handlers.handle_auc_start(match, skip_store=skip_store)
    return result


def _replay_handle_auc_end(match, skip_store=True):
    """End auction and override bids with the authoritative gratss data.

    The gratss message is the definitive source of winner/price. Replay
    may accumulate spurious bids from all-channel matching, so we replace
    the bid data with what the gratss message says actually happened.
    """
    result = message_handlers.handle_auc_end(match, skip_store=skip_store)
    if not result:
        # Auction wasn't active -- synthesize directly from the gratss data
        item_name = match.group("item")
        player = match.group("player")
        number = int(match.group("number"))
        timestamp = match.group("time")
        end_time = dateutil.parser.parse(timestamp)

        synthetic_item = models.ItemDrop(item_name, "(replay)", timestamp)
        if "target" in match.groupdict():
            auc = models.RandomAuction(synthetic_item)
            if player != "ROT":
                auc.rolls[player] = number
        else:
            auc = models.DKPAuction(synthetic_item, alliance="")
            if player != "ROT" and number > 0:
                auc.bids[number] = player
        auc.start_time = end_time
        auc.end_time = end_time
        config.HISTORICAL_AUCTIONS[synthetic_item.uuid] = auc
        result = True
    else:
        # Auction was active -- override bids with authoritative gratss data
        item_name = match.group("item")
        player = match.group("player")
        number = int(match.group("number"))
        for auc in reversed(list(config.HISTORICAL_AUCTIONS.values())):
            if auc.name().lower() == item_name.lower():
                if isinstance(auc, models.DKPAuction):
                    auc.bids = {number: player} if player != "ROT" else {}
                elif isinstance(auc, models.RandomAuction):
                    auc.rolls = {player: number} if player != "ROT" else {}
                break
    return result


FULL_SELF_MATCHERS = {
    MATCH_START_AUCTION_DKP: _replay_handle_auc_start,
    MATCH_START_AUCTION_RANDOM: _replay_handle_auc_start,
    MATCH_END_AUCTION_DKP: _replay_handle_auc_end,
    MATCH_END_AUCTION_RANDOM: _replay_handle_auc_end,
}


def replay_full(lines, start_time, end_time, progress_callback=None):
    """Full replay: attendance + auctions + creditt/gratss + kills.

    Uses all channels for drops/bids and synthesizes pending items for
    auctions that started before the time window.

    Args:
        lines: Full list of log file lines.
        start_time: Start of time range (inclusive).
        end_time: End of time range (inclusive).
        progress_callback: Optional callable(current, total) -> bool.
                          Returns False to cancel.
    """
    if config.TRIE is None:
        utils.setup_aho()

    old_raidtick = config.LAST_RAIDTICK
    config.LAST_RAIDTICK = datetime.datetime.fromtimestamp(0)

    start_idx = utils.find_timestamp(lines, start_time)
    if start_idx is None:
        LOG.info("No lines found in time range for full replay.")
        config.LAST_RAIDTICK = old_raidtick
        return

    subset = []
    for line in lines[start_idx:]:
        ts = utils.get_timestamp(line)
        if ts and ts > end_time:
            break
        subset.append(line)

    full_matchers = _build_full_matchers()
    total = len(subset)
    last_rand_player = None

    for idx, line in enumerate(subset):
        if progress_callback:
            if not progress_callback(idx, total):
                LOG.debug("User cancelled full replay.")
                break

        current_line = line.strip()
        if last_rand_player:
            current_line = current_line + last_rand_player
            last_rand_player = None

        # Pass 1: operator self-messages (auction start/end)
        result = None
        for matcher, match_func in FULL_SELF_MATCHERS.items():
            match = matcher.match(current_line)
            if match:
                try:
                    result = match_func(match, skip_store=True)
                except Exception:
                    LOG.exception("Failed to parse SELF line: %s", current_line)
        if result:
            continue

        # Pass 2: all other matchers (drops, bids, who, etc.)
        for matcher, match_func in full_matchers.items():
            match = matcher.match(current_line)
            if match:
                try:
                    result = match_func(match, skip_store=True)
                except Exception:
                    LOG.exception("Failed to parse line: %s", current_line)
                    break
                if matcher == config.MATCH_RAND1:
                    last_rand_player = result
                break

    LOG.info("Finished full replay!")
    config.LAST_RAIDTICK = old_raidtick
    utils.store_state()
