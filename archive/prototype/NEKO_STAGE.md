# Raster stage integration

The six approved PNGs are unchanged. `tests/neko_visual.py` verifies their SHA-256 hashes before exercising the scene. There is no backend or agent integration.

The stage now routes state changes through `character/neko-character.js`. The original renderer below remains the default fallback while the layered pack is incomplete. See [the layered-rig plan](character/RIG_PLAN.md) for the exact asset contract, motion design and activation steps.

## Audit findings

- `styles.css` defined `@keyframes drift` twice. The later dust definition won globally: the character ancestor moved upward by 180px and animated opacity from 0 to .4 to 0. Giving the active image opacity 1 could not undo its parent's fading.
- The old image frame was 108% of a 46%-wide zone, with a width-derived 1122/1402 aspect ratio. At the 1400px room width its height was about 869px, exceeding the 787.5px room before breathing, drift, manifest offsets or transition transforms. Room overflow then cropped it.
- Room offsets and anticipation shared `.nstage`; images also scaled and translated during fades; ancestor breathing, dust drift and success margin animation added more displacement.
- A strong soft-light key overlay, active-only glow filters and room grading above the image changed the approved artwork's appearance.
- A full-width desk and foreground caption crossed the oversized, translucent chair. Width-only room sizing also pushed the controls below a 768px viewport.
- The previous demo omitted frustrated. No obsolete SVG character remains in the supplied files. The brand SVG and procedural grain are still used and are retained.

## Ownership

`NekoStage (.neko-stage)` is the one fixed viewport in room coordinates.

1. `.neko-position` bottom-centres a shared envelope using a single contain scale. Only viewport resize updates this geometry.
2. `.neko-motion` owns a six-second breath: 0.12% uniform scaling and 0.35px horizontal drift, pivoted at wheel contact. It never changes opacity.
3. `.neko-layer` images have immutable geometry from `NEKO_MANIFEST`. Only their opacity transitions, over 300ms. Outgoing images become hidden when the fade finishes. Decode guards and a request version prevent stale asynchronous swaps.

Every nonzero alpha pixel is included in the safe envelope. Source bounds are deliberately not assumed equal:

| State | Canvas | Alpha bounds (left, top, right, bottom) |
| --- | --- | --- |
| editing | 1138 × 1382 | 49, 7, 1062, 1359 |
| testing | 1122 × 1402 | 49, 1, 1072, 1402 |
| failed | 1122 × 1402 | 33, 33, 1114, 1402 |
| frustrated | 1122 × 1402 | 0, 15, 1119, 1402 |
| verifying | 1122 × 1402 | 48, 11, 1056, 1402 |
| success | 1122 × 1402 | 0, 0, 1122, 1402 |

The manifest also records each chair's centre column and visible wheel-floor contact. This registers the chair independently of the changing tail/hand silhouette. The union of the registered bounds plus a 24-source-pixel gutter controls contain scaling. No state gets its own fitted viewport or animated offset.

Room grading is below furniture and Neko. The artwork supplies its own rim light. A separate floor shadow grounds the chair; speech and telemetry stay in room coordinates outside the character envelope. The monitor remains screen-right.

## Validation

With the prototype server running, execute `python prototype/tests/neko_visual.py` (Python Playwright and Pillow required). Evidence is written under `.artifacts/neko-validation/`.

Verified all six states at 1920×1080 and 1366×768 and reviewed chronological frames across the full ten-second demo at both sizes. The checks cover alpha-bound containment, full resting opacity, hidden inactive images, unchanged assets, rapid interruptions, reduced motion, keyboard activation, viewport overflow and console errors. The automated accessibility scan returned no violations. Additional 1440px and 390px screenshots were inspected; a native screen-reader pass was not performed.

The demo loops through editing → testing → failed → frustrated → verifying → success in ten seconds. Keys 1–6 select states. Space on the page starts/stops the loop; Space on a focused button retains native button activation. Legacy `?s=failed3` links resolve to frustrated.
