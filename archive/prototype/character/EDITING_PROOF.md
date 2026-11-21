# Editing / phone-scroll — quality gate 01

Open `/` or `/editing.html`. The other five states are outside this proof. No backend or native window integration was added.

## What runs

17 independently registered raster cutouts use the approved `neko-editing.png` as a shared source texture. SVG supplies extraction masks and joint transforms; it does not redraw the illustration. This is a cutout rig, not a whole-image translation or wobble. `editing-parts.js` is the single source of truth for joint pivots, parents, extraction paths and draw order. The original PNG is unchanged (SHA-256 `cd6500d853186828f041cf4a21081f7e0e77a54a63db3d4af7e47eaf9d6bd6fe`).

Parts: seated base, torso, upper leg, lower leg, swinging foot, resting foot/ankle, head, left ear, right ear, back hair, front hair, hair tips, tail, phone hand, thumb, eyes, mouth. Left/right ears mean screen-left/right. Chair pixels and the seated base have no animated transform. Upper leg stays fixed during this clip; the lower leg rotates from its own knee and the foot inherits that motion before applying a small ankle correction. Mouth is a separate registered layer, held neutral for this quiet pose.

`editing-rig.js` evaluates a deterministic 24-second clip from absolute time. There are no accumulated transforms or animation-state crossfades. All layers remain fully opaque; only the selected eye frame changes. `editing-surface.js` isolates this rig from the historical six-state renderer. Loading fails atomically back to the approved editing image.

## Motion budgets

| Part | Editing behavior |
| --- | --- |
| Chair / pelvis / upper leg | Fixed |
| Torso | At most 0.035° around seated support; zero root translation |
| Lower leg | Knee pivot (797,542), gentle ±1.65° swing plus 0.18° slow variation |
| Swinging foot | Inherits knee movement; independent ±0.20° ankle correction |
| Other ankle | Two eased 0.9° adjustments in 24 seconds |
| Tail | Independent slow sway, 0.95° plus 0.25° variation |
| Head | Slow ±0.22° tilt |
| Hair groups | Phase-delayed response to head/body, under 0.4° |
| Ears | Sparse, asymmetric twitches, about 1°; short settle |
| Phone hand / thumb | Four scroll gestures, ≤0.08° wrist and 1.8° thumb |
| Eyes | Five blinks; open → half → closed → half → open in 170 ms |
| Mouth | Independent layer, neutral |

Angles are source-space joint rotations, not percentages of a large global bounce. The active timeline pauses when hidden, when comparing the original, or when reduced motion is enabled. Scrubbing freezes playback; quarter-speed supports joint inspection.

## Debug and review controls

- **Rig debug** / **G**: live pivots, hierarchy connections, selected cutout bounds and selectable joint tree.
- **Clip position**: scrub the full 24 seconds. Current clip and exact time remain visible.
- **Compare approved original**: exact original in the same stage and at the same scale.
- **Pause** / **Space**, quarter speed, scale and transparency grid.

The character window contains no controls. The inspector lives in the development page. Debug bounds come from each extraction path, not the common PNG canvas.

## Support art and provenance

Built-in image generation created **editing-only** concealed repair and eye-frame derivatives. The only visible replacement pixels are small eye patches while blinking. Original head, face outside those patches, clothes, limbs, chair, hair and tail remain original-source pixels. Generated support art was saved into `assets/neko/rig/editing-v1/`; it is never loaded from a user-profile path. Exact prompts and files: [asset provenance](../assets/neko/rig/editing-v1/PROVENANCE.md).

A generated chair-only plate was rejected because its seat registration differed. A generated isolated lower leg was also rejected because its geometry drifted. Neither is used by the renderer. The renderer uses the original limb and the better-registered concealed repair plate, so it cannot expose a second generated foot.

## Validation / acceptance

Run `python prototype/tests/neko_editing.py` with the server on 5783. It checks only editing: immutable source hash, absence of other-state image requests, fixed chair/base/knee, exact inherited ankle attachment, all 17 joints, debug bounds/hierarchy, controls, reduced-motion and hidden lifecycles, failed-load fallback, and a complete live 24-second timeline. Screenshots and timeline samples go to `.artifacts/editing-proof/final/`.

Visually review both 1920×1080 and 1366×768, neutral and both knee extremes, every eye frame, thumb-scroll peak, resting ankle, and each ear twitch. Mask remnants and face seams found in the initial pass were corrected. Debug/technical checks do not confer production art approval: this remains the **editing-only review candidate**, and the other five poses remain gated. Its finite motion envelope is intentionally small; do not increase joint angles or change the pose without revisiting cutout overlap and concealed surfaces.
