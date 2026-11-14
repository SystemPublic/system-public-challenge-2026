// Workspace shell: projects sidebar (drawer on phones), profile menu, and the project or new-project view.
import { html, useState, useEffect, api, go, useRoute, savePrefs, signOut } from '../api.js';
import { plural, short } from '../../sections.js';
import { initials } from './auth.js';
import { ProjectHome } from './project.js';
import { Settings } from './settings.js';

const projectStatus = (x) => {
  const s = x.first_pass_status;
  if (s === 'running') return ['busy', 'First pass running'];
  if (s === 'done') return ['ok', `First pass ready · ${plural(x.n_runs ?? 1, 'run', 'runs')}`];
  if (!x.goals) return ['', 'No goals yet'];
  return [x.n_runs ? 'ok' : '', plural(x.n_runs ?? 0, 'run', 'runs')];
};

export function Workspace({ session, setSession }) {
  const route = useRoute();
  const [agents, setAgents] = useState([]);
  const [projects, setProjects] = useState(null);
  const [project, setProject] = useState(null);
  const [threads, setThreads] = useState(null);
  const [error, setError] = useState('');
  const [navOpen, setNavOpen] = useState(false);
  const { profiles, prefs } = session;
  const profile = profiles.find((p) => String(p.id) === route.profile) || null;
  const thread = route.thread ? Number(route.thread) : null;

  // Restore the last place from prefs, or fall back to the first profile.
  useEffect(() => {
    if (!route.profile && profiles.length) {
      const known = profiles.some((p) => String(p.id) === String(prefs.profile_id));
      go(known ? { profile: prefs.profile_id, project: prefs.project_id, thread: prefs.thread_id } : { profile: profiles[0].id }, true);
    } else if (route.profile && !profile && profiles.length) go({ profile: profiles[0].id }, true);
  }, [route.profile]);
  useEffect(() => {
    if (profile) savePrefs(session, { profile_id: profile.id, project_id: route.project ? Number(route.project) : null, thread_id: thread });
    setNavOpen(false);
  }, [route.profile, route.project, route.thread, route.view]);
  useEffect(() => { api('/api/agents').then(setAgents).catch(() => setAgents([])); }, []);

  const loadProjects = () => profile && api(`/api/profiles/${profile.id}/projects`).then(setProjects)
    .catch((e) => setError(`Could not load your projects: ${e.message}. Reload the page to try again.`));
  useEffect(() => { setProjects(null); loadProjects(); }, [profile?.id]);

  const reload = async () => {
    if (!route.project) return;
    try {
      const [pj, th] = await Promise.all([api(`/api/projects/${route.project}`), api(`/api/projects/${route.project}/threads`).catch(() => null)]);
      if (String(pj.id) !== String(parseHashProject())) return;  // the user moved on
      setProject(pj); setThreads(th); setError('');
    } catch (e) { setError(`Could not open that project: ${e.message}. Pick one from the list.`); setProject(null); }
    loadProjects();
  };
  useEffect(() => { setProject(null); setThreads(null); reload(); }, [route.project]);

  if (!profiles.length) return html`<${NoProfile} session=${session} setSession=${setSession} />`;
  if (!profile) return null;
  const current = project && String(project.id) === route.project ? project : null;

  return html`<div class="ws">
    <header class="topbar">
      <a class="brand" href=${`#profile=${profile.id}`}>CAMOX</a>
      <span class="topbar-title">${current?.title || ''}</span>
      <button type="button" class="outline small" aria-expanded=${navOpen} onClick=${() => setNavOpen(!navOpen)}>${navOpen ? 'Close' : 'Projects'}</button>
    </header>
    <div class="scrim" hidden=${!navOpen} onClick=${() => setNavOpen(false)}></div>
    <aside class="side" data-open=${navOpen} aria-label="Projects">
      <a class="brand side-brand" href=${`#profile=${profile.id}`}>CAMOX</a>
      <${ProfileMenu} session=${session} setSession=${setSession} profile=${profile} />
      <div class="side-label"><span class="eyebrow">Projects</span>
        <a class="ghost-btn small" href=${`#profile=${profile.id}`} aria-current=${!route.project ? 'page' : undefined}>New project</a></div>
      ${projects === null ? html`<p class="small muted pad">Loading projects</p>`
        : !projects.length ? html`<p class="small muted pad">No projects yet. Create one to start.</p>`
        : html`<ul class="proj-list">${byFolder(projects).map((x, i, all) => {
          const active = String(x.id) === route.project;
          const [tone, text] = projectStatus(active && current ? { ...x, first_pass_status: fpStatus(current) ?? x.first_pass_status } : x);
          const head = x.folder && x.folder !== all[i - 1]?.folder && html`<li key=${`f-${x.folder}`} class="folder eyebrow">${x.folder}</li>`;
          return html`${head}<li key=${x.id}>
            <a href=${`#profile=${profile.id}&project=${x.id}`} aria-current=${active ? 'page' : undefined}>
              <span class="t">${x.title}</span>
              ${x.goals && html`<span class="g">${short(x.goals.split('\n')[0], 90)}</span>`}
              <span class="st"><i class=${`dot ${tone}`}></i>${text}</span></a>
            ${active && threads && html`<${ThreadList} threads=${threads} thread=${thread} profile=${profile} project=${x} setError=${setError} />`}
          </li>`;
        })}</ul>`}
    </aside>
    <main class="main">
      ${session.mode === 'demo' && html`<p class="demo-banner"><span>Demo: example projects. Sign up to create your own.</span>
        <button type="button" class="outline small" onClick=${async () => { await signOut(session); setSession(null); }}>Sign up</button></p>`}
      ${error && html`<p class="notice" role="alert">${error}</p>`}
      ${route.view === 'settings' ? html`<${Settings} session=${session} setSession=${setSession} profile=${profile} agents=${agents} />`
        : route.project ? (current ? html`<${ProjectHome} key=${current.id} project=${current} profile=${profile} agents=${agents} session=${session}
            threads=${threads} thread=${thread} reload=${reload} projects=${projects || []}
            owner=${session.mode === 'account'} onDeleted=${() => { go({ profile: profile.id }); loadProjects(); }} />` : !error && html`<p class="muted pad-lg">Opening the project</p>`)
        : html`<${NewProject} profile=${profile} projects=${projects} />`}
    </main>
  </div>`;
}

// Ungrouped projects first, then each folder in name order.
const byFolder = (ps) => [...ps].sort((a, b) => (a.folder ? 1 : 0) - (b.folder ? 1 : 0) || String(a.folder || '').localeCompare(String(b.folder || '')));
const parseHashProject = () => new URLSearchParams(location.hash.slice(1)).get('project');
const fpStatus = (pj) => {
  const f = pj.runs.filter((r) => r.kind === 'first_pass' || /^first pass\b/i.test(r.query || ''));
  return f.some((r) => r.status === 'running') ? 'running' : f.some((r) => r.answer) ? 'done' : null;
};

function ThreadList({ threads, thread, profile, project, setError }) {
  const href = (t) => `#profile=${profile.id}&project=${project.id}${t.id ? `&thread=${t.id}` : ''}`;
  const create = async () => {
    try {
      const t = await api(`/api/projects/${project.id}/threads`, { method: 'POST', body: { title: 'New thread' } });
      go({ profile: profile.id, project: project.id, thread: t.id });
    } catch (e) { setError(`Could not create the thread: ${e.message}. Try again in a moment.`); }
  };
  return html`<ul class="threads" aria-label="Threads">
    ${threads.map((t) => html`<li key=${t.id ?? 'main'}><a href=${href(t)} aria-current=${(t.id ?? null) === thread ? 'true' : undefined}>
      <span>${t.title}</span>${Number.isFinite(t.n_runs) && html`<span class="num muted">${t.n_runs}</span>`}</a></li>`)}
    <li><button type="button" class="ghost-btn small" onClick=${create}>New thread</button></li></ul>`;
}

