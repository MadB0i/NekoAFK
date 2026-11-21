# NekoAFK — refinement candidate v002

This is a versioned character and single-clip study, not a final production sign-off. Application files and the other animation states were not changed.

## Review files

- `NekoAFK-model-v002.blend`: incremental model/material refinements, existing skeleton, facial targets and optional sock collection.
- `NekoAFK-editing-v002.blend`: one eight-second skeletal/facial Action and NLA proof, `Neko_QR02_EDITING_PHONE_08s`. Frames 1–192 play at 24 fps; frame 193 is the duplicate loop endpoint.
- `NekoAFK-editing-v002-mtoon.glb`: self-contained barefoot/chair/phone runtime candidate. Uses `VRMC_materials_mtoon` for toon surfaces and standard glTF physical materials for lacquer, metal and props. This is a GLB, not a complete VRM avatar package.
- `renders/before-after.png`: side-by-side unretouched Blender renders, v001 left and v002 right.
- `renders/after-fullbody.png`, `after-face.png`, `after-nails.png`, `after-seated-feet.png`: full-resolution Blender evidence.
- `renders/free-hand-check.png`, `phone-grip-check.png`: actual contact close-ups.
- `renders/runtime-full.png`, `runtime-face.png`, `runtime-hand.png`, `runtime-feet.png`: actual Three.js/MToon captures.
- `renders/NekoAFK-editing-v002-runtime.mp4`: eight-second deterministic runtime-rendered playback, not an image crossfade or CSS animation.

## Refinements

Existing hair locks were locally smoothed and subdivided, with six tapered tip strands weighted to existing hair chains. The canonical amber streak remains. Excessive specular response and backface artifacts found during rendering were reduced. Facial adjustments are deliberately small and applied to all existing expression targets. Skin/eye shading is softer; the acrylics use a portable original black/amber gradient, clear coat and existing gold inlays. Ankle/instep surfaces and toe-joint weight transitions were refined without remeshing the skeleton.

The editing clip uses a continuous, restrained knee arc with ankle lag rather than repeated eased stops. Hips have constant translation. Head movement is smaller; the phone follows the hand; thumb strokes, blinks, ears, tail and hair overlap are independently authored. The resting palm follows the thigh contour. A localized **editing-only** Body corrective reduces phone/hoodie-cuff intersection; it is not a general-purpose body shape and must be disabled when authoring unrelated poses.

## Runtime findings

The previous Blender Shader-to-RGB material graph could not survive ordinary glTF export. This candidate preserves the actual maps, explicitly writes MToon extension fields, adds an original analytic satin-hair matcap, and tests the official pixiv MToon loader. No downloaded character assets were used. The only approved download was the renderer dependency tree, isolated under `runtime-preview/` (`three` 0.186.1, `@pixiv/three-vrm` 3.5.5, MIT licenses included).

Reference: https://github.com/pixiv/three-vrm/tree/dev/packages/three-vrm-materials-mtoon

`runtime-preview/index.html` is an asset QA viewer, not the desktop application. Serve this v002 directory and open `/runtime-preview/`. It has a time scrubber and full/face/hand/feet views. Standard GLTFLoader without the MToon plugin will not reproduce this appearance. Optional socks remain in the Blender source and original runtime files; this candidate exports barefoot only.

## Validation and unresolved limitations

Original canonical/v001 Blender files and both original animated GLBs are checked against SHA-256 snapshots in `audit/source-hashes.json`. Reimport retains 168 bones, all 57 facial targets, and tail/ear/toe chains. Runtime evidence checks the actual MToon material types, animation duration, morph values, bone samples and WebGL errors. See `audit/runtime-playback.json`, `roundtrip.json` and `new-motion-checks.json`.

This does **not** yet meet the Wuthering Waves reference bar. Hair still has dense VRoid clumps and a conspicuous crown; the tail silhouette and some seated cloth creases remain coarse. Runtime skin is flatter than the Blender art shader. The local phone/cuff check still detects approximately 1.1 mm of residual intersection at a few evaluated vertices in sampled frames. Extreme poses beyond the editing loop have not been certified. The roughly 48 MB export and high draw count need optimization before shipping; screenshot capture is not an FPS benchmark. Secondary motion is authored, not a newly implemented physical simulation.

## Reproduction

Use the installed Blender 5.2 and existing VRM add-on. In order: `refine_model.py`, `prepare_clip.py` (ordinary Python), `build_editing.py -- --no-stills`, `refine_hair_surfaces.py`, `finalize_contact.py`, `export_runtime.py`, `roundtrip_validate.py`, `capture_evidence.py -- after`. `prepare_clip.py` includes the final palm/thumb orientation. The earlier `refine_free_thumb.py` is an unsuccessful diagnostic adjustment and is **not** part of the final build.

`capture_evidence.py -- before` reads v001 without saving it. `validate_motion.py -- --audit` checks the Blender loop. `runtime-preview/check_runtime.py --video` uses the installed Python Playwright browser to capture every skeletal-animation frame; `assemble_evidence.py` arranges the actual Blender renders for comparison. No source image pixels are retouched.

No commits, pushes or backend/application changes were made.
