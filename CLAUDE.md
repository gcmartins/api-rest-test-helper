# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`api-rest-test-helper` is a Python desktop GUI application for testing REST APIs, built with PySide6 (Qt) and the `requests` library. It allows users to compose HTTP requests manually or by importing CURL commands, execute them, and inspect responses.

## Running the Application

```bash
pip install -r requirements.txt
python app.py
```

## Architecture

The project uses a view/service separation:

- **`app.py`** — Entry point. Creates the `QApplication` and `MainWindow`.
- **`view/`** — PySide6 GUI components. Each file is one widget class.
  - `main_window.py` — Central orchestrator. Wires `RequestEditor`, `ResponseOutput`, and `CurlInputDialog` together; owns the request execution flow.
  - `request_editor.py` — Input form (method, URL, headers, cookies, body). Handles save/load of request payloads as JSON files.
  - `response_output.py` — Displays HTTP responses; handles both JSON and plain text. Supports saving response to a text file.
  - `curl_input_dialog.py` — Modal dialog that accepts a CURL command string and returns parsed parameters to `MainWindow` in two modes: full command parse or headers-only parse.
- **`services/request_helper.py`** — All HTTP and CURL logic lives here. `run_http_request()` executes requests; `parse_curl_to_requests()` and `parse_headers_to_requests()` use regex to extract parameters from CURL strings.

## Key Conventions

- Headers, cookies, and request body are passed as JSON-formatted strings between the view and service layers; `request_helper.py` deserializes them with `json.loads()` before use.
- CURL parsing is regex-based (no external CURL-parsing library). New CURL flags/options require adding corresponding regex patterns in `services/request_helper.py`.
- `TextEditWithTabSpaces` in `request_editor.py` is a custom `QTextEdit` subclass that converts Tab keypresses to spaces — used for all JSON input fields to keep formatting consistent.
- There is no test infrastructure, linting configuration, or CI/CD pipeline in this repository.
