import bpy,sys,json
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
R=Path(__file__).parent;T=Path('C:/Users/rupjy/.codex/visualizations/2026/10/07/01a11802-03a6-7f71-9210-318d920a3def/NekoAFK-Blender-tools');sys.path.insert(0,str(T));bpy.ops.preferences.addon_enable(module='io_scene_vrm')
bpy.ops.wm.open_mainfile(filepath=str(R/'NekoAFK-editing-v001.blend'));s=bpy.context.scene;r=bpy.data.objects['Armature'];body=bpy.data.objects['Body'];phone=bpy.data.objects['QR01 Phone']
faces=[tuple(p.vertices) for p in phone.data.polygons if 'satin obsidian' in phone.data.materials[p.material_index].name];bvh=BVHTree.FromPolygons([v.co for v in phone.data.vertices],faces)
if not body.data.shape_keys:body.shape_key_add(name='Basis')
key=body.shape_key_add(name='QR01 • phone-grip contact corrective');key.value=1
base=[v.co.copy() for v in body.data.vertices];sub=next(m for m in body.modifiers if m.type=='SUBSURF');report=[]
for repeat in range(3):
 for f in [1,19,22,58,64,193]:
  s.frame_set(f);ph=r.pose.bones['QR01_Phone'].matrix@r.data.bones['QR01_Phone'].matrix_local.inverted();inv=ph.inverted();dep=bpy.context.evaluated_depsgraph_get();ev=body.evaluated_get(dep);me=ev.to_mesh();bad=[]
  for v in me.vertices:
   p=inv@v.co
   if abs(p.x)>.029 or abs(p.y)>.0045 or abs(p.z)>.0645:continue
   h,n,idx,dist=bvh.find_nearest(p)
   if (p-h).dot(n)<-.0002:bad.append((v.co.copy(),ph@(h+n*.00035)-v.co))
  ev.to_mesh_clear();report.append((repeat,f,len(bad)))
  if not bad:continue
  sub.show_viewport=False;bpy.context.view_layer.update();dep=bpy.context.evaluated_depsgraph_get();ev=body.evaluated_get(dep);me=ev.to_mesh();kd=KDTree(len(me.vertices))
  for v in me.vertices:kd.insert(v.co,v.index)
  kd.balance();shifts={}
  for p,delta in bad:
   for co,i,d in kd.find_n(p,3):
    if i not in shifts or shifts[i].length<delta.length:shifts[i]=delta.copy()
  ev.to_mesh_clear()
  for i,delta in shifts.items():
   v=body.data.vertices[i];skin=Matrix(((0,0,0),(0,0,0),(0,0,0)))
   for g in v.groups:
    bn=body.vertex_groups[g.group].name
    if bn not in r.pose.bones:continue
    bm=(r.pose.bones[bn].matrix@r.data.bones[bn].matrix_local.inverted()).to_3x3()
    for a in range(3):
     for b in range(3):skin[a][b]+=bm[a][b]*g.weight
   local=skin.inverted_safe()@delta;candidate=key.data[i].co+local*.85;offset=candidate-base[i]
   if offset.length>.004:offset=offset.normalized()*.004
   key.data[i].co=base[i]+offset
  sub.show_viewport=True;body.data.update();bpy.context.view_layer.update()
changed=[(i,(k.co-base[i]).length) for i,k in enumerate(key.data) if (k.co-base[i]).length>.000001];key['purpose'] if False else None
body['QR01_contact_corrective']='The phone-grip corrective belongs only to this editing pose. Set to zero when authoring another state.'
s.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(R/'NekoAFK-editing-v001.blend'));(R/'audit'/'contact-corrective.json').write_text(json.dumps({'passes':report,'vertices':len(changed),'max_displacement_m':max([d for i,d in changed],default=0)},indent=2));print('CORRECTIVE',len(changed),max([d for i,d in changed],default=0))
