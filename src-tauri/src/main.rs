#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]
mod diagnostics;
mod hud_geometry;
mod model;
mod progress;
mod storage;
mod verification;
use model::*;
use serde::Serialize;
use std::{
    fs,
    path::PathBuf,
    sync::{
        atomic::{AtomicBool, Ordering},
        Arc, Mutex,
    },
    thread,
    time::Duration,
};
use tauri::{
    menu::{Menu, MenuItem},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
    Emitter, Listener, Manager, PhysicalPosition, PhysicalSize, WindowEvent,
};

struct Running {
    token: String,
    cancel: Arc<AtomicBool>,
}
struct Inner {
    config: Config,
    engine: Engine,
    notice: Option<String>,
    running: Option<Running>,
    dirty: bool,
    fullscreen: bool,
}
struct Host {
    inner: Mutex<Inner>,
    published: Mutex<Option<String>>,
    dir: PathBuf,
}
#[derive(Clone, Serialize)]
struct Snapshot {
    settings: Settings,
    engine: Engine,
    connected: bool,
    selected_connected: bool,
    selected_state: String,
    data_dir: String,
    notice: Option<String>,
    verification_running: bool,
    bridge_installed: bool,
    desktop_paused: bool,
    progress: progress::Progress,
}

fn snapshot(host: &Host) -> Snapshot {
    let h = host.inner.lock().unwrap();
    let at = now();
    let connected = h.engine.connected(at);
    let selected = h
        .engine
        .selected
        .as_ref()
        .and_then(|key| h.engine.sessions.get(key));
    let selected_connected = selected.map_or(connected, |s| {
        h.engine
            .sources
            .get(&s.source)
            .is_some_and(|t| at.saturating_sub(*t) < 45_000)
    });
    let state = selected
        .map_or(if connected { "idle" } else { "disconnected" }, |s| {
            s.display_state(selected_connected, at)
        })
        .to_string();
    Snapshot {
        progress: progress::derive(selected, selected_connected, &state),
        settings: h.config.settings.clone(),
        engine: h.engine.clone(),
        connected,
        selected_connected,
        selected_state: state,
        data_dir: host.dir.to_string_lossy().into(),
        notice: h.notice.clone(),
        verification_running: h.running.is_some(),
        bridge_installed: PathBuf::from(&h.config.settings.workspace)
            .join(".opencode/plugins/nekoafk.js")
            .is_file(),
        desktop_paused: h.fullscreen,
    }
}
fn publish(app: &tauri::AppHandle) {
    let host = app.state::<Host>();
    // Serialize publications and suppress identical UI snapshots. Polling still
    // evaluates time-based expiry; real evidence/settings changes still emit.
    let mut published = host.published.lock().unwrap();
    let value = snapshot(&host);
    if let Ok(signature) = serde_json::to_string(&value) {
        if published.as_ref() == Some(&signature) {
            return;
        }
        if app.emit("neko:snapshot", value).is_ok() {
            *published = Some(signature);
        }
    }
}
#[tauri::command]
fn get_snapshot(host: tauri::State<Host>) -> Snapshot {
    snapshot(&host)
}
#[tauri::command]
fn desktop_diagnostics(app: tauri::AppHandle) -> serde_json::Value {
    let windows: Vec<_> = ["neko", "telemetry", "settings", "hud"].iter().filter_map(|label| app.get_webview_window(label)).map(|w| {
        #[cfg(windows)] let native_handle = w.hwnd().ok().map(|h| h.0 as usize);
        #[cfg(not(windows))] let native_handle: Option<usize> = None;
        serde_json::json!({
        "label": w.label(), "visible": w.is_visible().ok(), "decorated": w.is_decorated().ok(),
        "always_on_top": w.is_always_on_top().ok(), "resizable": w.is_resizable().ok(),
        "position": w.outer_position().ok(), "size": w.outer_size().ok(), "inner_size": w.inner_size().ok(), "scale_factor": w.scale_factor().ok(), "native_handle": native_handle
    })}).collect();
    let monitors = app.available_monitors().unwrap_or_default().iter().map(|m| serde_json::json!({"name":m.name(),"position":m.position(),"size":m.size(),"scale_factor":m.scale_factor(),"work_area":m.work_area()})).collect::<Vec<_>>();
    serde_json::json!({"windows":windows,"monitors":monitors,"tray_available":app.tray_by_id("neko-tray").is_some()})
}

