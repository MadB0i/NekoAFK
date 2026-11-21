# Windows human acceptance — final quality gate

The [live progress HUD report](LIVE-PROGRESS-HUD.md) adds a fourth small native
surface. Its programmatic single-monitor edge positioning, keyboard controls,
reduced motion and accessibility scan are automated evidence only. The following
HUD-specific human checks remain **UNTESTED**:

- Drag the companion across physical monitors at different DPI scales in both
  directions, near every edge and with an attached or detached visible dock.
- Listen with Narrator while switching sessions, opening/closing telemetry,
  receiving permission requests, reconnecting and collapsing/expanding the HUD.
  Confirm that announcements are understandable and not duplicated.
- Use the real notification-area menu to disable/restore the HUD and recover
  click-through windows; test after Explorer restarts.
- Enter and leave a real exclusive-fullscreen application. Confirm the HUD yields
  and returns without taking focus. Repeat after actual sleep/hibernate and RDP.
- During the planned 2–3 hour daily-use trial, record build hash, workspace,
  disconnects, unexpected closures, resource growth and any misleading status.
  Automated short runs do not establish this trial or multi-day stability.

Unchecked items below are **not passed**. Automated accessibility scans, native
window fixtures and API calls do not substitute for these physical/spoken checks.
Record Windows/WebView2 versions, monitor layout/scales, build SHA-256, observer,
date, actual result and evidence path for every completed case. Use an isolated
workspace and configured local verification command. Never treat agent claims or
unknown shell exits as independent proof.

## Evidence already available

The [experience polish report](EXPERIENCE-POLISH.md) records the current candidate's
native keyboard scrolling at minimum companion size, activity reading preservation,
session-switch reset, collapsed context and repeated desktop/Settings/OpenCode checks.
These are automated native tests on one 125% display. They do not complete any of
the physical/spoken/manual cases below.

Focused follow-up: [RELEASE-GATE-INVESTIGATION.md](RELEASE-GATE-INVESTIGATION.md).
The new native lifecycle tests verify second-instance routing, repeated hide/show,
normal command-driven quit, injected renderer/browser/host termination diagnostics
and process suspension/resumption. These are automated cases; they do not pass any
physical notification-area, spoken, multi-monitor or actual sleep/hibernate item.
The repeated soak target closure was an orderly quit; the original uninstrumented
incident remains unclassified. No checkbox below is changed to passed.

| Area | Classification | Evidence / scope |
|---|---|---|
| Single-monitor native mouse drag at 125% | Native pointer automation in the preceding engineering pass; not human hardware acceptance | `.artifacts/engineering/physical-*-final.json`, companion/dock Windows captures; companion moved and dock followed; dragging dock detached it. Final-pass cross-monitor behavior is not established. |
| Keyboard, axe, persistence, focus/stacking, scale controls | Automated native WebView2 acceptance | `.artifacts/final-quality/native-smoke-report.json`; the serial suite manifest records the executable hash. |
| Borderless native fullscreen, pin restore, keyboard menu | Automated native HWND fixture | `.artifacts/final-quality/native-desktop.json`; excludes exclusive graphics modes. |
| Named native accessibility controls | Native UI Automation inspection in preceding pass | `.artifacts/engineering/*-native-accessibility.txt`; excludes spoken output. |
| Display-mode changes on one monitor | Automated native display acceptance in preceding pass | `.artifacts/premium-validation/display-report.json`; excludes physical mixed-DPI crossings. |
| Reduced motion | Automated saved-app preference and CDP-emulated WebView media preference | Final native character report records the method. This does not mark the physical Windows Settings toggle or spoken accessibility case passed. |

No human-performed manual acceptance result is claimed in this pass. Prior native
pointer and accessibility inspection evidence is retained with its actual scope.

## Physical mixed-DPI monitors — UNTESTED

