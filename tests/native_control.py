"""Local test-only IPC helper for isolated native acceptance windows."""
import argparse,json
from playwright.sync_api import sync_playwright
p=argparse.ArgumentParser();p.add_argument('command',nargs='?',default='desktop_diagnostics');p.add_argument('--port',type=int,default=9356);p.add_argument('--args',default='{}');p.add_argument('--probe',action='store_true');p.add_argument('--inputs',action='store_true');a=p.parse_args()
with sync_playwright() as pw:
 b=pw.chromium.connect_over_cdp(f'http://127.0.0.1:{a.port}')
 page=next(pg for c in b.contexts for pg in c.pages if 'surface=telemetry' in pg.url)
 if a.probe:
  for pg in b.contexts[0].pages:pg.evaluate("() => {window.nativeInputs=[];for(const kind of ['pointerdown','mousedown','pointerup','mouseup'])document.addEventListener(kind,e=>window.nativeInputs.push({kind,x:e.clientX,y:e.clientY,at:performance.now(),target:e.target.id||e.target.tagName}),true)}")
 elif a.inputs:
  print(json.dumps({pg.url:pg.evaluate('window.nativeInputs') for pg in b.contexts[0].pages},indent=2))
 else:print(json.dumps(page.evaluate('async([c,a])=>await window.__TAURI_INTERNALS__.invoke(c,a)',[a.command,json.loads(a.args)]),indent=2))
 b.close()
