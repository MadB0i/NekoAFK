import bpy,sys,json
from pathlib import Path
from mathutils.bvhtree import BVHTree
R=Path(__file__).parent;T=Path('C:/Users/rupjy/.codex/visualizations/2026/10/07/01a11802-03a6-7f71-9210-318d920a3def/NekoAFK-Blender-tools');sys.path.insert(0,str(T));bpy.ops.preferences.addon_enable(module='io_scene_vrm')
bpy.ops.wm.open_mainfile(filepath=str(R/'NekoAFK-editing-v002.blend'));r=bpy.data.objects['Armature'];bpy.context.scene.frame_set(19);p=r.pose.bones['QR01_Phone'].matrix@r.data.bones['QR01_Phone'].matrix_local.inverted();inv=p.inverted();dep=bpy.context.evaluated_depsgraph_get();rows=[]
for o in bpy.data.objects:
 if o.type!='MESH' or not (o.name=='Body' or o.name.startswith('QR01.Nail.R')):continue
 ev=o.evaluated_get(dep);me=ev.to_mesh();bad=[]
 for v in me.vertices:
  c=inv@v.co;d=min(.027-abs(c.x),.0038-abs(c.y),.062-abs(c.z))
  if d>.0005:bad.append({'i':v.index,'phone_local':list(c),'depth':d,'groups':[(o.vertex_groups[g.group].name,g.weight) for g in v.groups]})
 if bad:rows.append({'object':o.name,'bad':bad})
 ev.to_mesh_clear()
(R/'audit/contact-detail.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows),flush=True)
