// One editing pose. Each cutout owns a joint; root and chair never animate.
(() => {
  const NS='http://www.w3.org/2000/svg',spec=NekoEditingParts;
  const svg=(tag,attrs={})=>{const el=document.createElementNS(NS,tag);for(const [k,v] of Object.entries(attrs))el.setAttribute(k,v);return el;};
  const I=()=>new DOMMatrix();
  const pulse=(t,start,duration)=>{const u=(t-start)/duration;return u>0&&u<1?Math.sin(Math.PI*u)**2:0;};
  const wave=(t,period,amplitude)=>Math.sin(t*Math.PI*2/period)*amplitude;
  class EditingNeko {
    static async prepare(position){
      const sources={original:'assets/neko/neko-editing.png',repair:'assets/neko/rig/editing-v1/repair-plate.png',blink:'assets/neko/rig/editing-v1/blink-closed.png',half:'assets/neko/rig/editing-v1/blink-half.png'};
      await Promise.all(Object.values(sources).map(src=>{const image=new Image();image.src=src;return image.decode();}));
      return new EditingNeko(position,sources);
    }
    constructor(position,sources){
      this.time=0;this.playing=true;this.visible=true;this.last=null;this.frame=null;this.debug=false;this.selected='lower-leg';this.original=false;this.rate=1;this.sources=sources;
      this.root=svg('svg',{viewBox:'0 0 1274 1491','aria-hidden':'true',class:'editing-rig'});
      this.scene=svg('g',{transform:'translate(-5 65)'});this.defs=svg('defs');this.root.append(this.defs,this.scene);
      this.nodes=new Map();this.layers=new Map();this.matrices=new Map();this.reduced=matchMedia('(prefers-reduced-motion: reduce)');
      const image=src=>svg('image',{href:src,width:1138,height:1382,preserveAspectRatio:'none'});
      const mask=(id,white=true)=>{const m=svg('mask',{id,maskUnits:'userSpaceOnUse',x:-50,y:-50,width:1250,height:1500,'mask-type':'luminance'});m.append(svg('rect',{x:-50,y:-50,width:1250,height:1500,fill:white?'white':'black'}));this.defs.append(m);return m;};
      const staticMask=mask('editing-static');
      for(const part of spec.parts)staticMask.append(svg('path',{d:part.d,fill:'black',stroke:'white','stroke-width':1.6}));
      // Original chair pixels remain on top; generated plates only repair hidden surfaces.
      const repairMask=mask('editing-repair',false);
      for(const id of ['head','hair-back','torso','upper-leg','lower-leg','foot','second-foot','phone-hand','thumb','hair-tips']){const p=spec.parts.find(p=>p.id===id);repairMask.append(svg('path',{d:p.d,fill:'white'}));}
      const underlay=image(sources.repair);underlay.setAttribute('mask','url(#editing-repair)');this.scene.append(underlay);
      const stationary=image(sources.original);stationary.setAttribute('mask','url(#editing-static)');stationary.dataset.part='chair';this.scene.append(stationary);
      for(const id of spec.order){
        const p=spec.parts.find(p=>p.id===id),clip=svg('clipPath',{id:`editing-cut-${id}`,clipPathUnits:'userSpaceOnUse'});clip.append(svg('path',{d:p.d}));this.defs.append(clip);
        const ownMask=mask(`editing-own-${id}`);
        // Subtract all later occluding cutouts, even if they have another ancestor.
        for(const later of spec.order.slice(spec.order.indexOf(id)+1)){
          if(['eyes','mouth'].includes(later))continue;
          ownMask.append(svg('path',{d:spec.parts.find(p=>p.id===later).d,fill:'black',stroke:'white','stroke-width':1.6}));
        }
        ownMask.append(svg('path',{d:spec.chairFront,fill:'black'}));
        const group=svg('g',{'data-part':id}),cut=svg('g',{'clip-path':`url(#editing-cut-${id})`});
        const img=image(sources.original);img.setAttribute('mask',`url(#editing-own-${id})`);cut.append(img);group.append(cut);
        if(id==='eyes'){
          this.blinkImage=image(sources.blink);this.blinkHalf=image(sources.half);
          // Local registration from unchanged nose/brow/hair landmarks, not eyeball position.
          this.blinkImage.setAttribute('transform','matrix(1.003226 -0.000572 0.000572 1.003226 1.87222 0.13018)');
          this.blinkHalf.setAttribute('transform','matrix(0.98608 -0.002108 0.002108 0.98608 -5.94949 4.24208)');
          this.blinkImage.style.display=this.blinkHalf.style.display='none';cut.append(this.blinkHalf,this.blinkImage);
        }
        this.scene.append(group);this.nodes.set(id,{...p,group,angle:0});this.layers.set(id,cut);
      }
      const frontClip=svg('clipPath',{id:'editing-chair-front'});frontClip.append(svg('path',{d:spec.chairFront}));this.defs.append(frontClip);
      const foregroundChair=image(sources.original);foregroundChair.setAttribute('clip-path','url(#editing-chair-front)');this.scene.append(foregroundChair);
      this.reference=image(sources.original);this.reference.style.display='none';this.scene.append(this.reference);
      this.debugRoot=svg('g',{class:'editing-debug'});this.scene.append(this.debugRoot);
      this.lines=svg('g');this.boxes=svg('g');this.pivots=svg('g');this.debugRoot.append(this.lines,this.boxes,this.pivots);
      this.debugItems=new Map();
      for(const [id,node] of this.nodes){
        const line=svg('line'),box=svg('rect'),pivot=svg('g');pivot.append(svg('circle',{r:5}),svg('path',{d:'M-10 0H10 M0-10V10'}));
        const label=svg('text',{x:10,y:-9});label.textContent=id;pivot.append(label);
        this.lines.append(line);this.boxes.append(box);this.pivots.append(pivot);
        this.debugItems.set(id,{line,box,pivot});
      }
      position.append(this.root);this.onVisibility=()=>this.sync();this.onReduced=()=>this.sync();document.addEventListener('visibilitychange',this.onVisibility);this.reduced.addEventListener('change',this.onReduced);
      this.paint();this.sync();
    }
    setState(name){if(name!=='editing')return false;return true;}
    setActive(visible){this.visible=visible;this.sync();}
    control(payload){
      if(typeof payload.playing==='boolean')this.playing=payload.playing;
      if(Number.isFinite(payload.time))this.time=Math.max(0,Math.min(24,payload.time));
      if(typeof payload.debug==='boolean')this.debug=payload.debug;
      if(typeof payload.original==='boolean')this.original=payload.original;
      if(this.nodes.has(payload.selected))this.selected=payload.selected;
      if(Number.isFinite(payload.rate))this.rate=Math.max(.1,Math.min(1,payload.rate));
      this.paint();this.sync();
    }
    angles(t){
      const head=wave(t,12,.22),scroll=[2.8,7.4,12.6,20.2].reduce((s,v)=>s+pulse(t,v,.68),0);
      return {base:0,torso:wave(t,8,.035),'upper-leg':0,
        'lower-leg':wave(t,4,1.65)+wave(t,8,.18),foot:-wave(t,4,.20),
        'second-foot':(pulse(t,8.2,1.5)+pulse(t,18.1,1.8))*.9,
        tail:wave(t,8,.95)+wave(t,12,.25),head,
        'ear-left':(pulse(t,3.5,.38)-pulse(t,3.88,.22)*.3+pulse(t,16.2,.32))*.95,
        'ear-right':(pulse(t,10.3,.36)-pulse(t,10.66,.22)*.3)*1.1,
        'hair-back':-wave(t-.28,12,.12),'hair-front':wave(t-.16,12,.22)-head,
        'hair-tips':wave(t-.32,12,.35)-head,
        'phone-hand':-scroll*.08,thumb:scroll*1.8,mouth:0,eyes:0};
    }
    paint(){
      const t=this.reduced.matches?0:this.time,angles=this.angles(t);this.matrices.clear();
      const resolve=id=>{if(this.matrices.has(id))return this.matrices.get(id);const n=this.nodes.get(id),parent=n.parent?resolve(n.parent):I();const matrix=parent.translate(...n.pivot).rotate(angles[id]||0).translate(-n.pivot[0],-n.pivot[1]);this.matrices.set(id,matrix);return matrix;};
      for(const [id,node] of this.nodes){const m=resolve(id);node.angle=angles[id]||0;node.group.setAttribute('transform',`matrix(${m.a} ${m.b} ${m.c} ${m.d} ${m.e} ${m.f})`);}
      const elapsed=[2.1,6.7,11.4,17.6,22.7].map(start=>t-start).find(v=>v>=0&&v<.17);
      this.blink=elapsed!==undefined;this.eyeFrame=!this.blink?'open':elapsed<.035||elapsed>.115?'half':'closed';
      this.blinkImage.style.display=this.eyeFrame==='closed'?'':'none';this.blinkHalf.style.display=this.eyeFrame==='half'?'':'none';
      this.reference.style.display=this.original?'':'none';this.debugRoot.style.display=this.debug&&!this.original?'':'none';
      if(this.debug){for(const [id,n] of this.nodes){const m=resolve(id),pt=new DOMPoint(...n.pivot).matrixTransform(m),d=this.debugItems.get(id),selected=id===this.selected;d.pivot.setAttribute('transform',`translate(${pt.x} ${pt.y})`);d.pivot.classList.toggle('selected',selected);d.pivot.querySelector('text').style.display=selected?'':'none';const b=this.defs.querySelector(`#editing-cut-${id} path`).getBBox();Object.entries({x:b.x,y:b.y,width:b.width,height:b.height,transform:`matrix(${m.a} ${m.b} ${m.c} ${m.d} ${m.e} ${m.f})`}).forEach(([k,v])=>d.box.setAttribute(k,v));d.box.style.display=selected?'':'none';if(n.parent){const pn=this.nodes.get(n.parent),q=new DOMPoint(...pn.pivot).matrixTransform(resolve(n.parent));Object.entries({x1:q.x,y1:q.y,x2:pt.x,y2:pt.y}).forEach(([k,v])=>d.line.setAttribute(k,v));}else d.line.style.display='none';}}
      this.onFrame?.(this.snapshot());
    }
    snapshot(){return {clip:spec.clip.name,time:this.time,playing:this.playing&&!this.reduced.matches,blink:this.blink,eyeFrame:this.eyeFrame,selected:this.selected,nodes:[...this.nodes].map(([id,n])=>({id,parent:n.parent,label:n.label,pivot:n.pivot,angle:n.angle})),status:'candidate'};}
    sync(){cancelAnimationFrame(this.frame);this.frame=null;this.last=null;if(this.playing&&this.visible&&!document.hidden&&!this.reduced.matches&&!this.original)this.frame=requestAnimationFrame(t=>this.tick(t));}
    tick(now){
      // Recheck at the frame boundary: embedded webviews can deliver media changes late.
      if(!this.playing||!this.visible||document.hidden||this.reduced.matches||this.original){this.frame=null;this.last=null;this.paint();return;}
      const dt=this.last===null?0:Math.min((now-this.last)/1000,.05);this.last=now;this.time=(this.time+dt*this.rate)%24;this.paint();this.frame=requestAnimationFrame(t=>this.tick(t));
    }
    destroy(){cancelAnimationFrame(this.frame);this.frame=null;this.playing=false;document.removeEventListener('visibilitychange',this.onVisibility);this.reduced.removeEventListener('change',this.onReduced);this.root.remove();}
  }
  window.EditingNeko=EditingNeko;
})();
