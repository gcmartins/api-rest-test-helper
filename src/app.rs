use std::sync::mpsc;

use crate::services::request_helper::{self, ParsedResponse};
use crate::ui::{curl_dialog, request_editor, response_output};
use crate::ui::curl_dialog::CurlDialogState;
use crate::ui::request_editor::RequestEditorState;
use crate::ui::response_output::ResponseOutputState;

pub struct AppState {
    editor: RequestEditorState,
    response: ResponseOutputState,
    curl_dialog: Option<CurlDialogState>,
    request_in_flight: bool,
    response_rx: Option<mpsc::Receiver<Result<ParsedResponse, String>>>,
}

impl Default for AppState {
    fn default() -> Self {
        Self {
            editor: RequestEditorState {
                method: "GET".to_string(),
                ..Default::default()
            },
            response: ResponseOutputState::default(),
            curl_dialog: None,
            request_in_flight: false,
            response_rx: None,
        }
    }
}

impl AppState {
    fn poll_response(&mut self, ctx: &egui::Context) {
        if let Some(rx) = &self.response_rx {
            if let Ok(result) = rx.try_recv() {
                let req = self.editor.current_request();
                response_output::update_from_result(
                    &mut self.response,
                    &req.method,
                    &req.url,
                    req.payload.as_ref(),
                    result,
                );
                self.request_in_flight = false;
                self.response_rx = None;
                ctx.request_repaint();
            }
        }
    }

    fn start_request(&mut self) {
        let req = self.editor.current_request();
        let (tx, rx) = mpsc::channel();
        self.response_rx = Some(rx);
        self.request_in_flight = true;

        std::thread::spawn(move || {
            let result = request_helper::run_http_request(&req).map_err(|e| e.to_string());
            let _ = tx.send(result);
        });
    }
}

impl eframe::App for AppState {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        self.poll_response(ctx);

        // Render CURL dialog if open
        if self.curl_dialog.is_some() {
            curl_dialog::show(ctx, &mut self.curl_dialog, &mut self.editor);
        }

        egui::SidePanel::left("request_panel")
            .exact_width(450.0)
            .show(ctx, |ui| {
                egui::ScrollArea::vertical().show(ui, |ui| {
                    let mut open_curl_dialog = false;
                    request_editor::show(ui, &mut self.editor, &mut open_curl_dialog);
                    if open_curl_dialog && self.curl_dialog.is_none() {
                        self.curl_dialog = Some(CurlDialogState::default());
                    }
                });
            });

        egui::CentralPanel::default().show(ctx, |ui| {
            egui::ScrollArea::vertical().show(ui, |ui| {
                let action = response_output::show(ui, &mut self.response, self.request_in_flight);
                if matches!(action, response_output::Action::RunRequest) {
                    self.start_request();
                }
            });
        });
    }
}
