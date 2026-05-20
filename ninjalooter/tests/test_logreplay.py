import datetime
import os
import tempfile

from ninjalooter import config, logreplay
from ninjalooter.tests import base


SAMPLE_RAIDTICK_LOG = """\
[Sun Aug 16 22:46:29 2020] Toald tells the guild, 'RAIDTICK'
[Sun Aug 16 22:46:32 2020] Players on EverQuest:
[Sun Aug 16 22:46:32 2020] ---------------------------
[Sun Aug 16 22:46:32 2020] [50 Warrior] Bill (Dark Elf) <Kingdom> LFG
[Sun Aug 16 22:46:32 2020] [50 Druid] Tom (Wood Elf) <Freya's Chariot> LFG
[Sun Aug 16 22:46:32 2020] There are 2 players in Plane of Sky.
[Sun Aug 16 23:46:29 2020] Toald tells the guild, 'RAIDTICK'
[Sun Aug 16 23:46:32 2020] Players on EverQuest:
[Sun Aug 16 23:46:32 2020] ---------------------------
[Sun Aug 16 23:46:32 2020] [50 Warrior] Bill (Dark Elf) <Kingdom> LFG
[Sun Aug 16 23:46:32 2020] [50 Druid] Tom (Wood Elf) <Freya's Chariot> LFG
[Sun Aug 16 23:46:32 2020] [50 Wizard] Jim (Erudite) <Venerate> LFG
[Sun Aug 16 23:46:32 2020] There are 3 players in Plane of Sky.
"""

SAMPLE_NO_RAIDTICK_LOG = """\
[Sun Aug 16 22:46:32 2020] Players on EverQuest:
[Sun Aug 16 22:46:32 2020] ---------------------------
[Sun Aug 16 22:46:32 2020] [50 Warrior] Bill (Dark Elf) <Kingdom> LFG
[Sun Aug 16 22:46:32 2020] There are 1 player in Plane of Sky.
[Sun Aug 16 23:46:32 2020] Players on EverQuest:
[Sun Aug 16 23:46:32 2020] ---------------------------
[Sun Aug 16 23:46:32 2020] [50 Druid] Tom (Wood Elf) <Freya's Chariot> LFG
[Sun Aug 16 23:46:32 2020] There are 1 player in Plane of Sky.
"""


class TestScanAttendance(base.NLTestBase):

    def test_scan_with_raidticks(self):
        lines = SAMPLE_RAIDTICK_LOG.splitlines(keepends=True)
        start = datetime.datetime(2020, 8, 16, 22, 0, 0)
        end = datetime.datetime(2020, 8, 17, 0, 0, 0)

        result = logreplay.scan_attendance(lines, start, end)

        self.assertEqual(result.total_whos, 2)
        self.assertEqual(result.raidtick_whos, 2)

    def test_scan_no_raidticks(self):
        lines = SAMPLE_NO_RAIDTICK_LOG.splitlines(keepends=True)
        start = datetime.datetime(2020, 8, 16, 22, 0, 0)
        end = datetime.datetime(2020, 8, 17, 0, 0, 0)

        result = logreplay.scan_attendance(lines, start, end)

        self.assertEqual(result.total_whos, 2)
        self.assertEqual(result.raidtick_whos, 0)

    def test_scan_time_range_filters(self):
        lines = SAMPLE_RAIDTICK_LOG.splitlines(keepends=True)
        start = datetime.datetime(2020, 8, 16, 23, 0, 0)
        end = datetime.datetime(2020, 8, 17, 0, 0, 0)

        result = logreplay.scan_attendance(lines, start, end)

        self.assertEqual(result.total_whos, 1)
        self.assertEqual(result.raidtick_whos, 1)

    def test_scan_empty_range(self):
        lines = SAMPLE_RAIDTICK_LOG.splitlines(keepends=True)
        start = datetime.datetime(2021, 1, 1, 0, 0, 0)
        end = datetime.datetime(2021, 1, 2, 0, 0, 0)

        result = logreplay.scan_attendance(lines, start, end)

        self.assertEqual(result.total_whos, 0)
        self.assertEqual(result.raidtick_whos, 0)

    def test_scan_sample_attendance_logs(self):
        lines = base.SAMPLE_ATTENDANCE_LOGS.splitlines(keepends=True)
        start = datetime.datetime(2020, 8, 16, 0, 0, 0)
        end = datetime.datetime(2020, 8, 17, 0, 0, 0)

        result = logreplay.scan_attendance(lines, start, end)

        self.assertEqual(result.total_whos, 1)
        self.assertEqual(result.raidtick_whos, 0)


