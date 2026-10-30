import base64
import json
import re
import shlex
from urllib.parse import parse_qsl

import requests

DEFAULT_TIMEOUT = 30

DATA_FLAGS = {'-d', '--data', '--data-raw', '--data-binary', '--data-ascii', '--data-urlencode'}

# Flags that take an argument we don't use; listed so their argument isn't mistaken for the URL
IGNORED_FLAGS_WITH_ARG = {
    '-o', '--output', '-m', '--max-time', '--connect-timeout', '--retry', '-w', '--write-out',
    '-x', '--proxy', '--cacert', '--cert', '--key', '-K', '--config', '-c', '--cookie-jar',
    '-T', '--upload-file', '-r', '--range', '--resolve', '--interface',
}

# Short flags that accept their argument attached, e.g. -XPOST
SHORT_FLAGS_WITH_ARG = {'-X', '-H', '-d', '-b', '-u', '-F', '-A', '-e'}

FLAGS_WITH_ARG = DATA_FLAGS | IGNORED_FLAGS_WITH_ARG | SHORT_FLAGS_WITH_ARG | {
    '--request', '--url', '--header', '--cookie', '--json', '--form', '--user', '--user-agent', '--referer',
}


def run_http_request(method: str, url: str, headers: dict, cookies: dict, data, files=None,
                     timeout=DEFAULT_TIMEOUT):
    """Runs the request. Raises requests.RequestException on failure."""
    kwargs = {'headers': headers, 'cookies': cookies, 'files': files, 'timeout': timeout}
    if files:
        # Multipart requests can't carry a JSON or raw body; send it as form fields instead
        if isinstance(data, str):
            data = parse_qsl(data, keep_blank_values=True)
        if data:
            kwargs['data'] = data
    elif isinstance(data, (dict, list)):
        if data:
            kwargs['json'] = data
    elif data:
        kwargs['data'] = data
    return requests.request(method.upper(), url, **kwargs)


def parse_curl_to_requests(curl_command: str) -> dict:
    return _parse_curl(curl_command)


def parse_headers_to_requests(curl_command: str) -> dict:
    parsed = _parse_curl(curl_command)
    return {
        'headers': parsed['headers'],
        'cookies': parsed['cookies']
    }


def _tokenize(curl_command: str) -> list[str]:
    # Join shell line continuations before splitting
    curl_command = re.sub(r'\\\r?\n', ' ', curl_command.strip())
    curl_command = " ".join(curl_command.splitlines())
    return shlex.split(curl_command)


def _parse_curl(curl_command: str) -> dict:
    tokens = _tokenize(curl_command)
    if tokens and tokens[0] == 'curl':
        tokens = tokens[1:]

    method = None
    url = None
    headers = {}
    cookies = {}
    data_parts = []
    form = {}
    file_field = None
    force_get = False

    i = 0
    while i < len(tokens):
        token = tokens[i]
        i += 1

        if not token.startswith('-') or token == '-':
            if url is None:
                url = token
            continue

        # Split --flag=value and attached short flag values (-XPOST)
        value = None
        if token.startswith('--') and '=' in token:
            token, value = token.split('=', 1)
        elif not token.startswith('--') and len(token) > 2 and token[:2] in SHORT_FLAGS_WITH_ARG:
            token, value = token[:2], token[2:]

        # Flags that take an argument read it from the next token unless it was attached
        if token in FLAGS_WITH_ARG and value is None:
            value = tokens[i] if i < len(tokens) else ''
            i += 1

        if token in ('-X', '--request'):
            method = value.upper()
        elif token == '--url':
            url = value
        elif token in ('-H', '--header'):
            _add_header(value, headers, cookies)
        elif token in ('-b', '--cookie'):
            cookies.update(_parse_cookie_string(value))
        elif token in DATA_FLAGS:
            data_parts.append(value)
        elif token == '--json':
            data_parts.append(value)
            headers.setdefault('Content-Type', 'application/json')
            headers.setdefault('Accept', 'application/json')
        elif token in ('-F', '--form'):
            key, _, field_value = value.partition('=')
            if field_value.startswith('@'):
                file_field = (key, field_value[1:].split(';', 1)[0])
            else:
                form[key] = field_value
        elif token in ('-u', '--user'):
            credentials = base64.b64encode(value.encode()).decode()
            headers['Authorization'] = f'Basic {credentials}'
        elif token in ('-A', '--user-agent'):
            headers['User-Agent'] = value
        elif token in ('-e', '--referer'):
            headers['Referer'] = value
        elif token in ('-I', '--head'):
            method = 'HEAD'
        elif token in ('-G', '--get'):
            force_get = True

    payload = None
    if data_parts:
        raw_data = '&'.join(data_parts)
        try:
            payload = json.loads(raw_data)
        except json.JSONDecodeError:
            payload = raw_data
    elif form:
        payload = form

    if force_get and isinstance(payload, str) and url:
        url = f"{url}{'&' if '?' in url else '?'}{payload}"
        payload = None

    if method is None:
        has_body = payload is not None or file_field is not None
        method = 'POST' if has_body and not force_get else 'GET'

    result = {
        'method': method,
        'url': url,
        'headers': headers,
        'cookies': cookies,
        'payload': payload
    }
    if file_field:
        result['file_key'], result['filepath'] = file_field
    return result


def _add_header(header: str, headers: dict, cookies: dict):
    name, sep, value = header.partition(':')
    if not sep:
        return
    name, value = name.strip(), value.strip()
    if name.lower() == 'cookie':
        cookies.update(_parse_cookie_string(value))
    else:
        headers[name] = value


def _parse_cookie_string(cookie_string: str) -> dict:
    cookies = {}
    for cookie in cookie_string.split(';'):
        name, sep, value = cookie.strip().partition('=')
        if sep and name:
            cookies[name] = value
    return cookies
