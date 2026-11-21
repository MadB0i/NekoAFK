import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import ts from 'typescript';
const source = await readFile(new URL('../src/director.ts', import.meta.url),'utf8');
const code = ts.transpileModule(source,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ES2022}}).outputText;
const {Director,library,sample,moodFor} = await import('data:text/javascript;base64,'+Buffer.from(code).toString('base64'));

test('quiet scheduling sleeps only across unchanged settled poses and wakes for blinks and interrupts',()=>{
 const d=new Director(384);let sleeps=0;
 for(let t=0;t<600;t+=1/30){
  const before=d.tick(t),delay=d.quietDelay(t);
  if(delay>.05){
   assert.equal(before.activity,'rest');
   assert.deepEqual(d.frame(t+delay/2).pose,before.pose);
   assert.ok(delay<26);sleeps++;
  } else assert.ok(delay>=0);
 }
 assert.ok(sleeps>100);
 d.observe('permission',0,'new-request',601);assert.equal(d.quietDelay(601),0);
});

test('seeded 2-hour run is reproducible, finite and does not repeat adjacent activities',()=>{
 const run=()=>{const d=new Director(1234),sequence=[];let prev='';
  for(let t=0;t<7200;t+=.1){const f=d.tick(t);assert.ok(Object.values(f.pose).every(Number.isFinite));
   if(f.activity!=='rest'&&f.activity!==prev){sequence.push(f.activity);prev=f.activity;}
  }return sequence;};
 const one=run();assert.deepEqual(one,run());assert.ok(one.length>100);assert.equal(new Set(one).size,4);
});
test('permission interrupts work immediately and transitions begin from the previous pose',()=>{
 const d=new Director(8);d.observe('editing',0,'s:1',0);d.tick(3);
 const before=d.frame(3).pose;d.observe('permission',0,'s:2',3);
 assert.equal(d.frame(3).mood,'permission');assert.deepEqual(d.frame(3).pose,before);
 const after=d.tick(4);assert.ok(['beckon','listen'].includes(after.activity));
 d.observe('editing',0,'s:3',4);assert.equal(d.tick(4.7).mood,'writing');
});
test('unverified completion, disconnect and failed states never play victory',()=>{
 for(const state of ['claimed','inconclusive','disconnected','inactive','failed']){
  const d=new Director(5);d.observe(state,3,'s:1',0);
  for(let t=0;t<120;t+=.25)assert.ok(!['delight'].includes(d.tick(t).activity));
 }
 assert.equal(moodFor('active'),'busy');assert.equal(moodFor('failed',1),'failed');assert.equal(moodFor('failed',2),'irritated');
});
test('verified success celebrates once per evidence token, then returns to happy idle',()=>{
 const d=new Director(7);d.observe('verified',0,'s:9',0);let celebrations=0,prior='';
 for(let t=0;t<180;t+=.1){d.observe('verified',0,'s:9',t);const f=d.tick(t);
  if(['delight'].includes(f.activity)&&f.activity!==prior)celebrations++;
  prior=f.activity;
 }assert.equal(celebrations,1);
 d.observe('editing',0,'s:10',180);d.tick(181);d.observe('verified',0,'s:11',181);
 assert.ok(['delight'].includes(d.tick(182).activity));
});
test('rapid changes settle on newest factual state and hold pending permission',()=>{
 const d=new Director(44);const states=['editing','testing','failed','active','permission'];
 for(let i=0;i<500;i++) {const s=states[i%5];d.observe(s,i%3,'s:'+i,i*.03);d.tick(i*.03);}
 d.observe('permission',3,'last',15);assert.equal(d.tick(16).mood,'permission');
 assert.equal(d.tick(45).mood,'permission');
});

