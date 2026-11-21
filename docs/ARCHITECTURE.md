# NekoAFK desktop

The Tauri 2 Rust host owns four real Windows WebView2 windows: `neko`,
`hud`, `telemetry`, and `settings`. The old prototype's independent character/dock
boundary, attachment policy, and tray recovery design are retained. Browser
simulation, confidence guesses, and the old rig are excluded from the product.

The small `hud` surface follows the companion's physical monitor work area and
avoids visible telemetry. It has no independent persisted placement or animation
loop. `src-tauri/src/progress.rs` derives one `Snapshot.progress` value for both
HUD and dock: observed tool/activity, explicit plan counts, connection context
and verification status. The existing character director continues to receive
factual engine states; plan counts never trigger celebration. See
[Live Progress HUD](LIVE-PROGRESS-HUD.md) for semantics and validation.

OpenCode's supported local plugin hooks normalize evidence into schema-v1
events. The plugin writes atomic individual JSON files to a per-user queue.
The host consumes, validates, deduplicates, and removes those files. No network
listener, model client, model credentials, prompt text, file contents, tool
output, or raw shell commands are transported. The queue is not a security
boundary against other programs running as the same Windows user.

Sessions are isolated by workspace + session ID. The UI selects a session
explicitly and never merges their tasks or failures. A heartbeat establishes
plugin availability separately from work activity. Silence never means success.
Todo counts are agent-reported. Shell commands are classified heuristically as
test activity; only observed numeric exit metadata establishes tool pass/fail.
Assistant terminal messages are completion claims, not proof of correctness.

Verification runs the user-configured executable and argument array in the
configured workspace. It is independent of the agent. An empty verification
command cannot succeed. A workspace fingerprint and evidence revision guard
against celebrating a stale check. Timeouts, cancellation, missing executables,
nonzero exits, and files changing during verification all prevent celebration.
Success means only that the configured check passed, not that every requirement
was proven. stdout/stderr remain local in a bounded log, never an agent prompt.

Settings use a native atomic replacement file in the app local data directory.
Invalid files are preserved and reported. Native window positions and sizes are
saved separately from user preferences; offscreen windows are recovered against
the available monitor work areas. Close hides to tray. Tray recovery restores
all surfaces. Single-instance startup opens the existing settings window.

Future adapters can produce the same normalized evidence. Codex and Claude Code
are extension points, not bundled integrations. Character renderers consume
only state + preferences; a future character-pack manifest may supply canvas,
VRM, or GLB implementations. Those formats are not required or loaded today.

References: https://opencode.ai/docs/plugins/ and https://v2.tauri.app/learn/system-tray/.

## Living character layer

`src/director.ts` selects seeded authored performances from factual state and
preferences; `src/character.ts` renders the articulated SVG. Entertainment never
modifies the engine or suggests unobserved agent progress. Reasoning and assistant
text parts are mapped only when their metadata is observable; general work stays
busy. Tests/builds remain heuristic classifications. Consecutive failure evidence
selects stronger reactions. Cancelled, timed-out and stale checks are inconclusive.
The factual dock and playful performances remain separate. Rendering caches
attributes to avoid repeated SVG invalidation; hidden windows suspend animation,
and reduced motion selects still poses. See `LIVING-CAT.md` for the full map and
native acceptance evidence.
