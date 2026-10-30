import pytest
import requests
from PySide6.QtCore import QObject, Signal

from view import main_window
from view.main_window import MainWindow
from view.request_history import MAX_ENTRIES, RequestHistory

POST_FIELDS = {
    'method': 'POST', 'url': 'https://api.test/items', 'headers': {'X-A': '1'}, 'cookies': {},
    'payload': {'name': 'x'}, 'file_key': '', 'filepath': '',
}


@pytest.fixture
def history(app):
    return RequestHistory(None)


def test_add_entry_newest_first(history):
    history.add_entry(POST_FIELDS, '201')
    history.add_entry({**POST_FIELDS, 'method': 'GET', 'url': 'https://api.test/other'}, '404')

    assert history.list.count() == 2
    assert history.list.item(0).text().endswith('GET 404  https://api.test/other')
    assert history.list.item(1).text().endswith('POST 201  https://api.test/items')


def test_history_is_capped(history):
    for i in range(MAX_ENTRIES + 5):
        history.add_entry({**POST_FIELDS, 'url': f'https://api.test/{i}'}, '200')

    assert history.list.count() == MAX_ENTRIES
    assert history.list.item(0).toolTip() == f'https://api.test/{MAX_ENTRIES + 4}'
    assert history.list.item(MAX_ENTRIES - 1).toolTip() == 'https://api.test/5'


def test_click_emits_stored_copy(history):
    fields = {**POST_FIELDS, 'headers': {'X-A': '1'}}
    history.add_entry(fields, '201')
    fields['headers']['X-A'] = 'changed'

    emitted = []
    history.entry_selected.connect(emitted.append)
    history.list.itemClicked.emit(history.list.item(0))

    assert emitted == [POST_FIELDS]


def test_clear(history):
    history.add_entry(POST_FIELDS, '201')
    history.clear_btn.click()
    assert history.list.count() == 0


class FakeResponse:
    status_code = 201
    text = '{}'

    def json(self):
        return {}


def make_fake_worker(error=None):
    class FakeWorker(QObject):
        succeeded = Signal(object)
        failed = Signal(object)
        finished = Signal()

        def __init__(self, method, url, headers, cookies, payload, files=None, parent=None):
            super().__init__(parent)
            self.method, self.url, self.payload = method, url, payload

        def start(self):
            if error:
                self.failed.emit(error)
            else:
                self.succeeded.emit(FakeResponse())
            self.finished.emit()

        def wait(self):
            pass

    return FakeWorker


@pytest.fixture
def window(app):
    window = MainWindow()
    yield window
    window.close()


def test_completed_request_is_recorded_and_reloads(window, monkeypatch):
    monkeypatch.setattr(main_window, 'RequestWorker', make_fake_worker())
    editor = window.request_editor
    editor.setRequestFields(POST_FIELDS)
    window.run_request()

    assert window.history.list.count() == 1
    assert 'POST 201  https://api.test/items' in window.history.list.item(0).text()

    # Switch to a different request, then restore the recorded one from history
    editor.setRequestFields({'method': 'GET', 'url': 'https://api.test/other', 'cookies': {'c': '1'}})
    window.history.list.itemClicked.emit(window.history.list.item(0))

    assert editor.getRequestFields() == POST_FIELDS


def test_failed_request_is_recorded(window, monkeypatch):
    monkeypatch.setattr(main_window, 'RequestWorker', make_fake_worker(requests.ConnectionError('refused')))
    window.request_editor.setRequestFields({'method': 'GET', 'url': 'https://api.test/down'})
    window.run_request()

    assert 'GET ERROR  https://api.test/down' in window.history.list.item(0).text()
