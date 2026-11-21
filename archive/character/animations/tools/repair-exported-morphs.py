import bpy,sys,struct,json,numpy as np
from pathlib import Path
AN=Path(__file__).resolve().parent.parent
bpy.ops.wm.open_mainfile(filepath=str(AN/'NekoAFK-animation-library.blend'))
# Export the authoritative Action KEY slot directly. In this Blender exporter build,
# merging NLA skeletal and shape-key passes keeps a zero-valued duplicate weight track.
# Standard glTF LINEAR morph samplers are replaced with the baked source values.
validation={}
for variant in ['barefoot','socks']:
    path=AN/f'NekoAFK-{variant}-animated.glb'; raw=path.read_bytes()
    jl,jt=struct.unpack_from('<II',raw,12); gltf=json.loads(raw[20:20+jl]); bo=20+jl; bl,bt=struct.unpack_from('<II',raw,bo); binary=bytearray(raw[bo+8:bo+8+bl])
    faceNodes=[i for i,n in enumerate(gltf['nodes']) if 'mesh' in n and 'Fcl_EYE_Close' in gltf['meshes'][n['mesh']].get('extras',{}).get('targetNames',[])]
    assert len(faceNodes)==1; faceNode=faceNodes[0]; names=gltf['meshes'][gltf['nodes'][faceNode]['mesh']]['extras']['targetNames']; assert len(names)==57
    def accessor(values,minimum,maximum):
        binary.extend(b'\0'*(-len(binary)%4)); off=len(binary); data=np.asarray(values,dtype='<f4').tobytes(); binary.extend(data)
        vi=len(gltf['bufferViews']); gltf['bufferViews'].append({'buffer':0,'byteOffset':off,'byteLength':len(data)})
        ai=len(gltf['accessors']); gltf['accessors'].append({'bufferView':vi,'componentType':5126,'count':len(values),'type':'SCALAR','min':[float(minimum)],'max':[float(maximum)]}); return ai
    checks={}
    for anim in gltf['animations']:
        action=bpy.data.actions[anim['name']]; slot=next(s for s in action.slots if s.target_id_type=='KEY'); bag=action.layers[0].strips[0].channelbag(slot)
        curves={c.data_path:c for c in bag.fcurves}; count=round(action.frame_range[1]-action.frame_range[0])+1
        times=np.arange(count,dtype='<f4')/24
        weights=np.array([[curves[f'key_blocks["{n}"].value'].evaluate(i+1) for n in names] for i in range(count)],dtype='<f4')
        inp=accessor(times,0,times[-1]); out=accessor(weights.flatten(),weights.min(),weights.max())
        si=len(anim['samplers']); anim['samplers'].append({'input':inp,'output':out,'interpolation':'LINEAR'})
        targets=[c for c in anim['channels'] if c['target']=={'node':faceNode,'path':'weights'}]
        assert len(targets)==1; targets[0]['sampler']=si
        checks[anim['name']]={'morph_samples':count,'max_weight':float(weights.max()),'blink_max':float(weights[:,names.index('Fcl_EYE_Close')].max())}
        assert weights.max()>.05
    gltf['buffers'][0]['byteLength']=len(binary); gltf.setdefault('extras',{})['NekoAFK_morph_export']='Baked Action KEY slot; standard LINEAR glTF weights.'
    js=json.dumps(gltf,separators=(',',':')).encode(); js+=b' '*(-len(js)%4); binary.extend(b'\0'*(-len(binary)%4))
    packed=struct.pack('<III',0x46546c67,2,12+8+len(js)+8+len(binary))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(binary),0x004e4942)+binary
    path.write_bytes(packed); validation[variant]=checks
    print('FACIAL_TRACKS_EXPORTED',variant,len(checks),'editing blink',checks['Neko_EDITING_Idle']['blink_max'],flush=True)
(AN/'morph-export-validation.json').write_text(json.dumps(validation,indent=2))
