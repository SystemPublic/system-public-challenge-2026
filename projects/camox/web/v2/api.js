// Server calls, session and prefs, hash routing, and small shared helpers.
import React from 'react';
import htm from 'htm';

export const html = htm.bind(React.createElement);
export const { useState, useEffect, useRef, useMemo } = React;

export async function api(path, opts = {}) {
  const res = await fetch(path, {
    method: opts.method || 'GET', credentials: 'same-origin',
    headers: opts.body ? { 'Content-Type': 'application/json' } : {}, body: opts.body && JSON.stringify(opts.body),
  }).catch(() => { throw new Error('could not reach the server; check your connection'); });
  const text = await res.text();
  let data = text;
  try { data = JSON.parse(text); } catch { /* plain text body */ }
  if (!res.ok) {
    const d = data?.detail ?? data;
    const msg = res.status >= 502 ? 'the server is waking up or restarting; try again in a minute'
      : Array.isArray(d) ? d.map((x) => `${x.loc?.at(-1) ?? ''} ${x.msg}`.trim()).join('; ')
      : typeof d === 'string' && d && !d.trimStart().startsWith('<') ? d.slice(0, 200) : `server error ${res.status}`;
    throw Object.assign(new Error(msg), { status: res.status });
  }
  return data;
}

// Per-browser storage: demo prefs and question drafts. Never required for the page to work.
export const local = {
  get: (k, d = null) => { try { return JSON.parse(localStorage.getItem(`camox2.${k}`)) ?? d; } catch { return d; } },
  set: (k, v) => { try { v == null ? localStorage.removeItem(`camox2.${k}`) : localStorage.setItem(`camox2.${k}`, JSON.stringify(v)); } catch { /* storage off */ } },
};

// A session is {mode: 'account' | 'demo', user, profiles, prefs}. Accounts keep prefs on the server, demo in this browser.
export async function boot() {
  try { const me = await api('/api/auth/me'); return { mode: 'account', ...me, prefs: me.prefs || {} }; } catch { /* signed out or accounts off */ }
  if (local.get('mode') === 'demo' || parseHash().profile) return demoSession().catch(() => null);
  return null;
}
export async function demoSession() {
  local.set('mode', 'demo');
  return { mode: 'demo', user: null, profiles: await api('/api/profiles'), prefs: local.get('prefs', {}) };
}
export function savePrefs(session, patch) {
  Object.assign(session.prefs, patch);
  if (session.mode === 'demo') return local.set('prefs', session.prefs);
  api('/api/auth/prefs', { method: 'PUT', body: patch }).catch(() => { /* prefs are a convenience */ });
}
export async function signOut(session) {
  if (session.mode === 'account') await api('/api/auth/logout', { method: 'POST' }).catch(() => {});
  local.set('mode', null);
  history.replaceState(null, '', location.pathname);
}

// Hash routes: #profile=1&project=10&thread=2
export const parseHash = () => Object.fromEntries(new URLSearchParams(location.hash.slice(1)));
export function go(r, replace = false) {
  const s = new URLSearchParams(Object.entries(r).filter(([, v]) => v != null && v !== '')).toString();
  if (!replace) { location.hash = s; return; }
  history.replaceState(null, '', `#${s}`);
  window.dispatchEvent(new HashChangeEvent('hashchange'));
}
export function useRoute() {
  const [r, setR] = useState(parseHash);
  useEffect(() => { const f = () => setR(parseHash()); addEventListener('hashchange', f); return () => removeEventListener('hashchange', f); }, []);
  return r;
}

// Raw HTML from the shared renderers in ../sections.js; onMount runs after each new markup string.
export function Raw({ markup, className, onMount }) {
  const ref = useRef(null);
  useEffect(() => { onMount?.(ref.current); }, [markup]);
  return html`<div ref=${ref} className=${className} dangerouslySetInnerHTML=${{ __html: markup }} />`;
}

export const FIRST_PASS = 'First pass: what data is available for this project, and where do sources disagree or run out?';
export const isFirstPass = (r) => r.kind === 'first_pass' || /^first pass\b/i.test(r.query || '');
export const when = (iso) => (iso ? new Date(iso).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' }) : '');
export const dur = (ms) => (ms < 1000 ? `${Math.round(ms)} ms` : `${(ms / 1000).toFixed(1)} s`);
export const firstLine = (s) => String(s || '').split(/(?<=[.:;])\s/)[0].replace(/[.:;]$/, '');
