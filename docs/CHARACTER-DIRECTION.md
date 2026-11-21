# Neko character direction — 12 October 2026

This pass replaces the character performances while preserving the original
Neko identity and application architecture. Product changes are confined to
`assets/cat.svg`, `src/director.ts`, and `src/character.ts`. The desktop host,
OpenCode bridge, evidence interpretation, verification, windows, settings and
security behavior have not been rebuilt.

## The visual audit

The full previous 91.4-second native recording was reviewed as 366 sequential
quarter-second samples, across all 16 contact sheets. The original recording
and source snapshots are retained in `.artifacts/character-direction/before/`.
The following were visible problems, rather than conclusions from code alone:

| Evidence in the previous recording | Problem | Direction taken |
| --- | --- | --- |
| 0–6 seconds, grooming | The lifted paw mostly holds beside the cheek. The head supplies almost all the action. | Two actual cheek wipes, preceded by a paw-to-mouth beat; the nearby eyelid reacts. |
| 7–14 seconds, pencil | A floating prop carries the premise, with little believable handling. | Removed. A tiny winged visitor provides a gaze-led reach, miss and follow instead. |
| 22–31 seconds, working | The laptop appears in front of a largely stationary cat and covers her body. | A lower keyboard, connected hands, irregular tap phrases and a deliberate checking pause. |
| 49–55 seconds, facepalm | A long thin arm crosses the face and holds too long. It reads as an extended tube. | Removed. A look away, closed-eye exhale and one small paw protest. |
| 75–82 seconds, celebration | Flattened irises, symmetrical lifted arms, sparkles and bobbing compete for attention. | A compression, small seated rise, asymmetric paws, closed-eye smile and soft return. |
| Across the recording | Eye scaling compresses pupils and highlights. Rigid tail rotation and identical interpolation make separate actions feel related mechanically. | Clipped eyelids, continuous facial curves, bending tail, soft appendage overlap and beat-specific easing. |

The original purple tuxedo, amber eyes, cheek tufts, cream muzzle and gold charm
stay recognizable. The palette and outlines are softer; mitten paws now have
clear attachment, white tips and a palm detail for the attention gesture.
The feet remain grounded while the torso and head perform.

## Kept, removed, redesigned

The library now contains twelve authored performances. Shared performances
serve more than one factual state; labels do not count as extra animations.

- **Listen:** eyes notice something first, then the head and ears follow; a
  second look ends with a slow blink.
- **Wash:** a paw-to-mouth preparation, two cheek passes, release and contentment.
- **Nest:** asymmetric kneading, tucked head and curled tail, a long quiet rest,
  ear-led waking and a small yawn. This is a seated doze, not a lying-down pose.
- **Mote:** attention follows a small winged visitor, with anticipation, one
  attempted catch, a miss and a gaze following its departure.
- **Keyboard:** hands land, type in finite irregular phrases, stop to check,
  resume, then withdraw as the keyboard retreats.
- **Consider:** a chin paw, change of eyeline and deliberate release.
- **Recoil:** fast surprise, brief recoil and skeptical settling.
- **Huff:** look away, inhale/exhale, one paw tap and a quieter irritated rest.
- **Beckon:** notice the user, lift the palm, two small gestures and return.
- **Inspect:** the magnifying glass stays attached to the hand as she leans,
  changes angle, checks and lowers it.
- **Delight:** compressed anticipation, seated rise, uneven happy paws and smile.
- **Puzzle:** opposing ear and head angles, a hesitant paw and an uncertain finish.

Removed phone scrolling, popcorn, pencil routines, laptop checking, evidence
cards, question-mark props, tail chasing, the stretched facepalm and the
symmetrical sparkle cheer. Their replacement is clearer acting and longer
quiet space, rather than a larger inventory of props.

## Factual state mapping

| Host evidence/state | Character choices |
| --- | --- |
| Idle, offline or no recent work | Listen, wash, seated doze, mote |
| General busy; detail unavailable | Mote, listen, consider, wash |
| Observed reasoning part | Consider, listen |
| Observed assistant writing or editing | Keyboard, listen |
| Observed testing/building | Listen, consider |
| Failed tool/check | Recoil, huff |
| Repeated failures | Huff first, then recoil when available |
| Pending permission | Beckon, listen; highest interruption priority |
| Independent verification running | Inspect, consider |
| Fresh independently verified result | Delight once per evidence token, then happy idle |
| Completion claim or inconclusive check | Puzzle, consider; no celebration |

The busy cat's personal distractions are entertainment. They do not claim the
agent is reasoning, writing or testing. Existing host evidence determines the
telemetry independently, including permissions, stale results and disconnection.

The existing host marks activity **inactive after 60 seconds without a new work
event**, even if source heartbeats continue. This was observed in the long
native run: Neko correctly moved into idle choices, including her seated doze.
That timeout is preserved here. If long silent tool runs should remain busy,
the next engineering pass should decide that from actual tool-lifetime evidence;
the character must not invent it. The acceptance harness also exercises
continuing work using explicit fresh hook fixtures.

## Motion construction

Authored keys use seconds and carry unspecified channels forward. Previously,
a head-only key could accidentally release a hand or prop to neutral. Hands
now follow connected shoulder-to-hand curves; the glass shares its hand's
exact transform. Body settling does not move the feet. Ear, tail and charm
follow-through is damped without adding perpetual body motion.

Eyelid apertures clip intact irises and highlights. Closing lashes morph into
soft creases; the final amber slit fades away before a closed smile settles.
Brows, muzzle, mouth, gaze and subtle face parallax act independently.

