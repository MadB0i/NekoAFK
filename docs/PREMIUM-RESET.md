# Desktop reset audit

October 11, 2026 (Asia/Calcutta).

## Cleanup

The HKCU, HKLM and WOW6432Node Windows uninstall registrations contained no
NekoAFK installation. There was no registered uninstaller to run. The earlier
isolated install/uninstall smoke test had already removed its registration.
No source, asset, configuration, user data or archive directory was deleted.

Removed only the obsolete generated installer after checking its identity:

- Path: `src-tauri/target/release/bundle/nsis/NekoAFK_0.1.0_x64-setup.exe`
- Product: NekoAFK; product version: 0.1.0; size: 2,164,952 bytes.
- SHA-256: `7C4BA1E6B96026AEC656D866E71A3254D8D637F8FFF69BA740481FF28A66125E`
- Confirmed absent after removal. No replacement installer was generated.

## Runtime root cause

The actual native settings window reproduced the unmanaged `host` error on its
first `get_snapshot` invocation. Tauri 2.12.2 creates automatic configured
webviews before calling the application's setup callback. `Host` was managed
inside that callback, after the webviews could load and invoke commands.

All three window configurations now set `create: false`. Setup loads persisted
configuration and manages the exact `Host` type required by command signatures,
then constructs the webviews. This fixes the order rather than hiding or
retrying the runtime error. A Rust configuration regression guard and actual
cold-start/restart native assertions cover the failure.

Native review also found minimized Settings failed to restore and minimized
geometry could overwrite a saved placement. Reopening now restores the window;
minimized and zero-sized geometry is ignored. Saved sizes use client dimensions
and are supplied before native window construction so window borders do not
accumulate across restarts. Hidden startup geometry is ignored as well. A native
restart assertion compares restored dimensions and persisted hidden-dock
placement. Recovery accounts for the non-client border when fitting a window
into a monitor work area.

Pinned companion windows temporarily step behind open Settings so they do not
cover its controls, then recover their saved pin behavior when Settings closes.
Visibility, rather than native parent focus, governs this policy: Windows can
report parent blur while focus moves into the Settings WebView child.
Pin changes also queue a normal (non-topmost) Settings raise after the native
window-thread updates. Changing a dock from topmost to normal can otherwise
place it over a Settings window that already has foreground focus.

## Presentation

Fresh launch shows the transparent companion alone. Settings has five focused
sections, semantic switches, inline validation, a persistent save/discard bar,
and warm white/charcoal/amber styling. The dock has independent pin, collapse,
attach/detach and hide controls. Continuous mascot motion can be paused.

The original lightweight cat asset is reused. Archived modeling work remains
untouched. The adapter/engine/verification boundaries and bridge privacy filter
remain intact. All user-facing activity is derived from observed local events.

## Acceptance

The current acceptance results and screenshot paths are recorded in
`docs/VALIDATION.md`. Physical mixed-DPI transitions require suitable hardware;
browser device-scale emulation is not counted as native mixed-DPI validation.
Installer generation remains gated on the outstanding acceptance checks.
