import mimetypes
import os
from pathlib import Path

import requests
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QSplitter, QMessageBox

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

    def parse_curl_command(self):
        dialog = CurlInputDialog(self)
        if dialog.exec():
            data = dialog.get_curl_params()

            self.request_editor.setRequestFields(data)

    def run_request(self):
        try:
            fields = self.request_editor.getRequestFields()
        except ValueError as e:
            QMessageBox.warning(self, "Invalid request", str(e))
            return

        method = fields['method']
        url = fields['url']
        payload = fields['payload']
        if not method or not url:
            QMessageBox.warning(self, "Invalid request", "METHOD and URL are required.")
            return

        files = None
        filepath = fields['filepath']
        file_key = fields['file_key']
        if filepath and file_key:
            try:
                content = Path(filepath).read_bytes()
            except OSError as e:
                QMessageBox.warning(self, "Invalid file", f"Could not read '{filepath}': {e}")
                return
            mime_type = mimetypes.guess_type(filepath)[0] or 'application/octet-stream'
            files = {
                file_key: (os.path.basename(filepath), content, mime_type),
            }

        try:
            response = run_http_request(method, url, fields['headers'], fields['cookies'], payload, files)
        except requests.RequestException as e:
            self.response.show_error(method, url, e)
            return

        self.response.update_response(method, url, payload, response)
