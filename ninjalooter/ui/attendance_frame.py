import copy
from collections import defaultdict

import dateutil.parser
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QShowEvent, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from ninjalooter import config, models, utils
from ninjalooter.app_signals import signals
from ninjalooter.raidgroups import GroupBuilder
from ninjalooter.ui.table_model import ColumnDefn, ObjectTableView
from ninjalooter.ui.theme import apply_windows_window_frame, semantic


class _GroupBuilderThread(QThread):
    finished_signal = Signal(object)

    def __init__(self, players, parent=None):
        super().__init__(parent)
        self._players = players

    def run(self):
        builder = GroupBuilder()
        builder.build_groups(self._players)
        self.finished_signal.emit(builder.raid)


class AttendanceFrame(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        splitter = QSplitter(Qt.Orientation.Vertical, self)

        # ── Pane 1: Attendance / Raidtick List ──
        pane1 = QWidget()
        pane1_layout = QVBoxLayout(pane1)
        pane1_layout.setContentsMargins(10, 10, 10, 0)

        attendance_row = QHBoxLayout()
        pane1_layout.addLayout(attendance_row)

        self.attendance_list = ObjectTableView(
            columns=[
                ColumnDefn("Time", "time", width=115),
                ColumnDefn("Name", lambda x: x.tick_name or "", width=112),
                ColumnDefn("RT", lambda x: x.raidtick_display(), width=25),
                ColumnDefn("Zone", lambda x: x.zone or "", width=100),
                ColumnDefn("Populations", lambda x: x.populations() or "", width=300),
            ],
            parent=self,
            single_select=True,
            sortable=True,
        )
        self.attendance_list.setToolTip("Double-click an attendance record to edit it in detail.")
        self.attendance_list.doubleClicked.connect(self._show_attendance_detail)
        self.attendance_list.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        attendance_row.addWidget(self.attendance_list, 1)

        attendance_btn_col = QVBoxLayout()
        attendance_btn_col.setContentsMargins(0, 0, 0, 0)
        attendance_btn_col.setSpacing(2)
        btn_wrapper = QWidget()
        btn_wrapper.setFixedWidth(130)
        btn_wrapper.setLayout(attendance_btn_col)
        attendance_row.addWidget(btn_wrapper)

        self.raidtick_only_cb = QCheckBox("Show RaidTicks Only")
        self.raidtick_only_cb.setChecked(config.SHOW_RAIDTICK_ONLY)
        self.raidtick_only_cb.stateChanged.connect(self._on_raidtick_only)
        attendance_btn_col.addWidget(self.raidtick_only_cb)

        btn_toggle_rt = QPushButton("Toggle RaidTick")
        btn_toggle_rt.clicked.connect(self._on_mark_raidtick)
        attendance_btn_col.addWidget(btn_toggle_rt)

        btn_copy_tick = QPushButton("Copy Tick")
        btn_copy_tick.clicked.connect(self._on_export_tick)
        attendance_btn_col.addWidget(btn_copy_tick)

        btn_calc_groups = QPushButton("Calculate Raid Groups")
        btn_calc_groups.clicked.connect(self._on_calc_raid_groups)
        attendance_btn_col.addWidget(btn_calc_groups)

        btn_raid_overview = QPushButton("Show Raid Overview")
        btn_raid_overview.clicked.connect(self._on_show_raid_overview)
        attendance_btn_col.addWidget(btn_raid_overview)

        btn_delete_tick = QPushButton("Delete Tick")
        btn_delete_tick.clicked.connect(self._on_delete_tick)
        attendance_btn_col.addWidget(btn_delete_tick)

        attendance_btn_col.addStretch()

        # ── Pane 2: Creditt Log ──
        pane2 = QWidget()
        pane2_layout = QVBoxLayout(pane2)
        pane2_layout.setContentsMargins(10, 10, 10, 0)

        creditt_row = QHBoxLayout()
        pane2_layout.addLayout(creditt_row)

        self.creditt_list = ObjectTableView(
            columns=[
                ColumnDefn("Time", "time", width=160),
                ColumnDefn("From", "user", width=120),
                ColumnDefn("Message", "message", width=350),
                ColumnDefn("\u2713", lambda x: "\u2713" if x.applied else "", width=30),
            ],
            parent=self,
            single_select=True,
            empty_text="No messages received",
        )
        creditt_row.addWidget(self.creditt_list, 1)

        creditt_btn_col = QVBoxLayout()
        creditt_btn_col.setContentsMargins(0, 0, 0, 0)
        creditt_btn_col.setSpacing(2)
        btn_wrapper2 = QWidget()
        btn_wrapper2.setFixedWidth(130)
        btn_wrapper2.setLayout(creditt_btn_col)
        creditt_row.addWidget(btn_wrapper2)
        btn_apply_creditt = QPushButton("Apply Creditt")
        btn_apply_creditt.clicked.connect(self._on_apply_creditt)
        creditt_btn_col.addWidget(btn_apply_creditt)
        btn_ignore_creditt = QPushButton("Ignore Creditt")
        btn_ignore_creditt.clicked.connect(self._on_ignore_creditt)
        creditt_btn_col.addWidget(btn_ignore_creditt)
        creditt_btn_col.addStretch()

        # ── Pane 3: Gratss Log ──
        pane3 = QWidget()
        pane3_layout = QVBoxLayout(pane3)
        pane3_layout.setContentsMargins(10, 10, 10, 10)

        gratss_row = QHBoxLayout()
        pane3_layout.addLayout(gratss_row)

        self.gratss_list = ObjectTableView(
            columns=[
                ColumnDefn("Time", "time", width=160),
                ColumnDefn("From", "user", width=120),
                ColumnDefn("Message", "message", width=350),
            ],
            parent=self,
            single_select=True,
            empty_text="No messages received",
        )
        gratss_row.addWidget(self.gratss_list, 1)

        gratss_btn_col = QVBoxLayout()
        gratss_btn_col.setContentsMargins(0, 0, 0, 0)
        gratss_btn_col.setSpacing(2)
        btn_wrapper3 = QWidget()
        btn_wrapper3.setFixedWidth(130)
        btn_wrapper3.setLayout(gratss_btn_col)
        gratss_row.addWidget(btn_wrapper3)
        btn_ignore_gratss = QPushButton("Ignore Gratss")
        btn_ignore_gratss.clicked.connect(self._on_ignore_gratss)
        gratss_btn_col.addWidget(btn_ignore_gratss)
        gratss_btn_col.addStretch()

        # ── Assemble splitter ──
        splitter.addWidget(pane1)
        splitter.addWidget(pane2)
        splitter.addWidget(pane3)
        splitter.setChildrenCollapsible(False)
        splitter.setSizes(
            [
                config.CREDITT_SASH_POS,
                config.GRATSS_SASH_POS,
                150,
            ]
        )
        splitter.splitterMoved.connect(self._on_sash_changed)
        self._splitter = splitter

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(splitter)

        # ── Initial data ──
        self.attendance_list.set_objects(config.ATTENDANCE_LOGS)
        self.creditt_list.set_objects(config.CREDITT_LOG)
        self.gratss_list.set_objects(config.GRATSS_LOG)
        if config.SHOW_RAIDTICK_ONLY:
            self._apply_raidtick_filter()

        # ── Connect signals ──
        signals.who_history.connect(self._on_who_history)
        signals.creditt.connect(self._on_creditt)
        signals.gratss.connect(self._on_gratss)
        signals.app_clear.connect(self._on_clear_app)
        signals.app_reload.connect(self._on_reload_app)

    # ── Splitter persistence ──

    def _on_sash_changed(self, _pos, _index):
        sizes = self._splitter.sizes()
        if len(sizes) >= 2:
            config.CREDITT_SASH_POS = sizes[0]
            config.GRATSS_SASH_POS = sizes[1]

    # ── Attendance actions ──

    def _apply_raidtick_filter(self):
        if config.SHOW_RAIDTICK_ONLY:
            self.attendance_list.set_filter_func(lambda x: x.raidtick)
        else:
            self.attendance_list.set_filter_func(None)

    def _refresh_attendance(self):
        self.attendance_list.set_objects(config.ATTENDANCE_LOGS)
        self._apply_raidtick_filter()

    def _on_raidtick_only(self):
        config.SHOW_RAIDTICK_ONLY = self.raidtick_only_cb.isChecked()
        config.CONF.set("default", "raidtick_filter", str(config.SHOW_RAIDTICK_ONLY))
        self._refresh_attendance()
        config.write()

    def _on_mark_raidtick(self):
        selected = self.attendance_list.get_selected_object()
        if not selected:
            return
        selected.raidtick = not selected.raidtick
        self._refresh_attendance()
        self.attendance_list.select_object(selected)
        utils.store_state()

    def _on_export_tick(self):
        wholog = self.attendance_list.get_selected_object()
        if wholog is None or not wholog.log:
            return
        tick_lines = utils.parse_tick_for_export(wholog)
        txt = "\n".join(tick_lines) + "\n"
        QApplication.clipboard().setText(txt)

    def _on_calc_raid_groups(self):
        selected = self.attendance_list.get_selected_object()
        if not selected:
            return
        players = list(selected.log.values())
        self._group_thread = _GroupBuilderThread(players)
        self._group_thread.finished_signal.connect(self._on_groups_built)
        self._group_thread.start()
        signals.calc_raid_groups.emit()

    def _on_groups_built(self, raid):
        config.RAID_GROUPS = raid
        signals.calc_raid_groups.emit()

    def _on_show_raid_overview(self):
        selected = self.attendance_list.get_selected_object()
        if selected:
            signals.show_raid_overview.emit(selected)

    def _on_delete_tick(self):
        selected = self.attendance_list.get_selected_object()
        if not selected:
            return
        row = config.ATTENDANCE_LOGS.index(selected)
        config.ATTENDANCE_LOGS.remove(selected)
        self._refresh_attendance()
        # Select the next item (or previous if we deleted the last one)
        if config.ATTENDANCE_LOGS:
            next_row = min(row, len(config.ATTENDANCE_LOGS) - 1)
            self.attendance_list.select_object(config.ATTENDANCE_LOGS[next_row])
        utils.store_state()

    def _show_attendance_detail(self):
        selected = self.attendance_list.get_selected_object()
        if not selected:
            return
        win = AttendanceDetailWindow(
            selected,
            parent=self,
        )
        win.closed.connect(self._refresh_attendance)

    # ── Creditt / Gratss actions ──

    def _on_apply_creditt(self):
        selected = self.creditt_list.get_selected_object()
        if not selected:
            return
        dlg = ApplyCredittDialog(selected, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._refresh_attendance()
            self.creditt_list.set_objects(config.CREDITT_LOG)

    def _on_ignore_creditt(self):
        selected = self.creditt_list.get_selected_object()
        if not selected:
            return
        config.CREDITT_LOG.remove(selected)
        self.creditt_list.set_objects(config.CREDITT_LOG)
        utils.store_state()

    def _on_ignore_gratss(self):
        selected = self.gratss_list.get_selected_object()
        if not selected:
            return
        config.GRATSS_LOG.remove(selected)
        self.gratss_list.set_objects(config.GRATSS_LOG)
        utils.store_state()

    # ── Signal handlers ──

    def _on_who_history(self):
        self._refresh_attendance()

    def _on_creditt(self):
        self.creditt_list.set_objects(config.CREDITT_LOG)

    def _on_gratss(self):
        self.gratss_list.set_objects(config.GRATSS_LOG)

    def _on_clear_app(self):
        config.ATTENDANCE_LOGS.clear()
        config.CREDITT_LOG.clear()
        config.GRATSS_LOG.clear()
        self.attendance_list.set_objects(config.ATTENDANCE_LOGS)
        self.creditt_list.set_objects(config.CREDITT_LOG)
        self.gratss_list.set_objects(config.GRATSS_LOG)

    def _on_reload_app(self):
        self._refresh_attendance()
        self.creditt_list.set_objects(config.CREDITT_LOG)
        self.gratss_list.set_objects(config.GRATSS_LOG)


class AttendanceDetailWindow(QWidget):
    """Detail view for a single attendance / who log entry."""

    closed = Signal()

    def __init__(self, item, parent=None):
        super().__init__(parent, Qt.WindowType.Window)
        self.setWindowTitle(f"Attendance Record: {item.time}")
        self.resize(520, 800)
        self._item = item

        main_layout = QVBoxLayout(self)

        # ── Top button bar ──
        button_row = QHBoxLayout()
        main_layout.addLayout(button_row)

        btn_add = QPushButton("Add Player")
        btn_add.clicked.connect(self._on_add_player)
        button_row.addWidget(btn_add)

        btn_remove = QPushButton("Remove Player")
        btn_remove.clicked.connect(self._on_remove_player)
        button_row.addWidget(btn_remove)

        self._tick_name = QLineEdit()
        self._tick_name.setPlaceholderText(f"{item.zone}?" if item.zone else "Tick Name?")
        self._tick_name.setText(item.tick_name or "")
        self._tick_name.setFixedWidth(140)
        button_row.addWidget(self._tick_name)

        self._raidtick_cb = QCheckBox("RaidTick")
        self._raidtick_cb.setChecked(item.raidtick)
        button_row.addWidget(self._raidtick_cb)

        button_row.addStretch()

        # ── Player tree (grouped by alliance) ──
        self._tree = QTreeView(self)
        self._tree.setAlternatingRowColors(False)
        self._tree.setRootIsDecorated(True)
        self._tree.setItemsExpandable(True)
        self._tree.setAnimated(True)
        self._tree.setSortingEnabled(True)

        self._tree_model = QStandardItemModel(self)
        self._tree_model.setHorizontalHeaderLabels(["Name", "Guild", "Level", "Class"])
        self._tree.setModel(self._tree_model)

        header = self._tree.header()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.resizeSection(0, 160)
        header.resizeSection(1, 100)
        header.resizeSection(2, 50)
        header_font = header.font()
        header_font.setPointSize(header_font.pointSize() + 1)
        header.setFont(header_font)

        main_layout.addWidget(self._tree)

        self._rebuild_tree()

        if config.ALWAYS_ON_TOP:
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        self.show()

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        apply_windows_window_frame(self, dark_mode=config.DARK_MODE)

    def _rebuild_tree(self):
        self._tree_model.removeRows(0, self._tree_model.rowCount())
        players = list(self._item.log.values())

        by_alliance: dict[str, list] = defaultdict(list)
        for p in players:
            alliance = config.ALLIANCE_MAP.get(p.guild, "No Alliance")
            by_alliance[alliance].append(p)

        for alliance_name in sorted(by_alliance.keys()):
            alliance_players = sorted(by_alliance[alliance_name], key=lambda p: p.name)

            group_item = QStandardItem(f"{alliance_name} ({len(alliance_players)})")
            group_item.setEditable(False)
            group_item.setBackground(semantic.group_header)
            font = group_item.font()
            font.setBold(True)
            group_item.setFont(font)

            placeholders = [QStandardItem("") for _ in range(3)]
            for ph in placeholders:
                ph.setEditable(False)
                ph.setBackground(semantic.group_header)

            for i, p in enumerate(alliance_players):
                bg = semantic.alt_row if i % 2 == 1 else semantic.base_row
                name_item = QStandardItem(p.name)
                name_item.setEditable(False)
                name_item.setBackground(bg)
                guild_item = QStandardItem(p.guild or "")
                guild_item.setEditable(False)
                guild_item.setBackground(bg)
                level_item = QStandardItem(str(p.level) if p.level else "")
                level_item.setEditable(False)
                level_item.setBackground(bg)
                class_item = QStandardItem(p.pclass or "")
                class_item.setEditable(False)
                class_item.setBackground(bg)
                group_item.appendRow([name_item, guild_item, level_item, class_item])

            self._tree_model.appendRow([group_item] + placeholders)

        self._tree.expandAll()

    def _on_remove_player(self):
        indexes = self._tree.selectionModel().selectedIndexes()
        if not indexes:
            return
        idx = indexes[0]
        if not idx.parent().isValid():
            return
        name_item = self._tree_model.itemFromIndex(self._tree_model.index(idx.row(), 0, idx.parent()))
        if not name_item:
            return
        player_name = name_item.text()
        self._item.log.pop(player_name, None)
        self._rebuild_tree()
        utils.store_state()

    def _on_add_player(self):
        name, ok = QInputDialog.getText(self, "Add Player", "Player name:")
        if not ok or not name.strip():
            return
        player_name = name.strip().capitalize()

        player_guild = config.ALLIANCES[config.DEFAULT_ALLIANCE][0]
        if player_name in config.PLAYER_DB:
            player_record = copy.copy(config.PLAYER_DB[player_name])
            if not player_record.guild:
                player_record.guild = player_guild
        else:
            player_record = models.Player(player_name, None, None, player_guild)

        if player_name not in self._item.log:
            self._item.log[player_name] = player_record
            self._rebuild_tree()
            utils.store_state()

    def closeEvent(self, event):
        self._item.raidtick = self._raidtick_cb.isChecked()
        tick_name = self._tick_name.text()[:32]
        for c in "[]:?/\\":
            tick_name = tick_name.replace(c, "-")
        tick_name = tick_name.replace("*", "")
        self._item.tick_name = tick_name
        utils.store_state()
        self.closed.emit()
        event.accept()


def _find_last_raidtick_before(raidticks, creditt_time):
    """Return the index of the last raidtick whose time < creditt_time, or -1."""
    result = -1
    for i, tick in enumerate(raidticks):
        if tick.time < creditt_time:
            result = i
    return result


class ApplyCredittDialog(QDialog):
    """Confirmation dialog for applying a creditt entry to a raidtick."""

    def __init__(self, creditt_entry, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Apply Creditt")
        self.setMinimumWidth(460)
        self._creditt = creditt_entry

        self._raidticks = [w for w in config.ATTENDANCE_LOGS if w.raidtick]

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # -- Creditt details card --
        details = QLabel(
            f"<table cellpadding='2'>"
            f"<tr><td style='color:gray;'>From</td>"
            f"<td><b>{creditt_entry.user}</b></td></tr>"
            f"<tr><td style='color:gray;'>Time</td>"
            f"<td>{creditt_entry.time}</td></tr>"
            f"<tr><td style='color:gray;'>Message</td>"
            f"<td><i>{creditt_entry.message}</i></td></tr>"
            f"</table>"
        )
        details.setWordWrap(True)
        details.setStyleSheet(
            "QLabel { background: palette(base); border: 1px solid palette(mid);"
            " border-radius: 4px; padding: 8px; }"
        )
        layout.addWidget(details)

        # -- Form fields --
        form = QFormLayout()
        form.setSpacing(8)
        layout.addLayout(form)

        self._tick_combo = QComboBox()
        if self._raidticks:
            creditt_time = dateutil.parser.parse(creditt_entry.time)
            for tick in self._raidticks:
                label = tick.tick_name or tick.zone or ""
                self._tick_combo.addItem(f"{tick.time}  {label}".strip())
            default_idx = _find_last_raidtick_before(self._raidticks, creditt_time)
            if default_idx >= 0:
                self._tick_combo.setCurrentIndex(default_idx)
        form.addRow("Target tick:", self._tick_combo)

        self._name_edit = QLineEdit(creditt_entry.user)
        self._name_edit.textChanged.connect(self._update_status)
        form.addRow("Player name to add:", self._name_edit)

        self._replace_edit = QLineEdit(creditt_entry.user)
        self._replace_edit.textChanged.connect(self._update_status)
        form.addRow("Replace existing player:", self._replace_edit)

        # -- Status indicators --
        self._status_label = QLabel()
        self._status_label.setWordWrap(True)
        self._status_label.setStyleSheet("QLabel { padding: 4px 0; }")
        layout.addWidget(self._status_label)

        # -- Button box --
        self._buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self._buttons.accepted.connect(self._on_accept)
        self._buttons.rejected.connect(self.reject)
        layout.addWidget(self._buttons)

        self._tick_combo.currentIndexChanged.connect(self._update_status)
        self._update_status()

        if config.ALWAYS_ON_TOP:
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        apply_windows_window_frame(self, dark_mode=config.DARK_MODE)

    def _selected_tick(self):
        idx = self._tick_combo.currentIndex()
        if idx < 0 or idx >= len(self._raidticks):
            return None
        return self._raidticks[idx]

    def _update_status(self):
        tick = self._selected_tick()
        ok_btn = self._buttons.button(QDialogButtonBox.StandardButton.Ok)
        if tick is None:
            self._status_label.setText(
                "<span style='color:#e05050; font-weight:600;'>"
                "\u26A0 No raidticks available.</span>"
            )
            ok_btn.setEnabled(False)
            return

        ok_btn.setEnabled(True)
        parts = []

        add_name = self._name_edit.text().strip().capitalize()
        replace_name = self._replace_edit.text().strip().capitalize()

        if replace_name:
            if replace_name in tick.log:
                parts.append(
                    f"<span style='color:#e05050; font-weight:600;'>"
                    f"\u2713 {replace_name}</span> found on tick (will be removed)"
                )
            else:
                parts.append(
                    f"<span style='color:#ff9800;'>"
                    f"\u2717 {replace_name}</span> not found on tick"
                )

        if add_name:
            if add_name == replace_name:
                if replace_name not in tick.log:
                    parts.append(
                        f"<span style='color:#4caf50;'>"
                        f"\u2713 {add_name}</span> will be added"
                    )
                else:
                    parts.append(
                        f"<span style='color:gray;'>"
                        f"\u2194 {add_name}</span> will be re-added (no net change)"
                    )
            elif add_name in tick.log:
                parts.append(
                    f"<span style='color:#ff9800;'>"
                    f"\u26A0 {add_name}</span> is already on this tick"
                )
            else:
                parts.append(
                    f"<span style='color:#4caf50;'>"
                    f"\u2713 {add_name}</span> will be added"
                )

        self._status_label.setText("<br>".join(parts))

    def _on_accept(self):
        tick = self._selected_tick()
        if tick is None:
            return

        player_name = self._name_edit.text().strip().capitalize()
        if not player_name:
            QMessageBox.warning(self, "Apply Creditt", "Player name cannot be empty.")
            return

        replace_name = self._replace_edit.text().strip()
        if replace_name:
            replace_name = replace_name.capitalize()
            tick.log.pop(replace_name, None)

        if player_name not in tick.log:
            player_guild = config.ALLIANCES[config.DEFAULT_ALLIANCE][0]
            if player_name in config.PLAYER_DB:
                player_record = copy.copy(config.PLAYER_DB[player_name])
                if not player_record.guild:
                    player_record.guild = player_guild
            else:
                player_record = models.Player(player_name, None, None, player_guild)
            tick.log[player_name] = player_record

        self._creditt.applied = True
        utils.store_state()
        self.accept()
