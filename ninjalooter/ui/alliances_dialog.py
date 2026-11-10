"""Edit the alliance list and compare it with the list shipped in this version."""

from __future__ import annotations

import collections

from PySide6.QtCore import Qt
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ninjalooter import config
from ninjalooter.app_signals import signals
from ninjalooter.ui.theme import apply_windows_window_frame

_FORBIDDEN = ":;,"


def _invalid_token(text: str) -> bool:
    return any(character in text for character in _FORBIDDEN)


class AlliancesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Alliances")
        self.setMinimumSize(860, 560)
        self._shipped = config.shipped_alliances()
        self._home = {}
        for alliance_name, guilds in self._shipped.items():
            for guild in guilds:
                self._home[guild] = alliance_name
        self._yours = collections.OrderedDict((name, list(guilds)) for name, guilds in config.ALLIANCES.items())

        root = QVBoxLayout(self)
        root.setSpacing(8)

        self._summary = QLabel()
        self._summary.setWordWrap(True)
        root.addWidget(self._summary)

        columns = QHBoxLayout()
        root.addLayout(columns, stretch=1)
        columns.addLayout(self._build_yours_column(), stretch=1)
        columns.addLayout(self._build_shipped_column(), stretch=1)

        self._move_label = QLabel("")
        self._move_label.setWordWrap(True)
        root.addWidget(self._move_label)

        buttons = QHBoxLayout()
        buttons.addStretch()
        save_button = QPushButton("Save")
        reset_button = QPushButton("Reset to defaults")
        cancel_button = QPushButton("Cancel")
        save_button.clicked.connect(self._save)
        reset_button.clicked.connect(self._reset)
        cancel_button.clicked.connect(self.reject)
        buttons.addWidget(save_button)
        buttons.addWidget(reset_button)
        buttons.addWidget(cancel_button)
        root.addLayout(buttons)

        self._reload(select=next(iter(self._yours), None))
        if config.ALWAYS_ON_TOP:
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        apply_windows_window_frame(self, dark_mode=config.DARK_MODE)

    def _build_yours_column(self) -> QVBoxLayout:
        column = QVBoxLayout()
        title = QLabel("Yours")
        title_font = title.font()
        title_font.setBold(True)
        title.setFont(title_font)
        column.addWidget(title)

        alliance_row = QHBoxLayout()
        self._yours_alliances = QListWidget()
        self._yours_alliances.currentRowChanged.connect(self._on_yours_alliance_changed)
        self._yours_alliances.itemDoubleClicked.connect(self._rename_alliance)
        alliance_row.addWidget(self._yours_alliances, stretch=1)

        alliance_buttons = QVBoxLayout()
        add_alliance = QPushButton("Add")
        self._remove_alliance_button = QPushButton("Remove")
        self._up_button = QPushButton("Up")
        self._down_button = QPushButton("Down")
        add_alliance.clicked.connect(self._add_alliance)
        self._remove_alliance_button.clicked.connect(self._remove_alliance)
        self._up_button.clicked.connect(lambda: self._move_alliance(-1))
        self._down_button.clicked.connect(lambda: self._move_alliance(1))
        for button in (add_alliance, self._remove_alliance_button, self._up_button, self._down_button):
            alliance_buttons.addWidget(button)
        alliance_buttons.addStretch()
        alliance_row.addLayout(alliance_buttons)
        column.addLayout(alliance_row)

        self._yours_guild_label = QLabel("Guilds")
        guild_font = self._yours_guild_label.font()
        guild_font.setBold(True)
        self._yours_guild_label.setFont(guild_font)
        column.addWidget(self._yours_guild_label)

        self._yours_guilds = QListWidget()
        column.addWidget(self._yours_guilds, stretch=1)

        guild_row = QHBoxLayout()
        self._guild_edit = QLineEdit()
        self._guild_edit.setPlaceholderText("Guild tag")
        self._guild_edit.returnPressed.connect(self._add_guild)
        add_guild = QPushButton("Add guild")
        remove_guild = QPushButton("Remove guild")
        add_guild.clicked.connect(self._add_guild)
        remove_guild.clicked.connect(self._remove_guild)
        guild_row.addWidget(self._guild_edit, stretch=1)
        guild_row.addWidget(add_guild)
        guild_row.addWidget(remove_guild)
        column.addLayout(guild_row)
        return column

    def _build_shipped_column(self) -> QVBoxLayout:
        column = QVBoxLayout()
        title = QLabel("Shipped with this version")
        title_font = title.font()
        title_font.setBold(True)
        title.setFont(title_font)
        column.addWidget(title)

        self._shipped_alliances = QListWidget()
        self._shipped_alliances.currentRowChanged.connect(self._on_shipped_alliance_changed)
        for name in self._shipped:
            self._shipped_alliances.addItem(name)
        column.addWidget(self._shipped_alliances)

        self._shipped_guild_label = QLabel("Guilds")
        guild_font = self._shipped_guild_label.font()
        guild_font.setBold(True)
        self._shipped_guild_label.setFont(guild_font)
        column.addWidget(self._shipped_guild_label)

        self._shipped_guilds = QListWidget()
        column.addWidget(self._shipped_guilds, stretch=1)

        self._hint = QLabel("")
        self._hint.setWordWrap(True)
        column.addWidget(self._hint)
        # Keep the column aligned with the guild-entry row on the left.
        spacer = QWidget()
        spacer.setFixedHeight(self._guild_edit.sizeHint().height())
        column.addWidget(spacer)
        return column

    def _selected_alliance(self) -> str | None:
        item = self._yours_alliances.currentItem()
        if item is None:
            return None
        return item.text()

    def _reload(self, select: str | None = None, guild: str | None = None):
        self._move_label.setText("")
        names = list(self._yours)
        if select not in names:
            select = names[0] if names else None
        self._fill(self._yours_alliances, names, select)
        self._show_yours(select, guild)
        self._sync_shipped_selection(select)
        self._summary.setText(self._summary_text())
        self._update_alliance_buttons()

    def _fill(self, widget: QListWidget, names: list[str], select: str | None):
        widget.blockSignals(True)
        widget.clear()
        widget.addItems(names)
        if select:
            matches = widget.findItems(select, Qt.MatchFlag.MatchExactly)
            if matches:
                widget.setCurrentItem(matches[0])
        elif widget.count():
            widget.setCurrentRow(0)
        widget.blockSignals(False)

    def _summary_text(self) -> str:
        if config.alliances_match(self._yours, self._shipped):
            prefix = "Using the version defaults."
        else:
            prefix = "Custom alliances."
        return prefix + " A guild counts in one alliance."

    def _show_yours(self, name: str | None, guild: str | None = None):
        self._yours_guilds.clear()
        if not name:
            self._yours_guild_label.setText("Guilds")
            self._hint.setText("")
            return
        self._yours_guild_label.setText(f"Guilds in {name}")
        self._yours_guilds.addItems(self._yours.get(name, []))
        if guild:
            matches = self._yours_guilds.findItems(guild, Qt.MatchFlag.MatchExactly)
            if matches:
                self._yours_guilds.setCurrentItem(matches[0])
        self._hint.setText(self._comparison_hint(name))

    def _sync_shipped_selection(self, name: str | None):
        if name in self._shipped:
            matches = self._shipped_alliances.findItems(name, Qt.MatchFlag.MatchExactly)
            if matches:
                self._shipped_alliances.setCurrentItem(matches[0])
                return
        if self._shipped_alliances.currentRow() < 0 and self._shipped_alliances.count():
            self._shipped_alliances.setCurrentRow(0)

    def _comparison_hint(self, name: str) -> str:
        yours = list(self._yours.get(name, []))
        if name in self._shipped:
            shipped = list(self._shipped[name])
            if yours == shipped:
                return "Same guilds as this version."
            only_shipped = [guild for guild in shipped if guild not in yours]
            only_yours = [guild for guild in yours if guild not in shipped]
            if len(only_shipped) == 1 and not only_yours:
                return f"{only_shipped[0]} is inside {name} in this version."
            if len(only_yours) == 1 and not only_shipped:
                return f"{only_yours[0]} is not in {name} in this version."
            return "Guilds differ from this version."
        homes = {self._home[guild] for guild in yours if guild in self._home}
        if len(yours) == 1 and len(homes) == 1:
            return f"{yours[0]} is inside {next(iter(homes))} in this version."
        return f"{name} is not in this version."

    def _update_alliance_buttons(self):
        count = len(self._yours)
        row = self._yours_alliances.currentRow()
        self._remove_alliance_button.setEnabled(count > 1 and row >= 0)
        self._up_button.setEnabled(row > 0)
        self._down_button.setEnabled(row >= 0 and row < count - 1)

    def _on_yours_alliance_changed(self, _row: int):
        name = self._selected_alliance()
        self._show_yours(name)
        self._sync_shipped_selection(name)
        self._update_alliance_buttons()

    def _on_shipped_alliance_changed(self, _row: int):
        item = self._shipped_alliances.currentItem()
        self._shipped_guilds.clear()
        if item is None:
            self._shipped_guild_label.setText("Guilds")
            return
        name = item.text()
        self._shipped_guild_label.setText(f"Guilds in {name}")
        self._shipped_guilds.addItems(self._shipped.get(name, []))

    def _warn(self, message: str):
        QMessageBox.warning(self, "Edit Alliances", message)

    def _add_alliance(self):
        name, ok = self._ask_name("Add alliance", "Alliance name:")
        if not ok:
            return
        if name in self._yours:
            self._warn(f"{name} is already an alliance.")
            return
        self._yours[name] = []
        self._reload(select=name)

    def _rename_alliance(self, _item=None):
        current = self._selected_alliance()
        if current is None:
            return
        name, ok = self._ask_name("Rename alliance", "Alliance name:", current)
        if not ok or name == current:
            return
        if name in self._yours:
            self._warn(f"{name} is already an alliance.")
            return
        renamed = collections.OrderedDict()
        for alliance_name, guilds in self._yours.items():
            renamed[name if alliance_name == current else alliance_name] = guilds
        self._yours = renamed
        self._reload(select=name)

    def _ask_name(self, title: str, label: str, text: str = "") -> tuple[str, bool]:
        name, ok = QInputDialog.getText(self, title, label, text=text)
        name = name.strip()
        if not ok:
            return "", False
        if not name:
            self._warn("The alliance name cannot be empty.")
            return "", False
        if _invalid_token(name):
            self._warn("Alliance names cannot include colon, semicolon, or comma.")
            return "", False
        return name, True

    def _remove_alliance(self):
        name = self._selected_alliance()
        if name is None or len(self._yours) <= 1:
            return
        del self._yours[name]
        self._reload()

    def _move_alliance(self, delta: int):
        names = list(self._yours)
        row = self._yours_alliances.currentRow()
        target = row + delta
        if row < 0 or target < 0 or target >= len(names):
            return
        names[row], names[target] = names[target], names[row]
        self._yours = collections.OrderedDict((alliance_name, self._yours[alliance_name]) for alliance_name in names)
        self._reload(select=names[target])

    def _add_guild(self):
        name = self._selected_alliance()
        guild = self._guild_edit.text().strip()
        if name is None or not guild:
            return
        if _invalid_token(guild):
            self._warn("Guild tags cannot include colon, semicolon, or comma.")
            return
        moved_from = None
        for other, guilds in self._yours.items():
            if other != name and guild in guilds:
                guilds.remove(guild)
                moved_from = other
        if guild not in self._yours[name]:
            self._yours[name].append(guild)
        self._guild_edit.clear()
        self._reload(select=name, guild=guild)
        if moved_from:
            self._move_label.setText(f"Moved {guild} out of {moved_from}.")

    def _remove_guild(self):
        name = self._selected_alliance()
        item = self._yours_guilds.currentItem()
        if name is None or item is None:
            return
        guild = item.text()
        self._yours[name] = [entry for entry in self._yours[name] if entry != guild]
        self._reload(select=name)

    def _save(self):
        config.save_alliances(self._yours)
        signals.alliances_changed.emit()
        signals.alliance_changed.emit(config.DEFAULT_ALLIANCE)
        self.accept()

    def _reset(self):
        reply = QMessageBox.question(
            self,
            "Reset alliances",
            "Replace your alliances with the ones shipped in this version?\nThis clears the custom alliance settings.",
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
        )
        if reply != QMessageBox.StandardButton.Ok:
            return
        config.reset_alliances()
        self._yours = collections.OrderedDict((name, list(guilds)) for name, guilds in config.ALLIANCES.items())
        self._move_label.setText("")
        self._reload(select=next(iter(self._yours), None))
        signals.alliances_changed.emit()
        signals.alliance_changed.emit(config.DEFAULT_ALLIANCE)
