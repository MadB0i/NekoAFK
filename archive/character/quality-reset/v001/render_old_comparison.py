import bpy,sys
from pathlib import Path
from mathutils import Vector
R=Path(__file__).parent;T=Path('C:/Users/rupjy/.codex/visualizations/2026/10/07/01a11802-03a6-7f71-9210-318d920a3def/NekoAFK-Blender-tools');sys.path.insert(0,str(T));bpy.ops.preferences.addon_enable(module='io_scene_vrm')
bpy.ops.wm.open_mainfile(filepath='D:/Projects/NekoAFK/assets/character/animations/NekoAFK-animation-library.blend');s=bpy.context.scene
for ob in [bpy.data.objects['Armature'],bpy.data.objects['Face'].data.shape_keys]:
 ad=ob.animation_data;ad.action=None
 for tr in ad.nla_tracks:tr.mute=tr.name!='Neko_EDITING_Idle'
c=bpy.data.objects['QA Camera'];s.camera=c;c.location=(-2.5,-4.6,1.35);c.rotation_euler=(Vector((0,-.065,.66))-c.location).to_track_quat('-Z','Y').to_euler();c.data.ortho_scale=1.57
s.frame_start=1;s.frame_end=192;s.render.fps=24;s.render.resolution_x=640;s.render.resolution_y=768;s.render.resolution_percentage=100;s.eevee.taa_render_samples=24;s.render.image_settings.file_format='PNG';folder=R/'old-frames';folder.mkdir(exist_ok=True);s.render.filepath=str(folder/'frame-');bpy.ops.render.render(animation=True)
