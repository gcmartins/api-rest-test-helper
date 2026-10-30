import json
import re

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLineEdit, QLabel, QTextEdit, QFileDialog, QHBoxLayout, \
    QMessageBox


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
        self._layout = QVBoxLayout()

        self.btn = QPushButton("Import from CURL")
        self.load_btn = QPushButton("Load Payload")
        self.load_btn.clicked.connect(self.loadPayload)
        self.save_btn = QPushButton("Save Payload")
        self.file_btn = QPushButton("Choose File")
        self.save_btn.clicked.connect(self.savePayload)
        self.file_btn.clicked.connect(self.choose_file)

        self.url = QLineEdit(self)
        url_label = QLabel('URL')
        headers_label = QLabel('HEADERS')
        cookies_label = QLabel('COOKIES')
        body_label = QLabel('BODY')
        method_label = QLabel('METHOD')
        file_label = QLabel('FILE')
        self.headers = QTextEdit(self)
        self.headers.setMaximumHeight(250)
        self.cookies = QTextEdit(self)
        self.cookies.setMaximumHeight(150)
        self.body = TextEditWithTabSpaces(self)
        self.method = QLineEdit(self)
        self.file_key = QLineEdit(self)
        self.filepath = QLineEdit(self)

        h_layout = QHBoxLayout()
        h_layout.addWidget(self.btn)
        h_layout.addWidget(self.load_btn)
        self._layout.addLayout(h_layout)
        self._layout.addWidget(method_label)
        self._layout.addWidget(self.method)
        self._layout.addWidget(url_label)
        self._layout.addWidget(self.url)
        self._layout.addWidget(cookies_label)
        self._layout.addWidget(self.cookies)
        self._layout.addWidget(headers_label)
        self._layout.addWidget(self.headers)
        h_layout2 = QHBoxLayout()
        h_layout2.addWidget(self.file_key)
        h_layout2.addWidget(self.filepath)
        h_layout2.addWidget(self.file_btn)
        self._layout.addWidget(file_label)
        self._layout.addLayout(h_layout2)
        self._layout.addWidget(body_label)
        self._layout.addWidget(self.body)
        self._layout.addWidget(self.save_btn)

        self.setLayout(self._layout)

    def setRequestFields(self, data: dict):
        url = data.get('url')
        method = data.get('method')
        headers = data.get('headers')
        payload = data.get('payload')
        cookies = data.get('cookies')
        file_key = data.get('file_key')
        filepath = data.get('filepath')

        if method:
            self.method.setText(method)
        if url:
            self.url.setText(url)
        if headers:
            self.headers.setPlainText(json.dumps(headers, indent=4, ensure_ascii=False))
        if isinstance(payload, str):
            self.body.setPlainText(payload)
        elif payload:
            self.body.setPlainText(json.dumps(payload, indent=4, ensure_ascii=False))
        if cookies:
            self.cookies.setPlainText(json.dumps(cookies, indent=4, ensure_ascii=False))
        if file_key:
            self.file_key.setText(file_key)
        if filepath:
            self.filepath.setText(filepath)

    def getRequestFields(self) -> dict:
        """Returns the parsed editor fields. Raises ValueError naming the field with invalid JSON."""
        body = self.body.toPlainText().strip()
        try:
            payload = json.loads(body) if body else None
        except json.JSONDecodeError:
            # Non-JSON bodies are sent as raw text
            payload = body

        return {
            'method': self.method.text().strip().upper(),
            'url': self.url.text().strip(),
            'headers': self._parse_json_field('HEADERS', self.headers.toPlainText()),
            'cookies': self._parse_json_field('COOKIES', self.cookies.toPlainText()),
            'payload': payload,
            'file_key': self.file_key.text().strip(),
            'filepath': self.filepath.text().strip(),
        }

    @staticmethod
    def _parse_json_field(name: str, text: str) -> dict:
        if not text.strip():
            return {}
        try:
            value = json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f'{name} is not valid JSON: {e}')
        if not isinstance(value, dict):
            raise ValueError(f'{name} must be a JSON object')
        return value

    def choose_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select file",
        )
        if file_path:
            self.filepath.setText(file_path)

    def savePayload(self):
        try:
            fields = self.getRequestFields()
        except ValueError as e:
            QMessageBox.warning(self, "Invalid request", str(e))
            return

        method = fields['method']
        url = fields['url']
        data_save = {
            'url': url,
            'method': method,
            'payload': fields['payload'],
            'headers': fields['headers'],
            'cookies': fields['cookies'],
        }

        suggested_name = f"{method}_{re.sub(r'[^\w.-]+', '_', url).strip('_')}.json"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save as",
            suggested_name,
            "JSON Files (*.json);;All files (*)"
        )

        text_data = json.dumps(data_save, indent=4, ensure_ascii=False)

        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(text_data)

    def loadPayload(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Payload file",
            filter="JSON Files (*.json);;All files (*)"
        )

        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except (OSError, json.JSONDecodeError) as e:
                QMessageBox.warning(self, "Load failed", f"Could not load '{file_path}': {e}")
                return
            self.setRequestFields(data)
