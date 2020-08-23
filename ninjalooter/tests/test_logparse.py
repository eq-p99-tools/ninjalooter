from unittest import mock

from ninjalooter import logparse
from ninjalooter.tests import base
from ninjalooter import utils

SAMPLE_OOC = (
    "[Mon Aug 17 00:04:45 2020] "
    "Calcium says out of character, "
    "'Shiny Pauldrons Belt of Iniquity'")


class TestLogparse(base.NLTestBase):
    def setUp(self) -> None:
        super(TestLogparse, self).setUp()
        utils.setup_aho()

    @mock.patch('builtins.open', new_callable=mock.mock_open,
                read_data=base.SAMPLE_FULL_TEST)
    def test_parse_logfile(self, logfile):
        self.skipTest("Need to figure out how to do this properly")
        pending_auctions = logparse.config.PENDING_AUCTIONS
        active_auctions = logparse.config.ACTIVE_AUCTIONS
        pending_auctions.clear()
        active_auctions.clear()

        # Pre-activate this auction so we can pretend it became active
        pending_auctions.append('BELT OF INIQUITY')
        utils.start_auction_dkp('BELT OF INIQUITY')

        logparse.parse_logfile('somefile.log')

        self.assertEqual(1, len(active_auctions))
        self.assertIn('BELT OF INIQUITY', active_auctions)
        auc = active_auctions['BELT OF INIQUITY']
        highest_bid = auc.highest()
        self.assertEqual(1, len(highest_bid))
        self.assertIn(('Peter', 16), highest_bid)
