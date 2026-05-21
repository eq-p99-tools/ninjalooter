"""Fusion themes (dark / light) and semantic colors for the Qt UI.

Ported from p99-login-proxy and adapted with EQ auction/raid semantic colors.
"""

import ctypes
import logging
import platform
from ctypes import wintypes
from types import SimpleNamespace

from PySide6.QtGui import QColor, QPalette, QShowEvent
from PySide6.QtWidgets import QApplication, QFileDialog, QWidget

logger = logging.getLogger(__name__)

WINDOW_CHROME_RGB_DARK = (45, 45, 48)
WINDOW_CHROME_RGB_LIGHT = (243, 243, 243)

semantic = SimpleNamespace()

# QComboBox is intentionally omitted: any stylesheet on QComboBox switches it to "styled" mode and
# Fusion stops drawing the built-in dropdown indicator unless every subcontrol is replicated.
#
# QScrollBar is omitted so Fusion draws default scroll bars from the palette.
#
# QPushButton is omitted so Fusion draws default buttons from QPalette.Button / ButtonText.

_EXTRA_QSS_DARK = """
QTabWidget {
    background-color: #26262c;
}
QGroupBox {
    font-weight: bold;
    background-color: #2f2f36;
    border: 1px solid #555;
    border-radius: 6px;
    margin-top: 10px;
    padding-top: 8px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 6px;
}
QLineEdit, QPlainTextEdit, QTextEdit, QTextBrowser {
    background-color: #2a2a2e;
    color: #e6e6ea;
    border: 1px solid #555;
    border-radius: 4px;
    padding: 3px 6px;
    selection-background-color: #0d47a1;
    selection-color: #ffffff;
}
QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus, QTextBrowser:focus {
    border: 1px solid #4a9eff;
}
QLineEdit:disabled, QPlainTextEdit:disabled, QTextEdit:disabled, QTextBrowser:disabled {
    background-color: #323236;
    color: #888;
    border: 1px solid #444;
}
QTableView {
    gridline-color: #4a4a4a;
    background-color: #2a2a2e;
    alternate-background-color: #2a2a2e;
}
QHeaderView::section {
    background-color: #34343c;
    color: #d8d8dc;
    padding: 4px 6px;
    border: none;
    border-right: 1px solid #4a4a4a;
    border-bottom: 1px solid #4a4a4a;
    font-weight: 600;
}
QHeaderView::section:horizontal:last {
    border-right: none;
}
QTableCornerButton::section {
    background-color: #34343c;
    border-bottom: 1px solid #4a4a4a;
}
QTableView::item:selected {
    background-color: #0d47a1;
    color: #ffffff;
}
QCheckBox {
    spacing: 8px;
}
"""

_EXTRA_QSS_LIGHT = """
QTabWidget {
    background-color: #f0f0f0;
}
QGroupBox {
    font-weight: bold;
    background-color: #fafafa;
    border: 1px solid #c0c0c0;
    border-radius: 6px;
    margin-top: 10px;
    padding-top: 8px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 6px;
}
QLineEdit, QPlainTextEdit, QTextEdit, QTextBrowser {
    background-color: #ffffff;
    color: #202020;
    border: 1px solid #c0c0c0;
    border-radius: 4px;
    padding: 3px 6px;
    selection-background-color: #0078d7;
    selection-color: #ffffff;
}
QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus, QTextBrowser:focus {
    border: 1px solid #0078d7;
}
QLineEdit:disabled, QPlainTextEdit:disabled, QTextEdit:disabled, QTextBrowser:disabled {
    background-color: #f5f5f5;
    color: #a0a0a0;
    border: 1px solid #d0d0d0;
}
QTableView {
    gridline-color: #c8c8c8;
    background-color: #ffffff;
    alternate-background-color: #ffffff;
}
QHeaderView::section {
    background-color: #e6e6e6;
    color: #202020;
    padding: 4px 6px;
    border: none;
    border-right: 1px solid #c8c8c8;
    border-bottom: 1px solid #b8b8b8;
    font-weight: 600;
}
QHeaderView::section:horizontal:last {
    border-right: none;
}
QTableCornerButton::section {
    background-color: #e6e6e6;
    border-bottom: 1px solid #b8b8b8;
}
QTableView::item:selected {
    background-color: #0078d7;
    color: #ffffff;
}
QCheckBox {
    spacing: 8px;
}
"""

