"""Repeatable native process-tree workloads. Explicit adapter fixtures, no product API.

Frame measurements are DOM mutation/RAF cadence, not presented GPU frame times.
The diagnostic trace/allocation sampler is separate from timed CPU workloads.
"""
import argparse, hashlib, json, os, re, subprocess, time, urllib.request
from pathlib import Path
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import psutil
from playwright.sync_api import sync_playwright, expect
from quality_wait import wait_for_snapshot

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'.artifacts/final-quality'
def seed_character(cat, seed):
 """Set only the existing constructor parameter through CDP, then disable debugger.
 No crypto replacement, product source change, test URL or product API is needed.
 """
 cdp=cat.context.new_cdp_session(cat);scripts=[];cdp.on('Debugger.scriptParsed',lambda e:scripts.append(e));cdp.send('Debugger.enable')
 match=source=url=None
 for script in scripts:
  if not script.get('url','').endswith('.js'):continue
  text=cdp.send('Debugger.getScriptSource',{'scriptId':script['scriptId']})['scriptSource']
  found=re.search(r'constructor\(\w+,(\w+)=crypto\.getRandomValues\(new Uint32Array\(1\)\)\[0\]\)\{',text)
  if found:match=found;source=text;url=script['url'];break
 assert match,'Character constructor not found; refusing an unseeded comparison'
 point=match.end();line=source[:point].count('\n');column=point-(source.rfind('\n',0,point)+1);injected=[]
 def paused(event):
  frame=event['callFrames'][0]
  cdp.send('Debugger.setVariableValue',{'scopeNumber':0,'variableName':match.group(1),'newValue':{'value':seed},'callFrameId':frame['callFrameId']})
  actual=cdp.send('Debugger.evaluateOnCallFrame',{'callFrameId':frame['callFrameId'],'expression':match.group(1)})['result']['value'];assert actual==seed
  injected.append(actual);cdp.send('Debugger.resume')
 cdp.on('Debugger.paused',paused)
 cdp.send('Debugger.setBreakpointByUrl',{'url':url,'lineNumber':line,'columnNumber':column})
 cat.reload(wait_until='networkidle');assert injected==[seed],injected
 cdp.send('Debugger.disable');cdp.detach()

def distribution(values):
 values=sorted(values)
 return {f'p{p}':round(values[min(len(values)-1,int((len(values)-1)*p/100))],3) for p in [50,90,95,99]} if values else {}

