# Why the previous animation library looked unnatural

Evidence inspected: the canonical modeling captures, old editing video sampled at half-second intervals, the old animation authoring implementation, imported rest matrices, and an eight-second native rerender of `Neko_EDITING_Idle` for comparison.

1. **Imported bone roll was ignored.** The old solver assembled a world basis for the arm without accounting for the actual imported rest basis. The lower-arm rest X axis points approximately ±Z, while rest Z points −Y. Aligning an assumed world Z directly created extreme forearm/hand twist. The resulting pinched wrist and sleeve gap were visible when the hand was posed.
2. **Elbow hints were unused.** The previous arm function accepted an elbow hint but instead projected a fixed sideways pole. The pose tended toward hovering, spread elbows rather than an authored supported-arm position.
3. **Motion was driven by shared repeating phases.** Most breathing, knee, ankle, head, tail and scroll movement came from related sine waves. The knee repeated at a fixed cadence; short idle motions lacked a clear sequence of attention, gesture and rest.
4. **The phone's rotation did not come from the full hand frame.** It used a separate world rotation. Finger curling was generic, without verified pad/case placement. The revised proof uses a fixed hand-relative phone transform and a thumb target on the screen side.
5. **The original surface treatment hid form.** Skin had near-equal light and shade values; dark geometry often read as flat silhouettes. Painted nail patches had no meaningful free edge or acrylic thickness. Hair glare and coarse outlines emphasized construction artifacts.
6. **Technical clip counts were mistaken for an appeal test.** Passing track and transition checks does not establish natural poses or attractive rendering. This reset produces one inspectable study and preserves the other 42 clips unchanged.

## Reference use

Wuthering Waves is an aspirational quality reference for stylized form, materials and facial appeal, not a source of character designs. Official reference context: https://www.playstation.com/en-us/games/wuthering-waves/ . Neko's original textures, purple-black hair, amber eyes/streak/clip, cat identity and charcoal outfit remain her own.

## Review method and limits

The old and new motion were inspected through rendered frame sequences and close-ups. The new draft contact sheet samples the eight-second timeline; the delivery movie contains all 192 genuine rendered frames. The entire source loop was evaluated for fixed hip position, hand-relative phone attachment and joint continuity. Foot/phone mesh checks are sampled every six frames and at the loop endpoint; these checks are not a blanket claim of zero intersection anywhere on the character.

Static presentation, motion timing and close-up deformation should receive human art review before the other states are rebuilt. Hair silhouette detail, cloth fold behavior and runtime shader parity remain below the final target.
