# Final desktop quality engineering pass

Follow-up: [RELEASE-GATE-INVESTIGATION.md](RELEASE-GATE-INVESTIGATION.md) records the
focused closure investigation and persistent diagnostics. Its new target closure
was identified as normal application quit; that does not establish the cause of
the original uninstrumented incident described in this historical audit.

## Scope and baseline

The starting executable was copied to `.artifacts/final-quality/baseline/nekoafk.exe`
before source changes. SHA-256: `01c680e8aaa71253aef25ae9c5d578a87860e26183d149f6aaa8fa2f850cce5b`.
The working tree already contained the modern app as untracked files and a modified
README. That work is preserved; no reset, commit, installer, tag or publication.

Inspected the preceding engineering audit, raw measurements, native tests, adapter,
renderer/director, host event model, persistence, window/tray handling and verifier.
No AGENTS.md was found outside excluded dependency/archive/build directories.
The original SVG, identity, props, expressions, authored keyframes, clip selection
rules and all 12 performances are preserved. No new product API, service or dependency.

## Root causes and changes

1. **Mixed animation clocks.** `observe()` and timeout deadlines used
   `performance.now()`, but the frame loop stored the earlier RAF timestamp.
   Native callback lag was measured up to approximately 7 ms at p99. An observation
   followed by such a callback could rewind `previousTime`; the deadline comparison
   could also reject a callback whose execution had already reached the deadline.
   Elapsed motion now advances using execution time, matching observations. The
   original RAF-based paint deadlines and timer policy remain intact. A regression
   fails on the preserved source and passes with this correction, without changing
   any authored pose.
2. **Cancellation/publication race.** Cancellation was polled while running the
   command, but a successful outcome could be computed before a cancellation was
   accepted and published afterward. The cancellation flag is now checked under the
   same host lock used to accept the result. Matching job tokens and the original
   session key still bind results to the correct check/session. Deterministic tests
   cover cancellation after result computation, stale tokens and selected-session
   switching. Already-cancelled checks avoid launching another command.
3. **Contradictory inconclusive/pass flags.** The session model marked verification
   inconclusive but could still enter `verified` if both input flags were true.
   Inconclusive now explicitly prevents that transition; a regression protects it.
4. **Claim-first recovery invalidated proof.** A native quiet-state follow-up
   reproduced a verified result changing back to `claimed` at the first 15-second
   heartbeat. A completion claim can be the first observed event and leave the work
   revision at zero. Snapshot recovery treated that as a newly created session.
   Recovery now checks actual session creation; equal-time snapshots preserve proof.
   The new regression failed before the fix (`claimed` instead of `verified`).
   The failed native report and test log are retained as
   `quiet-claim-first-failed-report.json` and `claim-first-before.log`.

These cancellation issues were identified through code paths and deterministic
tests; a spontaneous false victory was not observed during native testing.

## Performance method and findings

Previous short profiles had different random activity mixes and cannot demonstrate
a universal active CPU improvement. New profiles record process-tree CPU/private
memory, per-process-kind CPU, RAF callback lag/count, pose-mutation distributions,
long tasks, WebView task/script/layout/style durations, JS heap size and actual clips.

Each repeat starts a fresh real Windows executable with isolated data, equal settings,
the same display and ordered workloads. No compilation runs concurrently. The seeded
comparison uses CDP to set only the existing Character constructor's seed parameter
to 1234, then disables the debugger before measurement. It does not replace crypto,
add a product hook or alter the binary. Timing jitter and event delivery remain real.

Workloads: idle 30 s, writing 35 s (authored typing plus natural rests), 500 unique
test-like operations with duplicate terminal hooks, an observed 70-second open tool,
hidden 15 s and reduced motion 10 s. A separate three-repeat, 14-second keyboard
entrance comparison isolates the same authored active clip from longer rest mixes.
External fixture producers are excluded from app process-tree CPU. Process births
and retirements are recorded to identify accounting limitations.
CPU uses cumulative times for processes present at both observation endpoints;
short-lived descendants that start/exit between reads are not fully accounted.
The animation profiles contain no verification launches and their recorded process
sets match. The soak includes short-lived verification children, so its aggregate
CPU must not be treated as complete lifetime accounting for those commands.

