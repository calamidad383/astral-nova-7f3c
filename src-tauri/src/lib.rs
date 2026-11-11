#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn correr() {
    tauri::Builder::default()
        .run(tauri::generate_context!())
        .expect("error al arrancar el panel NEXO");
}
