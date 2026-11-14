// Project knowledge graph: the project's topics, and entities (concepts, indicators, places, population groups, papers)
// with the facts linking them, their qualifiers, studies and source. Thin entities (<=2 studies) carry external evidence. Standalone: mountKG(el, projectId) works in any page.
const CY = 'https://cdn.jsdelivr.net/npm/cytoscape@3.30.2/dist/cytoscape.min.js';
const KINDS = { topic: ['Topics', 'hexagon', '--cat-6'], concept: ['Concepts', 'ellipse', '--cat-1'], indicator: ['Indicators', 'round-rectangle', '--cat-3'],
  place: ['Places', 'diamond', '--cat-2'], population: ['Populations', 'triangle', '--cat-4'], paper: ['Papers', 'rectangle', '--cat-5'] };
const STEP = 30;
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const css = (n, el) => getComputedStyle(el).getPropertyValue(n).trim();
const score = (n) => 2 * (n.data.n_papers || 0) + (n.data.facts || 0);
const rankOf = (n) => (n.kind === 'topic' ? 1e6 * (n.data.top ? 2 : 1) : 0) + score(n);   // topics first
const num = (v) => (typeof v === 'number' ? (Math.abs(v) >= 100 ? v.toFixed(0) : +v.toPrecision(3)) : v);

const STYLE = `.kg{--kg-line:var(--line,#e2e5ea);display:grid;gap:var(--s2,8px)}
.kg-bar{display:flex;flex-wrap:wrap;gap:var(--s2,8px);align-items:center}
.kg-bar input{flex:1 1 200px;width:auto}
.kg-body{display:grid;grid-template-columns:minmax(0,1fr) 340px;gap:var(--s3,16px)}
.kg-graph{height:520px;border:1px solid var(--kg-line);border-radius:6px;background:var(--surface,#fff)}
.kg-side{border:1px solid var(--kg-line);border-radius:6px;padding:var(--s3,16px);max-height:520px;overflow:auto;font-size:var(--fs-s,13px)}
.kg-side h3{margin:0 0 4px}.kg-side ul{padding-left:18px;margin:4px 0 var(--s3,16px)}.kg-side li{margin-bottom:6px}
.kg-q{color:var(--muted,#5a606c)}.kg-side button.link{border:0;padding:0;min-height:0;background:none;color:var(--accent,#2456c4);text-align:left}
.kg-src{display:inline-block;border:1px solid var(--line-strong,#c6cbd3);border-radius:4px;padding:0 4px;font-size:11px;color:var(--muted,#5a606c)}
.kg-src.ext{border-style:dashed;color:var(--v-mixed,#a35a00)}
.kg-legend{display:flex;flex-wrap:wrap;gap:var(--s3,16px);font-size:var(--fs-s,13px);color:var(--muted,#5a606c)}
@media (max-width:760px){.kg-body{grid-template-columns:1fr}.kg-graph{height:380px}}`;

function loadCytoscape() {
  if (window.cytoscape) return Promise.resolve();
  return new Promise((ok, fail) => { const s = Object.assign(document.createElement('script'), { src: CY, onload: ok, onerror: fail }); document.head.append(s); });
}

