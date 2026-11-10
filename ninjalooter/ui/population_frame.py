from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ninjalooter import config, utils
from ninjalooter.app_signals import signals
from ninjalooter.models import PopulationPreview
from ninjalooter.ui.table_model import ColumnDefn, ObjectTableView


class PopulationFrame(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self._alliance_spinners: dict[str, QSpinBox] = {}
        self._pop_overrides: dict[str, int] = {}
        self._roll_source = None

        root = QHBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)

        # --- Left: player table ---
        left = QVBoxLayout()

        pop_label = QLabel("Population Count")
        pop_font = pop_label.font()
        pop_font.setBold(True)
        pop_label.setFont(pop_font)
        left.addWidget(pop_label)

        source_row = QHBoxLayout()
        source_caption = QLabel("Source")
        source_caption.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._source_combo = QComboBox()
        self._source_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self._source_combo.setMinimumContentsLength(18)
        self._source_combo.setToolTip("Choose which /who the population roll counts.")
        self._source_combo.currentIndexChanged.connect(self._on_source_changed)
        source_row.addWidget(source_caption)
        source_row.addWidget(self._source_combo, stretch=1)
        left.addLayout(source_row)

        self._newer_label = QLabel("Newer /who available")
        self._newer_label.setVisible(False)
        left.addWidget(self._newer_label)

        self._player_table = ObjectTableView(
            columns=[
                ColumnDefn("Name", "name", width=130),
                ColumnDefn("Class", "pclass", width=100),
                ColumnDefn("Level", "level", width=50),
                ColumnDefn("Guild", "guild", width=130),
            ],
            parent=self,
            sortable=True,
            single_select=True,
        )
        left.addWidget(self._player_table)
        root.addLayout(left, stretch=3)

        # --- Right: adjustments + preview ---
        right = QVBoxLayout()
        right.setContentsMargins(6, 0, 0, 0)
        root.addLayout(right, stretch=1)

        adj_label = QLabel("Adjustments")
        adj_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        font = adj_label.font()
        font.setBold(True)
        adj_label.setFont(font)
        right.addWidget(adj_label)

        self._spinner_host = QWidget()
        self._spinner_layout = QVBoxLayout(self._spinner_host)
        self._spinner_layout.setContentsMargins(0, 0, 0, 0)
        self._spinner_layout.setSpacing(2)
        right.addWidget(self._spinner_host)

        self._preview_table = ObjectTableView(
            columns=[
                ColumnDefn("Alliance", "alliance", width=120),
                ColumnDefn("Pop", "population", width=60),
            ],
            parent=self,
            sortable=False,
            single_select=True,
        )
        self._preview_table.setMaximumHeight(180)
        right.addWidget(self._preview_table, stretch=1)

        btn_row1 = QHBoxLayout()
        btn_half = QPushButton("1/2")
        btn_zero = QPushButton("Zero")
        btn_reset = QPushButton("Reset")
        btn_half.clicked.connect(self._halve_extras)
        btn_zero.clicked.connect(self._zero_extras)
        btn_reset.clicked.connect(self._reset_extras)
        btn_row1.addWidget(btn_half)
        btn_row1.addWidget(btn_zero)
        btn_row1.addWidget(btn_reset)
        right.addLayout(btn_row1)

        btn_copy_pop = QPushButton("Copy Populations")
        btn_copy_roll = QPushButton("Copy Roll Text")
        btn_copy_pop.clicked.connect(self._copy_populations)
        btn_copy_roll.clicked.connect(self._copy_roll_text)
        right.addWidget(btn_copy_pop)
        right.addWidget(btn_copy_roll)

        right.addStretch()

        # --- Signals ---
        signals.who_end.connect(self._on_who_end)
        signals.who_history.connect(self._on_who_history)
        signals.app_clear.connect(self._on_app_clear)
        signals.app_reload.connect(self._on_app_reload)
        signals.use_for_pop_roll.connect(self._on_use_for_pop_roll)
        signals.alliances_changed.connect(self._rebuild_spinners)

        self._rebuild_spinners()
        self._refresh_player_table()
        self._update_preview()
        self._rebuild_source_combo()

    # ---- helpers ----

    def _rebuild_spinners(self):
        previous = {name: spinner.value() for name, spinner in self._alliance_spinners.items()}
        while self._spinner_layout.count():
            item = self._spinner_layout.takeAt(0)
            layout = item.layout()
            if layout is None:
                continue
            while layout.count():
                child = layout.takeAt(0)
                widget = child.widget()
                if widget is not None:
                    widget.deleteLater()
            layout.deleteLater()
        self._alliance_spinners = {}
        for name in list(self._pop_overrides):
            if name not in config.ALLIANCES:
                del self._pop_overrides[name]
        for alliance in config.ALLIANCES:
            row = QHBoxLayout()
            label = QLabel(alliance)
            label.setMinimumWidth(80)
            label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            label_font = label.font()
            label_font.setBold(True)
            label.setFont(label_font)
            spinner = QSpinBox()
            spinner.setRange(-999, 999)
            spinner.blockSignals(True)
            spinner.setValue(previous.get(alliance, 0))
            spinner.blockSignals(False)
            spinner.valueChanged.connect(lambda _val, a=alliance: self._on_spinner_changed(a))
            self._alliance_spinners[alliance] = spinner
            row.addWidget(label)
            row.addWidget(spinner)
            self._spinner_layout.addLayout(row)
        if hasattr(self, "_preview_table"):
            self._update_preview()

    def _extras(self) -> dict[str, int]:
        return {
            alliance: spinner.value() for alliance, spinner in self._alliance_spinners.items() if spinner.value() != 0
        }

    def _on_spinner_changed(self, alliance: str):
        self._pop_overrides.pop(alliance, None)
        self._update_preview()

    def _is_recorded(self, wholog) -> bool:
        return any(entry is wholog for entry in config.ATTENDANCE_LOGS)

    def _showing_recorded_tick(self) -> bool:
        return self._roll_source is not None and self._is_recorded(self._roll_source)

    def _player_source(self) -> dict:
        if self._showing_recorded_tick():
            return self._roll_source.log or {}
        return config.LAST_WHO_SNAPSHOT

    def _tick_label(self, wholog) -> str:
        parts = [wholog.eqtime()]
        if wholog.raidtick:
            parts.append("RaidTick")
        if wholog.tick_name:
            parts.append(wholog.tick_name)
        if wholog.zone:
            parts.append(wholog.zone)
        return " · ".join(parts)

    def _wholog_for_combo_index(self, index: int):
        if index <= 0:
            return None
        logs = config.ATTENDANCE_LOGS
        source_index = len(logs) - index
        if source_index < 0 or source_index >= len(logs):
            return None
        return logs[source_index]

    def _combo_index_for_source(self) -> int:
        wholog = self._roll_source
        if wholog is None:
            return 0
        for offset, entry in enumerate(reversed(config.ATTENDANCE_LOGS)):
            if entry is wholog:
                return offset + 1
        return 0

    def _has_newer_who(self) -> bool:
        if not self._showing_recorded_tick() or not config.ATTENDANCE_LOGS:
            return False
        return config.ATTENDANCE_LOGS[-1] is not self._roll_source

    def _rebuild_source_combo(self):
        self._source_combo.blockSignals(True)
        self._source_combo.clear()
        self._source_combo.addItem("Latest /who")
        for wholog in reversed(config.ATTENDANCE_LOGS):
            self._source_combo.addItem(self._tick_label(wholog))
        self._source_combo.setCurrentIndex(self._combo_index_for_source())
        self._source_combo.setToolTip(self._source_combo.currentText())
        self._source_combo.blockSignals(False)
        self._newer_label.setVisible(self._has_newer_who())

    def _ensure_source(self) -> bool:
        """Drop a pinned tick that is no longer in the attendance list."""
        if self._roll_source is not None and not self._is_recorded(self._roll_source):
            self._roll_source = None
            return True
        return False

    def _reload_from_source(self, reset_adjustments: bool):
        dropped = self._ensure_source()
        self._refresh_player_table()
        if reset_adjustments or dropped:
            self._pop_overrides.clear()
            self._reset_extras()
        else:
            self._update_preview()
        self._rebuild_source_combo()

    def _refresh_player_table(self):
        players = sorted(
            self._player_source().values(),
            key=lambda p: (p.guild or "", p.name),
        )
        self._player_table.set_objects(players)

    def _update_preview(self):
        pops = utils.get_pop_numbers(source=self._player_source(), extras=self._extras())
        pops.update(self._pop_overrides)
        previews = [PopulationPreview(a, p) for a, p in pops.items() if p > 0 or a in self._pop_overrides]
        self._preview_table.set_objects(previews)

    def _effective_pops(self) -> dict[str, int]:
        """Final population numbers with overrides applied."""
        pops = utils.get_pop_numbers(source=self._player_source(), extras=self._extras())
        pops.update(self._pop_overrides)
        return pops

    def _get_selected_alliance(self) -> str | None:
        obj = self._preview_table.get_selected_object()
        if obj:
            return obj.alliance
        return None

    # ---- button handlers ----

    def _halve_extras(self):
        alliance = self._get_selected_alliance()
        if not alliance:
            return
        current_pops = self._effective_pops()
        current_pop = current_pops.get(alliance, 0)
        self._pop_overrides[alliance] = current_pop // 2
        self._update_preview()

    def _zero_extras(self):
        alliance = self._get_selected_alliance()
        if not alliance:
            return
        self._pop_overrides[alliance] = 0
        self._update_preview()

    def _reset_extras(self):
        self._pop_overrides.clear()
        for spinner in self._alliance_spinners.values():
            spinner.setValue(0)
        self._update_preview()

    def _copy_populations(self):
        pops = self._effective_pops()
        lines = [f"{alliance}: {pop}" for alliance, pop in pops.items() if pop > 0]
        utils.to_clipboard("\n".join(lines))

    def _copy_roll_text(self):
        pops = self._effective_pops()
        if set(pops.values()) == {0}:
            return
        roll_text, rand_text = utils.generate_pop_roll(source=self._player_source(), extras=self._extras())
        if roll_text:
            utils.to_clipboard(f"{roll_text}\n{rand_text}")

    # ---- signal slots ----

    def _on_who_end(self):
        if self._showing_recorded_tick():
            self._rebuild_source_combo()
            return
        self._roll_source = None
        self._reload_from_source(reset_adjustments=True)

    def _on_who_history(self):
        self._rebuild_source_combo()

    def _on_source_changed(self, index: int):
        if index < 0:
            return
        wholog = self._wholog_for_combo_index(index)
        if wholog is self._roll_source:
            return
        self._roll_source = wholog
        self._reload_from_source(reset_adjustments=True)

    def _on_app_clear(self):
        self._roll_source = None
        config.LAST_WHO_SNAPSHOT.clear()
        self._reload_from_source(reset_adjustments=True)

    def _on_app_reload(self):
        self._reload_from_source(reset_adjustments=False)

    def _on_use_for_pop_roll(self, wholog):
        if wholog is None:
            return
        self._roll_source = wholog
        self._reload_from_source(reset_adjustments=True)

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self._reload_from_source(reset_adjustments=False)
