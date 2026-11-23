/**
 * NekoAFK Bridge for Google Antigravity
 * Connects Antigravity agent activity (tool execution, editing, reasoning, testing)
 * to the NekoAFK companion via local atomic file queue.
 */
import { NekoBridge, classifyTool, TOOL_LABELS } from '../shared/bridge-core.mjs';
import path from 'node:path';
import fs from 'node:fs';
import os from 'node:os';

function resolveWorkspace(cliArg) {
  if (cliArg) return path.resolve(cliArg);
  try {
    const settingsPath = path.join(
      process.env.LOCALAPPDATA || path.join(os.homedir(), 'AppData', 'Local'),
      'com.nekoafk.desktop',
      'settings.json'
    );
    if (fs.existsSync(settingsPath)) {
      const data = JSON.parse(fs.readFileSync(settingsPath, 'utf8'));
      if (data?.settings?.workspace && fs.existsSync(data.settings.workspace)) {
        return path.resolve(data.settings.workspace);
      }
    }
  } catch {}
  return process.cwd();
}

function findLatestTranscript() {
  try {
    const brainDir = path.join(os.homedir(), '.gemini', 'antigravity', 'brain');
    if (!fs.existsSync(brainDir)) return null;
    const entries = fs.readdirSync(brainDir, { withFileTypes: true });
    let latestPath = null;
    let latestMtime = 0;
    for (const entry of entries) {
      if (entry.isDirectory()) {
        const candidate = path.join(brainDir, entry.name, '.system_generated', 'logs', 'transcript.jsonl');
        if (fs.existsSync(candidate)) {
          const mtime = fs.statSync(candidate).mtimeMs;
          if (mtime > latestMtime) {
            latestMtime = mtime;
            latestPath = candidate;
          }
        }
      }
    }
    return latestPath;
  } catch {
    return null;
  }
}

export class AntigravityBridge extends NekoBridge {
  constructor({ workspace = process.cwd(), session = 'antigravity-main' } = {}) {
    super({ adapter: 'antigravity', workspace });
    this.session = session;
    this.startHeartbeat();
  }

  async reportToolStart(tool, args = {}, callId = Date.now().toString()) {
    const kind = classifyTool(tool, args);
    const label = TOOL_LABELS[tool] || 'Tool';
    await this.send(kind, this.session, {
      tool: String(tool).slice(0, 80),
      operation: String(callId).slice(0, 128),
      tool_details: {
        [String(callId).slice(0, 128)]: {
          label,
          started_at: Date.now()
        }
      }
    });
    return kind;
  }

  async reportToolEnd(tool, callId, exitCode = 0, wasTesting = false) {
    const failed = exitCode !== null && exitCode !== 0;
    await this.send(failed ? 'failure' : 'tool_finished', this.session, {
      tool: String(tool).slice(0, 80),
      operation: String(callId).slice(0, 128),
      exit_code: exitCode,
      testing: wasTesting
    });
  }

  async reportThinking() {
    await this.activity('planning', this.session);
  }

  async reportWriting() {
    await this.activity('writing', this.session);
  }

  async reportEditing() {
    await this.activity('editing', this.session);
  }

  async reportPermissionNeeded(requestId = 'user-approval') {
    await this.send('permission', this.session, { request: requestId });
  }

  async reportPermissionResolved(requestId = 'user-approval') {
    await this.send('permission_resolved', this.session, { request: requestId });
  }

  async reportClaimed() {
    await this.send('claimed', this.session);
  }

  async reportIdle() {
    await this.send('idle', this.session);
  }
}

// Standalone CLI execution
if (process.argv[1] && path.resolve(process.argv[1]) === path.resolve(import.meta.filename)) {
  const workspace = resolveWorkspace(process.argv[2]);
  console.log(`[NekoAFK] Antigravity Bridge active for: ${workspace}`);
  const bridge = new AntigravityBridge({ workspace });

  // Auto-detect or watch specified transcript.jsonl
  const transcriptPath = process.argv[3] || findLatestTranscript();
  if (transcriptPath && fs.existsSync(transcriptPath)) {
    console.log(`[NekoAFK] Watching Antigravity transcript: ${transcriptPath}`);
    let lastSize = fs.statSync(transcriptPath).size;
    let idleTimer = null;
    const resetIdleTimer = () => {
      if (idleTimer) clearTimeout(idleTimer);
      idleTimer = setTimeout(() => {
        bridge.reportIdle();
      }, 15000);
      idleTimer.unref?.();
    };

    fs.watchFile(transcriptPath, { interval: 300 }, () => {
      try {
        const stats = fs.statSync(transcriptPath);
        if (stats.size > lastSize) {
          const buffer = Buffer.alloc(stats.size - lastSize);
          const fd = fs.openSync(transcriptPath, 'r');
          fs.readSync(fd, buffer, 0, buffer.length, lastSize);
          fs.closeSync(fd);
          lastSize = stats.size;

          const text = buffer.toString('utf8');
          const lines = text.split('\n').filter(Boolean);
          for (const line of lines) {
            try {
              const data = JSON.parse(line);
              if (data.type === 'PLANNER_RESPONSE') {
                if (Array.isArray(data.tool_calls) && data.tool_calls.length > 0) {
                  for (const call of data.tool_calls) {
                    bridge.reportToolStart(call.name, call.args || {});
                  }
                } else {
                  bridge.reportThinking();
                }
                resetIdleTimer();
              } else if (data.type === 'GENERIC') {
                const content = String(data.content || '');
                const exitMatch = content.match(/Command exited with code (\d+)/);
                const exitCode = exitMatch ? parseInt(exitMatch[1], 10) : 0;
                bridge.reportToolEnd('tool', 'step', exitCode);
                resetIdleTimer();
              } else if (data.type === 'USER_INPUT') {
                bridge.reportWriting();
                resetIdleTimer();
              }
            } catch {}
          }
        }
      } catch {}
    });
  }

  process.on('SIGINT', async () => {
    console.log('[NekoAFK] Disconnecting bridge...');
    await bridge.close();
    process.exit(0);
  });
}
