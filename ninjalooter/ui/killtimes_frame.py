from __future__ import annotations

from collections import defaultdict

from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QApplication, QHeaderView, QTreeView, QVBoxLayout, QWidget

from ninjalooter import config
from ninjalooter.app_signals import signals
from ninjalooter.ui.theme import semantic


class KillTimesFrame(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)

        self._tree = QTreeView(self)
        self._tree.setAlternatingRowColors(False)
        self._tree.setRootIsDecorated(True)
        self._tree.setItemsExpandable(True)
        self._tree.setAnimated(True)
        self._tree.setHeaderHidden(False)

        self._tree_model = QStandardItemModel(self)
        self._tree_model.setHorizontalHeaderLabels(["Time / Island", "Mob"])
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

    def _refresh(self):
        self._tree_model.removeRows(0, self._tree_model.rowCount())

        by_island: dict[str, list] = defaultdict(list)
        for kt in config.KILL_TIMERS:
            by_island[kt.island()].append(kt)

        for island_key in sorted(by_island.keys(), key=lambda x: (x == "Other", x)):
            timers = by_island[island_key]
            island_name = f"Island {island_key}" if island_key != "Other" else "Other"

            group_item = QStandardItem(island_name)
            group_item.setEditable(False)
            group_item.setBackground(semantic.group_header)
            font = group_item.font()
            font.setBold(True)
            group_item.setFont(font)

            placeholder = QStandardItem("")
            placeholder.setEditable(False)
            placeholder.setBackground(semantic.group_header)

            for i, kt in enumerate(timers):
                bg = semantic.alt_row if i % 2 == 1 else semantic.base_row
                time_item = QStandardItem(str(kt.time) if kt.time else "")
                time_item.setEditable(False)
                time_item.setBackground(bg)
                mob_item = QStandardItem(kt.name or "")
                mob_item.setEditable(False)
                mob_item.setBackground(bg)
                group_item.appendRow([time_item, mob_item])

            self._tree_model.appendRow([group_item, placeholder])

        self._tree.expandAll()

    def _on_kill(self):
        self._refresh()

    def _on_app_clear(self):
        self._tree_model.removeRows(0, self._tree_model.rowCount())

    def _on_app_reload(self):
        self._refresh()
