import { mkdir, copyFile, readFile, readdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { setTimeout } from 'node:timers/promises';
const root = path.resolve(import.meta.dirname,'..');
const base = process.env.NEKOAFK_SMOKE_BASE || path.join(root,'.artifacts','opencode-live',String(Date.now()));
const workspace = path.join(base,'workspace'); const data = path.join(base,'data');
await mkdir(path.join(workspace,'.opencode','plugins'),{recursive:true});
await mkdir(path.join(base,'config'),{recursive:true});
await copyFile(path.join(root,'integrations','opencode','nekoafk.js'),path.join(workspace,'.opencode','plugins','nekoafk.js'));
await writeFile(path.join(workspace,'opencode.json'),JSON.stringify({enabled_providers:['neko-smoke'],model:'neko-smoke/local-test',provider:{'neko-smoke':{npm:'@ai-sdk/openai-compatible',name:'Local smoke metadata',options:{baseURL:'http://127.0.0.1:1/v1'},models:{'local-test':{name:'Local test metadata'}}}},share:'disabled',autoupdate:false}));
const exe = path.join(root,'.artifacts/opencode/node_modules/opencode-windows-x64/bin/opencode.exe');
const env = {...process.env, NEKOAFK_DATA_DIR:data, OPENCODE_CONFIG_DIR:path.join(base,'config'), XDG_CONFIG_HOME:path.join(base,'config-home'), XDG_DATA_HOME:path.join(base,'appdata'), XDG_STATE_HOME:path.join(base,'state'), XDG_CACHE_HOME:path.join(base,'cache'), OPENCODE_DISABLE_DEFAULT_PLUGINS:'true', OPENCODE_DISABLE_MODELS_FETCH:'true', OPENCODE_DISABLE_AUTOUPDATE:'true'};
const port = 14597;
const server = spawn(exe,['serve','--hostname','127.0.0.1','--port',String(port)],{cwd:workspace,env,windowsHide:true,stdio:['ignore','pipe','pipe']});
let output = ''; server.stdout.on('data',d=>output+=d);server.stderr.on('data',d=>output+=d);
async function request(route,body) {
  const response = await fetch(`http://127.0.0.1:${port}${route}`,{method:body?'POST':'GET',headers:{'content-type':'application/json','x-opencode-directory':workspace},body:body?JSON.stringify(body):undefined,signal:AbortSignal.timeout(120000)});
  if (!response.ok) throw Error(`${route}: ${response.status} ${await response.text()}`);
  return response.json();
}
try {
  let health;
  for (let i=0;i<80;i++) { try { health = await request('/global/health');break; } catch { if (server.exitCode!==null) throw Error('OpenCode server exited: '+output);await setTimeout(250); } }
  if (!health) throw Error('OpenCode server startup timed out: '+output);
  const session = await request('/session',{title:'NekoAFK live bridge smoke test'});
  const shell = await request(`/session/${session.id}/shell`,{agent:'build',command:'echo NEKOAFK_LIVE_HOOK_CHECK'});
  const nonzero = await request(`/session/${session.id}/shell`,{agent:'build',command:'exit 7'});
  await setTimeout(1000);
  const queue = path.join(data,'bridge','queue');
  const files = await readdir(queue);
  const events = await Promise.all(files.filter(f=>f.endsWith('.json')).map(async f=>JSON.parse(await readFile(path.join(queue,f),'utf8'))));
  if (!events.some(e=>e.kind==='connected')) throw Error('Real OpenCode did not load the local plugin');
  const live = events.filter(e=>e.session===session.id || !e.session && Date.now()-e.timestamp<90000);
  if (!live.some(e=>e.session===session.id)) throw Error('No real OpenCode session evidence captured');
  if (!live.some(e=>e.kind==='tool_finished')) throw Error('No real tool lifecycle evidence captured');
  const report = {health,workspace,session:session.id,event_kinds:live.map(e=>e.kind),shell_parts:shell.parts?.map(p=>({type:p.type,tool:p.tool,status:p.state?.status,exit:p.state?.metadata?.exit})),nonzero_shell_parts:nonzero.parts?.map(p=>({type:p.type,tool:p.tool,state:p.state})),model_calls:0};
  await writeFile(path.join(base,'report.json'),JSON.stringify(report,null,2));
  await writeFile(path.join(root,'.artifacts','opencode-live-report.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify(report,null,2));
} finally {
  server.kill();
  await Promise.race([new Promise(resolve=>server.once('exit',resolve)),setTimeout(5000)]);
  await writeFile(path.join(base,'server.log'),output);
}
