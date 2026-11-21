import bpy,sys,json,hashlib
from pathlib import Path
R=Path(__file__).parent
T=Path('C:/Users/rupjy/.codex/visualizations/2026/10/07/01a11802-03a6-7f71-9210-318d920a3def/NekoAFK-Blender-tools')
sys.path.insert(0,str(T));bpy.ops.preferences.addon_enable(module='io_scene_vrm')
(R/'audit').mkdir(exist_ok=True);(R/'renders').mkdir(exist_ok=True)
files=[R.parent/'v001/NekoAFK-editing-v001.blend',R.parent/'v001/NekoAFK-model-v001.blend',R.parents[1]/'blender/NekoAFK-canon.blend',R.parents[1]/'animations/NekoAFK-barefoot-animated.glb',R.parents[1]/'animations/NekoAFK-socks-animated.glb']
(R/'audit/source-hashes.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},indent=2))
bpy.ops.wm.open_mainfile(filepath=str(files[0]))
r=bpy.data.objects['Armature'];f=bpy.data.objects['Face']
info={'objects':[{'name':o.name,'vertices':len(o.data.vertices),'materials':[m.name if m else '' for m in o.data.materials],'modifiers':[(m.name,m.type) for m in o.modifiers]} for o in bpy.data.objects if o.type=='MESH'],'bones':{b.name:{'head':list(b.head_local),'tail':list(b.tail_local)} for b in r.data.bones},'face_keys':list(f.data.shape_keys.key_blocks.keys())}
(R/'audit/source.json').write_text(json.dumps(info,indent=2))
hair=bpy.data.objects['Hair']; adj=[set() for v in hair.data.vertices]
for e in hair.data.edges:a,b=e.vertices;adj[a].add(b);adj[b].add(a)
seen=set();comp=[]
for i in range(len(adj)):
 if i in seen:continue
 q=[i];seen.add(i);ids=[]
 while q:
  j=q.pop();ids.append(j)
  for k in adj[j]-seen:seen.add(k);q.append(k)
 vs=[hair.data.vertices[j] for j in ids]
 comp.append({'ids':ids,'min':[min(v.co[k] for v in vs) for k in range(3)],'max':[max(v.co[k] for v in vs) for k in range(3)]})
(R/'audit/hair-components.json').write_text(json.dumps(comp))
print('INSPECTED',len(comp),'hair islands',len(r.data.bones),'bones',flush=True)
for o in bpy.data.objects:
 if o.type=='MESH' and ('Hair' in o.name or 'Cuff' in o.name or 'Tail' in o.name):print(o.name,len(o.data.vertices),[m.name for m in o.data.materials],flush=True)
