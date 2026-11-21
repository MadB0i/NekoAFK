//! A single presentation model for the HUD and dock. Counts are plan steps,
//! never an estimate of effort or proof that a task has been completed.
use crate::model::Session;
use serde::Serialize;

#[derive(Clone, Debug, Serialize)]
pub struct Plan {
    pub completed: u32,
    pub total: u32,
    pub historical: bool,
}
#[derive(Clone, Debug, Serialize)]
pub struct Progress {
    pub session_key: Option<String>,
    pub context: String,
    pub activity: String,
    pub detail: String,
    pub tone: String,
    pub connected: bool,
    pub plan: Option<Plan>,
    pub started_at: Option<u64>,
}
pub fn derive(session: Option<&Session>, connected: bool, state: &str) -> Progress {
    let mut p = Progress {
        session_key: session.map(|s| s.key.clone()),
        context: session
            .map(|s| {
                format!(
                    "{} · {}",
                    s.workspace
                        .rsplit(['/', '\\'])
                        .find(|v| !v.is_empty())
                        .unwrap_or("Workspace")
                        .chars()
                        .filter(|c| !c.is_control())
                        .take(32)
                        .collect::<String>(),
                    s.id.chars()
                        .rev()
                        .take(6)
                        .collect::<String>()
                        .chars()
                        .rev()
                        .filter(|c| c.is_ascii_alphanumeric() || *c == '-')
                        .collect::<String>()
                )
            })
            .unwrap_or_else(|| "OpenCode".into()),
        activity: if connected {
            "Waiting for a session"
        } else {
            "Bridge offline"
        }
        .into(),
        detail: "Connect OpenCode in Settings".into(),
        tone: "quiet".into(),
        connected,
        plan: None,
        started_at: None,
    };
    let Some(s) = session else {
        return p;
    };
    p.plan = s
        .tasks
        .filter(|(done, total)| *total > 0 && done <= total)
        .map(|(completed, total)| Plan {
            completed,
            total,
            historical: !connected || state == "inactive" || state == "closed",
        });
    let (activity, detail, tone) = match state {
        "permission" => ("Permission needed", "Answer in OpenCode", "attention"),
        "verifying" => ("Verifying locally", "Independent check running", "active"),
        "disconnected" => (
            "Connection lost",
            "Last evidence · reconnect OpenCode",
            "offline",
        ),
        "inactive" => (
            "No recent activity",
            "Last evidence · current work unknown",
            "unknown",
        ),
        "closed" => ("Session closed", "Choose a session in the dock", "quiet"),
        "verified" => (
            "Locally verified",
            "Configured independent check passed",
            "verified",
        ),
        "claimed" => (
            "Completion unverified",
            "Agent finished · local proof pending",
            "unknown",
        ),
        "failed" => (
            "Needs attention",
            "Failure observed · review evidence",
            "failed",
        ),
        "inconclusive" if s.outcome.as_deref() == Some("interrupted") => {
            ("Work interrupted", "No verified completion", "unknown")
        }
        "inconclusive" => (
            "Check inconclusive",
            "Review evidence in the dock",
            "unknown",
        ),
        "planning" => ("Reasoning observed", "Observed OpenCode activity", "active"),
        "writing" => ("Writing response", "Observed OpenCode activity", "active"),
        "editing" => ("Editing files", "Observed OpenCode activity", "active"),
        "testing" => ("Running tests", "Command classified as test-like", "active"),
        "building" => ("Building", "Command classified as build-like", "active"),
        "active" => ("Working", "Observed OpenCode activity", "active"),
        _ => ("Waiting", "No independent check has run", "quiet"),
    };
    p.activity = activity.into();
    p.detail = detail.into();
    p.tone = tone.into();
    if !connected {
        p.detail = if state == "permission" {
            "Offline · permission still pending"
        } else if state == "verifying" {
            "OpenCode offline · local check running"
        } else {
            "Last evidence · reconnect OpenCode"
        }
        .into();
        return p;
    }
    if ["active", "editing", "testing", "building"].contains(&state) && !s.operations.is_empty() {
        if s.operations.len() > 1 {
            p.detail = format!("{} observed tools running", s.operations.len());
        } else if let Some((key, kind)) = s.operations.iter().next() {
            let tool = s.tool_details.get(key);
            if state == "active" {
                p.activity = format!("{} running", tool.map_or("Tool", |t| t.label.as_str()));
            }
            p.detail = format!(
                "{} · {}",
                tool.map_or("Tool", |t| t.label.as_str()),
                match kind.as_str() {
                    "testing" => "test-like command",
                    "building" => "build-like command",
                    "editing" => "file operation",
                    _ => "execution observed",
                }
            );
        }
        p.started_at = s.tool_details.values().map(|t| t.started_at).min();
    } else if ["active", "idle"].contains(&state) {
        match s.outcome.as_deref() {
            Some("unknown") => {
                p.detail = "Exit unknown · unverified".into();
                p.tone = "unknown".into();
            }
            Some("reported_pass") => {
                p.detail = "Tool exited 0 · unverified".into();
            }
            _ => {}
        }
    }
    p
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::model::{Engine, Evidence};
    fn emit(m: &mut Engine, value: serde_json::Value) {
        let mut base = serde_json::json!({"version":1,"adapter":"opencode","id":"event","source":"source","timestamp":1000,"workspace":"C:/private/project","session":"session","kind":"idle"});
        base.as_object_mut()
            .unwrap()
            .extend(value.as_object().unwrap().clone());
        let e: Evidence = serde_json::from_value(base).unwrap();
        let at = e.timestamp;
        m.ingest(e, at);
    }
    #[test]
    fn plan_can_grow_reopen_disappear_and_never_verifies() {
        let mut m = Engine::default();
        for (n, (done, total)) in [(1, 3), (3, 3), (3, 5), (2, 5), (0, 0)]
            .into_iter()
            .enumerate()
        {
            emit(
                &mut m,
                serde_json::json!({"kind":"tasks","id":n.to_string(),"completed":done,"total":total}),
            );
            let s = m.sessions.values().next().unwrap();
            let p = derive(Some(s), true, s.display_state(true, 1000));
            assert_ne!(p.tone, "verified");
            assert_eq!(
                p.plan.as_ref().map(|v| (v.completed, v.total)),
                if total == 0 {
                    None
                } else {
                    Some((done, total))
                }
            );
        }
    }
    #[test]
    fn unknown_terminal_offline_and_separate_sessions_are_explicit() {
        let mut m = Engine::default();
        emit(
            &mut m,
            serde_json::json!({"id":"start","kind":"active","operation":"a","tool":"PRIVATE CUSTOM NAME"}),
        );
        let s = m.sessions.values().next().unwrap();
        let p = derive(Some(s), true, "active");
        assert_eq!(p.activity, "Tool running");
        assert_eq!(p.started_at, Some(1000));
        emit(
            &mut m,
            serde_json::json!({"id":"end","kind":"tool_finished","operation":"a"}),
        );
        let s = m.sessions.values().next().unwrap();
        let p = derive(Some(s), true, "active");
        assert_eq!(p.tone, "unknown");
        assert!(p.detail.contains("unverified"));
        let p = derive(Some(s), false, "disconnected");
        assert_eq!(p.tone, "offline");
        assert!(p.started_at.is_none());
        emit(
            &mut m,
            serde_json::json!({"id":"other","session":"other","kind":"idle"}),
        );
        let s = m.sessions.values().find(|s| s.id == "other").unwrap();
        let p = derive(Some(s), true, "idle");
        assert!(p.plan.is_none());
        assert_eq!(p.tone, "quiet");
    }
    #[test]
    fn duplicate_old_terminal_and_interruption_cannot_invent_completion() {
        let mut m = Engine::default();
        emit(
            &mut m,
            serde_json::json!({"id":"begin","kind":"active","operation":"a","tool":"bash"}),
        );
        emit(
            &mut m,
            serde_json::json!({"id":"abort","timestamp":1100,"kind":"interrupted"}),
        );
        emit(
            &mut m,
            serde_json::json!({"id":"old","timestamp":1050,"kind":"tool_finished","operation":"a","exit_code":0}),
        );
        emit(
            &mut m,
            serde_json::json!({"id":"late","timestamp":1200,"kind":"tool_finished","operation":"a","exit_code":0}),
        );
        let s = m.sessions.values().next().unwrap();
        let p = derive(Some(s), true, s.display_state(true, 1100));
        assert_eq!(p.activity, "Work interrupted");
        assert!(p.started_at.is_none());
        assert_ne!(p.tone, "verified");
        emit(
            &mut m,
            serde_json::json!({"id":"abort","timestamp":1100,"kind":"interrupted"}),
        );
        assert_eq!(m.sessions.values().next().unwrap().revision, 2);
    }

    #[test]
    fn stale_reconnect_snapshot_cannot_erase_current_progress() {
        let mut m = Engine::default();
        emit(
            &mut m,
            serde_json::json!({"id":"plan","timestamp":2000,"kind":"tasks","completed":1,"total":3}),
        );
        emit(
            &mut m,
            serde_json::json!({"id":"start","timestamp":2100,"kind":"active","operation":"a","tool":"bash"}),
        );
        emit(
            &mut m,
            serde_json::json!({"id":"old-recovery","timestamp":2200,"source":"replacement","kind":"snapshot","observed_at":1900,"status":"idle"}),
        );
        let s = m.sessions.values().next().unwrap();
        assert_eq!(s.tasks, Some((1, 3)));
        assert_eq!(s.operations.len(), 1);
        assert_eq!(s.source, "source");
    }

    #[test]
    fn old_transport_records_do_not_rewind_a_live_source() {
        let mut m = Engine::default();
        emit(
            &mut m,
            serde_json::json!({"id":"heartbeat","timestamp":3000,"kind":"heartbeat"}),
        );
        emit(
            &mut m,
            serde_json::json!({"id":"old","timestamp":2000,"kind":"tasks","completed":1,"total":3}),
        );
        assert_eq!(m.sources["source"], 3000);
        emit(
            &mut m,
            serde_json::json!({"id":"old-disconnect","timestamp":2500,"kind":"disconnected"}),
        );
        assert_eq!(m.sources.get("source"), Some(&3000));
    }

    #[test]
    fn replacement_tool_source_does_not_silently_remove_an_incomplete_plan() {
        let mut m = Engine::default();
        emit(
            &mut m,
            serde_json::json!({"id":"plan","kind":"tasks","completed":1,"total":2}),
        );
        emit(
            &mut m,
            serde_json::json!({"id":"claim","timestamp":1100,"source":"replacement","kind":"claimed"}),
        );
        let s = m.sessions.values().next().unwrap();
        assert_eq!(s.tasks, Some((1, 2)));
        assert_eq!(derive(Some(s), true, "claimed").plan.unwrap().completed, 1);
    }
}
