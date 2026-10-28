from __future__ import annotations

from collections import defaultdict

from PySide6.QtCore import QModelIndex, QTimer
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from ninjalooter import config, utils
from ninjalooter.app_signals import signals
from ninjalooter.ui.theme import semantic

_POSKY = "Plane of Sky"
_UNKNOWN = "Unknown"
_FILTER_MAX_WIDTH = 400
_KILL_REFRESH_MS = 400


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

        toolbar = QHBoxLayout()
        toolbar.setSpacing(12)

        self._filter_edit = QLineEdit(self)
        self._filter_edit.setPlaceholderText("Filter by mob name\u2026")
        self._filter_edit.setClearButtonEnabled(True)
        self._filter_edit.setMaximumWidth(_FILTER_MAX_WIDTH)
        self._filter_edit.textChanged.connect(self._refresh)
        toolbar.addWidget(self._filter_edit)
        toolbar.addStretch()

        self._clear_btn = QPushButton("Clear Kill Timers", self)
        self._clear_btn.clicked.connect(self._on_clear_kill_timers)
        toolbar.addWidget(self._clear_btn)
        layout.addLayout(toolbar)

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

        self._restoring_expansion = False
        self._tree.expanded.connect(self._on_section_expanded)
        self._tree.collapsed.connect(self._on_section_collapsed)

        self._kill_refresh = QTimer(self)
        self._kill_refresh.setSingleShot(True)
        self._kill_refresh.setInterval(_KILL_REFRESH_MS)
        self._kill_refresh.timeout.connect(self._refresh)

        signals.kill.connect(self._on_kill)
        signals.app_clear.connect(self._on_app_clear)
        signals.app_reload.connect(self._on_app_reload)

        app = QApplication.instance()
        if app:
            app.paletteChanged.connect(self._refresh)

        self._refresh()

    def _on_clear_kill_timers(self):
        reply = QMessageBox.question(
            self,
            "Confirm Clear",
            "Are you sure you want to clear all kill timer data?",
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
        )
        if reply != QMessageBox.StandardButton.Ok:
            return
        self._kill_refresh.stop()
        config.KILL_TIMERS.clear()
        self._refresh()
        utils.store_state()

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

    def _section_cache_key(self, index: QModelIndex) -> str | None:
        item = self._tree_model.itemFromIndex(index)
        if item is None or not item.hasChildren():
            return None
        text = item.text()
        parent = item.parent()
        if parent is not None:
            return f"{parent.text()}/{text}"
        return text

    def _set_section_expanded(self, key: str, expanded: bool) -> None:
        config.KILL_TIMER_SECTIONS_EXPANDED_CACHE[key] = expanded
        utils.store_state()

    def _on_section_expanded(self, index: QModelIndex) -> None:
        if self._restoring_expansion:
            return
        key = self._section_cache_key(index)
        if key is not None:
            self._set_section_expanded(key, True)

    def _on_section_collapsed(self, index: QModelIndex) -> None:
        if self._restoring_expansion:
            return
        key = self._section_cache_key(index)
        if key is not None:
            self._set_section_expanded(key, False)

    def _apply_expansion_state(self) -> None:
        cache = config.KILL_TIMER_SECTIONS_EXPANDED_CACHE
        self._restoring_expansion = True
        try:
            for row in range(self._tree_model.rowCount()):
                zone_item = self._tree_model.item(row, 0)
                zone_index = self._tree_model.indexFromItem(zone_item)
                if cache.get(zone_item.text(), True):
                    self._tree.expand(zone_index)
                else:
                    self._tree.collapse(zone_index)
                for child_row in range(zone_item.rowCount()):
                    child = zone_item.child(child_row, 0)
                    if child is None or not child.hasChildren():
                        continue
                    child_key = f"{zone_item.text()}/{child.text()}"
                    child_index = self._tree_model.indexFromItem(child)
                    if cache.get(child_key, True):
                        self._tree.expand(child_index)
                    else:
                        self._tree.collapse(child_index)
        finally:
            self._restoring_expansion = False

    # ── refresh ───────────────────────────────────────────────────────────

    def _refresh(self, _filter_text=None):
        self._tree_model.removeRows(0, self._tree_model.rowCount())
        filter_text = self._filter_edit.text().strip().lower()

        timers = config.KILL_TIMERS
        if filter_text:
            timers = [
                kt
                for kt in timers
                if filter_text in (kt.name or "").lower() or filter_text in kt.effective_zone().lower()
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

        self._apply_expansion_state()

    def _find_group(self, parent, label: str):
        count = self._tree_model.rowCount() if parent is None else parent.rowCount()
        for row in range(count):
            item = self._tree_model.item(row, 0) if parent is None else parent.child(row, 0)
            if item is not None and item.text() == label and item.font().bold():
                return item
        return None

    def _append_kill(self, kt) -> bool:
        """Add one mob under an existing zone. Return False when the tree must be rebuilt."""
        zone_name = kt.effective_zone()
        zone_item = self._find_group(None, zone_name)
        if zone_item is None:
            return False
        parent = zone_item
        if zone_name == _POSKY:
            parent = self._find_group(zone_item, f"Island {kt.island()}")
            if parent is None:
                return False
        bg = semantic.alt_row if parent.rowCount() % 2 == 1 else semantic.base_row
        parent.appendRow(self._make_mob_row(kt, bg))
        return True

    def _on_kill(self, kt=None):
        if self._filter_edit.text().strip():
            if not self._kill_refresh.isActive():
                self._kill_refresh.start()
            return
        if kt is not None and self._append_kill(kt):
            return
        self._kill_refresh.stop()
        self._refresh()

    def _on_app_clear(self):
        self._kill_refresh.stop()
        self._tree_model.removeRows(0, self._tree_model.rowCount())

    def _on_app_reload(self):
        self._kill_refresh.stop()
        self._refresh()
