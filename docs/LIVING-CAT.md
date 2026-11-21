# Living cat desktop pass — 11 October 2026

## Audit and retained architecture

The starting mascot was the project's original 240-unit tuxedo SVG: a single
head group, body, tail and eyes. CSS looped head translation/rotation, tail
rotation and eye scaling. There were no articulated paws, props, authored
activities, activity selection, cooldowns or personality preferences.

The implementation retains Tauri 2, its three independent native windows,
single-instance behavior, tray, native dragging, persisted monitor placement,
click-through recovery, local atomic OpenCode spool and independent check runner.
No model downloads, replacement character, additional renderer, service,
listener or provider API key were introduced. Existing archives are untouched.

## Character and direction

`assets/cat.svg` is the original cat redesigned as an articulated vector rig:
midnight-purple fur, amber irises, shaded ears and face, white paw tips, cheek
tufts and a small gold collar charm. Gradients provide shading without raster
swaps, large textures or expensive blur filters. It stays sharp at 50–200% scale.

`src/director.ts` owns pure character behavior; `src/character.ts` applies poses
to the SVG. Head, ears, eyes/gaze, brows, mouth, paws, tail and root/body poses
are controlled separately. Authored poses contain anticipation, a held acting
section, individual gestures and a settled exit. Keyframes interpolate with
smoothstep. Props enter/exit with opacity and crossfade across interruptions.

## Two companions, one brain

A Settings preference selects between two rigs that share the same director and
the same 32-channel pose contract: **Nova** (`assets/robot.svg`, default) — a
floating midnight-plum robot with large amber LED eyes, side pods, an antenna,
a chest core and a hover pad — and **Neko** (`assets/cat.svg`), the original
cat. Both SVGs expose the identical renderer element ids; the tail channels
drive Nova's hover pad (bob and spread) instead of a bezier tail, and the face
constants (larger screen eyes, arc mouth) are the only other rig differences.
Switching the preference swaps the mascot markup at runtime and rebuilds the
renderer; the director seed, cooldowns and evidence state are unaffected.
Reduced motion, quiet-pose mutation suppression and the 30 Hz deadline behave
identically on both rigs.

The director uses a seedable xorshift generator, per-activity cooldowns,
no immediate repeats, and quiet gaps. The native renderer gets a fresh seed
at launch. Calm uses longer rests; Playful is default; Chaos shortens rests.
Priority: permission, verification, failure, verified result, uncertainty,
testing, detailed observed work, general busy, idle. Urgent events interrupt
immediately; lower priorities get at most 650 ms to settle. Pose blending takes
550 ms. The factual dock updates independently of the performance.

Rendering is limited to 30 updates per second. Hidden companions cancel their
animation frame. User reduced motion and the Windows media preference select
static expressive poses, with no ongoing animation timer. Rest periods have no
body bob or tail wag. Victory runs once for a stable verified result, then uses
happy idle behavior. Repeated errors use the consecutive failure streak;
a numeric successful tool exit resets that streak.

A bounded ledger remembers verified evidence tokens across session selection.
Selecting an already celebrated result does not replay victory, while a fresh
verified task can celebrate without inheriting the previous task's cooldown.

SVG attributes are cached and quantized below a visible subpixel to avoid
invalidating unchanged poses. The host suppresses identical snapshot broadcasts
while still polling for events and time-based source expiry. These optimizations
preserve the existing engine and three-window architecture.

## Activity mapping

| Observed state | Authored performances |
| --- | --- |
| Idle / offline / no recent activity | Catnap, full stretch, face grooming, chasing the tail |
| General busy, detail unavailable | Tiny phone, pencil play, fish daydream |
| Reasoning part observed | Chin-paw pondering, pencil consideration |
| Assistant text or editing tool observed | Keyboard with independent paw beats, checking a laptop, paw stretch |
| Test/build-like command observed | Attentive watch, popcorn, nervous crossed paws |
| Failed | Shock, unimpressed paw tap |
| Repeated failed tools | Facepalm, deliberate tail thumps |
| Pending permission | Look toward the user, wave, attention tap |
| Independent local check running | Magnifying glass inspection, reading evidence notes |
| Fresh configured check passed after a completion candidate | Celebration / paw flourish, then happy idle |
| Completion candidate or inconclusive check | Confused shrug, pondering missing evidence; no victory |

