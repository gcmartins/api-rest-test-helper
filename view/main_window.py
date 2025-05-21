import json

from PySide6.QtGui import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QSplitter

from services.request_helper import run_http_request
from view.curl_input_dialog import CurlInputDialog
from view.request_editor import RequestEditor
from view.response_output import ResponseOutput


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("API test helper")
        self.showMaximized()

        self.request_editor = RequestEditor(self)
        self.response = ResponseOutput(self)

        self.request_editor.btn.clicked.connect(self.parse_curl_command)
        self.response.request_btn.clicked.connect(self.run_request)

        layout = QVBoxLayout(self)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.request_editor)
        splitter.addWidget(self.response)
        splitter.setSizes([450, 550])
        layout.addWidget(splitter)
        self.setLayout(layout)
        self.cookies = None

    def parse_curl_command(self):
        dialog = CurlInputDialog(self)
        if dialog.exec_():
            data = dialog.get_curl_params()
            cookies = data.get('cookies')
            self.cookies = cookies

            self.request_editor.setRequestFields(data)

    def run_request(self):
        method = self.request_editor.method.text()
        url = self.request_editor.url.text()
        header_text = self.request_editor.headers.toPlainText()
        headers = json.loads(header_text) if header_text else dict()
        payload_text = self.request_editor.body.toPlainText()
        payload = json.loads(payload_text) if payload_text else dict()

        response = run_http_request(method, url, headers, self.cookies, payload)

        self.response.update_response(method, url, payload, response)

