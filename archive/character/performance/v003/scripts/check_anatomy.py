import bpy,bmesh,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(R/'NekoAFK-fashion-v003.blend'))
o=bpy.data.objects['Neko • continuous legs ankles and feet'];bm=bmesh.new();bm.from_mesh(o.data)
seen=set();comps=[]
for v in bm.verts:
 if v in seen:continue
 todo=[v];seen.add(v);ids=[]
 while todo:
  a=todo.pop();ids.append(a)
  for e in a.link_edges:
   b=e.other_vert(a)
   if b not in seen:seen.add(b);todo.append(b)
 comps.append({'n':len(ids),'bounds':[[min(v.co[k] for v in ids),max(v.co[k] for v in ids)] for k in range(3)]})
print('COMPONENTS',json.dumps(comps),flush=True)
print('BOUNDARY',sum(e.is_boundary for e in bm.edges),flush=True)
