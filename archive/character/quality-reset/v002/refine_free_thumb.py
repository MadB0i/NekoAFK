import bpy,sys,math
from pathlib import Path
from mathutils import Quaternion
R=Path(__file__).parent;T=Path('C:/Users/rupjy/.codex/visualizations/2026/10/07/01a11802-03a6-7f71-9210-318d920a3def/NekoAFK-Blender-tools');sys.path.insert(0,str(T));bpy.ops.preferences.addon_enable(module='io_scene_vrm')
bpy.ops.wm.open_mainfile(filepath=str(R/'NekoAFK-editing-v002.blend'));r=bpy.data.objects['Armature'];a=bpy.data.actions['Neko_QR02_EDITING_PHONE_08s'];slot=next(s for s in a.slots if s.target_id_type=='OBJECT');bag=a.layers[0].strips[0].channelbag(slot)
for name,angles in [('J_Bip_L_Thumb1',[((0,0,1),-8),((0,1,0),-22)]),('J_Bip_L_Thumb2',[((0,1,0),-3)])]:
 rest=r.data.bones[name].matrix_local.to_quaternion();q=Quaternion()
 for axis,deg in angles:q=q@Quaternion(axis,math.radians(deg))
 q=rest.inverted()@q@rest
 for fc in bag.fcurves:
  if fc.data_path==f'pose.bones["{name}"].rotation_quaternion':
   for k in fc.keyframe_points:k.co.y=q[fc.array_index]
   fc.update()
bpy.context.scene.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(R/'NekoAFK-editing-v002.blend'))
print('FREE_THUMB_CLEARANCE_REFINED',flush=True)
