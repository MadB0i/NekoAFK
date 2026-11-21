import bpy,bmesh,math,sys,json
import numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
ROOT=Path(__file__).parent; T=Path('C:/Users/rupjy/.codex/visualizations/2026/10/07/01a11802-03a6-7f71-9210-318d920a3def/NekoAFK-Blender-tools')
sys.path.insert(0,str(T)); bpy.ops.preferences.addon_enable(module='io_scene_vrm')
bpy.ops.wm.open_mainfile(filepath='D:/Projects/NekoAFK/assets/character/blender/NekoAFK-canon.blend')
scene=bpy.context.scene; rig=bpy.data.objects['Armature'];body=bpy.data.objects['Body'];face=bpy.data.objects['Face']
character=bpy.data.collections['NekoAFK • Character'];bare=bpy.data.collections['DEFAULT • barefoot']
for o in list(bpy.data.objects):
 if o.name.startswith('QA ') and o.type!='CAMERA': bpy.data.objects.remove(o,do_unlink=True)
for o in (rig,face.data.shape_keys):
 if o.animation_data:o.animation_data_clear()
for p in rig.pose.bones:p.rotation_mode='QUATERNION';p.rotation_quaternion=(1,0,0,0);p.location=(0,0,0);p.scale=(1,1,1)
for k in face.data.shape_keys.key_blocks:k.value=0
for o in character.all_objects:
 for m in list(o.modifiers):
  if m.name.startswith('MToon Outline'):o.modifiers.remove(m)

def material(name,color,rough=.45,metal=0):
 m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
 return m

# Preserve painted identity maps, replace the flat matcap response with a soft NPR
# light ramp and physical highlights. Shader-to-RGB is intentionally EEVEE source.
def anime_material(old):
 name=old.name; skin=('SKIN' in name or 'warm skin' in name); hair=('HAIR' in name or 'fur' in name); eye='EYE' in name
 nold=old.node_tree.nodes.get('Mtoon1BaseColorTexture.Image') if old.node_tree else None
 tex=nold.image if nold else None
 factor=tuple(old.vrm_addon_extension.mtoon1.pbr_metallic_roughness.base_color_factor)
 if skin:factor=tuple(factor[i]*[.78,.62,.55,1][i] for i in range(4))
 if 'warm skin' in name:factor=(.78,.62,.55,1)
 if 'FaceBrow' in name:factor=(.11,.065,.09,1)
 if 'FaceEyeline' in name:factor=(.18,.12,.18,1)
 m=bpy.data.materials.new('QR01 • '+name);m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;n.clear()
 out=n.new('ShaderNodeOutputMaterial');p=n.new('ShaderNodeBsdfPrincipled');p.inputs['Roughness'].default_value=.58 if skin else .48 if hair else .23 if eye else .78
 p.inputs['Specular IOR Level'].default_value=.22 if skin else .14 if hair else .4 if eye else .18
 if 'fur' in name:p.inputs['Roughness'].default_value=.82;p.inputs['Specular IOR Level'].default_value=.08
 if skin:p.inputs['Subsurface Weight'].default_value=.045;p.inputs['Subsurface Scale'].default_value=.006
 if eye:p.inputs['Coat Weight'].default_value=.7;p.inputs['Coat Roughness'].default_value=.10
 if hair:p.inputs['Anisotropic'].default_value=.5
 if tex:
  im=n.new('ShaderNodeTexImage');im.image=tex
  col=im.outputs['Color']
  mult=n.new('ShaderNodeMixRGB');mult.blend_type='MULTIPLY';mult.inputs[0].default_value=1;mult.inputs[2].default_value=factor;l.new(col,mult.inputs[1]);col=mult.outputs[0]
 else:
  rgb=n.new('ShaderNodeRGB');rgb.outputs[0].default_value=factor;col=rgb.outputs[0]
 if 'Face_00_SKIN' in name:
  attr=n.new('ShaderNodeVertexColor');attr.layer_name='QR01 skin warmth';mu=n.new('ShaderNodeMixRGB');mu.blend_type='MULTIPLY';mu.inputs[0].default_value=1;l.new(col,mu.inputs[1]);l.new(attr.outputs['Color'],mu.inputs[2]);col=mu.outputs[0]
 l.new(col,p.inputs['Base Color'])
 diff=n.new('ShaderNodeBsdfDiffuse');diff.inputs['Color'].default_value=(.8,.8,.8,1);s=n.new('ShaderNodeShaderToRGB');l.new(diff.outputs[0],s.inputs[0])
 ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.interpolation='EASE'
 ramp.color_ramp.elements[0].position=.10;ramp.color_ramp.elements[0].color=(.55,.39,.40,1) if skin else (.30,.31,.42,1)
 ramp.color_ramp.elements[1].position=.72;ramp.color_ramp.elements[1].color=(1,.95,.88,1) if skin else (1,1,1,1)
 mid=ramp.color_ramp.elements.new(.38);mid.color=(.83,.70,.65,1) if skin else (.62,.63,.75,1);l.new(s.outputs[0],ramp.inputs[0])
 mul=n.new('ShaderNodeMixRGB');mul.blend_type='MULTIPLY';mul.inputs[0].default_value=1;l.new(col,mul.inputs[1]);l.new(ramp.outputs[0],mul.inputs[2])
 em=n.new('ShaderNodeEmission');l.new(mul.outputs[0],em.inputs[0]);mix=n.new('ShaderNodeMixShader');mix.inputs[0].default_value=.62 if skin else .38 if hair else .4 if eye else .3;l.new(em.outputs[0],mix.inputs[1]);l.new(p.outputs[0],mix.inputs[2]);surface=mix.outputs[0]
 if tex:
  trans=n.new('ShaderNodeBsdfTransparent');alpha=n.new('ShaderNodeMixShader');l.new(im.outputs['Alpha'],alpha.inputs[0]);l.new(trans.outputs[0],alpha.inputs[1]);l.new(surface,alpha.inputs[2]);surface=alpha.outputs[0]
 l.new(surface,out.inputs[0]);m.surface_render_method='DITHERED';m['source_material']=name;m['render_note']='Soft toon ramp + physical specular. EEVEE art shader; runtime shader port required.'
 return m
