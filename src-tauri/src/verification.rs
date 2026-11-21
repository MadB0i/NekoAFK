use crate::{model::Settings, storage};
use std::{
    fs,
    io::{Read, Write},
    path::Path,
    process::{Command, Stdio},
    sync::{
        atomic::{AtomicBool, Ordering},
        Arc, Mutex,
    },
    thread,
    time::{Duration, Instant},
};

#[derive(Debug)]
pub struct Outcome {
    pub passed: bool,
    pub inconclusive: bool,
    pub detail: String,
}
impl Outcome {
    // Also applied under the host lock at publication: cancellation can arrive
    // after the command/fingerprint finished but before its result is accepted.
    pub fn with_cancellation(self, cancelled: bool) -> Self {
        if cancelled {
            Self {
                passed: false,
                inconclusive: true,
                detail: "Local verification cancelled".into(),
            }
        } else {
            self
        }
    }
}
pub fn hidden(command: &mut Command) {
    #[cfg(windows)]
    {
        use std::os::windows::process::CommandExt;
        command.creation_flags(0x08000000);
    }
}
fn drain(mut stream: impl Read, log: Arc<Mutex<fs::File>>) {
    let mut buffer = [0u8; 4096];
    let mut written = 0;
    while let Ok(n) = stream.read(&mut buffer) {
        if n == 0 {
            break;
        }
        let keep = n.min(65536usize.saturating_sub(written));
        if keep > 0 {
            if let Ok(mut f) = log.lock() {
                let _ = f.write_all(&buffer[..keep]);
            }
            written += keep;
        }
    }
}
// Keep verification descendants inside a native lifetime boundary. Detached
// children must not retain output pipes, consume CPU or outlive cancellation.
#[cfg(windows)]
struct CheckJob(windows_sys::Win32::Foundation::HANDLE);
#[cfg(windows)]
impl CheckJob {
    fn attach(child: &std::process::Child) -> Result<Self, ()> {
        use std::os::windows::io::AsRawHandle;
        use windows_sys::Win32::System::JobObjects::*;
        unsafe {
            let handle = CreateJobObjectW(std::ptr::null(), std::ptr::null());
            if handle.is_null() {
                return Err(());
            }
            let job = Self(handle);
            let mut info: JOBOBJECT_EXTENDED_LIMIT_INFORMATION = std::mem::zeroed();
            info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
            if SetInformationJobObject(
                handle,
                JobObjectExtendedLimitInformation,
                &info as *const _ as _,
                std::mem::size_of_val(&info) as u32,
            ) == 0
                || AssignProcessToJobObject(handle, child.as_raw_handle()) == 0
            {
                return Err(());
            }
            Ok(job)
        }
    }
    fn has_children(&self) -> bool {
        use windows_sys::Win32::System::JobObjects::*;
        unsafe {
            let mut info: JOBOBJECT_BASIC_ACCOUNTING_INFORMATION = std::mem::zeroed();
            QueryInformationJobObject(
                self.0,
                JobObjectBasicAccountingInformation,
                &mut info as *mut _ as _,
                std::mem::size_of_val(&info) as u32,
                std::ptr::null_mut(),
            ) == 0
                || info.ActiveProcesses > 0
        }
    }
}
#[cfg(windows)]
impl Drop for CheckJob {
    fn drop(&mut self) {
        unsafe {
            windows_sys::Win32::Foundation::CloseHandle(self.0);
        }
    }
}
pub fn run(settings: &Settings, log_path: &Path, cancel: Arc<AtomicBool>) -> Outcome {
    let fail = |s: &str| Outcome {
        passed: false,
        inconclusive: true,
        detail: s.into(),
    };
    if settings.verify_program.trim().is_empty() {
        return fail("No local verification executable configured");
    }
    if cancel.load(Ordering::SeqCst) {
        return fail("Local verification cancelled");
    }
    let before = match storage::fingerprint(Path::new(&settings.workspace)) {
        Ok(v) => v,
        Err(e) => return fail(&e),
    };
    let file = match fs::File::create(log_path) {
        Ok(f) => Arc::new(Mutex::new(f)),
        Err(_) => return fail("Cannot create local verification log"),
    };
    let mut command = Command::new(&settings.verify_program);
    hidden(&mut command);
    command
        .args(&settings.verify_args)
        .current_dir(&settings.workspace)
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());
    if cancel.load(Ordering::SeqCst) {
        return fail("Local verification cancelled");
    }
    let mut child = match command.spawn() {
        Ok(c) => c,
        Err(_) => {
            return fail("Cannot start verification executable. Check its path and arguments.")
        }
    };
    #[cfg(windows)]
    let job = match CheckJob::attach(&child) {
        Ok(j) => j,
        Err(()) => {
            let _ = child.kill();
            let _ = child.wait();
            return fail("Cannot isolate verification process lifetime");
        }
    };
    let out = child.stdout.take().unwrap();
    let err = child.stderr.take().unwrap();
    let log = file.clone();
    let reader1 = thread::spawn(move || drain(out, log));
    let reader2 = thread::spawn(move || drain(err, file));
    let start = Instant::now();
    let outcome = loop {
        let cancelled = cancel.load(Ordering::SeqCst);
        if cancelled || start.elapsed().as_secs() >= settings.verify_timeout {
            #[cfg(windows)]
            {
                let mut kill = Command::new("taskkill.exe");
                hidden(&mut kill);
                let _ = kill
                    .args(["/PID", &child.id().to_string(), "/T", "/F"])
                    .stdout(Stdio::null())
                    .stderr(Stdio::null())
                    .status();
            }
            let _ = child.kill();
            let _ = child.wait();
            break fail(if cancelled {
                "Local verification cancelled"
            } else {
                "Local verification timed out"
            });
        }
        match child.try_wait() {
            Ok(Some(exit)) => {
                #[cfg(windows)]
                if job.has_children() {
                    break fail(
                        "Verification left child processes running. Completion is inconclusive.",
                    );
                }
                if !exit.success() {
                    break Outcome {
                        passed: false,
                        inconclusive: false,
                        detail: format!(
                            "Local check failed (exit {})",
                            exit.code().map_or("unknown".into(), |c| c.to_string())
                        ),
                    };
                }
                match storage::fingerprint(Path::new(&settings.workspace)) {
                    Ok(after) if before == after => {
                        break Outcome {
                            passed: true,
                            inconclusive: false,
                            detail: "Configured local check passed; source fingerprint unchanged"
                                .into(),
                        }
                    }
                    Ok(_) => {
                        break fail("Source changed during verification. Run the check again.")
                    }
                    Err(e) => break fail(&e),
                }
            }
            Ok(None) => thread::sleep(Duration::from_millis(100)),
            Err(_) => {
                let _ = child.kill();
                let _ = child.wait();
                break fail("Cannot read verification process status");
            }
        }
    };
    #[cfg(windows)]
    drop(job);
    // Closing the job ends inherited pipe writers. Join promptly, with a bound
    // for abnormal OS/pipe failures rather than blocking the desktop host.
    let drain_deadline = Instant::now() + Duration::from_secs(1);
    while (!reader1.is_finished() || !reader2.is_finished()) && Instant::now() < drain_deadline {
        thread::sleep(Duration::from_millis(10));
    }
    if reader1.is_finished() {
        let _ = reader1.join();
    }
    if reader2.is_finished() {
        let _ = reader2.join();
    }
    outcome.with_cancellation(cancel.load(Ordering::SeqCst))
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn cancellation_after_success_computation_overrides_pass_and_failure() {
        for passed in [true, false] {
            let outcome = Outcome {
                passed,
                inconclusive: false,
                detail: "Already computed".into(),
            };
            let result = outcome.with_cancellation(true);
            assert!(!result.passed);
            assert!(result.inconclusive);
            assert_eq!(result.detail, "Local verification cancelled");
        }
        assert!(
            Outcome {
                passed: true,
                inconclusive: false,
                detail: "Passed".into()
            }
            .with_cancellation(false)
            .passed
        );
    }
    fn config(path: &Path, code: &str) -> Settings {
        Settings {
            workspace: path.to_string_lossy().into(),
            verify_program: "powershell.exe".into(),
            verify_args: vec!["-NoProfile".into(), "-Command".into(), code.into()],
            verify_timeout: 5,
            ..Default::default()
        }
    }
    #[test]
    #[cfg(windows)]
    fn detached_descendants_make_completion_inconclusive_and_are_terminated() {
        let d = tempfile::tempdir().unwrap();
        let log = tempfile::NamedTempFile::new().unwrap();
        let external = tempfile::tempdir().unwrap();
        let pid_file = external.path().join("child.pid");
        let path = pid_file.to_string_lossy().replace('\'', "''");
        let code=format!("$p=Start-Process powershell.exe -WindowStyle Hidden -PassThru -ArgumentList '-NoProfile','-Command','Start-Sleep 60'; $p.Id | Set-Content -LiteralPath '{path}'; exit 0");
        let result = run(
            &config(d.path(), &code),
            log.path(),
            Arc::new(AtomicBool::new(false)),
        );
        assert!(result.inconclusive);
        assert!(!result.passed);
        let pid = fs::read_to_string(&pid_file)
            .unwrap_or_else(|_| {
                panic!(
                    "{result:?}: {}",
                    fs::read_to_string(log.path()).unwrap_or_default()
                )
            })
            .trim()
            .to_string();
        assert!(
            !pid.is_empty(),
            "{result:?}: {}",
            fs::read_to_string(log.path()).unwrap_or_default()
        );
        let mut check = Command::new("powershell.exe");
        hidden(&mut check);
        let status=check.args(["-NoProfile","-Command",&format!("if(Get-Process -Id {pid} -ErrorAction SilentlyContinue){{exit 1}}else{{exit 0}}")]).status().unwrap();
        assert!(status.success(), "Detached verification child survived");
    }
    #[test]
    fn real_exit_codes_and_changed_sources() {
        let d = tempfile::tempdir().unwrap();
        let log = tempfile::NamedTempFile::new().unwrap();
        assert!(
            run(
                &config(d.path(), "exit 0"),
                log.path(),
                Arc::new(AtomicBool::new(false))
            )
            .passed
        );
        assert!(
            !run(
                &config(d.path(), "exit 7"),
                log.path(),
                Arc::new(AtomicBool::new(false))
            )
            .passed
        );
        assert!(
            !run(
                &config(d.path(), "Set-Content source.txt changed; exit 0"),
                log.path(),
                Arc::new(AtomicBool::new(false))
            )
            .passed
        );
    }
    #[test]
    fn cancellation_and_missing_executable_never_pass() {
        let d = tempfile::tempdir().unwrap();
        let log = tempfile::NamedTempFile::new().unwrap();
        let outcome = run(
            &config(d.path(), "Start-Sleep 20"),
            log.path(),
            Arc::new(AtomicBool::new(true)),
        );
        assert!(outcome.detail.contains("cancelled"));
        let mut c = config(d.path(), "exit 0");
        c.verify_program = "nekoafk-nonexistent-test-executable".into();
        assert!(!run(&c, log.path(), Arc::new(AtomicBool::new(false))).passed);
    }
    #[test]
    fn timeout_terminates_the_local_check() {
        let d = tempfile::tempdir().unwrap();
        let log = tempfile::NamedTempFile::new().unwrap();
        let result = run(
            &config(d.path(), "Start-Sleep 20"),
            log.path(),
            Arc::new(AtomicBool::new(false)),
        );
        assert!(!result.passed);
        assert!(result.detail.contains("timed out"));
    }
}
