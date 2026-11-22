import editingSrc from '../assets/kuro/editing.png';
import testingSrc from '../assets/kuro/testing.png';
import verifyingSrc from '../assets/kuro/verifying.png';
import successSrc from '../assets/kuro/success.png';
import failedSrc from '../assets/kuro/failed.png';
import frustratedSrc from '../assets/kuro/frustrated.png';
import repairSrc from '../assets/kuro/repair-plate.png';
import blinkClosedSrc from '../assets/kuro/blink-closed.png';
import blinkHalfSrc from '../assets/kuro/blink-half.png';
import previewSrc from '../assets/kuro/preview.png';
import type { Personality } from './director';

export { previewSrc as kuroPreviewUrl };

const NS = 'http://www.w3.org/2000/svg';
const svg = (tag: string, attrs: Record<string, string | number> = {}) => {
  const el = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, String(v));
  return el;
};
const I = () => new DOMMatrix();
const pulse = (t: number, start: number, duration: number) => {
  const u = (t - start) / duration;
  return u > 0 && u < 1 ? Math.sin(Math.PI * u) ** 2 : 0;
};
const wave = (t: number, period: number, amplitude: number) => Math.sin((t * Math.PI * 2) / period) * amplitude;

type ManifestFrame = { size: [number, number]; bounds: [number, number, number, number]; contact: [number, number] };
const MANIFEST: Record<string, ManifestFrame> = {
  editing:    { size: [1138, 1382], bounds: [49, 7, 1062, 1359], contact: [642, 1353] },
  testing:    { size: [1122, 1402], bounds: [49, 1, 1072, 1402], contact: [622, 1395] },
  failed:     { size: [1122, 1402], bounds: [33, 33, 1114, 1402], contact: [621, 1353] },
  frustrated: { size: [1122, 1402], bounds: [0, 15, 1119, 1402], contact: [613, 1355] },
  verifying:  { size: [1122, 1402], bounds: [48, 11, 1056, 1402], contact: [599, 1370] },
  success:    { size: [1122, 1402], bounds: [0, 0, 1122, 1402], contact: [607, 1388] },
};

