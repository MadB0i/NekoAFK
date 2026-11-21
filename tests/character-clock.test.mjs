import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import ts from 'typescript';
const transpile=source=>ts.transpileModule(source,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ES2022}}).outputText;
const data=source=>'data:text/javascript;base64,'+Buffer.from(source).toString('base64');
const director=data(transpile(await readFile(new URL('../src/director.ts',import.meta.url),'utf8')));
const character=transpile(await readFile(process.env.NEKO_CHARACTER_SOURCE_FILE||new URL('../src/character.ts',import.meta.url),'utf8')).replace("'./director'",JSON.stringify(director));
const {Character}=await import(data(character));
test('native frame timestamps cannot rewind observations while RAF paint deadlines stay intact',()=>{
 const saved=Object.fromEntries(['performance','window','matchMedia','requestAnimationFrame','cancelAnimationFrame','clearTimeout'].map(k=>[k,Object.getOwnPropertyDescriptor(globalThis,k)]));
 let clock=100,next=1,callback;const app={dataset:{}};const part={};
 const root={querySelector:()=>part,querySelectorAll:()=>[],closest:()=>app};
 try{
  Object.defineProperty(globalThis,'performance',{configurable:true,value:{now:()=>clock}});
  globalThis.window={setTimeout:()=>next++};globalThis.clearTimeout=()=>{};
  globalThis.matchMedia=()=>({matches:false,addEventListener:()=>{}});
  globalThis.requestAnimationFrame=cb=>{callback=cb;return next++};globalThis.cancelAnimationFrame=()=>{};
  const c=new Character(root,1234);let paints=0;c.paint=()=>paints++;
  c.observe('writing',0,'work','playful',false,true);
  clock=107;callback(100);assert.equal(c.previousTime,107);assert.equal(paints,1);
  clock=131;c.observe('writing',0,'work','playful',false,true);
  clock=135;callback(128); // Keep the established RAF paint deadline despite execution lag.
  assert.equal(c.previousTime,135);assert.equal(paints,1);
  clock=142;callback(135);assert.equal(paints,2);
  assert.ok(Math.abs(c.elapsed-.042)<1e-9,c.elapsed);
 }finally{
  for(const [key,descriptor] of Object.entries(saved))if(descriptor)Object.defineProperty(globalThis,key,descriptor);else delete globalThis[key];
 }
});
