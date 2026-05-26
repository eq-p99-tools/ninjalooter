from __future__ import annotations

from collections import defaultdict

from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QApplication,
    QHeaderView,
    QLineEdit,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from ninjalooter import config
from ninjalooter.app_signals import signals
from ninjalooter.ui.theme import semantic

_POSKY = "Plane of Sky"
_UNKNOWN = "Unknown"


def _zone_sort_key(zone_name: str) -> tuple:
    """Sort zones: Plane of Sky first, Unknown last, rest alphabetical."""
    if zone_name == _POSKY:
        return (0, "")
    if zone_name == _UNKNOWN:
        return (2, "")
    return (1, zone_name)


class KillTimesFrame(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)

        self._filter_edit = QLineEdit(self)
        self._filter_edit.setPlaceholderText("Filter by mob name\u2026")
        self._filter_edit.setClearButtonEnabled(True)
        self._filter_edit.textChanged.connect(self._refresh)
        layout.addWidget(self._filter_edit)

        self._tree = QTreeView(self)
        self._tree.setAlternatingRowColors(False)
        self._tree.setRootIsDecorated(True)
        self._tree.setItemsExpandable(True)
        self._tree.setAnimated(True)
        self._tree.setHeaderHidden(False)

        self._tree_model = QStandardItemModel(self)
        self._tree_model.setHorizontalHeaderLabels(["Time / Zone", "Mob"])
        self._tree.setModel(self._tree_model)

        header = self._tree.header()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header_font = header.font()
        header_font.setPointSize(header_font.pointSize() + 1)
        header.setFont(header_font)

        layout.addWidget(self._tree)

        signals.kill.connect(self._on_kill)
        signals.app_clear.connect(self._on_app_clear)
        signals.app_reload.connect(self._on_app_reload)

        app = QApplication.instance()
        if app:
            app.paletteChanged.connect(self._refresh)

        self._refresh()

    # ── helpers ────────────────────────────────────────────────────────────

    @staticmethod
    def _make_group_item(label: str) -> list[QStandardItem]:
        item = QStandardItem(label)
        item.setEditable(False)
        item.setBackground(semantic.group_header)
        font = item.font()
        font.setBold(True)
        item.setFont(font)
        placeholder = QStandardItem("")
        placeholder.setEditable(False)
        placeholder.setBackground(semantic.group_header)
        return [item, placeholder]

    @staticmethod
    def _make_mob_row(kt, bg) -> list[QStandardItem]:
        time_item = QStandardItem(str(kt.time) if kt.time else "")
        time_item.setEditable(False)
        time_item.setBackground(bg)
        mob_item = QStandardItem(kt.name or "")
        mob_item.setEditable(False)
        mob_item.setBackground(bg)
        return [time_item, mob_item]

    @staticmethod
    def _append_mob_rows(parent_item: QStandardItem, timers: list) -> None:
        for i, kt in enumerate(timers):
            bg = semantic.alt_row if i % 2 == 1 else semantic.base_row
            parent_item.appendRow(KillTimesFrame._make_mob_row(kt, bg))

    # ── refresh ───────────────────────────────────────────────────────────

    def _refresh(self, _filter_text=None):
        self._tree_model.removeRows(0, self._tree_model.rowCount())
        filter_text = self._filter_edit.text().strip().lower()

        timers = config.KILL_TIMERS
        if filter_text:
            timers = [
                kt for kt in timers
                if filter_text in (kt.name or "").lower()
                or filter_text in kt.effective_zone().lower()
            ]

        by_zone: dict[str, list] = defaultdict(list)
        for kt in timers:
            by_zone[kt.effective_zone()].append(kt)

        for zone_name in sorted(by_zone, key=_zone_sort_key):
            zone_timers = by_zone[zone_name]
            zone_row = self._make_group_item(zone_name)
            zone_item = zone_row[0]

            if zone_name == _POSKY:
                by_island: dict[str, list] = defaultdict(list)
                for kt in zone_timers:
                    by_island[kt.island()].append(kt)
                for island_key in sorted(by_island):
                    island_timers = by_island[island_key]
                    island_row = self._make_group_item(f"Island {island_key}")
                    island_item = island_row[0]
                    self._append_mob_rows(island_item, island_timers)
                    zone_item.appendRow(island_row)
            else:
                self._append_mob_rows(zone_item, zone_timers)

            self._tree_model.appendRow(zone_row)

        self._tree.expandAll()

    def _on_kill(self):
        self._refresh()

    def _on_app_clear(self):
        self._tree_model.removeRows(0, self._tree_model.rowCount())

    def _on_app_reload(self):
        self._refresh()
