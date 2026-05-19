import os
import threading
import time

from ninjalooter import config, logger, message_handlers, utils
from ninjalooter.app_signals import signals

# This is the app logger, not related to EQ logs
LOG = logger.getLogger(__name__)

LOG_MATCHERS = {}


def reset_matchers():
    LOG_MATCHERS.clear()
    LOG_MATCHERS.update(
        {
            config.MATCH_START_WHO: message_handlers.handle_start_who,
            config.MATCH_WHO: message_handlers.handle_who,
            config.MATCH_END_WHO: message_handlers.handle_end_who,
            config.MATCH_RAND1: message_handlers.handle_rand1,
            config.MATCH_RAND2: message_handlers.handle_rand2,
            config.MATCH_KILL: message_handlers.handle_kill,
            config.MATCH_RAIDTICK: message_handlers.handle_raidtick,
            config.MATCH_CREDITT: message_handlers.handle_creditt,
            config.MATCH_GRATSS: message_handlers.handle_gratss,
        }
    )
    for matcher in config.MATCH_BID:
        LOG_MATCHERS[matcher] = message_handlers.handle_bid
    for matcher in config.MATCH_DROP:
        LOG_MATCHERS[matcher] = message_handlers.handle_drop


reset_matchers()


def parse_logfile(logfile: str, run: threading.Event):
    if config.TRIE is None:
        utils.setup_aho()
    with open(logfile, encoding="utf-8", errors="replace") as lfp:
        lfp.seek(0, os.SEEK_END)
        LOG.info("Logfile loaded: %s", logfile)
        while run.is_set():
            pos = lfp.tell()
            lines = lfp.readlines()
            if not lines:
                # On Windows, TextIOWrapper can cache EOF state internally.
                # Seeking to current pos via the underlying buffer forces a
                # reset of the read-ahead buffer so new appended data is seen.
                lfp.buffer.seek(pos)
                lfp.seek(pos)
                time.sleep(0.1)
                continue
            last_rand_player = None
            for raw_line in lines:
                current_line = raw_line.strip()
                if last_rand_player:
                    current_line = current_line + last_rand_player
                    last_rand_player = None
                result = None
                for matcher, match_func in LOG_MATCHERS.items():
                    match = matcher.match(current_line)
                    if match:
                        try:
                            result = match_func(match)
                        except Exception:
                            LOG.exception(
                                "Error in log handler %s for line: %s",
                                match_func.__name__,
                                current_line,
                            )
                        if matcher == config.MATCH_RAND1:
                            last_rand_player = result
                        break
                if result:
                    LOG.debug("Handled line: %s", current_line)
            time.sleep(0.1)


class ParseThread(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.loop_run = threading.Event()
        self.loop_run.set()

    def run(self):
        try:
            logfile, name = utils.get_latest_logfile(config.LOG_DIRECTORY)
            config.LATEST_LOGFILE = logfile
            config.PLAYER_NAME = name
            LOG.info("Starting logparser thread for %s...", name)
            signals.title_changed.emit(
                "NinjaLooter EQ Raid Manager v{version} - {name}".format(version=config.VERSION, name=name)
            )
            if logfile:
                utils.alert_message(
                    "Now monitoring logs for %s" % name,
                    "A recently modified logfile was detected: %s" % os.path.basename(logfile),
                )
                parse_logfile(logfile, self.loop_run)
            else:
                utils.alert_message(
                    "Not monitoring any logs",
                    "No logfile detected. Please configure your EQ Log Directory via the File menu.",
                )
        except Exception:
            LOG.exception("ParseThread crashed")
            if self.loop_run.is_set():
                utils.alert_message(
                    "Log Parser Crashed",
                    "The log monitoring thread has stopped unexpectedly. Restarting...",
                )
                signals.title_changed.emit(
                    "NinjaLooter EQ Raid Manager v{version} - RESTARTING...".format(version=config.VERSION)
                )
                self._restart()

    def _restart(self):
        new_thread = ParseThread()
        config.PARSER_THREAD = new_thread
        new_thread.start()

    def abort(self):
        self.loop_run.clear()
