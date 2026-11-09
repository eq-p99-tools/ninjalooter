import datetime
import os
from unittest import mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import QApplication

from ninjalooter import config, models
from ninjalooter.app_signals import signals
from ninjalooter.tests import base
from ninjalooter.ui.population_frame import PopulationFrame

_app = QApplication.instance() or QApplication([])


def _names(table):
    return [player.name for player in table.object_model.get_objects()]


class TestPopulationFrame(base.NLTestBase):
    def setUp(self):
        super().setUp()
        self.frame = PopulationFrame()

    def tearDown(self):
        frame = self.frame
        for sig, slot in (
            (signals.who, frame._on_who),
            (signals.clear_who, frame._on_clear_who),
            (signals.who_end, frame._on_who_end),
            (signals.app_clear, frame._on_app_clear),
            (signals.app_reload, frame._on_app_reload),
            (signals.use_for_pop_roll, frame._on_use_for_pop_roll),
        ):
            try:
                sig.disconnect(slot)
            except RuntimeError:
                pass
        frame.deleteLater()
        QApplication.processEvents()
        super().tearDown()

    def _tick(self):
        tick = models.WhoLog(
            datetime.datetime(2020, 8, 16, 22, 46, 32),
            {"Amy": models.Player("Amy", "Wizard", 60, "Kingdom")},
            raidtick=True,
            tick_name="Castle",
            zone="Plane of Time",
        )
        config.ATTENDANCE_LOGS.append(tick)
        return tick

    def test_who_lines_still_fill_the_latest_table(self):
        signals.clear_who.emit()
        signals.who.emit("Jim", "Cleric", 60, "Castle")
        signals.who_end.emit()

        self.assertEqual(["Jim"], _names(self.frame._player_table))
        self.assertEqual("Castle", config.LAST_WHO_SNAPSHOT["Jim"].guild)
        self.assertEqual(["VCR"], [row.alliance for row in self.frame._preview_table.object_model.get_objects()])
        self.assertEqual("Source: latest /who", self.frame._source_label.text())
        self.assertFalse(self.frame._latest_button.isEnabled())

    def test_use_for_pop_roll_counts_the_selected_tick(self):
        config.LAST_WHO_SNAPSHOT["Jim"] = models.Player("Jim", "Cleric", 60, "Castle")
        self.frame._refresh_player_table()
        tick = self._tick()
        self.frame._alliance_spinners["Kingdom"].setValue(4)

        signals.use_for_pop_roll.emit(tick)

        self.assertEqual(["Amy"], _names(self.frame._player_table))
        alliances = [row.alliance for row in self.frame._preview_table.object_model.get_objects()]
        self.assertEqual(["Kingdom"], alliances)
        self.assertEqual(0, self.frame._alliance_spinners["Kingdom"].value())
        self.assertIn("Sun Aug 16 22:46:32 2020", self.frame._source_label.text())
        self.assertIn("RaidTick", self.frame._source_label.text())
        self.assertIn("Castle", self.frame._source_label.text())
        self.assertTrue(self.frame._latest_button.isEnabled())

        with mock.patch("ninjalooter.ui.population_frame.utils.to_clipboard") as clip:
            self.frame._copy_roll_text()
        self.assertEqual("/shout 1-1 Kingdom\n/random 1 1", clip.call_args[0][0])

    def test_new_who_leaves_a_pinned_tick_in_place(self):
        tick = self._tick()
        signals.use_for_pop_roll.emit(tick)
        self.frame._alliance_spinners["Kingdom"].setValue(2)

        config.LAST_WHO_SNAPSHOT.clear()
        signals.clear_who.emit()
        signals.who.emit("Ned", "Rogue", 60, "Black Lotus")
        signals.who_end.emit()

        self.assertEqual(["Amy"], _names(self.frame._player_table))
        self.assertEqual(2, self.frame._alliance_spinners["Kingdom"].value())
        self.assertEqual("Black Lotus", config.LAST_WHO_SNAPSHOT["Ned"].guild)
        self.assertTrue(self.frame._latest_button.isEnabled())

        self.frame._use_latest()

        self.assertEqual(["Ned"], _names(self.frame._player_table))
        self.assertEqual(["BL"], [row.alliance for row in self.frame._preview_table.object_model.get_objects()])
        self.assertEqual(0, self.frame._alliance_spinners["Kingdom"].value())
        self.assertEqual("Source: latest /who", self.frame._source_label.text())
        self.assertFalse(self.frame._latest_button.isEnabled())

    def test_deleted_tick_falls_back_to_the_latest_who(self):
        config.LAST_WHO_SNAPSHOT["Jim"] = models.Player("Jim", "Cleric", 60, "Castle")
        tick = self._tick()
        signals.use_for_pop_roll.emit(tick)
        config.ATTENDANCE_LOGS.remove(tick)

        self.frame.showEvent(QShowEvent())

        self.assertEqual(["Jim"], _names(self.frame._player_table))
        self.assertIsNone(self.frame._roll_source)
        self.assertEqual("Source: latest /who", self.frame._source_label.text())

    def test_clear_drops_the_pinned_tick(self):
        signals.use_for_pop_roll.emit(self._tick())
        signals.app_clear.emit()

        self.assertEqual([], _names(self.frame._player_table))
        self.assertIsNone(self.frame._roll_source)
        self.assertEqual({}, config.LAST_WHO_SNAPSHOT)
