from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ninjalooter import config
from ninjalooter.app_signals import signals
from ninjalooter.models import Player
from ninjalooter.raid_overview import (
    GUILDLESS_LABEL,
    group_players_by_class,
    guilds_in_snapshot,
    total_filtered_count,
)
from ninjalooter.ui.table_model import ColumnDefn, ObjectTableView

COLUMNS = 3
    """A single class panel: header label, compact table, and watermark for empty."""

    TABLE_ROWS = 6  # Fixed row count so all panels are uniform height

    def __init__(self, pclass: str, players: list[Player], total_filtered: int, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        shown = len(players)
        header = QLabel(f"<b>{pclass} ({shown} / {total_filtered})</b>")
        layout.addWidget(header)

        self._table = ObjectTableView(
            columns=[
                ColumnDefn("Player", "name", width=90),
                ColumnDefn("", "level", width=30),
                ColumnDefn("Guild", "guild", width=90),
            ],
            parent=self,
            sortable=True,
            single_select=True,
        )
        row_h = self._table.verticalHeader().defaultSectionSize()
        header_h = self._table.horizontalHeader().height()
        fixed_h = header_h + row_h * self.TABLE_ROWS + 4

        if players:
            self._table.set_objects(sorted(players, key=lambda p: p.name))
            self._table.setFixedHeight(fixed_h)
            layout.addWidget(self._table)
        else:
            self._table.hide()
            watermark = QLabel(f"No {pclass}s" if not pclass.endswith("s") else f"No {pclass}")
            watermark.setAlignment(Qt.AlignmentFlag.AlignCenter)
            watermark.setStyleSheet("font-size: 24px; font-weight: bold; color: rgba(180, 180, 180, 120);")
            watermark.setFixedHeight(fixed_h)
            layout.addWidget(watermark)


class RaidOverviewFrame(QScrollArea):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWidgetResizable(True)

        self._guild_checkboxes: dict[str, QCheckBox] = {}
        self._snapshot: dict[str, Player] = {}

        self._container = QWidget()
        self._root = QVBoxLayout(self._container)
        self._root.setContentsMargins(6, 6, 6, 6)
        self._root.setSpacing(6)

        # Filter row
        self._filter_row = QHBoxLayout()
        self._filter_row.setContentsMargins(0, 0, 0, 0)
        self._root.addLayout(self._filter_row)

        # Grid for class panels
        self._grid_container = QWidget()
        self._grid = QGridLayout(self._grid_container)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setSpacing(6)
        self._root.addWidget(self._grid_container)
        self._root.addStretch()

        self.setWidget(self._container)

        signals.show_raid_overview.connect(self._on_show_raid_overview)
        signals.who_end.connect(self._on_who_end)
        signals.app_clear.connect(self._on_app_clear)

    def _rebuild(self, snapshot: dict[str, Player]):
        self._snapshot = snapshot
        self._rebuild_filter_checkboxes()
        self._rebuild_grid()

    def _rebuild_filter_checkboxes(self):
        for cb in self._guild_checkboxes.values():
            self._filter_row.removeWidget(cb)
            cb.deleteLater()
        self._guild_checkboxes.clear()

        # Clear existing filter row items
        while self._filter_row.count():
            item = self._filter_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        guilds = guilds_in_snapshot(self._snapshot)

        for guild in sorted(guilds):
            cb = QCheckBox(guild)
            cached = config.RAID_OVERVIEW_GUILDS_ENABLED_CACHE.get(guild, True)
            cb.setChecked(cached)
            cb.stateChanged.connect(self._on_filter_changed)
            self._guild_checkboxes[guild] = cb
            self._filter_row.addWidget(cb)
        self._filter_row.addStretch()

    def _enabled_guilds(self) -> set[str]:
        enabled: set[str] = set()
        for guild, cb in self._guild_checkboxes.items():
            if cb.isChecked():
                enabled.add(guild)
        return enabled

    def _rebuild_grid(self):
        # Clear existing grid
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        enabled_guilds = self._enabled_guilds()
        by_class = group_players_by_class(self._snapshot, enabled_guilds)
        total_filtered = total_filtered_count(by_class)

        all_classes = list(config.OVERVIEW_CLASS_ORDER)
        remaining = set(by_class.keys()) - set(all_classes)
        all_classes.extend(sorted(remaining))

        for i, pclass in enumerate(all_classes):
            players = by_class.get(pclass, [])
            panel = _ClassPanel(pclass, players, total_filtered, self._grid_container)
            row = i // COLUMNS
            col = i % COLUMNS
            self._grid.addWidget(panel, row, col)

    def _clear(self):
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for cb in self._guild_checkboxes.values():
            self._filter_row.removeWidget(cb)
            cb.deleteLater()
        self._guild_checkboxes.clear()

        self._snapshot = {}

    # ---- signal slots ----

    def _on_show_raid_overview(self, wholog):
        self._rebuild(dict(wholog.log) if wholog and wholog.log else {})

    def _on_who_end(self):
        self._rebuild(dict(config.LAST_WHO_SNAPSHOT))

    def _on_app_clear(self):
        self._clear()

    def _on_filter_changed(self):
        for guild, cb in self._guild_checkboxes.items():
            config.RAID_OVERVIEW_GUILDS_ENABLED_CACHE[guild] = cb.isChecked()
        self._rebuild_grid()
