import bpy,sys,math,json
import numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
R=Path(__file__).resolve().parents[1]
T=Path('C:/Users/rupjy/.codex/visualizations/2026/10/07/01a11802-03a6-7f71-9210-318d920a3def/NekoAFK-Blender-tools')
sys.path.insert(0,str(T));bpy.ops.preferences.addon_enable(module='io_scene_vrm')
bpy.ops.wm.open_mainfile(filepath=str(R/'NekoAFK-fashion-v003.blend'))
scene=bpy.context.scene;rig=bpy.data.objects['Armature'];face=bpy.data.objects['Face'];keys=face.data.shape_keys.key_blocks
props=bpy.data.collections.new('04 • Mechanical gaming chair and phone');scene.collection.children.link(props)
with bpy.data.libraries.load(str(R.parents[1]/'animations/NekoAFK-animation-library.blend'),link=False) as (src,dst):
 dst.objects=[n for n in src.objects if n.startswith('NekoChair.') and not any(s in n for s in ['Dock','Brace','Lip','Mount'])]
for o in dst.objects:
 if o:props.objects.link(o)
hinge=bpy.data.objects.new('Chair • constrained backrest hinge',None);props.objects.link(hinge);hinge.location=(0,.15,.47);hinge.empty_display_type='ARROWS';hinge.empty_display_size=.08
bpy.context.view_layer.update()
lim=hinge.constraints.new('LIMIT_ROTATION');lim.owner_space='LOCAL';lim.use_limit_x=True;lim.min_x=math.radians(-12);lim.max_x=math.radians(2);lim.use_limit_y=True;lim.use_limit_z=True
lock=hinge.constraints.new('LIMIT_LOCATION');lock.owner_space='WORLD'
for a,v in zip('xyz',hinge.location):setattr(lock,'use_min_'+a,True);setattr(lock,'use_max_'+a,True);setattr(lock,'min_'+a,v);setattr(lock,'max_'+a,v)
for o in props.objects:
 if any(x in o.name for x in ['Back','Headrest','Wing','Piping']):
  m=o.matrix_world.copy();o.parent=hinge;o.matrix_world=m
 if 'Armrest' in o.name:o.location.x*=.86;o.dimensions.y=.21
 if 'ArmSupport' in o.name:o.location.x*=.86
hinge['mechanism']='One rotational DOF about actual lower back hinge; base/seat/casters remain fixed.'
def material(name,c,rough=.45,metal=0):
 m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal;return m
def cube(name,loc,size,mat,bev=.004,parent=None):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 for c in list(o.users_collection):c.objects.unlink(o)
 props.objects.link(o);o.data.materials.append(mat);m=o.modifiers.new('Rounded engineered edge','BEVEL');m.width=bev;m.segments=5
 m=o.modifiers.new('Weighted surface normals','WEIGHTED_NORMAL')
 if parent:o.parent=parent
 return o
case=material('Phone • anodized graphite',(.019,.022,.03),.25,.7);glass=material('Phone • dark sapphire glass',(.009,.023,.041),.14,.1);amber=material('Phone • amber interface',(.65,.30,.04),.32,.35);red=material('Phone • failure coral',(.70,.032,.018),.32)
screenp=glass.node_tree.nodes.get('Principled BSDF');screenp.inputs['Emission Color'].default_value=(.015,.052,.08,1);screenp.inputs['Emission Strength'].default_value=.65
phone=bpy.data.objects.new('Phone • rigid contact master',None);props.objects.link(phone);phone.rotation_mode='QUATERNION';phone.empty_display_size=.045
cube('Phone • case', (0,0,0),(.067,.009,.138),case,.007,phone)
cube('Phone • illuminated screen',(0,.005,0),(.060,.001,.125),glass,.005,phone)
cube('Phone • camera island',(-.018,-.005,.047),(.022,.003,.027),case,.005,phone)
for i in range(2):cube('Phone • lens.'+str(i),(-.018,-.007,.041+i*.012),(.009,.002,.009),glass,.004,phone)
for i in range(5):cube('Phone • activity line.'+str(i),(-.005,.0058,.034-i*.015),(.041 if i%2 else .033,.0004,.0013),amber,.0006,phone)
error=cube('Phone • failure banner',(0,.0063,.041),(.052,.0005,.014),red,.002,phone)
error.scale=(.001,.001,.001)
rest={b.name:b.matrix_local.copy() for b in rig.data.bones};cache={}
helpers=(R.parents[1]/'quality-reset/v002/build_editing.py').read_text(encoding='utf-8')
exec(helpers[helpers.index('def clamp'):helpers.index('def apply')])
# The original helper's pulse/curve endpoint is replaced for this 14-second story.
def smooth(t,pts):
 for (a,x),(b,y) in zip(pts,pts[1:]):
  if a<=t<=b:
   u=(t-a)/(b-a);u=u*u*u*(u*(6*u-15)+10);return x+(y-x)*u
 return pts[0][1] if t<pts[0][0] else pts[-1][1]
