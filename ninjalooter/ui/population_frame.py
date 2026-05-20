from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ninjalooter import config, utils
from ninjalooter.app_signals import signals
from ninjalooter.models import Player, PopulationPreview
from ninjalooter.ui.table_model import ColumnDefn, ObjectTableView


class PopulationFrame(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self._alliance_spinners: dict[str, QSpinBox] = {}
        self._pop_overrides: dict[str, int] = {}

        root = QHBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)

        # --- Left: player table ---
        left = QVBoxLayout()

        pop_label = QLabel("Population Count")
        pop_font = pop_label.font()
        pop_font.setBold(True)
        pop_label.setFont(pop_font)
        left.addWidget(pop_label)

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

        for alliance in config.ALLIANCES:
            row = QHBoxLayout()
            lbl = QLabel(alliance)
            lbl.setMinimumWidth(80)
            lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            lbl_font = lbl.font()
            lbl_font.setBold(True)
            lbl.setFont(lbl_font)
            spinner = QSpinBox()
            spinner.setRange(-999, 999)
            spinner.setValue(0)
            spinner.valueChanged.connect(lambda _val, a=alliance: self._on_spinner_changed(a))
            self._alliance_spinners[alliance] = spinner
            row.addWidget(lbl)
            row.addWidget(spinner)
            right.addLayout(row)

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
        signals.who.connect(self._on_who)
        signals.clear_who.connect(self._on_clear_who)
        signals.who_end.connect(self._on_who_end)
        signals.app_clear.connect(self._on_app_clear)
        signals.app_reload.connect(self._on_app_reload)

        self._refresh_player_table()
        self._update_preview()

    # ---- helpers ----

    def _extras(self) -> dict[str, int]:
        return {
            alliance: spinner.value() for alliance, spinner in self._alliance_spinners.items() if spinner.value() != 0
        }

    def _on_spinner_changed(self, alliance: str):
        self._pop_overrides.pop(alliance, None)
        self._update_preview()

    def _refresh_player_table(self):
        players = sorted(
            config.LAST_WHO_SNAPSHOT.values(),
            key=lambda p: (p.guild or "", p.name),
        )
        self._player_table.set_objects(players)

    def _update_preview(self):
        pops = utils.get_pop_numbers(extras=self._extras())
        pops.update(self._pop_overrides)
        previews = [PopulationPreview(a, p) for a, p in pops.items() if p > 0 or a in self._pop_overrides]
        self._preview_table.set_objects(previews)

    def _effective_pops(self) -> dict[str, int]:
        """Final population numbers with overrides applied."""
        pops = utils.get_pop_numbers(extras=self._extras())
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
        roll_text, rand_text = utils.generate_pop_roll(extras=self._extras())
        if roll_text:
            utils.to_clipboard(f"{roll_text}\n{rand_text}")

    # ---- signal slots ----

    def _on_who(self, name: str, pclass: str, level: int, guild: str):
        player = Player(name, pclass, level, guild)
        config.LAST_WHO_SNAPSHOT[name] = player
        self._player_table.object_model.add_object(player)

    def _on_clear_who(self):
        self._player_table.set_objects([])

    def _on_who_end(self):
        self._refresh_player_table()
        self._pop_overrides.clear()
        self._reset_extras()

    def _on_app_clear(self):
        config.LAST_WHO_SNAPSHOT.clear()
        self._player_table.set_objects([])
        self._pop_overrides.clear()
        self._reset_extras()

    def _on_app_reload(self):
        self._refresh_player_table()
        self._update_preview()
