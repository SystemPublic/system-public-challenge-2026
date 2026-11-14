// One renderer per section type. Each returns an HTML string; unknown types fall back to readable JSON.
export const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
export const slug = (s) => String(s).toLowerCase().replace(/[^a-z0-9]+/g, '-');
export const plural = (n, one, many) => `${n.toLocaleString()} ${n === 1 ? one : many}`;
const cap = (s) => s.charAt(0).toUpperCase() + s.slice(1);
const fmt = (v) => (v == null ? '' : Number(v).toLocaleString(undefined, { maximumFractionDigits: 2 }));
const isNum = (s) => /^[-+−]?[\d,.]+%?$/.test(String(s).trim());
const doiLink = (d) => (d ? `<a href="${esc('https://doi.org/' + encodeURI(d))}" target="_blank" rel="noopener">${esc(d)}</a>` : '');
const safeUrl = (u) => (/^https?:\/\//.test(u || '') ? u : null);
const facts = (pairs) => `<dl class="facts">${pairs.filter(([, v]) => v).map(([k, v]) => `<dt>${k}</dt><dd>${esc(v)}</dd>`).join('')}</dl>`;

export const verdictPill = (v, tag = 'span', attrs = '') => `<${tag} class="verdict v-${slug(v)}" ${attrs}>${esc(cap(v))}</${tag}>`;

function meter(m) {
  if (!m) return '';
  const total = m.up + m.down || 1;
  const w = (n) => `${((100 * n) / total).toFixed(1)}%`;
  const label = `${m.down} findings below null (${m.significant_down} significant), ${m.up} above null (${m.significant_up} significant)`;
  return `<div class="meter" role="img" aria-label="${esc(label)}">
      <span class="seg down sig" style="width:${w(m.significant_down)}"></span><span class="seg down" style="width:${w(m.down - m.significant_down)}"></span><span class="seg up" style="width:${w(m.up - m.significant_up)}"></span><span class="seg up sig" style="width:${w(m.significant_up)}"></span>
    </div>
    <div class="meter-text num"><span>${m.down} below null (${m.significant_down} sig.)</span><span>${m.up} above null (${m.significant_up} sig.)</span></div>
    <div class="meter-text num">${plural(m.findings, 'finding', 'findings')} in ${plural(m.studies, 'study', 'studies')}, ${esc(m.family)} effects</div>`;
}

// Verdict rules, as in agents/rules.md.
const RULES = {
  supported: '3 or more studies, and at least two thirds of the findings whose CI excludes the null point the same way.',
  contested: 'Findings whose CI excludes the null point both ways, and the smaller side is at least a quarter.',
  mixed: 'Effects go both ways but are mostly non-significant, or the variable wording is ambiguous.',
  thin: '1 or 2 studies, or fewer than 5 findings.',
  'no evidence': 'Nothing found after searching synonyms, raw variable wording and neighbouring concepts.',
};

function findingsTable(fs, verdict) {
  const rule = `<p class="small rule"><strong>Why ${esc(verdict)}:</strong> ${esc(RULES[verdict] || 'No rule recorded for this verdict.')}</p>`;
  if (!fs.length) return `<details class="findings"><summary>Why this verdict</summary>${rule}</details>`;
  const rows = fs.map((f) => `<tr><td>${esc(f.variable_1)} and ${esc(f.variable_2)}</td>
      <td class="r">${fmt(f.value)}<div class="small muted">${esc(String(f.stat_type || '').replaceAll('_', ' '))}</div></td>
      <td class="r">${f.ci_lower == null ? '' : `${fmt(f.ci_lower)} to ${fmt(f.ci_upper)}`}</td>
      <td>${esc(f.population)}</td><td>${doiLink(f.doi)}</td></tr>`).join('');
  return `<details class="findings"><summary>Why this verdict, and ${plural(fs.length, 'key finding', 'key findings')}</summary>${rule}
    <div class="scroll-x"><table><thead><tr><th>Finding</th><th class="r">Effect</th><th class="r">95% CI</th><th>Population</th><th>DOI</th></tr></thead>
    <tbody>${rows}</tbody></table></div></details>`;
}

const card = (c) => `<article class="card">
    <div class="card-head">${verdictPill(c.verdict, 'button', 'type="button" data-findings aria-expanded="false" title="Show why, and the findings"')}<h4>${esc(c.claim)}</h4></div>
    ${meter(c.meter)}
    <p>${esc(c.basis)}</p>
    ${findingsTable(c.findings || [], c.verdict)}
    ${facts([['Populations', c.populations], ['Gaps', c.gaps]])}
  </article>`;

function table(t) {
  const right = t.columns.map((_, i) => t.rows.length > 0 && t.rows.every((r) => isNum(r[i])));
  const cell = (tag, v, i) => `<${tag}${right[i] ? ' class="r"' : ''}>${esc(v)}</${tag}>`;
  return `<div class="scroll-x"><table><caption>${esc(t.title)}</caption>
    <thead><tr>${t.columns.map((c, i) => cell('th', c, i)).join('')}</tr></thead>
    <tbody>${t.rows.map((r) => `<tr>${r.map((v, i) => cell('td', v, i)).join('')}</tr>`).join('')}</tbody></table></div>`;
}

const specs = new Map();
let nextChart = 0;
function chart(c) {
  const id = `chart-${nextChart++}`;
  specs.set(id, c.vega_lite_json);
  return `<figure class="chart"><figcaption>${esc(c.title)}</figcaption><div class="vega" id="${id}"></div></figure>`;
}

const SUPPORT = { backed: 'Backed', partial: 'Partial', unbacked: 'Unbacked' };
const RANK = { unbacked: 0, partial: 1, backed: 2 };
const weakest = (links) => (links.length < 2 ? null
  : links.reduce((w, l) => ((RANK[l.support] ?? 0) - (RANK[w.support] ?? 0) || l.n_studies - w.n_studies) < 0 ? l : w));
const chainLink = (l, weak) => `<li${l === weak ? ' class="weak"' : ''}>
    <div class="link-head"><span class="pill s-${slug(l.support)}">${esc(SUPPORT[l.support] || l.support)}</span>${l === weak ? '<span class="weak-tag">Weakest link</span>' : ''}
      <span>${esc(l.cause)} → ${l.via?.length ? `${l.via.map(esc).join(' → ')} → ` : ''}${esc(l.effect)}</span>
      <span class="num muted small">${plural(l.n_studies, 'study', 'studies')}</span></div>
    ${l.note ? `<p>${esc(l.note)}</p>` : ''}
    ${l.dois?.length ? `<p class="dois">${l.dois.map(doiLink).join('')}</p>` : ''}
  </li>`;

function source(s) {
  const href = s.doi ? `https://doi.org/${encodeURI(s.doi)}` : safeUrl(s.url);
  const title = href ? `<a href="${esc(href)}" target="_blank" rel="noopener">${esc(s.title)}</a>` : esc(s.title);
  const meta = [s.venue, s.year].filter(Boolean).map(esc).join(', ');
  return `<li>${title}${meta ? `<div class="small muted">${meta}</div>` : ''}<div class="small">${esc(s.why_relevant)}</div></li>`;
}

const MATCH = { exact: 'Exact', narrower: 'Narrower', broader: 'Broader', proxy: 'Proxy' };
const dataset = (d) => `<span class="ds">${esc(String(d).replace(/^WB_/, ''))}</span>`;
const indicator = (i) => `<li>${esc(i.name)} <span class="num small muted">${esc(i.indicator_id)}</span> ${dataset(i.database)}</li>`;
const csvs = new Map();
let nextCsv = 0;

function indicatorCsv(s) {
  const q = (v) => `"${String(v ?? '').replace(/"/g, '""')}"`;
  const head = ['seed_indicator_id', 'seed_dataset', 'linked_concept', 'concept_id', 'studies', 'indicator_id', 'indicator_name', 'dataset', 'different_dataset', 'data_gap', 'dois'];
  const rows = s.links.flatMap((l) => (l.indicators.length ? l.indicators : [{}]).map((i) => [s.seed.indicator_id, s.seed.database,
    l.concept_label, l.concept_id, l.studies, i.indicator_id, i.name, i.database, l.cross_dataset, l.data_gap, (l.dois || []).join(' ')]));
  return [head, ...rows].map((r) => r.map(q).join(',')).join('\n');
}

function indicatorMap(s) {
  const id = `csv-${nextCsv++}`;
  csvs.set(id, { name: `${slug(s.seed.indicator_id || 'indicators')}-linked-indicators.csv`, text: indicatorCsv(s) });
  const rows = s.links.map((l) => `<tr>
      <td><strong>${esc(l.concept_label)}</strong>
        ${l.cross_dataset ? '<span class="pill s-backed">Different dataset</span>' : ''}${l.data_gap ? '<span class="pill s-partial">Data gap</span>' : ''}
        <div class="small muted">${esc(l.note)}</div>${l.dois?.length ? `<p class="dois">${l.dois.map(doiLink).join('')}</p>` : ''}</td>
      <td class="r num">${plural(l.studies, 'study', 'studies')}</td>
      <td>${l.indicators.length ? `<ul class="plain">${l.indicators.map(indicator).join('')}</ul>` : '<span class="small muted">No World Bank indicator measures this</span>'}</td>
    </tr>`).join('');
  return `<p><strong>Starting indicator:</strong> ${esc(s.seed.name)} <span class="num small muted">${esc(s.seed.indicator_id)}</span> ${dataset(s.seed.database)}</p>
    <ul class="plain small">${s.matches.map((m) => `<li>Graph concept <strong>${esc(m.label)}</strong>: ${esc(MATCH[m.match] || m.match)} match. ${esc(m.why)}</li>`).join('')}</ul>
    <div class="scroll-x"><table><thead><tr><th>Linked to</th><th class="r">Evidence</th><th>World Bank indicators</th></tr></thead><tbody>${rows}</tbody></table></div>
    ${facts([['Gaps', s.gaps]])}
    <p><button type="button" class="download" data-csv="${id}">Download indicators (CSV)</button></p>`;
}

export function downloadCsv(id) {
  const f = csvs.get(id);
  if (!f) return;
  const a = Object.assign(document.createElement('a'), { href: URL.createObjectURL(new Blob([f.text], { type: 'text/csv' })), download: f.name });
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}

const RENDERERS = {
  indicator_map: indicatorMap,
  evidence: (s) => `<div class="cards">${s.cards.map(card).join('')}</div>`,
  eda: (s) => `<p>${esc(s.summary)}</p>${s.tables.map(table).join('')}${s.charts.map(chart).join('')}`,
  policy: (s) => `<p><strong>Policy:</strong> ${esc(s.policy)}</p><ol class="chain">${s.links.map((l) => chainLink(l, weakest(s.links))).join('')}</ol>${facts([['Gaps', s.gaps]])}`,
  research: (s) => `<p>${esc(s.summary)}</p><ol class="sources">${s.sources.map(source).join('')}</ol>`,
};
const KIND = { evidence: 'Evidence', eda: 'Data', policy: 'Theory of change', research: 'Sources', indicator_map: 'Indicators' };

const fallback = (s) => `<p class="small muted">No view for "${esc(s.type)}" sections yet, so here is its data.</p><pre class="json">${esc(JSON.stringify(s, null, 2))}</pre>`;

function section(s) {
  let body;
  try { body = RENDERERS[s.type] ? RENDERERS[s.type](s) : fallback(s); } catch { body = fallback(s); }
  return `<section class="sec"><header class="sec-head"><h3>${esc(s.title || s.type)}</h3><span class="kind">${esc(KIND[s.type] || s.type)}</span></header>${body}</section>`;
}

export function renderAnswer(a) {
  const caveats = a.caveats?.length ? `<h4 class="small">Caveats</h4><ul class="caveats">${a.caveats.map((c) => `<li>${esc(c)}</li>`).join('')}</ul>` : '';
  return `<div class="answer-top"><div><h3>Answer</h3><p>${esc(a.summary)}</p>${caveats}</div><div class="graph-panel"></div></div>
    ${(a.sections || []).map(section).join('')}`;
}

// Concepts the answer rests on, and the verdict of the first evidence card that covers each one.
export function answerConcepts(a) {
  const ids = new Set(); const verdicts = {};
  for (const s of a.sections || []) {
    (s.concept_ids || []).forEach((id) => ids.add(id));
    for (const c of s.cards || []) for (const id of c.concept_ids || []) { ids.add(id); verdicts[id] ??= c.verdict; }
  }
  return { ids: [...ids], verdicts };
}

const css = (n) => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
function chartTheme() {
  const text = css('--text'); const muted = css('--muted'); const line = css('--line');
  return {
    background: 'transparent', font: css('--font'), view: { stroke: 'transparent' },
    axis: { labelColor: muted, titleColor: text, gridColor: line, domainColor: line, tickColor: line, labelFontSize: 12, titleFontSize: 12 },
    legend: { labelColor: muted, titleColor: text, labelFontSize: 12, titleFontSize: 12, orient: 'bottom' },
    title: { color: text }, mark: { color: css('--cat-1') },
    range: { category: ['--cat-1', '--cat-2', '--cat-3', '--cat-4'].map(css) },
  };
}

export function mountCharts(root) {
  for (const el of root.querySelectorAll('.vega')) {
    const raw = specs.get(el.id); specs.delete(el.id);
    let spec;
    try { spec = JSON.parse(raw); } catch { el.innerHTML = '<p class="small muted">This chart spec is not valid JSON, so it is not drawn.</p>'; continue; }
    spec = { ...spec, width: 'container', autosize: { type: 'fit-x', contains: 'padding' }, config: { ...spec.config, ...chartTheme() } };
    if (!window.vegaEmbed) { el.innerHTML = '<p class="small muted">The chart library did not load. Check your connection and reload.</p>'; continue; }
    window.vegaEmbed(el, spec, { actions: false, renderer: 'svg' })
      .catch((e) => { el.innerHTML = `<p class="small muted">Could not draw this chart: ${esc(e.message)}</p>`; });
  }
}
