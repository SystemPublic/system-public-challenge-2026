// Project dashboard: KPI tiles, charts and tables built by the dashboard agents from the project's answers.
import { esc, linked, wbUrl, table, chart, mountCharts } from './sections.js';

document.head.insertAdjacentHTML('beforeend', '<link rel="stylesheet" href="dashboard.css">');

// Sources become links: DOIs to the paper, World Bank ids to their Data360 page, anything else stays text.
const link = (href, text) => `<a href="${esc(href)}" target="_blank" rel="noopener">${esc(text)}</a>`;
const sourceLink = (s) => {
  const doi = String(s).match(/10\.\d{4,9}\/\S+/);
  if (doi) return link(`https://doi.org/${doi[0]}`, `paper ${doi[0]}`);
  if (/^WB_[A-Z0-9]+_\S+$/.test(s)) return link(wbUrl(s), s);
  return linked(s);
};

const kpis = (p) => `<div class="kpis">${p.kpis.map((k) => `<div class="kpi">
  <div class="kpi-label">${esc(k.label)}</div>
  <div class="kpi-value num">${esc(k.value)} <span class="kpi-unit">${esc(k.unit)}</span></div>
  <div class="kpi-source">${linked(k.source)}</div></div>`).join('')}</div>`;

const panel = (p) => `<section class="panel panel-${esc(p.kind)}">
  <h3>${esc(p.title)}</h3>
  ${p.caption ? `<p class="small">${linked(p.caption)}</p>` : ''}
  ${p.kind === 'kpis' ? kpis(p) : ''}
  ${p.vega_lite_json ? chart({ title: '', vega_lite_json: p.vega_lite_json }) : ''}
  ${p.table ? table(p.table) : ''}
  ${p.sources.length ? `<p class="panel-sources">Sources: ${p.sources.map(sourceLink).join('; ')}</p>` : ''}
</section>`;

export function renderDashboard(el, d) {
  el.innerHTML = `<div class="dash-head"><h3>${esc(d.title)}</h3><p class="small muted">${linked(d.summary)}</p></div>
    <div class="panels">${d.panels.map(panel).join('')}</div>`;
  mountCharts(el);
}

// The Build / Rebuild bar above the thread. While a build runs, poll the project every 4 s for its status.
export function bindDashboard(box, pj, api) {
  box.innerHTML = '<div class="dash-bar"><span class="small muted" role="status"></span><button type="button"></button></div><div class="dash-body"></div>';
  const [msg, btn, body] = ['span', 'button', '.dash-body'].map((s) => box.querySelector(s));
  let shown = null;
  const show = () => {
    const s = pj.dashboard_status || ''; const building = s.startsWith('building');
    const step = s.replace(/^building:? ?/, '').replace('dashboard_planner', 'planning panels').replace('panel: ', '');
    msg.textContent = building ? `Building dashboard: ${step || 'planning panels'}`
      : s === 'failed' ? 'The last dashboard build failed. Build it again; it reads the answers in this thread.'
      : pj.dashboard ? '' : pj.runs.some((r) => r.answer) ? 'No dashboard yet. Build it from the answers in this project.'
      : 'Builds itself when the first pass finishes. Nothing to show yet.';
    btn.textContent = pj.dashboard ? 'Rebuild dashboard' : 'Build dashboard';
    btn.disabled = building; btn.hidden = !pj.runs.some((r) => r.answer);
    if (pj.dashboard && pj.dashboard !== shown) { shown = pj.dashboard; renderDashboard(body, shown); }
    if (building) setTimeout(poll, 4000);
  };
  const poll = async () => {
    if (!box.isConnected) return;
    try { ({ dashboard: pj.dashboard, dashboard_status: pj.dashboard_status } = await api(`/api/projects/${pj.id}`)); } catch { /* next tick */ }
    show();
  };
  btn.onclick = async () => {
    try { pj.dashboard_status = (await api(`/api/projects/${pj.id}/dashboard`, { method: 'POST' })).dashboard_status; }
    catch (e) { msg.textContent = `Could not start the dashboard: ${e.message}`; return; }
    show();
  };
  show();
  return poll;
}
