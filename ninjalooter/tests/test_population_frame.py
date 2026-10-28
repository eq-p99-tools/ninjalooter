import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from ninjalooter import config, models
from ninjalooter.app_signals import signals
from ninjalooter.tests import base
from ninjalooter.ui.population_frame import PopulationFrame

_app = QApplication.instance() or QApplication([])


class TestPopulationFrame(base.NLTestBase):
    def test_who_lines_leave_the_snapshot_and_refresh_once(self):
        remembered = models.Player("Jim", "Cleric", 60, "Castle")
        config.LAST_WHO_SNAPSHOT["Jim"] = remembered
        frame = PopulationFrame()
        self.addCleanup(frame.deleteLater)

        signals.who.emit("Jim", "", 0, "")
        self.assertIs(config.LAST_WHO_SNAPSHOT["Jim"], remembered)
        self.assertEqual(["Jim"], [player.name for player in frame._player_table.object_model.get_objects()])

        config.LAST_WHO_SNAPSHOT["Amy"] = models.Player("Amy", "Wizard", 60, "Castle")
        signals.who_end.emit()
        names = [player.name for player in frame._player_table.object_model.get_objects()]
        self.assertEqual(["Amy", "Jim"], names)
