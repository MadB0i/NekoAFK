// Test-only long operation: real plugin heartbeat lifetime, no fabricated result.
import { NekoAFKPlugin } from '../integrations/opencode/nekoafk.js';
const plugin=await NekoAFKPlugin({directory:process.argv[2]});
await plugin['chat.message']({sessionID:'fixture-session',messageID:'long-operation-'+Date.now()});
// Optional ongoing observed-work fixture. Heartbeats alone deliberately do not
// refresh the host's factual activity age. Default retains the expiry test.
const activityTimer=process.argv[4]==='refresh'?setInterval(()=>{
  void plugin['chat.message']({sessionID:'fixture-session',messageID:'continued-operation-'+Date.now()});
},20000):undefined;
await new Promise(resolve=>setTimeout(resolve,Number(process.argv[3]||75)*1000));
if(activityTimer)clearInterval(activityTimer);
await plugin.dispose();