fn persist(host: &Host) -> Result<(), String> {
    let mut h = host.inner.lock().unwrap();
    storage::save(&host.dir, &h.config)?;
    h.dirty = false;
    Ok(())
}
fn follow(app: &tauri::AppHandle) {
    follow_dock(app);
    follow_hud(app);
}
fn follow_hud(app: &tauri::AppHandle) {
    let (Some(cat), Some(hud)) = (
        app.get_webview_window("neko"),
        app.get_webview_window("hud"),
    ) else {
        return;
    };
    let host = app.state::<Host>();
    let (s, fullscreen) = {
        let h = host.inner.lock().unwrap();
        (h.config.settings.clone(), h.fullscreen)
    };
    let settings_active = app
        .get_webview_window("settings")
        .is_some_and(|w| w.is_visible().unwrap_or(false));
    let visible = s.hud_enabled
        && s.neko_visible
        && !fullscreen
        && !settings_active
        && !cat.is_minimized().unwrap_or(false);
    if let (Ok(p), Ok(size), Ok(Some(m))) = (
        cat.outer_position(),
        cat.outer_size(),
        cat.current_monitor(),
    ) {
        let factor = m.scale_factor();
        let height = if s.hud_collapsed { 72. } else { 136. };
        let target = PhysicalSize::new(
            (248. * factor).round() as u32,
            (height * factor).round() as u32,
        );
        if hud.inner_size().ok() != Some(target) {
            let _ = hud.set_size(target);
        }
        let area = m.work_area();
        let cat_rect = Placement {
            x: p.x,
            y: p.y,
            width: size.width,
            height: size.height,
        };
        let area_rect = Placement {
            x: area.position.x,
            y: area.position.y,
            width: area.size.width,
            height: area.size.height,
        };
        let dock = app
            .get_webview_window("telemetry")
            .filter(|w| w.is_visible().unwrap_or(false))
            .and_then(|w| Some((w.outer_position().ok()?, w.outer_size().ok()?)))
            .map(|(p, s)| Placement {
                x: p.x,
                y: p.y,
                width: s.width,
                height: s.height,
            });
        let (x, y) = hud_geometry::position(
            &cat_rect,
            target.width,
            target.height,
            &area_rect,
            dock.as_ref(),
            (12. * factor).round() as i32,
        );
        let position = PhysicalPosition::new(x, y);
        if hud.outer_position().ok() != Some(position) {
            let _ = hud.set_position(position);
        }
    }
    let _ = hud.set_ignore_cursor_events(s.click_through);
    let pinned = s.always_on_top && !fullscreen && !settings_active;
    if hud.is_always_on_top().ok() != Some(pinned) {
        let _ = hud.set_always_on_top(pinned);
    }
    if hud.is_visible().ok() != Some(visible) {
        let _ = if visible { hud.show() } else { hud.hide() };
    }
}
fn follow_dock(app: &tauri::AppHandle) {
    if !app
        .state::<Host>()
        .inner
        .lock()
        .unwrap()
        .config
        .settings
        .attached
    {
        return;
    }
    let Some(neko) = app.get_webview_window("neko") else {
        return;
    };
    let Some(dock) = app.get_webview_window("telemetry") else {
        return;
    };
    if let (Ok(p), Ok(n), Ok(d), Ok(Some(m))) = (
        neko.outer_position(),
        neko.outer_size(),
        dock.outer_size(),
        neko.current_monitor(),
    ) {
        let area = m.work_area();
        let gap = (12. * m.scale_factor()) as i32;
        let left = p.x - d.width as i32 - gap;
        let x = if left >= area.position.x {
            left
        } else {
            p.x + n.width as i32 + gap
        };
        let x = x.clamp(
            area.position.x,
            (area.position.x + area.size.width as i32 - d.width as i32).max(area.position.x),
        );
        let y = (p.y + n.height as i32 - d.height as i32).clamp(
            area.position.y,
            (area.position.y + area.size.height as i32 - d.height as i32).max(area.position.y),
        );
        if dock.outer_position().ok() != Some(PhysicalPosition::new(x, y)) {
            let _ = dock.set_position(PhysicalPosition::new(x, y));
        }
    }
}
fn recover(app: &tauri::AppHandle, label: &str) {
    let Some(w) = app.get_webview_window(label) else {
        return;
    };
    if let (Ok(p), Ok(size), Ok(monitors)) =
        (w.outer_position(), w.outer_size(), w.available_monitors())
    {
        let fits = monitors.iter().any(|m| {
            let a = m.work_area();
            p.x >= a.position.x
                && p.y >= a.position.y
                && p.x as i64 + size.width as i64 <= a.position.x as i64 + a.size.width as i64
                && p.y as i64 + size.height as i64 <= a.position.y as i64 + a.size.height as i64
        });
        if !fits {
            // Recover onto the nearest display, rather than teleporting to the
            // first enumerated monitor after a display topology change.
            if let Some(m) = monitors.iter().min_by_key(|m| {
                let a = m.work_area();
                let cx = p.x as i64 + size.width as i64 / 2;
                let cy = p.y as i64 + size.height as i64 / 2;
                let dx = cx - (a.position.x as i64 + a.size.width as i64 / 2);
                let dy = cy - (a.position.y as i64 + a.size.height as i64 / 2);
                dx * dx + dy * dy
            }) {
                let a = m.work_area();
                let width = size.width.min(a.size.width);
                let height = size.height.min(a.size.height);
                let inner = w.inner_size().unwrap_or(size);
                let _ = w.set_size(PhysicalSize::new(
                    width.saturating_sub(size.width.saturating_sub(inner.width)),
                    height.saturating_sub(size.height.saturating_sub(inner.height)),
                ));
                let _ = w.set_position(PhysicalPosition::new(
                    p.x.clamp(a.position.x, a.position.x + (a.size.width - width) as i32),
                    p.y.clamp(a.position.y, a.position.y + (a.size.height - height) as i32),
                ));
            }
        }
    }
}
fn refresh_pin(app: &tauri::AppHandle) {
    let Some(host) = app.try_state::<Host>() else {
        return;
    };
    let (s, fullscreen) = {
        let h = host.inner.lock().unwrap();
        (h.config.settings.clone(), h.fullscreen)
    };
    // WebView child focus can blur the native parent without closing Settings.
    let settings_active = app
        .get_webview_window("settings")
        .is_some_and(|w| w.is_visible().unwrap_or(false));
    let mut changed = false;
    for (label, pinned) in [
        ("neko", s.always_on_top),
        ("telemetry", s.dock_pinned),
        ("hud", s.always_on_top),
    ] {
        if let Some(w) = app.get_webview_window(label) {
            let desired = pinned && !settings_active && !fullscreen;
            if w.is_always_on_top().ok() != Some(desired) {
                let _ = w.set_always_on_top(desired);
                changed = true;
            }
        }
    }
    if settings_active && changed {
        if let Some(w) = app.get_webview_window("settings") {
            let _ = w.set_focus();
        }
    }
    follow_hud(app);
}
fn foreground_fullscreen(app: &tauri::AppHandle) -> bool {
    #[cfg(windows)]
    unsafe {
        use windows_sys::Win32::UI::WindowsAndMessaging::{
            GetAncestor, GetClassNameW, GetForegroundWindow, GetWindowRect, IsIconic, GA_ROOT,
        };
        let foreground = GetAncestor(GetForegroundWindow(), GA_ROOT);
        if foreground.is_null() || IsIconic(foreground) != 0 {
            return false;
        }
        if ["neko", "telemetry", "settings", "hud"]
            .iter()
            .filter_map(|l| app.get_webview_window(l))
            .any(|w| w.hwnd().is_ok_and(|h| std::ptr::eq(h.0, foreground)))
        {
            return false;
        }
        let mut class = [0u16; 128];
        let n = GetClassNameW(foreground, class.as_mut_ptr(), class.len() as i32);
        if [
            "Progman",
            "WorkerW",
            "Shell_TrayWnd",
            "Shell_SecondaryTrayWnd",
        ]
        .contains(&String::from_utf16_lossy(&class[..n.max(0) as usize]).as_str())
        {
            return false;
        }
        let mut rect = std::mem::zeroed();
        if GetWindowRect(foreground, &mut rect) == 0 {
            return false;
        }
        app.available_monitors()
            .unwrap_or_default()
            .iter()
            .any(|m| {
                let p = m.position();
                let s = m.size();
                (rect.left - p.x).abs() <= 2
                    && (rect.top - p.y).abs() <= 2
                    && (rect.right as i64 - p.x as i64 - s.width as i64).abs() <= 2
                    && (rect.bottom as i64 - p.y as i64 - s.height as i64).abs() <= 2
            })
    }
    #[cfg(not(windows))]
    {
        let _ = app;
        false
    }
}
fn raise_settings(app: &tauri::AppHandle) -> Result<(), String> {
    #[cfg(windows)]
    {
        let app_handle = app.clone();
        // Pin changes are queued on the window thread. Raise afterward: changing
        // HWND_TOPMOST to HWND_NOTOPMOST can otherwise cover an already focused Settings.
        app.run_on_main_thread(move || {
            use windows_sys::Win32::UI::WindowsAndMessaging::{
                SetWindowPos, HWND_TOP, SWP_NOACTIVATE, SWP_NOMOVE, SWP_NOSIZE,
            };
            if let Some(w) = app_handle.get_webview_window("settings") {
                if w.is_visible().unwrap_or(false) {
                    if let Ok(hwnd) = w.hwnd() {
                        // The handle belongs to this live window; no geometry or activation changes.
                        unsafe {
                            SetWindowPos(
                                hwnd.0 as _,
                                HWND_TOP,
                                0,
                                0,
                                0,
                                0,
                                SWP_NOACTIVATE | SWP_NOMOVE | SWP_NOSIZE,
                            );
                        }
                    }
                }
            }
        })
        .map_err(|e| e.to_string())?;
    }
    Ok(())
}
fn apply(app: &tauri::AppHandle, resize: bool) -> Result<(), String> {
    let s = app
        .state::<Host>()
        .inner
        .lock()
        .unwrap()
        .config
        .settings
        .clone();
    let fullscreen = app.state::<Host>().inner.lock().unwrap().fullscreen;
    let settings_active = app
        .get_webview_window("settings")
        .is_some_and(|w| w.is_visible().unwrap_or(false));
    for (label, visible) in [("neko", s.neko_visible), ("telemetry", s.dock_visible)] {
        let w = app
            .get_webview_window(label)
            .ok_or("Native window missing")?;
        let pinned = !settings_active
            && !fullscreen
            && if label == "neko" {
                s.always_on_top
            } else {
                s.dock_pinned
            };
        if w.is_always_on_top().ok() != Some(pinned) {
            w.set_always_on_top(pinned).map_err(|e| e.to_string())?;
        }
        if label == "neko" && resize {
            w.set_size(tauri::LogicalSize::new(240. * s.scale, 240. * s.scale))
                .map_err(|e| e.to_string())?;
        }
        if label == "neko" {
            w.set_ignore_cursor_events(s.click_through)
                .map_err(|e| e.to_string())?;
            w.set_background_color(Some(tauri::window::Color(
                if s.transparent { 0 } else { 242 },
                if s.transparent { 0 } else { 244 },
                if s.transparent { 0 } else { 245 },
                if s.transparent { 0 } else { 255 },
            )))
            .map_err(|e| e.to_string())?;
        }
        if label == "telemetry" {
            let factor = w.scale_factor().map_err(|e| e.to_string())?;
            let size = w.inner_size().map_err(|e| e.to_string())?;
            let height = size.height as f64 / factor;
            if s.dock_collapsed && height > 113. || !s.dock_collapsed && height < 300. {
                w.set_size(tauri::LogicalSize::new(
                    size.width as f64 / factor,
                    if s.dock_collapsed { 112. } else { 520. },
                ))
                .map_err(|e| e.to_string())?;
            }
        }
        if visible && w.is_minimized().unwrap_or(false) {
            w.unminimize().map_err(|e| e.to_string())?;
        }
        recover(app, label);
        if w.is_visible().unwrap_or(false) != visible {
            if visible { w.show() } else { w.hide() }.map_err(|e| e.to_string())?;
        }
    }
    follow(app);
    Ok(())
}
#[tauri::command]
fn save_settings(app: tauri::AppHandle, settings: Settings) -> Result<(), String> {
    settings.validate()?;
    let old = {
        let host = app.state::<Host>();
        let mut h = host.inner.lock().unwrap();
        if h.running.is_some() {
            return Err(
                "Wait for verification to finish, or cancel it before changing settings".into(),
            );
        }
        let old = h.config.settings.clone();
        h.config.settings = settings.clone();
        if let Err(e) = storage::save(&host.dir, &h.config) {
            h.config.settings = old;
            return Err(e);
        }
        old
    };
    let result = apply(&app, old.scale != settings.scale);
    publish(&app);
    result
}
#[tauri::command]
fn select_session(app: tauri::AppHandle, key: String) -> Result<(), String> {
    {
        let host = app.state::<Host>();
        let mut h = host.inner.lock().unwrap();
        if !h.engine.sessions.contains_key(&key) {
            return Err("Session no longer available".into());
        }
        h.engine.selected = Some(key);
    }
    publish(&app);
    Ok(())
}
#[tauri::command]
fn start_window_drag(
    window: tauri::WebviewWindow,
    app: tauri::AppHandle,
    client_x: f64,
    client_y: f64,
) -> Result<(), String> {
    if !client_x.is_finite() || !client_y.is_finite() {
        return Err("Invalid drag position".into());
    }
    if !matches!(window.label(), "neko" | "telemetry") {
        return Err("This window has a native title bar".into());
    }
    if window.label() == "telemetry" {
        let host = app.state::<Host>();
        let mut h = host.inner.lock().unwrap();
        h.config.settings.attached = false;
        h.dirty = true;
    }
    // No apply()/follow()/disk I/O between pointer-down and native capture.
    // The existing polling loop persists the dirty placement/preferences.
    #[cfg(windows)]
    let result = app
        .run_on_main_thread(move || unsafe {
            use windows_sys::Win32::UI::{
                Input::KeyboardAndMouse::{GetAsyncKeyState, ReleaseCapture, VK_LBUTTON},
                WindowsAndMessaging::*,
            };
            if let Ok(hwnd) = window.hwnd() {
                let mut point = std::mem::zeroed();
                if GetCursorPos(&mut point) == 0 {
                    return;
                }
                // Preserve motion between the DOM pointer-down and IPC arrival.
                // Short drags can otherwise finish before native capture begins.
                if let (Ok(client), Ok(origin), Ok(scale), Ok(size)) = (
                    window.inner_position(),
                    window.outer_position(),
                    window.scale_factor(),
                    window.inner_size(),
                ) {
                    if client_x < 0.
                        || client_y < 0.
                        || client_x * scale > size.width as f64
                        || client_y * scale > size.height as f64
                    {
                        return;
                    }
                    let down_x = client.x + (client_x * scale).round() as i32;
                    let down_y = client.y + (client_y * scale).round() as i32;
                    let delta_x = point.x - down_x;
                    let delta_y = point.y - down_y;
                    if delta_x != 0 || delta_y != 0 {
                        let _ = window.set_position(PhysicalPosition::new(
                            origin.x + delta_x,
                            origin.y + delta_y,
                        ));
                    }
                }
                if GetAsyncKeyState(VK_LBUTTON as i32) >= 0 {
                    return;
                }
                ReleaseCapture();
                // WM_NCLBUTTONDOWN takes signed screen coordinates packed by
                // value. Tao 0.37.1 posts the address of a temporary POINTS here.
                SendMessageW(
                    hwnd.0 as _,
                    WM_SYSCOMMAND,
                    (SC_MOVE | HTCAPTION) as usize,
                    pack_drag_position(point.x, point.y),
                );
                PostMessageW(hwnd.0 as _, WM_LBUTTONUP, 0, 0);
            }
        })
        .map_err(|e| e.to_string());
    #[cfg(not(windows))]
    let result = window.start_dragging().map_err(|e| e.to_string());
    publish(&app);
    result
}
#[cfg(windows)]
fn pack_drag_position(x: i32, y: i32) -> isize {
    ((x as u16 as u32) | ((y as u16 as u32) << 16)) as isize
}
#[tauri::command]
fn window_action(app: tauri::AppHandle, action: String) -> Result<(), String> {
    if action == "settings" {
        let w = app
            .get_webview_window("settings")
            .ok_or("Settings window missing")?;
        if w.is_minimized().unwrap_or(false) {
            w.unminimize().map_err(|e| e.to_string())?;
        }
        recover(&app, "settings");
        w.show().map_err(|e| e.to_string())?;
        refresh_pin(&app);
        w.set_focus().map_err(|e| e.to_string())?;
        raise_settings(&app)?;
        return Ok(());
    }
    {
        let host = app.state::<Host>();
        let mut h = host.inner.lock().unwrap();
        let s = &mut h.config.settings;
        match action.as_str() {
            "toggle-neko" => s.neko_visible = !s.neko_visible,
            "toggle-dock" => s.dock_visible = !s.dock_visible,
            "show-dock" => {
                s.dock_visible = true;
                s.dock_collapsed = false;
            }
            "toggle-hud" => s.hud_enabled = !s.hud_enabled,
            "hide-hud" => s.hud_enabled = false,
            "toggle-hud-collapse" => s.hud_collapsed = !s.hud_collapsed,
            "hide-neko" => s.neko_visible = false,
            "hide-dock" => s.dock_visible = false,
            "toggle-attach" => s.attached = !s.attached,
            "detach" => s.attached = false,
            "toggle-top" => s.always_on_top = !s.always_on_top,
            "toggle-click-through" => s.click_through = !s.click_through,
            "toggle-motion" => s.reduced_motion = !s.reduced_motion,
            "toggle-pin" => s.dock_pinned = !s.dock_pinned,
            "toggle-collapse" => s.dock_collapsed = !s.dock_collapsed,
            "scale-up" => s.scale = (s.scale + 0.1).min(2.),
            "scale-down" => s.scale = (s.scale - 0.1).max(0.5),
            "recover" => {
                s.neko_visible = true;
                s.dock_visible = true;
                s.click_through = false;
            }
            _ => return Err("Unknown window action".into()),
        }
        h.dirty = true;
    }
    apply(&app, matches!(action.as_str(), "scale-up" | "scale-down"))?;
    if action == "show-dock" {
        if let Some(w) = app.get_webview_window("telemetry") {
            let _ = w.set_focus();
        }
    }
    persist(&app.state::<Host>())?;
    publish(&app);
    Ok(())
}
#[tauri::command]
fn install_bridge(app: tauri::AppHandle) -> Result<String, String> {
    let workspace = app
        .state::<Host>()
        .inner
        .lock()
        .unwrap()
        .config
        .settings
        .workspace
        .clone();
    if workspace.is_empty() || !PathBuf::from(&workspace).is_dir() {
        return Err("Save an existing workspace folder first".into());
    }
    let dir = PathBuf::from(workspace).join(".opencode/plugins");
    fs::create_dir_all(&dir).map_err(|e| e.to_string())?;
    let file = dir.join("nekoafk.js");
    let contents = include_str!("../../integrations/opencode/nekoafk.js");
    if file.exists() && fs::read_to_string(&file).map_err(|e| e.to_string())? != contents {
        fs::copy(&file, dir.join(format!("nekoafk.js.backup-{}", now())))
            .map_err(|e| e.to_string())?;
    }
    fs::write(&file, contents).map_err(|e| e.to_string())?;
    publish(&app);
    Ok(file.to_string_lossy().into())
}
#[tauri::command]
fn open_data_folder(host: tauri::State<Host>) -> Result<(), String> {
    let mut command = std::process::Command::new("explorer.exe");
    verification::hidden(&mut command);
    command
        .arg(&host.dir)
        .spawn()
        .map_err(|_| "Could not open the local data folder".to_string())?;
    Ok(())
}
fn finish_running_check(
    h: &mut Inner,
    token: &str,
    key: &str,
    revision: u64,
    outcome: verification::Outcome,
) {
    let Some(running) = h.running.as_ref().filter(|r| r.token == token) else {
        return;
    };
    let outcome = outcome.with_cancellation(running.cancel.load(Ordering::SeqCst));
    h.running = None;
    if let Some(s) = h.engine.sessions.get_mut(key) {
        s.finish_check_outcome(
            outcome.passed,
            outcome.inconclusive,
            revision,
            outcome.detail,
            now(),
        );
    }
}
fn start_verification(app: tauri::AppHandle, key: String) -> Result<(), String> {
    let token = uuid::Uuid::new_v4().to_string();
    let cancel = Arc::new(AtomicBool::new(false));
    let (settings, revision, log_path) = {
        let host = app.state::<Host>();
        let mut h = host.inner.lock().unwrap();
        if h.running.is_some() {
            return Err("A local verification check is already running".into());
        }
        let settings = h.config.settings.clone();
        settings.validate()?;
        if settings.verify_program.trim().is_empty() {
            return Err("Configure a local verification executable in settings".into());
        }
        let session = h
            .engine
            .sessions
            .get_mut(&key)
            .ok_or("Select an observed session first")?;
        if !storage::same_workspace(&settings.workspace, &session.workspace) {
            return Err("Selected session does not match the configured workspace".into());
        }
        if !session.permissions.is_empty() {
            return Err("Answer the pending permission request in OpenCode first".into());
        }
        if !session.operations.is_empty() {
            return Err("Wait for the observed OpenCode tools to finish before verifying".into());
        }
        session.verification = "running".into();
        let revision = session.revision;
        h.running = Some(Running {
            token: token.clone(),
            cancel: cancel.clone(),
        });
        (settings, revision, host.dir.join("verification.log"))
    };
    publish(&app);
    thread::spawn(move || {
        let outcome = verification::run(&settings, &log_path, cancel);
        {
            let host = app.state::<Host>();
            let mut h = host.inner.lock().unwrap();
            finish_running_check(&mut h, &token, &key, revision, outcome);
        }
        publish(&app);
    });
    Ok(())
}
#[tauri::command]
fn run_verification(app: tauri::AppHandle) -> Result<(), String> {
    let key = app
        .state::<Host>()
        .inner
        .lock()
        .unwrap()
        .engine
        .selected
        .clone()
        .ok_or("No observed session selected")?;
    start_verification(app, key)
}
#[tauri::command]
fn cancel_verification(host: tauri::State<Host>) {
    if let Some(r) = &host.inner.lock().unwrap().running {
        r.cancel.store(true, Ordering::SeqCst);
    }
}
#[tauri::command]
fn get_verification_log(host: tauri::State<Host>) -> Result<String, String> {
    let log_path = host.dir.join("verification.log");
    if !log_path.exists() {
        return Ok("No verification log available yet. Run local verification first.".into());
    }
    match fs::read_to_string(&log_path) {
        Ok(content) => {
            if content.is_empty() {
                Ok("Verification command exited without writing to standard output.".into())
            } else {
                Ok(content)
            }
        }
        Err(e) => Err(format!("Could not read verification log: {}", e)),
    }
}
#[tauri::command]
fn quit_app(app: tauri::AppHandle, window: tauri::WebviewWindow) {
    request_quit(app, window.label());
}
fn request_quit(app: tauri::AppHandle, origin: &str) {
    app.state::<Arc<diagnostics::Diagnostics>>()
        .record("quit_requested", serde_json::json!({"origin":origin}));
    if let Some(r) = &app.state::<Host>().inner.lock().unwrap().running {
        r.cancel.store(true, Ordering::SeqCst);
    }
    let _ = persist(&app.state::<Host>());
    thread::spawn(move || {
        while app.state::<Host>().inner.lock().unwrap().running.is_some() {
            thread::sleep(Duration::from_millis(100));
        }
        app.exit(0);
    });
}

