// How a run built its answer: question, plan, specialist agents in parallel, write, verify. Click a stage for its tool calls.
import { html, useState, dur } from '../api.js';
import { plural, short } from '../../sections.js';

const GRAPH = 'System Public Graph', SOURCE = {
  search_openalex: 'OpenAlex', count_openalex: 'OpenAlex', lookup_dois: 'OpenAlex', search_pubmed: 'PubMed',
  search_worldbank_indicators: 'World Bank', get_worldbank_data: 'World Bank', project_graph: 'Project', web_search: 'web',
};
const BADGE = { [GRAPH]: 's-graph', OpenAlex: 's-oa', PubMed: 's-pm', 'World Bank': 's-wb', Project: 's-pj', web: 's-web' };
const WORDS = {
  search_concepts: 'Search concepts', search_variables: 'Search variables', neighbours: 'Find linked concepts', paths: 'Find paths between concepts',
  get_findings: 'Read findings', summarise_evidence: 'Summarise evidence', sql: 'Query the graph', subgraph: 'Pull a subgraph', get_concept: 'Read a concept',
  search_openalex: 'Search OpenAlex', count_openalex: 'Count papers', lookup_dois: 'Look up DOIs', search_pubmed: 'Search PubMed',
  search_worldbank_indicators: 'Find World Bank indicators', get_worldbank_data: 'Get World Bank data', project_graph: 'Read the project graph',
};
const source = (tool) => SOURCE[tool] || (tool.includes('web') ? 'web' : GRAPH);
const words = (tool) => WORDS[tool] || tool.replaceAll('_', ' ').replace(/^./, (c) => c.toUpperCase());
const LABEL = { waiting: 'Waiting', running: 'Running', retrying: 'Retrying', done: 'Done', failed: 'Failed' };

export function Process({ events, live, title = (n) => n }) {
  const [sel, setSel] = useState(null);
  if (!events) return html`<p class="small muted">Loading how this answer was built</p>`;
  const m = model(events);
  const span = Math.max(m.end - m.start, 1);
  const time = (s) => (s.t0 && s.t1 ? dur(s.t1 - s.t0) : s.t0 && live ? 'running' : '');
  const node = (key, name, s, sub) => html`<button type="button" class=${`pnode ${s.status} ${sel === key ? 'on' : ''}`}
    aria-expanded=${sel === key} onClick=${() => setSel(sel === key ? null : key)}>
    <span class="pn-head"><i class="pdot"></i><strong>${name}</strong><span class="num muted">${time(s)}</span></span>
    <span class="small muted">${sub}</span></button>`;
  const lanes = [...m.lanes.values()];
  const picked = sel === 'plan' ? m.plan : sel === 'write' ? m.write : sel === 'verify' ? m.verify : m.lanes.get(sel);
  const v = m.verification;
  return html`<section class=${`process ${live ? 'live' : ''}`} aria-label="How this answer was built">
    ${m.question && html`<p class="pq"><span class="eyebrow">Question</span> ${m.question}</p>`}
    <div class="pflow">
      <div class="pcol">${node('plan', 'Plan: the planner picks agents and writes their tasks', m.plan, m.question ? plural(lanes.length, 'agent picked', 'agents picked') : 'Choosing agents')}</div>
      <div class="pcol plane-set"><span class="eyebrow">Specialist agents, in parallel, each with its data sources</span>${lanes.length ? lanes.map((a) => html`<div class="plane" key=${a.name}>
        ${node(a.name, title(a.name), a, html`${plural(a.calls.length, 'tool call', 'tool calls')} ${[...a.sources].map((s) => html`<b class=${`psrc ${BADGE[s]}`}>${s}</b>`)}`)}
        ${a.t0 && html`<span class="ptime" aria-hidden="true"><span style=${{ left: `${(100 * (a.t0 - m.start)) / span}%`, width: `${Math.max(2, (100 * ((a.t1 || m.end) - a.t0)) / span)}%` }}></span></span>`}
      </div>`) : html`<p class="small muted">Agents start after the plan.</p>`}</div>
      <div class="pcol">${node('write', 'Write: the formatter writes the summary from the sections', m.write, m.write.status === 'waiting' ? 'Summary and layout' : m.fix ? 'Rewrote once' : 'Summary written')}</div>
      <div class="pcol">${node('verify', 'Verify: claims checked against tool results', m.verify, v ? `${plural(v.claims_checked, 'claim', 'claims')} checked · ${v.issues.length ? plural(v.issues.length, 'issue', 'issues') : 'no issues'}`
        : m.fix ? `Fix pass for ${plural(m.fix, 'issue', 'issues')}` : 'Claims and numbers')}</div>
    </div>
    ${picked && html`<div class="pdetail">
      ${picked.instruction && html`<p class="small"><span class="eyebrow">Planner's instruction</span> ${picked.instruction}</p>`}
      ${sel === 'plan' && m.tasks.map((t) => html`<p class="small" key=${t.agent}><strong>${title(t.agent)}</strong>: ${t.instruction}</p>`)}
      ${sel === 'verify' && v && html`<p class="small">${v.status === 'verified' ? 'Verified' : 'Issues found'}: ${plural(v.claims_checked, 'claim', 'claims')} checked against the tool results${m.fix ? `, after one fix pass for ${plural(m.fix, 'issue', 'issues')}` : ''}.</p>
        <ul class="small pchecks">${v.code_checks.map((c) => html`<li key=${c}>${c}</li>`)}${v.issues.map((i, k) => html`<li key=${k} class="bad">${i.severity}: ${i.claim}: ${i.problem}</li>`)}</ul>`}
      ${picked.calls.length > 0 && html`<ol class="pcalls">${picked.calls.map((c, i) => html`<li key=${i}>
        <span class="pc-tool">${words(c.tool)}</span><span class="pc-line">${line(c)}</span>
        <b class=${`psrc ${BADGE[source(c.tool)]}`}>${source(c.tool)}</b><span class="num muted small">${dur(c.ms ?? 0)}</span></li>`)}</ol>`}
      ${picked.notes.map((n, i) => html`<p key=${i} class="small bad">${short(n)}</p>`)}
      ${!picked.calls.length && !picked.instruction && sel !== 'plan' && sel !== 'verify' && html`<p class="small muted">No tool calls yet.</p>`}
    </div>`}
  </section>`;
}

