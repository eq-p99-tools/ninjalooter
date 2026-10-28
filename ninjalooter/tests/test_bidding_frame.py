import datetime
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEvent, QPointF, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QApplication

from ninjalooter import config, models
from ninjalooter.tests import base
from ninjalooter.ui.bidding_frame import _COUNTDOWN_ROLES, _active_time_sort_key
from ninjalooter.ui.table_model import ColumnDefn, ObjectTableView

_app = QApplication.instance() or QApplication([])


def _auction(name, start):
    item = models.ItemDrop(name, "Jim", "timestamp")
    auction = models.DKPAuction(item, "VCR")
    auction.start_time = start
    return auction


def _visual_names(view):
    proxy = view.proxy_model
    model = view.object_model
    names = []
    for row in range(proxy.rowCount()):
        source = proxy.mapToSource(proxy.index(row, 0))
        names.append(model.get_object(source.row()).name())
    return names


class TestActiveAuctionOrder(base.NLTestBase):
    def setUp(self):
        super().setUp()
        now = datetime.datetime(2026, 10, 27, 23, 0, 0)
        expired = now - datetime.timedelta(seconds=config.MIN_BID_TIME + 30)
        just_expired = now - datetime.timedelta(seconds=config.MIN_BID_TIME)
        running = now - datetime.timedelta(seconds=10)
        self.early = _auction("Early", expired)
        self.mid = _auction("Mid", just_expired)
        self.late = _auction("Late", running)
        self.view = ObjectTableView(
            columns=[
                ColumnDefn(
                    "Time Left",
                    _active_time_sort_key,
                    string_converter=lambda auction: auction.time_remaining_ui(),
                )
            ]
        )
        self.addCleanup(self.view.deleteLater)
        self.view.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        self.view.set_objects([self.late, self.early, self.mid])

    def test_equal_zero_times_stay_in_start_order(self):
        self.assertEqual(["Early", "Mid", "Late"], _visual_names(self.view))

    def test_countdown_and_bid_refresh_do_not_reorder(self):
        self.view.object_model.refresh_all(_COUNTDOWN_ROLES)
        self.mid.bids[10] = "Jim"
        self.view.object_model.refresh_object(self.mid, _COUNTDOWN_ROLES)
        self.assertEqual(["Early", "Mid", "Late"], _visual_names(self.view))

    def test_changing_start_time_reorders(self):
        self.late.start_time = self.early.start_time - datetime.timedelta(seconds=1)
        self.view.object_model.refresh_object(self.late)
        self.assertEqual(["Late", "Early", "Mid"], _visual_names(self.view))


def _click_header(view, section):
    header = view.horizontalHeader()
    x = header.sectionViewportPosition(section) + header.sectionSize(section) // 2
    y = header.height() // 2
    pos = QPointF(x, y)
    for event_type in (QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonRelease):
        event = QMouseEvent(
            event_type,
            pos,
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        QApplication.sendEvent(header.viewport(), event)
    QApplication.processEvents()


class TestHistorySortCycle(base.NLTestBase):
    def test_third_click_restores_completion_order(self):
        class Row:
            def __init__(self, name, done):
                self.name = name
                self.done = done

        rows = [Row("C", 2), Row("A", 1), Row("B", 3)]
        view = ObjectTableView(
            columns=[
                ColumnDefn("Item", lambda row: row.name, width=80),
                ColumnDefn("Completed", lambda row: row.done, width=80),
            ]
        )
        self.addCleanup(view.deleteLater)
        view.set_objects(rows)
        view.setColumnHidden(1, True)
        view.sortByColumn(1, Qt.SortOrder.AscendingOrder)
        view.set_sort_cycle_default(1, Qt.SortOrder.AscendingOrder)
        view.resize(300, 200)
        view.show()

        def names():
            proxy = view.proxy_model
            found = []
            for row in range(proxy.rowCount()):
                source = proxy.mapToSource(proxy.index(row, 0))
                found.append(view.object_model.get_object(source.row()).name)
            return found

        self.assertEqual(["A", "C", "B"], names())

        _click_header(view, 0)
        self.assertEqual(["A", "B", "C"], names())
        self.assertEqual(0, view.horizontalHeader().sortIndicatorSection())

        _click_header(view, 0)
        self.assertEqual(["C", "B", "A"], names())

        _click_header(view, 0)
        self.assertEqual(["A", "C", "B"], names())
        self.assertEqual(-1, view.horizontalHeader().sortIndicatorSection())
