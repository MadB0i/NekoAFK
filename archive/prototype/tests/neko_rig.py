"""Layered-rig mechanics only: synthetic pixels never ship as character artwork.
Run with the static prototype server on 5783. Requires Python Playwright/Pillow.
"""
import copy, io, json
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]
scaffold=json.loads((ROOT/'prototype/assets/neko/rig/v2/manifest.json').read_text())
pack=copy.deepcopy(scaffold);pack['approved']=True
pack['nodes']={node:[637,850] for node in pack['nodes']}
for layer in pack['layers']:
    layer['variants']={'base':{'src':'/__rig_test__/base.png','rect':[600,650,16,16]}}
    if layer['id'].startswith('eye-'):
        layer['variants']={v:{'src':f'/__rig_test__/{v}.png','rect':[610,350,16,16]} for v in ['open','half','closed']}
for state,pose in pack['poses'].items():
    pose['views']={l['id']:'open' if l['id'].startswith('eye-') else 'base' for l in pack['layers']}
    pose['rotations']={'head':1.2 if state=='testing' else 0}
    if state=='success':pose['views']['phone']=None;pose['views']['hand-near-front']=None;pose['blink']=None
    if state!='frustrated':pose['views']['expression-accent']=None
png=io.BytesIO();Image.new('RGBA',(16,16),(128,64,192,255)).save(png,format='PNG')
PNG=png.getvalue()