mapping={}
warmth=face.data.color_attributes.new(name='QR01 skin warmth',type='FLOAT_COLOR',domain='CORNER')
for lp in face.data.loops:
 p=face.data.vertices[lp.vertex_index].co;front=max(0,min(1,(-p.y-.025)/.04))
 cheek=math.exp(-((abs(p.x)-.047)/.022)**2-((p.z-1.440)/.019)**2)*front
 lip=math.exp(-(p.x/.020)**4-((p.z-1.417)/.0038)**2)*front
 warmth.data[lp.index].color=(1-.03*cheek-.12*lip,1-.13*cheek-.34*lip,1-.11*cheek-.28*lip,1)
for o in character.all_objects:
 if o.type!='MESH':continue
 for slot in o.material_slots:
  old=slot.material
  if not old:continue
  if old.name not in mapping:mapping[old.name]=anime_material(old)
  slot.material=mapping[old.name]
 for p in o.data.polygons:p.use_smooth=True

# Remove the flat lacquer overlays in this version only.
for name in ['NekoManicure • black and amber','NekoPedicure • black and amber']:
 bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)

# Relax triangular surface ridges, retaining original joint locations and UVs.
bm=bmesh.new();bm.from_mesh(body.data)
for _ in range(5):bmesh.ops.smooth_vert(bm,verts=[v for v in bm.verts if abs(v.co.x)>.545],factor=.16,use_axis_x=True,use_axis_y=True,use_axis_z=True)
bm.to_mesh(body.data);bm.free()
sub=body.modifiers.new('Surface refinement • hands and cloth','SUBSURF');sub.levels=1;sub.render_levels=1
# Face subdivision retains every existing facial expression and paints.
sub=face.modifiers.new('Face surface refinement','SUBSURF');sub.levels=1;sub.render_levels=1
for label in ('L','R'):
 o=bpy.data.objects['NekoJoggerCuff.'+label]
 sub=o.modifiers.new('Soft ribbed cuff edges','SUBSURF');sub.levels=2;sub.render_levels=2

