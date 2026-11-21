import bpy,sys
from pathlib import Path
from mathutils import Vector,Quaternion
R=Path(__file__).parent;T=Path('C:/Users/rupjy/.codex/visualizations/2026/10/07/01a11802-03a6-7f71-9210-318d920a3def/NekoAFK-Blender-tools')
sys.path.insert(0,str(T));bpy.ops.preferences.addon_enable(module='io_scene_vrm')
def render(name,loc,target,scale,size=(900,900)):
 s=bpy.context.scene;c=bpy.data.objects['QA Camera'];s.camera=c;c.data.type='ORTHO';c.location=loc;c.rotation_euler=(Vector(target)-c.location).to_track_quat('-Z','Y').to_euler();c.data.ortho_scale=scale;s.render.resolution_x,s.render.resolution_y=size;s.render.resolution_percentage=100;s.eevee.taa_render_samples=32;s.render.image_settings.file_format='PNG';s.render.filepath=str(R/'renders'/name);bpy.context.view_layer.update();bpy.ops.render.render(write_still=True)
mode=sys.argv[-1] if sys.argv[-1] in ('before','after','contact','free') else 'after'
root=R.parent/'v001' if mode=='before' else R;v='v001' if mode=='before' else 'v002'
bpy.ops.wm.open_mainfile(filepath=str(root/f'NekoAFK-editing-{v}.blend'));s=bpy.context.scene;s.frame_set(1)
if mode in ('contact','free'):
 if mode=='contact':render('phone-grip-check.png',(-.80,-.04,1.20),(-.190,-.218,.922),.25)
 render('free-hand-check.png',(.7,-.8,1.04),(.108,-.225,.604),.30)
else:
 if '--details' not in sys.argv:
  render(mode+'-fullbody.png',(-2.5,-4.6,1.35),(0,-.065,.66),1.57,(900,1080))
  s.frame_set(51);render(mode+'-seated-feet.png',(-.9,-2,.63),(0,-.32,.24),.68)
 bpy.ops.wm.open_mainfile(filepath=str(root/f'NekoAFK-model-{v}.blend'))
 # Both saved model files must use the same rest pose for a fair detail comparison.
 for p in bpy.data.objects['Armature'].pose.bones:p.rotation_mode='QUATERNION';p.rotation_quaternion=(1,0,0,0);p.location=(0,0,0)
 render(mode+'-face.png',(-.20,-1.6,1.54),(0,-.025,1.475),.355)
 render(mode+'-nails.png',(.62,-.52,2.48),(.602,.016,1.311),.175)
print('CAPTURES_READY',mode,flush=True)
