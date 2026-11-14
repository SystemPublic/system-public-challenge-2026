// CAMOX v2 entry: boot the session, then show sign-in or the workspace.
import { createRoot } from 'react-dom/client';
import { html, useState, useEffect, boot } from './api.js';
import { AuthScreen } from './components/auth.js';
import { Workspace } from './components/workspace.js';
import { installAnswerClicks } from './components/answer.js';

function App() {
  const [session, setSession] = useState(undefined);
  useEffect(() => { boot().then(setSession); }, []);
  if (session === undefined) return html`<div class="boot"><span class="brand">CAMOX</span><p class="muted small">Opening your workspace</p></div>`;
  if (!session) return html`<${AuthScreen} onSession=${setSession} />`;
  return html`<${Workspace} key=${session.user?.id ?? 'demo'} session=${session} setSession=${setSession} />`;
}

installAnswerClicks();
createRoot(document.getElementById('root')).render(html`<${App} />`);
