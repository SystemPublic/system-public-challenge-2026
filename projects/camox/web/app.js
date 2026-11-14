// State, API calls, the run event stream and page layout. Section rendering is in sections.js, the graph in graph.js.
import { esc, plural, short, renderAnswer, refBody, mountCharts, answerConcepts, downloadCsv } from './sections.js';
import { drawGraph } from './graph.js';
import { bindDashboard } from './dashboard.js';

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

async function api(path, opts = {}, retry = !opts.method) {
  const res = await fetch(path, { ...opts, headers: { 'Content-Type': 'application/json' }, body: opts.body && JSON.stringify(opts.body) })
    .catch(() => { throw new Error('could not reach the server; check your connection'); });
  // The free host returns 502/503 while it wakes up or redeploys: retry a read once before giving up.
  if (retry && res.status >= 502 && res.status <= 504) {
    await new Promise((r) => setTimeout(r, 2500));
    return api(path, opts, false);
  }
  const text = await res.text();
  let data = text;
  try { data = JSON.parse(text); } catch { /* plain text body */ }
  if (!res.ok) {
    const d = data?.detail ?? data;
    const html = typeof d === 'string' && d.trimStart().startsWith('<');
    const msg = res.status >= 502 ? 'the server is waking up or restarting; try again in a minute'
      : (typeof d === 'string' && d && !html ? d.slice(0, 200) : `server error ${res.status}`);
    const err = new Error(msg);
    err.status = res.status;
    throw err;
  }
  return data;
}

const store = { get: (k) => { try { return localStorage.getItem(k); } catch { return null; } },
                set: (k, v) => { try { localStorage.setItem(k, v); } catch { /* storage off */ } } };
const route = () => Object.fromEntries(new URLSearchParams(location.hash.slice(1)));
const go = (r) => { location.hash = new URLSearchParams(Object.entries(r).filter(([, v]) => v != null)).toString(); };
const agentTitle = (name) => state.agents.find((a) => a.name === name)?.title || String(name).charAt(0).toUpperCase() + String(name).slice(1);
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
  btn.innerHTML = `<span class="small muted">Profile</span> ${esc(p.name)}<br><span class="small muted">Change profile or add keys</span>`;
  app.className = 'layout';
  app.onclick = null;
  app.innerHTML = `<nav class="projects" aria-label="Projects">
      <h2>Projects</h2>
      <ul>${state.projects.map((x) => `<li><a href="#profile=${p.id}&project=${x.id}" ${pj?.id === x.id ? 'aria-current="page"' : ''}>
        <span class="t">${esc(x.title)}</span>${x.goals ? `<div class="small muted g">${esc(short(x.goals.split('\n')[0], 70))}</div>` : ''}
        <div class="small muted num">${projectStatus(pj?.id === x.id ? { ...x, first_pass_status: fpStatus(pj) ?? x.first_pass_status } : x)}</div></a></li>`).join('')}</ul>
      <select aria-label="Project"><option value="">${state.projects.length ? 'Choose a project' : 'No projects yet'}</option>
        ${state.projects.map((x) => `<option value="${x.id}" ${pj?.id === x.id ? 'selected' : ''}>${esc(x.title)}</option>`).join('')}</select>
      <a class="button new-btn" href="#profile=${p.id}" ${pj ? '' : 'aria-current="page"'}>New project</a>
    </nav>
    <main>${pj ? projectView(pj) : newProjectView()}</main>`;

  $('nav select').onchange = (e) => e.target.value && go({ profile: p.id, project: e.target.value });
  if (!pj) {
    $('#new-project').onsubmit = async (e) => {
      e.preventDefault();
      const f = Object.fromEntries(new FormData(e.target));
      try {
        e.target.querySelector('button').disabled = true;
        const x = await api(`/api/profiles/${p.id}/projects`, { method: 'POST', body: { title: f.title.trim(), goals: f.goals.trim() } });
        go({ profile: p.id, project: x.id });
      } catch (err) {
        e.target.querySelector('button').disabled = false;
        $('#new-project .form-msg').textContent = `Could not create the project: ${err.message}. Try again.`;
      }
    };
    return;
  }
  bindGoals();
  state.pollDashboard = bindDashboard($('#dashboard'), pj, api);
  const runs = [...pj.runs].sort((a, b) => a.id - b.id);
  const fps = runs.filter(isFirstPass); const fpDone = fps.filter((r) => r.answer).at(-1);
  const asked = runs.filter((r) => !isFirstPass(r));
  const lastDone = asked.filter((r) => r.answer).at(-1);
  if (fps.length) $('#first-pass').innerHTML = '';
  fps.forEach((r) => mountTurn(r, r === fpDone, $('#first-pass')));
  asked.forEach((r) => mountTurn(r, r === lastDone));
  bindFirstPass();
  bindComposer();
}

