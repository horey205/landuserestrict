# -*- coding: utf-8 -*-
import os
import sys
import requests

from qgis.PyQt import QtGui, QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal, Qt
from qgis.PyQt.QtWidgets import (QDialog)
from PyQt5.QtWidgets import QMenu, QMessageBox
from qgis.gui import QgsMapCanvas, QgsMapToolZoom, QgsMapToolPan, QgsMapToolEmitPoint, QgsMapTool
from qgis.core import Qgis as QGis, QgsProject, QgsVectorLayer,QgsGeometry,QgsPoint,QgsPointXY

from qgis.utils import iface
from .public import public
from .v_world_dockWfs import VWorldDockWfs

plugin_dir = os.path.dirname(__file__)
sys.path.append(plugin_dir)
from config import API_KEY

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui/v_world_dockrgc_base.ui'))


class VWorldDockRGC(QDialog, QgsMapTool, FORM_CLASS):
    def __init__(self, parent=None):
        QDialog.__init__(self, None, Qt.WindowStaysOnTopHint)
        super(VWorldDockRGC, self).__init__(parent)
        self.setupUi(self)
        self.canvas = iface.mapCanvas()

        self.bubunBtn.clicked.connect(lambda: VWorldDockWfs.addWfsLayer(self, 'LX맵', 'lt_c_landinfobasemap'))

    def onSpotClicked(self):
        self.showMinimized()  # 수정된 코드 라인
        self.value_coordX, self.value_coordY = 0, 0
        mapTool = PointTool(self.canvas, self)
        self.canvas.setMapTool(mapTool)


class PointTool(QgsMapTool):
    def __init__(self, canvas,parent=None):
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self.parent = parent

    def canvasPressEvent(self, event):
        if event.button() == Qt.LeftButton:
            realCoordinates = QgsGeometry.fromPointXY(self.canvas.getCoordinateTransform().toMapCoordinates(event.pos().x(), event.pos().y()))
            plainCoordi = self.canvas.getCoordinateTransform().toMapCoordinates(event.pos().x(), event.pos().y())
            clickPointX = round(plainCoordi.x(), 4)
            clickPointY = round(plainCoordi.y(), 4)

            #캔버스 좌표계
            canvasCRS = self.canvas.mapSettings().destinationCrs().authid()

            # iface.messageBar().pushMessage("좌표", "좌표: " + str(clickPointX) + ", " + str(clickPointY), level=0, duration=3)
            # iface.messageBar().pushMessage("좌표계", "좌표계: " + canvasCRS, level=0, duration=3)


            returnProtocol = public.return_protocol(self)

            apiurl = f"{returnProtocol[0]}api.vworld.kr/req/address?"
            params = {
                "key": API_KEY,
                "request": "getAddress",
                "service": "address",
                "format": "json",
                "size": "10",
                "page": "1",
                "point": f"{clickPointX},{clickPointY}",
                "type": "both",
                "category": "PARCEL",
                "crs": canvasCRS
            }
            try:
                response = requests.get(apiurl, params=params, verify=returnProtocol[1])

                # iface.messageBar().pushMessage("Status Code", str(response.status_code), level=0, duration=3)
                # iface.messageBar().pushMessage("URL", response.url, level=0, duration=3)
                # iface.messageBar().pushMessage("Response", response.text[:100], level=0, duration=3)


                if response.status_code == 200:
                    data = response.json()  # JSON 데이터 파싱

                    self.parent.jibunAddr.setText('검색 결과가 없습니다.')
                    self.parent.roadAddr.setText('검색 결과가 없습니다.')

                    if data['response']['status'] != 'NOT_FOUND':
                        for item in data['response']['result']:
                            if item['type'] == 'parcel':
                                self.parent.jibunAddr.setText(item['text'])
                            elif item['type'] == 'road':
                                self.parent.roadAddr.setText(item['text'])

                    apiurl = f"{returnProtocol[0]}api.vworld.kr/req/data?"
                    params = {
                        "service": "data",
                        "request": "GetFeature",
                        "data": "LP_PA_CBND_BUBUN",
                        "key": API_KEY,
                        "crs": canvasCRS,
                        "geomFilter": f"POINT({clickPointX} {clickPointY})"
                    }
                    response = requests.get(apiurl, params=params, verify=returnProtocol[1])

                    if response.status_code == 200 and response.json().get('response', {}).get('status') != 'NOT_FOUND':
                        pnu = response.json()['response']['result']['featureCollection']['features'][0]['properties']['pnu']
                        self.parent.pnuAddr.setText(pnu)


                iface.actionPan().trigger()
                self.parent.showNormal()
            except requests.exceptions.SSLError as e:
                public.showMessage_sslConnectError(self)