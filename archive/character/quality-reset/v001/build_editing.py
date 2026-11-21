import bpy,math,sys,json
import numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
ROOT=Path(__file__).parent;T=Path('C:/Users/rupjy/.codex/visualizations/2026/10/07/01a11802-03a6-7f71-9210-318d920a3def/NekoAFK-Blender-tools')
sys.path.insert(0,str(T));bpy.ops.preferences.addon_enable(module='io_scene_vrm')
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'NekoAFK-model-v001.blend'))
scene=bpy.context.scene;rig=bpy.data.objects['Armature'];face=bpy.data.objects['Face'];keys=face.data.shape_keys.key_blocks
props=bpy.data.collections.new('QR01 • chair and phone');scene.collection.children.link(props)
with bpy.data.libraries.load('D:/Projects/NekoAFK/assets/character/animations/NekoAFK-animation-library.blend',link=False) as (src,dst):
 dst.objects=[n for n in src.objects if n.startswith('NekoChair.') and not any(s in n for s in ['Dock','Brace','Lip','Mount'])]
for ob in dst.objects:
 if ob:props.objects.link(ob)
for ob in list(props.objects):
 if 'Phone' in ob.name:bpy.data.objects.remove(ob,do_unlink=True)
# Recess the back cushion and remove the old protruding phone shelves entirely.
for ob in props.objects:
 if 'BackInset' in ob.name:ob.location.y=.177
 if 'Armrest.-1' in ob.name:ob.location=(-.19,.005,.722);ob.scale.y=.64
 if 'Armrest.1' in ob.name:ob.location=(.19,.005,.706);ob.scale.y=.64

def material(name,col,rough=.45,metal=0):
 m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*col,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal;return m
def cube(name,loc,scale,mat,bevel):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 for c in list(o.users_collection):c.objects.unlink(o)
 props.objects.link(o);o.data.materials.append(mat);m=o.modifiers.new('Machined soft edges','BEVEL');m.width=bevel;m.segments=5;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=m.name)
 for p in o.data.polygons:p.use_smooth=True
 m=o.modifiers.new('Surface normals','WEIGHTED_NORMAL');bpy.ops.object.modifier_apply(modifier=m.name);return o
case=material('QR01 Phone • satin obsidian',(.012,.014,.025),.28,.5);glass=material('QR01 Phone • screen glass',(.035,.045,.062),.18,.15);gold=material('QR01 Phone • amber trim',(.4,.18,.025),.27,.75)
parts=[cube('QR01 Phone case',(0,0,0),(.058,.009,.129),case,.006),cube('QR01 Phone screen',(0,.005,0),(.052,.001,.118),glass,.005)]
for i in range(4):parts.append(cube('QR01 Phone activity',(-.004,.0057,.033-i*.017),(.036,.0004,.0012),gold,.0005))
for x in [-.018,-.008]:parts.append(cube('QR01 Phone lens',(x,-.005,.047),(.007,.001,.008),glass,.003))
bpy.ops.object.select_all(action='DESELECT')
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();phone=bpy.context.object;phone.name='QR01 Phone';bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT');b=rig.data.edit_bones.new('QR01_Phone');b.head=(0,0,0);b.tail=(0,0,.1);b.parent=rig.data.edit_bones['J_Bip_R_Hand'];bpy.ops.object.mode_set(mode='OBJECT')
g=phone.vertex_groups.new(name='QR01_Phone');g.add(list(range(len(phone.data.vertices))),1,'REPLACE');m=phone.modifiers.new('Rigid grip attachment','ARMATURE');m.object=rig;phone.parent=rig
rest={b.name:b.matrix_local.copy() for b in rig.data.bones};cache={}
def clamp(v,a=0,b=1):return max(a,min(b,v))
def rot(n,axis,deg):
 q=rest[n].to_quaternion();rig.pose.bones[n].rotation_quaternion=q.inverted()@Quaternion(axis,math.radians(deg))@q
