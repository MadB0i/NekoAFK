# Focused release gate investigation — 13 October 2026

**Recommendation: NO-GO for a release candidate.** The latest target closure is
explained as an orderly application quit, not a demonstrated WebView crash.
The original uninstrumented incident remains unresolved, and the physical/manual
acceptance gates remain open. No newly confirmed spontaneous product crash was
found or claimed fixed. The confirmed diagnostic gap has been closed.

## Closure findings

| Observation | Evidence | Conclusion |
|---|---|---|
| 12 October, about 14:46 IST: historical `TargetClosedError` | Prior audit's `target-closed-soak` report; no host exit status or persistent lifecycle log | Cause UNKNOWN. A test connection closing alone does not identify the failing process or prove a crash. |
| Windows records around that incident | Application/System/WER queries, WER archive/queue inventory, retained run files, NekoAFK WebView Crashpad file inventory | No matching crash/power/shutdown evidence found. Absence of a report does not exclude a crash, termination, or lost diagnostic data. |
| 12 October, 21:28:06 IST: new soak target closure | `quit_requested` → `host_exit_requested(code=0)` → `host_exit`; external observer recorded host exit code 0 before cleanup | This occurrence followed the app's normal quit path. No native panic or WebView failure event was recorded. The quit caller was not recorded in that build; human action versus another caller is not established. |
| Deliberately terminated native renderer children | Native `ProcessFailed`, kind 1, reason 3, exit 15; host remained alive | Diagnostic coverage is confirmed. These were externally injected failures, even though the SDK labelled the reason “crashed.” A reason code alone does not identify the initiating actor. |
| Deliberately terminated WebView browser child | Native browser-process failure and browser-exit kind 1; host remained alive | Browser loss can be distinguished from host exit. Not a spontaneous reproduction. |
| Deliberately terminated native host | External observer exit code 1, missing orderly-exit record, retained marker, incomplete marker detected on relaunch | Abrupt loss is detectable. A retained marker alone cannot distinguish host crash, external termination, power loss or failed log writes. |

The source has one explicit `app.exit(0)` path, reached by the quit command or the
tray Quit action after cancellation/persistence. Window close requests hide the
window. Session events, reconnection and animation timers do not call quit.
This source audit supports the new logged normal-exit sequence; it does not prove
that the historical incident had the same cause.

## Changes and boundaries

- Added bounded local lifecycle records for host start, previous incomplete run,
  quit intent, exit request/completion, second-instance activation, window
  close-to-hide, Rust panic, native WebView process failure/browser exit and the
  first JavaScript error/rejection type per surface.
- The final follow-up records quit origin as `tray` or the Tauri-supplied native
  surface label. There is no client-supplied origin argument and no new command API.
- Logs exclude commands, source, URLs, exception messages, stacks, session IDs and
  agent payloads. Two files of at most 256 KiB each and a small active-run marker
  are retained. JavaScript reports are allowlisted and deduplicated. There is no
  per-frame or per-event-stream logging, upload, service or new timer.
- Native callbacks use the existing pinned WebView2/Windows crates already in
  Tauri's dependency graph. Callback registration failures are themselves recorded.
  Diagnostics failing to write does not prevent launch or change agent status.
- The soak harness now accepts a separate evidence directory, preserves diagnostics,
  records process exit status before cleanup, and waits for normal quit completion.

No character, animation, renderer scheduling, state model, verification logic,
OpenCode adapter or window architecture was changed in this investigation.
Astra's original artwork and all 12 authored performances pass preservation checks.
No CPU optimization or new comparative performance claim is made.

## Validation

The first diagnostic build was
`eaae182ff46d656c7c56e9678ec4b02414f98fb26feb8a7ffdbe799131da097e`.
Its native desktop suite passed all four checks; the native desktop/Settings smoke
suite passed ten checks with no JavaScript errors. Coverage includes native
borderless fullscreen pin/motion restoration, keyboard menu/Escape, selected-source
offline honesty, Settings validation, persistence/restart geometry, verification
pass/fail/cancel, accessibility scan and focus/scale/visibility interactions.
These do not substitute for physical tray, monitors, Narrator or exclusive graphics.

Five native lifecycle cases passed: normal quit (including second instance, ten
hide/show cycles and redacted JavaScript fault capture), renderer termination,
browser termination, host termination/relaunch, and a 50-second process suspension.
The initial suspension case started disconnected; it established responsiveness
after resumption, not stale-connection expiry. The final follow-up strengthens this
case with a labelled open-tool spool fixture, connection expiry and heartbeat
recovery. It passed on the final build without WebView failure or Rust panic;
the open operation remained pending and verification remained `not_run`.

