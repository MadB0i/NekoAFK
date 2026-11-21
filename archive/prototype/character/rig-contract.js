// Local asset contract. This does not contain or generate character artwork.
(() => {
  'use strict';
  const states = ['editing', 'testing', 'failed', 'frustrated', 'verifying', 'success'];
  const parents = {
    body:'root', head:'body', 'ear-far':'head', 'ear-near':'head',
    'tail-root':'root', 'tail-tip':'tail-root',
    'arm-far':'body', 'forearm-far':'arm-far', 'hand-far':'forearm-far',
    'pelvis':'root', 'thigh-near':'pelvis', 'shin-near':'thigh-near', 'foot-near':'shin-near',
    'thigh-far':'pelvis', 'shin-far':'thigh-far', 'foot-far':'shin-far',
    'hair-back':'head', 'hair-front':'head', 'hair-lock-near':'head',
    'phone':'hand-near', 'thumb-near':'hand-near',
    'arm-near':'body', 'forearm-near':'arm-near', 'hand-near':'forearm-near',
  };
  const slots = [
    ['chair-back','root'], ['chair-base','root'], ['tail-root','tail-root'], ['tail-tip','tail-tip'],
    ['hair-back','hair-back'], ['neck','body'], ['torso','body'],
    ['arm-far-upper','arm-far'], ['arm-far-lower','forearm-far'], ['hand-far','hand-far'],
    ['pelvis','pelvis'], ['leg-far-upper','thigh-far'], ['leg-far-lower','shin-far'], ['foot-far','foot-far'], ['leg-near-upper','thigh-near'], ['leg-near-lower','shin-near'], ['foot-near','foot-near'], ['chair-arm-far','root'], ['head-base','head'],
    ['ear-far','ear-far'], ['ear-near','ear-near'], ['eye-far','head'], ['eye-near','head'],
    ['brows','head'], ['mouth','head'], ['hair-front','hair-front'], ['chair-arm-near','root'],
    ['arm-near-upper','arm-near'], ['arm-near-lower','forearm-near'],
    ['hand-near-back','hand-near'], ['phone','phone'], ['hand-near-front','thumb-near'],
    ['hair-lock-near','hair-lock-near'], ['expression-accent','head'],
  ].map(([id,node]) => ({id,node}));
  const optional = new Set(['phone','hand-near-front','expression-accent']);
  const sameSet = (values, expected) => Array.isArray(values) && values.length === expected.length &&
    new Set(values).size === values.length && expected.every(id => values.includes(id));
  function validate(pack, canvas) {
    const fail = message => { throw new Error(`Invalid Neko rig: ${message}`); };
    if (pack.schemaVersion !== 2 || pack.approved !== true) fail('pack is not approved v2');
    if (!Array.isArray(pack.canvas) || pack.canvas.length !== 2 ||
        pack.canvas[0] !== canvas.width || pack.canvas[1] !== canvas.height ||
        !Array.isArray(pack.floor) || pack.floor[0] !== canvas.width/2 || pack.floor[1] !== canvas.floor) fail('canvas/floor registration');
    if (!pack.nodes || !sameSet(Object.keys(pack.nodes), Object.keys(parents))) fail('attachment nodes');
    for (const [id,pivot] of Object.entries(pack.nodes)) {
      if (!Array.isArray(pivot) || pivot.length !== 2 || !pivot.every(Number.isFinite) ||
          pivot[0]<0 || pivot[1]<0 || pivot[0]>canvas.width || pivot[1]>canvas.height) fail(`${id} pivot`);
    }
    if (!Array.isArray(pack.layers) || !sameSet(pack.layers.map(l=>l.id), slots.map(l=>l.id))) fail('34 unique layer slots required');
    const byId = new Map(pack.layers.map(l => [l.id,l]));
    for (const slot of slots) {
      const layer = byId.get(slot.id);
      if (layer.node !== slot.node || !layer.variants || !Object.keys(layer.variants).length) fail(`${slot.id} attachment/variants`);
      for (const view of Object.values(layer.variants)) {
        if (!view || typeof view.src !== 'string' || !view.src || !Array.isArray(view.rect) || view.rect.length !== 4 || !view.rect.every(Number.isFinite)) fail(`${slot.id} asset`);
        const [x,y,w,h] = view.rect;
        if (x<0 || y<0 || !Number.isInteger(w) || !Number.isInteger(h) || w<=0 || h<=0 || x+w>canvas.width || y+h>canvas.height) fail(`${slot.id} rect`);
      }
    }
    if (!pack.poses || !sameSet(Object.keys(pack.poses), states)) fail('all six poses required');
    for (const [name,pose] of Object.entries(pack.poses)) {
      if (!pose || !sameSet(pose.order, slots.map(l=>l.id)) || !pose.views || !sameSet(Object.keys(pose.views), slots.map(l=>l.id))) fail(`${name} order/views`);
      for (const slot of slots) {
        const key = pose.views[slot.id];
        if (key === null && optional.has(slot.id)) continue;
        if (typeof key !== 'string' || !Object.hasOwn(byId.get(slot.id).variants,key)) fail(`${name}/${slot.id} missing variant`);
      }
      if (pose.blink === null && name === 'success') { /* Closed happy eyes need no blink. */ }
      else for (const eye of ['eye-far','eye-near']) {
        const keys=pose.blink?.[eye];
        if (!Array.isArray(keys) || keys.length!==3 || keys[0]!==pose.views[eye] || keys.some(key => !Object.hasOwn(byId.get(eye).variants,key))) fail(`${name}/${eye} blink triplet`);
      }
      if (!pose.rotations || typeof pose.rotations !== 'object') fail(`${name} rotations`);
      for (const [node,angle] of Object.entries(pose.rotations)) {
        if (!Object.hasOwn(parents,node) || !Number.isFinite(angle) || Math.abs(angle)>90) fail(`${name}/${node} rotation (max 90 degrees)`);
      }
      // Optional authored state-entry curves, additive to the stable final pose.
      if (pose.entry !== undefined) {
        const clip=pose.entry;
        if (!clip || !Number.isFinite(clip.duration) || clip.duration<200 || clip.duration>1400 || !Array.isArray(clip.tracks)) fail(`${name} entry clip`);
        const used=new Set();
        for(const track of clip.tracks){
          if(!Object.hasOwn(parents,track.node)||used.has(track.node)||!Array.isArray(track.keys)||track.keys.length<2)fail(`${name} entry track`);
          used.add(track.node);let previous=-1;
          for(const key of track.keys){if(!Array.isArray(key)||key.length!==2||!key.every(Number.isFinite)||key[0]<0||key[0]>1||key[0]<=previous||Math.abs(key[1])>25)fail(`${name} entry keys`);previous=key[0];}
          if(track.keys[0][0]!==0||track.keys.at(-1)[0]!==1||track.keys.at(-1)[1]!==0)fail(`${name} entry must settle at zero`);
        }
      }
    }
    return pack;
  }
  window.NekoRigContract = Object.freeze({states, parents, slots, validate});
})();
