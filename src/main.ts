import { invoke, isTauri } from '@tauri-apps/api/core';
import { emit, listen } from '@tauri-apps/api/event';
import { createIcons, Settings as SettingsIcon, X, Pin, Unplug, PanelBottom, GripVertical, Play, Square, FolderOpen, RotateCcw, Download, Plug, ShieldCheck, Sun, Cat, PanelsTopLeft, HardDrive, Folder, Ellipsis, MousePointer2, Minus, Plus, Pause, Check, ChevronUp, ChevronDown } from 'lucide';
import { companionView, dockView, settingsView, hudView, sections, mascotSvg, characterUrls } from './views';
import { renderProgress, type LiveProgress } from './progress';
import { Character } from './character';
import { KuroCharacter, kuroMarkup } from './kuro';
import type { Personality } from './director';
import { sound } from './sound';
import './style.css';

type Settings = { personality: Personality; character: string; workspace: string; verify_program: string; verify_args: string[]; verify_timeout: number; auto_verify: boolean; scale: number; always_on_top: boolean; transparent: boolean; attached: boolean; reduced_motion: boolean; neko_visible: boolean; dock_visible: boolean; click_through: boolean; dock_pinned: boolean; dock_collapsed: boolean; hud_enabled: boolean; hud_collapsed: boolean; sfx_enabled?: boolean; theme?: string };
type Session = { key: string; id: string; adapter: string; workspace: string; state: string; last_activity: number; tasks: [number, number] | null; failures: number; failure_streak: number; revision: number; tests_passed: number; claimed: boolean; verification: string; activity: { at: number; text: string }[]; permissions: string[]; operations: Record<string,string> };
type Snapshot = { settings: Settings; engine: { sessions: Record<string, Session>; selected: string | null }; selected_state: string; connected: boolean; selected_connected: boolean; notice: string | null; data_dir: string; verification_running: boolean; bridge_installed: boolean; desktop_paused: boolean; progress: LiveProgress };
const surface = new URLSearchParams(location.search).get('surface') || 'neko';
// Persist only the first fault kind per surface. Never transmit error text or stacks.
for (const kind of ['error', 'unhandledrejection'] as const) {
  window.addEventListener(kind, () => {
    if (isTauri()) void emit('neko:runtime-fault', { surface, kind }).catch(() => {});
  }, { once: true });
}
const app = document.querySelector<HTMLDivElement>('#app')!;
const $ = <T extends HTMLElement = HTMLElement>(id: string) => document.getElementById(id) as T;
const field = (id: string) => $<HTMLInputElement>(id);
let current: Snapshot | undefined;
let dirty = false;
let lastActivity = '';
app.className = surface === 'neko' ? 'neko' : surface === 'telemetry' ? 'dock' : surface === 'hud' ? 'hud' : 'settings';
app.innerHTML = surface === 'neko' ? companionView() : surface === 'telemetry' ? dockView() : surface === 'hud' ? hudView() : settingsView();
if(surface==='settings') {
  const group=$('setupTitle').parentElement!;
  const setup=document.createElement('details'); setup.id='setupDetails'; setup.className='form-group';
  const summary=document.createElement('summary'); summary.textContent='Connection setup';
  $('setupTitle').replaceWith(summary); setup.append(...Array.from(group.childNodes)); group.replaceWith(setup);
  const privacy=document.querySelector<HTMLElement>('.privacy-copy')!;
  const data=document.createElement('details');
  const dataSummary=document.createElement('summary'); dataSummary.textContent='Local data and privacy';
  privacy.replaceWith(data); data.append(dataSummary,privacy);
}
const icons = () => createIcons({ icons: { Settings: SettingsIcon, X, Pin, Unplug, PanelBottom, GripVertical, Play, Square, FolderOpen, RotateCcw, Download, Plug, ShieldCheck, Sun, Cat, PanelsTopLeft, HardDrive, Folder, Ellipsis, MousePointer2, Minus, Plus, Pause, Check, ChevronUp, ChevronDown }, attrs: { 'aria-hidden':'true' } });
icons();
type CompanionInstance = Character | KuroCharacter;
let character: CompanionInstance | undefined = surface==='neko' ? new Character($('mascot')) : undefined;
let mountedCharacter = 'robot';
// The mascot SVG is baked at startup; switching companions swaps the markup and
// rebuilds the renderer, suspending the old instance so its loop stops.
function mountCharacter(kind: string) {
  const target = kind === 'cat' ? 'cat' : kind === 'kuro' ? 'kuro' : 'robot';
  if (surface !== 'neko' || !character || mountedCharacter === target) return;
  if ('destroy' in character && typeof (character as any).destroy === 'function') {
    (character as any).destroy();
  } else {
    character.observe('idle', 0, '', 'playful', true, false);
  }
  mountedCharacter = target;
  if (target === 'kuro') {
    $('mascot').innerHTML = kuroMarkup();
    character = new KuroCharacter($('mascot'));
  } else {
    $('mascot').innerHTML = mascotSvg(target);
    character = new Character($('mascot'));
  }
}

