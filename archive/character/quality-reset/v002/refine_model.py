"""Incremental, reversible refinements; no imported character assets."""
import bpy,bmesh,sys,math,json
import numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion
from mathutils.kdtree import KDTree
R=Path(__file__).parent;T=Path('C:/Users/rupjy/.codex/visualizations/2026/10/07/01a11802-03a6-7f71-9210-318d920a3def/NekoAFK-Blender-tools')
sys.path.insert(0,str(T));bpy.ops.preferences.addon_enable(module='io_scene_vrm')
bpy.ops.wm.open_mainfile(filepath=str(R.parent/'v001/NekoAFK-model-v001.blend'))
scene=bpy.context.scene;rig=bpy.data.objects['Armature'];face=bpy.data.objects['Face'];body=bpy.data.objects['Body'];hair=bpy.data.objects['Hair']
for p in rig.pose.bones:p.rotation_quaternion=(1,0,0,0);p.location=(0,0,0)
for k in face.data.shape_keys.key_blocks:k.value=0
char=bpy.data.collections['NekoAFK • Character'];bare=bpy.data.collections['DEFAULT • barefoot']
# Relax polygon ridges without collapsing the individually weighted hair locks.
bm=bmesh.new();bm.from_mesh(hair.data)
for _ in range(3):bmesh.ops.smooth_vert(bm,verts=[v for v in bm.verts if not v.is_boundary],factor=.18,use_axis_x=True,use_axis_y=True,use_axis_z=True)
bm.to_mesh(hair.data);bm.free()
sub=hair.modifiers.new('QR02 • polished lock surfaces','SUBSURF');sub.levels=1;sub.render_levels=1
# Small jaw/lip refinements are applied identically to every expression target.
for i,v in enumerate(face.data.vertices):
 p=v.co;front=max(0,min(1,(-p.y-.015)/.04));jaw=math.exp(-((p.z-1.399)/.028)**2)*front
 delta=Vector((p.x*.012*jaw,-.00065*math.exp(-(p.x/.027)**2-((p.z-1.418)/.005)**2)*front,.0012*math.exp(-(p.x/.018)**2-((p.z-1.382)/.017)**2)*front))
 for k in face.data.shape_keys.key_blocks:k.data[i].co+=delta
# Surface color keeps cheeks/lips understated; lower lip has a narrow satin sheen.
for mat in bpy.data.materials:
 if not mat.use_nodes:continue
 name=mat.name;skin='SKIN' in name or 'warm skin' in name;h='HAIR' in name;eye='EYE' in name
 for n in mat.node_tree.nodes:
  if n.type=='BSDF_PRINCIPLED':
   if skin:n.inputs['Roughness'].default_value=.48;n.inputs['Subsurface Weight'].default_value=.035
   if h:n.inputs['Roughness'].default_value=.43;n.inputs['Specular IOR Level'].default_value=.17;n.inputs['Anisotropic'].default_value=.65;n.inputs['Coat Weight'].default_value=.045
   if eye:n.inputs['Roughness'].default_value=.16;n.inputs['Coat Weight'].default_value=.55
  if n.type=='VALTORGB' and (skin or h):
   n.color_ramp.interpolation='EASE'
   es=sorted(n.color_ramp.elements,key=lambda e:e.position)
   if len(es)==3:
    es[0].color=(.68,.48,.47,1) if skin else (.22,.22,.34,1)
    es[1].position=.41;es[1].color=(.90,.77,.73,1) if skin else (.55,.53,.71,1)
    es[2].position=.62
  if n.type=='MIX_SHADER' and not n.inputs[0].is_linked:
   if skin:n.inputs[0].default_value=.42
   elif h:n.inputs[0].default_value=.42
 mat['QR02_runtime']='MToon extension for skin/hair/cloth; physical lacquer and metal remain PBR.'
# Additional tapered locks follow existing hair skinning, including lag bones.
kd=KDTree(len(hair.data.vertices))
for v in hair.data.vertices:kd.insert(v.co,v.index)
kd.balance()
def strand(name,pts,width,mat):
 vs=[];fs=[]
 for j in range(25):
  t=j/24;p=(1-t)**3*Vector(pts[0])+3*(1-t)**2*t*Vector(pts[1])+3*(1-t)*t*t*Vector(pts[2])+t**3*Vector(pts[3]);w=width*(.6+.4*math.sin(math.pi*t))*(1-t)**.65+.000035
  for u in (-1,0,1):vs.append(tuple(p+Vector((u*w,-.0007*(1-u*u)*(1-t),0))))
  if j:
   for c in range(2):a=(j-1)*3+c;fs.append((a,a+1,a+4,a+3))
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(name,me);char.objects.link(o);o.parent=rig;o.data.materials.append(mat)
 groups={}
 for v in me.vertices:
  _,idx,_=kd.find(v.co)
  for g in hair.data.vertices[idx].groups:
   n=hair.vertex_groups[g.group].name
   if n not in groups:groups[n]=o.vertex_groups.new(name=n)
   groups[n].add([v.index],g.weight,'REPLACE')
 for p in me.polygons:p.use_smooth=True
 m=o.modifiers.new('Existing hair chain weights','ARMATURE');m.object=rig
 m=o.modifiers.new('Fine strand thickness','SOLIDIFY');m.thickness=.00025