OpenCode events, not entertainment choices, set factual status. Reasoning is
recognized by a reasoning part type; assistant text requires an observed
assistant message role. Unknown/user text does not become writing. Part deltas
are rate-limited to one metadata update per activity per two seconds. Contents
are never forwarded. Build/test command classification is heuristic and is
labelled as such in evidence. A streamed reasoning part does not disclose or
interpret hidden thought contents.

Cancelled/timed-out checks, fingerprint changes and stale evidence are
inconclusive. An actual nonzero independent check is a failure. Permission
requests take display priority over a running check. Existing source/evidence
freshness and unfinished-task safeguards still gate celebration.

## Desktop polish

Settings keeps the existing warm-ivory native utility system and adds persistent
personality selection and a refined mascot preview. Accent text was darkened
after a native accessibility scan caught insufficient preview contrast. Motion
copy explains the system preference. The dock's evidence list now displays the
engine's newest-first order correctly; it had been reversed in the frontend.
Companion controls, scale, dock attach/detach, native window recovery and tray
remain on the existing paths.

Companion/dock mouse gestures now enter through one native command. Dock
detachment updates host state before mouse capture; it does not concurrently
apply preferences or write settings while Windows begins the move. Placement
and detach preferences use the existing deferred persistence loop.

## Validation and previews

Run `npm test`, `cargo test --manifest-path src-tauri/Cargo.toml`,
`cargo clippy --manifest-path src-tauri/Cargo.toml -- -D warnings`,
`python tests/native_smoke.py`, `node scripts/opencode-smoke.mjs`,
`python tests/opencode_live_desktop.py`, and
`python tests/living_cat_native.py`. Native suites must run serially because the
app intentionally allows only one instance.

Use `python tests/living_cat_native.py --keep-open` followed by
`python tests/rapid_native.py` to additionally verify a 62-event burst, permission
priority, zero SVG mutations for a still pose, and zero unchanged host broadcasts.

The pure director suite simulates two hours and rapid interrupts. Native tests
use isolated settings/workspaces, real WebView2 windows and test-only supported
OpenCode hook inputs. The separate live OpenCode test uses an actual OpenCode
1.18.35 session/shell without fixtures or model calls. The activity video is a
fixture demonstration, not a claimed model-driven coding session.

Preview and measurement files are under `.artifacts/living-cat/`; detailed
results and CPU/RSS observations are in `report.json`. The native capture uses
the Windows-composited window region, with the companion's opaque background
preference during video to exclude unrelated desktop content. Transparent alpha
is checked separately. Direct HWND GDI capture was rejected because it omitted
the GPU-rendered WebView2 content.

The final native video is 91.4 seconds at 600×600. Review `typing-native.png`,
`repeated-failure.png`, `permission.png`, `verifying.png`, `verified.png` and
`inconclusive.png` for character poses, `companion-transparent-native.png` for
alpha, and `settings-windows.jpg` / `dock-windows.jpg` / `companion-windows.jpg`
for Windows.Graphics.Capture exports. These are native previews, not mockups.
The report records whole-process-tree CPU and memory observations; see
`docs/VALIDATION.md` for their units and practical limits.

## Remaining limits

This is an authored 2D vector character. Sleep is a seated head tuck and tail
chasing is a planted-body pursuit; neither is a full body turn or locomotion.
The prop contact is stylized rather than an IK or physics simulation. More
nuanced silhouettes and hand acting remain valid visual iteration work.

Model-driven reasoning/editing/permission paths have contract and native fixture
coverage; the live OpenCode run proves session/shell transport and a real busy
performance returning to idle. Only one physical
monitor is available: mixed-monitor DPI transitions, unplugging a monitor,
fullscreen interactions and screen-reader acceptance remain unverified. Tray
registration/actions pass native IPC tests; physical notification-area menu
acceptance requires a separate user check.

Native dock detachment and mouse displacement were observed after retries.
The fast computer-use drag helper was inconsistent: final-build companion
displacement needs manual acceptance, despite successful native move/resize
regression checks. The two-hour director soak is simulated; the native busy
measurement spans 70 seconds, so hours-long desktop stability is unproven.

No installer, commit, push or release was produced in this pass. Passing tests
are not a visual quality score or release approval.
