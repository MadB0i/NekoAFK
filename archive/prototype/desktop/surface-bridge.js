// Browser transport only. The native host will inject this same small surface API.
(() => {
  const channel='neko-desktop-v1';
  const send=(type,payload={})=>{
    if (parent!==window) parent.postMessage({channel,type,payload},location.origin);
  };
  const listen=callback=>window.addEventListener('message',event=>{
    if (event.source===parent && event.origin===location.origin && event.data?.channel===channel) callback(event.data);
  });
  function makeDraggable(element) {
    let start=null;
    element.addEventListener('pointerdown',event=>{
      if(event.button!==0 || event.target.closest('button,input,a')) return;
      start={x:event.screenX,y:event.screenY};element.setPointerCapture(event.pointerId);
      send('drag-start');event.preventDefault();
    });
    element.addEventListener('pointermove',event=>{
      if(start) send('drag-move',{dx:event.screenX-start.x,dy:event.screenY-start.y});
    });
    const finish=()=>{if(start){start=null;send('drag-end');}};
    element.addEventListener('pointerup',finish);element.addEventListener('pointercancel',finish);element.addEventListener('lostpointercapture',finish);
  }
  window.NekoSurfaceBridge={send,listen,makeDraggable};
})();