for side in (-1,1):
 for j in range(3):
  strand(f'QR02.Hair-tip.{side}.{j}',[(side*(.080+j*.004),-.048,1.43-j*.014),(side*(.092+j*.006),-.065,1.365-j*.012),(side*(.095+j*.004),-.071,1.307-j*.007),(side*(.110+j*.004),-.063,1.283-j*.010)],.0018,hair.data.materials[0])
# Fine amber subdivision beside the existing broad canonical accent.
amber=hair.data.materials[1]
# Keep the canonical amber lock: an unattached accent strand failed the first visual check.
# Retain the existing toe rig and improve ankle transitions with volume-preserving local relaxation.
feet=bpy.data.objects['NekoBareFeet • anatomical skin'];bm=bmesh.new();bm.from_mesh(feet.data)
for _ in range(3):bmesh.ops.smooth_vert(bm,verts=[v for v in bm.verts if .045<v.co.z<.12 and v.co.y>-.05],factor=.10,use_axis_x=True,use_axis_y=True,use_axis_z=True)
bm.to_mesh(feet.data);bm.free()
for v in feet.data.vertices:
 p=v.co;s=1 if p.x>0 else -1
 # A subtle Achilles groove and medial instep; heel/toe contact volumes stay unchanged.
 if p.y>.020:p.y-=.0012*math.exp(-((p.z-.075)/.033)**2-((abs(p.x)-.077)/.012)**2)
 p.z+=.0008*math.exp(-((abs(p.x)-.068)/.018)**2-((p.y+.025)/.03)**2-((p.z-.049)/.014)**2)
# Split toe weights are smoothed only across their own anatomical toe region.
for s in ('L','R'):
 for i in range(1,6):
  prox=feet.vertex_groups.get(f'Neko_{s}_Toe{i:02d}_Prox');dist=feet.vertex_groups.get(f'Neko_{s}_Toe{i:02d}_Dist')
  if not prox or not dist:continue
  b=rig.data.bones[dist.name];a=b.head_local;y=b.tail_local;axis=(y-a).normalized();length=(y-a).length
  for v in feet.data.vertices:
   weights={g.group:g.weight for g in v.groups};total=weights.get(prox.index,0)+weights.get(dist.index,0)
   if total<.3:continue
   t=max(0,min(1,((v.co-a).dot(axis)+.004)/(length*.7+.004)));t=t*t*(3-2*t)
   prox.add([v.index],total*(1-t),'REPLACE');dist.add([v.index],total*t,'REPLACE')
# Cuffs retain their opening but use a softer, less rigid silhouette.
for s in ('L','R'):
 o=bpy.data.objects['NekoJoggerCuff.'+s]
 for v in o.data.vertices:
  v.co.z+=.0009*math.sin(v.co.x*85)*math.sin(v.co.y*70)
# A portable original lacquer texture replaces a Blender-only color ramp.
tex=bpy.data.images.new('QR02 • lacquer gradient',width=256,height=256,alpha=True)
pixels=np.zeros((256,256,4),dtype=np.float32)
for y in range(256):
 t=y/255;s=max(0,min(1,(t-.3)/.68));s=s*s*(3-2*s);col=np.array((.006,.003,.012))*(1-s)+np.array((.49,.145,.020))*s
 pixels[y,:,:3]=col;pixels[y,:,3]=1
tex.pixels.foreach_set(pixels.ravel());tex.pack()
m=bpy.data.materials['QR01 • obsidian amber lacquer'];p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');im=m.node_tree.nodes.new('ShaderNodeTexImage');im.image=tex;m.node_tree.links.new(im.outputs['Color'],p.inputs['Base Color']);p.inputs['Roughness'].default_value=.20;p.inputs['Coat Weight'].default_value=.82;p.inputs['Coat Roughness'].default_value=.10
# Less overexposed skin, cleaner colored separation in hair.
scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=-.06
scene.eevee.taa_render_samples=48
for ob in bpy.data.objects:
 if ob.type=='LIGHT' and 'rim' in ob.name.lower():ob.data.energy*=1.2
face.data.shape_keys.key_blocks['Fcl_MTH_Fun'].value=.16
face.data.shape_keys.key_blocks['Fcl_BRW_Fun'].value=.055
face.data.shape_keys.key_blocks['Fcl_EYE_Natural'].value=.05
rig['QR02_scope']='One editing clip only. Original armature, facial keys, tail/ears and socks preserved.'
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(R/'NekoAFK-model-v002.blend'))
print('MODEL_REFINED',flush=True)
