import bpy, json, hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1]
source=R.parents[1]/'blender/NekoAFK-canon.blend'
bpy.ops.wm.open_mainfile(filepath=str(source))
rig=bpy.data.objects['Armature']; body=bpy.data.objects['Body']
info={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'bones':{b.name:{'head':list(b.head_local),'tail':list(b.tail_local)} for b in rig.data.bones},'objects':[{'name':o.name,'type':o.type,'location':list(o.location),'dimensions':list(o.dimensions),'materials':[m.name if m else '' for m in o.data.materials] if o.type=='MESH' else []} for o in bpy.data.objects], 'keys':list(bpy.data.objects['Face'].data.shape_keys.key_blocks.keys())}
info['body_materials']=[]
for i,m in enumerate(body.data.materials):
 ids={v for p in body.data.polygons if p.material_index==i for v in p.vertices}
 vs=[body.data.vertices[j].co for j in ids]
 info['body_materials'].append({'name':m.name,'vertices':len(vs),'bounds':[[min(v[k] for v in vs),max(v[k] for v in vs)] for k in range(3)]})
(R/'audit/source.json').write_text(json.dumps(info,indent=2))
print('SOURCE_INSPECTED',info['body_materials'],flush=True)
