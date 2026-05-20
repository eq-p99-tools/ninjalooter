"""Reusable table model and view components replacing ObjectListView3.

Provides:
- ObjectTableModel: QAbstractTableModel backed by a list of objects
- SortFilterProxyModel: QSortFilterProxyModel with column-aware sorting
- ObjectTableView: QTableView preconfigured for common ninjaLooter patterns
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QSortFilterProxyModel, Qt
from PySide6.QtWidgets import QAbstractItemView, QApplication, QLabel, QTableView

from ninjalooter.ui.theme import semantic


@dataclass
class ColumnDefn:
    title: str
    value_getter: str | Callable
    width: int = -1
    formatter: Callable | None = None
    string_converter: Callable | None = None
    center: bool = False


class ObjectTableModel(QAbstractTableModel):
    """Table model backed by a list of objects with column definitions."""

    def __init__(self, columns: list[ColumnDefn], parent=None):
        super().__init__(parent)
        self._columns = columns
        self._objects: list = []
        self._row_color_func: Callable | None = None

    def set_row_color_func(self, func: Callable | None):
        self._row_color_func = func

    def set_objects(self, objects: list):
        self.beginResetModel()
        self._objects = list(objects)
        self.endResetModel()

    def add_object(self, obj):
        row = len(self._objects)
        self.beginInsertRows(QModelIndex(), row, row)
        self._objects.append(obj)
        self.endInsertRows()

    def remove_object(self, obj):
        try:
            row = self._objects.index(obj)
        except ValueError:
            return
        self.beginRemoveRows(QModelIndex(), row, row)
        self._objects.pop(row)
        self.endRemoveRows()

    def refresh_object(self, obj):
        try:
            row = self._objects.index(obj)
        except ValueError:
            return
        left = self.index(row, 0)
        right = self.index(row, self.columnCount() - 1)
        self.dataChanged.emit(left, right)

    def refresh_all(self):
        if self._objects:
            self.dataChanged.emit(
                self.index(0, 0),
                self.index(self.rowCount() - 1, self.columnCount() - 1),
            )

    def get_object(self, row: int):
        if 0 <= row < len(self._objects):
            return self._objects[row]
        return None

    def get_objects(self) -> list:
        return list(self._objects)

    def rowCount(self, parent=QModelIndex()):
        return len(self._objects)

    def columnCount(self, parent=QModelIndex()):
        return len(self._columns)

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        obj = self._objects[index.row()]
        col = self._columns[index.column()]

        if role == Qt.ItemDataRole.DisplayRole:
            value = self._get_value(obj, col)
            if col.formatter:
                return col.formatter(value)
            if col.string_converter:
                return col.string_converter(obj)
            if value is None:
                return ""
            return str(value)

        if role == Qt.ItemDataRole.BackgroundRole:
            if self._row_color_func:
                color = self._row_color_func(obj)
                if color:
                    return color
            if index.row() % 2 == 1:
                return semantic.alt_row
            return semantic.base_row

        if role == Qt.ItemDataRole.TextAlignmentRole and col.center:
            return Qt.AlignmentFlag.AlignCenter

        if role == Qt.ItemDataRole.UserRole:
            return self._get_value(obj, col)

        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal:
            if role == Qt.ItemDataRole.DisplayRole:
                if 0 <= section < len(self._columns):
                    return self._columns[section].title
            if role == Qt.ItemDataRole.TextAlignmentRole:
                return int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        return None

    def sort(self, column, order=Qt.SortOrder.AscendingOrder):
        if 0 <= column < len(self._columns):
            self.beginResetModel()
            col = self._columns[column]
            reverse = order == Qt.SortOrder.DescendingOrder
            try:
                self._objects.sort(
                    key=lambda obj: self._sort_key(obj, col),
                    reverse=reverse,
                )
            except TypeError:
                pass
            self.endResetModel()

    def _get_value(self, obj, col: ColumnDefn):
        if callable(col.value_getter):
            return col.value_getter(obj)
        return getattr(obj, col.value_getter, None)

    def _sort_key(self, obj, col: ColumnDefn):
        val = self._get_value(obj, col)
        if val is None:
            return ""
        return val


class SortFilterProxyModel(QSortFilterProxyModel):
    """Proxy model that supports predicate-based filtering."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._filter_func: Callable | None = None
        self.setSortRole(Qt.ItemDataRole.UserRole)

    def lessThan(self, left: QModelIndex, right: QModelIndex) -> bool:
        left_data = left.data(self.sortRole())
        right_data = right.data(self.sortRole())
        if left_data is None:
            return True
        if right_data is None:
            return False
        try:
            return left_data < right_data
        except TypeError:
            return str(left_data) < str(right_data)

    def set_filter_func(self, func: Callable | None):
        self._filter_func = func
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        if self._filter_func is None:
            return True
        source_model = self.sourceModel()
        if isinstance(source_model, ObjectTableModel):
            obj = source_model.get_object(source_row)
            if obj is not None:
                return self._filter_func(obj)
        return True