test('fresh verified tasks can each celebrate, while revisiting an old session cannot replay victory',()=>{
 const d=new Director(7);
 for(let i=0;i<4;i++){
  const at=i*30;d.observe('editing',0,'work:'+i,at);d.tick(at+1);
  d.observe('verified',0,'proof:'+i,at+2);
  assert.ok(['delight'].includes(d.tick(at+3).activity));d.tick(at+20);
 }
 d.observe('editing',0,'other',121);d.tick(122);d.observe('verified',0,'proof:0',123);
 assert.ok(!['delight'].includes(d.tick(124).activity));
});
test('personalities change rest intervals while every authored performance has finite poses',()=>{
 const counts=[];for(const personality of ['calm','playful','chaos']){
  const d=new Director(123);d.personality=personality;let count=0,prev='';
  for(let t=0;t<600;t+=.1){const f=d.tick(t);if(f.activity!=='rest'&&f.activity!==prev){count++;prev=f.activity;}}
  counts.push(count);
 }assert.ok(counts[0]<counts[1]&&counts[1]<=counts[2],counts.join(','));
 for(const activities of Object.values(library))for(const a of activities){
  assert.ok(a.duration>=5.5);for(let t=0;t<=a.duration;t+=.03)assert.ok(Object.values(sample(a,t)).every(Number.isFinite),a.id);
 }
});
test('cooldowns prevent rapid re-entry from repeatedly playing an urgent reaction',()=>{
 const d=new Director(91);const starts=[];
 for(let i=0;i<20;i++){
  d.observe('failed',0,'s:'+i,i*2);const f=d.tick(i*2+.7);
  if(f.activity!=='rest')starts.push([f.activity,i*2]);
  d.observe('active',0,'b:'+i,i*2+1);d.tick(i*2+1.8);
 }
 for(let i=0;i<starts.length;i++)for(let j=i+1;j<starts.length;j++)if(starts[i][0]===starts[j][0])assert.ok(starts[j][1]-starts[i][1]>=29);
});

test('held hand and prop channels survive a later head-only acting key',()=>{
 const keyboard=library.writing.find(a=>a.id==='keyboard');
 const p=sample(keyboard,6.65);
 assert.equal(p.prop,1);
 assert.equal(p.lx,9);
 assert.equal(p.ly,0);
 assert.equal(p.ry,-10);
});

test('an interrupt during a blink preserves the exact visible starting pose',()=>{
 const d=new Director(21);d.observe('editing',0,'work',0);
 let at=0;
 for(;at<30;at+=1/60){if(d.tick(at).pose.eyes<.2)break;}
 assert.ok(at<30);
 const before=d.frame(at).pose;d.observe('permission',0,'permission',at);
 assert.deepEqual(d.frame(at).pose,before);
 assert.equal(d.tick(at+.6).mood,'permission');
});

test('authored hands stay within a connected limb reach and return to rest',()=>{
 const clips=[...new Map(Object.values(library).flat().map(a=>[a.id,a])).values()];
 assert.equal(clips.length,12);
 for(const a of clips){
  for(let t=0;t<a.duration;t+=1/60){
   const p=sample(a,t);
   for(const [dx,dy] of [[p.lx+3,p.ly+35],[p.rx-3,p.ry+35]])assert.ok(Math.hypot(dx,dy)<100,`${a.id} ${t}`);
   assert.ok(p.eyes>=0&&p.eyes<=1.15);
  }
  const last=sample(a,a.duration);assert.equal(last.lx,0);assert.equal(last.rx,0);assert.equal(last.prop,0);
 }
});

test('quiet attention changes are finite, restrained and sleep between gestures',()=>{
 const d=new Director(1234);const attention=new Set();let heldFrames=0,sleepFrames=0;
 for(let t=0;t<240;t+=1/60){
  const f=d.tick(t);
  if(f.activity==='rest'){
   heldFrames++;assert.ok(Math.abs(f.pose.gazeX)<=5&&Math.abs(f.pose.head)<3);
   if(d.quietDelay(t)>.1){sleepFrames++;attention.add(f.pose.gazeX.toFixed(2));assert.deepEqual(f.pose,d.frame(t+.05).pose);}
  }
 }
 assert.ok(attention.size>=3,[...attention].join(','));
 assert.ok(sleepFrames>heldFrames*.65,`${sleepFrames}/${heldFrames}`);
});

test('urgent interruption inherits quiet attention without snapping and reduced motion stays static',()=>{
 const d=new Director(1234);let at=0;
 for(;at<240;at+=1/60){const f=d.tick(at);if(f.activity==='rest'&&Math.abs(f.pose.gazeX)>1&&d.quietDelay(at)>.1)break;}
 assert.ok(at<240);const before=d.frame(at).pose;
 d.observe('permission',0,'attention-needed',at);assert.deepEqual(d.frame(at).pose,before);
 assert.equal(d.tick(at+.7).mood,'permission');
 const still=d.still();d.tick(at+2);assert.deepEqual(d.still(),still);
});