def bump(t,c,w):return math.exp(-((t-c)/w)**2)
def blink(t,c):return smooth(t,[(c-.10,0),(c-.018,1),(c+.026,1),(c+.16,0)])
def aim_digit(n,a,b):
 current=matrix(n).copy();q=current.to_3x3().col[1].normalized().rotation_difference((Vector(b)-Vector(a)).normalized());m=q.to_matrix().to_4x4()@current;m.translation=a;setworld(n,m)
def thumb(side,pm,scroll):
 n1=f'J_Bip_{side}_Thumb1';n2=f'J_Bip_{side}_Thumb2';n3=f'J_Bip_{side}_Thumb3';sg=1 if side=='L' else -1
 root=matrix(n1).translation.copy();goal=pm@Vector((sg*.030,.020,-.014));aim_digit(n1,root,goal)
 origin=matrix(n2).translation.copy();target=pm@Vector((sg*.014,.013,-.015+scroll));delta=target-origin;d=delta.length;l1=rig.data.bones[n2].length;l2=rig.data.bones[n3].length;d=clamp(d,abs(l1-l2)+.0005,l1+l2-.0005);axis=delta.normalized();target=origin+axis*d
 aa=(l1*l1-l2*l2+d*d)/(2*d);hh=math.sqrt(max(0,l1*l1-aa*aa));pole=pm@Vector((sg*.042,.047,-.035))-origin;perp=(pole-axis*pole.dot(axis)).normalized();mid=origin+axis*aa+perp*hh
 aim_digit(n2,origin,mid);aim_digit(n3,mid,target)
