// Browser window boundary. Native capabilities are explicitly absent.
class BrowserDesktopHost {
  constructor(character,dock){
    this.character=character;this.dock=dock;this.state='editing';this.dockHeight=174;this.drag=null;
    this.capabilities=Object.freeze({native:false,alwaysOnTop:false,systemTray:false,globalHotkey:false,multiMonitor:false});
    this.prefs={scale:1,attached:true,characterVisible:true,dockVisible:true,passthrough:false};
    try{const p=JSON.parse(localStorage.getItem('neko-desktop-v2'));if(p){for(const k of ['attached','characterVisible','dockVisible'])if(typeof p[k]==='boolean')this.prefs[k]=p[k];if(Number.isFinite(p.scale))this.prefs.scale=Math.max(.65,Math.min(1.25,p.scale));if(Number.isFinite(p.x)&&Number.isFinite(p.y)){this.prefs.x=p.x;this.prefs.y=p.y;}if(Number.isFinite(p.dockX)&&Number.isFinite(p.dockY)){this.prefs.dockX=p.dockX;this.prefs.dockY=p.dockY;}}}catch{}
    const mode=new URLSearchParams(location.search).get('character');if(mode==='raster')character.src='character.html?character=raster';
    window.addEventListener('message',e=>this.receive(e));window.addEventListener('resize',()=>this.layout());for(const frame of [character,dock])frame.addEventListener('load',()=>this.publish());this.layout();
  }
  send(frame,type,payload={}){frame.contentWindow.postMessage({channel:'neko-desktop-v1',type,payload},location.origin);}
  publish(){this.send(this.character,'visibility',{visible:this.prefs.characterVisible});this.send(this.character,'renderer-request');this.send(this.character,'state',{state:this.state});this.send(this.dock,'state',NekoSimulation[this.state]);this.send(this.dock,'preferences',{attached:this.prefs.attached});}
  setState(state){if(!NekoSimulation[state])return;this.state=state;this.publish();}
  receive(e){if(e.origin!==location.origin||e.data?.channel!=='neko-desktop-v1')return;const frame=e.source===this.character.contentWindow?this.character:e.source===this.dock.contentWindow?this.dock:null;if(!frame)return;const {type,payload={}}=e.data;
    if(type==='ready')this.publish();if(type==='renderer'&&frame===this.character)this.onRenderer?.(payload);
    if(type==='resize'&&frame===this.dock&&Number.isFinite(payload.height)){this.dockHeight=Math.max(140,Math.min(360,payload.height));this.layout();}
    if(type==='dock-hide'&&frame===this.dock)this.setPreference('dockVisible',false);if(type==='dock-attach'&&frame===this.dock)this.setPreference('attached',!this.prefs.attached);
    if(type==='drag-start'){const r=frame.getBoundingClientRect();this.drag={frame,x:r.x,y:r.y};if(frame===this.dock){this.prefs.attached=false;this.publish();}}
    if(type==='drag-move'&&this.drag?.frame===frame&&Number.isFinite(payload.dx)&&Number.isFinite(payload.dy)){this.prefs[frame===this.character?'x':'dockX']=this.drag.x+payload.dx;this.prefs[frame===this.character?'y':'dockY']=this.drag.y+payload.dy;this.layout();}
    if(type==='drag-end'){this.drag=null;this.save();}
  }
  bounds(){return {left:280,top:112,right:innerWidth-28,bottom:innerHeight-86};}
  layout(){const a=this.bounds(),p=this.prefs,h=Math.min(600*p.scale,a.bottom-a.top),w=h*1274/1491;const clamp=(v,min,max)=>Math.max(min,Math.min(max,v));
    p.x=clamp(p.x??a.right-w,a.left,a.right-w);p.y=clamp(p.y??a.bottom-h,a.top,a.bottom-h);
    Object.assign(this.character.style,{left:p.x+'px',top:p.y+'px',width:w+'px',height:h+'px',pointerEvents:p.passthrough?'none':'auto'});this.character.hidden=!p.characterVisible;
    if(p.attached){p.dockX=p.x-276;p.dockY=p.y+h-this.dockHeight-22;if(p.dockX<a.left)p.dockX=p.x+w+16;}
    p.dockX=clamp(p.dockX??a.left,a.left,a.right-260);p.dockY=clamp(p.dockY??a.bottom-this.dockHeight,a.top,a.bottom-this.dockHeight);
    Object.assign(this.dock.style,{left:p.dockX+'px',top:p.dockY+'px',width:'260px',height:this.dockHeight+'px'});this.dock.hidden=!p.dockVisible;this.save();this.onChange?.();
  }
  setScale(value){if(!Number.isFinite(value))return;const style=this.character.style,r={x:parseFloat(style.left),y:parseFloat(style.top),width:parseFloat(style.width),height:parseFloat(style.height)};r.bottom=r.y+r.height;this.prefs.scale=Math.max(.65,Math.min(1.25,value));const h=Math.min(600*this.prefs.scale,this.bounds().bottom-this.bounds().top),w=h*1274/1491;this.prefs.x=r.x+r.width/2-w/2;this.prefs.y=r.bottom-h;this.layout();}
  setPreference(key,value){if(!['characterVisible','dockVisible','attached','passthrough'].includes(key))return;this.prefs[key]=!!value;this.layout();this.publish();}
  reset(){this.prefs={scale:1,attached:true,characterVisible:true,dockVisible:true,passthrough:false};this.layout();this.publish();}
  save(){try{localStorage.setItem('neko-desktop-v2',JSON.stringify(this.prefs));}catch{}}
}
