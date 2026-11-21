"""Real Windows HUD acceptance. Agent inputs here are labelled hook fixtures.
The independent verifier is a real process. OpenCode server coverage is separate.
"""
import argparse, ctypes, hashlib, json, os, subprocess, time, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[1]

def main():
    ctypes.windll.shcore.SetProcessDpiAwareness(2) # All Win32 fixture coordinates are physical pixels.
    parser=argparse.ArgumentParser();parser.add_argument('--art',type=Path,default=ROOT/'.artifacts/live-progress/native');args=parser.parse_args()
    args.art.mkdir(parents=True,exist_ok=True);data=args.art/f'data-{time.time_ns()}';data.mkdir();workspace=data/'workspace';workspace.mkdir()
    config={'settings':{'workspace':str(workspace),'verify_program':'cmd.exe','verify_args':['/d','/c','exit 0'],'hud_enabled':True,'attached':False,'transparent':True,'dock_visible':False},'placements':{'neko':{'x':650,'y':280,'width':300,'height':300},'telemetry':{'x':100,'y':100,'width':460,'height':650}}}
    (data/'settings.json').write_text(json.dumps(config));env=dict(os.environ,NEKOAFK_DATA_DIR=str(data),WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS='--remote-debugging-port=9393')
    exe=ROOT/'src-tauri/target/release/nekoafk.exe';app=subprocess.Popen([str(exe)],env=env);producer=video=backdrop=None
    report={'exe_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'checks':{},'errors':[],'fixture':'Production OpenCode hooks with labelled synthetic events; independent verification is a real command','limits':['Programmatic native positioning on one monitor is not physical mixed-DPI dragging.','No spoken Narrator, physical tray, exclusive fullscreen or actual OS sleep test.']}
    try:
        deadline=time.monotonic()+40
        while True:
            try:version=json.load(urllib.request.urlopen('http://127.0.0.1:9393/json/version',timeout=1));break
            except Exception:
                if time.monotonic()>deadline:raise
                time.sleep(.1)
        with sync_playwright() as p:
            browser=p.chromium.connect_over_cdp(version['webSocketDebuggerUrl']);deadline=time.monotonic()+30
            while True:
                pages=[pg for c in browser.contexts for pg in c.pages]
                if all(any('surface='+s in pg.url for pg in pages) for s in ['hud','neko','telemetry','settings']):break
                if time.monotonic()>deadline:raise AssertionError('Missing native surfaces')
                if pages:pages[0].wait_for_timeout(100)
            hud=next(pg for pg in pages if 'surface=hud' in pg.url);cat=next(pg for pg in pages if 'surface=neko' in pg.url);dock=next(pg for pg in pages if 'surface=telemetry' in pg.url);settings=next(pg for pg in pages if 'surface=settings' in pg.url)
            for pg in pages:pg.on('pageerror',lambda e:report['errors'].append(str(e)));expect(pg.locator('#app')).to_have_attribute('data-ready','true')
            def invoke(c,a=None):return hud.evaluate('async([c,a])=>await window.__TAURI_INTERNALS__.invoke(c,a)',[c,a or {}])
            def snap():return invoke('get_snapshot')
            def check(name):report['checks'][name]='passed';print('PASS '+name,flush=True)
            def state(value):expect(hud.locator('#app')).to_have_attribute('data-state',value)
            def capture(name):hud.screenshot(path=str(args.art/(name+'.png')),omit_background=True)
            producer=subprocess.Popen(['node',str(ROOT/'tests/quality_events.mjs'),str(workspace)],env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True,creationflags=subprocess.CREATE_NO_WINDOW);assert json.loads(producer.stdout.readline())['ready']
            def send(action,**fields):
                producer.stdin.write(json.dumps({'action':action,**fields})+'\n');producer.stdin.flush();assert json.loads(producer.stdout.readline())['ok']
            send('idle');state('idle');expect(hud.locator('#planTrack')).to_be_hidden();capture('no-plan')
            # A neutral, non-fullscreen native backdrop keeps unrelated desktop
            # content out of the compositor recording; the app pixels are unedited.
            code="import ctypes;ctypes.windll.shcore.SetProcessDpiAwareness(2);import tkinter as t;r=t.Tk();r.overrideredirect(True);r.geometry('730x400+610+230');r.configure(bg='#eeede8');r.mainloop()"
            backdrop=subprocess.Popen(['python','-c',code],creationflags=subprocess.CREATE_NO_WINDOW);cat.wait_for_timeout(700)
            log=open(args.art/'video.log','w');video=subprocess.Popen(['ffmpeg','-y','-f','gdigrab','-framerate','30','-draw_mouse','0','-offset_x','610','-offset_y','230','-video_size','730x400','-i','desktop','-an','-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p',str(args.art/'neko-live-progress.mp4')],stdin=subprocess.PIPE,stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)
            send('start',operation='demo');state('active');expect(hud.locator('#hudActivity')).to_have_text('Shell running');cat.wait_for_timeout(5000);capture('tool-no-plan')
            send('plan',statuses=['completed','pending','in_progress']);expect(hud.locator('#hudPlan')).to_have_text('Plan progress · 1 / 3');cat.wait_for_timeout(5000);capture('plan-one-third')
            send('plan',statuses=['completed','completed','pending']);expect(hud.locator('#hudPlan')).to_have_text('Plan progress · 2 / 3');cat.wait_for_timeout(4000)
            send('permission');state('permission');cat.wait_for_timeout(5000);capture('permission')
            send('resolved');send('end',operation='demo',exit=None);state('active');expect(hud.locator('#progressDetail')).to_contain_text('Exit unknown');cat.wait_for_timeout(5000);capture('unknown-exit')
            send('plan',statuses=['completed','completed','completed']);send('claimed');state('claimed');assert snap()['progress']['tone']!='verified';cat.wait_for_timeout(4000);capture('plan-complete-unverified')
            invoke('run_verification');state('verified');cat.wait_for_timeout(7000);capture('verified')
            video.stdin.write(b'q\n');video.stdin.flush();video.wait(timeout=30);video=None;log.close();backdrop.terminate();backdrop.wait(timeout=10);backdrop=None
            check('native_fixture_showcase_and_independent_verification')
            send('plan',statuses=['pending','completed','pending','pending']);expect(hud.locator('#hudPlan')).to_have_text('Plan progress · 1 / 4');state('claimed')
            send('plan',statuses=[]);expect(hud.locator('#planTrack')).to_be_hidden();send('plan',statuses=['bad']);expect(hud.locator('#hudPlan')).to_have_text('No plan observed');check('plan_add_reopen_remove_and_invalid')
            send('start',operation='cancelled');state('active');send('interrupted');state('inconclusive');send('end',operation='cancelled',exit=0);cat.wait_for_timeout(700);state('inconclusive');expect(hud.locator('#hudActivity')).to_have_text('Work interrupted');check('late_success_cannot_resurrect_interruption')
            send('start',operation='failure');send('end',operation='failure',exit=7);state('failed');capture('failure');check('numeric_failure')
            send('plan',statuses=['completed','pending']);send('writing',session='second-session')
            deadline=time.monotonic()+10
            while len(snap()['engine']['sessions'])<2:
                assert time.monotonic()<deadline;cat.wait_for_timeout(100)
            key=next(k for k,s in snap()['engine']['sessions'].items() if s['id']=='second-session');invoke('select_session',{'key':key});state('writing');expect(hud.locator('#planTrack')).to_be_hidden();assert snap()['progress']['session_key']==key;check('session_isolation')
            # Inject stale transport records only into this test's local spool.
            current=snap();selected=current['engine']['sessions'][key];queue=data/'bridge/queue';stamp=selected['last_activity']-1
            for n,at in enumerate([stamp,int(time.time()*1000)-100000]):
                event={'version':1,'adapter':'opencode','source':selected['source'],'id':f'stale-{n}','timestamp':at,'workspace':str(workspace),'session':'second-session','kind':'tasks','completed':99,'total':100}
                f=queue/f'{int(time.time()*1000)}-stale-{n}.tmp';f.write_text(json.dumps(event));f.replace(f.with_suffix('.json'))
            cat.wait_for_timeout(1000);assert snap()['progress']['plan'] is None;check('stale_and_out_of_order_plan_ignored')
            send('permission',session='second-session');state('permission');send('disconnect');expect(hud.locator('#progressDetail')).to_have_text('Offline · permission still pending');capture('offline-permission');check('offline_permission_remains_explicit')
            send('reconnect');send('resolved',session='second-session');send('start',session='second-session',operation='recovered');state('active');expect(hud.locator('#hudActivity')).to_have_text('Shell running');check('reconnect')
            invoke('window_action',{'action':'show-dock'});expect(dock.locator('#state')).to_have_text('Shell running');expect(dock.locator('#progressDetail')).to_have_text(hud.locator('#progressDetail').inner_text());dock.locator('#progressExplanation summary').click();expect(dock.locator('#progressExplanation')).to_contain_text('ETA unavailable');dock.screenshot(path=str(args.art/'dock-expanded-progress.png'));check('hud_and_dock_share_progress')
            invoke('window_action',{'action':'hide-dock'});hud.get_by_role('button',name='Collapse progress HUD').focus();hud.keyboard.press('Enter');expect(hud.locator('#hudDetails')).to_be_hidden();expect(hud.get_by_role('button',name='Expand progress HUD')).to_be_focused();capture('collapsed');assert hud.locator('#hudActivity').evaluate('e=>e.getBoundingClientRect().bottom<=innerHeight');hud.keyboard.press('Enter');expect(hud.locator('#hudDetails')).to_be_visible();check('keyboard_collapse_expand')
            diag=invoke('desktop_diagnostics');report['native']=diag;area=diag['monitors'][0]['work_area'];catwin=next(w for w in diag['windows'] if w['label']=='neko');setpos=ctypes.windll.user32.SetWindowPos;setpos.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_uint]
            report['corners']=[]
            for x,y in [(area['position']['x'],area['position']['y']),(area['position']['x']+area['size']['width']-300,area['position']['y']),(area['position']['x'],area['position']['y']+area['size']['height']-300),(area['position']['x']+area['size']['width']-300,area['position']['y']+area['size']['height']-300)]:
                assert setpos(catwin['native_handle'],None,x,y,0,0,0x0011);cat.wait_for_timeout(400);h=next(w for w in invoke('desktop_diagnostics')['windows'] if w['label']=='hud');pos=h['position'];size=h['size'];assert pos['x']>=area['position']['x'] and pos['y']>=area['position']['y'];assert pos['x']+size['width']<=area['position']['x']+area['size']['width'] and pos['y']+size['height']<=area['position']['y']+area['size']['height'];assert pos['x']+size['width']<=x or pos['x']>=x+300 or pos['y']+size['height']<=y or pos['y']>=y+300, {'target':(x,y),'actual':invoke('desktop_diagnostics')};report['corners'].append(h)
            setpos(catwin['native_handle'],None,650,280,0,0,0x0011);check('single_monitor_native_edge_positioning')
            s=snap()['settings'];s['reduced_motion']=True;invoke('save_settings',{'settings':s});expect(hud.locator('#app')).to_have_attribute('data-reduced-motion','true');assert hud.locator('#planMeter').evaluate("e=>getComputedStyle(e,'::-webkit-progress-value').transitionDuration")=='0s';check('reduced_motion')
            for pg in [hud,dock]:
                pg.evaluate((ROOT/'node_modules/axe-core/axe.min.js').read_text(encoding='utf-8'));violations=pg.evaluate('async()=> (await axe.run()).violations');assert not violations,violations
            check('axe_hud_and_dock')
            send('end',session='second-session',operation='recovered',exit=None);send('idle',session='second-session');state('idle')
            hud.evaluate("()=>{window.hudMutations=0;window.hudRaf=0;const raf=requestAnimationFrame.bind(window);window.requestAnimationFrame=cb=>{window.hudRaf++;return raf(cb)};new MutationObserver(()=>window.hudMutations++).observe(document.querySelector('main'),{subtree:true,childList:true,attributes:true,characterData:true})}");cat.wait_for_timeout(3500);quiet=hud.evaluate('()=>({mutations:window.hudMutations,raf:window.hudRaf})');assert quiet=={'mutations':0,'raf':0},quiet;report['quiet']=quiet;check('settled_hud_has_no_render_loop')
            invoke('window_action',{'action':'hide-neko'});assert not next(w for w in invoke('desktop_diagnostics')['windows'] if w['label']=='hud')['visible'];invoke('window_action',{'action':'recover'});check('companion_visibility')
            invoke('window_action',{'action':'settings'});settings.locator('[data-section="desktop"]').click();settings.locator('#hudEnabled').uncheck();settings.locator('#save').click();expect(settings.locator('#saved')).to_have_text('Settings saved locally');saved=json.loads((data/'settings.json').read_text());assert saved['settings']['hud_enabled'] is False and 'hud' not in saved['placements'];check('settings_disable_and_derived_placement_persistence')
            assert not report['errors'];send('quit');invoke('quit_app');app.wait(timeout=20);browser.close()
    finally:
        if video and video.poll() is None:video.stdin.write(b'q\n');video.stdin.flush();video.wait(timeout=30)
        for proc in [backdrop,producer,app]:
            if proc and proc.poll() is None:proc.terminate();proc.wait(timeout=15)
        (args.art/'report.json').write_text(json.dumps(report,indent=2))

if __name__=='__main__':main()
