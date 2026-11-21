# NekoAFK — Windows desktop companion

## Product boundary

Neko is the product surface. The browser is an animation lab, not the final application. Desktop targets: 1920×1080 and 1366×768. No mobile layout or backend integration in this pass.

Three entry points now exist:

| Entry | Role | Ships as a native surface later? |
| --- | --- | --- |
| `character.html` | Transparent, UI-free seated Neko; stable contain stage; raster fallback or layered rig | Yes: frameless character window |
| `dock.html` | Compact telemetry with details, attach/detach and hide | Yes: independent frameless dock |
| `index.html` | Desktop work area, state director, scale, window placement and transparency/click-through previews | No: development only |

`room.html`, `room.css`, `room.js` preserve the earlier room study for reference. Remove the desk, monitor, wall decorations, vignette, bubbles, large telemetry panels and room navigation from the desktop product. Keep Neko, her gold-trim chair, transparent art, state vocabulary, restrained plum/amber colors and concise telemetry. The chair stays part of the character, with independent fixed layers in the future rig. The room does not constrain desktop character placement.

## Character window

No title bar, toolbar, card, labels, state buttons or speech bubble. Transparent HTML and background; full seated silhouette, safe space for success arms/ears; no whole-character floating or dimming. Default lab window is 600 logical pixels tall, scaled to fit the desktop work area. One registered canvas controls every state; source-alpha bounds and chair floor landmarks are retained. Scaling preserves bottom-center registration until a work-area edge requires clamping.

The lab supports drag, 65–125% scale, hide/show and click-through preview. Controls remain outside the character surface. Click-through preview only changes browser pointer handling; it does NOT pass clicks to other desktop applications. It resets on reload so recovery stays easy. Rectangular hit testing is currently used; transparent pixels are also draggable.

## Telemetry dock

260 logical pixels wide, about 162 high collapsed; expands for three short activity lines. Example: `OpenCode · TESTING`, task fraction, failure count, approximate confidence + confidence label. Separate character and dock sizing means telemetry does not shrink with Neko. No activity feed over the face.

The dock follows alongside Neko by default, and can be detached by dragging its header or choosing the attach control. It can expand, collapse and hide. The lab controls recover hidden windows. State samples live exclusively in `simulation/states.js` and are explicitly labeled simulated by the director. There is no agent connection.

## Host boundary and future Tauri adapter

`surface-bridge.js` contains a small transport contract. Surfaces request `drag-start`, `drag-move`, `drag-end`, `dock-hide`, `dock-attach`, and intrinsic dock `resize`. The host sends `state`, `preferences`, and `renderer-request`; the character returns renderer status. Browser messages validate same origin and the expected window source.

`BrowserDesktopHost` owns virtual bounds, scale, visibility, dock attachment and preferences. It persists placement/scale in localStorage and clamps windows into the lab work area. No OS capabilities are advertised: native windowing, always-on-top, tray, global hotkeys and multi-monitor remain false. Attached dock placement prefers the left, then right, with clamping; users may intentionally overlap windows after dragging.

Next native shell: Tauri with **two** independent Windows webview windows (`neko`, `telemetry`), loading these surface entry points, both transparent and without decorations. A `TauriDesktopHost` adapter replaces parent messaging with scoped Tauri events/commands; character rendering does not import Tauri. A settings/tray route owns native preferences, never the character DOM.

| Native concern | Adapter responsibility |
| --- | --- |
| Drag | Native `startDragging`, not repeated JS `setPosition` |
| Always-on-top | User preference through `setAlwaysOnTop`; dock policy independent |
| Click-through | `setIgnoreCursorEvents`; enable only with a working tray/hotkey recovery path |
| Tray | Show/hide Neko, dock, input mode, settings, quit |
| Scale | Persist logical size and floor anchor, resize window and stage together |
| Multiple monitors | Store monitor identifier + logical offset; convert physical coordinates using each monitor's DPI; allow negative OS coordinates; clamp to available work area on unplug |
| Hotkey | Native global shortcut for hide/show/recover input, optional configurable binding |
| Lifecycle | Pause procedural animation while hidden; dispose listeners; stop timers on close |

These native features are **planned, not implemented or tested here**. API basis: [Tauri window API](https://tauri.app/reference/javascript/api/namespacewindow/), [window customization](https://tauri.app/learn/window-customization/). Validate Windows transparency, WebView2, DPI changes and actual click-through on-device when the adapter is built.

## Animation and next implementation step

See [rig handoff](../character/RIG_PLAN.md). V2 expands the earlier 28-slot rig to 34 parts, with independent upper/lower legs, feet, hair groups, phone and thumb. Separate registration, static pose, one-shot entry gesture, and procedural motion wrappers prevent transform accumulation. Chair/root never participate in breathing or celebration.

The exact next step is an **artist-approved editing rig export**: full chair, pelvis, separated thighs/shins/feet with covered knee/ankle overlaps, torso, arm/hand/phone/thumb layers, clean head, eye frames, ears, hair and two tail segments. Test knee swing → inherited foot motion → occasional ankle correction at actual desktop scale. Approve that loop before authoring the other five expression/pose sets. Do not cut rectangular parts from the flattened PNGs or fill missing anatomy with improvised shapes.

Only switch the default renderer after all six poses, blink variants and motion envelopes are supplied and visually approved. Until then the immutable originals stay as static 300 ms state-fade fallback. No stock placeholder art or fake whole-image idle animation is shown.

## Validation

Run `node prototype/server.mjs`, then `python prototype/tests/neko_desktop.py` and `python prototype/tests/neko_rig.py`.

The first checks both desktop targets, every state, source artwork hashes, transparent character background, no controls or whole-PNG animation, complete ten-second sequences, drag, scale, hide/show, dock details and persistence. Evidence is in `.artifacts/desktop-validation`. The second uses test-only pixels to verify rig mechanics, preload/fallback, blink, hierarchy and lifecycle. Synthetic tests establish mechanics, not animation quality with missing art.
