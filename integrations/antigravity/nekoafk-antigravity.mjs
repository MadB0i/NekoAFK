/**
 * NekoAFK Bridge for Google Antigravity
 * Connects Antigravity agent activity (tool execution, editing, reasoning, testing)
 * to the NekoAFK companion via local atomic file queue.
 */
import { NekoBridge, classifyTool, TOOL_LABELS } from '../shared/bridge-core.mjs';
import path from 'node:path';
import fs from 'node:fs';

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
  const workspace = process.argv[2] || process.cwd();
  console.log(`[NekoAFK] Antigravity Bridge active for: ${workspace}`);
  const bridge = new AntigravityBridge({ workspace });

  // Optional: watch transcript.jsonl if specified
  const transcriptPath = process.argv[3];
  if (transcriptPath && fs.existsSync(transcriptPath)) {
    console.log(`[NekoAFK] Watching Antigravity transcript: ${transcriptPath}`);
    let lastSize = 0;
    fs.watchFile(transcriptPath, { interval: 500 }, () => {
      try {
        const stats = fs.statSync(transcriptPath);
        if (stats.size > lastSize) {
          bridge.reportThinking();
          lastSize = stats.size;
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
