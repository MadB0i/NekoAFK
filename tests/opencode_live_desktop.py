"""A real OpenCode process -> local plugin -> Rust host -> native dock check.

No fixture events and no model requests are used in this integration test.
Run scripts/opencode-smoke.mjs first to prepare the isolated OpenCode sandbox.
"""
import json
import os
import pathlib
import shutil
import subprocess
import time
import urllib.request
import argparse
from concurrent.futures import ThreadPoolExecutor
from playwright.sync_api import sync_playwright, expect

ROOT = pathlib.Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--extended',action='store_true');args=parser.parse_args()
REPORT = json.loads((ROOT/'.artifacts/opencode-live-report.json').read_text())
WORKSPACE = pathlib.Path(REPORT['workspace'])
BASE = WORKSPACE.parent
DATA = BASE / ('desktop-data-' + str(int(time.time())))
PORT = 14597
env = dict(os.environ, NEKOAFK_DATA_DIR=str(DATA), OPENCODE_CONFIG_DIR=str(BASE/'config'),
           XDG_CONFIG_HOME=str(BASE/'config-home'), XDG_DATA_HOME=str(BASE/'appdata'),
           XDG_STATE_HOME=str(BASE/'state'), XDG_CACHE_HOME=str(BASE/'cache'),
           OPENCODE_DISABLE_DEFAULT_PLUGINS='true', OPENCODE_DISABLE_MODELS_FETCH='true',
           OPENCODE_DISABLE_AUTOUPDATE='true')
shutil.copyfile(ROOT/'integrations/opencode/nekoafk.js',WORKSPACE/'.opencode/plugins/nekoafk.js')
log = open(BASE/'desktop-server.log','w',encoding='utf-8')
server = subprocess.Popen([str(ROOT/'.artifacts/opencode/node_modules/opencode-windows-x64/bin/opencode.exe'),
                          'serve','--hostname','127.0.0.1','--port',str(PORT)],cwd=WORKSPACE,env=env,
                          stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)
app = None
def request(route, body=None, method=None):
    req = urllib.request.Request(f'http://127.0.0.1:{PORT}{route}',data=json.dumps(body).encode() if body is not None else None,
                                 headers={'content-type':'application/json','x-opencode-directory':str(WORKSPACE)},method=method)
    with urllib.request.urlopen(req,timeout=120) as r: return json.load(r)
