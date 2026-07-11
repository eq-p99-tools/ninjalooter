import os
from unittest import mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from ninjalooter import config, models
from ninjalooter.tests import base
from ninjalooter.ui import killtimes_frame

_app = QApplication.instance() or QApplication([])


class TestKillTimesFrame(base.NLTestBase):
    def setUp(self):
        super().setUp()
        config.KILL_TIMERS = [
            models.KillTimer("Mon Aug 17 07:15:39 2020", "an azarack", zone="Plane of Sky"),
            models.KillTimer("Mon Aug 17 07:16:39 2020", "a gnoll", zone="West Commonlands"),
        ]

    def test_defaults_to_expanded(self):
        frame = killtimes_frame.KillTimesFrame()
        self.addCleanup(frame.deleteLater)
        zone_index = frame._tree_model.index(0, 0)
        self.assertTrue(frame._tree.isExpanded(zone_index))

    def test_restores_collapsed_zone_from_cache(self):
        config.KILL_TIMER_SECTIONS_EXPANDED_CACHE["West Commonlands"] = False
        frame = killtimes_frame.KillTimesFrame()
        self.addCleanup(frame.deleteLater)

        collapsed = None
        for row in range(frame._tree_model.rowCount()):
            item = frame._tree_model.item(row, 0)
            if item.text() == "West Commonlands":
                collapsed = frame._tree.isExpanded(frame._tree_model.indexFromItem(item))
                break
        self.assertIsNotNone(collapsed)
        self.assertFalse(collapsed)

    def test_restores_collapsed_island_from_cache(self):
        config.KILL_TIMER_SECTIONS_EXPANDED_CACHE["Plane of Sky/Island 2"] = False
        frame = killtimes_frame.KillTimesFrame()
        self.addCleanup(frame.deleteLater)

        posky = None
        for row in range(frame._tree_model.rowCount()):
            item = frame._tree_model.item(row, 0)
            if item.text() == "Plane of Sky":
                posky = item
                break
        self.assertIsNotNone(posky)
        island = posky.child(0, 0)
        self.assertEqual("Island 2", island.text())
        self.assertFalse(frame._tree.isExpanded(frame._tree_model.indexFromItem(island)))

    @mock.patch("ninjalooter.ui.killtimes_frame.utils.store_state")
    def test_user_collapse_updates_cache(self, mock_store_state):
        frame = killtimes_frame.KillTimesFrame()
        self.addCleanup(frame.deleteLater)

        wc_index = None
        for row in range(frame._tree_model.rowCount()):
            item = frame._tree_model.item(row, 0)
            if item.text() == "West Commonlands":
                wc_index = frame._tree_model.indexFromItem(item)
                break
        self.assertIsNotNone(wc_index)
        self.assertTrue(frame._tree.isExpanded(wc_index))

        frame._tree.collapse(wc_index)
        self.assertFalse(config.KILL_TIMER_SECTIONS_EXPANDED_CACHE["West Commonlands"])
        mock_store_state.assert_called()
