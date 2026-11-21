# Character and desktop experience polish — 13 October 2026

This pass preserves Astra's artwork, identity and all twelve authored performances.
It adds small, finite attention shifts during quiet rests and improves the existing
native dock and companion controls. No adapter, verifier, native window architecture,
diagnostic service, dependency, installer or release action was changed.

## Observed weaknesses and changes

The native baseline's activity timestamps wrapped their AM/PM suffix onto a second
line. Large unknown task counts competed with the factual state. Collapsing the dock
removed workspace context. Reading older activity was vulnerable to list replacement.
At minimum companion size, a CSS rule hid six of the eight menu actions.

- Quiet rest now occasionally shifts gaze with an existing blink, followed by a
  small head turn and ear response. The motion settles and holds until the next
  existing deadline. It does not track the pointer or manufacture agent activity.
  Calm reduces the amplitude; Playful is the default; Chaos increases it slightly.
- Authored breathing, blinks, tail/ear follow-through, props and all twelve clips
  remain intact. Attention is blended out through the existing interruption path.
  Permission, failure and inconclusive resting poses do not casually look away.
- Reported task counts are subordinate inline information. Timestamps stay on one
  line; long activity text can wrap. Collapsed mode retains a truncated workspace
  name. Expansion uses a short content reveal, disabled by reduced motion.
- The activity log preserves a visible row while new evidence arrives. A `Latest`
  button returns to the newest entry and focuses the list. Changing sessions resets
  the reading position. This affects presentation only, not evidence retention.
- The minimum-size companion menu scrolls instead of hiding controls. All eight
  actions remain in the keyboard order. Click-through exposes its current pressed
  state and a matching accessible name.

Source changes: `src/director.ts`, `src/main.ts`, `src/views.ts`, `src/style.css`.
`src/character.ts`, `assets/cat.svg`, the authored library and its sampler are
unchanged. `tests/director.test.mjs` adds finite-rest/sleeping and interruption
regressions; `tests/experience_native.py` adds native interaction and paired
measurement coverage. Test-only CDP rig access is not a shipped product API.

## Evidence scope

Evidence lives in `.artifacts/experience-polish/`. `before/` preserves the starting
executable and frontend sources. Its executable SHA-256 is
`9b1ad5850754032d26abf29c7b4cf28d102194affceb6792e005ef60b7777483`.
The candidate SHA-256 is
`940d3b69c2f6daf9a032128513e4ba43dc9af20697e02019ba44b63bbe690cf1`.

`before-inspection/` and `after-inspection/` contain real native WebView captures
and complete Windows-compositor recordings of all twelve performances. These
recordings directly select clips through test-only debugger access; they are rig
reviews, not coding-agent activity. The preservation report compares the complete
clip library and every sampled pose at 60 Hz with the original Astra baseline.

Physical mixed-DPI monitors, spoken Narrator, actual tray interaction/Explorer
restart, exclusive fullscreen, real sleep/hibernate/RDP and multi-day endurance
remain UNTESTED. See [NATIVE-HUMAN-ACCEPTANCE.md](NATIVE-HUMAN-ACCEPTANCE.md).
The previous [closure investigation](RELEASE-GATE-INVESTIGATION.md) remains valid:
the later recorded exit was orderly; the original uninstrumented incident remains
unclassified. This pass does not claim a crash fix.

## Matched performance

Three fresh native processes per build, fixed character seed 1234, same scale,
transparency and window visibility. Each run observes 60 seconds of natural idle,
14 seconds of the authored keyboard performance, 5 hidden and 5 reduced-motion.
No recording or build workload ran during the completed comparison. CPU sums the
native host and its child processes, expressed as percent of **one core**. No child
process appeared or retired within a measured phase. Memory is summed unique
resident memory (USS), not a private-commit measurement or an endurance leak test.

| Workload | Before CPU median (range) | After CPU median (range) |
|---|---:|---:|
| Natural idle | 10.61% (9.58–11.25) | 11.36% (10.92–12.16) |
| Keyboard | 22.80% (17.72–24.46) | 18.62% (18.46–22.27) |
| Hidden | 2.13% (1.22–3.04) | 1.53% (1.22–2.44) |
| Reduced motion | 3.06% (0.91–3.06) | 0.91% (0.91–1.52) |

Idle's modest added work is an expected cost of finite attention gestures, not an
optimization: median rig mutations rose from 673 to 716 over 60 seconds. Both
builds still spent about 37 seconds of that window in resting poses. Resting poses
can include blinks/attention, so this is not a claim of 37 seconds of zero work.
Typing ranges overlap; no CPU improvement is claimed. Idle USS medians were
204.94/206.25 MiB and typing 206.17/207.82 MiB (before/after).

During active pose updates, idle p95 was 35.7–35.9 ms before and 35.8–36.0 ms after;
typing was 35.8–35.9 / 35.6–35.7 ms. Idle p99 was 62.4–63.2 / 62.3–69.2 ms.
These are native DOM mutation intervals below 100 ms, excluding quiet gaps; they
are **not GPU presentation times or a full hitch distribution**. Hidden and
reduced-motion phases had zero RAF callbacks in all six runs. Reduced motion had
one initial still-pose mutation; hidden had none.

Raw results: `before-paired/report.json`, `after-paired-final/report.json`, and
`performance-comparison.json`. Earlier partial harness attempts are excluded.
One after attempt stopped because a Python variable shadowed `list`; the corrected
complete run is used above. There was no product change to fix that harness error.

## Validation