try:
    deadline = time.time()+40
    while True:
        try: health = request('/global/health'); break
        except Exception:
            if time.time()>deadline or server.poll() is not None: raise
            time.sleep(.25)
    app_env = dict(env,WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS='--remote-debugging-port=9334')
    app = subprocess.Popen([str(ROOT/'src-tauri/target/release/nekoafk.exe')],env=app_env)
    deadline = time.time()+30
    while True:
        try:
            with urllib.request.urlopen('http://127.0.0.1:9334/json/version',timeout=1) as r: version=json.load(r)
            break
        except Exception:
            if time.time()>deadline: raise
            time.sleep(.25)
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(version['webSocketDebuggerUrl'])
        deadline=time.time()+30
        while True:
            pages = [pg for c in browser.contexts for pg in c.pages]
            if all(any('surface='+name in pg.url for pg in pages) for name in ['hud','neko','telemetry','settings']): break
            if time.time()>deadline: raise AssertionError('Native dock did not finish creation')
            if pages: pages[0].wait_for_timeout(50)
            else: time.sleep(.05)
        dock = next(pg for pg in pages if 'surface=telemetry' in pg.url)
        neko = next(pg for pg in pages if 'surface=neko' in pg.url)
        dock.wait_for_load_state('networkidle')
        dock.evaluate('async () => await window.__TAURI_INTERNALS__.invoke("window_action",{action:"recover"})')
        session = request('/session',{'title':'NekoAFK actual OpenCode integration check'})
        hud = next(pg for pg in pages if 'surface=hud' in pg.url)
        assert request(f"/session/{session['id']}/todo")==[], 'Genuine new session has no plan'
        expect(hud.locator('#planTrack')).to_be_hidden()
        expect(dock.locator('#bridgeLabel')).to_have_text('Connected',timeout=15000)
        with ThreadPoolExecutor(max_workers=1) as worker:
            started=time.monotonic()
            pending=worker.submit(request,f"/session/{session['id']}/shell",{'agent':'build','command':f'echo NEKOAFK_REAL_AGENT_EVENT; sleep {70 if args.extended else 4}'})
            expect(dock.locator('#app')).to_have_attribute('data-state','active',timeout=15000)
            expect(neko.locator('#app')).to_have_attribute('data-state','active',timeout=15000)
            expect(hud.locator('#hudActivity')).to_have_text('Shell running')
            hud.screenshot(path=str(ROOT/'.artifacts/live-progress/real-opencode-running.png'),omit_background=True)
            neko.wait_for_timeout(800) # Observe entry into the real busy performance.
            assert neko.locator('#mascot').get_attribute('data-activity') in ['mote','listen','consider','wash','rest']
            neko.screenshot(path=str(ROOT/'.artifacts/native-validation/opencode-real-busy-cat.png'),omit_background=True)
            if args.extended:
                dock.evaluate('async()=>await window.__TAURI_INTERNALS__.invoke("quit_app")');browser.close();app.wait(timeout=15)
                app=subprocess.Popen([str(ROOT/'src-tauri/target/release/nekoafk.exe')],env=app_env)
                time.sleep(3);browser=p.chromium.connect_over_cdp('http://127.0.0.1:9334')
                deadline=time.monotonic()+20
                while True:
                    pages=[pg for c in browser.contexts for pg in c.pages]
                    if all(any('surface='+name in pg.url for pg in pages) for name in ['hud','neko','telemetry','settings']):break
                    if time.monotonic()>deadline:raise AssertionError('Restarted native dock missing')
                    if pages:pages[0].wait_for_timeout(100)
                    else:browser.new_browser_cdp_session().send('Target.getTargets')
                dock=next(pg for pg in pages if 'surface=telemetry' in pg.url);neko=next(pg for pg in pages if 'surface=neko' in pg.url)
                expect(dock.locator('#app')).to_have_attribute('data-state','active',timeout=20000)
                dock.evaluate('async()=>await window.__TAURI_INTERNALS__.invoke("window_action",{action:"recover"})')
                while time.monotonic()-started<65:dock.wait_for_timeout(500)
                resumed=dock.evaluate('async()=>await window.__TAURI_INTERNALS__.invoke("get_snapshot")')
                assert resumed['selected_state']=='active' and next(iter(resumed['engine']['sessions'].values()))['operations']
            shell=pending.result(timeout=30)
        snapshot = None
        deadline = time.time()+15
        while time.time()<deadline:
            snapshot = dock.evaluate('async () => await window.__TAURI_INTERNALS__.invoke("get_snapshot")')
            actual = next((s for s in snapshot['engine']['sessions'].values() if s['id']==session['id']),None)
            if actual and any('Tool finished' in a['text'] for a in actual['activity']): break
            time.sleep(.25)
        else: raise AssertionError('Actual OpenCode shell evidence did not reach the native dock')
        assert actual['workspace'] == str(WORKSPACE)
        assert actual['claimed'] is False and actual['verification']=='not_run'
        expect(dock.locator('#tasks')).to_have_text('Unknown')
        assert snapshot['selected_state'] != 'verified'
        hud=next(pg for c in browser.contexts for pg in c.pages if 'surface=hud' in pg.url)
        expect(hud.locator('#progressDetail')).to_contain_text('Exit unknown')
        assert snapshot['progress']['plan'] is None
        hud.screenshot(path=str(ROOT/'.artifacts/live-progress/real-opencode-unknown.png'),omit_background=True)
        dock.locator('main').evaluate('e => e.scrollTop=0')
        dock.screenshot(path=str(ROOT/'.artifacts/native-validation/opencode-real-native.png'))
        report = {'opencode_version':health['version'],'real_session_id':session['id'],
                  'native_busy_state_and_performance':'passed','hud_genuine_tool_and_unknown_exit':'passed','genuine_empty_todo_response':'passed',
                  'native_state':snapshot['selected_state'],'activity':actual['activity'],
                  'model_requests':0,'transport':'supported OpenCode events -> atomic local queue -> Rust -> native WebView2'}
        other = request('/session',{'title':'NekoAFK actual session isolation check'})
        assert request(f"/session/{other['id']}/todo")==[]
        request(f"/session/{other['id']}/shell",{'agent':'build','command':'echo NEKOAFK_SECOND_SESSION'})
        deadline=time.monotonic()+15
        while True:
            sessions=dock.evaluate('async()=> (await window.__TAURI_INTERNALS__.invoke("get_snapshot")).engine.sessions')
            other_key=next((k for k,s in sessions.items() if s['id']==other['id'] and s['outcome']=='unknown'),None)
            if other_key:break
            assert time.monotonic()<deadline
            dock.wait_for_timeout(100)
        dock.evaluate('async key=>await window.__TAURI_INTERNALS__.invoke("select_session",{key})',other_key)
        expect(hud.locator('#progressDetail')).to_contain_text('Exit unknown')
        chosen=dock.evaluate('async()=>await window.__TAURI_INTERNALS__.invoke("get_snapshot")')
        assert chosen['progress']['session_key']==other_key and chosen['progress']['plan'] is None
        dock.evaluate('async key=>await window.__TAURI_INTERNALS__.invoke("select_session",{key})',actual['key'])
        report['genuine_session_switch_isolation']='passed'
        if args.extended:
            report['restart_during_real_70_second_tool']='passed'
            report['long_running_tool_does_not_age_into_inactive']='passed'
            nonzero=request(f"/session/{session['id']}/shell",{'agent':'build','command':'exit 7'})
            numeric=any(isinstance(part.get('state',{}).get('metadata',{}).get('exit'),int) for part in nonzero.get('parts',[]))
            if numeric:expect(dock.locator('#app')).to_have_attribute('data-state','failed',timeout=15000)
            else:expect(dock.locator('#activity')).to_contain_text('exit code unavailable',timeout=15000)
            dock.wait_for_timeout(16000)
            failed=dock.evaluate('async()=>await window.__TAURI_INTERNALS__.invoke("get_snapshot")')
            assert failed['engine']['sessions'][actual['key']]['failures']==(1 if numeric else 0)
            report['real_shell_exit_signal']='numeric nonzero observed once' if numeric else 'OpenCode 1.18.35 shell endpoint omits exit code, even for exit 7; shown as unknown, never passed'
            server.terminate();server.wait(timeout=15)
            expect(dock.locator('#app')).to_have_attribute('data-state','disconnected',timeout=50000)
            report['real_server_disconnect']='passed'
            server=subprocess.Popen([str(ROOT/'.artifacts/opencode/node_modules/opencode-windows-x64/bin/opencode.exe'),'serve','--hostname','127.0.0.1','--port',str(PORT)],cwd=WORKSPACE,env=env,stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)
            deadline=time.monotonic()+40
            while True:
                try:request('/global/health');break
                except Exception:
                    if time.monotonic()>deadline:raise
                    time.sleep(.25)
            request(f"/session/{session['id']}/shell",{'agent':'build','command':'echo NEKOAFK_RECOVERED'})
            expect(dock.locator('#app')).to_have_attribute('data-state',__import__('re').compile('active|idle'),timeout=15000)
            report['real_server_reconnect_and_new_tool']='passed'
            request(f"/session/{session['id']}",method='DELETE')
            expect(dock.locator('#app')).to_have_attribute('data-state','closed',timeout=15000)
            report['real_session_deletion']='passed'
            (ROOT/'.artifacts/engineering/opencode-recovery.json').write_text(json.dumps(report,indent=2))
        (ROOT/'.artifacts/opencode-desktop-report.json').write_text(json.dumps(report,indent=2))
        print(json.dumps(report,indent=2))
        dock.evaluate('async () => await window.__TAURI_INTERNALS__.invoke("quit_app")')
        browser.close()
    app.wait(timeout=15)
finally:
    if app and app.poll() is None: app.terminate(); app.wait(timeout=15)
    if server.poll() is None: server.terminate(); server.wait(timeout=15)
    log.close()
