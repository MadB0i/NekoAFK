const nekoStage=document.getElementById('nekoStage');
const rasterStage=NekoRasterStage.create(nekoStage);
const nekoCharacter=new NekoCharacter({stage:nekoStage,position:rasterStage.position,canvas:rasterStage.canvas,setRasterState:rasterStage.setState});
window.NekoSurface={setState:name=>nekoCharacter.setState(name)};
NekoSurfaceBridge.makeDraggable(nekoStage);
NekoSurfaceBridge.listen(({type,payload})=>{
  if(type==='state') NekoSurface.setState(payload.state);
  if(type==='renderer-request') NekoSurfaceBridge.send('renderer',nekoCharacter.status);
  if(type==='visibility') nekoCharacter.setVisible(payload.visible);
});
nekoCharacter.setState('editing');
const mode=new URLSearchParams(location.search).get('character');
(mode==='raster' ? nekoCharacter.useRaster() : nekoCharacter.loadRig()).then(()=>{
  NekoSurfaceBridge.send('renderer',nekoCharacter.status);
});
NekoSurfaceBridge.send('ready');
window.addEventListener('pagehide',()=>{nekoCharacter.destroy();rasterStage.destroy();},{once:true});
