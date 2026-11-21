"""Canonical Neko, reversible fashion/anatomy study. Run in Blender 5.2."""
from pathlib import Path
R=Path(__file__).resolve().parents[1]
legacy=R.parents[1]/'quality-reset/v001/build_model.py'
code=legacy.read_text(encoding='utf-8').split("reset();rot('J_Bip_L_UpperArm'")[0]
code=code.replace("ROOT=Path(__file__).parent;",f"ROOT=Path({str(R)!r});")
exec(compile(code,str(legacy),'exec'))
reset()
fashion=bpy.data.collections.new('03 • Hoodie dress and inner shorts');scene.collection.children.link(fashion)
optional=bpy.data.collections.new('OPTIONAL • Original hoodie and trousers');scene.collection.children.link(optional)
original=body.copy();original.data=body.data.copy();original.name='Original outfit • full body';optional.objects.link(original)
for name in ['NekoJoggerCuff.L','NekoJoggerCuff.R']:
 o=bpy.data.objects[name]
 for c in list(o.users_collection):c.objects.unlink(o)
 optional.objects.link(o)
optional.hide_render=True;optional.hide_viewport=True
original['variant_instructions']='Enable Original collection; hide Body, new bare legs and fashion collection. Original outfit geometry is preserved.'
# Preserve original hands, ears, neck and the upper hoodie. Remove trousers and
# covered skin below the new waist to avoid coincident surfaces.
bm=bmesh.new();bm.from_mesh(body.data)
kill=[f for f in bm.faces if f.material_index==1 or (f.material_index==2 and max(v.co.z for v in f.verts)<1.00) or (f.material_index==0 and max(v.co.z for v in f.verts)<1.035 and max(abs(v.co.x) for v in f.verts)<.20)]
bmesh.ops.delete(bm,geom=kill,context='FACES')
for v in bm.verts:
 if abs(v.co.x)<.19 and .97<v.co.z<1.18:
  v.co.x*=1-.09*math.exp(-((v.co.z-1.045)/.09)**2)
bm.to_mesh(body.data);bm.free()
cloth=material('Neko Atelier • charcoal technical fleece',(.011,.010,.014),.86)
p=cloth.node_tree.nodes.get('Principled BSDF');p.inputs['Sheen Weight'].default_value=.015;p.inputs['Sheen Roughness'].default_value=.7;p.inputs['Specular IOR Level'].default_value=.12
noise=cloth.node_tree.nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=310;noise.inputs['Detail'].default_value=2
bump=cloth.node_tree.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.10;bump.inputs['Distance'].default_value=.0003
cloth.node_tree.links.new(noise.outputs['Fac'],bump.inputs['Height']);cloth.node_tree.links.new(bump.outputs[0],p.inputs['Normal'])
trim=material('Neko Atelier • muted amber piping',(.42,.19,.039),.38,.35)
shortmat=material('Neko Atelier • inner shorts stretch knit',(.015,.014,.022),.86)
skin=feet.data.materials[0]
# Seamless ring topology follows the existing upper/lower leg and ankle bones.
profile=[(.13,.026,.029,.034),(.18,.028,.033,.027),(.26,.037,.043,.023),(.34,.046,.047,.021),(.41,.043,.044,.015),(.48,.037,.038,.004),(.525,.039,.040,.005),(.58,.047,.050,.000),(.68,.058,.062,-.004),(.79,.068,.072,-.002),(.89,.073,.079,.003),(.97,.078,.084,.006)]
def interp(z,col):return float(np.interp(z,[p[0] for p in profile],[p[col] for p in profile]))
def legweights(z,side):
 knee=max(0,min(1,(z-.48)/.10));knee=knee*knee*(3-2*knee)
 ankle=max(0,min(1,(.18-z)/.08));ankle=ankle*ankle*(3-2*ankle)
 return {f'J_Bip_{side}_UpperLeg':knee,f'J_Bip_{side}_LowerLeg':(1-knee)*(1-ankle),f'J_Bip_{side}_Foot':(1-knee)*ankle}
for side,sg in [('L',1),('R',-1)]:
 vs=[];fs=[];ws=[];N=64;J=92
 for j in range(J+1):
  z=.132+(.965-.132)*j/J;rx=interp(z,1);ry=interp(z,2);cy=interp(z,3)
  for i in range(N):
   a=math.tau*i/N;front=max(0,-math.sin(a));knee=.003*math.exp(-((z-.531)/.033)**2)*front**6
   vs.append((sg*.0731+rx*math.cos(a),cy+ry*math.sin(a)-knee,z));ws.append(legweights(z,side))
   if j:q=j*N+i;r=j*N+(i+1)%N;fs.append((q-N,r-N,r,q))
 fs.append(tuple(reversed(range(N))));fs.append(tuple(J*N+i for i in range(N)))
 o=mesh('Neko • bare leg.'+side,vs,fs,skin,bare,ws)
 m=o.modifiers.new('Silhouette polish','SUBSURF');m.levels=1;m.render_levels=1
 # Fitted safety shorts extend under the dress hem, never a painted texture.
 sv=[];sf=[];sw=[]
 for j in range(22):
  z=.775+.198*j/21
  for i in range(N):
   a=math.tau*i/N;sv.append((sg*.0731+(interp(z,1)+.0025)*math.cos(a),interp(z,3)+(interp(z,2)+.0025)*math.sin(a),z));sw.append(legweights(z,side))
   if j:q=j*N+i;r=j*N+(i+1)%N;sf.append((q-N,r-N,r,q))
 o=mesh('Neko • fitted inner shorts.'+side,sv,sf,shortmat,fashion,sw);m=o.modifiers.new('Tailored thickness','SOLIDIFY');m.thickness=.0015
