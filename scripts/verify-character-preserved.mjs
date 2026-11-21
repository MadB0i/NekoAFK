// Compare the engineering candidate to the explicitly preserved Astra baseline.
import {readFile,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
import ts from 'typescript';
const root=new URL('../',import.meta.url),base=new URL('.artifacts/engineering/baseline/',root);
const moduleOf=async url=>import('data:text/javascript;base64,'+Buffer.from(ts.transpileModule(await readFile(url,'utf8'),{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ES2022}}).outputText).toString('base64'));
const [before,after]=await Promise.all([moduleOf(new URL('director.ts',base)),moduleOf(new URL('src/director.ts',root))]);
assert.deepEqual(after.library,before.library,'Authored performances changed');
const hash=async url=>createHash('sha256').update(await readFile(url)).digest('hex');
const artwork=await hash(new URL('assets/cat.svg',root));assert.equal(artwork,await hash(new URL('cat.svg',base)));
const clips=Object.values(after.library).flat().filter((c,i,all)=>all.findIndex(a=>a.id===c.id)===i);
for(const clip of clips)for(let t=0;t<=clip.duration;t+=1/60)assert.deepEqual(after.sample(clip,t),before.sample(clip,t));
const report={artwork_sha256:artwork,authored_performances_unchanged:true,sampled_at_hz:60,performances:clips.map(c=>({id:c.id,duration:c.duration})),baseline_exe_sha256:await hash(new URL('nekoafk.exe',base)),candidate_exe_sha256:await hash(new URL('src-tauri/target/release/nekoafk.exe',root))};
await writeFile(new URL('.artifacts/engineering/character-preservation.json',root),JSON.stringify(report,null,2));console.log('Original artwork and all 12 authored performances are unchanged.');
