# Project
from quickfeatures.feature_template_table_model import *
from quickfeatures.__about__ import __title__

# Standard
from pathlib import Path
import os

# qgis
from qgis.core import QgsMessageLog, QgsProject, Qgis, QgsApplication, QgsSettings, QgsMapLayer

# PyQt
from qgis.PyQt import uic
from qgis.PyQt.QtCore import QSize
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QWidget, QHeaderView, QFileDialog, QPushButton, QToolBar, QAction, QAbstractItemView
from qgis.PyQt.QtXml import QDomDocument, QDomElement

class QuickFeaturesWidget(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.icon_dir = os.path.join(os.path.dirname(__file__), "resources/icons")

        # Load UI file
        uic.loadUi(Path(__file__).parent / "gui/{}.ui".format(Path(__file__).stem), self)

        # Deactivate 'Reuse last value' setting
        QgsSettings().setValue('qgis/digitizing/reuseLastValues', False)

        # Initialize table
        self.table_model = None
        self.table_map_lyr_delegate = None
        self.default_value_delegate = None
        self.init_table()

        # Actions
        self.action_add_template = QAction(QIcon(os.path.join(self.icon_dir, 'mActionAdd.svg')), "Add template", self)
        self.action_add_template.setStatusTip("Add templates")
        self.action_add_template.triggered.connect(self.add_template_dialog)

        self.action_clear_templates = QAction(QIcon(os.path.join(self.icon_dir, 'iconClearConsole.svg')), "Clear templates", self)
        self.action_clear_templates.setStatusTip("Clear templates")
        self.action_clear_templates.triggered.connect(self.table_model.clear_templates)

        self.action_load_templates = QAction(QIcon(os.path.join(self.icon_dir, 'mActionFileOpen.svg')), "Load templates", self)
        self.action_load_templates.setStatusTip("Load templates")
        self.action_load_templates.triggered.connect(self.load_templates_dialog)

        self.action_save_templates = QAction(QIcon(os.path.join(self.icon_dir, 'mActionFileSave.svg')), "Save templates", self)
        self.action_save_templates.setStatusTip("Save templates")
        self.action_save_templates.triggered.connect(self.save_templates_dialog)

        # Toolbar
        self.toolbar = QToolBar()
        self.toolbar_layout.addWidget(self.toolbar)
        self.toolbar.addAction(self.action_add_template)
        self.toolbar.addAction(self.action_clear_templates)
        self.toolbar.addAction(self.action_load_templates)
        self.toolbar.addAction(self.action_save_templates)
        self.toolbar.setIconSize(QSize(18,18))

        # On project load/save
        QgsProject.instance().readProject.connect(self.project_load)
        QgsProject.instance().writeProject.connect(self.project_save)

        # Button used for debugging purpose
        # self.add_debug_actions()

    def init_table(self):

        # Set row height
        self.table_view.verticalHeader().setDefaultSectionSize(30)

        # Disable native row selection: it would highlight a row on any click
        # within it (e.g. picking a layer), regardless of whether the
        # template is actually active. Whether a template is active is
        # already indicated by its own checkbox + row background color.
        self.table_view.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)

        # Set table's model
        self.table_model = FeatureTemplateTableModel(parent=self)
        self.table_model.rowsInserted.connect(self.table_rows_inserted)

        # Connect model to view
        self.table_view.setModel(self.table_model)

        # Set delegate for map layer column
        col_map_lyr = 3
        self.table_map_lyr_delegate = QgsMapLayerComboDelegate(self.table_view)
        self.table_view.setItemDelegateForColumn(col_map_lyr, self.table_map_lyr_delegate)

        # Set delegate for default values column
        col_default_value = 4
        table_icon = QIcon(os.path.join(self.icon_dir, 'mActionEditTable.svg'))
        self.default_value_delegate = DefaultValueDelegate(self.table_view, table_icon)
        self.table_view.setItemDelegateForColumn(col_default_value, self.default_value_delegate)

        # Set delegate for remove template column
        col_remove = 5
        delete_icon = QIcon(os.path.join(self.icon_dir, 'mActionDeleteSelected.svg'))
        self.remove_delegate = RemoveDelegate(self.table_view, delete_icon)
        self.table_view.setItemDelegateForColumn(col_remove, self.remove_delegate)

        # Set column sizes
        header = self.table_view.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_view.setColumnWidth(col_map_lyr, 150)
        for col_num in [0, 2, col_default_value, col_remove]:
            header.setSectionResizeMode(col_num, QHeaderView.ResizeMode.ResizeToContents)

    def table_rows_inserted(self, parent, first, last):

        for row in range(first, last + 1):
            for col in [3, 4, 5]:  # These are the columns with persistent widgets
                self.table_view.openPersistentEditor(self.table_model.index(row, col))

    def add_template_dialog(self):

        template = FeatureTemplate(parent=self.table_model, widget=self, name=None, shortcut_str=None, map_lyr=None, default_values={})

        self.table_model.add_templates([template])

    def clean_up(self):

        self.table_model.clear_templates()

    def load_templates_dialog(self):

        file_name = QFileDialog.getOpenFileName(self, 'Open file', 'c:\\', "JSON file (*.json)")[0]

        if file_name != '':
            self.table_model.from_json(Path(file_name))

        self.table_view.resizeColumnToContents(1)

    def save_templates_dialog(self):

        file_name = QFileDialog.getSaveFileName(self, 'Save file', 'c:\\', "JSON file (*.json)")[0]

        if file_name != '':
            self.table_model.to_json(Path(file_name))

    def project_load(self, doc: QDomDocument):

        root = doc.childNodes().item(0)

        plugin_elem = root.namedItem('quick_features')

        if not plugin_elem.isNull():
            feature_templates_elem = plugin_elem.namedItem('feature_templates')
            self.table_model.from_xml(feature_templates_elem)

    def project_save(self, doc: QDomDocument):

        templates = self.table_model.get_templates()

        if len(templates) > 0:

            root = doc.childNodes().item(0)
            plugin_elem = doc.createElement('quick_features')
            templates_elem = doc.createElement('feature_templates')

            for template in templates:
                template_xml = template.to_xml(doc)
                templates_elem.appendChild(template_xml)

            plugin_elem.appendChild(templates_elem)
            root.appendChild(plugin_elem)


    # def add_debug_actions(self):
    #
    #     debug_mode = True
    #     # QgsMessageLog.logMessage(f"Found DEBUG mode and it was '{debug_mode}'", tag=__title__, level=Qgis.Info)
    #
    #     if debug_mode:
    #
    #         self.action_testdata = QAction(QIcon(QgsApplication.iconPath("mIconFolderOpen.svg")),
    #                                              "Load test data", self)
    #         self.action_debug = QAction(QIcon(QgsApplication.iconPath("mIndicatorBadLayer.svg")),
    #                                              "Debug", self)
    #
    #         self.action_testdata.triggered.connect(self.load_test_data)
    #         self.action_debug.triggered.connect(self.debug)
    #
    #         self.toolbar.addAction(self.action_testdata)
    #         self.toolbar.addAction(self.action_debug)
    #
    # def load_test_data(self):
    #
    #     test_data_path = QgsProject.instance().readPath("./") + '/template_group.json'
    #     self.table_model.from_json(Path(test_data_path))
    #     self.table_view.resizeColumnToContents(1)
    #
    # def debug(self):
    #     QgsMessageLog.logMessage(f"Debug message", tag=__title__, level=Qgis.Info)
    #
    #     #QgsMessageLog.logMessage(f"My class is: {self.__class__.__name__}", tag=__title__, level=Qgis.Info)
    #     QgsMessageLog.logMessage(f"My palette is: {type(self.palette()).__name__}", tag=__title__, level=Qgis.Info)
    #
    #     # existing_shortcuts = self.findChildren(QShortcut) + QgsGui.shortcutsManager().listShortcuts()