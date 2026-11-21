/**
 * NekoAFK Bridge for Anthropic Claude Code
 * Connects Claude Code CLI / MCP activity to the NekoAFK companion.
 */
import { NekoBridge, classifyTool, TOOL_LABELS } from '../shared/bridge-core.mjs';
import path from 'node:path';

export class ClaudeCodeBridge extends NekoBridge {
  constructor({ workspace = process.cwd(), session = 'claude-session' } = {}) {
    super({ adapter: 'claudecode', workspace });
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

  async reportPermissionNeeded(request = 'tool-permission') {
    await this.send('permission', this.session, { request });
  }

  async reportPermissionResolved(request = 'tool-permission') {
    await this.send('permission_resolved', this.session, { request });
  }

  async reportClaimed() {
    await this.send('claimed', this.session);
  }

  async reportIdle() {
    await this.send('idle', this.session);
  }
}

// Standalone CLI runner / wrapper
if (process.argv[1] && path.resolve(process.argv[1]) === path.resolve(import.meta.filename)) {
  const workspace = process.argv[2] || process.cwd();
  console.log(`[NekoAFK] Claude Code Bridge active for: ${workspace}`);
  const bridge = new ClaudeCodeBridge({ workspace });

  process.on('SIGINT', async () => {
    console.log('[NekoAFK] Disconnecting Claude Code bridge...');
    await bridge.close();
    process.exit(0);
  });
}