const PARTS = [
  { id: 'base', parent: null, pivot: [570, 847], label: 'Pelvis / seated base', d: 'M381 678 Q462 637 595 699 L880 734 Q960 775 967 844 L956 912 Q759 961 546 905 L419 880 Z' },
  { id: 'tail', parent: null, pivot: [353, 758], label: 'Tail root', d: 'M369 595 C291 554 170 610 116 675 C51 750 25 846 89 904 C154 969 250 959 330 886 L371 791 Z' },
  { id: 'hair-back', parent: 'torso', pivot: [477, 310], label: 'Back hair', d: 'M490 175 C429 187 388 252 350 300 C305 344 278 380 288 429 L303 463 C268 494 200 528 153 501 C191 537 219 551 251 541 C194 587 177 626 225 695 L305 787 L406 810 L414 700 L403 558 L398 410 L479 341 Z M725 267 Q767 313 789 382 Q831 413 830 442 Q892 460 899 522 Q936 561 957 626 L975 671 L905 657 L836 558 L758 424 L697 344 Z' },
  { id: 'torso', parent: 'base', pivot: [491, 747], label: 'Torso / hip support', d: 'M357 312 Q438 322 489 294 L546 323 L624 365 Q657 368 689 355 L759 371 L787 424 L722 472 L660 535 L625 613 L555 683 L444 724 L357 681 L328 587 L302 474 L295 363 Z' },
  { id: 'upper-leg', parent: 'base', pivot: [485, 834], label: 'Upper leg / hip', d: 'M453 838 Q451 733 558 633 L731 527 Q780 476 820 503 L851 548 L809 626 L734 701 L659 805 L576 871 Z' },
  { id: 'lower-leg', parent: 'upper-leg', pivot: [797, 542], label: 'Lower leg / KNEE', d: 'M730 530 Q785 487 827 510 Q850 533 854 579 L879 652 Q902 713 921 770 L925 798 L876 842 L875 871 L880 904 L891 943 Q902 959 900 979 L913 1003 L929 1046 L809 1046 L814 1017 L813 1000 L810 979 L812 962 L805 942 L796 921 L790 902 L787 881 L781 863 L778 850 L749 863 Q725 884 711 854 L698 815 Q687 799 697 770 L705 741 Q674 740 664 711 Q651 686 665 643 L687 589 Z' },
  { id: 'foot', parent: 'lower-leg', pivot: [860, 1042], label: 'Swing foot / ankle', d: 'M806 1010 Q852 995 910 1010 L962 1080 L1030 1140 L1004 1200 L931 1196 Q898 1194 881 1178 Q868 1162 860 1134 L853 1120 L835 1111 Q808 1109 793 1097 Q788 1083 800 1054 Z' },
  { id: 'second-foot', parent: 'base', pivot: [608, 871], label: 'Resting foot / ankle', d: 'M617 835 Q585 829 550 841 L469 838 Q417 836 398 853 L370 896 Q363 919 382 931 L416 917 L475 908 L550 920 L611 914 L625 877 Z' },
  { id: 'head', parent: 'torso', pivot: [579, 351], label: 'Head / neck', d: 'M421 203 Q449 164 493 133 Q534 108 567 81 L637 4 L672 104 Q708 114 724 142 L811 153 L763 212 Q752 242 746 275 Q736 310 709 331 L660 371 L607 391 L563 365 L523 327 Q481 324 458 280 L454 248 Z' },
  { id: 'ear-left', parent: 'head', pivot: [616, 124], label: 'Screen-left ear', d: 'M550 110 Q578 52 637 4 Q658 49 671 110 L639 126 L601 128 Z' },
  { id: 'ear-right', parent: 'head', pivot: [732, 182], label: 'Screen-right ear', d: 'M709 139 Q751 140 811 153 L778 180 L749 221 L727 203 Z' },
  { id: 'hair-front', parent: 'head', pivot: [633, 151], label: 'Front fringe', d: 'M459 210 Q485 152 565 125 L630 112 Q696 119 714 165 L734 232 L720 286 L690 312 L706 257 L695 211 L661 184 Q608 225 567 228 L536 218 L528 266 L517 284 L507 239 L480 229 Z' },
  { id: 'hair-tips', parent: 'head', pivot: [552, 313], label: 'Front hair tips', d: 'M529 276 Q534 317 550 346 L559 382 L590 439 L590 487 L608 526 L578 509 L559 474 L549 403 L524 362 L510 326 Z M692 301 L722 317 Q758 365 774 394 L760 432 L724 415 L696 369 L675 345 Z' },
  { id: 'phone-hand', parent: 'torso', pivot: [692, 488], label: 'Phone hand / wrist', d: 'M683 453 L725 439 L767 424 L787 386 Q797 377 818 381 L874 388 L881 399 L851 446 L835 480 L784 492 L740 507 L710 520 L691 502 Z' },
  { id: 'thumb', parent: 'phone-hand', pivot: [727, 468], label: 'Scrolling thumb', d: 'M698 462 Q713 449 738 439 L760 429 Q770 430 772 437 L760 447 L737 459 L724 476 L707 481 Z' },
  { id: 'mouth', parent: 'head', pivot: [596, 303], label: 'Mouth', d: 'M575 284 L616 302 L612 320 L573 302 Z' },
  { id: 'eyes', parent: 'head', pivot: [617, 255], label: 'Eyes / blink', d: 'M553 212 Q580 205 609 240 L602 262 Q569 251 550 229 Z M626 251 Q658 248 678 274 L664 295 Q639 288 621 272 Z' },
];
const ORDER = ['tail', 'hair-back', 'base', 'torso', 'upper-leg', 'lower-leg', 'foot', 'second-foot', 'head', 'ear-left', 'ear-right', 'hair-front', 'hair-tips', 'phone-hand', 'thumb', 'mouth', 'eyes'];
const CHAIR_FRONT = 'M236 743 Q231 726 249 720 Q326 704 403 721 Q431 727 440 748 L440 765 L365 776 L377 1007 Q376 1033 357 1035 L328 1035 Q316 1032 316 1017 L311 783 L256 780 Q239 777 236 763 Z';

export function kuroMarkup(): string {
  return `<div class="kuro-stage" id="kuroStage" role="img" aria-label="Kuro, anime catgirl companion">
    <div class="kuro-shadow"></div>
    <div class="kuro-position">
      <div class="kuro-motion">
        <img data-k="editing" class="kuro-layer is-active" src="${editingSrc}" alt="" draggable="false" />
        <img data-k="testing" class="kuro-layer" src="${testingSrc}" alt="" draggable="false" />
        <img data-k="verifying" class="kuro-layer" src="${verifyingSrc}" alt="" draggable="false" />
        <img data-k="success" class="kuro-layer" src="${successSrc}" alt="" draggable="false" />
        <img data-k="failed" class="kuro-layer" src="${failedSrc}" alt="" draggable="false" />
        <img data-k="frustrated" class="kuro-layer" src="${frustratedSrc}" alt="" draggable="false" />
      </div>
    </div>
  </div>`;
}

