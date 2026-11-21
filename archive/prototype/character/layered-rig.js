(() => {
  'use strict';
  const contract = window.NekoRigContract;
  // Conservative source-coordinate budgets. Tune with real art, never global wobble.
  const intensity = {editing:.75, testing:.35, failed:.3, frustrated:.2, verifying:.2, success:1};
  const blinkIntervals = [4100,5700,4800,6300];
  class LayeredNeko {
    static async prepare(pack, canvas, baseURL) {
      contract.validate(pack,canvas);
      const images = new Map(), jobs=[];
      const resolve = src => {
        const url = new URL(src,baseURL);
        if (url.origin !== location.origin || !/^https?:$/.test(url.protocol)) throw new Error('Rig assets must be local to this prototype');
        return url.href;
      };
      for (const layer of pack.layers) {
        const variants=new Map();images.set(layer.id,variants);
        for (const [key,view] of Object.entries(layer.variants)) {
          const img=new Image();img.alt='';img.draggable=false;img.hidden=true;
          img.src=resolve(view.src);variants.set(key,img);
          jobs.push(img.decode().then(() => {
            if (img.naturalWidth!==view.rect[2] || img.naturalHeight!==view.rect[3]) throw new Error(`Wrong export dimensions: ${layer.id}`);
          }));
        }
      }
      // Mount the actual decoded elements. Never change src while blinking/posing.
      await Promise.all(jobs);
      return new LayeredNeko(pack,canvas,images);
    }
    constructor(pack,canvas,images) {
      this.pack=pack; this.canvas=canvas;
      this.root=document.createElement('div'); this.root.className='neko-rig'; this.root.hidden=true;
      this.slots=new Map(); this.nodes=new Map(Object.keys(contract.parents).map(id=>[id,[]]));
      this.state=null; this.time=0; this.blinkIndex=0; this.nextBlink=blinkIntervals[0];
      this.blinkStart=null; this.blinkFrame=0; this.frame=null; this.last=null; this.running=false;
      this.amount=0; this.targetAmount=0;this.legAmount=0;this.legPhase=0;this.legSpeed=1;this.entryStart=0;
      this.reduced=matchMedia('(prefers-reduced-motion: reduce)');
      this.onVisibility=()=>this.syncActivity(); this.onPreference=()=>this.syncActivity();
      for (const layer of pack.layers) {
        const slot=document.createElement('div'); slot.className='neko-rig-slot'; slot.dataset.part=layer.id;
        const chain=[];
        for (let node=layer.node; node!=='root'; node=contract.parents[node]) chain.unshift(node);
        let parent=slot;
        for (const id of chain) {
          const pose=document.createElement('div'), motion=document.createElement('div'),gesture=document.createElement('div');
          pose.className='neko-rig-pose'; motion.className='neko-rig-motion';
          gesture.className='neko-rig-gesture';gesture.dataset.node=id;
          pose.dataset.node=id; motion.dataset.node=id;
          const pivot=pack.nodes[id];
          pose.style.transformOrigin=motion.style.transformOrigin=gesture.style.transformOrigin=`${pivot[0]/canvas.width*100}% ${pivot[1]/canvas.height*100}%`;
          parent.append(pose);pose.append(gesture);gesture.append(motion);parent=motion;
          this.nodes.get(id).push({pose,motion,gesture});
        }
        const variants=images.get(layer.id);
        for (const [key,img] of variants) {
          const [x,y,w,h]=layer.variants[key].rect;
          Object.assign(img.style,{left:`${x/canvas.width*100}%`,top:`${y/canvas.height*100}%`,width:`${w/canvas.width*100}%`,height:`${h/canvas.height*100}%`});
          parent.append(img);
        }
        this.root.append(slot);this.slots.set(layer.id,{slot,variants,key:null,img:null});
      }
      document.addEventListener('visibilitychange',this.onVisibility);
      this.reduced.addEventListener('change',this.onPreference);
    }
    showView(id,key) {
      const item=this.slots.get(id);
      item.slot.hidden=key===null;
      if (key===null || item.key===key) return;
      if (item.img) item.img.hidden=true;
      item.key=key;item.img=item.variants.get(key);item.img.hidden=false;
    }
    setState(name) {
      if (!contract.states.includes(name) || name===this.state) return;
      this.state=name;this.root.dataset.state=name;
      this.entryStart=this.time;
      const pose=this.pack.poses[name];
      pose.order.forEach((id,z)=>{this.slots.get(id).slot.style.zIndex=String(z);this.showView(id,pose.views[id]);});
      for (const [id,wrappers] of this.nodes) for (const {pose:element} of wrappers) element.style.transform=`rotate(${pose.rotations[id] || 0}deg)`;
      this.targetAmount=intensity[name];
      // A state change always restores its own eye frames; never inherit a half blink.
      this.blinkStart=null;this.blinkFrame=0;this.nextBlink=this.time+blinkIntervals[this.blinkIndex%blinkIntervals.length];
    }
    start() { this.running=true;this.root.hidden=false;this.syncActivity(); }
    setActive(active){this.running=active;this.syncActivity();}
    syncActivity() {
      if (this.frame!==null) cancelAnimationFrame(this.frame);
      this.frame=null;this.last=null;
      if (!this.running || document.hidden || this.reduced.matches) {
        this.applyMotion(0);
        this.blinkStart=null;this.blinkFrame=0;
        if (this.state) for (const eye of ['eye-far','eye-near']) this.showView(eye,this.pack.poses[this.state].views[eye]);
        this.nextBlink=this.time+blinkIntervals[this.blinkIndex%blinkIntervals.length];
        return;
      }
      this.frame=requestAnimationFrame(t=>this.tick(t));
    }
    tick(timestamp) {
      const delta=this.last===null ? 0 : Math.min(50,timestamp-this.last);
      this.last=timestamp;this.time+=delta;
      this.amount+=(this.targetAmount-this.amount)*Math.min(1,delta/300);
      const legTarget=this.state==='editing'?1:this.state==='testing'?.15:0;
      this.legAmount+=(legTarget-this.legAmount)*Math.min(1,delta/180);
      this.legSpeed+=((this.state==='testing'?.58:1)-this.legSpeed)*Math.min(1,delta/300);
      this.legPhase+=delta/1000*Math.PI*2/3.8*this.legSpeed;
      this.applyMotion(this.amount);
      const blink=this.pack.poses[this.state].blink;
      if (blink && this.time>=this.nextBlink && this.blinkStart===null) this.blinkStart=this.time;
      if (blink && this.blinkStart!==null) {
        const elapsed=this.time-this.blinkStart;
        const frame=elapsed<45 ? 1 : elapsed<110 ? 2 : elapsed<160 ? 1 : 0;
        if (frame!==this.blinkFrame) for (const eye of ['eye-far','eye-near']) this.showView(eye,blink[eye][frame]);
        this.blinkFrame=frame;
        if (elapsed>=160) {this.blinkStart=null;this.nextBlink=this.time+blinkIntervals[++this.blinkIndex%blinkIntervals.length];}
      }
      this.frame=requestAnimationFrame(t=>this.tick(t));
    }
    applyMotion(amount) {
      const t=this.time/1000, tau=Math.PI*2;
      const breath=(1-Math.cos(t*tau/5.8))*.5*amount;
      const twitchTime=(t+.7)%11;
      const twitch=amount && !['failed','frustrated'].includes(this.state) && twitchTime<.32 ? Math.sin(twitchTime/.32*tau)*1.2 : 0;
      const leg=amount ? this.legAmount : 0;
      const scrollPhase=t%6.7,scroll=scrollPhase<.7?Math.sin(scrollPhase/.7*Math.PI):0;
      const rotations={
        body:Math.sin(t*tau/9)*.16*amount+breath*.08,
        'tail-root':['failed','frustrated'].includes(this.state)?0:Math.sin(t*tau/7.5)*.7*amount,
        'tail-tip':['failed','frustrated'].includes(this.state)?0:Math.sin(t*tau/7.5-.55)*1.4*amount,
        'ear-near':twitch,
        'hand-near':this.state==='editing' ? Math.sin(t*tau/6.4)*.12*amount : 0,
        'shin-near':Math.sin(this.legPhase)*2.4*leg,
        'foot-near':Math.sin(t*tau/6.8-.4)*.45*leg,
        'thumb-near':this.state==='editing'?scroll*1.1*amount:0,
        'hair-back':Math.sin(t*tau/9-.6)*.15*amount,
        'hair-front':Math.sin(t*tau/9-.3)*.09*amount,
        'hair-lock-near':Math.sin(t*tau/9-.8)*.24*amount,
      };
      const entry=this.pack.poses[this.state]?.entry, gestures={};
      if(amount && entry){
        const progress=Math.min(1,(this.time-this.entryStart)/entry.duration);
        for(const track of entry.tracks){let value=0;for(let i=1;i<track.keys.length;i++){const a=track.keys[i-1],b=track.keys[i];if(progress>=a[0]&&progress<=b[0]){const u=(progress-a[0])/(b[0]-a[0]);value=a[1]+(b[1]-a[1])*(u*u*(3-2*u));break;}}gestures[track.node]=value;}
      }
      for (const [id,wrappers] of this.nodes) {
        const y=id==='body' ? -1.2*breath : 0;
        // Percent translation tracks source pixels through room contain scaling.
        const transform=`translateY(${y/this.canvas.height*100}%) rotate(${rotations[id] || 0}deg)`;
        for (const {motion,gesture} of wrappers){motion.style.transform=transform;gesture.style.transform=`rotate(${gestures[id]||0}deg)`;}
      }
    }
    destroy() {
      this.running=false;
      if (this.frame!==null) cancelAnimationFrame(this.frame);
      this.frame=null;
      document.removeEventListener('visibilitychange',this.onVisibility);
      this.reduced.removeEventListener('change',this.onPreference);
      this.root.remove();this.slots.clear();this.nodes.clear();
    }
  }
  window.LayeredNeko=LayeredNeko;
})();
