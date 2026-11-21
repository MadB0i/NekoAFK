import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, readdir, readFile, rm } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { NekoAFKPlugin } from '../integrations/opencode/nekoafk.js';

test('supported hooks emit sanitized, atomic evidence without leaking command or prompts', async () => {
  const dir = await mkdtemp(path.join(os.tmpdir(), 'neko-bridge-'));
  process.env.NEKOAFK_DATA_DIR = dir;
  const hooks = await NekoAFKPlugin({directory:dir});
  try {
    await hooks['chat.message']({sessionID:'session',messageID:'user-1'});
    await hooks['tool.execute.before']({tool:'bash',sessionID:'session',callID:'tool-1'}, {args:{command:'npm test --private-token=SECRET'}});
    await hooks['tool.execute.after']({tool:'bash',sessionID:'session',callID:'tool-1'}, {metadata:{exit:2},output:'SECRET SOURCE TEXT',title:'SECRET TITLE'});
    await hooks.event({event:{type:'permission.asked',properties:{id:'ask',sessionID:'session',patterns:['SECRET']}}});
    await hooks.event({event:{type:'permission.replied',properties:{requestID:'ask',sessionID:'session',reply:'once'}}});
    await hooks.event({event:{type:'todo.updated',properties:{sessionID:'session',todos:[{status:'completed',content:'SECRET'},{status:'pending'},{status:'cancelled'}]}}});
    const claim = {type:'message.updated',properties:{info:{id:'assistant-1',sessionID:'session',role:'assistant',finish:'stop',time:{completed:Date.now()},content:'SECRET'}}};
    await hooks.event({event:claim}); await hooks.event({event:claim});
    await hooks.event({event:{type:'session.idle',properties:{sessionID:'session'}}});
    const queue = path.join(dir,'bridge','queue'); const files = await readdir(queue);
    assert.ok(files.every(f=>f.endsWith('.json')));
    const bytes = await Promise.all(files.map(f=>readFile(path.join(queue,f),'utf8')));
    assert.ok(bytes.every(b=>!b.includes('SECRET')));
    const events = bytes.map(JSON.parse);
    for (const kind of ['connected','active','testing','failure','permission','permission_resolved','tasks','claimed','idle']) assert.ok(events.some(e=>e.kind===kind),kind);
    assert.equal(events.filter(e=>e.kind==='claimed').length,1);
    assert.equal(events.find(e=>e.kind==='failure').exit_code,2);
    assert.deepEqual([events.find(e=>e.kind==='tasks').completed,events.find(e=>e.kind==='tasks').total],[1,2]);
  } finally { await hooks.dispose(); delete process.env.NEKOAFK_DATA_DIR; await rm(dir,{recursive:true,force:true}); }
});

test('unknown exit metadata never becomes a passing test result', async () => {
  const dir = await mkdtemp(path.join(os.tmpdir(),'neko-bridge-')); process.env.NEKOAFK_DATA_DIR = dir;
  const hooks = await NekoAFKPlugin({directory:dir});
  try {
    await hooks['tool.execute.before']({tool:'bash',sessionID:'session',callID:'tool'}, {args:{command:'pytest'}});
    await hooks['tool.execute.after']({tool:'bash',sessionID:'session',callID:'tool'}, {metadata:{},output:'all tests passed'});
    const queue = path.join(dir,'bridge','queue'); const events = await Promise.all((await readdir(queue)).map(async f=>JSON.parse(await readFile(path.join(queue,f),'utf8'))));
    assert.equal(events.find(e=>e.kind==='tool_finished').exit_code,null);
  } finally { await hooks.dispose(); delete process.env.NEKOAFK_DATA_DIR; await rm(dir,{recursive:true,force:true}); }
});

