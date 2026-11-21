# Cute Robot Character "Nova" + Character Selector

## Context

NekoAFK ka current mascot ek articulated midnight-purple cat hai jiska "chhota dimag" (`src/director.ts` — 12 authored clips, mood engine) beautifully kaam karta hai, par user chahta hai ki character Grok-companion jaise **cute floating bot** style ka ho. Decision (user-confirmed): **naya cute robot "Nova" banega — naya default character; existing cat Settings > Character selector me rahega. Palette: Midnight + Amber (app brand match).**

Key architectural fact: Director brain (clips, poses, moods) is **character-agnostic** — ye 32-channel `Pose` deta hai. Sirf rendering layer (`src/character.ts` `paint()` + `assets/cat.svg`) cat-specific hai. Naya robot = naya SVG + naya paint-rig; **Director aur saare 11 performances (thinking/consider, typing/keyboard, fail/recoil, celebration/delight...) bina kisi change ke robot me bhi chalenge.**

## Hard contract (invariants — tests isse coupled hain)

- `Character` class **`src/character.ts` me hi** rahe, constructor signature exactly: `constructor(root, seed=crypto.getRandomValues(new Uint32Array(1))[0])` — `tests/experience_native.py:19` aur `tests/quality_native.py:25` isse regex-match karte hain. Sab rig code bhi character.ts me hi rahega (`tests/character-clock.test.mjs:8` sirf `'./director'` import inline karta hai, koi aur import bundle nahi hota).
- `src/director.ts` **zero changes** — `tests/director.test.mjs` clip ids, durations, hand-reach (SVG coords) pin karta hai.
- Dataset contract surakshit: `#app` `data-motion` (full|reduced|paused), `#mascot` `data-activity`/`data-performance` (clip ids: keyboard, huff, beckon...), `#rig` mutation-freezing quiet optimization.
- Robot SVG me **saare 30 renderer IDs** hone chahiye (jinme kuch empty `<g/>` ho sakte hain: muzzle, whiskers n/a) + `.pupil` class + `#head` id (`tests/native_smoke.py:208` `#head` query karta hai).
- Geometry anchors reuse: haath rest (119,252)/(201,252), shoulders (116/204, 217), pivots — head(160,190), face(160,145), ears→ear-pods(110,96)/(212,96), charm→core(160,211), torso(160,267). Isse keyboard/glass/mote props **bina change** kaam karenge.

## Nova design spec (Midnight + Amber)

- **Anatomy**: round helmet head (~55% canvas width — cat se bada), bade glossy amber LED eyes (cat eyes se ~30% bade, white highlight dots), arc smile + open-mouth (jaw), soft pink blush, forehead par chhoti antenna with glowing amber tip, side ear-pods (earL/earR channels inhe rotate karte hain), chhota rounded hover-body, chest gold core (charm channel), stubby arms, neeche **hover ring** jiske niche ground-glow.
- **Palette**: body `#2a2140` deep plum, panels `#3a2f55`, eyes `#ffb84d`→`#b97223` amber radial, screen `#fff0de` cream, cheeks `#e8899a`, core `#ffd97a` gold, hover glow `#8e779b`. Sirf gradients (LIVING-CAT.md rule: no raster/blur), 320×320 viewBox.
- **Pose channel mapping** (rendered by new robot rig):
  - `earL/earR` → ear-pod rotations (same pivots) · `tail` → hover-ring wobble/pulse · `curl` → ring spread/tilt · `eyes/eyeL/eyeR/brow/lash/lid` → LED screen face (bade eye constants) · `mouth/jaw` → arc smile / open mouth · `squash/breath/y/body/head/hx/hy/turn` → same body/head transforms as cat · `gaze*` → `.pupil` translate · `palm` → hand palm-light · `charm` → chest core rotation · props identical.
- Cuteness details: blink (existing lid math, bigger aperture), eye-sparkle highlight jo gaze ke saath slide kare, hover ring ka soft gradient glow, screen par subtle scanline-free clean gloss sweep (static gradient).

## Files

**Create:**
- `assets/robot.svg` — Nova rig, same 30 IDs + `.pupil`, `data-character="robot"` root attr.
- `tests/robot_visual.html` (optional dev page) — static preview for shape iteration.

**Modify:**
- `src/character.ts` — class + scheduling same rahe; `paint()` dispatch: constructor root par `data-character` padh ke cat-rig ya robot-rig select kare. Cat rig = aaj ka code as-is (extract into private method), robot rig = naya private method (bigger eye constants, ear-pods, ring wobble instead of tail bezier, core instead of charm-rotation reuse). `props` map unchanged.
- `src/views.ts` — imports `robot.svg?raw` + `robotUrl`; `companionView()` me mascot placeholder dono me se ek se fill hoga (initial robot); settings `panel-character` me `Companion` select `[robot: Nova | cat: Neko]` + dono characters ke preview `<img>` side-by-side; "Reduce cat motion" → "Reduce companion motion"; alt/copy updates.
- `src/main.ts` — `Settings` type me `character: string`; `let character` (const nahi) + `mountCharacter(kind)` helper jo `#mascot` innerHTML swap karke naya `Character` banaye jab `s.settings.character` change ho; aria-label prefix per character (`Nova:`/`Neko:`); `settingsFromForm()`/`fill()` me character select; settings preview img src swap.
- `src-tauri/src/model.rs` — `Settings` me `pub character: String` (+`Default` = `"robot"`), `validate_structure()` me membership check `["cat","robot"]` (personality pattern copy, model.rs:67-69).
- `src-tauri/src/storage.rs` — test me invalid-character fallback assertion (personality parallel).
- `src/style.css` — `.mascot-preview` duo styling, koi aur change nahi (`.mascot>svg` generic hai).
- Tests: `tests/character_native.py` me `character_persistence` round-trip; `tests/living_cat_native.py` character-select UI round-trip; `tests/native_smoke.py:204` label update.
- `README.md` + `docs/LIVING-CAT.md` — character selector + Nova note (pose contract shared).

## Work order

1. **Art first**: `assets/robot.svg` static banao, browser me preview karke shape iterate karo (browser-use se screenshot check).
2. **Rig**: character.ts me robot paint rig; character-stage/dev page se animated sanity.
3. **Settings plumbing**: Rust field+validate → TS type/select/fill → runtime swap in main.ts.
4. **Tests + docs** update.
5. Full verification (neeche).

## Verification

1. `npm test` — director/character-clock/bridge tests (character-clock ab bhi character.ts+director bundle pass kare).
2. `cargo test --manifest-path src-tauri/Cargo.toml` — settings round-trip + invalid-character quarantine.
3. `npm run build` — tsc clean.
4. `npm run desktop` + `node tests/emit-fixture.mjs <ws> <scenario>` se scenarios emit karke Nova ke keyboard/thinking/celebration animations visually confirm (screenshots).
5. `python tests/native_smoke.py --exe src-tauri/target/release/nekoafk.exe` (build ke baad) — reduced-motion freeze, #head animation none, axe checks.
6. Settings me character switch karke cat↔robot runtime swap confirm + persistence restart ke baad.
