// NekoAFK visual prototype — simulated agent states, no backend.
const stage = document.getElementById('stage');
const nekoStage = document.getElementById('nekoStage');
const nimgs = [...nekoStage.querySelectorAll('.neko-layer')];
const stateLabel = document.getElementById('stateLabel');
const stateChip = document.getElementById('stateChip');
const bubbleText = document.getElementById('bubbleText');
const monBody = document.getElementById('monBody');
const monTitle = document.getElementById('monTitle');
const monPhase = document.getElementById('monPhase');
const monTime = document.getElementById('monTime');
const capPhase = document.getElementById('capPhase');
const capTasks = document.getElementById('capTasks');
const capConf = document.getElementById('capConf');
const taskDots = document.getElementById('taskDots');
const taskCount = document.getElementById('taskCount');
const confChip = document.getElementById('confChip');
const failLine = document.getElementById('failLine');
const ledFill = document.getElementById('ledFill');
const elapsedEl = document.getElementById('elapsed');
const autoBtn = document.getElementById('autoBtn');
const buttons = [...document.querySelectorAll('.dir-btns button[data-s]')];

const STATES = {
  editing: {
    label: 'EDITING', chip: '#ffb86b',
    bubble: 'scroll scroll…',
    cap: 'EDITING · phone scroll', tasks: '7 / 11 observable tasks', conf: '~64% · MEDIUM',
    monTitle: 'agent · opencode — editing', monPhase: 'EDITING', turn: 'turn 12:04',
    lines: [
      ['<span class="dim2">edit</span>  components/*.tsx <span class="amber2">×2</span>', ''],
      ['<span class="dim2">write</span>  hooks/use-neko.ts <span class="ok">ok</span>', ''],
      ['<span class="dim2">lsp</span>   diagnostics <span class="ok">clean</span>', ''],
      ['<span class="dim2">diff</span>   +84 −12 · 3 files', ''],
    ],
    dots: 7, total: 11, confShort: 'MED', fail: 'last run · <b>ok</b>', led: '64%',
  },
  testing: {
    label: 'TESTING', chip: '#7de8ff',
    bubble: 'hmm… watching.',
    cap: 'TESTING · eyes on monitor', tasks: '7 / 11 observable tasks', conf: '~72% · MEDIUM',
    monTitle: 'agent · opencode — running tests', monPhase: 'TESTING', turn: 'turn 12:06',
    lines: [
      ['<span class="amber2">vitest</span> run <span class="dim2">— 41 tests</span>', ''],
      ['<span class="ok">✓</span> neko-state.test.ts <span class="dim2">18 passed</span>', ''],
      ['<span class="dim2">…</span> verify.test.ts <span class="amber2">running</span>', ''],
      ['<span class="dim2">watch</span>  Neko glances up from phone', ''],
    ],
    dots: 7, total: 11, confShort: 'MED', fail: 'tests · <b>running…</b>', led: '72%',
  },
  failed: {
    label: 'FAILED', chip: '#ff5d5d',
    bubble: 'tch. again?!',
    cap: 'FAILED · ears down', tasks: '7 / 11 observable tasks', conf: '~58% · LOW',
    monTitle: 'agent · opencode — 1 test failed', monPhase: 'FAILED', turn: 'turn 12:07',
    lines: [
      ['<span class="bad">✗</span> verify.test.ts › <span class="bad">lied-about-done</span>', ''],
      ['<span class="dim2">bash</span>  vitest <span class="bad">exit 1</span>', ''],
      ['<span class="dim2">diff</span>   +86 −12 · 3 files', ''],
      ['<span class="amber2">note</span>  phone down · ears react', ''],
    ],
    dots: 7, total: 11, confShort: 'LOW', fail: 'last run · <b style="color:#ff7d7d">exit 1</b>', led: '58%',
  },
  frustrated: {
    label: 'FAILED ×3', chip: '#ff5d5d',
    bubble: 'THREE times?! same test?!',
    cap: 'FAILED ×3 · frustration rising', tasks: '7 / 11 observable tasks', conf: '~41% · LOW',
    monTitle: 'agent · opencode — same test ×3', monPhase: 'FIXING?', turn: 'turn 12:11',
    lines: [
      ['<span class="bad">✗✗✗</span> same test <span class="bad">×3 in 8 min</span>', ''],
      ['<span class="dim2">bash</span>  vitest <span class="bad">exit 1 ×3</span>', ''],
      ['<span class="amber2">hint</span>  maybe read the output?', ''],
      ['<span class="dim2">neko</span>  tail thump intensifies', ''],
    ],
    dots: 7, total: 11, confShort: 'LOW', fail: 'streak · <b style="color:#ff7d7d">✗✗✗ same test</b>', led: '41%',
  },
  verifying: {
    label: 'VERIFYING', chip: '#ffd66b',
    bubble: 'uh-huh. prove it.',
    cap: 'VERIFYING · “done” is not 100%', tasks: '10 / 11 observable tasks', conf: 'checking · NO CELEBRATION YET',
    monTitle: 'neko verify — independent check', monPhase: 'VERIFYING', turn: 'turn 12:14',
    lines: [
      ['<span class="amber2">claim</span>  agent: “done!” <span class="dim2">→ not trusted</span>', ''],
      ['<span class="dim2">check</span>  last exit <span class="ok">0</span> · todo <span class="ok">10/11</span>', ''],
      ['<span class="dim2">check</span>  diffstat +112 −18 · 4 files', ''],
      ['<span class="amber2">…</span>    holding celebration…', ''],
    ],
    dots: 10, total: 11, confShort: '…', fail: 'verify · <b style="color:#ffd66b">running</b>', led: '95%',
  },
  success: {
    label: 'DONE · VERIFIED', chip: '#7dff9a',
    bubble: '★ ok! you may celebrate.',
    cap: 'DONE · verified ✓', tasks: '11 / 11 observable tasks', conf: '100% · VERIFIED PASS',
    monTitle: 'agent · opencode — verified done', monPhase: 'DONE ✓', turn: 'turn 12:15',
    lines: [
      ['<span class="ok">✓✓✓</span> all checks <span class="ok">passed</span>', ''],
      ['<span class="dim2">tests</span>  41/41 · todo <span class="ok">11/11</span>', ''],
      ['<span class="dim2">diff</span>   +112 −18 · 4 files', ''],
      ['<span class="amber2">neko</span>  celebration unlocked ★', ''],
    ],
    dots: 11, total: 11, confShort: 'MAX', fail: 'verify · <b>PASS ✓</b>', led: '100%',
  },
};