test('heartbeat rehydrates sanitized session context and richer terminal parts keep their exit and classification', async()=>{
 const dir=await mkdtemp(path.join(os.tmpdir(),'neko-recover-'));process.env.NEKOAFK_DATA_DIR=dir;
 const real=globalThis.setInterval;let heartbeat;
 globalThis.setInterval=(fn)=>{heartbeat=fn;return real(()=>{},60000)};
 let hooks;try{hooks=await NekoAFKPlugin({directory:dir});}finally{globalThis.setInterval=real;}
 try{
  await hooks['tool.execute.before']({tool:'bash',sessionID:'s',callID:'c'},{args:{command:'pytest PRIVATE'}});
  await hooks.event({event:{type:'permission.asked',properties:{sessionID:'s',id:'p',patterns:['PRIVATE']}}});
  await heartbeat();
  await hooks['tool.execute.after']({tool:'bash',sessionID:'s',callID:'c'},{metadata:{}});
  await hooks.event({event:{type:'message.part.updated',properties:{part:{type:'tool',tool:'bash',sessionID:'s',callID:'c',state:{status:'completed',metadata:{exit:3}}}}}});
  await hooks.event({event:{type:'session.deleted',properties:{info:{id:'s'}}}});await heartbeat();
  const q=path.join(dir,'bridge/queue');const bytes=await Promise.all((await readdir(q)).map(f=>readFile(path.join(q,f),'utf8')));const events=bytes.map(JSON.parse);
  assert.ok(bytes.every(s=>!s.includes('PRIVATE')));
  const snapshot=events.find(e=>e.kind==='snapshot');assert.equal(snapshot.status,'testing');assert.deepEqual(snapshot.operations,{c:'testing'});assert.deepEqual(snapshot.requests,['p']);
  assert.equal(events.filter(e=>e.kind==='snapshot').length,1);assert.ok(events.some(e=>e.kind==='closed'));
  const failure=events.find(e=>e.kind==='failure');assert.equal(failure.exit_code,3);assert.equal(failure.testing,true);
  assert.notEqual(failure.id,events.find(e=>e.kind==='tool_finished').id);
 }finally{await hooks.dispose();delete process.env.NEKOAFK_DATA_DIR;await rm(dir,{recursive:true,force:true});}
});

test('reasoning and assistant text are observable types, while user text and unknown work stay unclassified', async () => {
 const dir=await mkdtemp(path.join(os.tmpdir(),'neko-parts-'));process.env.NEKOAFK_DATA_DIR=dir;
 const hooks=await NekoAFKPlugin({directory:dir});
 try {
  await hooks.event({event:{type:'message.updated',properties:{info:{id:'u',sessionID:'s',role:'user'}}}});
  await hooks.event({event:{type:'message.part.updated',properties:{part:{id:'ut',type:'text',messageID:'u',sessionID:'s',text:'PRIVATE USER'}}}});
  await hooks.event({event:{type:'message.updated',properties:{info:{id:'a',sessionID:'s',role:'assistant'}}}});
  await hooks.event({event:{type:'message.part.updated',properties:{part:{id:'r',type:'reasoning',messageID:'a',sessionID:'s',text:'PRIVATE REASONING'}}}});
  await hooks.event({event:{type:'message.part.updated',properties:{part:{id:'t',type:'text',messageID:'a',sessionID:'s',text:'PRIVATE ANSWER'}}}});
  for(let i=0;i<100;i++)await hooks.event({event:{type:'message.part.delta',properties:{sessionID:'s',partID:'t',delta:'PRIVATE DELTA'}}});
  await hooks['tool.execute.before']({sessionID:'s',tool:'bash',callID:'b'},{args:{command:'cargo build'}});
  const q=path.join(dir,'bridge/queue');const bytes=await Promise.all((await readdir(q)).map(f=>readFile(path.join(q,f),'utf8')));
  assert.ok(bytes.every(s=>!s.includes('PRIVATE')));
  const events=bytes.map(JSON.parse);
  assert.equal(events.filter(e=>e.kind==='planning').length,1);
  assert.equal(events.filter(e=>e.kind==='writing').length,1);
  assert.ok(events.some(e=>e.kind==='building'));
 } finally {await hooks.dispose();delete process.env.NEKOAFK_DATA_DIR;await rm(dir,{recursive:true,force:true});}
});
