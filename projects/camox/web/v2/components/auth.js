// First screen when signed out: log in, sign up, or try the example profiles without an account.
import { html, useState, useEffect, api, local, demoSession, go } from '../api.js';

const ACCOUNTS_OFF = 'Accounts are not switched on on this server yet. Try the demo profiles below; they need no account.';

export function AuthScreen({ onSession }) {
  const [tab, setTab] = useState('login');
  const [err, setErr] = useState('');
  const [busy, setBusy] = useState(false);
  const [demo, setDemo] = useState(null);
  const [nAgents, setNAgents] = useState(null);
  useEffect(() => { api('/api/agents').then((a) => setNAgents(a.length)).catch(() => {}); }, []);

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true); setErr('');
    try {
      const r = await api(`/api/auth/${tab}`, { method: 'POST', body: Object.fromEntries(new FormData(e.target)) });
      const session = { mode: 'account', ...r, profiles: r.profiles || [], prefs: r.prefs || {} };
      if (tab === 'signup' && session.profiles.length) go({ profile: session.profiles.at(-1).id }, true);  // the profile just created
      onSession(session);
    } catch (x) {
      setErr(x.status === 404 || x.status === 405 ? ACCOUNTS_OFF
        : x.status === 401 ? 'That email and password do not match an account. Check them, or sign up.'
        : `Could not ${tab === 'login' ? 'log in' : 'sign up'}: ${x.message}.`);
    } finally { setBusy(false); }
  };
  const showDemo = async () => {
    try { setDemo(await api('/api/profiles')); } catch (x) { setErr(`Could not load the demo profiles: ${x.message}.`); }
  };
  const pick = async (p) => {
    const prefs = local.get('prefs', {});
    const same = String(prefs.profile_id) === String(p.id);
    go({ profile: p.id, project: same ? prefs.project_id : null, thread: same ? prefs.thread_id : null }, true);
    onSession(await demoSession());
  };

  return html`<div class="auth">
    <section class="auth-hero">
      <a class="brand" href="#">CAMOX</a>
      <p class="eyebrow">An agentic layer over the System Public Graph</p>
      <h1>Ask the evidence. See where it runs out.</h1>
      <p class="lede">Specialist agents read about 2M published statistical findings, World Bank indicators and the wider literature, then answer your question with verdicts, counts and the gaps in the evidence. Every claim is checked and cited. They report associations, not causes.</p>
      <div class="hero-actions">
        <button type="button" class="primary" onClick=${() => { showDemo(); setTimeout(() => document.querySelector('.demo-list button')?.focus(), 300); }}>Try the demo</button>
        <button type="button" class="outline" onClick=${() => { setTab('signup'); setErr(''); setTimeout(() => document.getElementById('a-name')?.focus(), 0); }}>Sign up</button>
        <button type="button" class="ghost-btn" onClick=${() => { setTab('login'); setErr(''); setTimeout(() => document.getElementById('a-email')?.focus(), 0); }}>Log in</button>
      </div>
      <dl class="stats">
        <div><dt class="num">2M</dt><dd>published findings</dd></div>
        <div><dt class="num">${nAgents ?? '·'}</dt><dd>specialist agents</dd></div>
        <div><dt class="num">[n]</dt><dd>every claim cited</dd></div>
      </dl>
    </section>
    <section class="auth-card panel-box">
      <div class="tabs" role="tablist">
        ${[['login', 'Log in'], ['signup', 'Sign up']].map(([k, t]) => html`<button key=${k} type="button" role="tab" aria-selected=${tab === k}
          onClick=${() => { setTab(k); setErr(''); }}>${t}</button>`)}
      </div>
      <form onSubmit=${submit} key=${tab}>
        ${tab === 'signup' && html`<div class="field"><label for="a-name">Name</label><input id="a-name" name="name" required autocomplete="name" /></div>`}
        <div class="field"><label for="a-email">Email</label><input id="a-email" name="email" type="email" required autocomplete="email" /></div>
        <div class="field"><label for="a-pw">Password</label><input id="a-pw" name="password" type="password" required minlength=${tab === 'signup' ? 8 : undefined}
          autocomplete=${tab === 'signup' ? 'new-password' : 'current-password'} /></div>
        ${tab === 'signup' && html`
          <p class="hint">The agents tailor every answer to who you are and what you work on.</p>
          <div class="grid2">
            <div class="field"><label for="a-role">Role</label><input id="a-role" name="role" required placeholder="Jobs data analyst" /></div>
            <div class="field"><label for="a-org">Organisation</label><input id="a-org" name="organisation" required placeholder="World Bank" /></div>
          </div>
          <div class="field"><label for="a-about">What you work on</label>
            <textarea id="a-about" name="about" rows="3" placeholder="Places, populations and decisions you inform. For example: community health in Lagos, children under 5, district budget choices"></textarea></div>`}
        ${err && html`<p class="msg bad" role="alert">${err}</p>`}
        <button class="primary wide" disabled=${busy}>${busy ? 'One moment' : tab === 'login' ? 'Log in' : 'Create account'}</button>
      </form>
      <div class="or"><span>or</span></div>
      ${!demo ? html`<button type="button" class="outline wide" onClick=${showDemo}>Try the demo</button>
        <p class="hint center">Example profiles with finished projects, no account needed.</p>`
      : html`<p class="eyebrow">Pick an example profile</p><ul class="demo-list">${demo.map((p) => html`<li key=${p.id}><button type="button" onClick=${() => pick(p)}>
          <span class="avatar">${initials(p.name)}</span>
          <span><strong>${p.name}</strong><span class="small muted">${[p.role, p.organisation].filter(Boolean).join(', ')}</span></span>
          <span class="go" aria-hidden="true">→</span></button></li>`)}</ul>`}
    </section>
  </div>`;
}

export const initials = (n) => String(n || '?').split(/\s+/).map((w) => w[0]).slice(0, 2).join('').toUpperCase();