- [ ] Use two physical monitors at different scales (for example 100% and 150%),
  including a negative screen origin. Drag companion slowly, quickly and with a
  very short press across each boundary in both directions. The pointer remains
  attached, geometry does not jump or grow, and the artwork stays crisp/unclipped.
- [ ] Repeat with attached dock, detached dock, collapsed dock, click-through
  toggled, minimum/maximum pet scale and each pin preference. Dock following must
  not fight an intentional dock drag; dragging detaches it.
- [ ] Save placements on each display, quit/restart, then unplug the display that
  owns the windows. Recovery must bring all requested windows into an available
  work area without losing preferences. Repeat after moving taskbars/changing the
  primary monitor and after reconnecting the display.
- [ ] Open Settings from the companion and tray on either monitor. Settings must
  gain focus, remain reachable and retain a visible keyboard focus indicator.

## Spoken Narrator — UNTESTED

- [ ] Start Narrator and traverse companion menu, dock and every Settings section
  using Tab/Shift+Tab, Enter/Space, arrows and Escape. Controls have understandable
  names/states; no trap or unexpected focus loss; validation errors are announced
  and focus reaches the invalid field. Unsaved input survives telemetry updates.
- [ ] Listen through idle, observed work, permission, failure, cancellation,
  disconnected, claimed, verifying and independently verified states. Announcements
  must reflect evidence, avoid repetitive unchanged status, and distinguish an
  inconclusive check from failure/success.
- [ ] With two OpenCode instances, disconnect the selected session during a
  permission wait. Narrator must expose both pending permission and offline status;
  another live bridge must not make that selected session sound connected.
- [ ] Enable Windows reduced motion and the app preference separately. Character
  motion stops while factual expressions/status remain available to Narrator.

## Real notification-area/tray lifecycle — UNTESTED

- [ ] Cold start, launch a second instance, hide all windows, recover via tray,
  toggle companion/dock/click-through/pins and open Settings. Exactly one usable
  icon remains; menu state/actions are clear and focus behaves consistently.
- [ ] Exercise left click, right click, hidden-icon overflow and keyboard access
  to the actual notification area. Confirm no lost icon or unreachable companion.
- [ ] Restart Explorer during use; verify icon recovery. Quit from the tray while
  verification has children running. The icon and app processes must disappear,
  children terminate, and the next launch must recover preferences correctly.

## Exclusive fullscreen and OS resume — UNTESTED

- [ ] With taskbar auto-hide enabled and disabled, compare ordinary maximized
  editors/browsers, borderless fullscreen and exclusive fullscreen. Record any
  unwanted suspension of the companion during normal coding. Current detection
  uses foreground-window bounds, so this distinction needs actual desktop evidence.
- [ ] Enter/exit an exclusive DirectX application on each display; Alt+Tab,
  minimize/restore, and change its resolution. Companion/dock must yield visibility
  and pinning, pause motion, then restore saved behavior without changing factual
  agent status or stealing game/Settings focus. Repeat with pins disabled.
- [ ] Sleep/hibernate and resume during a real long tool and a permission wait.
  Confirm stale connectivity is not presented as current, reconnect restores only
  observed context, and no false completion/celebration occurs.
- [ ] Repeat over remote desktop and reconnect. Record limitations rather than
  assuming local borderless-window results apply.

## Endurance and clean-machine gate — UNTESTED

- [ ] Run a multi-day workload with agent/server restarts and occasional monitor
  changes; record CPU, private memory, handle/process counts, event loss and UI errors.
  Compare warm-state memory at the same repeated workload boundary.
- [ ] On representative slower hardware, check sustained active animation and
  high-frequency events against an agreed CPU/power/frame-pacing budget.
- [ ] After separate release authorization, validate signing, clean-machine WebView2
  bootstrap, installation/update/uninstall. This task does not build an installer.

## Result record

| Case | Observer/date | Build/Windows/WebView2 | Hardware/scales | Actual result | Evidence | Follow-up |
|---|---|---|---|---|---|---|
| Pending | — | — | — | UNTESTED | — | — |
