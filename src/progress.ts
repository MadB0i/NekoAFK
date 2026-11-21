export type LiveProgress = {
  session_key: string|null; context: string; activity: string; detail: string;
  tone: string; connected: boolean; started_at: number|null;
  plan: {completed:number;total:number;historical:boolean}|null;
};
export const planTrack = `<div id="planTrack" hidden><progress id="planMeter" aria-label="Plan steps completed" max="1" value="0"></progress></div>`;
export function dockProgressView() {
  return `<section class="progress-evidence expanded" aria-label="Live progress"><p id="progressDetail" class="muted"></p><div class="evidence-counts"><div><strong id="tasks">Unknown</strong><span id="planCaption">Plan progress</span></div><div><strong id="failures">0</strong><span>Observed failures</span></div></div>${planTrack}<details id="progressExplanation"><summary>Progress details</summary><p id="progressTiming" class="hint"></p><p class="hint">ETA unavailable. Plan counts are agent-reported steps, not effort or overall completion. Local verification is separate.</p></details></section>`;
}
const text = (id:string,value:string) => { const el=document.getElementById(id);if(el&&el.textContent!==value)el.textContent=value; };
export function renderProgress(p:LiveProgress,hud:boolean,announce:boolean) {
  text(hud?'hudActivity':'state',p.activity);
  text('progressContext',p.context);text('progressDetail',p.detail);
  text('planCaption',p.plan?.historical?'Last plan progress':'Plan progress');
  text('tasks',p.plan?`${p.plan.completed} / ${p.plan.total}`:'Unknown');
  text('hudPlan',p.plan?`${p.plan.historical?'Last plan':'Plan progress'} · ${p.plan.completed} / ${p.plan.total}`:'No plan observed');
  text('progressTiming',p.started_at?`Tool start observed at ${new Date(p.started_at).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit',second:'2-digit'})}.`:'Execution timing unavailable for this state.');
  const track=document.getElementById('planTrack')!;track.hidden=!p.plan;
  if(p.plan) {
    const meter=document.getElementById('planMeter') as HTMLProgressElement;
    if(meter.max!==p.plan.total)meter.max=p.plan.total;
    if(meter.value!==p.plan.completed)meter.value=p.plan.completed;
    meter.setAttribute('aria-valuetext',`${p.plan.completed} of ${p.plan.total} agent-reported plan steps${p.plan.historical?', historical':''}; not overall task completion`);
  }
  document.getElementById('app')!.dataset.progressTone=p.tone;
  const live=document.getElementById('progressAnnouncement');
  if(live) {live.setAttribute('aria-live',announce?'polite':'off');text('progressAnnouncement',`${p.context}. ${p.activity}. ${p.detail}.${p.plan?` ${p.plan.completed} of ${p.plan.total} ${p.plan.historical?'historical ':''}plan steps.`:''}`);}
}
