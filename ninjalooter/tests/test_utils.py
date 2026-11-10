import datetime
import json
import os
import tempfile
from unittest import mock

import requests_mock

from ninjalooter import config
from ninjalooter import models
from ninjalooter.tests import base
from ninjalooter import utils


class TestEasternTimeOffset(base.NLTestBase):
    def _run_offset_test(self, local_hours, eastern_hours):
        """Helper: mock local and Eastern UTC offsets, return eastern_time_offset()."""
        with mock.patch('ninjalooter.utils.datetime') as mock_dt:
            mock_dt.timedelta = datetime.timedelta
            mock_now = mock.MagicMock()
            mock_dt.datetime.utcnow.return_value = mock_now

            local_offset = datetime.timedelta(hours=local_hours)
            eastern_offset = datetime.timedelta(hours=eastern_hours)
            mock_local = mock.MagicMock()
            mock_local.utcoffset.return_value = local_offset
            mock_eastern = mock.MagicMock()
            mock_eastern.utcoffset.return_value = eastern_offset
            mock_now.astimezone.side_effect = (
                lambda tz=None: mock_local if tz is None else mock_eastern)

            return utils.eastern_time_offset()

    def test_offset_behind_eastern(self):
        """User in US/Pacific (UTC-8) with Eastern at UTC-5: offset = +3h."""
        result = self._run_offset_test(local_hours=-8, eastern_hours=-5)
        self.assertEqual(result, datetime.timedelta(hours=3))

    def test_offset_ahead_of_eastern(self):
        """User in CET (UTC+1) with Eastern at UTC-5: offset = -6h."""
        result = self._run_offset_test(local_hours=1, eastern_hours=-5)
        self.assertEqual(result, datetime.timedelta(hours=-6))

    def test_offset_already_eastern(self):
        """User already in Eastern: offset = 0."""
        result = self._run_offset_test(local_hours=-5, eastern_hours=-5)
        self.assertEqual(result, datetime.timedelta(0))


