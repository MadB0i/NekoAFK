import bpy,gpu
from pathlib import Path
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(R/'NekoAFK-performance-v003.blend'))
s=bpy.context.scene;s.render.resolution_x=540;s.render.resolution_y=640;s.render.resolution_percentage=100;s.eevee.taa_render_samples=8;s.render.image_settings.file_format='PNG';s.render.filepath=str(R/'renders/probe-');s.frame_start=1;s.frame_end=4
for o in bpy.data.objects:
 if o.name=='Neko • continuous legs ankles and feet':
  for m in o.modifiers:
   if m.type=='SUBSURF':m.show_render=False
bpy.ops.render.render(animation=True)
print('GPU',gpu.platform.vendor_get(),gpu.platform.renderer_get(),gpu.platform.version_get(),flush=True)
print('PROBE_SUCCESS',flush=True)
