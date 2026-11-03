import mimetypes
import os
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QMessageBox, QSplitter, QVBoxLayout, QWidget

from view.curl_input_dialog import CurlInputDialog
from view.request_editor import RequestEditor
from view.request_history import RequestHistory
from view.request_worker import RequestWorker
from view.response_output import ResponseOutput


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("API test helper")
        self.showMaximized()

        self.history = RequestHistory(self)
        self.request_editor = RequestEditor(self)
        self.response = ResponseOutput(self)
        self._worker = None
        self._pending_fields = None

        self.history.entry_selected.connect(lambda fields: self.request_editor.setRequestFields(fields, replace=True))
        self.request_editor.btn.clicked.connect(self.parse_curl_command)
        self.response.request_btn.clicked.connect(self.run_request)
        # click() is a no-op while the button is disabled, so this can't start a second request
        for keys in ("Ctrl+Return", "Ctrl+Enter"):
            QShortcut(QKeySequence(keys), self).activated.connect(self.response.request_btn.click)
        self.request_editor.history_btn.toggled.connect(self.history.setVisible)
        QShortcut(QKeySequence("Ctrl+H"), self).activated.connect(self.request_editor.history_btn.toggle)

        layout = QVBoxLayout(self)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.history)
        splitter.addWidget(self.request_editor)
        splitter.addWidget(self.response)
        splitter.setSizes([220, 450, 550])
        # Hidden by default; the minimum width keeps it readable when toggled on
        self.history.setMinimumWidth(200)
        self.history.hide()
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

        # Only one request runs at a time (the Run button is disabled), so this matches the finished request
        self._pending_fields = fields
        self._worker = RequestWorker(method, url, fields['headers'], fields['cookies'], payload, files, self)
        self._worker.succeeded.connect(self._on_request_succeeded)
        self._worker.failed.connect(self._on_request_failed)
        self._worker.finished.connect(self._on_request_finished)
        self.response.request_btn.setEnabled(False)
        self.response.request_btn.setText("Running...")
        self._worker.start()

    def _on_request_succeeded(self, response):
        worker = self.sender()
        self.response.update_response(worker.method, worker.url, worker.payload, response)
        self.history.add_entry(self._pending_fields, str(response.status_code))

    def _on_request_failed(self, error):
        worker = self.sender()
        self.response.show_error(worker.method, worker.url, error)
        self.history.add_entry(self._pending_fields, 'ERROR')

    def _on_request_finished(self):
        self.sender().deleteLater()
        self._worker = None
        self.response.request_btn.setText("Run request")
        self.response.request_btn.setEnabled(True)

    def closeEvent(self, event):
        # A QThread destroyed while running aborts the app; let the request finish (bounded by its timeout)
        if self._worker is not None:
            self._worker.wait()
        super().closeEvent(event)
