# -*- coding: utf-8 -*-
from PyQt5.QtCore import QSettings, QTranslator, QCoreApplication, Qt
from PyQt5.QtWidgets import QAction, QDockWidget, QAction, QMenu, QMessageBox, QFileDialog, QDialog, QVBoxLayout, QLabel, QPushButton, QLineEdit
from qgis.core import (
    QgsPointXY, QgsFeature, QgsGeometry,
    QgsVectorLayer, QgsProject, QgsField,
    QgsCoordinateReferenceSystem, QgsMapLayer, QgsVectorFileWriter,
    QgsMapSettings, QgsLayerTreeGroup, QgsPrintLayout,
    QgsLayoutExporter, QgsLayoutPoint, QgsLayoutSize, QgsUnitTypes,
    QgsLayoutItemMap, QgsDxfExport)

from qgis.PyQt import QtGui, QtWidgets, uic
from qgis.gui import QgsProjectionSelectionWidget, QgsScaleWidget

from . import resources


from .v_world_addWmts import addWmtsLayer
from .v_world_dockWfs import VWorldDockWfs
from .v_world_dockSearch import VWorldDockSearch
from .v_world_dockRGC import VWorldDockRGC
# from .v_world_3Dmap import VWorld3Dmap
from .v_world_dockEncode import VWorldEncoding
from .v_world_dockStyleChange import VWorldStyleChange
from .v_world_geocoder import VWorldDockGeocoder
from .v_world_setting import VWorldSetting
# from .v_world_dock3D import VWorld3Dmap
from .public import public

from PyQt5.QtGui import QIcon
import os.path
import json