// The first pass is the run the server starts when a project gets goals: it maps what data exists for them.
const FIRST_PASS = 'First pass: what data is available for this project, and where do sources disagree or run out?';
const isFirstPass = (r) => r.kind === 'first_pass' || /^first pass\b/i.test(r.query || '');
const fpStatus = (pj) => { const f = pj.runs.filter(isFirstPass); return f.some((r) => r.status === 'running') ? 'running' : f.some((r) => r.answer) ? 'done' : null; };
const projectStatus = (x) => {
  const s = x.first_pass_status;
  if (s === 'running') return 'First pass running';
  if (s === 'done') return `First pass ready, ${plural(x.n_runs ?? 1, 'run', 'runs')}`;
  if (!x.goals) return 'No goals yet';
  return plural(x.n_runs ?? 0, 'run', 'runs');
};

const firstPassEmpty = (pj) => (pj.goals
  ? `<div class="empty"><p>No first pass for this project yet. It reads the goals, checks which data and studies exist for them and where sources disagree.</p>
     <button type="button" class="primary" data-first-pass>Run the first pass</button></div>`
  : `<div class="empty"><p><strong>Add goals to start the first pass.</strong> It reads them, checks which data and studies exist and where sources disagree, then builds the dashboard.</p>
     <button type="button" class="primary" data-add-goals>Add goals</button></div>`);

function bindFirstPass() {
  const box = $('#first-pass');
  box.onclick = async (e) => {
    if (e.target.dataset.addGoals !== undefined) return $('#goals [data-edit-goals]')?.click();
    if (e.target.dataset.firstPass === undefined) return;
    e.target.disabled = true;
    try {
      const { run_id: id } = await api(`/api/projects/${state.project.id}/runs`, { method: 'POST', body: { query: FIRST_PASS } });
      box.innerHTML = '';
      mountTurn({ id, query: FIRST_PASS, status: 'running', created_at: new Date().toISOString(), answer: null }, true, box);
    } catch (err) { e.target.disabled = false; notice(`Could not start the first pass: ${err.message}.`, 'Try again in a moment.'); }
  };
}

const GOALS_HINT = 'What the work is for, who will read it, and its scope: countries, populations, years.';
const newProjectView = () => `<div class="new-project"><h1>New project</h1>
  <p>A project is one piece of work, such as a brief or a programme design note. <strong>Its goals drive everything:</strong></p>
  <ol class="how small">
    <li>A first pass reads the goals and maps which data and studies exist, and where sources disagree.</li>
    <li>A dashboard of key numbers is built from that first pass.</li>
    <li>You ask questions; every answer reads the goals and the earlier answers.</li>
  </ol>
  <form id="new-project">
    <label for="np-title">Title</label><input id="np-title" name="title" required placeholder="Youth employment brief">
    <label for="np-goals">Goals and context</label>
    <textarea id="np-goals" name="goals" rows="5" required placeholder="${GOALS_HINT}"></textarea>
    <p class="form-msg" role="status"></p>
    <div class="form-actions"><button class="primary">Create and start the first pass</button></div>
  </form>
  <p class="small muted">Answers are written for your profile, ${esc(state.profile.name)}${state.profile.role ? `, ${esc(state.profile.role)}` : ''}. Change it with the profile button at the top.</p></div>`;

const goalsView = (pj) => (pj.goals
  ? `<div class="goals-head"><span class="label">Goals and context</span><button type="button" class="ghost small" data-edit-goals>Edit</button></div>
     <p>${esc(pj.goals)}</p>`
  : `<p class="small">No goals yet. Say what this work is for, who reads it and its scope; the agents read the goals with every question.
     <button type="button" class="small" data-edit-goals>Add goals</button></p>`);

