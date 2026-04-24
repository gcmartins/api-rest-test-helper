use std::collections::HashMap;
use std::sync::LazyLock;

use anyhow::anyhow;
use regex::Regex;

static METHOD_RE: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"-X\s+(\w+)").unwrap());
static URL_RE: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"curl\s+'([^']+)'").unwrap());
static HEADER_RE: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"-H\s+'([^:]+):\s*([^']+)'").unwrap());
static COOKIE_RE: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"-b\s+'([^']+)'").unwrap());
static DATA_RE: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"--data(?:-raw|-binary)?\s+'([^']+)'").unwrap());

#[derive(Debug, Default, Clone, serde::Serialize, serde::Deserialize)]
pub struct RequestData {
    pub method: String,
    pub url: String,
    pub headers: HashMap<String, String>,
    pub cookies: HashMap<String, String>,
    pub payload: Option<serde_json::Value>,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct SavedPayload {
    pub url: String,
    pub method: String,
    pub payload: Option<serde_json::Value>,
}

#[derive(Debug, Clone)]
pub struct ParsedResponse {
    pub status_code: u16,
    pub body: String,
}

fn normalize(input: &str) -> String {
    input
        .lines()
        .map(str::trim)
        .collect::<Vec<_>>()
        .join(" ")
}

fn extract_method(input: &str) -> String {
    if let Some(cap) = METHOD_RE.captures(input) {
        return cap[1].to_uppercase();
    }
    if DATA_RE.is_match(input) {
        "POST".to_string()
    } else {
        "GET".to_string()
    }
}

fn extract_url(input: &str) -> String {
    URL_RE
        .captures(input)
        .map(|c| c[1].to_string())
        .unwrap_or_default()
}

fn extract_headers(input: &str) -> HashMap<String, String> {
    HEADER_RE
        .captures_iter(input)
        .map(|c| (c[1].trim().to_string(), c[2].trim().to_string()))
        .collect()
}

fn extract_cookies(input: &str) -> HashMap<String, String> {
    COOKIE_RE
        .captures(input)
        .map(|c| {
            c[1].split(';')
                .filter_map(|pair| {
                    let mut parts = pair.trim().splitn(2, '=');
                    let k = parts.next()?.trim().to_string();
                    let v = parts.next().unwrap_or("").trim().to_string();
                    Some((k, v))
                })
                .collect()
        })
        .unwrap_or_default()
}

fn extract_payload(input: &str) -> Option<serde_json::Value> {
    DATA_RE
        .captures(input)
        .and_then(|c| serde_json::from_str(&c[1]).ok())
}

pub fn parse_curl_command(input: &str) -> RequestData {
    let s = normalize(input);
    RequestData {
        method: extract_method(&s),
        url: extract_url(&s),
        headers: extract_headers(&s),
        cookies: extract_cookies(&s),
        payload: extract_payload(&s),
    }
}

pub fn parse_headers_only(input: &str) -> RequestData {
    let s = normalize(input);
    RequestData {
        headers: extract_headers(&s),
        cookies: extract_cookies(&s),
        ..Default::default()
    }
}

pub fn run_http_request(req: &RequestData) -> anyhow::Result<ParsedResponse> {
    let client = reqwest::blocking::Client::new();

    let cookie_str: String = req
        .cookies
        .iter()
        .map(|(k, v)| format!("{}={}", k, v))
        .collect::<Vec<_>>()
        .join("; ");

    let mut builder = match req.method.as_str() {
        "GET" => client.get(&req.url),
        "POST" => client.post(&req.url),
        "PUT" => client.put(&req.url),
        "DELETE" => client.delete(&req.url),
        m => return Err(anyhow!("Unsupported HTTP method: {}", m)),
    };

    for (k, v) in &req.headers {
        builder = builder.header(k, v);
    }
    if !cookie_str.is_empty() {
        builder = builder.header("Cookie", &cookie_str);
    }

    if matches!(req.method.as_str(), "POST" | "PUT") {
        if let Some(payload) = &req.payload {
            builder = builder.json(payload);
        }
    }

    let resp = builder.send()?;
    let status_code = resp.status().as_u16();
    let bytes = resp.bytes()?;

    let body = match serde_json::from_slice::<serde_json::Value>(&bytes) {
        Ok(v) => serde_json::to_string_pretty(&v)?,
        Err(_) => String::from_utf8_lossy(&bytes).to_string(),
    };

    Ok(ParsedResponse { status_code, body })
}

#[cfg(test)]
mod tests {
    use super::*;

