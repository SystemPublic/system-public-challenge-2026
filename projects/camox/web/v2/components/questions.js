// Questions: the thread of runs, then the ask box with follow-ups, the agent chooser and the editable plan.
import { html, useState, useEffect, api, local, savePrefs, firstLine } from '../api.js';
import { Turn } from './turn.js';

// Example questions follow the profile: the first set whose keyword appears in role, organisation or about.
const EXAMPLES = [
  [/malaria|health|epidem|path/i, ['Validate: girls under 12 are more vulnerable to malaria because of sexism in malaria-endemic countries.',
    'Is bed net use associated with lower anaemia in children under 5?', 'Map the evidence from seasonal malaria chemoprevention to child mortality.']],
  [/job|labou?r|employ|world bank|econom/i, ['Is vocational training associated with higher youth employment in low-income countries?',
    'What does the graph hold on minimum wage and informal work?', 'Map the evidence from cash transfers to adult labour supply.']],
  [/obes|nutrition|nesta|diet|food/i, ['Which school interventions are associated with lower childhood obesity, and how many studies back each?',
    'Is screen time associated with obesity in children aged 5 to 11?', 'Map the evidence from a sugar tax to childhood BMI.']],
  [/./, ['Validate: girls under 12 are more vulnerable to malaria because of sexism in malaria-endemic countries.',
    'Is vocational training associated with higher youth employment?', 'Which interventions are associated with lower childhood obesity?']],
];
const examples = (p) => EXAMPLES.find(([re]) => re.test([p.role, p.organisation, p.about].join(' ')))[1];

