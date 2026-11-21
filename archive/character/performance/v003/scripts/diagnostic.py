import bpy,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(R/'NekoAFK-fashion-v003.blend'))
o=bpy.data.objects['NekoBareFeet • anatomical skin']
for z in [.13,.14,.15,.16,.17]:
 vs=[v.co for v in o.data.vertices if v.co.x>0 and abs(v.co.z-z)<.003]
 print('FOOT_RING',z,len(vs), [[min(v[k] for v in vs),max(v[k] for v in vs)] for k in range(3)] if vs else [])