_REGION_DEBUG_QSS = """
QMainWindow {
    background-color: #ff0000;
}
QMainWindow > QWidget {
    background-color: #00ff00;
}
QTabWidget {
    background-color: #0000ff;
}
QTabWidget::pane {
    background-color: #ffff00;
}
QGroupBox {
    background-color: #ff00ff;
}
QLineEdit, QPlainTextEdit, QTextEdit, QTextBrowser {
    background-color: #00ffff;
}
QTableView {
    background-color: #ff8800;
}
QHeaderView::section {
    background-color: #ffffff;
    color: #000000;
}
"""

_region_debug_easter_active = False


def toggle_region_debug_easter_egg() -> bool:
    """Toggle the region-color debug QSS overlay. Returns the new active state."""
    global _region_debug_easter_active
    _region_debug_easter_active = not _region_debug_easter_active
    logger.debug("Region color debug easter egg: %s", _region_debug_easter_active)
    return _region_debug_easter_active


def _populate_semantic(*, dark: bool) -> None:
    """Fill `semantic` for auction timer tints and general UI colors."""
    if dark:
        semantic.timer_safe = QColor(46, 80, 56)
        semantic.timer_warn = QColor(90, 74, 26)
        semantic.timer_danger = QColor(90, 32, 32)
        semantic.base_row = QColor(35, 35, 40)
        semantic.alt_row = QColor(42, 45, 52)
        semantic.changelog_bg = "#252526"
        semantic.changelog_fg = "#d4d4d4"
        semantic.muted = QColor(158, 158, 158)
        semantic.group_header = QColor(50, 55, 70)
    else:
        semantic.timer_safe = QColor(204, 226, 203)
        semantic.timer_warn = QColor(246, 234, 194)
        semantic.timer_danger = QColor(255, 174, 165)
        semantic.base_row = QColor(255, 255, 200)
        semantic.alt_row = QColor(208, 224, 255)
        semantic.changelog_bg = "#ffffff"
        semantic.changelog_fg = "#202020"
        semantic.muted = QColor(97, 97, 97)
        semantic.group_header = QColor(146, 180, 230)