feet=bpy.data.objects['NekoBareFeet • anatomical skin']
# Smooth the excessively decimated surface, add medial arch, heel and ankle form.
bm=bmesh.new();bm.from_mesh(feet.data)
for _ in range(7):bmesh.ops.smooth_vert(bm,verts=[v for v in bm.verts if v.co.z<.155],factor=.23,use_axis_x=True,use_axis_y=True,use_axis_z=True)
bm.to_mesh(feet.data);bm.free()
for v in feet.data.vertices:
 p=v.co;x=abs(p.x);s=1 if p.x>0 else -1
 # Lift the medial arch without moving the toe ball or heel contact patches.
 medial=math.exp(-((x-.052)/.016)**2);mid=math.exp(-((p.y+.008)/.034)**2)
 if p.z<.065:p.z+=.0060*medial*mid*math.exp(-((p.z-.014)/.025)**2)
 # Softer Achilles taper; small malleoli, not a cylindrical ankle.
 a=math.exp(-((p.z-.082)/.018)**2)*math.exp(-((p.y-.035)/.033)**2)
 p.x+=s*.0006*a*(1 if x>.073 else -1)
# Preserve all ten toe volumes and their exact skin weights. Pair compatible
# triangles locally; global automatic remeshing was rejected by visual QA.
bm=bmesh.new();bm.from_mesh(feet.data)
bmesh.ops.join_triangles(bm,faces=list(bm.faces),angle_face_threshold=.70,angle_shape_threshold=.80)
bm.to_mesh(feet.data);bm.free()
for p in feet.data.polygons:p.use_smooth=True
print('FEET_SURFACE',len(feet.data.vertices),len(feet.data.polygons),flush=True)
sub=feet.modifiers.new('Smooth heel arch and toe silhouette','SUBSURF');sub.levels=1;sub.render_levels=1

def mesh(name,vs,fs,mat,col,weights=None,uvs=None):
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(name,me);col.objects.link(o);me.materials.append(mat)
 for p in me.polygons:p.use_smooth=True
 if uvs:
  uv=me.uv_layers.new(name='Nail design')
  for loop in me.loops:uv.data[loop.index].uv=uvs[loop.vertex_index]
 if weights:
  for i,ws in enumerate(weights):
   for bn,w in ws.items():
    g=o.vertex_groups.get(bn) or o.vertex_groups.new(name=bn);g.add([i],w,'REPLACE')
  mod=o.modifiers.new('Canonical skeleton','ARMATURE');mod.object=rig;o.parent=rig
 return o
gold=material('QR01 • brushed gold micro-inlay',(.65,.32,.061),.24,.82)
clip=bpy.data.objects['NekoAmberClip • permanent'];clip.data.materials.clear();clip.data.materials.append(gold);be=clip.modifiers.new('Hair clip softened metal edge','BEVEL');be.width=.00065;be.segments=3
for side,sg in [('L',1),('R',-1)]:
 vs=[];fs=[];ws=[]
 for j in range(9):
  t=j/8;x=.495+.041*t
  for i in range(32):
   a=math.tau*i/32;vs.append((sg*x,.02499+.0175*math.cos(a),1.30932+.0117*math.sin(a)));w=max(0,min(1,(t-.15)/.60));ws.append({f'J_Bip_{side}_LowerArm':1-w,f'J_Bip_{side}_Hand':w})
   if j:aa=j*32+i;bb=j*32+(i+1)%32;fs.append((aa-32,bb-32,bb,aa) if sg==1 else (aa,bb,bb-32,aa-32))
 mesh('QR01.Wrist continuity.'+side,vs,fs,body.data.materials[0],character,ws)
cuticle=material('QR01 • soft cuticle',(.67,.41,.34),.62)
nailmat=material('QR01 • obsidian amber lacquer',(.01,.007,.018),.26,.08)
p=nailmat.node_tree.nodes.get('Principled BSDF');p.inputs['Coat Weight'].default_value=.65;p.inputs['Coat Roughness'].default_value=.16
n=nailmat.node_tree.nodes;l=nailmat.node_tree.links;uv=n.new('ShaderNodeTexCoord');sep=n.new('ShaderNodeSeparateXYZ');l.new(uv.outputs['UV'],sep.inputs[0]);r=n.new('ShaderNodeValToRGB');r.color_ramp.elements[0].position=.30;r.color_ramp.elements[0].color=(.005,.003,.010,1);r.color_ramp.elements[1].position=.98;r.color_ramp.elements[1].color=(.48,.14,.018,1);e=r.color_ramp.elements.new(.72);e.color=(.08,.016,.009,1);l.new(sep.outputs['Y'],r.inputs[0]);l.new(r.outputs[0],p.inputs['Base Color'])