# Genuine skinned skirt, with a sculpted seated corrective fitted to the pose.
vs=[];fs=[];ws=[];uv=[];N=96;J=32
for j in range(J+1):
 t=j/J
 for i in range(N):
  a=math.tau*i/N;fold=.0018*math.sin(12*a+2*t)*t*t
  vs.append(((.145+.025*t+fold)*math.cos(a),.012+(.125+.012*t+fold)*math.sin(a),1.023-.306*t));ws.append({'J_Bip_C_Hips':1});uv.append((i/N,t))
  if j:q=j*N+i;r=j*N+(i+1)%N;fs.append((q-N,r-N,r,q))
skirt=mesh('Neko • hoodie-dress skirt',vs,fs,cloth,fashion,ws,uv)
skirt.shape_key_add(name='Basis');seated=skirt.shape_key_add(name='Seated drape • fitted over thighs')
for j in range(J+1):
 t=j/J
 for i in range(N):
  a=math.tau*i/N;front=max(0,-math.sin(a));back=max(0,math.sin(a));fold=.0022*math.sin(12*a+2.5*t)*math.sin(math.pi*t*.8)**2
  x=(.128+.046*t+fold)*math.cos(a)
  y=.006+(.120+.230*t*front)*math.sin(a)
  z=1.065-.179*t+.104*t*front**2+.004*math.sin(a*8+t*3)*t*front
  seated.data[j*N+i].co=(x,y,z)
seated.value=1
m=skirt.modifiers.new('Cloth surface','SUBSURF');m.levels=2;m.render_levels=2
m=skirt.modifiers.new('Bound hem thickness','SOLIDIFY');m.thickness=.002;m.offset=-.5
# A narrow stitched amber hem is a second real mesh following the same corrective.
for label,t0,t1,mat in [('Amber hem',.952,.965,trim),('Hem binding',.971,1.0,cloth)]:
 ids=[];hv=[];hf=[];hw=[]
 for j,t in enumerate([t0,t1]):
  for i in range(N):
   a=math.tau*i/N;front=max(0,-math.sin(a));fold=.0022*math.sin(12*a+2.5*t)*math.sin(math.pi*t*.8)**2
   hv.append(((.128+.046*t+fold+.0006)*math.cos(a),.006+(.120+.230*t*front+.0006)*math.sin(a),1.065-.179*t+.104*t*front**2+.004*math.sin(a*8+t*3)*t*front));hw.append({'J_Bip_C_Hips':1})
   if j:hf.append((i,(i+1)%N,N+(i+1)%N,N+i))
 o=mesh('Neko • '+label,hv,hf,mat,fashion,hw);m=o.modifiers.new('Soft seam','SUBSURF');m.levels=1;m.render_levels=1
# Improve the canonical hair surfaces without changing identity or hair chains.
hair=bpy.data.objects['Hair'];bm=bmesh.new();bm.from_mesh(hair.data)
for _ in range(4):bmesh.ops.smooth_vert(bm,verts=[v for v in bm.verts if not v.is_boundary],factor=.17,use_axis_x=True,use_axis_y=True,use_axis_z=True)
bm.to_mesh(hair.data);bm.free();m=hair.modifiers.new('Fine lock surfaces','SUBSURF');m.levels=1;m.render_levels=1
for mat in bpy.data.materials:
 if not mat.use_nodes:continue
 if 'HAIR' in mat.name:
  mat.use_backface_culling=True
  for n in mat.node_tree.nodes:
   if n.type=='BSDF_PRINCIPLED':n.inputs['Roughness'].default_value=.5;n.inputs['Specular IOR Level'].default_value=.12
 if 'SKIN' in mat.name or 'warm skin' in mat.name:
  for n in mat.node_tree.nodes:
   if n.type=='BSDF_PRINCIPLED':n.inputs['Roughness'].default_value=.47;n.inputs['Subsurface Weight'].default_value=.035
# Re-fine face planes identically across the original 57 expression deltas.
for v in face.data.vertices:
 p=v.co;front=max(0,min(1,(-p.y-.015)/.04));jaw=math.exp(-((p.z-1.398)/.026)**2)*front
 delta=Vector((p.x*.014*jaw,0,.0012*math.exp(-(p.x/.018)**2-((p.z-1.382)/.017)**2)*front))
 for k in face.data.shape_keys.key_blocks:k.data[v.index].co+=delta
