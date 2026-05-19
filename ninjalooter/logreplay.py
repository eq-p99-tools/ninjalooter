import re

from ninjalooter import config, logger, logparse, message_handlers, utils

# This is the app logger, not related to EQ logs
LOG = logger.getLogger(__name__)

MATCH_START_AUCTION_DKP = re.compile(
    config.TIMESTAMP + r"(?P<name>\w+) (tells the guild|say to your guild), '"
    r"\[(?P<item>.*?)\](?P<classes> \(.*?\))? - BID IN /GU"
    r"(, MIN (?P<min_dkp>\d+) DKP)?\. "
    r"You MUST include the item name in your bid! "
    r"(Currently: `(?P<player>\w+)` with (?P<bid>\d+) DKP - )?Closing in "
    r"(?P<time_remaining>.*?)(\.|!).*'"
)
MATCH_END_AUCTION_DKP = re.compile(
    config.TIMESTAMP + r"(?P<name>\w+) (tells the guild|say to your guild), '"
    r"Gratss (?P<player>\w+) on \[(?P<item>.*?)] \((?P<number>\d+) DKP\)!.*'"
)
MATCH_START_AUCTION_RANDOM = re.compile(
    config.TIMESTAMP + r"(?P<name>\w+) (tells the guild|say to your guild), '"
    r"\[(?P<item>.*?)\](?P<classes> \(.*?\))? ROLL (?P<number>\d+) NOW!.*'"
)
MATCH_END_AUCTION_RANDOM = re.compile(
    config.TIMESTAMP + r"(?P<name>\w+) (tells the guild|say to your guild), '"
    r"Gratss (?P<player>\w+) on \[(?P<item>.*?)] with "
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
