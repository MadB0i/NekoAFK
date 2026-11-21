# Windows engineering audit — October 12, 2026

Follow-up measurements, cancellation/clock fixes, corrected test-harness findings
and the current release recommendation are in
[FINAL-QUALITY-AUDIT.md](FINAL-QUALITY-AUDIT.md). The historical results below retain
their original scope; see [NATIVE-HUMAN-ACCEPTANCE.md](NATIVE-HUMAN-ACCEPTANCE.md) for
the physical/spoken acceptance gate.

## Scope and architecture

This pass preserves Astra's SVG artwork, all 12 authored clips, poses, expressions,
props, easing and sample functions. The character comparison checks the original
art hash, complete clip definitions and poses sampled at 60 Hz. Rendering remains
in the existing companion WebView2 window. The dock and Settings remain separate
native windows. No adapter replacement, installer, commit or publication.

OpenCode supported hooks write sanitized atomic queue files. The Rust host validates
and deduplicates evidence, keeps bounded session state, and publishes snapshots.
The deterministic character director interprets factual state separately from its
entertaining performances. Independent configured checks run in the saved workspace
and compare source fingerprints before/after; agent claims and tool exits alone
cannot verify completion. Future adapters can extend the evidence boundary; future
packs can implement the existing pose/part contract. Neither is implemented here.

## Audit findings and fixes

- The companion scheduled callbacks at the display's refresh rate (144 Hz here),
  including completely settled rest. It painted at 30 Hz. It now schedules near
  the next 30 Hz deadline and sleeps across unchanged rest until a blink or new
  performance. Agent observations immediately wake it. Authored settling and soft
  appendage follow-through finish before sleep. Reduced motion and hidden/fullscreen
  suspension stop the frame loop.
- Long-running tools aged into inactivity after one minute, despite a connected
  bridge. Bounded operation IDs now retain observed tool state until terminal or
  idle evidence arrives. Disconnection still overrides work. Verification is held
  while observed tools remain open.
- A restarted companion lost context until the next event. Bridge heartbeats now
  include bounded, sanitized session snapshots with original observation times,
  open operations, pending requests and task counts. Recovery never creates proof,
  increments historical failure counts or invents recent activity. Equal snapshots
  leave existing independent proof unchanged.
- An early terminal hook with unknown exit could suppress a later richer tool part.
  Terminal IDs and an operation-result ledger now admit richer evidence and count
  it once. Conflicting error evidence conservatively invalidates a prior success.
  Windows crash exit values above signed 32-bit range are accepted as failures.
- Session deletion now retires pending operations/permissions and displays closed.
  Both older permission.updated/permissionID and current permission.asked/requestID
  shapes are supported. Commands, reasoning, prompts and output stay out of telemetry.
- Cancelled or stale independent checks were labelled failed. They now store and
  explain an inconclusive result without adding a failure streak.
- Verification children could outlive the parent and retain reader pipes. A native
  Windows job closes descendants on cancellation/completion; a parent leaving live
  descendants cannot produce verified success. Output remains bounded.
- Native dragging used Tao 0.37.1's pointer-valued WM_NCLBUTTONDOWN coordinate
  parameter. It now uses packed coordinate values and preserves pointer movement
  between DOM mouse-down and native capture, including short completed drags.
  Physical testing at 125% scale confirms companion movement, attached following,
  dock movement and automatic detachment.
- DPI crossings no longer invoke recovery mid-drag. Explicit recovery clamps onto
  the nearest display instead of jumping to the first enumerated monitor. Dock
  following avoids unchanged position calls.
- Fullscreen foreground windows now yield companion/dock pinning and pause character
  motion, then restore saved preferences. A real borderless native window validates
  this independently of browser fullscreen emulation.
- Lease timestamps no longer generate redundant UI broadcasts. An unchanged dock
  status no longer rewrites its live-region text. Settings preserves focused select
  controls. Persisted settings receive structural validation while a temporarily
  missing workspace is retained with an actionable notice.
- The dock now reports the selected session's connection independently of other
  bridges. A pending permission keeps its priority while a disconnected source is
  clearly shown offline, even if another OpenCode instance remains connected.

