from unittest import mock

from ninjalooter.tests import base
from ninjalooter import utils


class TestUtils(base.NLTestBase):
    def test_generate_pop_roll(self):
        utils.config.PLAYER_AFFILIATIONS = base.SAMPLE_PLAYER_AFFILIATIONS

        pop_roll_text, total = utils.generate_pop_roll()

        expected = '1-4 BL // 5-9 Kingdom // 10-15 VCR'
        self.assertEqual(16, total)
        self.assertEqual(expected, pop_roll_text)

    def test_get_character_name_from_logfile(self):
        result = utils.get_character_name_from_logfile(
            r"C:\EverQuest\Logs\eqlog_charname_P1999Green.txt")
        self.assertEqual("Charname", result)
        result = utils.get_character_name_from_logfile(
            r"C:\EverQuest\Logs\eqlog_UNKNOWN.txt")
        self.assertEqual("NO MATCH", result)

    @mock.patch('builtins.open', new_callable=mock.mock_open, read_data='1')
    @mock.patch('os.stat')
    @mock.patch('os.walk')
    def test_load_latest_logfile(self, mock_walk, mock_stat, mock_open):
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
        logfile, name = utils.load_latest_logfile("C:\\somedir")
        self.assertEqual("Bob", name)
        mock_open.assert_called_once_with(
            "C:\\somedir\\eqlog_Bob_P1999Green.txt", 'r')

        # One file: only irrelevant
        mock_walk.return_value = [
            ('C:\\somedir', [], ['dbg.log'])]
        logfile, name = utils.load_latest_logfile("C:\\somedir")
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

    def test_get_next_number(self):
        utils.config.NUMBERS = [10, 20, 30]
        utils.config.LAST_NUMBER = 0
        self.assertEqual(10, utils.get_next_number())
        self.assertEqual(20, utils.get_next_number())
        self.assertEqual(30, utils.get_next_number())
        self.assertEqual(10, utils.get_next_number())
