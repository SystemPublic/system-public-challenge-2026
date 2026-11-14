// Settings: account, the profile the agents read, API keys, default agents, log out and delete account.
import { html, useState, api, savePrefs, signOut } from '../api.js';

export function Settings({ session, setSession, profile, agents }) {
  const account = session.mode === 'account';
  const out = async () => { await signOut(session); setSession(null); };
  return html`<div class="page settings">
    <header class="phead"><p class="eyebrow">Settings</p><h1>Your account</h1></header>
    ${account && html`<${Section} title="Account" line="Who is signed in.">
      <dl class="kv"><dt>Name</dt><dd>${session.user?.name || profile.name}</dd><dt>Email</dt><dd>${session.user?.email}</dd></dl>
      <${PasswordForm} />
    <//>`}
    <${Section} title="Profile" line="Every agent reads this to tailor plans and answers.">
      <${ProfileForm} key=${profile.id} session=${session} setSession=${setSession} profile=${profile} />
    <//>
    <${Section} title="API keys" line="Optional. Store your own API keys (for example OpenAlex) for keyed tools as we add them. Keys are stored encrypted; only their names are shown again.">
      <${Keys} key=${profile.id} profile=${profile} />
    <//>
    <//>
    <${Section} title=${account ? 'Log out' : 'Leave demo'} line=${account ? 'Ends this session on this browser.' : 'Returns to the sign-in screen. Your place is kept in this browser.'}>
      <div><button type="button" class="outline" onClick=${out}>${account ? 'Log out' : 'Leave demo'}</button></div>
    <//>
    ${account && html`<${Section} title="Danger zone" line="Deleting your account removes your profiles, projects and runs." danger>
      <${DeleteAccount} session=${session} setSession=${setSession} />
    <//>`}
  </div>`;
}

const Section = ({ title, line, danger, children }) => html`<section class=${`block ${danger ? 'danger' : ''}`}>
  <div class="block-head"><h2>${title}</h2><p class="muted small">${line}</p></div>${children}</section>`;

function useSubmit(fn) {
  const [msg, setMsg] = useState(['', false]);
  const [busy, setBusy] = useState(false);
  const submit = async (e) => {
    e.preventDefault(); setBusy(true); setMsg(['', false]);
    try { setMsg([await fn(Object.fromEntries(new FormData(e.target)), e.target), false]); }
    catch (x) { setMsg([x.message, true]); } finally { setBusy(false); }
  };
  return [submit, busy, msg[0] && html`<p class=${`msg ${msg[1] ? 'bad' : ''}`} role="status">${msg[0]}</p>`];
}

function PasswordForm() {
  const [submit, busy, note] = useSubmit(async (f, form) => {
    try { await api('/api/auth/password', { method: 'PUT', body: { current: f.current, new: f.new } }); }
    catch (x) { throw new Error(x.status === 401 ? 'Current password is wrong.' : `Could not change the password: ${x.message}.`); }
    form.reset();
    return 'Password changed.';
  });
  return html`<form class="settings-form" onSubmit=${submit}>
    <div class="grid2">
      <div class="field"><label for="pw-cur">Current password</label><input id="pw-cur" name="current" type="password" required autocomplete="current-password" /></div>
      <div class="field"><label for="pw-new">New password</label><input id="pw-new" name="new" type="password" required minlength="8" autocomplete="new-password" /></div>
    </div>${note}
    <div class="row-end"><button class="outline" disabled=${busy}>Change password</button></div></form>`;
}

function ProfileForm({ session, setSession, profile }) {
  const editable = session.mode === 'account';
  const [submit, busy, note] = useSubmit(async (f) => {
    const p = await api(`/api/auth/profiles/${profile.id}`, { method: 'PUT', body: f })
      .catch((x) => { throw new Error(`Could not save the profile: ${x.message}.`); });
    setSession({ ...session, profiles: session.profiles.map((x) => (x.id === profile.id ? { ...x, ...p } : x)) });
    return 'Saved. New questions use this profile.';
  });
  return html`<form class="settings-form" onSubmit=${submit}>
    <fieldset disabled=${!editable}>
      <div class="grid2">
        <div class="field"><label for="sp-name">Name</label><input id="sp-name" name="name" required defaultValue=${profile.name} /></div>
        <div class="field"><label for="sp-role">Role</label><input id="sp-role" name="role" defaultValue=${profile.role || ''} placeholder="Jobs data analyst" /></div>
      </div>
      <div class="field"><label for="sp-org">Organisation</label><input id="sp-org" name="organisation" defaultValue=${profile.organisation || ''} placeholder="World Bank" /></div>
      <div class="field"><label for="sp-about">What you work on</label><textarea id="sp-about" name="about" rows="3" defaultValue=${profile.about || ''}
        placeholder="Places, populations and decisions you inform"></textarea></div>
    </fieldset>${note}
    ${editable ? html`<div class="row-end"><button class="primary" disabled=${busy}>Save profile</button></div>`
      : html`<p class="small muted">Demo profiles are read-only. Sign up to make your own.</p>`}</form>`;
}

function Keys({ profile }) {
  const [names, setNames] = useState(profile.key_names || []);
  const [submit, busy, note] = useSubmit(async (f, form) => {
    setNames((await api(`/api/profiles/${profile.id}/keys`, { method: 'PUT', body: { [f.name.trim()]: f.value } })).key_names);
    form.reset();
    return 'Key saved.';
  });
  const remove = async (k) => { try { setNames((await api(`/api/profiles/${profile.id}/keys`, { method: 'PUT', body: { [k]: '' } })).key_names); } catch { /* list stays */ } };
  return html`${names.length ? html`<ul class="key-list">${names.map((k) => html`<li key=${k}><code>${k}</code>
      <button type="button" class="ghost-btn small" onClick=${() => remove(k)}>Remove</button></li>`)}</ul>` : html`<p class="small muted">No keys saved.</p>`}
    <form class="settings-form" onSubmit=${submit}>
      <div class="grid2">
        <div class="field"><label for="k-name">Key name</label><input id="k-name" name="name" list="key-names" required placeholder="OPENALEX_API_KEY" /></div>
        <div class="field"><label for="k-value">Value</label><input id="k-value" name="value" type="password" autocomplete="off" required /></div>
      </div>
      <datalist id="key-names"><option value="OPENALEX_API_KEY" /><option value="DHS_API_KEY" /></datalist>${note}
      <div class="row-end"><button class="outline" disabled=${busy}>Save key</button></div></form>`;
}
