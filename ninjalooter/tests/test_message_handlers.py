import datetime
from unittest import mock

import dateutil.parser

from ninjalooter import config
from ninjalooter import logreplay
from ninjalooter import message_handlers
from ninjalooter import models
from ninjalooter.tests import base
from ninjalooter import utils


class TestMessageHandlers(base.NLTestBase):
    def setUp(self) -> None:
        super(TestMessageHandlers, self).setUp()
        utils.setup_aho()

    @mock.patch('ninjalooter.utils.store_state')
    @mock.patch('ninjalooter.message_handlers.signals')
    def test_handle_start_who(self, mock_signals, mock_store_state):
        # Empty List, full /who
        config.LAST_WHO_SNAPSHOT = {}
        config.REMEMBER_PLAYER_DATA = True
        for line in base.SAMPLE_ATTENDANCE_LOGS.splitlines():
            match = config.MATCH_WHO.match(line)
            if match:
                message_handlers.handle_who(match)
        self.assertEqual(25, len(config.LAST_WHO_SNAPSHOT))
        self.assertEqual(25, mock_signals.who.emit.call_count)
        mock_signals.who.emit.reset_mock()

        # Peter and Fred should be marked as guildless
        self.assertIsNone(config.LAST_WHO_SNAPSHOT['Peter'].guild)
        self.assertIsNone(config.LAST_WHO_SNAPSHOT['Fred'].guild)

        # Mark Peter and Fred as historically belonging to Kingdom
        config.PLAYER_DB['Peter'] = models.Player(
            'Peter', None, None, 'Kingdom')
        config.PLAYER_DB['Fred'] = models.Player(
            'Fred', None, None, 'Kingdom')

        # Trigger New Who
        message_handlers.handle_start_who(None)
        mock_signals.clear_who.emit.assert_called_once()
        mock_signals.clear_who.emit.reset_mock()

        # Run the full who-list again
        for line in base.SAMPLE_ATTENDANCE_LOGS.splitlines():
            match = config.MATCH_WHO.match(line)
            if match:
                message_handlers.handle_who(match)
        self.assertEqual(25, len(config.LAST_WHO_SNAPSHOT))

        # Peter should be marked as Kingdom, and Fred as guildless
        self.assertEqual('Kingdom', config.LAST_WHO_SNAPSHOT['Peter'].guild)
        self.assertIsNone(config.LAST_WHO_SNAPSHOT['Fred'].guild)

        # It should have picked up Tom in Freya's Chariot
        self.assertEqual(
            "Freya's Chariot", config.LAST_WHO_SNAPSHOT['Tom'].guild)

    @mock.patch('ninjalooter.utils.store_state')
    @mock.patch('ninjalooter.message_handlers.signals')
    def test_handle_who(self, mock_signals, mock_store_state):
        # Empty List, full /who
        config.LAST_WHO_SNAPSHOT = {}
        for line in base.SAMPLE_ATTENDANCE_LOGS.splitlines():
            match = config.MATCH_WHO.match(line)
            if match:
                message_handlers.handle_who(match)
        self.assertEqual(25, len(config.LAST_WHO_SNAPSHOT))
        self.assertEqual(25, mock_signals.who.emit.call_count)
        mock_signals.who.emit.reset_mock()

        # Member changed from ANONYMOUS/Unguilded to Guilded
        config.LAST_WHO_SNAPSHOT = {
            'Jim': models.Player('Jim', None, None, None)}
        line = '[Sun Aug 16 22:46:32 2020] [ANONYMOUS] Jim (Gnome) <Guild>'
        match = config.MATCH_WHO.match(line)
        message_handlers.handle_who(match)
        self.assertEqual(1, len(config.LAST_WHO_SNAPSHOT))
        self.assertEqual('Guild', config.LAST_WHO_SNAPSHOT['Jim'].guild)
        mock_signals.who.emit.assert_called_once()
        mock_signals.who.emit.reset_mock()

        # Member changed guilds
        config.LAST_WHO_SNAPSHOT = {
            'Jim': models.Player('Jim', None, None, 'Guild')}
        line = '[Sun Aug 16 22:46:32 2020] [ANONYMOUS] Jim (Gnome) <Other>'
        match = config.MATCH_WHO.match(line)
        message_handlers.handle_who(match)
        self.assertEqual(1, len(config.LAST_WHO_SNAPSHOT))
        self.assertEqual('Other', config.LAST_WHO_SNAPSHOT['Jim'].guild)
        mock_signals.who.emit.assert_called_once()
        mock_signals.who.emit.reset_mock()

        # Member left their guild
        config.LAST_WHO_SNAPSHOT = {
            'Jim': models.Player('Jim', None, None, 'Guild')}
        line = '[Sun Aug 16 22:46:32 2020] [50 Cleric] Jim (Gnome)'
        match = config.MATCH_WHO.match(line)
        message_handlers.handle_who(match)
        self.assertEqual(1, len(config.LAST_WHO_SNAPSHOT))
        self.assertIsNone(config.LAST_WHO_SNAPSHOT['Jim'].guild)
        mock_signals.who.emit.assert_called_once()
        mock_signals.who.emit.reset_mock()

    @mock.patch('ninjalooter.message_handlers.signals')
    def test_handle_end_who(self, mock_signals):
        config.LAST_WHO_SNAPSHOT = {
            'Jim': models.Player('Jim', None, None, None)}
        config.PLAYER_DB = {
            'Jim': models.Player('Jim', "Wizard", 60, 'Guild')}
        line = '[Sun Aug 16 22:46:32 2020] There is 1 player in Oggok.'
        match = config.MATCH_END_WHO.match(line)

        # REMEMBER_PLAYER_DATA: False
        # Player data should simply be copied from the /who entry
        config.ATTENDANCE_LOGS.clear()
        config.REMEMBER_PLAYER_DATA = False
        config.DEFAULT_ALLIANCE = "VCR"

        message_handlers.handle_end_who(match, skip_store=True)
        self.assertIsNone(config.ATTENDANCE_LOGS[0].log['Jim'].guild)

        # REMEMBER_PLAYER_DATA: True
        # Player lookup should get data from playerDB
        config.ATTENDANCE_LOGS.clear()
        config.REMEMBER_PLAYER_DATA = True

        message_handlers.handle_end_who(match, skip_store=True)
        self.assertEqual('Guild', config.ATTENDANCE_LOGS[0].log['Jim'].guild)

    @mock.patch('ninjalooter.config.AUDIO_ALERTS', True)
    @mock.patch('ninjalooter.utils.store_state')
    @mock.patch('ninjalooter.message_handlers.signals')
    def test_handle_drop(self, mock_signals, mock_store_state):
        config.PLAYER_DB = {
            'Jim': models.Player('Jim', None, None, 'Force of Will'),
            'James': models.Player('James', None, None, 'Kingdom'),
            'Dan': models.Player('Dan', None, None, 'Dial a Daniel'),
        }
        config.PENDING_AUCTIONS = list()
        config.ACTIVE_AUCTIONS = {}

        # NODROP filter on, droppable item
        config.NODROP_ONLY = True
        line = ("[Sun Aug 16 22:47:31 2020] Jim says out of character, "
                "'Copper Disc'")
        jim_disc_1_uuid = "jim_disc_1_uuid"
        jim_disc_1 = models.ItemDrop(
            'Copper Disc', 'Jim', 'Sun Aug 16 22:47:31 2020',
            uuid=jim_disc_1_uuid)
        match = config.MATCH_DROP_OOC.match(line)
        items = list(message_handlers.handle_drop(match))
        self.assertEqual(1, len(items))
        self.assertIn('Copper Disc', items)
        self.assertEqual(0, len(config.PENDING_AUCTIONS))
        mock_signals.drop.emit.assert_not_called()
        mock_signals.drop.emit.reset_mock()
        self.mock_playsound.assert_not_called()
        self.mock_playsound.reset_mock()

        # NODROP filter on, NODROP item
        line = ("[Sun Aug 16 22:47:31 2020] Jim says, "
                "'Belt of Iniquity'")
        jim_belt_1_uuid = "jim_belt_1_uuid"
        jim_belt_1 = models.ItemDrop(
            'Belt of Iniquity', 'Jim', 'Sun Aug 16 22:47:31 2020',
            uuid=jim_belt_1_uuid)
        match = config.MATCH_DROP_SAY.match(line)
        with mock.patch('uuid.uuid4') as mock_uuid4:
            mock_uuid4.return_value = jim_belt_1_uuid
            items = list(message_handlers.handle_drop(match))
        self.assertEqual(1, len(items))
        self.assertIn('Belt of Iniquity', items)
        self.assertEqual(1, len(config.PENDING_AUCTIONS))
        self.assertListEqual(
            [jim_belt_1],
            config.PENDING_AUCTIONS)
        mock_signals.drop.emit.assert_called_once()
        mock_signals.drop.emit.reset_mock()
        self.mock_playsound.assert_called_once()
        self.mock_playsound.reset_mock()

        # NODROP filter off, droppable item
        config.NODROP_ONLY = False
        line = ("[Sun Aug 16 22:47:31 2020] Jim tells the guild, "
                "'Copper Disc'")
        match = config.MATCH_DROP_GU.match(line)
        with mock.patch('uuid.uuid4') as mock_uuid4:
            mock_uuid4.return_value = jim_disc_1_uuid
            items = list(message_handlers.handle_drop(match))
        self.assertEqual(1, len(items))
        self.assertIn('Copper Disc', items)
        self.assertEqual(2, len(config.PENDING_AUCTIONS))
        self.assertListEqual(
            [jim_belt_1, jim_disc_1],
            config.PENDING_AUCTIONS)
        mock_signals.drop.emit.assert_called_once()
        mock_signals.drop.emit.reset_mock()
        self.mock_playsound.assert_called_once()
        self.mock_playsound.reset_mock()

        # Two items linked by a federation guild member, plus chat
        line = ("[Sun Aug 16 22:47:41 2020] James tells the guild, "
                "'Platinum Disc and Golden Amber Earring woo'")
        james_disc_uuid = "james_disc_uuid"
        james_earring_uuid = "james_earring_uuid"
        james_disc = models.ItemDrop(
            'Platinum Disc', 'James', 'Sun Aug 16 22:47:41 2020',
            uuid=james_disc_uuid)
        james_earring = models.ItemDrop(
            'Golden Amber Earring', 'James', 'Sun Aug 16 22:47:41 2020',
            uuid=james_earring_uuid)
        match = config.MATCH_DROP_GU.match(line)
        with mock.patch('uuid.uuid4') as mock_uuid4:
            mock_uuid4.side_effect = [james_disc_uuid, james_earring_uuid]
            items = list(message_handlers.handle_drop(match))
        self.assertEqual(2, len(items))
        self.assertListEqual(
            ['Platinum Disc', 'Golden Amber Earring'], items)
        self.assertListEqual(
            [jim_belt_1, jim_disc_1, james_disc, james_earring],
            config.PENDING_AUCTIONS)
        mock_signals.drop.emit.assert_called_once()
        mock_signals.drop.emit.reset_mock()
        self.mock_playsound.assert_called_once()
        self.mock_playsound.reset_mock()

        # Random chatter by federation guild member
        line = ("[Sun Aug 16 22:47:31 2020] Jim tells the guild, "
                "'four score and seven years ago, we wanted pixels'")
        match = config.MATCH_DROP_GU.match(line)
        items = list(message_handlers.handle_drop(match))
        self.assertEqual(0, len(items))
        self.assertListEqual(
            [jim_belt_1, jim_disc_1, james_disc, james_earring],
            config.PENDING_AUCTIONS)
        mock_signals.drop.emit.assert_not_called()
        self.mock_playsound.assert_not_called()

        # Someone reports they looted an item
        line = ("[Sun Aug 16 22:47:31 2020] Jim tells the guild, "
                "'looted Belt of Iniquity'")
        match = config.MATCH_DROP_GU.match(line)
        items = list(message_handlers.handle_drop(match))
        self.assertEqual(0, len(items))
        self.assertListEqual(
            [jim_belt_1, jim_disc_1, james_disc, james_earring],
            config.PENDING_AUCTIONS)
        mock_signals.drop.emit.assert_not_called()
        self.mock_playsound.assert_not_called()

        # Bid message doesn't register as a drop
        config.ACTIVE_AUCTIONS.clear()
        jerkin_1 = models.ItemDrop(
            'Shiverback-hide Jerkin', 'Jim', 'Sun Aug 16 22:47:31 2020')
        config.PENDING_AUCTIONS.append(jerkin_1)
        auction1 = utils.start_auction_dkp(jerkin_1, 'VCR')
        self.assertEqual(
            config.ACTIVE_AUCTIONS.get(auction1.item.uuid), auction1)
        config.PENDING_AUCTIONS.clear()
        line = ("[Sun Aug 16 22:47:31 2020] Jim tells the guild, "
                "'Shiverback-hide Jerkin'")
        match = config.MATCH_DROP_GU.match(line)
        items = list(message_handlers.handle_drop(match))
        # One item should be found
        self.assertListEqual(['Shiverback-hide Jerkin'], items)
        self.assertListEqual([], config.PENDING_AUCTIONS)
        mock_signals.drop.emit.assert_not_called()
        self.mock_playsound.assert_not_called()

        # A gratss message from another app should not register as a drop
        bid_line = ("[Sun Aug 16 22:47:31 2020] Toald tells the guild, "
                    "'Shiverback-hide Jerkin 1 main'")
        config.RESTRICT_BIDS = False
        bid_match = config.MATCH_BID_GU.match(bid_line)
        message_handlers.handle_bid(bid_match)
        config.HISTORICAL_AUCTIONS[auction1.item.uuid] = (
            config.ACTIVE_AUCTIONS.pop(auction1.item.uuid))
        line = ("[Sun Aug 16 22:47:31 2020] Jim tells the guild, "
                "'~Gratss Toald on [Shiverback-hide Jerkin] (1 DKP)!'")
        match = config.MATCH_DROP_GU.match(line)
        items = list(message_handlers.handle_drop(match))
        self.assertListEqual([], items)

        # Ignore items if a number is present, it's probably a bid
        match = config.MATCH_DROP_GU.match(bid_line)
        items = list(message_handlers.handle_drop(match))
        self.assertListEqual([], items)

        # second same drop shouldn't record if it is within cooldown time
        jerkin_2 = models.ItemDrop(
            'Shiverback-hide Jerkin', 'Jim',
            utils.datetime_to_eq_format(datetime.datetime.now()))
        config.PENDING_AUCTIONS.append(jerkin_2)
        line = ("[{}] Jim tells the guild, 'Shiverback-hide Jerkin'".format(
            utils.datetime_to_eq_format(datetime.datetime.now())))
        match = config.MATCH_DROP_GU.match(line)
        self.assertEqual([jerkin_2], config.PENDING_AUCTIONS)
        items = list(message_handlers.handle_drop(match))
        self.assertListEqual([jerkin_2.name], items)
        self.assertEqual([jerkin_2], config.PENDING_AUCTIONS)

        # second same drop should record if it is past cooldown time
        jerkin_2.timestamp = utils.datetime_to_eq_format(
            datetime.datetime.now() -
            datetime.timedelta(seconds=config.DROP_COOLDOWN))
        self.assertEqual(1, len(config.PENDING_AUCTIONS))
        items = list(message_handlers.handle_drop(match))
        self.assertListEqual([jerkin_2.name], items)
        self.assertEqual(2, len(config.PENDING_AUCTIONS))
        mock_signals.drop.emit.reset_mock()
        self.mock_playsound.reset_mock()

        # Teir'dal Sai (testing apostrophes)
        # NODROP filter off, droppable item
        config.NODROP_ONLY = False
        config.PENDING_AUCTIONS.clear()
        line = ("[Sun Aug 16 22:47:31 2020] Jim tells the guild, "
                "'Teir'dal Sai'")
        jim_sai_1_uuid = "jim_sai_1_uuid"
        jim_sai_1 = models.ItemDrop(
            "Teir'dal Sai", 'Jim', 'Sun Aug 16 22:47:31 2020',
            uuid=jim_sai_1_uuid)
        match = config.MATCH_DROP_GU.match(line)
        with mock.patch('uuid.uuid4') as mock_uuid4:
            mock_uuid4.return_value = jim_sai_1_uuid
            items = list(message_handlers.handle_drop(match))
        self.assertEqual(1, len(items))
        self.assertIn("Teir'dal Sai", items)
        self.assertEqual(1, len(config.PENDING_AUCTIONS))
        self.assertListEqual(
            [jim_sai_1],
            config.PENDING_AUCTIONS)
        mock_signals.drop.emit.assert_called_once()
        mock_signals.drop.emit.reset_mock()
        self.mock_playsound.assert_called_once()
        self.mock_playsound.reset_mock()

    @mock.patch('ninjalooter.config.AUDIO_ALERTS', True)
    @mock.patch('ninjalooter.utils.store_state')
    @mock.patch('ninjalooter.message_handlers.signals')
    def test_handle_drops_all_matchers(self, mock_signals, mock_store_state):
        # Check SAY
        line = ("[Sun Aug 16 22:47:31 2020] Jim says, "
                "'Belt of Iniquity'")
        match = config.MATCH_DROP_SAY.match(line)
        items = list(message_handlers.handle_drop(match))
        self.assertEqual(['Belt of Iniquity'], items)

        # Check OOC
        line = ("[Sun Aug 16 22:47:31 2020] Jim says out of character, "
                "'Belt of Iniquity'")
        match = config.MATCH_DROP_OOC.match(line)
        items = list(message_handlers.handle_drop(match))
        self.assertEqual(['Belt of Iniquity'], items)

        # Check AUC
        line = ("[Sun Aug 16 22:47:31 2020] Jim auctions, "
                "'Belt of Iniquity'")
        match = config.MATCH_DROP_AUC.match(line)
        items = list(message_handlers.handle_drop(match))
        self.assertEqual(['Belt of Iniquity'], items)

        # Check SHOUT
        line = ("[Sun Aug 16 22:47:31 2020] Jim shouts, "
                "'Belt of Iniquity'")
        match = config.MATCH_DROP_SHOUT.match(line)
        items = list(message_handlers.handle_drop(match))
        self.assertEqual(['Belt of Iniquity'], items)

        # Check GU
        line = ("[Sun Aug 16 22:47:31 2020] Jim tells the guild, "
                "'Belt of Iniquity'")
        match = config.MATCH_DROP_GU.match(line)
        items = list(message_handlers.handle_drop(match))
        self.assertEqual(['Belt of Iniquity'], items)

    @mock.patch('ninjalooter.config.AUDIO_ALERTS', True)
    @mock.patch('ninjalooter.utils.store_state')
    @mock.patch('ninjalooter.message_handlers.signals')
    def test_handle_drop_alert(self, mock_signals, mock_store_state):
        config.PENDING_AUCTIONS = list()
        config.NODROP_ONLY = False

        copper_disc_uuid = "1"
        platinum_disc_uuid = "2"
        jade_reaver_uuid = "3"
        line = ("[Sun Aug 16 22:47:31 2020] Jim tells the guild, "
                "'Copper Disc Platinum Disc Jade Reaver'")
        match = config.MATCH_DROP_GU.match(line)
        with mock.patch('uuid.uuid4') as mock_uuid4:
            mock_uuid4.return_value = [
                copper_disc_uuid, platinum_disc_uuid, jade_reaver_uuid]
            items = list(message_handlers.handle_drop(match))
        self.assertEqual(3, len(items))
        self.assertIn('Copper Disc', items)
        self.assertIn('Platinum Disc', items)
        self.assertIn('Jade Reaver', items)
        mock_signals.drop.emit.assert_called_once()
        mock_signals.drop.emit.reset_mock()
        self.mock_playsound.assert_called_once()
        self.mock_playsound.reset_mock()

    @mock.patch('ninjalooter.utils.store_state')
    @mock.patch('ninjalooter.message_handlers.signals')
    def test_handle_bid(self, mock_signals, mock_store_state):
        config.PLAYER_DB = {
            'Jim': models.Player('Jim', None, None, 'Venerate'),
            'Pim': models.Player('Pim', None, None, 'Castle'),
            'Tim': models.Player('Tim', None, None, 'Kingdom'),
            'Dan': models.Player('Dan', None, None, 'Dial a Daniel'),
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
        match = config.MATCH_BID[1].match(line)
        result = message_handlers.handle_bid(match)
        self.assertFalse(result)
        self.assertListEqual([], disc_auction.highest())
        self.assertEqual(1, len(config.ACTIVE_AUCTIONS))
        mock_signals.bid.emit.assert_not_called()

        # FILTER ON - Someone outside the alliance bids on an active item
        line = ("[Sun Aug 16 22:47:31 2020] Dan auctions, "
                "'Copper Disc 10 DKP'")
        match = config.MATCH_BID[1].match(line)
        result = message_handlers.handle_bid(match)
        self.assertFalse(result)
        self.assertEqual([], disc_auction.highest())
        mock_signals.bid.emit.assert_not_called()

        # FILTER OFF - Someone in the alliance bids on an inactive item
        config.RESTRICT_BIDS = False
        line = ("[Sun Aug 16 22:47:31 2020] Jim auctions, "
                "'Platinum Disc 10 DKP'")
        match = config.MATCH_BID[1].match(line)
        result = message_handlers.handle_bid(match)
        self.assertFalse(result)
        self.assertListEqual([], disc_auction.highest())
        self.assertEqual(1, len(config.ACTIVE_AUCTIONS))
        mock_signals.bid.emit.assert_not_called()

        # FILTER ON - Someone outside the alliance bids on an active item
        config.RESTRICT_BIDS = True
        line = ("[Sun Aug 16 22:47:31 2020] Dan auctions, "
                "'Copper Disc 10 DKP'")
        match = config.MATCH_BID[1].match(line)
        result = message_handlers.handle_bid(match)
        self.assertFalse(result)
        self.assertEqual([], disc_auction.highest())
        mock_signals.bid.emit.assert_not_called()

        # Someone in the alliance says random stuff with a number
        line = ("[Sun Aug 16 22:47:31 2020] Tim auctions, "
                "'I am 12 and what channel is this'")
        match = config.MATCH_BID[1].match(line)
        result = message_handlers.handle_bid(match)
        self.assertFalse(result)
        self.assertListEqual([], disc_auction.highest())
        mock_signals.bid.emit.assert_not_called()

        # Someone in the alliance bids on two items at once
        line = ("[Sun Aug 16 22:47:31 2020] Jim auctions, "
                "'Copper Disc 10 DKP Platinum Disc'")
        match = config.MATCH_BID[1].match(line)
        result = message_handlers.handle_bid(match)
        self.assertFalse(result)
        self.assertListEqual([], disc_auction.highest())
        mock_signals.bid.emit.assert_not_called()

        # Someone we haven't seen bids on an active item
        line = ("[Sun Aug 16 22:47:31 2020] Paul auctions, "
                "'Copper Disc 5 DKP'")
        match = config.MATCH_BID[1].match(line)
        result = message_handlers.handle_bid(match)
        self.assertTrue(result)
        self.assertListEqual([('Paul', 5)], disc_auction.highest())
        mock_signals.bid.emit.assert_called_once()
        mock_signals.bid.emit.reset_mock()

        # Someone in the alliance bids on an active item
        line = ("[Sun Aug 16 22:47:31 2020] Jim auctions, "
                "'Copper Disc 10 DKP'")
        match = config.MATCH_BID[1].match(line)
        result = message_handlers.handle_bid(match)
        self.assertTrue(result)
        self.assertIn(('Jim', 10), disc_auction.highest())
        mock_signals.bid.emit.assert_called_once()
        mock_signals.bid.emit.reset_mock()

        # Someone in the alliance bids on an active item with wrong case
        line = ("[Sun Aug 16 22:47:31 2020] Pim auctions, "
                "'copper DISC 11 DKP'")
        match = config.MATCH_BID[1].match(line)
        result = message_handlers.handle_bid(match)
        self.assertTrue(result)
        self.assertIn(('Pim', 11), disc_auction.highest())
        mock_signals.bid.emit.assert_called_once()
        mock_signals.bid.emit.reset_mock()

        # Someone in the alliance bids on an active item for their 2nd main
        line = ("[Sun Aug 16 22:47:31 2020] Jim auctions, "
                "'Copper Disc 2nd main 12dkp'")
        match = config.MATCH_BID[1].match(line)
        result = message_handlers.handle_bid(match)
        self.assertTrue(result)
        self.assertIn(('Jim', 12), disc_auction.highest())
        mock_signals.bid.emit.assert_called_once()
        mock_signals.bid.emit.reset_mock()

        # Someone in the alliance avoids bidding using ~
        line = ("[Sun Aug 16 22:47:31 2020] Jim auctions, "
                "'~Copper Disc 14 DKP'")
        match = config.MATCH_BID[1].match(line)
        result = message_handlers.handle_bid(match)
        self.assertFalse(result)
        self.assertListEqual([('Jim', 12)], disc_auction.highest())
        mock_signals.bid.emit.assert_not_called()

        # Someone in the alliance bids on an active item via tell (windows off)
        line = "[Sun Aug 16 22:47:31 2020] Jim tells you, 'Copper Disc 15 DKP'"
        match = config.MATCH_BID_TELL.match(line)
        result = message_handlers.handle_bid(match)
        self.assertTrue(result)
        self.assertIn(('Jim', 15), disc_auction.highest())
        mock_signals.bid.emit.assert_called_once()
        mock_signals.bid.emit.reset_mock()

        # Someone in the alliance bids on an active item via tell (windows on)
        line = "[Sun Aug 16 22:47:31 2020] Jim -> You: Copper Disc 16 DKP"
        match = config.MATCH_BID_TELL.match(line)
        result = message_handlers.handle_bid(match)
        self.assertTrue(result)
        self.assertIn(('Jim', 16), disc_auction.highest())
        mock_signals.bid.emit.assert_called_once()
        mock_signals.bid.emit.reset_mock()

        config.ACTIVE_AUCTIONS.clear()

    @mock.patch('ninjalooter.utils.store_state')
    @mock.patch('ninjalooter.message_handlers.signals')
    def test_handle_bid_all_matchers(self, mock_signals, mock_store_state):
        item_name = 'Copper Disc'
        itemdrop = models.ItemDrop(item_name, "Jim", "timestamp")
        disc_auction = models.DKPAuction(itemdrop, 'VCR')
        config.ACTIVE_AUCTIONS = {
            itemdrop.uuid: disc_auction
        }

        # Check SAY
        line = ("[Sun Aug 16 22:47:31 2020] Jim says, "
                "'Copper Disc 10 DKP'")
        match = config.MATCH_BID_SAY.match(line)
        result = message_handlers.handle_bid(match)
        self.assertTrue(result)

        # Check OOC
        line = ("[Sun Aug 16 22:47:31 2020] Jim says out of character, "
                "'Copper Disc 11 DKP'")
        match = config.MATCH_BID_OOC.match(line)
        result = message_handlers.handle_bid(match)
        self.assertTrue(result)

        # Check AUC
        line = ("[Sun Aug 16 22:47:31 2020] Jim auctions, "
                "'Copper Disc 12 DKP'")
        match = config.MATCH_BID_AUC.match(line)
        result = message_handlers.handle_bid(match)
        self.assertTrue(result)

        # Check SHOUT
        line = ("[Sun Aug 16 22:47:31 2020] Jim shouts, "
                "'Copper Disc 13 DKP'")
        match = config.MATCH_BID_SHOUT.match(line)
        result = message_handlers.handle_bid(match)
        self.assertTrue(result)

        # Check GU
        line = ("[Sun Aug 16 22:47:31 2020] Jim tells the guild, "
                "'Copper Disc 14 DKP'")
        match = config.MATCH_BID_GU.match(line)
        result = message_handlers.handle_bid(match)
        self.assertTrue(result)

        config.ACTIVE_AUCTIONS.clear()

    @mock.patch('ninjalooter.utils.store_state')
    @mock.patch('ninjalooter.message_handlers.signals')
    def test_handle_bid_restricts_via_player_db_without_snapshot(
            self, mock_signals, mock_store_state):
        config.LAST_WHO_SNAPSHOT = {}
        config.PLAYER_DB = {
            'Dan': models.Player('Dan', None, None, 'Dial a Daniel'),
        }
        config.RESTRICT_BIDS = True
        item_name = 'Copper Disc'
        itemdrop = models.ItemDrop(item_name, "Jim", "timestamp")
        disc_auction = models.DKPAuction(itemdrop, 'VCR')
        config.ACTIVE_AUCTIONS = {itemdrop.uuid: disc_auction}

        line = ("[Sun Aug 16 22:47:31 2020] Dan auctions, "
                "'Copper Disc 10 DKP'")
        match = config.MATCH_BID[1].match(line)
        result = message_handlers.handle_bid(match)
        self.assertFalse(result)
        self.assertEqual([], disc_auction.highest())
        mock_signals.bid.emit.assert_not_called()

        config.ACTIVE_AUCTIONS.clear()

    @mock.patch('ninjalooter.utils.store_state')
    @mock.patch('ninjalooter.message_handlers.signals')
    def test_handle_bid_proxy(self, mock_signals, mock_store_state):
        config.PLAYER_DB = {
            'Jim': models.Player('Jim', None, None, 'Venerate'),
            'Pim': models.Player('Pim', None, None, 'Castle'),
            'Tim': models.Player('Tim', None, None, 'Kingdom'),
            'Otherchar': models.Player('Otherchar', None, None, 'Venerate'),
        }
        config.LAST_WHO_SNAPSHOT = {
            'Jim': models.Player('Jim', None, None, 'Venerate'),
        }
        config.RESTRICT_BIDS = False
        item_name = 'Copper Disc'
        itemdrop = models.ItemDrop(item_name, "Jim", "timestamp")
        disc_auction = models.DKPAuction(itemdrop, 'VCR')
        config.ACTIVE_AUCTIONS = {
            itemdrop.uuid: disc_auction
        }

        # Proxy bid: known player name after the bid number
        line = ("[Sun Aug 16 22:47:31 2020] Jim auctions, "
                "'Copper Disc 10 Otherchar'")
        match = config.MATCH_BID_AUC.match(line)
        result = message_handlers.handle_bid(match)
        self.assertTrue(result)
        self.assertIn(('Otherchar', 10), disc_auction.highest())
        mock_signals.bid.emit.assert_called_once()
        mock_signals.bid.emit.reset_mock()

        # Proxy bid: known player name before the item
        line = ("[Sun Aug 16 22:47:31 2020] Jim auctions, "
                "'Pim Copper Disc 11'")
        match = config.MATCH_BID_AUC.match(line)
        result = message_handlers.handle_bid(match)
        self.assertTrue(result)
        self.assertIn(('Pim', 11), disc_auction.highest())
        mock_signals.bid.emit.assert_called_once()
        mock_signals.bid.emit.reset_mock()

        # Proxy bid: known player name with DKP noise word
        line = ("[Sun Aug 16 22:47:31 2020] Jim auctions, "
                "'Copper Disc 12 DKP Tim'")
        match = config.MATCH_BID_AUC.match(line)
        result = message_handlers.handle_bid(match)
        self.assertTrue(result)
        self.assertIn(('Tim', 12), disc_auction.highest())
        mock_signals.bid.emit.assert_called_once()
        mock_signals.bid.emit.reset_mock()

        # No proxy: unknown word is not treated as a player
        line = ("[Sun Aug 16 22:47:31 2020] Jim auctions, "
                "'Copper Disc 13 DKP'")
        match = config.MATCH_BID_AUC.match(line)
        result = message_handlers.handle_bid(match)
        self.assertTrue(result)
        self.assertIn(('Jim', 13), disc_auction.highest())
        mock_signals.bid.emit.assert_called_once()
        mock_signals.bid.emit.reset_mock()

        # No proxy: sender's own name in text is not treated as proxy
        line = ("[Sun Aug 16 22:47:31 2020] Jim auctions, "
                "'Copper Disc 14 Jim'")
        match = config.MATCH_BID_AUC.match(line)
        result = message_handlers.handle_bid(match)
        self.assertTrue(result)
        self.assertIn(('Jim', 14), disc_auction.highest())
        mock_signals.bid.emit.assert_called_once()
        mock_signals.bid.emit.reset_mock()

        config.ACTIVE_AUCTIONS.clear()

    @mock.patch('ninjalooter.utils.store_state')
    @mock.patch('ninjalooter.message_handlers.signals')
    def test_handle_gratss(self, mock_signals, mock_store_state):
        config.PENDING_AUCTIONS.clear()
        config.ACTIVE_AUCTIONS.clear()

        # Set up a historical auction with bids
        jerkin_1 = models.ItemDrop(
            'Shiverback-hide Jerkin', 'Jim', 'Sun Aug 16 22:47:31 2020')
        config.PENDING_AUCTIONS.append(jerkin_1)
        auction1 = utils.start_auction_dkp(jerkin_1, 'VCR')
        self.assertEqual(
            config.ACTIVE_AUCTIONS.get(auction1.item.uuid), auction1)
        bid_line = ("[Sun Aug 16 22:47:31 2020] Toald tells the guild, "
                    "'Shiverback-hide Jerkin 1 main'")
        config.RESTRICT_BIDS = False
        bid_match = config.MATCH_BID_GU.match(bid_line)
        message_handlers.handle_bid(bid_match)
        config.HISTORICAL_AUCTIONS[auction1.item.uuid] = (
            config.ACTIVE_AUCTIONS.pop(auction1.item.uuid))

        # Set up a historical auction without bids (rot)
        disc_1 = models.ItemDrop(
            'Copper Disc', 'Jim', 'Sun Aug 16 22:47:31 2020')
        config.PENDING_AUCTIONS.append(disc_1)
        auction2 = utils.start_auction_dkp(disc_1, 'VCR')
        self.assertEqual(
            config.ACTIVE_AUCTIONS.get(auction2.item.uuid), auction2)
        config.HISTORICAL_AUCTIONS[auction2.item.uuid] = (
            config.ACTIVE_AUCTIONS.pop(auction2.item.uuid))

        # A gratss message from auction history should not register (bids)
        line = ("[Sun Aug 16 22:47:31 2020] Jim tells the guild, "
                "'~Gratss Toald on [Shiverback-hide Jerkin] (1 DKP)!'")
        match = config.MATCH_GRATSS.match(line)
        self.assertFalse(message_handlers.handle_gratss(match))

        # A gratss message from auction history should not register (no bids)
        line = ("[Sun Aug 16 22:47:31 2020] Jim tells the guild, "
                "'~Gratss ROT on [Copper Disc] (0 DKP)!'")
        match = config.MATCH_GRATSS.match(line)
        self.assertFalse(message_handlers.handle_gratss(match))

        # A gratss message that doesn't match auction history SHOULD register
        line = ("[Sun Aug 16 22:47:31 2020] Jim tells the guild, "
                "'~Gratss Jim on [Bladestopper] (100 DKP)!'")
        match = config.MATCH_GRATSS.match(line)
        self.assertTrue(message_handlers.handle_gratss(match))

        # A gratss message direct to /tell should register (no tell windows)
        line = ("[Sun Aug 16 22:47:31 2020] Jim tells you, "
                "'~Gratss Jim on [Bladestopper] (100 DKP)!'")
        match = config.MATCH_GRATSS.match(line)
        self.assertTrue(message_handlers.handle_gratss(match))

        # A gratss message direct to /tell should register (tell windows)
        line = ("[Sun Aug 16 22:47:31 2020] Jim -> You, "
                "'~Gratss Jim on [Bladestopper] (100 DKP)!'")
        match = config.MATCH_GRATSS.match(line)
        self.assertTrue(message_handlers.handle_gratss(match))

    @mock.patch('ninjalooter.utils.store_state')
    @mock.patch('ninjalooter.message_handlers.signals')
    def test_handle_creditt(self, mock_signals, mock_store_state):
        config.PLAYER_NAME = "PlayerName"
        # A creditt message direct to /tell should register (no tell windows)
        line = ("[Sun Aug 16 22:47:31 2020] Jim tells you, "
                "'Creditt Bill'")
        match = config.MATCH_CREDITT.match(line)
        self.assertTrue(message_handlers.handle_creditt(match))

        # A creditt message direct to /tell should register (tell windows)
        line = ("[Sun Aug 16 22:47:31 2020] Jim -> PlayerName: "
                "Creditt Tony")
        match = config.MATCH_CREDITT.match(line)
        self.assertTrue(message_handlers.handle_creditt(match))

        config.PLAYER_NAME = ""

    @mock.patch('ninjalooter.message_handlers.signals')
    def test_handle_raidtick(self, mock_signals):
        old_raidtick = config.LAST_RAIDTICK
        line = "[Sun Aug 16 22:47:31 2020] Jim tells the guild, 'RAIDTICK'"
        match = config.MATCH_RAIDTICK.match(line)
        self.assertIsNotNone(match)
        result = message_handlers.handle_raidtick(match)
        self.assertTrue(result)
        self.assertEqual(
            dateutil.parser.parse("Sun Aug 16 22:47:31 2020"),
            config.LAST_RAIDTICK)
        self.assertNotEqual(old_raidtick, config.LAST_RAIDTICK)

    @mock.patch('ninjalooter.utils.store_state')
    @mock.patch('ninjalooter.message_handlers.signals')
    def test_handle_kill(self, mock_signals, mock_store_state):
        line = "[Sun Aug 16 17:41:25 2020] an azarack has been slain by Peter!"
        match = config.MATCH_KILL.match(line)
        self.assertIsNotNone(match)
        result = message_handlers.handle_kill(match)
        self.assertTrue(result)
        self.assertEqual(1, len(config.KILL_TIMERS))
        self.assertEqual("an azarack", config.KILL_TIMERS[0].name)
        mock_signals.kill.emit.assert_called_once()

    @mock.patch('ninjalooter.utils.store_state')
    @mock.patch('ninjalooter.message_handlers.signals')
    def test_handle_kill_stamps_zone(self, mock_signals, mock_store_state):
        config.CURRENT_ZONE = "Plane of Sky"
        line = "[Sun Aug 16 17:41:25 2020] an azarack has been slain by Peter!"
        match = config.MATCH_KILL.match(line)
        message_handlers.handle_kill(match)
        self.assertEqual("Plane of Sky", config.KILL_TIMERS[0].zone)

    @mock.patch('ninjalooter.utils.store_state')
    @mock.patch('ninjalooter.message_handlers.signals')
    def test_handle_kill_no_zone(self, mock_signals, mock_store_state):
        line = "[Sun Aug 16 17:41:25 2020] an azarack has been slain by Peter!"
        match = config.MATCH_KILL.match(line)
        message_handlers.handle_kill(match)
        self.assertIsNone(config.KILL_TIMERS[0].zone)

    @mock.patch('ninjalooter.utils.store_state')
    @mock.patch('ninjalooter.message_handlers.signals')
    def test_handle_kill_ignores_player_death(self, mock_signals, mock_store_state):
        config.PLAYER_DB["Peter"] = models.Player("Peter", "Warrior", 60, "Castle")
        line = "[Sun Aug 16 17:41:25 2020] Peter has been slain by an azarack!"
        match = config.MATCH_KILL.match(line)
        result = message_handlers.handle_kill(match)
        self.assertFalse(result)
        self.assertEqual(0, len(config.KILL_TIMERS))
        mock_signals.kill.emit.assert_not_called()

    @mock.patch('ninjalooter.utils.store_state')
    @mock.patch('ninjalooter.message_handlers.signals')
    def test_handle_kill_ignores_who_snapshot_player(self, mock_signals, mock_store_state):
        config.LAST_WHO_SNAPSHOT["Jim"] = models.Player("Jim", "Cleric", 60, "Castle")
        line = "[Sun Aug 16 17:41:25 2020] Jim has been slain by a gnoll!"
        match = config.MATCH_KILL.match(line)
        result = message_handlers.handle_kill(match)
        self.assertFalse(result)
        self.assertEqual(0, len(config.KILL_TIMERS))

    def test_handle_zone_change(self):
        line = "[Sun Aug 16 17:40:00 2020] You have entered Plane of Sky."
        match = config.MATCH_ZONE_CHANGE.match(line)
        self.assertIsNotNone(match)
        result = message_handlers.handle_zone_change(match)
        self.assertTrue(result)
        self.assertEqual("Plane of Sky", config.CURRENT_ZONE)

    def test_handle_zone_change_different_zone(self):
        line = "[Sun Aug 16 17:40:00 2020] You have entered West Commonlands."
        match = config.MATCH_ZONE_CHANGE.match(line)
        self.assertIsNotNone(match)
        message_handlers.handle_zone_change(match)
        self.assertEqual("West Commonlands", config.CURRENT_ZONE)

    @mock.patch('ninjalooter.utils.store_state')
    @mock.patch('ninjalooter.message_handlers.signals')
    def test_handle_end_who_sets_current_zone(self, mock_signals, mock_store_state):
        config.LAST_WHO_SNAPSHOT.clear()
        line = "[Sun Aug 16 22:46:32 2020] There are 25 players in Plane of Sky."
        match = config.MATCH_END_WHO.match(line)
        self.assertIsNotNone(match)
        message_handlers.handle_end_who(match)
        self.assertEqual("Plane of Sky", config.CURRENT_ZONE)

    @mock.patch('ninjalooter.utils.store_state')
    @mock.patch('ninjalooter.message_handlers.signals')
    def test_handle_end_who_everquest_no_zone_update(self, mock_signals, mock_store_state):
        config.CURRENT_ZONE = "Plane of Sky"
        config.LAST_WHO_SNAPSHOT.clear()
        line = "[Sun Aug 16 22:46:32 2020] There are 25 players in EverQuest."
        match = config.MATCH_END_WHO.match(line)
        message_handlers.handle_end_who(match)
        self.assertEqual("Plane of Sky", config.CURRENT_ZONE)

    @mock.patch('ninjalooter.message_handlers.signals')
    def test_handle_rand1(self, mock_signals):
        line = "[Sun Aug 16 22:47:31 2020] **A Magic Die is rolled by Jim."
        match = config.MATCH_RAND1.match(line)
        self.assertIsNotNone(match)
        result = message_handlers.handle_rand1(match)
        self.assertEqual("Jim", result)

    @mock.patch('ninjalooter.utils.store_state')
    @mock.patch('ninjalooter.message_handlers.signals')
    def test_handle_rand2(self, mock_signals, mock_store_state):
        item_name = 'Copper Disc'
        itemdrop = models.ItemDrop(item_name, "Jim", "timestamp")
        config.PENDING_AUCTIONS.append(itemdrop)
        auc = utils.start_auction_random(itemdrop)
        target = auc.number

        # Valid roll matching active auction target
        line = (
            "[Sun Aug 16 22:47:31 2020] "
            "**It could have been any number from 0 to {to}, "
            "but this time it turned up a 42.Peter"
        ).format(to=target)
        match = config.MATCH_RAND2.match(line)
        self.assertIsNotNone(match)
        result = message_handlers.handle_rand2(match)
        self.assertTrue(result)
        self.assertListEqual([('Peter', 42)], auc.highest())
        mock_signals.bid.emit.assert_called_once()
        mock_signals.bid.emit.reset_mock()

        # Invalid roll: from != 0
        line = (
            "[Sun Aug 16 22:47:31 2020] "
            "**It could have been any number from 1 to {to}, "
            "but this time it turned up a 99.Paul"
        ).format(to=target)
        match = config.MATCH_RAND2.match(line)
        result = message_handlers.handle_rand2(match)
        self.assertFalse(result)
        mock_signals.bid.emit.assert_not_called()

        # Roll doesn't match any active auction target
        line = (
            "[Sun Aug 16 22:47:31 2020] "
            "**It could have been any number from 0 to 9999, "
            "but this time it turned up a 50.Mary"
        )
        match = config.MATCH_RAND2.match(line)
        result = message_handlers.handle_rand2(match)
        self.assertFalse(result)
        mock_signals.bid.emit.assert_not_called()

    @mock.patch('ninjalooter.utils.store_state')
    @mock.patch('ninjalooter.message_handlers.signals')
    def test_handle_auc_start_dkp(self, mock_signals, mock_store_state):
        item = models.ItemDrop(
            'Copper Disc', 'Jim', 'Sun Aug 16 22:47:31 2020')
        config.PENDING_AUCTIONS.append(item)
        config.ACTIVE_AUCTIONS.clear()
        config.HISTORICAL_AUCTIONS.clear()

        line = (
            "[Sun Aug 16 22:47:31 2020] Jim tells the guild, "
            "'[Copper Disc] (DRU, SHD) - BID IN /GU, MIN 1 DKP. "
            "You MUST include the item name in your bid! "
            "Closing in 2m31s.'"
        )
        match = logreplay.MATCH_START_AUCTION_DKP.match(line)
        self.assertIsNotNone(match)

        result = message_handlers.handle_auc_start(match)

        self.assertTrue(result)
        self.assertNotIn(item, config.PENDING_AUCTIONS)
        self.assertIn(item.uuid, config.ACTIVE_AUCTIONS)
        auc = config.ACTIVE_AUCTIONS[item.uuid]
        self.assertIsInstance(auc, models.DKPAuction)
        self.assertEqual(1, auc.item.min_dkp_override)
        mock_signals.auction_started.emit.assert_called_once()

    @mock.patch('ninjalooter.utils.store_state')
    @mock.patch('ninjalooter.message_handlers.signals')
    def test_handle_auc_start_random(self, mock_signals, mock_store_state):
        item = models.ItemDrop(
            'Copper Disc', 'Jim', 'Sun Aug 16 22:47:31 2020')
        config.PENDING_AUCTIONS.append(item)
        config.ACTIVE_AUCTIONS.clear()

        line = (
            "[Sun Aug 16 22:47:31 2020] Jim tells the guild, "
            "'[Copper Disc] (DRU, SHD) ROLL 1234 NOW!'"
        )
        match = logreplay.MATCH_START_AUCTION_RANDOM.match(line)
        self.assertIsNotNone(match)

        result = message_handlers.handle_auc_start(match)

        self.assertTrue(result)
        self.assertNotIn(item, config.PENDING_AUCTIONS)
        self.assertIn(item.uuid, config.ACTIVE_AUCTIONS)
        auc = config.ACTIVE_AUCTIONS[item.uuid]
        self.assertIsInstance(auc, models.RandomAuction)
        self.assertEqual(1234, auc.number)
        mock_signals.auction_started.emit.assert_called_once()

    @mock.patch('ninjalooter.utils.store_state')
    @mock.patch('ninjalooter.message_handlers.signals')
    def test_handle_auc_start_with_existing_bid(
            self, mock_signals, mock_store_state):
        item = models.ItemDrop(
            'Copper Disc', 'Jim', 'Sun Aug 16 22:47:31 2020')
        config.PENDING_AUCTIONS.append(item)
        config.ACTIVE_AUCTIONS.clear()
        config.HISTORICAL_AUCTIONS.clear()

        line = (
            "[Sun Aug 16 22:47:31 2020] Jim tells the guild, "
            "'[Copper Disc] (DRU, SHD) - BID IN /GU. "
            "You MUST include the item name in your bid! "
            "Currently: `Peter` with 10 DKP - Closing in 2m00s!'"
        )
        match = logreplay.MATCH_START_AUCTION_DKP.match(line)
        self.assertIsNotNone(match)

        result = message_handlers.handle_auc_start(match)

        self.assertTrue(result)
        auc = config.ACTIVE_AUCTIONS[item.uuid]
        self.assertIsInstance(auc, models.DKPAuction)
        self.assertEqual('Peter', auc.bids[10])

    @mock.patch('ninjalooter.utils.store_state')
    @mock.patch('ninjalooter.message_handlers.signals')
    def test_handle_auc_start_not_pending(
            self, mock_signals, mock_store_state):
        config.PENDING_AUCTIONS.clear()
        config.ACTIVE_AUCTIONS.clear()
        config.HISTORICAL_AUCTIONS.clear()

        line = (
            "[Sun Aug 16 22:47:31 2020] Jim tells the guild, "
            "'[Copper Disc] (DRU, SHD) - BID IN /GU, MIN 1 DKP. "
            "You MUST include the item name in your bid! "
            "Closing in 2m31s.'"
        )
        match = logreplay.MATCH_START_AUCTION_DKP.match(line)
        self.assertIsNotNone(match)

        result = message_handlers.handle_auc_start(match)

        self.assertFalse(result)
        self.assertEqual(0, len(config.ACTIVE_AUCTIONS))

    @mock.patch('ninjalooter.utils.store_state')
    @mock.patch('ninjalooter.message_handlers.signals')
    def test_handle_auc_start_already_active(
            self, mock_signals, mock_store_state):
        item = models.ItemDrop(
            'Copper Disc', 'Jim', 'Sun Aug 16 22:47:31 2020')
        config.PENDING_AUCTIONS.append(item)
        auc = utils.start_auction_dkp(item, 'VCR')
        self.assertIn(item.uuid, config.ACTIVE_AUCTIONS)
        config.HISTORICAL_AUCTIONS.clear()

        line = (
            "[Sun Aug 16 22:47:31 2020] Jim tells the guild, "
            "'[Copper Disc] (DRU, SHD) - BID IN /GU. "
            "You MUST include the item name in your bid! "
            "Currently: `Peter` with 10 DKP - Closing in 2m00s!'"
        )
        match = logreplay.MATCH_START_AUCTION_DKP.match(line)
        self.assertIsNotNone(match)

        result = message_handlers.handle_auc_start(match)

        self.assertFalse(result)
        self.assertEqual(auc, config.ACTIVE_AUCTIONS[item.uuid])

    @mock.patch('ninjalooter.utils.store_state')
    @mock.patch('ninjalooter.message_handlers.signals')
    def test_handle_auc_start_restart_historical(
            self, mock_signals, mock_store_state):
        item = models.ItemDrop(
            'Copper Disc', 'Jim', 'Sun Aug 16 22:47:31 2020')
        config.PENDING_AUCTIONS.append(item)
        auc = utils.start_auction_dkp(item, 'VCR')
        auc.add(10, 'Peter')
        config.HISTORICAL_AUCTIONS[item.uuid] = (
            config.ACTIVE_AUCTIONS.pop(item.uuid))
        self.assertEqual(0, len(config.ACTIVE_AUCTIONS))
        self.assertEqual(1, len(config.HISTORICAL_AUCTIONS))

        line = (
            "[Sun Aug 16 22:47:31 2020] Jim tells the guild, "
            "'[Copper Disc] (DRU, SHD) - BID IN /GU. "
            "You MUST include the item name in your bid! "
            "Currently: `Peter` with 10 DKP - Closing in 2m00s!'"
        )
        match = logreplay.MATCH_START_AUCTION_DKP.match(line)
        self.assertIsNotNone(match)

        result = message_handlers.handle_auc_start(match)

        self.assertTrue(result)
        self.assertIn(item.uuid, config.ACTIVE_AUCTIONS)
        self.assertNotIn(item.uuid, config.HISTORICAL_AUCTIONS)

    @mock.patch('ninjalooter.utils.store_state')
    @mock.patch('ninjalooter.message_handlers.signals')
    def test_handle_auc_end_dkp(self, mock_signals, mock_store_state):
        item = models.ItemDrop(
            'Copper Disc', 'Jim', 'Sun Aug 16 22:47:31 2020')
        config.PENDING_AUCTIONS.append(item)
        auc = utils.start_auction_dkp(item, 'VCR')
        auc.add(10, 'Peter')
        config.HISTORICAL_AUCTIONS.clear()

        line = (
            "[Sun Aug 16 22:47:31 2020] Jim tells the guild, "
            "'Gratss Peter on [Copper Disc] (10 DKP)!'"
        )
        match = logreplay.MATCH_END_AUCTION_DKP.match(line)
        self.assertIsNotNone(match)

        result = message_handlers.handle_auc_end(match)

        self.assertTrue(result)
        self.assertNotIn(item.uuid, config.ACTIVE_AUCTIONS)
        self.assertIn(item.uuid, config.HISTORICAL_AUCTIONS)
        mock_signals.auction_completed.emit.assert_called_once()

    @mock.patch('ninjalooter.utils.store_state')
    @mock.patch('ninjalooter.message_handlers.signals')
    def test_handle_auc_end_not_active(
            self, mock_signals, mock_store_state):
        config.ACTIVE_AUCTIONS.clear()

        line = (
            "[Sun Aug 16 22:47:31 2020] Jim tells the guild, "
            "'Gratss Peter on [Copper Disc] (10 DKP)!'"
        )
        match = logreplay.MATCH_END_AUCTION_DKP.match(line)
        self.assertIsNotNone(match)

        result = message_handlers.handle_auc_end(match)

        self.assertFalse(result)

    @mock.patch('ninjalooter.utils.alert_sound')
    @mock.patch('ninjalooter.utils.alert_message')
    def test_raidtick_reminder_alert(
            self, mock_alert_message, mock_alert_sound):
        config.RAIDTICK_REMINDER_COUNT = 0
        config.MAX_RAIDTICK_REMINDERS = 3

        message_handlers.raidtick_reminder_alert()
        self.assertEqual(1, config.RAIDTICK_REMINDER_COUNT)
        mock_alert_message.assert_called_once()
        mock_alert_sound.assert_called_once()
        mock_alert_message.reset_mock()
        mock_alert_sound.reset_mock()

        message_handlers.raidtick_reminder_alert()
        self.assertEqual(2, config.RAIDTICK_REMINDER_COUNT)

        message_handlers.raidtick_reminder_alert()
        self.assertEqual(3, config.RAIDTICK_REMINDER_COUNT)
        mock_alert_message.reset_mock()

        # At max: should NOT increment further
        message_handlers.raidtick_reminder_alert()
        self.assertEqual(3, config.RAIDTICK_REMINDER_COUNT)
        title_arg = mock_alert_message.call_args[0][0]
        msg_arg = mock_alert_message.call_args[0][1]
        self.assertIn("Reminder #4", title_arg)
        self.assertIn("Next reminder: 10 minutes", msg_arg)
