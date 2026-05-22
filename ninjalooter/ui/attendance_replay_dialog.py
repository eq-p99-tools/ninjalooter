import datetime

from PySide6.QtCore import QDateTime, QThread, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateTimeEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from ninjalooter import config, logger, logreplay, utils
from ninjalooter.app_signals import signals
from ninjalooter.ui.theme import apply_windows_window_frame

LOG = logger.getLogger(__name__)


class _ScanThread(QThread):
    """Runs attendance scan in background."""

    finished_signal = Signal(object)

    def __init__(self, lines, start_time, end_time, parent=None):
        super().__init__(parent)
        self._lines = lines
        self._start = start_time
        self._end = end_time

    def run(self):
        result = logreplay.scan_attendance(self._lines, self._start, self._end)
        self.finished_signal.emit(result)


class _ImportThread(QThread):
    """Runs replay (commit) in background."""

    finished_signal = Signal()

    def __init__(self, lines, start_time, end_time, full_replay=False, parent=None):
        super().__init__(parent)
        self._lines = lines
        self._start = start_time
        self._end = end_time
        self._full_replay = full_replay
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def _is_cancelled(self, cur, tot):  # pylint: disable=unused-argument
        return not self._cancelled

    def run(self):
        if self._full_replay:
            logreplay.replay_full(
                self._lines,
                self._start,
                self._end,
                progress_callback=self._is_cancelled,
            )
        else:
            logreplay.replay_attendance(
                self._lines,
                self._start,
                self._end,
                progress_callback=self._is_cancelled,
            )
        if not self._cancelled:
            self.finished_signal.emit()


class AttendanceReplayDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Replay Attendance Log")
        self.setMinimumWidth(420)
        apply_windows_window_frame(self, dark_mode=config.DARK_MODE)

        self._logfiles = utils.enumerate_logfiles(config.LOG_DIRECTORY)
        self._lines = None
        self._file_start = None
        self._file_end = None
        self._thread = None
        self._cached_scan = None
        self._cached_start = None
        self._cached_end = None

        layout = QVBoxLayout(self)

        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        # Character dropdown
        self._char_combo = QComboBox()
        self._char_combo.setMaxVisibleItems(12)
        self._char_combo.setStyleSheet("QComboBox { combobox-popup: 0; }")
        for filepath, charname, server, _mtime in self._logfiles:
            self._char_combo.addItem(f"{charname} ({server})", userData=filepath)
        self._char_combo.currentIndexChanged.connect(self._on_char_changed)
        form.addRow("Character:", self._char_combo)

        # Time bounds (read-only)
        self._bounds_label = QLabel("—")
        form.addRow("File range:", self._bounds_label)

        # Start / End pickers
        self._start_edit = QDateTimeEdit()
        self._start_edit.setCalendarPopup(True)
        self._start_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        form.addRow("Start:", self._start_edit)

        self._end_edit = QDateTimeEdit()
        self._end_edit.setCalendarPopup(True)
        self._end_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        form.addRow("End:", self._end_edit)

        layout.addLayout(form)

        # Quick-range buttons
        quick_layout = QHBoxLayout()
        quick_layout.addWidget(QLabel("Last:"))
        for label, hours in (("1h", 1), ("6h", 6), ("24h", 24), ("1w", 168), ("1m", 720)):
            btn = QPushButton(label)
            btn.setFixedWidth(48)
            btn.clicked.connect(lambda checked=False, h=hours: self._set_quick_range(h))
            quick_layout.addWidget(btn)
        quick_layout.addStretch()
        layout.addLayout(quick_layout)

        # Include auctions checkbox
        self._auctions_check = QCheckBox("Include auctions (full replay)")
        self._auctions_check.stateChanged.connect(self._invalidate_cache)
        layout.addWidget(self._auctions_check)

        # Scan button + results
        scan_layout = QHBoxLayout()
        self._scan_btn = QPushButton("Scan")
        self._scan_btn.clicked.connect(self._on_scan)
        scan_layout.addWidget(self._scan_btn)

        self._result_label = QLabel("")
        scan_layout.addWidget(self._result_label, 1)
        layout.addLayout(scan_layout)

        # Import / Cancel
        self._button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        self._import_btn = self._button_box.addButton("Import", QDialogButtonBox.ButtonRole.AcceptRole)
        self._import_btn.setEnabled(False)
        self._button_box.accepted.connect(self._on_accept)
        self._button_box.rejected.connect(self._on_close)
        layout.addWidget(self._button_box)

        # Load initial file if any
        if self._logfiles:
            self._on_char_changed(0)
        else:
            self._scan_btn.setEnabled(False)
            self._bounds_label.setText("No log files found in log directory.")

    def _invalidate_cache(self):
        self._cached_scan = None
        self._cached_start = None
        self._cached_end = None
        self._import_btn.setEnabled(False)
        self._result_label.setText("")

    def _on_char_changed(self, index):
        if index < 0 or index >= len(self._logfiles):
            return
        filepath = self._char_combo.itemData(index)
        self._invalidate_cache()

        try:
            with open(filepath, encoding="utf-8", errors="replace") as f:
                self._lines = f.readlines()
        except OSError:
            LOG.exception("Failed to read log file: %s", filepath)
            self._lines = None
            self._bounds_label.setText("Error reading file.")
            self._scan_btn.setEnabled(False)
            return

        self._file_start = utils.get_first_timestamp(self._lines)
        self._file_end = utils.get_first_timestamp(reversed(self._lines))
        epoch = datetime.datetime.fromtimestamp(0)

        if epoch in (self._file_start, self._file_end):
            self._bounds_label.setText("No valid timestamps found in file.")
            self._scan_btn.setEnabled(False)
            return

        self._scan_btn.setEnabled(True)
        self._bounds_label.setText(
            f"{self._file_start.strftime('%Y-%m-%d %H:%M')} — {self._file_end.strftime('%Y-%m-%d %H:%M')}"
        )

        qt_start = QDateTime(self._file_start)
        qt_end = QDateTime(self._file_end)
        self._start_edit.setDateTimeRange(qt_start, qt_end)
        self._end_edit.setDateTimeRange(qt_start, qt_end)
        self._start_edit.setDateTime(qt_start)
        self._end_edit.setDateTime(qt_end)

    def _set_quick_range(self, hours):
        if self._file_end is None:
            return
        new_start = max(
            self._file_end - datetime.timedelta(hours=hours),
            self._file_start,
        )
        self._start_edit.setDateTime(QDateTime(new_start))
        self._end_edit.setDateTime(QDateTime(self._file_end))

    def _on_scan(self):
        if self._lines is None:
            return
        start = self._start_edit.dateTime().toPython()
        end = self._end_edit.dateTime().toPython()

        self._scan_btn.setEnabled(False)
        self._result_label.setText("Scanning...")

        self._thread = _ScanThread(self._lines, start, end, parent=self)
        self._thread.finished_signal.connect(self._on_scan_done)
        self._thread.start()

    def _on_scan_done(self, scan_result):
        self._thread = None
        self._scan_btn.setEnabled(True)

        start = self._start_edit.dateTime().toPython()
        end = self._end_edit.dateTime().toPython()
        self._cached_scan = scan_result
        self._cached_start = start
        self._cached_end = end

        parts = [
            f"{scan_result.total_whos} /who snapshot(s)",
            f"{scan_result.raidtick_whos} raid tick(s)",
        ]
        if scan_result.creditt_count:
            parts.append(f"{scan_result.creditt_count} creditt(s)")
        if scan_result.gratss_count:
            parts.append(f"{scan_result.gratss_count} gratss")
        self._result_label.setText("Found " + ", ".join(parts))
        has_data = scan_result.total_whos > 0 or scan_result.creditt_count > 0 or scan_result.gratss_count > 0
        self._import_btn.setEnabled(has_data)

    def _on_accept(self):
        if self._lines is None or self._cached_scan is None:
            return

        start = self._start_edit.dateTime().toPython()
        end = self._end_edit.dateTime().toPython()

        # Use cached range if unchanged, otherwise re-scan is needed
        if start != self._cached_start or end != self._cached_end:
            self._invalidate_cache()
            self._result_label.setText("Time range changed — please scan again.")
            return

        self._import_btn.setEnabled(False)
        self._scan_btn.setEnabled(False)
        self._char_combo.setEnabled(False)
        self._start_edit.setEnabled(False)
        self._end_edit.setEnabled(False)
        self._result_label.setText("Importing...")

        full = self._auctions_check.isChecked()
        self._thread = _ImportThread(
            self._lines, start, end, full_replay=full, parent=self
        )
        self._thread.finished_signal.connect(self._on_import_done)
        self._thread.start()

    def _on_import_done(self):
        self._thread = None
        signals.who_history.emit()
        # Switch to Attendance Logs tab
        window = self.parent()
        if window and hasattr(window, "_notebook"):
            window._notebook.setCurrentIndex(1)
        self.accept()

    def _on_close(self):
        if self._thread and self._thread.isRunning():
            self._thread.cancel()
            self._thread.wait(3000)
        self.reject()

    def closeEvent(self, event):
        if self._thread and self._thread.isRunning():
            self._thread.cancel()
            self._thread.wait(3000)
        super().closeEvent(event)