def evaluated_surface(o):
 bpy.context.view_layer.update();dep=bpy.context.evaluated_depsgraph_get();ev=o.evaluated_get(dep);me=ev.to_mesh();vs=[v.co.copy() for v in me.vertices];fs=[tuple(p.vertices) for p in me.polygons];bvh=BVHTree.FromPolygons(vs,fs);ev.to_mesh_clear();return bvh
handbvh=evaluated_surface(body);footbvh=evaluated_surface(feet)
def rayheight(bvh,p):
 h,no,idx,d=bvh.ray_cast(Vector((p.x,p.y,p.z+.2)),Vector((0,0,-1)),.4)
 return h.z if h is not None else p.z

def acrylic(name,base,axis,width,length,bone,bvh,extension=True,col=character):
 axis=Vector((axis.x,axis.y,0)).normalized();across=axis.cross(Vector((0,0,1))).normalized();base=base.copy()
 # Fit a smooth nail bed to the actual digit. Distal free edge continues its tangent.
 samples=[]
 for t in np.linspace(0,.56,8):
  q=base+axis*(length*t);samples.append((t,rayheight(bvh,q)))
 slope,intercept=np.polyfit([v[0] for v in samples],[v[1] for v in samples],1)
 slope=max(-.004,min(.004,float(slope)))
 def surface(u,t):
  # Rounded proximal edge, full stress area, almond taper at free edge.
  if extension:w=width*(max(.0001,t)**.38*max(.0001,1-t)**.55)/(.409**.38*.591**.55)
  else:w=width*math.sqrt(max(.0001,1-(2*t-1)**2))
  q=base+axis*(length*t)+across*(w*u)
  q.z=intercept+slope*t+.00045+(.00145 if extension else .00065)*(1-u*u)*math.sin(math.pi*(.16+.7*t))-.00050*max(0,(t-.65)/.35)**2
  return q
 vs=[];fs=[];uvs=[];rows=28;cols=16
 for j in range(rows+1):
  for k in range(cols+1):vs.append(tuple(surface(k/cols*2-1,j/rows)));uvs.append((k/cols,j/rows))
 for j in range(rows):
  for k in range(cols):a=j*(cols+1)+k;fs.append((a,a+1,a+cols+2,a+cols+1))
 o=mesh(name,vs,fs,nailmat,col,[{bone:1}]*len(vs),uvs)
 solid=o.modifiers.new('Acrylic free-edge thickness','SOLIDIFY');solid.thickness=.00038 if extension else .00015;solid.offset=-1
 bevel=o.modifiers.new('Polished acrylic edge','BEVEL');bevel.width=.00012;bevel.segments=2
 # Fine asymmetric gold sweep: actual inlay geometry, not a painted circular dot.
 iv=[];iff=[]
 for j in range(35):
  t=.32+j/34*.60;u=.73-.40*math.sin(j/34*math.pi)
  for du in (-.019,.019):q=surface(u+du,t);q.z+=.00006;iv.append(tuple(q))
  if j:a=2*j;iff.append((a-2,a-1,a+1,a))
 mesh(name+' • gold filament',iv,iff,gold,col,[{bone:1}]*len(iv))
 # Thin proximal skin fold follows the nail bed, absent at the free edge.
 cv=[];cf=[]
 for j in range(21):
  u=-.92+1.84*j/20
  for tt in (.025,.047):q=surface(u,tt);q.z+=.00006;cv.append(tuple(q))
  if j:a=2*j;cf.append((a-2,a-1,a+1,a))
 mesh(name+' • proximal fold',cv,cf,cuticle,col,[{bone:1}]*len(cv))
 return o

for side in ('L','R'):
 for finger in ('Thumb','Index','Middle','Ring','Little'):
  bn=f'J_Bip_{side}_{finger}3';b=rig.data.bones[bn];axis=(b.tail_local-b.head_local).normalized();g=body.vertex_groups[bn]
  candidates=[v.co.copy() for v in body.data.vertices if any(w.group==g.index and w.weight>.65 for w in v.groups)]
  tip=max((v-b.head_local).dot(axis) for v in candidates)
  base=b.head_local+axis*(tip-(.0090 if finger=='Thumb' else .0105))
  acrylic(f'QR01.Nail.{side}.{finger}',base,axis,.0037 if finger=='Thumb' else .00335 if finger!='Little' else .0028,.0158 if finger!='Thumb' else .014,bn,handbvh)