class ObjectTableView(QTableView):
    """QTableView preconfigured with common defaults."""

    def __init__(self, columns: list[ColumnDefn], parent=None, sortable=True, single_select=True, empty_text: str = ""):
        super().__init__(parent)
        self._model = ObjectTableModel(columns, self)

        if sortable:
            self._proxy = SortFilterProxyModel(self)
            self._proxy.setSourceModel(self._model)
            self.setModel(self._proxy)
            self.setSortingEnabled(True)
        else:
            self._proxy = None
            self.setModel(self._model)

        if single_select:
            self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(22)
        header = self.horizontalHeader()
        header.setStretchLastSection(True)
        header_font = header.font()
        header_font.setPointSize(header_font.pointSize() + 1)
        header.setFont(header_font)

        for i, col in enumerate(columns):
            if col.width > 0:
                self.setColumnWidth(i, col.width)

        self._empty_label: QLabel | None = None
        if empty_text:
            self._empty_label = QLabel(empty_text, self.viewport())
            self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._empty_label.setStyleSheet("font-size: 18px; font-weight: bold; color: rgba(150, 150, 150, 160);")
            self._empty_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            self._model.rowsInserted.connect(self._update_empty_label)
            self._model.rowsRemoved.connect(self._update_empty_label)
            self._model.modelReset.connect(self._update_empty_label)
            self._update_empty_label()

    def _update_empty_label(self):
        if self._empty_label:
            self._empty_label.setVisible(self._model.rowCount() == 0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._empty_label:
            self._empty_label.setGeometry(self.viewport().rect())

    @property
    def object_model(self) -> ObjectTableModel:
        return self._model

    @property
    def proxy_model(self) -> SortFilterProxyModel | None:
        return self._proxy

    def set_objects(self, objects: list):
        self._model.set_objects(objects)

    def get_selected_object(self):
        indexes = self.selectionModel().selectedRows()
        if not indexes:
            return None
        index = indexes[0]
        if self._proxy:
            index = self._proxy.mapToSource(index)
        return self._model.get_object(index.row())

    def select_object(self, obj):
        try:
            row = self._model._objects.index(obj)
        except ValueError:
            return
        if self._proxy:
            source_index = self._model.index(row, 0)
            proxy_index = self._proxy.mapFromSource(source_index)
            self.selectRow(proxy_index.row())
        else:
            self.selectRow(row)

    def set_filter_func(self, func: Callable | None):
        if self._proxy:
            self._proxy.set_filter_func(func)

    def copy_selected_to_clipboard(self, formatter: Callable | None = None):
        obj = self.get_selected_object()
        if obj is None:
            return
        if formatter:
            text = formatter(obj)
        else:
            text = str(obj)
        QApplication.clipboard().setText(text)