function bindGoals() {
  const box = $('#goals'); const pj = state.project;
  box.onclick = (e) => {
    if (e.target.dataset.editGoals !== undefined) {
      box.innerHTML = `<form id="goals-form"><label for="g-title">Title</label><input id="g-title" name="title" required value="${esc(pj.title)}">
        <label for="g-goals">Goals and context</label><textarea id="g-goals" name="goals" rows="5" placeholder="${GOALS_HINT}">${esc(pj.goals)}</textarea>
        <p class="form-msg" role="status"></p>
        <div class="form-actions"><button type="button" data-cancel-goals>Cancel</button><button class="primary">Save</button></div></form>`;
      $('#g-goals').focus();
      $('#goals-form').onsubmit = async (ev) => {
        ev.preventDefault();
        const f = Object.fromEntries(new FormData(ev.target));
        try {
          const x = await api(`/api/projects/${pj.id}`, { method: 'PUT', body: { title: f.title.trim(), goals: f.goals.trim() } });
          if (x.first_pass_run_id) return load();
          Object.assign(pj, { title: x.title ?? f.title.trim(), goals: x.goals ?? f.goals.trim() });
          Object.assign(state.projects.find((q) => q.id === pj.id) || {}, { title: pj.title, goals: pj.goals });
          $('main h1').textContent = pj.title;
          $('nav a[aria-current] .t').textContent = pj.title;
          $(`nav option[value="${pj.id}"]`).textContent = pj.title;
          box.innerHTML = goalsView(pj);
        } catch (err) { $('#goals-form .form-msg').textContent = `Could not save: ${err.message}. Try again.`; }
      };
    }
    if (e.target.dataset.cancelGoals !== undefined) box.innerHTML = goalsView(pj);
  };
}

const block = (id, title, line, body, cls = '') => `<section class="block ${cls}" aria-labelledby="${id}-h">
  <div class="block-head"><h2 id="${id}-h">${title}</h2><p class="small muted">${line}</p></div>${body}</section>`;
const profileLine = (p) => `For <strong>${esc(p.name)}</strong>${[p.role, p.organisation].some(Boolean) ? `, ${esc([p.role, p.organisation].filter(Boolean).join(', '))}` : ''}.
  Answers are written for this profile. <button type="button" class="ghost small link" onclick="document.getElementById('profile-btn').click()">Change profile</button>`;

const projectView = (pj) => `<header class="project-head"><h1>${esc(pj.title)}</h1>
  <p class="small muted for">${profileLine(state.profile)}</p>
  <div id="goals" class="goals">${goalsView(pj)}</div>
  <nav class="jump small" aria-label="On this page"><span class="muted">On this page</span>
    <button type="button" class="ghost small link" data-jump="fp-h">Data availability</button>
    <button type="button" class="ghost small link" data-jump="db-h">Dashboard</button>
    <button type="button" class="ghost small link" data-jump="qs-h">Questions (${pj.runs.filter((r) => !isFirstPass(r)).length})</button></nav></header>
  ${block('fp', 'Data availability and gaps', 'What exists for this project, and where sources disagree. Runs once, from the goals.',
    `<div id="first-pass">${firstPassEmpty(pj)}</div>`)}
  ${block('db', 'Dashboard', 'Key numbers, World Bank data and charts built from the answers in this project.', '<div id="dashboard" class="dashboard"></div>')}
  ${block('qs', 'Questions', 'Ask about this project. Every answer reads the goals and the earlier answers. Older answers fold away; reply under the latest.', `
  <form id="composer" class="composer">
    <label for="q">${pj.runs.some((r) => !isFirstPass(r)) ? 'Ask a new question' : 'Ask a question'}</label>
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
  </form>
  <div id="thread">${pj.runs.some((r) => !isFirstPass(r)) ? '' : '<p class="empty-line small muted">No questions yet. Ask one above or pick an example.</p>'}</div>`)}`;

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
      await startRun(query(), plan);
      $('#q').value = ''; $('#plan-editor').hidden = true; say('');
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
    <textarea rows="4" aria-label="Instruction">${esc(t.instruction)}</textarea><button type="button" data-remove>Remove</button></div>`;
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
function mountTurn(run, latest, box = $('#thread')) {
  const fp = box.id === 'first-pass';
  if (run.status === 'failed' && !run.answer) {
    box.insertAdjacentHTML('beforeend', failedTurn(run, fp));
    return $(`#run-${run.id}`);
  }
  box.insertAdjacentHTML('beforeend', `<section class="turn" id="run-${run.id}">
    ${fp ? `<p class="small muted fp-when">${run.status === 'running' ? 'First pass running, started' : 'First pass ran'} ${esc(when(run.created_at))}</p>`
      : `<div class="q"><p>${esc(run.query)}</p><time class="small muted">${esc(when(run.created_at))}</time></div>`}
    <p class="context small muted" hidden></p>
    <div class="status-line" role="status" hidden></div>
    <details class="trace"><summary>Show agents and tool calls</summary><div class="trace-body"></div></details>
    ${latest || !run.answer ? '<div class="answer"></div>' : `<details class="older"><summary><span class="more-label">Show the answer</span> <span class="muted">${esc(short(run.answer.summary.replace(/\s*\[[^\]]*10\.\d{4}[^\]]*\]/g, ''), 170))}</span></summary><div class="answer"></div></details>`}</section>`);
  const el = $(`#run-${run.id}`);
  el.run = run;
  if (run.status === 'running') {
    $('.trace', el).open = true;
    follow(run.id, el);
  } else {
    if (run.answer) mountAnswer(el, run.answer, latest);
    else status(el, 'This run finished without an answer. Open the trace to see which step failed, then ask again.', true);
    // Stored events give the context line now and the trace when it is opened.
    const tr = $('.trace', el);
    const events = () => (el.events ??= api(`/api/runs/${run.id}`).then((r) => r.events || []));
    events().then((evs) => { if (!tr.open) renderTrace(el, evs, false); }).catch(() => { el.events = null; });
    tr.addEventListener('toggle', async () => {
      if (!tr.open) return;
      $('.trace-body', el).innerHTML = '<p class="small muted">Loading the trace for this run</p>';
      try { renderTrace(el, await events(), false, true); }
      catch (e) { el.events = null; $('.trace-body', el).innerHTML = `<p class="small">Could not load the trace: ${esc(e.message)}. Close and open it to retry.</p>`; }
    });
  }
  return el;
}

