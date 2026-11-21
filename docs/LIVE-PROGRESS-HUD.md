# Live coding progress HUD

Windows-only feature pass. Astra’s artwork and all 12 authored performances remain unchanged. No installer, commit, push, tag or publication.

## Evidence and semantics

The Rust host derives `Snapshot.progress` from the selected session and its own connection lease. The floating HUD and expanded dock render that same value. Character state continues through the existing director, independent of plan counts.

| Observed evidence | HUD / dock behavior |
|---|---|
| Real tool start | Fixed allowlisted tool label; current observed activity. Commands and outputs are never shown. |
| Reasoning/text/edit/test/build signals | Observed activity label. Generic busy stays Working when details are unavailable. |
| Explicit `todo.updated` | Completed / non-cancelled plan steps; labelled Plan progress. Added, removed and reopened steps replace the count. |
| Empty/malformed/missing plan | No progress bar. Unknown in dock; No plan observed in HUD. |
| Numeric exit 0 | Tool exited 0, still unverified. |
| Missing numeric exit | Exit unknown, still unverified. No inference from output or HTTP success. |
| Numeric nonzero / explicit tool error | Needs attention. |
| Explicit `MessageAbortedError` | Work interrupted; late callbacks from interrupted operations cannot restore success. |
| Permission request | Permission needed; remains explicit when disconnected. |
| Agent completion claim / all plan steps complete | Unverified. Counts never imply task completion. |
| Independent configured check passes with valid current evidence | Locally verified, through the existing verification gate. |
| Disconnect / inactivity | Historical plan marked Last plan progress; current execution is not asserted. |

Plan steps are not weighted effort. There is no calibrated ETA source: the compact HUD omits ETA, and expanded details say **ETA unavailable**. Optional elapsed time was omitted to avoid a continuous clock update. Expanded details show the observed tool-start time when available; it is not an inferred execution duration.

