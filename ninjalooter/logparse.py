import os
import threading
import time

from ninjalooter import config
from ninjalooter import logging
from ninjalooter import message_handlers
from ninjalooter import utils

# This is the app logger, not related to EQ logs
LOG = logging.getLogger(__name__)

LOG_MATCHERS = {
    config.MATCH_NEW_WHO: message_handlers.handle_new_who,
    config.MATCH_WHO: message_handlers.handle_who,
    config.MATCH_OOC: message_handlers.handle_ooc,
    config.MATCH_AUC: message_handlers.handle_auc,
    config.MATCH_RAND: message_handlers.handle_rand,
}


def match_line(line, window) -> bool:
    for matcher in LOG_MATCHERS:
        match = matcher.match(line)
        if match:
            return LOG_MATCHERS[matcher](match, window)
    # Nothing matched, not a useful line
    return False


def parse_logfile(logfile: str, window: object, run: threading.Event):
    if config.TREE is None:
        utils.setup_aho()
    with open(logfile, 'r') as lfp:
        lfp.seek(0, os.SEEK_END)
        LOG.info("Logfile loaded: %s", logfile)
        while run.is_set():
            lines = lfp.readlines()
            for line in lines:
                line = line.strip()
                result = match_line(line, window)
                if result:
                    LOG.info("Handled line: %s", line)
            # run.clear()  # TODO: right now, end loop quickly for testing
            time.sleep(0.1)


class ParseThread(threading.Thread):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.loop_run = threading.Event()
        self.loop_run.set()

    def run(self):
        logfile, name = utils.get_latest_logfile(config.LOG_DIRECTORY)
        LOG.info("Starting logparser thread for %s...", name)
        parse_logfile(logfile, self.window, self.loop_run)

    def abort(self):
        self.loop_run.clear()
