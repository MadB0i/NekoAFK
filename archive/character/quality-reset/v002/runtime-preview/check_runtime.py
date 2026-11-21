from pathlib import Path
import json,sys,base64
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,args=['--enable-webgl','--ignore-gpu-blocklist'])
 page=browser.new_page(viewport={'width':900,'height':1080},device_scale_factor=1)
 errors=[];warnings=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.on('console',lambda m:errors.append(m.text) if m.type=='error' else warnings.append(m.text) if m.type=='warning' else None)
 page.goto('http://127.0.0.1:5797/runtime-preview/',wait_until='networkidle');page.wait_for_function('window.qa?.ready || window.qa?.error',timeout=120000)
 assert page.evaluate('window.qa.ready'),page.evaluate('window.qa')
 page.evaluate('window.qa.setTime(0)');page.locator('footer,#note').evaluate_all('(els)=>els.forEach(e=>e.style.visibility="hidden")')
 for name in ['full','face','hand','feet']:
  page.evaluate('(name)=>window.qa.view(name)',name);page.evaluate('window.qa.setTime(0)');page.screenshot(path=str(R/'renders'/f'runtime-{name}.png'))
 page.evaluate('window.qa.view("full")')
 samples=[]
 for time in [0,.75,1.6,2.4,3.2,4.72,5.25,6.98,8]:
  page.evaluate('(t)=>window.qa.setTime(t)',time);samples.append({'time':time,**page.evaluate('window.qa.stats()')})
 if '--video' in sys.argv:
  folder=R/'runtime-frames';folder.mkdir(exist_ok=True)
  page.set_viewport_size({'width':720,'height':864});page.evaluate('window.qa.view("full")')
  for frame in range(192):
   data=page.evaluate('(t)=>{window.qa.setTime(t);return document.querySelector("canvas").toDataURL("image/png").split(",")[1]}',frame/24)
   (folder/f'frame-{frame:04d}.png').write_bytes(base64.b64decode(data))
   if frame%24==0:print('CAPTURED_SECOND',frame//24,flush=True)
 (R/'audit/runtime-playback.json').write_text(json.dumps({'errors':errors,'warnings':warnings,'samples':samples},indent=2))
 print(json.dumps({'errors':errors,'warnings':warnings,'clips':samples[0]['clips'],'mtoon':samples[0]['mtoon'],'render':samples[0]['render']},indent=2))
 browser.close()
