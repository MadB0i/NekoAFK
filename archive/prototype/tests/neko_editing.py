"""Editing-only rig acceptance evidence. No other states are loaded or exercised."""
from pathlib import Path
import hashlib,json,math,time
from playwright.sync_api import sync_playwright
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'.artifacts/editing-proof/final';OUT.mkdir(parents=True,exist_ok=True)
assert hashlib.sha256((ROOT/'prototype/assets/neko/neko-editing.png').read_bytes()).hexdigest()=='cd6500d853186828f041cf4a21081f7e0e77a54a63db3d4af7e47eaf9d6bd6fe'
TIMES=[0,1.05,3.05,2.12,2.15,2.24,3.14,3.69,9.0,10.47,16.35,18.9,23.99]
with sync_playwright() as p:
    browser=p.chromium.launch()
    for width,height in [(1920,1080),(1366,768)]:
        context=browser.new_context(viewport={'width':width,'height':height})
        page=context.new_page();errors=[];requests=[]
        page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:requests.append(r.url))
        page.goto('http://127.0.0.1:5783');page.wait_for_load_state('networkidle')
        frame=page.locator('#characterWindow').element_handle().content_frame();frame.wait_for_function('window.editingRig')
        assert frame.locator('#nekoStage').get_attribute('data-renderer')=='editing-rig'
        assert not any(f'neko-{s}.png' in u for u in requests for s in ['testing','failed','frustrated','verifying','success'])
        for t in TIMES:
            frame.evaluate('t=>editingRig.control({playing:false,time:t})',t)
            sample=frame.evaluate('''() => {
              const r=editingRig,m=r.matrices,n=r.nodes;
              const point=(id,p)=>{const q=new DOMPoint(...p).matrixTransform(m.get(id));return [q.x,q.y]};
              return {time:r.time,base:m.get('base').isIdentity,upper:m.get('upper-leg').isIdentity,
                knee:point('lower-leg',n.get('lower-leg').pivot),expectedKnee:n.get('lower-leg').pivot,
                footPivot:point('foot',n.get('foot').pivot),parentFoot:point('lower-leg',n.get('foot').pivot),
                chairTransform:r.scene.querySelector('[data-part="chair"]').getAttribute('transform'),
                global:r.scene.getAttribute('transform'),root:r.root.getAttribute('transform'),snapshot:r.snapshot()};
            }''')
            assert sample['base'] and sample['upper'] and sample['chairTransform'] is None and sample['root'] is None
            assert sample['global']=='translate(-5 65)'
            assert math.dist(sample['knee'],sample['expectedKnee'])<.0001
            assert math.dist(sample['footPivot'],sample['parentFoot'])<.0001
            assert max(abs(n['angle']) for n in sample['snapshot']['nodes'] if n['id']=='torso')<.04
            page.screenshot(path=str(OUT/f'{width}-{t:05.2f}.png'))
        # Debug bounds use the cutout geometry, not the full source image rectangle.
        page.locator('#debug').check();page.wait_for_timeout(100)
        assert page.locator('#jointTree button').count()==17
        assert frame.locator('.editing-debug').is_visible()
        bounds=frame.evaluate('editingRig.debugItems.get("lower-leg").box.getBBox().width')
        assert 100<bounds<400,bounds
        page.screenshot(path=str(OUT/f'{width}-debug.png'))
        page.locator('#jointTree [data-node="thumb"]').click();frame.wait_for_function('editingRig.selected === "thumb"')
        page.locator('#debug').uncheck()
        # Scrub, original comparison, playback, hidden activity and reduced motion.
        page.locator('#time').fill('2.15');page.locator('#time').dispatch_event('input');frame.wait_for_function('editingRig.time === 2.15');assert frame.evaluate('editingRig.blink')
        page.locator('#original').check();frame.wait_for_function('editingRig.original');assert frame.evaluate('editingRig.frame') is None
        page.screenshot(path=str(OUT/f'{width}-original.png'));page.locator('#original').uncheck()
        page.locator('#play').click();frame.wait_for_function('editingRig.frame !== null')
        frame.evaluate('editingRig.setActive(false)');assert frame.evaluate('editingRig.frame') is None
        frame.evaluate('editingRig.setActive(true)');frame.wait_for_function('editingRig.frame !== null')
        page.emulate_media(reduced_motion='reduce');frame.wait_for_function('editingRig.frame === null')
        page.emulate_media(reduced_motion='no-preference');frame.wait_for_function('editingRig.frame !== null')
        page.locator('#checker').check();page.wait_for_timeout(100);page.screenshot(path=str(OUT/f'{width}-transparent.png'))
        # Full 24-second live clip: observe every joint changing without resetting.
        if width==1366:
            page.locator('#checker').uncheck();frame.evaluate('editingRig.control({time:0,playing:true})')
            samples=[];start=time.monotonic();i=0
            while time.monotonic()-start<24.4:
                samples.append(frame.evaluate('editingRig.snapshot()'))
                if i%4==0:page.screenshot(path=str(OUT/f'live-{i//4:02}.png'))
                page.wait_for_timeout(70);i+=1
            assert any(s['blink'] for s in samples)
            for part in ['head','ear-left','ear-right','tail','lower-leg','foot','second-foot','thumb','hair-front','hair-back']:
                values=[next(n['angle'] for n in s['nodes'] if n['id']==part) for s in samples]
                assert max(values)-min(values)>.005,(part,values)
            (OUT/'live-samples.json').write_text(json.dumps(samples),encoding='utf-8')
        assert not errors,errors
        context.close()
    # Missing support art keeps the original, never a half-assembled rig.
    page=browser.new_page();page.route('**/blink-closed.png',lambda r:r.abort());page.goto('http://127.0.0.1:5783/editing-character.html');page.wait_for_load_state('networkidle');assert page.locator('.neko-motion').is_visible();assert page.locator('.editing-rig').count()==0
    browser.close()

for width in [1920,1366]:
    sheet=Image.new('RGB',(1500,900),'#17131f')
    for i,t in enumerate(TIMES[:9]):
        im=Image.open(OUT/f'{width}-{t:05.2f}.png').convert('RGB');im.thumbnail((500,275));x=i%3*500;y=i//3*300;sheet.paste(im,(x,y+22));ImageDraw.Draw(sheet).text((x+10,y+5),f'{t:.2f}s',fill='white')
    sheet.save(OUT/f'{width}-review.jpg')
print('PASS: original hash; editing-only assets; fixed chair/base/knee; inherited ankle; 17 joints; debug bounds/tree; controls; full 24s live timeline; reduced motion; decode fallback; no page errors. Visual quality requires reviewing evidence, not just these assertions.')