RAF/DOM mutation distributions are **not GPU presented-frame times**. Separate
diagnostic traces expose Paint/Raster/Layout/compositor events; allocation sampling
is labelled separately from comparable CPU phases. The first live-allocation sample
retained no sampled objects, which does not mean the app allocates nothing. The
expanded sampler includes collected objects. No power/ETW/GPU presentation claim.
Pose-interval quantiles exclude gaps of 100 ms or more to separate authored holds;
they do not prove absence of every stall. Long-task observations begin after the
native surfaces load, so they do not characterize startup. JS heap measurements
cover the companion renderer; private memory and CPU cover the whole app tree.
The separately launched OpenCode server and fixture producer are excluded. The
`private_*_mib` fields measure unique resident memory (`psutil` USS), not Windows
committed Private Bytes; committed-memory growth is not established by these data.

Initial diagnostics show graphics/rendering work dominates; no JavaScript long tasks
were observed in the initial timed workloads. A 10-second diagnostic trace recorded
590 Paint events, 534 RasterTask events and 295 Layout events. Event-flood host CPU
was approximately 2% of one core in early samples. The existing bounded spool,
publication suppression and attribute cache are retained; no speculative rewrite.

An execution-time paint-deadline prototype was **rejected** after three fixed-seed,
same-keyboard samples. Callback counts fell from 804–831 to 459–476 per approximately
14 seconds and pose counts remained 391–395, but median run p95 mutation interval
worsened from 35.8 to 48.0 ms. CPU ranges overlapped (18.76–28.07% before,
16.54–23.24% prototype), so they do not establish a reliable CPU gain. The final code
retains only the elapsed-time correctness fix and restores the original smoother
paint scheduling. Raw rejected measurements are preserved as
`.artifacts/final-quality/rejected-clock-profile.json`; they are not final results.

Final process-tree CPU, median and min–max across three fresh-process repeats,
percent of one core:

| Workload | Before | Final |
|---|---:|---:|
| Idle with natural performances/rest | 8.872% (7.022–10.154) | 9.133% (7.748–10.626) |
| Writing, including authored rests | 10.547% (9.850–12.063) | 10.308% (9.231–11.146) |
| High-frequency duplicate-terminal workload | 22.178% (20.325–25.635) | 22.131% (21.261–25.407) |
| Open tool, 70 seconds | 9.127% (7.619–9.869) | 8.569% (8.102–8.801) |
| Hidden | 1.442% (0.923–1.543) | 1.848% (1.742–2.477) |
| Reduced motion | 1.362% (0.303–1.664) | 0.908% (0.906–1.368) |
| Same keyboard entrance, 14 seconds | 20.879% (18.764–28.070) | 20.617% (19.141–31.360) |

**No reliable active CPU reduction is claimed.** The final change corrects elapsed
time rather than lowering rendering work. Hidden CPU is somewhat higher in this
sample despite zero RAF callbacks, pose mutations, script duration and layout
duration; it is not evidence of a hidden animation loop. All repeated hidden and
reduced-motion samples recorded zero RAF/pose updates. Recorded endpoint process
sets matched in every measured phase. No JavaScript long tasks were recorded.

The same-keyboard run's median p95 pose interval is 35.8 ms before and 35.7 ms final;
final samples contain 393–395 pose updates versus 392–395 before. These are native
mutation intervals, not GPU presentation. Keyboard process-kind median CPU is
10.805% GPU-process and 8.489% renderer in the final runs; host median is 0.219%.
Medians of individual process categories do not necessarily sum to the median total.

A separate final 10-second diagnostic recorded 588 Paint, 532 RasterTask and 294
Layout events. Sampled allocation estimates total 7,638,416 bytes (233 samples,
including objects later collected); `paint` accounts for 2,851,784 sampled bytes.
This identifies transient pose/string work, not a demonstrated allocation leak or
GC stall. Nested trace durations are not additive CPU/wall time. No additional
renderer changes were retained without demonstrated visual and resource benefit.

Raw evidence: `.artifacts/final-quality/seeded-{before,final}-profile.json`,
`typing-{before,final}-profile.json`, `seeded-final-trace.json`,
`seeded-final-allocations.json`, and the rejected prototype report above.
The generated `summary.json` includes distributions, process-kind measurements,
activities, private memory and exact binary identities. The performance-measured
executable SHA-256 is:
`03f031a7fa15e2177c3bf5058a7c5fa2d05ce91d8da28073a08fbf80a6487d8f`.
The later claim-first recovery correction changes only the model's snapshot
hydration condition and its regression. The rebuilt final executable is
`cfb8af2546189c7cde8982e7cf1aa1c045faad977772c3999a57512fa84ac138`.
The repeated CPU comparison applies to the measured binary, not a measurement of
that later build. No extra performance benefit is attributed to the model fix.

### Measurement-harness correction

