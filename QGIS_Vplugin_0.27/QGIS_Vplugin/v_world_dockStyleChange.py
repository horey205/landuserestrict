# -*- coding: utf-8 -*-
import os
import sys
import requests

from qgis.PyQt import QtGui, QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal, Qt
from qgis.PyQt.QtWidgets import QDialog, QListWidgetItem
from PyQt5.QtWidgets import QMenu, QMessageBox
from qgis.gui import QgsMapCanvas, QgsMapToolZoom, QgsMapToolPan, QgsMapToolEmitPoint, QgsMapTool
from qgis.core import QgsProject, QgsVectorLayer, QgsWkbTypes, QgsSymbol, QgsSimpleFillSymbolLayer, QgsRendererCategory, QgsCategorizedSymbolRenderer, QgsSingleSymbolRenderer
from PyQt5.QtGui import QColor

import random

from qgis.utils import iface


plugin_dir = os.path.dirname(__file__)
sys.path.append(plugin_dir)
from config import API_KEY

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui/v_world_dockStyleChange_base.ui'))


class VWorldStyleChange(QDialog, QgsMapTool, FORM_CLASS):
    def __init__(self, parent=None):
        QDialog.__init__(self, None, Qt.WindowStaysOnTopHint)
        super(VWorldStyleChange, self).__init__(parent)
        self.setupUi(self)
        self.canvas = iface.mapCanvas()

        self.layersList.itemClicked.connect(self.on_layersList_itemClicked)

        self.BTNstyleChange.clicked.connect(self.styleChange)

        self.layersList.keyPressEvent = self.on_layersList_keyPressEvent

    def on_layersList_itemClicked(self, item):
        if item.checkState() == Qt.Checked:
            item.setCheckState(Qt.Unchecked)
        else:
            item.setCheckState(Qt.Checked)

    def on_layersList_keyPressEvent(self, event):
        if event.key() == Qt.Key_Space:
            for item in self.layersList.selectedItems():
                if item.checkState() == Qt.Checked:
                    item.setCheckState(Qt.Unchecked)
                else:
                    item.setCheckState(Qt.Checked)
    def layerList(self):
        self.layersList.clear()
        layers = QgsProject.instance().mapLayers().values()
        for layer in layers:

            if layer.type() == QgsVectorLayer.VectorLayer and layer.geometryType() == QgsWkbTypes.PolygonGeometry:
                item = QListWidgetItem(layer.name())
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Unchecked)
                self.layersList.addItem(item)

    def styleChange(self):
        for item in self.layersList.selectedItems():
            if item.checkState() == Qt.Checked:
                # 레이어 이름으로부터 레이어 객체를 가져옴
                layer = QgsProject.instance().mapLayersByName(item.text())[0]

                if not layer or layer.type() != QgsVectorLayer.VectorLayer or layer.geometryType() != QgsWkbTypes.PolygonGeometry:
                    continue  # 레이어가 유효하지 않거나 벡터 레이어가 아니거나 폴리곤 타입이 아닌 경우 건너뜀

                # 새 심볼 생성 (폴리곤 레이어용)
                symbol = QgsSymbol.defaultSymbol(layer.geometryType())

                # 랜덤 색상 생성
                random_color = QColor(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

                # 면 심볼 레이어 생성 및 설정
                fill_layer = QgsSimpleFillSymbolLayer()
                fill_layer.setStrokeColor(random_color)  # 선 색상 설정
                fill_layer.setFillColor(QColor(0, 0, 0, 0))  # 면 색상 투명으로 설정
                symbol.changeSymbolLayer(0, fill_layer)

                # 레이어에 새 심볼 설정
                layer.setRenderer(QgsSingleSymbolRenderer(symbol))
                layer.triggerRepaint()
                iface.layerTreeView().refreshLayerSymbology(layer.id())