The director keeps seeded randomization, no immediate activity repeats,
per-performance cooldowns and bounded verified-result memory. Variants change
timing and head/ear softness without disturbing hand-to-prop contact. Incoming
urgent states blend from the precise current pose, including a mid-blink pose.
The transition lasts 420 ms; lower priorities wait at most 450 ms before entry.

Calm leaves 19–38 seconds between performances; Playful 10–25; Chaos 5–13.
Cooldowns can extend a gap when no performance is available. Playful remains
the default. Rest has occasional seeded blinks, not constant bobbing.

Rendering uses a carried 30 Hz deadline, avoiding the former 33/50 ms cadence
caused by a strict elapsed-time threshold on a 60 Hz display. Cached attributes
avoid rewriting unchanged poses. Reduced motion renders a static expression;
hidden companions suspend their animation loop.

## Native evidence and validation

The review artifacts are under `.artifacts/character-direction/`:

- `neko-native-showcase.mp4`: the final 30–60 second production native capture.
- `before-after.png`: unchanged native frames arranged side by side.
- `native-art-review.mp4`: a longer internal native authoring review, including
  the visitor, grooming, success, inspection and seated doze.
- `native-acceptance.json`: native state, rendering and resource checks.
- `showcase-timeline.json`: observed state/activity times for the showcase.
- `audit/`, `motion-review/`, `final-review/`: full sequential visual review sheets.

The showcase is deliberately fixture-driven: supported OpenCode hook fixtures
pass through the existing bridge and native host. The victory follows an
actual configured command's successful exit. It is not a recording of an
autonomous coding session. The separate real OpenCode integration check tests
an actual OpenCode process and session without model requests.

TypeScript/Vite and the native `--no-bundle` build pass. Fourteen focused tests
pass, including a seeded two-hour simulation, 500 rapid changes, verified-only
celebration, no immediate repeats, contact preservation through sparse keys,
interruption during a blink, finite poses and connected hand reach.

The ten-minute native continuity run passed rapid permission priority, repeated
failure, inconclusive completion, disconnect/reconnect, transparent pixels,
user reduced motion and the system media preference (emulated in native
WebView2), hiding/resuming, personality persistence and
absence of runtime errors or overflow. Its raw report is retained as
`native-long-session-raw.json`; `native-long-session.json` adds the activity
expiry interpretation. This run preceded only the final cosmetic eyelid-slit
fade refinement; the director, rig and frame scheduler were already final.

At normal scale on this Windows machine, across the app and nine related
processes, that run measured:

| Measurement | Observed result |
| --- | --- |
| Native observation duration | 600.06 seconds |
| CPU, percentage of one logical core | 21.8% average |
| Private working set, start / end | 314.6 / 230.1 MiB |
| Private working set, sampled peak | 326.9 MiB |
| Summed process RSS, start / end | 751.2 / 671.0 MiB |
| Reduced-motion CPU, one-core basis | 0.47% over a separate 10-second sample |
| Active SVG mutation interval, median / p95 | 34.6 / 35.5 ms |

RSS includes shared process pages and must not be presented as exclusive memory.
The mutation intervals measure renderer updates, not GPU presentation timing.
The recording, automation, desktop activity and machine affect these results;
they are observations, not a cross-machine performance benchmark. Memory did
not grow over this run, but the CPU cost still warrants an engineering profile.
Passing checks establishes reliability, not an artistic quality score.

The **final build** also passed a 120.08-second run with fresh work fixtures
every 20 seconds. Every sampled factual state remained active while wash,
listen, consider, mote and quiet rests varied independently. Permission
interrupted an in-progress keyboard performance and its previous prop faded
out; repeated failure and inconclusive results did not produce victory.
The remaining native checks passed again with zero runtime errors. This run
averaged 18.88% of one core; private working set fell from 286.2 to 233.6 MiB.
Reduced motion averaged 0.47% of one core. Active mutation cadence again
measured 34.6 ms median / 35.5 ms p95.

The final showcase is **57.9 seconds, 600 × 600, 30 fps**, recorded from the
actual Windows-composited companion region. Its opaque capture preference
keeps unrelated desktop content out of the video; normal-scale transparency
was checked separately. All 232 quarter-second samples across the full final
timeline were visually reviewed. The sequence is visitor → keyboard →
attention → independent check → delight and settling. A transient completion
claim remains unverified before that check. The source/build/video hashes are
in `review-manifest.json`.

Finally, an actual **OpenCode 1.18.35** process, real session and shell operation
were rerun against this final native build. Busy activity reached both native
surfaces, the new performance played, and tool completion stayed unverified.
No model request was made. Evidence is retained in
`.artifacts/opencode-desktop-report.json` and copied beside the character
artifacts as `opencode-final.json`.

## Remaining visual weaknesses

- The character is still a front-facing 2D vector rig. Face parallax helps,
  but cannot replace drawn three-quarter and side poses or real foreshortening.
- The seated silhouette remains dominant. There is no convincing full-body
  roll, walk, turn or lying-down sleep pose in this pass.
- Shading is polished static artwork, not lighting that changes with limb
  rotation. Strongly bent arms can still reveal their curve-based construction.
- Props enter by a short retreat/fade rather than a fully staged retrieval.
  The glass is held correctly but does not optically magnify the eye.
- Small typing and ear details are restrained at normal desktop size. Quiet
  gaps are intentional, but twelve performances remain a finite repertoire.
- A dark character loses some lower-body contrast over busy dark desktops;
  the existing opaque companion preference improves readability when needed.

The next substantial artistic step would be a set of original alternate body
poses and turn drawings, rather than adding more front-facing prop routines.
No installer, commit, push or release is part of this pass.
