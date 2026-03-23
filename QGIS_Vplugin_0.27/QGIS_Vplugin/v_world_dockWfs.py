# -*- coding: utf-8 -*-
import os
import sys
import json
import requests
import xml.etree.ElementTree as ET
from qgis.core import Qgis, QgsVectorLayer, QgsProject, QgsFillSymbol, QgsPalLayerSettings, QgsTextFormat, QgsTextBufferSettings, QgsVectorLayerSimpleLabeling
from qgis.PyQt import QtGui, QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal, Qt
from PyQt5 import QtGui, QtCore
from qgis.PyQt.QtWidgets import QListWidgetItem, QMenu
from PyQt5.QtGui import QFont, QColor

from qgis.utils import iface
from .public import public

plugin_dir = os.path.dirname(__file__)
sys.path.append(plugin_dir)
from config import API_KEY

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui/v_world_dockWfs_base.ui'))


class VWorldDockWfs(QtWidgets.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        """Constructor."""
        super(VWorldDockWfs, self).__init__(parent)
        self.setupUi(self)
        self.addItemsToListWidget()

        self.wfsList.itemDoubleClicked.connect(self.onWfsListDoubleClicked)
        self.wfsSearch.textChanged.connect(self.on_inputSearch_textChanged)
        self.wfsFavorites.itemDoubleClicked.connect(self.onMyWfsListDoubleClicked)

        #wfsList에서 아이템 우클릭 시 메뉴 생성
        self.wfsList.setContextMenuPolicy(Qt.CustomContextMenu)
        self.wfsList.customContextMenuRequested.connect(self.showContextMenuForWfsList)

        self.wfsFavorites.setContextMenuPolicy(Qt.CustomContextMenu)
        self.wfsFavorites.customContextMenuRequested.connect(self.showContextMenuforMyWfsList)

        # label인 linktoVworld 클릭 시 'https://www.vworld.kr/dtmk/dtmk_ntads_s001.do'로 연결
        self.linktoVworld.linkActivated.connect(self.openVworld)

        self.refreshMyWfs()

    def showContextMenuforMyWfsList(self, position):
        # 우클릭한 아이템을 찾습니다.
        item = self.wfsFavorites.itemAt(position)
        if not item:
            return
        menu = QMenu()
        removeFavorites = menu.addAction("즐겨찾기 삭제")

        removeFavorites.triggered.connect(self.mywfsRemoveFavorites)

        menu.exec_(self.wfsFavorites.viewport().mapToGlobal(position))

    def showContextMenuForWfsList(self, position):
        # 우클릭한 아이템을 찾습니다.
        item = self.wfsList.itemAt(position)
        if not item:
            return  # 아이템이 없으면 메뉴를 표시하지 않습니다.

        # 컨텍스트 메뉴 생성
        menu = QMenu()
        addFavorites = menu.addAction("즐겨찾기 추가")
        wfsDownload = menu.addAction("다운로드 바로가기")

        # 액션에 대한 신호를 슬롯에 연결할 수 있습니다.
        addFavorites.triggered.connect(self.mywfsAddFavorites)
        wfsDownload.triggered.connect(self.wfsDownload)

        # 메뉴를 표시
        menu.exec_(self.wfsList.viewport().mapToGlobal(position))

    def wfsDownload(self):
        selectedItems = self.wfsList.selectedItems()
        returnProtocol = public.return_protocol(self)
        for item in selectedItems:
            layerName = item.text().split("[")[0]
            QtGui.QDesktopServices.openUrl(QtCore.QUrl(f"{returnProtocol[0]}vworld.kr/dtmk/dtmk_ntads_s001.do?searchKeyword={layerName}&searchFrm=SHP"))
        pass

    def mywfsRemoveFavorites(self):
        # 즐겨찾기 파일 경로
        favorites_path = os.path.join(os.path.dirname(__file__), "datas", "wfs_favorites.json")

        # 선택된 아이템 삭제
        selectedItems = self.wfsFavorites.selectedItems()
        with open(favorites_path, "r") as f:
            favorites = json.load(f)

        for item in selectedItems:
            layerId = item.text().split("[")[1].split("]")[0].strip()
            del favorites[layerId]

        with open(favorites_path, "w", encoding='utf-8') as f:
            json.dump(favorites, f, indent=4, ensure_ascii=False)

        self.refreshMyWfs()

    def mywfsAddFavorites(self):
        # 즐겨찾기 파일 경로
        favorites_path = os.path.join(os.path.dirname(__file__), "datas", "wfs_favorites.json")

        # 디렉토리가 없다면 생성
        os.makedirs(os.path.dirname(favorites_path), exist_ok=True)

        # 파일이 없다면 빈 JSON 파일 생성
        if not os.path.exists(favorites_path):
            with open(favorites_path, "w", encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False)

        # 즐겨찾기 추가
        selectedItems = self.wfsList.selectedItems()
        with open(favorites_path, "r") as f:
            favorites = json.load(f)  # 파일 내용을 딕셔너리로 읽기

        for item in selectedItems:
            layerName = item.text().split("[")[0].strip()  # 레이어 이름 추출
            layerId = item.text().split("[")[1].split("]")[0].strip()  # 레이어 ID 추출
            favorites[layerId] = layerName  # 즐겨찾기 딕셔너리에 추가

        # 파일에 즐겨찾기 딕셔너리 다시 쓰기
        with open(favorites_path, "w", encoding='utf-8') as f:
                json.dump(favorites, f, indent=4, ensure_ascii=False)

        self.refreshMyWfs()

    def refreshMyWfs(self):
        self.wfsFavorites.clear()

        if os.path.exists(os.path.join(os.path.dirname(__file__), "datas", "wfs_favorites.json")):
            favorites_path = os.path.join(os.path.dirname(__file__), "datas", "wfs_favorites.json")
            with open(favorites_path, "r") as f:
                favorites = json.load(f)
                for key, value in favorites.items():
                    item = QListWidgetItem(f"{value}[{key}]")
                    item.setData(Qt.UserRole, key)
                    self.wfsFavorites.addItem(item)


    def addItemsToListWidget(self):
        returnProtocol = public.return_protocol(self)
        apiurl = returnProtocol[0] + "api.vworld.kr/req/wfs?"
        params = {
            "key": API_KEY,
            "request": "GetCapabilities",
            "output": "text/javascript"
        }
        try:
            response = requests.get(apiurl, params=params, verify=returnProtocol[1])
            if response.status_code == 200:
                root = ET.fromstring(response.text)
                for featureType in root.findall(".//FeatureType"):
                    name = featureType.find("Name")
                    title = featureType.find("Title")
                    if name is not None and title is not None:
                        item = QListWidgetItem(f"{title.text}[{name.text}]")
                        item.setData(Qt.UserRole, name.text)  # 레이어 이름을 사용자 정의 데이터로 저장
                        self.wfsList.addItem(item)
                self.wfsList.sortItems()
        except requests.exceptions.SSLError as e:
            public.showMessage_sslConnectError(self)



    def on_inputSearch_textChanged(self, text):
        searchText = text.lower()

        for i in range(self.wfsList.count()):
            item = self.wfsList.item(i)
            if searchText in item.text().lower():
                item.setHidden(False)
            else:
                item.setHidden(True)
        for i in range(self.wfsFavorites.count()):
            item = self.wfsFavorites.item(i)
            if searchText in item.text().lower():
                item.setHidden(False)
            else:
                item.setHidden(True)

    def openVworld(self):
        url = "https://www.vworld.kr/dtmk/dtmk_ntads_s001.do"
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))

    def onMyWfsListDoubleClicked(self, item):
        selectedItems = self.wfsFavorites.selectedItems()
        for item in selectedItems:
            layerName = item.text().split("[")[1].split("]")[0]
            layerId = item.text().split("[")[0]
            # iface.messageBar().pushMessage(f"Layer Name: {layerName}", level=0)
            self.addWfsLayer(layerId, layerName)

        self.wfsFavorites.clearSelection()

    def onWfsListDoubleClicked(self, item):
        selectedItems = self.wfsList.selectedItems()
        for item in selectedItems:
            layerName = item.text().split("[")[1].split("]")[0]
            layerId = item.text().split("[")[0]
            # iface.messageBar().pushMessage(f"Layer Name: {layerName}", level=0)
            self.addWfsLayer(layerId, layerName)

        self.wfsList.clearSelection()

    def addWfsLayer(self, layerId, layerName):
        labelList = {
            'lt_c_landinfobasemap': 'jibun', 'lp_pa_cbnd_bonbun': 'bonbun', 'lp_pa_cbnd_bubun': 'jibun',
        }

        # 캔버스의 좌표계 가져오기
        crs = iface.mapCanvas().mapSettings().destinationCrs().authid()

        maxFeatures = 1000

        returnProtocol = public.return_protocol(self)
        wfsUrl = f"maxNumFeatures='{maxFeatures}' request='GetFeature' pagingEnabled='true' preferCoordinatesForWfsT11='false' restrictToRequestBBOX='1' srsname='{crs}' typename='{layerName}' url='{returnProtocol[0]}api.vworld.kr/req/wfs?key={API_KEY}&maxfeatures={maxFeatures}' version='auto'"

        try:
            wfsLayer = QgsVectorLayer(wfsUrl, layerId, "WFS")

            if not wfsLayer.isValid():
                errorDetails = wfsLayer.error().message()
                iface.messageBar().pushMessage("오류", f"주제도 데이터를 불러오던 중 오류가 발생했습니다: {errorDetails}", level=Qgis.Critical)
                return

            # for layer in QgsProject.instance().mapLayers().values():
            #     if layer.dataProvider().dataSourceUri() == wfsLayer.dataProvider().dataSourceUri():
            #         iface.messageBar().pushMessage("오류", "이미 동일한 레이어가 존재합니다.", level=Qgis.Warning)
            #         return

            if public.return_landLabelSytle(self) and labelList.get(layerName):
                symbol = QgsFillSymbol.createSimple({
                    'color': '0,0,0,1',
                    'outline_color': f'{public.randomColor(self)}',
                    'outline_width': '0.2',
                    'outline_style': 'solid'
                })
                wfsLayer.renderer().setSymbol(symbol)

                # 라벨 설정
                labelSettings = QgsPalLayerSettings()
                labelSettings.fieldName = labelList[layerName]

                if hasattr(QgsPalLayerSettings.Placement, 'AboveLine'):
                    labelSettings.placement = QgsPalLayerSettings.Placement.AboveLine
                elif hasattr(QgsPalLayerSettings.Placement, 'LineAbove'):
                    labelSettings.placement = QgsPalLayerSettings.Placement.LineAbove
                else:
                    labelSettings.placement = QgsPalLayerSettings.Placement.OverPoint

                # 라벨 형식 설정
                textFormat = QgsTextFormat()
                textFormat.setFont(QFont("Arial", 10))
                textFormat.setColor(QColor(0, 0, 0))

                # 텍스트 버퍼 설정 (선택적)
                bufferSettings = QgsTextBufferSettings()
                bufferSettings.setEnabled(True)
                bufferSettings.setSize(1)
                bufferSettings.setColor(QColor(255, 255, 255))

                textFormat.setBuffer(bufferSettings)
                labelSettings.setFormat(textFormat)

                # 라벨링을 레이어에 적용
                wfsLayer.setLabeling(QgsVectorLayerSimpleLabeling(labelSettings))
                wfsLayer.setLabelsEnabled(True)

            QgsProject.instance().addMapLayer(wfsLayer)
        except requests.exceptions.SSLError as e:
            public.showMessage_sslConnectError(self)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()
