import time

from ninjalooter import config
from ninjalooter import logging
from ninjalooter import message_handlers
from ninjalooter import utils

# This is the app logger, not related to EQ logs
LOG = logging.getLogger(__name__)

LOG_MATCHERS = {
    config.MATCH_WHO: message_handlers.handle_who,
    config.MATCH_OOC: message_handlers.handle_ooc,
    config.MATCH_AUC: message_handlers.handle_auc,
}


def match_line(line) -> tuple:
    for matcher in LOG_MATCHERS:
        match = matcher.match(line)
        if match:
            return LOG_MATCHERS[matcher](match)
    # Nothing matched, not a useful line
    return tuple()


def parse_logfile(logfile):
    if config.TREE is None:
        utils.setup_aho()
    config.LOGFILE_LOOP_RUN.set()
    with open(logfile, 'r') as lfp:
        while config.LOGFILE_LOOP_RUN.is_set():
            lines = lfp.readlines()
            for line in lines:
                line = line.strip()
                result = match_line(line)
                if result:
                    LOG.info("Handled line: %s", line)
            config.LOGFILE_LOOP_RUN.clear()  # end loop quickly for testing
            time.sleep(0.1)