def apply(t):
 for p in rig.pose.bones:p.rotation_mode='QUATERNION';p.rotation_quaternion=(1,0,0,0);p.location=(0,0,0);p.scale=(1,1,1)
 for k in keys:k.value=0
 cache.clear();hips=rig.pose.bones['J_Bip_C_Hips'];hips.location=rest[hips.name].to_3x3().inverted()@Vector((0,0,-.38))
 surprise=smooth(t,[(0,0),(5.15,0),(5.38,1),(5.75,.72),(6.32,0),(14,0)])
 angry=smooth(t,[(0,0),(5.80,0),(6.6,.75),(8.3,1),(11.9,.73),(14,.64)])
 lower=smooth(t,[(0,0),(5.95,0),(7.2,1),(14,1)])
 lean=smooth(t,[(0,4.5),(5.15,4.5),(5.44,0),(5.88,1.5),(7.55,3),(8.15,-13),(8.48,-9.6),(8.95,-10.7),(9.55,-10),(11.5,-8),(14,-5.5)])
 breath=.23*math.sin(math.tau*t/3.8)*(1-.7*surprise)
 rot('J_Bip_C_Spine',(1,0,0),lean*.65+breath);rot('J_Bip_C_Chest',(1,0,0),lean*.35);rot('J_Bip_C_UpperChest',(0,0,1),-1.5*angry)
 pitch=smooth(t,[(0,17),(2.6,18.5),(4.6,17),(5.43,2),(5.82,4),(6.8,13),(8.2,3),(9.3,9),(11.2,7),(14,12)])
 yaw=smooth(t,[(0,-1.5),(5.1,-1.5),(5.47,-8),(6.6,-5),(8.15,-11),(9.4,-17),(11.3,-10),(14,-6)])
 compound('J_Bip_C_Head',[((0,0,1),yaw),((1,0,0),pitch),((0,1,0),-1.7+2.7*angry)])
 # Seated pelvis contact is fixed. Small leg arcs decelerate before the reaction.
 leglife=1-smooth(t,[(0,0),(5.1,0),(5.5,1),(14,1)])
 compound('J_Bip_L_UpperLeg',[((0,0,1),-2.5),((1,0,0),-88)])
 compound('J_Bip_R_UpperLeg',[((0,0,1),3),((1,0,0),-90)])
 rot('J_Bip_L_LowerLeg',(1,0,0),91+1.7*math.sin(t*2.0)*leglife+2*bump(t,8.25,.22))
 rot('J_Bip_R_LowerLeg',(1,0,0),94+1.2*bump(t,8.35,.28))
 rot('J_Bip_L_Foot',(1,0,0),-3+1.4*math.sin(t*2.0-.4)*leglife-2.4*bump(t,8.35,.3))
 rot('J_Bip_R_Foot',(1,0,0),-4+2*bump(t,9.0,.38))
 for side,sg in [('L',1),('R',-1)]:
  ear=3*bump(t,2.8+(0 if side=='L' else .14),.09)
  compound(f'J_Opt_{side}_CatEar2_01',[((0,1,0),sg*(ear+28*angry-5*surprise)),((1,0,0),-12*angry)])
  for i in range(1,6):
   rot(f'Neko_{side}_Toe{i:02d}_Prox',(1,0,0),(2.7*bump(t,8.4,.25)+1.4*bump(t,10.2,.32))*(1-i*.07))
 for i in range(1,9):
  wave=(2.3+5*angry)*math.sin(t*(1.15+angry*.55)-i*.4)
  compound(f'Neko_Tail_{i:02d}',[((0,1,0),-29 if i==1 else wave*i/8),((0,0,1),0 if i==1 else (1.5+4*angry)*math.sin(t*1.8-i*.38)*i/8)])
 for n in rest:
  if n.startswith('J_Sec_Hair') and not n.endswith('_end'):
   rot(n,(1,0,0),1.7*bump(t,5.55,.18)-2.4*bump(t,8.33,.22)+.6*bump(t,8.7,.2))
 # Phone and two contact poses use one rigid transform, avoiding drift between palms.
 phone.location=(0,-.273+.025*lower,.889-.172*lower+.003*math.sin(t*1.7)*(1-lower))
 phone.rotation_quaternion=Quaternion((1,0,0),math.radians(-12+12*lower))@Quaternion((0,0,1),math.radians(-5*angry))
 pm=phone.matrix_basis.copy();pm.translation=phone.location
 release=smooth(t,[(0,0),(8.6,0),(9.12,1),(10.10,1),(11.25,0),(14,0)])
 for side,sg in [('L',1),('R',-1)]:
  wp=Vector((sg*.069,-.021,-.075+(0 if side=='L' else -.009)));dd=Vector((-sg*.36,-.06,.93));nn=Vector((sg*.05,-.98,-.18))
  if side=='L':
   wp+=Vector((.09*release,-.015*release,.125*release));dd=dd.lerp(Vector((.38,.05,.93)),release);nn=nn.lerp(Vector((-.40,-.75,.40)),release)
  wrist=pm@wp;direction=pm.to_3x3()@dd;normal=pm.to_3x3()@nn
  arm(side,wrist,(sg*.23,.005,.71),direction,normal)
  for j,finger in enumerate(['Index','Middle','Ring','Little']):
   for k,ang in [(1,6+j*2),(2,22+j*2),(3,15+j)]:
    rot(f'J_Bip_{side}_{finger}{k}',(0,1,0),sg*ang*(1-(.72*release if side=='L' else 0)))
  if side=='L' and release>.01:
   compound('J_Bip_L_Thumb1',[((0,0,1),-15),((0,1,0),-10)])
  else:
   scroll=(.006*bump(t,1.18,.22)+.006*bump(t,2.55,.22)+.005*bump(t,4.06,.23)) if side=='R' else 0
   thumb(side,pm,scroll)
 keys['Fcl_MTH_Fun'].value=.16*(1-angry)*(1-surprise)
 keys['Fcl_BRW_Fun'].value=.09*(1-angry)*(1-surprise)
 keys['Fcl_BRW_Surprised'].value=.8*surprise;keys['Fcl_EYE_Surprised'].value=.72*surprise;keys['Fcl_MTH_Surprised'].value=.38*surprise
 keys['Fcl_BRW_Angry'].value=.92*angry;keys['Fcl_EYE_Angry'].value=.42*angry;keys['Fcl_MTH_Angry'].value=.58*angry;keys['Fcl_MTH_Down'].value=.17*angry
 keys['Fcl_EYE_Close'].value=max(blink(t,c) for c in [1.75,3.68,6.14,9.98,12.55])
 keys['Fcl_EYE_Natural'].value=.03*(1-surprise)
 hinge.rotation_euler.x=math.radians(smooth(t,[(0,0),(7.7,0),(8.24,-7.6),(8.53,-4.7),(8.92,-5.8),(9.6,-5.4),(11.6,-4.4),(14,-3)]))
 error.scale=(1,1,1) if t>=5.2 else (.001,.001,.001)
 return {'surprise':surprise,'angry':angry,'release':release}
