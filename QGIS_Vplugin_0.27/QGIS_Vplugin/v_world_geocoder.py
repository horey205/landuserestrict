import os
import sys
import requests
import json
import pandas as pd
from PyQt5.QtWidgets import QDialog, QMessageBox, QTableView, QApplication, QProgressBar
from PyQt5.QtGui import QColor
from PyQt5 import uic
from qgis.core import QgsVectorLayer, QgsFeature, QgsGeometry, QgsPointXY, QgsField, QgsProject
from PyQt5.QtCore import QVariant, Qt, QAbstractTableModel, QThread, pyqtSignal
import subprocess
from qgis.utils import iface

plugin_dir = os.path.dirname(__file__)
sys.path.append(plugin_dir)
from .public import public

FORM_CLASS, _ = uic.loadUiType(os.path.join(plugin_dir, 'ui/v_world_dockGeocoder_base.ui'))


class PandasModel(QAbstractTableModel):
    def __init__(self, data):
        super(PandasModel, self).__init__()
        self._data = data

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parent=None):
        return self._data.shape[1]

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid() and role == Qt.DisplayRole:
            return str(self._data.iloc[index.row(), index.column()])
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._data.columns[section])
            else:
                return str(section)


class GeocodeThread(QThread):
    finished = pyqtSignal(list)
    progress = pyqtSignal(int)

    def __init__(self, addresses, canvasCRS, apiKey):
        super().__init__()
        self.addresses = addresses
        self.canvasCRS = canvasCRS

    def run(self):
        results = []
        apiurl = "https://api.vworld.kr/req/address?"
        params = {
            "service": "address",
            "request": "getcoord",
            "crs": self.canvasCRS,
            "address": "",
            "format": "json",
            "type": "road",
            "key": public.reTurnAPIKEY(self)
        }
        total = len(self.addresses)
        for idx, address in enumerate(self.addresses):
            params['address'] = address
            response = requests.get(apiurl, params=params)
            if response.status_code == 200:
                data = response.json()
                if data['response']['status'] == 'OK':
                    results.append((data['response']['result']['point'], '성공'))
                else:
                    params['type'] = 'parcel'
                    response = requests.get(apiurl, params=params)
                    data = response.json()
                    if data['response']['status'] == 'OK':
                        results.append((data['response']['result']['point'], '성공'))
                    else:
                        if data['response']['status'] == 'NOT_FOUND':
                            results.append(({'x': 0, 'y': 0}, '주소를 찾을 수 없습니다.'))
                        else:
                            results.append(({'x': 0, 'y': 0}, f'{data["response"]["error"]["text"]}'))
            else:
                results.append(({'x': 0, 'y': 0}, f'Error {response.status_code}'))

            # Emit progress signal
            self.progress.emit(int((idx + 1) / total * 100))

        self.finished.emit(results)


class VWorldDockGeocoder(QDialog, FORM_CLASS):
    def __init__(self, parent=iface.mainWindow()):
        super(VWorldDockGeocoder, self).__init__(parent, Qt.WindowStaysOnTopHint)
        self.setupUi(self)
        self.canvas = iface.mapCanvas()
        self.mQgsFileWidget.setFilter("*.csv *.xls *.xlsx")

        # Connect signals
        self.mQgsFileWidget.fileChanged.connect(self.onFileSelected)
        self.BTNGeoStart.clicked.connect(self.geoStart)

        # Setup the tableView for column selection
        self.tableView.setSelectionBehavior(QTableView.SelectColumns)  # 열 전체 선택
        self.tableView.setSelectionMode(QTableView.SingleSelection)  # 단일 선택

        self.geocoderProgressBar.setValue(0)  # Initialize progress bar

        try:
            import pandas
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pandas"])

    def geoStart(self):
        self.BTNGeoStart.setEnabled(False)
        self.geocoderProgressBar.setValue(0)
        canvasCRS = self.canvas.mapSettings().destinationCrs().authid()

        selected = self.tableView.selectedIndexes()
        if not selected:
            QMessageBox.warning(self, "안내", "주소가 들어간 열을 선택해주세요.")
            self.BTNGeoStart.setEnabled(True)
            return

        column = selected[0].column()
        model = self.tableView.model()
        addresses = [model.data(model.index(row, column), Qt.DisplayRole) for row in range(model.rowCount())]

        self.thread = GeocodeThread(addresses, canvasCRS, public.reTurnAPIKEY(self))
        self.thread.finished.connect(self.onGeocodingFinished)
        self.thread.progress.connect(self.updateProgressBar)
        self.thread.start()

    def updateProgressBar(self, value):
        self.geocoderProgressBar.setValue(value)

    def onGeocodingFinished(self, results):
        model = self.tableView.model()
        canvasCRS = self.canvas.mapSettings().destinationCrs().authid()

        layer = QgsVectorLayer(f'Point?crs={canvasCRS}', 'Geocoder', 'memory')
        pr = layer.dataProvider()

        for col_index in range(model.columnCount()):
            field_name = model.headerData(col_index, Qt.Horizontal)
            pr.addAttributes([QgsField(field_name, QVariant.String)])
        pr.addAttributes([QgsField("비고", QVariant.String)])
        layer.updateFields()

        for idx, (result, success) in enumerate(results):
            feat = QgsFeature()
            x, y = float(result['x']), float(result['y'])
            feat.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(x, y)))
            attributes = [model.data(model.index(idx, col_index), Qt.DisplayRole) for col_index in range(model.columnCount())]
            attributes.append(success)
            feat.setAttributes(attributes)
            pr.addFeature(feat)

        layer.updateExtents()
        QgsProject.instance().addMapLayer(layer)

        QMessageBox.information(self, "안내", "지오코딩이 완료되었습니다.")
        self.BTNGeoStart.setEnabled(True)

    def onFileSelected(self, file):
        if not file:
            QMessageBox.warning(self, "오류", "선택된 파일이 없습니다.")
        else:
            self.loadData(file)

    def loadData(self, file):
        try:
            if file.endswith(('.xls', '.xlsx')):
                data = pd.read_excel(file)
            else:
                for encoding in ['utf-8', 'cp949', 'latin1']:
                    try:
                        data = pd.read_csv(file, encoding=encoding, skip_blank_lines=True)
                        break
                    except pd.errors.ParserError:
                        data = pd.read_csv(file, encoding=encoding, skip_blank_lines=False)
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    QMessageBox.warning(self, "오류", "지원하는 인코딩이 없습니다.")

            data = data.dropna(how='all')
            model = PandasModel(data)
            self.tableView.setModel(model)
        except Exception as e:
            QMessageBox.warning(self, "오류가 발생했습니다.", f"오류내용을 관리자에게 문의하세요. \n {str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VWorldDockGeocoder()
    window.show()
    sys.exit(app.exec_())