for side,s in [('L',1),('R',-1)]:
 for i,(cx,tip) in enumerate(zip([.0558,.0711,.0841,.0953,.1044],[-.115,-.112,-.105,-.096,-.088])):
  base=Vector((s*cx,tip+(.014 if i==0 else .011),.027))
  acrylic(f'QR01.Pedicure.{side}.{i+1}',base,Vector((0,-1,0)),.0051 if i==0 else .0032 if i==1 else .0025,.0118 if i==0 else .0088,f'Neko_{side}_Toe{i+1:02d}_Dist',footbvh,False,bare)

# Clean, deliberately shaped studio lighting, with no translucent character overlay.
studio=bpy.data.collections.new('QR01 • render studio');scene.collection.children.link(studio)
def light(name,loc,target,energy,size,color,shape='DISK',size_y=None):
 d=bpy.data.lights.new(name,'AREA');d.energy=energy;d.shape=shape;d.size=size;d.color=color
 if size_y is not None:d.size_y=size_y
 o=bpy.data.objects.new(name,d);studio.objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();return o
light('QR01 Key softbox',(-1.3,-2.1,2.7),(0,0,1),180,1.8,(1,.88,.77))
light('QR01 Cool fill',(1.5,-1.1,1.9),(0,0,1),65,1.5,(.72,.79,1))
light('QR01 Hair rim',(.5,.95,2.2),(0,0,1.05),75,1.3,(.79,.71,1))
light('QR01 Nail strip',(-.3,-1.6,1.8),(0,0,1),45,.13,(1,.91,.78),'RECTANGLE',1.2)
world=bpy.data.worlds.new('QR01 • midnight studio');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.028,.035,.058,1);world.node_tree.nodes['Background'].inputs[1].default_value=.35;scene.world=world
floor=material('QR01 • studio floor',(.031,.041,.063),.87)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.012));o=bpy.context.object;o.name='QR01 Studio cyclorama';o.data.materials.append(floor)
for c in list(o.users_collection):c.objects.unlink(o)
studio.objects.link(o)
scene.render.engine='CYCLES' if False else 'CYCLES' if False else 'BLENDER_EEVEE';scene.eevee.taa_render_samples=64
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=.10
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
rest={b.name:b.matrix_local.copy() for b in rig.data.bones}
def rot(n,axis,d):r=rest[n].to_quaternion();rig.pose.bones[n].rotation_quaternion=r.inverted()@Quaternion(axis,math.radians(d))@r
def reset():
 for p in rig.pose.bones:p.rotation_quaternion=(1,0,0,0);p.location=(0,0,0);p.scale=(1,1,1)
 for k in face.data.shape_keys.key_blocks:k.value=0
def camera(loc,target,scale,size):
 c=bpy.data.objects['QA Camera'];scene.camera=c;c.data.type='ORTHO';c.location=loc;c.rotation_euler=(Vector(target)-c.location).to_track_quat('-Z','Y').to_euler();c.data.ortho_scale=scale;scene.render.resolution_x,scene.render.resolution_y=size;scene.render.resolution_percentage=100
def render(name,loc,target,scale,size):
 camera(loc,target,scale,size);scene.render.filepath=str(ROOT/'renders'/name);bpy.ops.render.render(write_still=True)
reset();rot('J_Bip_L_UpperArm',(0,1,0),70);rot('J_Bip_R_UpperArm',(0,1,0),-70)
face.data.shape_keys.key_blocks['Fcl_MTH_Fun'].value=.17;face.data.shape_keys.key_blocks['Fcl_BRW_Fun'].value=.08
bpy.context.view_layer.update();bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'NekoAFK-model-v001.blend'))
if '--feet-only' not in sys.argv:
 render('model-fullbody.png',(-2.4,-4.7,2.0),(0,0,.83),1.88,(1000,1300))
 render('face-closeup.png',(-.20,-1.6,1.54),(0,-.025,1.475),.355,(1200,1200))
 reset();render('hand-nails-closeup.png',(.62,-.52,2.48),(.602,.016,1.311),.175,(1200,1200))
reset()
render('feet-model-closeup.png',(-.40,-.90,.50),(0,-.015,.08),.33,(1200,1200))
print('QUALITY_MODEL_BUILT',flush=True)
