from unittest import mock

from ninjalooter import config
from ninjalooter import message_handlers
from ninjalooter import models
from ninjalooter.tests import base
from ninjalooter import utils


class TestMessageHandlers(base.NLTestBase):
    def setUp(self) -> None:
        utils.setup_aho()

    @mock.patch('ninjalooter.utils.store_state')
    @mock.patch('wx.PostEvent')
    def test_handle_start_who(self, mock_post_event, mock_store_state):
        # Empty List, full /who
        config.PLAYER_AFFILIATIONS = {}
        for line in base.SAMPLE_WHO_LOG.splitlines():
            match = config.MATCH_WHO.match(line)
            if match:
                message_handlers.handle_who(match, 'window')
        self.assertEqual(24, len(config.PLAYER_AFFILIATIONS))
        self.assertEqual(24, mock_post_event.call_count)
        mock_post_event.reset_mock()

        # Peter and Fred should be marked as guildless
        self.assertIsNone(config.PLAYER_AFFILIATIONS['Peter'])
        self.assertIsNone(config.PLAYER_AFFILIATIONS['Fred'])

        # Mark Peter and Fred as historically belonging to Kingdom
        config.HISTORICAL_AFFILIATIONS['Peter'] = 'Kingdom'
        config.HISTORICAL_AFFILIATIONS['Fred'] = 'Kingdom'

        # Trigger New Who
        message_handlers.handle_start_who(None, 'window')
        mock_post_event.assert_called_once_with(
            'window', models.ClearWhoEvent())
        mock_post_event.reset_mock()

        # Run the full who-list again
        for line in base.SAMPLE_WHO_LOG.splitlines():
            match = config.MATCH_WHO.match(line)
            if match:
                message_handlers.handle_who(match, 'window')
        self.assertEqual(24, len(config.PLAYER_AFFILIATIONS))

        # Peter should be marked as Kingdom, and Fred as guildless
        self.assertEqual('Kingdom', config.PLAYER_AFFILIATIONS['Peter'])
        self.assertIsNone(config.PLAYER_AFFILIATIONS['Fred'])

    @mock.patch('ninjalooter.utils.store_state')
    @mock.patch('wx.PostEvent')
    def test_handle_who(self, mock_post_event, mock_store_state):
        # Empty List, full /who
        config.PLAYER_AFFILIATIONS = {}
        for line in base.SAMPLE_WHO_LOG.splitlines():
            match = config.MATCH_WHO.match(line)
            if match:
                message_handlers.handle_who(match, 'window')
        self.assertEqual(24, len(config.PLAYER_AFFILIATIONS))
        self.assertEqual(24, mock_post_event.call_count)
        mock_post_event.reset_mock()

        # Member changed from ANONYMOUS/Unguilded to Guilded
        config.PLAYER_AFFILIATIONS = {'Jim': None}
        line = '[Sun Aug 16 22:46:32 2020] [ANONYMOUS] Jim (Gnome) <Guild>'
        match = config.MATCH_WHO.match(line)
        message_handlers.handle_who(match, 'window')
        self.assertEqual(1, len(config.PLAYER_AFFILIATIONS))
        self.assertEqual('Guild', config.PLAYER_AFFILIATIONS['Jim'])
        mock_post_event.assert_called_once_with(
            'window', models.WhoEvent('Jim', 'ANONYMOUS', '??', 'Guild'))
        mock_post_event.reset_mock()

        # Member changed guilds
        config.PLAYER_AFFILIATIONS = {'Jim': 'Guild'}
        line = '[Sun Aug 16 22:46:32 2020] [ANONYMOUS] Jim (Gnome) <Other>'
        match = config.MATCH_WHO.match(line)
        message_handlers.handle_who(match, 'window')
        self.assertEqual(1, len(config.PLAYER_AFFILIATIONS))
        self.assertEqual('Other', config.PLAYER_AFFILIATIONS['Jim'])
        mock_post_event.assert_called_once_with(
            'window', models.WhoEvent('Jim', 'ANONYMOUS', '??', 'Other'))
        mock_post_event.reset_mock()

        # Member left their guild
        config.PLAYER_AFFILIATIONS = {'Jim': 'Guild'}
        line = '[Sun Aug 16 22:46:32 2020] [50 Cleric] Jim (Gnome)'
        match = config.MATCH_WHO.match(line)
        message_handlers.handle_who(match, 'window')
        self.assertEqual(1, len(config.PLAYER_AFFILIATIONS))
        self.assertIsNone(config.PLAYER_AFFILIATIONS['Jim'])
        mock_post_event.assert_called_once_with(
            'window', models.WhoEvent('Jim', 'Cleric', '50', None))
        mock_post_event.reset_mock()

        # Some bad line is passed somehow
        config.PLAYER_AFFILIATIONS = {}
        line = "???"
        match = config.MATCH_WHO.match(line)
        message_handlers.handle_who(match, 'window')
        self.assertEqual(0, len(config.PLAYER_AFFILIATIONS))
        mock_post_event.assert_not_called()

    @mock.patch('ninjalooter.utils.store_state')
    @mock.patch('wx.PostEvent')
    def test_handle_drop(self, mock_post_event, mock_store_state):
        config.PLAYER_AFFILIATIONS = {
            'Jim': 'Venerate',
            'James': 'Kingdom',
            'Dan': 'Dial a Daniel',
        }
        config.PENDING_AUCTIONS = list()
        # FILTER OFF - Item linked by a non-federation guild member
        config.RESTRICT_BIDS = False
        line = ("[Sun Aug 16 22:47:31 2020] Dan says out of character, "
                "'Belt of Iniquity'")
        match = config.MATCH_DROP.match(line)
        items = message_handlers.handle_drop(match, 'window')
        self.assertEqual(1, len(items))
        self.assertEqual(1, len(config.PENDING_AUCTIONS))
        mock_post_event.assert_called_once_with(
            'window', models.DropEvent())
        mock_post_event.reset_mock()

        config.PENDING_AUCTIONS = list()
        # FILTER ON - Item linked by a non-federation guild member
        config.RESTRICT_BIDS = True
        line = ("[Sun Aug 16 22:47:31 2020] Dan says out of character, "
                "'Belt of Iniquity'")
        match = config.MATCH_DROP.match(line)
        items = message_handlers.handle_drop(match, 'window')
        self.assertEqual(0, len(items))
        self.assertEqual(0, len(config.PENDING_AUCTIONS))
        mock_post_event.assert_not_called()

        # Item linked by a federation guild member

        # NODROP filter on, droppable item
        config.NODROP_ONLY = True
        line = ("[Sun Aug 16 22:47:31 2020] Jim says out of character, "
                "'Copper Disc'")
        jim_disc_1_uuid = "jim_disc_1_uuid"
        jim_disc_1 = models.ItemDrop(
            'Copper Disc', 'Jim', 'Sun Aug 16 22:47:31 2020',
            uuid=jim_disc_1_uuid)
        match = config.MATCH_DROP.match(line)
        items = list(message_handlers.handle_drop(match, 'window'))
        self.assertEqual(1, len(items))
        self.assertIn('Copper Disc', items)
        self.assertEqual(0, len(config.PENDING_AUCTIONS))
        mock_post_event.assert_called_once_with(
            'window', models.DropEvent())
        mock_post_event.reset_mock()

        # NODROP filter on, NODROP item
        line = ("[Sun Aug 16 22:47:31 2020] Jim says out of character, "
                "'Belt of Iniquity'")
        jim_belt_1_uuid = "jim_belt_1_uuid"
        jim_belt_1 = models.ItemDrop(
            'Belt of Iniquity', 'Jim', 'Sun Aug 16 22:47:31 2020',
            uuid=jim_belt_1_uuid)
        match = config.MATCH_DROP.match(line)
        with mock.patch('uuid.uuid4') as mock_uuid4:
            mock_uuid4.return_value = jim_belt_1_uuid
            items = list(message_handlers.handle_drop(match, 'window'))
        self.assertEqual(1, len(items))
        self.assertIn('Belt of Iniquity', items)
        self.assertEqual(1, len(config.PENDING_AUCTIONS))
        self.assertListEqual(
            [jim_belt_1],
            config.PENDING_AUCTIONS)
        mock_post_event.assert_called_once_with(
            'window', models.DropEvent())
        mock_post_event.reset_mock()

        # NODROP filter off, droppable item
        config.NODROP_ONLY = False
        line = ("[Sun Aug 16 22:47:31 2020] Jim says out of character, "
                "'Copper Disc'")
        match = config.MATCH_DROP.match(line)
        with mock.patch('uuid.uuid4') as mock_uuid4:
            mock_uuid4.return_value = jim_disc_1_uuid
            items = list(message_handlers.handle_drop(match, 'window'))
        self.assertEqual(1, len(items))
        self.assertIn('Copper Disc', items)
        self.assertEqual(2, len(config.PENDING_AUCTIONS))
        self.assertListEqual(
            [jim_belt_1, jim_disc_1],
            config.PENDING_AUCTIONS)
        mock_post_event.assert_called_once_with(
            'window', models.DropEvent())
        mock_post_event.reset_mock()

        # Two items linked by a federation guild member, plus chat
        line = ("[Sun Aug 16 22:47:41 2020] James says out of character, "
                "'Platinum Disc and Golden Amber Earring woo'")
        james_disc_uuid = "james_disc_uuid"
        james_earring_uuid = "james_earring_uuid"
        james_disc = models.ItemDrop(
            'Platinum Disc', 'James', 'Sun Aug 16 22:47:41 2020',
            uuid=james_disc_uuid)
        james_earring = models.ItemDrop(
            'Golden Amber Earring', 'James', 'Sun Aug 16 22:47:41 2020',
            uuid=james_earring_uuid)
        match = config.MATCH_DROP.match(line)
        with mock.patch('uuid.uuid4') as mock_uuid4:
            mock_uuid4.side_effect = [james_disc_uuid, james_earring_uuid]
            items = list(message_handlers.handle_drop(match, 'window'))
        self.assertEqual(2, len(items))
        self.assertListEqual(
            ['Platinum Disc', 'Golden Amber Earring'], items)
        self.assertListEqual(
            [jim_belt_1, jim_disc_1, james_disc, james_earring],
            config.PENDING_AUCTIONS)
        mock_post_event.assert_called_once_with(
            'window', models.DropEvent())
        mock_post_event.reset_mock()

        # Random chatter by federation guild member
        line = ("[Sun Aug 16 22:47:31 2020] Jim says out of character, "
                "'four score and seven years ago, we wanted pixels'")
        match = config.MATCH_DROP.match(line)
        items = list(message_handlers.handle_drop(match, 'window'))
        self.assertEqual(0, len(items))
        self.assertListEqual(
            [jim_belt_1, jim_disc_1, james_disc, james_earring],
            config.PENDING_AUCTIONS)
        mock_post_event.assert_not_called()

        # Someone reports they looted an item
        line = ("[Sun Aug 16 22:47:31 2020] Jim says out of character, "
                "'looted Belt of Iniquity'")
        match = config.MATCH_DROP.match(line)
        items = list(message_handlers.handle_drop(match, 'window'))
        self.assertEqual(0, len(items))
        self.assertListEqual(
            [jim_belt_1, jim_disc_1, james_disc, james_earring],
            config.PENDING_AUCTIONS)
        mock_post_event.assert_not_called()

        # Some bad line is passed somehow
        line = "???"
        match = config.MATCH_DROP.match(line)
        items = list(message_handlers.handle_drop(match, 'window'))
        self.assertEqual(0, len(items))
        self.assertListEqual(
            [jim_belt_1, jim_disc_1, james_disc, james_earring],
            config.PENDING_AUCTIONS)
        mock_post_event.assert_not_called()

    @mock.patch('ninjalooter.utils.store_state')
    @mock.patch('wx.PostEvent')
    def test_handle_bid(self, mock_post_event, mock_store_state):
        config.PLAYER_AFFILIATIONS = {
            'Jim': 'Venerate',
            'Pim': 'Castle',
            'Tim': 'Kingdom',
            'Dan': 'Dial a Daniel',
        }
        item_name = 'Copper Disc'
        itemdrop = models.ItemDrop(item_name, "Jim", "timestamp")
        disc_auction = models.DKPAuction(itemdrop, 'VCR')
        config.ACTIVE_AUCTIONS = {
            itemdrop.uuid: disc_auction
        }

        # FILTER ON - Someone in the alliance bids on an inactive item
        config.RESTRICT_BIDS = True
        line = ("[Sun Aug 16 22:47:31 2020] Jim auctions, "
                "'Platinum Disc 10 DKP'")
        match = config.MATCH_BID.match(line)
        result = message_handlers.handle_bid(match, 'window')
        self.assertFalse(result)
        self.assertListEqual([], disc_auction.highest())
        self.assertEqual(1, len(config.ACTIVE_AUCTIONS))
        mock_post_event.assert_not_called()

        # FILTER ON - Someone outside the alliance bids on an active item
        line = ("[Sun Aug 16 22:47:31 2020] Dan auctions, "
                "'Copper Disc 10 DKP'")
        match = config.MATCH_BID.match(line)
        result = message_handlers.handle_bid(match, 'window')
        self.assertFalse(result)
        self.assertEqual([], disc_auction.highest())
        mock_post_event.assert_not_called()

        # FILTER OFF - Someone in the alliance bids on an inactive item
        config.RESTRICT_BIDS = False
        line = ("[Sun Aug 16 22:47:31 2020] Jim auctions, "
                "'Platinum Disc 10 DKP'")
        match = config.MATCH_BID.match(line)
        result = message_handlers.handle_bid(match, 'window')
        self.assertFalse(result)
        self.assertListEqual([], disc_auction.highest())
        self.assertEqual(1, len(config.ACTIVE_AUCTIONS))
        mock_post_event.assert_not_called()

        # FILTER ON - Someone outside the alliance bids on an active item
        config.RESTRICT_BIDS = True
        line = ("[Sun Aug 16 22:47:31 2020] Dan auctions, "
                "'Copper Disc 10 DKP'")
        match = config.MATCH_BID.match(line)
        result = message_handlers.handle_bid(match, 'window')
        self.assertFalse(result)
        self.assertEqual([], disc_auction.highest())
        mock_post_event.assert_not_called()

        # Someone we haven't seen bids on an active item
        line = ("[Sun Aug 16 22:47:31 2020] Paul auctions, "
                "'Copper Disc 10 DKP'")
        match = config.MATCH_BID.match(line)
        result = message_handlers.handle_bid(match, 'window')
        self.assertFalse(result)
        self.assertListEqual([], disc_auction.highest())
        mock_post_event.assert_not_called()

        # Someone in the alliance says random stuff with a number
        line = ("[Sun Aug 16 22:47:31 2020] Tim auctions, "
                "'I am 12 and what channel is this'")
        match = config.MATCH_BID.match(line)
        result = message_handlers.handle_bid(match, 'window')
        self.assertFalse(result)
        self.assertListEqual([], disc_auction.highest())
        mock_post_event.assert_not_called()

        # Some bad line is passed somehow
        line = "???"
        match = config.MATCH_BID.match(line)
        result = message_handlers.handle_bid(match, 'window')
        self.assertFalse(result)
        self.assertListEqual([], disc_auction.highest())
        mock_post_event.assert_not_called()

        # Someone in the alliance bids on two items at once
        line = ("[Sun Aug 16 22:47:31 2020] Jim auctions, "
                "'Copper Disc 10 DKP Platinum Disc'")
        match = config.MATCH_BID.match(line)
        result = message_handlers.handle_bid(match, 'window')
        self.assertFalse(result)
        self.assertListEqual([], disc_auction.highest())
        mock_post_event.assert_not_called()

        # Someone in the alliance bids on an active item
        line = ("[Sun Aug 16 22:47:31 2020] Jim auctions, "
                "'Copper Disc 10 DKP'")
        match = config.MATCH_BID.match(line)
        result = message_handlers.handle_bid(match, 'window')
        self.assertTrue(result)
        self.assertIn(('Jim', 10), disc_auction.highest())
        mock_post_event.assert_called_once_with(
            'window', models.BidEvent(disc_auction))
        mock_post_event.reset_mock()

        # Someone in the alliance bids on an active item with wrong case
        line = ("[Sun Aug 16 22:47:31 2020] Pim auctions, "
                "'copper DISC 11 DKP'")
        match = config.MATCH_BID.match(line)
        result = message_handlers.handle_bid(match, 'window')
        self.assertTrue(result)
        self.assertIn(('Pim', 11), disc_auction.highest())
        mock_post_event.assert_called_once_with(
            'window', models.BidEvent(disc_auction))
        mock_post_event.reset_mock()

        # Someone in the alliance bids on an active item for their 2nd main
        # This would trigger a bug with "2nd" being read as "2 DKP"
        line = ("[Sun Aug 16 22:47:31 2020] Jim auctions, "
                "'Copper Disc 2nd main 12dkp'")
        match = config.MATCH_BID.match(line)
        result = message_handlers.handle_bid(match, 'window')
        self.assertTrue(result)
        self.assertIn(('Jim', 12), disc_auction.highest())
        mock_post_event.assert_called_once_with(
            'window', models.BidEvent(disc_auction))
        mock_post_event.reset_mock()
