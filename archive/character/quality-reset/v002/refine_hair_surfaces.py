import bpy,sys
from pathlib import Path
R=Path(__file__).parent;T=Path('C:/Users/rupjy/.codex/visualizations/2026/10/07/01a11802-03a6-7f71-9210-318d920a3def/NekoAFK-Blender-tools');sys.path.insert(0,str(T));bpy.ops.preferences.addon_enable(module='io_scene_vrm')
for file in ['NekoAFK-model-v002.blend','NekoAFK-editing-v002.blend']:
 bpy.ops.wm.open_mainfile(filepath=str(R/file))
 for m in bpy.data.materials:
  if 'HAIR' not in m.name:continue
  m.use_backface_culling=True
  if hasattr(m,'use_backface_culling_shadow'):m.use_backface_culling_shadow=True
  for n in m.node_tree.nodes:
   if n.type=='BSDF_PRINCIPLED':n.inputs['Roughness'].default_value=.52;n.inputs['Specular IOR Level'].default_value=.11;n.inputs['Coat Weight'].default_value=0
   if n.type=='MIX_SHADER' and not n.inputs[0].is_linked:n.inputs[0].default_value=.30
 bpy.ops.wm.save_as_mainfile(filepath=str(R/file))
print('HAIR_SURFACES_REFINED',flush=True)
