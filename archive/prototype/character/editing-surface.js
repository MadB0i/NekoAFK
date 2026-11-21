const nekoStage=document.getElementById('nekoStage');
const rasterStage=NekoRasterStage.create(nekoStage);
let editingRig=null,lastReport=-1;
window.NekoEditingSurface={control:payload=>editingRig?.control(payload)};
NekoSurfaceBridge.makeDraggable(nekoStage);
NekoSurfaceBridge.listen(({type,payload})=>{
  if(type==='editing-control')editingRig?.control(payload);
  if(type==='visibility')editingRig?.setActive(payload.visible);
  if(type==='renderer-request')NekoSurfaceBridge.send('renderer',{renderer:editingRig?'editing-rig':'raster',reason:editingRig?'candidate':'loading'});
});
EditingNeko.prepare(rasterStage.position).then(rig=>{
  editingRig=rig;window.editingRig=rig;rasterStage.position.querySelector('.neko-motion').hidden=true;
  nekoStage.dataset.renderer='editing-rig';rig.onFrame=data=>{if(!data.playing||Math.abs(data.time-lastReport)>.08){lastReport=data.time;NekoSurfaceBridge.send('editing-frame',data);}};
  rig.paint();NekoSurfaceBridge.send('renderer',{renderer:'editing-rig',reason:'candidate'});NekoSurfaceBridge.send('ready');
}).catch(error=>{nekoStage.dataset.renderer='raster';NekoSurfaceBridge.send('renderer',{renderer:'raster',reason:'load-failed',detail:error.message});});
NekoSurfaceBridge.send('ready');
window.addEventListener('pagehide',()=>{editingRig?.destroy();rasterStage.destroy();},{once:true});
