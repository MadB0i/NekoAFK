import { mkdir, readdir, rename, unlink, writeFile } from 'node:fs/promises';
import { randomUUID } from 'node:crypto';
import path from 'node:path';
import os from 'node:os';

export function getQueueDir() {
  const base = process.env.NEKOAFK_DATA_DIR || path.join(
    process.env.LOCALAPPDATA || path.join(os.homedir(), '.local', 'share'),
    'com.nekoafk.desktop'
  );
  return path.join(base, 'bridge', 'queue');
}

export const TOOL_LABELS = {
  bash: 'Shell',
  shell: 'Shell',
  powershell: 'Shell',
  cmd: 'Shell',
  terminal: 'Shell',
  run_command: 'Shell',
  edit: 'File edit',
  write: 'File edit',
  edit_file: 'File edit',
  write_file: 'File edit',
  apply_patch: 'File edit',
  patch: 'File edit',
  multiedit: 'File edit',
  read: 'File read',
  read_file: 'File read',
  glob: 'File search',
  grep: 'File search',
  search_web: 'Web lookup',
  webfetch: 'Web lookup',
  websearch: 'Web lookup',
  todowrite: 'Plan update',
  todoread: 'Plan update',
  task: 'Subagent',
  invoke_subagent: 'Subagent'
};

export function classifyCommand(command = '') {
  const testing = /(?:^|[\s;&|])(?:npm|pnpm|yarn|bun|cargo|pytest|jest|vitest|ctest|dotnet|go|python)(?:\s|$)/i.test(command)
    && /(?:test|pytest|jest|vitest|ctest|check)/i.test(command);
  const building = /(?:^|[\s;&|])(?:npm|pnpm|yarn|bun|cargo|dotnet|go|cmake|make|msbuild)(?:\s|$)/i.test(command)
    && /(?:build|compile|publish)/i.test(command);
  return testing ? 'testing' : building ? 'building' : 'active';
}

export function classifyTool(tool = '', args = {}) {
  const t = String(tool).toLowerCase();
  const cmd = typeof args?.command === 'string' ? args.command : (typeof args?.CommandLine === 'string' ? args.CommandLine : '');
  if (['bash', 'shell', 'powershell', 'cmd', 'run_command'].includes(t)) {
    return classifyCommand(cmd);
  }
  if (['edit', 'write', 'edit_file', 'write_file', 'apply_patch', 'patch', 'multiedit'].includes(t)) {
    return 'editing';
  }
  return 'active';
}

export class NekoBridge {
  constructor({ adapter = 'generic', workspace = process.cwd(), source = randomUUID() } = {}) {
    this.adapter = adapter;
    this.workspace = path.resolve(workspace);
    this.source = source;
    this.queue = getQueueDir();
    this.chain = Promise.resolve();
    this.sequence = 0;
    this.closed = false;
    this.sessions = new Map();
    this.activityAt = new Map();
  }

  async send(kind, session = 'default', fields = {}, key) {
    if (this.closed) return Promise.resolve();
    const timestamp = Date.now();
    const event = {
      version: 1,
      adapter: this.adapter,
      id: key ? `${this.source}:${key}` : randomUUID(),
      source: this.source,
      timestamp,
      workspace: this.workspace,
      session: String(session),
      kind,
      ...fields
    };

    this.chain = this.chain.then(async () => {
      await mkdir(this.queue, { recursive: true });
      if (this.sequence % 100 === 0) {
        try {
          const files = (await readdir(this.queue)).filter(n => /^\d+-\d+-[a-f0-9-]+\.json$/.test(n)).sort();
          const own = files.filter(n => n.endsWith(`-${this.source}.json`));
          const stale = files.filter(n => Number(n.split('-')[0]) < timestamp - 90000);
          const remove = new Set([...stale, ...files.slice(0, Math.max(0, files.length - 2000)), ...own.slice(0, Math.max(0, own.length - 500))]);
          for (const name of remove) await unlink(path.join(this.queue, name)).catch(() => {});
        } catch {}
      }
      const file = path.join(this.queue, `${timestamp}-${String(this.sequence++).padStart(8, '0')}-${this.source}.json`);
      await writeFile(file + '.tmp', JSON.stringify(event), { mode: 0o600 });
      await rename(file + '.tmp', file);
    }).catch(() => {});
    return this.chain;
  }

  async activity(kind, session = 'default') {
    const key = `${session}:${kind}`;
    if (Date.now() - (this.activityAt.get(key) || 0) < 2000) return;
    this.activityAt.set(key, Date.now());
    if (this.activityAt.size > 1000) this.activityAt.delete(this.activityAt.keys().next().value);
    await this.send(kind, session);
  }

  startHeartbeat(intervalMs = 15000) {
    this.send('connected');
    this.timer = setInterval(async () => {
      await this.send('heartbeat');
    }, intervalMs);
    this.timer.unref?.();
  }

  async close() {
    if (this.timer) clearInterval(this.timer);
    await this.send('disconnected');
    this.closed = true;
    await this.chain;
  }
}
