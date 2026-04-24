use crate::services::request_helper;
use crate::ui::request_editor::RequestEditorState;

pub struct CurlDialogState {
    pub curl_input: String,
}

impl Default for CurlDialogState {
    fn default() -> Self {
        Self {
            curl_input: String::new(),
        }
    }
}

pub fn show(
    ctx: &egui::Context,
    dialog: &mut Option<CurlDialogState>,
    editor: &mut RequestEditorState,
) {
    let mut close = false;

    if let Some(state) = dialog.as_mut() {
        egui::Window::new("Import from CURL")
            .collapsible(false)
            .resizable(true)
            .min_size([620.0, 400.0])
            .show(ctx, |ui| {
                ui.label("Paste your curl command below:");
                ui.add_space(4.0);
                ui.add(
                    egui::TextEdit::multiline(&mut state.curl_input)
                        .desired_rows(20)
                        .desired_width(f32::INFINITY)
                        .code_editor(),
                );
                ui.add_space(8.0);
                ui.horizontal(|ui| {
                    if ui.button("Parse full CURL command").clicked() {
                        let parsed = request_helper::parse_curl_command(&state.curl_input);
                        editor.apply_full(parsed);
                        close = true;
                    }
                    if ui.button("Parse headers only").clicked() {
                        let parsed = request_helper::parse_headers_only(&state.curl_input);
                        editor.apply_headers_only(parsed);
                        close = true;
                    }
                    if ui.button("Cancel").clicked() {
                        close = true;
                    }
                });
            });
    }

    if close {
        *dialog = None;
    }
}