The existing plugin consumes supported hooks/events without model requests or another service. The locally installed SDK describes todo statuses pending, in_progress, completed and cancelled. The real server’s session todo endpoint can confirm an empty plan; populated-plan cases are explicitly labelled hook fixtures. Official references: [OpenCode server](https://dev.opencode.ai/docs/server/) and [plugins](https://docs.opencode.ai/docs/plugins/).

## Desktop behavior and privacy

The HUD is a fourth small native surface, 248 × 136 logical pixels (248 × 72 collapsed), derived from the companion’s monitor/work area. It tries each side and avoids visible telemetry. It shares companion visibility, pin and click-through preferences, hides during fullscreen and Settings, and has no independently persisted position. Desktop Settings and the tray can disable it. Buttons open telemetry and collapse/expand; both support keyboard use.

The HUD carries a bounded workspace basename and session suffix, fixed activity labels and numeric counts. No prompt, milestone content, tool arguments, command output or source content is added. No new account, service, dependency, adapter or product IPC endpoint. The existing window action endpoint gains HUD actions.

HUD updates are event-driven. It has no RAF loop or elapsed-time interval. Plan-value transitions honor both saved and system reduced-motion preferences. Status announcements are polite and suppressed while the dock is visible; spoken Narrator still requires human acceptance.

## Confirmed fixes

- Temporarily disabling the HUD collapse button removed keyboard focus in WebView2. Focus now returns after the action only if the user has not moved to another control; native regression asserts consecutive Enter collapse/expand.
- A stale replacement-source snapshot cleared current plan/tool evidence before checking its observation time. Recovery validation now precedes session mutation; equal-time replacement-source snapshots hydrate their own context.
- Older transport events rewound the connection lease, and old disconnects removed a newer lease. Lease updates are monotonic and stale disconnects are ignored.
- The full native smoke suite caught a new-source regression in this feature: a known incomplete plan was cleared by an unrelated replacement-source event, bypassing the pending-plan verification gate. Plan counts now persist until explicit replacement/clearing evidence; the original smoke assertion and a new Rust regression cover it.
- Explicit interruption is represented separately from failure. Interrupted operation tombstones prevent late exit callbacks from reviving cancelled work in both adapter cache and host.

The two reconnect defects were first demonstrated by failing Rust regressions in `.artifacts/live-progress/reconnect-before.log`.

## Validation

Candidate executable SHA-256: `4127e18cd709fc646165b33ba6ba6c64665657962960682da3ac2a02a05d78d0`.
Baseline: `940d3b69c2f6daf9a032128513e4ba43dc9af20697e02019ba44b63bbe690cf1`.

- **41 Rust / 21 JavaScript tests passed**, including plan replacement/reopening, private-content exclusion, fixed tool labels, late terminal results after interruption, stale snapshots and connection ordering. Frontend type check/build passed; native executable built with `--no-bundle`.
- **16 native HUD checks passed**: plan/no-plan, invalid/empty plan, unknown/numeric-failure exits, independent proof, interruption, session isolation, stale records, reconnect, offline permission, identical dock/HUD progress, keyboard collapse/expand, all four single-monitor corners, reduced motion, axe, settled rendering, visibility and Settings persistence.
- Existing native smoke, desktop/fullscreen, experience interactions, character acceptance, real OpenCode, lifecycle and combined soak suites passed. `suite-manifest.json` records commands, durations and the executable hash. The fullscreen test explicitly restores a known non-fullscreen foreground after removing its fixture. Its final rerun also checks HUD visibility during fullscreen and after return.
- Genuine **OpenCode 1.18.35**, no model calls: two real sessions, real shell starts/finishes, an empty todo endpoint response, 70-second tool across companion restart, selected-session switching, nonzero shell command, server disconnect/restart and session deletion. Numeric exits were absent from the actual response/events, including `exit 7`; HUD remained unknown/unverified. Populated todos, permission waits and explicit agent cancellation are hook fixtures, not claimed as model-driven OpenCode trials.
- Character preservation compares the SVG SHA and all 12 authored performances sampled at 60 Hz. Artwork SHA: `6818c8b4722414f8552a3c6f0b64381cf131f4c60137840113be5f7b194ee7c3`. No authored poses, clips, props, artwork or motion rate changed in this feature pass.
- Native character acceptance included 180 seconds of continuing work, rapid permission interrupts, repeated failures, user/system reduced motion, transparency, hide/resume and personality persistence. The combined authentic/simulated soak ran **340.73 seconds**, including 500 duplicate-terminal-protected tool results, cancellation races, session switching during verification, independently verified success, actual server restart and hidden/resumed windows. No JavaScript errors or unexplained full-motion callback gaps were recorded. Host exited normally.
- Combined-soak private memory: **216.21 → 230.36 MiB**, peak **258.12 MiB**; measured app-tree CPU average **13.17% of one core**. Instrumented one-second samples include event bursts and test observation overhead; they are not the matched before/after benchmark. Short warm-up growth does not establish or disprove a memory leak. It is not a 2–3 hour or multi-day acceptance test.
- The separate 65-second verified-idle regression passed across heartbeats. The older `living_cat_native.py` and attached `rapid_native.py` regressions also passed; their isolated test app was closed afterward. `validation.json` ties this evidence and the video to the candidate. All three hidden/reduced-motion benchmark runs recorded zero character RAF callbacks. The settled HUD observation recorded zero DOM mutations and zero RAF requests over 3.5 seconds; heartbeat/event updates remain expected.

A run interrupted by a tray Quit is preserved in `tray-interrupted-lifecycle.jsonl`: `quit_requested(origin=tray)`, `host_exit_requested(code=0)`, `host_exit`. It is an observed orderly exit, not a renderer failure and not an explanation for the older uninstrumented incident. Controlled lifecycle tests separately passed renderer/browser/host termination diagnostics and a 50-second process suspend/resume. They do not demonstrate automatic renderer recovery or real OS sleep.

## Matched performance

Same native harness, seed 1234, Playful mode, companion geometry, display (1920 × 1080, 125%), WebView2 version, process-tree accounting and phase durations; three fresh processes per candidate. No concurrent build, recording or second native suite during these measurements. The baseline predates the HUD; the candidate has it enabled. Sequential desktop runs cannot eliminate ambient-load/thermal variation.

CPU is **percent of one core**, median (range). Memory is median endpoint process-tree private working set (USS), not summed shared RSS.

| Workload | Before CPU | HUD CPU | Before → HUD private MiB |
|---|---:|---:|---:|
| Natural idle, 60 s | 11.01 (10.76–11.27) | 11.40 (10.83–11.58) | 205.15 → 226.61 |
| Authored keyboard, 14 s | 16.23 (14.53–23.78) | 18.57 (17.08–20.78) | 207.12 → 228.48 |
| Hidden, 5 s | 1.83 (1.81–2.74) | 3.32 (2.41–3.92) | 207.08 → 229.04 |
| Reduced motion, 5 s | 0.61 (0.00–2.43) | 3.01 (1.20–5.14) | 209.02 → 229.32 |

The HUD adds about **21 MiB** median private memory. Idle and active CPU ranges overlap; the active median is higher, so this is not claimed as a speed improvement or zero-cost feature. Hidden/reduced medians also rose; the five-second phases are short and variable. No speculative optimization or motion-quality reduction was made.

Active-pose mutation p95 was **35.7–35.8 ms before / 35.8–35.9 ms after**. Natural-idle p95 was **35.7–37.2 / 36.1–36.2 ms**. These are DOM pose-update intervals below 100 ms; deliberate quiet gaps are excluded. They are **not GPU presentation timing**. No allocation/paint trace claim is made. Raw distributions, callbacks, process churn and per-run memory are in `before-profile/report.json`, `after-profile/report.json` and `performance-comparison.json`.

## Native previews

All paths are under `.artifacts/live-progress/`:

- `native/neko-live-progress.mp4` — approximately 39-second real Windows compositor capture, transparent companion and native HUD over a neutral native backdrop. Hook-fixture plan/permission/claim sequence is labelled as such; independent verification actually executes a local command. It is not a browser mockup or a fabricated live-agent recording.
- `native/companion-with-plan.png` — frame from that native capture.
- `native/dock-expanded-progress.png`, `native/collapsed.png`, `native/offline-permission.png`, `native/unknown-exit.png` — actual WebView2 surfaces.
- `real-opencode-running.png`, `real-opencode-unknown.png` — HUD driven by the genuine server.
- `native/contact-sheet-final.png` — sampled native video frames used for visual review.

Review at actual Windows sizes found readable activity/plan hierarchy and intact character transparency. The expanded dock keeps provenance and ETA explanation separate from the compact HUD. Long context/detail strings intentionally truncate; the full progress details remain in telemetry. This is desktop acceptance, not a mobile redesign.

## Remaining gates and recommendation

**GO for a supervised 2–3 hour daily-use trial. NO-GO for release sign-off yet.** Run the current executable and update the workspace bridge from Settings before the trial so the installed plugin includes the new tool/interruption metadata. Existing different bridge files are backed up by that action.

| Priority | Remaining item | Classification |
|---|---|---|
| P1 | Physical mixed-DPI crossings/edge placement, spoken Narrator, real tray lifecycle, exclusive fullscreen, actual sleep/hibernate/RDP | UNTESTED human acceptance; follow `NATIVE-HUMAN-ACCEPTANCE.md`. |
| P1 | Planned daily-use trial, sustained resource growth and unexpected closure recurrence | UNTESTED beyond the bounded native runs here; retain persistent lifecycle diagnostics. |
| P2 | Historical uninstrumented WebView closure | Unresolved incident, not a confirmed current-build failure. This pass’s interrupted run was a logged normal tray quit. |
| P2 | Missing numeric exits and plan signals that OpenCode does not emit | Protocol limitation. Unknown stays unknown; no progress/ETA inference. A plugin restart may have no plan context until fresh todo evidence arrives. |
| P2 | Additional WebView memory and variable quiet-state CPU | Measured cost above; watch during trial. Disabling the HUD hides the surface, it does not unload its WebView. |

No physical/manual acceptance case is marked passed. No installer, commit, push, tag or publication was performed.