## Validation

Evidence lives in `.artifacts/engineering`; historical character-direction media is
preserved. Native suites use isolated settings/workspaces and test-only local CDP
endpoints. No debugging listener was added to production configuration.

All **26 Rust** and **16 JavaScript** tests passed. TypeScript/Vite production build,
Rust formatting and Clippy with warnings denied passed. The application was rebuilt
with `--no-bundle`; no installer was produced. A final source/art comparison confirms
all 12 authored performances and original artwork remain identical.

The full desktop suite passed independent pass/fail/cancel checks, permission waits,
honest task counts, visibility/attachment/scaling/pinning, keyboard controls, axe on
all three native WebViews and Settings sections (zero violations), local persistence
and restart geometry without frame growth. Runtime console errors: zero. Display
acceptance passed at 1920×1080 and 1366×768, restoring the original mode afterward.
Physical mouse testing confirmed movement and attached-dock following at 125% scale,
and dock dragging detached it. Native UI Automation exposes named controls; this
does not establish that spoken Narrator behavior is correct.
The final native fullscreen/keyboard suite also passed the multi-bridge connection
regression: a disconnected selected session with a pending permission remains visibly
offline while another bridge is live.

The complete existing activity suite passed on the final executable, including its
70-second native run, user/system reduced motion, hide/recover, personality Settings,
native axe/overflow and transparent pixels. The 62-event burst preserved permission
priority. Unchanged reduced-motion SVG mutations: **0**; unchanged host snapshot
broadcasts: **0**. Its actual native video is 92.43 seconds. That suite measured
12.86% of one core during its 70-second, enlarged-character activity sample, 226.5 MiB
private memory afterward, and 9.48% during its short default-scale sample. These
different activity/configuration samples are supplementary, not substituted into
the paired before/after table.

Real OpenCode 1.18.35 acceptance passed a 70-second shell operation, companion restart
during that operation, original-time context recovery, server disconnect/reconnect,
new tool activity after recovery, and actual session deletion. No model requests were
made. Success animation acceptance uses an actual independent local command; the
showcase's agent activity is explicitly identified as hook fixtures.

### Performance

Same display/settings, sequential release-executable runs, no concurrent compilation.
CPU includes the native host and its WebView2 process tree, expressed as a percentage
of **one core**, not total-machine CPU. CDP instrumentation was attached in both runs.
Idle selection was random; actual activities are retained in the raw reports.

| Phase | Before CPU | After CPU | Before private MiB | After private MiB |
|---|---:|---:|---:|---:|
| Idle mix, 35 s | 33.20% | 18.71% | 208.6 | 195.5 |
| Quiet rest with occasional blink, 8 s | 25.63% | 11.71% | 226.2 | 210.4 |
| Authored keyboard, 14 s | 47.82% | 35.62% | 238.5 | 223.3 |
| Reduced motion, 10 s | 9.67% | 5.11% | 209.2 | 207.4 |
| Static dock, 10 s | 11.94% | 11.53% | 202.0 | 199.8 |
| All windows hidden, 10 s | 2.95% | 1.86% | 209.6 | 208.2 |

The baseline woke at approximately 144 callbacks/s even in quiet rest. The candidate
averaged 22/s over the idle mix and 14.6/s across quiet rest including blink/settling.
Typing averaged 57.7 callbacks/s while changing SVG poses at approximately 30 Hz;
median mutation cadence remained 34.6 ms before versus 34.7 ms after. This is DOM
cadence, not proof of GPU frame presentation. Reduced motion and hidden states had
zero animation callbacks. An unchanged reduced-motion pose has zero SVG mutations,
and identical host snapshots produce zero redundant broadcasts.

**The CPU issue is improved in this paired run, not closed.** Earlier baseline runs
measured 23.31% idle and 15.39% typing, versus 33.20% and 47.82% in the repeat. Candidate
typing measured 36.94% and 35.62%. These variable short samples do not demonstrate a
universal active CPU improvement. Remaining typing cost is concentrated in renderer
and GPU processes; JavaScript script time was 0.115 s across the 14.12-second candidate
sample. Further graphics profiling on representative machines is required before
setting release resource targets. Phase-end memory values are not a leak test.

