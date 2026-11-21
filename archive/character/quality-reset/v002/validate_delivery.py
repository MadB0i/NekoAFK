from pathlib import Path
import json,hashlib,math
from playwright.sync_api import sync_playwright
R=Path(__file__).parent
expected=json.loads((R/'audit/source-hashes.json').read_text());preserved=all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in expected.items());assert preserved
data=json.loads((R/'audit/runtime-playback.json').read_text());assert not data['errors'];samples=data['samples'];assert samples[0]['clips'][0]['duration']==8 and len(samples[0]['clips'])==1
assert all(s['webglError']==0 for s in samples)
def bone(sample,name):return next(b for b in sample['bones'] if b['name']==name)
hip0=bone(samples[0],'J_Bip_C_Hips')['pos'];drift=max(math.dist(hip0,bone(s,'J_Bip_C_Hips')['pos']) for s in samples)
blink=[m['values'][m['dict']['Fcl_EYE_Close']] for s in samples for m in s['morphs'] if 'Fcl_EYE_Close' in m['dict']]
assert max(blink)>.9 and min(blink)==0
with sync_playwright() as p:
 b=p.chromium.launch(headless=True)
 page=b.new_page();page.goto('http://127.0.0.1:5797/renders/NekoAFK-editing-v002-runtime.mp4',wait_until='domcontentloaded')
 page.wait_for_function('document.querySelector("video")?.readyState>=2')
 metadata=page.evaluate('''async()=>{const v=document.querySelector('video');v.muted=true;v.currentTime=0;await v.play();return {duration:v.duration,width:v.videoWidth,height:v.videoHeight}}''')
 page.wait_for_function('document.querySelector("video").ended',timeout=15000)
 metadata['ended']=True;metadata['error']=page.evaluate('document.querySelector("video").error?.message ?? null');assert not metadata['error'];b.close()
report={'original_files_preserved':preserved,'video':metadata,'runtime_errors':data['errors'],'runtime_hip_drift_m':drift,'blink_range':[min(blink),max(blink)],'clip':samples[0]['clips'][0],'mtoon_material_instances':samples[0]['mtoon'],'remaining_limits':'See README.md. Visual candidate, not production sign-off.'}
(R/'audit/delivery-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
