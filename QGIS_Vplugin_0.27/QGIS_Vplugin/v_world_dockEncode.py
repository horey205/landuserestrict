# -*- coding: utf-8 -*-
import os
import sys
import requests

from qgis.PyQt import QtGui, QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal, Qt
from qgis.PyQt.QtWidgets import QDialog, QListWidgetItem
from PyQt5.QtWidgets import QMenu, QMessageBox
from qgis.gui import QgsMapCanvas, QgsMapToolZoom, QgsMapToolPan, QgsMapToolEmitPoint, QgsMapTool
from qgis.core import QgsProject, QgsVectorLayer,QgsGeometry,QgsPoint,QgsPointXY, Qgis

from qgis.utils import iface


plugin_dir = os.path.dirname(__file__)
sys.path.append(plugin_dir)
from config import API_KEY

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui/v_world_dockEncode_base.ui'))


class VWorldEncoding(QDialog, QgsMapTool, FORM_CLASS):
    def __init__(self, parent=None):
        QDialog.__init__(self, None, Qt.WindowStaysOnTopHint)
        super(VWorldEncoding, self).__init__(parent)
        self.setupUi(self)
        self.canvas = iface.mapCanvas()

        # self.layersList.itemDoubleClicked.connect(self.on_layersList_itemClicked)
        self.layersList.itemClicked.connect(self.on_layersList_itemClicked)
        self.encodingUTF.clicked.connect(lambda: self.encoding('UTF-8'))
        self.encodingEUC.clicked.connect(lambda: self.encoding('EUC-KR'))
        self.encodingCP.clicked.connect(lambda: self.encoding('CP949'))

        self.layersList.keyPressEvent = self.on_layersList_keyPressEvent

    def on_layersList_itemClicked(self, item):
        if item.checkState() == Qt.Checked:
            item.setCheckState(Qt.Unchecked)
        else:
            item.setCheckState(Qt.Checked)

    def on_layersList_keyPressEvent(self, event):
        if event.key() == Qt.Key_Space:
            for item in self.layersList.selectedItems():
                item.setCheckState(Qt.Unchecked if item.checkState() == Qt.Checked else Qt.Checked)


    def layerList(self):
        self.layersList.clear()
        layers = QgsProject.instance().mapLayers().values()
        for layer in layers:
            item = QListWidgetItem(layer.name())
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.layersList.addItem(item)

    def encoding(self, encoding):
        # 레이어 목록을 가져옴
        layers = {layer.name(): layer for layer in QgsProject.instance().mapLayers().values() if layer.type() == QgsVectorLayer.VectorLayer}
        # 체크된 레이어 목록을 가져옴
        checked_items = [self.layersList.item(index) for index in range(self.layersList.count()) if self.layersList.item(index).checkState() == Qt.Checked]
        # QGIS 3.17 이상이라면 CP949를 MS949로 변경
        if Qgis.QGIS_VERSION_INT >= 31700 and encoding == 'CP949':
            encoding = 'MS949'
        for item in checked_items:
            layer = layers.get(item.text())
            if layer:
                layer.setProviderEncoding(encoding)
                layer.reload()
        QMessageBox.information(self, "인코딩 적용", "선택된 레이어들에 인코딩이 적용되었습니다.")