export async function mountKG(el, projectId, { base = '' } = {}) {
  if (!document.getElementById('kg-style')) document.head.append(Object.assign(document.createElement('style'), { id: 'kg-style', textContent: STYLE }));
  const url = `${base}/api/projects/${projectId}/kg`;
  el.innerHTML = '<p class="small muted">Reading the project graph…</p>';
  let g;
  try { [g] = await Promise.all([fetch(url).then((r) => r.json()), loadCytoscape()]); } catch (err) {
    el.innerHTML = `<p class="small">Could not load the project graph (${esc(err.message)}). Reload the page to try again.</p>`; return;
  }
  const rebuild = async (btn) => {
    btn.disabled = true; btn.textContent = 'Building from the answers…';
    const r = await fetch(`${url}/rebuild`, { method: 'POST' });
    if (!r.ok) { btn.disabled = false; btn.textContent = 'Build failed: try again'; return; }
    mountKG(el, projectId, { base });
  };
  if (!g.nodes.length) {
    el.innerHTML = `<div class="kg"><p class="small muted">No graph yet. It is built from the answers in this project after each run.</p>
      <div><button type="button" data-build>Build graph now</button></div></div>`;
    el.querySelector('[data-build]').onclick = (e) => rebuild(e.target);
    return;
  }
  const byId = new Map(g.nodes.map((n) => [n.id, n]));
  const ranked = [...g.nodes].sort((a, b) => rankOf(b) - rankOf(a));
  const st = { kinds: new Set(Object.keys(KINDS)), q: '', limit: STEP, thin: false };
  const ext = (src) => !/System Public Graph|Project goals/.test(src || '');
  const badge = (src, url) => `<span class="kg-src${ext(src) ? ' ext' : ''}">${url ? `<a href="${esc(url)}" target="_blank" rel="noopener">${esc(src)}</a>` : esc(src)}</span>`;
  const sources = {}; g.nodes.forEach((n) => { sources[n.data.source] = (sources[n.data.source] || 0) + 1; });
  const nThin = g.nodes.filter((n) => n.data.thin).length;
  const counts = g.stats.nodes;
  el.innerHTML = `<div class="kg">
    <div class="kg-bar"><input type="search" placeholder="Search entities, e.g. a place or concept" aria-label="Search the project graph">
      ${Object.entries(KINDS).filter(([k]) => counts[k]).map(([k, [name]]) => `<button type="button" class="chip" data-kind="${k}" aria-pressed="true">${name} <span class="num">${counts[k]}</span></button>`).join('')}
      ${nThin ? `<button type="button" class="chip" data-thin aria-pressed="false" title="Entities with 2 or fewer studies in the System Public Graph, with external evidence">Thin coverage <span class="num">${nThin}</span></button>` : ''}
    </div>
    <div class="kg-body"><div class="kg-graph" role="img" aria-label="Project knowledge graph"></div>
      <aside class="kg-side" aria-live="polite"><p class="muted">Tap an entity to see its facts, their qualifiers and the studies behind them.</p></aside></div>
    <div class="kg-bar"><span class="small muted num" data-shown></span><button type="button" class="ghost small" data-more>Show more</button>
      <button type="button" class="ghost small" data-fit>Fit</button><button type="button" class="ghost small" data-rebuild>Rebuild from answers</button></div>
    <div class="kg-legend"><span>Shape and colour: kind</span><span>Line width: studies behind the link</span><span>Solid: linked to; dashed: measures; dotted: studied in or reported in; orange dashed: external evidence</span>
      <span>Dashed outline: from an external source, not the System Public Graph</span></div>
    <div class="kg-legend"><span>Sources:</span>${Object.entries(sources).map(([src, k]) => `<span>${badge(src)} <span class="num">${k}</span></span>`).join('')}</div></div>`;
  const side = el.querySelector('.kg-side');
  const color = (k) => css(KINDS[k][2], el) || '#8b909a';
  const cy = window.cytoscape({
    container: el.querySelector('.kg-graph'), minZoom: 0.2, maxZoom: 3,
    style: [
      { selector: 'node', style: { shape: 'data(shape)', 'background-color': 'data(color)', width: 'data(size)', height: 'data(size)', label: 'data(short)',
        color: css('--text', el) || '#181b21', 'font-size': 11, 'font-family': css('--font', el) || 'sans-serif', 'text-valign': 'bottom', 'text-margin-y': 3,
        'text-wrap': 'wrap', 'text-max-width': 110, 'text-background-color': css('--surface', el) || '#fff', 'text-background-opacity': 0.85, 'text-background-padding': 1 } },
      { selector: 'edge', style: { width: 'data(w)', 'line-color': css('--edge', el) || '#b8bdc6', 'curve-style': 'bezier', opacity: 0.8, 'line-style': 'data(ls)' } },
      { selector: 'node:selected', style: { 'border-width': 3, 'border-color': css('--accent', el) || '#2456c4' } },
      { selector: '.ext', style: { 'border-width': 2, 'border-style': 'dashed', 'border-color': css('--v-mixed', el) || '#a35a00' } },
      { selector: 'edge.extE', style: { 'line-color': css('--v-mixed', el) || '#a35a00' } },
    ],
  });

  function visible() {
    const q = st.q.toLowerCase();
    let pool = ranked.filter((n) => st.kinds.has(n.kind));
    if (st.thin) {   // thin entities and their external evidence
      const keep = new Set(pool.filter((n) => n.data.thin).map((n) => n.id));
      g.edges.filter((e) => e.kind === 'external evidence' && keep.has(e.source)).forEach((e) => keep.add(e.target));
      pool = pool.filter((n) => keep.has(n.id));
    }
    if (q) {
      const hit = new Set(pool.filter((n) => n.label.toLowerCase().includes(q)).map((n) => n.id));
      g.edges.filter((e) => hit.has(e.source) || hit.has(e.target)).forEach((e) => { hit.add(e.source); hit.add(e.target); });
      pool = pool.filter((n) => hit.has(n.id));
    }
    return pool;
  }
  function draw() {
    const pool = visible(); let nodes = pool.slice(0, st.limit); const ids = new Set(nodes.map((n) => n.id));
    const edges = g.edges.filter((e) => ids.has(e.source) && ids.has(e.target));
    const linked = new Set(edges.flatMap((e) => [e.source, e.target]));
    if (edges.length) nodes = nodes.filter((n) => linked.has(n.id));   // unlinked entities stay out of the picture
    const maxS = Math.max(1, ...nodes.filter((n) => n.kind !== 'topic').map(score)); const maxE = Math.max(1, ...edges.map((e) => e.data.n_studies || 1));
    const top = new Set(nodes.slice(0, 18).map((n) => n.id));
    cy.elements().remove();
    cy.add([...nodes.map((n) => ({ classes: n.data.external ? 'ext' : '', data: { id: n.id, kind: n.kind, shape: KINDS[n.kind][1], color: color(n.kind),
        size: n.kind === 'topic' ? (n.data.top ? 40 : 28) : 14 + 26 * Math.sqrt(Math.min(score(n), maxS) / maxS),
        short: top.has(n.id) || st.q ? (n.label.length > 34 ? `${n.label.slice(0, 33)}…` : n.label) : '' } })),
      ...edges.map((e, i) => ({ classes: e.kind === 'external evidence' ? 'extE' : '', data: { id: `e${i}`, source: e.source, target: e.target, w: 1 + 6 * Math.sqrt((e.data.n_studies || 1) / maxE),
        ls: ['linked to', 'includes', 'about'].includes(e.kind) ? 'solid' : ['studied in', 'reported in'].includes(e.kind) ? 'dotted' : 'dashed' } }))]);
    cy.layout({ name: 'cose', animate: false, randomize: true, nodeRepulsion: () => 40000, idealEdgeLength: () => 90, nodeOverlap: 30, gravity: 0.25, padding: 20 }).run();
    cy.fit(undefined, 20);
    el.querySelector('[data-shown]').textContent = `${nodes.length} of ${pool.length} entities, ${edges.length} facts shown`;
    el.querySelector('[data-more]').hidden = nodes.length >= pool.length;
  }

  const paper = (d) => { const p = byId.get(`doi:${d}`); return `<li><a href="https://doi.org/${esc(d)}" target="_blank" rel="noopener">${esc(p?.data.title || d)}</a>${p?.data.year ? ` <span class="muted">${p.data.year}</span>` : ''}</li>`; };
  const qual = (f) => [f.effect && `${f.effect.replaceAll('_', ' ')} ${num(f.value) ?? ''}${f.ci ? ` [${num(f.ci[0])}, ${num(f.ci[1])}]` : ''}`,
    f.verdict && `verdict: ${f.verdict}`, f.support && `support: ${f.support}`, f.match && `match: ${f.match}`, f.n_studies != null && `${f.n_studies} studies`,
    f.population && `population: ${f.population}`, f.claim && `claim: ${f.claim}`, f.policy && `policy: ${f.policy}`, f.search_term && `concept search: ${f.search_term}`, f.search && `search: ${f.search}`,
    f.note, f.basis, f.run_id && `run ${f.run_id}`].filter(Boolean).map(esc).join(' · ');
  function show(id) {
    const n = byId.get(id); const d = n.data;
    const facts = g.edges.filter((e) => e.source === id || e.target === id).sort((a, b) => (b.data.n_studies || 0) - (a.data.n_studies || 0));
    const head = n.kind === 'indicator' ? `<a href="https://data360.worldbank.org/en/indicator/${encodeURIComponent(d.indicator_id)}" target="_blank" rel="noopener">${esc(n.label)}</a> <code>${esc(d.indicator_id)}</code>`
      : d.wikidata_id ? `<a href="https://www.wikidata.org/wiki/${esc(d.wikidata_id)}" target="_blank" rel="noopener">${esc(n.label)}</a>`
      : n.kind === 'paper' && d.url ? `<a href="${esc(d.url)}" target="_blank" rel="noopener">${esc(n.label)}</a>` : esc(n.label);
    side.innerHTML = `<h3>${head}</h3><p class="muted num">${KINDS[n.kind][0].slice(0, -1)}${d.n_studies != null ? ` · ${d.n_studies.toLocaleString()} studies in the System Public Graph${n.kind === 'topic' ? ' (best linked concept)' : ''}` : ''} · ${d.facts} facts · ${d.n_papers} papers in this project</p>
      <p>Source: ${badge(d.source, d.url)}${d.year ? ` <span class="muted num">${d.year}</span>` : ''}</p>
      ${d.thin ? '<p class="small"><strong>Thin coverage:</strong> 2 or fewer studies in the System Public Graph. External evidence is listed below; it is not checked against the graph.</p>' : ''}
      <h4>Facts</h4><ul>${facts.slice(0, 30).map((e) => { const out = e.source === id; const o = byId.get(out ? e.target : e.source);
        return `<li>${out ? '' : `<button type="button" class="link" data-go="${esc(o.id)}">${esc(o.label)}</button> `}<strong>${esc(e.kind)}</strong>${out ? ` <button type="button" class="link" data-go="${esc(o.id)}">${esc(o.label)}</button>` : ' this'}
          ${o.data.url ? `<a href="${esc(o.data.url)}" target="_blank" rel="noopener" aria-label="Open ${esc(o.label)}">↗</a>` : ''} ${badge(e.data.source)}
          ${e.data.n_papers ? `<span class="num muted">(${e.data.n_papers} papers)</span>` : ''}${e.data.facts.slice(0, 3).map((f) => `<div class="kg-q">${qual(f)}</div>`).join('')}</li>`; }).join('')}</ul>
      ${d.dois.length ? `<h4>Studies (${d.dois.length})</h4><ul>${d.dois.slice(0, 25).map(paper).join('')}</ul>` : ''}`;
    side.querySelectorAll('[data-go]').forEach((b) => { b.onclick = () => { const t = b.dataset.go; if (!cy.getElementById(t).length) { st.q = byId.get(t).label; el.querySelector('input').value = st.q; draw(); } cy.$(':selected').unselect(); cy.getElementById(t).select(); show(t); }; });
  }

  cy.on('tap', 'node', (e) => show(e.target.id()));
  el.querySelector('input').oninput = (e) => { st.q = e.target.value.trim(); st.limit = STEP; draw(); };
  el.querySelectorAll('[data-kind]').forEach((b) => { b.onclick = () => {
    const on = b.getAttribute('aria-pressed') !== 'true'; b.setAttribute('aria-pressed', on); st.kinds[on ? 'add' : 'delete'](b.dataset.kind); draw(); }; });
  el.querySelector('[data-thin]')?.addEventListener('click', (e) => {
    st.thin = !st.thin; e.currentTarget.setAttribute('aria-pressed', st.thin); st.limit = STEP; draw(); });
  el.querySelector('[data-more]').onclick = () => { st.limit += STEP; draw(); };
  el.querySelector('[data-fit]').onclick = () => cy.fit(undefined, 20);
  el.querySelector('[data-rebuild]').onclick = (e) => rebuild(e.target);
  draw();
}