def compound(n,angles):
 q=Quaternion();r=rest[n].to_quaternion()
 for axis,angle in angles:q=q@Quaternion(axis,math.radians(angle))
 rig.pose.bones[n].rotation_quaternion=r.inverted()@q@r
def matrix(n):
 if n in cache:return cache[n]
 b=rig.data.bones[n];kw={'parent_matrix':matrix(b.parent.name),'parent_matrix_local':rest[b.parent.name]} if b.parent else {}
 m=b.convert_local_to_pose(rig.pose.bones[n].matrix_basis,rest[n],**kw);cache[n]=m;return m
def setworld(n,m):
 b=rig.data.bones[n];kw={'parent_matrix':matrix(b.parent.name),'parent_matrix_local':rest[b.parent.name]} if b.parent else {}
 rig.pose.bones[n].matrix_basis=b.convert_local_to_pose(m,rest[n],invert=True,**kw);cache[n]=m
def frame(direction,normal):
 y=Vector(direction).normalized();z=Vector(normal);z=(z-y*z.dot(y)).normalized();return Matrix((y.cross(z).normalized(),y,z)).transposed()
def arm(side,wrist,hint,direction,normal):
 up=rig.pose.bones[f'J_Bip_{side}_UpperArm'];lo=rig.pose.bones[f'J_Bip_{side}_LowerArm'];hand=rig.pose.bones[f'J_Bip_{side}_Hand']
 shoulder=matrix(up.name).translation;target=Vector(wrist);delta=target-shoulder;d=clamp(delta.length,abs(up.bone.length-lo.bone.length)+.002,up.bone.length+lo.bone.length-.002);axis=delta.normalized();target=shoulder+axis*d
 x=(up.bone.length**2-lo.bone.length**2+d*d)/(2*d);h=math.sqrt(max(0,up.bone.length**2-x*x));pole=Vector(hint)-shoulder;perp=(pole-axis*pole.dot(axis)).normalized();elbow=shoulder+axis*x+perp*h
 plane=axis.cross(perp).normalized()*(1 if side=='L' else -1)
 for p,a,b in [(up,shoulder,elbow),(lo,elbow,target)]:
  yy=(b-a).normalized();src=frame(p.bone.tail_local-p.bone.head_local,(0,0,1));dst=frame(yy,normal)
  if p==up:m=(p.bone.tail_local-p.bone.head_local).normalized().rotation_difference(yy).to_matrix().to_4x4()@rest[p.name]
  else:m=(dst@src.transposed()).to_4x4()@rest[p.name]
  m.translation=a;setworld(p.name,m)
 basis=frame(direction,normal);src=frame(hand.bone.tail_local-hand.bone.head_local,(0,0,1));m=(basis@src.transposed()).to_4x4()@rest[hand.name];m.translation=target;setworld(hand.name,m)
 return target,basis,elbow
def curve(t,pts):
 # Authored holds and eased beats. Each segment arrives with zero velocity.
 for (a,x),(b,y) in zip(pts,pts[1:]):
  if a<=t<=b:
   u=(t-a)/(b-a);u=u*u*u*(u*(6*u-15)+10);return x+(y-x)*u
 return pts[0][1] if t<pts[0][0] else pts[-1][1]
