# API REST Test Helper

A desktop app (PySide6 + `requests`) for building, importing and running HTTP API requests. Paste a cURL command copied from the browser dev tools or another tool, tweak the request, and inspect the response side by side.

## Features

- **Request editor**: method dropdown (GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS, or type a custom one), URL, headers and cookies as JSON, a JSON or raw body, and an optional file upload (sent as multipart form data).
- **cURL import**: parse a full cURL command, or only its headers and cookies. Supports `-X`, `-H`, `-b`, `-d`/`--data-*`, `--json`, `-F`, `-u`, `-G` and more.
- **Save and load requests** as JSON files.
- **Request history** for the session: click an entry to load it back into the editor. History is kept in memory only and cleared when the app closes.
- **Responses**: status code, pretty-printed JSON (or raw text) appended to a log you can save to a file.
- Requests run in the background with a 30-second timeout, so the window stays responsive. Press **Ctrl+Enter** to run the request.

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- On headless or minimal Linux installs, Qt also needs `libegl1` and `libxkbcommon0`.

## Running

```bash
uv sync
uv run app.py
```

## Development

```bash
uv run pytest --cov      # tests with coverage
uv run ruff check .      # lint
```

CI (`.github/workflows/tests.yml`) runs the linter and the tests on every pull request and posts a coverage report as a PR comment. Widget tests run headless with `QT_QPA_PLATFORM=offscreen`, which `tests/conftest.py` sets by default.

## Project layout

```
app.py          entry point
services/       HTTP request and cURL parsing logic (no Qt)
view/           Qt widgets: main window, request editor, response output, background request worker
tests/          pytest suite
```
