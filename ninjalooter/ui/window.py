import os

import semver
from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent, QIcon, QShowEvent
from PySide6.QtWidgets import (
    QMainWindow,
    QMenu,
    QMessageBox,
    QSystemTrayIcon,
    QTabWidget,
)
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from ninjalooter import autoupdate, config, logger, logparse, utils
from ninjalooter.app_signals import signals
from ninjalooter.ui import (
    attendance_frame,
    bidding_frame,
    changelog_frame,
    killtimes_frame,
    menu_bar,
    population_frame,
    raid_overview_frame,
    raidgroups_frame,
)
from ninjalooter.ui.theme import apply_windows_window_frame

LOG = logger.getLogger(__name__)


class _LogDirHandler(FileSystemEventHandler):
    """Watchdog handler that triggers log file swap check on modifications."""

    def __init__(self, window):
        super().__init__()
        self._window = window

    def on_modified(self, event):
        if event.is_directory:
            return
        self._window._on_filesystem_event()

    def on_created(self, event):
        if event.is_directory:
            return
        self._window._on_filesystem_event()


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("NinjaLooter EQ Raid Manager")
        self.resize(855, 800)

        icon_path = os.path.join(config.PROJECT_DIR, "data", "icons", "ninja_attack.ico")
        if os.path.exists(icon_path):
            self._app_icon = QIcon(icon_path)
        else:
            png_path = os.path.join(config.PROJECT_DIR, "data", "icons", "ninja_attack.png")
            self._app_icon = QIcon(png_path)
        self.setWindowIcon(self._app_icon)

        # Menu bar
        self._menu_bar = menu_bar.MenuBar(self)
        self.setMenuBar(self._menu_bar)

        # Tab widget
        self._notebook = QTabWidget()
        self._notebook.setTabPosition(QTabWidget.TabPosition.North)
        self.setCentralWidget(self._notebook)

        self.bidding_frame = bidding_frame.BiddingFrame(self._notebook)
        self._notebook.addTab(self.bidding_frame, "Bidding")

        self.attendance_frame = attendance_frame.AttendanceFrame(self._notebook)
        self._notebook.addTab(self.attendance_frame, "Attendance Logs")

        self.population_frame = population_frame.PopulationFrame(self._notebook)
        self._notebook.addTab(self.population_frame, "Population Rolls")

        self.killtimes_frame = killtimes_frame.KillTimesFrame(self._notebook)
        self._notebook.addTab(self.killtimes_frame, "Time of Death Tracking")

        self.raidgroups_frame = raidgroups_frame.RaidGroupsFrame(self._notebook)
        self._notebook.addTab(self.raidgroups_frame, "Raid Groups")

        self.raid_ov_frame = raid_overview_frame.RaidOverviewFrame(self._notebook)
        self._notebook.addTab(self.raid_ov_frame, "Raid Overview")

        self.changelog_frame = changelog_frame.ChangelogFrame(self._notebook)
        self._notebook.addTab(self.changelog_frame, "Changelog")

        self._notebook.setCurrentIndex(config.TAB_SELECTION)

        # System tray icon
        self._tray_icon = QSystemTrayIcon(self._app_icon, self)
        self._tray_icon.setToolTip("NinjaLooter " + config.VERSION)
        tray_menu = QMenu()
        self._tray_aot_action = tray_menu.addAction("Always On Top")
        self._tray_aot_action.setCheckable(True)
        self._tray_aot_action.setChecked(config.ALWAYS_ON_TOP)
        self._tray_aot_action.triggered.connect(self._on_tray_always_on_top)
        tray_menu.addSeparator()
        check_updates_action = tray_menu.addAction("Check for Updates")
        check_updates_action.triggered.connect(self._on_tray_check_updates)
        tray_menu.addSeparator()
        quit_action = tray_menu.addAction("Quit")
        quit_action.triggered.connect(self.close)
        self._tray_icon.setContextMenu(tray_menu)
        self._tray_icon.show()

        # Apply always-on-top
        if config.ALWAYS_ON_TOP:
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

        # Signals
        signals.title_changed.connect(self.setWindowTitle)
        signals.alert.connect(self._show_tray_notification)
        signals.show_raid_overview.connect(self._switch_to_raid_overview)
        signals.calc_raid_groups.connect(self._switch_to_raid_groups)

        # Start parse thread
        config.PARSER_THREAD = logparse.ParseThread()
        config.PARSER_THREAD.start()

        # Filesystem watcher for auto-detecting new/changed log files
        self._log_observer = None
        if os.path.isdir(config.LOG_DIRECTORY):
            self._start_log_observer(config.LOG_DIRECTORY)

        # Switch to Changelog tab on version bump
        try:
            last_run = semver.VersionInfo.parse(config.LAST_RUN_VERSION)
            current = semver.VersionInfo.parse(config.VERSION)
            if current > last_run:
                idx = self._notebook.indexOf(self.changelog_frame)
                if idx >= 0:
                    self._notebook.setCurrentIndex(idx)
                config.LAST_RUN_VERSION = config.VERSION
                config.CONF.set("default", "last_run_version", config.VERSION)
                config.write()
        except (ValueError, TypeError):
            config.LAST_RUN_VERSION = config.VERSION
            config.CONF.set("default", "last_run_version", config.VERSION)
            config.write()

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        apply_windows_window_frame(self, dark_mode=config.DARK_MODE)

    def update_always_on_top(self):
        flags = self.windowFlags() | Qt.WindowType.Window
        if config.ALWAYS_ON_TOP:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.show()
        self._tray_aot_action.setChecked(config.ALWAYS_ON_TOP)

    def update_fs_watcher(self, new_dir: str):
        if self._log_observer is not None:
            self._log_observer.stop()
            self._log_observer = None
        if os.path.isdir(new_dir):
            self._start_log_observer(new_dir)

    def _start_log_observer(self, directory: str):
        handler = _LogDirHandler(self)
        self._log_observer = Observer(timeout=1)
        self._log_observer.schedule(handler, directory, recursive=False)
        self._log_observer.daemon = True
        self._log_observer.start()

    def restart_parser(self):
        if config.PARSER_THREAD:
            config.PARSER_THREAD.abort()
        config.PARSER_THREAD = logparse.ParseThread()
        config.PARSER_THREAD.start()

    def _on_tray_always_on_top(self, checked: bool):
        config.ALWAYS_ON_TOP = checked
        config.CONF.set("default", "always_on_top", str(config.ALWAYS_ON_TOP))
        config.write()
        self.update_always_on_top()
        self._menu_bar.sync_always_on_top()

    def _on_tray_check_updates(self):
        autoupdate.check_update(notify_no_update=True)

    def _on_filesystem_event(self):
        if not config.AUTO_SWAP_LOGFILE:
            return
        logfile, name = utils.get_latest_logfile(config.LOG_DIRECTORY)
        if logfile and logfile != config.LATEST_LOGFILE:
            config.PLAYER_NAME = name
            config.LATEST_LOGFILE = logfile
            self.restart_parser()

    def _show_tray_notification(self, title: str, message: str, msec: int):
        if self._tray_icon.supportsMessages():
            self._tray_icon.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, msec)

    def _switch_to_raid_overview(self, _wholog=None):
        idx = self._notebook.indexOf(self.raid_ov_frame)
        if idx >= 0:
            self._notebook.setCurrentIndex(idx)

    def _switch_to_raid_groups(self):
        idx = self._notebook.indexOf(self.raidgroups_frame)
        if idx >= 0:
            self._notebook.setCurrentIndex(idx)

    def closeEvent(self, event: QCloseEvent) -> None:
        if config.CONFIRM_EXIT:
            reply = QMessageBox.question(
                self,
                "Confirm Exit",
                "Do you really want to close this application?",
                QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
            )
            if reply != QMessageBox.StandardButton.Ok:
                event.ignore()
                return

        config.TAB_SELECTION = self._notebook.currentIndex()
        utils.clear_alerts()
        if config.PARSER_THREAD:
            config.PARSER_THREAD.abort()
            config.PARSER_THREAD.join(timeout=2)
        utils.store_state()
        self._tray_icon.hide()
        event.accept()
