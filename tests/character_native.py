"""Character-direction acceptance in the production Windows WebView2 app.

The showcase uses clearly identified OpenCode hook fixtures, through the real
bridge. Its success reaction follows an actual independent command exit.
It is a native desktop-region recording, never a browser preview.
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
from PIL import Image
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / '.artifacts/character-direction'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--soak', type=int, default=600)
    parser.add_argument('--port', type=int, default=9343)
    parser.add_argument('--continuous', action='store_true', help='Keep work evidence fresh through explicit hook fixtures')
    parser.add_argument('--art',type=Path,default=ART)
    args = parser.parse_args()
    globals()['ART']=args.art
    ART.mkdir(parents=True,exist_ok=True)
    data = ART / ('acceptance-' + str(int(time.time())))
    data.mkdir()
    workspace = ART / 'workspace'
    workspace.mkdir(exist_ok=True)
    config = {'settings': {'workspace': str(workspace), 'verify_program': 'powershell.exe',
              'verify_args': ['-NoProfile', '-Command', 'Start-Sleep 9; exit 0'],
              'scale': 2, 'attached': False, 'neko_visible': True, 'dock_visible': False,
              'personality': 'playful', 'transparent': False},
              'placements': {'neko': {'x': 700, 'y': 220, 'width': 600, 'height': 600},
                             'telemetry': {'x': 1320, 'y': 220, 'width': 460, 'height': 650}}}
    (data/'settings.json').write_text(json.dumps(config))
    env = dict(os.environ, NEKOAFK_DATA_DIR=str(data),
               WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS=f'--remote-debugging-port={args.port}')
    app = subprocess.Popen([str(ROOT/'src-tauri/target/release/nekoafk.exe')], env=env)
    video = holder = None
    report = {'fixture_demonstration': True, 'pid': app.pid, 'data_dir': str(data),
              'checks': {}, 'timeline': [], 'screenshots': [], 'errors': []}
    try:
        deadline = time.monotonic()+40
        while True:
            try:
                with urllib.request.urlopen(f'http://127.0.0.1:{args.port}/json/version', timeout=1) as r:
                    version = json.load(r)
                break
            except Exception:
                if time.monotonic()>deadline or app.poll() is not None:
                    raise
                time.sleep(.1)
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(version['webSocketDebuggerUrl'])
            deadline = time.monotonic()+30
            while True:
                pages = [pg for c in browser.contexts for pg in c.pages]
                if all(any('surface='+s in pg.url for pg in pages) for s in ['neko', 'telemetry', 'settings']):
                    break
                if time.monotonic()>deadline:
                    raise AssertionError('Native windows missing')
                if pages: pages[0].wait_for_timeout(100)
                else: browser.new_browser_cdp_session().send('Target.getTargets')
            neko = next(pg for pg in pages if 'surface=neko' in pg.url)
            dock = next(pg for pg in pages if 'surface=telemetry' in pg.url)
            for pg in pages:
                pg.on('pageerror', lambda e: report['errors'].append(str(e)))
                pg.on('console', lambda m: report['errors'].append(m.text) if m.type=='error' else None)
                expect(pg.locator('#app')).to_have_attribute('data-ready', 'true')

            def invoke(cmd, fields=None):
                return dock.evaluate('async ([c,a])=>await window.__TAURI_INTERNALS__.invoke(c,a)', [cmd, fields or {}])

            def emit(scenario):
                subprocess.run(['node', str(ROOT/'tests/emit-fixture.mjs'), str(workspace), scenario],
                               env=env, check=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)

            def state(value):
                for pg in [neko, dock]:
                    expect(pg.locator('#app')).to_have_attribute('data-state', value, timeout=15000)

            def wait(seconds):
                neko.wait_for_timeout(seconds*1000)

            def capture(name):
                neko.screenshot(path=str(ART/(name+'.png')), omit_background=True)
                report['screenshots'].append(name+'.png')

            def observe_for(seconds, capture_name=None, capture_at=3):
                start = time.monotonic()
                captured = False
                while time.monotonic()-start<seconds:
                    report['timeline'].append({'seconds': round(time.monotonic()-movie_start, 3),
                        'state': neko.locator('#app').get_attribute('data-state'),
                        'activity': neko.locator('#mascot').get_attribute('data-activity')})
                    if capture_name and not captured and time.monotonic()-start>=capture_at:
                        capture(capture_name)
                        captured = True
                    wait(.3)

            diag = invoke('desktop_diagnostics')
            report['native_windows'] = diag
            bounds = next(w for w in diag['windows'] if w['label']=='neko')
            log = open(ART/'showcase-capture.log', 'w')
            video = subprocess.Popen(['ffmpeg', '-y', '-f', 'gdigrab', '-framerate', '30', '-draw_mouse', '0',
                '-offset_x', str(bounds['position']['x']), '-offset_y', str(bounds['position']['y']),
                '-video_size', f"{bounds['size']['width']}x{bounds['size']['height']}", '-i', 'desktop',
                '-an', '-c:v', 'libx264', '-preset', 'fast', '-crf', '18', '-pix_fmt', 'yuv420p',
                str(ART/'neko-native-showcase.mp4')], stdin=subprocess.PIPE, stdout=log, stderr=log,
                creationflags=subprocess.CREATE_NO_WINDOW)
            movie_start = time.monotonic()
            emit('busy'); state('active'); observe_for(12.5, 'native-busy', 3.2)
            emit('writing'); state('writing'); observe_for(15, 'native-keyboard', 6)
            emit('permission'); state('permission'); observe_for(8, 'native-beckon', 2.2)
            emit('resolved'); emit('claimed'); state('claimed')
            invoke('run_verification'); state('verifying'); observe_for(7, 'native-inspect', 3.5)
            state('verified'); observe_for(9, 'native-delight', 1.8)
            video.stdin.write(b'q\n'); video.stdin.flush(); video.wait(timeout=30); log.close()
            assert video.returncode==0
            meta = json.loads(subprocess.check_output(['ffprobe', '-v', 'quiet', '-show_format', '-show_streams',
                        '-of', 'json', str(ART/'neko-native-showcase.mp4')]))
            report['video'] = {'file': 'neko-native-showcase.mp4', 'seconds': float(meta['format']['duration']),
                'size': [meta['streams'][0]['width'], meta['streams'][0]['height']],
                'capture': 'Actual Windows-composited companion; opaque capture preference'}
            assert 30<=report['video']['seconds']<=60, report['video']
            (ART/'showcase-timeline.json').write_text(json.dumps(report, indent=2))
            print('SHOWCASE READY '+json.dumps(report['video']), flush=True)

            emit('failure'); state('failed'); wait(2); capture('native-recoil')
            emit('failure'); state('failed'); wait(3); capture('native-huff')
            assert neko.locator('#mascot').get_attribute('data-activity')=='huff'
            emit('rapid'); state('permission'); wait(1)
            emit('editing'); state('permission')
            report['checks']['rapid_events_and_permission_priority'] = 'passed'
            emit('resolved'); state('editing'); emit('claimed'); state('claimed')
            invoke('run_verification'); state('verifying'); invoke('cancel_verification'); state('inconclusive')
            wait(3); capture('native-puzzle')
            assert neko.locator('#mascot').get_attribute('data-activity') in ['puzzle', 'consider', 'rest']
            report['checks']['repeated_failure_and_inconclusive_without_victory'] = 'passed'

            # Interrupt a visible prop performance, rather than only switching
            # state once its final neutral key has already been reached.
            emit('writing'); state('writing'); wait(2.5)
            assert neko.locator('#mascot').get_attribute('data-activity')=='keyboard'
            emit('permission'); state('permission'); wait(.6)
            assert neko.locator('#mascot').get_attribute('data-activity') in ['beckon', 'listen', 'rest']
            assert not neko.locator('#rig').evaluate('e => /NaN|Infinity/.test(e.innerHTML)')
            wait(.5)
            assert float(neko.locator('#props-back').get_attribute('opacity'))==0
            emit('resolved'); state('writing')
            report['checks']['permission_interrupts_held_keyboard_and_retires_prop'] = 'passed'

            prefs = invoke('get_snapshot')['settings']
            prefs['scale'] = 1; prefs['transparent'] = True
            invoke('save_settings', {'settings': prefs})
            holder = subprocess.Popen(['node', str(ROOT/'tests/hold-busy.mjs'), str(workspace), str(args.soak+5),
                                       'refresh' if args.continuous else ''],
                        env=env, creationflags=subprocess.CREATE_NO_WINDOW)
            state('active'); wait(2)
            img = Image.open(io.BytesIO(neko.screenshot(omit_background=True))).convert('RGBA')
            assert img.getpixel((0,0))[3]==0
            img.save(ART/'native-default-transparent.png')
            report['checks']['transparent_pixels'] = 'passed'
            process = psutil.Process(app.pid)

            def usage():
                cpu = rss = private = 0
                processes = [process]+process.children(recursive=True)
                for proc in processes:
                    try:
                        times = proc.cpu_times(); cpu += times.user+times.system
                        mem = proc.memory_full_info(); rss += mem.rss; private += mem.uss
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                return {'cpu': cpu, 'rss': rss, 'private': private, 'processes': len(processes)}

            # Measure actual renderer mutation cadence during an active performance.
            neko.evaluate('''() => {
              window.paintTimes=[]; let prior=0;
              window.paintObserver=new MutationObserver(() => {
                const t=performance.now(); if(t-prior>2){window.paintTimes.push(t);prior=t;}
              });
              window.paintObserver.observe(document.querySelector('#rig'), {subtree:true,attributes:true});
            }''')
            before = usage(); start = time.monotonic(); samples = []; activities = []
            while time.monotonic()-start<args.soak:
                wait(min(5, args.soak-(time.monotonic()-start)))
                activity = neko.locator('#mascot').get_attribute('data-activity')
                factual = neko.locator('#app').get_attribute('data-state')
                if args.continuous:
                    assert factual=='active', factual
                if not activities or activities[-1]['activity']!=activity or activities[-1]['state']!=factual:
                    activities.append({'seconds': round(time.monotonic()-start, 1), 'activity': activity, 'state': factual})
                samples.append(usage())
                if len(samples)==2:
                    times = neko.evaluate('() => {window.paintObserver.disconnect();return window.paintTimes}')
                    intervals = sorted(b-a for a,b in zip(times,times[1:]) if b-a<100)
                    report['frame_pacing'] = {'sample_seconds': 10, 'mutations': len(times),
                        'median_ms': round(intervals[len(intervals)//2], 2),
                        'p95_ms': round(intervals[int(len(intervals)*.95)], 2),
                        'note': 'DOM mutation cadence during active motion; not a GPU frame-time measurement'}
                if len(samples)%12==0:
                    print('SOAK '+str(round(time.monotonic()-start))+'s '+json.dumps(activities[-3:]), flush=True)
            after = usage(); duration = time.monotonic()-start
            report['resources'] = {'seconds': round(duration, 2), 'scale': 1, 'transparent': True,
                'cpu_percent_one_core': round((after['cpu']-before['cpu'])/duration*100, 2),
                'rss_start_mib': round(before['rss']/1048576, 1), 'rss_end_mib': round(after['rss']/1048576, 1),
                'private_start_mib': round(before['private']/1048576, 1),
                'private_end_mib': round(after['private']/1048576, 1),
                'private_peak_mib': round(max(before['private'],max(s['private'] for s in samples))/1048576, 1),
                'process_count': after['processes'], 'activities': activities}
            assert len({a['activity'] for a in activities})>=3
            report['checks']['native_continuing_work_soak' if args.continuous else 'native_session_with_activity_expiry'] = 'passed'
            holder.wait(timeout=20); state('disconnected'); emit('busy'); state('active')
            report['checks']['disconnect_and_recovery'] = 'passed'
            prefs['reduced_motion'] = True; invoke('save_settings', {'settings': prefs})
            expect(neko.locator('#app')).to_have_attribute('data-motion', 'reduced')
            frozen = neko.locator('#rig').inner_html(); wait(2)
            assert frozen==neko.locator('#rig').inner_html()
            reduced_before = usage(); reduced_start = time.monotonic(); wait(10); reduced_after = usage()
            report['resources']['reduced_motion_cpu_percent_one_core'] = round(
                (reduced_after['cpu']-reduced_before['cpu'])/(time.monotonic()-reduced_start)*100, 2)
            emit('permission'); state('permission'); wait(.3)
            assert frozen!=neko.locator('#rig').inner_html()
            emit('resolved'); prefs['reduced_motion'] = False; invoke('save_settings', {'settings': prefs})
            neko.emulate_media(reduced_motion='reduce')
            expect(neko.locator('#app')).to_have_attribute('data-motion', 'reduced')
            frozen = neko.locator('#rig').inner_html(); wait(2)
            assert frozen==neko.locator('#rig').inner_html()
            neko.emulate_media(reduced_motion='no-preference')
            expect(neko.locator('#app')).to_have_attribute('data-motion', 'full')
            report['checks']['user_and_system_reduced_motion'] = 'passed'
            report['reduced_motion_method'] = 'Saved app preference and CDP-emulated WebView prefers-reduced-motion media query; physical Windows setting acceptance remains untested.'
            invoke('window_action', {'action': 'hide-neko'})
            expect(neko.locator('#app')).to_have_attribute('data-motion', 'paused')
            invoke('window_action', {'action': 'recover'})
            expect(neko.locator('#app')).to_have_attribute('data-motion', 'full')
            report['checks']['hide_and_resume'] = 'passed'
            for mode in ['calm', 'chaos', 'playful']:
                prefs['personality'] = mode; invoke('save_settings', {'settings': prefs})
                assert invoke('get_snapshot')['settings']['personality']==mode
            report['checks']['personality_persistence'] = 'passed'
            for mode in ['cat', 'robot']:
                prefs['character'] = mode; invoke('save_settings', {'settings': prefs})
                assert invoke('get_snapshot')['settings']['character']==mode
                expect(neko.locator('#mascot svg')).to_have_attribute('data-character', mode)
            report['checks']['character_persistence'] = 'passed'
            for pg in pages:
                assert pg.evaluate('document.documentElement.scrollWidth<=innerWidth')
            assert not report['errors'], report['errors']
            report['checks']['runtime_errors_and_overflow'] = 'passed'
            print(json.dumps(report, indent=2), flush=True)
            invoke('quit_app'); browser.close()
    finally:
        (ART/'native-acceptance.json').write_text(json.dumps(report, indent=2))
        for child in [video, holder, app]:
            if child and child.poll() is None:
                child.terminate(); child.wait(timeout=15)


if __name__=='__main__':
    main()