fn poll(app: tauri::AppHandle) {
    thread::spawn(move || loop {
        let app_clone = app.clone();
        let result = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
            poll_cycle(&app_clone);
        }));
        if let Err(e) = result {
            eprintln!("NekoAFK: Spool poller recovered from panic: {:?}", e);
            thread::sleep(Duration::from_millis(1000));
        }
    });
}
fn poll_cycle(app: &tauri::AppHandle) {
    loop {
        thread::sleep(Duration::from_millis(500));
        let host = app.state::<Host>();
        let fullscreen = foreground_fullscreen(app);
        let changed = {
            let mut h = host.inner.lock().unwrap();
            let changed = h.fullscreen != fullscreen;
            h.fullscreen = fullscreen;
            changed
        };
        if changed {
            refresh_pin(app);
        }
        let dir = host.dir.join("bridge/queue");
        let mut auto = vec![];
        if let Ok(files) = fs::read_dir(&dir) {
            let mut files: Vec<_> = files
                .flatten()
                .filter(|e| e.path().extension().is_some_and(|x| x == "json"))
                .collect();
            files.sort_by_key(|e| e.file_name());
            for file in files.into_iter().take(200) {
                if let Ok(meta) = file.metadata() {
                    if meta.len() <= 16384 {
                        if let Ok(bytes) = fs::read(file.path()) {
                            if let Ok(e) = serde_json::from_slice::<Evidence>(&bytes) {
                                let mut h = host.inner.lock().unwrap();
                                if let Some(key) = h.engine.ingest(e, now()) {
                                    if h.config.settings.auto_verify {
                                        auto.push(key);
                                    }
                                }
                            }
                        }
                    }
                }
                let _ = fs::remove_file(file.path());
            }
        }
        {
            let mut h = host.inner.lock().unwrap();
            if h.dirty {
                match storage::save(&host.dir, &h.config) {
                    Ok(()) => h.dirty = false,
                    Err(_) => {
                        h.notice =
                            Some("Settings could not be saved. Check the local data folder.".into())
                    }
                }
            }
        }
        for key in auto {
            let _ = start_verification(app.clone(), key);
        }
        publish(app);
    }
}
fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_single_instance::init(|app, _, _| {
            if let Some(d) = app.try_state::<Arc<diagnostics::Diagnostics>>() {
                d.record("second_instance", serde_json::json!({}));
            }
            let handle = app.clone();
            let _ = app.run_on_main_thread(move || {
                let _ = window_action(handle, "settings".into());
            });
        }))
        .invoke_handler(tauri::generate_handler![
            get_snapshot,
            desktop_diagnostics,
            save_settings,
            select_session,
            window_action,
            start_window_drag,
            install_bridge,
            run_verification,
            cancel_verification,
            get_verification_log,
            open_data_folder,
            quit_app
        ])
        .setup(|app| {
            let dir = std::env::var_os("NEKOAFK_DATA_DIR")
                .map(PathBuf::from)
                .unwrap_or(app.path().app_local_data_dir()?);
            fs::create_dir_all(dir.join("bridge/queue"))?;
            let diagnostics = diagnostics::Diagnostics::start(dir.join("diagnostics"));
            app.manage(diagnostics.clone());
            let panic_diagnostics = diagnostics.clone();
            let previous_hook = std::panic::take_hook();
            std::panic::set_hook(Box::new(move |info| {
                // No payload, file path or stack: these may contain private workspace data.
                panic_diagnostics.record(
                    "rust_panic",
                    serde_json::json!({
                        "line": info.location().map(|l| l.line()),
                        "file": info.location().map(|l| l.file()),
                        "msg": info.to_string(),
                    }),
                );
                previous_hook(info);
            }));
            let js_diagnostics = diagnostics.clone();
            app.listen("neko:runtime-fault", move |event| {
                if let Ok(value) = serde_json::from_str::<serde_json::Value>(event.payload()) {
                    js_diagnostics.js_fault(
                        value["surface"].as_str().unwrap_or(""),
                        value["kind"].as_str().unwrap_or(""),
                    );
                }
            });
            let (config, notice) = storage::load(&dir);
            app.manage(Host {
                published: Mutex::new(None),
                inner: Mutex::new(Inner {
                    config: config.clone(),
                    engine: Engine::default(),
                    notice,
                    running: None,
                    dirty: false,
                    fullscreen: false,
                }),
                dir,
            });
            // Configured webviews must not exist until command state is registered.
            // Tauri otherwise creates them before setup and their first IPC can race manage().
            let monitors = app.available_monitors()?;
            for mut window_config in app.config().app.windows.clone() {
                if let Some(p) = config
                    .placements
                    .get(&window_config.label)
                    .filter(|p| p.width > 0 && p.height > 0)
                {
                    let factor = monitors
                        .iter()
                        .find(|m| {
                            let pos = m.position();
                            let size = m.size();
                            p.x >= pos.x
                                && p.y >= pos.y
                                && (p.x as i64) < pos.x as i64 + size.width as i64
                                && (p.y as i64) < pos.y as i64 + size.height as i64
                        })
                        .or(monitors.first())
                        .map_or(1., |m| m.scale_factor());
                    // Initial client dimensions avoid hidden frameless window
                    // non-client metrics being added again during restoration.
                    window_config.width = (p.width.min(2000) as f64 / factor)
                        .max(window_config.min_width.unwrap_or(1.))
                        .min(window_config.max_width.unwrap_or(2000.));
                    window_config.height = (p.height.min(1600) as f64 / factor)
                        .max(window_config.min_height.unwrap_or(1.))
                        .min(window_config.max_height.unwrap_or(1600.));
                }
                let window =
                    tauri::WebviewWindowBuilder::from_config(app.handle(), &window_config)?
                        .build()?;
                #[cfg(windows)]
                if diagnostics::attach(&window, diagnostics.clone()).is_err() {
                    diagnostics.record(
                        "webview_dispatch_failed",
                        serde_json::json!({"surface":window.label()}),
                    );
                }
            }
            for (label, p) in &config.placements {
                if let Some(w) = app.get_webview_window(label) {
                    if p.width > 0 && p.height > 0 {
                        let _ = w.set_position(PhysicalPosition::new(p.x, p.y));
                    }
                }
            }
            if !config.placements.contains_key("settings") {
                if let Some(w) = app.get_webview_window("settings") {
                    let _ = w.center();
                }
            }
            if !config.placements.contains_key("neko") {
                if let Some(w) = app.get_webview_window("neko") {
                    if let (Ok(Some(m)), Ok(size)) = (w.primary_monitor(), w.outer_size()) {
                        let a = m.work_area();
                        let margin = (24. * m.scale_factor()) as i32;
                        let _ = w.set_position(PhysicalPosition::new(
                            a.position.x + a.size.width as i32 - size.width as i32 - margin,
                            a.position.y + a.size.height as i32 - size.height as i32 - margin,
                        ));
                    }
                }
            }
            let items: Vec<MenuItem<_>> = [
                ("recover", "Show companion and dock"),
                ("toggle-neko", "Show / hide companion"),
                ("toggle-dock", "Show / hide telemetry"),
                ("toggle-hud", "Show / hide progress HUD"),
                ("toggle-top", "Toggle always on top"),
                ("toggle-click-through", "Toggle companion click-through"),
                ("settings", "Settings"),
                ("quit", "Quit NekoAFK"),
            ]
            .iter()
            .map(|(id, label)| MenuItem::with_id(app, *id, *label, true, None::<&str>))
            .collect::<Result<_, _>>()?;
            let refs: Vec<&dyn tauri::menu::IsMenuItem<_>> = items
                .iter()
                .map(|i| i as &dyn tauri::menu::IsMenuItem<_>)
                .collect();
            let menu = Menu::with_items(app, &refs)?;
            TrayIconBuilder::with_id("neko-tray")
                .icon(
                    app.default_window_icon()
                        .ok_or("Application icon missing")?
                        .clone(),
                )
                .tooltip("NekoAFK")
                .menu(&menu)
                .show_menu_on_left_click(false)
                .on_menu_event(|app, event| {
                    if event.id.as_ref() == "quit" {
                        request_quit(app.clone(), "tray");
                    } else {
                        let _ = window_action(app.clone(), event.id.as_ref().into());
                    }
                })
                .on_tray_icon_event(|tray, event| {
                    if matches!(
                        event,
                        TrayIconEvent::Click {
                            button: MouseButton::Left,
                            button_state: MouseButtonState::Up,
                            ..
                        }
                    ) {
                        let _ = window_action(tray.app_handle().clone(), "recover".into());
                    }
                })
                .build(app)?;
            apply(app.handle(), !config.placements.contains_key("neko"))?;
            let _ = window_action(app.handle().clone(), "settings".into());
            poll(app.handle().clone());
            Ok(())
        })
        .on_window_event(|w, event| {
            let app = w.app_handle();
            let label = w.label();
            match event {
                WindowEvent::CloseRequested { api, .. } => {
                    if let Some(d) = app.try_state::<Arc<diagnostics::Diagnostics>>() {
                        d.record("window_close_to_hide", serde_json::json!({"surface":label}));
                    }
                    api.prevent_close();
                    if label == "settings" {
                        let _ = w.hide();
                        refresh_pin(app);
                    } else {
                        let _ = window_action(
                            app.clone(),
                            if label == "neko" {
                                "hide-neko"
                            } else if label == "hud" {
                                "hide-hud"
                            } else {
                                "hide-dock"
                            }
                            .into(),
                        );
                    }
                }
                WindowEvent::Moved(_) | WindowEvent::Resized(_) => {
                    // HUD geometry is derived, never independently persisted.
                    if label == "hud" {
                        return;
                    }
                    if label == "neko" {
                        follow_hud(app);
                    }
                    if !w.is_visible().unwrap_or(false) || w.is_minimized().unwrap_or(false) {
                        return;
                    }
                    if let (Ok(p), Ok(size)) = (w.outer_position(), w.inner_size()) {
                        if size.width == 0 || size.height == 0 {
                            return;
                        }
                        if let Some(host) = app.try_state::<Host>() {
                            let mut h = host.inner.lock().unwrap();
                            h.config.placements.insert(
                                label.into(),
                                Placement {
                                    x: p.x,
                                    y: p.y,
                                    width: size.width,
                                    height: size.height,
                                },
                            );
                            h.dirty = true;
                        }
                    }
                    if label == "neko" {
                        follow(app);
                    } else if label == "telemetry" {
                        follow_hud(app);
                    }
                }
                WindowEvent::ScaleFactorChanged { .. } => {
                    // Windows supplies the suggested rectangle during a DPI
                    // crossing. Recovery here used to snap an in-flight drag
                    // back onto the first monitor before that move completed.
                    if label == "neko" {
                        follow(app);
                    } else if label == "hud" {
                        follow_hud(app);
                    }
                }
                WindowEvent::Focused(focused) if label == "settings" => {
                    refresh_pin(app);
                    if *focused {
                        let _ = raise_settings(app);
                    }
                }
                _ => {}
            }
        })
        .build(tauri::generate_context!())
        .expect("NekoAFK could not start")
        .run(|app, event| {
            if let Some(d) = app.try_state::<Arc<diagnostics::Diagnostics>>() {
                match event {
                    tauri::RunEvent::ExitRequested { code, .. } => {
                        d.record("host_exit_requested", serde_json::json!({"code":code}))
                    }
                    tauri::RunEvent::Exit => d.exited(),
                    _ => {}
                }
            }
        });
}

