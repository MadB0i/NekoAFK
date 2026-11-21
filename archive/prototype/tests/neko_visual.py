"""Archived room regression + visual evidence. Desktop product tests: neko_desktop.py. Run with the prototype server on 5783.
Requires Python Playwright and Pillow. Never writes to the approved asset directory.
"""
from pathlib import Path
import json, hashlib, time
from PIL import Image, ImageOps, ImageDraw
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / '.artifacts' / 'neko-validation'
OUT.mkdir(parents=True, exist_ok=True)
STATES = ['editing', 'testing', 'failed', 'frustrated', 'verifying', 'success']
HASHES = ['cd6500d853186828f041cf4a21081f7e0e77a54a63db3d4af7e47eaf9d6bd6fe', '8d9b00ddc28c60936b593df0fc5f32504a82804153d87735631cebf5fa6e1512', 'c8329aa637432a0ffbe96071f6834dfbd415afb5ee08304b724e67af731d9b7e', 'b630c80f3507d11200ed21f48cdc2a635a3c2082cf35c67c7f0702310cf314f5', '0b8e9785237df3bc03d6d433b6b3e2250c743eee0564f2e51ca0c7360d6c9867', '6c5711f486916ac00537095e7c49ef6f2e61b6c0292d544eb4fcaa4db1957990']
for state, expected in zip(STATES, HASHES):
    asset = ROOT / 'prototype/assets/neko' / f'neko-{state}.png'
    assert hashlib.sha256(asset.read_bytes()).hexdigest() == expected, f'Artwork changed: {state}'

# Bounds include all nonzero alpha, even almost-invisible edge pixels.
MEASURE = '''() => {
 const r = el => el.getBoundingClientRect().toJSON();
 const room = r(stage), viewport = r(nekoStage);
 const images = nimgs.map(img => {
   const box=r(img), m=NEKO_MANIFEST[img.dataset.k], c=getComputedStyle(img);
   return {state:img.dataset.k, opacity:+c.opacity, visibility:c.visibility, transform:c.transform,
     bounds:{left:box.left+m.bounds[0]/m.size[0]*box.width,
       top:box.top+m.bounds[1]/m.size[1]*box.height,
       right:box.left+m.bounds[2]/m.size[0]*box.width,
       bottom:box.top+m.bounds[3]/m.size[1]*box.height}};
 });
 return {state:stage.dataset.state, room, viewport, images,
   ancestors:[nekoStage,position,nekoStage.querySelector('.neko-motion')].map(e=>({opacity:+getComputedStyle(e).opacity, filter:getComputedStyle(e).filter})),
   bubble:r(document.querySelector('.bubble')), monitor:r(document.querySelector('.monitor')),
   height:document.documentElement.scrollHeight, width:document.documentElement.scrollWidth};
}'''

def check(m, settled=True):
    assert all(a['opacity']==1 and a['filter']=='none' for a in m['ancestors']), m
    for im in m['images']:
        assert im['transform']=='none', im
        for outer in [m['room'],m['viewport']]:
            assert im['bounds']['left'] >= outer['left']-1, im
            assert im['bounds']['top'] >= outer['top']-1, im
            assert im['bounds']['right'] <= outer['right']+1, im
            assert im['bounds']['bottom'] <= outer['bottom']+1, im
        if settled:
            assert im['opacity'] == (1 if im['state']==m['state'] else 0), im
            assert im['visibility'] == ('visible' if im['state']==m['state'] else 'hidden'), im

