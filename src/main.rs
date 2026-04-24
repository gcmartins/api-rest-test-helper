mod app;
mod services;
mod ui;

fn main() -> eframe::Result<()> {
    let options = eframe::NativeOptions {
        viewport: egui::ViewportBuilder::default()
            .with_title("API test helper")
            .with_maximized(true)
            .with_min_inner_size([800.0, 600.0]),
        ..Default::default()
    };

    eframe::run_native(
        "API test helper",
        options,
        Box::new(|_cc| Ok(Box::new(app::AppState::default()))),
    )
}
