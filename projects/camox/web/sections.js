// One renderer per section type. Each returns an HTML string; unknown types fall back to readable JSON.
export const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
export const slug = (s) => String(s).toLowerCase().replace(/[^a-z0-9]+/g, '-');
export const plural = (n, one, many) => `${n.toLocaleString()} ${n === 1 ? one : many}`;
const cap = (s) => s.charAt(0).toUpperCase() + s.slice(1);
const fmt = (v) => (v == null ? '' : Number(v).toLocaleString(undefined, { maximumFractionDigits: 2 }));
const isNum = (s) => /^[-+−]?[\d,.]+%?$/.test(String(s).trim());
const safeUrl = (u) => (/^https?:\/\//.test(u || '') ? u : null);
// Short, plain-text version of an error from the server or a library: never raw HTML or a long body.
export const short = (m, n = 160) => {
  const t = String(m ?? '');
  if (/<(html|!doctype|body|head)\b/i.test(t)) return 'the server returned an error page';
  const s = t.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
  return s.length > n ? `${s.slice(0, n - 1)}…` : s;
};

// Citations: every DOI (and source URL) in an answer gets one number, summary first, then sections in order.
let refs = { run: '', list: [], index: new Map() };
const normDoi = (d) => String(d).trim().replace(/^https?:\/\/(dx\.)?doi\.org\//i, '').replace(/^doi:\s*/i, '').replace(/[.,;]+$/, '');
function cite(doi, url, meta = {}) {
  const key = doi ? normDoi(doi).toLowerCase() : url;
  if (!refs.index.has(key)) { refs.list.push({ doi: doi ? normDoi(doi) : null, url, ...meta }); refs.index.set(key, refs.list.length); }
  const n = refs.index.get(key);
  return `<a class="cite" href="#ref-${refs.run}-${n}" data-ref="ref-${refs.run}-${n}" title="Reference ${n}">[${n}]</a>`;
}
const doiLink = (d) => (d ? `<span class="doi">${cite(d)} <a href="${esc('https://doi.org/' + encodeURI(normDoi(d)))}" target="_blank" rel="noopener">${esc(normDoi(d))}</a></span>` : '');
// Summary text with [10.x/y] (or [10.x/a; 10.y/b]) replaced by numbered superscript links.
const citedText = (text) => esc(text).replace(/\s*\[([^\]]*10\.\d{4,9}\/[^\]]*)\]/g, (_, inner) =>
  `<sup>${inner.split(/[;,]\s*|\s+/).filter((d) => /^10\.\d{4,9}\//.test(d)).map((d) => cite(d.replace(/&amp;/g, '&'))).join('')}</sup>`).replaceAll('</sup><sup>', '');

export function refBody(r) {
  const href = r.doi ? `https://doi.org/${encodeURI(r.doi)}` : safeUrl(r.url);
  const cited = Number.isFinite(r.cited_by_count) ? plural(r.cited_by_count, 'citation', 'citations') : '';
  const meta = [r.venue, r.year, cited].filter(Boolean).map(esc).join(', ');
  const label = r.doi || (href ? new URL(href).hostname : '');
  const pmid = String(r.pmid ?? '').match(/\d+/)?.[0];
  return `<span class="ref-title">${esc(r.title || label)}</span>${meta ? `<span class="muted">${meta}</span>` : ''}
    <span class="ref-actions">${href ? `<a class="act" href="${esc(href)}" target="_blank" rel="noopener">${r.doi ? 'Open paper' : 'Open source'}</a>` : ''}
    ${pmid ? `<a class="act" href="https://pubmed.ncbi.nlm.nih.gov/${pmid}/" target="_blank" rel="noopener">PubMed</a>` : ''}
    ${r.doi && r.title ? `<span class="doi-text">${esc(r.doi)}</span>` : ''}</span>`;
}
const references = () => (refs.list.length ? `<section class="sec refs" id="refs-${refs.run}"><header class="sec-head"><h3>References</h3>
    <span class="kind">${plural(refs.list.length, 'source', 'sources')}</span></header>
    <ol class="refs-list">${refs.list.map((r, i) => `<li id="ref-${refs.run}-${i + 1}"${r.doi ? ` data-doi="${esc(r.doi)}"` : ''}>
      <span class="n num">[${i + 1}]</span><div>${refBody(r)}</div></li>`).join('')}</ol></section>` : '');
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

export function table(t) {
  const blank = (v) => /^[\s—–-]*$/.test(String(v ?? ''));
  const right = t.columns.map((_, i) => t.rows.some((r) => isNum(r[i])) && t.rows.every((r) => isNum(r[i]) || blank(r[i])));
  const cell = (tag, v, i) => `<${tag}${right[i] ? ' class="r"' : ''}${tag === 'td' ? ` data-label="${esc(t.columns[i])}"` : ''}>${esc(v)}</${tag}>`;
  return `<div class="scroll-x"><table class="stack"><caption>${esc(t.title)}</caption>
    <thead><tr>${t.columns.map((c, i) => cell('th', c, i)).join('')}</tr></thead>
    <tbody>${t.rows.map((r) => `<tr>${r.map((v, i) => cell('td', v, i)).join('')}</tr>`).join('')}</tbody></table></div>`;
}