export class KuroCharacter {
  readonly root: HTMLElement;
  private stage: HTMLElement;
  private position: HTMLElement;
  private motion: HTMLElement;
  private layers: HTMLImageElement[];
  private puppetRoot: SVGSVGElement | null = null;
  private blinkImage: SVGImageElement | null = null;
  private blinkHalf: SVGImageElement | null = null;
  private nodes = new Map<string, { id: string; parent: string | null; pivot: [number, number]; group: SVGGElement; angle: number }>();
  private matrices = new Map<string, DOMMatrix>();

  private currentState = 'editing';
  private targetState = 'editing';
  private time = 0;
  private frameId: number | null = null;
  private lastTime: number | null = null;
  private suspended = false;
  private reduced = false;
  private petBoost = 0;
  private resizeObserver: ResizeObserver;
  private systemMotion = matchMedia('(prefers-reduced-motion: reduce)');

  constructor(root: HTMLElement) {
    this.root = root;
    this.stage = root.querySelector('.kuro-stage') || root;
    this.position = this.stage.querySelector('.kuro-position')!;
    this.motion = this.stage.querySelector('.kuro-motion')!;
    this.layers = Array.from(this.stage.querySelectorAll<HTMLImageElement>('.kuro-layer'));

    this.setupStageLayout();
    this.buildPuppetRig();

    this.resizeObserver = new ResizeObserver(() => this.fitStage());
    this.resizeObserver.observe(this.stage);
    this.fitStage();

    this.systemMotion.addEventListener('change', () => this.sync());
    this.sync();
  }

  private setupStageLayout() {
    const frames = Object.values(MANIFEST);
    const gutter = 24;
    const halfWidth = Math.max(...frames.flatMap(m => [m.contact[0] - m.bounds[0], m.bounds[2] - m.contact[0]])) + gutter;
    const above = Math.max(...frames.map(m => m.contact[1] - m.bounds[1])) + gutter;
    const below = Math.max(...frames.map(m => m.bounds[3] - m.contact[1])) + gutter;
    const envelope = { width: halfWidth * 2, height: above + below };

    this.layers.forEach(img => {
      const k = img.dataset.k || 'editing';
      const m = MANIFEST[k];
      if (!m) return;
      img.style.width = `${(m.size[0] / envelope.width) * 100}%`;
      img.style.height = `${(m.size[1] / envelope.height) * 100}%`;
      img.style.left = `${((halfWidth - m.contact[0]) / envelope.width) * 100}%`;
      img.style.top = `${((above - m.contact[1]) / envelope.height) * 100}%`;
    });
  }

  private fitStage() {
    const frames = Object.values(MANIFEST);
    const gutter = 24;
    const halfWidth = Math.max(...frames.flatMap(m => [m.contact[0] - m.bounds[0], m.bounds[2] - m.contact[0]])) + gutter;
    const above = Math.max(...frames.map(m => m.contact[1] - m.bounds[1])) + gutter;
    const below = Math.max(...frames.map(m => m.bounds[3] - m.contact[1])) + gutter;
    const envelope = { width: halfWidth * 2, height: above + below };

    const scale = Math.min(this.stage.clientWidth / envelope.width, this.stage.clientHeight / envelope.height) || 0.45;
    this.position.style.width = `${envelope.width * scale}px`;
    this.position.style.height = `${envelope.height * scale}px`;

    const shadow = this.stage.querySelector<HTMLElement>('.kuro-shadow');
    if (shadow) shadow.style.bottom = `${below * scale - 5}px`;
  }

