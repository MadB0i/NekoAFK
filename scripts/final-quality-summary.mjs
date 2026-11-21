import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
const root=path.resolve(import.meta.dirname,'..'),dir=path.join(root,'.artifacts/final-quality');
const read=(name)=>{const file=path.join(dir,name);return fs.existsSync(file)?JSON.parse(fs.readFileSync(file,'utf8').replace(/^\uFEFF/,'')):null;};
const median=values=>{const v=[...values].sort((a,b)=>a-b);return v.length?+(v.length%2?v[(v.length-1)/2]:(v[v.length/2-1]+v[v.length/2])/2).toFixed(3):null;};
const range=v=>({median:median(v),min:Math.min(...v),max:Math.max(...v)});
function phase(report,name){
 const samples=report?.runs.map(r=>r.phases[name]).filter(Boolean)||[];
 if(!samples.length)return null;
 return {repeats:samples.length,cpu_one_core:range(samples.map(s=>s.cpu_one_core)),
  raf_per_second:range(samples.map(s=>+(s.raf_count/s.seconds).toFixed(3))),
  pose_mutations:range(samples.map(s=>s.pose_mutations)),
  median_of_run_p95_pose_interval_ms:median(samples.map(s=>s.pose_intervals_ms.p95).filter(Number.isFinite)),
  cpu_by_kind_median:Object.fromEntries([...new Set(samples.flatMap(s=>Object.keys(s.cpu_by_kind)))].map(k=>[k,median(samples.map(s=>s.cpu_by_kind[k]||0))])),
  private_end_mib:range(samples.map(s=>s.private_end_mib)),
  processes_changed:samples.some(s=>s.processes_appeared.length||s.processes_retired.length),
  long_tasks:samples.reduce((n,s)=>n+s.long_tasks_ms.length,0),
  activities:samples.map(s=>s.activities)};
}
const before=read('seeded-before-profile.json'),after=read('seeded-final-profile.json');
const comparisons=['idle','writing','event_flood','long_tool','hidden','reduced_motion'].map(name=>({workload:name,before:phase(before,name),final:phase(after,name)}));
const soak=read('soak-report.json'),quiet=read('quiet-report.json');
const allocation=read('seeded-final-allocations.json')?.profile;
const allocationRows=[];
function collectAllocation(node){allocationRows.push({function:node.callFrame.functionName,url:node.callFrame.url,line_zero_based:node.callFrame.lineNumber,sampled_bytes:node.selfSize});node.children.forEach(collectAllocation);}
if(allocation)collectAllocation(allocation.head);
const result={recommendation:'NO-GO for a release candidate until outstanding stability, human, hardware and resource gates are met.',
 current_exe_sha256:createHash('sha256').update(fs.readFileSync(path.join(root,'src-tauri/target/release/nekoafk.exe'))).digest('hex'),
 baseline_exe_sha256:before?.exe_sha256,measured_final_sha256:after?.exe_sha256,
 method:'Three fresh-process repeats, same ordered native workloads/settings and existing constructor seed 1234 via temporary CDP breakpoint. Debugger disabled before measurement. Actual event delivery/timer jitter and clip mixtures recorded. CPU is app + observed descendants, percent of one core; external producers excluded. Endpoint sampling can omit short-lived children; the soak is not full lifetime accounting for verification commands.',
 limits:['The paired performance candidate is 03f031a7; the later cfb8af25 build adds only the claim-first snapshot correctness fix and is covered by final native/quiet/soak validation.','CPU ranges overlap and graphics cost varies; no universal reduction is claimed.','Run p95 medians are not pooled quantiles or GPU presentation measurements.','Writing 35 seconds includes authored rests; the separate 14-second comparison stays on keyboard.','Short phase-end memory is not leak evidence.','Rejected deadline prototype is preserved separately and is not the final executable.','The original paired profiles used an invalid async polling predicate after the timed flood. Their actual counter snapshots are preserved (493–500), not complete-delivery proof. The corrected soak requires exactly 500 drained results per cycle.','Pose interval quantiles exclude gaps of 100 ms or more (including authored holds); they do not characterize all stalls.'],
 comparisons,typing_only:{before:phase(read('typing-before-profile.json'),'typing_only'),final:phase(read('typing-final-profile.json'),'typing_only'),rejected:phase(read('rejected-clock-profile.json'),'typing_only')},
 environment:read('environment.json'),
 repeated_workload_integrity:{before:before?.runs.map(r=>({repeat:r.repeat,duplicates:r.duplicate_terminal_integrity,errors:r.errors})),final:after?.runs.map(r=>({repeat:r.repeat,duplicates:r.duplicate_terminal_integrity,errors:r.errors}))},
 diagnostics:{trace:after?.runs[0]?.diagnostic_trace,allocation:allocation?{separate_from_comparable_cpu:true,includes_collected_objects:true,estimated_sampled_bytes:allocationRows.reduce((s,r)=>s+r.sampled_bytes,0),samples:allocation.samples.length,top:allocationRows.sort((a,b)=>b.sampled_bytes-a.sampled_bytes).slice(0,10)}:null},
 tests:{rust:Number(fs.readFileSync(path.join(dir,'rust-tests.log'),'utf8').match(/test result: ok\. (\d+) passed/)[1]),javascript:Number(fs.readFileSync(path.join(dir,'javascript-tests.log'),'utf8').match(/tests (\d+)/)[1]),polling_harness:{count:Number(fs.readFileSync(path.join(dir,'harness-tests.log'),'utf8').match(/Ran (\d+) tests/)[1]),passed:/\bOK\b/.test(fs.readFileSync(path.join(dir,'harness-tests.log'),'utf8'))}},
 native_suite_build:read('native-suite-build.json'),native_desktop:read('native-desktop.json'),full_desktop:read('native-smoke-report.json'),character:read('character/native-acceptance.json'),character_preservation:read('character-preservation.json'),
 soak_history:['pre-heartbeat-fix/soak-report.json','target-closed-soak/soak-report.json','startup-timeout-soak/soak-report.json'].map(file=>{const r=read(file);return r?{file,exe_sha256:r.exe_sha256,completed:!!r.resources&&!r.errors.length,seconds:r.resources?.seconds??r.samples.at(-1)?.seconds,errors:r.errors,processes_at_failure:r.processes_at_failure}:null;}).filter(Boolean),
 quiet_followup:quiet?{exe_sha256:quiet.exe_sha256,complete:!!quiet.resources&&quiet.resources.seconds>=quiet.seconds_requested&&!quiet.errors.length&&Object.values(quiet.checks).every(v=>v==='passed'),resources:quiet.resources,checks:quiet.checks,errors:quiet.errors,unexplained_full_motion_gap_count:quiet.unexplained_full_motion_gaps.length,context_counts:quiet.samples.reduce((counts,s)=>{const key=JSON.stringify([s.motion,s.hidden,s.desktop_paused]);counts[key]=(counts[key]||0)+1;return counts;},{})}:null,
 soak:soak?{exe_sha256:soak.exe_sha256,complete:!!soak.resources&&soak.resources.seconds>=soak.seconds_requested&&!soak.errors.length&&Object.values(soak.checks).every(v=>v==='passed'),unexplained_full_motion_gap_count:soak.unexplained_full_motion_gaps?.length,max_full_visible_callback_gap_ms:Math.max(0,...soak.samples.filter(s=>s.motion==='full'&&!s.document_hidden&&!s.desktop_paused).map(s=>s.last_frame_gap_ms||0)),resources:soak.resources,checks:soak.checks,errors:soak.errors,protocol_events:soak.protocol_events,opencode_version:soak.opencode_version,model_requests:soak.model_requests,duplicate_terminal_counts:soak.duplicate_terminal_snapshots?.map(s=>({tests_passed:s.tests_passed,open_operations:Object.keys(s.operations).length}))}:null};
fs.writeFileSync(path.join(dir,'summary.json'),JSON.stringify(result,null,2));
const rows=comparisons.filter(r=>r.before&&r.final).map(r=>`| ${r.workload} | ${r.before.cpu_one_core.median}% (${r.before.cpu_one_core.min}–${r.before.cpu_one_core.max}) | ${r.final.cpu_one_core.median}% (${r.final.cpu_one_core.min}–${r.final.cpu_one_core.max}) |`);
fs.writeFileSync(path.join(dir,'performance-table.md'),['CPU: median and min–max across three native runs, percent of one core.','', '| Workload | Before | Final |','|---|---:|---:|',...rows,'','Writing includes authored rests. See summary.json for the same-keyboard comparison, frame cadence, process-kind CPU, private memory and limitations.'].join('\n'));
console.log('Wrote .artifacts/final-quality/summary.json and performance-table.md');
