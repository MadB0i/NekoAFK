# NekoAFK desktop animation lab

**Current gate: EDITING / PHONE-SCROLL only.** `/` opens the articulated editing proof. Use **Rig debug** (G), pause (Space), clip scrubbing and original comparison. [Editing proof and validation](character/EDITING_PROOF.md). Run `python prototype/tests/neko_editing.py` for this gate. Other poses are not being developed.

Run `node prototype/server.mjs`, then open http://127.0.0.1:5783.

- `index.html` / `editing.html`: editing-only quality gate.
- `editing-character.html`: transparent 17-part editing rig surface.
- `desktop-lab.html`: archived six-state development director.
- `character.html`: transparent character surface, without traditional UI.
- `dock.html`: separate compact telemetry surface.
- `room.html`: archived room reference; not the product direction.

[Desktop architecture](desktop/DESKTOP_ARCHITECTURE.md) · [34-part rig / asset handoff](character/RIG_PLAN.md)

The six approved raster images are unchanged. The editing proof uses masked original raster parts, concealed repair art and eye frames; the historical six-state renderer remains a fallback/scaffold. No native wrapper or backend is implemented.

Checks: `python prototype/tests/neko_desktop.py` and `python prototype/tests/neko_rig.py`. The older `neko_visual.py` applies only to the archived room.
