import base64

import pytest

from services import request_helper
from services.request_helper import parse_curl_to_requests, parse_headers_to_requests, run_http_request


def test_url_flag_style():
    parsed = parse_curl_to_requests("curl --url 'https://api.test/items' -X PUT")
    assert parsed['url'] == 'https://api.test/items'
    assert parsed['method'] == 'PUT'


def test_positional_url_defaults_to_get():
    parsed = parse_curl_to_requests("curl 'https://api.test/items'")
    assert parsed['url'] == 'https://api.test/items'
    assert parsed['method'] == 'GET'
    assert parsed['payload'] is None


def test_chrome_style_multiline_with_continuations():
    cmd = (
        "curl 'https://api.test/items' \\\n"
        "  -H 'accept: application/json' \\\n"
        "  -H 'authorization: Bearer abc:def' \\\n"
        "  -b 'session=123; theme=dark' \\\n"
        "  --data-raw '{\"name\":\"x\",\"tags\":[1,2]}' \\\n"
        "  --compressed"
    )
    parsed = parse_curl_to_requests(cmd)
    assert parsed['method'] == 'POST'
    assert parsed['url'] == 'https://api.test/items'
    assert parsed['headers'] == {'accept': 'application/json', 'authorization': 'Bearer abc:def'}
    assert parsed['cookies'] == {'session': '123', 'theme': 'dark'}
    assert parsed['payload'] == {'name': 'x', 'tags': [1, 2]}


def test_double_quotes_and_long_flags():
    cmd = 'curl --request patch --header "Content-Type: application/json" --data "{\\"a\\": 1}" "https://api.test/x"'
    parsed = parse_curl_to_requests(cmd)
    assert parsed['method'] == 'PATCH'
    assert parsed['headers'] == {'Content-Type': 'application/json'}
    assert parsed['payload'] == {'a': 1}
    assert parsed['url'] == 'https://api.test/x'


def test_attached_and_equals_values():
    parsed = parse_curl_to_requests("curl -XDELETE --url=https://api.test/1 -HX-Trace:abc")
    assert parsed['method'] == 'DELETE'
    assert parsed['url'] == 'https://api.test/1'
    assert parsed['headers'] == {'X-Trace': 'abc'}


def test_non_json_payload_is_kept_raw():
    parsed = parse_curl_to_requests("curl https://api.test -d 'a=1' -d 'b=2'")
    assert parsed['method'] == 'POST'
    assert parsed['payload'] == 'a=1&b=2'


def test_get_flag_moves_data_to_query_string():
    parsed = parse_curl_to_requests("curl -G https://api.test/search?x=1 -d q=term")
    assert parsed['method'] == 'GET'
    assert parsed['url'] == 'https://api.test/search?x=1&q=term'
    assert parsed['payload'] is None


def test_cookie_header_and_malformed_cookie():
    parsed = parse_curl_to_requests("curl https://api.test -H 'Cookie: a=1; broken; b=x=y'")
    assert parsed['headers'] == {}
    assert parsed['cookies'] == {'a': '1', 'b': 'x=y'}


def test_basic_auth_and_ignored_flags():
    parsed = parse_curl_to_requests("curl -s -L -o out.json -u user:pass https://api.test")
    assert parsed['url'] == 'https://api.test'
    expected = base64.b64encode(b'user:pass').decode()
    assert parsed['headers'] == {'Authorization': f'Basic {expected}'}


def test_json_flag_sets_headers():
    parsed = parse_curl_to_requests("curl --json '{\"k\": true}' https://api.test")
    assert parsed['method'] == 'POST'
    assert parsed['payload'] == {'k': True}
    assert parsed['headers']['Content-Type'] == 'application/json'


def test_form_with_file():
    parsed = parse_curl_to_requests("curl -F 'name=report' -F 'upload=@/tmp/data.csv;type=text/csv' https://api.test/up")
    assert parsed['method'] == 'POST'
    assert parsed['payload'] == {'name': 'report'}
    assert parsed['file_key'] == 'upload'
    assert parsed['filepath'] == '/tmp/data.csv'


def test_parse_headers_only():
    parsed = parse_headers_to_requests("curl https://api.test -H 'X-A: 1' -b 'c=2' -d '{}'")
    assert parsed == {'headers': {'X-A': '1'}, 'cookies': {'c': '2'}}


class _Recorder:
    def __call__(self, method, url, **kwargs):
        self.method, self.url, self.kwargs = method, url, kwargs
        return 'response'


@pytest.fixture
def recorder(monkeypatch):
    rec = _Recorder()
    monkeypatch.setattr(request_helper.requests, 'request', rec)
    return rec


def test_run_request_sends_json_body_for_any_method(recorder):
    assert run_http_request('delete', 'https://api.test', {}, {}, {'id': 1}) == 'response'
    assert recorder.method == 'DELETE'
    assert recorder.kwargs['json'] == {'id': 1}
    assert 'data' not in recorder.kwargs


def test_run_request_empty_body_sends_nothing(recorder):
    run_http_request('POST', 'https://api.test', {}, {}, None)
    assert 'json' not in recorder.kwargs and 'data' not in recorder.kwargs


def test_run_request_raw_body(recorder):
    run_http_request('PUT', 'https://api.test', {}, {}, 'a=1')
    assert recorder.kwargs['data'] == 'a=1'
    assert recorder.kwargs['timeout'] == request_helper.DEFAULT_TIMEOUT


def test_run_request_with_files_sends_body_as_form_fields(recorder):
    files = {'f': ('a.csv', b'x', 'text/csv')}
    run_http_request('PUT', 'https://api.test', {}, {}, {'name': 'report'}, files)
    assert recorder.kwargs['data'] == {'name': 'report'}
    assert recorder.kwargs['files'] == files
    assert 'json' not in recorder.kwargs

    run_http_request('POST', 'https://api.test', {}, {}, 'a=1&b=2', files)
    assert recorder.kwargs['data'] == [('a', '1'), ('b', '2')]
