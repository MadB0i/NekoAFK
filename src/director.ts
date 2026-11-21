// Authored character acting only. Agent evidence remains owned by the native host.
export type Personality = 'calm' | 'playful' | 'chaos';
export type Mood = 'idle' | 'busy' | 'planning' | 'writing' | 'testing' | 'failed' | 'irritated' | 'permission' | 'verifying' | 'verified' | 'inconclusive';
export type Pose = {
 x:number; y:number; body:number; squash:number; head:number; hx:number; hy:number; turn:number;
 left:number; right:number; lx:number; ly:number; rx:number; ry:number; earL:number; earR:number;
 tail:number; curl:number; eyes:number; eyeL:number; eyeR:number; gazeX:number; gazeY:number;
 brow:number; mouth:number; jaw:number; prop:number; propX:number; propY:number; propR:number;
 palm:number; breath:number;
};
export const neutral:Pose = {x:0,y:0,body:0,squash:1,head:0,hx:0,hy:0,turn:0,left:0,right:0,lx:0,ly:0,rx:0,ry:0,earL:0,earR:0,tail:0,curl:0,eyes:.96,eyeL:0,eyeR:0,gazeX:0,gazeY:0,brow:0,mouth:0,jaw:0,prop:0,propX:0,propY:0,propR:0,palm:0,breath:0};
type Ease='smooth'|'out'|'in'|'hold';
type Key=[number,Partial<Pose>,Ease?];
export type Activity={id:string;label:string;duration:number;keys:[number,Pose,Ease][];prop?:string;cooldown:number;};
// Sparse keys HOLD their earlier channels. A head adjustment cannot silently
// release a paw or prop. Seconds are intentional acting beats, not percentages.
function clip(id:string,label:string,duration:number,keys:Key[],prop?:string,cooldown=45):Activity {
 let pose={...neutral};
 const result:[number,Pose,Ease][]=[[0,{...pose},'smooth']];
 for(const [at,patch,ease='smooth'] of keys){pose={...pose,...patch};result.push([at,{...pose},ease]);}
 result.push([duration,{...neutral},'smooth']);
 return {id,label,duration,keys:result,prop,cooldown};
}
const listen=clip('listen','Did you hear that?',8.6,[
 [.45,{gazeX:-5,earL:-9},'out'],[.85,{gazeX:-7,head:-6,hx:-2,turn:-3}],
 [1.3,{earR:4,tail:5}],[2.7,{eyeL:-.12}],[3.2,{gazeX:5,earR:-8},'out'],
 [3.75,{head:5,hx:2,turn:3,eyeL:0,earL:2}],[4.8,{gazeX:2,gazeY:-2}],
 [5.8,{head:1,hx:0,turn:0,gazeX:0,gazeY:0,earL:0,earR:0}],
 [6.1,{eyes:.05,mouth:.18}],[6.6,{eyes:.82}],[7.3,{head:-1,tail:0,mouth:0}]
],undefined,24);
const wash=clip('wash','One paw, one whisker',10.2,[
 [.55,{gazeY:6,head:4,earL:3}],[1.25,{lx:18,ly:-61,left:-28,hy:4,eyes:.8}],
 [1.65,{lx:25,ly:-78,left:-38,head:6,jaw:.22},'out'],[1.95,{jaw:0,ly:-73}],
 [2.5,{lx:-7,ly:-116,left:-18,head:11,eyeL:-.7,eyes:.8,hy:4}],
 [3.2,{lx:-12,ly:-99,left:-33,head:13,eyeL:-.3}],
 [3.7,{lx:-7,ly:-113,left:-14,eyeL:-.7}],[4.5,{lx:-11,ly:-94,left:-30,eyeL:-.25}],
 [5.1,{lx:6,ly:-67,left:-15,head:6,eyes:.72,eyeL:0}],
 [6.1,{lx:0,ly:0,left:0,head:3,hy:0,eyes:.7,earL:0}],
 [6.6,{eyes:.03,mouth:.24}],[7.5,{eyes:.75,head:-2,mouth:.1}],[8.8,{head:0,eyes:.9,mouth:0}]
],undefined,85);
const nest=clip('nest','Making herself comfortable',28,[
 [.6,{gazeY:6,hy:2,eyes:.8}],
 [1.3,{lx:9,rx:-8,ly:3,ry:-4,body:-1.8,hy:4,tail:3}],
 [1.9,{ly:-4,ry:3,body:1.7}],[2.6,{ly:3,ry:-3,body:-1.4}],
 [3.2,{ly:0,ry:0,body:0,head:8,hy:10,eyes:.4,earL:6,earR:-4,curl:22}],
 [4.5,{lx:11,rx:-10,ly:1,ry:1,head:12,hy:17,eyes:.015,earL:10,earR:-9,curl:45,squash:.975,breath:1}],
 [21,{head:12,hy:17,eyes:.015},'hold'],
 [22,{earL:-4,eyes:.22,eyeR:-.13},'out'],
 [23.3,{eyes:.7,eyeR:0,head:5,hy:8,curl:24,breath:0}],
 [24.3,{eyes:.02,hy:4,jaw:.42,earL:5,earR:-3}],
 [25.3,{eyes:.75,jaw:0,lx:0,rx:0,ly:0,ry:0,squash:1}],
 [26.7,{head:0,hy:0,earL:0,earR:0,curl:0}]
],undefined,140);
const mote=clip('mote','A small, very important distraction',12.4,[
 [.25,{prop:1,propX:235,propY:96,gazeX:7,gazeY:-6},'out'],
 [.85,{head:6,turn:4,hx:2,earR:-8,eyes:1.04,propX:246,propY:103}],
 [1.7,{propX:257,propY:133,gazeX:9,gazeY:1,head:9,body:2,tail:7}],
 [2.4,{propX:243,propY:154,gazeY:6,head:12,hy:3,rx:11,ry:-13,right:12}],
 [2.95,{rx:18,ry:-38,right:22,eyes:.85,body:3,propX:237,propY:170}],
 [3.28,{rx:38,ry:-67,right:34,head:6,hy:0,eyes:1.08,propX:264,propY:148},'out'],
 [3.75,{rx:30,ry:-59,right:20,head:8,propX:257,propY:104,gazeY:-7,tail:-7}],
 [4.4,{rx:20,ry:-39,right:5,propX:212,propY:74,head:-3,turn:0,gazeX:4,gazeY:-10}],
 [5.2,{rx:0,ry:0,right:0,head:-8,hx:-2,body:0,propX:130,propY:76,gazeX:-6,earL:-6}],
 [6.3,{propX:88,propY:113,head:-12,turn:-5,gazeX:-9,gazeY:-2}],
 [7.4,{propX:63,propY:78,gazeX:-8,gazeY:-8,head:-9,earL:0}],
 [8,{prop:0,propX:48,propY:48}],[8.8,{eyes:.1,head:-4,turn:0,earR:0,tail:0}],
 [9.5,{eyes:.87,gazeX:-2,gazeY:0,head:-2,hx:0}],[11,{head:0,gazeX:0}]
],'mote',65);
const keyboard=clip('keyboard','A little work, then a second look',15,[
 [.45,{gazeY:8,head:2,hy:3}],
 [1.2,{prop:1,propY:0,lx:9,rx:-9,ly:-3,ry:-3,left:-6,right:6,hy:6,eyes:.9}],
 [1.9,{ly:0,ry:0,head:3}],[5.1,{head:-2,gazeX:-2}],
 [6.1,{ry:-10,right:10,head:0,hy:2,gazeY:-4,earR:-6}],
 [6.65,{head:-5,turn:-2,gazeX:-5,eyes:1}],
 [7.3,{head:-4,gazeX:-4,eyes:.6}],[8.2,{head:2,turn:0,gazeX:0,gazeY:8,hy:6,ry:0,right:6,eyes:.9,earR:0}],
 [11.5,{ly:-4,ry:-4,head:0,hy:2,gazeY:3}],
 [12.3,{propY:10,prop:.9,lx:0,rx:0,ly:0,ry:0,left:0,right:0,gazeY:5}],
 [13,{propY:22,prop:0,head:0,hy:0,gazeY:0}],[14,{eyes:.9}]
],'keyboard',38);
const consider=clip('consider','Let me look at that again',9.4,[
 [.45,{gazeX:-5,gazeY:-4,earR:4}],[1.1,{head:-7,turn:-3,hx:-2,eyes:.85}],
 [1.85,{lx:31,ly:-75,left:-24,head:-9,hy:3,eyeR:-.1}],
 [3.0,{gazeX:5,gazeY:-6,earL:-6},'out'],[3.5,{head:-3,turn:1,hx:0}],
 [4.8,{eyes:.4,mouth:-.12}],[5.3,{eyes:.9,eyeR:0,gazeX:1,gazeY:0,head:2}],
 [6.4,{lx:0,ly:0,left:0,hy:0,earL:0,earR:0,turn:0,mouth:0}],
 [7.4,{head:0,gazeX:0}]
],undefined,48);
const recoil=clip('recoil','Oh. That was unexpected.',5.6,[
 [.13,{gazeY:-2,eyes:1.12,earL:-8,earR:8},'out'],
 [.28,{hy:-7,head:-3,body:-2,lx:-4,rx:4,ly:-6,ry:-6,eyes:1.12,jaw:.45,tail:-12},'out'],
 [.65,{hy:-4,head:-2,body:-1,jaw:.2,earL:12,earR:-10}],
 [1.3,{hy:3,head:5,eyes:.65,jaw:0,brow:.6,tail:6,lx:0,rx:0,ly:0,ry:0,body:0}],
 [2.3,{gazeX:5,turn:2,eyes:.62,mouth:-.3}],
 [3.6,{head:2,hy:1,earL:5,earR:-3,tail:0}],
 [4.6,{head:0,hy:0,gazeX:0,turn:0,brow:.3}]
],undefined,40);
const huff=clip('huff','A very small protest',8.3,[
 [.35,{eyes:.6,brow:.7,gazeX:6}],
 [1,{head:11,turn:5,hx:3,earL:15,earR:-13,mouth:-.35,tail:-7}],
 [1.9,{eyes:.03,hy:-2,squash:1.015}],
 [2.65,{hy:5,squash:.975,jaw:.12,tail:12,rx:1,ry:-5},'out'],
 [3.1,{jaw:0,eyes:.42,eyeL:-.12,ry:0,squash:1}],
 [4,{gazeX:0,eyes:.6,head:7,hy:2,rx:3,ry:-12,right:12}],
 [4.27,{ry:3,right:0,tail:-4},'in'],[4.65,{ry:0,rx:0,tail:2}],
 [5.7,{head:3,turn:1,hx:0,eyes:.72,eyeL:0,earL:6,earR:-5}],
 [7,{head:0,turn:0,hy:0,tail:0,brow:.3,mouth:-.1}]
],undefined,62);
const beckon=clip('beckon','A moment of your attention',8.5,[
 [.3,{gazeX:-4,gazeY:-3,earL:-7,eyes:1.03},'out'],
 [.85,{head:-7,turn:-2,hx:-2}],
 [1.6,{lx:-7,ly:-57,left:-12,body:-1,palm:.65}],
 [2.1,{lx:-12,ly:-69,left:-24,head:-5,palm:1}],
 [2.65,{lx:-8,ly:-61,left:0}],[3.15,{lx:-12,ly:-69,left:-22}],
 [3.75,{lx:-8,ly:-61,left:-4,eyes:.83,mouth:.2}],
 [4.6,{lx:0,ly:0,left:0,palm:0,body:0}],
 [5.2,{eyes:.03}],[5.75,{eyes:.9}],[7,{head:-3,hx:0,turn:0,earL:0,gazeX:-2,mouth:0}]
],undefined,32);
const inspect=clip('inspect','One careful look',11.2,[
 [.5,{gazeY:6,head:4}],
 [1.3,{rx:9,ry:-34,right:-12,prop:1,head:5,hy:3,gazeX:4}],
 [2.2,{rx:4,ry:-69,right:-14,head:-5,turn:-2,hx:-2,hy:2,gazeX:4,gazeY:0,eyeL:-.18}],
 [3.8,{rx:17,ry:-66,right:-4,head:7,hx:3,turn:3,gazeX:7,earR:-6}],
 [5.1,{rx:5,ry:-71,right:-12,head:-4,hx:-2,turn:-2,gazeX:3,earL:-4,earR:0}],
 [6.1,{eyes:.65,eyeL:0}],
 [6.8,{rx:9,ry:-37,right:-3,head:0,hx:0,turn:0,hy:0,eyes:1,gazeY:-4,gazeX:0}],
 [8,{rx:0,ry:0,right:0,prop:0,gazeY:3,earL:0}],
 [9.4,{gazeY:0,eyes:.92}]
],'glass',34);
const delight=clip('delight','A quiet, thoroughly pleased cat',7.8,[
 [.22,{eyes:1.08,hy:-2,earL:-4,earR:4},'out'],
 [.58,{hy:5,squash:.965,eyes:.4,ly:3,ry:3}],
 [1.08,{hy:-8,squash:1.045,head:-5,eyes:.06,mouth:.65,ly:-28,ry:-20,lx:-7,rx:6,left:-18,right:15,curl:17},'out'],
 [1.7,{hy:-4,squash:1.015,head:-9,ly:-22,ry:-17,earL:6,earR:-2}],
 [2.7,{head:7,ly:-13,ry:-24,left:-5,right:22,tail:5,curl:9}],
 [3.6,{hy:1,squash:.99,head:3,ly:0,ry:0,lx:0,rx:0,left:0,right:0,eyes:.35,mouth:.45}],
 [4.3,{hy:0,squash:1,eyes:.82,head:-2,curl:4,earL:0,earR:0}],
 [5.8,{eyes:.75,head:0,tail:0,curl:0,mouth:.25}]
],undefined,3600);
const puzzle=clip('puzzle','Something is still missing',9,[
 [.4,{gazeX:4,gazeY:-3,eyeL:-.25,earL:8,earR:-7}],
 [1.15,{head:12,turn:3,hx:2,eyes:.88}],
 [2.6,{gazeX:-4,gazeY:1},'out'],
 [3.35,{head:-9,turn:-3,hx:-2,eyeL:0,eyeR:-.25,earL:-5,earR:13}],
 [4.5,{lx:9,ly:-23,left:-15,mouth:-.14}],
 [5.6,{head:-5,turn:0,hx:0,eyes:.1,eyeR:0}],
 [6.3,{eyes:.85,lx:0,ly:0,left:0,earL:0,earR:5}],
 [7.7,{head:-2,gazeX:0,gazeY:0,mouth:0}]
],undefined,45);
export const library:Record<Mood,Activity[]>={
 idle:[listen,wash,nest,mote],busy:[mote,listen,consider,wash],planning:[consider,listen],writing:[keyboard,listen],
 testing:[listen,consider],failed:[recoil,huff],irritated:[huff,recoil],permission:[beckon,listen],
 verifying:[inspect,consider],verified:[delight],inconclusive:[puzzle,consider]
};
const priorities:Record<Mood,number>={idle:0,busy:1,planning:2,writing:2,testing:3,inconclusive:4,verified:5,failed:6,irritated:6,verifying:7,permission:8};
export function moodFor(state:string,streak=0):Mood {
 if(state==='failed')return streak>=2?'irritated':'failed';
 return ({active:'busy',planning:'planning',writing:'writing',editing:'writing',testing:'testing',building:'testing',permission:'permission',verifying:'verifying',verified:'verified',claimed:'inconclusive',inconclusive:'inconclusive'} as Record<string,Mood>)[state]||'idle';
}
const clamp=(v:number)=>Math.max(0,Math.min(1,v));
const smooth=(v:number)=>{v=clamp(v);return v*v*v*(v*(v*6-15)+10);};
export function mix(from:Pose,to:Pose,t:number):Pose {const p={...from};for(const k of Object.keys(p) as (keyof Pose)[])p[k]=from[k]+(to[k]-from[k])*t;return p;}
export function sample(a:Activity,elapsed:number):Pose {
 const t=Math.max(0,Math.min(a.duration,elapsed));let i=1;
 while(i<a.keys.length-1&&a.keys[i][0]<t)i++;
 const [start,from]=a.keys[i-1], [end,to,ease]=a.keys[i];
 const raw=clamp((t-start)/(end-start));
 const u=ease==='hold'?0:ease==='out'?1-Math.pow(1-raw,3):ease==='in'?raw*raw*raw:smooth(raw);
 const p=mix(from,to,u);
 // Irregular, finite phrases. No perpetual sine-wave typing, bobbing or shaking.
 if(a.id==='keyboard')for(const [at,side] of [[2.05,'l'],[2.31,'r'],[2.72,'r'],[3.06,'l'],[3.62,'r'],[4.12,'l'],[4.34,'r'],[4.8,'l'],[8.5,'r'],[8.8,'l'],[9.3,'l'],[9.64,'r'],[10.12,'l'],[10.54,'r']] as const){
  const dt=t-at;if(dt>=-.16&&dt<.24){const lift=dt<0?smooth((dt+.16)/.16):1-smooth(dt/.24);if(side==='l')p.ly-=5*lift;else p.ry-=5*lift;}
 }
 if(a.id==='nest')p.hy+=Math.sin((t-4.5)*1.05)*.55*p.breath;
 return p;
}
function settled(mood:Mood):Pose {
 const p={...neutral};
 if(mood==='failed'||mood==='irritated')Object.assign(p,{eyes:.72,brow:.3,earL:5,earR:-4,mouth:-.12});
 if(mood==='permission')Object.assign(p,{head:-3,gazeX:-2,earL:-3});
 if(mood==='inconclusive')Object.assign(p,{head:-3,eyeR:-.1});
 if(mood==='verified')Object.assign(p,{eyes:.86,mouth:.22});
 return p;
}
export class Director {
 private seed:number;private last='';private cooldown=new Map<string,number>();
 private current?:Activity;private started=0;private until=0;private transition=0;private from={...neutral};
 private requested:Mood='idle';private mood:Mood='idle';private observed='';private celebrated=new Set<string>();private successToken='';
 private lastBlink=-10;private blinkAt=4;private clock=0;private variant=1;private rate=1;
 private attentionAt=-10;private attentionIndex=0;private restBlinks=0;
 private attention={gazeX:0,gazeY:0,head:0,earL:0,earR:0};private attentionFrom={...this.attention};
 personality:Personality='playful';
 constructor(seed=0x4e454b4f){this.seed=seed>>>0||1;this.attentionIndex=this.seed%6;}
 private random(){let x=this.seed;x^=x<<13;x^=x>>>17;x^=x<<5;this.seed=x>>>0;return this.seed/4294967296;}
 observe(state:string,streak:number,token:string,at:number){
  this.requested=moodFor(state,streak);this.successToken=token;
  const signature=`${this.requested}:${token}`;if(signature===this.observed)return;this.observed=signature;
  if(this.requested!==this.mood||this.requested==='verified'&&!this.celebrated.has(token)){
   if(priorities[this.requested]>=priorities[this.mood]||at-this.started>=.45)this.begin(at,true);
  }
 }
 private begin(at:number,entering=false){
  // Capture precisely the visible pose, including eyelids, before an interrupt.
  this.from=this.frame(at).pose;this.transition=at;this.mood=this.requested;
  this.attention=this.attentionFrom={gazeX:0,gazeY:0,head:0,earL:0,earR:0};this.attentionAt=-10;
  const victory=this.mood==='verified'&&!this.celebrated.has(this.successToken);
  const pool=this.mood==='verified'&&!victory?library.idle:library[this.mood];
  let choices=pool.filter(a=>(victory||a.id!==this.last)&&(victory||(this.cooldown.get(a.id)||0)<=at));
  if(!choices.length){this.current=undefined;this.started=at;this.until=at+5+this.random()*4;return;}
  // State changes get a readable entrance. Later performances can be quieter.
  const lead=entering&&choices.includes(pool[0])?pool[0]:undefined;
  this.current=lead||choices[Math.floor(this.random()*choices.length)];
  if(victory){this.celebrated.add(this.successToken);if(this.celebrated.size>128)this.celebrated.delete(this.celebrated.values().next().value!);}
  this.last=this.current.id;this.started=at;
  this.rate=(this.personality==='calm'?.92:this.personality==='chaos'?1.04:1)*(.97+this.random()*.06);
  this.variant=.94+this.random()*.12;
  const duration=this.current.duration/this.rate;
  this.cooldown.set(this.current.id,at+duration+this.current.cooldown);
  const rest=this.personality==='calm'?19+this.random()*19:this.personality==='chaos'?5+this.random()*8:10+this.random()*15;
  this.until=at+duration+rest;
 }
 tick(at:number){
  this.clock=Math.max(this.clock,at);at=this.clock;
  if(at>=this.until||this.requested!==this.mood&&at-this.started>=.45)this.begin(at,this.requested!==this.mood);
  if(at>=this.blinkAt){
   this.lastBlink=at;this.blinkAt=at+4.5+this.random()*5.5;
   const resting=!this.current||at>=this.started+(this.current.duration+2.4)/this.rate;
   if(resting&&['idle','busy','planning','writing','testing','verified'].includes(this.mood)&&++this.restBlinks%2===1){
    // A finite attention shift starts with an existing blink, then holds. It
    // never wakes a sleeping state on a new timer or changes authored clip RNG.
    const targets=[[4.5,-1.5],[0,0],[-4,-2.5],[0,0],[2.5,1.5],[0,0]];
    const [x,y]=targets[this.attentionIndex++%targets.length];
    const strength=this.personality==='calm'?.65:this.personality==='chaos'?1.1:1;
    this.attentionFrom={...this.attention};this.attentionAt=at;
    this.attention={gazeX:x*strength,gazeY:y*strength,head:x*.28*strength,earL:Math.min(0,x)*.45*strength,earR:-Math.max(0,x)*.45*strength};
   }
  }
  return this.frame(at);
 }
 // Once the authored settling and appendage follow-through finish, there is
 // nothing to composite until the next blink, performance or interruption.
 quietDelay(at:number):number {
  if(this.requested!==this.mood)return 0;
  if(at<this.transition+.42||at<this.lastBlink+.28||at<this.attentionAt+1.1)return 0;
  if(this.current&&at<this.started+(this.current.duration+2.4)/this.rate)return 0;
  return Math.max(0,Math.min(this.until,this.blinkAt)-at);
 }
 frame(at:number){
  const elapsed=Math.max(0,(at-this.started)*this.rate),held=!this.current||elapsed>=this.current.duration;
  let pose=this.current&&!held?sample(this.current,elapsed):settled(this.mood);
  if(this.current&&held)pose=mix(sample(this.current,this.current.duration),pose,smooth((elapsed-this.current.duration)/1.1));
  // Variants affect the softness of the acting; paw/prop contact stays authored.
  pose.head*=this.variant;pose.earL*=this.variant;pose.earR*=this.variant;
  if(!held&&this.current&&elapsed>this.current.duration-1.2)pose=mix(pose,settled(this.mood),smooth((elapsed-this.current.duration+1.2)/1.2));
  if(held)for(const key of Object.keys(this.attention) as (keyof typeof this.attention)[]){
   const duration=key.startsWith('gaze')?.22:.65;
   pose[key]+=this.attentionFrom[key]+(this.attention[key]-this.attentionFrom[key])*smooth((at-this.attentionAt)/duration);
  }
  const blink=at-this.lastBlink;
  if(pose.eyes>.45&&blink>=0&&blink<.28){const closure=blink<.085?smooth(blink/.085):1-smooth((blink-.085)/.195);pose.eyes*=1-closure;}
  // Blend AFTER the blink. Interrupting on a closed eyelid cannot reopen it twice.
  pose=mix(this.from,pose,smooth((at-this.transition)/.42));
  return {pose,prop:held?undefined:this.current?.prop,activity:held?'rest':this.current!.id,label:held?'Quietly keeping you company':this.current!.label,mood:this.mood};
 }
 still(){const a=library[this.requested][0];return {pose:sample(a,a.duration*.38),prop:a.prop,activity:a.id,label:a.label,mood:this.requested};}
}
