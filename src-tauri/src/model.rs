use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, HashSet, VecDeque};
use std::time::{SystemTime, UNIX_EPOCH};

pub fn now() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis() as u64
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(default)]
pub struct Settings {
    pub workspace: String,
    pub verify_program: String,
    pub verify_args: Vec<String>,
    pub verify_timeout: u64,
    pub auto_verify: bool,
    pub scale: f64,
    pub always_on_top: bool,
    pub transparent: bool,
    pub attached: bool,
    pub reduced_motion: bool,
    pub personality: String,
    pub character: String,
    pub neko_visible: bool,
    pub dock_visible: bool,
    pub click_through: bool,
    pub dock_pinned: bool,
    pub dock_collapsed: bool,
    pub hud_enabled: bool,
    pub hud_collapsed: bool,
    pub sfx_enabled: bool,
    pub theme: String,
}
impl Default for Settings {
    fn default() -> Self {
        Self {
            workspace: String::new(),
            verify_program: String::new(),
            verify_args: vec![],
            verify_timeout: 120,
            auto_verify: false,
            scale: 1.,
            always_on_top: true,
            transparent: true,
            attached: true,
            reduced_motion: false,
            personality: "playful".into(),
            character: "robot".into(),
            neko_visible: true,
            dock_visible: false,
            click_through: false,
            dock_pinned: true,
            dock_collapsed: false,
            hud_enabled: true,
            hud_collapsed: false,
            sfx_enabled: true,
            theme: "amber".into(),
        }
    }
}
impl Settings {
    pub fn validate(&self) -> Result<(), String> {
        self.validate_structure()?;
        if !self.workspace.is_empty() && !std::path::Path::new(&self.workspace).is_dir() {
            return Err("Workspace folder does not exist".into());
        }
        Ok(())
    }
    pub fn validate_structure(&self) -> Result<(), String> {
        if !["calm", "playful", "chaos"].contains(&self.personality.as_str()) {
            return Err("Choose Calm, Playful or Chaos personality".into());
        }
        if !["cat", "robot"].contains(&self.character.as_str()) {
            return Err("Choose the Nova robot or Neko cat companion".into());
        }
        if !self.theme.is_empty() && !["amber", "cyan", "emerald", "sakura"].contains(&self.theme.as_str()) {
            return Err("Choose Amber, Cyan, Emerald or Sakura theme".into());
        }
        if !self.scale.is_finite() || !(0.5..=2.).contains(&self.scale) {
            return Err("Scale must be between 50 and 200 percent".into());
        }
        if !(5..=600).contains(&self.verify_timeout) {
            return Err("Verification timeout must be 5 to 600 seconds".into());
        }
        if self.verify_args.len() > 100 || self.verify_args.iter().any(|a| a.len() > 4096) {
            return Err("Verification arguments are too long".into());
        }
        if self.workspace.len() > 4096 || self.verify_program.len() > 4096 {
            return Err("Workspace or executable path is too long".into());
        }
        if self.auto_verify && (self.workspace.is_empty() || self.verify_program.trim().is_empty())
        {
            return Err("Automatic verification needs a workspace and executable".into());
        }
        Ok(())
    }
}
#[derive(Clone, Debug, Default, Deserialize, Serialize)]
pub struct Placement {
    pub x: i32,
    pub y: i32,
    pub width: u32,
    pub height: u32,
}
#[derive(Clone, Debug, Default, Deserialize, Serialize)]
#[serde(default)]
pub struct Config {
    pub settings: Settings,
    pub placements: BTreeMap<String, Placement>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct Evidence {
    pub version: u32,
    pub adapter: String,
    pub id: String,
    pub source: String,
    pub timestamp: u64,
    pub workspace: String,
    pub session: String,
    pub kind: String,
    pub tool: Option<String>,
    pub exit_code: Option<i64>,
    pub testing: Option<bool>,
    pub completed: Option<u32>,
    pub total: Option<u32>,
    pub request: Option<String>,
    pub operation: Option<String>,
    pub status: Option<String>,
    pub observed_at: Option<u64>,
    pub operations: Option<BTreeMap<String, String>>,
    pub requests: Option<Vec<String>>,
    pub tool_details: Option<BTreeMap<String, ToolObservation>>,
    pub outcome: Option<String>,
}
#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct ToolObservation {
    pub label: String,
    pub started_at: u64,
}
pub fn tool_label(tool: &str) -> &'static str {
    match tool {
        "bash" | "shell" => "Shell",
        "edit" | "write" | "apply_patch" | "patch" | "multiedit" => "File edit",
        "read" => "File read",
        "glob" | "grep" => "File search",
        "webfetch" | "websearch" => "Web lookup",
        "todowrite" | "todoread" => "Plan update",
        "task" => "Subagent",
        _ => "Tool",
    }
}
#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct Activity {
    pub at: u64,
    pub text: String,
}
#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct Session {
    pub key: String,
    pub adapter: String,
    pub workspace: String,
    pub id: String,
    pub source: String,
    pub state: String,
    pub last_activity: u64,
    pub revision: u64,
    pub tasks: Option<(u32, u32)>,
    pub failures: u32,
    pub failure_streak: u32,
    pub tests_passed: u32,
    pub claimed: bool,
    pub verification: String,
    pub activity: VecDeque<Activity>,
    pub permissions: HashSet<String>,
    pub operations: BTreeMap<String, String>,
    pub tool_details: BTreeMap<String, ToolObservation>,
    pub outcome: Option<String>,
    #[serde(skip)]
    results: BTreeMap<String, (Option<i64>, bool, bool)>,
}
impl Session {
    #[cfg(test)]
    pub fn finish_check(&mut self, passed: bool, revision: u64, detail: String, at: u64) {
        self.finish_check_outcome(passed, false, revision, detail, at);
    }
    pub fn finish_check_outcome(
        &mut self,
        passed: bool,
        inconclusive: bool,
        revision: u64,
        detail: String,
        at: u64,
    ) {
        let fresh = self.revision == revision;
        let pending = self.tasks.is_some_and(|(done, total)| done < total);
        self.verification = if !fresh || inconclusive {
            "inconclusive"
        } else if passed {
            "passed"
        } else {
            "failed"
        }
        .into();
        if passed
            && !inconclusive
            && fresh
            && self.claimed
            && !pending
            && self.permissions.is_empty()
            && self.operations.is_empty()
        {
            self.state = "verified".into();
        } else if !fresh || inconclusive {
            self.state = "inconclusive".into();
        } else if !passed {
            self.state = "failed".into();
            self.failure_streak += 1;
        }
        self.record(
            at,
            if !fresh {
                "Agent work changed during verification. Check again.".into()
            } else if inconclusive {
                detail
            } else if passed && pending {
                "Local check passed; agent still reports unfinished tasks. Celebration held.".into()
            } else {
                detail
            },
        );
    }
    fn record(&mut self, at: u64, text: String) {
        self.activity.push_front(Activity { at, text });
        self.activity.truncate(40);
    }
    pub fn display_state(&self, connected: bool, at: u64) -> &str {
        if !self.permissions.is_empty() {
            return "permission";
        }
        if self.verification == "running" {
            return "verifying";
        }
        if !connected {
            return "disconnected";
        }
        if self.state == "verified"
            || self.state == "failed"
            || self.state == "claimed"
            || self.state == "inconclusive"
            || self.state == "closed"
        {
            return &self.state;
        }
        if at.saturating_sub(self.last_activity) > 60_000 {
            if !self.operations.is_empty() {
                return &self.state;
            }
            return "inactive";
        }
        &self.state
    }
}
#[derive(Clone, Debug, Default, Serialize)]
pub struct Engine {
    pub sessions: BTreeMap<String, Session>,
    pub selected: Option<String>,
    #[serde(skip)]
    pub sources: BTreeMap<String, u64>,
    #[serde(skip)]
    seen: HashSet<String>,
    #[serde(skip)]
    order: VecDeque<String>,
}
pub const SUPPORTED_ADAPTERS: &[&str] = &[
    "opencode",
    "antigravity",
    "claudecode",
    "claude",
    "codex",
    "zai",
    "cursor",
    "generic",
];

