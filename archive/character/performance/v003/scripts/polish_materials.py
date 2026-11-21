import bpy,sys,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,'C:/Users/rupjy/.codex/visualizations/2026/10/07/01a11802-03a6-7f71-9210-318d920a3def/NekoAFK-Blender-tools');bpy.ops.preferences.addon_enable(module='io_scene_vrm')
bpy.ops.wm.open_mainfile(filepath=str(R/'NekoAFK-fashion-v003.blend'))
body=bpy.data.objects['Body'];skin=bpy.data.objects['Neko • continuous legs ankles and feet'].data.materials[0]
body.data.materials.append(skin);idx=len(body.data.materials)-1
for p in body.data.polygons:
 if p.material_index==0 and all(abs(body.data.vertices[i].co.x)>.475 for i in p.vertices):p.material_index=idx
for side in ['L','R']:
 o=bpy.data.objects.get('QR01.Wrist continuity.'+side)
 if o:bpy.data.objects.remove(o,do_unlink=True)
manifest={}
used={s.material for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render for s in o.material_slots if s.material}
for old in used:
 if not old.use_nodes or old.name.startswith('MToon03'):continue
 ns=old.node_tree.nodes;im=next((n for n in ns if n.type=='TEX_IMAGE' and n.image),None)
 p=next((n for n in ns if n.type=='BSDF_PRINCIPLED'),None);rgb=next((n for n in ns if n.type=='RGB'),None)
 factor=list(rgb.outputs[0].default_value) if rgb else list(p.inputs['Base Color'].default_value) if p else list(old.diffuse_color)
 if im:
  factor=[1,1,1,1]
  mult=next((n for n in ns if n.type=='MIX_RGB' and n.blend_type=='MULTIPLY' and n.inputs[1].is_linked and n.inputs[1].links[0].from_node==im and not n.inputs[2].is_linked),None)
  if mult:factor=list(mult.inputs[2].default_value)
 # Lacquer and metal remain physical materials; MToon supports skin/cloth/hair.
 if any(s in old.name.lower() for s in ['lacquer','inlay','clip','cuticle']):continue
 name='MToon03 • '+old.name.replace('QR01 • ','')
 m=bpy.data.materials.new(name);m.use_fake_user=True;m.vrm_addon_extension.mtoon1.enabled=True
 g=m.vrm_addon_extension.mtoon1;g.pbr_metallic_roughness.base_color_factor=factor
 if im:g.pbr_metallic_roughness.base_color_texture.index.source=im.image;g.alpha_mode='MASK';g.alpha_cutoff=.35
 skinmat='SKIN' in old.name or 'warm skin' in old.name;hair='HAIR' in old.name or 'fur' in old.name
 mt=g.extensions.vrmc_materials_mtoon;shade=(.84,.73,.73) if skinmat else (.46,.43,.60) if hair else (.55,.54,.63)
 mt.shade_color_factor=tuple(factor[i]*shade[i] for i in range(3));mt.shading_toony_factor=.45 if skinmat else .7;mt.shading_shift_factor=.02 if skinmat else -.08;mt.gi_equalization_factor=.65
 if im:mt.shade_multiply_texture.index.source=im.image
 mt.parametric_rim_color_factor=(.028,.019,.038) if hair else (.008,.006,.012);mt.parametric_rim_fresnel_power_factor=4;mt.rim_lighting_mix_factor=.7;mt.outline_width_mode='none'
 old['mtoon_companion']=m.name;m['beauty_companion']=old.name;manifest[old.name]=m.name
text=bpy.data.texts.new('README • Material modes and outfit variants')
text.write('NekoAFK v003 is a review candidate. Beauty uses the EEVEE art shader. Every mapped skin/hair/cloth material has a real registered VRM MToon 1.0 companion datablock with packed maps. Physical nails/metals remain PBR. Run the included switch_materials.py with MODE="MTOON" or "BEAUTY". MToon look is a portable approximation, not identical lighting.\nOriginal outfit: hide current Body, fashion collection and continuous legs object; show OPTIONAL original outfit. The original Face/Hair/rig are shared.\n')
(R/'audit/mtoon-material-map.json').write_text(json.dumps(manifest,indent=2))
print('ANATOMY_VERTICES',len(bpy.data.objects['Neko • continuous legs ankles and feet'].data.vertices),'MTOON',len(manifest),flush=True)
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(R/'NekoAFK-fashion-v003.blend'))
