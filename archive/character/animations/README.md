# NekoAFK animation library

Character animation assets only. The desktop application and the finalized canonical character source were not changed.

## Deliverables

- `NekoAFK-animation-library.blend`: authoritative editable animation source, original toon materials, Actions and matching NLA tracks.
- `NekoAFK-animation-previews.blend`: assembled demonstration timelines with cameras, lights and captions; these presentation objects are excluded from runtime exports.
- `NekoAFK-barefoot-animated.glb` and `NekoAFK-socks-animated.glb`: complete self-contained glTF 2.0 variants, including character, gaming chair and phone.
- `animation-manifest.json`: clip names, durations, loop flags and transition policy.
- `previews/NekoAFK-all-states.mp4`: all six entrances/reactions and living idles.
- `previews/NekoAFK-reaction-chain.mp4`: FAILED → FRUSTRATED → VERIFYING → SUCCESS.

## Clips

42 clips at 24 fps: six entrances, six seamless living idle loops and all 30 directed transitions between different states. Names are `Neko_EDITING_Enter`, `Neko_EDITING_Idle` and `Neko_EDITING_to_TESTING`, with the same convention for the other states.

EDITING loops for 12 seconds; the other idles loop for eight seconds. Each Action has an Armature slot and a facial shape-key slot, with matching NLA track names on both owners. Activate both tracks together when previewing a single clip in Blender. The default source playback is EDITING idle. Entrances have the predecessor documented in the manifest; use the directed transition for a different predecessor.

Hips stay fixed against the seat. Knee swing, ankles, all ten toes, thumb, head, eyes, facial expressions, ears, tail and secondary hair/hoodie motion have their own tracks. Existing humanoid, facial, tail, ear and toe controls remain intact. Three controls were added: `Neko_Prop_Phone` and `Neko_Cloth_Hem.L/R`, giving 170 bones in the exported hierarchy.

The phone follows the right-hand grip, then is placed on the chair's phone dock before the hand is released. Transitions toward a state that needs the phone pick it back up. Celebrations starting with the phone in hand include the placement and therefore last longer.

## Renderer contract

Load either GLB with Three.js GLTFLoader and drive its named clips with AnimationMixer. Play entrances/transitions once, then the destination idle as a repeating loop. Use the manifest's short pose blend when switching from an arbitrary idle phase into its directed transition; avoid starting an unrelated entrance from an incompatible predecessor. Blend skeletal and morph tracks together. Keep the exported character, chair and phone in the same world transform.

Apply EDITING idle at time zero before the first visible frame (`play()` followed by `mixer.update(0)`) so the transparent companion window opens with a seated pose.

Secondary motion is deterministic and baked into the clips, including damped hair follow-through. It is not a live collision/physics simulation. Do not add another procedural oscillator on the same bones without first excluding their baked tracks.

GLBs use standard PBR material fallbacks with the original embedded textures. Blender retains the original MToon materials; their key shading settings are also stored in GLB material extras as `NekoAFK_MToon`. A later desktop renderer can recreate the toon treatment from those settings. No renderer or application integration is included in this pass.

## Export safety

The exports were tested with Blender 5.2.2 and the VRM Add-on 4.7.2. Export selected runtime character/prop objects as GLB using NLA Tracks, merge by NLA track name, skins, morph targets, morph animation, sampled animation and extras; exclude presentation objects. Export each clothing variant separately.

This exporter version incorrectly merges a zero-valued duplicate facial weight track over the actual facial animation. The delivered GLBs are repaired and reimport-validated. After a fresh native export, run `tools/repair-exported-morphs.py` with Blender's background Python runner. It reads the authoritative facial Action slot and writes standard LINEAR glTF morph samplers into both GLBs. Run it once after each fresh export, then reimport and check blinks and expressions before distributing.

## Validation evidence

- `authoring-validation.json`: clip durations, continuity and idle seam checks.
- `transition-boundary-validation.json`: neighboring idle/transition pose differences, accounting for equivalent quaternion signs and the tiny authored anticipation at the beginning of startled reactions.
- `dynamic-validation.json`: nine sampled poses for every clip, fixed hips, seat clearance, floor clearance and conservative chair collision candidates.
- `chair-surface-validation.json`: actual evaluated chair/dock surfaces checked across all 42 clips (378 sampled poses), with no penetrations beyond the 3 mm contact tolerance after clearance corrections. The individual armrest/dock reports additionally cover every frame of the placement entrance.
- `chair-surface-dense-validation.json`: final exhaustive check of all 3,546 library frames against the chair and phone-mount surfaces, with no penetrations beyond the 3 mm tolerance.
- `export-validation.json` and `morph-export-validation.json`: packaged structure and actual facial sampler checks.
- `roundtrip-validation.json`: both variants reimported with all 42 clips, 170 bones and 57 facial morph targets; movement and blink playback sampled after import.
- `preview-timelines.json`: exact demonstration schedules.

Key-pose PNGs are actual Blender renders. Videos are actual rendered skeletal/morph animation, with short pose blends on the demonstration timelines.

The preview Blender file contains the demonstration NLA timelines. State captions in the movies are updated during rendering; use the NLA clip names and timeline manifest when inspecting playback in Blender.