with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    page=browser.new_page(viewport={'width':1366,'height':768})
    errors=[];requests=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('request',lambda r:requests.append(r.url))
    page.goto('http://127.0.0.1:5783/character.html');page.wait_for_load_state('networkidle')
    page.wait_for_function('nekoCharacter.status.reason === "awaiting-assets"')
    assert page.locator('.neko-rig').count()==0
    assert not any('/parts/' in u or '/expressions/' in u for u in requests)
    initial=page.locator('.neko-position').bounding_box()
    page.route('**/__rig_test__/*.png',lambda r:r.fulfill(body=PNG,content_type='image/png'))
    def install(data,path='pack.json'):
        page.route('**/__rig_test__/'+path,lambda r:r.fulfill(json=data))
        return page.evaluate('(path)=>nekoCharacter.loadRig(path)','/__rig_test__/'+path)
    assert install(pack)
    assert page.locator('.neko-rig-slot').count()==34
    assert page.locator('.neko-position').bounding_box()==initial
    assert page.locator('.neko-motion').is_hidden()
    assert page.locator('[data-part="chair-base"] .neko-rig-motion').count()==0
    asset_requests=len([u for u in requests if '/__rig_test__/' in u and u.endswith('.png')])
    # Real-time scheduler: body moves while chair remains fixed, with actual eye swaps.
    chair=page.locator('[data-part="chair-base"] img').bounding_box()
    page.wait_for_function('nekoCharacter.rig.slots.get("eye-near").key === "closed"',timeout=7000)
    assert page.evaluate('nekoCharacter.rig.slots.get("eye-far").key')=='closed'
    assert page.locator('[data-part="chair-base"] img').bounding_box()==chair
    assert page.locator('[data-part="torso"] .neko-rig-motion').evaluate('(e)=>getComputedStyle(e).transform')!='matrix(1, 0, 0, 1, 0, 0)'
    # Feet inherit knee rotation through the actual ancestor chain, independently of the chair.
    assert page.locator('[data-part="foot-near"] .neko-rig-motion[data-node="shin-near"]').count()==1
    assert page.locator('[data-part="foot-near"] .neko-rig-motion[data-node="foot-near"]').count()==1
    assert page.locator('[data-part="phone"] .neko-rig-motion[data-node="phone"]').count()==1
    assert page.locator('[data-part="hair-back"] .neko-rig-motion[data-node="hair-back"]').count()==1
    # Deterministic source-time sampling proves one-shot settling, not a recurring thump.
    reaction=page.evaluate('''() => {
      const r=nekoCharacter.rig;r.setState('failed');r.time=r.entryStart+175;r.applyMotion(1);
      const peak=r.nodes.get('tail-tip')[0].gesture.style.transform;
      r.time=r.entryStart+1600;r.applyMotion(1);
      const settled=r.nodes.get('tail-tip')[0].gesture.style.transform;
      r.setState('success');r.time=r.entryStart+330;r.applyMotion(1);
      return {peak,settled,arm:r.nodes.get('arm-near')[0].gesture.style.transform,
        chair:r.slots.get('chair-base').slot.querySelector('.neko-rig-gesture')===null};
    }''')
    assert reaction['peak']!='rotate(0deg)' and reaction['settled']=='rotate(0deg)' and reaction['arm']!='rotate(0deg)' and reaction['chair'],reaction
    for key,state in enumerate(scaffold['poses'],1):
        page.evaluate("s=>NekoSurface.setState(s)",state)
        assert page.locator('.neko-rig').get_attribute('data-state')==state
        assert page.locator('.neko-position').bounding_box()==initial
    assert page.locator('[data-part="phone"]').is_hidden()
    page.evaluate('NekoSurface.setState("editing")');assert page.locator('[data-part="phone"]').is_visible()
    assert len([u for u in requests if '/__rig_test__/' in u and u.endswith('.png')])==asset_requests, 'Pose changes must not fetch images'
    page.emulate_media(reduced_motion='reduce')
    page.wait_for_function('nekoCharacter.rig.frame === null')
    assert page.locator('[data-part="torso"] .neko-rig-motion').evaluate('(e)=>new DOMMatrix(getComputedStyle(e).transform).isIdentity'), page.locator('[data-part="torso"] .neko-rig-motion').get_attribute('style')
    assert page.evaluate('nekoCharacter.rig.slots.get("eye-near").key')=='open'
    page.emulate_media(reduced_motion='no-preference')
    page.wait_for_function('nekoCharacter.rig.frame !== null')
    page.evaluate('nekoCharacter.setVisible(false)');assert page.evaluate('nekoCharacter.rig.frame') is None
    page.evaluate('nekoCharacter.setVisible(true)');page.wait_for_function('nekoCharacter.rig.frame !== null')
    # Exercise visibility lifecycle deterministically without OS window automation.
    page.evaluate('Object.defineProperty(document,"hidden",{configurable:true,value:true});document.dispatchEvent(new Event("visibilitychange"))')
    assert page.evaluate('nekoCharacter.rig.frame') is None
    page.evaluate('delete document.hidden;document.dispatchEvent(new Event("visibilitychange"))')
    page.wait_for_function('nekoCharacter.rig.frame !== null')
    # Incomplete state, bad draw order, missing blink, wrong dimensions, failed decode.
    invalid=[]
    v=copy.deepcopy(pack);del v['poses']['success'];invalid.append(v)
    v=copy.deepcopy(pack);v['poses']['editing']['order'][0]='phone';invalid.append(v)
    v=copy.deepcopy(pack);v['poses']['testing']['blink']['eye-near'][1]='absent';invalid.append(v)
    v=copy.deepcopy(pack);v['poses']['failed']['entry']['tracks'][0]['keys'][-1][1]=2;invalid.append(v)
    v=copy.deepcopy(pack);v['layers'][0]['variants']['base']['rect'][2]=17;invalid.append(v)
    page.route('**/__rig_test__/broken.png',lambda r:r.fulfill(body=b'not a PNG',content_type='image/png'))
    v=copy.deepcopy(pack);v['layers'][0]['variants']['base']['src']='/__rig_test__/broken.png';invalid.append(v)
    for i,bad in enumerate(invalid):
        assert not install(bad,f'bad-{i}.json')
        assert page.locator('#nekoStage').get_attribute('data-renderer')=='raster'
        assert page.locator('.neko-rig').count()==0
        assert page.locator('.neko-layer.is-active').evaluate('(e)=>getComputedStyle(e).opacity')=='1'
        assert install(pack,f'recover-{i}.json')
    # A slow, stale manifest cannot replace a newer successful load.
    pending=[]
    page.route('**/__rig_test__/slow.json',lambda r:pending.append(r))
    page.evaluate('nekoCharacter.loadRig("/__rig_test__/slow.json"); true')
    page.wait_for_timeout(50)
    assert install(pack,'latest.json')
    assert pending
    pending[0].fulfill(json=scaffold)
    page.wait_for_timeout(100)
    assert page.locator('#nekoStage').get_attribute('data-renderer')=='rig'
    assert page.locator('.neko-rig').count()==1
    # Return to the current raster immediately, without changing stage geometry.
    page.evaluate('NekoSurface.setState("frustrated")');page.evaluate('nekoCharacter.useRaster()')
    assert page.locator('.neko-layer.is-active').get_attribute('data-k')=='frustrated'
    assert page.locator('.neko-layer.is-active').evaluate('(e)=>getComputedStyle(e).opacity')=='1'
    assert page.locator('.neko-position').bounding_box()==initial
    assert install(pack,'destroy.json')
    page.evaluate('window.oldRig=nekoCharacter.rig;nekoCharacter.destroy()')
    assert page.evaluate('oldRig.frame') is None
    assert page.locator('.neko-rig').count()==0
    # Forced raster must not even fetch the manifest.
    requests.clear();page.goto('http://127.0.0.1:5783/character.html?character=raster');page.wait_for_load_state('networkidle')
    assert not any('manifest.json' in u for u in requests)
    assert page.locator('#nekoStage').get_attribute('data-renderer')=='raster'
    assert not errors,errors
    browser.close()
print('PASS: pending pack, 34 layers, blink, chair isolation, all poses, reduced motion, visibility, malformed/decode fallback, stale load, rollback, disposal, and forced raster.')
