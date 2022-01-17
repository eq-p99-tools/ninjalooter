import re

from ninjalooter import config
from ninjalooter import logger
from ninjalooter import logparse
from ninjalooter import message_handlers
from ninjalooter import utils

# This is the app logger, not related to EQ logs
LOG = logger.getLogger(__name__)

MATCH_START_AUCTION_DKP = re.compile(
    config.TIMESTAMP +
    r"(?P<name>\w+) (tells the guild|say to your guild), '"
    r"\[(?P<item>.*?)\](?P<classes> \(.*?\))? - BID IN /GU"
    r"(, MIN (?P<min_dkp>\d+) DKP)?\. "
    r"You MUST include the item name in your bid! "
    r"(Currently: `(?P<player>\w+)` with (?P<bid>\d+) DKP - )?Closing in "
    r"(?P<time_remaining>.*?)(\.|!).*'"
)
MATCH_END_AUCTION_DKP = re.compile(
    config.TIMESTAMP +
    r"(?P<name>\w+) (tells the guild|say to your guild), '"
    r"Gratss (?P<player>\w+) on \[(?P<item>.*?)] \((?P<number>\d+) DKP\)!.*'"
)
MATCH_START_AUCTION_RANDOM = re.compile(
    config.TIMESTAMP +
    r"(?P<name>\w+) (tells the guild|say to your guild), '"
    r"\[(?P<item>.*?)\](?P<classes> \(.*?\))? ROLL (?P<number>\d+) NOW!.*'"
)
MATCH_END_AUCTION_RANDOM = re.compile(
    config.TIMESTAMP +
    r"(?P<name>\w+) (tells the guild|say to your guild), '"
    r"Gratss (?P<player>\w+) on \[(?P<item>.*?)] with "
    r"(?P<number>\d+) / (?P<target>\d+)!.*'"
)
SELF_MESSAGE_MATCHERS = {
    MATCH_START_AUCTION_DKP: message_handlers.handle_auc_start,
    MATCH_START_AUCTION_RANDOM: message_handlers.handle_auc_start,
    MATCH_END_AUCTION_DKP: message_handlers.handle_auc_end,
    MATCH_END_AUCTION_RANDOM: message_handlers.handle_auc_end,
}


def replay_logs(replay_lines, progress_dialog):
    old_charname = config.PLAYER_NAME
    total_picked_lines = len(replay_lines)
    last_rand_player = None
    for idx, line in enumerate(replay_lines):
        keep_going, _ = progress_dialog.Update(
            idx, newmsg="Now parsing line %s of %s..." %
                        (idx, total_picked_lines))
        if not keep_going:
            LOG.debug("User cancelled log replay.")
            break

        line = line.strip()
        if last_rand_player:
            line = line + last_rand_player
            last_rand_player = None
        result = None
        for matcher in SELF_MESSAGE_MATCHERS:
            match = matcher.match(line)
            if match:
                match_func = SELF_MESSAGE_MATCHERS[matcher]
                try:
                    result = match_func(match, progress_dialog.Parent, True)
                except Exception:
                    LOG.exception("Failed to parse SELF line: %s", line)
        if result:
            LOG.debug("Handled SELF line: %s", line)
            continue

        for matcher in logparse.LOG_MATCHERS:
            match = matcher.match(line)
            if match:
                match_func = logparse.LOG_MATCHERS[matcher]
                result = match_func(match, progress_dialog.Parent, True)
                if matcher == config.MATCH_RAND1:
                    last_rand_player = result
        if result:
            LOG.debug("Handled line: %s", line)
    LOG.info("Finished log replay!")
    config.PLAYER_NAME = old_charname
    utils.store_state()