def pulse(t,a,b,c):return curve(t,[(0,0),(a,0),(b,1),(c,0),(8,0)])
def blink(t,a):return curve(t,[(0,0),(a,0),(a+.075,1),(a+.115,.95),(a+.255,0),(8,0)])
def apply(t):
 for p in rig.pose.bones:p.rotation_mode='QUATERNION';p.rotation_quaternion=(1,0,0,0);p.location=(0,0,0);p.scale=(1,1,1)
 for k in keys:k.value=0
 cache.clear();h=rig.pose.bones['J_Bip_C_Hips'];h.location=rest[h.name].to_3x3().inverted()@Vector((0,0,-.353))
 breath=.17*math.sin(math.tau*t/4)
 rot('J_Bip_C_Spine',(1,0,0),3.8+breath);rot('J_Bip_C_Chest',(0,0,1),-2);rot('J_Bip_C_UpperChest',(1,0,0),-.7+breath*.35)
 glance=curve(t,[(0,0),(4.3,0),(4.9,1),(5.45,1),(6.2,0),(8,0)])
 smile=pulse(t,2.9,3.7,4.5)
 pitch=curve(t,[(0,15),(1.2,16.2),(2.5,15),(3.6,13.8),(4.2,14.5),(4.9,10.5),(5.5,11),(6.2,15),(8,15)])
 compound('J_Bip_C_Head',[((0,0,1),-28+23*glance),((1,0,0),pitch+6),((0,1,0),-2.5-2*smile)])
 compound('J_Bip_L_UpperLeg',[((0,0,1),-3),((1,0,0),-87)])
 compound('J_Bip_R_UpperLeg',[((0,0,1),4),((1,0,0),-90)])
 knee=curve(t,[(0,96),(1.15,89),(2.15,101),(3.35,91),(4.6,98),(5.7,96),(6.5,96),(7.3,93),(8,96)])
 rot('J_Bip_L_LowerLeg',(1,0,0),knee);rot('J_Bip_R_LowerLeg',(1,0,0),100)
 ankle=curve(t,[(0,-8),(1.4,-5),(2.4,-11),(3.6,-6),(4.8,-9),(6.3,-8),(8,-8)])
 rot('J_Bip_L_Foot',(1,0,0),ankle);rot('J_Bip_R_Foot',(1,0,0),-5+3*pulse(t,5.7,6.5,7.3))
 for s in ['L','R']:
  toe=2.4*pulse(t,1.6,2.35,3.05) if s=='L' else 1.6*pulse(t,6.0,6.55,7.15)
  for i in range(1,6):rot(f'Neko_{s}_Toe{i:02d}_Prox',(1,0,0),toe*(1-i*.065));rot(f'Neko_{s}_Toe{i:02d}_Dist',(1,0,0),toe*.4)
  ear=curve(t,[(0,0),(3.05,0),(3.15,3.5 if s=='L' else 1),(3.28,-.8),(3.55,0),(8,0)])
  rot(f'J_Opt_{s}_CatEar2_01',(0,1,0),(1 if s=='L' else -1)*(2+ear+2*glance))
 for i in range(1,9):
  phase=math.tau*t/8-(i-1)*.33
  compound(f'Neko_Tail_{i:02d}',[((0,1,0),-30 if i==1 else 1.8*math.sin(phase)*i/8),((0,0,1),0 if i==1 else 2.2*math.sin(phase+.8)*i/8)])
 # Hair response follows the head's changes; no continuously wobbling hair cards.
 lag=(curve(max(0,t-.12),[(0,15),(1.2,16.2),(2.5,15),(3.6,13.8),(4.2,14.5),(4.9,10.5),(5.5,11),(6.2,15),(8,15)])-pitch)*.22
 for n in rest:
  if n.startswith('J_Sec_Hair') and not n.endswith('_end'):
   depth=int(n.split('Hair')[1].split('_')[0]);rot(n,(1,0,0),lag*min(depth,3)/3)
 shift=.004*pulse(t,.45,.78,1.25)+.003*pulse(t,2.10,2.48,2.85)
 left,lb,le=arm('L',(.105,-.185,.638),(.20,-.005,.69),(0,-.995,-.10),(0,-.10,.995))
 right,rb,re=arm('R',(-.190,-.220,.830+shift),(-.16,.030,.700),(-.38,-.45,.81),(0,-.874,-.486))
 for s in ['L','R']:
  for j,finger in enumerate(['Index','Middle','Ring','Little']):
   angles=[(1,8+2*j),(2,16+2*j),(3,9+j)] if s=='L' else [(1,3+j*.65),(2,8+j*1.2),(3,3+j*.65)]
   for i,angle in angles:rot(f'J_Bip_{s}_{finger}{i}',(0,1,0),(1 if s=='L' else -1)*angle)
  compound(f'J_Bip_{s}_Thumb1',[((0,0,1),-8 if s=='L' else 22),((1,0,0),0 if s=='L' else 35)])
 scroll=curve(t,[(0,0),(.5,0),(.75,4.5),(.98,-1),(1.28,0),(2.15,0),(2.38,4),(2.65,-.8),(2.95,0),(8,0)])
 compound('J_Bip_R_Thumb2',[((0,0,1),-15),((0,1,0),-18)]);rot('J_Bip_R_Thumb3',(0,1,0),-8)
 rot('J_Bip_L_Thumb2',(0,1,0),5)
 # Phone derives from the actual hand frame; grip is invariant over the clip.
 xx=rb.col[0];long=rb.col[1];back=rb.col[2];pos=right+long*.075-back*.026+xx*.005
 m=Matrix((xx,-back,long)).transposed().to_4x4()@Quaternion((0,1,0),math.radians(15)).to_matrix().to_4x4()@Quaternion((1,0,0),math.radians(12)).to_matrix().to_4x4();m.translation=pos;setworld('QR01_Phone',m@rest['QR01_Phone'])
 # Thumb wraps around the lower case edge; its pad follows a short screen stroke.
 normal=m.to_3x3()@Vector((0,1,0));root=matrix('J_Bip_R_Thumb1').translation.copy();elbow_goal=m@Vector((-.043,-.010,-.064))
 def digit_segment(name,a,b):
  current=matrix(name).copy();q=current.to_3x3().col[1].normalized().rotation_difference((Vector(b)-Vector(a)).normalized());mm=q.to_matrix().to_4x4()@current;mm.translation=a;setworld(name,mm)
 origin=matrix('J_Bip_R_Thumb2').translation.copy();target=m@Vector((-.028,.018,-.037+.0012*scroll/4.5));delta=target-origin;d=delta.length;l1=rig.data.bones['J_Bip_R_Thumb2'].length;l2=rig.data.bones['J_Bip_R_Thumb3'].length;d=clamp(d,abs(l1-l2)+.001,l1+l2-.001);axis=delta.normalized();target=origin+axis*d
 aa=(l1*l1-l2*l2+d*d)/(2*d);hh=math.sqrt(max(0,l1*l1-aa*aa));pole=m@Vector((-.054,.040,-.037))-origin;perp=(pole-axis*pole.dot(axis)).normalized();middle=origin+axis*aa+perp*hh
 digit_segment('J_Bip_R_Thumb2',origin,middle);digit_segment('J_Bip_R_Thumb3',middle,target)
 keys['Fcl_MTH_Fun'].value=.12+.13*smile;keys['Fcl_BRW_Fun'].value=.06+.05*smile;keys['Fcl_EYE_Close'].value=max(blink(t,1.52),blink(t,4.61),blink(t,6.92))
 for s in ['L','R']:
  n=f'J_Adj_{s}_FaceEye'
  if n in rest:compound(n,[((1,0,0),2*(1-glance)),((0,0,1),curve(t,[(0,-.4),(.32,-.4),(.40,.1),(2.1,.1),(2.20,-.6),(4.4,-.6),(4.54,1.3),(5.55,1.3),(5.67,-.4),(8,-.4)]))])
 return {'left_elbow':tuple(le),'right_elbow':tuple(re),'phone':tuple(pos),'left_wrist':tuple(left),'right_wrist':tuple(right)}
