// State, API calls, the run event stream and page layout. Section rendering is in sections.js, the graph in graph.js.
import { esc, plural, renderAnswer, mountCharts, answerConcepts } from './sections.js';
import { drawGraph } from './graph.js';

const $ = (s, r = document) => r.querySelector(s);
const app = $('#app');
const state = { agents: [], profile: null, projects: [], project: null, pinned: new Set() };
const streams = new Set();
// Example questions follow the profile: the first set whose keyword appears in role, organisation or about.
const EXAMPLES = [
  [/malaria|health|epidem|path/i, [
    'Validate: girls under 12 are more vulnerable to malaria because of sexism in malaria-endemic countries.',
    'Is bed net use associated with lower anaemia in children under 5?',
    'Map the evidence from seasonal malaria chemoprevention to child mortality.']],
  [/job|labou?r|employ|world bank|econom/i, [
    'Is vocational training associated with higher youth employment in low-income countries?',
    'What does the graph hold on minimum wage and informal work?',
    'Map the evidence from cash transfers to adult labour supply.']],
  [/obes|nutrition|nesta|diet|food/i, [
    'Which school interventions are associated with lower childhood obesity, and how many studies back each?',
    'Is screen time associated with obesity in children aged 5 to 11?',
    'Map the evidence from a sugar tax to childhood BMI.']],
  [/./, [
    'Validate: girls under 12 are more vulnerable to malaria because of sexism in malaria-endemic countries.',
    'Is vocational training associated with higher youth employment?',
    'Which interventions are associated with lower childhood obesity?']],
];
const examples = (p) => EXAMPLES.find(([re]) => re.test([p.role, p.organisation, p.about].join(' ')))[1];

async function api(path, opts = {}) {
  const res = await fetch(path, { ...opts, headers: { 'Content-Type': 'application/json' }, body: opts.body && JSON.stringify(opts.body) });
  const text = await res.text();
  let data = text;
  try { data = JSON.parse(text); } catch { /* plain text body */ }
  if (!res.ok) {
    const d = data?.detail ?? data;
    const err = new Error(typeof d === 'string' && d ? d : `${res.status} ${res.statusText}`);
    err.status = res.status;
    throw err;
  }
  return data;
}

const store = { get: (k) => { try { return localStorage.getItem(k); } catch { return null; } },
                set: (k, v) => { try { localStorage.setItem(k, v); } catch { /* storage off */ } } };
