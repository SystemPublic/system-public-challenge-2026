// One run: the question, a live taskboard over the SSE stream, the trace, and the answer.
import { html, useState, useEffect, useRef, api, when, dur } from '../api.js';
import { plural, short } from '../../sections.js';
import { Answer } from './answer.js';
import { Process } from './process.js';

export function Turn({ run, latest, firstPass, agents = [], onDone, onAgain }) {
  const [events, setEvents] = useState(null);
  const [answer, setAnswer] = useState(run.answer);
  const [status, setStatus] = useState(run.status);
  const [conn, setConn] = useState('');
  const [traceOpen, setTraceOpen] = useState(run.status === 'running');
  const [open, setOpen] = useState(latest);
  useEffect(() => { if (run.answer && !answer) setAnswer(run.answer); if (run.status !== 'running') setStatus(run.status); }, [run.answer, run.status]);
  useEffect(() => { if (latest) setOpen(true); }, [latest]);

  // Live runs stream their events; the server replays stored ones after a reconnect, so skip what we have.
  useEffect(() => {
    if (run.status !== 'running') return;
    const evs = []; let seen = 0;
    const es = new EventSource(`/api/runs/${run.id}/events`);
    setConn('Connecting to the run');
    es.onopen = () => { seen = 0; setConn(''); };
    es.onmessage = (m) => {
      if (seen++ < evs.length) return;
      const ev = JSON.parse(m.data);
      evs.push(ev); setEvents([...evs]);
      if (ev.type === 'answer') setAnswer(ev.answer);
      if (ev.type === 'run_done') { es.close(); setStatus(ev.status); setTraceOpen(false); onDone?.(); }
    };
    es.onerror = () => setConn(es.readyState === EventSource.CLOSED
      ? 'Lost the connection to this run. Reload the page to pick it up again.' : 'Connection dropped. Reconnecting to the run.');
    return () => es.close();
  }, [run.id]);

  // Finished runs load their stored events when the trace is opened.
  const toggleTrace = (e) => {
    setTraceOpen(e.currentTarget.open);
    if (e.currentTarget.open && !events) api(`/api/runs/${run.id}`).then((r) => setEvents(r.events || [])).catch(() => setEvents([]));
  };

  const title = (n) => agents.find((a) => a.name === n)?.title || String(n).charAt(0).toUpperCase() + String(n).slice(1);
  const live = status === 'running';
  const m = traceModel(events || []);

  if (status === 'failed' && !answer) {
    return html`<article class="turn failed" id=${`run-${run.id}`}><div class="fail-line"><span class="st-pill failed">Did not finish</span>
      <span class="fq">${short(firstPass ? 'First pass' : run.query, 110)}</span><time class="small muted">${when(run.created_at)}</time>
      ${onAgain && html`<button type="button" class="ghost-btn small" onClick=${() => onAgain(run.query)}>${firstPass ? 'Run again' : 'Ask again'}</button>`}</div></article>`;
  }

  const summary = answer ? short(String(answer.summary || '').replace(/\s*\[[^\]]*10\.\d{4}[^\]]*\]/g, ''), 170) : '';
  return html`<article class=${`turn ${latest ? 'latest' : ''}`} id=${`run-${run.id}`}>
    ${firstPass ? html`<p class="small muted"><span class="eyebrow">Data run</span> ${live ? 'First pass running, started' : 'First pass ran'} ${when(run.created_at)}</p>`
      : html`<div class="q"><span class="eyebrow">${/^(data:|first pass)/i.test(run.query) ? 'Data run' : 'Question'}</span><p>${run.query}</p><time class="small muted">${when(run.created_at)}</time></div>`}
    ${live && html`<${LiveStatus} m=${m} conn=${conn} title=${title} hasAnswer=${!!answer} />`}
    ${live && html`<${Thread} m=${m} title=${title} />`}
    <details class="trace" open=${traceOpen} onToggle=${toggleTrace}>
      <summary>${live ? 'Agents and tool calls' : events ? `Trace · ${plural([...m.agents.values()].length, 'agent', 'agents')}, ${plural(m.tools, 'tool call', 'tool calls')}, ${dur(m.ms)}` : 'Show agents and tool calls'}</summary>
      ${traceOpen && html`<${Process} events=${events} live=${live} title=${title} />`}
    </details>
    ${answer && (open ? html`<${Answer} answer=${answer} runId=${String(run.id)} drawNow=${latest} />`
      : html`<button type="button" class="older" onClick=${() => setOpen(true)}><span class="more">Show the answer</span><span class="muted">${summary}</span></button>`)}
  </article>`;
}

