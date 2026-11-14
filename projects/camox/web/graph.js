// Cytoscape view of the concepts an answer rests on. Size (log) and width scale with n_studies; colour is the verdict.
// Circle layout keeps labels apart on a phone; zoom stays between 0.7 and 1 so labels stay readable (pan for the rest).
import { esc, slug, verdictPill } from './sections.js';

const css = (n) => getComputedStyle(document.documentElement).getPropertyValue(n).trim();

export function drawGraph(panel, data, verdicts) {
  const ids = new Set(data.nodes.map((n) => n.id));
  const edges = data.edges.filter((e) => ids.has(e.source) && ids.has(e.target));
  const maxN = Math.max(1, ...data.nodes.map((n) => n.n_studies));
  const maxE = Math.max(1, ...edges.map((e) => e.n_studies));
  const shown = [...new Set(data.nodes.map((n) => verdicts[n.id]).filter(Boolean))];

  panel.innerHTML = `<div class="graph-head"><h3>Concepts behind this answer</h3>
      <span class="small muted num">${data.nodes.length} concepts, ${edges.length} links</span>
      <button type="button" class="ghost small" data-fit>Fit</button></div>
    <div class="graph" role="img" aria-label="${esc(`Graph of ${data.nodes.map((n) => n.label).join(', ')}`)}"></div>
    <div class="legend">${shown.map((v) => verdictPill(v)).join('')}<span>Grey: no card covers it</span><span>Size and line width: number of studies</span></div>`;

  const cy = window.cytoscape({
    container: panel.querySelector('.graph'),
    elements: [
      ...data.nodes.map((n) => ({ data: {
        id: n.id, label: `${n.label} (${n.n_studies.toLocaleString()})`,
        size: 12 + 30 * (Math.log1p(n.n_studies) / Math.log1p(maxN)), rank: n.n_studies,
        color: verdicts[n.id] ? css(`--v-${slug(verdicts[n.id])}`) : css('--node'),
      } })),
      ...edges.map((e) => ({ data: { id: `${e.source}|${e.target}`, source: e.source, target: e.target, w: 1 + 7 * Math.sqrt(e.n_studies / maxE) } })),
    ],
    style: [
      { selector: 'node', style: {
        'background-color': 'data(color)', width: 'data(size)', height: 'data(size)', label: 'data(label)',
        color: css('--text'), 'font-size': 11, 'font-family': css('--font'), 'text-valign': 'bottom', 'text-margin-y': 4,
        'text-wrap': 'wrap', 'text-max-width': 96, 'text-background-color': css('--surface'), 'text-background-opacity': 0.85, 'text-background-padding': 2 } },
      { selector: 'edge', style: { width: 'data(w)', 'line-color': css('--edge'), 'curve-style': 'bezier' } },
    ],
    layout: { name: 'circle', sort: (a, b) => b.data('rank') - a.data('rank'), padding: 24, animate: false },
    minZoom: 0.3, maxZoom: 3,
  });
  const fit = () => { cy.fit(undefined, 24); const z = Math.min(1, Math.max(0.7, cy.zoom())); if (z !== cy.zoom()) { cy.zoom(z); cy.center(); } };
  fit();
  panel.querySelector('[data-fit]').onclick = fit;
  return cy;
}
