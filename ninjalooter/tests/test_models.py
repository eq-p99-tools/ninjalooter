import json

import dateutil.parser

from ninjalooter import config
from ninjalooter import models
from ninjalooter.tests import base
from ninjalooter import utils


class TestModels(base.NLTestBase):
    def test_Player_model(self):
        player = models.Player("Jim", "Cleric", 50, "Guild")

        # Should be JSON Encodable
        player_json = json.dumps(player, cls=utils.JSONEncoder)

        # Should be JSON Decodable
        loaded_player = json.loads(player_json, cls=utils.JSONDecoder)
        self.assertEqual(player, loaded_player)

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
        self.assertEqual(
            "/shout [Copper Disc] (DRU, SHD) - `VCR` BID IN SHOUT, MIN 3 DKP. "
            "You MUST include the item name in your bid! ",
            auc.bid_text())

        # Valid bid
        result = auc.add(3, 'Peter')
        self.assertTrue(result)
        self.assertListEqual([('Peter', 3)], auc.highest())

        # Bid exists
        self.assertEqual(
            "/shout [Copper Disc] (DRU, SHD) - `VCR` BID IN SHOUT. "
            "You MUST include the item name in your bid! Currently: "
            "`Peter` with 3 DKP - Closing Soon! ",
            auc.bid_text())

        item_name = 'Golden Jasper Earring'
        itemdrop = models.ItemDrop(item_name, "Jim", "timestamp")
        auc = models.DKPAuction(itemdrop, 'VCR', min_dkp=3)

        # No bids
        self.assertEqual(
            "/shout [Golden Jasper Earring] - `VCR` BID IN SHOUT, MIN 3 DKP. "
            "You MUST include the item name in your bid! ",
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
        config.NUMBERS = ['12345']
        auc = models.RandomAuction(itemdrop)

        self.assertEqual(
            "/shout [Copper Disc] (DRU, SHD) ROLL 12345 NOW!",
            auc.bid_text())

        item_name = 'Golden Jasper Earring'
        itemdrop = models.ItemDrop(item_name, "Jim", "timestamp")
        auc = models.RandomAuction(itemdrop)

        self.assertEqual(
            "/shout [Golden Jasper Earring] ROLL 12345 NOW!",
            auc.bid_text())

    def test_get_next_number(self):
        models.config.NUMBERS = [10, 20, 30]
        models.config.LAST_NUMBER = 0
        self.assertEqual(10, models.get_next_number())
        self.assertEqual(20, models.get_next_number())
        self.assertEqual(30, models.get_next_number())
        self.assertEqual(10, models.get_next_number())
