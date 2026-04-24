# API REST Test Helper

A desktop GUI application for testing REST APIs. Supports building requests manually or importing from `curl` commands, executing HTTP requests, and viewing/saving responses.

Available in two implementations:
- **Python** (original) — PySide6 + requests
- **Rust** (port) — egui/eframe + reqwest

---

## Features

- Import requests from `curl` commands (full parse or headers-only)
- Edit HTTP method, URL, headers, cookies, and JSON body
- Execute GET, POST, PUT, DELETE requests
- View response status code and pretty-printed JSON (or raw text)
- Save and load request payloads as JSON files
- Export responses to `.txt` files

---

## Python

### Requirements

- Python 3.10+
- [PySide6](https://pypi.org/project/PySide6/) 6.9.0
- [requests](https://pypi.org/project/requests/) 2.32.3

### Setup

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run

```bash
python app.py
```

---

## Rust

### Requirements

- [Rust](https://rustup.rs/) 1.80+

### Build & Run

```bash
cargo run
```

### Tests

```bash
cargo test
```

All CURL parsing logic is covered by unit tests in `src/services/request_helper.rs`.

---

## Project Structure

```
├── app.py                        # Python entry point
├── requirements.txt              # Python dependencies
├── services/
│   └── request_helper.py         # HTTP client + curl parsing (Python)
├── view/
│   ├── main_window.py            # Main window (Python)
│   ├── request_editor.py         # Request form panel (Python)
│   ├── response_output.py        # Response display panel (Python)
│   └── curl_input_dialog.py      # Curl import dialog (Python)
├── Cargo.toml                    # Rust dependencies
└── src/
    ├── main.rs                   # Rust entry point
    ├── app.rs                    # App state + eframe::App loop
    ├── services/
    │   └── request_helper.rs     # HTTP client + curl parsing (Rust)
    └── ui/
        ├── request_editor.rs     # Request form panel (Rust)
        ├── response_output.rs    # Response display panel (Rust)
        └── curl_dialog.rs        # Curl import dialog (Rust)
```

---

## curl Import Format

The parser expects standard `curl` syntax with single-quoted arguments:

```bash
curl 'https://api.example.com/users' \
  -X POST \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <token>' \
  -b 'session=abc123' \
  --data '{"name": "Alice"}'
```

Supported flags: `-X`, `-H`, `-b`, `--data`, `--data-raw`, `--data-binary`.

---

## Payload File Format

Request payloads are saved and loaded as JSON:

```json
{
  "url": "https://api.example.com/users",
  "method": "POST",
  "payload": {
    "name": "Alice"
  }
}
```
