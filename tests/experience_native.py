"""Native visual review and paired measurements. Review-only rig access uses CDP,
never a product API. Rig review is labelled separately from OpenCode state evidence.
"""
import argparse, hashlib, json, os, re, subprocess, time, urllib.request
from pathlib import Path
from collections import Counter
import psutil
from playwright.sync_api import sync_playwright, expect
from quality_native import distribution

ROOT=Path(__file__).resolve().parents[1]

def expose_character(cat):
    cdp=cat.context.new_cdp_session(cat);scripts=[]
    cdp.on('Debugger.scriptParsed',lambda event:scripts.append(event));cdp.send('Debugger.enable')
    for script in scripts:
        if not script.get('url','').endswith('.js'):continue
        source=cdp.send('Debugger.getScriptSource',{'scriptId':script['scriptId']})['scriptSource']
        match=re.search(r'constructor\(\w+,(\w+)=crypto\.getRandomValues\(new Uint32Array\(1\)\)\[0\]\)\{',source)
        if match:break
    assert match
    def paused(e):
        frame=e['callFrames'][0]['callFrameId']
        cdp.send('Debugger.setVariableValue',{'scopeNumber':0,'variableName':match.group(1),'newValue':{'value':1234},'callFrameId':frame})
        cdp.send('Debugger.evaluateOnCallFrame',{'callFrameId':frame,'expression':'window.__nekoReview=this'})
        cdp.send('Debugger.resume')
    cdp.on('Debugger.paused',paused);point=match.end()
    cdp.send('Debugger.setBreakpointByUrl',{'url':script['url'],'lineNumber':source[:point].count('\n'),'columnNumber':point-source.rfind('\n',0,point)-1})
    cat.reload(wait_until='networkidle');cdp.send('Debugger.disable');cdp.detach()
    assert cat.evaluate('()=>!!window.__nekoReview?.director')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--exe',type=Path,default=ROOT/'src-tauri/target/release/nekoafk.exe');parser.add_argument('--art',type=Path,required=True);parser.add_argument('--mode',choices=['inspect','profile','ux','attention'],default='inspect');parser.add_argument('--repeats',type=int,default=3)
    args=parser.parse_args();args.art.mkdir(parents=True,exist_ok=True)
    report={'exe_sha256':hashlib.sha256(args.exe.read_bytes()).hexdigest(),'mode':args.mode,'runs':[],'limits':['Native WebView2 DOM mutation cadence is not GPU presentation timing.','Performance uses fixed seed 1234 and app process-tree CPU, percent of one core.','All-clip rig review directly selects authored clips through CDP; it is not agent activity.','Physical tray, mixed-DPI, Narrator, exclusive fullscreen and OS sleep are not tested here.']}
    for repeat in range(args.repeats if args.mode=='profile' else 1):
        data=args.art/f'data-{time.time_ns()}';data.mkdir();workspace=data/'workspace';workspace.mkdir()
        settings={'workspace':str(workspace),'scale':1,'attached':False,'transparent':True,'dock_visible':args.mode=='inspect','personality':'playful','verify_program':'cmd.exe','verify_args':['/d','/c','exit 0']}
        (data/'settings.json').write_text(json.dumps({'settings':settings,'placements':{'neko':{'x':650,'y':200,'width':300,'height':300},'telemetry':{'x':1040,'y':160,'width':460,'height':650}}}))
        port=9381+repeat if args.mode=='profile' else 9371
        env=dict(os.environ,NEKOAFK_DATA_DIR=str(data),WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS=f'--remote-debugging-port={port}')
        app=subprocess.Popen([str(args.exe.resolve())],env=env);producer=video=None;run={'phases':{},'errors':[]};report['runs'].append(run)
        try:
            deadline=time.monotonic()+40
            while True:
                try:version=json.load(urllib.request.urlopen(f'http://127.0.0.1:{port}/json/version',timeout=1));break
                except Exception:
                    if time.monotonic()>deadline:raise
                    time.sleep(.1)
            with sync_playwright() as p:
                browser=p.chromium.connect_over_cdp(version['webSocketDebuggerUrl'])
                deadline=time.monotonic()+20
                while True:
                    pages=[pg for c in browser.contexts for pg in c.pages]
                    if all(any('surface='+surface in pg.url for pg in pages) for surface in ['neko','telemetry','settings']):break
                    if time.monotonic()>deadline:raise AssertionError('Native surfaces did not finish opening')
                    if pages:pages[0].wait_for_timeout(100)
                    else:browser.new_browser_cdp_session().send('Target.getTargets')
                cat=next(pg for pg in pages if 'surface=neko' in pg.url);dock=next(pg for pg in pages if 'surface=telemetry' in pg.url);prefs=next(pg for pg in pages if 'surface=settings' in pg.url)
                for pg in pages:pg.on('pageerror',lambda e:run['errors'].append(str(e)));expect(pg.locator('#app')).to_have_attribute('data-ready','true')
                expose_character(cat)
                def invoke(c,a=None):return dock.evaluate('async([c,a])=>await window.__TAURI_INTERNALS__.invoke(c,a)',[c,a or {}])
                producer=subprocess.Popen(['node',str(ROOT/'tests/quality_events.mjs'),str(workspace)],env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True,creationflags=subprocess.CREATE_NO_WINDOW)
                assert json.loads(producer.stdout.readline())['ready']
                def send(action,**fields):
                    producer.stdin.write(json.dumps({'action':action,**fields})+'\n');producer.stdin.flush();assert json.loads(producer.stdout.readline())['ok']
                run['native']=invoke('desktop_diagnostics');run['webview_version']=version['Browser']
                if args.mode=='attention':
                    s=invoke('get_snapshot')['settings'];s.update(scale=2,transparent=False);invoke('save_settings',{'settings':s})
                    send('idle');expect(dock.locator('#app')).to_have_attribute('data-state','idle')
                    bounds=next(w for w in invoke('desktop_diagnostics')['windows'] if w['label']=='neko');log=open(args.art/'attention-video.log','w')
                    video=subprocess.Popen(['ffmpeg','-y','-f','gdigrab','-framerate','30','-draw_mouse','0','-offset_x',str(bounds['position']['x']),'-offset_y',str(bounds['position']['y']),'-video_size',f"{bounds['size']['width']}x{bounds['size']['height']}",'-i','desktop','-an','-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p',str(args.art/'natural-idle.mp4')],stdin=subprocess.PIPE,stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)
                    run['idle_samples']=[]
                    for second in range(60):
                        cat.wait_for_timeout(1000)
                        sample=cat.evaluate('()=>{const c=window.__nekoReview;return {elapsed:c.elapsed,...c.director.frame(c.elapsed)}}')
                        run['idle_samples'].append(sample)
                    video.stdin.write(b'q\n');video.stdin.flush();video.wait(timeout=30);video=None;log.close()
                elif args.mode=='inspect':
                    def capture(pg,name):pg.screenshot(path=str(args.art/(name+'.png')),omit_background=True)
                    send('writing');expect(dock.locator('#app')).to_have_attribute('data-state','writing');capture(dock,'dock-expanded')
                    invoke('window_action',{'action':'toggle-collapse'});expect(dock.locator('#app')).to_have_attribute('data-collapsed','true');capture(dock,'dock-collapsed')
                    run['collapsed']=dock.evaluate("()=>({height:innerHeight,state:document.querySelector('#state').getBoundingClientRect().toJSON(),header:document.querySelector('header').getBoundingClientRect().toJSON(),font:getComputedStyle(document.querySelector('#state')).fontSize})")
                    invoke('window_action',{'action':'toggle-collapse'});send('permission');expect(dock.locator('#app')).to_have_attribute('data-state','permission');capture(dock,'dock-permission')
                    # Review clips at the real native scale used for the existing showcase.
                    s=invoke('get_snapshot')['settings'];s.update(scale=2,transparent=False);invoke('save_settings',{'settings':s});invoke('window_action',{'action':'hide-dock'})
                    clips=json.loads(subprocess.check_output(['node','--input-type=module','-e',"import fs from 'node:fs';import ts from 'typescript';const code=ts.transpileModule(fs.readFileSync('src/director.ts','utf8'),{compilerOptions:{target:99,module:99}}).outputText;const m=await import('data:text/javascript;base64,'+Buffer.from(code).toString('base64'));console.log(JSON.stringify([...new Map(Object.entries(m.library).flatMap(([mood,clips])=>clips.map(clip=>[clip.id,{mood,clip}]))).values()]));"],cwd=ROOT))
                    bounds=next(w for w in invoke('desktop_diagnostics')['windows'] if w['label']=='neko');log=open(args.art/'rig-video.log','w')
                    video=subprocess.Popen(['ffmpeg','-y','-f','gdigrab','-framerate','30','-draw_mouse','0','-offset_x',str(bounds['position']['x']),'-offset_y',str(bounds['position']['y']),'-video_size',f"{bounds['size']['width']}x{bounds['size']['height']}",'-i','desktop','-an','-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p',str(args.art/'authored-rig-review.mp4')],stdin=subprocess.PIPE,stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)
                    run['clips']=[]
                    for item in clips:
                        cat.evaluate("item=>{const c=window.__nekoReview,d=c.director,t=c.elapsed;d.from=d.frame(t).pose;d.attention=d.attentionFrom={gazeX:0,gazeY:0,head:0,earL:0,earR:0};d.attentionAt=-10;d.current=item.clip;d.requested=d.mood=item.mood;d.started=d.transition=t;d.until=t+item.clip.duration+2;d.rate=d.variant=1;c.refresh();}",item)
                        cat.wait_for_timeout(3000);capture(cat,'clip-'+item['clip']['id']);cat.wait_for_timeout(max(0,item['clip']['duration']-3)*1000+800)
                        run['clips'].append(item['clip']['id']);print('Reviewed '+item['clip']['id'],flush=True)
                    video.stdin.write(b'q\n');video.stdin.flush();video.wait(timeout=30);video=None;log.close()
                    invoke('window_action',{'action':'settings'});prefs.locator('[data-section="character"]').click();capture(prefs,'settings-character')
                elif args.mode=='ux':
                    def capture(pg,name):pg.screenshot(path=str(args.art/(name+'.png')),omit_background=True)
                    send('writing');expect(dock.locator('#app')).to_have_attribute('data-state','writing')
                    invoke('window_action',{'action':'recover'});capture(dock,'dock-expanded')
                    send('flood',count=40,interval_ms=5)
                    expect(dock.locator('#activity li')).to_have_count(40,timeout=15000)
                    activity_list=dock.locator('#activity');activity_list.evaluate('e=>e.scrollTop=80')
                    anchor=activity_list.evaluate("e=>{const r=[...e.children].find(c=>c.getBoundingClientRect().bottom>e.getBoundingClientRect().top);return {key:r.dataset.key,offset:r.getBoundingClientRect().top-e.getBoundingClientRect().top}}")
                    send('start',operation='reading-anchor',testing=True);expect(dock.locator('#latestActivity')).to_be_visible()
                    offset=activity_list.evaluate("(e,key)=>[...e.children].find(c=>c.dataset.key===key).getBoundingClientRect().top-e.getBoundingClientRect().top",anchor['key'])
                    assert abs(offset-anchor['offset'])<2,(anchor,offset);capture(dock,'dock-reading-preserved')
                    dock.locator('#latestActivity').click();assert activity_list.evaluate('e=>e.scrollTop')==0;expect(activity_list).to_be_focused()
                    run['log_anchor_shift_px']=offset-anchor['offset']
                    assert dock.locator('#activity time').first.evaluate("e=>getComputedStyle(e).whiteSpace")=='nowrap'
                    send('writing',session='other-session');expect(dock.locator('#session option')).to_have_count(2)
                    activity_list.evaluate('e=>e.scrollTop=80')
                    other=dock.locator('#session option').filter(has_text='er-session').get_attribute('value')
                    dock.locator('#session').select_option(other)
                    expect(activity_list.locator('li')).to_have_count(1)
                    assert activity_list.evaluate('e=>e.scrollTop')==0;expect(dock.locator('#latestActivity')).to_be_hidden()
                    invoke('window_action',{'action':'toggle-collapse'});expect(dock.locator('#compactContext')).to_be_visible();expect(dock.locator('#compactContext')).to_contain_text('workspace');capture(dock,'dock-collapsed')
                    assert dock.locator('#state').evaluate('e=>e.getBoundingClientRect().bottom<=innerHeight')
                    invoke('window_action',{'action':'toggle-collapse'})
                    s=invoke('get_snapshot')['settings'];s.update(scale=.5,reduced_motion=True);invoke('save_settings',{'settings':s})
                    assert dock.locator('.verification-block').evaluate('e=>getComputedStyle(e).animationName')=='none'
                    cat.locator('#menuToggle').click();actions=[]
                    for _ in range(8):
                        cat.keyboard.press('Tab')
                        item=cat.evaluate("()=>{const e=document.activeElement,n=document.querySelector('#companionTools'),r=e.getBoundingClientRect(),b=n.getBoundingClientRect();return {action:e.dataset.action,visible:r.top>=b.top&&r.bottom<=b.bottom}}")
                        actions.append(item['action']);assert item['visible'],item
                    assert len(set(actions))==8,actions;capture(cat,'companion-minimum-controls');cat.keyboard.press('Escape');expect(cat.locator('#menuToggle')).to_be_focused()
                    invoke('window_action',{'action':'settings'});prefs.locator('[data-section="character"]').click();prefs.locator('#personality').select_option('calm');send('claimed');expect(prefs.locator('#personality')).to_have_value('calm');expect(prefs.locator('#saved')).to_have_text('Unsaved changes');capture(prefs,'settings-unsaved')
                    run['checks']={name:'passed' for name in ['activity_reading_anchor','latest_activity_focus','session_switch_resets_activity_reading','timestamp_no_wrap','collapsed_workspace_context','minimum_size_all_eight_controls','reduced_motion_disclosure','settings_dirty_input_preserved']}
                else:
                    cat.evaluate("()=>{window.paints=[];window.frames=0;const raf=requestAnimationFrame.bind(window);window.requestAnimationFrame=cb=>raf(t=>{window.frames++;cb(t)});new MutationObserver(()=>window.paints.push(performance.now())).observe(document.querySelector('#rig'),{subtree:true,attributes:true});}")
                    def usage():
                        result={}
                        for proc in [psutil.Process(app.pid)]+psutil.Process(app.pid).children(recursive=True):
                            try:t=proc.cpu_times();result[proc.pid]={'cpu':t.user+t.system,'uss':proc.memory_full_info().uss}
                            except psutil.Error:pass
                        return result
                    def phase(name,seconds):
                        cat.evaluate('()=>{window.paints=[];window.frames=0;}');before=usage();start=time.monotonic();activities=Counter()
                        while time.monotonic()-start<seconds:
                            cat.wait_for_timeout(500);activities[cat.locator('#mascot').get_attribute('data-activity')]+=1
                        after=usage();duration=time.monotonic()-start;raw=cat.evaluate('()=>({paint:window.paints,frames:window.frames})')
                        if name in ['natural_idle','keyboard']:assert raw['frames']>0, 'Visible animation must run for a valid comparison'
                        run['phases'][name]={'seconds':duration,'cpu_one_core':sum(v['cpu']-before[k]['cpu'] for k,v in after.items() if k in before)/duration*100,'uss_mib':sum(v['uss'] for v in after.values())/1048576,'frames':raw['frames'],'mutations':len(raw['paint']),'intervals_under_100ms':distribution([b-a for a,b in zip(raw['paint'],raw['paint'][1:]) if b-a<100]),'activities':dict(activities),'processes_appeared':list(set(after)-set(before)),'processes_retired':list(set(before)-set(after))}
                        (args.art/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps({'repeat':repeat,'phase':name,**run['phases'][name]}),flush=True)
                    send('idle');expect(dock.locator('#app')).to_have_attribute('data-state','idle');phase('natural_idle',60)
                    send('writing');expect(dock.locator('#app')).to_have_attribute('data-state','writing');phase('keyboard',14)
                    invoke('window_action',{'action':'hide-neko'});phase('hidden',5);assert run['phases']['hidden']['frames']==0
                    s=invoke('get_snapshot')['settings'];s['reduced_motion']=True;invoke('save_settings',{'settings':s});invoke('window_action',{'action':'recover'});phase('reduced',5);assert run['phases']['reduced']['frames']==0
                assert not run['errors'];send('quit');invoke('quit_app');app.wait(timeout=20);browser.close()
        finally:
            if video:video.stdin.write(b'q\n');video.stdin.flush();video.wait(timeout=30)
            for proc in [producer,app]:
                if proc and proc.poll() is None:proc.terminate();proc.wait(timeout=15)
            (args.art/'report.json').write_text(json.dumps(report,indent=2))

if __name__=='__main__':main()