def sheet(paths, target, columns=3, width=600):
    thumbs=[]
    for path in paths:
        im=Image.open(path).convert('RGB'); im.thumbnail((width,420))
        tile=Image.new('RGB',(width,450),'#100c1a'); tile.paste(im,((width-im.width)//2,26))
        ImageDraw.Draw(tile).text((12,8),path.stem,fill='white'); thumbs.append(tile)
    canvas=Image.new('RGB',(width*columns,450*((len(thumbs)+columns-1)//columns)),'#100c1a')
    for i,tile in enumerate(thumbs): canvas.paste(tile,((i%columns)*width,(i//columns)*450))
    canvas.save(target)

with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    page=browser.new_page()
    errors=[]
    page.on('pageerror',lambda e: errors.append(str(e)))
    page.on('console',lambda m: errors.append(m.text) if m.type=='error' else None)
    all_metrics=[]
    for w,h in [(1920,1080),(1366,768)]:
        page.set_viewport_size({'width':w,'height':h})
        page.goto('http://127.0.0.1:5783/room.html');page.wait_for_load_state('networkidle')
        page.wait_for_function('nimgs.every(im => im.complete && im.naturalWidth > 0)')
        paths=[]
        for i,state in enumerate(STATES):
            page.keyboard.press(str(i+1))
            page.wait_for_function('(s) => document.querySelector(".neko-layer.is-active").dataset.k===s && !nekoStage.dataset.transitioning',arg=state)
            page.wait_for_timeout(550) # authored monitor-line stagger, then inspect settled frame
            metrics=page.evaluate(MEASURE);check(metrics)
            assert metrics['height'] <= h and metrics['width'] <= w, (w,metrics['height'],metrics['width'])
            # Speech and monitor do not overlap at either required viewport.
            assert metrics['bubble']['bottom'] < metrics['monitor']['top'], metrics
            path=OUT/f'{w}-{state}.png';page.screenshot(path=str(path));paths.append(path)
            all_metrics.append(metrics)
        sheet(paths,OUT/f'states-{w}.jpg')
        # Capture the ENTIRE actual demo, with rAF telemetry and visual samples targeted at 4/sec.
        page.evaluate('''(measure) => {
          window.samples=[]; window.sampleStop=false;
          const read=eval('('+measure+')');
          function tick(){samples.push(read());if(!sampleStop)requestAnimationFrame(tick)}
          requestAnimationFrame(tick);
        }''',MEASURE)
        page.locator('#autoBtn').click()
        started=time.monotonic(); frames=[]
        for frame in range(41):
            remaining=started+frame*.25-time.monotonic()
            if remaining>0: page.wait_for_timeout(remaining*1000)
            path=OUT/f'demo-{w}-{frame:02}.png';page.screenshot(path=str(path));frames.append(path)
        page.locator('#autoBtn').click()
        samples=page.evaluate('() => {sampleStop=true;return samples}')
        assert set(s['state'] for s in samples)==set(STATES)
        for sample in samples:check(sample,False)
        (OUT/f'demo-{w}-metrics.json').write_text(json.dumps(samples),encoding='utf-8')
        for offset in range(0,41,12):sheet(frames[offset:offset+12],OUT/f'demo-{w}-review-{offset//12}.jpg',columns=3,width=480)
    # Rapid interruptions must resolve to exactly one fully opaque state.
    for i in range(24):page.keyboard.press(str(i%6+1))
    page.wait_for_function('!nekoStage.dataset.transitioning')
    check(page.evaluate(MEASURE))
    page.emulate_media(reduced_motion='reduce');page.keyboard.press('2')
    page.wait_for_function('!nekoStage.dataset.transitioning');check(page.evaluate(MEASURE))
    assert page.locator('.neko-motion').evaluate('(e)=>getComputedStyle(e).animationName')=='none'
    # Space on a focused state button selects it, not the global demo shortcut.
    page.locator('[data-s="failed"]').focus();page.keyboard.press('Space')
    assert page.locator('#stage').get_attribute('data-state')=='failed'
    assert not page.locator('#autoBtn').evaluate('(e)=>e.classList.contains("run")')
    assert page.locator('[data-s="failed"]').evaluate('(e)=>getComputedStyle(e).outlineStyle')!='none'
    page.emulate_media(reduced_motion='no-preference')
    try:
        page.add_script_tag(url='https://cdn.jsdelivr.net/npm/axe-core@4/axe.min.js')
        axe=page.evaluate('async ()=>(await axe.run()).violations')
        (OUT/'axe.json').write_text(json.dumps(axe,indent=2),encoding='utf-8')
        print('AXE',[(v['id'],v['impact']) for v in axe])
    except Exception as e:print('AXE unavailable:',str(e)[:180])
    assert not errors,errors
    (OUT/'states-metrics.json').write_text(json.dumps(all_metrics,indent=2),encoding='utf-8')
    browser.close()
print('PASS: assets unchanged; all six states, both desktop sizes, full demos, rapid interruption, reduced motion, keyboard and no console errors.')

