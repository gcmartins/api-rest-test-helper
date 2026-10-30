import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

from view.main_window import MainWindow
from view.request_editor import RequestEditor, HTTP_METHODS


@pytest.fixture
def editor(app):
    return RequestEditor(None)


def test_method_dropdown_lists_common_methods(editor):
    items = [editor.method.itemText(i) for i in range(editor.method.count())]
    assert items == HTTP_METHODS
    assert 'PATCH' in items
    assert editor.method.currentText() == 'GET'


def test_set_fields_selects_method_case_insensitively(editor):
    editor.setRequestFields({'method': 'patch', 'url': 'https://api.test'})
    assert editor.method.currentText() == 'PATCH'
    assert editor.method.currentIndex() == HTTP_METHODS.index('PATCH')


def test_custom_method_round_trips(editor):
    editor.setRequestFields({'method': 'purge'})
    assert editor.getRequestFields()['method'] == 'PURGE'


def test_typed_method_is_uppercased(editor):
    editor.method.setEditText(' delete ')
    assert editor.getRequestFields()['method'] == 'DELETE'


def test_get_fields_parses_json_and_raw_body(editor):
    editor.setRequestFields({'headers': {'X-A': '1'}, 'cookies': {'c': '2'}, 'payload': 'a=1'})
    fields = editor.getRequestFields()
    assert fields['headers'] == {'X-A': '1'}
    assert fields['cookies'] == {'c': '2'}
    assert fields['payload'] == 'a=1'


def test_invalid_headers_json_raises(editor):
    editor.headers.setPlainText('{bad')
    with pytest.raises(ValueError, match='HEADERS'):
        editor.getRequestFields()


@pytest.mark.parametrize('key', [Qt.Key.Key_Return, Qt.Key.Key_Enter])
def test_ctrl_enter_runs_request(app, monkeypatch, key):
    runs = []
    monkeypatch.setattr(MainWindow, 'run_request', lambda self: runs.append(True))
    window = MainWindow()
    window.activateWindow()
    window.request_editor.body.setFocus()
    app.processEvents()

    QTest.keyClick(window.request_editor.body, key, Qt.KeyboardModifier.ControlModifier)

    assert runs == [True]
    window.close()
