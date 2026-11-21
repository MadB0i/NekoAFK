# NekoAFK — quality reset v001

This is a versioned visual and motion study, not approval to rebuild the other states.

## Source

- `NekoAFK-model-v001.blend`: model/material refinements, original skeleton and face expressions, barefoot default and optional socks.
- `NekoAFK-editing-v001.blend`: one 8-second, 24 fps Action/NLA proof, `Neko_QR01_EDITING_PHONE_08s`. Frame 193 is the duplicate loop endpoint; playback/render uses frames 1–192.
- The original canonical Blender source and both animated GLBs were checked with SHA-256 and remain unchanged. See `audit/originals-preserved.json`.

## What changed

- Curved, solid almond acrylic nails with black-to-amber UV gradients, physical clear-coat highlights, separate gold filaments and proximal folds. Short rounded pedicure plates use the matching palette.
- Smoothed finger surfaces, wrist continuity under the hoodie cuffs, local foot topology cleanup, softer toe/heel/ankle surfaces and a small medial-arch refinement. Global automatic foot remeshing was rejected because it removed toe detail.
- Original identity textures retained. Softer toon light ramps, physical highlights, warm skin shading, restrained cheek/lip color, darker brows, amber eye reflections, reduced hair glare, softened clothing/cuffs, and a metal hair clip.
- Corrected imported forearm bone-roll handling. Arm targets now use the elbow direction and the imported rest matrices. The free hand rests over the thigh; the phone follows the actual hand frame.
- Two short thumb-scroll beats, reading holds, a small smile, a glance, three blinks, a decelerating knee swing, ankle/toe relaxation, independently phased tail joints, one ear twitch, and restrained head-driven hair overlap. Hip translation is constant.
- A localized Body shape key, `QR01 • phone-grip contact corrective`, reduces thumb contact clipping in this specific pose. Set it to **zero** when authoring other states; it is not a universal body-shape change.

## Actual rendered evidence

- `renders/NekoAFK-editing-v001.mp4` — final 8-second proof.
- `renders/NekoAFK-old-vs-v001.mp4` — simultaneous old/new comparison, matching camera and 8-second duration. Old Action, model and lighting remain unchanged.
- `renders/fullbody-three-quarter.png`
- `renders/face-closeup.png`
- `renders/hand-nails-closeup.png`
- `renders/seated-leg-foot.png`
- `renders/phone-contact-closeup.png`
- `renders/ankle-toe-deformation-check.png` — temporary deformation pose, not another animation.

## Quality limits

The result improves the previous prototype but does not yet match the Wuthering Waves reference bar. Hair-card silhouettes and some hoodie/hand deformation still reveal the underlying VRoid construction. This is a candidate for visual review, not a final production-quality sign-off.

The EEVEE toon shader uses Shader-to-RGB and is **not** a validated Three.js shader. No degraded PBR-only GLB is presented as a finished runtime version. Existing GLBs were preserved. A renderer-matched toon implementation and art review remain necessary before runtime replacement.

The contact check found up to two evaluated skin vertices approximately 1.1 mm inside the curved phone case after the local corrective, at sampled frames. The close-up is provided so this is not hidden behind a numeric pass label. Foot clearance in the authored loop remains positive; hips and phone attachment do not drift. See `audit/new-motion-checks.json` for the measurements.

## Reproduction

Use Blender 5.2 with the locally available VRM add-on. Run `build_model.py`, `build_editing.py`, then `finalize_contact.py` in order. `render_validate.py -- --audit` checks the resulting clip; without that argument it renders the final PNG sequence. `capture_details.py` renders the detail evidence. `render_old_comparison.py` reads the original animation library without saving to it.

All generated work stays in this versioned character directory. No application code, backend integration, commits or pushes are part of this pass.