def camera(loc,target,scale,size):
 c=bpy.data.objects['QA Camera'];scene.camera=c;c.data.type='ORTHO';c.location=loc;c.rotation_euler=(Vector(target)-c.location).to_track_quat('-Z','Y').to_euler();c.data.ortho_scale=scale;scene.render.resolution_x,scene.render.resolution_y=size;scene.render.resolution_percentage=100
def render(name,loc,target,scale,size):
 bpy.context.view_layer.update();camera(loc,target,scale,size);scene.render.filepath=str(ROOT/'renders'/name);bpy.ops.render.render(write_still=True)
scene.render.fps=24;scene.frame_start=1;scene.frame_end=192
info=apply(0);print('POSE_CONTACTS',info,flush=True)
camera((-2.5,-4.6,1.35),(0,-.065,.66),1.57,(1000,1200));bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'NekoAFK-editing-work-v001.blend'))
if '--pose-only' in sys.argv:
 render('seated-pose-check.png',(-2.5,-4.6,1.35),(0,-.065,.66),1.57,(850,1020))
 render('grip-check.png',(-1,-2,1.7),(-.10,-.27,.81),.42,(1000,1000))
 render('seated-leg-foot.png',(-.9,-2,.63),(0,-.32,.24),.68,(1200,1200))