// "search_concepts \"malaria\" -> 5 concepts, top: ..." becomes "“malaria” → 5 concepts, top: ..."
function line(c) {
  const [head, ...rest] = String(c.summary || '').split(/\s+(?:->|→)\s+/);
  const arg = head.replace(c.tool, '').trim().replace(/^["\s]+|["\s]+$/g, '');
  return short(`${arg ? `“${arg}” → ` : ''}${rest.join(' → ') || head}`, 220);
}

function model(events) {
  const at = (e) => +new Date(e.t);
  const stage = () => ({ status: 'waiting', calls: [], notes: [], sources: new Set() });
  const m = { start: events.length ? at(events[0]) : 0, end: events.length ? at(events.at(-1)) : 0, lanes: new Map(), tasks: [],
    plan: { ...stage(), status: 'running', t0: events.length ? at(events[0]) : 0 }, write: stage(), verify: stage() };
  const of = (n) => (n === 'planner' ? m.plan : n === 'formatter' ? m.write : n === 'verifier' ? m.verify
    : m.lanes.get(n) || m.lanes.set(n, { ...stage(), name: n }).get(n));
  for (const e of events) {
    const s = e.agent && of(e.agent);
    if (e.type === 'plan') { Object.assign(m.plan, { status: 'done', t1: at(e) }); m.question = e.plan.question; m.tasks = e.plan.tasks;
      e.plan.tasks.forEach((t) => { of(t.agent).instruction = t.instruction; }); }
    if (e.type === 'agent_started' && s) Object.assign(s, { status: 'running', t0: at(e), instruction: e.instruction || s.instruction });
    if (e.type === 'tool_call' && s) { s.calls.push(e); s.sources.add(source(e.tool)); }
    if (e.type === 'retry' && s) { s.status = 'retrying'; s.notes.push(`Fixing output: ${e.error}`); }
    if (e.type === 'agent_done' && s) Object.assign(s, { status: 'done', t1: at(e) });
    if (e.type === 'agent_failed' && s) { if (m.lanes.has(e.agent)) Object.assign(s, { status: 'failed', t1: at(e) }); s.notes.push(`Failed: ${e.error}`); }
    if (e.type === 'formatting') Object.assign(m.write, { status: 'running', t0: at(e) });
    if (e.type === 'verifying') { if (m.write.status === 'running') Object.assign(m.write, { status: 'done', t1: at(e) });
      Object.assign(m.verify, { status: 'running', t0: m.verify.t0 || at(e) }); }
    if (e.type === 'fixing') { m.fix = e.issues; m.write.status = 'running'; }
    if (e.type === 'answer') { m.verification = e.answer.verification; [m.write, m.verify].forEach((x) => { if (x.t0) Object.assign(x, { status: 'done', t1: at(e) }); }); }
    if (e.type === 'run_done' || e.type === 'error') for (const x of [m.plan, m.write, m.verify, ...m.lanes.values()])
      if (['running', 'retrying'].includes(x.status)) Object.assign(x, { status: e.status === 'done' ? 'done' : 'failed', t1: at(e) });
  }
  return m;
}