tail=bpy.data.objects['NekoTail • curved fluffy rest']
bm=bmesh.new();bm.from_mesh(tail.data)
for _ in range(3):bmesh.ops.smooth_vert(bm,verts=list(bm.verts),factor=.18,use_axis_x=True,use_axis_y=True,use_axis_z=True)
bm.to_mesh(tail.data);bm.free();m=tail.modifiers.new('Fur silhouette smoothing','SUBSURF');m.levels=1;m.render_levels=1
scene.view_settings.exposure=-.10
scene.eevee.taa_render_samples=48
# Fuse the new legs into the existing feet in rest space and transfer original
# leg/foot/toe weights. This removes the overlapping ankle shells.
parts=[feet,bpy.data.objects['Neko • bare leg.L'],bpy.data.objects['Neko • bare leg.R']]
of=feet.copy();of.data=feet.data.copy();of.name='Original outfit • barefoot feet';optional.objects.link(of)
points=[];weights=[];joined_v=[];joined_f=[]
for ob in parts:
 for md in ob.modifiers:
  if md.type=='ARMATURE':md.show_viewport=False
bpy.context.view_layer.update();dep=bpy.context.evaluated_depsgraph_get()
for ob in parts:
 ev=ob.evaluated_get(dep);me=ev.to_mesh();offset=len(joined_v)
 joined_v.extend(tuple(v.co) for v in me.vertices);joined_f.extend(tuple(offset+i for i in p.vertices) for p in me.polygons)
 for v in me.vertices:
  points.append(v.co.copy());weights.append({ob.vertex_groups[g.group].name:g.weight for g in v.groups})
 ev.to_mesh_clear()
kd=KDTree(len(points))
for i,p in enumerate(points):kd.insert(p,i)
kd.balance()
unified=mesh('Neko • continuous legs ankles and feet',joined_v,joined_f,skin,bare)
bpy.context.view_layer.objects.active=unified;bpy.ops.object.select_all(action='DESELECT');unified.select_set(True)
rm=unified.modifiers.new('Anatomical ankle union','REMESH');rm.mode='VOXEL';rm.voxel_size=.0018;rm.use_smooth_shade=True;bpy.ops.object.modifier_apply(modifier=rm.name)
sm=unified.modifiers.new('Relax ankle transition','SMOOTH');sm.factor=.58;sm.iterations=4;bpy.ops.object.modifier_apply(modifier=sm.name)
dc=unified.modifiers.new('Balanced surface density','DECIMATE');dc.ratio=.38;bpy.ops.object.modifier_apply(modifier=dc.name)
groups={}
for v in unified.data.vertices:
 donors=kd.find_n(v.co,3);sums={};den=0
 for _,idx,dist in donors:
  fac=1/(dist+.0003)**2;den+=fac
  for n,w in weights[idx].items():sums[n]=sums.get(n,0)+w*fac
 ww=sorted(sums.items(),key=lambda p:p[1],reverse=True)[:4];tot=sum(w for n,w in ww)
 for n,w in ww:
  if w<1e-8:continue
  if n not in groups:groups[n]=unified.vertex_groups.new(name=n)
  groups[n].add([v.index],w/tot,'REPLACE')
for p in unified.data.polygons:p.use_smooth=True
md=unified.modifiers.new('Preserved humanoid and toe skinning','ARMATURE');md.object=rig;unified.parent=rig
md=unified.modifiers.new('Final anatomy surface','SUBSURF');md.levels=1;md.render_levels=1
for ob in parts:bpy.data.objects.remove(ob,do_unlink=True)
# Use the same skin response on the wrist bridges, extending them underneath
# both neighboring skin regions to cover the pronounced posed wrist opening.
for side,sg in [('L',1),('R',-1)]:
 ob=bpy.data.objects['QR01.Wrist continuity.'+side];ob.data.materials.clear();ob.data.materials.append(skin)
 for v in ob.data.vertices:
  t=(abs(v.co.x)-.495)/.041;v.co.x=sg*(.487+.068*t)
  w=max(0,min(1,(t-.15)/.6));
  for g in ob.vertex_groups:g.remove([v.index])
  ob.vertex_groups[f'J_Bip_{side}_LowerArm'].add([v.index],1-w,'REPLACE');ob.vertex_groups[f'J_Bip_{side}_Hand'].add([v.index],w,'REPLACE')
 md=ob.modifiers.new('Smooth wrist contour','SUBSURF');md.levels=2;md.render_levels=2
# The canonical skin atlas clips the wrist with an alpha mask. Use a continuous
# opaque skin response on hands/wrists; the actual original hand topology stays.
body.data.materials.append(skin);hand_skin=len(body.data.materials)-1
for poly in body.data.polygons:
 if poly.material_index==0 and all(abs(body.data.vertices[i].co.x)>.475 for i in poly.vertices):poly.material_index=hand_skin
for side in ['L','R']:
 ob=bpy.data.objects.get('QR01.Wrist continuity.'+side)
 if ob:bpy.data.objects.remove(ob,do_unlink=True)
rig['source']='D:/Projects/NekoAFK/assets/character/blender/NekoAFK-canon.blend'
rig['status']='Fashion/performance candidate v003; not final quality sign-off.'
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(R/'NekoAFK-fashion-v003.blend'))
print('FASHION_MODEL_SAVED',flush=True)
