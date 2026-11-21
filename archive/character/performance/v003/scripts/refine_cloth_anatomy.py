import bpy,bmesh,sys,math
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,'C:/Users/rupjy/.codex/visualizations/2026/10/07/01a11802-03a6-7f71-9210-318d920a3def/NekoAFK-Blender-tools');bpy.ops.preferences.addon_enable(module='io_scene_vrm')
bpy.ops.wm.open_mainfile(filepath=str(R/'NekoAFK-fashion-v003.blend'))
rig=bpy.data.objects['Armature'];char=bpy.data.collections['NekoAFK • Character'];legs=bpy.data.objects['Neko • continuous legs ankles and feet'];skin=legs.data.materials[0]
old=bpy.data.objects['Body'];source=bpy.data.objects['Original outfit • full body'];body=source.copy();body.data=source.data.copy();char.objects.link(body);bpy.data.objects.remove(old,do_unlink=True);body.name='Body'
bm=bmesh.new();bm.from_mesh(body.data)
kill=[f for f in bm.faces if f.material_index==1 or (f.material_index==0 and max(v.co.z for v in f.verts)<1.035 and max(abs(v.co.x) for v in f.verts)<.20)]
bmesh.ops.delete(bm,geom=kill,context='FACES');bm.to_mesh(body.data);bm.free()
body.data.materials.append(skin);idx=len(body.data.materials)-1
for p in body.data.polygons:
 if p.material_index==0 and all(abs(body.data.vertices[i].co.x)>.475 for i in p.vertices):p.material_index=idx
cloth_ids={i for p in body.data.polygons if p.material_index==2 for i in p.vertices}
orig={v.index:v.co.copy() for v in body.data.vertices}
# Extend the original hoodie itself, keeping continuous topology and original
# chest emblem. The seated corrective reshapes its lower rings over the thighs.
for i in cloth_ids:
 v=body.data.vertices[i];p=orig[i]
 if p.z<1.065 and abs(p.x)<.22:v.co.z-=.077*max(0,min(1,(1.065-p.z)/.271))
body.shape_key_add(name='Basis');key=body.shape_key_add(name='Seated hoodie-dress • sculpted thigh drape')
hips=body.vertex_groups.get('J_Bip_C_Hips')
for i in cloth_ids:
 p=orig[i]
 if p.z>=1.065 or abs(p.x)>.22:continue
 t=max(0,min(1,(1.065-p.z)/.271));a=math.atan2((p.y-.006)/.12,p.x/.145);front=max(0,-math.sin(a))
 blend=min(1,t/.32);blend=blend*blend*(3-2*blend)
 radial=math.sqrt((p.x/.145)**2+((p.y-.006)/.12)**2)
 detail=(radial-1)*.045*(1-t*.5)
 fold=.0015*math.sin(12*a+2.5*t)*t*t
 q=Vector(((.128+.046*t+fold+detail)*math.cos(a),.006+(.120+.230*t*front+detail)*math.sin(a),1.065-.179*t+.104*t*front**2+.003*math.sin(a*8+t*3)*t*front))
 key.data[i].co=body.data.vertices[i].co.lerp(q,blend)
 if t>.07:
  for vg in body.vertex_groups:vg.remove([i])
  hips.add([i],1,'REPLACE')
key.value=1
o=bpy.data.objects.get('Neko • hoodie-dress skirt')
if o:bpy.data.objects.remove(o,do_unlink=True)
# Smooth the ankle union and remove a weight discontinuity inherited from the
# original foot surface at the old trouser cuff line.
bm=bmesh.new();bm.from_mesh(legs.data)
for _ in range(18):
 bmesh.ops.smooth_vert(bm,verts=[v for v in bm.verts if .105<v.co.z<.225],factor=.35,use_axis_x=True,use_axis_y=True,use_axis_z=False)
bm.to_mesh(legs.data);bm.free()
for v in legs.data.vertices:
 z=v.co.z
 if not .09<z<.27:continue
 side='L' if v.co.x>0 else 'R';t=max(0,min(1,(.22-z)/.13));t=t*t*(3-2*t)
 for g in legs.vertex_groups:g.remove([v.index])
 for n,w in [(f'J_Bip_{side}_Foot',t),(f'J_Bip_{side}_LowerLeg',1-t)]:
  vg=legs.vertex_groups.get(n) or legs.vertex_groups.new(name=n);vg.add([v.index],w,'REPLACE')
body['outfit']='Original canonical hoodie topology extended into a short dress, seated corrective, inner shorts, amber sewn hem.'
bpy.ops.wm.save_as_mainfile(filepath=str(R/'NekoAFK-fashion-v003.blend'))
print('CONTINUOUS_DRESS_AND_ANKLE_REFINED',flush=True)
