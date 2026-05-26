import os

from PySide6.QtGui import QAction, QActionGroup, QIcon, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QMenuBar,
    QMessageBox,
)

from ninjalooter import config, logger, logparse, utils
from ninjalooter.app_signals import signals
from ninjalooter.ui.attendance_replay_dialog import AttendanceReplayDialog
from ninjalooter.ui.bidding_frame import IgnoredItemsWindow
from ninjalooter.ui.theme import ThemedQFileDialog, apply_app_theme, apply_windows_window_frame

LOG = logger.getLogger(__name__)


class MenuBar(QMenuBar):
    def __init__(self, parent):
        super().__init__(parent)
        self._window = parent

        self._build_file_menu()
        self._build_options_menu()
        self._build_bidding_menu()
        self._build_alerts_menu()

        signals.alliance_changed.connect(self._on_alliance_changed_signal)

    # ------------------------------------------------------------------
    # File Menu
    # ------------------------------------------------------------------

    def _build_file_menu(self):
        menu = self.addMenu("&File")
        icons_dir = os.path.join(config.PROJECT_DIR, "data", "icons")

        configure_action = menu.addAction(
            QIcon(os.path.join(icons_dir, "gear.png")),
            "&Configure Log Directory",
        )
        configure_action.triggered.connect(self._on_configure_log_dir)

        menu.addSeparator()

        self._export_excel_action = menu.addAction(
            QIcon(os.path.join(icons_dir, "excel.png")),
            "Export to &Excel",
        )
        self._export_excel_action.setShortcut(QKeySequence("Ctrl+E"))
        self._export_excel_action.setEnabled(config.ALLOW_EXCEL_EXPORT)
        self._export_excel_action.triggered.connect(self._on_export_excel)

        self._export_eqdkp_action = menu.addAction(
            QIcon(os.path.join(icons_dir, "export.png")),
            "Export to EQDKPlus",
        )
        self._export_eqdkp_action.setShortcut(QKeySequence("Ctrl+P"))
        self._export_eqdkp_action.triggered.connect(self._on_export_eqdkp)

        menu.addSeparator()

        load_action = menu.addAction(
            QIcon(os.path.join(icons_dir, "import.png")),
            "&Load State",
        )
        load_action.setShortcut(QKeySequence("Ctrl+L"))
        load_action.triggered.connect(self._on_load_state)

        self._replay_action = menu.addAction(
            QIcon(os.path.join(icons_dir, "reload.png")),
            "Replay &Attendance Log",
        )
        self._replay_action.triggered.connect(self._on_replay_attendance)

        clear_action = menu.addAction(
            QIcon(os.path.join(icons_dir, "clear.png")),
            "&Clear Data",
        )
        clear_action.triggered.connect(self._on_clear_app)

        clear_tod_action = menu.addAction(
            QIcon(os.path.join(icons_dir, "clear.png")),
            "Clear &Kill Timers",
        )
        clear_tod_action.triggered.connect(self._on_clear_kill_timers)

        menu.addSeparator()

        exit_action = menu.addAction(
            QIcon(os.path.join(icons_dir, "exit.png")),
            "&Quit",
        )
        exit_action.setShortcut(QKeySequence("Ctrl+W"))
        exit_action.triggered.connect(self._window.close)

    # ------------------------------------------------------------------
    # Options Menu
    # ------------------------------------------------------------------

    def _build_options_menu(self):
        menu = self.addMenu("&Options")

        self._always_on_top_action = menu.addAction("&Always On Top")
        self._always_on_top_action.setCheckable(True)
        self._always_on_top_action.setChecked(config.ALWAYS_ON_TOP)
        self._always_on_top_action.triggered.connect(self._on_always_on_top)

        self._auto_swap_action = menu.addAction("Auto-Switch &Characters")
        self._auto_swap_action.setCheckable(True)
        self._auto_swap_action.setChecked(config.AUTO_SWAP_LOGFILE)
        self._auto_swap_action.triggered.connect(self._on_auto_swap)

        self._confirm_exit_action = menu.addAction("Confirm Exit")
        self._confirm_exit_action.setCheckable(True)
        self._confirm_exit_action.setChecked(config.CONFIRM_EXIT)
        self._confirm_exit_action.triggered.connect(self._on_confirm_exit)

        self._dark_mode_action = menu.addAction("&Dark Mode")
        self._dark_mode_action.setCheckable(True)
        self._dark_mode_action.setChecked(config.DARK_MODE)
        self._dark_mode_action.triggered.connect(self._on_dark_mode)

        self._native_dialogs_action = menu.addAction("Use &Native File Dialogs")
        self._native_dialogs_action.setCheckable(True)
        self._native_dialogs_action.setChecked(config.NATIVE_FILE_DIALOGS)
        self._native_dialogs_action.triggered.connect(self._on_native_file_dialogs)

        self._export_tz_action = menu.addAction("Export in &Eastern Time")
        self._export_tz_action.setCheckable(True)
        self._export_tz_action.setChecked(config.EXPORT_TIME_IN_EASTERN)
        self._export_tz_action.triggered.connect(self._on_export_timezone)

    # ------------------------------------------------------------------
    # Bidding Menu
    # ------------------------------------------------------------------

    def _build_bidding_menu(self):
        menu = self.addMenu("&Bidding")

        self._show_ignored_action = menu.addAction("&Show Ignored Items...")
        self._show_ignored_action.triggered.connect(self._on_show_ignored)

        menu.addSeparator()

        # Alliance submenu
        alliance_menu = menu.addMenu("&Alliance")
        self._alliance_group = QActionGroup(self)
        self._alliance_group.setExclusive(True)
        self._alliance_actions: dict[str, QAction] = {}
        for alliance in config.ALLIANCES:
            action = QAction(alliance, self, checkable=True)
            if alliance == config.DEFAULT_ALLIANCE:
                action.setChecked(True)
            self._alliance_group.addAction(action)
            alliance_menu.addAction(action)
            self._alliance_actions[alliance] = action
        self._alliance_group.triggered.connect(self._on_set_alliance)

        # Drop channels submenu
        drop_menu = menu.addMenu("&Drop Channels")
        self._drop_channel_actions: dict[str, QAction] = {}
        for channel in config.DROP_CHANNEL_OPTIONS:
            action = QAction(channel, self, checkable=True)
            if config.DROP_CHANNEL_OPTIONS[channel] in config.MATCH_DROP:
                action.setChecked(True)
            drop_menu.addAction(action)
            action.triggered.connect(self._on_drop_channels_changed)
            self._drop_channel_actions[channel] = action

        # Bid channels submenu
        bid_menu = menu.addMenu("&Bid Channels")
        self._bid_channel_actions: dict[str, QAction] = {}
        for channel in config.BID_CHANNEL_OPTIONS:
            action = QAction(channel, self, checkable=True)
            if config.BID_CHANNEL_OPTIONS[channel] in config.MATCH_BID:
                action.setChecked(True)
            bid_menu.addAction(action)
            action.triggered.connect(self._on_bid_channels_changed)
            self._bid_channel_actions[channel] = action

        # Options
        self._restrict_bids_action = menu.addAction("Restrict Bids to Alliance")
        self._restrict_bids_action.setCheckable(True)
        self._restrict_bids_action.setChecked(config.RESTRICT_BIDS)
        self._restrict_bids_action.triggered.connect(self._on_restrict_bids)

        self._restrict_export_action = menu.addAction("Restrict &Export to Alliance")
        self._restrict_export_action.setCheckable(True)
        self._restrict_export_action.setChecked(config.RESTRICT_EXPORT)
        self._restrict_export_action.triggered.connect(self._on_restrict_export)

        self._nodrop_only_action = menu.addAction("&Ignore Droppable Items")
        self._nodrop_only_action.setCheckable(True)
        self._nodrop_only_action.setChecked(config.NODROP_ONLY)
        self._nodrop_only_action.triggered.connect(self._on_nodrop_only)

        self._tick_before_loot_action = menu.addAction("Tick Before Loot (Quake Mode)")
        self._tick_before_loot_action.setCheckable(True)
        self._tick_before_loot_action.setChecked(config.TICK_BEFORE_LOOT)
        self._tick_before_loot_action.triggered.connect(self._on_tick_before_loot)

        self._remember_player_action = menu.addAction("Use &Cached Player Data")
        self._remember_player_action.setCheckable(True)
        self._remember_player_action.setChecked(config.REMEMBER_PLAYER_DATA)
        self._remember_player_action.triggered.connect(self._on_remember_player_data)

    # ------------------------------------------------------------------
    # Alerts Menu
    # ------------------------------------------------------------------

    def _build_alerts_menu(self):
        menu = self.addMenu("A&lerts")

        self._audio_alerts_action = menu.addAction("&Audio Alerts")
        self._audio_alerts_action.setCheckable(True)
        self._audio_alerts_action.setChecked(config.AUDIO_ALERTS)
        self._audio_alerts_action.triggered.connect(self._on_audio_alerts)

        self._text_alerts_action = menu.addAction("&Text Alerts")
        self._text_alerts_action.setCheckable(True)
        self._text_alerts_action.setChecked(config.TEXT_ALERTS)
        self._text_alerts_action.triggered.connect(self._on_text_alerts)

    # ------------------------------------------------------------------
    # Sync helpers (called externally to keep tray/menu in agreement)
    # ------------------------------------------------------------------

    def sync_always_on_top(self):
        self._always_on_top_action.setChecked(config.ALWAYS_ON_TOP)

    # ------------------------------------------------------------------
    # File handlers
    # ------------------------------------------------------------------

    def _on_configure_log_dir(self):
        existing = config.LOG_DIRECTORY
        if not os.path.isdir(existing):
            existing = os.path.dirname(existing)
        dlg = ThemedQFileDialog(self._window, dark_mode=config.DARK_MODE, qt_dialogs=not config.NATIVE_FILE_DIALOGS)
        dlg.setWindowTitle("Select Log Directory")
        dlg.setFileMode(QFileDialog.FileMode.Directory)
        dlg.setDirectory(existing)
        dlg.setOption(QFileDialog.Option.ShowDirsOnly, True)
        if dlg.exec() != QFileDialog.DialogCode.Accepted:
            return
        dirs = dlg.selectedFiles()
        if not dirs:
            return
        selected = dirs[0]
        LOG.info("Selected log directory: %s", selected)
        config.LOG_DIRECTORY = selected
        config.CONF.set("default", "logdir", selected)
        config.write()
        self._window.restart_parser()
        self._window.update_fs_watcher(selected)

    def _on_export_timezone(self, checked: bool):
        config.EXPORT_TIME_IN_EASTERN = checked
        config.CONF.set("default", "export_time_in_eastern", str(config.EXPORT_TIME_IN_EASTERN))
        config.write()

    def _on_load_state(self):
        LOG.info("Attempting to load a state.json file...")
        dlg = ThemedQFileDialog(self._window, dark_mode=config.DARK_MODE, qt_dialogs=not config.NATIVE_FILE_DIALOGS)
        dlg.setWindowTitle("Open Statefile")
        dlg.setNameFilter("NL State File (state_*.json)")
        dlg.setFileMode(QFileDialog.FileMode.ExistingFile)
        dlg.setDirectory(os.curdir)
        if dlg.exec() != QFileDialog.DialogCode.Accepted:
            return
        files = dlg.selectedFiles()
        if not files:
            return
        utils.load_state(files[0])
        signals.app_reload.emit()

    def _on_replay_attendance(self):
        LOG.info("Opening attendance replay dialog...")
        dlg = AttendanceReplayDialog(self._window)
        dlg.exec()

    def _on_export_excel(self):
        LOG.info("Exporting to Excel format.")
        dlg = ThemedQFileDialog(self._window, dark_mode=config.DARK_MODE, qt_dialogs=not config.NATIVE_FILE_DIALOGS)
        dlg.setWindowTitle("Export to Excel")
        dlg.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        dlg.setNameFilter("Excel Spreadsheet (*.xlsx)")
        dlg.setDefaultSuffix("xlsx")
        if dlg.exec() != QFileDialog.DialogCode.Accepted:
            return
        files = dlg.selectedFiles()
        if not files:
            return
        filename = files[0]
        try:
            result = utils.export_to_excel(filename)
        except Exception:
            LOG.exception("Unexpected error during Excel export.")
            result = False
        if not result:
            QMessageBox.critical(
                self._window,
                "Failed to Export",
                "Failed to export data. The most common cause of this\n"
                "error is attempting to export to a file that is still open\nin Excel.",
            )
        else:
            QMessageBox.information(
                self._window,
                "Export Complete",
                f"Successfully exported data to:\n{filename}",
            )

    def _on_export_eqdkp(self):
        LOG.info("Exporting to EQDKPlus format.")
        dlg = ThemedQFileDialog(self._window, dark_mode=config.DARK_MODE, qt_dialogs=not config.NATIVE_FILE_DIALOGS)
        dlg.setWindowTitle("Export to EQDKPlus")
        dlg.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        dlg.setNameFilter("Excel Spreadsheet (*.xlsx)")
        dlg.setDefaultSuffix("xlsx")
        if dlg.exec() != QFileDialog.DialogCode.Accepted:
            return
        files = dlg.selectedFiles()
        if not files:
            return
        filename = files[0]
        try:
            result = utils.export_to_eqdkp(filename)
        except Exception:
            LOG.exception("Unexpected error during EQDKPlus export.")
            result = False
        if not result:
            QMessageBox.critical(
                self._window,
                "Failed to Export",
                "Failed to export data. The most common cause of this\n"
                "error is attempting to export to a file that is still open\nin Excel.",
            )
        else:
            QMessageBox.information(
                self._window,
                "Export Complete",
                f"Successfully exported data to:\n{filename}",
            )

    def _on_clear_app(self):
        reply = QMessageBox.question(
            self._window,
            "Confirm Clear",
            "Are you sure you want to clear all data?",
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
        )
        if reply == QMessageBox.StandardButton.Ok:
            utils.store_state(backup=True)
            signals.app_clear.emit()
            utils.clear_alerts()

    def _on_clear_kill_timers(self):
        reply = QMessageBox.question(
            self._window,
            "Confirm Clear",
            "Are you sure you want to clear all kill timer data?",
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
        )
        if reply == QMessageBox.StandardButton.Ok:
            config.KILL_TIMERS.clear()
            signals.kill.emit()
            utils.store_state()

    # ------------------------------------------------------------------
    # Bidding handlers
    # ------------------------------------------------------------------

    def _on_set_alliance(self, action: QAction):
        config.DEFAULT_ALLIANCE = action.text()
        config.CONF.set("default", "default_alliance", config.DEFAULT_ALLIANCE)
        config.write()
        signals.alliance_changed.emit(config.DEFAULT_ALLIANCE)

    def _on_drop_channels_changed(self):
        selected = [ch for ch, act in self._drop_channel_actions.items() if act.isChecked()]
        config.MATCH_DROP = [config.DROP_CHANNEL_OPTIONS[ch] for ch in selected]
        logparse.reset_matchers()
        config.CONF.set("default", "drop_channels", ",".join(selected))
        config.write()

    def _on_bid_channels_changed(self):
        selected = [ch for ch, act in self._bid_channel_actions.items() if act.isChecked()]
        config.MATCH_BID = [config.BID_CHANNEL_OPTIONS[ch] for ch in selected]
        logparse.reset_matchers()
        config.CONF.set("default", "bid_channels", ",".join(selected))
        config.write()

    def _on_restrict_bids(self, checked: bool):
        config.RESTRICT_BIDS = checked
        config.CONF.set("default", "restrict_bids", str(config.RESTRICT_BIDS))
        config.write()

    def _on_restrict_export(self, checked: bool):
        config.RESTRICT_EXPORT = checked
        config.CONF.set("default", "restrict_export", str(config.RESTRICT_EXPORT))
        config.write()

    def _on_nodrop_only(self, checked: bool):
        config.NODROP_ONLY = checked
        config.CONF.set("default", "nodrop_only", str(config.NODROP_ONLY))
        config.write()

    def _on_tick_before_loot(self, checked: bool):
        config.TICK_BEFORE_LOOT = checked
        config.CONF.set("default", "tick_before_loot", str(config.TICK_BEFORE_LOOT))
        config.write()

    def _on_remember_player_data(self, checked: bool):
        config.REMEMBER_PLAYER_DATA = checked
        config.CONF.set("default", "remember_player_data", str(config.REMEMBER_PLAYER_DATA))
        config.write()

    def _on_show_ignored(self):
        IgnoredItemsWindow(parent=self._window)

    # ------------------------------------------------------------------
    # View handlers
    # ------------------------------------------------------------------

    def _on_always_on_top(self, checked: bool):
        config.ALWAYS_ON_TOP = checked
        config.CONF.set("default", "always_on_top", str(config.ALWAYS_ON_TOP))
        config.write()
        self._window.update_always_on_top()

    def _on_confirm_exit(self, checked: bool):
        config.CONFIRM_EXIT = checked
        config.CONF.set("default", "confirm_exit", str(config.CONFIRM_EXIT))
        config.write()

    def _on_auto_swap(self, checked: bool):
        config.AUTO_SWAP_LOGFILE = checked
        config.CONF.set("default", "auto_swap_logfile", str(config.AUTO_SWAP_LOGFILE))
        config.write()

    def _on_dark_mode(self, checked: bool):
        config.DARK_MODE = checked
        if not config.CONF.has_section("theme"):
            config.CONF.add_section("theme")
        config.CONF.set("theme", "dark_mode", str(config.DARK_MODE))
        config.write()

        app = QApplication.instance()
        if app:
            apply_app_theme(app, dark_mode=config.DARK_MODE)
            apply_windows_window_frame(self._window, dark_mode=config.DARK_MODE)

    def _on_native_file_dialogs(self, checked: bool):
        config.NATIVE_FILE_DIALOGS = checked
        if not config.CONF.has_section("theme"):
            config.CONF.add_section("theme")
        config.CONF.set("theme", "native_file_dialogs", str(config.NATIVE_FILE_DIALOGS))
        config.write()

    # ------------------------------------------------------------------
    # Alerts handlers
    # ------------------------------------------------------------------

    def _on_audio_alerts(self, checked: bool):
        config.AUDIO_ALERTS = checked
        config.CONF.set("alerts", "audio_enabled", str(config.AUDIO_ALERTS))
        config.write()

    def _on_text_alerts(self, checked: bool):
        config.TEXT_ALERTS = checked
        config.CONF.set("alerts", "text_enabled", str(config.TEXT_ALERTS))
        config.write()

    # ------------------------------------------------------------------
    # External signal handlers
    # ------------------------------------------------------------------

    def _on_alliance_changed_signal(self, alliance_name: str):
        action = self._alliance_actions.get(alliance_name)
        if action:
            action.setChecked(True)
