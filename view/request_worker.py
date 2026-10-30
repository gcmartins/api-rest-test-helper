from PySide6.QtCore import QThread, Signal

from services.request_helper import run_http_request


class RequestWorker(QThread):
    """Runs an HTTP request off the GUI thread and reports the result through signals."""
    succeeded = Signal(object)
    failed = Signal(object)

    def __init__(self, method: str, url: str, headers: dict, cookies: dict, payload, files=None, parent=None):
        super().__init__(parent)
        self.method = method
        self.url = url
        self.headers = headers
        self.cookies = cookies
        self.payload = payload
        self.files = files

    def run(self):
        try:
            response = run_http_request(self.method, self.url, self.headers, self.cookies, self.payload, self.files)
        except Exception as e:
            # Report anything, so a failure never leaves the UI waiting for a result
            self.failed.emit(e)
        else:
            self.succeeded.emit(response)
