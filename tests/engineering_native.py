"""Native fullscreen/quiet-hold checks; optionally leave app for physical input QA."""
import argparse,json,os,subprocess,time,urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright,expect

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'.artifacts/engineering'

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--keep-open',action='store_true');parser.add_argument('--exe',default=str(ROOT/'src-tauri/target/release/nekoafk.exe'));args=parser.parse_args()
 data=ART/('desktop-data-'+str(int(time.time())));data.mkdir(parents=True)
 workspace=ART/'desktop-workspace';workspace.mkdir(exist_ok=True)
 (data/'settings.json').write_text(json.dumps({'settings':{'workspace':str(workspace),'attached':True,'dock_visible':True,'scale':1,'transparent':True},'placements':{'neko':{'x':1000,'y':300,'width':300,'height':300},'telemetry':{'x':500,'y':200,'width':460,'height':650}}}))
 env=dict(os.environ,NEKOAFK_DATA_DIR=str(data),WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS='--remote-debugging-port=9356')
 app=subprocess.Popen([args.exe],env=env);fixture=None;success=False
 report={'pid':app.pid,'data_dir':str(data),'checks':{}}
 try:
  deadline=time.monotonic()+40
  while True:
   try:version=json.load(urllib.request.urlopen('http://127.0.0.1:9356/json/version',timeout=1));break
   except Exception:
    if time.monotonic()>deadline:raise
    time.sleep(.1)
  with sync_playwright() as p:
   browser=p.chromium.connect_over_cdp(version['webSocketDebuggerUrl'])
   deadline=time.monotonic()+30
   while True:
    pages=[pg for c in browser.contexts for pg in c.pages]
    if all(any('surface='+s in pg.url for pg in pages) for s in ['neko','telemetry','settings']):break
    if time.monotonic()>deadline:raise RuntimeError('Missing native surfaces')
    if pages:pages[0].wait_for_timeout(100)
    else:browser.new_browser_cdp_session().send('Target.getTargets')
   cat=next(pg for pg in pages if 'surface=neko' in pg.url);dock=next(pg for pg in pages if 'surface=telemetry' in pg.url)
   expect(cat.locator('#app')).to_have_attribute('data-ready','true')
   def invoke(c,a=None):return dock.evaluate('async([c,a])=>await window.__TAURI_INTERNALS__.invoke(c,a)',[c,a or {}])
   report['initial_geometry']=invoke('desktop_diagnostics')
   # A real borderless native HWND, not browser fullscreen/viewport emulation.
   code="import tkinter as t;r=t.Tk();r.title('NekoAFK fullscreen acceptance');r.configure(bg='#24212d');r.attributes('-fullscreen',True);r.after(200,r.focus_force);r.mainloop()"
   fixture=subprocess.Popen(['python','-c',code],creationflags=subprocess.CREATE_NO_WINDOW)
   expect(cat.locator('#app')).to_have_attribute('data-motion','paused',timeout=15000)
   paused=invoke('get_snapshot');assert paused['desktop_paused'] and paused['selected_state']=='disconnected'
   diag=invoke('desktop_diagnostics');assert all(not w['always_on_top'] for w in diag['windows'] if w['label']!='settings')
   assert not next(w for w in diag['windows'] if w['label']=='hud')['visible']
   report['checks']['real_native_fullscreen_yields_pins_and_pauses_without_changing_agent_state']='passed'
   fixture.terminate();fixture.wait(timeout=10);fixture=None
   # Establish a known non-fullscreen foreground; the user's previously focused
   # application may itself cover the monitor when the fixture closes.
   invoke('window_action',{'action':'show-dock'})
   expect(cat.locator('#app')).to_have_attribute('data-motion','full',timeout=15000)
   deadline=time.monotonic()+10
   while not all(w['always_on_top'] for w in invoke('desktop_diagnostics')['windows'] if w['label']!='settings'):
    if time.monotonic()>deadline:raise AssertionError('Pins not restored')
    cat.wait_for_timeout(100)
   report['checks']['fullscreen_exit_restores_motion_and_pins']='passed'
   assert next(w for w in invoke('desktop_diagnostics')['windows'] if w['label']=='hud')['visible']
   cat.locator('#menuToggle').focus();cat.keyboard.press('Enter');expect(cat.locator('#companionTools')).to_be_visible();cat.keyboard.press('Escape');expect(cat.locator('#companionTools')).to_be_hidden();expect(cat.locator('#menuToggle')).to_be_focused()
   report['checks']['companion_keyboard_menu_and_escape']='passed'
   # Another live bridge must not make a disconnected selected session appear
   # connected merely because its unresolved permission has display priority.
   queue=data/'bridge/queue';queue.mkdir(parents=True,exist_ok=True)
   for index,(source,session,kind) in enumerate([('waiting-source','waiting','permission'),('other-source','','connected'),('waiting-source','','disconnected')]):
    stamp=int(time.time()*1000)
    evidence={'version':1,'adapter':'opencode','id':f'connection-{time.time_ns()}','source':source,'timestamp':stamp,'workspace':str(workspace),'session':session,'kind':kind,'request':'pending-question'}
    temporary=queue/f'{stamp}-{index}.tmp';temporary.write_text(json.dumps(evidence));temporary.replace(temporary.with_suffix('.json'))
    cat.wait_for_timeout(600)
   expect(dock.locator('#app')).to_have_attribute('data-state','permission')
   expect(dock.locator('#bridgeLabel')).to_have_text('Offline')
   expect(dock.locator('#connection')).to_contain_text('Connection lost')
   snap=invoke('get_snapshot');assert snap['connected'] and not snap['selected_connected']
   dock.screenshot(path=str(ART/'dock-selected-session-offline.png'))
   report['checks']['selected_session_connection_is_honest_with_another_live_bridge_and_pending_permission']='passed'
   report['ready_geometry']=invoke('desktop_diagnostics')
   success=True
   if not args.keep_open:invoke('quit_app')
   browser.close()
 finally:
  if fixture and fixture.poll() is None:fixture.terminate();fixture.wait(timeout=10)
  if (not args.keep_open or not success) and app.poll() is None:app.terminate();app.wait(timeout=15)
  (ART/'desktop-native.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2),flush=True)

if __name__=='__main__':main()
