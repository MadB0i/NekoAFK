"""Serial current native acceptance suites, with per-suite logs and build identity."""
import argparse,hashlib,json,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'.artifacts/live-progress'
commands=[
 ('hud',['python','tests/progress_native.py']),
 ('smoke',['python','tests/native_smoke.py']),
 ('desktop',['python','tests/engineering_native.py']),
 ('experience',['python','tests/experience_native.py','--mode','ux','--art',str(ART/'experience-ux')]),
 ('character',['python','tests/character_native.py','--soak','180','--continuous','--art',str(ART/'character')]),
 ('opencode',['python','tests/opencode_live_desktop.py','--extended']),
 ('lifecycle',['python','tests/lifecycle_native.py','--art',str(ART/'lifecycle')]),
 ('soak',['python','tests/quality_soak.py','--seconds','300','--art',str(ART/'soak')]),
 ('wait-helper',['python','tests/quality_wait_test.py']),
]
parser=argparse.ArgumentParser();parser.add_argument('--from-suite',default='hud');args=parser.parse_args()
commands=commands[next(i for i,(name,_) in enumerate(commands) if name==args.from_suite):]
report={'exe_sha256':hashlib.sha256((ROOT/'src-tauri/target/release/nekoafk.exe').read_bytes()).hexdigest(),'suites':[]}
if args.from_suite!='hud' and (ART/'suite-manifest.json').exists():
 old=json.loads((ART/'suite-manifest.json').read_text())
 assert old['exe_sha256']==report['exe_sha256']
 report['suites']=[s for s in old['suites'] if s['exit_code']==0 and s['name'] not in [n for n,_ in commands]]
for name,command in commands:
 print('START '+name,flush=True);started=time.monotonic()
 with open(ART/(name+'-suite.log'),'w',encoding='utf-8') as log:
  result=subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
 report['suites'].append({'name':name,'command':command,'exit_code':result.returncode,'seconds':round(time.monotonic()-started,2)})
 (ART/'suite-manifest.json').write_text(json.dumps(report,indent=2))
 print('END '+name+' '+str(result.returncode),flush=True)
 if result.returncode:raise SystemExit(result.returncode)
