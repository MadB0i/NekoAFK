// Explicit test harness, never included in the product build.
import { NekoAFKPlugin } from '../integrations/opencode/nekoafk.js';
const [workspace, scenario] = process.argv.slice(2);
const plugin = await NekoAFKPlugin({ directory: workspace });
const input = {sessionID:'fixture-session',messageID:`fixture-${Date.now()}`,tool:'edit',callID:`call-${Date.now()}`};
switch (scenario) {
  case 'rapid':
    for(let i=0;i<60;i++) {
      const call={...input,callID:`rapid-${Date.now()}-${i}`};
      if(i%3===0)await plugin['tool.execute.after']({...call,tool:'bash'},{metadata:{exit:1}});
      else await plugin['tool.execute.before']({...call,tool:i%3===1?'edit':'bash'},{args:{command:'npm test'}});
    }
    await plugin['tool.execute.before']({...input,callID:input.callID+'last'},{args:{}});
    await plugin.event({event:{type:'permission.asked',properties:{sessionID:input.sessionID,id:'fixture-request'}}});
    break;
  case 'busy': await plugin['chat.message'](input); break;
  case 'idle': await plugin.event({event:{type:'session.idle',properties:{sessionID:input.sessionID}}}); break;
  case 'planning': await plugin.event({event:{type:'message.part.updated',properties:{part:{id:input.messageID,type:'reasoning',sessionID:input.sessionID,time:{start:Date.now()}}}}}); break;
  case 'writing':
    await plugin.event({event:{type:'message.updated',properties:{info:{id:input.messageID,sessionID:input.sessionID,role:'assistant'}}}});
    await plugin.event({event:{type:'message.part.updated',properties:{part:{id:input.callID,type:'text',messageID:input.messageID,sessionID:input.sessionID}}}}); break;
  case 'building': await plugin['tool.execute.before']({...input,tool:'bash'},{args:{command:'cargo build'}}); break;
  case 'editing': await plugin['tool.execute.before'](input,{args:{}}); break;
  case 'testing': await plugin['tool.execute.before']({...input,tool:'bash'},{args:{command:'npm test'}}); break;
  case 'failure': await plugin['tool.execute.after']({...input,tool:'bash'},{metadata:{exit:1}}); break;
  case 'permission': await plugin.event({event:{type:'permission.asked',properties:{sessionID:input.sessionID,id:'fixture-request'}}}); break;
  case 'resolved': await plugin.event({event:{type:'permission.replied',properties:{sessionID:input.sessionID,requestID:'fixture-request'}}}); break;
  case 'claimed': await plugin.event({event:{type:'message.updated',properties:{info:{id:`fixture-claim-${Date.now()}`,sessionID:input.sessionID,role:'assistant',time:{completed:Date.now()},finish:'stop'}}}}); break;
  case 'tasks': await plugin.event({event:{type:'todo.updated',properties:{sessionID:input.sessionID,todos:[{status:'completed'},{status:'pending'}]}}}); break;
  case 'tasks-complete': await plugin.event({event:{type:'todo.updated',properties:{sessionID:input.sessionID,todos:[{status:'completed'},{status:'completed'}]}}}); break;
  default: throw Error('Unknown test scenario');
}
// Process exit stops the unref heartbeat. Do not send disconnected until the
// scenario has been observed; each native smoke step starts a new source.
