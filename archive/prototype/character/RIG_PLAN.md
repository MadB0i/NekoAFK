# Neko articulated rig v2 — desktop asset handoff

**Scope update:** the editing-only proof now runs separately with 17 original-texture cutouts and generated concealed/eye support art. See [EDITING_PROOF.md](EDITING_PROOF.md). The six-state plan below is historical; the other five states remain gated and no new assets for them have been created.

## Status and scope

This supersedes the room-oriented v1 plan. Use web-native transparent PNG parts, DOM joint chains and a small motion scheduler. No Live2D, Spine or backend. The approved six raster originals are unchanged. They flatten chair, anatomy, hair and facial features; no safe automatic cutting can recover hidden shoulder/scalp/knee pixels. No layered artwork currently exists. The v2 manifest is intentionally `approved: false` with empty variants/pivots.

The desktop architecture is documented in [DESKTOP_ARCHITECTURE.md](../desktop/DESKTOP_ARCHITECTURE.md). Keep dark plum hair/hoodie, amber eyes, cat clip and ears, pale cat socks, warm rim light and the gold-trim chair. Preserve identity; export independent parts from an approved layered source with hidden joint overlap coverage.

## Exact layer list

`near` / `far` refer to camera depth. This is default back-to-front order; all six poses can explicitly reorder the same slots.

| # | PNG layer ID | Joint attachment |
| --- | --- | --- |
| 1 | chair-back | root |
| 2 | chair-base | root |
| 3 | tail-root | tail-root |
| 4 | tail-tip | tail-tip |
| 5 | hair-back | hair-back |
| 6 | neck | body |
| 7 | torso | body |
| 8 | arm-far-upper | arm-far |
| 9 | arm-far-lower | forearm-far |
| 10 | hand-far | hand-far |
| 11 | pelvis | pelvis |
| 12 | leg-far-upper | thigh-far |
| 13 | leg-far-lower | shin-far |
| 14 | foot-far | foot-far |
| 15 | leg-near-upper | thigh-near |
| 16 | leg-near-lower | shin-near |
| 17 | foot-near | foot-near |
| 18 | chair-arm-far | root |
| 19 | head-base | head |
| 20 | ear-far | ear-far |
| 21 | ear-near | ear-near |
| 22 | eye-far | head |
| 23 | eye-near | head |
| 24 | brows | head |
| 25 | mouth | head |
| 26 | hair-front | hair-front |
| 27 | chair-arm-near | root |
| 28 | arm-near-upper | arm-near |
| 29 | arm-near-lower | forearm-near |
| 30 | hand-near-back | hand-near |
| 31 | phone | phone |
| 32 | hand-near-front | thumb-near |
| 33 | hair-lock-near | hair-lock-near |
| 34 | expression-accent | head |

The 34 slots may have multiple art variants. Four chair pieces stay fixed. `head-base` contains face skin/nose but no eyes/brows/mouth/ears. Each eye requires expression-matched open/half/closed variants, not a scale-to-zero blink. Ears need upright and flattened silhouettes. Hand and arm variants cover seated grip, lowering phone, annoyance and raised celebration. `hand-near-front` is the separate thumb overlay. Hair-back/front/near lock require hidden overlap. Two tail pieces need fur overlap at the joint. Pelvis contains pants/hip fabric, not baked shins or feet. Every thigh/shin/foot pair needs overlap that survives knee and ankle rotation; far leg may remain still. Phone art must remain separate from both palm and thumb; scrolling finger motion is supported, scrolling phone-screen content would require a later optional screen insert.

## Skeleton / pivots

```text
fixed stage / floor
├── chair parts (no motion)
├── pelvis → thigh-near → shin-near → foot-near
│          → thigh-far  → shin-far  → foot-far
├── tail-root → tail-tip
└── body (seated hip pivot)
    ├── head (neck pivot)
    │   ├── ear-near / ear-far (ear roots)
    │   └── hair-back / hair-front / hair-lock-near (hair roots)
    ├── arm-near → forearm-near → hand-near
    │                             ├── phone (grip)
    │                             └── thumb-near (thumb base)
    └── arm-far → forearm-far → hand-far
```

Use shoulder, elbow, wrist, hip, knee and ankle pivots from the actual illustration. Nodes are expressed in shared source coordinates, never guessed from rectangle centers. Nested full-canvas wrappers let feet inherit knee rotation naturally. Draw slots duplicate their ancestor transforms so each state can change occlusion without breaking attachment.

Wrappers: stage placement → shared contain registration → per-part static pose → per-part one-shot gesture → per-part procedural motion → trimmed image. Every frame assigns absolute transforms from time; no additive DOM transform accumulation. Chair and root never bob. Head eyes follow the head art; gaze changes use expression variants rather than sliding eyes off the face.

