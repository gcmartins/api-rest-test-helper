import json

from PySide6.QtWidgets import QVBoxLayout, QPushButton, QPlainTextEdit, QWidget, QLabel, QLineEdit, QHBoxLayout, \
    QFileDialog


class ResponseOutput(QWidget):

    def __init__(self, parent):
        super().__init__(parent)
        layout = QVBoxLayout()

        self.output = QPlainTextEdit(self)
        self.request_btn = QPushButton("Run request")
        self.status_code = QLineEdit(self)

        layout.addWidget(self.request_btn)
        layout.addWidget(QLabel('STATUS CODE'))
        layout.addWidget(self.status_code)
        layout.addWidget(QLabel('RESPONSE'))
        layout.addWidget(self.output)

        h_layout = QHBoxLayout()
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.output.clear)
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.saveResponse)
        h_layout.addWidget(self.clear_btn)
        h_layout.addWidget(self.save_btn)
        layout.addLayout(h_layout)

        self.setLayout(layout)

    def update_response(self, method: str, url: str, payload: dict, response):
        self.status_code.setText(str(response.status_code))
        self.output.appendPlainText('---')
        self.output.appendPlainText(f'{method} {url}')
        if payload:
            self.output.appendPlainText('PAYLOAD:')
            self.output.appendPlainText(json.dumps(payload, indent=4))
        try:
            result = json.dumps(response.json(), indent=4)
            self.output.appendPlainText(f'STATUS CODE: {response.status_code}')
            self.output.appendPlainText('RESPONSE:')
            self.output.appendPlainText(result)
        except json.JSONDecodeError:
            self.output.appendPlainText(f'STATUS CODE: {response.status_code}')
            self.output.appendPlainText('RESPONSE:')
            self.output.appendPlainText(response.text)

    def saveResponse(self):
        data = self.output.toPlainText()
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save as",
            filter="TXT Files (*.txt);;All files (*)"
        )

        with open(file_path, 'w') as f:
            f.write(data)