The first mixed-event soak stopped at an early open-operation assertion. Investigation
reproduced a test-harness defect: this installed Playwright implementation resolves
`wait_for_function('async()=>false')` immediately because it tests the Promise's
truthiness. The resolved value is actually false. Evidence is saved in
`async-wait-repro.json`; the installed driver's polling implementation was also read.
The next instrumented run confirmed premature acceptance at 487 of 500 results.
Neither early run is counted as a passed soak; both reports/logs are retained.

The harness now polls already-resolved native snapshots in Python and requires
both the exact counter delta and zero open operations. Two regression tests cover
continued polling through false/intermediate conditions and timeout. No product
code change was needed for this failure. A fresh corrected 20-minute soak completed.

The original paired CPU measurements retain their actual sampling windows and
resource values; the erroneous predicate ran after the timed event-flood phase.
Their recorded counter snapshots range from 493 to 500 results, rather than proving
that every run had fully drained at that point. Do not interpret their legacy
`duplicate_terminal_integrity` field as complete delivery proof. Exact delivery is
established separately by the corrected soak; original raw evidence is not rewritten.

## OpenCode protocol and correctness

The installed OpenCode 1.18.35 SDK exposes direct-shell terminal payloads with output
and call/session IDs, but no numeric exit in `session.next.shell.ended` (including
its sync-event form). The existing `tool.execute.after` hook accepts arbitrary
metadata; numeric `metadata.exit` remains supported where actually supplied. The
direct-shell route previously emitted completed parts with only output metadata,
including for `exit 7`. Live protocol capture rechecks property/metadata keys and
numeric exits without interpreting command output. Unknown must remain unknown;
neither tool completion nor an agent claim establishes independent success.

The SDK does expose a numeric `exitCode` on `pty.exited`, but that payload identifies
a PTY, without a session/call mapping. The observed direct-shell operations do not
emit that event. Applying unrelated PTY exits to coding-agent tools would invent
correlation, so no speculative adapter path was added. References inspected locally:
`@opencode-ai/sdk/dist/v2/gen/types.gen.d.ts` (`EventPtyExited`,
`SessionNextShellEnded`, and its sync/event forms) and the existing production hook.

The soak combines an authentic isolated OpenCode server with explicitly labelled
production-adapter fixtures: real 70-second shell execution, server restart and
reconnection, duplicate results, permission interruption, cancellation, switching
sessions during interrupted verification, independent local checks, hidden/unhidden
and application resume. No model requests or remote provider calls are made.

## Native acceptance and human gate

The final build passes **30 Rust tests, 17 JavaScript tests and two polling-harness
regressions**, plus formatting, Clippy with warnings denied, TypeScript/Vite and
the no-bundle native build. The three serial native suites also pass:
four native desktop checks, ten desktop/Settings checks and ten character checks.
`native-suite-build.json` ties all three suites to the final executable hash.
No installer was produced.

Native coverage includes keyboard menu/Escape, focus/stacking, Settings validation,
saved scale/visibility/attachment/pins, restart geometry without frame growth,
independent verification pass/fail/cancel, selected-source disconnection while
another bridge remains connected, and real borderless HWND fullscreen suspension
with restored pinning. The character run includes permission interruption and
prop retirement, repeated failure/inconclusive reactions, hide/resume, transparency,
personality persistence, reduced motion and 180.06 seconds of continuing activity.
Its process-tree CPU was 9.86% of one core; unique resident memory was
273.5 → 229.6 MiB (peak 273.5 MiB). Reduced-motion CPU was 0.31% in that sample.
These separate workloads are not additional paired optimization results.

The new **56.4-second native showcase** and screenshots show the preserved character
and transitions. Native transparent, typing, dock and Settings captures were inspected.
Reduced-motion coverage uses the saved app setting and a CDP-emulated WebView media
preference; it does not establish physical Windows Settings toggle behavior.

See **[NATIVE-HUMAN-ACCEPTANCE.md](NATIVE-HUMAN-ACCEPTANCE.md)** for a separate checklist
and evidence classification. Automated native checks are distinct from prior real
pointer/UI Automation observations and unperformed physical/spoken acceptance.
No cross-monitor, spoken Narrator, physical tray or exclusive-fullscreen item is
marked passed on the basis of browser/IPC testing.

### Final-build soak result

The final repeat completed **1200.08 seconds** on build `cfb8af25…`, with **all 11
checks passed and no runtime errors**. Both cycles drained exactly 500 results
(500 then 1000 total), with zero open operations. Real 70-second tools, two server
restarts, permission waits, six immediate cancellations, session switching during
interrupted verification, independent local success and application hide/resume
all completed. No model/provider requests were made. Actual shell `exit 7` remained
unknown/unverified because no numeric exit signal was supplied.