#[cfg(test)]
mod startup_tests {
    #[test]
    fn accepted_cancellation_wins_publication_and_results_stay_bound_to_the_checked_session() {
        use super::*;
        for cancelled in [false, true] {
            let at = now();
            let mut engine = Engine::default();
            for id in ["checked", "selected"] {
                engine.ingest(serde_json::from_value(serde_json::json!({"version":1,"adapter":"opencode","id":id,"source":"source","timestamp":at,"workspace":"D:/workspace","session":id,"kind":"claimed"})).unwrap(),at);
            }
            let checked = engine
                .sessions
                .values()
                .find(|s| s.id == "checked")
                .unwrap()
                .key
                .clone();
            let selected = engine
                .sessions
                .values()
                .find(|s| s.id == "selected")
                .unwrap()
                .key
                .clone();
            let revision = engine.sessions[&checked].revision;
            engine.selected = Some(selected.clone());
            let mut h = Inner {
                config: Config::default(),
                engine,
                notice: None,
                running: Some(Running {
                    token: "current".into(),
                    cancel: Arc::new(AtomicBool::new(cancelled)),
                }),
                dirty: false,
                fullscreen: false,
            };
            let success = || verification::Outcome {
                passed: true,
                inconclusive: false,
                detail: "Computed success".into(),
            };
            finish_running_check(&mut h, "stale", &checked, revision, success());
            assert!(h.running.is_some());
            finish_running_check(&mut h, "current", &checked, revision, success());
            assert!(h.running.is_none());
            assert_eq!(
                h.engine.sessions[&checked].state,
                if cancelled {
                    "inconclusive"
                } else {
                    "verified"
                }
            );
            assert_eq!(h.engine.sessions[&selected].verification, "not_run");
            assert_eq!(h.engine.selected, Some(selected));
        }
    }
    #[test]
    fn pending_permission_does_not_hide_selected_source_disconnection() {
        use super::*;
        let at = now();
        let mut engine = Engine::default();
        for (source, session, kind) in [
            ("offline", "waiting", "permission"),
            ("online", "working", "active"),
        ] {
            let evidence = serde_json::from_value(serde_json::json!({
                "version":1,"adapter":"opencode","id":session,"source":source,
                "timestamp":at,"workspace":"D:/workspace","session":session,"kind":kind,"request":"question"
            })).unwrap();
            engine.ingest(evidence, at);
        }
        engine.sources.insert("offline".into(), at - 45_001);
        let host = Host {
            inner: Mutex::new(Inner {
                config: Config::default(),
                engine,
                notice: None,
                running: None,
                dirty: false,
                fullscreen: false,
            }),
            published: Mutex::new(None),
            dir: PathBuf::new(),
        };
        let snap = snapshot(&host);
        assert!(snap.connected);
        assert!(!snap.selected_connected);
        assert_eq!(snap.selected_state, "permission");
    }
    #[test]
    #[cfg(windows)]
    fn native_drag_coordinates_preserve_signed_monitor_positions() {
        for (x, y) in [(-1500, 700), (1000, -900), (0, 0), (30000, 30000)] {
            let packed = super::pack_drag_position(x, y) as u32;
            assert_eq!(packed as u16 as i16 as i32, x);
            assert_eq!((packed >> 16) as u16 as i16 as i32, y);
        }
    }
    #[test]
    fn configured_webviews_wait_for_managed_command_state() {
        let config: tauri::Config =
            serde_json::from_str(include_str!("../tauri.conf.json")).unwrap();
        assert_eq!(config.app.windows.len(), 4);
        for label in ["neko", "telemetry", "settings", "hud"] {
            assert!(config.app.windows.iter().any(|w| w.label == label));
        }
        assert!(
            config.app.windows.iter().all(|w| !w.create),
            "Automatic webviews load before setup registers Host; create them after manage()"
        );
    }
}
