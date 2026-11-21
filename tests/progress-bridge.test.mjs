import {test} from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,readdir,readFile,rm} from 'node:fs/promises';
import os from 'node:os';import path from 'node:path';
import {NekoAFKPlugin} from '../integrations/opencode/nekoafk.js';

test('plan replacement, reopened steps and invalid data never become invented progress',async()=>{
 const dir=await mkdtemp(path.join(os.tmpdir(),'neko-plan-'));process.env.NEKOAFK_DATA_DIR=dir;
 const hooks=await NekoAFKPlugin({directory:dir});
 try {
  for(const statuses of [['completed','pending','cancelled'],['completed','completed'],['pending','completed','in_progress'],[],['unexpected']]) {
   await hooks.event({event:{type:'todo.updated',properties:{sessionID:'one',todos:statuses.map(status=>({status,content:'PRIVATE TASK DETAILS',priority:'high'}))}}});
  }
  await hooks.dispose();const queue=path.join(dir,'bridge/queue');const bytes=await Promise.all((await readdir(queue)).map(f=>readFile(path.join(queue,f),'utf8')));
  assert.ok(bytes.every(s=>!s.includes('PRIVATE')));
  assert.deepEqual(bytes.map(JSON.parse).filter(e=>e.kind==='tasks').map(e=>[e.completed,e.total]),[[1,2],[2,2],[1,3],[0,0],[null,null]]);
 }finally{await hooks.dispose();delete process.env.NEKOAFK_DATA_DIR;await rm(dir,{recursive:true,force:true});}
});

test('recovery retains bounded tool labels and observed start while explicit abort stays inconclusive',async()=>{
 const dir=await mkdtemp(path.join(os.tmpdir(),'neko-progress-'));process.env.NEKOAFK_DATA_DIR=dir;
 const original=globalThis.setInterval;let heartbeat;
 globalThis.setInterval=fn=>{heartbeat=fn;return original(()=>{},60000)};
 let hooks;try{hooks=await NekoAFKPlugin({directory:dir});}finally{globalThis.setInterval=original;}
 try {
  await hooks['tool.execute.before']({tool:'constructor',sessionID:'one',callID:'operation'},{args:{command:'PRIVATE COMMAND'}});await heartbeat();
  await hooks.event({event:{type:'session.error',properties:{sessionID:'one',error:{name:'MessageAbortedError',data:{message:'PRIVATE ERROR'}}}}});
  await hooks['tool.execute.after']({tool:'constructor',sessionID:'one',callID:'operation'},{metadata:{exit:0}});
  await hooks.event({event:{type:'session.idle',properties:{sessionID:'one'}}});await heartbeat();await hooks.dispose();
  const q=path.join(dir,'bridge/queue');const bytes=await Promise.all((await readdir(q)).map(f=>readFile(path.join(q,f),'utf8')));assert.ok(bytes.every(s=>!s.includes('PRIVATE')));
  const events=bytes.map(JSON.parse);const snapshots=events.filter(e=>e.kind==='snapshot');
  assert.equal(snapshots[0].tool_details.operation.label,'Tool');assert.equal(snapshots[0].tool_details.operation.started_at,events.find(e=>e.operation==='operation').timestamp);
  assert.equal(snapshots[1].status,'inconclusive');assert.equal(snapshots[1].outcome,'interrupted');assert.deepEqual(snapshots[1].operations,{});assert.deepEqual(snapshots[1].tool_details,{});
  assert.equal(events.filter(e=>e.kind==='failure').length,0);
 }finally{await hooks.dispose();delete process.env.NEKOAFK_DATA_DIR;await rm(dir,{recursive:true,force:true});}
});
