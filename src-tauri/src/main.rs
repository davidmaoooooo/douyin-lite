#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::Manager;

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            // 启动嵌入的 Flask API sidecar
            let sidecar = app
                .shell()
                .sidecar("douyin-api")
                .expect("未找到 douyin-api sidecar");

            let (_rx, _child) = sidecar
                .args(["--port", "3010"])
                .spawn()
                .expect("启动 API 服务失败");

            // 等 Flask 就绪
            std::thread::sleep(std::time::Duration::from_millis(1500));

            // macOS 窗口配置
            #[cfg(target_os = "macos")]
            if let Some(window) = app.get_webview_window("main") {
                window.set_min_size(Some(tauri::LogicalSize::new(400.0, 700.0))).ok();
            }

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("应用启动失败");
}