    const FULL_CURL: &str = r#"curl 'https://api.example.com/users' \
  -X POST \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer tok123' \
  -b 'session=abc; user=bob' \
  --data '{"name":"Alice","age":30}'"#;

    #[test]
    fn test_parse_full_curl() {
        let data = parse_curl_command(FULL_CURL);
        assert_eq!(data.method, "POST");
        assert_eq!(data.url, "https://api.example.com/users");
        assert_eq!(data.headers.get("Content-Type").map(|s| s.as_str()), Some("application/json"));
        assert_eq!(data.headers.get("Authorization").map(|s| s.as_str()), Some("Bearer tok123"));
        assert_eq!(data.cookies.get("session").map(|s| s.as_str()), Some("abc"));
        assert_eq!(data.cookies.get("user").map(|s| s.as_str()), Some("bob"));
        assert!(data.payload.is_some());
    }

    #[test]
    fn test_extract_method_explicit() {
        let data = parse_curl_command("curl 'https://example.com' -X DELETE");
        assert_eq!(data.method, "DELETE");
    }

    #[test]
    fn test_extract_method_defaults_to_get() {
        let data = parse_curl_command("curl 'https://example.com'");
        assert_eq!(data.method, "GET");
    }

    #[test]
    fn test_extract_method_defaults_to_post_with_data() {
        let data = parse_curl_command("curl 'https://example.com' --data '{}'");
        assert_eq!(data.method, "POST");
    }

    #[test]
    fn test_extract_cookies() {
        let data = parse_curl_command("curl 'https://example.com' -b 'a=1; b=2; c=3'");
        assert_eq!(data.cookies.get("a").map(|s| s.as_str()), Some("1"));
        assert_eq!(data.cookies.get("b").map(|s| s.as_str()), Some("2"));
        assert_eq!(data.cookies.get("c").map(|s| s.as_str()), Some("3"));
    }

    #[test]
    fn test_extract_headers_multiple() {
        let data = parse_curl_command(
            "curl 'https://example.com' -H 'Accept: application/json' -H 'X-Foo: bar'",
        );
        assert_eq!(data.headers.get("Accept").map(|s| s.as_str()), Some("application/json"));
        assert_eq!(data.headers.get("X-Foo").map(|s| s.as_str()), Some("bar"));
    }

    #[test]
    fn test_extract_payload_valid_json() {
        let data = parse_curl_command("curl 'https://example.com' --data '{\"key\":\"val\"}'");
        let p = data.payload.unwrap();
        assert_eq!(p["key"], "val");
    }

    #[test]
    fn test_extract_payload_invalid_json_returns_none() {
        let data = parse_curl_command("curl 'https://example.com' --data 'not-json'");
        assert!(data.payload.is_none());
    }

    #[test]
    fn test_parse_headers_only() {
        let data = parse_headers_only(FULL_CURL);
        assert!(data.method.is_empty());
        assert!(data.url.is_empty());
        assert!(data.headers.contains_key("Content-Type"));
        assert!(data.cookies.contains_key("session"));
    }

    #[test]
    fn test_data_raw_and_data_binary() {
        let raw = parse_curl_command("curl 'https://example.com' --data-raw '{\"x\":1}'");
        assert!(raw.payload.is_some());
        let binary = parse_curl_command("curl 'https://example.com' --data-binary '{\"x\":1}'");
        assert!(binary.payload.is_some());
    }
}
