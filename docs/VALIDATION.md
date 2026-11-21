# Desktop validation

Windows x64, October 11, 2026 (Asia/Calcutta). Tests target the actual Tauri
release executable and its WebView2 windows, not a browser preview. No commit,
push, release or replacement installer was produced.

## Passed

- TypeScript/Vite build and `tauri build --no-bundle`.
- Fifteen Rust tests and eleven director/OpenCode plugin tests. Formatting and Clippy
  pass with warnings denied. Archive verification matches all 1,028 original
  source/asset SHA-256 hashes.
- Cold launch and restart have managed command state before any webview is
  constructed. All three surfaces load without runtime banners or console
  errors. First launch shows only the companion.
- Native persistence, transparent companion pixels, nonblank animated cat,
  reduced motion, scale, independent pin settings, click-through and recovery,
  show/hide, dock attach/detach and collapse/expand. Tray registration succeeds.
- Saved client sizes survive restart without frame-height growth. Hidden and
  minimized geometry cannot replace the last visible placement. Reopening
  minimized Settings restores its prior size and position.
- Repeated dock-to-Settings opening preserves real Win32 stacking order after
  queued pin changes. Native pointer inspection confirms Settings is unobstructed;
  closing it restores both saved pin preferences.
- Real Windows system-menu movement and resizing were observed. Attached dock
  movement followed the companion. This is not counted as mouse-drag acceptance.
- Bridge installation, input validation and recovery, independent executable
  verification pass/fail/cancel, and incomplete tasks holding celebration.
  Explicit test fixtures cover editing, testing, failures, permission requests,
  completion claims and stale evidence. Production has no seeded live activity.
- Keyboard focus is visible and automated axe checks report zero violations
  across all three native surfaces and all five Settings sections.
- Actual OpenCode 1.18.35 loads the project-local bridge. A real session and
  shell command reach the Rust engine and native dock without fixtures, extra
  keys or model requests. Missing numeric exit metadata remains unknown;
  activity alone never becomes independent verification.
- Actual Windows display modes 1920x1080 and 1366x768, with native scale
  transition from 125% to 100%. All Settings sections and expanded dock controls
  fit without page or horizontal overflow. Original display mode is restored.

## Evidence

- `.artifacts/native-validation/report.json`: native startup, state, controls,
  accessibility, verification, persistence and geometry regression results.
- `.artifacts/opencode-desktop-report.json`: real OpenCode-to-desktop evidence.
- `.artifacts/native-validation/opencode-real-native.png`: real connected dock.
- `.artifacts/premium-validation/display-report.json`: actual monitor dimensions
  and DPI, window geometry, display acceptance limits.
- `.artifacts/premium-validation/companion-windows.jpg`, `dock-windows.jpg` and
  `settings-windows.jpg`: Windows.Graphics.Capture screenshots of native windows.
- `.artifacts/premium-validation/1920x1080-*.png` and `1366x768-*.png`: native
  WebView2 screenshots for both display modes, not viewport emulation.

The state/verification suite uses named test-only hook inputs in isolated data
and workspace folders. It is distinct from the real OpenCode transport test.
Native test CDP ports are test-process environment overrides, not production
listeners. Test processes are stopped after validation.

## Acceptance Still Required

- Physical mixed-DPI transitions between two monitors, monitor unplugging,
  fullscreen applications and Narrator. Only one monitor is available here.
- Final physical companion dragging and Windows notification-area menu
  interaction. Dock detachment and displacement were observed with native mouse
  input after retries. Companion and attached dock moved 69 physical pixels
  together before the atomic-drag refactor; final-build mouse displacement was
  inconsistent with the computer-use helper. Native move/resize and tray action
  commands pass, but complete physical acceptance remains pending.
- Fresh Windows/WebView2 bootstrap and installer acceptance after the UI gate.
  The earlier isolated installer test is historical, not approval for this build.
- Code signing and a release/update channel remain unconfigured. No installer
  is currently approved for generation.
- A model-driven OpenCode coding session was not launched. Real session/shell
  transport passes; the editing/test/permission/completion variants use contract
  and native fixture coverage, clearly separate from live evidence.

Completion candidates are assistant responses, not proof every requirement is
done. Independent success is limited to the user's configured local command and
the source/evidence freshness safeguards documented in README.md.

Codex/Claude Code adapters, external character packs, VRM/GLB rendering, Windows
autostart and global shortcuts remain future work, not prerequisites for the
current OpenCode desktop app. Existing assets and archives remain preserved.

## Living-cat pass

The final articulated cat build passes 15 Rust and 11 JavaScript tests,
TypeScript/Vite, Rust formatting, Clippy with warnings denied, and the native
regression suite. The director runs a reproducible **simulated** two-hour test;
the native sustained-activity sample is **70 seconds**, not an hours-long soak.
The actual native 62-event burst settles on pending permission, and unchanged
still poses produce zero SVG mutations and zero host snapshot broadcasts.
User/system reduced motion, hide/resume, bridge disconnection/recovery,
verification cancellation, fresh-evidence celebration and three personality
preferences pass. Native axe scans report no violations; no runtime errors
were observed. Full Narrator acceptance remains separate.

`.artifacts/living-cat/neko-native-activities.mp4` is a **91.4-second**, 600×600
Windows-composited recording of the actual companion. Named hook fixtures drive
its activity sequence. It is not a model-driven coding session. The opaque
background preference keeps unrelated desktop content out of the recording;
transparent WebView2 alpha is separately verified and exported. Three
Windows.Graphics.Capture JPEGs and native WebView2 PNGs are in the same folder.

On this machine the nine-process app/WebView2 tree used 21.62% of **one CPU
core** during mixed activity at maximum scale, 13.32% at default scale, and
2.81% with reduced motion. These are short observational samples with different
activity mixes, not a controlled benchmark. Private working set was 279.4 MiB.
Summed RSS increased from 709.7 to 715.5 MiB, peaking at 720.9 MiB; that sum
counts shared pages repeatedly and is not private memory. Longer native memory
and stability testing remains necessary before release.

See `.artifacts/living-cat/report.json` for measured results and executable
SHA-256, and `docs/LIVING-CAT.md` for the audit, performances and event mapping.
No installer, commit, push or release was created.
