import datetime
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QPushButton

from ninjalooter import config, models
from ninjalooter.app_signals import signals
from ninjalooter.tests import base
from ninjalooter.ui.attendance_frame import AttendanceFrame

_app = QApplication.instance() or QApplication([])


class TestAttendancePopRoll(base.NLTestBase):
    def test_use_for_pop_roll_emits_the_selected_tick(self):
        tick = models.WhoLog(
            datetime.datetime(2020, 8, 16, 22, 46, 32),
            {"Amy": models.Player("Amy", "Wizard", 60, "Kingdom")},
            raidtick=True,
            tick_name="Castle",
        )
        config.ATTENDANCE_LOGS.append(tick)
        frame = AttendanceFrame()
        self.addCleanup(frame.deleteLater)
        labels = [button.text() for button in frame.findChildren(QPushButton)]
        self.assertIn("Use for Pop Roll", labels)

        received = []
        signals.use_for_pop_roll.connect(received.append)
        self.addCleanup(lambda: signals.use_for_pop_roll.disconnect(received.append))

        frame._on_use_for_pop_roll()
        self.assertEqual([], received)

        frame.attendance_list.select_object(tick)
        frame._on_use_for_pop_roll()
        self.assertEqual([tick], received)
