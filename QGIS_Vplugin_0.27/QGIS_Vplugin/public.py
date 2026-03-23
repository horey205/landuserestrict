from PyQt5 import QtWidgets, QtGui
import json
import os
import random
from PyQt5.QtGui import QColor


class public:
    def showMessage_sslConnectError(self):  # 오타 수정
        QDialog = QtWidgets.QDialog()
        QDialog.setWindowTitle("SSL 연결 실패")
        QDialog.resize(500, 200)
        layout = QtWidgets.QVBoxLayout()
        #텍스트 추가
        label = QtWidgets.QLabel("옵션에서 '브이월드 호출방식'을 HTTP 또는 HTTPS(보안무시)로 변경해주세요.")
        layout.addWidget(label)
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        label.setFont(font)
        labelWarning = QtWidgets.QLabel("설정 후 QGIS 재시작을 권장합니다.")
        fontWarning = QtGui.QFont()
        fontWarning.setPointSize(11)
        labelWarning.setStyleSheet("color: red")

        labelWarning.setFont(fontWarning)
        layout.addWidget(labelWarning)
        #이미지 추가
        label = QtWidgets.QLabel()
        label.setPixmap(QtGui.QPixmap(os.path.join(os.path.dirname(__file__), "images", "SSL통신오류.png")))
        layout.addWidget(label)
        QDialog.setLayout(layout)
        QDialog.exec_()

    def reTurnAPIKEY(self):
        options_path = os.path.join(os.path.dirname(__file__), "datas", "options.json")

        # 해당 경로의 폴더가 없다면 폴더를 생성
        if not os.path.exists(os.path.dirname(options_path)):
            os.makedirs(os.path.dirname(options_path))

        # 옵션 파일이 없다면 빈 JSON 파일을 생성
        if not os.path.exists(options_path):
            with open(options_path, "w", encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False)

        try:
            # 옵션 파일을 열고 JSON 데이터를 로드
            with open(options_path, "r") as file:
                options = json.load(file)
            # API_KEY 값을 반환하되, 없을 경우 빈 문자열을 반환
            return options.get('API_KEY', '')
        except Exception:
            # 파일 열기 오류나 JSON 로딩 실패 시 빈 문자열 반환
            return ''

    def randomColor(self):
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        return QColor(r, g, b).name()

    def return_protocol(self):
        options_path = os.path.join(os.path.dirname(__file__), "datas", "options.json")

        # 해당 경로의 폴더가 없다면 폴더를 생성
        if not os.path.exists(os.path.dirname(options_path)):
            os.makedirs(os.path.dirname(options_path))

        # 옵션 파일이 없다면 빈 JSON 파일을 생성
        if not os.path.exists(options_path):
            with open(options_path, "w", encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False)
        try:
            # 옵션 파일을 열어 내용을 읽습니다.
            with open(options_path, "r") as file:
                options = json.load(file)
            # 'protocol' 키가 없을 경우 기본값을 반환합니다.
            if "protocol" not in options:
                return ["https://", True]
            # 'protocol' 키에 따라 적절한 값을 반환합니다.
            if options["protocol"] == "HTTP":
                return ["http://", True]
            elif options["protocol"] == "HTTPS(기본값)":
                return ["https://", True]
            elif options["protocol"] == "HTTPS(보안무시)":
                return ["https://", False]
        except Exception as e:
            return ["https://", True]
        return ["https://", True]

    def return_landLabelSytle(self):
        options_path = os.path.join(os.path.dirname(__file__), "datas", "options.json")
        if not os.path.exists(options_path):
            os.makedirs(os.path.dirname(options_path), exist_ok=True)
            with open(options_path, "w", encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False)

        try:
            # 옵션 파일을 열어 내용을 읽습니다.
            with open(options_path, "r", encoding='utf-8') as file:
                options = json.load(file)
                return options.get("landLabelSytle", True)
        except Exception as e:
            return False
