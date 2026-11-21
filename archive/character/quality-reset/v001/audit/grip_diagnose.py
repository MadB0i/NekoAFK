import bpy,sys,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).parents[1];bpy.ops.wm.open_mainfile(filepath=str(R/'NekoAFK-editing-v001.blend'));s=bpy.context.scene;s.frame_set(1);r=bpy.data.objects['Armature'];p=r.pose.bones['QR01_Phone'].matrix@r.data.bones['QR01_Phone'].matrix_local.inverted();inv=p.inverted();d={}
for f in ['Index','Middle','Ring','Little','Thumb']:
 b=r.pose.bones['J_Bip_R_'+f+'3'];d[f]={'tip':list(inv@b.tail),'head':list(inv@b.head)}
d['thumb_chain']=[{'name':f'J_Bip_R_Thumb{i}','head':list(inv@r.pose.bones[f'J_Bip_R_Thumb{i}'].head),'length':r.data.bones[f'J_Bip_R_Thumb{i}'].length} for i in [1,2,3]]
o=bpy.data.objects['Body'];ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();ys=[];groups={};contacts={}
for v in me.vertices:
 q=inv@v.co
 if abs(q.x)<.032 and abs(q.z)<.0645 and abs(q.y)<.07:ys.append(q.y)
 if min(.032-abs(q.x),.0045-abs(q.y),.0645-abs(q.z))>.0008:
  n=o.vertex_groups[max(v.groups,key=lambda g:g.weight).group].name if v.groups else 'none';groups[n]=groups.get(n,0)+1;contacts.setdefault(n,[]).append(list(q))
d['intersecting_groups']=groups;d['contact_bounds']={n:[[min(p[i] for p in pts),max(p[i] for p in pts)] for i in range(3)] for n,pts in contacts.items()}
d['surface_y_quantiles']=[sorted(ys)[int((len(ys)-1)*t)] for t in [0,.1,.25,.5,.75,.9,.95,1]];ev.to_mesh_clear();print(json.dumps(d,indent=2))
