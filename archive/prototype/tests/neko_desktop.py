"""Desktop sandbox: two resolutions, six states, complete demo, real pointer controls.
Run: python prototype/tests/neko_desktop.py (server on 5783).
"""
from pathlib import Path
import hashlib, re, time
from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'.artifacts/desktop-validation';OUT.mkdir(parents=True,exist_ok=True)
STATES=['editing','testing','failed','frustrated','verifying','success']
hashes=re.search(r'HASHES = (\[.*?\])',(ROOT/'prototype/tests/neko_visual.py').read_text()).group(1)
import ast
for state,expected in zip(STATES,ast.literal_eval(hashes)):
    assert hashlib.sha256((ROOT/f'prototype/assets/neko/neko-{state}.png').read_bytes()).hexdigest()==expected

def inspect(frame,state):
    result=frame.evaluate('''() => {
      const r=e=>e.getBoundingClientRect(),stage=r(nekoStage);
      return {state:nekoCharacter.state, backgrounds:[document.documentElement,document.body].map(e=>getComputedStyle(e).backgroundColor),
        controls:document.querySelectorAll('button,input,a').length,
        ancestors:[nekoStage,rasterStage.position,document.querySelector('.neko-motion')].map(e=>({opacity:getComputedStyle(e).opacity,animation:getComputedStyle(e).animationName})),
        images:rasterStage.images.map(img=>{const b=r(img),m=rasterStage.manifest[img.dataset.k];return {state:img.dataset.k,opacity:+getComputedStyle(img).opacity,
          safe:b.left+m.bounds[0]/m.size[0]*b.width>=stage.left-1&&b.top+m.bounds[1]/m.size[1]*b.height>=stage.top-1&&b.left+m.bounds[2]/m.size[0]*b.width<=stage.right+1&&b.top+m.bounds[3]/m.size[1]*b.height<=stage.bottom+1};})};
    }''')
    assert result['state']==state,result
    assert result['controls']==0 and all(c=='rgba(0, 0, 0, 0)' for c in result['backgrounds'])
    assert all(a=={'opacity':'1','animation':'none'} for a in result['ancestors'])
    assert all(i['safe'] and i['opacity']==(1 if i['state']==state else 0) for i in result['images']),result

with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    for width,height in [(1920,1080),(1366,768)]:
        context=browser.new_context(viewport={'width':width,'height':height},record_video_dir=str(OUT/'video'),record_video_size={'width':width,'height':height})
        page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto('http://127.0.0.1:5783/desktop-lab.html');page.wait_for_load_state('networkidle')
        char=page.frame_locator('#characterWindow');dock=page.frame_locator('#dockWindow')
        frame=page.locator('#characterWindow').element_handle().content_frame()
        page.wait_for_function('document.querySelector("#rendererStatus").textContent.includes("Raster fallback")')
        for state in STATES:
            page.locator(f'[data-state="{state}"]').click();page.wait_for_timeout(450);inspect(frame,state)
            assert dock.locator('#state').inner_text()==state.upper()
            page.screenshot(path=str(OUT/f'{width}-{state}.png'))
        # Follow the entire real-time ten-second sequence, not just the final frame.
        page.locator('#demo').click();frame.wait_for_function('nekoCharacter.state === "editing"');seen=[];start=time.monotonic()
        while time.monotonic()-start<10.5:
            seen.append(frame.evaluate('nekoCharacter.state'));page.wait_for_timeout(180)
        assert list(dict.fromkeys(seen))==STATES,seen
        assert page.locator('#demo').inner_text()=='Play 10s sequence'
        before=page.locator('#characterWindow').bounding_box()
        # Drag with real pointer capture across the moving iframe.
        page.mouse.move(before['x']+before['width']/2,before['y']+before['height']/2);page.mouse.down();page.mouse.move(before['x']+before['width']/2-75,before['y']+before['height']/2-15,steps=12);page.mouse.up();page.wait_for_timeout(100)
        after=page.locator('#characterWindow').bounding_box();assert abs(after['x']-(before['x']-75))<2,(before,after)
        page.locator('#scale').fill('80');page.locator('#scale').dispatch_event('input');page.wait_for_timeout(100)
        scaled=page.locator('#characterWindow').bounding_box();assert abs(scaled['y']+scaled['height']-after['y']-after['height'])<2
        inspect(frame,'success')
        dock.locator('#expand').click();page.wait_for_timeout(100);assert dock.locator('#activity').is_visible()
        dock.locator('#attach').click();page.wait_for_timeout(100);assert not page.locator('#attached').is_checked()
        db=page.locator('#dockWindow').bounding_box();page.mouse.move(db['x']+70,db['y']+23);page.mouse.down();page.mouse.move(db['x']+105,db['y']-20,steps=8);page.mouse.up();page.wait_for_timeout(100)
        assert page.locator('#dockWindow').bounding_box()['y']<db['y']-30
        dock.locator('#hide').click();page.locator('#dockWindow').wait_for(state='hidden');page.locator('#showDock').check();assert page.locator('#dockWindow').is_visible()
        page.locator('#passthrough').check();assert page.locator('#characterWindow').evaluate('(e)=>getComputedStyle(e).pointerEvents')=='none'
        page.locator('#showCharacter').uncheck();assert page.locator('#characterWindow').is_hidden();page.locator('#showCharacter').check()
        page.reload();page.wait_for_load_state('networkidle');assert page.locator('#scale').input_value()=='80';assert not page.locator('#passthrough').is_checked()
        page.locator('#reset').click();page.locator('#checker').check();page.wait_for_timeout(150);page.screenshot(path=str(OUT/f'{width}-transparency.png'))
        # Computed transparent CSS alone misses an iframe UA color-scheme canvas fill.
        shot=Image.open(OUT/f'{width}-transparency.png').convert('RGB');r=page.locator('#characterWindow').bounding_box()
        assert max(shot.getpixel((int(r['x']+3),int(r['y']+3))))<80,'Unexpected opaque iframe canvas'
        assert not errors,errors
        context.close()
    browser.close()

for width in [1920,1366]:
    sheet=Image.new('RGB',(1500,630),'#17131f')
    for i,state in enumerate(STATES):
        im=Image.open(OUT/f'{width}-{state}.png').convert('RGB');im.thumbnail((500,290));x=(i%3)*500;y=(i//3)*315;sheet.paste(im,(x,y+22));ImageDraw.Draw(sheet).text((x+8,y+6),state,fill='white')
    sheet.save(OUT/f'{width}-states.jpg')
print('PASS: immutable art; all states at both desktop sizes; transparent UI-free character; no PNG animation; complete demos; drag, scale, dock, click-through preview, persistence; no page errors.')
