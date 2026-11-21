"""Exercise the actual Windows WebView2 app through its local CDP endpoint.

Use an isolated NEKOAFK_DATA_DIR. Fixture scenarios are explicitly test-only.
The separate OpenCode smoke test establishes the live supported hook contract.
"""
import argparse
import ctypes
import io
import json
import os
import pathlib
import subprocess
import time
import urllib.request
from playwright.sync_api import sync_playwright, expect
from PIL import Image, ImageChops

ROOT = pathlib.Path(__file__).resolve().parents[1]
ART = ROOT / '.artifacts' / 'native-validation'
ART.mkdir(parents=True, exist_ok=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--exe', default=str(ROOT / 'src-tauri/target/release/nekoafk.exe'))
    parser.add_argument('--port', type=int, default=9333)
    args = parser.parse_args()
    data = ART / ('data-' + str(int(time.time())))
    workspace = ART / ('workspace-' + str(int(time.time())))
    workspace.mkdir()
    (workspace / 'source.txt').write_text('original', encoding='utf-8')
    env = dict(os.environ, NEKOAFK_DATA_DIR=str(data), WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS=f'--remote-debugging-port={args.port}')
    proc = subprocess.Popen([args.exe], env=env)
    errors = []
    results = {}
    try:
        deadline = time.time() + 40
        while True:
            try:
                with urllib.request.urlopen(f'http://127.0.0.1:{args.port}/json/version', timeout=1) as response:
                    version = json.load(response)
                break
            except Exception:
                if proc.poll() is not None or time.time() > deadline:
                    raise RuntimeError('Native app did not expose test CDP endpoint')
                time.sleep(.25)
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(version['webSocketDebuggerUrl'])
            deadline = time.time()+30
            while True:
                pages = [pg for context in browser.contexts for pg in context.pages]
                if all(any('surface='+name in pg.url for pg in pages) for name in ['settings','neko','telemetry']): break
                if time.time()>deadline: raise AssertionError('Native webviews did not finish creation')
                if pages: pages[0].wait_for_timeout(50)
                else: time.sleep(.05)
            settings = next(pg for pg in pages if 'surface=settings' in pg.url)
            dock = next(pg for pg in pages if 'surface=telemetry' in pg.url)
            neko = next(pg for pg in pages if 'surface=neko' in pg.url)
            for pg in pages:
                pg.on('pageerror', lambda e: errors.append(str(e)))
                pg.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
                pg.wait_for_load_state('networkidle')
                expect(pg.locator('#app')).to_have_attribute('data-ready','true')
                assert pg.locator('#app').get_attribute('data-startup-error') is None, 'First IPC raced host registration'
                expect(pg.locator('#errorBox')).to_be_hidden()
            def invoke(command, args=None):
                return settings.evaluate('async ([command,args]) => await window.__TAURI_INTERNALS__.invoke(command,args)', [command,args or {}])
            def wait_state(state):
                expect(dock.locator('#state')).to_have_text(state,timeout=15000)
            def emit(scenario):
                subprocess.run(['node',str(ROOT/'tests/emit-fixture.mjs'),str(workspace),scenario],env=env,check=True,capture_output=True)
            def eventually(check, timeout=10):
                deadline = time.time()+timeout
                while not check():
                    if time.time()>deadline: raise AssertionError('Native condition did not become true')
                    time.sleep(.1)
            expect(dock.locator('#tasks')).to_have_text('Unknown')
            expect(dock.locator('#state')).to_have_text('Bridge offline')
            initial = invoke('desktop_diagnostics')
            assert initial['tray_available']
            assert next(w for w in initial['windows'] if w['label']=='neko')['visible']
            assert not next(w for w in initial['windows'] if w['label']=='settings')['visible']
            assert not next(w for w in initial['windows'] if w['label']=='telemetry')['visible']
            results['cold_start_state_registration_and_companion_default'] = 'passed'
            invoke('window_action',{'action':'settings'})
            invoke('window_action',{'action':'recover'})
            # Read-only Win32 inspection verifies the real OS stacking order;
            # issuing an unchanged pin setter can raise a dock over Settings.
            user32=ctypes.windll.user32
            user32.GetTopWindow.argtypes=[ctypes.c_void_p]
            user32.GetTopWindow.restype=ctypes.c_void_p
            user32.GetWindow.argtypes=[ctypes.c_void_p,ctypes.c_uint]
            user32.GetWindow.restype=ctypes.c_void_p
            def settings_unobstructed():
                handles={w['label']:w['native_handle'] for w in invoke('desktop_diagnostics')['windows']}
                order=[]; handle=user32.GetTopWindow(None)
                while handle and len(order)<1000:
                    order.append(handle); handle=user32.GetWindow(handle,2)
                return all(handles[label] in order for label in handles) and all(order.index(handles['settings'])<order.index(handles[label]) for label in ['neko','telemetry'])
            invoke('window_action',{'action':'settings'})
            eventually(settings_unobstructed)
            # Reopening the focused window must not reorder the companion above it.
            invoke('window_action',{'action':'settings'})
            eventually(settings_unobstructed)
            for _ in range(3):
                dock.get_by_role('button',name='Settings',exact=True).click()
                settings.get_by_role('button',name='Agent connections',exact=True).click()
                eventually(settings_unobstructed)
                for _ in range(5):
                    time.sleep(.1)
                    assert settings_unobstructed(), 'Queued pin updates must not cover Settings after opening from the dock'
            results['settings_native_stacking_order'] = 'passed'
            for _ in range(5): invoke('window_action',{'action':'scale-down'})
            neko.get_by_role('button',name='Companion controls',exact=True).click()
            expect(neko.locator('#companionTools button:visible')).to_have_count(8)
            for button in neko.locator('#companionTools button:visible').all():
                # At minimum scale the complete menu scrolls. Previously six
                # actions were display:none and escaped this visibility check.
                button.scroll_into_view_if_needed()
                expect(button).to_be_in_viewport()
            neko.screenshot(path=str(ART/'cat-minimum-native.png'),omit_background=True)
            neko.keyboard.press('Escape')
            settings.get_by_role('button',name='Agent connections',exact=True).click()
            eventually(settings_unobstructed)
            assert all(not w['always_on_top'] for w in invoke('desktop_diagnostics')['windows'] if w['label']!='settings'), 'Child or companion focus must not repin windows over open Settings'
            for _ in range(5): invoke('window_action',{'action':'scale-up'})
            for w in initial['windows']:
                if w['label'] != 'settings':
                    assert w['decorated'] is False and w['always_on_top'] is True and w['resizable'] is (w['label'] != 'hud')
            results['native_windows_and_tray'] = initial
            # OS drag/resize and tray interactions are checked separately with
            # Windows Computer Use. These assertions exercise real native IPC.
            def section(name):
                invoke('window_action',{'action':'settings'})
                settings.get_by_role('button',name=name,exact=True).click()
            def save():
                settings.get_by_role('button',name='Save settings',exact=True).click()
                expect(settings.locator('#saved')).to_have_text('Settings saved locally')
                eventually(settings_unobstructed)
            settings.get_by_label('Workspace folder').fill(str(workspace))
            section('Verification')
            settings.get_by_label('Executable', exact=True).fill('powershell.exe')
            settings.get_by_label('Arguments (JSON array)').fill('["-NoProfile","-Command","exit 0"]')
            settings.get_by_role('button',name='Save settings',exact=True).click()
            expect(settings.locator('#saved')).to_have_text('Settings saved locally')
            section('Agent connections')
            settings.get_by_role('button',name='Install local bridge',exact=True).click()
            expect(settings.locator('#installStatus')).to_contain_text('Bridge installed')
            assert (workspace/'.opencode/plugins/nekoafk.js').is_file()
            emit('editing'); wait_state('Editing files')
            first_frame = Image.open(io.BytesIO(neko.screenshot(omit_background=True))).convert('RGBA')
            assert first_frame.getbbox() is not None
            neko.wait_for_timeout(300)  # Sample a known animation interval.
            next_frame = Image.open(io.BytesIO(neko.screenshot(omit_background=True))).convert('RGBA')
            assert ImageChops.difference(first_frame,next_frame).getbbox() is not None, 'Cat must visibly animate'
            assert first_frame.getpixel((0,0))[3] == 0, 'Companion corners should remain transparent'
            emit('tasks'); expect(dock.locator('#tasks')).to_have_text('1 / 2')
            emit('testing'); wait_state('Running tests')
            emit('failure'); wait_state('Needs attention')
            emit('permission'); wait_state('Permission needed')
            emit('resolved')
            emit('claimed'); wait_state('Completion unverified')
            dock.get_by_role('button',name='Verify locally',exact=True).click()
            expect(dock.locator('#verification')).to_contain_text('Configured check passed')
            wait_state('Completion unverified')
            emit('tasks-complete'); expect(dock.locator('#tasks')).to_have_text('2 / 2')
            dock.get_by_role('button',name='Verify locally',exact=True).click()
            wait_state('Locally verified')
            results['evidence_and_independent_verification'] = 'passed'
            dock.screenshot(path=str(ART/'telemetry-verified.png'))
            neko.screenshot(path=str(ART/'cat-verified.png'), omit_background=True)
            # A fresh edit invalidates verified state. A real nonzero local check
            # must never produce celebration.
            emit('editing'); wait_state('Editing files')
            section('Verification')
            settings.get_by_label('Arguments (JSON array)').fill('["-NoProfile","-Command","exit 9"]')
            settings.get_by_role('button',name='Save settings',exact=True).click()
            expect(settings.locator('#saved')).to_have_text('Settings saved locally')
            emit('claimed'); wait_state('Completion unverified')
            dock.get_by_role('button',name='Verify locally',exact=True).click()
            wait_state('Needs attention')
            expect(dock.locator('#verification')).to_contain_text('did not pass')
            settings.get_by_label('Arguments (JSON array)').fill('["-NoProfile","-Command","Start-Sleep 20"]')
            settings.get_by_role('button',name='Save settings',exact=True).click()
            expect(settings.locator('#saved')).to_have_text('Settings saved locally')
            dock.get_by_role('button',name='Verify locally',exact=True).click()
            expect(dock.get_by_role('button',name='Cancel',exact=True)).to_be_visible()
            dock.get_by_role('button',name='Cancel',exact=True).click()
            expect(dock.locator('#verification')).to_contain_text('cancelled or evidence changed')
            expect(dock.locator('#activity')).to_contain_text('cancelled')
            results['failed_and_cancelled_verification'] = 'passed'
            section('Desktop behavior')
            settings.get_by_label('Always on top',exact=True).uncheck()
            settings.get_by_label('Pin telemetry dock',exact=True).uncheck()
            save()
            settings.get_by_label('Click-through companion',exact=True).check()
            save()
            assert invoke('get_snapshot')['settings']['click_through'] is True
            invoke('window_action',{'action':'recover'})
            assert invoke('get_snapshot')['settings']['click_through'] is False
            section('Appearance')
            settings.get_by_label('Transparent companion background').uncheck()
            settings.get_by_label('Companion scale').evaluate("e => { e.value = '150'; e.dispatchEvent(new Event('input',{bubbles:true})); }")
            section('Character')
            settings.get_by_label('Reduce companion motion').check()
            settings.get_by_role('button',name='Save settings',exact=True).click()
            expect(settings.locator('#saved')).to_have_text('Settings saved locally')
            expect(neko.locator('#app')).to_have_attribute('data-motion','reduced')
            assert neko.locator('#head').evaluate('e => getComputedStyle(e).animationName') == 'none'
            diag = invoke('desktop_diagnostics')
            assert all(not w['always_on_top'] for w in diag['windows'] if w['label']!='settings')
            cat_window = next(w for w in diag['windows'] if w['label']=='neko')
            assert abs(cat_window['size']['width']/cat_window['scale_factor']-360)<3
            invoke('window_action',{'action':'hide-neko'})
            assert next(w for w in invoke('desktop_diagnostics')['windows'] if w['label']=='neko')['visible'] is False
            invoke('window_action',{'action':'recover'})
            assert next(w for w in invoke('desktop_diagnostics')['windows'] if w['label']=='neko')['visible'] is True
            invoke('window_action',{'action':'toggle-attach'})
            assert invoke('get_snapshot')['settings']['attached'] is False
            invoke('window_action',{'action':'toggle-attach'})
            dock.get_by_role('button',name='Collapse dock',exact=True).click()
            expect(dock.locator('#app')).to_have_attribute('data-collapsed','true')
            eventually(lambda: next(w for w in invoke('desktop_diagnostics')['windows'] if w['label']=='telemetry')['inner_size']['height'] < 200)
            dock.get_by_role('button',name='Expand dock',exact=True).click()
            expect(dock.locator('#app')).to_have_attribute('data-collapsed','false')
            results['visibility_attachment_scaling_topmost'] = 'passed'
            # Form errors preserve input and do not reset settings.
            section('Verification')
            settings.get_by_label('Arguments (JSON array)').fill('not json')
            settings.get_by_role('button',name='Save settings',exact=True).click()
            expect(settings.locator('#error')).to_contain_text('JSON array')
            expect(settings.get_by_label('Arguments (JSON array)')).to_have_value('not json')
            settings.get_by_label('Arguments (JSON array)').fill('["-NoProfile","-Command","exit 0"]')
            settings.get_by_role('button',name='Save settings',exact=True).click()
            expect(settings.locator('#saved')).to_have_text('Settings saved locally')
            # Inspect rendered native surfaces, and run local axe without CDN.
            for name, pg in [('settings',settings),('telemetry',dock),('cat',neko)]:
                pg.evaluate((ROOT/'node_modules/axe-core/axe.min.js').read_text(encoding='utf-8'))
                audit = pg.evaluate('async () => (await axe.run()).violations.map(v=>({id:v.id,impact:v.impact,nodes:v.nodes.length}))')
                assert not audit, (name,audit)
                pg.evaluate('window.scrollTo(0,0)')
                if name == 'telemetry': pg.locator('main').evaluate('e => e.scrollTop=0')
                pg.screenshot(path=str(ART/f'{name}-native.png'), animations='disabled')
                assert pg.evaluate('document.documentElement.scrollWidth <= innerWidth'), name
            results['axe_native_surfaces'] = 'passed'
            for title in ['Agent connections','Verification','Appearance','Character','Desktop behavior']:
                section(title)
                assert settings.evaluate('document.documentElement.scrollWidth <= innerWidth')
                expect(settings.locator('#save')).to_be_in_viewport()
                settings.screenshot(path=str(ART/f'settings-{title.split()[0].lower()}-native.png'),animations='disabled')
                settings.evaluate((ROOT/'node_modules/axe-core/axe.min.js').read_text(encoding='utf-8'))
                audit=settings.evaluate('async () => (await axe.run()).violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>n.target)}))')
                assert not audit,(title,audit)
            for pg in [settings,dock,neko]:
                for _ in range(12):
                    pg.keyboard.press('Tab')
                    visible = pg.evaluate("() => { const e = document.activeElement; return e===document.body || getComputedStyle(e).outlineStyle!=='none'; }")
                    assert visible, 'Keyboard focus must remain visible'
            results['keyboard_minimum_window_animation_transparency'] = 'passed'
            settings.keyboard.press('Tab')
            focus = settings.evaluate('getComputedStyle(document.activeElement).outlineStyle')
            assert focus != 'none'
            assert not errors, errors
            invoke('window_action',{'action':'hide-dock'})
            saved = json.loads((data/'settings.json').read_text())
            assert saved['settings']['scale'] == 1.5
            assert saved['settings']['transparent'] is False
            results['settings_persistence_file'] = 'passed'
            results['console_errors'] = errors
            (ART/'report.json').write_text(json.dumps(results,indent=2))
            # All helper processes are stopped before ending the test.
            invoke('quit_app')
            browser.close()
        proc.wait(timeout=15)
        # Relaunch the same native binary and inspect settings loaded from disk.
        proc = subprocess.Popen([args.exe], env=env)
        time.sleep(3)
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(f'http://127.0.0.1:{args.port}')
            pages = [pg for c in browser.contexts for pg in c.pages]
            pg = next(pg for pg in pages if 'surface=telemetry' in pg.url)
            loaded = pg.evaluate('async () => await window.__TAURI_INTERNALS__.invoke("get_snapshot")')
            assert loaded['settings']['scale'] == 1.5 and loaded['settings']['transparent'] is False
            assert not loaded['engine']['sessions'], 'Session history must not pretend to remain live after restart'
            restored_config=json.loads((data/'settings.json').read_text())
            assert restored_config['placements']['telemetry']==saved['placements']['telemetry'], 'Hidden startup geometry must not replace the last visible dock geometry'
            pg.evaluate('async () => await window.__TAURI_INTERNALS__.invoke("window_action",{action:"recover"})')
            geometry=pg.evaluate('async () => await window.__TAURI_INTERNALS__.invoke("desktop_diagnostics")')
            for window in geometry['windows']:
                placement=saved['placements'].get(window['label'])
                if placement:
                    for dimension in ['width','height']:
                        assert abs(window['inner_size'][dimension]-placement[dimension])<=2,(window,placement)
            results['native_restart_geometry_no_frame_growth']='passed'
            assert pg.locator('#app').get_attribute('data-startup-error') is None
            pg.evaluate('async () => await window.__TAURI_INTERNALS__.invoke("quit_app")')
            browser.close()
        proc.wait(timeout=15)
        results['native_restart_persistence'] = 'passed'
        (ART/'report.json').write_text(json.dumps(results,indent=2))
        print(json.dumps(results,indent=2))
    finally:
        if proc.poll() is None:
            proc.terminate()
            proc.wait(timeout=15)

if __name__ == '__main__':
    main()