pub fn adapter_display_name(adapter: &str) -> &'static str {
    match adapter {
        "antigravity" => "Antigravity",
        "claudecode" | "claude" => "Claude Code",
        "codex" => "Codex",
        "zai" => "Zai",
        "cursor" => "Cursor",
        "generic" => "Agent",
        _ => "OpenCode",
    }
}

impl Engine {
    pub fn ingest(&mut self, e: Evidence, at: u64) -> Option<String> {
        if e.version != 1
            || !SUPPORTED_ADAPTERS.contains(&e.adapter.as_str())
            || e.id.len() > 256
            || e.source.len() > 128
            || e.session.len() > 256
            || e.workspace.len() > 4096
            || e.request.as_ref().is_some_and(|r| r.len() > 256)
            || e.operation
                .as_ref()
                .is_some_and(|r| r.len() > 128 || r.is_empty())
            || e.operations.as_ref().is_some_and(|ops| {
                ops.len() > 128
                    || ops.iter().any(|(k, v)| {
                        k.is_empty()
                            || k.len() > 128
                            || !["active", "editing", "testing", "building"].contains(&v.as_str())
                    })
            })
            || e.requests
                .as_ref()
                .is_some_and(|rs| rs.len() > 128 || rs.iter().any(|r| r.len() > 256))
            || e.tool_details.as_ref().is_some_and(|items| {
                items.len() > 128
                    || items.iter().any(|(key, v)| {
                        key.is_empty()
                            || key.len() > 128
                            || v.started_at == 0
                            || v.started_at > e.timestamp
                            || ![
                                "Shell",
                                "File edit",
                                "File read",
                                "File search",
                                "Web lookup",
                                "Plan update",
                                "Subagent",
                                "Tool",
                            ]
                            .contains(&v.label.as_str())
                    })
            })
            || e.outcome.as_ref().is_some_and(|v| {
                !["unknown", "reported_pass", "failed", "interrupted"].contains(&v.as_str())
            })
            || e.timestamp > at + 30_000
            || at.saturating_sub(e.timestamp) > 90_000
            || self.seen.contains(&e.id)
        {
            return None;
        }
        let allowed = [
            "connected",
            "heartbeat",
            "disconnected",
            "session",
            "active",
            "busy",
            "editing",
            "planning",
            "writing",
            "building",
            "testing",
            "tool_finished",
            "failure",
            "permission",
            "permission_resolved",
            "idle",
            "tasks",
            "claimed",
            "snapshot",
            "closed",
            "interrupted",
        ];
        if !allowed.contains(&e.kind.as_str()) {
            return None;
        }
        self.seen.insert(e.id.clone());
        self.order.push_back(e.id);
        while self.order.len() > 4096 {
            if let Some(id) = self.order.pop_front() {
                self.seen.remove(&id);
            }
        }
        if e.kind == "disconnected" {
            if self
                .sources
                .get(&e.source)
                .is_some_and(|at| *at <= e.timestamp)
            {
                self.sources.remove(&e.source);
            }
            return None;
        }
        if self.sources.len() >= 100 && !self.sources.contains_key(&e.source) {
            self.sources.retain(|_, t| at.saturating_sub(*t) < 45_000);
            if self.sources.len() >= 100 {
                return None;
            }
        }
        self.sources
            .entry(e.source.clone())
            .and_modify(|at| *at = (*at).max(e.timestamp))
            .or_insert(e.timestamp);
        if e.session.is_empty() {
            return None;
        }
        let key = format!("{}|{}|{}", e.adapter, e.workspace, e.session);
        // Validate recovery before changing the session's source or clearing its
        // evidence. Transport freshness is not work-observation freshness.
        if e.kind == "snapshot" {
            let observed = e.observed_at.unwrap_or(0);
            if observed == 0
                || observed > e.timestamp
                || self
                    .sessions
                    .get(&key)
                    .is_some_and(|s| observed < s.last_activity)
                || ![
                    "idle",
                    "active",
                    "planning",
                    "writing",
                    "editing",
                    "testing",
                    "building",
                    "failed",
                    "claimed",
                    "inconclusive",
                ]
                .contains(&e.status.as_deref().unwrap_or("idle"))
            {
                return None;
            }
        }
        let new_session = !self.sessions.contains_key(&key);
        if new_session && self.sessions.len() >= 50 {
            let old = self
                .sessions
                .values()
                .filter(|s| Some(&s.key) != self.selected.as_ref() && s.verification != "running")
                .min_by_key(|s| s.last_activity)
                .map(|s| s.key.clone())?;
            self.sessions.remove(&old);
        }
        let s = self.sessions.entry(key.clone()).or_insert_with(|| Session {
            key: key.clone(),
            adapter: e.adapter,
            workspace: e.workspace,
            id: e.session,
            source: e.source.clone(),
            state: "idle".into(),
            last_activity: if e.kind == "snapshot" {
                e.observed_at.unwrap_or(e.timestamp).min(e.timestamp)
            } else {
                e.timestamp
            },
            revision: 0,
            tasks: None,
            failures: 0,
            failure_streak: 0,
            tests_passed: 0,
            claimed: false,
            verification: "not_run".into(),
            activity: VecDeque::new(),
            permissions: HashSet::new(),
            operations: BTreeMap::new(),
            tool_details: BTreeMap::new(),
            outcome: None,
            results: BTreeMap::new(),
        });
        if e.timestamp < s.last_activity {
            return None;
        }
        let new_source = s.source != e.source;
        if new_source {
            s.operations.clear();
            s.tool_details.clear();
            s.outcome = None;
            s.results.clear();
        }
        s.source = e.source;
        if self.selected.is_none() {
            self.selected = Some(key.clone());
        }
        if e.kind == "snapshot" {
            let observed = e.observed_at.unwrap_or(0);
            if observed == 0 || observed > e.timestamp || observed < s.last_activity {
                return None;
            }
            let status = e.status.as_deref().unwrap_or("idle");
            if ![
                "idle",
                "active",
                "planning",
                "writing",
                "editing",
                "testing",
                "building",
                "failed",
                "claimed",
                "inconclusive",
            ]
            .contains(&status)
            {
                return None;
            }
            // Equal snapshots refresh only the source lease, never revise work,
            // repeat failures, fabricate recent activity or invalidate proof.
            // A first claim can legitimately have revision zero. Only a newly
            // created session or replacement source needs hydration when the
            // observation times match. Source replacement invalidates old proof.
            if observed > s.last_activity || new_session || new_source {
                s.revision += 1;
                s.last_activity = observed;
                s.state = status.into();
                s.claimed = status == "claimed";
                if s.verification != "running" {
                    s.verification = "not_run".into();
                }
                s.operations = e.operations.unwrap_or_default();
                s.tool_details = e
                    .tool_details
                    .unwrap_or_default()
                    .into_iter()
                    .filter(|(key, _)| s.operations.contains_key(key))
                    .collect();
                s.outcome = e.outcome;
                s.permissions = e.requests.unwrap_or_default().into_iter().collect();
                s.tasks = None;
                if let (Some(done), Some(total)) = (e.completed, e.total) {
                    if done <= total && total <= 10000 {
                        s.tasks = Some((done, total));
                    }
                }
                s.record(
                    e.timestamp,
                    format!(
                        "Session context recovered from {}; completion still requires a local check",
                        adapter_display_name(&s.adapter)
                    ),
                );
            }
            return None;
        }
        if let Some(op) = e.operation.as_ref() {
            let op = format!("{}:{}", s.source, op);
            if ["tool_finished", "failure"].contains(&e.kind.as_str()) {
                s.operations.remove(e.operation.as_ref().unwrap());
                s.tool_details.remove(e.operation.as_ref().unwrap());
                let failed = e.kind == "failure";
                if let Some((exit, was_failed, was_testing)) = s.results.get(&op) {
                    if *was_failed || exit.is_some() && !failed || e.exit_code.is_none() && !failed
                    {
                        return None;
                    }
                    // Conflicting successful and failed terminal evidence is
                    // resolved conservatively: a later error invalidates success.
                    if failed && *exit == Some(0) && *was_testing {
                        s.tests_passed = s.tests_passed.saturating_sub(1);
                    }
                }
                s.results
                    .insert(op, (e.exit_code, failed, e.testing == Some(true)));
                if s.results.len() > 1000 {
                    let first = s.results.keys().next().cloned().unwrap();
                    s.results.remove(&first);
                }
            } else if ["active", "editing", "testing", "building"].contains(&e.kind.as_str())
                && s.operations.len() < 128
            {
                if s.results.contains_key(&op) {
                    return None;
                }
                s.operations
                    .insert(e.operation.clone().unwrap(), e.kind.clone());
                s.tool_details
                    .entry(e.operation.clone().unwrap())
                    .or_insert_with(|| ToolObservation {
                        label: tool_label(e.tool.as_deref().unwrap_or("")).into(),
                        started_at: e.timestamp,
                    });
            }
        }
        if e.kind != "heartbeat" && e.kind != "connected" {
            s.last_activity = e.timestamp;
        }
        let mut claim = None;
        match e.kind.as_str() {
            "closed" => {
                s.operations.clear();
                s.tool_details.clear();
                s.outcome = None;
                s.permissions.clear();
                s.claimed = false;
                s.revision += 1;
                s.state = "closed".into();
                if s.verification != "running" {
                    s.verification = "not_run".into();
                }
                s.record(
                    e.timestamp,
                    format!("Session closed in {}", adapter_display_name(&s.adapter)),
                );
            }
            "active" | "editing" | "testing" | "planning" | "writing" | "building" => {
                s.outcome = None;
                s.revision += 1;
                s.claimed = false;
                if s.verification != "running" {
                    s.verification = "not_run".into();
                }
                s.state = e.kind.clone();
                s.record(
                    e.timestamp,
                    match e.kind.as_str() {
                        "editing" => "Editing tool started",
                        "testing" => "Test-like command started",
                        "building" => "Build-like command started",
                        "planning" => "Reasoning part observed (content private)",
                        "writing" => "Assistant text observed (content private)",
                        _ => "Agent activity observed",
                    }
                    .into(),
                );
            }
            "busy" => {
                if ["idle", "inactive", "claimed", "verified"].contains(&s.state.as_str()) {
                    s.state = "active".into();
                    s.outcome = None;
                    s.claimed = false;
                    s.revision += 1;
                    if s.verification != "running" {
                        s.verification = "not_run".into();
                    }
                }
            }
            "tool_finished" => {
                s.outcome = Some(
                    if e.exit_code == Some(0) {
                        "reported_pass"
                    } else {
                        "unknown"
                    }
                    .into(),
                );
                s.revision += 1;
                s.claimed = false;
                if s.verification != "running" {
                    s.verification = "not_run".into();
                }
                if e.testing == Some(true) && e.exit_code == Some(0) {
                    s.tests_passed += 1;
                    s.record(
                        e.timestamp,
                        "Test-like command exited 0 (agent evidence)".into(),
                    );
                } else {
                    s.record(
                        e.timestamp,
                        if e.exit_code.is_none() {
                            "Tool finished; exit code unavailable. No independent verification"
                        } else {
                            "Tool finished; no independent verification"
                        }
                        .into(),
                    );
                }
                if e.exit_code == Some(0) {
                    s.failure_streak = 0;
                }
                s.state = "active".into();
            }
            "failure" => {
                s.outcome = Some("failed".into());
                s.failures += 1;
                s.failure_streak += 1;
                s.revision += 1;
                s.claimed = false;
                if s.verification != "running" {
                    s.verification = "not_run".into();
                }
                s.state = "failed".into();
                s.record(
                    e.timestamp,
                    "Agent error or nonzero tool exit observed".into(),
                );
            }
            "permission" => {
                if s.permissions.len() < 128 {
                    s.permissions.insert(e.request.unwrap_or_default());
                }
                s.revision += 1;
                if s.verification != "running" {
                    s.verification = "not_run".into();
                }
                if s.state == "verified" {
                    s.state = "active".into();
                    s.claimed = false;
                }
                s.record(
                    e.timestamp,
                    format!("Permission requested in {}", adapter_display_name(&s.adapter)),
                );
            }
            "permission_resolved" => {
                s.permissions.remove(&e.request.unwrap_or_default());
                s.record(
                    e.timestamp,
                    format!("Permission answered in {}", adapter_display_name(&s.adapter)),
                );
            }
            "tasks" => {
                let tasks = e
                    .completed
                    .zip(e.total)
                    .filter(|(done, total)| done <= total && *total <= 10000);
                if s.tasks != tasks {
                    s.revision += 1;
                    if s.verification != "running" {
                        s.verification = "not_run".into();
                    }
                    if s.state == "verified" {
                        s.state = "claimed".into();
                    }
                }
                s.tasks = tasks;
            }
            "idle" => {
                s.operations.clear();
                s.tool_details.clear();
                if !["claimed", "verified", "failed", "inconclusive"].contains(&s.state.as_str()) {
                    s.state = "idle".into();
                }
            }
            "claimed" => {
                s.claimed = true;
                s.state = "claimed".into();
                s.record(
                    e.timestamp,
                    "Assistant finished its response; completion is unverified".into(),
                );
                claim = Some(key);
            }
            "interrupted" => {
                // Keep terminal tombstones for cancelled operations. A delayed
                // tool callback must not resurrect them or count a passing exit.
                // The blocking flag is private; no failure is added to telemetry.
                for key in s.operations.keys() {
                    s.results
                        .insert(format!("{}:{}", s.source, key), (None, true, false));
                }
                while s.results.len() > 1000 {
                    let key = s.results.keys().next().cloned().unwrap();
                    s.results.remove(&key);
                }
                s.operations.clear();
                s.tool_details.clear();
                s.permissions.clear();
                s.outcome = Some("interrupted".into());
                s.claimed = false;
                s.revision += 1;
                s.state = "inconclusive".into();
                if s.verification != "running" {
                    s.verification = "not_run".into();
                }
                s.record(
                    e.timestamp,
                    format!(
                        "{} reported an interrupted response; completion unverified",
                        adapter_display_name(&s.adapter)
                    ),
                );
            }
            _ => {}
        }
        claim
    }
    pub fn connected(&self, at: u64) -> bool {
        self.sources
            .values()
            .any(|t| at.saturating_sub(*t) < 45_000)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn an_inconclusive_outcome_cannot_celebrate_even_with_a_pass_flag() {
        let mut m = Engine::default();
        m.ingest(event("claimed", "claim"), 1000);
        let s = m.sessions.values_mut().next().unwrap();
        s.finish_check_outcome(
            true,
            true,
            s.revision,
            "Cancelled at publication".into(),
            1001,
        );
        assert_eq!(s.verification, "inconclusive");
        assert_eq!(s.state, "inconclusive");
    }
    #[test]
    fn windows_crash_exit_codes_are_valid_failure_evidence() {
        let mut m = Engine::default();
        let mut e = event("failure", "crash");
        e.exit_code = Some(0xc0000005);
        let e: Evidence = serde_json::from_slice(&serde_json::to_vec(&e).unwrap()).unwrap();
        m.ingest(e, 1000);
        assert_eq!(m.sessions.values().next().unwrap().failures, 1);
    }
    #[test]
    fn a_closed_session_retires_pending_tools_and_permissions() {
        let mut m = Engine::default();
        m.ingest(event("permission", "p"), 1000);
        let mut e = event("editing", "start");
        e.operation = Some("tool".into());
        m.ingest(e, 1000);
        m.ingest(event("closed", "closed"), 1000);
        let s = m.sessions.values().next().unwrap();
        assert!(s.permissions.is_empty() && s.operations.is_empty());
        assert_eq!(s.display_state(true, 1000), "closed");
        assert!(!s.claimed);
    }
    #[test]
    fn a_conflicting_error_invalidates_a_known_success() {
        let mut m = Engine::default();
        let mut e = event("tool_finished", "ok");
        e.operation = Some("call".into());
        e.testing = Some(true);
        e.exit_code = Some(0);
        m.ingest(e, 1000);
        assert_eq!(m.sessions.values().next().unwrap().tests_passed, 1);
        let mut e = event("failure", "error");
        e.operation = Some("call".into());
        e.exit_code = Some(2);
        m.ingest(e, 1000);
        let s = m.sessions.values().next().unwrap();
        assert_eq!(s.tests_passed, 0);
        assert_eq!(s.failures, 1);
        assert_eq!(s.state, "failed");
    }
    fn event(kind: &str, id: &str) -> Evidence {
        serde_json::from_value(serde_json::json!({"version":1,"adapter":"opencode","id":id,"source":"test","timestamp":1000,"workspace":"C:/project","session":"one","kind":kind})).unwrap()
    }
    #[test]
    fn connected_long_tools_remain_observed_but_disconnection_wins() {
        let mut m = Engine::default();
        let mut e = event("testing", "start");
        e.operation = Some("call".into());
        m.ingest(e, 1000);
        let s = m.sessions.values().next().unwrap();
        assert_eq!(s.display_state(true, 90000), "testing");
        assert_eq!(s.display_state(false, 90000), "disconnected");
        let mut e = event("tool_finished", "end");
        e.operation = Some("call".into());
        m.ingest(e, 1000);
        assert_eq!(
            m.sessions
                .values()
                .next()
                .unwrap()
                .display_state(true, 90000),
            "inactive"
        );
    }
    #[test]
    fn richer_terminal_evidence_recovers_a_missed_exit_without_double_counting() {
        let mut m = Engine::default();
        let mut e = event("tool_finished", "unknown");
        e.operation = Some("call".into());
        m.ingest(e, 1000);
        let mut e = event("failure", "known");
        e.operation = Some("call".into());
        e.exit_code = Some(2);
        m.ingest(e.clone(), 1000);
        e.id = "another-hook".into();
        m.ingest(e, 1000);
        let s = m.sessions.values().next().unwrap();
        assert_eq!(s.failures, 1);
        assert_eq!(s.failure_streak, 1);
        assert_eq!(s.state, "failed");
    }
    #[test]
    fn restart_snapshots_recover_context_without_inventing_recent_activity_or_proof() {
        let mut m = Engine::default();
        let mut e = event("snapshot", "snap");
        e.timestamp = 80000;
        e.observed_at = Some(1000);
        e.status = Some("claimed".into());
        m.ingest(e.clone(), 80000);
        let s = m.sessions.values_mut().next().unwrap();
        assert_eq!(s.last_activity, 1000);
        assert_eq!(s.state, "claimed");
        assert_eq!(s.verification, "not_run");
        s.finish_check(true, s.revision, "passed".into(), 80000);
        let rev = s.revision;
        e.id = "next-heartbeat".into();
        e.timestamp = 95000;
        m.ingest(e, 95000);
        let s = m.sessions.values().next().unwrap();
        assert_eq!(s.state, "verified");
        assert_eq!(s.revision, rev);
    }
    #[test]
    fn equal_snapshot_preserves_proof_when_claim_was_the_first_observation() {
        let mut m = Engine::default();
        m.ingest(event("claimed", "first-claim"), 1000);
        let s = m.sessions.values_mut().next().unwrap();
        s.finish_check(true, s.revision, "passed".into(), 2000);
        let revision = s.revision;
        let mut snapshot = event("snapshot", "heartbeat");
        snapshot.timestamp = 16000;
        snapshot.observed_at = Some(1000);
        snapshot.status = Some("claimed".into());
        m.ingest(snapshot, 16000);
        let s = m.sessions.values().next().unwrap();
        assert_eq!(s.state, "verified");
        assert_eq!(s.verification, "passed");
        assert_eq!(s.revision, revision);
        assert_eq!(s.last_activity, 1000);
    }
    #[test]
    fn cancellation_is_inconclusive_and_does_not_add_a_failure() {
        let mut m = Engine::default();
        m.ingest(event("claimed", "c"), 1000);
        let s = m.sessions.values_mut().next().unwrap();
        s.finish_check_outcome(false, true, s.revision, "Cancelled".into(), 1000);
        assert_eq!(s.verification, "inconclusive");
        assert_eq!(s.failure_streak, 0);
    }
    #[test]
    fn claims_and_idle_never_verify() {
        let mut m = Engine::default();
        m.ingest(event("claimed", "a"), 1000);
        m.ingest(event("idle", "b"), 1000);
        let s = m.sessions.values().next().unwrap();
        assert_eq!(s.state, "claimed");
        assert_eq!(s.verification, "not_run");
    }
    #[test]
    fn multi_agent_adapters_are_accepted_and_recorded() {
        let mut m = Engine::default();
        for adapter in ["antigravity", "claudecode", "codex", "zai"] {
            let ev: Evidence = serde_json::from_value(serde_json::json!({
                "version": 1,
                "adapter": adapter,
                "id": format!("{}-1", adapter),
                "source": "multi-test",
                "timestamp": 1000,
                "workspace": "D:/test-workspace",
                "session": format!("{}-sess", adapter),
                "kind": "editing"
            })).unwrap();
            m.ingest(ev, 1000);
            let key = format!("{}|D:/test-workspace|{}-sess", adapter, adapter);
            let s = m.sessions.get(&key).expect("session exists");
            assert_eq!(s.adapter, adapter);
            assert_eq!(s.state, "editing");
        }
    }
    #[test]
    fn duplicates_and_stale_events_are_ignored() {
        let mut m = Engine::default();
        m.ingest(event("failure", "a"), 1000);
        m.ingest(event("failure", "a"), 1000);
        m.ingest(event("failure", "b"), 100000);
        assert_eq!(m.sessions.values().next().unwrap().failures, 1);
    }
    #[test]
    fn permissions_survive_heartbeats_and_activity() {
        let mut m = Engine::default();
        m.ingest(event("permission", "a"), 1000);
        m.ingest(event("editing", "b"), 1000);
        assert_eq!(
            m.sessions
                .values()
                .next()
                .unwrap()
                .display_state(true, 1001),
            "permission"
        );
        m.ingest(event("permission_resolved", "c"), 1000);
        assert_eq!(
            m.sessions
                .values()
                .next()
                .unwrap()
                .display_state(true, 1001),
            "editing"
        );
    }
    #[test]
    fn sessions_are_isolated_and_silence_is_inactivity() {
        let mut m = Engine::default();
        m.ingest(event("editing", "a"), 1000);
        let mut b = event("failure", "b");
        b.session = "two".into();
        m.ingest(b, 1000);
        assert_eq!(m.sessions.len(), 2);
        assert_eq!(
            m.sessions
                .values()
                .next()
                .unwrap()
                .display_state(true, 62000),
            "inactive"
        );
    }
    #[test]
    fn invalid_counts_do_not_create_progress() {
        let mut m = Engine::default();
        let mut e = event("tasks", "a");
        e.completed = Some(4);
        e.total = Some(2);
        m.ingest(e, 1000);
        assert!(m.sessions.values().next().unwrap().tasks.is_none());
    }
    #[test]
    fn failure_streak_needs_a_known_success_and_permissions_override_checks() {
        let mut m = Engine::default();
        m.ingest(event("failure", "a"), 1000);
        m.ingest(event("failure", "b"), 1000);
        m.ingest(event("tool_finished", "c"), 1000);
        assert_eq!(m.sessions.values().next().unwrap().failure_streak, 2);
        let mut success = event("tool_finished", "d");
        success.exit_code = Some(0);
        m.ingest(success, 1000);
        assert_eq!(m.sessions.values().next().unwrap().failure_streak, 0);
        m.ingest(event("permission", "e"), 1000);
        let s = m.sessions.values_mut().next().unwrap();
        s.verification = "running".into();
        assert_eq!(s.display_state(true, 1001), "permission");
    }
    #[test]
    fn cancelled_or_stale_checks_are_inconclusive() {
        let mut m = Engine::default();
        m.ingest(event("claimed", "a"), 1000);
        let s = m.sessions.values_mut().next().unwrap();
        s.finish_check_outcome(false, true, s.revision, "cancelled".into(), 1000);
        assert_eq!(s.state, "inconclusive");
        assert_eq!(s.display_state(true, 1001), "inconclusive");
        assert_ne!(s.state, "verified");
    }
    #[test]
    fn stale_checks_and_pending_tasks_cannot_celebrate() {
        let mut m = Engine::default();
        m.ingest(event("claimed", "a"), 1000);
        let s = m.sessions.values_mut().next().unwrap();
        s.tasks = Some((1, 2));
        s.finish_check(true, s.revision, "passed".into(), 1000);
        assert_ne!(s.state, "verified");
        assert_eq!(s.verification, "passed");
        s.tasks = Some((2, 2));
        s.revision += 1;
        s.finish_check(true, s.revision - 1, "passed".into(), 1000);
        assert_ne!(s.state, "verified");
        assert_eq!(s.verification, "inconclusive");
        s.finish_check(true, s.revision, "passed".into(), 1000);
        assert_eq!(s.state, "verified");
    }
    #[test]
    fn new_permission_invalidates_a_previous_verified_result() {
        let mut m = Engine::default();
        m.ingest(event("claimed", "a"), 1000);
        let s = m.sessions.values_mut().next().unwrap();
        s.finish_check(true, s.revision, "passed".into(), 1000);
        assert_eq!(s.state, "verified");
        m.ingest(event("permission", "b"), 1000);
        m.ingest(event("permission_resolved", "c"), 1000);
        let s = m.sessions.values().next().unwrap();
        assert_ne!(s.state, "verified");
        assert_eq!(s.verification, "not_run");
    }
}