function ProfileMenu({ session, setSession, profile }) {
  const [adding, setAdding] = useState(false);
  const [msg, setMsg] = useState('');
  const others = session.profiles.filter((p) => p.id !== profile.id);
  const add = async (e) => {
    e.preventDefault();
    const body = Object.fromEntries(new FormData(e.target));
    try {
      const p = await api(session.mode === 'account' ? '/api/auth/profiles' : '/api/profiles', { method: 'POST', body });
      const made = p.profiles ? p.profiles.at(-1) : p;  // the endpoint may return the profile or the whole list
      setSession({ ...session, profiles: p.profiles || [...session.profiles, made] });
      setAdding(false); go({ profile: made.id });
    } catch (x) { setMsg(`Could not add the profile: ${x.message}.`); }
  };
  const out = async () => { await signOut(session); setSession(null); };
  return html`<details class="profile-menu">
    <summary><span class="avatar">${initials(profile.name)}</span>
      <span class="who"><strong>${profile.name}</strong><span class="small muted">${[profile.role, profile.organisation].filter(Boolean).join(', ') || 'No role set'}</span></span>
      <span class="caret" aria-hidden="true">▾</span></summary>
    <div class="menu-body">
      ${session.user?.email && html`<p class="small muted">Signed in as ${session.user.email}</p>`}
      ${session.mode === 'demo' && html`<p class="small muted">Demo mode: example profiles, no account. Your place is kept in this browser.</p>`}
      ${others.length > 0 && html`<p class="eyebrow">Switch profile</p>
        <ul class="plain-list">${others.map((p) => html`<li key=${p.id}><a href=${`#profile=${p.id}`}>${p.name}<span class="small muted">${[p.role, p.organisation].filter(Boolean).join(', ')}</span></a></li>`)}</ul>`}
      <a class="ghost-btn small" href=${`#profile=${profile.id}&view=settings`}>Settings</a>
      ${adding ? html`<${ProfileForm} onSubmit=${add} onCancel=${() => setAdding(false)} msg=${msg} />`
        : html`<button type="button" class="ghost-btn small" onClick=${() => setAdding(true)}>Add a profile</button>`}
      <button type="button" class="outline small wide" onClick=${out}>${session.mode === 'account' ? 'Log out' : 'Leave demo'}</button>
    </div></details>`;
}

const ProfileForm = ({ onSubmit, onCancel, msg }) => html`<form class="stack-form" onSubmit=${onSubmit}>
  <div class="field"><label for="pf-name">Name</label><input id="pf-name" name="name" required /></div>
  <div class="field"><label for="pf-role">Role</label><input id="pf-role" name="role" placeholder="Community health worker" /></div>
  <div class="field"><label for="pf-org">Organisation</label><input id="pf-org" name="organisation" placeholder="NYU Langone Health" /></div>
  <div class="field"><label for="pf-about">What you work on</label><textarea id="pf-about" name="about" rows="2" placeholder="Places, populations, decisions you inform"></textarea></div>
  ${msg && html`<p class="msg bad">${msg}</p>`}
  <div class="row-end">${onCancel && html`<button type="button" class="ghost-btn" onClick=${onCancel}>Cancel</button>`}<button class="primary">Save profile</button></div>
</form>`;

function NoProfile({ session, setSession }) {
  const [msg, setMsg] = useState('');
  const add = async (e) => {
    e.preventDefault();
    try {
      const p = await api('/api/auth/profiles', { method: 'POST', body: Object.fromEntries(new FormData(e.target)) });
      const list = p.profiles || [p];
      go({ profile: list.at(-1).id }, true);
      setSession({ ...session, profiles: list });
    } catch (x) { setMsg(`Could not save the profile: ${x.message}.`); }
  };
  return html`<div class="center-page"><div class="panel-box narrow">
    <p class="eyebrow">One step left</p><h1>Who are the answers for?</h1>
    <p class="muted">The agents tailor every answer to your role and work. You can add more profiles later.</p>
    <${ProfileForm} onSubmit=${add} msg=${msg} />
    <button type="button" class="ghost-btn small" onClick=${async () => { await signOut(session); setSession(null); }}>Log out</button>
  </div></div>`;
}

function NewProject({ profile, projects }) {
  const [msg, setMsg] = useState('');
  const [busy, setBusy] = useState(false);
  const create = async (e) => {
    e.preventDefault();
    const f = Object.fromEntries(new FormData(e.target));
    setBusy(true);
    try {
      const x = await api(`/api/profiles/${profile.id}/projects`, { method: 'POST', body: { title: f.title.trim(), goals: f.goals.trim() } });
      go({ profile: profile.id, project: x.id });
    } catch (err) { setBusy(false); setMsg(`Could not create the project: ${err.message}. Try again.`); }
  };
  return html`<div class="page">
    ${projects?.length > 0 && html`<section class="cards-list">
      <p class="eyebrow">Your projects</p>
      <ul>${projects.map((x) => { const [tone, text] = projectStatus(x); return html`<li key=${x.id}><a class="proj-card" href=${`#profile=${profile.id}&project=${x.id}`}>
        <strong>${x.title}</strong>${x.goals && html`<span class="small muted">${short(x.goals, 140)}</span>`}
        <span class="st small"><i class=${`dot ${tone}`}></i>${text}</span></a></li>`; })}</ul></section>`}
    <section class="panel-box">
      <p class="eyebrow">New project</p>
      <h1>Start from the goals</h1>
      <p class="muted">A project is one piece of work, such as a brief or a programme note. Its goals drive what happens next:</p>
      <ol class="how">
        <li><strong>First pass.</strong> Maps which data and studies exist for the goals, and where sources disagree.</li>
        <li><strong>Dashboard.</strong> Key numbers and charts built from that first pass.</li>
        <li><strong>Questions.</strong> Every answer reads the goals and the earlier answers.</li>
      </ol>
      <form onSubmit=${create}>
        <div class="field"><label for="np-title">Title</label><input id="np-title" name="title" required placeholder="Youth employment brief" /></div>
        <div class="field"><label for="np-goals">Goals and context</label>
          <textarea id="np-goals" name="goals" rows="5" required placeholder="What the work is for, who will read it, and its scope: countries, populations, years."></textarea></div>
        ${msg && html`<p class="msg bad" role="alert">${msg}</p>`}
        <div class="row-end"><button class="primary" disabled=${busy}>${busy ? 'Creating' : 'Create and start the first pass'}</button></div>
      </form>
      <p class="small muted">Tailored for ${[profile.role, profile.organisation].filter(Boolean).join(', ') || profile.name}.</p>
    </section></div>`;
}
