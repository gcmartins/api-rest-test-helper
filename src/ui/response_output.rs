#[derive(Default)]
pub struct ResponseOutputState {
    pub status_code: String,
    pub output_log: String,
}

pub enum Action {
    None,
    RunRequest,
}

pub fn show(
    ui: &mut egui::Ui,
    state: &mut ResponseOutputState,
    request_in_flight: bool,
) -> Action {
    let mut action = Action::None;

    ui.heading("Response");
    ui.separator();

    egui::Grid::new("response_fields")
        .num_columns(2)
        .spacing([8.0, 6.0])
        .show(ui, |ui| {
            ui.label("Status Code:");
            ui.add(
                egui::TextEdit::singleline(&mut state.status_code)
                    .interactive(false)
                    .desired_width(120.0),
            );
            ui.end_row();
        });

    ui.add_space(4.0);

    let available = ui.available_height() - 40.0;
    egui::ScrollArea::vertical()
        .max_height(available)
        .show(ui, |ui| {
            ui.add(
                egui::TextEdit::multiline(&mut state.output_log)
                    .desired_width(f32::INFINITY)
                    .interactive(false)
                    .code_editor(),
            );
        });

    ui.add_space(4.0);
    ui.horizontal(|ui| {
        let run_label = if request_in_flight { "Running…" } else { "Run Request" };
        if ui
            .add_enabled(!request_in_flight, egui::Button::new(run_label))
            .clicked()
        {
            action = Action::RunRequest;
        }
        if ui.button("Clear").clicked() {
            state.status_code.clear();
            state.output_log.clear();
        }
        if ui.button("Save").clicked() {
            save_response(&state.output_log);
        }
    });

    action
}

pub fn update_from_result(
    state: &mut ResponseOutputState,
    method: &str,
    url: &str,
    payload: Option<&serde_json::Value>,
    result: Result<crate::services::request_helper::ParsedResponse, String>,
) {
    match result {
        Ok(resp) => {
            state.status_code = resp.status_code.to_string();
            let mut entry = format!("---\n{} {}\n", method, url);
            if let Some(p) = payload {
                entry.push_str("PAYLOAD:\n");
                entry.push_str(&serde_json::to_string_pretty(p).unwrap_or_default());
                entry.push('\n');
            }
            entry.push_str(&format!("STATUS CODE: {}\nRESPONSE:\n{}\n", resp.status_code, resp.body));
            state.output_log.push_str(&entry);
        }
        Err(e) => {
            state.status_code = "ERROR".to_string();
            state.output_log.push_str(&format!("---\nERROR: {}\n", e));
        }
    }
}

fn save_response(output: &str) {
    let Some(path) = rfd::FileDialog::new()
        .add_filter("Text Files", &["txt"])
        .add_filter("All Files", &["*"])
        .save_file()
    else {
        return;
    };
    let _ = std::fs::write(path, output);
}
