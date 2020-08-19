from ninjalooter import config
from ninjalooter import message_handlers
from ninjalooter import models
from ninjalooter.tests import base
from ninjalooter import utils


class TestMessageHandlers(base.NLTestBase):
    def setUp(self) -> None:
        utils.setup_aho()

    def test_handle_who(self):
        # Empty List, full /who
        config.PLAYER_AFFILIATIONS = {}
        for line in base.SAMPLE_WHO_LOG.splitlines():
            match = config.MATCH_WHO.match(line)
            if match:
                message_handlers.handle_who(match)
        self.assertEqual(24, len(config.PLAYER_AFFILIATIONS))

        # Member changed from ANONYMOUS/Unguilded to Guilded
        config.PLAYER_AFFILIATIONS = {'Jim': None}
        line = '[Sun Aug 16 22:46:32 2020] [ANONYMOUS] Jim (Gnome) <Guild>'
        match = config.MATCH_WHO.match(line)
        message_handlers.handle_who(match)
        self.assertEqual(1, len(config.PLAYER_AFFILIATIONS))
        self.assertEqual('Guild', config.PLAYER_AFFILIATIONS['Jim'])

        # Member changed guilds
        config.PLAYER_AFFILIATIONS = {'Jim': 'Guild'}
        line = '[Sun Aug 16 22:46:32 2020] [ANONYMOUS] Jim (Gnome) <Other>'
        match = config.MATCH_WHO.match(line)
        message_handlers.handle_who(match)
        self.assertEqual(1, len(config.PLAYER_AFFILIATIONS))
        self.assertEqual('Other', config.PLAYER_AFFILIATIONS['Jim'])

        # Member left their guild
        config.PLAYER_AFFILIATIONS = {'Jim': 'Guild'}
        line = '[Sun Aug 16 22:46:32 2020] [50 Cleric] Jim (Gnome)'
        match = config.MATCH_WHO.match(line)
        message_handlers.handle_who(match)
        self.assertEqual(1, len(config.PLAYER_AFFILIATIONS))
        self.assertIsNone(config.PLAYER_AFFILIATIONS['Jim'])

        # Some bad line is passed somehow
        config.PLAYER_AFFILIATIONS = {}
        line = "???"
        match = config.MATCH_WHO.match(line)
        message_handlers.handle_who(match)
        self.assertEqual(0, len(config.PLAYER_AFFILIATIONS))

    def test_handle_ooc(self):
        config.PLAYER_AFFILIATIONS = {
            'Jim': 'Venerate',
            'Dan': 'Dial a Daniel',
        }
        config.PENDING_AUCTIONS = list()
        # Item linked by a non-federation guild member
        line = ("[Sun Aug 16 22:47:31 2020] Dan says out of character, "
                "'Copper Disc'")
        match = config.MATCH_OOC.match(line)
        items = list(message_handlers.handle_ooc(match))
        self.assertEqual(0, len(items))
        self.assertEqual(0, len(config.PENDING_AUCTIONS))

        # Item linked by a federation guild member
        line = ("[Sun Aug 16 22:47:31 2020] Jim says out of character, "
                "'Copper Disc'")
        match = config.MATCH_OOC.match(line)
        items = list(message_handlers.handle_ooc(match))
        self.assertEqual(1, len(items))
        self.assertIn('COPPER DISC', items)
        self.assertEqual(1, len(config.PENDING_AUCTIONS))
        self.assertListEqual(
            ['COPPER DISC'],
            config.PENDING_AUCTIONS)

        # Two items linked by a federation guild member, plus chat
        line = ("[Sun Aug 16 22:47:31 2020] Jim says out of character, "
                "'Copper Disc and Platinum Disc woot'")
        match = config.MATCH_OOC.match(line)
        items = list(message_handlers.handle_ooc(match))
        self.assertEqual(2, len(items))
        self.assertIn('COPPER DISC', items)
        self.assertIn('PLATINUM DISC', items)
        self.assertListEqual(
            ['COPPER DISC', 'COPPER DISC', 'PLATINUM DISC'],
            config.PENDING_AUCTIONS)

        # Random chatter by federation guild member
        line = ("[Sun Aug 16 22:47:31 2020] Jim says out of character, "
                "'four score and seven years ago, we wanted pixels'")
        match = config.MATCH_OOC.match(line)
        items = list(message_handlers.handle_ooc(match))
        self.assertEqual(0, len(items))
        self.assertListEqual(
            ['COPPER DISC', 'COPPER DISC', 'PLATINUM DISC'],
            config.PENDING_AUCTIONS)

        # Some bad line is passed somehow
        line = "???"
        match = config.MATCH_OOC.match(line)
        items = list(message_handlers.handle_ooc(match))
        self.assertEqual(0, len(items))
        self.assertListEqual(
            ['COPPER DISC', 'COPPER DISC', 'PLATINUM DISC'],
            config.PENDING_AUCTIONS)

    def test_handle_auc(self):
        config.PLAYER_AFFILIATIONS = {
            'Jim': 'Venerate',
            'Tim': 'Kingdom',
            'Dan': 'Dial a Daniel',
        }
        item_name = 'COPPER DISC'
        disc_auction = models.DKPAuction(item_name)
        config.ACTIVE_AUCTIONS = {
            item_name: disc_auction
        }

        # Someone in the alliance bids on an inactive item
        line = ("[Sun Aug 16 22:47:31 2020] Jim auctions, "
                "'Platinum Disc 10 DKP'")
        match = config.MATCH_AUC.match(line)
        result = message_handlers.handle_auc(match)
        self.assertFalse(result)
        self.assertEqual(None, disc_auction.highest())
        self.assertEqual(1, len(config.ACTIVE_AUCTIONS))

        # Someone outside the alliance bids on an active item
        line = ("[Sun Aug 16 22:47:31 2020] Dan auctions, "
                "'Copper Disc 10 DKP'")
        match = config.MATCH_AUC.match(line)
        result = message_handlers.handle_auc(match)
        self.assertFalse(result)
        self.assertIsNone(disc_auction.highest())

        # Someone we haven't seen bids on an active item
        line = ("[Sun Aug 16 22:47:31 2020] Paul auctions, "
                "'Copper Disc 10 DKP'")
        match = config.MATCH_AUC.match(line)
        result = message_handlers.handle_auc(match)
        self.assertFalse(result)
        self.assertIsNone(disc_auction.highest())

        # Someone in the alliance says random stuff with a number
        line = ("[Sun Aug 16 22:47:31 2020] Tim auctions, "
                "'I am 12 and what channel is this'")
        match = config.MATCH_AUC.match(line)
        result = message_handlers.handle_auc(match)
        self.assertFalse(result)
        self.assertIsNone(disc_auction.highest())

        # Some bad line is passed somehow
        line = "???"
        match = config.MATCH_AUC.match(line)
        result = message_handlers.handle_auc(match)
        self.assertFalse(result)
        self.assertIsNone(disc_auction.highest())

        # Someone in the alliance bids on two items at once
        line = ("[Sun Aug 16 22:47:31 2020] Jim auctions, "
                "'Copper Disc 10 DKP Platinum Disc'")
        match = config.MATCH_AUC.match(line)
        result = message_handlers.handle_auc(match)
        self.assertFalse(result)
        self.assertIsNone(disc_auction.highest())

        # Someone in the alliance bids on an active item
        line = ("[Sun Aug 16 22:47:31 2020] Jim auctions, "
                "'Copper Disc 10 DKP'")
        match = config.MATCH_AUC.match(line)
        result = message_handlers.handle_auc(match)
        self.assertTrue(result)
        self.assertIn('Jim', disc_auction.highest())
