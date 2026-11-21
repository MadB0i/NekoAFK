/**
 * Live Interactive Demonstration of Antigravity connecting to NekoAFK
 * Run this while NekoAFK is open to watch Nova/Neko animate in real-time on your screen!
 */
import { AntigravityBridge } from './nekoafk-antigravity.mjs';

const sleep = ms => new Promise(r => setTimeout(r, ms));

async function main() {
  const workspace = process.cwd();
  console.log('----------------------------------------------------');
  console.log('🤖 Starting NekoAFK Live Antigravity Experience Demo');
  console.log(`📁 Workspace: ${workspace}`);
  console.log('👀 Dekhiye apne desktop par Nova / Neko mascot ko!');
  console.log('----------------------------------------------------\n');

  const bridge = new AntigravityBridge({ workspace, session: 'antigravity-live-demo' });
  await sleep(1500);

  console.log('1️⃣ [Step 1] Antigravity Connected -> Waiting / Idle');
  await bridge.reportIdle();
  await sleep(3500);

  console.log('2️⃣ [Step 2] Antigravity Thinking & Planning (Reasoning mode)...');
  await bridge.reportThinking();
  await sleep(4000);

  console.log('3️⃣ [Step 3] Antigravity Editing Code (Floating keyboard typing animation)...');
  const editOp = `op-${Date.now()}`;
  await bridge.reportToolStart('edit_file', { path: 'src/main.ts' }, editOp);
  await sleep(5000);
  await bridge.reportToolEnd('edit_file', editOp, 0);
  await sleep(1500);

  console.log('4️⃣ [Step 4] Antigravity Running Tests (Magnifying glass inspection animation)...');
  const testOp = `op-${Date.now()}`;
  await bridge.reportToolStart('run_command', { CommandLine: 'cargo test' }, testOp);
  await sleep(5000);
  await bridge.reportToolEnd('run_command', testOp, 0, true);
  await sleep(1500);

  console.log('5️⃣ [Step 5] Antigravity Asking User Permission (Alert / Attention recoil)...');
  await bridge.reportPermissionNeeded('permission-demo-1');
  await sleep(4500);

  console.log('6️⃣ [Step 6] User Granted Permission -> Resuming work...');
  await bridge.reportPermissionResolved('permission-demo-1');
  await bridge.reportWriting();
  await sleep(3000);

  console.log('7️⃣ [Step 7] Antigravity Claimed Task Completion...');
  await bridge.reportClaimed();
  await sleep(3000);

  console.log('🎉 Demo cycle completed! Mascot is waiting in Idle state.');
  console.log('Disconnecting demo bridge in 5 seconds...');
  await sleep(5000);
  await bridge.close();
  console.log('Bridge disconnected.');
}

main().catch(console.error);
