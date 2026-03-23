# -*- coding: utf-8 -*-
import os
import sys
import json

from qgis.PyQt import QtGui, QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal, Qt
from qgis.PyQt.QtWidgets import QDialog, QListWidgetItem
from PyQt5.QtWidgets import QMenu, QMessageBox
from qgis.gui import QgsMapCanvas, QgsMapToolZoom, QgsMapToolPan, QgsMapToolEmitPoint, QgsMapTool
from qgis.core import QgsProject, QgsVectorLayer,QgsGeometry,QgsPoint,QgsPointXY, Qgis

from .public import public
from qgis.utils import iface


plugin_dir = os.path.dirname(__file__)
sys.path.append(plugin_dir)
from config import API_KEY

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui/v_world_setting_base.ui'))

class VWorldSetting(QDialog, QgsMapTool, FORM_CLASS):
    def __init__(self, parent=None):
        QDialog.__init__(self, None, Qt.WindowStaysOnTopHint)
        super(VWorldSetting, self).__init__(parent)
        self.setupUi(self)
        self.canvas = iface.mapCanvas()

        self.APIKey.setText(public.reTurnAPIKEY(self))

        self.APIKey.editingFinished.connect(self.saveApiKey)
        self.HTTP.clicked.connect(self.saveHttp)
        self.HTTPS.clicked.connect(self.saveHttp)
        self.HTTPSX.clicked.connect(self.saveHttp)

        selProtocl = public.return_protocol(self)
        if selProtocl[0] == "http://":
            self.HTTP.setChecked(True)
        elif selProtocl[0] == "https://" and selProtocl[1] == True:
            self.HTTPS.setChecked(True)
        elif selProtocl[0] == "https://" and selProtocl[1] == False:
            self.HTTPSX.setChecked(True)

        self.landLabelSytleOFF.clicked.connect(lambda: self.saveLandLabelSytle(False))
        self.landLabelSytleON.clicked.connect(lambda: self.saveLandLabelSytle(True))

        if public.return_landLabelSytle(self):
            self.landLabelSytleON.setChecked(True)
            self.landLabelSytleOFF.setChecked(False)
        else:
            self.landLabelSytleON.setChecked(False)
            self.landLabelSytleOFF.setChecked(True)

    def saveApiKey(self):
        # iface.messageBar().pushMessage("API Key 저장", "API Key가 저장되었습니다.", level=Qgis.Info, duration=3)

        myOptions = os.path.join(os.path.dirname(__file__), "datas", "options.json")
        # 파일을 읽기 모드로 열고 데이터를 로드
        with open(myOptions, "r", encoding='utf-8') as f:
            data = json.load(f)

        data['API_KEY'] = self.APIKey.text().replace(" ", "")
        self.APIKey.setText(data['API_KEY'])

        # 데이터를 다시 파일에 쓰기 위해 파일을 쓰기 모드로 다시 열기
        with open(myOptions, "w", encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)

    def saveHttp(self):

        myOptions = os.path.join(os.path.dirname(__file__), "datas", "options.json")
        # 파일을 읽기 모드로 열고 데이터를 로드
        with open(myOptions, "r", encoding='utf-8') as f:
            data = json.load(f)

        data['protocol'] = self.sender().text()

        # 데이터를 다시 파일에 쓰기 위해 파일을 쓰기 모드로 다시 열기
        with open(myOptions, "w", encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)

    def saveLandLabelSytle(self, onoff):
        myOptions = os.path.join(os.path.dirname(__file__), "datas", "options.json")
        with open(myOptions, "r", encoding='utf-8') as f:
            data = json.load(f)
        data['landLabelSytle'] = onoff
        with open(myOptions, "w", encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)