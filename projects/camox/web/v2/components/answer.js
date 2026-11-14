// One answer: the shared section renderers from ../sections.js, charts, references with titles, and the concept graph.
import { html, useEffect, useMemo, useRef, api } from '../api.js';
import { esc, plural, short, renderAnswer, refBody, mountCharts, answerConcepts, downloadCsv } from '../../sections.js';
import { drawGraph } from '../../graph.js';

export function Answer({ answer, runId, drawNow }) {
  const ref = useRef(null);
  const markup = useMemo(() => renderAnswer(answer, runId), [runId, !!answer]);
  useEffect(() => {
    const box = ref.current;
    mountCharts(box);
    fillReferences(box);
    mountGraph(box.querySelector('.graph-panel'), answer, drawNow);
  }, [markup]);
  return html`<div class="answer" ref=${ref} dangerouslySetInnerHTML=${{ __html: markup }} />`;
}

function mountGraph(panel, answer, drawNow) {
  const { ids, verdicts } = answerConcepts(answer);
  if (!panel) return;
  if (!ids.length) { panel.innerHTML = '<p class="small muted">No graph concepts in this answer, so there is no graph to draw.</p>'; return; }
  const draw = async () => {
    panel.innerHTML = `<p class="small muted">Loading ${plural(ids.length, 'concept', 'concepts')} from the graph</p>`;
    try {
      const data = await api(`/api/graph?ids=${encodeURIComponent(ids.join(','))}`);
      if (!data.nodes?.length) { panel.innerHTML = '<p class="small muted">The graph has none of these concepts.</p>'; return; }
      if (!window.cytoscape) throw new Error('the graph library did not load');
      drawGraph(panel, data, verdicts);
    } catch (e) {
      panel.innerHTML = `<p class="small">Could not draw the graph: ${esc(short(e.message))}. The answer is unaffected. <button type="button" class="outline small">Try again</button></p>`;
      panel.querySelector('button').onclick = draw;
    }
  };
  if (drawNow) return draw();
  panel.innerHTML = `<button type="button" class="outline graph-open">Show graph of ${plural(ids.length, 'concept', 'concepts')}</button>`;
  panel.firstChild.onclick = draw;
}

// Titles, venues and years for the References list; unknown DOIs stay plain DOI links.
async function fillReferences(box) {
  const items = [...box.querySelectorAll('.refs-list li[data-doi]')];
  for (let i = 0; i < items.length; i += 50) {
    const chunk = items.slice(i, i + 50);
    try {
      const found = await api(`/api/references?dois=${encodeURIComponent(chunk.map((li) => li.dataset.doi).join(','))}`);
      const by = new Map(found.map((r) => [String(r.doi).toLowerCase(), r]));
      for (const li of chunk) {
        const r = by.get(li.dataset.doi.toLowerCase());
        if (r?.title) li.querySelector('div').innerHTML = refBody({ ...r, doi: li.dataset.doi });
      }
    } catch { /* the DOI links still work without titles */ }
  }
}

// Clicks inside rendered answers: citations scroll to their reference, indicator filters, CSV download, verdict pills.
export function installAnswerClicks() {
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
}
