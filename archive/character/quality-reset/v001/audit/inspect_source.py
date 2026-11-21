import bpy,sys,json
from pathlib import Path
T=Path('C:/Users/rupjy/.codex/visualizations/2026/10/07/01a11802-03a6-7f71-9210-318d920a3def/NekoAFK-Blender-tools')
sys.path.insert(0,str(T));bpy.ops.preferences.addon_enable(module='io_scene_vrm')
bpy.ops.wm.open_mainfile(filepath='D:/Projects/NekoAFK/assets/character/blender/NekoAFK-canon.blend')
d={}
d['objects']=[dict(name=o.name,type=o.type,verts=len(o.data.vertices) if o.type=='MESH' else 0,materials=[m.name if m else '' for m in o.data.materials] if o.type=='MESH' else [],modifiers=[(m.name,m.type) for m in o.modifiers],location=list(o.location)) for o in bpy.data.objects]
d['materials']=[]
for m in bpy.data.materials:
 if not m.users:continue
 q={'name':m.name,'toon':m.vrm_addon_extension.mtoon1.enabled,'nodes':[]}
 for n in m.node_tree.nodes if m.node_tree else []:
  if n.type in ('TEX_IMAGE','BSDF_PRINCIPLED','GROUP'):
   q['nodes'].append({'name':n.name,'type':n.type,'image':n.image.name if n.type=='TEX_IMAGE' and n.image else None,'inputs':[(i.name,str(i.default_value) if hasattr(i,'default_value') else '',i.is_linked) for i in n.inputs]})
 d['materials'].append(q)
d['bones']=[(b.name,list(b.head_local),list(b.tail_local)) for b in bpy.data.objects['Armature'].data.bones]
d['keys']=[k.name for k in bpy.data.objects['Face'].data.shape_keys.key_blocks]
Path(__file__).with_name('source-inspection.json').write_text(json.dumps(d,indent=2))
print('SOURCE_INSPECTED')