export function Questions({ project, projects, runs, thread, threads, agents, session, profile, reload }) {
  const sorted = [...runs].sort((a, b) => a.id - b.id);
  const lastAnswer = sorted.filter((r) => r.answer).at(-1)?.answer;
  const followUps = (lastAnswer?.follow_ups || []).filter(Boolean).slice(0, 3);
  const start = async (query, plan = null, pinned = null) => {
    const { run_id: id } = await api(`/api/projects/${project.id}/runs`, { method: 'POST', body: { query, agents: pinned, plan, thread_id: thread } });
    await reload();
    setTimeout(() => document.getElementById(`run-${id}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 150);
  };
  return html`
    ${thread && html`<${ThreadTitle} key=${thread} thread=${threads?.find((t) => t.id === thread)} reload=${reload} project=${project} projects=${projects} />`}
    <div class="thread">
      ${sorted.length ? sorted.map((r, i) => html`<${Turn} key=${r.id} run=${r} agents=${agents} latest=${i === sorted.length - 1} onDone=${reload}
          onAgain=${(q) => start(q, null, session.prefs.agents || null).catch(() => {})} />`)
        : html`<p class="muted small empty-line">No questions in this thread yet. Ask one below or start from an example.</p>`}
    </div>
    <${SelectReply} />
    <${Composer} key=${`${project.id}.${thread ?? 'main'}`} project=${project} thread=${thread} agents=${agents} session=${session}
      suggestions=${sorted.length ? followUps : examples(profile)} isFollowUp=${sorted.length > 0 && followUps.length > 0} start=${start} />`;
}

function ThreadTitle({ thread, reload, project, projects }) {
  const [msg, setMsg] = useState('');
  if (!thread) return null;
  const save = async (e) => {
    const title = e.target.value.trim();
    if (!title || title === thread.title) return;
    try { await api(`/api/threads/${thread.id}`, { method: 'PUT', body: { title } }); setMsg(''); reload(); }
    catch (x) { setMsg(`Could not rename the thread: ${x.message}.`); }
  };
  const move = async (pid) => {
    if (!pid) return;
    try {
      const t = await api(`/api/threads/${thread.id}/project`, { method: 'PUT', body: { project_id: Number(pid) } });
      location.hash = new URLSearchParams({ ...Object.fromEntries(new URLSearchParams(location.hash.slice(1))), project: t.project_id, thread: t.id }).toString();
    } catch (x) { setMsg(x.status === 403 ? 'You can only move threads between your own projects.' : `Could not move the thread: ${x.message}.`); }
  };
  return html`<div class="thread-title"><label for="tt" class="eyebrow">Thread name</label>
    <input id="tt" defaultValue=${thread.title} onBlur=${save} onKeyDown=${(e) => e.key === 'Enter' && e.target.blur()} />
    ${projects.length > 1 && html`<select aria-label="Move this thread to another project" value="" onChange=${(e) => move(e.target.value)}>
      <option value="">Move thread to another project…</option>
      ${projects.filter((p) => p.id !== project.id).map((p) => html`<option key=${p.id} value=${p.id}>${p.title}</option>`)}</select>`}
    ${msg && html`<p class="msg bad">${msg}</p>`}</div>`;
}

// Select any text in an answer and a Reply button appears; it hands the quote to the composer as context.
function SelectReply() {
  const [sel, setSel] = useState(null);
  useEffect(() => {
    const check = () => setTimeout(() => {
      const s = getSelection(); const text = s && !s.isCollapsed ? s.toString().trim() : '';
      const inTurn = text.length > 3 && s.anchorNode?.parentElement?.closest('.turn');
      if (!inTurn) return setSel(null);
      const r = s.getRangeAt(0).getBoundingClientRect();
      setSel({ text: text.slice(0, 800), x: Math.min(r.left + r.width / 2, innerWidth - 60), y: Math.max(r.top - 44, 8) });
    }, 0);
    document.addEventListener('mouseup', check); document.addEventListener('keyup', check); document.addEventListener('touchend', check);
    return () => { document.removeEventListener('mouseup', check); document.removeEventListener('keyup', check); document.removeEventListener('touchend', check); };
  }, []);
  if (!sel) return null;
  return html`<button type="button" class="select-reply primary" style=${{ left: `${sel.x}px`, top: `${sel.y}px` }}
    onMouseDown=${(e) => e.preventDefault()}
    onClick=${() => { dispatchEvent(new CustomEvent('camox:quote', { detail: sel.text })); getSelection().removeAllRanges(); setSel(null); }}>Reply</button>`;
}

function Composer({ project, thread, agents, session, suggestions, isFollowUp, start }) {
  const [quote, setQuote] = useState(null);
  useEffect(() => {
    const take = (e) => { setQuote(e.detail); const t = document.getElementById('q'); t?.scrollIntoView({ block: 'nearest' }); t?.focus(); };
    addEventListener('camox:quote', take);
    return () => removeEventListener('camox:quote', take);
  }, []);
  const withQuote = (text) => (quote ? `About this part of the earlier analysis: "${quote}"\n\n${text}` : text);
  const key = `draft.${project.id}.${thread ?? 'main'}`;
  const [q, setQ] = useState(() => local.get(key, ''));
  const [pinned, setPinned] = useState(() => session.prefs.agents || null);  // null: the planner chooses
  const [chooser, setChooser] = useState(false);
  const [plan, setPlan] = useState(null);
  const [msg, setMsg] = useState(['', false]);
  const [busy, setBusy] = useState(false);
  const draft = (v) => { setQ(v); local.set(key, v || null); };
  const pin = (next) => { setPinned(next); savePrefs(session, { agents: next }); };
  const say = (t, bad = false) => setMsg([t, bad]);

  const run = async (p = null) => {
    if (!q.trim()) return say('Write a question first.', true);
    setBusy(true); say('Starting the run');
    try { await start(withQuote(q.trim()), p, pinned); draft(''); setQuote(null); setPlan(null); say(''); }
    catch (e) { say(e.status === 429 ? e.message : `Could not start the run: ${e.message}. Try again in a moment.`, true); }
    finally { setBusy(false); }
  };
  const review = async () => {
    if (!q.trim()) return say('Write a question first.', true);
    setBusy(true); say('The planner is choosing agents for this question');
    try { setPlan(await api(`/api/projects/${project.id}/plan`, { method: 'POST', body: { query: withQuote(q.trim()), agents: pinned, thread_id: thread } })); say(''); }
    catch (e) { say(`Could not get a plan: ${e.message}. Use Ask to let the planner choose during the run.`, true); }
    finally { setBusy(false); }
  };
  const chosen = pinned ? agents.filter((a) => pinned.includes(a.name)) : [];

  return html`<form class="composer" onSubmit=${(e) => { e.preventDefault(); run(); }}>
    <label for="q" class="eyebrow">${isFollowUp ? 'Ask a follow-up' : 'Ask a question'}</label>
    ${suggestions.length > 0 && html`<div class="suggest">${suggestions.map((s) => html`<button key=${s} type="button" class="suggestion"
      onClick=${() => draft(s)}>${s}</button>`)}</div>`}
    ${quote && html`<blockquote class="reply-quote"><span class="eyebrow">Replying to</span> ${quote}
      <button type="button" class="ghost-btn small" aria-label="Remove the quote" onClick=${() => setQuote(null)}>×</button></blockquote>`}
    <textarea id="q" rows="3" value=${q} onInput=${(e) => draft(e.target.value)} placeholder="Ask about this project"
      onKeyDown=${(e) => { if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) run(); }}></textarea>
    <div class="composer-row">
      <button type="button" class="agents-btn" aria-expanded=${chooser} onClick=${() => setChooser(!chooser)}>
        <span class="eyebrow">Agents</span><span>${pinned ? chosen.map((a) => a.title).join(', ') || 'None chosen' : 'Planner chooses'}</span><span aria-hidden="true">${chooser ? '▴' : '▾'}</span></button>
      <span class="spacer"></span>
      <button type="button" class="outline" disabled=${busy} onClick=${review}>Review plan</button>
      <button class="primary" disabled=${busy}>Ask</button>
    </div>
    ${chooser && html`<${AgentChooser} agents=${agents} pinned=${pinned} pin=${pin} />`}
    <p class="scope small muted">Answers from about 2M published findings in the System Graph. Shows associations, not causes, and says where the evidence runs out.</p>
    ${msg[0] && html`<p class=${`msg ${msg[1] ? 'bad' : ''}`} role="status">${msg[0]}</p>`}
    ${plan && html`<${PlanEditor} plan=${plan} agents=${agents} busy=${busy} cancel=${() => setPlan(null)} run=${run} say=${say} />`}
  </form>`;
}

export function AgentChooser({ agents, pinned, pin }) {
  const toggle = (name) => {
    const s = new Set(pinned || []);
    s.has(name) ? s.delete(name) : s.add(name);
    pin(s.size ? [...s] : null);
  };
  return html`<div class="chooser" role="group" aria-label="Choose agents">
    <button type="button" class="agent-card planner" role="checkbox" aria-checked=${!pinned} onClick=${() => pin(null)}>
      <span class="tick" aria-hidden="true"></span><strong>Let the planner choose</strong>
      <span class="small muted">Picks the agents that fit each question. Recommended.</span></button>
    ${agents.map((a) => html`<button key=${a.name} type="button" class="agent-card" role="checkbox" aria-checked=${!!pinned?.includes(a.name)}
      title=${a.description} onClick=${() => toggle(a.name)}>
      <span class="tick" aria-hidden="true"></span><strong>${a.title}</strong><span class="small muted">${firstLine(a.description)}</span></button>`)}
    <p class="small muted chooser-note">${pinned ? 'The planner may only use the agents you picked.' : 'Pick agents to limit the planner to them.'} Your choice is kept for next time.</p>
  </div>`;
}

function PlanEditor({ plan, agents, busy, cancel, run, say }) {
  const [question, setQuestion] = useState(plan.question);
  const [tasks, setTasks] = useState(plan.tasks.map((t, i) => ({ ...t, k: i })));
  const set = (k, patch) => setTasks(tasks.map((t) => (t.k === k ? { ...t, ...patch } : t)));
  const go = () => {
    const ts = tasks.map(({ agent, instruction }) => ({ agent, instruction: instruction.trim() })).filter((t) => t.instruction);
    if (!ts.length) return say('Add at least one task with an instruction, or use Ask to let the planner choose.', true);
    run({ question: question.trim() || plan.question, tasks: ts });
  };
  return html`<div class="plan">
    <p class="eyebrow">Plan · ${tasks.length} ${tasks.length === 1 ? 'task' : 'tasks'}</p>
    <div class="field"><label for="plan-q">Question</label><input id="plan-q" value=${question} onInput=${(e) => setQuestion(e.target.value)} /></div>
    <ol class="tasks">${tasks.map((t) => html`<li key=${t.k} class="task">
      <div class="task-body">
        <select aria-label="Agent" value=${t.agent} onChange=${(e) => set(t.k, { agent: e.target.value })}>
          ${agents.map((a) => html`<option key=${a.name} value=${a.name}>${a.title}</option>`)}</select>
        <textarea rows="3" aria-label="Instruction" value=${t.instruction} onInput=${(e) => set(t.k, { instruction: e.target.value })}></textarea>
      </div>
      <button type="button" class="ghost-btn small" onClick=${() => setTasks(tasks.filter((x) => x.k !== t.k))}>Remove</button></li>`)}</ol>
    <div class="row-end">
      <button type="button" class="ghost-btn" onClick=${() => setTasks([...tasks, { agent: agents[0]?.name, instruction: '', k: Date.now() }])}>Add task</button>
      <span class="spacer"></span>
      <button type="button" class="ghost-btn" onClick=${cancel}>Cancel</button>
      <button type="button" class="primary" disabled=${busy} onClick=${go}>Run this plan</button></div>
  </div>`;
}
