(() => {
  'use strict';
  class NekoCharacter {
    constructor({stage,position,canvas,setRasterState}) {
      this.stage=stage;this.position=position;this.canvas=canvas;this.setRasterState=setRasterState;
      this.raster=position.querySelector('.neko-motion');
      this.rig=null;this.state='editing';this.revision=0;this.destroyed=false;this.visible=true;
      this.status={renderer:'raster',reason:'initial'};this.publish();
    }
    publish() {
      this.stage.dataset.renderer=this.status.renderer;
      this.stage.dataset.rigStatus=this.status.reason;
    }
    setVisible(visible){this.visible=!!visible;this.rig?.setActive(this.visible);}
    setState(name) {
      if (this.destroyed || !NekoRigContract.states.includes(name)) return;
      this.state=name;
      this.stage.setAttribute('aria-label',`Neko, cat-girl companion — ${name}`);
      if (this.rig) this.rig.setState(name);
      else this.setRasterState(name);
    }
    async useRaster(reason='forced-raster') {
      if (this.destroyed) return;
      const revision=++this.revision;
      // Decode/show the correct fallback before retiring the current rig.
      let state;
      do {
        state=this.state;
        await this.setRasterState(state,{immediate:true});
        if (this.destroyed || revision!==this.revision) return;
      } while (state!==this.state);
      this.rig?.destroy();this.rig=null;this.raster.hidden=false;
      this.status={renderer:'raster',reason};this.publish();
    }
    async loadRig(url='./assets/neko/rig/v2/manifest.json') {
      if (this.destroyed) return false;
      const revision=++this.revision;
      let candidate;
      try {
        const absolute=new URL(url,location.href);
        if (absolute.origin!==location.origin) throw new Error('Rig manifest must be local');
        const response=await fetch(absolute,{cache:'no-store'});
        if (!response.ok) throw new Error(`Rig manifest HTTP ${response.status}`);
        const pack=await response.json();
        if (this.destroyed || revision!==this.revision) return false;
        if (pack.approved!==true) {await this.useRaster('awaiting-assets');return false;}
        candidate=await LayeredNeko.prepare(pack,this.canvas,absolute.href);
        if (this.destroyed || revision!==this.revision) {candidate.destroy();return false;}
        this.stage.dataset.rigSnap='';
        candidate.setState(this.state);
        this.position.append(candidate.root);
        this.rig?.destroy();this.rig=candidate;
        this.raster.hidden=true;
        candidate.start();
        candidate.setActive(this.visible);
        // Establish the authored first pose before allowing future pose transitions.
        void candidate.root.offsetWidth;
        delete this.stage.dataset.rigSnap;
        this.status={renderer:'rig',reason:'ready'};this.publish();
        return true;
      } catch (error) {
        candidate?.destroy();
        if (this.destroyed || revision!==this.revision) return false;
        await this.useRaster('invalid-or-missing-assets');
        this.status.detail=error.message;
        return false;
      }
    }
    destroy() {
      this.destroyed=true;++this.revision;
      this.rig?.destroy();this.rig=null;this.raster.hidden=false;
    }
  }
  window.NekoCharacter=NekoCharacter;
})();
