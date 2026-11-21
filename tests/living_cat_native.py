"""Actual WebView2 character acceptance and native-window video.

Activity demonstration uses explicit test-only OpenCode hook fixtures. The
separate opencode_live_desktop test is the real OpenCode transport evidence.
No product preview mode, seeded telemetry, browser window or installer is used.
"""
import argparse
import io
import json
import os
from pathlib import Path
import subprocess
import time
import urllib.request
import psutil
from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / '.artifacts/living-cat'

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--keep-open', action='store_true')
    parser.add_argument('--port', type=int, default=9341)
    parser.add_argument('--art',type=Path,default=ART)
    args = parser.parse_args()
    globals()['ART']=args.art
    ART.mkdir(parents=True,exist_ok=True)
    data = ART / ('data-' + str(int(time.time())))
    workspace = ART / 'workspace'
    workspace.mkdir(exist_ok=True)
    data.mkdir()
    config = {'settings': {'workspace':str(workspace), 'verify_program':'powershell.exe',
              'verify_args':['-NoProfile','-Command','Start-Sleep 7; exit 0'],
              'scale':2, 'attached':False, 'neko_visible':True, 'dock_visible':True,
              'personality':'playful', 'transparent':False},
              'placements':{'neko':{'x':700,'y':280,'width':600,'height':600},
              'telemetry':{'x':1300,'y':280,'width':460,'height':650}}}
    (data/'settings.json').write_text(json.dumps(config))
    env = dict(os.environ, NEKOAFK_DATA_DIR=str(data),
               WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS=f'--remote-debugging-port={args.port}')
    app = subprocess.Popen([str(ROOT/'src-tauri/target/release/nekoafk.exe')],env=env)
    video = holder = None
    success = False
    report = {'fixture_demonstration':True, 'real_opencode_evidence':'../opencode-desktop-report.json',
              'screenshots':[], 'checks':{}, 'performances':[], 'data_dir':str(data), 'pid':app.pid}
    try:
        deadline = time.monotonic()+40
        while True:
            try:
                with urllib.request.urlopen(f'http://127.0.0.1:{args.port}/json/version',timeout=1) as r:
                    version=json.load(r)
                break
            except Exception:
                if time.monotonic()>deadline or app.poll() is not None: raise
                time.sleep(.1)
        with sync_playwright() as p:
            browser=p.chromium.connect_over_cdp(version['webSocketDebuggerUrl'])
            deadline=time.monotonic()+30
            while True:
                pages=[pg for c in browser.contexts for pg in c.pages]
                if all(any('surface='+s in pg.url for pg in pages) for s in ['settings','neko','telemetry']): break
                if time.monotonic()>deadline: raise AssertionError('native windows missing')
                if pages: pages[0].wait_for_timeout(100)
                else: browser.new_browser_cdp_session().send('Target.getTargets')
            neko=next(pg for pg in pages if 'surface=neko' in pg.url)
            dock=next(pg for pg in pages if 'surface=telemetry' in pg.url)
            settings=next(pg for pg in pages if 'surface=settings' in pg.url)
            errors=[]
            for pg in pages:
                pg.on('pageerror',lambda e:errors.append(str(e)))
                pg.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
                pg.wait_for_load_state('networkidle')
                expect(pg.locator('#app')).to_have_attribute('data-ready','true')
            def invoke(cmd,fields=None):
                return dock.evaluate('async ([c,a])=>await window.__TAURI_INTERNALS__.invoke(c,a)',[cmd,fields or {}])
            def emit(scenario):
                subprocess.run(['node',str(ROOT/'tests/emit-fixture.mjs'),str(workspace),scenario],
                               env=env,check=True,capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
            def state(value):
                for pg in [dock,neko]:expect(pg.locator('#app')).to_have_attribute('data-state',value,timeout=15000)
            def wait(seconds): neko.wait_for_timeout(seconds*1000)  # Deliberate performance observation interval.
            def capture(name):
                neko.screenshot(path=str(ART/f'{name}.png'),omit_background=True)
                report['screenshots'].append(name+'.png')
                report['performances'].append({'file':name+'.png','activity':neko.locator('#mascot').get_attribute('data-activity'),
                                              'state':dock.locator('#app').get_attribute('data-state')})
            invoke('window_action',{'action':'recover'})
            diag=invoke('desktop_diagnostics');report['native_windows']=diag
            # Capture the desktop-composited native window region. Direct HWND GDI
            # reads omit GPU WebView2 surfaces. The opaque background preference
            # keeps unrelated desktop content out of this review video.
            bounds=next(w for w in diag['windows'] if w['label']=='neko')
            log=open(ART/'video-capture.log','w')
            video=subprocess.Popen(['ffmpeg','-y','-f','gdigrab','-framerate','30','-draw_mouse','0',
                 '-offset_x',str(bounds['position']['x']),'-offset_y',str(bounds['position']['y']),
                 '-video_size',f"{bounds['size']['width']}x{bounds['size']['height']}",
                 '-i','desktop','-an','-c:v','libx264','-preset','fast','-crf','18',
                 '-pix_fmt','yuv420p',str(ART/'neko-native-activities.mp4')],stdin=subprocess.PIPE,
                 stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)
            failure_seen=0
            for scenario,expected,seconds in [('idle','idle',6),('busy','active',7),('planning','planning',7),
                 ('writing','writing',9),('testing','testing',8),('failure','failed',7),('failure','failed',8),
                 ('permission','permission',8)]:
                emit(scenario);state(expected);wait(3)
                name=scenario
                if scenario=='failure':
                    name='failure' if failure_seen==0 else 'repeated-failure';failure_seen+=1
                capture(name);wait(seconds-3)
            # Permissions retain priority even while later work is observed.
            emit('editing');state('permission');report['checks']['permission_priority']='passed'
            emit('resolved');state('editing');emit('claimed');state('claimed');wait(3);capture('unverified');
            invoke('run_verification');state('verifying');wait(4);capture('verifying');state('verified');wait(3);capture('verified');wait(6)
            # Explicit inconclusive outcome through a real cancelled check.
            invoke('run_verification');state('verifying');invoke('cancel_verification');state('inconclusive');wait(3);capture('inconclusive');wait(4)
            video.stdin.write(b'q\n');video.stdin.flush();video.wait(timeout=30);log.close();assert video.returncode==0
            meta=json.loads(subprocess.check_output(['ffprobe','-v','quiet','-show_format','-show_streams','-of','json',str(ART/'neko-native-activities.mp4')]))
            report['video']={'file':'neko-native-activities.mp4','duration':float(meta['format']['duration']),
                             'size':[meta['streams'][0]['width'],meta['streams'][0]['height']],
                             'capture':'desktop composition of actual native companion; opaque background preference'}
            assert report['video']['duration']>=20
            preferences=invoke('get_snapshot')['settings'];preferences['transparent']=True
            invoke('save_settings',{'settings':preferences})
            # Long observed busy period: sample a whole process tree including WebView2.
            holder=subprocess.Popen(['node',str(ROOT/'tests/hold-busy.mjs'),str(workspace),'75'],env=env,creationflags=subprocess.CREATE_NO_WINDOW)
            state('active');wait(2)
            process=psutil.Process(app.pid)
            def usage():
                processes=[process]+process.children(recursive=True);cpu=0;memory=0
                for proc in processes:
                    try:
                        times=proc.cpu_times();cpu+=times.user+times.system;memory+=proc.memory_info().rss
                    except (psutil.NoSuchProcess,psutil.AccessDenied): pass
                return cpu,memory,len(processes)
            before=usage();start=time.monotonic();observed=set();memory=[]
            for _ in range(14):
                wait(5);observed.add(neko.locator('#mascot').get_attribute('data-activity'));memory.append(usage()[1])
            after=usage();duration=time.monotonic()-start
            report['resources']={'seconds':duration,'cpu_percent_one_core':round((after[0]-before[0])/duration*100,2),
                  'rss_start_mib':round(before[1]/1048576,1),'rss_end_mib':round(after[1]/1048576,1),
                  'rss_peak_mib':round(max(memory)/1048576,1),'process_count':after[2], 'sampled_activities':sorted(observed)}
            try:
                report['resources']['private_working_set_mib']=round(sum(q.memory_full_info().uss for q in [process]+process.children(recursive=True))/1048576,1)
            except (psutil.NoSuchProcess,psutil.AccessDenied):pass
            assert len(observed)>=2
            report['checks']['70_second_native_activity']='passed'
            holder.wait(timeout=15);state('disconnected');emit('busy');state('active')
            report['checks']['bridge_disconnect_and_recovery']='passed'
            # User and OS motion controls freeze transforms while preserving expressions.
            s=invoke('get_snapshot')['settings'];s['reduced_motion']=True
            invoke('save_settings',{'settings':s});expect(neko.locator('#app')).to_have_attribute('data-motion','reduced')
            before_svg=neko.locator('#rig').inner_html();wait(1);assert before_svg==neko.locator('#rig').inner_html()
            static_before=usage();static_start=time.monotonic();wait(10);static_after=usage()
            report['resources']['reduced_motion_cpu_percent_one_core']=round((static_after[0]-static_before[0])/(time.monotonic()-static_start)*100,2)
            emit('permission');state('permission');wait(1);assert before_svg!=neko.locator('#rig').inner_html();emit('resolved');state('active')
            s['reduced_motion']=False;invoke('save_settings',{'settings':s})
            neko.emulate_media(reduced_motion='reduce');expect(neko.locator('#app')).to_have_attribute('data-motion','reduced')
            before_svg=neko.locator('#rig').inner_html();wait(1);assert before_svg==neko.locator('#rig').inner_html()
            neko.emulate_media(reduced_motion='no-preference');expect(neko.locator('#app')).to_have_attribute('data-motion','full')
            report['checks']['user_and_system_reduced_motion']='passed'
            invoke('window_action',{'action':'hide-neko'});expect(neko.locator('#app')).to_have_attribute('data-motion','paused')
            invoke('window_action',{'action':'recover'});expect(neko.locator('#app')).to_have_attribute('data-motion','full')
            report['checks']['hidden_window_suspension_and_recovery']='passed'
            s=invoke('get_snapshot')['settings'];s['scale']=1
            invoke('save_settings',{'settings':s});wait(1)
            default_before=usage();default_start=time.monotonic();wait(15);default_after=usage()
            report['resources']['default_scale_cpu_percent_one_core']=round((default_after[0]-default_before[0])/(time.monotonic()-default_start)*100,2)
            # Every personality persists through the real host and uses native controls.
            invoke('window_action',{'action':'settings'})
            settings.get_by_role('button',name='Character',exact=True).click()
            for mode in ['calm','chaos','playful']:
                settings.get_by_label('Personality',exact=True).select_option(mode)
                settings.get_by_role('button',name='Save settings',exact=True).click()
                expect(settings.locator('#saved')).to_have_text('Settings saved locally')
                assert invoke('get_snapshot')['settings']['personality']==mode
            settings.screenshot(path=str(ART/'settings-character-native.png'))
            report['checks']['personality_settings']='passed'
            # The companion selector swaps the mascot SVG at runtime and persists.
            for mode in ['cat','robot']:
                settings.get_by_label('Companion',exact=True).select_option(mode)
                settings.get_by_role('button',name='Save settings',exact=True).click()
                expect(settings.locator('#saved')).to_have_text('Settings saved locally')
                assert invoke('get_snapshot')['settings']['character']==mode
                expect(neko.locator('#mascot svg')).to_have_attribute('data-character',mode)
            report['checks']['character_settings']='passed'
            # Local axe, not a remote CDN, on actual native WebViews.
            for name,pg in [('settings',settings),('telemetry',dock),('neko',neko)]:
                pg.evaluate((ROOT/'node_modules/axe-core/axe.min.js').read_text(encoding='utf-8'))
                violations=pg.evaluate('async ()=>(await axe.run()).violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>n.target)}))')
                assert not violations,(name,violations)
                assert pg.evaluate('document.documentElement.scrollWidth<=innerWidth')
            report['checks']['native_axe_and_overflow']='passed'
            assert not errors,errors
            report['checks']['runtime_errors']='none'
            dock.screenshot(path=str(ART/'dock-native.png'))
            # Transparency comes from real WebView2 alpha, independent of the video codec.
            img=Image.open(io.BytesIO(neko.screenshot(omit_background=True))).convert('RGBA')
            assert img.getpixel((0,0))[3]==0
            report['checks']['transparent_pixels']='passed'
            (ART/'report.json').write_text(json.dumps(report,indent=2))
            print(json.dumps(report,indent=2),flush=True)
            success = True
            if not args.keep_open: invoke('quit_app')
            browser.close()
    finally:
        if video and video.poll() is None:
            video.terminate();video.wait(timeout=10)
        if holder and holder.poll() is None:
            holder.terminate();holder.wait(timeout=10)
        if (not args.keep_open or not success) and app.poll() is None:
            app.terminate();app.wait(timeout=15)

if __name__=='__main__':main()
