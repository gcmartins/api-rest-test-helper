use std::collections::HashMap;

use crate::services::request_helper::{RequestData, SavedPayload};

#[derive(Default)]
pub struct RequestEditorState {
    pub method: String,
    pub url: String,
    pub headers_text: String,
    pub cookies_text: String,
    pub body_text: String,
}

impl RequestEditorState {
    pub fn apply_full(&mut self, data: RequestData) {
        self.method = data.method;
        self.url = data.url;
        self.headers_text = pretty_map(&data.headers);
        self.cookies_text = pretty_map(&data.cookies);
        self.body_text = data
            .payload
            .map(|v| serde_json::to_string_pretty(&v).unwrap_or_default())
            .unwrap_or_default();
    }

    pub fn apply_headers_only(&mut self, data: RequestData) {
        self.headers_text = pretty_map(&data.headers);
        self.cookies_text = pretty_map(&data.cookies);
    }

    pub fn current_request(&self) -> RequestData {
        RequestData {
            method: self.method.clone(),
            url: self.url.clone(),
            headers: parse_map(&self.headers_text),
            cookies: parse_map(&self.cookies_text),
            payload: parse_json_value(&self.body_text),
        }
    }
}

fn pretty_map(map: &HashMap<String, String>) -> String {
    if map.is_empty() {
        return String::new();
    }
    serde_json::to_string_pretty(map).unwrap_or_default()
}

pub fn parse_map(s: &str) -> HashMap<String, String> {
    let s = s.trim();
    if s.is_empty() {
        return HashMap::new();
    }
    serde_json::from_str(s).unwrap_or_default()
}

pub fn parse_json_value(s: &str) -> Option<serde_json::Value> {
    let s = s.trim();
    if s.is_empty() {
        None
    } else {
        serde_json::from_str(s).ok()
    }
}

pub fn show(ui: &mut egui::Ui, state: &mut RequestEditorState, show_curl_dialog: &mut bool) {
    ui.heading("Request");
    ui.separator();

    egui::Grid::new("request_fields")
        .num_columns(2)
        .spacing([8.0, 6.0])
        .show(ui, |ui| {
            ui.label("Method:");
            ui.text_edit_singleline(&mut state.method);
            ui.end_row();

            ui.label("URL:");
            ui.add(egui::TextEdit::singleline(&mut state.url).desired_width(f32::INFINITY));
            ui.end_row();
        });

    ui.add_space(4.0);
    ui.label("Cookies (JSON):");
    ui.add(
        egui::TextEdit::multiline(&mut state.cookies_text)
            .desired_rows(4)
            .desired_width(f32::INFINITY)
            .code_editor(),
    );

    ui.add_space(4.0);
    ui.label("Headers (JSON):");
    ui.add(
        egui::TextEdit::multiline(&mut state.headers_text)
            .desired_rows(6)
            .desired_width(f32::INFINITY)
            .code_editor(),
    );

    ui.add_space(4.0);
    ui.label("Body (JSON):");
    let body_resp = ui.add(
        egui::TextEdit::multiline(&mut state.body_text)
            .desired_rows(12)
            .desired_width(f32::INFINITY)
            .code_editor(),
    );

    // Replace tabs with 4 spaces (mirrors TextEditWithTabSpaces from Python)
    if body_resp.changed() && state.body_text.contains('\t') {
        state.body_text = state.body_text.replace('\t', "    ");
    }

    ui.add_space(8.0);
    ui.horizontal(|ui| {
        if ui.button("Import from CURL").clicked() {
            *show_curl_dialog = true;
        }
        if ui.button("Load Payload").clicked() {
            load_payload(state);
        }
        if ui.button("Save Payload").clicked() {
            save_payload(state);
        }
    });
}

fn load_payload(state: &mut RequestEditorState) {
    let Some(path) = rfd::FileDialog::new()
        .add_filter("JSON Files", &["json"])
        .add_filter("All Files", &["*"])
        .pick_file()
    else {
        return;
    };

    let Ok(text) = std::fs::read_to_string(&path) else {
        return;
    };

    let Ok(saved) = serde_json::from_str::<SavedPayload>(&text) else {
        return;
    };

    state.method = saved.method;
    state.url = saved.url;
    state.body_text = saved
        .payload
        .map(|v| serde_json::to_string_pretty(&v).unwrap_or_default())
        .unwrap_or_default();
}

fn save_payload(state: &RequestEditorState) {
    let Some(path) = rfd::FileDialog::new()
        .add_filter("JSON Files", &["json"])
        .save_file()
    else {
        return;
    };

    let data = SavedPayload {
        url: state.url.clone(),
        method: state.method.clone(),
        payload: parse_json_value(&state.body_text),
    };

    if let Ok(text) = serde_json::to_string_pretty(&data) {
        let _ = std::fs::write(path, text);
    }
}
