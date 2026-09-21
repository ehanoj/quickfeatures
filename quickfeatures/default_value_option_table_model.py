# Project
from quickfeatures.__about__ import __title__
from quickfeatures.default_value_option import *

# Misc
from typing import Dict

# qgis
from qgis.core import QgsVectorLayer, QgsMessageLog, Qgis

# PyQt
from qgis.PyQt.QtCore import Qt, QModelIndex, QAbstractTableModel, pyqtSlot
from qgis.PyQt.QtWidgets import QStyledItemDelegate, QLineEdit
from qgis.PyQt.QtGui import QColor

class DefaultValueOptionTableModel(QAbstractTableModel):
    header_labels = [
        "Select",
        "Field",
        "Value"
    ]

    def __init__(self, parent):
        super().__init__(parent)
        self.default_values_options = []

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.header_labels[section]
        return super().headerData(section, orientation, role)

    def rowCount(self, index=QModelIndex(), **kwargs) -> int:
        return len(self.default_values_options)

    def columnCount(self, index=QModelIndex(), **kwargs) -> int:
        return len(self.header_labels)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):

        if not index.isValid():
            return None

        row = index.row()
        default_val = self.default_values_options[row]

        column = index.column()
        column_header_label = self.header_labels[column]

        if role == Qt.ItemDataRole.CheckStateRole:
            if column_header_label == "Select":
                if default_val.is_selected():
                    return Qt.CheckState.Checked
                else:
                    return Qt.CheckState.Unchecked

        if role == Qt.ItemDataRole.DisplayRole:
            if column_header_label == "Field":
                return default_val.get_name()

        if role == Qt.ItemDataRole.ForegroundRole:
            if column_header_label == "Field":
                if not default_val.is_valid():
                    return QColor(180, 180, 180)

    def flags(self, index):

        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags

        row = index.row()
        default_val = self.default_values_options[row]

        col = index.column()
        column_header_label = self.header_labels[col]

        if column_header_label == 'Select':
            return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable
        elif column_header_label == 'Field':
            return Qt.ItemFlag.ItemIsEnabled
        elif column_header_label == 'Value':
            return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEditable
        else:
            return Qt.ItemFlag.ItemIsEnabled


    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):

        if not index.isValid():
            return False

        row = index.row()
        default_value_option = self.default_values_options[row]

        col = index.column()
        column_header_label = self.header_labels[col]

        # QgsMessageLog.logMessage(f"setData: header '{column_header_label}', row: '{row}', value: '{value}'", tag=__title__, level=Qgis.Info)

        if column_header_label == 'Select' and role == Qt.ItemDataRole.CheckStateRole:
            default_value_option.toggle_selected()
            return True

        if column_header_label == 'Value' and role == Qt.ItemDataRole.EditRole:
            default_value_option.set_value(value)
            return True

    def set_default_values(self, map_lyr: QgsVectorLayer, default_values: Dict) -> None:

        # This is called when the editor is initialized.
        # The editor's table will be populated with fields based on:
        #   1. The default values that belong to the template (provided through the 'default_values' parameter)
        #   2. The fields available in the template's map layer (provided through the 'map_lyr' parameter)

        # Begin by clearing the table
        self.clear_default_values()

        default_values_to_set = []

        # Get fields from map layer
        if map_lyr:

            field_list = map_lyr.fields().toList()

            for field in field_list:
                default_values_to_set.append(
                    DefaultValueOption(name=field.name(), selected=False, valid=True)
                )

        # Get fields from default values
        for field_name in default_values:

            value = default_values[field_name]

            add_invalid_default_value = True

            for existing_default_value in default_values_to_set:
                if existing_default_value.get_name() == field_name:
                    existing_default_value.set_selected(True)
                    existing_default_value.set_value(value)
                    add_invalid_default_value = False

            if add_invalid_default_value:

                default_values_to_set.append(
                    DefaultValueOption(name=field_name, selected=True, valid=False, value=value)
                )

        # Add rows to model
        if default_values_to_set:

            row = self.rowCount()
            self.beginInsertRows(QModelIndex(), row, row + len(default_values_to_set) - 1)

            self.default_values_options = default_values_to_set

            self.endInsertRows()

        # QgsMessageLog.logMessage(f".... start row count {row}", tag=__title__, level=Qgis.Info)
        # QgsMessageLog.logMessage(f".... end row count {self.rowCount()}", tag=__title__, level=Qgis.Info)

    def clear_default_values(self):
        if len(self.default_values_options) > 0:

            self.beginRemoveRows(QModelIndex(), 0, self.rowCount() - 1)
            self.default_values_options.clear()
            self.endRemoveRows()

    def get_selected_default_values(self) -> Dict:

        # When the editor is closed, this function will grab all default value options that
        # are selected and return them to the template

        out_values = {}
        for default_values_options in self.default_values_options:
            if default_values_options.is_selected():
                key = default_values_options.get_name()
                value = default_values_options.get_value()
                out_values[key] = value

        return out_values


class DefaultValueOptionDelegate(QStyledItemDelegate):

    def __init__(self, parent):
        super().__init__(parent)

    def createEditor(self, parent, option, index):

        editor = QLineEdit(parent)
        return editor

    def setModelData(self, editor, model, index):

        data = None

        if editor.hasAcceptableInput():
            data = editor.text()

        if data == "":
            data = None

        model.setData(index, data)

    def setEditorData(self, editor, index):

        default_value_option = index.model().default_values_options[index.row()]

        value = default_value_option.get_value()

        # QgsMessageLog.logMessage(f"Setting value {value}", tag=__title__, level=Qgis.Info)

        if not value == '' and value is not None:
            try:
                editor.setText(value)
                editor.deselect()
            except TypeError:
                pass


