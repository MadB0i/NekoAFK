//! Bounded, local lifecycle evidence. Never record commands, URLs, payloads or error text.
use serde_json::{json, Value};
use std::{
    collections::HashSet,
    fs::{self, OpenOptions},
    io::Write,
    path::PathBuf,
    sync::{Arc, Mutex},
    time::{Instant, SystemTime, UNIX_EPOCH},
};

const LIMIT: u64 = 256 * 1024;
pub struct Diagnostics {
    dir: PathBuf,
    run: String,
    started: Instant,
    lock: Mutex<()>,
    js_seen: Mutex<HashSet<(String, String)>>,
}
impl Diagnostics {
    pub fn start(dir: PathBuf) -> Arc<Self> {
        let d = Arc::new(Self {
            dir,
            run: uuid::Uuid::new_v4().to_string(),
            started: Instant::now(),
            lock: Mutex::new(()),
            js_seen: Mutex::new(HashSet::new()),
        });
        let _ = fs::create_dir_all(&d.dir);
        // A missing exit record is NOT proof of a crash (kill, power loss and I/O failure also qualify).
        let previous_incomplete = d.dir.join("active-run").exists();
        let _ = fs::write(d.dir.join("active-run"), &d.run);
        d.record("host_started", json!({"previous_run_incomplete":previous_incomplete,"version":env!("CARGO_PKG_VERSION")}));
        d
    }
    pub fn record(&self, event: &str, fields: Value) {
        let Ok(_guard) = self.lock.lock() else { return };
        let path = self.dir.join("lifecycle.jsonl");
        let row = json!({"unix_ms":SystemTime::now().duration_since(UNIX_EPOCH).unwrap_or_default().as_millis(),"elapsed_ms":self.started.elapsed().as_millis(),"pid":std::process::id(),"run":self.run,"event":event,"fields":fields});
        let Ok(mut bytes) = serde_json::to_vec(&row) else {
            return;
        };
        bytes.push(b'\n');
        if fs::metadata(&path).is_ok_and(|m| m.len() + bytes.len() as u64 > LIMIT) {
            let old = self.dir.join("lifecycle.previous.jsonl");
            let _ = fs::remove_file(&old);
            if fs::rename(&path, old).is_err() {
                return;
            }
        }
        if let Ok(mut f) = OpenOptions::new().create(true).append(true).open(path) {
            let _ = f.write_all(&bytes);
        }
    }
    pub fn js_fault(&self, surface: &str, kind: &str) {
        if !["neko", "telemetry", "settings", "hud"].contains(&surface)
            || !["error", "unhandledrejection"].contains(&kind)
        {
            return;
        }
        let Ok(mut seen) = self.js_seen.lock() else {
            return;
        };
        if seen.insert((surface.into(), kind.into())) {
            self.record(
                "javascript_fault",
                json!({"surface":surface,"kind":kind,"first_per_surface_and_kind":true}),
            );
        }
    }
    pub fn exited(&self) {
        self.record("host_exit", json!({}));
        let _ = fs::remove_file(self.dir.join("active-run"));
    }
}

#[cfg(windows)]
pub fn attach(window: &tauri::WebviewWindow, diagnostics: Arc<Diagnostics>) -> tauri::Result<()> {
    use webview2_com::{
        BrowserProcessExitedEventHandler, Microsoft::Web::WebView2::Win32::*,
        ProcessFailedEventHandler,
    };
    use windows::core::Interface;
    let surface = window.label().to_string();
    window.with_webview(move |platform| {
        let result = (|| -> windows::core::Result<()> { unsafe {
            let view = platform.controller().CoreWebView2()?;
            let mut pid = 0;
            view.BrowserProcessId(&mut pid)?;
            let d = diagnostics.clone();
            let label = surface.clone();
            let handler = ProcessFailedEventHandler::create(Box::new(move |_, args| {
                if let Some(args) = args {
                    let mut kind = COREWEBVIEW2_PROCESS_FAILED_KIND(-1);
                    let kind = args.ProcessFailedKind(&mut kind).ok().map(|_|kind.0);
                    let mut reason = COREWEBVIEW2_PROCESS_FAILED_REASON(-1);
                    let mut exit = 0;
                    let more = args.cast::<ICoreWebView2ProcessFailedEventArgs2>().ok();
                    let reason = more.as_ref().and_then(|a|a.Reason(&mut reason).ok().map(|_|reason.0));
                    let exit = more.as_ref().and_then(|a|a.ExitCode(&mut exit).ok().map(|_|exit));
                    d.record("webview_process_failed", json!({"surface":label,"browser_pid":pid,"kind":kind,"reason":reason,"exit_code":exit}));
                }
                Ok(())
            }));
            let mut token = 0;
            view.add_ProcessFailed(&handler, &mut token)?;
            // WebView2 retains the handlers until its view/environment is released.
            // They capture diagnostics only, not COM objects or the window itself.
            let environment = platform.environment().cast::<ICoreWebView2Environment5>()?;
            let d = diagnostics.clone();
            let label = surface.clone();
            let handler = BrowserProcessExitedEventHandler::create(Box::new(move |_, args| {
                if let Some(args) = args {
                    let mut kind = COREWEBVIEW2_BROWSER_PROCESS_EXIT_KIND(-1);
                    let mut pid = 0;
                    let kind = args.BrowserProcessExitKind(&mut kind).ok().map(|_|kind.0);
                    let pid = args.BrowserProcessId(&mut pid).ok().map(|_|pid);
                    d.record("webview_browser_exited", json!({"surface":label,"browser_pid":pid,"kind":kind}));
                }
                Ok(())
            }));
            environment.add_BrowserProcessExited(&handler, &mut token)?;
            diagnostics.record("webview_diagnostics_attached", json!({"surface":surface,"browser_pid":pid}));
            Ok(())
        }})();
        if let Err(e) = result { diagnostics.record("webview_diagnostics_unavailable", json!({"surface":surface,"hresult":e.code().0})); }
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn incomplete_is_distinct_from_clean_exit() {
        let temp = tempfile::tempdir().unwrap();
        let a = Diagnostics::start(temp.path().into());
        drop(a); // Simulate a lost host: no claim about its cause.
        let b = Diagnostics::start(temp.path().into());
        assert!(fs::read_to_string(temp.path().join("lifecycle.jsonl"))
            .unwrap()
            .contains("\"previous_run_incomplete\":true"));
        b.exited();
        assert!(!temp.path().join("active-run").exists());
    }
    #[test]
    fn untrusted_js_fields_are_rejected_and_fault_storm_is_bounded() {
        let temp = tempfile::tempdir().unwrap();
        let d = Diagnostics::start(temp.path().into());
        d.js_fault("secret workspace", "secret command");
        for _ in 0..1000 {
            d.js_fault("neko", "error");
        }
        let text = fs::read_to_string(temp.path().join("lifecycle.jsonl")).unwrap();
        assert!(!text.contains("secret"));
        assert_eq!(text.matches("javascript_fault").count(), 1);
    }
    #[test]
    fn log_retention_is_bounded_and_unwritable_log_is_nonfatal() {
        let temp = tempfile::tempdir().unwrap();
        let d = Diagnostics::start(temp.path().into());
        for _ in 0..3000 {
            d.record("fixture", json!({"code":42}));
        }
        for name in ["lifecycle.jsonl", "lifecycle.previous.jsonl"] {
            assert!(fs::metadata(temp.path().join(name)).unwrap().len() <= LIMIT);
        }
        let file = temp.path().join("not-a-directory");
        fs::write(&file, "").unwrap();
        Diagnostics::start(file).record("fixture", json!({}));
    }
}