// A failed run is one quiet line: what was asked, when, and a way to ask again. The trace stays one click away.
const failedTurn = (run, fp) => `<section class="turn failed" id="run-${run.id}">
  <div class="fail-line"><span class="st st-failed">Did not finish</span>
    <span class="fq">${esc(short(fp ? 'First pass' : run.query, 110))}</span><time class="small muted">${esc(when(run.created_at))}</time>
    <button type="button" class="ghost small" data-ask-again="${esc(run.query)}">${fp ? 'Run again' : 'Ask again'}</button></div></section>`;

document.addEventListener('click', (e) => {
  const j = e.target.dataset?.jump;
  if (j) return document.getElementById(j)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  const q = e.target.dataset?.askAgain;
  if (q === undefined) return;
  if (e.target.closest('#first-pass')) { $('#first-pass').innerHTML = firstPassEmpty(state.project); return $('[data-first-pass]')?.click(); }
  startRun(q).catch((err) => notice(`Could not start the run: ${err.message}.`, 'Try again in a moment.'));
});

// Starts a question in this project's thread; the new turn streams at the end of the thread.
async function startRun(query, plan = null) {
  const { run_id: id } = await api(`/api/projects/${state.project.id}/runs`, { method: 'POST', body: { query, agents: state.pinned.size ? [...state.pinned] : null, plan } });
  $('#thread .empty-line')?.remove();
  const el = mountTurn({ id, query, status: 'running', created_at: new Date().toISOString(), answer: null }, true);
  el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  return el;
}