const labels: Record<string,string> = { disconnected:'Bridge offline', closed:'Session closed', idle:'Waiting', active:'Working', planning:'Reasoning observed', writing:'Writing response', building:'Building', inconclusive:'Check inconclusive', editing:'Editing', testing:'Testing', failed:'Needs attention', permission:'Permission needed', claimed:'Completion unverified', verified:'Locally verified', verifying:'Verifying locally', inactive:'No recent activity' };
function clearError() { $('errorBox').hidden = true; $('error').textContent = ''; }
function showError(e: unknown) { $('errorBox').hidden = false; $('error').textContent = String(e).replace(/^Error: /,''); }
async function call<T>(name: string, args?: Record<string,unknown>): Promise<T> {
  if (!isTauri()) throw Error('Desktop host unavailable. Launch the NekoAFK Windows application.');
  return invoke<T>(name,args);
}
async function busy(button: HTMLButtonElement, operation: () => Promise<unknown>) {
  const hadFocus = document.activeElement === button;
  clearError(); button.disabled = true; button.setAttribute('aria-busy','true');
  try { await operation(); }
  catch (e) { showError(e); }
  finally {
    button.disabled = false; button.removeAttribute('aria-busy'); if(current) update(current);
    // Disabling a focused control moves focus to body in WebView2. Restore it
    // only if the user has not moved to another control while the action ran.
    if(hadFocus && document.activeElement === document.body && !button.disabled) button.focus({preventScroll:true});
  }
}
function section(key: string, focus = false) {
  if (!sections[key]) key = 'connections';
  document.querySelectorAll<HTMLElement>('.panel').forEach(p => p.hidden = p.id !== `panel-${key}`);
  document.querySelectorAll<HTMLButtonElement>('[data-section]').forEach(b => { if (b.dataset.section === key) b.setAttribute('aria-current','page'); else b.removeAttribute('aria-current'); });
  $('sectionTitle').textContent = sections[key].title; $('sectionCaption').textContent = sections[key].caption;
  document.querySelector('main')!.scrollTop = 0;
  if (location.hash !== `#${key}`) history.replaceState(null,'',`#${key}`);
  if (focus) $('sectionTitle').focus();
}
function invalid(id: string, message: string, errorId: string): never {
  section($(id).closest('.panel')!.id.replace('panel-',''));
  $(id).setAttribute('aria-invalid','true'); $(errorId).hidden = false; $(errorId).textContent = message;
  $(id).focus(); throw Error(message);
}
function settingsFromForm(): Settings {
  if (!current) throw Error('Desktop host is unavailable. Restart NekoAFK and try again.');
  for (const id of ['workspaceInput','arguments','timeout']) $(id).removeAttribute('aria-invalid');
  for (const id of ['workspaceError','argsError','timeoutError']) $(id).hidden = true;
  let args: unknown;
  try { args = JSON.parse($<HTMLTextAreaElement>('arguments').value); }
  catch { return invalid('arguments','Arguments must be a JSON array of strings.','argsError'); }
  if (!Array.isArray(args) || args.some(a => typeof a !== 'string')) return invalid('arguments','Arguments must be a JSON array of strings.','argsError');
  const timeout = Number(field('timeout').value);
  if (!Number.isInteger(timeout) || timeout < 5 || timeout > 600) return invalid('timeout','Choose a timeout from 5 to 600 seconds.','timeoutError');
  const themeEl = $<HTMLSelectElement>('theme');
  const sfxEl = field('sfx');
  return { ...current.settings, personality:$<HTMLSelectElement>('personality').value as Personality, character:$<HTMLSelectElement>('character').value, workspace:field('workspaceInput').value.trim(), verify_program:field('program').value.trim(), verify_args:args, verify_timeout:timeout, auto_verify:field('auto').checked, scale:Number(field('scale').value)/100, always_on_top:field('top').checked, transparent:field('transparent').checked, attached:field('attached').checked, reduced_motion:field('motion').checked, click_through:field('clickThrough').checked, dock_pinned:field('dockPinned').checked, hud_enabled:field('hudEnabled').checked, hud_collapsed:field('hudCollapsed').checked, sfx_enabled:sfxEl?sfxEl.checked:true, theme:themeEl?themeEl.value:'amber' };
}
function syncCharacterUI(choice: string) {
  const kind = choice === 'cat' ? 'cat' : choice === 'kuro' ? 'kuro' : 'robot';
  const select = $<HTMLSelectElement>('character');
  if (select && select.value !== kind) select.value = kind;
  document.querySelectorAll<HTMLButtonElement>('.char-picker-card').forEach(card => {
    const isThis = card.dataset.character === kind;
    card.classList.toggle('selected', isThis);
    card.setAttribute('aria-checked', String(isThis));
  });
  if ($('previewRobot')) $('previewRobot').classList.toggle('selected', kind === 'robot');
  if ($('previewCat')) $('previewCat').classList.toggle('selected', kind === 'cat');
  if ($('previewKuro')) $('previewKuro').classList.toggle('selected', kind === 'kuro');
  const url = characterUrls[kind];
  for (const id of ['brandImg', 'appearanceImg'] as const) {
    const img = $<HTMLImageElement>(id);
    if (img && img.getAttribute('src') !== url) img.src = url;
  }
  const appImg = $<HTMLImageElement>('appearanceImg');
  if (appImg) {
    appImg.alt = kind === 'cat' ? 'Neko, the midnight cat' : kind === 'kuro' ? 'Kuro, anime catgirl companion' : 'Nova, the floating robot companion';
  }
}
async function selectCharacter(choice: string) {
  syncCharacterUI(choice);
  await save();
}
function fill(s: Settings) {
  $<HTMLSelectElement>('personality').value=s.personality||'playful';
  syncCharacterUI(s.character || 'robot');
  field('workspaceInput').value=s.workspace; field('program').value=s.verify_program; $<HTMLTextAreaElement>('arguments').value=JSON.stringify(s.verify_args);
  field('timeout').value=String(s.verify_timeout); field('scale').value=String(s.scale*100); $('scaleValue').textContent=`${Math.round(s.scale*100)}%`;
  if($('theme')) $<HTMLSelectElement>('theme').value=s.theme||'amber';
  if(field('sfx')) field('sfx').checked=s.sfx_enabled!==false;
  for (const [id,val] of Object.entries({ auto:s.auto_verify,top:s.always_on_top,transparent:s.transparent,attached:s.attached,motion:s.reduced_motion,clickThrough:s.click_through,dockPinned:s.dock_pinned,hudEnabled:s.hud_enabled,hudCollapsed:s.hud_collapsed })) field(id).checked=val;
}
function pressed(action: string, value: boolean, title?: string) {
  document.querySelectorAll<HTMLButtonElement>(`[data-action="${action}"]`).forEach(b => { b.setAttribute('aria-pressed',String(value)); if(title) { b.title=title; b.setAttribute('aria-label',title); } });
}
function update(s: Snapshot) {
  const first = !current;
  if (current && current.selected_state !== s.selected_state) {
    if (s.selected_state === 'verified') sound.playVictory();
    else if (s.selected_state === 'failed') sound.playAlert();
  }
  current=s;
  document.documentElement.dataset.theme = s.settings.theme || 'amber';
  sound.enabled = s.settings.sfx_enabled !== false;
  app.dataset.ready='true'; app.dataset.state=s.selected_state;
  app.dataset.reducedMotion=String(s.settings.reduced_motion);
  if(surface==='neko') {
    mountCharacter(s.settings.character);
    const selected=s.engine.selected?s.engine.sessions[s.engine.selected]:undefined;
    character!.observe(s.selected_state,selected?.failure_streak||0,`${selected?.key||''}:${selected?.revision||0}`,s.settings.personality||'playful',s.settings.reduced_motion,!document.hidden&&s.settings.neko_visible&&!s.desktop_paused);
    app.style.background=s.settings.transparent?'transparent':'var(--base)';
    const name=s.settings.character==='cat'?'Neko':s.settings.character==='kuro'?'Kuro':'Nova';
    $('mascot').setAttribute('aria-label',`${name}: ${labels[s.selected_state]||s.selected_state}`);
    pressed('toggle-top',s.settings.always_on_top); pressed('toggle-motion',s.settings.reduced_motion); pressed('toggle-dock',s.settings.dock_visible);
    pressed('toggle-click-through',s.settings.click_through,s.settings.click_through?'Disable click-through from Settings or tray':'Enable click-through; recover from tray');
    return;
  }
  if(surface==='hud') {
    app.dataset.collapsed=String(s.settings.hud_collapsed);
    $('hudDetails').hidden=s.settings.hud_collapsed;
    const button=document.querySelector<HTMLButtonElement>('[data-action="toggle-hud-collapse"]')!;
    button.setAttribute('aria-expanded',String(!s.settings.hud_collapsed));
    button.setAttribute('aria-controls','hudDetails');
    button.title=s.settings.hud_collapsed?'Expand progress HUD':'Collapse progress HUD';button.setAttribute('aria-label',button.title);
    button.querySelector('svg')!.style.transform=s.settings.hud_collapsed?'rotate(180deg)':'';
    renderProgress(s.progress,true,!s.settings.dock_visible&&!document.hidden);
    return;
  }
  $('connectionDot').classList.toggle('connected',s.connected);
  if(surface==='telemetry') {
    app.dataset.collapsed=String(s.settings.dock_collapsed);
    renderProgress(s.progress,false,false);
    const selected=s.engine.selected?s.engine.sessions[s.engine.selected]:undefined;
    const workspaceName=(selected?.workspace||s.settings.workspace||'').split(/[\\/]/).filter(Boolean).pop()||'';
    $('compactContext').textContent=workspaceName?` · ${workspaceName}`:'';
    $('compactContext').title=selected?`${selected.workspace} · ${selected.id}`:workspaceName;
    const online=s.selected_connected;
    $('bridgeLabel').textContent=online?'Connected':'Offline'; $('connectionDot').classList.toggle('connected',online);
    const agentName = selected?.adapter ? (
      selected.adapter === 'antigravity' ? 'Antigravity' :
      selected.adapter === 'claudecode' || selected.adapter === 'claude' ? 'Claude Code' :
      selected.adapter === 'cursor' ? 'Cursor' :
      selected.adapter === 'windsurf' ? 'Windsurf' :
      selected.adapter === 'codex' ? 'Codex' :
      selected.adapter === 'zai' ? 'Zai' : 'OpenCode'
    ) : 'OpenCode';
    $('connection').textContent=online ? s.selected_state==='inactive'?'No observed activity in the last minute.':`Receiving local ${agentName} events` : selected?'Connection lost. Evidence below is historical.':'Connect an agent in settings to get started.';
    $('connection').hidden=online && s.selected_state!=='inactive' || s.settings.dock_collapsed;
    const select=$<HTMLSelectElement>('session'); const signature=Object.keys(s.engine.sessions).join('\n');
    if(select.dataset.signature!==signature) {
      select.replaceChildren();
      for(const session of Object.values(s.engine.sessions)) { const option=document.createElement('option'); option.value=session.key; option.textContent=`${session.workspace.split(/[\\/]/).pop()} / ${session.id.slice(-10)}`; select.append(option); }
      if(!select.options.length) { const o=document.createElement('option'); o.textContent='No observed sessions'; o.value=''; select.append(o); }
      select.dataset.signature=signature;
    }
    select.value=s.engine.selected||''; select.disabled=!selected;
    $('workspace').textContent=selected?.workspace||s.settings.workspace||'No workspace connected'; $('workspace').title=$('workspace').textContent||'';
    $('failures').textContent=String(selected?.failures||0);
    $('verification').textContent=selected?.verification==='running'?'Independent local check running':selected?.verification==='passed'?'Configured check passed. See evidence below.':selected?.verification==='inconclusive'?'Check cancelled or evidence changed. Verify again.':selected?.verification==='failed'?'Local verification did not pass. See evidence below.':selected?.claimed?'Agent finished its response. Local proof is pending.':'No independent check has run';
    const hint=!selected?'Select an observed session to verify.':!s.settings.verify_program?'Set a verification command in Settings.':selected.permissions.length?'Answer the permission request in OpenCode first.':Object.keys(selected.operations||{}).length?'Wait for the observed OpenCode tools to finish.':'';
    $('verifyHint').textContent=hint; $('verifyHint').hidden=!hint;
    $<HTMLButtonElement>('verify').disabled=!!hint||s.verification_running; $('cancel').hidden=!s.verification_running;
    $('footer').textContent=selected?`${selected.tests_passed} test-like commands exited 0 \u00b7 ${new Date(selected.last_activity).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'})}`:'Local evidence only';
    const activity=JSON.stringify([selected?.key,selected?.activity||[]]);
    if(activity!==lastActivity) {
      const list=$('activity'),reading=list.scrollTop>8,oldSession=list.dataset.session;
      const anchor=reading?Array.from(list.children).find(e=>e.getBoundingClientRect().bottom>list.getBoundingClientRect().top) as HTMLElement|undefined:undefined;
      const anchorKey=anchor?.dataset.key,offset=anchor?anchor.getBoundingClientRect().top-list.getBoundingClientRect().top:0;
      lastActivity=activity;list.dataset.session=selected?.key||'';
      list.replaceChildren(...(selected?.activity||[]).map(a=>{ const li=document.createElement('li'),time=document.createElement('time'),text=document.createElement('span');li.dataset.key=`${a.at}:${a.text}`; time.textContent=new Date(a.at).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'}); time.dateTime=new Date(a.at).toISOString(); text.textContent=a.text; li.append(time,text); return li; }));
      const sameSession=oldSession===list.dataset.session;
      const restored=reading&&sameSession?Array.from(list.children).find(e=>(e as HTMLElement).dataset.key===anchorKey):undefined;
      if(restored)list.scrollTop+=restored.getBoundingClientRect().top-list.getBoundingClientRect().top-offset;
      else if(!reading||!sameSession)list.scrollTop=0;
      $('latestActivity').hidden=!reading||!sameSession;
      $('emptyActivity').hidden=!!selected?.activity.length; $('eventCount').textContent=selected?.activity.length?String(selected.activity.length):'';
    }
    pressed('toggle-attach',s.settings.attached,s.settings.attached?'Detach dock':'Attach dock'); pressed('toggle-pin',s.settings.dock_pinned,s.settings.dock_pinned?'Unpin dock':'Pin dock');
    const collapse=document.querySelector<HTMLButtonElement>('[data-action="toggle-collapse"]')!;
    collapse.title=s.settings.dock_collapsed?'Expand dock':'Collapse dock'; collapse.setAttribute('aria-label',collapse.title); collapse.setAttribute('aria-expanded',String(!s.settings.dock_collapsed));
    const arrow=collapse.querySelector('svg')!; arrow.style.transform=s.settings.dock_collapsed?'rotate(180deg)':'';
    document.querySelectorAll<HTMLButtonElement>('.dock-char-pill').forEach(btn => {
      const isThis = btn.dataset.character === s.settings.character;
      btn.classList.toggle('selected', isThis);
      btn.setAttribute('aria-checked', String(isThis));
    });
  } else {
    if(first || !dirty && !document.querySelector('input:focus,textarea:focus,select:focus')) fill(s.settings);
    syncCharacterUI(s.settings.character || 'robot');
    $('connection').textContent=s.connected?'Connected':'Offline';
    $('notice').hidden=!s.notice; $('notice').textContent=s.notice||'';
    $('bridgeStatus').textContent=s.connected?`${Object.keys(s.engine.sessions).length} observed sessions` : s.bridge_installed?'Bridge installed. Restart OpenCode in the saved workspace to connect.':'Waiting for a local bridge connection.';
    $('installed').textContent=s.bridge_installed?'Installed for saved workspace':'';
    const setup=$<HTMLDetailsElement>('setupDetails');
    if(setup.dataset.installed!==String(s.bridge_installed)) { setup.open=!s.bridge_installed; setup.dataset.installed=String(s.bridge_installed); }
    $('dataPath').textContent=s.data_dir;
    if(first) $('saved').textContent='Settings saved locally';
    pressed('toggle-neko',s.settings.neko_visible); pressed('toggle-dock',s.settings.dock_visible);
  }
}
async function save() {
  const settings=settingsFromForm();
  try { await call('save_settings',{settings}); }
  catch(e) { if(String(e).includes('Workspace folder')) return invalid('workspaceInput',String(e),'workspaceError'); throw e; }
  dirty=false; $<HTMLButtonElement>('discard').disabled=true; $('saved').textContent='Settings saved locally';
  update(await call<Snapshot>('get_snapshot'));
}
document.querySelectorAll<HTMLButtonElement>('[data-action]').forEach(b=>b.addEventListener('click',()=>void busy(b,async()=>{ await call('window_action',{action:b.dataset.action}); update(await call<Snapshot>('get_snapshot')); })));
$('dismissError').addEventListener('click',clearError);
if(surface==='settings') {
  section(location.hash.slice(1)||'connections');
  document.querySelectorAll<HTMLButtonElement>('[data-section]').forEach(b=>b.addEventListener('click',()=>section(b.dataset.section!,true)));
  document.querySelectorAll<HTMLButtonElement>('.char-picker-card').forEach(b => {
    b.addEventListener('click', () => {
      const char = b.dataset.character;
      if (char) void selectCharacter(char);
    });
  });
  $<HTMLSelectElement>('character')?.addEventListener('change', e => {
    void selectCharacter((e.target as HTMLSelectElement).value);
  });
  window.addEventListener('hashchange',()=>section(location.hash.slice(1)));
  $('preferences').addEventListener('input',()=>{ dirty=true; $('saved').textContent='Unsaved changes'; $<HTMLButtonElement>('discard').disabled=false; });
  $('scale').addEventListener('input',()=>{ $('scaleValue').textContent=`${field('scale').value}%`; });
  $('preferences').addEventListener('submit',e=>{ e.preventDefault(); void busy($<HTMLButtonElement>('save'),save); });
  $('discard').addEventListener('click',()=>{ if(current) fill(current.settings); dirty=false; $<HTMLButtonElement>('discard').disabled=true; $('saved').textContent='Changes discarded'; clearError(); });
  $('install').addEventListener('click',()=>void busy($<HTMLButtonElement>('install'),async()=>{ await save(); await call('install_bridge'); $('installStatus').textContent='Bridge installed. Restart OpenCode in this workspace.'; update(await call<Snapshot>('get_snapshot')); }));
  $('openData').addEventListener('click',()=>void busy($<HTMLButtonElement>('openData'),()=>call('open_data_folder')));
  $('browseWorkspace')?.addEventListener('click', async () => {
    try {
      const chosen = await call<string | null>('pick_workspace_folder');
      if (chosen) {
        $<HTMLInputElement>('workspaceInput').value = chosen;
        await save();
      }
    } catch (e) {
      showError(e);
    }
  });
} else if(surface==='telemetry') {
  document.querySelectorAll<HTMLButtonElement>('.dock-char-pill').forEach(btn => {
    btn.addEventListener('click', async () => {
      const char = btn.dataset.character;
      if (char && current) {
        current.settings.character = char;
        await call('save_settings', { settings: current.settings });
        update(await call<Snapshot>('get_snapshot'));
      }
    });
  });
  $('dockBrowse')?.addEventListener('click', async () => {
    try {
      const chosen = await call<string | null>('pick_workspace_folder');
      if (chosen && current) {
        current.settings.workspace = chosen;
        await call('save_settings', { settings: current.settings });
        update(await call<Snapshot>('get_snapshot'));
      }
    } catch (e) {
      showError(e);
    }
  });
  $('latestActivity').addEventListener('click',()=>{ $('activity').scrollTop=0;$('latestActivity').hidden=true;$('activity').focus(); });
  $('activity').addEventListener('scroll',()=>{if($('activity').scrollTop<=8)$('latestActivity').hidden=true;},{passive:true});
  $('session').addEventListener('change',e=>void call('select_session',{key:(e.target as HTMLSelectElement).value}).catch(showError));
  $('verify').addEventListener('click',()=>void busy($<HTMLButtonElement>('verify'),()=>call('run_verification')));
  $('cancel').addEventListener('click',()=>void busy($<HTMLButtonElement>('cancel'),()=>call('cancel_verification')));
  $('viewLog')?.addEventListener('click',async()=>{
    const drawer=$('logDrawer'); if(!drawer) return;
    const open=drawer.hidden;
    if(open){
      drawer.hidden=false; $('logContent').textContent='Loading verification log...';
      try { const log=await call<string>('get_verification_log'); $('logContent').textContent=log; }
      catch(e){ $('logContent').textContent=String(e); }
    } else { drawer.hidden=true; }
  });
  $('closeLog')?.addEventListener('click',()=>{ const d=$('logDrawer'); if(d) d.hidden=true; });
} else if(surface==='neko') {
  const closeTools=()=>{ const tools=$('companionTools'); if(!tools||tools.hidden) return; tools.classList.add('tools-hiding'); setTimeout(()=>{ tools.hidden=true; tools.classList.remove('tools-hiding'); },160); $('menuToggle').setAttribute('aria-expanded','false'); };
  $('menuToggle').addEventListener('click',()=>{ const tools=$('companionTools'),open=tools.hidden; if(open){ tools.hidden=false; tools.classList.remove('tools-hiding'); } else { closeTools(); } $('menuToggle').setAttribute('aria-expanded',String(open)); });
  document.addEventListener('keydown',e=>{ if(e.key==='Escape'){ closeTools(); $('menuToggle').focus(); } });
  document.addEventListener('pointerdown',e=>{ if(!(e.target as Element).closest('#companionTools, #menuToggle')) closeTools(); });
  let downPos={x:0,y:0,time:0};
  $('mascot')?.addEventListener('pointerdown',e=>{ downPos={x:e.clientX,y:e.clientY,time:Date.now()}; });
  $('mascot')?.addEventListener('pointerup',e=>{
    const dx=Math.abs(e.clientX-downPos.x),dy=Math.abs(e.clientY-downPos.y),dt=Date.now()-downPos.time;
    if(dx<6 && dy<6 && dt<400 && !(e.target as Element).closest('button,select,input')){
      character?.pet();
      sound.playPet();
    }
  });
}
const handle=$('handle')||$('mascot');
handle?.addEventListener('mousedown',async e=>{
  if(e.button!==0||(e.target as Element).closest('button,select,input')||!isTauri()) return;
  e.preventDefault();
  // Detach and capture the mouse in one native command, without applying
  // window preferences while Windows is already moving the dock.
  try { await call('start_window_drag',{clientX:e.clientX,clientY:e.clientY}); } catch(e) { showError(e); }
});
document.addEventListener('visibilitychange',()=>{ if(current&&surface==='neko') update(current); });
if(isTauri()) {
  const unlisten=await listen<Snapshot>('neko:snapshot',e=>update(e.payload));
  window.addEventListener('beforeunload',unlisten,{once:true});
  try { update(await call<Snapshot>('get_snapshot')); }
  catch(e) { app.dataset.startupError=String(e); showError(e); }
} else {
  showError('Desktop host unavailable. Launch NekoAFK from its Windows executable.');
  document.querySelectorAll('button,input,textarea,select').forEach(e=>(e as HTMLButtonElement).disabled=true);
}
