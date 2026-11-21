// Dev-only director. The character and dock surfaces contain none of this UI.
(() => {
  const $=id=>document.getElementById(id),states=Object.keys(NekoSimulation);
  const host=window.desktopHost=new BrowserDesktopHost($('characterWindow'),$('dockWindow'));
  let timer=null,start=0,frame=null;
  function select(state){host.setState(state);document.querySelectorAll('#states button').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.state===state)));}
  function stop(){clearTimeout(timer);cancelAnimationFrame(frame);timer=null;frame=null;$('demo').textContent='Play 10s sequence';$('demoTime').textContent='';}
  function play(){if(timer!==null){stop();return;}start=performance.now();let index=0;select(states[index]);$('demo').textContent='Stop sequence';const next=()=>{index++;if(index<states.length){select(states[index]);timer=setTimeout(next,10000/6);}else stop();};timer=setTimeout(next,10000/6);const tick=()=>{$('demoTime').textContent=`${Math.min(10,(performance.now()-start)/1000).toFixed(1)}s`;frame=requestAnimationFrame(tick);};tick();}
  states.forEach((state,i)=>{const b=document.createElement('button');b.dataset.state=state;b.textContent=`${i+1} ${state}`;b.onclick=()=>{stop();select(state);};$('states').append(b);});
  $('demo').onclick=play;$('reset').onclick=()=>{host.reset();sync();};$('scale').oninput=e=>{host.setScale(+e.target.value/100);sync();};
  for(const [id,key] of [['showCharacter','characterVisible'],['showDock','dockVisible'],['attached','attached'],['passthrough','passthrough']])$(id).onchange=e=>{host.setPreference(key,e.target.checked);sync();};
  $('checker').onchange=e=>$('desktop').classList.toggle('checker',e.target.checked);
  function sync(){for(const [id,key] of [['showCharacter','characterVisible'],['showDock','dockVisible'],['attached','attached'],['passthrough','passthrough']])$(id).checked=host.prefs[key];$('scale').value=host.prefs.scale*100;$('scaleValue').textContent=`${Math.round(host.prefs.scale*100)}%`;}
  host.onChange=sync;host.onRenderer=payload=>{$('rendererStatus').textContent=payload.renderer==='rig'?'Layered rig · joint animation active':'Raster fallback · articulated artwork pending';};
  document.addEventListener('keydown',e=>{if(e.target.closest('input,button,a')||e.repeat)return;if(states[+e.key-1]){stop();select(states[+e.key-1]);}else if(e.code==='Space'){e.preventDefault();play();}});select('editing');sync();
})();
