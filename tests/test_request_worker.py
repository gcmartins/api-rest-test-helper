import threading

import requests
from PySide6.QtCore import QEventLoop, QTimer

from view import request_worker
from view.request_worker import RequestWorker


def run_worker(worker):
    results = {}
    loop = QEventLoop()
    worker.succeeded.connect(lambda response: results.update(response=response))
    worker.failed.connect(lambda error: results.update(error=error))
    worker.finished.connect(loop.quit)
    QTimer.singleShot(5000, loop.quit)
    worker.start()
    loop.exec()
    worker.wait()
    return results


def test_request_runs_off_the_calling_thread(app, monkeypatch):
    calls = {}

    def fake_request(method, url, headers, cookies, payload, files):
        calls.update(args=(method, url, headers, cookies, payload, files), thread=threading.current_thread())
        return 'response'

    monkeypatch.setattr(request_worker, 'run_http_request', fake_request)
    results = run_worker(RequestWorker('POST', 'https://api.test', {'h': '1'}, {'c': '2'}, {'a': 1}))

    assert results == {'response': 'response'}
    assert calls['args'] == ('POST', 'https://api.test', {'h': '1'}, {'c': '2'}, {'a': 1}, None)
    assert calls['thread'] is not threading.main_thread()


def test_request_error_is_reported(app, monkeypatch):
    error = requests.ConnectionError('refused')

    def fake_request(*args):
        raise error

    monkeypatch.setattr(request_worker, 'run_http_request', fake_request)
    results = run_worker(RequestWorker('GET', 'https://api.test', {}, {}, None))

    assert results == {'error': error}
