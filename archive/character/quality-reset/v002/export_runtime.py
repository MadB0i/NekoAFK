"""Standalone glTF+MToon candidate; exports one skeletal/morph Action only."""
import bpy,sys,json,struct,math
from pathlib import Path
import numpy as np
R=Path(__file__).parent;T=Path('C:/Users/rupjy/.codex/visualizations/2026/10/07/01a11802-03a6-7f71-9210-318d920a3def/NekoAFK-Blender-tools')
sys.path.insert(0,str(T));bpy.ops.preferences.addon_enable(module='io_scene_vrm')
bpy.ops.wm.open_mainfile(filepath=str(R/'NekoAFK-editing-v002.blend'))
rig=bpy.data.objects['Armature'];scene=bpy.context.scene;scene.frame_set(1)
character=bpy.data.collections['NekoAFK • Character'];props=bpy.data.collections['QR01 • chair and phone']
objects=[o for o in list(character.all_objects)+list(props.all_objects) if o.type in ('MESH','ARMATURE') and o.visible_get()]
if rig not in objects:objects.append(rig)
# Apply surface modifiers in rest space, retaining all facial morph targets and weights.
for o in objects:
 if o.type!='MESH':continue
 mods=[m for m in o.modifiers if m.type!='ARMATURE' and m.show_viewport]
 if not mods:continue
 arm=[m for m in o.modifiers if m.type=='ARMATURE']
 for m in arm:m.show_viewport=False
 keys=o.data.shape_keys
 if keys:
  values={k.name:k.value for k in keys.key_blocks};saved_anim=keys.animation_data
  # Facial NLA must be muted during geometry evaluation.
  if saved_anim:
   saved_anim.action=None
   for tr in saved_anim.nla_tracks:tr.mute=True
  for k in keys.key_blocks:k.value=0
  bpy.context.view_layer.update();dep=bpy.context.evaluated_depsgraph_get();newmesh=bpy.data.meshes.new_from_object(o.evaluated_get(dep),preserve_all_data_layers=True,depsgraph=dep)
  coords={}
  for key in list(keys.key_blocks)[1:]:
   key.value=1;bpy.context.view_layer.update();eo=o.evaluated_get(dep);me=eo.to_mesh();arr=np.empty(len(me.vertices)*3,dtype=np.float32);me.vertices.foreach_get('co',arr);coords[key.name]=arr;eo.to_mesh_clear();key.value=0
  o.data=newmesh
  o.shape_key_add(name='Basis')
  for name,arr in coords.items():k=o.shape_key_add(name=name);k.data.foreach_set('co',arr);k.value=values[name]
  if o.name=='Face':
   act=bpy.data.actions['Neko_QR02_EDITING_PHONE_08s'];slot=next(s for s in act.slots if s.target_id_type=='KEY');ad=o.data.shape_keys.animation_data_create();tr=ad.nla_tracks.new();tr.name='QR02 • single refinement candidate';st=tr.strips.new(act.name,1,act);st.action_slot=slot;st.action_frame_start=1;st.action_frame_end=193;st.frame_start=1;st.frame_end=193;st.extrapolation='NOTHING'
 else:
  bpy.context.view_layer.update();dep=bpy.context.evaluated_depsgraph_get();o.data=bpy.data.meshes.new_from_object(o.evaluated_get(dep),preserve_all_data_layers=True,depsgraph=dep)
 for m in mods:o.modifiers.remove(m)
 for m in arm:m.show_viewport=True
# Standard base maps plus real VRMC_materials_mtoon extension, rather than extras.
mapping={};specs={}
for o in objects:
 if o.type!='MESH':continue
 for slot in o.material_slots:
  old=slot.material
  if not old or 'source_material' not in old:continue
  if old.name in mapping:slot.material=mapping[old.name];continue
  name=old.name;source=bpy.data.materials.get(old['source_material']);g=source.vrm_addon_extension.mtoon1 if source else None
  skin='SKIN' in name or 'warm skin' in name;hair='HAIR' in name or 'fur' in name;eyes='EYE' in name
  # Unused original MToon datablocks were pruned by Blender on save. Read the
  # preserved maps/factors from the active NPR material graph instead.
  nodes=old.node_tree.nodes
  image_node=next((n for n in nodes if n.type=='TEX_IMAGE' and n.image),None);im=image_node.image if image_node else None
  factor=[1,1,1,1]
  if im:
   mult=next((n for n in nodes if n.type=='MIX_RGB' and n.blend_type=='MULTIPLY' and n.inputs[1].is_linked and n.inputs[1].links[0].from_node==image_node and not n.inputs[2].is_linked),None)
   if mult:factor=list(mult.inputs[2].default_value)
  else:
   rgb=next((n for n in nodes if n.type=='RGB'),None)
   if rgb:factor=list(rgb.outputs[0].default_value)
  m=bpy.data.materials.new('MToon02 '+old['source_material']);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=factor;p.inputs['Roughness'].default_value=.48;p.inputs['Specular IOR Level'].default_value=.2
  if im:
   t=m.node_tree.nodes.new('ShaderNodeTexImage');t.image=im
   m.node_tree.links.new(t.outputs['Color'],p.inputs['Base Color'])
   # Factors are enforced explicitly in JSON so no exporter heuristic drops maps.
   m.node_tree.links.new(t.outputs['Alpha'],p.inputs['Alpha']);m.surface_render_method='DITHERED'
  shade=[.85,.72,.70] if skin else [.43,.40,.57] if hair else [.55,.55,.64]
  ext={'specVersion':'1.0','shadeColorFactor':[factor[i]*shade[i] for i in range(3)],'shadingShiftFactor':.02 if skin else -.12,'shadingToonyFactor':.35 if skin else .76,'giEqualizationFactor':.65,'parametricRimColorFactor':[.035,.026,.055] if hair else [.012,.009,.011],'parametricRimFresnelPowerFactor':4.5,'parametricRimLiftFactor':0,'rimLightingMixFactor':.75,'outlineWidthMode':'none','outlineWidthFactor':0,'outlineColorFactor':[.08,.06,.10],'outlineLightingMixFactor':1}
  specs[m.name]={'extension':ext,'factor':factor,'hair':'HAIR' in name,'use_map':bool(im),'alpha':'MASK' if im else 'OPAQUE'};mapping[old.name]=m;slot.material=m
