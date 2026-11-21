"""Summarize matched native HUD/baseline measurements; no optimization claims."""
import json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];ART=ROOT/'.artifacts/live-progress'
before=json.loads((ART/'before-profile/report.json').read_text());after=json.loads((ART/'after-profile/report.json').read_text())
result={'before_sha256':before['exe_sha256'],'after_sha256':after['exe_sha256'],'cpu_unit':'percent of one core, native host and descendant processes','repeats':3,'phases':{},'limits':['Same harness, seed, geometry and durations; sequential runs, ambient desktop load is not experimentally controlled.','Pose mutation intervals under 100 ms exclude deliberate quiet gaps and are not GPU presentation times.','USS is endpoint process-tree private memory, not allocation profiling.']}
for phase in before['runs'][0]['phases']:
 row={}
 for label,report in [('before',before),('after',after)]:
  samples=[r['phases'][phase] for r in report['runs']];assert len(samples)==3
  cpu=[s['cpu_one_core'] for s in samples];memory=[s['uss_mib'] for s in samples]
  row[label]={'cpu_median':round(statistics.median(cpu),2),'cpu_range':[round(min(cpu),2),round(max(cpu),2)],'private_mib_median':round(statistics.median(memory),2),'mutation_p95_ms':[s['intervals_under_100ms'].get('p95') for s in samples],'frames':[s['frames'] for s in samples],'errors':[r['errors'] for r in report['runs']]}
 row['cpu_median_delta']=round(row['after']['cpu_median']-row['before']['cpu_median'],2)
 row['private_mib_median_delta']=round(row['after']['private_mib_median']-row['before']['private_mib_median'],2)
 result['phases'][phase]=row
(ART/'performance-comparison.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
