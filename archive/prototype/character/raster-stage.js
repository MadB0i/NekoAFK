// Static fallback and shared stage registration. No whole-image idle animation.
(() => {
  function create(nekoStage) {
    const nimgs=[...nekoStage.querySelectorAll('.neko-layer')];
// Measured from the ORIGINAL PNGs, alpha > 0 (including faint edge pixels).
// contact is the chair's centre column / wheel-floor landmark. It avoids shifting
// the chair when a pose's tail, feet or raised hands change the silhouette.
// These small registration corrections are fixed geometry, never animated.
const NEKO_MANIFEST = {
  editing:   { size:[1138,1382], bounds:[49,7,1062,1359], contact:[642,1353] },
  testing:   { size:[1122,1402], bounds:[49,1,1072,1402], contact:[622,1395] },
  failed:    { size:[1122,1402], bounds:[33,33,1114,1402], contact:[621,1353] },
  frustrated:{ size:[1122,1402], bounds:[0,15,1119,1402], contact:[613,1355] },
  verifying: { size:[1122,1402], bounds:[48,11,1056,1402], contact:[599,1370] },
  success:   { size:[1122,1402], bounds:[0,0,1122,1402], contact:[607,1388] },
};

// One shared envelope contains EVERY pose. Changing state never refits the box.
const frames = Object.values(NEKO_MANIFEST);
const gutter = 24; // source pixels, room for alpha edges + subpixel breathing
const halfWidth = Math.max(...frames.flatMap(m => [m.contact[0]-m.bounds[0], m.bounds[2]-m.contact[0]])) + gutter;
const above = Math.max(...frames.map(m => m.contact[1]-m.bounds[1])) + gutter;
const below = Math.max(...frames.map(m => m.bounds[3]-m.contact[1])) + gutter;
const envelope = { width:halfWidth*2, height:above+below };
const position = nekoStage.querySelector('.neko-position');
nekoStage.style.setProperty('--neko-floor', `${above/envelope.height*100}%`);
nimgs.forEach(img => {
  const m = NEKO_MANIFEST[img.dataset.k];
  img.style.width = `${m.size[0]/envelope.width*100}%`;
  img.style.height = `${m.size[1]/envelope.height*100}%`;
  img.style.left = `${(halfWidth-m.contact[0])/envelope.width*100}%`;
  img.style.top = `${(above-m.contact[1])/envelope.height*100}%`;
});
function fitNekoStage() {
  const scale = Math.min(nekoStage.clientWidth/envelope.width, nekoStage.clientHeight/envelope.height);
  position.style.width = `${envelope.width*scale}px`;
  position.style.height = `${envelope.height*scale}px`;
  // The contact shadow sits on the same floor, outside the breathing wrapper.
  nekoStage.querySelector('.neko-shadow').style.bottom = `${below*scale-5}px`;
}
const observer=new ResizeObserver(fitNekoStage); observer.observe(nekoStage);
fitNekoStage();

const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
const decoded = new Map(nimgs.map(img => [img.dataset.k, img.decode().then(() => true).catch(() => false)]));
let swapVersion = 0;
let swapTimer;
let displayedState = 'editing';
async function swapNeko(name, {immediate=false} = {}) {
  const version = ++swapVersion;
  // Keep the current image until the incoming asset can actually paint.
  if (!await decoded.get(name) || version !== swapVersion) return;
  if (displayedState === name && !immediate) return;
  displayedState = name;
  clearTimeout(swapTimer);
  nekoStage.setAttribute('aria-label', `Neko, cat-girl companion — ${name}`);
  if (immediate) {
    // Atomic renderer rollback must never reveal a half-faded fallback.
    nimgs.forEach(img => {
      img.style.transition='none';
      img.classList.remove('is-leaving');
      img.classList.toggle('is-active',img.dataset.k===name);
    });
    void position.offsetWidth;
    nimgs.forEach(img => img.style.removeProperty('transition'));
    delete nekoStage.dataset.transitioning;
    return;
  }
  nekoStage.dataset.transitioning = 'true';
  nimgs.forEach(img => {
    const wasVisible = img.classList.contains('is-active') || img.classList.contains('is-leaving');
    img.classList.toggle('is-leaving', wasVisible && img.dataset.k !== name);
    img.classList.toggle('is-active', img.dataset.k === name);
  });
  // Retire ALL outgoing layers, including interrupted rapid selections.
  const duration = reducedMotion.matches ? 0 : parseFloat(getComputedStyle(nekoStage).getPropertyValue('--neko-crossfade'));
  swapTimer = setTimeout(() => {
    nimgs.forEach(img => img.classList.remove('is-leaving'));
    delete nekoStage.dataset.transitioning;
  }, duration + 20);
}


    return {position,canvas:{...envelope,floor:above},images:nimgs,manifest:NEKO_MANIFEST,setState:swapNeko,destroy(){observer.disconnect();clearTimeout(swapTimer);++swapVersion;}};
  }
  window.NekoRasterStage={create};
})();
