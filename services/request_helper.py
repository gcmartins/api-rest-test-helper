import json
import re

import requests


def run_http_request(method: str, url: str, headers: dict, cookies: dict, data: dict, files=None):
    try:
        if method == "GET":
            return requests.get(url, headers=headers, cookies=cookies)
        elif method == "POST":
            return requests.post(url, headers=headers, cookies=cookies,
                                 json=data if isinstance(data, dict) else None,
                                 data=None if isinstance(data, dict) else data,
                                 files=files)
        elif method == "PUT":
            return requests.put(url, headers=headers, cookies=cookies,
                                json=data if isinstance(data, dict) else None,
                                data=None if isinstance(data, dict) else data)
        elif method == "DELETE":
            return requests.delete(url, headers=headers, cookies=cookies)
        else:
            print(f"Unsupported HTTP method: '{method}'.")

    except requests.RequestException as e:
        print(f"Request error: {e}")


def parse_curl_to_requests(curl_command: str) -> dict:
    curl_command = " ".join(curl_command.strip().splitlines())
    return {
        'method': extract_http_method(curl_command),
        'url': extract_url(curl_command),
        'headers': extract_headers(curl_command),
        'cookies': extract_cookies(curl_command),
        'payload': extract_payload(curl_command)
    }


def parse_headers_to_requests(curl_command: str) -> dict:
    curl_command = " ".join(curl_command.strip().splitlines())
    return {
        'headers': extract_headers(curl_command),
        'cookies': extract_cookies(curl_command)
    }


def extract_http_method(curl_command):
    method_match = re.search(r"-X (\w+)", curl_command)
    method = method_match.group(1).upper() if method_match else ("POST" if "--data" in curl_command else "GET")
    return method


def extract_url(curl_command):
    url_pattern = r"curl '([^']+)'"
    url_match = re.search(url_pattern, curl_command)
    url = url_match.group(1) if url_match else None
    return url


def extract_payload(curl_command):
    payload_match = re.search(r"--data(?:-raw|-binary)? '([^']+)'", curl_command)
    raw_data = payload_match.group(1) if payload_match else None
    payload = None
    if raw_data:
        try:
            payload = json.loads(raw_data)
        except json.JSONDecodeError:
            pass
    return payload


def extract_cookies(curl_command):
    cookies_match = re.search(r"-b '([^']+)'", curl_command)
    cookies = {}
    if cookies_match:
        cookie_string = cookies_match.group(1)
        cookies = dict(cookie.strip().split("=", 1) for cookie in cookie_string.split(";"))
    return cookies


def extract_headers(curl_command):
    headers_pattern = r"-H '([^:]+): ([^']+)'"
    headers = dict(re.findall(headers_pattern, curl_command))
    return headers