- Build and TypeScript check passed without bundling an installer; 19 JavaScript
  regressions passed. The character preservation check passed for `listen`, `wash`,
  `nest`, `mote`, `consider`, `keyboard`, `recoil`, `huff`, `beckon`, `inspect`,
  `delight` and `puzzle`, with unchanged artwork SHA-256
  `6818c8b4722414f8552a3c6f0b64381cf131f4c60137840113be5f7b194ee7c3`.
- Eight native interaction checks passed: preserved reading anchor (0.40 px shift),
  Latest/focus, session-switch reset, non-wrapping timestamps, collapsed workspace,
  all eight minimum-size controls, reduced-motion disclosure and dirty Settings
  preservation. See `after-ux-final/report.json` and its native screenshots.
- The complete before/after clip recordings were inspected through frame contact
  sheets across their entire duration, plus full-size native captures. Matched
  60-second natural-idle recordings show the finite gaze changes. There were no
  JavaScript page errors in either inspection or the six paired measurement runs.

- All 33 Rust regressions and two polling-harness tests passed. Final JavaScript
  rerun: 19/19. One restricted-filesystem run saw a temporary spool file in an
  atomic-file assertion; the normal host run passed with no adapter/test change.
  That failed log is retained as `unit-tests-sandbox-failure.log`; no product
  root cause or fix is inferred from it.
- Native character acceptance: 10 checks passed, no reported runtime errors.
  Includes rapid priority changes, repeated failure, no unverified victory,
  interruption of a visible keyboard prop, transparency, disconnect/recovery,
  hide/resume, personality persistence and both reduced-motion preference paths.
  The system preference is CDP-emulated; it is not a physical Windows toggle test.
- The separate 180.06-second continuing-work run passed, with 9.01% average CPU
  of one core. Its `private_*` fields are USS: 232.5 → 230.4 MiB, peak 232.5 MiB.
  Different seed/state history and dock visibility make this a separate short
  stability observation, not another before/after performance pair. No multi-day
  memory claim is made. See `character/native-acceptance.json`.
- Native desktop suite: four checks passed, covering real borderless HWND
  fullscreen suspension/pin restoration, keyboard/Escape and selected-session
  offline honesty while another bridge is live. See `desktop-report.json`.
- Native Settings/desktop smoke: ten checks passed, including native focus and
  stacking, saved geometry, attachment/visibility/scale, validation, independent
  verification pass/fail/cancel, axe scans and restart persistence. No console
  errors. The old menu assertion assumed every visible control fitted at once;
  it now requires all eight controls and verifies scroll reachability. The new UX
  suite independently verifies automatic keyboard scrolling. See `smoke-report.json`.
- Real OpenCode 1.18.35: busy state/performance, app restart during a real 70-second
  tool, continued pending operation after 65 seconds, server disconnect/reconnect,
  another real tool and session deletion passed. Zero model requests. Direct-shell
  `exit 7` still omitted numeric exit metadata; the app retained unknown/unverified
  status. See `opencode-report.json`, `opencode-recovery.json` and
  `opencode-real-native.png`. This is separate from the fixture showcase.

All tests used isolated app data. The final manifest records Windows 11 build
26200, executable/source hashes, video dimensions/durations and no remaining
test-owned native host or OpenCode server. The native WebView version was
154.0.4258.62, on one 125% display. No installer, commit, push, tag or publication.

## Preview guide

- `dock-before-after.png`: native dock screenshots, baseline left, candidate right.
- `idle-before-after.mp4`: matched 60-second native recordings, baseline left,
  candidate right. Fixed seed, natural idle after a labelled idle hook fixture.
- `character/neko-native-showcase.mp4`: 57.5-second Windows compositor recording.
  Busy, writing and permission are clearly identified test fixtures through the
  production bridge. Verification runs a real configured command; only its zero
  exit enables celebration. `character/showcase-timeline.json` records the states.
- `after-inspection/authored-rig-review.mp4`: complete review of all twelve
  preserved performances, selected directly by the test rig.
- `source-changes.diff`: frontend diff against the preserved starting sources.

Opaque companion backgrounds are used for readable compositor videos. Transparent
native rendering is tested separately. None of these videos are browser previews.

## Remaining limitations and gate

**GO for a supervised local daily-use trial; NO-GO for a public release candidate.**
This is an evidence-based scope recommendation, not a visual quality score.

| Priority | Open item | Classification |
|---|---|---|
| P1 | Physical mixed-DPI, spoken Narrator, actual tray/Explorer lifecycle, exclusive fullscreen, real sleep/hibernate/RDP | Untested human acceptance gates; not demonstrated failures. |
| P1 | Multi-day use and representative slower-hardware CPU/power budget | Untested; this pass adds three-minute activity evidence and bounded comparisons only. |
| P2 | Original uninstrumented closure and fatal WebView recovery experience | Historical unresolved risk; persistent diagnostics and prior injected-failure evidence preserved. The later orderly quit is not a crash. |
| P2 | Long-session subjective repetition | Twelve performances and quiet intervals remain; a short review cannot certify how every user feels after hours or days. |

The character still uses a seated, primarily forward-facing rig. The new attention
is intentionally slight and less legible at minimum size. At that size the complete
menu requires scrolling and covers part of the cat while open. Collapsed telemetry
shows workspace context but the full session selector remains in the expanded view.
These are retained presentation tradeoffs, not claims of new animation capability.

No confirmed product failure from this pass remains open. The native checks do not
replace the unchecked [human checklist](NATIVE-HUMAN-ACCEPTANCE.md), and no checkbox
there has been promoted to passed.