def cam(loc,target,scale,size):
 c=bpy.data.objects['QA Camera'];scene.camera=c;c.data.type='ORTHO';c.location=loc;c.rotation_euler=(Vector(target)-c.location).to_track_quat('-Z','Y').to_euler();c.data.ortho_scale=scale;scene.render.resolution_x,scene.render.resolution_y=size;scene.render.resolution_percentage=100
def render(name,loc,target,scale,size=(1000,1000)):
 cam(loc,target,scale,size);bpy.context.view_layer.update();scene.render.filepath=str(R/'renders'/name);bpy.ops.render.render(write_still=True)
scene.render.fps=24;scene.frame_start=1;scene.frame_end=336;scene.eevee.taa_render_samples=32;scene.render.image_settings.file_format='PNG'
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.05,.045,.07,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.4
cam((-2.15,-4.8,1.72),(0,-.07,.66),1.62,(1100,1200))
if '--pose-only' in sys.argv:
 apply(1);bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(R/'NekoAFK-performance-work-v003.blend'))
 render('pose-check.png',(-2.15,-4.8,1.72),(0,-.07,.66),1.62,(850,1000))
 render('grip-check.png',(-.5,-1.4,1.21),(0,-.29,.87),.32,(1100,1100))
 render('outfit-check.png',(-.7,-1.5,.95),(0,-.17,.52),.78,(950,950))
 apply(8.3);render('angry-check.png',(-2.15,-4.8,1.72),(0,-.07,.66),1.62,(850,1000))
else:
 moving=[p for p in rig.pose.bones if not p.name.endswith('_end')]
 for f in range(1,337,2):
  scene.frame_set(f);apply((f-1)/24)
  for p in moving:
   p.keyframe_insert('rotation_quaternion',frame=f,group=p.name)
   if p.name=='J_Bip_C_Hips':p.keyframe_insert('location',frame=f,group='Seated contact')
  for k in keys:
   if k.name!='Basis':k.keyframe_insert('value',frame=f,group='Facial performance')
  phone.keyframe_insert('location',frame=f);phone.keyframe_insert('rotation_quaternion',frame=f);hinge.keyframe_insert('rotation_euler',frame=f);error.keyframe_insert('scale',frame=f)
 for owner,label in [(rig,'NEKO • SCROLL / FAILURE / FRUSTRATION • 14s'),(face.data.shape_keys,'NEKO • facial acting'),(phone,'PHONE • rigid contact'),(hinge,'CHAIR • spring recoil'),(error,'PHONE • agent failure')]:
  if owner.animation_data and owner.animation_data.action:
   a=owner.animation_data.action;a.name=label
   for layer in a.layers:
    for strip in layer.strips:
     for bag in strip.channelbags:
      for fc in bag.fcurves:
       for kp in fc.keyframe_points:kp.interpolation='BEZIER';kp.handle_left_type='AUTO_CLAMPED';kp.handle_right_type='AUTO_CLAMPED'
 for name,t in [('Scroll',0),('Agent failure',5.2),('Surprise',5.45),('Phone lowers',6.5),('Anger',7.2),('Chair recoil',8.25),('Frustrated gesture',9.4),('Settling',11.7)]:scene.timeline_markers.new(name,frame=round(t*24)+1)
 scene.frame_set(1);cam((-2.15,-4.8,1.72),(0,-.07,.66),1.62,(1100,1200));bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(R/'NekoAFK-performance-v003.blend'))
 print('PERFORMANCE_SAVED',flush=True)
