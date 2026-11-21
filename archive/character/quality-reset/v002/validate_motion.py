import bpy,sys,json,math
from pathlib import Path
from mathutils import Vector,Quaternion
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).parent;T=Path('C:/Users/rupjy/.codex/visualizations/2026/10/07/01a11802-03a6-7f71-9210-318d920a3def/NekoAFK-Blender-tools')
sys.path.insert(0,str(T));bpy.ops.preferences.addon_enable(module='io_scene_vrm')
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'NekoAFK-editing-v002.blend'))
s=bpy.context.scene;r=bpy.data.objects['Armature'];body=bpy.data.objects['Body'];feet=bpy.data.objects['NekoBareFeet • anatomical skin'];face=bpy.data.objects['Face']
if '--audit' in sys.argv:
 phone=bpy.data.objects['QR01 Phone'];casefaces=[tuple(p.vertices) for p in phone.data.polygons if 'satin obsidian' in phone.data.materials[p.material_index].name];casebvh=BVHTree.FromPolygons([v.co for v in phone.data.vertices],casefaces)
 rows=[];start={};maxstep=0;previous={};worst=None
 for f in range(1,194):
  s.frame_set(f);dep=bpy.context.evaluated_depsgraph_get();hip=r.pose.bones['J_Bip_C_Hips'].matrix.translation.copy();ph=r.pose.bones['QR01_Phone'].matrix@r.data.bones['QR01_Phone'].matrix_local.inverted();hand=r.pose.bones['J_Bip_R_Hand'].matrix.copy();rel=hand.inverted()@ph
  for p in r.pose.bones:
   q=p.rotation_quaternion.copy()
   if p.name in previous:
    step=math.degrees(q.rotation_difference(previous[p.name]).angle)
    if step>maxstep:maxstep=step;worst=(p.name,f)
   previous[p.name]=q
  if f==1:start={p.name:p.rotation_quaternion.copy() for p in r.pose.bones};start_rel=rel.copy();start_hip=hip.copy()
  if f%6==1 or f==193:
   eo=feet.evaluated_get(dep);me=eo.to_mesh();floor=min(v.co.z for v in me.vertices);eo.to_mesh_clear()
   eo=body.evaluated_get(dep);me=eo.to_mesh();inv=ph.inverted();inside=[]
   for v in me.vertices:
    p=inv@v.co;d=min(.029-abs(p.x),.0045-abs(p.y),.0645-abs(p.z))
    if d>.0008:
     hit,normal,idx,dist=casebvh.find_nearest(p)
     if hit is not None and (p-hit).dot(normal)<-.0008:inside.append(dist)
   eo.to_mesh_clear();rows.append({'frame':f,'foot_min_z':floor,'hip_drift':(hip-start_hip).length,'grip_attachment_error':max(abs(rel[i][j]-start_rel[i][j]) for i in range(4) for j in range(4)),'phone_skin_penetrating_vertices':len(inside),'phone_max_skin_depth':max(inside,default=0)})
 result={'samples':rows,'max_joint_step_deg':maxstep,'worst_joint_frame':worst,'loop_rotation_error_deg':max(math.degrees(r.pose.bones[n].rotation_quaternion.rotation_difference(q).angle) for n,q in start.items()),'bone_count':len(r.data.bones),'facial_keys':len(face.data.shape_keys.key_blocks)-1,'actions':[a.name for a in bpy.data.actions if a.users], 'render_note':'Blender uses an EEVEE art shader. The separate MToon export is checked in runtime-playback.json and actual runtime captures.'}
 (ROOT/'audit'/'new-motion-checks.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
else:
 draft='--draft' in sys.argv;folder=ROOT/('draft-frames' if draft else 'frames');folder.mkdir(exist_ok=True)
 s.render.resolution_x=500 if draft else 1000;s.render.resolution_y=600 if draft else 1200;s.render.resolution_percentage=100;s.eevee.taa_render_samples=16 if draft else 48
 s.render.image_settings.file_format='PNG';s.render.filepath=str(folder/'frame-');s.frame_start=1;s.frame_end=192;s.render.fps=24
 bpy.ops.render.render(animation=True)