function LiveStatus({ m, conn, title, hasAnswer }) {
  const agents = [...m.agents.values()];
  const done = agents.filter((a) => a.status === 'done' || a.status === 'failed').length;
  const last = m.last && ['running', 'retrying'].includes(m.agents.get(m.last.agent)?.status) ? m.last : null;
  const text = conn || (m.error ? `The run stopped: ${short(m.error)}. Ask the question again.`
    : !m.plan ? 'Planning: choosing agents for this question'
    : m.verifying ? 'Verifying: checking the claims and numbers against the tool results'
    : m.formatting || hasAnswer ? `Writing the answer from ${plural(agents.filter((a) => a.status === 'done').length, 'section', 'sections')}`
    : `${done} of ${agents.length} agents finished. ${last ? `${title(last.agent)}: ${last.tool.replaceAll('_', ' ')} ${toolLine(last)}` : 'Agents are starting their first tool calls.'}`);
  const pct = agents.length ? Math.round((100 * done) / agents.length) : 4;
  return html`<div class=${`live ${m.error ? 'bad' : ''}`} role="status"><i class="dot busy"></i><span>${text}</span>
    <span class="bar" aria-hidden="true"><span style=${{ width: `${m.formatting || hasAnswer ? 100 : Math.max(pct, 6)}%` }}></span></span></div>`;
}

// Live tool thread: every tool call as it arrives, newest at the bottom, with elapsed times.
function Thread({ m, title }) {
  const [, tick] = useState(0);
  const ref = useRef(null);
  useEffect(() => { const t = setInterval(() => tick((x) => x + 1), 1000); return () => clearInterval(t); }, []);
  useEffect(() => { const el = ref.current; if (el) el.scrollTop = el.scrollHeight; }, [m.tools]);
  const ago = (t) => (t ? `${Math.round((Date.now() - new Date(t)) / 1000)} s` : '');
  const agents = [...m.agents.values()];
  return html`<div class="tool-thread small">
    <p class="muted">Run time ${ago(m.t0) || '0 s'}${agents.length ? ' · ' : ''}${agents.map((a) => html`<span key=${a.name} class="t-agent">
      ${a.status === 'running' && html`<i class="dot busy"></i>`}${title(a.name)} ${a.status === 'running' ? ago(a.t0) : STATUS[a.status].toLowerCase()} </span>`)}</p>
    <ol ref=${ref} style=${{ maxHeight: '14rem', overflowY: 'auto', margin: 0 }}>
      ${!m.tools && html`<li class="muted"><i class="dot busy"></i> Planning: choosing agents for this question…</li>`}
      ${m.all.map((t, i) => html`<li key=${i}><strong>${title(t.agent)}</strong> · ${t.tool.replaceAll('_', ' ')} · ${toolLine(t)}</li>`)}
    </ol></div>`;
}

