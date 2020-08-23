from unittest import mock

from ninjalooter import models
from ninjalooter.tests import base
from ninjalooter import utils


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
        utils.config.PLAYER_AFFILIATIONS = base.SAMPLE_PLAYER_AFFILIATIONS

        pop_roll_text, pop_rand_text = utils.generate_pop_roll()

        expected = '/shout 0-3 BL // 4-8 Kingdom // 9-14 VCR'
        self.assertEqual('/random 14', pop_rand_text)
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
        self.assertTrue(utils.config.TREE._finalized)
        self.assertGreater(utils.config.TREE._counter, 100000)
