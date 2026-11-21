"""Attach after living_cat_native.py --keep-open; exercise a native event burst."""
import json
import os
from pathlib import Path
import subprocess
import argparse
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'.artifacts/living-cat'
parser=argparse.ArgumentParser();parser.add_argument('--art',type=Path,default=ART);ART=parser.parse_args().art
report=json.loads((ART/'report.json').read_text())
env=dict(os.environ,NEKOAFK_DATA_DIR=report['data_dir'])
with sync_playwright() as p:
    browser=p.chromium.connect_over_cdp('http://127.0.0.1:9341')
    pages=[pg for c in browser.contexts for pg in c.pages]
    neko=next(pg for pg in pages if 'surface=neko' in pg.url)
    dock=next(pg for pg in pages if 'surface=telemetry' in pg.url)
    def invoke(c,a=None):return dock.evaluate('async([c,a])=>await window.__TAURI_INTERNALS__.invoke(c,a)',[c,a or {}])
    subprocess.run(['node',str(ROOT/'tests/emit-fixture.mjs'),str(ART/'workspace'),'rapid'],env=env,check=True,capture_output=True)
    for pg in [neko,dock]:expect(pg.locator('#app')).to_have_attribute('data-state','permission',timeout=15000)
    expect(neko.locator('#mascot')).to_have_attribute('data-activity',__import__('re').compile('beckon|listen|rest'))
    report['checks']['62_event_native_burst_and_permission_priority']='passed'
    s=invoke('get_snapshot')['settings'];s['reduced_motion']=True;invoke('save_settings',{'settings':s})
    expect(neko.locator('#app')).to_have_attribute('data-motion','reduced')
    event_id=dock.evaluate('''async()=>{
      window.snapshotCount=0;
      return await window.__TAURI_INTERNALS__.invoke('plugin:event|listen',{
        event:'neko:snapshot',target:{kind:'Any'},
        handler:window.__TAURI_INTERNALS__.transformCallback(()=>window.snapshotCount++)});
    }''')
    neko.evaluate('window.rigMutations=0;window.rigObserver=new MutationObserver(m=>window.rigMutations+=m.length);window.rigObserver.observe(document.querySelector("#rig"),{attributes:true,childList:true,subtree:true})')
    neko.wait_for_timeout(1500) # Sample across several native snapshot publications.
    mutations=neko.evaluate('window.rigObserver.disconnect();window.rigMutations')
    assert mutations==0,mutations
    snapshots=dock.evaluate('window.snapshotCount')
    assert snapshots==0,snapshots
    dock.evaluate('async id=>await window.__TAURI_INTERNALS__.invoke("plugin:event|unlisten",{event:"neko:snapshot",eventId:id})',event_id)
    report['checks']['unchanged_still_pose_has_zero_svg_mutations']='passed'
    report['checks']['unchanged_host_snapshot_has_zero_broadcasts']='passed'
    s['reduced_motion']=False;invoke('save_settings',{'settings':s})
    subprocess.run(['node',str(ROOT/'tests/emit-fixture.mjs'),str(ART/'workspace'),'resolved'],env=env,check=True,capture_output=True)
    for pg in [neko,dock]:expect(pg.locator('#app')).to_have_attribute('data-state','editing',timeout=15000)
    (ART/'report.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({'rapid_native':'passed','unchanged_svg_mutations':mutations}))
    browser.close()