let current = 'editing';
let autoTimer = null;

function renderDots(done, total) {
  taskDots.innerHTML = '';
  for (let i = 0; i < total; i++) {
    const d = document.createElement('i');
    if (i < done) d.className = 'done';
    if (i === done && done < total) d.className = 'now';
    taskDots.appendChild(d);
  }
}

function setState(name) {
  if (!STATES[name]) return;
  current = name;
  const s = STATES[name];
  stage.dataset.state = name;
  stateLabel.textContent = s.label;
  stateChip.querySelector('.dot').style.background = s.chip;
  stateChip.querySelector('.dot').style.boxShadow = `0 0 10px ${s.chip}`;
  bubbleText.textContent = s.bubble;
  // retrigger bubble animation
  const b = document.getElementById('bubble');
  b.style.animation = 'none'; void b.offsetWidth; b.style.animation = '';
  capPhase.textContent = s.cap;
  capTasks.textContent = s.tasks;
  capConf.textContent = s.conf;
  monTitle.textContent = s.monTitle;
  monPhase.textContent = s.monPhase;
  monTime.textContent = s.turn;
  monBody.innerHTML = s.lines.map(([html]) => `<div class="ln">${html}</div>`).join('');
  renderDots(s.dots, s.total);
  if (taskCount) taskCount.textContent = `${s.dots} / ${s.total}`;
  confChip.textContent = s.confShort;
  failLine.innerHTML = s.fail;
  ledFill.style.width = s.led;
  buttons.forEach(btn => {
    btn.classList.toggle('on', btn.dataset.s === name);
    btn.setAttribute('aria-pressed', String(btn.dataset.s === name));
  });
  nekoCharacter.setState(name); // The room does not know which renderer is active.
}

buttons.forEach(btn => btn.addEventListener('click', () => { stopAuto(); setState(btn.dataset.s); }));
document.addEventListener('keydown', e => {
  const map = { 1: 'editing', 2: 'testing', 3: 'failed', 4: 'frustrated', 5: 'verifying', 6: 'success' };
  if (map[e.key]) { stopAuto(); setState(map[e.key]); }
  if (e.code === 'Space' && e.target === document.body) { e.preventDefault(); toggleAuto(); }
});

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
new ResizeObserver(fitNekoStage).observe(nekoStage);
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

// Both renderers use the exact existing room envelope and floor registration.
const nekoCharacter = new NekoCharacter({
  stage:nekoStage, position, canvas:{...envelope,floor:above}, setRasterState:swapNeko,
});

// elapsed clock
let secs = 724;
setInterval(() => {
  secs++;
  const m = String(Math.floor(secs / 60)).padStart(2, '0');
  const s = String(secs % 60).padStart(2, '0');
  elapsedEl.textContent = `${m}:${s}`;
}, 1000);

// 10-second GIF loop includes all six authored states.
const RUN = [['editing', 1700], ['testing', 1600], ['failed', 1400], ['frustrated', 1400], ['verifying', 1800], ['success', 2100]];
function toggleAuto() { autoTimer ? stopAuto() : startAuto(); }
function startAuto() {
  autoBtn.classList.add('run'); autoBtn.textContent = '■ stop';
  let i = 0;
  const step = () => {
    const [name, dur] = RUN[i % RUN.length];
    setState(name);
    i++;
    autoTimer = setTimeout(step, dur);
  };
  step();
}
function stopAuto() {
  if (autoTimer) clearTimeout(autoTimer);
  autoTimer = null; autoBtn.classList.remove('run'); autoBtn.textContent = '▶ 10s run';
}
autoBtn.addEventListener('click', toggleAuto);

setState('editing');

// preview params (no UI): ?s=failed deep-links a state, ?run=1 starts the 10s loop
try {
  const q = new URLSearchParams(location.search);
  const s = q.get('s') === 'failed3' ? 'frustrated' : q.get('s');
  if (s && STATES[s]) setState(s);
  else if (q.get('run') === '1') startAuto();
} catch (e) { /* file:// or old browser — stay on editing */ }

// The pending manifest makes no part-image requests. An incomplete pack stays raster.
if (new URLSearchParams(location.search).get('character') === 'raster') {
  nekoCharacter.useRaster();
} else {
  nekoCharacter.loadRig();
}
