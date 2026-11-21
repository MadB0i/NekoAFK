(() => {
  const $=id=>document.getElementById(id),host=window.desktopHost=new BrowserDesktopHost($('characterWindow'),$('dockWindow'));
  host.state='editing';host.prefs.passthrough=false;host.prefs.characterVisible=true;host.prefs.dockVisible=false;host.layout();
  let playing=true,selected='lower-leg',nodes=[];
  const send=payload=>host.send(host.character,'editing-control',payload);
  function togglePlay(){playing=!playing;send({playing});$('play').textContent=playing?'Pause animation':'Play animation';$('play').setAttribute('aria-pressed',String(playing));}
  $('play').onclick=togglePlay;
  $('time').oninput=e=>{playing=false;send({time:+e.target.value,playing:false});$('play').textContent='Play animation';$('play').setAttribute('aria-pressed','false');};
  $('slow').onchange=e=>send({rate:e.target.checked?.25:1});
  $('original').onchange=e=>send({original:e.target.checked});
  $('debug').onchange=e=>{$('rigInspector').hidden=!e.target.checked;send({debug:e.target.checked,selected});};
  $('checker').onchange=e=>$('desktop').classList.toggle('checker',e.target.checked);
  $('scale').oninput=e=>{host.setScale(+e.target.value/100);$('scaleValue').textContent=e.target.value+'%';};
  $('reset').onclick=()=>{host.reset();host.prefs.dockVisible=false;host.layout();$('scale').value=100;$('scaleValue').textContent='100%';};
  host.onRenderer=p=>{$('rendererStatus').textContent=p.renderer==='editing-rig'?'Editing rig · visual acceptance pending':p.reason==='load-failed'?'Support asset failed to load · original retained':'Preparing editing rig…';};
  window.addEventListener('message',e=>{
    if(e.origin!==location.origin||e.source!==host.character.contentWindow||e.data?.channel!=='neko-desktop-v1'||e.data.type!=='editing-frame')return;
    const p=e.data.payload;nodes=p.nodes;$('time').value=p.time;$('timeValue').textContent=`${p.time.toFixed(2)} / 24s`;
    $('motionStatus').textContent=p.blink?`Blink · ${p.eyeFrame} eyelids`:'Seated · knee swing · phone scroll';
    if(!$('jointTree').children.length){const walk=(parent,depth)=>nodes.filter(n=>n.parent===parent).forEach(n=>{const b=document.createElement('button');b.textContent=`${'· '.repeat(depth)}${n.id}`;b.title=n.label;b.dataset.node=n.id;b.onclick=()=>{selected=n.id;send({selected});};$('jointTree').append(b);walk(n.id,depth+1);});walk(null,0);}
    for(const b of $('jointTree').children)b.setAttribute('aria-pressed',String(b.dataset.node===p.selected));
    const n=nodes.find(n=>n.id===p.selected);$('jointReadout').textContent=n?`${n.label}\nPivot ${n.pivot.join(', ')} · ${n.angle.toFixed(2)}°`:'';
  });
  document.addEventListener('keydown',e=>{if(e.repeat||e.target.closest('input,button,a'))return;if(e.code==='Space'){e.preventDefault();togglePlay();}if(e.key.toLowerCase()==='g'){$('debug').click();}});
  $('scale').value=host.prefs.scale*100;$('scaleValue').textContent=Math.round(host.prefs.scale*100)+'%';host.publish();
})();
