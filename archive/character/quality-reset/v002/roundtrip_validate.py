import bpy,sys,json,hashlib,math
from pathlib import Path
R=Path(__file__).parent
source=json.loads((R/'audit/source-hashes.json').read_text())
hashes={p:hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in source.items()}
assert all(hashes.values()),'An original source changed'
bpy.ops.wm.read_factory_settings(use_empty=True)
result=bpy.ops.import_scene.gltf(filepath=str(R/'NekoAFK-editing-v002-mtoon.glb'))
assert result=={'FINISHED'}
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');names=set(rig.data.bones.keys());face=next(o for o in bpy.data.objects if o.type=='MESH' and o.data.shape_keys and 'Fcl_EYE_Close' in o.data.shape_keys.key_blocks)
assert all(f'Neko_Tail_{i:02d}' in names for i in range(1,9))
assert all(f'J_Opt_{s}_CatEar2_01' in names for s in ('L','R'))
assert all(f'Neko_{s}_Toe{i:02d}_{j}' in names for s in ('L','R') for i in range(1,6) for j in ('Prox','Dist'))
assert len(face.data.shape_keys.key_blocks)>=58
actions=[a.name for a in bpy.data.actions];report={'originals_unchanged':hashes,'imported_bones':len(names),'face_keys':len(face.data.shape_keys.key_blocks)-1,'actions':actions,'tail_ears_toe_chains_present':True,'note':'Blender core importer does not implement VRMC_materials_mtoon: material appearance is validated in Three.js using pixiv plugin, not inferred from this import.'}
(R/'audit/roundtrip.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
