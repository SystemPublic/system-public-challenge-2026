// Project home, top to bottom: header and goals, data availability (first pass), dashboard, report, questions.
import { html, useState, useEffect, useRef, useMemo, api, Raw, FIRST_PASS, isFirstPass, isDataRun, when } from '../api.js';
import { esc, linked, wbUrl, table, chart, mountCharts, plural, kpiStrip, linkGroups, overviewCharts, renderMyList } from '../../sections.js';
import { Turn } from './turn.js';
import { Questions } from './questions.js';
import { mountKG } from '../../kg.js';

const building = (s) => String(s || '').startsWith('building');
const GOALS_HINT = 'What the work is for, who will read it, and its scope: countries, populations, years.';

export function ProjectHome({ project, profile, agents, session, threads, thread, reload, projects, owner, onDeleted }) {
  const [editGoals, setEditGoals] = useState(false);
  const [tab, setTab] = useState('questions');  // chat first; the rest are one tap away
  useEffect(() => setTab('questions'), [project.id]);
  // Poll the project while a dashboard or report is being built.
  useEffect(() => {
    if (!building(project.dashboard_status) && !building(project.report_status)) return;
    const t = setTimeout(reload, 4000);
    return () => clearTimeout(t);
  }, [project]);

  const inThread = project.runs.filter((r) => !isDataRun(r) && (r.thread_id ?? null) === thread);
  const topics = project.runs.filter((r) => isDataRun(r) && !isFirstPass(r)).sort((a, b) => b.id - a.id);
  const hasReport = 'reports' in project || 'report_status' in project;
  const threadTitle = threads?.find((t) => (t.id ?? null) === thread)?.title || 'Main';
  const fp = project.runs.filter(isFirstPass);
  const tailored = [profile.role, profile.organisation].filter(Boolean).join(', ');

  return html`<div class="page">
    <header class="phead">
      <div class="phead-row">
        <h1>${project.title}</h1>
        <p class="tailored">Tailored for <strong>${tailored || profile.name}</strong>${owner && html` <a class="small" href=${`#profile=${profile.id}&view=settings`}>Edit profile</a>`}</p>
      </div>
      ${tab === 'overview' && (editGoals ? html`<${GoalsForm} project=${project} reload=${reload} done=${() => setEditGoals(false)} />`
        : html`<div class="goals">
          ${project.goals ? html`<p>${project.goals}</p>` : html`<p class="muted">No goals yet. Say what this work is for, who reads it and its scope; the agents read the goals with every question.</p>`}
          ${owner && html`<button type="button" class="ghost-btn small" onClick=${() => setEditGoals(true)}>${project.goals ? 'Edit goals' : 'Add goals'}</button>`}</div>`)}
      ${tab === 'overview' && owner && html`<${ProjectTools} project=${project} projects=${projects} reload=${reload} onDeleted=${onDeleted} />`}
      <nav class="jump" aria-label="Project views">
        ${[['questions', `Chat · ${inThread.length}`], ['overview', `Data · ${fp.length + topics.length}`], ['dashboard', 'Dashboard'], ['kg', 'Knowledge graph'], hasReport && ['report', 'Report']]
          .filter(Boolean).map(([id, t]) => html`<button key=${id} type="button" class="chip" aria-pressed=${tab === id} onClick=${() => setTab(id)}>${t}</button>`)}
      </nav>
    </header>

    ${tab === 'overview' && html`<${Block} id="data" title="Data availability" eyebrow=${fp.some((r) => r.status === 'running') ? 'First pass · running' : fp.some((r) => r.answer) ? 'First pass · ready' : 'First pass'}
      line="What exists for this project and where sources disagree. Runs once, from the goals.">
      <${FirstPass} project=${project} runs=${fp} reload=${reload} addGoals=${() => setEditGoals(true)} />
    <//>`}
    ${tab === 'overview' && html`<${Block} id="topics" title="Data by topic" eyebrow=${`Data thread · ${plural(topics.length, 'topic', 'topics')}`}
      line="Pull everything on one topic: graph coverage, World Bank indicators, and outside studies where the graph is thin. Every chat thread reads these.">
      <${DataTopics} project=${project} runs=${topics} reload=${reload} />
    <//>`}
    ${tab === 'dashboard' && html`<${Block} id="dashboard" title="Dashboard" eyebrow=${project.dashboard ? `Dashboard · ${plural(project.dashboard.panels?.length ?? 0, 'panel', 'panels')}` : 'Dashboard'}
      line="Key numbers, World Bank data and charts built from the answers in this project.">
      <${Dashboard} project=${project} reload=${reload} />
    <//>`}
    ${tab === 'kg' && html`<${Block} id="kg" title="Knowledge graph" eyebrow="Knowledge graph"
      line="The entities in this project's answers and the facts linking them, with the studies behind each.">
      <${KG} project=${project} />
    <//>`}
    ${tab === 'report' && hasReport && html`<${Block} id="report" title="Report" eyebrow=${`Report · ${plural(project.reports?.length ?? 0, 'version', 'versions')}`}
      line="A cited report of this project with references and data provenance, to print or save as PDF.">
      <${Report} project=${project} reload=${reload} />
    <//>`}
    ${tab === 'questions' && html`<section class="block open" id="questions" aria-labelledby="questions-h">
      <div class="block-head"><p class="eyebrow">Questions · ${threadTitle} thread</p><h2 id="questions-h">Questions</h2>
        <p class="muted small">Every answer reads the goals and the earlier answers in this thread.</p></div>
      <${Questions} project=${project} projects=${owner ? projects : []} runs=${inThread} thread=${thread} threads=${threads} agents=${agents} session=${session} profile=${profile} reload=${reload} />
    </section>`}
  </div>`;
}

// The project knowledge graph view from ../kg.js, remounted when the project's runs change.
function KG({ project }) {
  const ref = useRef(null);
  useEffect(() => { if (ref.current) mountKG(ref.current, project.id); }, [project.id, project.runs.length]);
  return html`<div ref=${ref}></div>`;
}

function DataTopics({ project, runs, reload }) {
  const [topic, setTopic] = useState('');
  const [msg, setMsg] = useState('');
  const pull = async (e) => {
    e.preventDefault();
    if (!topic.trim()) return;
    try { await api(`/api/projects/${project.id}/runs`, { method: 'POST', body: { query: `Data: ${topic.trim()}` } }); setTopic(''); setMsg(''); reload(); }
    catch (err) { setMsg(`Could not start: ${err.message}.`); }
  };
  return html`<form class="topic-form" onSubmit=${pull}>
      <input aria-label="Topic" value=${topic} onInput=${(e) => setTopic(e.target.value)} placeholder="A topic, e.g. AI adoption and jobs in AI-exposed industries" />
      <button class="primary">Pull data</button></form>
    ${msg && html`<p class="msg bad">${msg}</p>`}
    ${runs.map((r, i) => html`<${Turn} key=${r.id} run=${r} latest=${i === 0} onDone=${reload} onAgain=${() => {}} />`)}`;
}

// Owner-only: file the project in a folder, or delete it after a confirm step.
function ProjectTools({ project, projects, reload, onDeleted }) {
  const [msg, setMsg] = useState('');
  const [newFolder, setNewFolder] = useState(false);
  const [confirm, setConfirm] = useState(false);
  const folder = projects.find((p) => p.id === project.id)?.folder || '';
  const folders = [...new Set(projects.map((p) => p.folder).filter(Boolean))].sort();
  const move = async (f) => {
    try { await api(`/api/projects/${project.id}/folder`, { method: 'PUT', body: { folder: f || null } }); setNewFolder(false); setMsg(''); reload(); }
    catch (e) { setMsg(`Could not move the project: ${e.message}.`); }
  };
  const del = async () => {
    try { await api(`/api/projects/${project.id}`, { method: 'DELETE' }); onDeleted(); }
    catch (e) { setMsg(e.status === 403 ? 'Only the owner can delete this project.' : `Could not delete the project: ${e.message}.`); }
  };
  return html`<div class="ptools">
    <label for="pf" class="small muted">Folder</label>
    ${newFolder ? html`<input id="pf" class="folder-input" placeholder="Folder name" autoFocus
        onKeyDown=${(e) => { if (e.key === 'Enter') move(e.target.value.trim()); if (e.key === 'Escape') setNewFolder(false); }} onBlur=${(e) => (e.target.value.trim() ? move(e.target.value.trim()) : setNewFolder(false))} />`
      : html`<select id="pf" value=${folder} onChange=${(e) => (e.target.value === '+' ? setNewFolder(true) : move(e.target.value))}>
        <option value="">No folder</option>${folders.map((f) => html`<option key=${f} value=${f}>${f}</option>`)}<option value="+">New folder…</option></select>`}
    <span class="spacer"></span>
    ${confirm ? html`<span class="confirm-inline small">Delete this project and all its runs? This cannot be undone.
        <button type="button" class="ghost-btn small" onClick=${() => setConfirm(false)}>Cancel</button>
        <button type="button" class="danger-btn small" onClick=${del}>Delete for good</button></span>`
      : html`<button type="button" class="ghost-btn small" onClick=${() => setConfirm(true)}>Delete project</button>`}
    ${msg && html`<p class="msg bad">${msg}</p>`}</div>`;
}

const Block = ({ id, title, eyebrow, line, children }) => html`<section class="block" id=${id} aria-labelledby=${`${id}-h`}>
  <div class="block-head"><p class="eyebrow">${eyebrow}</p><h2 id=${`${id}-h`}>${title}</h2><p class="muted small">${line}</p></div>
  ${children}</section>`;

function GoalsForm({ project, reload, done }) {
  const [msg, setMsg] = useState('');
  const save = async (e) => {
    e.preventDefault();
    const f = Object.fromEntries(new FormData(e.target));
    try {
      await api(`/api/projects/${project.id}`, { method: 'PUT', body: { title: f.title.trim(), goals: f.goals.trim() } });
      await reload(); done();
    } catch (err) { setMsg(`Could not save: ${err.message}. Try again.`); }
  };
  return html`<form class="goals-form" onSubmit=${save}>
    <div class="field"><label for="g-title">Title</label><input id="g-title" name="title" required defaultValue=${project.title} /></div>
    <div class="field"><label for="g-goals">Goals and context</label><textarea id="g-goals" name="goals" rows="5" placeholder=${GOALS_HINT} defaultValue=${project.goals || ''} autoFocus /></div>
    ${msg && html`<p class="msg bad">${msg}</p>`}
    <div class="row-end"><button type="button" class="ghost-btn" onClick=${done}>Cancel</button><button class="primary">Save</button></div>
  </form>`;
}

function FirstPass({ project, runs, reload, addGoals }) {
  const [msg, setMsg] = useState('');
  const last = [...runs].sort((a, b) => a.id - b.id).at(-1);
  const start = async () => {
    try { await api(`/api/projects/${project.id}/runs`, { method: 'POST', body: { query: FIRST_PASS } }); reload(); }
    catch (e) { setMsg(`Could not start the first pass: ${e.message}. Try again in a moment.`); }
  };
  if (last) return html`<${Turn} key=${last.id} run=${last} latest firstPass onDone=${reload} onAgain=${start} />`;
  return html`<div class="empty">
    ${project.goals ? html`<p>No first pass yet. It reads the goals, checks which data and studies exist for them, and where sources disagree.</p>
      <button type="button" class="primary" onClick=${start}>Run the first pass</button>`
    : html`<p><strong>Add goals to start the first pass.</strong> It reads them, checks which data and studies exist, then builds the dashboard.</p>
      <button type="button" class="primary" onClick=${addGoals}>Add goals</button>`}
    ${msg && html`<p class="msg bad">${msg}</p>`}</div>`;
}

// Dashboard panels, ported from ../dashboard.js so v2 keeps its own styles.
const sourceLink = (s) => {
  const doi = String(s).match(/10\.\d{4,9}\/\S+/);
  if (doi) return `<a href="https://doi.org/${esc(doi[0])}" target="_blank" rel="noopener">paper ${esc(doi[0])}</a>`;
  if (/^WB_[A-Z0-9]+_\S+$/.test(s)) return `<a class="ind-id small muted" href="${esc(wbUrl(s))}" target="_blank" rel="noopener">${esc(s)}</a>`;
  return linked(s);
};
const kpis = (p) => `<div class="kpis">${p.kpis.map((k) => `<div class="kpi"><div class="kpi-value num">${esc(k.value)} <span class="kpi-unit">${esc(k.unit)}</span></div>
  <div class="kpi-label">${esc(k.label)}</div><div class="kpi-source">${linked(k.source)}</div></div>`).join('')}</div>`;
const panel = (p) => `<section class="panel panel-${esc(p.kind)}"><h3>${esc(p.title)}</h3>
  ${p.caption ? `<p class="small muted">${linked(p.caption)}</p>` : ''}${p.kind === 'kpis' ? kpis(p) : ''}
  ${p.vega_lite_json ? chart({ title: '', vega_lite_json: p.vega_lite_json }) : ''}${p.table ? table(p.table) : ''}
  ${p.sources?.length ? `<p class="panel-sources">Sources: ${p.sources.map(sourceLink).join('; ')}</p>` : ''}</section>`;
const dashboardHtml = (d) => `<div class="dash-head"><h3>${esc(d.title)}</h3><p class="small muted">${linked(d.summary)}</p></div>
  <div class="panels">${(d.panels || []).map(panel).join('')}</div>`;

function StatusBar({ text, busy, children }) {
  return html`<div class="status-bar"><span class=${`status ${busy ? 'busy' : ''}`} role="status">${busy && html`<i class="dot busy"></i>`}${text}</span>${children}</div>`;
}

// Top to bottom: KPI strip, overview charts, links across questions, where the data runs out, the agent-built panels, my list.
const isGap = (p) => /runs out|gaps?\b/i.test(p.title || '');
const sub = (title, line, body) => `<section class="dsec"><h3>${title}</h3><p class="small muted">${line}</p>${body}</section>`;

function Dashboard({ project, reload }) {
  const [msg, setMsg] = useState('');
  const s = project.dashboard_status || '';
  const busy = building(s);
  const hasAnswers = project.runs.some((r) => r.answer);
  const key = JSON.stringify(project.dashboard || null);
  const runsKey = project.runs.map((r) => `${r.id}${r.answer ? 'a' : ''}`).join();
  const gap = project.dashboard?.panels?.find(isGap);
  const top = useMemo(() => {
    const g = linkGroups(project.runs);
    const charts = overviewCharts(project.runs).map(([, title, line, body], i, a) =>
      `<section class="panel${i === a.length - 1 && a.length % 2 ? ' wide' : ''}"><h3>${title}</h3><p class="small muted">${line}</p>${body}</section>`);
    return kpiStrip(project.runs) + (charts.length ? `<div class="viz">${charts.join('')}</div>` : '')
      + (g ? sub('Links across questions', 'Every indicator map in this project, merged. Pick a number or a bar above to filter.', g) : '')
      + (gap ? sub('Where the data runs out', 'Topics the evidence covers but no data series measures well.', panel(gap)) : '');
  }, [runsKey, key]);
  const markup = useMemo(() => (project.dashboard ? dashboardHtml({ ...project.dashboard, panels: (project.dashboard.panels || []).filter((p) => p !== gap) }) : ''), [key]);
  const step = s.replace(/^building:? ?/, '').replace('dashboard_planner', 'planning panels').replace('panel: ', '');
  const build = async () => {
    try { await api(`/api/projects/${project.id}/dashboard`, { method: 'POST' }); setMsg(''); reload(); }
    catch (e) { setMsg(`Could not start the dashboard: ${e.message}`); }
  };
  const text = msg || (busy ? `Building the dashboard: ${step || 'planning panels'}`
    : s === 'failed' ? 'The last build failed. Build it again; it reads the answers in this project.'
    : project.dashboard ? '' : hasAnswers ? 'No dashboard yet. Build it from the answers in this project.'
    : 'Builds itself when the first pass finishes. Nothing to show yet.');
  return html`${top && html`<${Raw} className="dash-top" markup=${top} onMount=${mountCharts} />`}
    <section class=${top ? 'dsec' : ''}>
      <${StatusBar} text=${text} busy=${busy}>
        ${hasAnswers && html`<button type="button" class=${project.dashboard ? 'outline' : 'primary'} disabled=${busy} onClick=${build}>${project.dashboard ? 'Rebuild' : 'Build dashboard'}</button>`}
      <//>
      ${markup && html`<${Raw} className="dashboard" markup=${markup} onMount=${mountCharts} />`}
    </section>
    <${MyList} project=${project} />`;
}

function MyList({ project }) {
  const ref = useRef(null);
  useEffect(() => { renderMyList(ref.current); }, [project.id]);
  return html`<section class="dsec"><h3>My list</h3><p class="small muted">Indicators you picked from this project's indicator maps, to download as CSV.</p>
    <div class="my-list" ref=${ref}></div></section>`;
}

function Report({ project, reload }) {
  const [msg, setMsg] = useState('');
  const [instruction, setInstruction] = useState('');
  const s = project.report_status || '';
  const busy = building(s);
  const reports = [...(project.reports || [])].sort((a, b) => b.version - a.version);
  const hasAnswers = project.runs.some((r) => r.answer);
  const start = async (ins) => {
    try { await api(`/api/projects/${project.id}/report`, { method: 'POST', body: { instruction: ins } }); setMsg(''); setInstruction(''); reload(); }
    catch (e) { setMsg(`Could not start the report: ${e.message}`); }
  };
  const text = msg || (busy ? `Building the report: ${s.replace(/^building:? ?/, '')}` : s === 'failed' ? 'The last report build failed. Generate it again.'
    : reports.length ? 'Each version opens as a page you can print or save as PDF.'
    : hasAnswers ? 'A cited report built from the answers and dashboard in this project.' : 'Ask a question first; the report is built from the answers.');
  return html`<${StatusBar} text=${text} busy=${busy}>
      ${hasAnswers && html`<button type="button" class=${reports.length ? 'outline' : 'primary'} disabled=${busy} onClick=${() => start(null)}>${reports.length ? 'New version' : 'Generate report'}</button>`}
    <//>
    ${reports.length > 0 && html`<ul class="versions">${reports.map((r, i) => html`<li key=${r.version}>
      <a href=${`/report.html?project=${project.id}&v=${r.version}`} target="_blank" rel="noopener">
        <span class="v num">v${r.version}</span><span class="small muted">${when(r.created_at)}</span>
        ${i === 0 && html`<span class="tag">Latest</span>`}<span class="small instr">${r.instruction || 'From the answers in this project'}</span>
        <span class="go" aria-hidden="true">↗</span></a></li>`)}</ul>
    <form class="revise" onSubmit=${(e) => { e.preventDefault(); if (instruction.trim()) start(instruction.trim()); }}>
      <label for="rv">Revise the latest version</label>
      <div class="inline"><input id="rv" value=${instruction} onInput=${(e) => setInstruction(e.target.value)} placeholder="Make section 2 shorter and add the regional data" />
        <button class="outline" disabled=${busy || !instruction.trim()}>Revise</button></div></form>`}`;
}
