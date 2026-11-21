"""Controlled native failure evidence; never target processes outside this test's app tree.
These injected terminations are NOT spontaneous reproductions of the historical incident.
"""
import argparse, hashlib, json, os, subprocess, time, urllib.request
from pathlib import Path
import psutil
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]

def until(predicate, seconds=20):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        value = predicate()
        if value: return value
        time.sleep(.1)
    raise AssertionError('Condition did not become true')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--art', type=Path, default=ROOT/'.artifacts/release-investigation/lifecycle')
    args = parser.parse_args(); args.art.mkdir(parents=True, exist_ok=True)
    exe = ROOT/'src-tauri/target/release/nekoafk.exe'
    report = {'exe_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(), 'cases':{}, 'limits':['Process suspension is not Windows sleep/hibernate.', 'Native command actions do not exercise the physical tray.', 'Forced process exits establish diagnostic coverage, not the historical root cause.']}
    for case in ['normal', 'renderer_termination', 'browser_termination', 'host_termination', 'resume_gap']:
        data = args.art/case; data.mkdir(exist_ok=True)
        env = dict(os.environ, NEKOAFK_DATA_DIR=str(data), WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS='--remote-debugging-port=9367')
        proc = subprocess.Popen([str(exe)], env=env)
        children = []; suspended = []
        def records():
            path = data/'diagnostics/lifecycle.jsonl'
            if not path.exists(): return []
            return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        def event(kind): return [row for row in records() if row['event']==kind]
        try:
            def endpoint():
                try: return json.load(urllib.request.urlopen('http://127.0.0.1:9367/json/version',timeout=1))
                except Exception: return None
            version = until(endpoint,40)
            until(lambda:{r['fields']['surface'] for r in event('webview_diagnostics_attached')}=={'hud','neko','telemetry','settings'})
            with sync_playwright() as p:
                browser=p.chromium.connect_over_cdp(version['webSocketDebuggerUrl'])
                pages=[pg for ctx in browser.contexts for pg in ctx.pages]
                cat=next(pg for pg in pages if 'surface=neko' in pg.url)
                expect(cat.locator('#app')).to_have_attribute('data-ready','true')
                def invoke(name, args=None): return cat.evaluate('async([c,a])=>await window.__TAURI_INTERNALS__.invoke(c,a)',[name,args or {}])
                children=psutil.Process(proc.pid).children(recursive=True)
                result={'pid':proc.pid, 'webview_version':version['Browser']}
                if case=='normal':
                    cat.evaluate("()=>{setTimeout(()=>{throw Error('PRIVATE_SENTINEL')},0);setTimeout(()=>Promise.reject('PRIVATE_SENTINEL'),10)}")
                    until(lambda:len(event('javascript_fault'))==2)
                    assert 'PRIVATE_SENTINEL' not in (data/'diagnostics/lifecycle.jsonl').read_text()
                    second=subprocess.Popen([str(exe)],env=env);second.wait(timeout=15)
                    until(lambda:event('second_instance'))
                    for _ in range(10):
                        invoke('window_action',{'action':'hide-neko'});invoke('window_action',{'action':'hide-dock'});invoke('window_action',{'action':'recover'})
                    invoke('quit_app');proc.wait(timeout=20)
                    assert proc.returncode==0 and event('quit_requested') and event('host_exit')
                    assert event('quit_requested')[-1]['fields']['origin']=='neko'
                    assert not (data/'diagnostics/active-run').exists()
                    result['js_fault_privacy_and_single_instance_and_hide_show']='passed'
                elif case=='resume_gap':
                    queue=data/'bridge/queue'
                    def evidence(kind, **fields):
                        stamp=int(time.time()*1000)
                        value={'version':1,'adapter':'opencode','id':str(time.time_ns()),'source':'resume-fixture','timestamp':stamp,'workspace':str(data),'session':'resume-session','kind':kind,**fields}
                        path=queue/f'{stamp}.tmp';path.write_text(json.dumps(value));path.replace(path.with_suffix('.json'))
                    evidence('active',operation='long-tool')
                    until(lambda:invoke('get_snapshot')['selected_state']=='active')
                    # Suspend only our native tree, resume in finally even if observation fails.
                    suspended=[psutil.Process(proc.pid)]+children
                    for child in suspended:
                        try:child.suspend()
                        except psutil.NoSuchProcess:pass
                    time.sleep(50)
                    for child in reversed(suspended):
                        try:child.resume()
                        except psutil.NoSuchProcess:pass
                    suspended=[]
                    snapshot=invoke('get_snapshot')
                    assert snapshot['selected_state']=='disconnected' and not snapshot['connected']
                    assert next(iter(snapshot['engine']['sessions'].values()))['operations']=={'long-tool':'active'}
                    evidence('heartbeat')
                    until(lambda:invoke('get_snapshot')['selected_state']=='active')
                    assert next(iter(invoke('get_snapshot')['engine']['sessions'].values()))['verification']=='not_run'
                    assert not event('webview_process_failed') and not event('rust_panic')
                    result['stale_source_expired_and_open_tool_recovered_without_success']=True
                    invoke('quit_app');proc.wait(timeout=20)
                elif case=='host_termination':
                    proc.terminate();proc.wait(timeout=15)
                    assert not event('host_exit') and (data/'diagnostics/active-run').exists()
                    result['observer_termination_exit_code']=proc.returncode
                else:
                    if case=='renderer_termination':
                        targets=[c for c in children if '--type=renderer' in c.cmdline()]
                    else:
                        pids={r['fields']['browser_pid'] for r in event('webview_diagnostics_attached')}
                        targets=[c for c in children if c.pid in pids]
                    assert targets
                    result['externally_terminated_test_children']=[c.pid for c in targets]
                    for child in targets:
                        try:child.terminate()
                        except psutil.NoSuchProcess:pass
                    until(lambda:event('webview_process_failed'))
                    if case=='browser_termination':until(lambda:event('webview_browser_exited'))
                    assert proc.poll() is None
                    result['host_survived']=True
                result['events']=records();result['result']='passed';report['cases'][case]=result
        except BaseException as error:
            report['cases'][case]={'error':str(error),'host_exit_before_cleanup':proc.poll(),'events':records()}
            raise
        finally:
            for child in reversed(suspended):
                try:child.resume()
                except psutil.Error:pass
            if proc.poll() is None:proc.terminate();proc.wait(timeout=15)
            for child in children:
                try:child.wait(timeout=3)
                except psutil.TimeoutExpired:child.terminate()
                except psutil.NoSuchProcess:pass
            (args.art/'report.json').write_text(json.dumps(report,indent=2))
        if case=='host_termination':
            # Real relaunch confirms that the marker is read; it must not be labelled "crash".
            restart=subprocess.Popen([str(exe)],env=env)
            try:
                until(lambda:len(event('host_started'))==2)
                assert event('host_started')[-1]['fields']['previous_run_incomplete'] is True
                report['cases'][case]['restart_detected_incomplete']=True
            finally:
                restart.terminate();restart.wait(timeout=15)
    (args.art/'report.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({key:value.get('result') for key,value in report['cases'].items()}))

if __name__=='__main__':main()
