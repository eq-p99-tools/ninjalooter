import threading
from unittest import mock

from ninjalooter import config
from ninjalooter import logparse
from ninjalooter import message_handlers
from ninjalooter.tests import base
from ninjalooter import utils


class TestLogparse(base.NLTestBase):
    def setUp(self) -> None:
        super(TestLogparse, self).setUp()
        utils.setup_aho()
        logparse.reset_matchers()

    def test_reset_matchers(self):
        logparse.LOG_MATCHERS.clear()
        self.assertEqual(0, len(logparse.LOG_MATCHERS))

        logparse.reset_matchers()

        self.assertIn(config.MATCH_START_WHO, logparse.LOG_MATCHERS)
        self.assertIn(config.MATCH_WHO, logparse.LOG_MATCHERS)
        self.assertIn(config.MATCH_END_WHO, logparse.LOG_MATCHERS)
        self.assertIn(config.MATCH_RAND1, logparse.LOG_MATCHERS)
        self.assertIn(config.MATCH_RAND2, logparse.LOG_MATCHERS)
        self.assertIn(config.MATCH_KILL, logparse.LOG_MATCHERS)
        self.assertIn(config.MATCH_RAIDTICK, logparse.LOG_MATCHERS)
        self.assertIn(config.MATCH_CREDITT, logparse.LOG_MATCHERS)
        self.assertIn(config.MATCH_GRATSS, logparse.LOG_MATCHERS)

        self.assertEqual(
            logparse.LOG_MATCHERS[config.MATCH_START_WHO],
            message_handlers.handle_start_who)
        self.assertEqual(
            logparse.LOG_MATCHERS[config.MATCH_KILL],
            message_handlers.handle_kill)

        for bid_matcher in config.MATCH_BID:
            self.assertIn(bid_matcher, logparse.LOG_MATCHERS)
        for drop_matcher in config.MATCH_DROP:
            self.assertIn(drop_matcher, logparse.LOG_MATCHERS)

    @mock.patch('ninjalooter.utils.store_state')
    @mock.patch('time.sleep')
    @mock.patch('wx.PostEvent')
    def test_parse_logfile(self, mock_post_event, mock_sleep, mock_store_state):
        log_data = (
            base.SAMPLE_ATTENDANCE_LOGS
            + base.SAMPLE_OOC_DROP
            + base.SAMPLE_KILL_TIMES
        )
        log_lines = log_data.splitlines(keepends=True)

        run = threading.Event()
        run.set()
        iteration = 0

        def fake_readlines():
            nonlocal iteration
            iteration += 1
            if iteration == 1:
                return log_lines
            run.clear()
            return []

        mock_file = mock.MagicMock()
        mock_file.readlines = fake_readlines
        mock_file.tell.return_value = 0

        mock_open = mock.MagicMock()
        mock_open.__enter__ = mock.Mock(return_value=mock_file)
        mock_open.__exit__ = mock.Mock(return_value=False)

        with mock.patch('builtins.open', return_value=mock_open):
            logparse.parse_logfile('somefile.log', mock.Mock(), run)

        # Who parsing should have populated the snapshot
        self.assertGreater(len(config.LAST_WHO_SNAPSHOT), 0)
        self.assertIn('Bill', config.LAST_WHO_SNAPSHOT)
        self.assertIn('Tim', config.LAST_WHO_SNAPSHOT)

        # handle_end_who should have created an attendance log entry
        self.assertEqual(1, len(config.ATTENDANCE_LOGS))
        self.assertEqual(
            "Plane of Sky", config.ATTENDANCE_LOGS[0].zone)

        # Drops from OOC should have been parsed
        pending_names = [p.name for p in config.PENDING_AUCTIONS]
        self.assertIn("Belt of Iniquity", pending_names)

        # Kills should have been parsed
        self.assertEqual(3, len(config.KILL_TIMERS))
        kill_names = [kt.name for kt in config.KILL_TIMERS]
        self.assertIn("an azarack", kill_names)
        self.assertIn("a shimmering meteor", kill_names)
        self.assertIn("a soul carrier", kill_names)

        # wx.PostEvent should have been called multiple times
        self.assertGreater(mock_post_event.call_count, 0)

        # time.sleep should have been called (loop ran)
        mock_sleep.assert_called()
