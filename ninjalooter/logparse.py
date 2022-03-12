import os
import threading
import time

import wx

from ninjalooter import config
from ninjalooter import logger
from ninjalooter import message_handlers
from ninjalooter import utils

# This is the app logger, not related to EQ logs
LOG = logger.getLogger(__name__)

LOG_MATCHERS = {}


def reset_matchers():
    LOG_MATCHERS.clear()
    LOG_MATCHERS.update({
        config.MATCH_START_WHO: message_handlers.handle_start_who,
        config.MATCH_WHO: message_handlers.handle_who,
        config.MATCH_END_WHO: message_handlers.handle_end_who,
        config.MATCH_RAND1: message_handlers.handle_rand1,
        config.MATCH_RAND2: message_handlers.handle_rand2,
        config.MATCH_KILL: message_handlers.handle_kill,
        config.MATCH_RAIDTICK: message_handlers.handle_raidtick,
        config.MATCH_CREDITT: message_handlers.handle_creditt,
        config.MATCH_GRATSS: message_handlers.handle_gratss,
    })
    for matcher in config.MATCH_BID:
        LOG_MATCHERS[matcher] = message_handlers.handle_bid
    for matcher in config.MATCH_DROP:
        LOG_MATCHERS[matcher] = message_handlers.handle_drop


reset_matchers()


# pylint: disable=no-member
def parse_logfile(logfile: str, window: wx.Window, run: threading.Event):
    if config.TRIE is None:
        utils.setup_aho()
    with open(logfile, 'r') as lfp:
        lfp.seek(0, os.SEEK_END)
        LOG.info("Logfile loaded: %s", logfile)
        while run.is_set():
            lines = lfp.readlines()
            last_rand_player = None
            for line in lines:
                line = line.strip()
                if last_rand_player:
                    line = line + last_rand_player
                    last_rand_player = None
                result = None
                for matcher in LOG_MATCHERS:
                    match = matcher.match(line)
                    if match:
                        match_func = LOG_MATCHERS[matcher]
                        result = match_func(match, window)
                        if matcher == config.MATCH_RAND1:
                            last_rand_player = result
                if result:
                    LOG.debug("Handled line: %s", line)
            time.sleep(0.1)


class ParseThread(threading.Thread):
    # pylint: disable=no-member
    def __init__(self, window: wx.Window):
        super().__init__()
        self.window = window
        self.loop_run = threading.Event()
        self.loop_run.set()

    def run(self):
        logfile, name = utils.get_latest_logfile(config.LOG_DIRECTORY)
        config.LATEST_LOGFILE = logfile
        config.PLAYER_NAME = name
        LOG.info("Starting logparser thread for %s...", name)
        self.window.SetLabel("NinjaLooter EQ Raid Manager v{version} - {name}"
                             .format(version=config.VERSION, name=name))
        if logfile:
            utils.alert_message(
                "Now monitoring logs for %s" % name,
                "A recently modified logfile was detected: %s" %
                os.path.basename(logfile)
            )
            parse_logfile(logfile, self.window, self.loop_run)
        else:
            utils.alert_message(
                "Not monitoring any logs",
                "No logfile detected. Please configure your EQ Log Directory "
                "via the File menu."
            )

    def abort(self):
        self.loop_run.clear()