| Final mixed-workload measurement | Observed |
|---|---:|
| Sampled app-tree CPU, percent of one core | 11.579% average |
| One-second CPU p50 / p95 / p99 | 7.462% / 30.868% / 36.919% |
| Unique resident memory, start → end | 194.46 → 223.98 MiB |
| Unique resident memory, sampled peak | 245.93 MiB |
| Quiet-window mutation p95, first / second | 35.9 / 36.6 ms |
| Full-motion, visible, unpaused context samples | 922 |
| Paused context samples | 61 |
| Unexplained full-motion callback gaps over 15 s | 0 |

The two quiet windows lasted 338.69 and 286.36 seconds, with 9620 and 8269 RAF
callbacks. Both 30-second hidden intervals had zero callbacks/pose updates. The
largest sampled full-motion callback gap was 9.038 seconds, within the authored
quiet/blink interval range. This diagnostic threshold does not exclude shorter
stutters; mutation distributions retain the <100 ms limit described above.
Memory at the first quiet boundary was 233.65 MiB and at the final boundary
223.98 MiB. These observations do not establish multi-day or leak-free endurance.

This successful repeat required **no native foreground activation**. The earlier
interrupted run's activation and fullscreen-paused intervals are preserved with
that run, not applied to this one. The successful repeat does not explain the
earlier target closure. Evidence: `soak-report.json`, `soak-run.log`, the read-only
`soak-midpoint-observation.json` and generated `summary.json`. The measured binary,
native suite manifest and final executable hashes match. All test-owned NekoAFK
and OpenCode processes had exited after completion.

### Earlier runs and follow-up scope

The first complete corrected soak ran **1200.06 seconds**, with all ten integrity
checks passing and no runtime errors. Both 500-operation cycles drained exactly:
500 then 1000 passing test results, no open operations and no duplicate inflation.
Real OpenCode 1.18.35 restarted/reconnected; its real 70-second shell remained active
past 60 seconds. Actual `exit 7` still supplied only output metadata and correctly
remained unknown/unverified. Six immediate cancellations and session switching
during interrupted checks never produced a false success. This run precedes the
subsequently discovered claim-first snapshot correction above; its exact binary
identity is retained in the report.
That earlier report is `pre-heartbeat-fix/soak-report.json`.

Its aggregate sampled app-tree CPU was 9.584% of one core; one-second CPU samples
had p50/p95/p99 of 2.988/29.398/42.667%. Private memory started at 192.46 MiB,
fell as low as 178.67 MiB and ended/peaked at 251.19 MiB. This variability does not
establish either a leak or leak-free endurance. Both 30-second hidden intervals
recorded zero RAF callbacks and pose mutations. The last 289-second quiet interval
recorded only 764 callbacks/288 mutations, versus 10162/4579 in the earlier
338-second interval. Visibility/pause context was not sampled in that original
run, so intentional suspension versus a stall cannot be resolved from it. A
targeted follow-up and future soak samples explicitly record that context.

The final-build quiet follow-up completed **300.28 seconds** after an actual local
check, with verified status and connection preserved throughout. All 286 context
samples were full motion, visible and not desktop-paused. It recorded 9407 RAF
callbacks and 4189 pose mutations, no runtime errors, and no unexplained callback
gap above the 15-second diagnostic threshold. The largest callback gap was 9.391 s,
consistent with authored quiet/blink deadlines; sampled activities included
delight, wash, mote, listen, nest and rest. Mutation p50/p95/p99 was
34.7/36.2/69.6 ms (same <100 ms quantile limit). App-tree CPU was 10.99% of one core;
unique resident memory was 186.10 → 190.83 MiB, peak 197.90 MiB. This did not
reproduce the earlier sparse interval and cannot retroactively explain its missing
visibility context. Evidence: `quiet-report.json` and `quiet-run.log`.

The reports retain chronological stages, one-second resource/state samples,
observed counter integrity, mutation cadence, failures and executable identity.
API/polling gaps and short-lived-child limitations are disclosed above.
Application hide/resume is not OS sleep/wake; twenty minutes is not multi-day proof.

