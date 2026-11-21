"""Run with Blender GUI to prepare an actual editable viewport and capture it."""
import bpy
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1]
s=bpy.context.scene;s.frame_set(36)
bpy.ops.object.select_all(action='DESELECT')
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   sp=area.spaces.active;sp.region_3d.view_perspective='CAMERA';sp.region_3d.view_camera_zoom=3;sp.overlay.show_overlays=False
   sp.shading.type='MATERIAL';sp.shading.use_scene_world=False;sp.shading.use_scene_lights=False
def capture():
 for area in bpy.context.screen.areas:
  if area.type=='VIEW_3D':
   area.spaces.active.shading.type='SOLID';area.spaces.active.shading.light='STUDIO';area.spaces.active.shading.color_type='MATERIAL';area.spaces.active.overlay.show_overlays=False
   region=next(r for r in area.regions if r.type=='WINDOW')
   s.render.filepath=str(R/'renders/blender-solid-viewport.png')
   with bpy.context.temp_override(area=area,region=region):bpy.ops.render.opengl(write_still=True,view_context=True)
   area.spaces.active.shading.type='MATERIAL'
   break
 return None
bpy.app.timers.register(capture,first_interval=6)