## File contract

```text
assets/neko/
  neko-editing.png ... neko-success.png   # immutable fallback originals
  rig/v1/manifest.json                    # historical, no longer active
  rig/v2/
    manifest.json
    parts/<layer-id>--<view>.png
    expressions/<eye-or-brow-or-mouth>--<expression>--<frame>.png
```

Examples: `parts/leg-near-lower--seated.png`, `parts/hand-near-front--phone-scroll.png`, `parts/arm-near-upper--raised.png`, `expressions/eye-near--skeptical--closed.png`. Lowercase kebab-case, transparent RGBA, no baked background or room light overlays. Export at source resolution without stretching.

Canonical canvas: **1274 × 1491**, floor **(637, 1418)**. Original visible alpha bounds and chair-contact landmarks determine this shared envelope. Trim exports; each variant stores `src` relative to manifest and `rect: [x,y,width,height]` in the shared canvas. Natural PNG dimensions must exactly equal rect width/height. Common nodes carry `[pivotX,pivotY]`; pose variants must be re-registered onto those pivots. A substantially different projection requires authored variant art, not extreme rotation. Art and all transformed motion extrema must fit the canvas; static rect validation alone cannot prove that moving joints fit. Review/export with safe overlap and test all extremes before approval.

Manifest v2 requires all 34 slots, all six complete `views` and `order` maps, `rotations`, and blink triplets. Only phone, thumb overlay and expression-accent may be explicitly hidden with null. Rotations are absolute final joint angles (validation maximum ±90°, not a recommended motion amplitude). Optional `entry` clips contain duration 200–1400 ms and tracks `{node, keys:[[normalizedTime, degrees], ...]}`. Times increase 0→1; each track must end at zero; offsets max ±25°. Entry curves use smoothstep interpolation and play once per actual state change. Re-selecting a state does not re-trigger it. Proposed curves in the unapproved scaffold are starting budgets, not artist-approved animation.

## Procedural vs state-authored animation

| State | Continuous part motion | Authored pose / one-shot |
| --- | --- | --- |
| editing | Near shin ±2.4°, foot inherits; ≤0.45° ankle; sparse thumb scroll; tail sway; tiny hair lag, breathing, blink and ear twitch | Natural seated phone grip, one lower leg free to swing |
| testing | Knee amplitude settles to 15%; calmer body; blink | Head/gaze activity-facing, perky ears, slightly lowered phone |
| failed | Knee settles to still; tail loop stops; restrained breathing/blink | Flattened ear variant; one 500 ms tail thump |
| frustrated | Legs still; no repeated tail agitation | Annoyed face, hand/head posture; stronger 750 ms tail/forearm reaction |
| verifying | Legs still, quieter hair/breathing | Phone down, torso forward around hip, skeptical eyes |
| success | Gentle breath/blink if open-eyed, low tail sway | Raised arm/hand variants and 950 ms independent arm/forearm celebration; no chair/root bounce |

Current scheduler: body breathing ≤1.2 source pixels, low-amplitude sway, deterministic nonuniform 4–6 s blinks, sparse ear twitch, phase-offset hair, slower tail. Rig-only motion is paused while hidden or reduced motion is requested. Static poses and expression selection still work. Interruption selects the next absolute pose and restarts only that state's entry curve; no queue of stale celebrations. Failed/frustrated reactions settle to zero and do not loop. Final amplitudes and pacing require real-art review; no claim of premium finished motion is made from mechanical fixtures.

## Safe fallback and integration

The coordinator fetches the v2 manifest. `approved:false` immediately retains raster; it does not request nonexistent parts. A valid approved pack must decode every variant and match dimensions before replacing raster atomically. Malformed packs, failed image decode or stale asynchronous loads cannot leave an empty character. `character.html?character=raster` forces fallback without even fetching a manifest.

The original PNGs render at opacity 1, with only a 300 ms state crossfade. They do not breathe, sway, zoom or float as a single image. Geometry stays fixed across state changes. Lighting never reduces their opacity. Room reference uses the same contract but is archived; desktop UI uses the standalone character surface.

## Exact next art/implementation step

Obtain and approve the separated **editing pose** first, with proper knees/ankles, hidden overlaps, grip/thumb and head layers. Assemble its 34 parts in a rig-only review fixture. Validate seated knee swing, foot inheritance, phone grip, blink and hair lag at 1366×768 and 1920×1080. Tune pivots against actual art. Then export the other five poses/expressions and inspect state entry/interruptions. Set `approved:true` only after all six are visually accepted. Do not redraw, edit, trace or replace the approved fallback PNGs in this pass.
