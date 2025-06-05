import json

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLineEdit, QLabel, QTextEdit, QFileDialog, QHBoxLayout


class TextEditWithTabSpaces(QTextEdit):
    def __init__(self, parent=None, tab_spaces=4):
        super().__init__(parent)
        self.tab_spaces = tab_spaces

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Tab:
            cursor = self.textCursor()
            cursor.insertText(' ' * self.tab_spaces)
        else:
            super().keyPressEvent(event)


class RequestEditor(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.layout = QVBoxLayout()

        self.btn = QPushButton("Import from CURL")
        self.load_btn = QPushButton("Load Payload")
        self.load_btn.clicked.connect(self.loadPayload)
        self.save_btn = QPushButton("Save Payload")
        self.save_btn.clicked.connect(self.savePayload)

        self.url = QLineEdit(self)
        url_label = QLabel('URL')
        headers_label = QLabel('HEADERS')
        cookies_label = QLabel('COOKIES')
        body_label = QLabel('BODY')
        method_label = QLabel('METHOD')
        self.headers = QTextEdit(self)
        self.headers.setMaximumHeight(250)
        self.cookies = QTextEdit(self)
        self.cookies.setMaximumHeight(150)
        self.body = TextEditWithTabSpaces(self)
        self.method = QLineEdit(self)

        h_layout = QHBoxLayout()
        h_layout.addWidget(self.btn)
        h_layout.addWidget(self.load_btn)
        self.layout.addLayout(h_layout)
        self.layout.addWidget(method_label)
        self.layout.addWidget(self.method)
        self.layout.addWidget(url_label)
        self.layout.addWidget(self.url)
        self.layout.addWidget(cookies_label)
        self.layout.addWidget(self.cookies)
        self.layout.addWidget(headers_label)
        self.layout.addWidget(self.headers)
        self.layout.addWidget(body_label)
        self.layout.addWidget(self.body)
        self.layout.addWidget(self.save_btn)

        self.setLayout(self.layout)

    def setRequestFields(self, data: dict):
        url = data.get('url')
        method = data.get('method')
        headers = data.get('headers')
        payload = data.get('payload')
        cookies = data.get('cookies')

        if method:
            self.method.setText(method)
        if url:
            self.url.setText(url)
        if headers:
            self.headers.setPlainText(json.dumps(headers, indent=4, ensure_ascii=False))
        if payload:
            self.body.setPlainText(json.dumps(payload, indent=4, ensure_ascii=False))
        if cookies:
            self.cookies.setPlainText(json.dumps(cookies, indent=4, ensure_ascii=False))

    def savePayload(self):
        method = self.method.text()
        url = self.url.text()
        payload = self.body.toPlainText()
        data = json.loads(payload) if payload else ''

        data_save = {
            'url': url,
            'method': method,
            'payload': data
        }

        suggested_name = f'{method}_{url.replace('/', '\\')}.json'
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save as",
            suggested_name,
            "JSON Files (*.json);;All files (*)"
        )

        text_data = json.dumps(data_save, indent=4, ensure_ascii=False)

        with open(file_path, 'w') as f:
            f.write(text_data)

    def loadPayload(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Payload file",
            filter="JSON Files (*.json);;All files (*)"
        )

        with open(file_path, 'r') as f:
            text = f.read()
            data = json.loads(text)
            self.setRequestFields(data)
