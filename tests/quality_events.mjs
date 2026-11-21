// Test-only producer. Uses the production adapter; never ships in the app.
import readline from 'node:readline';
import {setTimeout as delay} from 'node:timers/promises';
import {NekoAFKPlugin} from '../integrations/opencode/nekoafk.js';
const directory=process.argv[2];let plugin=await NekoAFKPlugin({directory}), serial=0;
const input=(c)=>({sessionID:c.session||'quality-session',callID:c.operation||`quality-${serial++}`,tool:c.tool||'bash'});
async function act(c){
 const i=input(c),event=(type,properties)=>plugin.event({event:{type,properties:{sessionID:i.sessionID,...properties}}});
 switch(c.action){
  case 'idle':await event('session.idle',{});break;
  case 'plan':await event('todo.updated',{todos:c.statuses.map(status=>({status,content:'PRIVATE FIXTURE MILESTONE',priority:'medium'}))});break;
  case 'interrupted':await event('session.error',{error:{name:'MessageAbortedError',data:{message:'PRIVATE FIXTURE INTERRUPTION'}}});break;
  case 'writing':
   await event('message.updated',{info:{id:'quality-message',sessionID:i.sessionID,role:'assistant'}});
   await event('message.part.updated',{part:{id:'quality-part',messageID:'quality-message',sessionID:i.sessionID,type:'text'}});break;
  case 'start':await plugin['tool.execute.before'](i,{args:{command:c.testing?'npm test':'sleep 70'}});break;
  case 'end':await plugin['tool.execute.after'](i,{metadata:c.exit===null?{}:{exit:c.exit??0}});break;
  case 'permission':await event('permission.asked',{id:'quality-permission'});break;
  case 'resolved':await event('permission.replied',{requestID:'quality-permission'});break;
  case 'claimed':await event('message.updated',{info:{id:`claim-${serial++}`,sessionID:i.sessionID,role:'assistant',time:{completed:Date.now()},finish:'stop'}});break;
  case 'disconnect':await plugin.dispose();break;
  case 'reconnect':plugin=await NekoAFKPlugin({directory});break;
  case 'flood':
   for(let n=0;n<(c.count||500);n++){
    const op=`flood-${serial++}`;
    await act({action:'start',operation:op,testing:true,session:i.sessionID});
    await act({action:'end',operation:op,exit:0,session:i.sessionID});
    await act({action:'end',operation:op,exit:0,session:i.sessionID});
    await delay(c.interval_ms??20);
   }break;
  case 'quit':await plugin.dispose();break;
  default:throw Error('Unknown quality fixture action');
 }
}
console.log(JSON.stringify({ready:true}));
for await(const line of readline.createInterface({input:process.stdin})){
 try{const c=JSON.parse(line);await act(c);console.log(JSON.stringify({ok:true}));if(c.action==='quit')break;}
 catch(e){console.log(JSON.stringify({error:String(e)}));}
}
