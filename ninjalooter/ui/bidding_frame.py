import datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ninjalooter import config, models, utils
from ninjalooter.app_signals import signals
from ninjalooter.ui.table_model import ColumnDefn, ObjectTableView
from ninjalooter.ui.theme import apply_windows_window_frame, semantic


class BiddingFrame(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        splitter = QSplitter(Qt.Orientation.Vertical, self)

        # ── Pane 1: Pending Drops ──
        pane1 = QWidget()
        pane1_layout = QVBoxLayout(pane1)
        pane1_layout.setContentsMargins(10, 10, 10, 0)

        pending_label = QLabel("Pending Drops")
        pending_label.setStyleSheet("font-size: 13px; font-weight: bold;")
        pane1_layout.addWidget(pending_label)

        pending_row = QHBoxLayout()
        pane1_layout.addLayout(pending_row)

        self.pending_list = ObjectTableView(
            columns=[
                ColumnDefn("Report Time", "timestamp", width=170),
                ColumnDefn("Reporter", "reporter", width=95),
                ColumnDefn("Item", "name", width=225),
                ColumnDefn("Min. DKP", lambda x: str(x.min_dkp()), width=61, center=True),
                ColumnDefn("Restrictions", lambda x: x.classes(), width=85, center=True),
                ColumnDefn("Droppable", lambda x: x.droppable(), width=70, center=True),
            ],
            parent=self,
            single_select=True,
        )
        self.pending_list.setToolTip("Double click an item to ignore it")
        self.pending_list.doubleClicked.connect(self._on_ignore_pending)
        self.pending_list.clicked.connect(self._update_min_dkp_spinner)
        self.pending_list.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        pending_row.addWidget(self.pending_list, 1)

        pending_btn_col = QVBoxLayout()
        pending_row.addLayout(pending_btn_col)

        btn_ignore = QPushButton("Ignore")
        btn_ignore.clicked.connect(self._on_ignore_pending)
        pending_btn_col.addWidget(btn_ignore)

        btn_dkp = QPushButton("DKP Bid")
        btn_dkp.clicked.connect(self._start_auction_dkp)
        pending_btn_col.addWidget(btn_dkp)

        btn_roll = QPushButton("Roll")
        btn_roll.clicked.connect(self._start_auction_random)
        pending_btn_col.addWidget(btn_roll)

        btn_wiki_pending = QPushButton("Wiki?")
        btn_wiki_pending.clicked.connect(self._show_wiki_pending)
        pending_btn_col.addWidget(btn_wiki_pending)

        pending_btn_col.addSpacing(8)
        min_dkp_label = QLabel("Min. DKP")
        min_dkp_label.setStyleSheet("font-weight: bold;")
        pending_btn_col.addWidget(min_dkp_label)

        self.min_dkp_spinner = QSpinBox()
        self.min_dkp_spinner.setRange(0, 10000)
        self.min_dkp_spinner.setValue(config.MIN_DKP)
        self.min_dkp_spinner.valueChanged.connect(self._on_min_dkp_spin)
        pending_btn_col.addWidget(self.min_dkp_spinner)
        pending_btn_col.addStretch()

        # ── Pane 2: Active Auctions ──
        pane2 = QWidget()
        pane2_layout = QVBoxLayout(pane2)
        pane2_layout.setContentsMargins(10, 10, 10, 0)

        active_label = QLabel("Active Auctions")
        active_label.setStyleSheet("font-size: 13px; font-weight: bold;")
        pane2_layout.addWidget(active_label)

        active_row = QHBoxLayout()
        pane2_layout.addLayout(active_row)

        self.active_list = ObjectTableView(
            columns=[
                ColumnDefn("Item", lambda x: x.name(), width=215),
                ColumnDefn("Restrictions", lambda x: x.classes(), width=95, center=True),
                ColumnDefn("Droppable", lambda x: x.droppable(), width=70, center=True),
                ColumnDefn("Rand/Min", lambda x: str(x.get_target_min()), width=70, center=True),
                ColumnDefn("Bid/Roll", lambda x: str(x.highest_number()), width=65, center=True),
                ColumnDefn("Leading", lambda x: x.highest_players(), width=90),
                ColumnDefn(
                    "Time Left",
                    lambda x: x.time_remaining_seconds(),
                    width=100,
                    string_converter=lambda x: x.time_remaining_ui(),
                ),
            ],
            parent=self,
            single_select=True,
        )
        self.active_list.setToolTip("Double click an auction to view bid history")
        self.active_list.doubleClicked.connect(self._show_active_detail)
        active_row.addWidget(self.active_list, 1)
        self.active_list.sortByColumn(6, Qt.SortOrder.AscendingOrder)

        self.active_list.object_model.set_row_color_func(self._active_row_color)

        active_btn_col = QVBoxLayout()
        active_row.addLayout(active_btn_col)

        btn_undo_start = QPushButton("Undo")
        btn_undo_start.clicked.connect(self._undo_start)
        active_btn_col.addWidget(btn_undo_start)

        active_btn_col.addSpacing(4)

        time_row = QHBoxLayout()
        self.btn_time_sub = QPushButton("-")
        self.btn_time_sub.setFixedWidth(24)
        self.btn_time_sub.setToolTip("Remove time from Auction")
        self.btn_time_sub.clicked.connect(lambda: self._auc_time_delta(subtract=True))
        time_row.addWidget(self.btn_time_sub)

        self.time_spinner = QSpinBox()
        self.time_spinner.setRange(1, 30)
        self.time_spinner.setValue(1)
        self.time_spinner.setToolTip("Minutes to add/remove")
        self.time_spinner.setFixedWidth(50)
        time_row.addWidget(self.time_spinner)

        self.btn_time_add = QPushButton("+")
        self.btn_time_add.setFixedWidth(24)
        self.btn_time_add.setToolTip("Add time to Auction")
        self.btn_time_add.clicked.connect(lambda: self._auc_time_delta(subtract=False))
        time_row.addWidget(self.btn_time_add)
        active_btn_col.addLayout(time_row)

        btn_copy_bid = QPushButton("Copy Bid")
        btn_copy_bid.clicked.connect(self._copy_bid_text)
        active_btn_col.addWidget(btn_copy_bid)

        btn_complete = QPushButton("Complete")
        btn_complete.clicked.connect(self._complete_auction)
        active_btn_col.addWidget(btn_complete)

        btn_wiki_active = QPushButton("Wiki?")
        btn_wiki_active.clicked.connect(self._show_wiki_active)
        active_btn_col.addWidget(btn_wiki_active)

        active_btn_col.addSpacing(4)

        self.bid_channel_combo = QComboBox()
        self.bid_channel_combo.addItems(list(config.BID_CHANNEL_OPTIONS))
        idx = self.bid_channel_combo.findText(config.PRIMARY_BID_CHANNEL)
        if idx >= 0:
            self.bid_channel_combo.setCurrentIndex(idx)
        self.bid_channel_combo.setToolTip("Selected channel will be used for Auction clipboard messages")
        self.bid_channel_combo.currentTextChanged.connect(self._select_bid_target)
        active_btn_col.addWidget(self.bid_channel_combo)
        active_btn_col.addStretch()

        # 1-second refresh timer for active auctions
        self._active_timer = QTimer(self)
        self._active_timer.timeout.connect(self._refresh_active_list)
        self._active_timer.start(1000)

        # ── Pane 3: Historical Auctions ──
        pane3 = QWidget()
        pane3_layout = QVBoxLayout(pane3)
        pane3_layout.setContentsMargins(10, 10, 10, 10)

        history_label = QLabel("Historical Auctions")
        history_label.setStyleSheet("font-size: 13px; font-weight: bold;")
        pane3_layout.addWidget(history_label)

        history_row = QHBoxLayout()
        pane3_layout.addLayout(history_row)

        self._history_completed_col = 6
        self.history_list = ObjectTableView(
            columns=[
                ColumnDefn("Item", lambda x: x.name(), width=240),
                ColumnDefn("Restrictions", lambda x: x.classes(), width=95, center=True),
                ColumnDefn("Droppable", lambda x: x.droppable(), width=70),
                ColumnDefn("Rand/Min", lambda x: str(x.get_target_min()), width=65),
                ColumnDefn("Bid/Roll", lambda x: str(x.highest_number()), width=65),
                ColumnDefn("Winner", lambda x: x.highest_players(), width=108),
                ColumnDefn("Completed", lambda x: x.end_time),
            ],
            parent=self,
            single_select=True,
        )
        self.history_list.setColumnHidden(self._history_completed_col, True)
        self.history_list.sortByColumn(self._history_completed_col, Qt.SortOrder.AscendingOrder)
        self.history_list.setToolTip("Double click an auction to view bid history")
        self.history_list.doubleClicked.connect(self._show_history_detail)
        history_row.addWidget(self.history_list, 1)

        history_btn_col = QVBoxLayout()
        history_row.addLayout(history_btn_col)

        btn_undo_complete = QPushButton("Undo")
        btn_undo_complete.clicked.connect(self._undo_complete)
        history_btn_col.addWidget(btn_undo_complete)

        btn_copy_win = QPushButton("Copy Text")
        btn_copy_win.clicked.connect(self._copy_win_text)
        history_btn_col.addWidget(btn_copy_win)

        btn_wiki_history = QPushButton("Wiki?")
        btn_wiki_history.clicked.connect(self._show_wiki_history)
        history_btn_col.addWidget(btn_wiki_history)

        self.hide_rots_cb = QCheckBox("Hide Rots")
        self.hide_rots_cb.setChecked(config.HIDE_ROTS)
        self.hide_rots_cb.stateChanged.connect(self._on_hide_rot)
        history_btn_col.addWidget(self.hide_rots_cb)
        history_btn_col.addStretch()

        # ── Assemble splitter ──
        splitter.addWidget(pane1)
        splitter.addWidget(pane2)
        splitter.addWidget(pane3)
        splitter.setChildrenCollapsible(False)
        splitter.setSizes(
            [
                config.ACTIVE_SASH_POS,
                config.HISTORICAL_SASH_POS,
                215,
            ]
        )
        splitter.splitterMoved.connect(self._on_sash_changed)
        self._splitter = splitter

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(splitter)

        # ── Initial data ──
        self.pending_list.set_objects(config.PENDING_AUCTIONS)
        self.active_list.set_objects(list(config.ACTIVE_AUCTIONS.values()))
        self.history_list.set_objects(list(config.HISTORICAL_AUCTIONS.values()))
        if config.HIDE_ROTS:
            self._apply_hide_rot_filter()

        # ── Connect signals ──
        signals.drop.connect(self._on_drop)
        signals.bid.connect(self._on_bid)
        signals.auction_started.connect(self._on_auction_started)
        signals.auction_completed.connect(self._on_auction_completed)
        signals.app_clear.connect(self._on_clear_app)
        signals.app_reload.connect(self._on_reload_app)
        signals.ignore.connect(self._refresh_pending)

    # ── Timer / row color ──

    @staticmethod
    def _active_row_color(obj):
        try:
            remaining = obj.time_remaining().total_seconds()
        except Exception:
            return None
        danger_zone = config.MIN_BID_TIME / 3
        warn_zone = config.MIN_BID_TIME / 3 * 2
        if remaining < danger_zone:
            return semantic.timer_danger
        if remaining < warn_zone:
            return semantic.timer_warn
        return semantic.timer_safe

    def _refresh_active_list(self):
        row = self._visual_row(self.active_list)
        self.active_list.set_objects(list(config.ACTIVE_AUCTIONS.values()))
        self._reselect_row(self.active_list, row)

    # ── Splitter persistence ──

    def _on_sash_changed(self, _pos, _index):
        sizes = self._splitter.sizes()
        if len(sizes) >= 2:
            config.ACTIVE_SASH_POS = sizes[0]
            config.HISTORICAL_SASH_POS = sizes[1]

    # ── Selection helpers ──

    @staticmethod
    def _visual_row(table_view) -> int:
        """Return the visual (proxy) row index of the current selection, or -1."""
        indexes = table_view.selectionModel().selectedRows()
        return indexes[0].row() if indexes else -1

    @staticmethod
    def _reselect_row(table_view, row: int):
        """Re-select *table_view* at *row*, clamping to the last item."""
        if row < 0:
            return
        count = table_view.model().rowCount()
        if count > 0:
            table_view.selectRow(min(row, count - 1))

    # ── Pending pane actions ──

    def _update_min_dkp_spinner(self):
        selected = self.pending_list.get_selected_object()
        if selected:
            val = selected.min_dkp()
            if isinstance(val, int):
                self.min_dkp_spinner.setValue(val)

    def _on_min_dkp_spin(self, value):
        selected = self.pending_list.get_selected_object()
        if not selected:
            return
        selected.min_dkp_override = value
        self.pending_list.object_model.refresh_object(selected)

    def _on_ignore_pending(self):
        selected = self.pending_list.get_selected_object()
        if not selected:
            return
        row = self._visual_row(self.pending_list)
        utils.ignore_pending_item(selected)
        self.pending_list.set_objects(config.PENDING_AUCTIONS)
        self._reselect_row(self.pending_list, row)
        utils.store_state()
        signals.ignore.emit()

    def _start_auction_dkp(self):
        selected = self.pending_list.get_selected_object()
        if not selected:
            return
        row = self._visual_row(self.pending_list)
        auc = utils.start_auction_dkp(selected, config.DEFAULT_ALLIANCE)
        if not auc:
            QMessageBox.critical(
                self,
                "Duplicate Auction",
                "An item with this name is already pending auction.\n"
                "Please complete the existing auction before starting another.",
            )
            return
        self.pending_list.set_objects(config.PENDING_AUCTIONS)
        self._reselect_row(self.pending_list, row)
        self.active_list.set_objects(list(config.ACTIVE_AUCTIONS.values()))
        utils.to_clipboard(auc.bid_text())
        utils.store_state()
        signals.auction_started.emit()

    def _start_auction_random(self):
        selected = self.pending_list.get_selected_object()
        if not selected:
            return
        row = self._visual_row(self.pending_list)
        auc = utils.start_auction_random(selected)
        if not auc:
            QMessageBox.critical(
                self,
                "Duplicate Auction",
                "An item with this name is already pending auction.\n"
                "Please complete the existing auction before starting another.",
            )
            return
        self.pending_list.set_objects(config.PENDING_AUCTIONS)
        self._reselect_row(self.pending_list, row)
        self.active_list.set_objects(list(config.ACTIVE_AUCTIONS.values()))
        utils.to_clipboard(auc.bid_text())
        utils.store_state()
        signals.auction_started.emit()

    def _show_wiki_pending(self):
        selected = self.pending_list.get_selected_object()
        if selected:
            utils.open_wiki_url(selected)

    # ── Active pane actions ──

    def _undo_start(self):
        selected = self.active_list.get_selected_object()
        if not selected:
            return
        row = self._visual_row(self.active_list)
        selected.cancel()
        config.PENDING_AUCTIONS.append(selected.item)
        config.ACTIVE_AUCTIONS.pop(selected.item.uuid)
        self.pending_list.set_objects(config.PENDING_AUCTIONS)
        self.active_list.set_objects(list(config.ACTIVE_AUCTIONS.values()))
        self._reselect_row(self.active_list, row)
        utils.store_state()

    def _auc_time_delta(self, subtract=False):
        selected = self.active_list.get_selected_object()
        if not selected:
            return
        delta = datetime.timedelta(minutes=self.time_spinner.value())
        if subtract:
            selected.start_time -= delta
        else:
            if selected.time_remaining().total_seconds() <= 0:
                selected.start_time = datetime.datetime.now() - datetime.timedelta(seconds=config.MIN_BID_TIME)
            selected.start_time += delta

    def _copy_bid_text(self):
        selected = self.active_list.get_selected_object()
        if not selected:
            return
        utils.to_clipboard(selected.bid_text())

    def _complete_auction(self):
        selected = self.active_list.get_selected_object()
        if not selected:
            return
        row = self._visual_row(self.active_list)
        selected.complete()
        config.HISTORICAL_AUCTIONS[selected.item.uuid] = selected
        config.ACTIVE_AUCTIONS.pop(selected.item.uuid)
        self.active_list.set_objects(list(config.ACTIVE_AUCTIONS.values()))
        self._reselect_row(self.active_list, row)
        self._refresh_history()
        utils.to_clipboard(selected.win_text())
        utils.store_state()
        signals.auction_completed.emit()

    def _show_wiki_active(self):
        selected = self.active_list.get_selected_object()
        if selected:
            utils.open_wiki_url(selected.item)

    def _show_active_detail(self):
        selected = self.active_list.get_selected_object()
        if selected:
            BidDetailWindow(selected, self.active_list, parent=self)

    @staticmethod
    def _select_bid_target(text):
        config.PRIMARY_BID_CHANNEL = text
        config.CONF.set("default", "primary_bid_channel", config.PRIMARY_BID_CHANNEL)
        config.write()

    # ── History pane actions ──

    def _on_hide_rot(self):
        config.HIDE_ROTS = self.hide_rots_cb.isChecked()
        config.CONF.set("default", "hide_rots", str(config.HIDE_ROTS))
        self._refresh_history()
        config.write()

    def _apply_hide_rot_filter(self):
        if config.HIDE_ROTS:
            self.history_list.set_filter_func(lambda x: bool(x.highest()))
        else:
            self.history_list.set_filter_func(None)

    def _refresh_history(self):
        row = self._visual_row(self.history_list)
        self.history_list.set_objects(list(config.HISTORICAL_AUCTIONS.values()))
        self._apply_hide_rot_filter()
        self._reselect_row(self.history_list, row)

    def _undo_complete(self):
        selected = self.history_list.get_selected_object()
        if not selected:
            return
        selected.end_time = None
        config.ACTIVE_AUCTIONS[selected.item.uuid] = selected
        config.HISTORICAL_AUCTIONS.pop(selected.item.uuid)
        self.active_list.set_objects(list(config.ACTIVE_AUCTIONS.values()))
        self._refresh_history()
        utils.store_state()

    def _copy_win_text(self):
        selected = self.history_list.get_selected_object()
        if not selected:
            return
        utils.to_clipboard(selected.win_text())

    def _show_wiki_history(self):
        selected = self.history_list.get_selected_object()
        if selected:
            utils.open_wiki_url(selected.item)

    def _show_history_detail(self):
        selected = self.history_list.get_selected_object()
        if selected:
            BidDetailWindow(selected, self.history_list, parent=self)

    # ── Refresh helpers ──

    def _refresh_pending(self):
        row = self._visual_row(self.pending_list)
        self.pending_list.set_objects(config.PENDING_AUCTIONS)
        self._reselect_row(self.pending_list, row)

    # ── Signal handlers ──

    def _on_drop(self):
        self._refresh_pending()

    def _on_bid(self, item):
        self.active_list.object_model.refresh_object(item)

    def _on_auction_started(self):
        self._refresh_pending()
        row = self._visual_row(self.active_list)
        self.active_list.set_objects(list(config.ACTIVE_AUCTIONS.values()))
        self._reselect_row(self.active_list, row)

    def _on_auction_completed(self):
        row = self._visual_row(self.active_list)
        self.active_list.set_objects(list(config.ACTIVE_AUCTIONS.values()))
        self._reselect_row(self.active_list, row)
        self._refresh_history()

    def _on_clear_app(self):
        config.PENDING_AUCTIONS.clear()
        config.ACTIVE_AUCTIONS.clear()
        config.HISTORICAL_AUCTIONS.clear()
        config.IGNORED_AUCTIONS.clear()
        self.pending_list.set_objects(config.PENDING_AUCTIONS)
        self.active_list.set_objects(list(config.ACTIVE_AUCTIONS.values()))
        self._refresh_history()

    def _on_reload_app(self):
        self.pending_list.set_objects(config.PENDING_AUCTIONS)
        row = self._visual_row(self.active_list)
        self.active_list.set_objects(list(config.ACTIVE_AUCTIONS.values()))
        self._reselect_row(self.active_list, row)
        self._refresh_history()


class BidDetailWindow(QWidget):
    """Table-based editor for bids/rolls with live-sync and inline editing."""

    def __init__(self, item, listview, parent=None):
        super().__init__(parent, Qt.WindowType.Window)
        self.setWindowTitle(f"Bid Detail - {item.name()}")
        self.resize(400, 400)

        self._item = item
        self._listview = listview
        self._is_random = isinstance(item, models.RandomAuction)
        self._refreshing = False

        layout = QVBoxLayout(self)

        btn_row = QHBoxLayout()
        layout.addLayout(btn_row)

        btn_add = QPushButton("Add")
        btn_add.clicked.connect(self._add_entry)
        btn_row.addWidget(btn_add)

        btn_remove = QPushButton("Remove")
        btn_remove.clicked.connect(self._remove_entry)
        btn_row.addWidget(btn_remove)

        btn_row.addStretch()

        self._table = QTableWidget()
        self._table.setColumnCount(2)
        if self._is_random:
            self._table.setHorizontalHeaderLabels(["Player", "Roll"])
        else:
            self._table.setHorizontalHeaderLabels(["Bid", "Player"])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        layout.addWidget(self._table)

        self._table.cellChanged.connect(self._on_cell_changed)
        signals.bid.connect(self._on_live_bid)

        self._refresh_table()

        if config.ALWAYS_ON_TOP:
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        self.show()

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        apply_windows_window_frame(self, dark_mode=config.DARK_MODE)

    def closeEvent(self, event):
        try:
            signals.bid.disconnect(self._on_live_bid)
        except RuntimeError:
            pass
        event.accept()

    def _data_dict(self):
        return getattr(self._item, "rolls", getattr(self._item, "bids", {}))

    def _refresh_table(self):
        self._refreshing = True
        try:
            data = self._data_dict()
            self._table.setRowCount(0)
            if self._is_random:
                sorted_items = sorted(data.items(), key=lambda x: x[1], reverse=True)
                for player, roll in sorted_items:
                    row = self._table.rowCount()
                    self._table.insertRow(row)
                    self._table.setItem(row, 0, QTableWidgetItem(str(player)))
                    self._table.setItem(row, 1, QTableWidgetItem(str(roll)))
            else:
                sorted_items = sorted(data.items(), key=lambda x: x[0], reverse=True)
                for bid, player in sorted_items:
                    row = self._table.rowCount()
                    self._table.insertRow(row)
                    self._table.setItem(row, 0, QTableWidgetItem(str(bid)))
                    self._table.setItem(row, 1, QTableWidgetItem(str(player)))
        finally:
            self._refreshing = False

    def _on_live_bid(self, auction):
        if auction is self._item:
            self._refresh_table()

    def _on_cell_changed(self, row, col):
        if self._refreshing:
            return
        data = self._data_dict()
        try:
            if self._is_random:
                self._apply_random_edit(data, row, col)
            else:
                self._apply_dkp_edit(data, row, col)
            self._refresh_table()
            self._listview.object_model.refresh_object(self._item)
            utils.store_state()
        except (ValueError, KeyError):
            self._refresh_table()

    def _apply_dkp_edit(self, data, row, col):
        new_val = self._table.item(row, col).text().strip()
        sorted_keys = sorted(data.keys(), reverse=True)
        old_bid = sorted_keys[row]
        old_player = data[old_bid]
        if col == 0:
            new_bid = int(new_val)
            if new_bid != old_bid:
                del data[old_bid]
                data[new_bid] = old_player
        else:
            data[old_bid] = new_val

    def _apply_random_edit(self, data, row, col):
        new_val = self._table.item(row, col).text().strip()
        sorted_items = sorted(data.items(), key=lambda x: x[1], reverse=True)
        old_player, old_roll = sorted_items[row]
        if col == 0:
            if new_val != old_player:
                del data[old_player]
                data[new_val] = old_roll
        else:
            data[old_player] = int(new_val)

    def _add_entry(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Add Roll" if self._is_random else "Add Bid")
        form = QFormLayout(dlg)

        player_edit = QLineEdit()
        number_edit = QSpinBox()
        number_edit.setRange(0, 100000 if not self._is_random else 10000)

        form.addRow("Player:", player_edit)
        form.addRow("Roll:" if self._is_random else "Bid:", number_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        form.addRow(buttons)

        player_edit.setFocus()
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        player = player_edit.text().strip()
        number = number_edit.value()
        if not player:
            return

        data = self._data_dict()
        if self._is_random:
            data[player] = number
        else:
            data[number] = player
        self._refresh_table()
        self._listview.object_model.refresh_object(self._item)
        utils.store_state()

    def _remove_entry(self):
        row = self._table.currentRow()
        if row < 0:
            return
        data = self._data_dict()
        if self._is_random:
            sorted_items = sorted(data.items(), key=lambda x: x[1], reverse=True)
            player, _ = sorted_items[row]
            del data[player]
        else:
            sorted_keys = sorted(data.keys(), reverse=True)
            del data[sorted_keys[row]]
        self._refresh_table()
        self._listview.object_model.refresh_object(self._item)
        utils.store_state()


class IgnoredItemsWindow(QWidget):
    """Window showing ignored items with restore on double-click."""

    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Window)
        self.setWindowTitle("Ignored Auctions (Double Click to Restore)")
        self.resize(616, 600)

        layout = QVBoxLayout(self)

        self.ignored_list = ObjectTableView(
            columns=[
                ColumnDefn("Report Time", "timestamp", width=170),
                ColumnDefn("Reporter", "reporter", width=80),
                ColumnDefn("Item", "name", width=178),
                ColumnDefn("Restrictions", lambda x: x.classes(), width=85),
                ColumnDefn("Droppable", lambda x: x.droppable(), width=70),
            ],
            parent=self,
            single_select=True,
        )
        layout.addWidget(self.ignored_list)

        self.ignored_list.set_objects(config.IGNORED_AUCTIONS)
        self.ignored_list.doubleClicked.connect(self._on_restore)

        signals.ignore.connect(self._on_refresh)

        if config.ALWAYS_ON_TOP:
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        self.show()

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        apply_windows_window_frame(self, dark_mode=config.DARK_MODE)

    def _on_refresh(self):
        try:
            self.ignored_list.set_objects(config.IGNORED_AUCTIONS)
        except RuntimeError:
            pass

    def _on_restore(self):
        item = self.ignored_list.get_selected_object()
        if not item:
            return
        config.IGNORED_AUCTIONS.remove(item)
        config.PENDING_AUCTIONS.append(item)
        self.ignored_list.set_objects(config.IGNORED_AUCTIONS)
        signals.drop.emit()
