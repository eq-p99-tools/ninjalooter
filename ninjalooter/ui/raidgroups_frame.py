from __future__ import annotations

from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtWidgets import (
    QLabel,
    QLayout,
    QLayoutItem,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ninjalooter import config
from ninjalooter.app_signals import signals
from ninjalooter.ui.table_model import ColumnDefn, ObjectTableView


class _FlowLayout(QLayout):
    """Layout that wraps child widgets left-to-right, top-to-bottom."""

    def __init__(self, parent=None, h_spacing=8, v_spacing=8):
        super().__init__(parent)
        self._h_spacing = h_spacing
        self._v_spacing = v_spacing
        self._items: list[QLayoutItem] = []

    def addItem(self, item: QLayoutItem):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), test_only=True)

    def setGeometry(self, rect: QRect):
        super().setGeometry(rect)
        self._do_layout(rect, test_only=False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        m = self.contentsMargins()
        size += QSize(m.left() + m.right(), m.top() + m.bottom())
        return size

    def _do_layout(self, rect: QRect, *, test_only: bool) -> int:
        x = rect.x()
        y = rect.y()
        line_height = 0

        for item in self._items:
            wid = item.widget()
            if wid is None:
                continue
            space_x = self._h_spacing
            space_y = self._v_spacing
            next_x = x + item.sizeHint().width() + space_x
            if next_x - space_x > rect.right() and line_height > 0:
                x = rect.x()
                y = y + line_height + space_y
                next_x = x + item.sizeHint().width() + space_x
                line_height = 0
            if not test_only:
                item.setGeometry(QRect(x, y, item.sizeHint().width(), item.sizeHint().height()))
            x = next_x
            line_height = max(line_height, item.sizeHint().height())

        return y + line_height - rect.y()


class _GroupWidget(QWidget):
    """A single group panel: title label + small player table."""

    FIXED_WIDTH = 265

    def __init__(self, group, index: int, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFixedWidth(self.FIXED_WIDTH)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 4, 2, 4)

        title = f"{group.group_type} Group"
        label = QLabel(title)
        font = label.font()
        font.setBold(True)
        label.setFont(font)
        layout.addWidget(label)

        table = ObjectTableView(
            columns=[
                ColumnDefn("Name", "name", width=120),
                ColumnDefn("Class", "pclass", width=85),
                ColumnDefn("Level", "level", width=35),
            ],
            parent=self,
            sortable=False,
            single_select=False,
        )
        table.set_objects(group.player_list)
        row_height = table.verticalHeader().defaultSectionSize()
        header_height = table.horizontalHeader().height()
        table.setFixedHeight(header_height + row_height * max(len(group.player_list), 1) + 4)
        layout.addWidget(table)

    def sizeHint(self):
        return QSize(self.FIXED_WIDTH, super().sizeHint().height())


class RaidGroupsFrame(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self._outer = QVBoxLayout(self)
        self._outer.setContentsMargins(6, 6, 6, 6)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._outer.addWidget(self._scroll)

        self._empty_label: QLabel | None = None
        self._content: QWidget | None = None

        self._show_empty()

        signals.calc_raid_groups.connect(self._on_calc_raid_groups)
        signals.app_clear.connect(self._on_app_clear)

    def _show_empty(self):
        self._clear_content()
        container = QWidget()
        vbox = QVBoxLayout(container)
        self._empty_label = QLabel("No raid groups calculated")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.addStretch()
        vbox.addWidget(self._empty_label)
        vbox.addStretch()
        self._content = container
        self._scroll.setWidget(container)

    def _clear_content(self):
        old = self._scroll.takeWidget()
        if old is not None:
            old.deleteLater()
        self._content = None
        self._empty_label = None

    def _build_groups(self):
        raid = config.RAID_GROUPS
        if raid is None or not raid.groups:
            self._show_empty()
            return

        self._clear_content()
        container = QWidget()
        flow = _FlowLayout(container, h_spacing=4, v_spacing=10)

        for i, group in enumerate(raid.groups):
            gw = _GroupWidget(group, i, container)
            flow.addWidget(gw)

        container.setLayout(flow)
        self._content = container
        self._scroll.setWidget(container)

    def _on_calc_raid_groups(self):
        if config.RAID_GROUPS is None or not config.RAID_GROUPS.groups:
            self._show_calculating()
        else:
            self._build_groups()

    def _show_calculating(self):
        self._clear_content()
        container = QWidget()
        vbox = QVBoxLayout(container)
        label = QLabel("Calculating raid groups...")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.addStretch()
        vbox.addWidget(label)
        vbox.addStretch()
        self._content = container
        self._scroll.setWidget(container)

    def _on_app_clear(self):
        config.RAID_GROUPS = None
        self._show_empty()