class VWorld:
    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.dockwidget_wfs = None
        self.dockwidget_search = None
        self.dockwidget_3Dmap = None
        self.actions = []
        self.menu = self.tr(u'&공간정보 오픈플랫폼(브이월드)')
        self.toolbar = self.iface.addToolBar(u'브이월드')
        self.toolbar.setObjectName(u'브이월드')
        self.canvas = self.iface.mapCanvas()


        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(self.plugin_dir, 'i18n', 'VWorld_{}.qm'.format(locale))
        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)


    def tr(self, message):
        return QCoreApplication.translate('VWorld', message)

    def initGui(self):
        self.add_action(
            ':/icon_base',
            text=self.tr(u'브이월드 일반지도'),
            callback=lambda: addWmtsLayer('Base'),
            parent=self.iface.mainWindow())

        self.add_action(
            ':/icon_satellite',
            text=self.tr(u'브이월드 항공지도'),
            callback=lambda: addWmtsLayer('Satellite'),
            parent=self.iface.mainWindow())

        self.add_action(
            ':/icon_hybrid',
            text=self.tr(u'브이월드 하이브리드'),
            callback=lambda: addWmtsLayer('Hybrid'),
            parent=self.iface.mainWindow())

        # self.add_action(
        #     ':/icon_3d',
        #     text=self.tr(u'브이월드 3D지도'),
        #     callback=self.run3Dmap,
        #     parent=self.iface.mainWindow())

        self.toolbar.addSeparator()

        self.add_action(
            ':/icon_layer',
            text=self.tr(u'브이월드 주제도'),
            callback=self.runWfs,
            parent=self.iface.mainWindow())

        self.add_action(
            ':/icon_styleChange',
            text=self.tr(u'폴리곤 스타일 변경'),
            callback=self.runStyleChange,
            parent=self.iface.mainWindow()
        )

        self.toolbar.addSeparator()

        self.add_action(
            ':/icon_search',
            text=self.tr(u'주소 검색'),
            callback=self.runSearch,
            parent=self.iface.mainWindow())

        self.rgc=self.add_action(
            ':/icon_rgc',
            text=self.tr(u'주소 조회'),
            callback=self.runRgc,
            parent=self.iface.mainWindow())

        self.add_action(
            ':/icon_geocoder',
            text=self.tr(u'지오코딩'),
            callback=self.runGeocoder,
            parent=self.iface.mainWindow()
        )

        self.toolbar.addSeparator()

        self.add_action(
            ':/icon_languages',
            text=self.tr(u'인코딩 변경'),
            callback=self.runEncoding,
            parent=self.iface.mainWindow())

        self.add_action(
            ':/icon_mappingPoint',
            text=self.tr(u'포인트 일괄 매핑'),
            callback=self.runMappingPoint,
            parent=self.iface.mainWindow()
        )

        # self.add_action(
        #     ':/icon_findSplit',
        #     text=self.tr(u'지역 통합짜르기'),
        #     callback=self.runFindSplit,
        #     parent=self.iface.mainWindow()
        # )

        # self.add_action(
        #     ':/icon_cad',
        #     text=self.tr(u'CAD 변환'),
        #     callback=self.runCad,
        #     parent=self.iface.mainWindow())

        self.toolbar.addSeparator()

        self.add_action(
            ':/icon_setting',
            text=self.tr(u'설정'),
            callback=self.runSetting,
            parent=self.iface.mainWindow())


    def add_action(self, icon_path, text, callback, parent=None):
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        self.toolbar.addAction(action)
        self.iface.addPluginToMenu(self.menu, action)
        self.actions.append(action)
        return action


    def onClosePluginWfs(self):
        self.iface.removeDockWidget(self.dockwidget_wfs)
        self.dockwidget_wfs.close()
        self.dockwidget_wfs = None

    def onClosePluginSearch(self):
        self.iface.removeDockWidget(self.dockwidget_search)  # 독 위젯을 인터페이스에서 제거
        self.dockwidget_search.close()  # 안전하게 닫기
        self.dockwidget_search = None  # 참조 제거

    def onClosePlugin3Dmap(self):
        self.iface.removeDockWidget(self.dockwidget_3Dmap)  # 독 위젯을 인터페이스에서 제거
        self.dockwidget_3Dmap.close()  # 안전하게 닫기
        self.dockwidget_3Dmap = None  # 참조 제거

    def runWfs(self):
        if not self.dockwidget_wfs:
            self.dockwidget_wfs = VWorldDockWfs(self.iface.mainWindow())
            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dockwidget_wfs)
            self.dockwidget_wfs.closingPlugin.connect(self.onClosePluginWfs)  # 시그널 연결
        self.dockwidget_wfs.show()


    def runSearch(self):
        if not self.dockwidget_search:
            self.dockwidget_search = VWorldDockSearch(self.iface.mainWindow())
            self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.dockwidget_search)
            self.dockwidget_search.closingPlugin.connect(self.onClosePluginSearch)  # 시그널 연결
        self.dockwidget_search.show()

    def run3Dmap(self):
        if not self.dockwidget_3Dmap:
            self.dockwidget_3Dmap = VWorld3Dmap(self.iface.mainWindow())
            self.iface.addDockWidget(Qt.TopDockWidgetArea, self.dockwidget_3Dmap)
            self.dockwidget_3Dmap.closingPlugin.connect(self.onClosePlugin3Dmap)
        self.dockwidget_3Dmap.show()


    def runRgc(self):
        if hasattr(self, 'rgcdock'):
            self.rgcDock.showNormal()
        else:
            self.rgcDock = VWorldDockRGC()
            self.rgcDock.spotClick.clicked.connect(self.rgcDock.onSpotClicked)
            self.rgcDock.show()

    def runStyleChange(self):
        if hasattr(self, 'styleChangeDock'):
            self.styleChangeDock.showNormal()
        else:
            self.styleChangeDock = VWorldStyleChange()
            self.styleChangeDock.show()

        self.styleChangeDock.layerList()

    def runSetting(self):
        if hasattr(self, 'setting'):
            self.setting.showNormal()
        else:
            self.setting = VWorldSetting()
            self.setting.show()

    def runEncoding(self):
        if hasattr(self, 'encodingDock'):
            self.encodingDock.showNormal()
        else:
            self.encodingDock = VWorldEncoding()
            self.encodingDock.show()

        self.encodingDock.layerList()

    def runCad(self):
        # Create the dialog and set its properties
        dialog = QDialog()
        dialog.setWindowTitle("CAD 변환")
        dialog.resize(500, 300)

        layout = QVBoxLayout(dialog)

        textProjection = QLabel("출력할 좌표계를 선택하세요.")
        layout.addWidget(textProjection)

        projSelector = QgsProjectionSelectionWidget()
        layout.addWidget(projSelector)

        scaleLabel = QLabel("출력할 스케일 설정:")
        scaleSelector = QgsScaleWidget()
        scaleSelector.setToolTip("Set the scale for output")
        layout.addWidget(scaleLabel)
        layout.addWidget(scaleSelector)

        pathLineEdit = QLineEdit()
        pathLineEdit.setPlaceholderText("파일 저장 경로를 입력하거나 선택하세요.")
        pathLineEdit.setHidden(True)
        browseButton = QPushButton("저장하기")
        browseButton.clicked.connect(lambda: self.selectSavePath(pathLineEdit, dialog, projSelector, scaleSelector))

        layout.addWidget(pathLineEdit)
        layout.addWidget(browseButton)

        # Show the dialog
        dialog.setLayout(layout)
        dialog.exec_()

    def selectSavePath(self, lineEdit, parentDialog, projSelector, scaleSelector):
        # Open a file dialog to select the path
        filePath = QFileDialog.getSaveFileName(parentDialog, "파일 저장", "", "CAD Files (*.dxf)")
        if filePath[0]:
            lineEdit.setText(filePath[0])
            self.exportToCAD(filePath[0], projSelector.crs(), scaleSelector.scale())

    def exportToCAD(self, filePath, crs, scale):
        # Collect the layer IDs you want to export
        layer_ids = [layer.id() for layer in QgsProject.instance().mapLayers().values()]

        # Initialize the DXF export object with the layer IDs
        dxf_export = QgsDxfExport(QgsProject.instance(), layer_ids)
        dxf_export.setDestinationCrs(crs)
        dxf_export.setSymbologyScale(scale)
        dxf_export.setFileName(filePath)

        # Perform the export
        result = dxf_export.exportDxf()
        if result == QgsDxfExport.ExportResult.Success:
            self.iface.messageBar().pushMessage("Export", "Export successful", level=0)
        else:
            self.iface.messageBar().pushMessage("Export", "Export failed", level=1)

    def unload(self):
        for action in self.actions:
            self.iface.removePluginMenu(self.tr(u'&공간정보 오픈플랫폼(브이월드)'), action)
            self.iface.removeToolBarIcon(action)
        del self.toolbar

    def runGeocoder(self):
        if not public.reTurnAPIKEY(self) or public.reTurnAPIKEY(self) == "":
            QMessageBox.about(None, "API 키 입력", "옵션(톱니바퀴)에서 API 키를 입력하세요.")
            return

        if hasattr(self, 'geocoderDock'):
            self.geocoderDock.showNormal()
        else:
            self.geocoderDock = VWorldDockGeocoder()
            self.geocoderDock.show()



    def runMappingPoint(self):
        QDialog = QtWidgets.QDialog()
        QDialog.setWindowTitle("포인트 일괄 매핑")
        QDialog.resize(500, 200)  # 높이를 조금 더 늘려 좌표계 선택 위젯에 공간을 제공
        layout = QtWidgets.QVBoxLayout()

        textONE = QtWidgets.QLabel("좌표를 입력하세요.")
        point = QtWidgets.QLineEdit()
        point.setPlaceholderText("경도 위도 경도 위도 ... 순으로 입력하세요. ex) 127.5 37.5 127.6 37.6 127.7 37.7")
        textTWO = QtWidgets.QLabel("입력한 좌표의 좌표계를 선택하세요.")
        projSelector = QgsProjectionSelectionWidget()
        layout.addWidget(textONE)
        layout.addWidget(point)
        layout.addWidget(textTWO)
        layout.addWidget(projSelector)

        QDialog.setLayout(layout)

        save = QtWidgets.QPushButton("저장")
        # 좌표계 정보를 함께 넘겨주도록 lambda 수정
        save.clicked.connect(lambda: self.mappingPoint(point.text(), projSelector.crs().authid(), QDialog))
        layout.addWidget(save)
        QDialog.exec_()

    def mappingPoint(self, pointText, crsAuthId, QDialog):
        if crsAuthId == "" or pointText == "":
            QMessageBox.warning(None, "경고", "좌표계와 좌표를 입력하세요.")
            return

        pointList = pointText.replace(",", " ").split()
        if len(pointList) % 2 != 0:  # 좌표 값이 짝수가 아니면 각 포인트에 대한 경도와 위도 값이 모두 제공되지 않은 것
            QMessageBox.warning(None, "경고", "좌표 입력 형식이 잘못되었습니다. 경도와 위도 쌍을 정확히 입력해주세요.")
            return

        # 입력된 텍스트를 숫자로 변환할 수 있는지 확인
        try:
            pointList = [float(num) for num in pointList]
        except ValueError:
            QMessageBox.warning(None, "경고", "좌표에 숫자만 입력해야 합니다.")
            return

        # 숫자 리스트를 (경도, 위도) 쌍으로 구성
        pointPairs = [pointList[i:i + 2] for i in range(0, len(pointList), 2)]

        uri = f"Point?crs={crsAuthId}"
        vl = QgsVectorLayer(uri, "포인트 매핑", "memory")
        if not vl.isValid():
            QMessageBox.warning(None, "경고", "레이어 생성 실패. 좌표계 설정을 확인하세요.")
            return

        # CRS 명시적 설정
        crs = QgsCoordinateReferenceSystem(f"{crsAuthId}")
        if not crs.isValid():
            QMessageBox.warning(None, "경고", "유효하지 않은 좌표계 코드입니다.")
            return
        vl.setCrs(crs)

        pr = vl.dataProvider()
        for idx, (lon, lat) in enumerate(pointPairs):
            feature = QgsFeature()
            feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(lon, lat)))
            pr.addFeature(feature)

        vl.updateExtents()
        QgsProject.instance().addMapLayer(vl)
        QDialog.close()