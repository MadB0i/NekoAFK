import bpy,sys,math
from pathlib import Path
from mathutils import Vector,Quaternion
R=Path(__file__).parent;T=Path('C:/Users/rupjy/.codex/visualizations/2026/10/07/01a11802-03a6-7f71-9210-318d920a3def/NekoAFK-Blender-tools');sys.path.insert(0,str(T));bpy.ops.preferences.addon_enable(module='io_scene_vrm')
bpy.ops.wm.open_mainfile(filepath=str(R/'NekoAFK-editing-v001.blend'));s=bpy.context.scene;r=bpy.data.objects['Armature'];s.frame_set(19)
def capture(name,loc,target,scale,size):
 c=bpy.data.objects['QA Camera'];s.camera=c;c.location=loc;c.rotation_euler=(Vector(target)-c.location).to_track_quat('-Z','Y').to_euler();c.data.ortho_scale=scale;s.render.resolution_x,s.render.resolution_y=size;s.render.resolution_percentage=100;s.eevee.taa_render_samples=64;s.render.filepath=str(R/'renders'/name);bpy.ops.render.render(write_still=True)
capture('phone-contact-closeup.png',(-1.0,.0,1.2),(-.205,-.215,.9),.235,(1200,1200))
if '--contact-only' not in sys.argv:
 s.frame_set(1);capture('fullbody-three-quarter.png',(-2.5,-4.6,1.35),(0,-.065,.66),1.57,(1200,1440))
 s.frame_set(51);capture('seated-leg-foot.png',(-.9,-2,.63),(0,-.32,.24),.68,(1200,1200))
r.animation_data_clear()
def rot(n,d):
 q=r.data.bones[n].matrix_local.to_quaternion();r.pose.bones[n].rotation_quaternion=q.inverted()@Quaternion((1,0,0),math.radians(d))@q
rot('J_Bip_L_Foot',14);rot('J_Bip_R_Foot',-19);rot('J_Bip_L_UpperLeg',-100)
for side in ['L','R']:
 for i in range(1,6):rot(f'Neko_{side}_Toe{i:02d}_Prox',9 if side=='L' else -5);rot(f'Neko_{side}_Toe{i:02d}_Dist',6 if side=='L' else -3)
bpy.context.view_layer.update();ev=bpy.data.objects['NekoBareFeet • anatomical skin'].evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();print('DEFORMATION_POSE_MIN_Z',min(v.co.z for v in me.vertices),flush=True);ev.to_mesh_clear();capture('ankle-toe-deformation-check.png',(-.75,-1.5,.44),(0,-.32,.17),.48,(1200,1200))
