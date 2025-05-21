from PySide6.QtWidgets import QDialog, QPushButton, QVBoxLayout, QPlainTextEdit, QHBoxLayout

from services.request_helper import parse_curl_to_requests, parse_headers_to_requests


class CurlInputDialog(QDialog):

    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Paste CURL command")
        self.setMinimumSize(600, 600)

        layout = QVBoxLayout()

        h_layout = QHBoxLayout()

        self.btn = QPushButton("Parse full CURL command")
        self.btn.clicked.connect(self.parse_curl_command)
        self.headers_btn = QPushButton("Parse headers only")
        self.headers_btn.clicked.connect(self.parse_headers)

        h_layout.addWidget(self.btn)
        h_layout.addWidget(self.headers_btn)

        self.curl_input = QPlainTextEdit()

        layout.addWidget(self.curl_input)
        layout.addLayout(h_layout)
        self.setLayout(layout)

    def parse_curl_command(self):
        self.output = parse_curl_to_requests(self.curl_input.toPlainText())
        self.accept()

    def parse_headers(self):
        self.output = parse_headers_to_requests(self.curl_input.toPlainText())
        self.accept()

    def get_curl_params(self):
        return self.output