else:
 moving=[p.name for p in rig.pose.bones if not p.name.endswith('_end')];data={n:[] for n in moving};locs={n:[] for n in moving};morph={k.name:[] for k in keys if k.name!='Basis'}
 for f in range(193):
  apply(f/24)
  for n in moving:
   pb=rig.pose.bones[n];q=pb.rotation_quaternion.copy()
   if data[n] and q.dot(Quaternion(data[n][-1]))<0:q.negate()
   data[n].append(tuple(q));locs[n].append(tuple(pb.location))
  for n in morph:morph[n].append(keys[n].value)
 act=bpy.data.actions.new('Neko_QR01_EDITING_PHONE_08s');act.use_fake_user=True;slot=act.slots.new('OBJECT',rig.name);fslot=act.slots.new('KEY',face.data.shape_keys.name);layer=act.layers.new('Authored editing proof');strip=layer.strips.new(type='KEYFRAME');bag=strip.channelbag(slot,ensure=True);fb=strip.channelbag(fslot,ensure=True)
 def channel(b,path,index,vals):
  fc=b.fcurves.new(data_path=path,index=index);fc.keyframe_points.add(len(vals));co=np.empty(len(vals)*2);co[0::2]=np.arange(1,len(vals)+1);co[1::2]=vals;fc.keyframe_points.foreach_set('co',co)
  for k in fc.keyframe_points:k.interpolation='LINEAR'
  fc.update()
 for n in moving:
  q=np.array(data[n]);pos=np.array(locs[n])
  if np.max(np.abs(q-np.array([1,0,0,0])))>.000001:
   for i in range(4):channel(bag,f'pose.bones["{n}"].rotation_quaternion',i,q[:,i])
  if np.max(np.abs(pos))>.000001:
   for i in range(3):channel(bag,f'pose.bones["{n}"].location',i,pos[:,i])
 for n,vals in morph.items():
  if max(vals)>.000001:channel(fb,f'key_blocks["{n}"].value',0,vals)
 for ob,sl in [(rig,slot),(face.data.shape_keys,fslot)]:
  ad=ob.animation_data_create();tr=ad.nla_tracks.new();tr.name='QR01 • single approved-quality candidate';st=tr.strips.new(act.name,1,act);st.action_slot=sl;st.extrapolation='NOTHING'
 scene.frame_set(1);bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'NekoAFK-editing-v001.blend'))
 if '--no-stills' not in sys.argv:
  render('fullbody-three-quarter.png',(-2.5,-4.6,1.35),(0,-.065,.66),1.57,(1200,1440))
  render('seated-leg-foot.png',(-.9,-2,.63),(0,-.32,.24),.68,(1200,1200))
 print('EDITING_BUILT',len(bag.fcurves),len(fb.fcurves),flush=True)
