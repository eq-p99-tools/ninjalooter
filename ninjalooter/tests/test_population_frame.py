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
            (signals.who_end, frame._on_who_end),
            (signals.who_history, frame._on_who_history),
            (signals.app_clear, frame._on_app_clear),
            (signals.app_reload, frame._on_app_reload),
            (signals.use_for_pop_roll, frame._on_use_for_pop_roll),
            (signals.alliances_changed, frame._rebuild_spinners),
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

    def test_who_lines_leave_the_snapshot_and_refresh_once(self):
        remembered = models.Player("Jim", "Cleric", 60, "Castle")
        config.LAST_WHO_SNAPSHOT["Jim"] = remembered

        signals.who.emit("Jim", "", 0, "")

        self.assertIs(config.LAST_WHO_SNAPSHOT["Jim"], remembered)
        self.assertEqual([], _names(self.frame._player_table))

        signals.who_end.emit()

        self.assertIs(config.LAST_WHO_SNAPSHOT["Jim"], remembered)
        self.assertEqual(["Jim"], _names(self.frame._player_table))
        self.assertEqual(["VCR"], [row.alliance for row in self.frame._preview_table.object_model.get_objects()])
        self.assertEqual("Latest /who", self.frame._source_combo.currentText())
        self.assertTrue(self.frame._newer_label.isHidden())

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
        self.assertEqual(1, self.frame._source_combo.currentIndex())
        chosen = self.frame._source_combo.currentText()
        self.assertIn("Sun Aug 16 22:46:32 2020", chosen)
        self.assertIn("RaidTick", chosen)
        self.assertIn("Castle", chosen)
        self.assertIn("Plane of Time", chosen)
        self.assertTrue(self.frame._newer_label.isHidden())

        with mock.patch("ninjalooter.ui.population_frame.utils.to_clipboard") as clip:
            self.frame._copy_roll_text()
        self.assertEqual("/shout 1-1 Kingdom\n/random 1 1", clip.call_args[0][0])

    def test_new_who_leaves_a_pinned_tick_in_place(self):
        tick = self._tick()
        signals.use_for_pop_roll.emit(tick)
        self.frame._alliance_spinners["Kingdom"].setValue(2)

        newer = models.WhoLog(
            datetime.datetime(2020, 8, 16, 23, 0, 0),
            {"Ned": models.Player("Ned", "Rogue", 60, "Black Lotus")},
            tick_name="Later",
        )
        config.ATTENDANCE_LOGS.append(newer)
        config.LAST_WHO_SNAPSHOT.clear()
        config.LAST_WHO_SNAPSHOT["Ned"] = models.Player("Ned", "Rogue", 60, "Black Lotus")
        signals.who.emit("Ned", "", 0, "")
        signals.who_end.emit()

        self.assertEqual(["Amy"], _names(self.frame._player_table))
        self.assertEqual(2, self.frame._alliance_spinners["Kingdom"].value())
        self.assertEqual("Black Lotus", config.LAST_WHO_SNAPSHOT["Ned"].guild)
        self.assertIn("Castle", self.frame._source_combo.currentText())
        self.assertIn("Later", self.frame._source_combo.itemText(1))
        self.assertFalse(self.frame._newer_label.isHidden())

        self.frame._source_combo.setCurrentIndex(0)

        self.assertEqual(["Ned"], _names(self.frame._player_table))
        self.assertEqual(["BL"], [row.alliance for row in self.frame._preview_table.object_model.get_objects()])
        self.assertEqual(0, self.frame._alliance_spinners["Kingdom"].value())
        self.assertEqual("Latest /who", self.frame._source_combo.currentText())
        self.assertTrue(self.frame._newer_label.isHidden())

    def test_deleted_tick_falls_back_to_the_latest_who(self):
        config.LAST_WHO_SNAPSHOT["Jim"] = models.Player("Jim", "Cleric", 60, "Castle")
        tick = self._tick()
        signals.use_for_pop_roll.emit(tick)
        config.ATTENDANCE_LOGS.remove(tick)

        self.frame.showEvent(QShowEvent())

        self.assertEqual(["Jim"], _names(self.frame._player_table))
        self.assertIsNone(self.frame._roll_source)
        self.assertEqual("Latest /who", self.frame._source_combo.currentText())

    def test_clear_drops_the_pinned_tick(self):
        signals.use_for_pop_roll.emit(self._tick())
        config.ATTENDANCE_LOGS.clear()
        signals.app_clear.emit()

        self.assertEqual([], _names(self.frame._player_table))
        self.assertIsNone(self.frame._roll_source)
        self.assertEqual({}, config.LAST_WHO_SNAPSHOT)
        self.assertEqual(["Latest /who"], [self.frame._source_combo.itemText(0)])
        self.assertEqual(1, self.frame._source_combo.count())

    def test_source_list_is_newest_first_and_selecting_one_counts_it(self):
        older = models.WhoLog(
            datetime.datetime(2020, 8, 16, 21, 0, 0),
            {"Bob": models.Player("Bob", "Warrior", 60, "Kingdom")},
            tick_name="Early",
            zone="Plane of Sky",
        )
        newer = models.WhoLog(
            datetime.datetime(2020, 8, 16, 22, 0, 0),
            {"Ned": models.Player("Ned", "Rogue", 60, "Black Lotus")},
            raidtick=True,
            tick_name="Later",
            zone="Plane of Fear",
        )
        config.ATTENDANCE_LOGS.extend([older, newer])
        self.frame._alliance_spinners["Kingdom"].setValue(3)
        signals.who_history.emit()

        self.assertEqual(0, self.frame._source_combo.currentIndex())
        self.assertEqual(3, self.frame._alliance_spinners["Kingdom"].value())
        self.assertEqual(3, self.frame._source_combo.count())
        self.assertIn("Later", self.frame._source_combo.itemText(1))
        self.assertIn("RaidTick", self.frame._source_combo.itemText(1))
        self.assertIn("Plane of Fear", self.frame._source_combo.itemText(1))
        self.assertIn("Early", self.frame._source_combo.itemText(2))
        self.assertTrue(self.frame._newer_label.isHidden())

        self.frame._source_combo.setCurrentIndex(2)

        self.assertEqual(["Bob"], _names(self.frame._player_table))
        self.assertEqual(["Kingdom"], [row.alliance for row in self.frame._preview_table.object_model.get_objects()])
        self.assertEqual(0, self.frame._alliance_spinners["Kingdom"].value())
        self.assertFalse(self.frame._newer_label.isHidden())