const STATUS = { waiting: 'Waiting', running: 'Running', retrying: 'Retrying', done: 'Done', failed: 'Failed' };
function Trace({ m, loading, title }) {
  const [all, setAll] = useState(new Set());
  if (loading) return html`<p class="small muted">Loading the trace for this run</p>`;
  const agents = [...m.agents.values()];
  if (!agents.length) return html`<p class="small muted">${m.plan ? 'Waiting for the agents to start.' : 'The planner is choosing agents.'}</p>`;
  const flip = (n) => { const s = new Set(all); s.has(n) ? s.delete(n) : s.add(n); setAll(s); };
  return html`<div class="trace-body">
    ${m.context && html`<p class="small muted">What the agents knew: profile ${m.context.profile || 'none'}; ${m.context.project_goals ? 'the project goals' : 'no project goals'};
      ${m.context.earlier_turns ? plural(m.context.earlier_turns, 'earlier answer', 'earlier answers') : 'no earlier answers'}.</p>`}
    ${m.plan && html`<p class="plan-q"><span class="eyebrow">Plan</span> ${m.plan.question}</p>`}
    <ul class="agents">${agents.map((a) => html`<li key=${a.name} class="agent">
      <div class="agent-head"><span class=${`st-pill ${a.status}`}>${STATUS[a.status]}</span><strong>${title(a.name)}</strong>
        <span class="small muted num">${plural(a.tools.length, 'tool call', 'tool calls')}${a.t0 && a.t1 ? ` · ${dur(new Date(a.t1) - new Date(a.t0))}` : ''}</span></div>
      ${a.instruction && html`<p class="instr small">${a.instruction}</p>`}
      ${a.tools.length > 0 && html`<ol class="tools">${a.tools.slice(all.has(a.name) ? 0 : -3).map((t, i) => html`<li key=${i}>
        <code>${t.tool}</code><span>${toolLine(t)}</span><span class="num muted">${dur(t.ms ?? 0)}</span></li>`)}</ol>`}
      ${a.tools.length > 3 && html`<button type="button" class="ghost-btn small" onClick=${() => flip(a.name)}>${all.has(a.name) ? 'Show the last 3' : `Show all ${a.tools.length} tool calls`}</button>`}
      ${a.notes.map(([k, v], i) => html`<p key=${i} class=${`note small ${k === 'Failed' ? 'bad' : ''}`}>${k === 'Failed' ? 'Failed' : 'Fixing output'}: ${short(v)}</p>`)}
    </li>`)}</ul></div>`;
}

const mainArg = (t) => Object.values(t.args || {}).find((v) => typeof v === 'string' && v);
const result = (t) => short(String(t.summary || '').split(/\s+(?:->|→)\s+/).slice(1).join(' → ') || t.summary, 200);
const toolLine = (t) => `${mainArg(t) ? `“${short(mainArg(t), 90)}” → ` : ''}${result(t)}`;

function traceModel(events) {
  const m = { all: [], t0: events[0]?.t, plan: null, agents: new Map(), formatting: false, verifying: false, error: null, done: null, tools: 0, last: null, context: null };
  const agent = (n) => m.agents.get(n) || m.agents.set(n, { name: n, status: 'waiting', tools: [], notes: [] }).get(n);
  for (const e of events) {
    if (e.type === 'context') m.context = e;
    if (e.type === 'plan') {
      m.agents.forEach((a) => { if (a.status === 'running') a.status = 'done'; });  // the planner's own tool calls
      m.plan = e.plan; e.plan.tasks.forEach((t) => { agent(t.agent).instruction = t.instruction; });
    }
    if (e.type === 'agent_started') Object.assign(agent(e.agent), { status: 'running', instruction: e.instruction || agent(e.agent).instruction, t0: e.t });
    if (e.type === 'tool_call') { const a = agent(e.agent); if (a.status === 'waiting') a.status = 'running'; a.tools.push(e); m.all.push(e); m.tools++; m.last = e; }
    if (e.type === 'retry') { agent(e.agent).status = 'retrying'; agent(e.agent).notes.push(['Retry', e.error]); }
    if (e.type === 'agent_done') Object.assign(agent(e.agent), { status: 'done', t1: e.t });
    if (e.type === 'agent_failed') { Object.assign(agent(e.agent), { status: 'failed', t1: e.t }); agent(e.agent).notes.push(['Failed', e.error]); }
    if (e.type === 'formatting') m.formatting = true;
    if (e.type === 'verifying') m.verifying = true;
    if (e.type === 'error') m.error = e.message;
    if (e.type === 'run_done') m.done = e.status;
  }
  m.ms = events.length > 1 ? new Date(events.at(-1).t) - new Date(events[0].t) : 0;
  return m;
}