A subsequent final-build soak stopped at **1050.45 seconds** when Playwright lost
its WebView target (`TargetClosedError`). Both cycles had drained 500 then 1000
results with zero open operations; its last sample was verified, full-motion,
visible and unpaused. **This is not a passed 20-minute run.** The report did not
capture process exit status before cleanup, so app exit, WebView loss and external
interruption cannot be distinguished. Windows Application events 1000/1001 in the
14:44–14:48 local-time window contained no NekoAFK/WebView2 match; absence of an
event does not rule out a fault. Evidence is retained under `target-closed-soak/`.
The repeat harness now captures app/server/producer exit status and surviving
WebView children before cleanup if another failure occurs.

The first evening repeat timed out on OpenCode's initial `/global/health` request,
before Neko launched. The server was still running; this is not a native-app soak
result. Restarted short probes succeeded both with and without workspace context
(`server-health-probe.json`). The harness had used the 120-second long-command
request timeout inside a nominal 40-second startup loop. Health requests now use
three-second timeouts and bounded retries; real 70-second commands keep their
long timeout. The cold-start stall itself was not reproduced by those short probes.
The failed attempt remains under `startup-timeout-soak/` and is not counted passed.

## Ranked outstanding release gates

| Severity | Gate | Required evidence |
|---|---|---|
| P1 | Active graphics CPU/power and endurance resource acceptance | Repeated same-clip evidence and an agreed resource/frame-presentation budget; private-memory variability and longer stability require follow-up. No universal CPU or leak-free claim. |
| P1 | Unexplained native/WebView target loss | Attribute or reproduce the 1050-second target closure with process-exit evidence. A successful repeat alone cannot establish its cause. |
| P1 | Physical mixed-DPI drag/recovery and monitor loss | Two-monitor checklist with negative origins and different scales; one display available here. |
| P1 | Spoken accessibility and actual tray lifecycle | Narrator and notification-area/Explorer restart checks; axe/API registration alone are insufficient. |
| P1 | Fullscreen classification and OS sleep/resume | Actual exclusive graphics modes, ordinary maximized editors with taskbar auto-hide, and resume acceptance; current foreground-bounds detection and borderless native HWND tests are narrower. |
| P2 | Direct-shell numeric exit is absent upstream | Explicit unknown/unverified remains correct; failure-specific reporting needs a real signal, never parsed output. |
| P2 | Multi-day, RDP and slow/network workspace behavior | Endurance, reconnect and fingerprint-cancellation latency measurements. |
| P2 | History and external edits | Recovery covers bridge-observed sessions; counters are bounded/in-memory; proof is point-in-time and external edits are not continuously watched. |
| Release gate | Signing and clean-machine installation | Separate authorization and clean-machine/WebView2 acceptance; no installer built here. |

The release-candidate recommendation remains **NO-GO** while required human/hardware
gates and representative resource acceptance are outstanding. Automated success can
support an internal preview, not substitute for those checks.

## Reproduction and evidence layout

Run native suites serially on an interactive Windows desktop with no other
NekoAFK instance and no concurrent compilation. The local harness uses Python
Playwright/psutil, installed WebView2, Node and FFmpeg. The authentic soak reuses
the isolated OpenCode installation/configuration referenced by
`.artifacts/opencode-live-report.json`; those local prerequisites must exist.
Remote-debugging ports are test-launch environment settings, not new product APIs.

```powershell
cargo test --manifest-path src-tauri/Cargo.toml
cargo clippy --manifest-path src-tauri/Cargo.toml -- -D warnings
npm test
python tests/quality_wait_test.py
npx tauri build --no-bundle
node scripts/verify-character-preserved.mjs
python tests/quality_quiet.py --seconds 300
powershell -NoProfile -File scripts/final-quality-native.ps1
python tests/quality_soak.py --seconds 1200
node scripts/final-quality-summary.mjs
```

For paired profiles, use `tests/quality_native.py --name <label> --exe <path>
--repeats 3 --seed 1234`; add `--typing-only` for the 14-second keyboard entrance,
or `--diagnostics` for a separate trace/allocation sample. Preserve reports before
reusing names. The before binary and rejected prototype evidence are retained.

Evidence lives under `.artifacts/final-quality/`: `summary.json` is the index;
unit/build logs, raw paired profiles, diagnostic trace/allocation files, native
acceptance reports, quiet/soak reports and progress logs retain their detailed scope.
`pre-heartbeat-fix/` preserves completed acceptance from the preceding executable.
The native showcase is `character/neko-native-showcase.mp4`, captured from the
Windows compositor with the opaque capture preference. The separate
`character/native-default-transparent.png` covers the normal transparent surface.
Fixture-driven demonstrations are test evidence, not a claim that an AI model
performed those actions. Celebrations follow actual independent local checks.