def apply_app_theme(app: QApplication, *, dark_mode: bool) -> None:
    """Apply Fusion + palette + QSS + semantic colors for dark or light mode."""
    _populate_semantic(dark=dark_mode)
    app.setStyle("Fusion")
    pal = QPalette()

    if dark_mode:
        pal.setColor(QPalette.ColorRole.Window, QColor(*WINDOW_CHROME_RGB_DARK))
        pal.setColor(QPalette.ColorRole.WindowText, QColor(230, 230, 230))
        pal.setColor(QPalette.ColorRole.Base, QColor(42, 42, 46))
        pal.setColor(QPalette.ColorRole.AlternateBase, QColor(55, 58, 68))
        pal.setColor(QPalette.ColorRole.Text, QColor(230, 230, 230))
        pal.setColor(QPalette.ColorRole.PlaceholderText, QColor(140, 140, 140))
        pal.setColor(QPalette.ColorRole.ToolTipBase, QColor(60, 60, 65))
        pal.setColor(QPalette.ColorRole.ToolTipText, QColor(240, 240, 240))
        pal.setColor(QPalette.ColorRole.Button, QColor(58, 58, 62))
        pal.setColor(QPalette.ColorRole.ButtonText, QColor(235, 235, 235))
        pal.setColor(QPalette.ColorRole.BrightText, QColor(255, 80, 80))
        pal.setColor(QPalette.ColorRole.Link, QColor(100, 180, 255))
        pal.setColor(QPalette.ColorRole.Highlight, QColor(0, 120, 215))
        pal.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        pal.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(127, 127, 127))
        pal.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(127, 127, 127))
        pal.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(127, 127, 127))
    else:
        pal.setColor(QPalette.ColorRole.Window, QColor(*WINDOW_CHROME_RGB_LIGHT))
        pal.setColor(QPalette.ColorRole.WindowText, QColor(30, 30, 30))
        pal.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
        pal.setColor(QPalette.ColorRole.AlternateBase, QColor(232, 240, 252))
        pal.setColor(QPalette.ColorRole.Text, QColor(30, 30, 30))
        pal.setColor(QPalette.ColorRole.PlaceholderText, QColor(120, 120, 120))
        pal.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 220))
        pal.setColor(QPalette.ColorRole.ToolTipText, QColor(30, 30, 30))
        pal.setColor(QPalette.ColorRole.Button, QColor(225, 225, 225))
        pal.setColor(QPalette.ColorRole.ButtonText, QColor(30, 30, 30))
        pal.setColor(QPalette.ColorRole.BrightText, QColor(200, 0, 0))
        pal.setColor(QPalette.ColorRole.Link, QColor(0, 102, 204))
        pal.setColor(QPalette.ColorRole.Highlight, QColor(0, 120, 215))
        pal.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        pal.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(150, 150, 150))
        pal.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(150, 150, 150))
        pal.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(150, 150, 150))

    app.setPalette(pal)
    qss = _EXTRA_QSS_DARK if dark_mode else _EXTRA_QSS_LIGHT
    if _region_debug_easter_active:
        qss += _REGION_DEBUG_QSS
    app.setStyleSheet(qss)


def apply_windows_window_frame(widget: QWidget, *, dark_mode: bool) -> None:
    """Tune native Windows title bar to match app (dark or light) via DWM."""
    if platform.system() != "Windows":
        return
    try:
        hwnd = int(widget.winId())
    except (TypeError, ValueError):
        return
    if hwnd == 0:
        return

    dwm = ctypes.windll.dwmapi
    DWMWA_USE_IMMERSIVE_DARK_MODE = 20
    DWMWA_BORDER_COLOR = 34
    DWMWA_CAPTION_COLOR = 35

    def _set_attr(attr: int, data, size: int) -> None:
        hr = dwm.DwmSetWindowAttribute(
            wintypes.HWND(hwnd),
            wintypes.DWORD(attr),
            data,
            wintypes.DWORD(size),
        )
        if hr != 0:
            logger.debug("DwmSetWindowAttribute attr=%s hr=%#x", attr, hr & 0xFFFFFFFF)

    use_dark = ctypes.c_int(1 if dark_mode else 0)
    _set_attr(DWMWA_USE_IMMERSIVE_DARK_MODE, ctypes.byref(use_dark), ctypes.sizeof(use_dark))

    rgb = WINDOW_CHROME_RGB_DARK if dark_mode else WINDOW_CHROME_RGB_LIGHT
    r, g, b = rgb
    colorref = wintypes.DWORD(r | (g << 8) | (b << 16))
    _set_attr(DWMWA_CAPTION_COLOR, ctypes.byref(colorref), ctypes.sizeof(colorref))
    _set_attr(DWMWA_BORDER_COLOR, ctypes.byref(colorref), ctypes.sizeof(colorref))


class ThemedQFileDialog(QFileDialog):
    """QFileDialog that optionally uses a non-native Qt dialog with themed DWM title bar."""

    def __init__(self, parent: QWidget | None, *, dark_mode: bool, qt_dialogs: bool = True):
        super().__init__(parent)
        self._dark_mode = dark_mode
        self._qt_dialogs = qt_dialogs
        if qt_dialogs:
            self.setOption(QFileDialog.Option.DontUseNativeDialog, True)

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        if self._qt_dialogs:
            apply_windows_window_frame(self, dark_mode=self._dark_mode)


_populate_semantic(dark=True)