const specs = new Map();
let nextChart = 0;
export function chart(c) {
  const id = `chart-${nextChart++}`;
  specs.set(id, c.vega_lite_json);
  return `<figure class="chart"><figcaption>${esc(c.title)}</figcaption><div class="vega" id="${id}"></div></figure>`;
}

const SUPPORT = { backed: 'Backed', partial: 'Partial', unbacked: 'Unbacked' };
const RANK = { unbacked: 0, partial: 1, backed: 2 };
const weakest = (links) => (links.length < 2 ? null
  : links.reduce((w, l) => ((RANK[l.support] ?? 0) - (RANK[w.support] ?? 0) || l.n_studies - w.n_studies) < 0 ? l : w));
const chainLink = (l, weak) => `<li${l === weak ? ' class="weak"' : ''}>
    <div class="link-head"><span class="pill s-${slug(l.support)}">${esc(SUPPORT[l.support] || l.support)}</span>
      <span class="num muted small">${plural(l.n_studies, 'study', 'studies')}</span>${l === weak ? '<span class="weak-tag">Weakest link</span>' : ''}</div>
    <div class="link-path">${esc(l.cause)} → ${l.via?.length ? `${l.via.map(esc).join(' → ')} → ` : ''}${esc(l.effect)}</div>
    ${l.note ? `<p>${esc(l.note)}</p>` : ''}
    ${l.dois?.length ? `<p class="dois">${l.dois.map(doiLink).join('')}</p>` : ''}
  </li>`;

function source(s) {
  const href = s.doi ? `https://doi.org/${encodeURI(normDoi(s.doi))}` : safeUrl(s.url);
  const n = href ? `${cite(s.doi, href, { title: s.title, venue: s.venue, year: s.year })} ` : '';
  const title = `${n}${href ? `<a href="${esc(href)}" target="_blank" rel="noopener">${esc(s.title)}</a>` : esc(s.title)}`;
  const meta = [s.venue, s.year].filter(Boolean).map(esc).join(', ');
  return `<li>${title}${meta ? `<div class="small muted">${meta}</div>` : ''}<div class="small">${esc(s.why_relevant)}</div></li>`;
}

const MATCH = { exact: 'Exact', narrower: 'Narrower', broader: 'Broader', proxy: 'Proxy' };
const dataset = (d) => `<span class="ds">${esc(String(d).replace(/^WB_/, ''))}</span>`;
const wbUrl = (id) => `https://data360.worldbank.org/en/indicator/${encodeURIComponent(id)}`;
const indId = (id) => (id ? `<a class="ind-id num small" href="${esc(wbUrl(id))}" target="_blank" rel="noopener">${esc(id)}</a>` : '');
const indicator = (i) => `<li>${esc(i.name)} ${indId(i.indicator_id)} ${dataset(i.database)}</li>`;
const csvs = new Map();
let nextCsv = 0;

function indicatorCsv(s) {
  const q = (v) => `"${String(v ?? '').replace(/"/g, '""')}"`;
  const head = ['seed_indicator_id', 'seed_dataset', 'linked_concept', 'concept_id', 'studies', 'indicator_id', 'indicator_name', 'dataset', 'url', 'different_dataset', 'data_gap', 'dois'];
  const rows = s.links.flatMap((l) => (l.indicators.length ? l.indicators : [{}]).map((i) => [s.seed.indicator_id, s.seed.database,
    l.concept_label, l.concept_id, l.studies, i.indicator_id, i.name, i.database, i.indicator_id ? wbUrl(i.indicator_id) : '', l.cross_dataset, l.data_gap, (l.dois || []).join(' ')]));
  return [head, ...rows].map((r) => r.map(q).join(',')).join('\n');
}