The 600.06-second transparent, default-scale native soak passed with general busy
evidence refreshed through explicit hook fixtures: **11.96% of one core**, private
memory 287.5 MiB initially and 217.9 MiB finally (284.1 MiB maximum among subsequent
samples). Reduced motion measured 0.31%. There were no runtime errors, overflows or
loss of the factual busy state. Authored variations continued for the entire run.
This ten-minute result does not establish multi-day stability or absence of leaks.
Motion sampling measured median 34.7 ms and p95 35.7 ms DOM mutation cadence.

The native character regression passed rapid-event/permission priority, interrupted
keyboard/prop cleanup, repeated failure, inconclusive without victory, transparent
pixels, disconnection/recovery, user/system reduced motion, hide/resume, and all
personality modes. It recorded a 57.4-second actual Windows-composited video.

Raw performance reports and JS sampling profiles are preserved alongside
`performance-comparison.json`. Performance and the ten-minute soak were captured
before the final selected-connection metadata/UI correction; the renderer and all
authored performances are identical in the final build. Each report retains its
measured executable hash rather than relabelling earlier measurements.

### Evidence paths

- `.artifacts/engineering/performance-comparison.json`: paired measurements, exact
  executable hashes, short-run limitations and ten-minute resource results.
- `.artifacts/engineering/character-regression/native-acceptance.json` and
  `neko-native-showcase.mp4`: 600-second native acceptance and 57.4-second capture.
- `.artifacts/native-validation/report.json`: complete desktop acceptance, rerun on
  the final executable.
- `.artifacts/engineering/desktop-native.json` and
  `dock-selected-session-offline.png`: native fullscreen, keyboard and connection case.
- `.artifacts/engineering/opencode-recovery.json`: actual OpenCode server/session tests.
- `.artifacts/engineering/companion-windows-before.jpg`, `companion-windows-after.jpg`,
  `dock-windows-after.jpg` and `physical-*-final.json`: real mouse and Windows captures.
- `.artifacts/premium-validation/display-report.json`: native display-mode changes.
- `.artifacts/engineering/character-preservation.json`: art/clip identity and final hash.
- `.artifacts/engineering/living-regression/report.json` and
  `neko-native-activities.mp4`: final-executable activity, rapid-event and accessibility
  regression with its second native capture.

## Release blockers and limits

- Active rendering CPU remains material and variable; longer graphics profiling on
  representative hardware is needed. The paired improvement alone is insufficient
  to declare the original 19–22% CPU concern resolved.
- Physical mixed-DPI dragging across two monitors and monitor unplug/replug need
  suitable hardware. This host exposes one monitor. Native display-mode acceptance
  covers 1920×1080 and 1366×768, including their exposed scale transition.
- Full spoken Narrator acceptance and physical notification-area menu acceptance
  remain separate from axe, keyboard and native accessibility-tree checks. Narrator
  started, but its helper window could not be targeted reliably; spoken behavior is
  not marked passed. The computer-use surface does not expose the notification area.
- OpenCode 1.18.35's direct shell API reports a completed tool with metadata containing
  output but no numeric exit, even for `exit 7`. Neko explicitly reports an unknown
  exit and never treats it as a passing test. Reliable failures on that route require
  an upstream numeric exit/error signal; parsing output would fabricate certainty.
- Recovery snapshots cover sessions observed by the running bridge. They do not
  reconstruct full historical activity/counters or discover every pre-existing
  session before any hook has fired. Session counts are bounded and in memory.
- A passing configured command proves only that command against the observed revision
  and source snapshot. External edits after verification without any agent signal
  are not continuously watched. Fingerprinting has file/byte budgets, but slow or
  unavailable network filesystems still need cancellation/latency acceptance.
- Process jobs provide cleanup, not a security sandbox. Assignment follows process
  creation; adversarial descendants are outside the local-check trust model.
- Fullscreen handling was tested with a real native borderless window. Exclusive
  DirectX games, remote desktop, sleep/wake and multi-day operation need acceptance.
- Signing, clean-machine WebView2 bootstrap and installer acceptance remain gated;
  no installer was built during this pass.
