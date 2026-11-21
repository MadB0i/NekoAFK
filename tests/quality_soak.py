"""20-minute repeatable native soak: real local OpenCode plus labelled hook fixtures.
No model requests, external services, install/package commands or product debug API.
"""
import argparse, hashlib, json, os, shutil, subprocess, threading, time, urllib.request
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from collections import Counter
import psutil
from playwright.sync_api import sync_playwright, expect
from quality_native import distribution, seed_character
from quality_wait import wait_for_snapshot

ROOT=Path(__file__).resolve().parents[1];ART=ROOT/'.artifacts/final-quality'
def main():
 global ART
 parser=argparse.ArgumentParser();parser.add_argument('--seconds',type=int,default=1200);parser.add_argument('--art',type=Path,default=ART);args=parser.parse_args()
 ART=args.art.resolve();ART.mkdir(parents=True,exist_ok=True)
 base=ART/f'soak-{time.time_ns()}';base.mkdir(parents=True);workspace=base/'workspace';workspace.mkdir();data=base/'data';data.mkdir()
 previous=json.loads((ROOT/'.artifacts/opencode-live-report.json').read_text())
 shutil.copyfile(Path(previous['workspace'])/'opencode.json',workspace/'opencode.json')
 (workspace/'.opencode/plugins').mkdir(parents=True);shutil.copyfile(ROOT/'integrations/opencode/nekoafk.js',workspace/'.opencode/plugins/nekoafk.js')
 (workspace/'source.txt').write_text('unchanged source\n')
 settings={'workspace':str(workspace),'verify_program':'cmd.exe','verify_args':['/d','/c','ping -n 3 127.0.0.1 >nul & exit 0'],'verify_timeout':10,'scale':1,'attached':False,'transparent':True,'dock_visible':True}
 (data/'settings.json').write_text(json.dumps({'settings':settings,'placements':{'neko':{'x':700,'y':220,'width':300,'height':300},'telemetry':{'x':1050,'y':220,'width':460,'height':650}}}))
 env=dict(os.environ,NEKOAFK_DATA_DIR=str(data),OPENCODE_CONFIG_DIR=str(base/'config'),XDG_CONFIG_HOME=str(base/'config-home'),XDG_DATA_HOME=str(base/'appdata'),XDG_STATE_HOME=str(base/'state'),XDG_CACHE_HOME=str(base/'cache'),OPENCODE_DISABLE_DEFAULT_PLUGINS='true',OPENCODE_DISABLE_MODELS_FETCH='true',OPENCODE_DISABLE_AUTOUPDATE='true')
 exe=ROOT/'src-tauri/target/release/nekoafk.exe';app=server=producer=None;log=open(base/'server.log','w');report={'exe_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'seconds_requested':args.seconds,'base':str(base),'model_requests':0,'stages':[],'samples':[],'checks':{},'errors':[],'protocol_events':{},'limits':['Native DOM mutation cadence is not presented GPU frame timing.','Application hide/resume is not OS sleep/wake.','Twenty minutes does not establish multi-day stability.']}
 def request(route,body=None,method=None,timeout=120):
  req=urllib.request.Request('http://127.0.0.1:14601'+route,data=json.dumps(body).encode() if body is not None else None,headers={'content-type':'application/json','x-opencode-directory':str(workspace)},method=method)
  with urllib.request.urlopen(req,timeout=timeout) as r:return json.load(r)
 def start_server():
  return subprocess.Popen([str(ROOT/'.artifacts/opencode/node_modules/opencode-windows-x64/bin/opencode.exe'),'serve','--hostname','127.0.0.1','--port','14601'],cwd=workspace,env=env,stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)
 def collect_protocol():
  try:
   with urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:14601/event',headers={'x-opencode-directory':str(workspace)}),timeout=120) as stream:
    for line in stream:
     if not line.startswith(b'data:'):continue
     event=json.loads(line[5:]);kind=event.get('type','unknown');record=report['protocol_events'].setdefault(kind,{'count':0,'property_keys':[],'numeric_exits':[],'metadata_keys':[]});record['count']+=1
     properties=event.get('properties',{});record['property_keys']=sorted(properties.keys())
     metadata=properties.get('part',{}).get('state',{}).get('metadata',{})
     if isinstance(metadata,dict):
      record['metadata_keys']=sorted(set(record['metadata_keys'])|set(metadata))
      if type(metadata.get('exit')) is int:record['numeric_exits'].append(metadata['exit'])
  except Exception:pass # Server stop/restart intentionally closes the stream.
 try:
  server=start_server();deadline=time.monotonic()+40
  while True:
   try:report['opencode_version']=request('/global/health',timeout=3)['version'];break
   except Exception:
    if time.monotonic()>deadline:raise
    time.sleep(.1)
  threading.Thread(target=collect_protocol,daemon=True).start()
  app=subprocess.Popen([str(exe)],env=dict(env,WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS='--remote-debugging-port=9362'))
  deadline=time.monotonic()+40
  while True:
   try:version=json.load(urllib.request.urlopen('http://127.0.0.1:9362/json/version',timeout=1));break
   except Exception:
    if time.monotonic()>deadline:raise
    time.sleep(.1)
  with sync_playwright() as p,ThreadPoolExecutor(max_workers=1) as worker:
   browser=p.chromium.connect_over_cdp(version['webSocketDebuggerUrl']);deadline=time.monotonic()+30
   while True:
    pages=[pg for c in browser.contexts for pg in c.pages]
    if all(any('surface='+s in pg.url for pg in pages) for s in ['neko','telemetry','settings']):break
    if time.monotonic()>deadline:raise RuntimeError('Missing native surfaces')
    if pages:pages[0].wait_for_timeout(100)
    else:browser.new_browser_cdp_session().send('Target.getTargets')
   cat=next(pg for pg in pages if 'surface=neko' in pg.url);dock=next(pg for pg in pages if 'surface=telemetry' in pg.url)
   for pg in pages:pg.on('pageerror',lambda e:report['errors'].append(str(e)))
   expect(cat.locator('#app')).to_have_attribute('data-ready','true')
   seed_character(cat,1234);report['character_seed']=1234
   expect(cat.locator('#app')).to_have_attribute('data-ready','true')
   def invoke(c,a=None):return dock.evaluate('async([c,a])=>await window.__TAURI_INTERNALS__.invoke(c,a)',[c,a or {}])
   def snapshot():return invoke('get_snapshot')
   def session(id):return next(s for s in snapshot()['engine']['sessions'].values() if s['id']==id)
   def select(id):invoke('select_session',{'key':session(id)['key']})
   producer=subprocess.Popen(['node',str(ROOT/'tests/quality_events.mjs'),str(workspace)],env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True,creationflags=subprocess.CREATE_NO_WINDOW)
   assert json.loads(producer.stdout.readline())['ready']
   def send(action,**fields):
    producer.stdin.write(json.dumps({'action':action,**fields})+'\n');producer.stdin.flush();reply=json.loads(producer.stdout.readline());assert reply.get('ok'),reply
   cat.evaluate('''()=>{window.soakPaint=[];window.soakFrames=0;window.soakLastFrame=performance.now();const raf=requestAnimationFrame.bind(window);window.requestAnimationFrame=cb=>raf(t=>{window.soakFrames++;window.soakLastFrame=performance.now();cb(t)});new MutationObserver(()=>window.soakPaint.push(performance.now())).observe(document.querySelector('#rig'),{attributes:true,subtree:true});}''')
   cdp=cat.context.new_cdp_session(cat);cdp.send('Performance.enable')
   def usage():
    results={}
    for proc in [psutil.Process(app.pid)]+psutil.Process(app.pid).children(recursive=True):
     try:
      t=proc.cpu_times();m=proc.memory_full_info();results[proc.pid]={'cpu':t.user+t.system,'private':m.uss}
     except (psutil.NoSuchProcess,psutil.AccessDenied):pass
    return results
   start=time.monotonic();prior_time=start;prior=usage();initial=prior
   def wait(seconds,label,expected=None):
    nonlocal prior_time,prior
    begin=time.monotonic();cat.evaluate('()=>{window.soakPaint=[];window.soakFrames=0}')
    while time.monotonic()-begin<seconds:
     cat.wait_for_timeout(min(1000,max(1,(seconds-(time.monotonic()-begin))*1000)))
     now=time.monotonic();current=usage();snap=snapshot()
     if expected:assert snap['selected_state']==expected,(label,snap['selected_state'])
     metrics={v['name']:v['value'] for v in cdp.send('Performance.getMetrics')['metrics']}
     context=cat.evaluate('()=>({activity:document.querySelector("#mascot").dataset.activity,motion:document.querySelector("#app").dataset.motion,document_hidden:document.hidden,raf_count:window.soakFrames,last_frame_gap_ms:performance.now()-window.soakLastFrame})')
     report['samples'].append({'seconds':round(now-start,2),'stage':label,'cpu_one_core':round(sum(v['cpu']-prior[k]['cpu'] for k,v in current.items() if k in prior)/(now-prior_time)*100,3),'private_mib':round(sum(v['private'] for v in current.values())/1048576,2),'js_heap_bytes':metrics.get('JSHeapUsedSize'),'state':snap['selected_state'],**context,'desktop_paused':snap['desktop_paused']})
     prior=current;prior_time=now
    raw=cat.evaluate('()=>({paint:window.soakPaint,frames:window.soakFrames})')
    report['stages'].append({'stage':label,'seconds':round(time.monotonic()-begin,2),'raf_count':raw['frames'],'pose_mutations':len(raw['paint']),'pose_intervals_ms':distribution([b-a for a,b in zip(raw['paint'],raw['paint'][1:]) if b-a<100])})
    (ART/'soak-progress.json').write_text(json.dumps(report,indent=2));print(json.dumps({'stage':label,'elapsed':round(time.monotonic()-start),'last_sample':report['samples'][-1]}),flush=True)
   real=request('/session',{'title':'NekoAFK quality soak authentic shell'})['id']
   request(f'/session/{real}/shell',{'agent':'build','command':'echo NEKO_QUALITY_READY'})
   expect(dock.locator('#app')).to_have_attribute('data-state',__import__('re').compile('idle|active'))
   send('idle');cat.wait_for_timeout(800);select(real)
   cycle=0
   while time.monotonic()-start<args.seconds:
    cycle_start=time.monotonic();cycle+=1
    select(real);wait(20,f'{cycle}:authentic_idle')
    future=worker.submit(request,f'/session/{real}/shell',{'agent':'build','command':'sleep 70'})
    expect(dock.locator('#app')).to_have_attribute('data-state','active',timeout=15000)
    wait(65,f'{cycle}:authentic_long_tool','active');assert session(real)['operations'];future.result(timeout=15)
    expect(dock.locator('#activity')).to_contain_text('exit code unavailable',timeout=15000)
    assert session(real)['verification']=='not_run'
    send('writing');cat.wait_for_timeout(700);select('quality-session');wait(35,f'{cycle}:simulated_writing','writing')
    before=session('quality-session')['tests_passed'];flood=worker.submit(send,'flood',count=500,interval_ms=20);wait(15,f'{cycle}:simulated_duplicate_flood');flood.result(timeout=5)
    drained=wait_for_snapshot(lambda:session('quality-session'),lambda s:s['tests_passed']==before+500 and not s['operations'],cat.wait_for_timeout)
    report.setdefault('duplicate_terminal_snapshots',[]).append(drained)
    assert not report['duplicate_terminal_snapshots'][-1]['operations'],report['duplicate_terminal_snapshots'][-1]
    send('permission');expect(dock.locator('#app')).to_have_attribute('data-state','permission');send('writing');wait(5,f'{cycle}:permission_interrupt','permission');send('resolved');send('idle')
    for attempt in range(3):
     send('claimed');expect(dock.locator('#app')).to_have_attribute('data-state','claimed');invoke('run_verification');invoke('cancel_verification');expect(dock.locator('#app')).to_have_attribute('data-state','inconclusive',timeout=15000)
     assert session('quality-session')['verification']=='inconclusive'
    send('claimed');expect(dock.locator('#app')).to_have_attribute('data-state','claimed');invoke('run_verification');select(real);send('writing');wait(4,f'{cycle}:switch_during_interrupted_verification');assert session('quality-session')['verification']=='inconclusive';assert snapshot()['selected_state']!='verified'
    select('quality-session');send('idle');send('claimed');expect(dock.locator('#app')).to_have_attribute('data-state','claimed');invoke('run_verification');expect(dock.locator('#app')).to_have_attribute('data-state','verified',timeout=15000);wait(10,f'{cycle}:independently_verified','verified')
    send('idle');invoke('window_action',{'action':'hide-neko'});invoke('window_action',{'action':'hide-dock'});wait(30,f'{cycle}:hidden');assert report['stages'][-1]['raf_count']==0
    invoke('window_action',{'action':'recover'});wait(10,f'{cycle}:application_resume')
    select(real);server.terminate();server.wait(timeout=15)
    expect(dock.locator('#bridgeLabel')).to_have_text('Offline',timeout=50000);wait(5,f'{cycle}:real_server_disconnected','disconnected')
    server=start_server();deadline=time.monotonic()+40
    while True:
     try:request('/global/health',timeout=3);break
     except Exception:
      if time.monotonic()>deadline:raise
      cat.wait_for_timeout(100)
    threading.Thread(target=collect_protocol,daemon=True).start()
    request(f'/session/{real}/shell',{'agent':'build','command':'exit 7'})
    expect(dock.locator('#bridgeLabel')).to_have_text('Connected',timeout=15000)
    expect(dock.locator('#activity')).to_contain_text('exit code unavailable',timeout=15000)
    assert session(real)['tests_passed']==0 and session(real)['failures']==0 and session(real)['verification']=='not_run'
    select('quality-session');send('idle');wait(min(max(0,600-(time.monotonic()-cycle_start)),max(0,args.seconds-(time.monotonic()-start))),f'{cycle}:quiet_remainder')
   report['checks']={k:'passed' for k in ['authentic_70_second_tools','duplicate_terminal_integrity','permission_priority','cancelled_verification','session_switch_during_interrupted_verification','independent_verified_success','real_opencode_restart','unknown_direct_shell_exit_never_passed','hidden_and_application_resume','runtime_errors']}
   report['unexplained_full_motion_gaps']=[s for s in report['samples'] if s['motion']=='full' and not s['document_hidden'] and not s['desktop_paused'] and s['last_frame_gap_ms']>15000]
   report['checks']['full_motion_callback_gaps']='needs_investigation' if report['unexplained_full_motion_gaps'] else 'passed'
   assert not report['errors']
   samples=report['samples'];duration=time.monotonic()-start
   report['resources']={'seconds':round(duration,2),'cpu_one_core':round(sum(v['cpu']-initial[k]['cpu'] for k,v in prior.items() if k in initial)/duration*100,3),'private_start_mib':round(sum(v['private'] for v in initial.values())/1048576,2),'private_end_mib':samples[-1]['private_mib'],'private_peak_mib':max(s['private_mib'] for s in samples),'cpu_samples':distribution([s['cpu_one_core'] for s in samples]),'processes_appeared':list(set(prior)-set(initial)),'processes_retired':list(set(initial)-set(prior)),'sample_interval':'1 second inside labelled waits; API/polling gaps are included in the next interval; stage assertions record observed states.'}
   cat.screenshot(path=str(ART/'soak-native-companion.png'),omit_background=True);dock.screenshot(path=str(ART/'soak-native-dock.png'))
   send('quit');invoke('quit_app');app.wait(timeout=20);report['normal_host_exit_code']=app.returncode;browser.close()
 except BaseException as error:
  report['errors'].append(f'{type(error).__name__}: {error}')
  report['processes_at_failure']={name:{'pid':child.pid,'returncode_before_cleanup':child.poll()} for name,child in [('app',app),('server',server),('producer',producer)] if child}
  if app and app.poll() is None:
   try:report['app_children_at_failure']=[{'pid':child.pid,'name':child.name()} for child in psutil.Process(app.pid).children(recursive=True)]
   except psutil.Error:pass
  raise
 finally:
  if (data/'diagnostics').exists():shutil.copytree(data/'diagnostics',ART/'soak-diagnostics',dirs_exist_ok=True)
  (ART/'soak-report.json').write_text(json.dumps(report,indent=2))
  for child in [producer,app,server]:
   if child and child.poll() is None:child.terminate();child.wait(timeout=15)
  log.close()
if __name__=='__main__':main()