  private buildPuppetRig() {
    this.puppetRoot = svg('svg', { viewBox: '0 0 1274 1491', 'aria-hidden': 'true', class: 'editing-rig' }) as SVGSVGElement;
    const scene = svg('g', { transform: 'translate(-5 65)' });
    const defs = svg('defs');
    this.puppetRoot.append(defs, scene);

    const image = (src: string) => svg('image', { href: src, width: 1138, height: 1382, preserveAspectRatio: 'none' }) as SVGImageElement;
    const mask = (id: string, white = true) => {
      const m = svg('mask', { id, maskUnits: 'userSpaceOnUse', x: -50, y: -50, width: 1250, height: 1500, 'mask-type': 'luminance' });
      m.append(svg('rect', { x: -50, y: -50, width: 1250, height: 1500, fill: white ? 'white' : 'black' }));
      defs.append(m);
      return m;
    };

    const staticMask = mask('kuro-static');
    for (const part of PARTS) staticMask.append(svg('path', { d: part.d, fill: 'black', stroke: 'white', 'stroke-width': 1.6 }));

    const repairMask = mask('kuro-repair', false);
    for (const id of ['head', 'hair-back', 'torso', 'upper-leg', 'lower-leg', 'foot', 'second-foot', 'phone-hand', 'thumb', 'hair-tips']) {
      const p = PARTS.find(p => p.id === id);
      if (p) repairMask.append(svg('path', { d: p.d, fill: 'white' }));
    }

    const underlay = image(repairSrc);
    underlay.setAttribute('mask', 'url(#kuro-repair)');
    scene.append(underlay);

    const stationary = image(editingSrc);
    stationary.setAttribute('mask', 'url(#kuro-static)');
    stationary.dataset.part = 'chair';
    scene.append(stationary);

    for (const id of ORDER) {
      const p = PARTS.find(p => p.id === id);
      if (!p) continue;
      const clip = svg('clipPath', { id: `kuro-cut-${id}`, clipPathUnits: 'userSpaceOnUse' });
      clip.append(svg('path', { d: p.d }));
      defs.append(clip);

      const ownMask = mask(`kuro-own-${id}`);
      for (const later of ORDER.slice(ORDER.indexOf(id) + 1)) {
        if (['eyes', 'mouth'].includes(later)) continue;
        const lp = PARTS.find(p => p.id === later);
        if (lp) ownMask.append(svg('path', { d: lp.d, fill: 'black', stroke: 'white', 'stroke-width': 1.6 }));
      }
      ownMask.append(svg('path', { d: CHAIR_FRONT, fill: 'black' }));

      const group = svg('g', { 'data-part': id }) as SVGGElement;
      const cut = svg('g', { 'clip-path': `url(#kuro-cut-${id})` });
      const img = image(editingSrc);
      img.setAttribute('mask', `url(#kuro-own-${id})`);
      cut.append(img);
      group.append(cut);

      if (id === 'eyes') {
        this.blinkImage = image(blinkClosedSrc);
        this.blinkHalf = image(blinkHalfSrc);
        this.blinkImage.setAttribute('transform', 'matrix(1.003226 -0.000572 0.000572 1.003226 1.87222 0.13018)');
        this.blinkHalf.setAttribute('transform', 'matrix(0.98608 -0.002108 0.002108 0.98608 -5.94949 4.24208)');
        this.blinkImage.style.display = this.blinkHalf.style.display = 'none';
        cut.append(this.blinkHalf, this.blinkImage);
      }

      scene.append(group);
      this.nodes.set(id, { id: p.id, parent: p.parent, pivot: p.pivot as [number, number], group, angle: 0 });
    }

    const frontClip = svg('clipPath', { id: 'kuro-chair-front' });
    frontClip.append(svg('path', { d: CHAIR_FRONT }));
    defs.append(frontClip);

    const foregroundChair = image(editingSrc);
    foregroundChair.setAttribute('clip-path', 'url(#kuro-chair-front)');
    scene.append(foregroundChair);

    this.position.append(this.puppetRoot);
    this.paintPuppet();
  }

  private angles(t: number): Record<string, number> {
    const head = wave(t, 12, 0.22);
    const scroll = [2.8, 7.4, 12.6, 20.2].reduce((s, v) => s + pulse(t, v, 0.68), 0);
    const angles: Record<string, number> = {
      base: 0,
      torso: wave(t, 8, 0.035),
      'upper-leg': 0,
      'lower-leg': wave(t, 4, 1.65) + wave(t, 8, 0.18),
      foot: -wave(t, 4, 0.2),
      'second-foot': (pulse(t, 8.2, 1.5) + pulse(t, 18.1, 1.8)) * 0.9,
      tail: wave(t, 8, 0.95) + wave(t, 12, 0.25),
      head,
      'ear-left': (pulse(t, 3.5, 0.38) - pulse(t, 3.88, 0.22) * 0.3 + pulse(t, 16.2, 0.32)) * 0.95,
      'ear-right': (pulse(t, 10.3, 0.36) - pulse(t, 10.66, 0.22) * 0.3) * 1.1,
      'hair-back': -wave(t - 0.28, 12, 0.12),
      'hair-front': wave(t - 0.16, 12, 0.22) - head,
      'hair-tips': wave(t - 0.32, 12, 0.35) - head,
      'phone-hand': -scroll * 0.08,
      thumb: scroll * 1.8,
      mouth: 0,
      eyes: 0,
    };

    if (this.petBoost > 0) {
      angles['ear-left'] += Math.sin(this.petBoost * 14) * 2.2;
      angles['ear-right'] -= Math.sin(this.petBoost * 14) * 2.2;
      angles.tail += Math.sin(this.petBoost * 18) * 3.8;
      angles.head += Math.sin(this.petBoost * 8) * 0.9;
    }
    return angles;
  }