// Reply box under an answer, like a chat: suggested follow-ups send at once; Review plan hands the question to the main ask box.
function replyBox(el, answer) {
  $('.reply', el)?.remove();
  const id = el.id.replace('run-', '');
  const fu = (Array.isArray(answer.follow_ups) ? answer.follow_ups : []).filter(Boolean).slice(0, 3);
  $('.answer', el).insertAdjacentHTML('afterend', `<form class="reply"><label for="reply-${id}">Ask a follow-up</label>
    ${fu.length ? `<div class="examples">${fu.map((q) => `<button type="button" class="ghost small" data-follow>${esc(q)}</button>`).join('')}</div>` : ''}
    <div class="reply-row"><textarea id="reply-${id}" rows="2" placeholder="Ask about this answer"></textarea>
      <div class="reply-actions"><button type="button" data-review>Review plan</button><button class="primary">Ask</button></div></div>
    <p class="form-msg" role="status"></p></form>`);
  const form = $('.reply', el); const box = $('textarea', form);
  const send = async () => {
    if (!box.value.trim()) { $('.form-msg', form).textContent = 'Write a question first.'; return; }
    form.querySelectorAll('button').forEach((b) => { b.disabled = true; });
    try { await startRun(box.value.trim()); box.value = ''; $('.form-msg', form).textContent = ''; }
    catch (e) { $('.form-msg', form).textContent = e.status === 429 ? e.message : `Could not start the run: ${e.message}. Try again in a moment.`; }
    finally { form.querySelectorAll('button').forEach((b) => { b.disabled = false; }); }
  };
  form.onsubmit = (e) => { e.preventDefault(); send(); };
  form.onclick = (e) => {
    if (e.target.dataset.follow !== undefined) { box.value = e.target.textContent; send(); }
    if (e.target.dataset.review !== undefined) {
      if (!box.value.trim()) { $('.form-msg', form).textContent = 'Write a question first.'; return; }
      $('#q').value = box.value.trim(); $('#composer').scrollIntoView({ behavior: 'smooth' }); $('#review').click();
    }
  };
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
    if (ev.type === 'run_done') {
      es.close(); streams.delete(es);
      if (ev.status === 'failed' && !$('.answer', el).innerHTML) {
        el.outerHTML = failedTurn({ ...el.run, created_at: el.run.created_at }, el.parentElement.id === 'first-pass');
        return;
      }
      if (el.parentElement.id === 'first-pass') setTimeout(() => state.pollDashboard?.(), 2000);
    }
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
    if (e.type === 'verifying') m.verifying = true;
    if (e.type === 'error') m.error = e.message;
    if (e.type === 'run_done') m.done = e.status;
  }
  m.ms = events.length > 1 ? new Date(events.at(-1).t) - new Date(events[0].t) : 0;
  return m;
}

const mainArg = (t) => Object.values(t.args || {}).find((v) => typeof v === 'string' && v);
// The server's summary repeats the tool and its argument ("search_concepts "x" -> 5 concepts"): keep only the result.
const result = (t) => short(String(t.summary || '').split(/\s+(?:->|→)\s+/).slice(1).join(' → ') || t.summary, 200);
const toolLine = (t) => `${mainArg(t) ? `“${short(mainArg(t), 90)}” → ` : ''}${result(t)}`;
const STATUS = { waiting: 'Waiting', running: 'Running', retrying: 'Retrying', done: 'Done', failed: 'Failed' };

function contextLine(el, c) {
  const p = $('.context', el);
  if (!c || !p) return;
  p.hidden = false;
  p.textContent = `What the agents knew: profile ${c.profile || 'none'}; ${c.project_goals ? 'the project goals' : 'no project goals'}; `
    + `${c.earlier_turns ? plural(c.earlier_turns, 'earlier answer', 'earlier answers') : 'no earlier answers'} in this project.`;
}

function renderTrace(el, events, live, keepOpen = false) {
  const m = traceModel(events);
  contextLine(el, events.find((e) => e.type === 'context'));
  const agents = [...m.agents.values()];
  const open = (el.expanded ??= new Set());
  $('.trace-body', el).onclick = (e) => {
    const n = e.target.dataset.more;
    if (n === undefined) return;
    open.has(n) ? open.delete(n) : open.add(n);
    renderTrace(el, events, live && !m.done, true);
  };
  const doneN = agents.filter((a) => a.status === 'done' || a.status === 'failed').length;
  $('.trace-body', el).innerHTML = `${m.plan ? `<p class="plan-q">Plan: ${esc(m.plan.question)}</p>` : ''}
    ${agents.length ? `<ul class="agents">${agents.map((a) => `<li class="agent">
      <div class="agent-head"><span class="st st-${a.status}">${STATUS[a.status]}</span><strong>${esc(agentTitle(a.name))}</strong>
        <span class="meta small muted num">${plural(a.tools.length, 'tool call', 'tool calls')}${a.t0 && a.t1 ? `, ${dur(new Date(a.t1) - new Date(a.t0))}` : ''}</span></div>
      ${a.instruction ? `<p class="instr">${esc(a.instruction)}</p>` : ''}
      ${a.tools.length ? `<ol class="tools">${a.tools.slice(open.has(a.name) ? 0 : -3).map((t) => `<li><code>${esc(t.tool)}</code><span>${esc(toolLine(t))}</span><span class="num">${dur(t.ms ?? 0)}</span></li>`).join('')}</ol>` : ''}
      ${a.tools.length > 3 ? `<button type="button" class="ghost small more" data-more="${esc(a.name)}">${open.has(a.name) ? 'Show the last 3' : `Show all ${a.tools.length} tool calls`}</button>` : ''}
      ${a.notes.map(([k, v]) => `<p class="note ${k === 'Failed' ? 'bad' : ''}">${k}: ${esc(short(v))}</p>`).join('')}
    </li>`).join('')}</ul>` : ''}`;
  $('.trace summary', el).textContent = m.done || !live
    ? `Trace: ${plural(agents.length, 'agent', 'agents')}, ${plural(m.tools, 'tool call', 'tool calls')}, ${dur(m.ms)}`
    : 'Agents and tool calls';

  if (m.error) return status(el, `The run stopped: ${short(m.error).replace(/[.\s]+$/, '')}. Ask the question again.`, true);
  if (m.done === 'failed' && !$('.answer', el).innerHTML) return status(el, 'The run failed before writing an answer. Check the failed agent above, then ask again.', true);
  if (!live) { status(el, ''); if (!keepOpen) $('.trace', el).open = false; return; }
  if (!m.plan) return status(el, 'Planning: choosing agents for this question');
  if (m.verifying) return status(el, 'Verifying: checking the answer\'s claims and numbers against the tool results');
  if (m.formatting) return status(el, `Writing the answer from ${plural(agents.filter((a) => a.status === 'done').length, 'section', 'sections')}`);
  const lastRunning = m.last && ['running', 'retrying'].includes(m.agents.get(m.last.agent)?.status) ? m.last : null;
  status(el, `${doneN} of ${agents.length} agents finished. `
    + (lastRunning ? `${agentTitle(lastRunning.agent)}: ${lastRunning.tool.replaceAll('_', ' ')} ${toolLine(lastRunning)}` : 'Agents are starting their first tool calls'));
}