The instrumented 20-minute soak was **INCOMPLETE**, ending at the normal quit above.
The last successful sample was 968.39 seconds into the workload (767 samples).
Both duplicate-terminal cycles drained exactly 500 then 1000 results with no open
operations. Both cycles reached real OpenCode restart/reconnection and quiet idle,
after real 70-second tools, permission interruption, cancellation, session switching,
independent verification and two hidden/resumed intervals. Actual shell `exit 7`
remained unknown/unverified where OpenCode supplied no numeric exit.
The partial run is not presented as a passed endurance test or a runtime-crash
reproduction. The earlier completed 20-minute runs retain their original scope
in `FINAL-QUALITY-AUDIT.md`.

Final diagnostic-origin build:
`9b1ad5850754032d26abf29c7b4cf28d102194affceb6792e005ef60b7777483`.
All five native lifecycle cases, all four native desktop checks and all ten native
Settings/desktop smoke checks passed again on this final build. Normal quit origin
was recorded as the invoking `neko` surface. No physical tray action was performed.
`native-final-build.json` ties these suites to the executable.
Rust regressions: 33 passed, including three new diagnostic tests; JavaScript: 17
passed; polling harness: 2 passed. Final formatting, Clippy/build and native outcome
passed and are recorded in the evidence directory. Native Rust panic capture is installed but
has not been deliberately fault-injected into the production host. No product test
API was added to cause a panic.

## Remaining gates and risk

| Priority | Item | Status |
|---|---|---|
| P1 | Physical mixed-DPI crossing/recovery, spoken Narrator, real tray/Explorer lifecycle, exclusive fullscreen | UNTESTED; release acceptance blockers, not demonstrated failures. |
| P1 | Real Windows sleep/hibernate/RDP and longer endurance | UNTESTED. Process suspension and app hide/show are explicitly narrower evidence. |
| P2 | Original uninstrumented target closure | Unresolved historical incident. The newly observed normal quit does not retroactively classify it. Persistent diagnostics now support a future recurrence. |
| P2 | Fatal WebView recovery experience | Failure detection verified by injection; automatic recovery behavior is unchanged and is not certified by these tests. No speculative renderer rebuild was added. |
| P2 | Representative slower-hardware resource/pacing budget | Prior active CPU comparisons overlap; no new improvement claimed. Hardware acceptance remains open. |

The available historical evidence is exhausted. Additional uninstrumented repeats
or unrelated refactors would not establish the original cause. Continue normal
use with the diagnostics and collect the evidence on recurrence. No installer,
commit, push, tag or publication was produced.

## Evidence and recurrence instructions

All new evidence is under `.artifacts/release-investigation/`:

- `windows-events.json`, `wer-inventory.json`, `webview-crash-inventory.json`,
  `historical-runtime-files.json`, `repeated-closure-events.json`.
- `lifecycle/report.json` and `lifecycle-final/report.json` plus each case's native
  JSONL records; failures here were deliberately injected. Initial acceptance is
  `native-desktop.json` / `native-smoke-report.json`; final acceptance is
  `native-desktop-final.json` / `native-smoke-final-report.json`, tied to
  `native-final-build.json`.
- `soak/soak-report.json`, `soak/soak-diagnostics/lifecycle.jsonl`, `soak-run.log`.
- `rust-tests-final.log`, `javascript-tests.log`, `harness-tests.log`,
  `clippy-final.log`, `build-final.log`, `character-preservation.json`.
- `native-captures/` preserves final native companion, dock and Settings images;
  companion and Settings captures were inspected. `cleanup.json` records no
  remaining test-owned NekoAFK/OpenCode processes. The user's OpenCode desktop
  processes were not targeted.

The app's existing data-folder control opens its local data directory. Preserve
`diagnostics/lifecycle.jsonl`, `diagnostics/lifecycle.previous.jsonl` (if present)
and `diagnostics/active-run` (if present), together with the time/timezone and
Windows Application/System events around any recurrence. Do not infer a crash
from the marker alone. Shutdown can end the host before a normal browser-exit
callback is delivered; the host exit sequence is the primary orderly-quit evidence.
Writes are best effort and not a guarantee against disk failure or sudden power loss.

Reproduction commands (test-owned native processes only):

```powershell
cargo test --offline --manifest-path src-tauri/Cargo.toml
npm test
python tests/quality_wait_test.py
npx tauri build --no-bundle
python tests/lifecycle_native.py --art .artifacts/release-investigation/lifecycle-new
python tests/quality_soak.py --seconds 1200 --art .artifacts/release-investigation/soak-new
```

See [NATIVE-HUMAN-ACCEPTANCE.md](NATIVE-HUMAN-ACCEPTANCE.md) for the separate unchecked
human gate. No manual case has been promoted to passed by automated evidence.