function indicatorMap(s) {
  const id = `csv-${nextCsv++}`;
  csvs.set(id, { name: `${slug(s.seed.indicator_id || 'indicators')}-linked-indicators.csv`, text: indicatorCsv(s) });
  const rows = s.links.map((l) => `<tr data-kind="${l.cross_dataset ? 'other' : ''} ${l.data_gap ? 'gap' : ''}">
      <td><strong>${esc(l.concept_label)}</strong>
        ${l.cross_dataset ? '<span class="pill s-backed">Different dataset</span>' : ''}${l.data_gap ? '<span class="pill s-partial">Data gap</span>' : ''}
        <div class="small muted">${esc(l.note)}</div>${l.dois?.length ? `<p class="dois">${l.dois.map(doiLink).join('')}</p>` : ''}</td>
      <td class="r num">${plural(l.studies, 'study', 'studies')}</td>
      <td>${l.indicators.length ? `<ul class="plain">${l.indicators.map(indicator).join('')}</ul>` : '<span class="small muted">No World Bank indicator measures this</span>'}</td>
    </tr>`).join('');
  return `<p><strong>Starting indicator:</strong> ${esc(s.seed.name)} ${indId(s.seed.indicator_id)} ${dataset(s.seed.database)}</p>
    <ul class="plain small">${s.matches.map((m) => `<li>Graph concept <strong>${esc(m.label)}</strong>: ${esc(MATCH[m.match] || m.match)} match. ${esc(m.why)}</li>`).join('')}</ul>
    <div class="filter" role="group" aria-label="Show links"><button type="button" class="chip" data-show="" aria-pressed="true">All ${s.links.length}</button>
      <button type="button" class="chip" data-show="other" aria-pressed="false">Other datasets ${s.links.filter((l) => l.cross_dataset).length}</button>
      <button type="button" class="chip" data-show="gap" aria-pressed="false">Data gaps ${s.links.filter((l) => l.data_gap).length}</button></div>
    <div class="scroll-x"><table><thead><tr><th>Linked to</th><th class="r">Evidence</th><th>World Bank indicators</th></tr></thead><tbody>${rows}</tbody></table></div>
    <p class="small muted">Study counts: System Public Graph. Indicators: World Bank Data360.</p>
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

function section(s, sources) {
  let body;
  try { body = RENDERERS[s.type] ? RENDERERS[s.type](s) : fallback(s); } catch { body = fallback(s); }
  const data = Array.isArray(sources) && sources.length ? `<p class="data-src small muted">Data: ${sources.map(esc).join('; ')}</p>` : '';
  return `<section class="sec"><header class="sec-head"><h3>${esc(s.title || s.type)}</h3><span class="kind">${esc(KIND[s.type] || s.type)}</span></header>${data}${body}</section>`;
}

// Verification badge: what the checker looked at, and any issues it found.
function verification(v) {
  if (!v || typeof v !== 'object') return '';
  const issues = Array.isArray(v.issues) ? v.issues : [];
  const checks = Array.isArray(v.code_checks) ? v.code_checks : [];
  const ok = v.status === 'verified';
  const major = issues.filter((i) => i.severity === 'major').length;
  const label = ok ? [`Verified`, `${plural(v.claims_checked ?? 0, 'claim', 'claims')} checked`, issues.length ? plural(issues.length, 'note', 'notes') : ''].filter(Boolean).join(' · ')
    : `${plural(major || issues.length, 'issue', 'issues')} found`;
  return `<details class="verify ${ok ? 'ok' : 'issues'}"><summary><span class="pill ${ok ? 's-backed' : 's-partial'}">${esc(label)}</span></summary>
    <div class="verify-body small">
      ${issues.length ? `<ul>${issues.map((i) => `<li><strong>${esc(cap(String(i.severity || 'minor')))}:</strong> ${esc(i.problem)}${i.claim ? `<div class="muted">Claim: ${esc(i.claim)}</div>` : ''}</li>`).join('')}</ul>` : ''}
      ${Number.isFinite(v.claims_checked) ? `<p>${plural(v.claims_checked, 'claim', 'claims')} in the answer checked against the tool results.</p>` : ''}
      ${checks.length ? `<p class="label">Checks run in code</p><ul>${checks.map((c) => `<li>${esc(c)}</li>`).join('')}</ul>` : ''}
    </div></details>`;
}

export function renderAnswer(a, run) {
  refs = { run, list: [], index: new Map() };
  const summary = citedText(a.summary);
  const body = (a.sections || []).map((s, i) => section(s, a.section_sources?.[i])).join('');
  const caveats = a.caveats?.length ? `<h4 class="small">Caveats</h4><ul class="caveats">${a.caveats.map((c) => `<li>${esc(c)}</li>`).join('')}</ul>` : '';
  const jump = refs.list.length ? `<a class="sources-jump small" href="#refs-${run}" data-ref="refs-${run}">Sources (${refs.list.length})</a>` : '';
  return `<div class="answer-top"><div><div class="answer-head"><h3>Answer</h3>${verification(a.verification)}${jump}</div>
    <p class="summary">${summary}</p>${caveats}</div><div class="graph-panel"></div></div>
    ${body}${references()}`;
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
    range: { category: ['--cat-1', '--cat-2', '--cat-3', '--cat-4', '--cat-5', '--cat-6'].map(css) },
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
      .catch((e) => { el.innerHTML = `<p class="small muted">Could not draw this chart: ${esc(short(e.message))}. The rest of the answer is unaffected.</p>`; });
  }
}