def main():
 parser=argparse.ArgumentParser()
 parser.add_argument('--exe',type=Path,default=ROOT/'src-tauri/target/release/nekoafk.exe')
 parser.add_argument('--name',required=True)
 parser.add_argument('--repeats',type=int,default=3)
 parser.add_argument('--diagnostics',action='store_true')
 parser.add_argument('--seed',type=int)
 parser.add_argument('--typing-only',action='store_true',help='Compare only the same 14-second authored keyboard entrance')
 args=parser.parse_args();ART.mkdir(parents=True,exist_ok=True)
 report={'exe_sha256':hashlib.sha256(args.exe.read_bytes()).hexdigest(),'runs':[],
  'method':f'Fresh native process per repeat; identical ordered hook workloads/settings, 5-second warmup. Character seed: {args.seed if args.seed is not None else "random"}; activities and active-pose ratios recorded. CPU includes app descendants, excludes external fixture producer.',
  'frame_limit':'RAF and DOM mutation cadence are not GPU presented-frame times.'}
 for repeat in range(args.repeats):
  data=ART/f'{args.name}-{repeat}-{time.time_ns()}';data.mkdir();workspace=data/'workspace';workspace.mkdir()
  (data/'settings.json').write_text(json.dumps({'settings':{'workspace':str(workspace),'scale':1,'attached':False,'transparent':True,'dock_visible':False},'placements':{'neko':{'x':700,'y':220,'width':300,'height':300}}}))
  port=9360+repeat
  env=dict(os.environ,NEKOAFK_DATA_DIR=str(data),WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS=f'--remote-debugging-port={port}')
  app=subprocess.Popen([str(args.exe.resolve())],env=env)
  producer=None
  run={'repeat':repeat,'data_dir':str(data),'phases':{},'errors':[]};report['runs'].append(run)
  try:
   deadline=time.monotonic()+40
   while True:
    try:version=json.load(urllib.request.urlopen(f'http://127.0.0.1:{port}/json/version',timeout=1));break
    except Exception:
     if time.monotonic()>deadline or app.poll() is not None:raise
     time.sleep(.1)
   with sync_playwright() as p,ThreadPoolExecutor(max_workers=1) as pool:
    browser=p.chromium.connect_over_cdp(version['webSocketDebuggerUrl'])
    deadline=time.monotonic()+30
    while True:
     pages=[pg for c in browser.contexts for pg in c.pages]
     if all(any('surface='+s in pg.url for pg in pages) for s in ['neko','telemetry','settings']):break
     if time.monotonic()>deadline:raise RuntimeError('Native targets missing')
     if pages:pages[0].wait_for_timeout(100)
     else:browser.new_browser_cdp_session().send('Target.getTargets')
    cat=next(pg for pg in pages if 'surface=neko' in pg.url);dock=next(pg for pg in pages if 'surface=telemetry' in pg.url)
    for pg in pages:pg.on('pageerror',lambda e:run['errors'].append(str(e)))
    expect(cat.locator('#app')).to_have_attribute('data-ready','true')
    if args.seed is not None:
     seed_character(cat,args.seed);run['character_seed']=args.seed
     expect(cat.locator('#app')).to_have_attribute('data-ready','true')
    def invoke(c,a=None):return dock.evaluate('async([c,a])=>await window.__TAURI_INTERNALS__.invoke(c,a)',[c,a or {}])
    producer=subprocess.Popen(['node',str(ROOT/'tests/quality_events.mjs'),str(workspace)],env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True,creationflags=subprocess.CREATE_NO_WINDOW)
    assert json.loads(producer.stdout.readline())['ready']
    def send(action,**fields):
     producer.stdin.write(json.dumps({'action':action,**fields})+'\n');producer.stdin.flush()
     reply=json.loads(producer.stdout.readline());assert reply.get('ok'),reply
    cdp=cat.context.new_cdp_session(cat);cdp.send('Performance.enable')
    cat.evaluate('''()=>{window.qRAF=[];window.qPaint=[];window.qLong=[];window.qLag=[];
      const original=requestAnimationFrame.bind(window);window.requestAnimationFrame=cb=>original(t=>{window.qRAF.push(t);window.qLag.push(performance.now()-t);cb(t)});
      new MutationObserver(()=>window.qPaint.push(performance.now())).observe(document.querySelector('#rig'),{attributes:true,subtree:true});
      new PerformanceObserver(list=>window.qLong.push(...list.getEntries().map(e=>e.duration))).observe({entryTypes:['longtask']});}''')
    def usage():
     result={}
     for proc in [psutil.Process(app.pid)]+psutil.Process(app.pid).children(recursive=True):
      try:
       times=proc.cpu_times();cmd=proc.cmdline();mem=proc.memory_full_info()
       result[proc.pid]={'cpu':times.user+times.system,'private':mem.uss,'kind':next((v.split('=',1)[1] for v in cmd if v.startswith('--type=')),proc.name())}
      except (psutil.NoSuchProcess,psutil.AccessDenied):pass
     return result
    def metrics():return {v['name']:v['value'] for v in cdp.send('Performance.getMetrics')['metrics']}
    def phase(name,seconds,required_state=None):
     cat.evaluate('()=>{window.qRAF=[];window.qPaint=[];window.qLong=[];window.qLag=[];}')
     initial=usage();m0=metrics();start=time.monotonic();activities=Counter();memory=[];cpu_samples=[];previous=initial;prior_time=start
     while time.monotonic()-start<seconds:
      cat.wait_for_timeout(500)
      state=cat.locator('#app').get_attribute('data-state')
      if required_state:assert state==required_state,(name,state)
      activities[cat.locator('#mascot').get_attribute('data-activity')]+=1
      current=usage();now=time.monotonic();memory.append(sum(v['private'] for v in current.values())/1048576)
      cpu_samples.append(sum(v['cpu']-previous[k]['cpu'] for k,v in current.items() if k in previous)/(now-prior_time)*100)
      previous=current;prior_time=now
     elapsed=time.monotonic()-start;last=usage();m1=metrics();by=Counter()
     for pid,v in last.items():
      if pid in initial:by[v['kind']]+=v['cpu']-initial[pid]['cpu']
     raw=cat.evaluate('()=>({raf:window.qRAF,paint:window.qPaint,long:window.qLong,lag:window.qLag})')
     item={'seconds':round(elapsed,2),'cpu_one_core':round(sum(by.values())/elapsed*100,3),'cpu_by_kind':{k:round(v/elapsed*100,3) for k,v in by.items()},
      'cpu_half_second_distribution':distribution(cpu_samples),'private_start_mib':round(sum(v['private'] for v in initial.values())/1048576,1),'private_end_mib':round(sum(v['private'] for v in last.values())/1048576,1),'private_peak_mib':round(max(memory),1),
      'activities':dict(activities),'raf_count':len(raw['raf']),'pose_mutations':len(raw['paint']),
      'raf_callback_lag_ms':distribution(raw['lag']),
      'processes_appeared':list(set(last)-set(initial)),'processes_retired':list(set(initial)-set(last)),
      'pose_intervals_ms':distribution([b-a for a,b in zip(raw['paint'],raw['paint'][1:]) if b-a<100]),
      'pose_gaps_over_50ms':sum(50<b-a<100 for a,b in zip(raw['paint'],raw['paint'][1:])),
      'long_tasks_ms':raw['long'],'webview_delta':{k:round(m1.get(k,0)-m0.get(k,0),6) for k in ['TaskDuration','ScriptDuration','LayoutDuration','RecalcStyleDuration']},
      'js_heap_end_bytes':m1.get('JSHeapUsedSize')}
     run['phases'][name]=item
     (ART/f'{args.name}-profile.json').write_text(json.dumps(report,indent=2))
     print(json.dumps({'repeat':repeat,'phase':name,**item}),flush=True)
    cat.wait_for_timeout(5000)
    if args.typing_only:
     send('writing');expect(cat.locator('#app')).to_have_attribute('data-state','writing');phase('typing_only',14,'writing')
     assert not run['errors'];send('quit');invoke('quit_app');browser.close();app.wait(timeout=15)
     continue
    send('idle');expect(cat.locator('#app')).to_have_attribute('data-state','idle');phase('idle',30,'idle')
    send('writing');expect(cat.locator('#app')).to_have_attribute('data-state','writing');phase('writing',35,'writing')
    initial=invoke('get_snapshot');before_tests=next(iter(initial['engine']['sessions'].values()))['tests_passed']
    flood=pool.submit(send,'flood',count=500,interval_ms=20);phase('event_flood',15)
    flood.result(timeout=5)
    final=wait_for_snapshot(lambda:next(iter(invoke('get_snapshot')['engine']['sessions'].values())),lambda s:s['tests_passed']==before_tests+500 and not s['operations'],cat.wait_for_timeout)
    assert not final['operations'] and final['failures']==0
    run['duplicate_terminal_integrity']={'unique_tests':500,'observed_delta':final['tests_passed']-before_tests,'open_operations':0}
    send('start',operation='long-tool');expect(cat.locator('#app')).to_have_attribute('data-state','active');phase('long_tool',70,'active')
    send('end',operation='long-tool',exit=None);send('idle')
    invoke('window_action',{'action':'hide-neko'});phase('hidden',15)
    assert run['phases']['hidden']['raf_count']==0
    invoke('window_action',{'action':'recover'})
    prefs=invoke('get_snapshot')['settings'];prefs['reduced_motion']=True;invoke('save_settings',{'settings':prefs})
    expect(cat.locator('#app')).to_have_attribute('data-motion','reduced')
    cat.evaluate('()=>new Promise(resolve=>queueMicrotask(resolve))');phase('reduced_motion',10)
    assert run['phases']['reduced_motion']['pose_mutations']==0
    prefs['reduced_motion']=False;invoke('save_settings',{'settings':prefs})
    if args.diagnostics and repeat==0:
     send('writing');cat.wait_for_timeout(600)
     cdp.send('HeapProfiler.startSampling',{'samplingInterval':32768,'includeObjectsCollectedByMajorGC':True,'includeObjectsCollectedByMinorGC':True})
     complete=[];cdp.on('Tracing.tracingComplete',lambda e:complete.append(e))
     cdp.send('Tracing.start',{'categories':'devtools.timeline,disabled-by-default-devtools.timeline.frame,cc','transferMode':'ReturnAsStream'})
     cat.wait_for_timeout(10000);cdp.send('Tracing.end')
     while not complete:cat.wait_for_timeout(100)
     chunks=[];handle=complete[0]['stream']
     while True:
      piece=cdp.send('IO.read',{'handle':handle});chunks.append(piece['data'])
      if piece.get('eof'):break
     cdp.send('IO.close',{'handle':handle})
     trace=json.loads(''.join(chunks));(ART/f'{args.name}-trace.json').write_text(json.dumps(trace))
     allocations=cdp.send('HeapProfiler.stopSampling');(ART/f'{args.name}-allocations.json').write_text(json.dumps(allocations))
     events=trace['traceEvents'];durations=Counter();counts=Counter()
     for e in events:
      if e.get('ph')=='X':counts[e['name']]+=1;durations[e['name']]+=e.get('dur',0)/1000
     run['diagnostic_trace']={'separate_from_comparable_cpu_samples':True,'top_duration_ms':durations.most_common(15),'counts':{k:counts[k] for k in ['Paint','RasterTask','Layout','UpdateLayoutTree','FunctionCall','DrawFrame']}}
    assert not run['errors'];send('quit');invoke('quit_app');browser.close();app.wait(timeout=15)
  finally:
   if producer and producer.poll() is None:producer.terminate();producer.wait(timeout=10)
   if app.poll() is None:app.terminate();app.wait(timeout=15)
   (ART/f'{args.name}-profile.json').write_text(json.dumps(report,indent=2))

if __name__=='__main__':main()
