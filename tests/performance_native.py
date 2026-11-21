"""Native WebView2 profile with matched settings; randomized activities are recorded."""
import argparse, hashlib, json, os, subprocess, time, urllib.request
from pathlib import Path
from collections import Counter
import psutil
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'.artifacts/engineering'

def main():
 parser=argparse.ArgumentParser()
 parser.add_argument('--exe',default=str(ROOT/'src-tauri/target/release/nekoafk.exe'))
 parser.add_argument('--name',default='after')
 parser.add_argument('--keep-open',action='store_true')
 args=parser.parse_args()
 data=ART/(args.name+'-data-'+str(int(time.time())));data.mkdir(parents=True)
 workspace=ART/'workspace';workspace.mkdir(exist_ok=True)
 (data/'settings.json').write_text(json.dumps({'settings':{'workspace':str(workspace),'attached':False,'scale':1,
   'transparent':True,'dock_visible':False,'personality':'playful'},'placements':{'neko':{'x':700,'y':220,'width':300,'height':300}}}))
 env=dict(os.environ,NEKOAFK_DATA_DIR=str(data),WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS='--remote-debugging-port=9350')
 app=subprocess.Popen([args.exe],env=env)
 result={'exe':str(Path(args.exe).resolve()),'exe_sha256':hashlib.sha256(Path(args.exe).read_bytes()).hexdigest(),'pid':app.pid,'data_dir':str(data),'phases':{},'fixture_events':True,'seeded':False}
 try:
  deadline=time.monotonic()+40
  while True:
   try:
    version=json.load(urllib.request.urlopen('http://127.0.0.1:9350/json/version',timeout=1));break
   except Exception:
    if time.monotonic()>deadline:raise
    time.sleep(.1)
  with sync_playwright() as p:
   browser=p.chromium.connect_over_cdp(version['webSocketDebuggerUrl'])
   deadline=time.monotonic()+30
   while True:
    pages=[pg for c in browser.contexts for pg in c.pages]
    if all(any('surface='+s in pg.url for pg in pages) for s in ['neko','telemetry','settings']):break
    if time.monotonic()>deadline:raise RuntimeError('Native surfaces missing')
    if pages:pages[0].wait_for_timeout(100)
    else:browser.new_browser_cdp_session().send('Target.getTargets')
   cat=next(pg for pg in pages if 'surface=neko' in pg.url)
   dock=next(pg for pg in pages if 'surface=telemetry' in pg.url)
   expect(cat.locator('#app')).to_have_attribute('data-ready','true')
   # Instrument an already running native surface; never replace the crypto
   # source used by Tauri's IPC callback IDs.
   cat.evaluate('''() => {window.frameCallbacks=0;const originalRAF=requestAnimationFrame.bind(window);
     window.requestAnimationFrame=cb=>originalRAF(t=>{window.frameCallbacks++;cb(t)}); }''')
   cdp=cat.context.new_cdp_session(cat);cdp.send('Performance.enable')
   cat.evaluate('''() => {window.paintTimes=[];new MutationObserver(()=>window.paintTimes.push(performance.now())).observe(document.querySelector('#rig'),{subtree:true,attributes:true});}''')
   def invoke(c,a=None):return dock.evaluate('async([c,a])=>await window.__TAURI_INTERNALS__.invoke(c,a)',[c,a or {}])
   def emit(s):subprocess.run(['node',str(ROOT/'tests/emit-fixture.mjs'),str(workspace),s],env=env,check=True,capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
   def usage():
    stats={}
    for proc in [psutil.Process(app.pid)]+psutil.Process(app.pid).children(recursive=True):
     try:
      t=proc.cpu_times();mem=proc.memory_full_info();cmd=proc.cmdline()
      kind=next((v.split('=',1)[1] for v in cmd if v.startswith('--type=')),proc.name())
      stats[proc.pid]={'cpu':t.user+t.system,'private':mem.uss,'kind':kind}
     except (psutil.NoSuchProcess,psutil.AccessDenied):pass
    return stats
   def metrics():return {m['name']:m['value'] for m in cdp.send('Performance.getMetrics')['metrics']}
   def phase(name,seconds,profile=False):
    before=usage();m0=metrics();f0=cat.evaluate('window.frameCallbacks');start=time.monotonic();activities=Counter()
    cat.evaluate('window.paintTimes=[]')
    if profile:cdp.send('Profiler.enable');cdp.send('Profiler.start')
    while time.monotonic()-start<seconds:
     activities[cat.locator('#mascot').get_attribute('data-activity')]+=1
     cat.wait_for_timeout(200)
    elapsed=time.monotonic()-start;after=usage();m1=metrics();by_kind=Counter()
    for pid,s in after.items():
     if pid in before:by_kind[s['kind']]+=s['cpu']-before[pid]['cpu']
    item={'seconds':round(elapsed,2),'cpu_percent_one_core':round(sum(by_kind.values())/elapsed*100,2),
      'cpu_by_process_kind':{k:round(v/elapsed*100,2) for k,v in by_kind.items()},
      'private_mib':round(sum(s['private'] for s in after.values())/1048576,1),
      'raf_callbacks':cat.evaluate('window.frameCallbacks')-f0,'sampled_activities':dict(activities),
      'webview_seconds':{k:round(m1.get(k,0)-m0.get(k,0),5) for k in ['TaskDuration','ScriptDuration','LayoutDuration','RecalcStyleDuration']}}
    paints=cat.evaluate('window.paintTimes');intervals=sorted(b-a for a,b in zip(paints,paints[1:]) if 2<b-a<100)
    item['paint_count']=len(paints)
    if intervals:item['mutation_cadence_ms']={'median':round(intervals[len(intervals)//2],2),'p95':round(intervals[int(len(intervals)*.95)],2)}
    if profile:
     prof=cdp.send('Profiler.stop')['profile'];(ART/(args.name+'-'+name+'-cpu-profile.json')).write_text(json.dumps(prof))
     nodes={n['id']:n['callFrame']['functionName'] or '(anonymous)' for n in prof['nodes']};counts=Counter(nodes[n] for n in prof.get('samples',[]))
     item['js_top_samples']=dict(counts.most_common(12))
    result['phases'][name]=item;print(name+' '+json.dumps(item),flush=True)
   result['native']=invoke('desktop_diagnostics')
   phase('idle_mix',35)
   expect(cat.locator('#mascot')).to_have_attribute('data-activity','rest',timeout=40000)
   phase('quiet_rest',8,True)
   emit('writing');expect(cat.locator('#app')).to_have_attribute('data-state','writing')
   phase('active_typing',14,True)
   prefs=invoke('get_snapshot')['settings'];prefs['reduced_motion']=True;invoke('save_settings',{'settings':prefs})
   phase('reduced_motion',10)
   prefs['dock_visible']=True;invoke('save_settings',{'settings':prefs})
   phase('dock_visible_static',10)
   invoke('window_action',{'action':'hide-neko'});invoke('window_action',{'action':'hide-dock'})
   phase('all_hidden',10)
   if not args.keep_open:invoke('quit_app')
   browser.close()
 finally:
  (ART/(args.name+'-performance.json')).write_text(json.dumps(result,indent=2))
  if not args.keep_open and app.poll() is None:app.terminate();app.wait(timeout=10)

if __name__=='__main__':main()

