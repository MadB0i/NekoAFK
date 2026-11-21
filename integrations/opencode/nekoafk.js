import { mkdir, readdir, rename, unlink, writeFile } from 'node:fs/promises';
import { randomUUID } from 'node:crypto';
import path from 'node:path';
import os from 'node:os';

// This module uses only supported OpenCode plugin hooks. It never changes tools.
export const NekoAFKPlugin = async ({ directory, client }) => {
  const base = process.env.NEKOAFK_DATA_DIR || path.join(process.env.LOCALAPPDATA || path.join(os.homedir(), '.local', 'share'), 'com.nekoafk.desktop');
  const queue = path.join(base, 'bridge', 'queue');
  const source = randomUUID();
  let chain = Promise.resolve(), sequence = 0, closed = false;
  const completedMessages = new Set();
  const lastToolKind = new Map();
  const roles = new Map();
  const parts = new Map();
  const activityAt = new Map();
  const sessions = new Map();
  const interruptedTools = new Set();
  const toolLabel = tool => { const labels={bash:'Shell',shell:'Shell',edit:'File edit',write:'File edit',apply_patch:'File edit',patch:'File edit',multiedit:'File edit',read:'File read',glob:'File search',grep:'File search',webfetch:'Web lookup',websearch:'Web lookup',todowrite:'Plan update',todoread:'Plan update',task:'Subagent'};return Object.hasOwn(labels,tool)?labels[tool]:'Tool'; };
  function remember(kind, session, fields, timestamp) {
    if (!session || ['heartbeat','snapshot','connected','disconnected'].includes(kind)) return;
    let s=sessions.get(session);
    if (!s) { s={status:'idle',observed_at:timestamp,operations:{},tool_details:{},requests:[],completed:null,total:null,outcome:null};sessions.set(session,s); }
    s.observed_at=timestamp;
    if (fields.operation) {
      if (['tool_finished','failure'].includes(kind)) { delete s.operations[fields.operation]; delete s.tool_details[fields.operation]; }
      else if (Object.keys(s.operations).length<128) { s.operations[fields.operation]=kind; s.tool_details[fields.operation] ||= {label:toolLabel(fields.tool),started_at:timestamp}; }
    }
    if (['active','editing','testing','planning','writing','building','busy','idle','claimed','failure'].includes(kind)) s.status=kind==='busy'?'active':kind==='failure'?'failed':kind;
    if (['active','editing','testing','planning','writing','building','busy'].includes(kind)) s.outcome=null;
    if (kind==='tool_finished') { s.status='active';s.outcome=fields.exit_code===0?'reported_pass':'unknown'; }
    if (kind==='failure') s.outcome='failed';
    if (kind==='interrupted') {
      for(const operation of Object.keys(s.operations)) interruptedTools.add(`${session}:${operation}`);
      while(interruptedTools.size>1000)interruptedTools.delete(interruptedTools.values().next().value);
      s.status='inconclusive';s.outcome='interrupted';s.operations={};s.tool_details={};s.requests=[];
    }
    if (kind==='idle') {s.operations={};s.tool_details={};if(['failed','claimed','inconclusive'].includes(s.prior))s.status=s.prior;}
    s.prior=s.status;
    if (kind==='permission'&&!s.requests.includes(fields.request)&&s.requests.length<128) s.requests.push(fields.request);
    if (kind==='permission_resolved') s.requests=s.requests.filter(r=>r!==fields.request);
    if (kind==='tasks') {s.completed=fields.completed;s.total=fields.total;}
    if (sessions.size>50) sessions.delete(sessions.keys().next().value);
  }
  const classify = (tool, args) => {
    const command = typeof args?.command === 'string' ? args.command : '';
    const testing = /(?:^|[\s;&|])(?:npm|pnpm|yarn|bun|cargo|pytest|jest|vitest|ctest|dotnet|go|python)(?:\s|$)/i.test(command) && /(?:test|pytest|jest|vitest|ctest|check)/i.test(command);
    const building = /(?:^|[\s;&|])(?:npm|pnpm|yarn|bun|cargo|dotnet|go|cmake|make|msbuild)(?:\s|$)/i.test(command) && /(?:build|compile|publish)/i.test(command);
    return testing ? 'testing' : building ? 'building' : ['edit', 'write', 'apply_patch', 'patch', 'multiedit'].includes(tool) ? 'editing' : 'active';
  };
  async function activity(kind, session) {
    const key = `${session}:${kind}`;
    if (Date.now() - (activityAt.get(key) || 0) < 2000) return;
    activityAt.set(key, Date.now());
    if (activityAt.size > 1000) activityAt.delete(activityAt.keys().next().value);
    await send(kind, session);
  }
  function send(kind, session = '', fields = {}, key) {
    if (closed) return Promise.resolve();
    if (fields.operation && interruptedTools.has(`${session}:${fields.operation}`)) return Promise.resolve();
    const timestamp = Date.now();
    remember(kind,session,fields,timestamp);
    const event = { version: 1, adapter: 'opencode', id: key ? `${source}:${key}` : randomUUID(), source, timestamp, workspace: path.resolve(directory), session, kind, ...fields };
    chain = chain.then(async () => {
      await mkdir(queue, { recursive: true });
      // Bounded spool, even when the companion is not running for days.
      if (sequence % 100 === 0) {
        const files = (await readdir(queue)).filter(n => /^\d+-\d+-[a-f0-9-]+\.json$/.test(n)).sort();
        const own = files.filter(n => n.endsWith(`-${source}.json`));
        const stale = files.filter(n => Number(n.split('-')[0]) < timestamp - 90000);
        const remove = new Set([...stale, ...files.slice(0,Math.max(0,files.length-2000)), ...own.slice(0,Math.max(0,own.length-500))]);
        for (const name of remove) await unlink(path.join(queue, name)).catch(() => {});
      }
      const file = path.join(queue, `${timestamp}-${String(sequence++).padStart(8, '0')}-${source}.json`);
      await writeFile(file + '.tmp', JSON.stringify(event), { mode: 0o600 });
      await rename(file + '.tmp', file);
    }).catch(async () => {
      // Observability must never break the agent's tools or permission flow.
      await client?.app?.log?.({ body: { service: 'nekoafk', level: 'warn', message: 'Local telemetry queue unavailable' } }).catch(() => {});
    });
    return chain;
  }
  await send('connected');
  const heartbeat = async () => {
    await send('heartbeat');
    // Sanitized current evidence allows a restarted companion to reconnect.
    // Historical activity times remain historical; snapshots are never proof.
    for (const [session,s] of sessions) await send('snapshot',session,{...s,operations:{...s.operations},requests:[...s.requests]});
  };
  const timer = setInterval(heartbeat, 15000);
  timer.unref?.();
  return {
    dispose: async () => { clearInterval(timer); await send('disconnected'); closed = true; await chain; },
    'chat.message': async (input) => { await send('active', input.sessionID, {}, `turn:${input.messageID || randomUUID()}`); },
    'tool.execute.before': async (input, output) => {
      const kind = classify(input.tool, output.args);
      lastToolKind.set(`${input.sessionID}:${input.callID}`, kind);
      if (lastToolKind.size > 1000) lastToolKind.delete(lastToolKind.keys().next().value);
      await send(kind, input.sessionID, { tool: String(input.tool).slice(0, 80), operation:String(input.callID).slice(0,128) }, `start:${input.sessionID}:${input.callID}`);
    },
    'tool.execute.after': async (input, output) => {
      const exit = Number.isInteger(output.metadata?.exit) ? output.metadata.exit : null;
      await send(exit !== null && exit !== 0 ? 'failure' : 'tool_finished', input.sessionID,
        { tool: String(input.tool).slice(0, 80), operation:String(input.callID).slice(0,128), exit_code: exit, testing: lastToolKind.get(`${input.sessionID}:${input.callID}`) === 'testing' }, `end:${input.sessionID}:${input.callID}:${exit ?? 'unknown'}`);
      // Keep the bounded classification cache: a richer terminal part can arrive
      // after this hook and must retain whether the command was test-like.
    },
    event: async ({ event }) => {
      const p = event.properties || {};
      const session = p.sessionID || p.info?.sessionID || p.part?.sessionID || p.info?.id || '';
      switch (event.type) {
        case 'session.created': await send('session', session); break;
        case 'session.deleted': await send('closed',session); sessions.delete(session); break;
        case 'session.status':
          if (p.status?.type === 'busy') await send('busy', session);
          else if (p.status?.type === 'retry') await send('failure', session);
          else if (p.status?.type === 'idle') await send('idle', session);
          break;
        case 'session.idle': await send('idle', session); break;
        case 'session.error': await send(p.error?.name==='MessageAbortedError'?'interrupted':'failure', session); break;
        case 'permission.updated':
        case 'permission.asked': await send('permission', session, { request: p.id || '' }); break;
        case 'permission.replied': await send('permission_resolved', session, { request: p.requestID || p.permissionID || '' }); break;
        case 'file.edited': if (session) await send('editing', session); break;
        case 'todo.updated': {
          // Only explicit, well-formed plan states support a count. An empty
          // or replaced list clears the plan; content/priority never leave here.
          if (!Array.isArray(p.todos) || p.todos.length>10000 || p.todos.some(t=>!['pending','in_progress','completed','cancelled'].includes(t?.status))) {
            await send('tasks',session,{completed:null,total:null});break;
          }
          const todos = p.todos.filter(t => t.status !== 'cancelled');
          await send('tasks', session, { completed: todos.filter(t => t.status === 'completed').length, total: todos.length });
          break;
        }
        case 'message.part.updated': {
          const part = p.part;
          if (part?.type === 'reasoning' || part?.type === 'text' && roles.get(part.messageID) === 'assistant') {
            const kind = part.type === 'reasoning' ? 'planning' : 'writing';
            parts.set(part.id, kind);
            if (parts.size > 1000) parts.delete(parts.keys().next().value);
            if (!part.time?.end) await activity(kind, session);
            break;
          }
          if (part?.type !== 'tool') break;
          const tool = String(part.tool).slice(0, 80);
          if (part.state?.status === 'running') {
            const kind=classify(part.tool,part.state.input);
            lastToolKind.set(`${session}:${part.callID}`,kind);
            if(lastToolKind.size>1000)lastToolKind.delete(lastToolKind.keys().next().value);
            await send(kind, session, {tool,operation:String(part.callID).slice(0,128)}, `start:${session}:${part.callID}`);
          }
          else if (part.state?.status === 'completed' || part.state?.status === 'error') {
            const exit = Number.isInteger(part.state.metadata?.exit) ? part.state.metadata.exit : null;
            await send(part.state.status === 'error' || exit !== null && exit !== 0 ? 'failure' : 'tool_finished', session,
              {tool, operation:String(part.callID).slice(0,128), exit_code:exit, testing:(lastToolKind.get(`${session}:${part.callID}`)||classify(part.tool,part.state.input))==='testing'}, `end:${session}:${part.callID}:${exit ?? (part.state.status==='error'?'error':'unknown')}`);
          }
          break;
        }
        case 'message.part.delta': {
          const kind = parts.get(p.partID);
          if (kind && session) await activity(kind, session);
          break;
        }
        case 'message.updated': {
          const info = p.info;
          if (info?.id && info.role) {
            roles.set(info.id, info.role);
            if (roles.size > 1000) roles.delete(roles.keys().next().value);
          }
          if (info?.role === 'assistant' && info.time?.completed && info.finish === 'stop' && !info.error && !completedMessages.has(info.id)) {
            completedMessages.add(info.id);
            if (completedMessages.size > 1000) completedMessages.delete(completedMessages.values().next().value);
            await send('claimed', session, {}, `claim:${info.id}`);
          }
          break;
        }
      }
    }
  };
};
