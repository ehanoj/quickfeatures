from quickfeatures.__about__ import __title__

# Project
from quickfeatures.default_value_option_table_model import DefaultValueOptionTableModel, DefaultValueOptionDelegate

# Misc
from pathlib import Path
from typing import Dict

# qgis
from qgis.core import QgsDefaultValue, QgsVectorLayer, QgsMessageLog, Qgis
from qgis.utils import iface

# PyQt
from qgis.PyQt import uic
from qgis.PyQt.QtCore import Qt, QPoint
from qgis.PyQt.QtGui import QCursor, QPixmap
from qgis.PyQt.QtWidgets import QDialog, QHeaderView

class DefaultValueEditor(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        root_path = Path(__file__).parent

        # Load UI file
        uic.loadUi(root_path / "gui/{}.ui".format(Path(__file__).stem), self)

        # Set icon
        metadata_icon = QPixmap(f"{root_path}/resources/icons/mActionPropertiesWidget.svg")
        self.info_icon.setPixmap(metadata_icon)
        self.info_icon.show()

        # Set modality
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        # Initialize table
        self.table_model = None
        self.default_value_option_delegate = None
        self.init_table()

        self.accept_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

    def showEvent(self, event):
        self.resize(380, 280)

        # Show the dialog at the current mouse position
        geom = self.frameGeometry()

        win = iface.mainWindow()
        p = win.pos()
        r = win.rect()
        np = QPoint(int(p.x() + r.width() / 2), int(p.y() + r.height() / 2))
        #np = QCursor.pos()
        geom.moveCenter(np)
        self.setGeometry(geom)

        super().showEvent(event)

    def get_editor_default_values(self) -> Dict[str, QgsDefaultValue]:
        return self.table_model.get_selected_default_values()

    def populate_table(self, map_lyr: QgsVectorLayer, default_values: Dict[str, QgsDefaultValue]):
        self.table_model.set_default_values(map_lyr, default_values)
        #self.table_model.set_selected_default_values(default_values)

    def init_table(self):
        # Create model
        self.table_model = DefaultValueOptionTableModel(self)
        self.table_model.rowsInserted.connect(self.rows_inserted)

        # Connect view and model
        self.table_view.setModel(self.table_model)

        # Set delegates
        self.default_value_option_delegate = DefaultValueOptionDelegate(self.table_view)
        self.table_view.setItemDelegateForColumn(2, self.default_value_option_delegate)

        # Set Column sizes
        header = self.table_view.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

    def rows_inserted(self, parent, first, last):
        for row in range(first, last + 1):
            self.table_view.openPersistentEditor(self.table_model.index(row, 2))
