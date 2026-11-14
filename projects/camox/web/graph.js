// Cytoscape view of the concepts an answer rests on. Size (log) and width scale with n_studies; colour is the verdict.
// Only the strongest links are drawn (top 3 per concept, at most 40) so 20+ concepts stay readable; pan and zoom for the rest.
import { esc, slug, verdictPill } from './sections.js';

const css = (n) => getComputedStyle(document.documentElement).getPropertyValue(n).trim();

export function drawGraph(panel, data, verdicts) {
  const ids = new Set(data.nodes.map((n) => n.id));
  const all = data.edges.filter((e) => ids.has(e.source) && ids.has(e.target)).sort((a, b) => b.n_studies - a.n_studies);
  const deg = new Map(); const edges = [];
  for (const e of all) {
    if (edges.length >= 40) break;
    if ((deg.get(e.source) || 0) >= 3 && (deg.get(e.target) || 0) >= 3) continue;
    edges.push(e); [e.source, e.target].forEach((n) => deg.set(n, (deg.get(n) || 0) + 1));
  }
  const maxN = Math.max(1, ...data.nodes.map((n) => n.n_studies));
  const maxE = Math.max(1, ...edges.map((e) => e.n_studies));
  const top = new Set([...data.nodes].sort((a, b) => b.n_studies - a.n_studies).slice(0, 12).map((n) => n.id));
  const shown = [...new Set(data.nodes.map((n) => verdicts[n.id]).filter(Boolean))];

  panel.innerHTML = `<div class="graph-head"><h3>Concepts behind this answer</h3>
      <span class="small muted num">${data.nodes.length} concepts, strongest ${edges.length} of ${all.length} links</span>
      <button type="button" class="ghost small" data-fit>Fit</button></div>
    <div class="graph" role="img" aria-label="${esc(`Graph of ${data.nodes.map((n) => n.label).join(', ')}`)}"></div>
    <p class="small graph-pick" role="status">Labels show the 12 concepts with most studies; tap any concept for its name and study count. Drag to pan, pinch or scroll to zoom.</p>
    <div class="legend">${shown.length ? `${shown.map((v) => verdictPill(v)).join('')}<span>Grey: no card covers it</span>` : ''}<span>Circle size: studies on the concept</span><span>Line width: studies linking the pair</span></div>`;

  const cy = window.cytoscape({
    container: panel.querySelector('.graph'),
    elements: [
      ...data.nodes.map((n) => ({ data: {
        id: n.id, label: top.has(n.id) || verdicts[n.id] ? (n.label.length > 26 ? `${n.label.slice(0, 25)}…` : n.label) : '', full: n.label, n: n.n_studies,
        size: 12 + 30 * (Math.log1p(n.n_studies) / Math.log1p(maxN)), rank: n.n_studies,
        color: verdicts[n.id] ? css(`--v-${slug(verdicts[n.id])}`) : css('--node'),
      } })),
      ...edges.map((e) => ({ data: { id: `${e.source}|${e.target}`, source: e.source, target: e.target, w: 1 + 7 * Math.sqrt(e.n_studies / maxE) } })),
    ],
    style: [
      { selector: 'node', style: {
        'background-color': 'data(color)', width: 'data(size)', height: 'data(size)', label: 'data(label)',
        color: css('--text'), 'font-size': 13, 'font-family': css('--font'), 'text-valign': 'bottom', 'text-margin-y': 4,
        'text-wrap': 'wrap', 'text-max-width': 96, 'text-background-color': css('--surface'), 'text-background-opacity': 0.85, 'text-background-padding': 2 } },
      { selector: 'edge', style: { width: 'data(w)', 'line-color': css('--edge'), 'curve-style': 'bezier', opacity: 0.8 } },
      { selector: 'node:selected', style: { 'border-width': 2, 'border-color': css('--accent') } },
    ],
    layout: data.nodes.length > 10
      ? { name: 'cose', animate: false, randomize: false, nodeRepulsion: () => 30000, idealEdgeLength: () => 80, nodeOverlap: 40, gravity: 0.15, componentSpacing: 60, padding: 24 }
      : { name: 'circle', sort: (a, b) => b.data('rank') - a.data('rank'), padding: 24, animate: false },
    minZoom: 0.3, maxZoom: 3,
  });
  const fit = () => { cy.fit(undefined, 24); const z = Math.min(1.2, Math.max(0.5, cy.zoom())); if (z !== cy.zoom()) { cy.zoom(z); cy.center(); } };
  fit();
  panel.querySelector('[data-fit]').onclick = fit;
  cy.on('tap', 'node', (e) => { panel.querySelector('.graph-pick').textContent = `${e.target.data('full')}: ${e.target.data('n').toLocaleString()} studies, ${e.target.degree()} links shown`; });
  return cy;
}
