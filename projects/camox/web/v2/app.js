// CAMOX v2 entry: boot the session, then show sign-in or the workspace.
import { createRoot } from 'react-dom/client';
import { html, useState, useEffect, boot } from './api.js';
import { AuthScreen } from './components/auth.js';
import { Workspace } from './components/workspace.js';
import { installAnswerClicks } from './components/answer.js';

function App() {
  const [session, setSession] = useState(undefined);
  const [slow, setSlow] = useState(false);
  useEffect(() => { const t = setTimeout(() => setSlow(true), 5000); boot().then(setSession).finally(() => clearTimeout(t)); }, []);
  if (session === undefined) return html`<div class="boot"><span class="brand">CAMOX</span><p class="muted small">${slow ? 'Waking the server, about a minute' : 'Loading projects…'}</p></div>`;
  if (!session) return html`<${AuthScreen} onSession=${setSession} />`;
  return html`<${Workspace} key=${session.user?.id ?? 'demo'} session=${session} setSession=${setSession} />`;
}

installAnswerClicks();
createRoot(document.getElementById('root')).render(html`<${App} />`);
