"""Native quiet-period follow-up with explicit visibility/pause/RAF context.
Independent command proof precedes the happy-idle interval. No model requests.
"""
import argparse,hashlib,json,os,subprocess,time,urllib.request
from pathlib import Path
import psutil
from playwright.sync_api import sync_playwright,expect
from quality_native import seed_character,distribution

ROOT=Path(__file__).resolve().parents[1];ART=ROOT/'.artifacts/final-quality'

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--seconds',type=int,default=300);args=parser.parse_args()
 base=ART/f'quiet-{time.time_ns()}';base.mkdir();workspace=base/'workspace';workspace.mkdir()
 settings={'workspace':str(workspace),'verify_program':'cmd.exe','verify_args':['/d','/c','exit 0'],'verify_timeout':5,'scale':1,'attached':False,'transparent':True,'dock_visible':False}
 (base/'settings.json').write_text(json.dumps({'settings':settings,'placements':{'neko':{'x':700,'y':220,'width':300,'height':300}}}))
 exe=ROOT/'src-tauri/target/release/nekoafk.exe';env=dict(os.environ,NEKOAFK_DATA_DIR=str(base),WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS='--remote-debugging-port=9365')
 app=subprocess.Popen([str(exe)],env=env);producer=None
 report={'exe_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'seconds_requested':args.seconds,'samples':[],'errors':[],'unexplained_full_motion_gaps':[],'method':'Native app process tree, 1-second sampling; explicit app/DOM visibility and desktop-pause context. No callbacks for >15 seconds while full/visible is flagged, not assumed to be a director failure. No GPU presentation measurement.'}
 try:
  deadline=time.monotonic()+40
  while True:
   try:version=json.load(urllib.request.urlopen('http://127.0.0.1:9365/json/version',timeout=1));break
   except Exception:
    if time.monotonic()>deadline:raise
    time.sleep(.1)
  with sync_playwright() as p:
   browser=p.chromium.connect_over_cdp(version['webSocketDebuggerUrl']);deadline=time.monotonic()+30
   while True:
    pages=[pg for c in browser.contexts for pg in c.pages]
    if all(any('surface='+s in pg.url for pg in pages) for s in ['neko','telemetry','settings']):break
    if time.monotonic()>deadline:raise RuntimeError('Missing native surfaces')
    if pages:pages[0].wait_for_timeout(100)
    else:browser.new_browser_cdp_session().send('Target.getTargets')
   cat=next(pg for pg in pages if 'surface=neko' in pg.url);dock=next(pg for pg in pages if 'surface=telemetry' in pg.url)
   for pg in pages:pg.on('pageerror',lambda e:report['errors'].append(str(e)))
   expect(cat.locator('#app')).to_have_attribute('data-ready','true');seed_character(cat,1234)
   def invoke(c,a=None):return dock.evaluate('async([c,a])=>await window.__TAURI_INTERNALS__.invoke(c,a)',[c,a or {}])
   report['native_geometry']=invoke('desktop_diagnostics')
   producer=subprocess.Popen(['node',str(ROOT/'tests/quality_events.mjs'),str(workspace)],env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True,creationflags=subprocess.CREATE_NO_WINDOW)
   assert json.loads(producer.stdout.readline())['ready']
   def send(action):
    producer.stdin.write(json.dumps({'action':action})+'\n');producer.stdin.flush();assert json.loads(producer.stdout.readline()).get('ok')
   send('claimed');expect(cat.locator('#app')).to_have_attribute('data-state','claimed');invoke('run_verification');expect(cat.locator('#app')).to_have_attribute('data-state','verified')
   cat.evaluate('''()=>{window.quietFrames=[];window.quietPaint=[];window.quietLast=performance.now();const raf=requestAnimationFrame.bind(window);window.requestAnimationFrame=cb=>raf(t=>{window.quietLast=performance.now();window.quietFrames.push(window.quietLast);cb(t)});new MutationObserver(()=>window.quietPaint.push(performance.now())).observe(document.querySelector('#rig'),{attributes:true,subtree:true});}''')
   def usage():
    result={}
    for proc in [psutil.Process(app.pid)]+psutil.Process(app.pid).children(recursive=True):
     try:
      t=proc.cpu_times();m=proc.memory_full_info();result[proc.pid]={'cpu':t.user+t.system,'private':m.uss}
     except (psutil.NoSuchProcess,psutil.AccessDenied):pass
    return result
   initial=prior=usage();start=prior_time=time.monotonic();cdp=cat.context.new_cdp_session(cat);cdp.send('Performance.enable')
   while time.monotonic()-start<args.seconds:
    cat.wait_for_timeout(1000);snap=invoke('get_snapshot');current=usage();now=time.monotonic()
    context=cat.evaluate('()=>({motion:document.querySelector("#app").dataset.motion,hidden:document.hidden,activity:document.querySelector("#mascot").dataset.activity,frames:window.quietFrames.length,last_frame_gap_ms:performance.now()-window.quietLast})')
    metrics={m['name']:m['value'] for m in cdp.send('Performance.getMetrics')['metrics']}
    sample={'seconds':round(now-start,2),'state':snap['selected_state'],'desktop_paused':snap['desktop_paused'],'app_visible':snap['settings']['neko_visible'],'selected_connected':snap['selected_connected'],**context,'cpu_one_core':round(sum(v['cpu']-prior[k]['cpu'] for k,v in current.items() if k in prior)/(now-prior_time)*100,3),'private_mib':round(sum(v['private'] for v in current.values())/1048576,2),'js_heap_bytes':metrics.get('JSHeapUsedSize')}
    report['samples'].append(sample);prior=current;prior_time=now
    assert sample['state']=='verified' and sample['selected_connected'],sample
    if sample['motion']=='full' and not sample['hidden'] and not sample['desktop_paused'] and sample['last_frame_gap_ms']>15000:report['unexplained_full_motion_gaps'].append(sample)
    if len(report['samples'])%60==0:
     (ART/'quiet-progress.json').write_text(json.dumps(report,indent=2));print(json.dumps(sample),flush=True)
   raw=cat.evaluate('()=>({frames:window.quietFrames,paint:window.quietPaint})');duration=time.monotonic()-start
   report['resources']={'seconds':round(duration,2),'cpu_one_core':round(sum(v['cpu']-initial[k]['cpu'] for k,v in prior.items() if k in initial)/duration*100,3),'private_start_mib':round(sum(v['private'] for v in initial.values())/1048576,2),'private_end_mib':report['samples'][-1]['private_mib'],'private_peak_mib':max(s['private_mib'] for s in report['samples']),'raf_count':len(raw['frames']),'pose_mutations':len(raw['paint']),'pose_intervals_ms':distribution([b-a for a,b in zip(raw['paint'],raw['paint'][1:]) if b-a<100]),'max_callback_gap_ms':max([b-a for a,b in zip(raw['frames'],raw['frames'][1:])],default=0)}
   report['checks']={'independent_proof_and_connection':'passed','runtime_errors':'passed' if not report['errors'] else 'failed','full_motion_callback_gaps':'passed' if not report['unexplained_full_motion_gaps'] else 'needs_investigation'}
   send('quit');invoke('quit_app');browser.close()
 except BaseException as error:
  report['errors'].append(f'{type(error).__name__}: {error}');raise
 finally:
  (ART/'quiet-report.json').write_text(json.dumps(report,indent=2))
  for child in [producer,app]:
   if child and child.poll() is None:child.terminate();child.wait(timeout=15)

if __name__=='__main__':main()
