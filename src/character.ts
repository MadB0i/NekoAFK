import { Director, type Personality, type Pose } from './director';

const props:Record<string,string>={
 keyboard:`<path d="M101 251Q160 247 219 251L231 273Q162 279 89 273Z" fill="#443b53" stroke="#282235" stroke-width="1.4"/><path d="M104 252Q160 249 216 252L226 268Q160 274 94 269Z" fill="#b4a9be"/><g fill="#72617f" stroke="#d8cbdc" stroke-width=".6">${[0,1,2].map(row=>Array.from({length:10},(_,i)=>`<rect x="${105+i*10-row*2}" y="${254+row*5}" width="7" height="3.2" rx=".8"/>`).join('')).join('')}</g><path d="M140 270h40" stroke="#ead9ca" stroke-width="2.5" stroke-linecap="round"/><path d="M94 273Q161 278 227 273" stroke="#8a7698" stroke-opacity=".6"/>`,
 glass:'<path d="M-1 2 8-20" stroke="#432e39" stroke-width="7" stroke-linecap="round"/><path d="M-2 0 6-20" stroke="url(#gold)" stroke-width="4" stroke-linecap="round"/><circle cx="13" cy="-34" r="20" fill="#cfe5dc" fill-opacity=".16" stroke="#624635" stroke-width="5"/><circle cx="13" cy="-34" r="20" stroke="url(#gold)" stroke-width="3"/><path d="M0-34q1-10 11-13" stroke="#fff6dc" stroke-opacity=".8" stroke-width="2" stroke-linecap="round"/>',
 mote:'<g fill="#e9c27c"><path d="M0 0C-15-9-10-15-3-9Q1-6 0 0Z" opacity=".65"/><path d="M0 0C7-17 14-9 7-3Z" opacity=".75"/><ellipse rx="2.4" ry="4" fill="#ffe0a0"/><circle cy="-2" r="1.1" fill="#fff4d6"/></g>'
};
const clamp=(n:number,a:number,b:number)=>Math.min(b,Math.max(a,n));
// One face model, two characters. The lid/lash/brow math is shared; only the
// geometry constants and the mouth shape differ between Neko and Nova.
type FaceGeom={left:number;right:number;cy:number;w:number;hT:number;hB:number;brow:number;crease:number;smileCrease:number;lash:[number,number,number];lashTo:[number,number,number];mouthStyle:'cat'|'arc';mouthBase:number;openBase:number};
const CAT_FACE:FaceGeom={left:119,right:201,cy:132,w:21,hT:31,hB:29,brow:105,crease:140,smileCrease:120,lash:[44,34,57],lashTo:[154,122,151],mouthStyle:'cat',mouthBase:162,openBase:166};
const ROBOT_FACE:FaceGeom={left:118,right:202,cy:134,w:26,hT:34,hB:30,brow:92,crease:138,smileCrease:138,lash:[58,47,85],lashTo:[160,140,178],mouthStyle:'arc',mouthBase:170,openBase:172};
type Painter=(id:string,name:string,value:string)=>void;
type Mover=(id:string,value:string)=>void;
export class Character {
 readonly director:Director;
 private rig:'cat'|'robot';
 private root:HTMLElement;private parts:Record<string,SVGElement>={};private attributes=new Map<string,string>();private pupils:SVGElement[]=[];
 private frameId=0;private rendered=0;private suspended=true;private reduced=false;private elapsed=0;private previousTime=0;
 private timerId=0;private sleeping=false;private observed='';
 private activeProp='';private propChanged=0;private priorOpacity=0;private lastPropOpacity=0;
 private system=matchMedia('(prefers-reduced-motion: reduce)');
 private follow={earL:0,earR:0,tail:0,curl:0,charm:0};
 constructor(root:HTMLElement,seed=crypto.getRandomValues(new Uint32Array(1))[0]){
  this.root=root;this.director=new Director(seed);
  this.rig=(root.querySelector('svg') as (SVGElement&{dataset?:DOMStringMap})|null)?.dataset?.character==='robot'?'robot':'cat';
  for(const id of ['rig','torso','body','head','face-features','muzzle','tail-outline','tail-fur','tail-light','ear-left','ear-right','arm-left','arm-right','paw-left','paw-right','paw-pad','eye-left','eye-right','lid-left','lid-right','lash-left','lash-right','brow-left','brow-right','mouth','mouth-open','props-back','props-front','charm','ground-shadow'])this.parts[id]=root.querySelector<SVGElement>(`#${id}`)!;
  this.pupils=Array.from(root.querySelectorAll<SVGElement>('.pupil'));
  this.system.addEventListener('change',()=>this.refresh());
 }
 pet(){
  if(this.suspended) return;
  this.follow.earL += 22;
  this.follow.earR -= 22;
  this.follow.charm += 25;
  if(this.rig==='cat') this.follow.tail += 26;
  this.sleeping = false;
  this.refresh();
 }
 observe(state:string,streak:number,token:string,personality:Personality,reduced:boolean,visible:boolean){
  this.advance(performance.now());
  const signature=`${state}:${streak}:${token}:${personality}`;const interrupted=signature!==this.observed;this.observed=signature;
  this.director.personality=personality;this.director.observe(state,streak,token,this.elapsed);
  const changed=this.reduced!==reduced||this.suspended===visible;
  this.reduced=reduced;this.suspended=!visible;
  if(changed||interrupted||(!this.frameId&&!this.timerId))this.refresh();
 }
 private advance(timestamp:number){
  if(this.previousTime&&!this.suspended)this.elapsed+=this.sleeping?Math.max(0,(timestamp-this.previousTime)/1000):Math.min(.08,Math.max(0,(timestamp-this.previousTime)/1000));
  this.previousTime=timestamp;
 }
 private refresh(){
  if(this.frameId)cancelAnimationFrame(this.frameId);clearTimeout(this.timerId);this.frameId=0;this.timerId=0;this.sleeping=false;this.previousTime=performance.now();this.rendered=0;
  const still=this.reduced||this.system.matches;
  this.root.closest<HTMLElement>('#app')!.dataset.motion=this.suspended?'paused':still?'reduced':'full';
  if(this.suspended)return;
  if(still){const f=this.director.still();this.paint(f.pose,f.prop||'',f.activity,f.label,1,true);return;}
  this.frameId=requestAnimationFrame(this.loop);
 }
 private loop=(timestamp:number)=>{
  this.frameId=0;if(this.suspended)return;
  // Observations use execution time; an earlier RAF timestamp must not rewind
  // that clock. Keep RAF-based paint deadlines: native profiling found that
  // execution-time paint deadlines reduce callbacks but worsen frame pacing.
  this.advance(performance.now());this.sleeping=false;
  // 30 Hz with a carried deadline: >=33.333 on a 60 Hz screen otherwise
  // alternates 33/50 ms frames and visibly stutters during slow head arcs.
  if(!this.rendered||timestamp-this.rendered>100)this.rendered=timestamp;
  if(timestamp+.75>=this.rendered){this.rendered+=1000/30;const f=this.director.tick(this.elapsed);this.paint(f.pose,f.prop||'',f.activity,f.label,1/30,false);}
  const quiet=this.director.quietDelay(this.elapsed);
  this.sleeping=quiet>.05;
  // Request frames at the authored 30 Hz, rather than waking at the monitor's
  // 60–240 Hz. Idle holds sleep until a real visual deadline; observe() wakes
  // them immediately for agent events or accessibility preference changes.
  const delay=this.sleeping?quiet*1000:Math.max(0,this.rendered-performance.now()-1);
  this.timerId=window.setTimeout(()=>{this.timerId=0;this.frameId=requestAnimationFrame(this.loop);},delay);
 };
 private paint(input:Pose,prop:string,activity:string,label:string,dt=1/30,still=false){
  let p={...input};
  // Overlap only on soft appendages. Hands and eyes must hit their authored marks.
  const goals={earL:p.earL-p.head*.16,earR:p.earR-p.head*.12,tail:p.tail-p.body*1.5,curl:p.curl,charm:-p.body*.6-p.head*.12};
  for(const k of Object.keys(goals) as (keyof typeof goals)[]){const speed=k==='tail'||k==='curl'?8:15;this.follow[k]=still?goals[k]:this.follow[k]+(goals[k]-this.follow[k])*(1-Math.exp(-speed*dt));}
  p.earL=this.follow.earL;p.earR=this.follow.earR;p.tail=this.follow.tail;p.curl=this.follow.curl;
  for(const key of Object.keys(p) as (keyof Pose)[]){const precision=key==='squash'?10000:100;p[key]=Math.round(p[key]*precision)/precision;}
  if(this.root.dataset.activity!==activity)this.root.dataset.activity=activity;
  if(this.root.dataset.performance!==label)this.root.dataset.performance=label;
  const set=(id:string,name:string,value:string)=>{const key=`${id}:${name}`;if(this.attributes.get(key)!==value){this.parts[id].setAttribute(name,value);this.attributes.set(key,value);}};
  const t=(id:string,value:string)=>set(id,'transform',value);
  this.renderFrame(p,set,t);
  if(this.rig==='robot')this.renderRing(p,set);else this.renderTail(p,set);
  this.renderFace(p,set,t);
  this.renderArms(p,set,t);
  if(prop!==this.activeProp){
   this.priorOpacity=this.lastPropOpacity;this.propChanged=this.elapsed;
   this.parts['props-back'].innerHTML=this.activeProp?props[this.activeProp]:'';
   this.parts['props-back'].setAttribute('transform',this.parts['props-front'].getAttribute('transform')||'');
   this.activeProp=prop;this.parts['props-front'].innerHTML=props[prop]||'';
  }
  const fade=still?1:Math.min(1,(this.elapsed-this.propChanged)/.3);
  set('props-back','opacity',String(still?0:Math.round(this.priorOpacity*(1-fade)*100)/100));
  this.lastPropOpacity=p.prop*fade;set('props-front','opacity',String(Math.round(this.lastPropOpacity*100)/100));
  if(prop==='glass')t('props-front',`translate(${201+p.rx} ${252+p.ry}) rotate(${p.right})`);
  else if(prop==='mote')t('props-front',`translate(${p.propX} ${p.propY}) rotate(${Math.round(Math.sin(this.elapsed*12)*14)})`);
  else t('props-front',`translate(0 ${p.propY+12*(1-p.prop)})`);
 }
 // Body, head and face placement are identical for both characters; the same
 // pivots keep the director's authored beats readable on either rig.
 private renderFrame(p:Pose,set:Painter,t:Mover){
  t('rig',`translate(${p.x} 0)`);
  t('torso',`translate(0 ${p.y}) rotate(${p.body} 160 267)`);
  t('body',`translate(160 267) scale(${1+(1-p.squash)*.35} ${p.squash}) translate(-160 -267)`);
  t('head',`translate(${p.hx} ${p.hy}) rotate(${p.head} 160 190)`);
  t('face-features',`translate(${p.turn*.65} ${Math.abs(p.turn)*.07}) translate(160 145) scale(${1-Math.abs(p.turn)*.004} 1) translate(-160 -145)`);
  t('muzzle',`translate(${p.turn*.22} ${p.jaw*.7})`);
  t('ear-left',`rotate(${p.earL} 110 96)`);t('ear-right',`rotate(${p.earR} 212 96)`);
  t('charm',`rotate(${Math.round(this.follow.charm*100)/100} 160 211)`);
  set('ground-shadow','opacity',String(Math.round(clamp(1+p.y*.014,.65,1)*100)/100));
 }
 private renderTail(p:Pose,set:Painter){
  // A bending tail, with a stable root; no rigid windscreen-wiper rotation.
  const q=p.tail,c=p.curl;
  const d=`M213 255 C${264-c*.5} ${268+q*.3} ${289-c*.36} ${241+c*.4+q*.65} ${278-c*.65} ${214+c*1.06+q} C${275-c*.72} ${207+c*1.13+q} ${269-c*.9} ${206+c*1.04+q} ${269-c} ${212+c*.95+q}`;
  set('tail-outline','d',d);set('tail-fur','d',d);
  set('tail-light','d',`M219 251 C${262-c*.5} ${263+q*.3} ${283-c*.36} ${240+c*.4+q*.65} ${275-c*.65} ${216+c*1.06+q}`);
 }
 private renderRing(p:Pose,set:Painter){
  // Nova's hover pad: the tail channel bobs the ring, curl spreads it flat.
  // The ellipses scale about their shared center; no path surgery needed.
  const ring=`translate(0 ${p.tail*.32}) translate(160 272) scale(${1+p.curl*.004} ${1-p.curl*.005}) translate(-160 -272)`;
  set('tail-outline','transform',ring);set('tail-fur','transform',ring);set('tail-light','transform',ring);
 }
 // Iris and highlight retain volume. The lid boundary, not the eyeball,
 // closes. Left/right apertures and brow pressure can act asymmetrically.
 private renderFace(p:Pose,set:Painter,t:Mover){
  const g=this.rig==='robot'?ROBOT_FACE:CAT_FACE;
  for(const [side,cx,offset] of [['left',g.left,p.eyeL],['right',g.right,p.eyeR]] as const){
   const open=clamp(p.eyes+offset,0,1.15),left=cx-g.w,right=cx+g.w;
   const upper=g.cy-g.hT*open+3*p.brow,lower=g.cy+g.hB*open;
   const innerPressure=p.brow*7;
   const top=`M${left} ${g.cy} C${left+4} ${upper+(side==='left'?0:innerPressure)} ${right-4} ${upper+(side==='left'?innerPressure:0)} ${right} ${g.cy}`;
   set(`lid-${side}`,'d',`${top} C${right-4} ${lower} ${left+4} ${lower} ${left} ${g.cy}Z`);
   const closed=clamp((.24-open)/.24,0,1),crease=p.mouth>.2?g.smileCrease:g.crease;
   const lashY=upper+(crease-upper)*closed;
   // The last slit closes before the smile crease settles; otherwise tiny
   // amber fragments linger underneath an apparently closed eyelid.
   set(`eye-${side}`,'opacity',String(Math.round(clamp((open-.08)/.16,0,1)*100)/100));
   set(`lash-${side}`,'d',`M${left+closed*3} ${g.cy} C${left+4} ${lashY} ${right-4} ${lashY} ${right-closed*3} ${g.cy}`);
   set(`lash-${side}`,'stroke',`rgb(${Math.round(g.lash[0]+(g.lashTo[0]-g.lash[0])*closed)} ${Math.round(g.lash[1]+(g.lashTo[1]-g.lash[1])*closed)} ${Math.round(g.lash[2]+(g.lashTo[2]-g.lash[2])*closed)})`);
   set(`brow-${side}`,'d',`M${cx-14} ${g.brow+p.brow*(side==='left'?-1:5)} Q${cx} ${g.brow-5+p.brow*5} ${cx+13} ${g.brow+p.brow*(side==='left'?5:-1)}`);
  }
  const gaze=`translate(${p.gazeX*.55} ${p.gazeY*.42})`;
  if(this.attributes.get('gaze')!==gaze){this.pupils.forEach(e=>e.setAttribute('transform',gaze));this.attributes.set('gaze',gaze);}
  if(g.mouthStyle==='cat')set('mouth','d',`M160 ${g.mouthBase}v5m0 0q-7 ${7+p.mouth*6}-13 ${1+p.mouth*2}m13 ${-1-p.mouth*2}q7 ${7+p.mouth*6} 13 ${1+p.mouth*2}`);
  else set('mouth','d',`M148 ${g.mouthBase}Q160 ${g.mouthBase+p.mouth*9} 172 ${g.mouthBase}`);
  set('mouth','opacity',String(Math.round((1-p.jaw)*100)/100));
  set('mouth-open','opacity',String(p.jaw));
  t('mouth-open',`translate(0 ${g.openBase*(1-p.jaw)}) scale(1 ${Math.max(.01,p.jaw)})`);
 }
 private renderArms(p:Pose,set:Painter,t:Mover){
  const armY=this.rig==='robot'?218:217;
  for(const [side,sx,x,dx,dy,rotation,bend] of [['left',116,119,p.lx,p.ly,p.left,-15],['right',204,201,p.rx,p.ry,p.right,15]] as const){
   const handX=x+dx,handY=252+dy;
   t(`paw-${side}`,`translate(${handX} ${handY}) rotate(${rotation})`);
   set(`arm-${side}`,'d',`M${sx} ${armY} Q${sx+bend+dx*.38} ${armY+18+dy*.5} ${handX} ${handY-5}`);
   set(`arm-${side}`,'stroke-width',String(this.rig==='robot'?19:21));
  }
  set('paw-pad','opacity',String(p.palm));
 }
}