class TestUtils(base.NLTestBase):
    def test_start_auction_dkp(self):
        pending = utils.config.PENDING_AUCTIONS
        active = utils.config.ACTIVE_AUCTIONS
        pending.clear()
        active.clear()

        copper_disc = models.ItemDrop('Copper Disc', 'Jim', 'timestamp')
        pending.append(copper_disc)

        utils.start_auction_dkp(copper_disc, 'VCR')

        self.assertListEqual([], pending)
        self.assertIn(copper_disc.uuid, active)
        self.assertIsInstance(active[copper_disc.uuid], models.DKPAuction)

    def test_start_auction_random(self):
        pending = utils.config.PENDING_AUCTIONS
        active = utils.config.ACTIVE_AUCTIONS
        pending.clear()
        active.clear()

        copper_disc = models.ItemDrop('Copper Disc', 'Jim', 'timestamp')
        pending.append(copper_disc)

        utils.start_auction_random(copper_disc)

        self.assertListEqual([], pending)
        self.assertIn(copper_disc.uuid, active)
        self.assertIsInstance(active[copper_disc.uuid], models.RandomAuction)

    def test_generate_pop_roll(self):
        utils.config.LAST_WHO_SNAPSHOT = base.SAMPLE_LAST_WHO_SNAPSHOT

        pop_roll_text, pop_rand_text = utils.generate_pop_roll()

        expected = '/shout 1-4 BL // 5-9 Kingdom // 10-15 VCR'
        self.assertEqual('/random 1 15', pop_rand_text)
        self.assertEqual(expected, pop_roll_text)

    def test_get_character_name_from_logfile(self):
        result = utils.get_character_name_from_logfile(
            r"C:\EverQuest\Logs\eqlog_charname_P1999Green.txt")
        self.assertEqual("Charname", result)
        result = utils.get_character_name_from_logfile(
            r"C:\EverQuest\Logs\eqlog_UNKNOWN.txt")
        self.assertEqual("NO MATCH", result)

    @mock.patch('os.stat')
    @mock.patch('os.walk')
    def test_get_latest_logfile(self, mock_walk, mock_stat):
        # Three files: one recent, one irrelevant, one old
        mock_walk.return_value = [
            ('C:\\somedir', [],
             ['eqlog_Bob_P1999Green.txt', 'dbg.log',
              'eqlog_Tom_P1999Green.txt'])]
        file_stat1 = mock.Mock()
        file_stat1.st_mtime = 2
        file_stat2 = mock.Mock()
        file_stat2.st_mtime = 1
        mock_stat.side_effect = (file_stat1, file_stat2)
        logfile, name = utils.get_latest_logfile("C:\\somedir")
        self.assertEqual("Bob", name)

        # One file: only irrelevant
        mock_walk.return_value = [
            ('C:\\somedir', [], ['dbg.log'])]
        logfile, name = utils.get_latest_logfile("C:\\somedir")
        self.assertIsNone(name)
        self.assertIsNone(logfile)

    def test_load_item_data(self):
        item_data = utils.load_item_data()
        self.assertIsNotNone(item_data)
        self.assertIn('BELT OF INIQUITY', item_data)

    def test_setup_aho(self):
        utils.setup_aho()
        self.assertTrue(utils.config.TRIE._finalized)
        self.assertGreater(utils.config.TRIE._counter, 100000)

    @requests_mock.Mocker()
    def test_fetch_google_sheet_data(self, mock_requests):
        test_id = "1vIHTT-YqlS5V8qkCQF8du5Xgl-QOVu1nMNjk_h8eLDQ"
        test_url = (
            "https://docs.google.com/spreadsheets/d/{id}/edit#gid=0"
        ).format(id=test_id)

        csv_url = (
            "https://docs.google.com/spreadsheets/d/{id}/export?format=csv"
        ).format(id=test_id)
        mock_requests.get(csv_url, text=base.SAMPLE_GSHEETS_TEXT)

        # Fetch URL from ID
        data = utils.fetch_google_sheet_data(test_id)
        self.assertListEqual(
            list(base.SAMPLE_GSHEETS_DATA[0].keys()), data.fieldnames)
        self.assertEqual(base.SAMPLE_GSHEETS_DATA, list(data))

        # Fetch URL from URL
        data = utils.fetch_google_sheet_data(test_url)
        self.assertListEqual(
            list(base.SAMPLE_GSHEETS_DATA[0].keys()), data.fieldnames)
        self.assertEqual(base.SAMPLE_GSHEETS_DATA, list(data))

        # Fail gracefully if URL has no valid ID
        self.assertIsNone(utils.fetch_google_sheet_data("http://google.com"))

        # Fail gracefully if URL can't be fetched
        mock_requests.get(csv_url, status_code=404)
        self.assertIsNone(utils.fetch_google_sheet_data(test_url))

        # Fail gracefully if URL returns bad/no data
        mock_requests.get(csv_url, text="<html>This isn't csv</html>")
        self.assertEqual([], list(utils.fetch_google_sheet_data(test_url)))

    def test_translate_sheet_csv_to_mindkp_json(self):
        data = utils.translate_sheet_csv_to_mindkp_json(
            base.SAMPLE_GSHEETS_DATA)
        self.assertEqual(base.SAMPLE_GSHEETS_MINDKP_JSON, data)

    def test_compose_ranges_no_overlap(self):
        text = "Alpha Beta Gamma"
        ranges = [(0, 5), (6, 10), (11, 16)]
        result = utils.compose_ranges(ranges, text)
        self.assertEqual(["Alpha", "Beta", "Gamma"], result)

    def test_compose_ranges_with_overlap(self):
        text = "Belt of Iniquity"
        ranges = [(0, 16), (5, 16)]
        result = utils.compose_ranges(ranges, text)
        self.assertEqual(["Belt of Iniquity"], result)

    def test_compose_ranges_empty(self):
        result = utils.compose_ranges([], "any text")
        self.assertEqual([], result)

    def test_get_items_from_text(self):
        utils.setup_aho()
        items = utils.get_items_from_text("Belt of Iniquity and Copper Disc here")
        self.assertIn("Belt of Iniquity", items)
        self.assertIn("Copper Disc", items)
        self.assertEqual(2, len(items))

    def test_get_items_from_text_no_match(self):
        utils.setup_aho()
        items = utils.get_items_from_text("just some random chatting")
        self.assertEqual([], items)

    def test_datetime_to_eq_format(self):
        dt = datetime.datetime(2020, 8, 16, 22, 46, 32)
        config.EXPORT_TIME_IN_EASTERN = False
        result = utils.datetime_to_eq_format(dt)
        self.assertEqual("Sun Aug 16 22:46:32 2020", result)

    def test_datetime_from_eq_format(self):
        config.EXPORT_TIME_IN_EASTERN = False
        result = utils.datetime_from_eq_format("Sun Aug 16 22:46:32 2020")
        self.assertEqual(datetime.datetime(2020, 8, 16, 22, 46, 32), result)

    def test_datetime_roundtrip(self):
        config.EXPORT_TIME_IN_EASTERN = False
        dt = datetime.datetime(2020, 8, 16, 22, 46, 32)
        eq_str = utils.datetime_to_eq_format(dt)
        result = utils.datetime_from_eq_format(eq_str)
        self.assertEqual(dt, result)

    def test_get_timestamp(self):
        line = "[Sun Aug 16 22:46:32 2020] Some log text here"
        result = utils.get_timestamp(line)
        self.assertIsNotNone(result)
        self.assertEqual(datetime.datetime(2020, 8, 16, 22, 46, 32), result)

    def test_get_timestamp_no_match(self):
        result = utils.get_timestamp("no timestamp here")
        self.assertIsNone(result)

    def test_get_first_timestamp(self):
        lines = [
            "no timestamp",
            "[Sun Aug 16 22:46:32 2020] first real line",
            "[Sun Aug 16 22:47:00 2020] second line",
        ]
        result = utils.get_first_timestamp(lines)
        self.assertEqual(datetime.datetime(2020, 8, 16, 22, 46, 32), result)

    def test_get_first_timestamp_none(self):
        result = utils.get_first_timestamp(["no timestamps at all"])
        self.assertEqual(datetime.datetime.fromtimestamp(0), result)

    def test_find_timestamp_empty(self):
        self.assertIsNone(utils.find_timestamp([], datetime.datetime.now()))

    def test_find_timestamp_no_timestamps_in_lines(self):
        lines = ["no timestamps", "still none"]
        self.assertIsNone(utils.find_timestamp(lines, datetime.datetime.now()))

    def test_find_timestamp_target_before_all(self):
        lines = [
            "[Sun Aug 16 22:46:32 2020] line one",
            "[Sun Aug 16 22:47:32 2020] line two",
        ]
        target = datetime.datetime(2020, 8, 16, 22, 0, 0)
        result = utils.find_timestamp(lines, target)
        self.assertEqual(0, result)

    def test_find_timestamp_target_after_all(self):
        lines = [
            "[Sun Aug 16 22:46:32 2020] line one",
            "[Sun Aug 16 22:47:32 2020] line two",
        ]
        target = datetime.datetime(2020, 8, 16, 23, 0, 0)
        self.assertIsNone(utils.find_timestamp(lines, target))

    def test_find_timestamp_target_in_middle(self):
        lines = [
            "[Sun Aug 16 22:00:00 2020] early",
            "[Sun Aug 16 22:30:00 2020] middle",
            "[Sun Aug 16 23:00:00 2020] late",
        ]
        target = datetime.datetime(2020, 8, 16, 22, 30, 0)
        result = utils.find_timestamp(lines, target)
        self.assertIsNotNone(result)
        self.assertGreaterEqual(result, 0)
        self.assertLess(result, len(lines))

    def test_ignore_pending_item(self):
        item = models.ItemDrop('Copper Disc', 'Jim', 'timestamp')
        config.PENDING_AUCTIONS.append(item)
        self.assertEqual(1, len(config.PENDING_AUCTIONS))
        self.assertEqual(0, len(config.IGNORED_AUCTIONS))

        utils.ignore_pending_item(item)
        self.assertEqual(0, len(config.PENDING_AUCTIONS))
        self.assertEqual(1, len(config.IGNORED_AUCTIONS))
        self.assertEqual(item, config.IGNORED_AUCTIONS[0])

    def test_get_pending_item_names(self):
        config.PENDING_AUCTIONS = [
            models.ItemDrop('Copper Disc', 'Jim', 'ts'),
            models.ItemDrop('Belt of Iniquity', 'Jim', 'ts'),
        ]
        result = utils.get_pending_item_names()
        self.assertEqual(['copper disc', 'belt of iniquity'], result)

    def test_get_active_item_names(self):
        item = models.ItemDrop('Copper Disc', 'Jim', 'timestamp')
        config.PENDING_AUCTIONS.append(item)
        utils.start_auction_dkp(item, 'VCR')
        result = utils.get_active_item_names()
        self.assertEqual(['copper disc'], result)

    def test_complete_old_auctions(self):
        config.ACTIVE_AUCTIONS.clear()
        config.HISTORICAL_AUCTIONS.clear()

        old_item = models.ItemDrop('Copper Disc', 'Jim', 'ts')
        config.PENDING_AUCTIONS.append(old_item)
        old_auc = utils.start_auction_dkp(old_item, 'VCR')
        old_auc.start_time = datetime.datetime.now() - datetime.timedelta(
            hours=2)

        new_item = models.ItemDrop('Platinum Disc', 'Jim', 'ts')
        config.PENDING_AUCTIONS.append(new_item)
        new_auc = utils.start_auction_dkp(new_item, 'VCR')
        new_auc.start_time = datetime.datetime.now()

        self.assertEqual(2, len(config.ACTIVE_AUCTIONS))

        cutoff = datetime.datetime.now() - datetime.timedelta(hours=1)
        utils.complete_old_auctions(cutoff)

        self.assertNotIn(old_item.uuid, config.ACTIVE_AUCTIONS)
        self.assertIn(old_item.uuid, config.HISTORICAL_AUCTIONS)
        self.assertIn(new_item.uuid, config.ACTIVE_AUCTIONS)
        self.assertNotIn(new_item.uuid, config.HISTORICAL_AUCTIONS)

    def test_get_pop_numbers(self):
        config.LAST_WHO_SNAPSHOT = base.SAMPLE_LAST_WHO_SNAPSHOT
        pops = utils.get_pop_numbers()
        self.assertEqual(4, pops['BL'])
        self.assertEqual(5, pops['Kingdom'])
        self.assertEqual(6, pops['VCR'])
        self.assertEqual(0, pops['Seal Team'])

    def test_get_pop_numbers_with_extras(self):
        config.LAST_WHO_SNAPSHOT = base.SAMPLE_LAST_WHO_SNAPSHOT
        pops = utils.get_pop_numbers(extras={'Other': 3})
        self.assertEqual(3, pops['Other'])

    def test_request_store_state_coalesces(self):
        utils.cancel_pending_state_save()
        with mock.patch('ninjalooter.utils.threading.Timer') as timer_cls:
            utils.request_store_state()
            utils.request_store_state()
            self.assertEqual(1, timer_cls.call_count)
            timer_cls.return_value.start.assert_called_once()
        utils.cancel_pending_state_save()

    def test_flush_store_state_writes_immediately(self):
        utils.cancel_pending_state_save()
        with mock.patch('ninjalooter.utils.threading.Timer') as timer_cls:
            utils.request_store_state()
            with mock.patch('ninjalooter.utils.store_state') as store:
                utils.flush_store_state()
            timer_cls.return_value.cancel.assert_called_once()
            store.assert_called_once_with()
        utils.cancel_pending_state_save()

    @mock.patch('os.walk')
    def test_consider_logfile_switch_ignores_current_file(self, mock_walk):
        current = os.path.abspath('eqlog_Bob_P1999Green.txt')
        self.assertIsNone(utils.consider_logfile_switch(current, current))
        mock_walk.assert_not_called()

    def test_consider_logfile_switch_picks_newer_log(self):
        with tempfile.TemporaryDirectory() as directory:
            current = os.path.join(directory, 'eqlog_Old_P1999Green.txt')
            newer = os.path.join(directory, 'eqlog_New_P1999Green.txt')
            with open(current, 'w') as handle:
                handle.write('old')
            with open(newer, 'w') as handle:
                handle.write('new')
            os.utime(current, (1, 1))
            os.utime(newer, (2, 2))
            # Windows deletes this directory with os.walk, so the patch
            # cannot still be active when the temporary directory closes.
            with mock.patch('os.walk') as mock_walk:
                found = utils.consider_logfile_switch(newer, current)
                self.assertEqual((os.path.abspath(newer), 'New'), found)
                self.assertIsNone(utils.consider_logfile_switch(current, newer))
                self.assertIsNone(
                    utils.consider_logfile_switch(os.path.join(directory, 'dbg.txt'), current)
                )
                mock_walk.assert_not_called()

    def test_store_state(self):
        config.PENDING_AUCTIONS = []
        config.ACTIVE_AUCTIONS = {}
        config.HISTORICAL_AUCTIONS = {}
        config.ATTENDANCE_LOGS = []
        config.KILL_TIMERS = []

        with tempfile.NamedTemporaryFile(
                mode='w', suffix='.json', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            old_save = config.SAVE_STATE_FILE
            config.SAVE_STATE_FILE = tmp_path
            utils.store_state()
            config.SAVE_STATE_FILE = old_save

            with open(tmp_path) as f:
                data = json.load(f)
            self.assertIn('PENDING_AUCTIONS', data)
            self.assertIn('ACTIVE_AUCTIONS', data)
            self.assertIn('HISTORICAL_AUCTIONS', data)
            self.assertIn('ATTENDANCE_LOGS', data)
            self.assertIn('PLAYER_DB', data)
            self.assertIn('KILL_TIMER_SECTIONS_EXPANDED_CACHE', data)
        finally:
            os.unlink(tmp_path)

    def test_load_state(self):
        item = models.ItemDrop('Copper Disc', 'Jim', 'ts')
        json_state = {
            'PENDING_AUCTIONS': [item],
            'ACTIVE_AUCTIONS': {},
            'HISTORICAL_AUCTIONS': {},
            'ATTENDANCE_LOGS': [],
            'KILL_TIMERS': [],
            'PLAYER_DB': {},
            'LAST_WHO_SNAPSHOT': {},
        }
        with tempfile.NamedTemporaryFile(
                mode='w', suffix='.json', delete=False) as tmp:
            json.dump(json_state, tmp, cls=utils.JSONEncoder)
            tmp_path = tmp.name

        try:
            config.PENDING_AUCTIONS = []
            utils.load_state(state_file=tmp_path)
            self.assertEqual(1, len(config.PENDING_AUCTIONS))
            self.assertEqual('Copper Disc', config.PENDING_AUCTIONS[0].name)
        finally:
            os.unlink(tmp_path)

    def test_load_state_missing_file(self):
        config.PENDING_AUCTIONS = ['sentinel']
        utils.load_state(state_file='nonexistent_file_12345.json')
        self.assertEqual(['sentinel'], config.PENDING_AUCTIONS)

    def test_export_to_eqdkp_distinct_sheets_for_case_only_tick_names(self):
        """Excel sheet names are unique case-insensitively; export must disambiguate."""
        config.RESTRICT_EXPORT = False
        base_time = datetime.datetime(2020, 8, 16, 22, 46, 32)
        player = models.Player("Jim", level=50, pclass="Warrior", guild="Venerate")
        log = {"Jim": player}
        wholog_a = models.WhoLog(
            base_time,
            log,
            raidtick=True,
            tick_name="LadyVox",
        )
        wholog_b = models.WhoLog(
            base_time + datetime.timedelta(seconds=1),
            log,
            raidtick=True,
            tick_name="ladyvox",
        )
        config.ATTENDANCE_LOGS = [wholog_a, wholog_b]

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            path = tmp.name
        try:
            result = utils.export_to_eqdkp(path)
            self.assertTrue(result)
            self.assertGreater(os.path.getsize(path), 0)
        finally:
            os.unlink(path)


class TestPurgeExpiredKillTimers(base.NLTestBase):
    def test_purge_removes_old_entries(self):
        now = datetime.datetime.now()
        old_time = (now - datetime.timedelta(days=10)).strftime("%a %b %d %H:%M:%S %Y")
        recent_time = (now - datetime.timedelta(days=1)).strftime("%a %b %d %H:%M:%S %Y")
        config.KILL_TIMERS = [
            models.KillTimer(old_time, "old mob"),
            models.KillTimer(recent_time, "recent mob"),
        ]
        config.KILL_TIMER_TTL_DAYS = 7
        utils.purge_expired_kill_timers()
        self.assertEqual(1, len(config.KILL_TIMERS))
        self.assertEqual("recent mob", config.KILL_TIMERS[0].name)

    def test_purge_disabled_when_ttl_zero(self):
        now = datetime.datetime.now()
        old_time = (now - datetime.timedelta(days=100)).strftime("%a %b %d %H:%M:%S %Y")
        config.KILL_TIMERS = [models.KillTimer(old_time, "ancient mob")]
        config.KILL_TIMER_TTL_DAYS = 0
        utils.purge_expired_kill_timers()
        self.assertEqual(1, len(config.KILL_TIMERS))

    def test_purge_keeps_unparseable_times(self):
        config.KILL_TIMERS = [models.KillTimer("not a real time", "mystery mob")]
        config.KILL_TIMER_TTL_DAYS = 7
        utils.purge_expired_kill_timers()
        self.assertEqual(1, len(config.KILL_TIMERS))

    def test_purge_empty_list(self):
        config.KILL_TIMERS = []
        config.KILL_TIMER_TTL_DAYS = 7
        utils.purge_expired_kill_timers()
        self.assertEqual(0, len(config.KILL_TIMERS))


class TestAlertSound(base.NLTestBase):
    def test_disabled_alerts_do_not_play(self):
        config.AUDIO_ALERTS = False
        utils.alert_sound(config.NEW_DROP_SOUND)
        self.mock_playsound.assert_not_called()

    def test_enabled_alerts_request_playback(self):
        config.AUDIO_ALERTS = True
        utils.alert_sound(config.NEW_DROP_SOUND)
        self.mock_playsound.assert_called_once_with(config.NEW_DROP_SOUND)

    def test_player_ignores_missing_file_and_starts_a_real_one(self):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PySide6.QtWidgets import QApplication

        from ninjalooter.ui.alert_sound import AlertSoundPlayer

        app = QApplication.instance() or QApplication([])
        player = AlertSoundPlayer()
        player.play(os.path.join(config.PROJECT_DIR, "data", "sounds", "missing.mp3"))
        self.assertEqual([], player._players)

        player.play(config.NEW_DROP_SOUND)
        self.assertEqual(1, len(player._players))
        self.assertTrue(player._players[0].source().toLocalFile().endswith("new_drop.mp3"))
        player._discard(player._players[0])
        app.processEvents()
        self.assertEqual([], player._players)