  private paintPuppet() {
    if (!this.puppetRoot) return;
    const t = this.reduced || this.systemMotion.matches ? 0 : this.time;
    const angles = this.angles(t);
    this.matrices.clear();

    const resolve = (id: string): DOMMatrix => {
      if (this.matrices.has(id)) return this.matrices.get(id)!;
      const n = this.nodes.get(id);
      if (!n) return I();
      const parent = n.parent ? resolve(n.parent) : I();
      const matrix = parent.translate(...n.pivot).rotate(angles[id] || 0).translate(-n.pivot[0], -n.pivot[1]);
      this.matrices.set(id, matrix);
      return matrix;
    };

    for (const [id, node] of this.nodes) {
      const m = resolve(id);
      node.angle = angles[id] || 0;
      node.group.setAttribute('transform', `matrix(${m.a} ${m.b} ${m.c} ${m.d} ${m.e} ${m.f})`);
    }

    if (this.blinkImage && this.blinkHalf) {
      const elapsed = [2.1, 6.7, 11.4, 17.6, 22.7].map(start => t - start).find(v => v >= 0 && v < 0.17);
      const blink = elapsed !== undefined;
      const eyeFrame = !blink ? 'open' : elapsed < 0.035 || elapsed > 0.115 ? 'half' : 'closed';
      this.blinkImage.style.display = eyeFrame === 'closed' ? '' : 'none';
      this.blinkHalf.style.display = eyeFrame === 'half' ? '' : 'none';
    }
  }

  pet() {
    if (this.suspended) return;
    this.petBoost = 1.0;
    this.sync();
  }

  observe(state: string, _streak: number, _token: string, _personality: Personality, reduced: boolean, visible: boolean) {
    this.reduced = reduced;
    this.suspended = !visible;

    let target = 'editing';
    if (state === 'verified') target = 'success';
    else if (state === 'failed') target = 'failed';
    else if (state === 'testing' || state === 'building') target = 'testing';
    else if (state === 'verifying') target = 'verifying';
    else if (state === 'inconclusive' || state === 'claimed') target = 'frustrated';
    else target = 'editing';

    if (target !== this.targetState) {
      this.targetState = target;
      this.transitionTo(target);
    }

    this.sync();
  }

  private transitionTo(name: string) {
    this.currentState = name;
    const isPuppet = name === 'editing';

    if (this.puppetRoot) {
      this.puppetRoot.style.display = isPuppet ? '' : 'none';
    }
    this.motion.hidden = isPuppet;

    this.layers.forEach(img => {
      const active = img.dataset.k === name;
      img.classList.toggle('is-active', active && !isPuppet);
    });
  }

  private sync() {
    if (this.frameId) cancelAnimationFrame(this.frameId);
    this.frameId = null;
    this.lastTime = null;

    const running = !this.suspended && !document.hidden && !this.reduced && !this.systemMotion.matches;
    if (running && this.currentState === 'editing') {
      this.frameId = requestAnimationFrame(t => this.tick(t));
    } else {
      this.paintPuppet();
    }
  }

  private tick(now: number) {
    if (this.suspended || document.hidden || this.reduced || this.systemMotion.matches) {
      this.frameId = null;
      this.lastTime = null;
      this.paintPuppet();
      return;
    }

    const dt = this.lastTime === null ? 0 : Math.min((now - this.lastTime) / 1000, 0.05);
    this.lastTime = now;
    this.time = (this.time + dt) % 24;

    if (this.petBoost > 0) {
      this.petBoost = Math.max(0, this.petBoost - dt * 1.5);
    }

    this.paintPuppet();
    this.frameId = requestAnimationFrame(t => this.tick(t));
  }

  destroy() {
    if (this.frameId) cancelAnimationFrame(this.frameId);
    this.frameId = null;
    this.resizeObserver.disconnect();
    if (this.puppetRoot) this.puppetRoot.remove();
  }
}
