import json
from unittest import mock

import dateutil.parser

from ninjalooter import config
from ninjalooter import constants
from ninjalooter import extra_data
from ninjalooter import models
from ninjalooter.tests import base
from ninjalooter import utils


class TestModels(base.NLTestBase):
    def test_Player_model(self):
        player = models.Player("Jim", constants.CLERIC, 50, "Guild")

        # Should be JSON Encodable
        player_json = json.dumps(player, cls=utils.JSONEncoder)

        # Should be JSON Decodable
        loaded_player = json.loads(player_json, cls=utils.JSONDecoder)
        self.assertEqual(player, loaded_player)

    def test_CredittLog_model(self):
        creditt = models.CredittLog('time', 'user', 'cReDiTt john', 'raw')
        self.assertEqual('time', creditt.time)
        self.assertEqual('user', creditt.user)
        self.assertEqual('cReDiTt john', creditt.message)
        self.assertEqual('raw', creditt.raw_message)
        self.assertEqual('John', creditt.target())

    def test_GratssLog_model(self):
        gratss = models.GratssLog(
            'time', 'user', 'GRAtss toald Cloak of Flames 5 DKP', 'raw')
        self.assertEqual('time', gratss.time)
        self.assertEqual('user', gratss.user)
        self.assertEqual('GRAtss toald Cloak of Flames 5 DKP', gratss.message)
        self.assertEqual('raw', gratss.raw_message)
        self.assertEqual('Toald', gratss.target())

    def test_WhoLog_model(self):
        # WhoLogs use real datetime times
        sometime = dateutil.parser.parse("Mon Aug 17 07:15:39 2020")
        affils = {"Jim": "Guild"}
        wholog = models.WhoLog(sometime, affils)

        # Should be JSON Encodable
        wholog_json = json.dumps(wholog, cls=utils.JSONEncoder)

        # Should be JSON Decodable
        loaded_wholog = json.loads(wholog_json, cls=utils.JSONDecoder)
        self.assertEqual(wholog, loaded_wholog)

    def test_PopulationPreview_model(self):
        popprev = models.PopulationPreview("VCR", 20)

        # Should be JSON Encodable
        popprev_json = json.dumps(popprev, cls=utils.JSONEncoder)

        # Should be JSON Decodable
        loaded_popprev = json.loads(popprev_json, cls=utils.JSONDecoder)
        self.assertEqual(popprev, loaded_popprev)

    def test_KillTimer_model(self):
        # KillTimers just use string-times
        killtime = models.KillTimer(
            "Mon Aug 17 07:15:39 2020", "A Mob")

        # Should be JSON Encodable
        killtime_json = json.dumps(killtime, cls=utils.JSONEncoder)

        # Should be JSON Decodable
        loaded_killtime = json.loads(killtime_json, cls=utils.JSONDecoder)
        self.assertEqual(killtime, loaded_killtime)

    def test_ItemDrop_model(self):
        # ItemDrops just use string-times
        # This item is for BRD and CLR, and is droppable with min_dkp 3
        itemdrop = models.ItemDrop(
            "Ochre Tessera", "Bob", "Mon Aug 17 07:15:39 2020")
        self.assertEqual("BRD, CLR", itemdrop.classes())
        self.assertEqual("Yes", itemdrop.droppable())
        self.assertEqual(config.MIN_DKP, itemdrop.min_dkp())

        # This item is for BRD only and is NODROP
        itemdrop = models.ItemDrop(
            "Light Woolen Mask", "Bob", "Mon Aug 17 07:15:39 2020")
        self.assertEqual("BRD", itemdrop.classes())
        self.assertEqual("NO", itemdrop.droppable())

        # This item should have the case fixed
        itemdrop = models.ItemDrop(
            "light WOOLEN Mask", "Bob", "Mon Aug 17 07:15:39 2020")
        self.assertEqual("Light Woolen Mask", itemdrop.name)

        # Should be JSON Encodable
        itemdrop_json = json.dumps(itemdrop, cls=utils.JSONEncoder)

        # Should be JSON Decodable
        loaded_itemdrop = json.loads(itemdrop_json, cls=utils.JSONDecoder)
        self.assertEqual(itemdrop, loaded_itemdrop)

    def test_Auction_base_model(self):
        item_name = 'Copper Disc'
        itemdrop = models.ItemDrop(item_name, "Jim", "timestamp")
        auc = models.Auction(itemdrop)
        self.assertRaises(NotImplementedError, auc.add, 1, 'Jim')
        self.assertRaises(NotImplementedError, auc.highest)

        # Should be JSON Encodable
        auc_json = json.dumps(auc, cls=utils.JSONEncoder)

        # Should be JSON Decodable
        loaded_auc = json.loads(auc_json, cls=utils.JSONDecoder)
        self.assertEqual(auc, loaded_auc)

    def test_DKPAuction_model_add(self):
        item_name = 'Copper Disc'
        itemdrop = models.ItemDrop(item_name, "Jim", "timestamp")
        auc = models.DKPAuction(itemdrop, 'VCR', min_dkp=3)
        self.assertListEqual([], auc.highest())

        # Bid too low
        result = auc.add(2, 'Peter')
        self.assertFalse(result)
        self.assertListEqual([], auc.highest())

        # First bid, valid
        result = auc.add(10, 'Peter')
        self.assertTrue(result)
        self.assertListEqual([('Peter', 10)], auc.highest())

        # Second bid, lower than first bid
        result = auc.add(8, 'Paul')
        self.assertFalse(result)
        self.assertListEqual([('Peter', 10)], auc.highest())

        # Third bid, higher than first bid
        result = auc.add(12, 'Mary')
        self.assertTrue(result)
        self.assertListEqual([('Mary', 12)], auc.highest())

        # Fourth bid, tied with highest bid
        result = auc.add(12, 'Dan')
        self.assertFalse(result)
        self.assertListEqual([('Mary', 12)], auc.highest())

        # Invalid bid
        result = auc.add(None, 'Fred')
        self.assertFalse(result)

        # Should be JSON Encodable
        auc_json = json.dumps(auc, cls=utils.JSONEncoder)

        # Should be JSON Decodable
        loaded_auc = json.loads(auc_json, cls=utils.JSONDecoder)
        self.assertEqual(auc, loaded_auc)

    def test_DKPAuction_model_bid_text(self):
        item_name = 'Copper Disc'
        itemdrop = models.ItemDrop(item_name, "Jim", "timestamp")
        auc = models.DKPAuction(itemdrop, 'VCR', min_dkp=3)

        # No bids
        config.PRIMARY_BID_CHANNEL = 'auc'
        self.assertEqual(
            "/AUC ~[Copper Disc] (DRU, SHD) - BID IN /AUC, MIN 3 DKP. "
            "You MUST include the item name in your bid! Closing in {}. "
            .format(auc.time_remaining_text()),
            auc.bid_text())

        # Valid bid
        result = auc.add(3, 'Peter')
        self.assertTrue(result)
        self.assertListEqual([('Peter', 3)], auc.highest())

        # Bid exists
        config.PRIMARY_BID_CHANNEL = 'shout'
        self.assertEqual(
            "/SHOUT ~[Copper Disc] (DRU, SHD) - BID IN /SHOUT. "
            "You MUST include the item name in your bid! Currently: "
            "`Peter` with 3 DKP - Closing in {}! "
            .format(auc.time_remaining_text()),
            auc.bid_text())

        item_name = 'Golden Jasper Earring'
        itemdrop = models.ItemDrop(item_name, "Jim", "timestamp")
        auc = models.DKPAuction(itemdrop, 'VCR', min_dkp=3)

        # No bids
        config.PRIMARY_BID_CHANNEL = 'gu'
        self.assertEqual(
            "/GU ~[Golden Jasper Earring] - BID IN /GU, MIN 3 DKP. "
            "You MUST include the item name in your bid! Closing in {}. "
            .format(auc.time_remaining_text()),
            auc.bid_text())

    def test_RandomAuction_model_add(self):
        item_name = 'Copper Disc'
        itemdrop = models.ItemDrop(item_name, "Jim", "timestamp")
        auc = models.RandomAuction(itemdrop)
        self.assertListEqual([], auc.highest())

        # First roll, valid
        result = auc.add(10, 'Peter')
        self.assertTrue(result)
        self.assertListEqual([('Peter', 10)], auc.highest())

        # Second roll, lower than first roll
        result = auc.add(8, 'Paul')
        self.assertTrue(result)
        self.assertListEqual([('Peter', 10)], auc.highest())

        # Third roll, higher than first roll
        result = auc.add(12, 'Mary')
        self.assertTrue(result)
        self.assertListEqual([('Mary', 12)], auc.highest())

        # Fifth roll, player rolls a second time
        result = auc.add(18, 'Paul')
        self.assertFalse(result)
        self.assertListEqual([('Mary', 12)], auc.highest())

        # Fifth roll, tied with highest roll
        result = auc.add(12, 'Dan')
        self.assertTrue(result)
        self.assertEqual(2, len(tuple(auc.highest())))
        self.assertIn(('Mary', 12), tuple(auc.highest()))
        self.assertIn(('Dan', 12), tuple(auc.highest()))

        # Invalid roll
        result = auc.add(None, 'Fred')
        self.assertFalse(result)

        # All rolls should be tracked
        self.assertDictEqual(
            {'Dan': 12, 'Mary': 12, 'Paul': 8, 'Peter': 10},
            auc.rolls)

        # Should be JSON Encodable
        auc_json = json.dumps(auc, cls=utils.JSONEncoder)

        # Should be JSON Decodable
        loaded_auc = json.loads(auc_json, cls=utils.JSONDecoder)
        self.assertEqual(auc, loaded_auc)

    def test_RandomAuction_model_bid_text(self):
        item_name = 'Copper Disc'
        itemdrop = models.ItemDrop(item_name, "Jim", "timestamp")
        config.NUMBERS = [12345]
        auc = models.RandomAuction(itemdrop)

        config.PRIMARY_BID_CHANNEL = 'auc'
        self.assertEqual(
            "/AUC ~[Copper Disc] (DRU, SHD) ROLL 12345 NOW!",
            auc.bid_text())

        item_name = 'Golden Jasper Earring'
        itemdrop = models.ItemDrop(item_name, "Jim", "timestamp")
        auc = models.RandomAuction(itemdrop)

        config.PRIMARY_BID_CHANNEL = 'gu'
        self.assertEqual(
            "/GU ~[Golden Jasper Earring] ROLL 12345 NOW!",
            auc.bid_text())

    def test_RandomAuction_model_win_text(self):
        item_name = 'Copper Disc'
        itemdrop = models.ItemDrop(item_name, "Jim", "timestamp")
        config.NUMBERS = [12345]
        auc = models.RandomAuction(itemdrop)

        config.PRIMARY_BID_CHANNEL = 'auc'

        auc.add(10, "Bill")
        auc.add(20, "Tom")
        auc.add(5, "James")

        self.assertEqual(
            "/AUC ~Gratss Tom on [Copper Disc] with 20 / 12345!",
            auc.win_text())

    def test_get_next_number(self):
        models.config.NUMBERS = [10, 20, 30]
        models.config.LAST_NUMBER = 0
        self.assertEqual(10, models.get_next_number())
        self.assertEqual(20, models.get_next_number())
        self.assertEqual(30, models.get_next_number())
        self.assertEqual(10, models.get_next_number())

    def test_Player_helpers(self):
        warrior = models.Player("War", constants.WARRIOR, 60, "G")
        self.assertTrue(warrior.is_tank())
        self.assertTrue(warrior.is_war())
        self.assertFalse(warrior.is_knight())
        self.assertFalse(warrior.is_priest())
        self.assertFalse(warrior.is_melee())
        self.assertFalse(warrior.is_caster())

        paladin = models.Player("Pal", constants.PALADIN, 60, "G")
        self.assertTrue(paladin.is_tank())
        self.assertFalse(paladin.is_war())
        self.assertTrue(paladin.is_knight())

        cleric = models.Player("Clr", constants.CLERIC, 60, "G")
        self.assertTrue(cleric.is_priest())
        self.assertTrue(cleric.is_cleric())
        self.assertFalse(cleric.is_tank())

        bard = models.Player("Brd", constants.BARD, 60, "G")
        self.assertTrue(bard.is_melee())
        self.assertTrue(bard.is_bard())
        self.assertFalse(bard.is_caster())

        wizard = models.Player("Wiz", constants.WIZARD, 60, "G")
        self.assertTrue(wizard.is_caster())
        self.assertTrue(wizard.is_wizard())
        self.assertFalse(wizard.is_melee())

        enchanter = models.Player("Enc", constants.ENCHANTER, 60, "G")
        self.assertTrue(enchanter.is_enchanter())
        self.assertTrue(enchanter.is_caster())

        necro = models.Player("Nec", constants.NECROMANCER, 60, "G")
        self.assertTrue(necro.is_necromancer())

        monk = models.Player("Mnk", constants.MONK, 60, "G")
        self.assertTrue(monk.is_monk())
        self.assertTrue(monk.is_melee())

        shaman = models.Player("Shm", constants.SHAMAN, 60, "G")
        self.assertTrue(shaman.is_shaman())
        self.assertTrue(shaman.is_priest())

    def test_DKPAuction_win_text(self):
        item_name = 'Copper Disc'
        itemdrop = models.ItemDrop(item_name, "Jim", "timestamp")
        auc = models.DKPAuction(itemdrop, 'VCR', min_dkp=3)
        config.PRIMARY_BID_CHANNEL = 'gu'

        # No bids = ROT
        self.assertEqual(
            "/GU ~Gratss ROT on [Copper Disc] (0 DKP)!",
            auc.win_text())

        # With a bid
        auc.add(10, 'Peter')
        self.assertEqual(
            "/GU ~Gratss Peter on [Copper Disc] (10 DKP)!",
            auc.win_text())

    def test_ItemDrop_min_dkp_sentinels(self):
        saved = extra_data.EXTRA_ITEM_DATA.get("TestSentinelItem")

        extra_data.EXTRA_ITEM_DATA["TestSentinelItem"] = {"min_dkp": -1}
        item = models.ItemDrop("TestSentinelItem", "Bob", "ts")
        self.assertEqual("Random", item.min_dkp())

        extra_data.EXTRA_ITEM_DATA["TestSentinelItem"] = {"min_dkp": -2}
        item = models.ItemDrop("TestSentinelItem", "Bob", "ts")
        self.assertEqual("Bank", item.min_dkp())

        extra_data.EXTRA_ITEM_DATA["TestSentinelItem"] = {"min_dkp": -3}
        item = models.ItemDrop("TestSentinelItem", "Bob", "ts")
        self.assertEqual("???", item.min_dkp())

        if saved is None:
            del extra_data.EXTRA_ITEM_DATA["TestSentinelItem"]
        else:
            extra_data.EXTRA_ITEM_DATA["TestSentinelItem"] = saved

    def test_ItemDrop_min_dkp_override(self):
        item = models.ItemDrop("Copper Disc", "Bob", "ts", min_dkp_override=50)
        self.assertEqual(50, item.min_dkp())

    def test_KillTimer_island(self):
        kt_known = models.KillTimer("Mon Aug 17 07:15:39 2020", "an azarack")
        self.assertEqual("2", kt_known.island())

        kt_unknown = models.KillTimer("Mon Aug 17 07:15:39 2020", "Unknown Mob")
        self.assertEqual("Other", kt_unknown.island())

    def test_Group_tank_score(self):
        group = models.Group(constants.GT_TANK)
        war = models.Player("War", constants.WARRIOR, 60, "G")
        clr = models.Player("Clr", constants.CLERIC, 60, "G")
        brd = models.Player("Brd", constants.BARD, 60, "G")
        group.player_list = [war, clr, brd]
        score = group.tank_score()
        self.assertGreater(score, 0)

    def test_Group_cleric_score(self):
        group = models.Group(constants.GT_CLERIC)
        clr1 = models.Player("Clr1", constants.CLERIC, 60, "G")
        clr2 = models.Player("Clr2", constants.CLERIC, 60, "G")
        war = models.Player("War", constants.WARRIOR, 60, "G")
        group.player_list = [clr1, clr2, war]
        score = group.cleric_score()
        self.assertGreater(score, 0)

    def test_Group_general_score(self):
        group = models.Group(constants.GT_GENERAL)
        enc = models.Player("Enc", constants.ENCHANTER, 60, "G")
        wiz = models.Player("Wiz", constants.WIZARD, 60, "G")
        group.player_list = [enc, wiz]
        score = group.general_score()
        self.assertGreater(score, 0)

    def test_Auction_time_remaining_ui(self):
        item = models.ItemDrop("Copper Disc", "Jim", "timestamp")
        auc = models.DKPAuction(item, 'VCR')
        ui_text = auc.time_remaining_ui()
        self.assertRegex(ui_text, r'\d+m\d+s|\d+s')