class TestReplayAttendance(base.NLTestBase):

    def test_replay_creates_attendance_logs(self):
        lines = SAMPLE_RAIDTICK_LOG.splitlines(keepends=True)
        start = datetime.datetime(2020, 8, 16, 22, 0, 0)
        end = datetime.datetime(2020, 8, 17, 0, 0, 0)

        self.assertEqual(len(config.ATTENDANCE_LOGS), 0)
        logreplay.replay_attendance(lines, start, end)

        self.assertEqual(len(config.ATTENDANCE_LOGS), 2)
        self.assertTrue(config.ATTENDANCE_LOGS[0].raidtick)
        self.assertTrue(config.ATTENDANCE_LOGS[1].raidtick)
        self.assertEqual(len(config.ATTENDANCE_LOGS[0].log), 2)
        self.assertEqual(len(config.ATTENDANCE_LOGS[1].log), 3)

    def test_replay_without_raidtick(self):
        lines = SAMPLE_NO_RAIDTICK_LOG.splitlines(keepends=True)
        start = datetime.datetime(2020, 8, 16, 22, 0, 0)
        end = datetime.datetime(2020, 8, 17, 0, 0, 0)

        logreplay.replay_attendance(lines, start, end)

        self.assertEqual(len(config.ATTENDANCE_LOGS), 2)
        self.assertFalse(config.ATTENDANCE_LOGS[0].raidtick)
        self.assertFalse(config.ATTENDANCE_LOGS[1].raidtick)

    def test_replay_time_range_filters(self):
        lines = SAMPLE_RAIDTICK_LOG.splitlines(keepends=True)
        start = datetime.datetime(2020, 8, 16, 23, 0, 0)
        end = datetime.datetime(2020, 8, 17, 0, 0, 0)

        logreplay.replay_attendance(lines, start, end)

        self.assertEqual(len(config.ATTENDANCE_LOGS), 1)
        self.assertTrue(config.ATTENDANCE_LOGS[0].raidtick)
        self.assertEqual(len(config.ATTENDANCE_LOGS[0].log), 3)

    def test_replay_cancellation(self):
        lines = SAMPLE_RAIDTICK_LOG.splitlines(keepends=True)
        start = datetime.datetime(2020, 8, 16, 22, 0, 0)
        end = datetime.datetime(2020, 8, 17, 0, 0, 0)

        call_count = [0]

        def cancel_after_one(current, total):  # pylint: disable=unused-argument
            call_count[0] += 1
            return call_count[0] <= 3

        logreplay.replay_attendance(lines, start, end, progress_callback=cancel_after_one)
        # Should have stopped early; may or may not complete first who block
        self.assertLessEqual(len(config.ATTENDANCE_LOGS), 1)

    def test_replay_sample_attendance_logs(self):
        lines = base.SAMPLE_ATTENDANCE_LOGS.splitlines(keepends=True)
        start = datetime.datetime(2020, 8, 16, 0, 0, 0)
        end = datetime.datetime(2020, 8, 17, 0, 0, 0)

        logreplay.replay_attendance(lines, start, end)

        self.assertEqual(len(config.ATTENDANCE_LOGS), 1)
        self.assertEqual(len(config.ATTENDANCE_LOGS[0].log), 25)
        self.assertEqual(config.ATTENDANCE_LOGS[0].zone, "Plane of Sky")


class TestEnumerateLogfiles(base.NLTestBase):

    def test_enumerate_logfiles(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create fake logfiles
            f1 = os.path.join(tmpdir, "eqlog_Toald_P1999Green.txt")
            f2 = os.path.join(tmpdir, "eqlog_Alara_P1999Green.txt")
            f3 = os.path.join(tmpdir, "not_a_logfile.txt")

            for f in (f1, f2, f3):
                with open(f, "w") as fp:
                    fp.write("test")

            # Make f2 newer
            os.utime(f1, (1000, 1000))
            os.utime(f2, (2000, 2000))

            results = utils.enumerate_logfiles(tmpdir)

            self.assertEqual(len(results), 2)
            # f2 is newer, should be first
            self.assertEqual(results[0][1], "Alara")
            self.assertEqual(results[0][2], "P1999Green")
            self.assertEqual(results[1][1], "Toald")
            self.assertEqual(results[1][2], "P1999Green")

    def test_enumerate_empty_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            results = utils.enumerate_logfiles(tmpdir)
            self.assertEqual(results, [])

    def test_enumerate_nonexistent_dir(self):
        results = utils.enumerate_logfiles("/nonexistent/path/abc123")
        self.assertEqual(results, [])


# Need utils import for TestEnumerateLogfiles
from ninjalooter import utils  # noqa: E402
