# -*- coding: utf-8 -*-
import os
import sys
from qgis.PyQt import QtGui, QtWidgets, uic
from qgis.PyQt.QtWidgets import QDialog, QMessageBox, QFileDialog
from qgis.utils import iface

from .v_world_dockWfs import VWorldDockWfs


plugin_dir = os.path.dirname(__file__)
sys.path.append(plugin_dir)
from config import API_KEY

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui/v_world_dockCAD_base.ui'))


class VWorldDockCAD(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(VWorldDockCAD, self).__init__(parent)
        self.setupUi(self)

        # Set up connections
        self.toCad.clicked.connect(self.onToCadClicked)
        self.canvas = iface.mapCanvas()

    def onToCadClicked(self):
        layer = self.mMapLayerComboBox.currentLayer()
        if layer is None:
            QMessageBox.information(self, "Error", "No layer selected.", QMessageBox.Ok)
            return
        file, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save File", "", "DXF files (*.dxf)")
        if not file:
            return

