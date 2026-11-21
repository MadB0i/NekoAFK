import bpy,sys,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,'C:/Users/rupjy/.codex/visualizations/2026/10/07/01a11802-03a6-7f71-9210-318d920a3def/NekoAFK-Blender-tools');bpy.ops.preferences.addon_enable(module='io_scene_vrm')
bpy.ops.wm.open_mainfile(filepath=str(R/'NekoAFK-performance-v003.blend'))
s=bpy.context.scene;c=bpy.data.objects['QA Camera'];s.camera=c;s.eevee.taa_render_samples=32;s.render.image_settings.file_format='PNG'
def render(name,f,loc,target,scale,size):
 s.frame_set(f);c.data.type='ORTHO';c.location=loc;c.rotation_euler=(Vector(target)-c.location).to_track_quat('-Z','Y').to_euler();c.data.ortho_scale=scale;s.render.resolution_x,s.render.resolution_y=size;s.render.resolution_percentage=100;s.render.filepath=str(R/'renders'/name);bpy.ops.render.render(write_still=True)
mode=sys.argv[-1]
if mode=='beats':
 for f in [1,132,161,199,229,285,335]:render(f'beat-{f:03d}.png',f,(-2.15,-4.8,1.72),(0,-.07,.66),1.62,(720,840))
elif mode=='details':
 render('beauty-seated.png',36,(-2.15,-4.8,1.72),(0,-.07,.66),1.62,(1320,1500))
 render('face-relaxed.png',36,(-.35,-1.8,1.29),(0,-.066,1.08),.36,(1300,1300))
 render('face-frustrated.png',224,(-.45,-1.8,1.30),(-.015,.016,1.10),.39,(1300,1300))
 render('nails-and-grip.png',36,(-.40,-1.5,1.23),(0,-.29,.87),.30,(1400,1400))
 render('screen-thumb-contact.png',36,(.75,.38,1.25),(0,-.27,.88),.30,(1200,1200))
 render('seated-outfit.png',36,(-.65,-1.7,.99),(0,-.15,.55),.75,(1300,1300))
 render('feet-ankles.png',36,(-.65,-1.5,.47),(0,-.4,.15),.43,(1200,1200))
elif mode=='video':
 c.location=(-2.15,-4.8,1.72);c.rotation_euler=(Vector((0,-.07,.66))-c.location).to_track_quat('-Z','Y').to_euler();c.data.ortho_scale=1.62
 s.render.resolution_x=960;s.render.resolution_y=1080;s.render.resolution_percentage=100;s.eevee.taa_render_samples=24;s.render.image_settings.color_mode='RGB';s.render.filepath=str(R/'frames/frame-');s.render.use_file_extension=True
 s.render.use_persistent_data=True;s.render.use_overwrite=False
 bpy.ops.render.render(animation=True)
else:
 render('current-pose.png',36,(-2.15,-4.8,1.72),(0,-.07,.66),1.62,(850,1000))
 render('current-grip.png',36,(-.4,-1.5,1.23),(0,-.29,.87),.30,(1000,1000))
print('RENDER_REVIEW_DONE',mode,flush=True)