// Answer and graph ---------------------------------------------------------------------------------
function mountAnswer(el, answer, drawNow) {
  const box = $('.answer', el);
  box.innerHTML = renderAnswer(answer, el.id.replace('run-', ''));
  replyBox(el, answer);
  mountCharts(box);
  fillReferences(box);
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
    } catch (e) {
      panel.innerHTML = `<p class="small">Could not draw the graph: ${esc(short(e.message))}. The answer is unaffected. <button type="button" class="small">Try again</button></p>`;
      $('button', panel).onclick = draw;
    }
  };
  if (drawNow) draw();
  else {
    panel.innerHTML = `<button type="button">Show graph of ${plural(ids.length, 'concept', 'concepts')}</button>`;
    panel.firstChild.onclick = draw;
  }
}

// Titles, venues and years for the References list; DOIs the lookup does not know stay as plain DOI links.
async function fillReferences(box) {
  const items = [...box.querySelectorAll('.refs-list li[data-doi]')];
  for (let i = 0; i < items.length; i += 50) {
    const chunk = items.slice(i, i + 50);
    try {
      const found = await api(`/api/references?dois=${encodeURIComponent(chunk.map((li) => li.dataset.doi).join(','))}`);
      const by = new Map(found.map((r) => [String(r.doi).toLowerCase(), r]));
      for (const li of chunk) {
        const r = by.get(li.dataset.doi.toLowerCase());
        if (r?.title) $('div', li).innerHTML = refBody({ ...r, doi: li.dataset.doi });
      }
    } catch { /* the DOI links still work without titles */ }
  }
}

// Citation links scroll to their reference and flash it. Verdict pills open the findings table of their card.
document.addEventListener('click', (e) => {
  const c = e.target.closest('a[data-ref]');
  if (c) {
    e.preventDefault();
    const li = document.getElementById(c.dataset.ref);
    if (!li) return;
    li.scrollIntoView({ behavior: 'smooth', block: 'center' });
    li.classList.remove('flash'); void li.offsetWidth; li.classList.add('flash');
    return;
  }
  const f = e.target.closest('button[data-show]');
  if (f) {
    const sec = f.closest('.sec');
    sec.querySelectorAll('[data-show]').forEach((b) => b.setAttribute('aria-pressed', b === f));
    sec.querySelectorAll('tr[data-kind]').forEach((tr) => { tr.hidden = !!f.dataset.show && !tr.dataset.kind.split(' ').includes(f.dataset.show); });
    return;
  }
  const csv = e.target.closest('button[data-csv]');
  if (csv) return downloadCsv(csv.dataset.csv);
  const v = e.target.closest('button[data-findings]');
  const d = v?.closest('.card')?.querySelector('details.findings');
  if (!d) return;
  d.open = !d.open;
  v.setAttribute('aria-expanded', d.open);
});

load();