for owner in (rig,bpy.data.objects['Face'].data.shape_keys):
 if owner.animation_data:
  for tr in owner.animation_data.nla_tracks:tr.name='Neko_QR02_EDITING_PHONE_08s'
scene.frame_end=193
scene.frame_set(1);bpy.context.view_layer.update();bpy.ops.object.select_all(action='DESELECT')
for o in objects:o.select_set(True)
bpy.context.view_layer.objects.active=rig
out=R/'NekoAFK-editing-v002-mtoon.glb'
assert bpy.ops.export_scene.gltf(filepath=str(out),export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='NLA_TRACKS',export_merge_animation='NLA_TRACK',export_morph=True,export_morph_animation=True,export_morph_normal=True,export_force_sampling=True,export_frame_range=True,export_anim_slide_to_zero=True,export_optimize_animation_size=True,export_skins=True,export_extras=True,export_vertex_color='ACTIVE',export_all_vertex_colors=False,export_cameras=False,export_lights=False)=={'FINISHED'}
raw=out.read_bytes();n,typ=struct.unpack_from('<II',raw,12);doc=json.loads(raw[20:20+n]);offset=20+n;blen,btyp=struct.unpack_from('<II',raw,offset);binary=raw[offset+8:offset+8+blen]
# Original analytic matcap: a broad off-axis lobe and narrow satin highlight.
# This is a material asset authored here, not a downloaded reference texture.
cap=bpy.data.images.new('QR02 original hair matcap',width=128,height=128,alpha=True)
px=np.zeros((128,128,4),dtype=np.float32)
for y in range(128):
 for x in range(128):
  u=x/127*2-1;v=y/127*2-1
  l=.48*math.exp(-((u+.30)/.36)**2-((v-.40)/.16)**2)+.10*math.exp(-((u-.42)/.22)**2-((v-.16)/.55)**2)
  px[y,x]=[l*.85,l*.81,l,1]
cap.pixels.foreach_set(px.ravel());cap.filepath_raw=str(R/'runtime-preview/hair-matcap.png');cap.file_format='PNG';cap.save()
png=Path(cap.filepath_raw).read_bytes();binary+=b'\x00'*((-len(binary))%4);bv=len(doc['bufferViews']);doc['bufferViews'].append({'buffer':0,'byteOffset':len(binary),'byteLength':len(png)});binary+=png
ii=len(doc['images']);doc['images'].append({'bufferView':bv,'mimeType':'image/png','name':'Neko original satin hair highlight'});ti=len(doc['textures']);doc['textures'].append({'source':ii})
for mat in doc['materials']:
 s=specs.get(mat['name'])
 if not s:continue
 mat.setdefault('extensions',{})['VRMC_materials_mtoon']=s['extension'];pbr=mat.setdefault('pbrMetallicRoughness',{});pbr['baseColorFactor']=s['factor'];pbr['metallicFactor']=0
 mat['extensions'].pop('KHR_materials_specular',None)
 if 'baseColorTexture' in pbr:s['extension']['shadeMultiplyTexture']=dict(pbr['baseColorTexture'])
 if s['alpha']!='OPAQUE':mat['alphaMode']='MASK';mat['alphaCutoff']=.35
 if s['hair']:
  s['extension']['matcapTexture']={'index':ti};s['extension']['matcapFactor']=[.11,.085,.14];mat['doubleSided']=False
doc.setdefault('extensionsUsed',[]).append('VRMC_materials_mtoon')
doc['buffers'][0]['byteLength']=len(binary)
js=json.dumps(doc,separators=(',',':')).encode();js+=b' '*((-len(js))%4);binary+=b'\x00'*((-len(binary))%4)
out.write_bytes(struct.pack('<III',0x46546c67,2,12+8+len(js)+8+len(binary))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(binary),0x004e4942)+binary)
report={'file':str(out),'materials':len(doc['materials']),'mtoon_materials':len(specs),'animations':[{'name':a['name'],'channels':len(a['channels']),'morph_channels':sum(c['target']['path']=='weights' for c in a['channels'])} for a in doc['animations']],'skins':len(doc['skins']),'largest_skin_joints':max(len(s['joints']) for s in doc['skins'])}
(R/'audit/runtime-export.json').write_text(json.dumps(report,indent=2));print('RUNTIME_EXPORTED',json.dumps(report),flush=True)
