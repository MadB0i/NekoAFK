# NekoAFK canonical character

Production: `blender/NekoAFK-canon.blend` (Blender 5.2.2).
Default runtime: `runtime/NekoAFK-canon.vrm` (VRM 1.0, barefoot).
Optional runtime: `runtime/NekoAFK-canon-socks.vrm` (cream socks).
Approved VRoid sources remain unmodified in `source/`.

Animated companion source: `animations/NekoAFK-animation-library.blend`.
Animated runtime variants: `animations/NekoAFK-barefoot-animated.glb` and `animations/NekoAFK-socks-animated.glb`.
See [animation library notes](animations/README.md) for the 42 clips, rendered previews and validation evidence.

## Final appeal/modeling pass

Restrained adult jaw/chin and eye refinements, a subtle asymmetric smile and confident brows preserve the original identity. All 57 facial keys retain their expression deltas. Purple-black hair, amber streak, eyes and permanent clip, cat ears, charcoal cat-logo hoodie, dark joggers and curved fluffy tail remain canonical.

Hands have smoother local finger topology and short fitted charcoal/amber nail plates. Bare feet recover the approved heel/ankle base and add a continuous smooth forefoot, medial arch and five distinct toes, with restrained black/amber polish. Cuffs taper around bare ankles. Foot geometry is reduced to practical runtime density.

## Rig and variants

All 147 existing bones are preserved. Twenty toe bones bring the total to 167. The runtime retains 54 humanoid assignments, 18 expression presets and 57 facial morphs. All skinned vertices have normalized weights and at most four influences.

- Tail: `Neko_Tail_01` through `Neko_Tail_08`, parented to `J_Bip_C_Hips`.
- Independent ears: `J_Opt_L_CatEar2_01` and `J_Opt_R_CatEar2_01`.
- Toes: `Neko_L_Toe01_Prox` / `Neko_L_Toe01_Dist`, through toe 05, with matching R controls. Each proximal bone is parented to its humanoid ToeBase; its distal bone is a child.
- Barefoot: show `DEFAULT • barefoot`; hide `OPTIONAL • cream socks`.
- Socks: hide barefoot; show socks. Keep these collections mutually exclusive. Manicure is common to both variants.

Textures are packed. The source is saved in neutral T pose, with no active action or authored animation clips. The original importer T-Pose calibration asset remains available. QA Studio and its chair are preview-only and excluded from runtime. Export only visible Character meshes and Armature.

## Validation and captures

Actual Blender renders in `previews/final/` include front, three-quarter, side and seated barefoot, plus close-ups and temporary checks for knee bend, leg swing, ankle flex, toe tension, torso lean, raised arms, head turn, blink, ears, tail and finger flex. No major deformation failure or barefoot cuff clipping was observed in these static checks. Dynamic hair/clothing collisions and chair contact require checks during animation authoring.

Both runtime variants were successfully reimported. Standing and seated barefoot reimport renders were visually inspected. The validator reported informational automatic-triangulation notices only. Neither runtime contains QA geometry, external buffers or animation clips.

Current validation: `blender/appeal-validation.json`. Earlier `finishing-validation.json` and `runtime-validation.json` document the previous socks-default pass.

Use the official VRM Add-on for Blender 4.7.2 for metadata/export: https://vrm-addon-for-blender.info/

No application/backend files were changed. No animation was produced. No commit or push was made.
