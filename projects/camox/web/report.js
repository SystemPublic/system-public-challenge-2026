// Project report: Generate / revise a cited report; each version opens as a printable page (report.html).
import { esc, plural } from './sections.js';

// The report version's verifier result in a few words; versions from before the verifier count as not verified.
export const verifiedLabel = (v) => (v?.status === 'verified' ? `Verified: ${plural(v.claims_checked ?? 0, 'claim', 'claims')} checked`
  : v?.status === 'issues_found' ? `${plural(v.issues.filter((i) => i.severity === 'major').length, 'issue', 'issues')} found` : 'Not verified');

const time = (t) => new Date(t).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

// The Generate bar, the version list and a revise box under the latest version. Polls every 4 s while building.
export function bindReport(box, pj, api) {
  box.innerHTML = `<div class="dash-bar"><span class="small muted" role="status"></span><button type="button">Generate report</button></div>
    <label for="report-purpose" class="small">What is this report for? (optional)</label>
    <textarea id="report-purpose" rows="2" placeholder="For example: funding case for internet expansion in Kenya, 2 pages, for a World Bank task team"></textarea>
    <ul class="report-versions small"></ul>
    <form class="report-revise" hidden><label for="report-instruction" class="small">Revise the latest version</label>
      <textarea id="report-instruction" rows="2" placeholder="For example: make section 2 shorter and add the regional data"></textarea>
      <button type="submit" class="ghost">Revise report</button></form>`;
  const [msg, btn, list, form] = ['span', 'button', 'ul', 'form'].map((s) => box.querySelector(s));
  const show = () => {
    const s = pj.report_status || ''; const building = s.startsWith('building'); const reports = pj.reports || [];
    msg.textContent = building ? `Building report: ${s.replace(/^building:? ?/, '')}`
      : s === 'failed' ? 'The last report build failed. Generate it again.'
      : reports.length ? 'Each version opens as a page you can print or save as PDF.'
      : pj.runs.some((r) => r.answer) ? 'A cited report built from the answers and dashboard in this project.' : 'Ask a question first; the report is built from the answers.';
    btn.hidden = !pj.runs.some((r) => r.answer); btn.disabled = building;
    list.innerHTML = reports.map((r) => `<li><a href="report.html?project=${pj.id}&v=${r.version}" target="_blank" rel="noopener">v${r.version} · ${time(r.created_at)}</a>
      <a href="report.html?project=${pj.id}&v=${r.version}&print=1" target="_blank" rel="noopener">Download PDF</a>
      <span class="muted">${esc(verifiedLabel(r.verification))}</span>
      ${r.auto ? '<span class="muted">Automatic first report</span>' : r.instruction ? `<span class="muted">${esc(r.instruction)}</span>` : ''}</li>`).join('');
    form.hidden = !reports.length; form.querySelector('button').disabled = building;
    if (building) setTimeout(poll, 4000);
  };
  const poll = async () => {
    if (!box.isConnected) return;
    try { ({ reports: pj.reports, report_status: pj.report_status } = await api(`/api/projects/${pj.id}`)); } catch { /* next tick */ }
    show();
  };
  const start = async (instruction) => {
    try { pj.report_status = (await api(`/api/projects/${pj.id}/report`, { method: 'POST', body: { instruction } })).report_status; }
    catch (e) { msg.textContent = `Could not start the report: ${e.message}`; return; }
    show();
  };
  btn.onclick = () => start(box.querySelector('#report-purpose').value.trim() || null);
  form.onsubmit = (e) => { e.preventDefault(); const t = form.querySelector('textarea').value.trim(); if (t) start(t); };
  show();
}