const route = () => Object.fromEntries(new URLSearchParams(location.hash.slice(1)));
const go = (r) => { location.hash = new URLSearchParams(Object.entries(r).filter(([, v]) => v != null)).toString(); };
const agentTitle = (name) => state.agents.find((a) => a.name === name)?.title || name;
const dur = (ms) => (ms < 1000 ? `${Math.round(ms)} ms` : `${(ms / 1000).toFixed(1)} s`);
const when = (iso) => (iso ? new Date(iso).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' }) : '');

function notice(what, next) {
  const el = $('#notice');
  el.hidden = !what;
  el.textContent = what ? `${what} ${next}` : '';
}

// Routing ------------------------------------------------------------------------------------------
let loads = 0;
async function load() {
  streams.forEach((s) => s.close()); streams.clear();
  const r = route(); const me = ++loads;
  const stale = () => me !== loads;  // a newer hash change took over
  if (!r.profile && store.get('profile')) { go({ profile: store.get('profile') }); return; }
  try {
    if (!state.agents.length) state.agents = await api('/api/agents').catch(() => []);
    const profiles = await api('/api/profiles');
    if (stale()) return;
    state.profile = profiles.find((p) => String(p.id) === r.profile) || null;
    if (!state.profile) return renderProfiles(profiles);
    store.set('profile', state.profile.id);
    const projects = await api(`/api/profiles/${state.profile.id}/projects`);
    notice('');
    const project = r.project ? await api(`/api/projects/${r.project}`).catch((e) => {
      notice(`Could not open that project: ${e.message}.`, 'Pick one from the list.'); return null;
    }) : null;
    if (stale()) return;
    Object.assign(state, { projects, project });
    renderWorkspace();
  } catch (e) {
    if (!stale()) notice(`Could not load your workspace: ${e.message}.`, 'Check that the server is running, then reload the page.');
  }
}
window.addEventListener('hashchange', load);

// Profiles -----------------------------------------------------------------------------------------
function renderProfiles(profiles) {
  $('#profile-btn').hidden = true;
  app.className = 'layout single';
  app.innerHTML = `<div class="page">
    <h1>Choose a profile</h1>
    <p class="muted">A profile tells the agents who you are and what you work on. It adds context and never hides a feature. There are no passwords.</p>
    ${profiles.length ? `<ul class="list">${profiles.map((p) => `<li><div><strong>${esc(p.name)}</strong>
        <div class="small muted">${esc([p.role, p.organisation].filter(Boolean).join(', '))}</div>
        ${p.about ? `<div class="small">${esc(p.about)}</div>` : ''}</div>
        <button type="button" data-use="${p.id}">Use</button></li>`).join('')}</ul>`
      : '<p class="empty">No profiles yet. Create the first one below.</p>'}
    <h2>New profile</h2>
    <form id="new-profile">
      <div class="grid2">
        <div><label for="p-name">Name</label><input id="p-name" name="name" required></div>
        <div><label for="p-role">Role</label><input id="p-role" name="role" placeholder="Malaria researcher"></div>
      </div>
      <label for="p-org">Organisation</label><input id="p-org" name="organisation">
      <label for="p-about">About your work</label>
      <textarea id="p-about" name="about" rows="3" placeholder="What you work on and which populations or countries matter to you"></textarea>
      <div class="form-actions"><button class="primary">Create profile</button></div>
    </form></div>`;
  app.onclick = (e) => { const id = e.target.dataset.use; if (id) go({ profile: id }); };
  $('#new-profile').onsubmit = async (e) => {
    e.preventDefault();
    try {
      const p = await api('/api/profiles', { method: 'POST', body: Object.fromEntries(new FormData(e.target)) });
      go({ profile: p.id });
    } catch (err) { notice(`Could not create the profile: ${err.message}.`, 'Check the fields and try again.'); }
  };
}

function renderProfileDialog() {
  const p = state.profile;
  $('#profile-body').innerHTML = `
    <p><strong>${esc(p.name)}</strong><br><span class="small muted">${esc([p.role, p.organisation].filter(Boolean).join(', '))}</span></p>
    ${p.about ? `<p class="small">${esc(p.about)}</p>` : ''}
    <h2>API keys</h2>
    <p class="small muted">Optional. A key switches on the tools that need it. Keys are stored encrypted and only their names are shown again.</p>
    ${p.key_names?.length ? `<ul class="list">${p.key_names.map((k) => `<li><div><code>${esc(k)}</code></div>
        <button type="button" data-remove-key="${esc(k)}">Remove</button></li>`).join('')}</ul>` : '<p class="small">No keys saved.</p>'}
    <form id="key-form">
      <div class="grid2">
        <div><label for="k-name">Key name</label><input id="k-name" name="name" list="key-names" required placeholder="OPENALEX_API_KEY"></div>
        <div><label for="k-value">Value</label><input id="k-value" name="value" type="password" autocomplete="off" required></div>
      </div>
      <datalist id="key-names"><option value="OPENALEX_API_KEY"><option value="DHS_API_KEY"></datalist>
      <p class="form-msg" role="status"></p>
      <div class="form-actions"><button type="button" id="switch-profile">Switch profile</button><button class="primary">Save key</button></div>
    </form>`;
  const saveKeys = async (body) => {
    try {
      p.key_names = (await api(`/api/profiles/${p.id}/keys`, { method: 'PUT', body })).key_names;
      renderProfileDialog();
    } catch (e) { $('#key-form .form-msg').textContent = `Could not save: ${e.message}. Try again.`; }
  };
  $('#key-form').onsubmit = (e) => { e.preventDefault(); const f = new FormData(e.target); saveKeys({ [f.get('name').trim()]: f.get('value') }); };
  $('#profile-body').onclick = (e) => { const k = e.target.dataset.removeKey; if (k) saveKeys({ [k]: '' }); };
  $('#switch-profile').onclick = () => { store.set('profile', ''); $('#profile-dialog').close(); go({}); };
}
$('#profile-btn').onclick = () => { renderProfileDialog(); $('#profile-dialog').showModal(); };

// Workspace ----------------------------------------------------------------------------------------
function renderWorkspace() {
  const p = state.profile; const pj = state.project;
  const btn = $('#profile-btn');
  btn.hidden = false;
  btn.innerHTML = `${esc(p.name)}<br><span class="small muted">Profile and keys</span>`;
  app.className = 'layout';
  app.onclick = null;
  app.innerHTML = `<nav class="projects" aria-label="Projects">
      <h2>Projects</h2>
      <ul>${state.projects.map((x) => `<li><a href="#profile=${p.id}&project=${x.id}" ${pj?.id === x.id ? 'aria-current="page"' : ''}>
        ${esc(x.title)}<div class="small muted num">${plural(x.n_runs ?? 0, 'question', 'questions')}</div></a></li>`).join('')}</ul>
      <select aria-label="Project"><option value="">${state.projects.length ? 'Choose a project' : 'No projects yet'}</option>
        ${state.projects.map((x) => `<option value="${x.id}" ${pj?.id === x.id ? 'selected' : ''}>${esc(x.title)}</option>`).join('')}</select>
      <form id="new-project" class="row"><input name="title" required placeholder="New project title" aria-label="New project title"><button>Create</button></form>
    </nav>
    <main>${pj ? projectView(pj) : `<div class="empty"><h2>Pick a project</h2>
      <p>A project keeps a thread of questions and answers, so follow-ups can build on earlier ones. Choose one from the list or create one.</p></div>`}</main>`;

  $('nav select').onchange = (e) => e.target.value && go({ profile: p.id, project: e.target.value });
  $('#new-project').onsubmit = async (e) => {
    e.preventDefault();
    try {
      const x = await api(`/api/profiles/${p.id}/projects`, { method: 'POST', body: { title: new FormData(e.target).get('title').trim() } });
      go({ profile: p.id, project: x.id });
    } catch (err) { notice(`Could not create the project: ${err.message}.`, 'Try again.'); }
  };
  if (!pj) return;
  const runs = [...pj.runs].sort((a, b) => a.id - b.id);
  const lastDone = runs.filter((r) => r.answer).at(-1);
  runs.forEach((r) => mountTurn(r, r === lastDone));
  bindComposer();
}

const projectView = (pj) => `<h1>${esc(pj.title)}</h1>
  <div id="thread">${pj.runs.length ? '' : '<div class="empty"><p>No questions in this project yet. Ask one below or pick an example.</p></div>'}</div>
  <form id="composer" class="composer">
    <label for="q">${pj.runs.length ? 'Ask a follow-up' : 'Ask a question'}</label>
    <textarea id="q" rows="3" placeholder="${esc(examples(state.profile)[0])}"></textarea>
    <p class="small muted scope">Answers from about 2M published findings in the System Graph. Shows associations, not causes, and says where the evidence runs out.</p>
    <div class="examples">${examples(state.profile).map((q) => `<button type="button" class="ghost small" data-example>${esc(q)}</button>`).join('')}</div>
    <div class="chips" role="group" aria-label="Agents"><span class="small muted">Agents</span>
      <button type="button" class="chip" data-agent="" aria-pressed="${!state.pinned.size}">Planner chooses</button>
      ${state.agents.map((a) => `<button type="button" class="chip" data-agent="${esc(a.name)}" title="${esc(a.description)}" aria-pressed="${state.pinned.has(a.name)}">${esc(a.title)}</button>`).join('')}
    </div>
    <div class="form-actions"><div><button type="button" id="review">Review plan</button><button class="primary" id="run">Run</button></div></div>
    <p class="form-msg" role="status"></p>
    <div id="plan-editor" class="plan-editor" hidden></div>
  </form>`;

// Composer and editable plan -----------------------------------------------------------------------
function bindComposer() {
  const form = $('#composer'); const msg = $('.form-msg', form);
  const say = (text, bad = false) => { msg.textContent = text; msg.classList.toggle('bad', bad); };
  const query = () => $('#q').value.trim();
  const agents = () => (state.pinned.size ? [...state.pinned] : null);

  $('.examples', form).onclick = (e) => { if (e.target.dataset.example !== undefined) { $('#q').value = e.target.textContent; $('#q').focus(); } };
  $('.chips', form).onclick = (e) => {
    const name = e.target.dataset.agent;
    if (name === undefined) return;
    if (name === '') state.pinned.clear(); else state.pinned.has(name) ? state.pinned.delete(name) : state.pinned.add(name);
    form.querySelectorAll('.chip').forEach((c) => c.setAttribute('aria-pressed', c.dataset.agent ? state.pinned.has(c.dataset.agent) : !state.pinned.size));
  };

  async function start(plan = null) {
    if (!query()) return say('Write a question first.', true);
    form.querySelectorAll('button').forEach((b) => { b.disabled = true; });
    say('Starting the run');
    try {
      const { run_id: id } = await api(`/api/projects/${state.project.id}/runs`, { method: 'POST', body: { query: query(), agents: agents(), plan } });
      const run = { id, query: query(), status: 'running', created_at: new Date().toISOString(), answer: null };
      $('#thread .empty')?.remove();
      $('#q').value = ''; $('#plan-editor').hidden = true; say('');
      mountTurn(run, true).scrollIntoView({ behavior: 'smooth', block: 'start' });
    } catch (e) {
      say(e.status === 429 ? `${e.message}` : `Could not start the run: ${e.message}. Try again in a moment.`, true);
    } finally { form.querySelectorAll('button').forEach((b) => { b.disabled = false; }); }
  }
  form.onsubmit = (e) => { e.preventDefault(); start(); };

  $('#review').onclick = async () => {
    if (!query()) return say('Write a question first.', true);
    say('The planner is choosing agents for this question');
    try {
      const plan = await api(`/api/projects/${state.project.id}/plan`, { method: 'POST', body: { query: query(), agents: agents() } });
      say(''); renderPlanEditor(plan);
    } catch (e) { say(`Could not get a plan: ${e.message}. Use Run to let the planner choose during the run.`, true); }
  };

  const ed = $('#plan-editor');
  const options = (sel) => state.agents.map((a) => `<option value="${esc(a.name)}" ${a.name === sel ? 'selected' : ''}>${esc(a.title)}</option>`).join('');
  const taskRow = (t) => `<div class="task-row"><select aria-label="Agent">${options(t.agent)}</select>
    <textarea rows="3" aria-label="Instruction">${esc(t.instruction)}</textarea><button type="button" data-remove>Remove</button></div>`;
  function renderPlanEditor(plan) {
    ed.hidden = false;
    ed.innerHTML = `<h3>Plan</h3><label for="plan-q">Question</label><input id="plan-q" value="${esc(plan.question)}">
      <div id="tasks">${plan.tasks.map(taskRow).join('')}</div>
      <div class="form-actions"><button type="button" data-add>Add task</button><button type="button" data-cancel>Cancel</button>
        <button type="button" class="primary" data-go>Run this plan</button></div>`;
  }
  ed.onclick = (e) => {
    const d = e.target.dataset;
    if (d.remove !== undefined) e.target.closest('.task-row').remove();
    if (d.add !== undefined) $('#tasks').insertAdjacentHTML('beforeend', taskRow({ agent: state.agents[0]?.name, instruction: '' }));
    if (d.cancel !== undefined) ed.hidden = true;
    if (d.go !== undefined) {
      const tasks = [...ed.querySelectorAll('.task-row')].map((r) => ({ agent: $('select', r).value, instruction: $('textarea', r).value.trim() }))
        .filter((t) => t.instruction);
      if (!tasks.length) return say('Add at least one task with an instruction, or use Run to let the planner choose.', true);
      start({ question: $('#plan-q').value.trim() || query(), tasks });
    }
  };
}

// Turns: one per run --------------------------------------------------------------------------------
function mountTurn(run, latest) {
  $('#thread').insertAdjacentHTML('beforeend', `<section class="turn" id="run-${run.id}">
    <div class="q"><p>${esc(run.query)}</p><time class="small muted">${esc(when(run.created_at))}</time></div>
    <div class="status-line" role="status" hidden></div>
    <details class="trace"><summary>Show agents and tool calls</summary><div class="trace-body"></div></details>
    <div class="answer"></div></section>`);
  const el = $(`#run-${run.id}`);
  if (run.status === 'running') {
    $('.trace', el).open = true;
    follow(run.id, el);
  } else {
    if (run.answer) mountAnswer(el, run.answer, latest);
    else status(el, 'This run finished without an answer. Open the trace to see which step failed, then ask again.', true);
    const tr = $('.trace', el);
    tr.addEventListener('toggle', async () => {
      if (!tr.open || tr.dataset.loaded) return;
      tr.dataset.loaded = '1';
      $('.trace-body', el).innerHTML = '<p class="small muted">Loading the trace for this run</p>';
      try { renderTrace(el, (await api(`/api/runs/${run.id}`)).events || [], false); }
      catch (e) { $('.trace-body', el).innerHTML = `<p class="small">Could not load the trace: ${esc(e.message)}. Close and open it to retry.</p>`; delete tr.dataset.loaded; }
    });
  }
  return el;
}

function status(el, text, bad = false) {
  const s = $('.status-line', el);
  s.hidden = !text; s.textContent = text || ''; s.classList.toggle('error', bad);
}

function follow(id, el) {
  const events = []; let seen = 0;
  const es = new EventSource(`/api/runs/${id}/events`);
  streams.add(es);
  status(el, 'Connecting to the run');
  es.onopen = () => { seen = 0; };
  es.onmessage = (m) => {
    if (seen++ < events.length) return;  // the server replays stored events after a reconnect
    const ev = JSON.parse(m.data);
    events.push(ev);
    if (ev.type === 'answer') mountAnswer(el, ev.answer, true);
    if (ev.type === 'run_done') { es.close(); streams.delete(es); }
    renderTrace(el, events, ev.type !== 'run_done');
  };
  es.onerror = () => {
    if (es.readyState === EventSource.CLOSED) status(el, 'Lost the connection to this run. Reload the page to pick it up again.', true);
    else status(el, 'Connection dropped. Reconnecting to the run');
  };
}

function traceModel(events) {
  const m = { plan: null, agents: new Map(), formatting: false, error: null, done: null, tools: 0, last: null };
  const agent = (n) => m.agents.get(n) || m.agents.set(n, { name: n, status: 'waiting', tools: [], notes: [] }).get(n);
  for (const e of events) {
    if (e.type === 'plan') {
      m.agents.forEach((a) => { if (a.status === 'running') a.status = 'done'; });  // the planner's own tool calls
      m.plan = e.plan; e.plan.tasks.forEach((t) => { agent(t.agent).instruction = t.instruction; });
    }
    if (e.type === 'agent_started') Object.assign(agent(e.agent), { status: 'running', instruction: e.instruction || agent(e.agent).instruction, t0: e.t });
    if (e.type === 'tool_call') {
      const a = agent(e.agent);
      if (a.status === 'waiting') a.status = 'running';
      a.tools.push(e); m.tools++; m.last = e;
    }
    if (e.type === 'retry') { agent(e.agent).status = 'retrying'; agent(e.agent).notes.push(['Retrying after a check failed', e.error]); }
    if (e.type === 'agent_done') Object.assign(agent(e.agent), { status: 'done', t1: e.t });
    if (e.type === 'agent_failed') { Object.assign(agent(e.agent), { status: 'failed', t1: e.t }); agent(e.agent).notes.push(['Failed', e.error]); }
    if (e.type === 'formatting') m.formatting = true;
    if (e.type === 'error') m.error = e.message;
    if (e.type === 'run_done') m.done = e.status;
  }
  m.ms = events.length > 1 ? new Date(events.at(-1).t) - new Date(events[0].t) : 0;
  return m;
}

const mainArg = (t) => Object.values(t.args || {}).find((v) => typeof v === 'string' && v);
const STATUS = { waiting: 'Waiting', running: 'Running', retrying: 'Retrying', done: 'Done', failed: 'Failed' };

function renderTrace(el, events, live) {
  const m = traceModel(events);
  const agents = [...m.agents.values()];
  const open = (el.expanded ??= new Set());
  $('.trace-body', el).onclick = (e) => {
    const n = e.target.dataset.more;
    if (n === undefined) return;
    open.has(n) ? open.delete(n) : open.add(n);
    renderTrace(el, events, live && !m.done);
  };
  const doneN = agents.filter((a) => a.status === 'done' || a.status === 'failed').length;
  $('.trace-body', el).innerHTML = `${m.plan ? `<p class="plan-q">Plan: ${esc(m.plan.question)}</p>` : ''}
    ${agents.length ? `<ul class="agents">${agents.map((a) => `<li class="agent">
      <div class="agent-head"><span class="st st-${a.status}">${STATUS[a.status]}</span><strong>${esc(agentTitle(a.name))}</strong>
        <span class="meta small muted num">${plural(a.tools.length, 'tool call', 'tool calls')}${a.t0 && a.t1 ? `, ${dur(new Date(a.t1) - new Date(a.t0))}` : ''}</span></div>
      ${a.instruction ? `<p class="instr">${esc(a.instruction)}</p>` : ''}
      ${a.tools.length ? `<ol class="tools">${a.tools.slice(open.has(a.name) ? 0 : -3).map((t) => `<li><code>${esc(t.tool)}</code><span>${mainArg(t) ? `<q>${esc(mainArg(t))}</q> ` : ''}${esc(t.summary)}</span><span class="num">${dur(t.ms ?? 0)}</span></li>`).join('')}</ol>` : ''}
      ${a.tools.length > 3 ? `<button type="button" class="ghost small more" data-more="${esc(a.name)}">${open.has(a.name) ? 'Show the last 3' : `Show all ${a.tools.length} tool calls`}</button>` : ''}
      ${a.notes.map(([k, v]) => `<p class="note ${k === 'Failed' ? 'bad' : ''}">${k}: ${esc(v)}</p>`).join('')}
    </li>`).join('')}</ul>` : ''}`;
  $('.trace summary', el).textContent = m.done || !live
    ? `Trace: ${plural(agents.length, 'agent', 'agents')}, ${plural(m.tools, 'tool call', 'tool calls')}, ${dur(m.ms)}`
    : 'Agents and tool calls';

  if (m.error) return status(el, `The run stopped: ${m.error}. Ask again, or pin fewer agents.`, true);
  if (m.done === 'failed' && !$('.answer', el).innerHTML) return status(el, 'The run failed before writing an answer. Check the failed agent above, then ask again.', true);
  if (!live) { status(el, ''); $('.trace', el).open = false; return; }
  if (!m.plan) return status(el, 'Planning: choosing agents for this question');
  if (m.formatting) return status(el, `Writing the answer from ${plural(agents.filter((a) => a.status === 'done').length, 'section', 'sections')}`);
  const lastRunning = m.last && ['running', 'retrying'].includes(m.agents.get(m.last.agent)?.status) ? m.last : null;
  status(el, `${doneN} of ${agents.length} agents finished. `
    + (lastRunning ? `${agentTitle(lastRunning.agent)}: ${lastRunning.tool}${mainArg(lastRunning) ? ` "${mainArg(lastRunning)}"` : ''}, ${lastRunning.summary}` : 'Agents are starting their first tool calls'));
}

// Answer and graph ---------------------------------------------------------------------------------
function mountAnswer(el, answer, drawNow) {
  const box = $('.answer', el);
  box.innerHTML = renderAnswer(answer);
  mountCharts(box);
  const { ids, verdicts } = answerConcepts(answer);
  const panel = $('.graph-panel', box);
  if (!ids.length) { panel.innerHTML = '<p class="small muted">No graph concepts in this answer, so there is no graph to draw.</p>'; return; }
  const draw = async () => {
    panel.innerHTML = `<p class="small muted">Loading ${plural(ids.length, 'concept', 'concepts')} from the graph</p>`;
    try {
      const data = await api(`/api/graph?ids=${encodeURIComponent(ids.join(','))}`);
      if (!data.nodes?.length) { panel.innerHTML = '<p class="small muted">The graph has none of these concepts.</p>'; return; }
      if (!window.cytoscape) throw new Error('the graph library did not load');
      drawGraph(panel, data, verdicts);
    } catch (e) { panel.innerHTML = `<p class="small">Could not draw the graph: ${esc(e.message)}. The answer is unaffected; reload to try again.</p>`; }
  };
  if (drawNow) draw();
  else {
    panel.innerHTML = `<button type="button">Show graph of ${plural(ids.length, 'concept', 'concepts')}</button>`;
    panel.firstChild.onclick = draw;
  }
}

// Verdict pills open the findings table of their card.
document.addEventListener('click', (e) => {
  const v = e.target.closest('button[data-findings]');
  const d = v?.closest('.card')?.querySelector('details.findings');
  if (!d) return;
  d.open = !d.open;
  v.setAttribute('aria-expanded', d.open);
});

load();
