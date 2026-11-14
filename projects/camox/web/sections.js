// One renderer per section type. Each returns an HTML string; unknown types fall back to readable JSON.
export const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
export const slug = (s) => String(s).toLowerCase().replace(/[^a-z0-9]+/g, '-');
export const plural = (n, one, many) => `${n.toLocaleString()} ${n === 1 ? one : many}`;
const cap = (s) => s.charAt(0).toUpperCase() + s.slice(1);
const fmt = (v) => (v == null ? '' : Number(v).toLocaleString(undefined, { maximumFractionDigits: 2 }));
const isNum = (s) => /^[-+−]?[\d,.]+%?$/.test(String(s).trim());
// Indicator ids (WB_WDI_IT_NET_USER_ZS, FAO_FS_210091) anywhere in text link to their Data360 page.
const IND_RE = /\b(?:WB|FAO|ILO|IMF|WHO|UN|UNESCO|OECD)_[A-Z0-9]+_[A-Z0-9_]+\b/g;
export const wbUrl = (id) => `https://data360.worldbank.org/en/indicator/${encodeURIComponent(id)}`;
export const linked = (t) => esc(t).replace(IND_RE, (id) => `<a class="ind-id" href="${wbUrl(id)}" target="_blank" rel="noopener">${id}</a>`);
const DATASETS = { WB_WDI: 'World Development Indicators', WB_GS: 'Gender Statistics', WB_HNP: 'Health, Nutrition and Population',
  WB_FINDEX: 'Global Findex', WB_WBL: 'Women, Business and the Law', WB_ES: 'Enterprise Surveys', WB_BREADY: 'B-READY',
  WB_EDSTATS: 'Education Statistics', WB_WWBI: 'Worldwide Bureaucracy Indicators', WB_ESG: 'Environment, Social and Governance',
  WB_CLEAR: 'CLEAR', FAO_FS: 'FAO Food Security' };
export const datasetName = (d) => DATASETS[String(d).toUpperCase()] || String(d);
// Source labels name their provider; each becomes a chip linking to that provider. Older labels match by prefix.
const PROVIDERS = [[/^system public graph|^system graph|^graph/i, 'https://system.com/public'], [/data360|world bank/i, 'https://data360.worldbank.org'],
  [/openalex/i, 'https://openalex.org'], [/pubmed|ncbi/i, 'https://pubmed.ncbi.nlm.nih.gov'], [/web search|openai/i, null]];
export const sourceChips = (list) => `<span class="src-chips">${list.map((l) => {
  const href = PROVIDERS.find(([re]) => re.test(l))?.[1];
  return href ? `<a class="src-chip" href="${href}" target="_blank" rel="noopener">${esc(l)}</a>` : `<span class="src-chip">${esc(l)}</span>`;
}).join('')}</span>`;
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
const citedText = (text) => linked(text).replace(/\s*\[([^\]]*10\.\d{4,9}\/[^\]]*)\]/g, (_, inner) =>
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
const facts = (pairs) => `<dl class="facts">${pairs.filter(([, v]) => v).map(([k, v]) => `<dt>${k}</dt><dd>${linked(v)}</dd>`).join('')}</dl>`;

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
  const rows = fs.map((f) => `<tr><td data-label="Finding">${esc(f.variable_1)} and ${esc(f.variable_2)}</td>
      <td class="r" data-label="Effect">${fmt(f.value)}<div class="small muted">${esc(String(f.stat_type || '').replaceAll('_', ' '))}</div></td>
      <td class="r" data-label="95% CI">${f.ci_lower == null ? '' : `${fmt(f.ci_lower)} to ${fmt(f.ci_upper)}`}</td>
      <td data-label="Population">${esc(f.population)}</td><td data-label="DOI">${doiLink(f.doi)}</td></tr>`).join('');
  return `<details class="findings"><summary>Why this verdict, and ${plural(fs.length, 'key finding', 'key findings')}</summary>${rule}
    <div class="scroll-x"><table class="stack"><thead><tr><th>Finding</th><th class="r">Effect</th><th class="r">95% CI</th><th>Population</th><th>DOI</th></tr></thead>
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
  const cell = (tag, v, i) => `<${tag}${right[i] ? ' class="r"' : ''}${tag === 'td' ? ` data-label="${esc(t.columns[i])}"` : ''}>${tag === 'td' ? linked(v) : esc(v)}</${tag}>`;
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
    ${l.note ? `<p>${linked(l.note)}</p>` : ''}
    ${l.dois?.length ? `<p class="dois">${l.dois.map(doiLink).join('')}</p>` : ''}
  </li>`;

function source(s) {
  const href = s.doi ? `https://doi.org/${encodeURI(normDoi(s.doi))}` : safeUrl(s.url);
  const n = href ? `${cite(s.doi, href, { title: s.title, venue: s.venue, year: s.year })} ` : '';
  const title = `${n}${href ? `<a href="${esc(href)}" target="_blank" rel="noopener">${esc(s.title)}</a>` : esc(s.title)}`;
  const meta = [s.venue, s.year].filter(Boolean).map(esc).join(', ');
  return `<li>${title}${meta ? `<div class="small muted">${meta}</div>` : ''}<div class="small">${linked(s.why_relevant)}</div></li>`;
}

const MATCH = { exact: 'Exact', narrower: 'Narrower', broader: 'Broader', proxy: 'Proxy' };
const dataset = (d) => (d ? `<span class="ds" title="${esc(d)}">${esc(datasetName(d))}${datasetName(d) !== String(d) ? ` (${esc(d)})` : ''}</span>` : '');
// Graph concepts link to Wikidata; ids come from the project graph, so the links fill in once it loads.
const wd = new Map(); let wdProject = null;
const concept = (label, id) => `<a class="concept" data-cid="${esc(id)}"${wd.has(id) ? ` href="https://www.wikidata.org/wiki/${esc(wd.get(id))}"` : ''} target="_blank" rel="noopener"><strong>${esc(label)}</strong></a>`;
function loadWikidata() {
  const p = new URLSearchParams(location.hash.slice(1)).get('project');
  if (!p || p === wdProject) return;
  wdProject = p;
  fetch(`/api/projects/${encodeURIComponent(p)}/kg`).then((r) => r.json()).then((g) => {
    for (const n of g.nodes || []) if (n.data?.wikidata_id) wd.set(n.id, n.data.wikidata_id);
    document.querySelectorAll('a.concept[data-cid]:not([href])').forEach((a) => { if (wd.has(a.dataset.cid)) a.href = `https://www.wikidata.org/wiki/${wd.get(a.dataset.cid)}`; });
  }).catch(() => { wdProject = null; });
}
// Indicator: its name links to Data360; the id follows as small muted text.
const indLink = (name, id) => (id ? `<a href="${esc(wbUrl(id))}" target="_blank" rel="noopener">${esc(name || id)}</a> <span class="ind-id small muted">${esc(id)}</span>` : esc(name));
const tier = (n) => (n >= 10 ? 'strong' : n >= 3 ? 'moderate' : 'thin');
const pick = (i, l) => esc(JSON.stringify({ id: i.indicator_id, name: i.name, dataset: datasetName(i.database), url: wbUrl(i.indicator_id),
  concept: l.concept_label, tier: tier(l.studies), studies: l.studies, dois: (l.dois || []).join(' ') }));
// Project overview: every indicator map in the project merged into rows (one per concept and indicator, gaps with none).
function mapRows(runs) {
  const rows = new Map(); const seeds = new Set();
  for (const r of runs) for (const s of r.answer?.sections || []) if (s.type === 'indicator_map') {
    seeds.add(s.seed.database);
    for (const l of s.links) for (const i of l.indicators.length ? l.indicators : [null]) {
      const k = `${l.concept_id}|${i?.indicator_id ?? ''}`;
      (rows.get(k) || rows.set(k, { l, i, seed: s.seed.database, runs: new Set() }).get(k)).runs.add(r.id);
    }
  }
  const all = [...rows.values()].sort((a, b) => b.l.studies - a.l.studies);
  const found = new Set(all.filter((x) => x.i).map((x) => x.l.concept_id));
  all.forEach((x) => { x.kind = x.i ? (![x.seed, 'unknown dataset'].includes(x.i.database) ? 'other' : 'same') : found.has(x.l.concept_id) ? '' : 'gap'; });
  return { all: all.filter((x) => x.kind), seeds };
}
const questions = (xs) => plural(new Set(xs.flatMap((x) => [...x.runs])).size, 'question', 'questions');
const uniq = (xs) => new Set(xs).size;

export function kpiStrip(runs) {
  const { all, seeds } = mapRows(runs);
  if (!all.length) return '';
  const ind = all.filter((x) => x.i), other = all.filter((x) => x.kind === 'other'), gap = all.filter((x) => x.kind === 'gap');
  const studies = new Map(); all.forEach(({ l }) => studies.set(l.concept_id, Math.max(l.studies, studies.get(l.concept_id) || 0)));
  const datasets = new Set([...seeds, ...ind.map((x) => x.i.database)]); datasets.delete('unknown dataset');
  const cards = [[studies.size, 'linked concepts', '', all], [[...studies.values()].reduce((a, b) => a + b, 0), 'total studies', '', all],
    [uniq(ind.map((x) => x.i.indicator_id)), 'World Bank indicators found', 'ind', ind], [datasets.size, 'datasets spanned', 'ind', ind],
    [other.length, 'links outside the starting dataset', 'other', other], [uniq(gap.map((x) => x.l.concept_id)), 'not found in the World Bank datasets we checked', 'gap', gap]];
  return `<div class="kstrip" role="group" aria-label="Project totals; pick one to filter the links">${cards.map(([v, label, f, xs]) =>
    `<button type="button" class="kcard" data-kfilter="${f}" aria-pressed="false"><span class="kv num">${v.toLocaleString()}</span>
      <span class="kl">${label}</span><span class="small muted">from ${questions(xs.length ? xs : all)}</span></button>`).join('')}</div>`;
}
const TIER = { strong: 's-backed', moderate: 's-partial', thin: 's-unbacked' };
export function linkGroups(runs) {
  const { all } = mapRows(runs);
  if (!all.length) return '';
  const max = Math.max(...all.map((x) => x.l.studies));
  const row = ({ l, i, kind }) => `<li data-kind="${i ? 'ind ' : ''}${kind}">
    <span class="lr-c"><strong>${esc(l.concept_label)}</strong> <span class="pill ${TIER[tier(l.studies)]}">${cap(tier(l.studies))}</span></span>
    <span class="lr-n num">${plural(l.studies, 'study', 'studies')}<span class="sbar"><span style="width:${((100 * l.studies) / max).toFixed(1)}%"></span></span></span>
    <span class="lr-i">${i ? `${indLink(i.name, i.indicator_id)} ${dataset(i.database)}` : '<span class="small muted">No World Bank indicator measures this</span>'}</span>
    ${i ? `<button type="button" class="chip" data-pick="${pick(i, l)}">Add to my list</button>` : ''}</li>`;
  const group = (title, line, xs, note = '') => (xs.length ? `<div class="lgroup"><h3>${title} <span class="muted num">${xs.length}</span></h3>
    <p class="small muted">${line}</p><ul class="links">${xs.map(row).join('')}</ul>${note}</div>` : '');
  const other = all.filter((x) => x.kind === 'other'), thin = other.filter((x) => tier(x.l.studies) === 'thin').length;
  return group('Less obvious', 'Linked by 3 or more studies, measured in a different World Bank dataset from the starting indicator.',
    other.filter((x) => tier(x.l.studies) !== 'thin'), thin ? `<p class="small muted">${plural(thin, 'more link', 'more links')} to other datasets rest on 1 or 2 studies; they are in the full analysis below.</p>` : '')
    + group('Obvious', 'Measured in the same dataset as the starting indicator.', all.filter((x) => x.kind === 'same'))
    + group('Gaps', 'Research links these to the topic, but no World Bank indicator in the datasets we checked measures them.', all.filter((x) => x.kind === 'gap'))
    + `<p class="small muted">From ${questions(all)}. Study counts: System Public Graph. Indicators: World Bank Data360.</p>`;
}
// A KPI card filters the link lists to its rows; pressing it again shows all.
document.addEventListener('click', (e) => {
  const k = e.target.closest('[data-kfilter]');
  if (!k) return;
  const on = k.getAttribute('aria-pressed') !== 'true' && k.dataset.kfilter;
  document.querySelectorAll('[data-kfilter]').forEach((b) => b.setAttribute('aria-pressed', b === k && k.getAttribute('aria-pressed') !== 'true'));
  document.querySelectorAll('.lgroup').forEach((g) => {
    g.querySelectorAll('li[data-kind]').forEach((li) => { li.hidden = !!on && !li.dataset.kind.split(' ').includes(on); });
    g.hidden = !g.querySelector('li[data-kind]:not([hidden])');
  });
});

const indicator = (i, l) => `<li>${indLink(i.name, i.indicator_id)} ${dataset(i.database)}
  <button type="button" class="chip" data-pick="${pick(i, l)}">Add to my list</button></li>`;

// "My list": indicators the user picks across answers, kept per project in localStorage (in memory if storage is blocked).
const lists = new Map();
const listKey = () => `camox-list-${new URLSearchParams(location.hash.slice(1)).get('project') || ''}`;
const myList = () => {
  if (!lists.has(listKey())) { let l = []; try { l = JSON.parse(localStorage.getItem(listKey())) || []; } catch { /* no storage */ } lists.set(listKey(), l); }
  return lists.get(listKey());
};
const saveList = (l) => {
  lists.set(listKey(), l);
  try { localStorage.setItem(listKey(), JSON.stringify(l)); } catch { /* no storage: the list lasts this page */ }
  document.querySelectorAll('.my-list').forEach(renderMyList);
};
export function renderMyList(el) {
  const l = myList();
  el.innerHTML = l.length ? `<ul class="plain">${l.map((x) => `<li>${indLink(x.name, x.id)} <span class="ds">${esc(x.dataset)}</span>
      <span class="small muted">${esc(x.concept)}, ${plural(x.studies, 'study', 'studies')}</span>
      <button type="button" class="chip" data-unpick="${esc(x.id)}">Remove</button></li>`).join('')}</ul>
    <p><button type="button" class="download" data-mylist>Download my list (CSV)</button></p>`
    : '<p class="small muted">Add indicators from any indicator map in this project with "Add to my list".</p>';
}
document.addEventListener('click', (e) => {
  const add = e.target.closest('[data-pick]'), rm = e.target.closest('[data-unpick]');
  if (add) { const x = JSON.parse(add.dataset.pick); if (!myList().some((y) => y.id === x.id)) saveList([...myList(), x]); add.textContent = 'In my list'; }
  if (rm) saveList(myList().filter((y) => y.id !== rm.dataset.unpick));
  if (e.target.closest('[data-mylist]')) {
    const q = (v) => `"${String(v ?? '').replace(/"/g, '""')}"`;
    const rows = [['indicator_id', 'name', 'dataset', 'url', 'linked_concept', 'tier', 'studies', 'dois'],
      ...myList().map((x) => [x.id, x.name, x.dataset, x.url, x.concept, x.tier, x.studies, x.dois])];
    csvs.set('my-list', { name: 'my-indicator-list.csv', text: rows.map((r) => r.map(q).join(',')).join('\n') });
    downloadCsv('my-list');
  }
});
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
      <td data-label="Linked to">${concept(l.concept_label, l.concept_id)}
        ${l.cross_dataset ? '<span class="pill s-backed">Different dataset</span>' : ''}${l.data_gap ? '<span class="pill s-partial">Data gap</span>' : ''}
        <div class="small muted">${linked(l.note)}</div>${l.dois?.length ? `<p class="dois">${l.dois.map(doiLink).join('')}</p>` : ''}</td>
      <td class="r num" data-label="Evidence">${plural(l.studies, 'study', 'studies')}</td>
      <td data-label="World Bank indicators">${l.indicators.length ? `<ul class="plain">${l.indicators.map((i) => indicator(i, l)).join('')}</ul>` : '<span class="small muted">No World Bank indicator measures this</span>'}</td>
    </tr>`).join('');
  return `<p><strong>Starting indicator:</strong> ${indLink(s.seed.name, s.seed.indicator_id)} ${dataset(s.seed.database)}</p>
    <ul class="plain small">${s.matches.map((m) => `<li>Graph concept ${concept(m.label, m.concept_id)}:${esc(MATCH[m.match] || m.match)} match. ${linked(m.why)}</li>`).join('')}</ul>
    <div class="filter" role="group" aria-label="Show links"><button type="button" class="chip" data-show="" aria-pressed="true">All ${s.links.length}</button>
      <button type="button" class="chip" data-show="other" aria-pressed="false">Other datasets ${s.links.filter((l) => l.cross_dataset).length}</button>
      <button type="button" class="chip" data-show="gap" aria-pressed="false">Data gaps ${s.links.filter((l) => l.data_gap).length}</button></div>
    <div class="scroll-x"><table class="stack"><thead><tr><th>Linked to</th><th class="r">Evidence</th><th>World Bank indicators</th></tr></thead><tbody>${rows}</tbody></table></div>
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
  eda: (s) => `<p>${linked(s.summary)}</p>${s.tables.map(table).join('')}${s.charts.map(chart).join('')}`,
  policy: (s) => `<p><strong>Policy:</strong> ${esc(s.policy)}</p><ol class="chain">${s.links.map((l) => chainLink(l, weakest(s.links))).join('')}</ol>${facts([['Gaps', s.gaps]])}`,
  research: (s) => `<p>${linked(s.summary)}</p><ol class="sources">${s.sources.map(source).join('')}</ol>`,
};
const KIND = { evidence: 'Evidence', eda: 'Data', policy: 'Theory of change', research: 'Sources', indicator_map: 'Indicators' };

const fallback = (s) => `<p class="small muted">No view for "${esc(s.type)}" sections yet, so here is its data.</p><pre class="json">${esc(JSON.stringify(s, null, 2))}</pre>`;

// Each section ends with one source line built from section_sources: provider names, links, and the graph licence.
const NAMES = [[/web search|openai/i, 'Web search (web, not checked against the graph)'], [/graph/i, 'System Public Graph'],
  [/data360|world bank/i, 'World Bank Data360'], [/openalex/i, 'OpenAlex'], [/pubmed|ncbi/i, 'PubMed']];
function sourceLine(sources) {
  if (!Array.isArray(sources) || !sources.length) return '';
  const seen = new Map();
  for (const l of sources) {
    const name = NAMES.find(([re]) => re.test(l))?.[1] || l;
    if (!seen.has(name)) seen.set(name, PROVIDERS.find(([re]) => re.test(l))?.[1]);
  }
  const items = [...seen].map(([n, href]) => (href ? `<a href="${href}" target="_blank" rel="noopener">${esc(n)}</a>` : esc(n))).join(' · ');
  const lic = seen.has('System Public Graph') ? ' Graph-derived content: <a href="https://creativecommons.org/licenses/by-nc/4.0/" target="_blank" rel="noopener">CC BY-NC 4.0</a>.' : '';
  return `<p class="src-line small muted">Source: ${items}.${lic}</p>`;
}

function section(s, sources) {
  let body;
  try { body = RENDERERS[s.type] ? RENDERERS[s.type](s) : fallback(s); } catch { body = fallback(s); }
  return `<section class="sec"><header class="sec-head"><h3>${esc(s.title || s.type)}</h3><span class="kind">${esc(KIND[s.type] || s.type)}</span></header>${body}${sourceLine(sources)}</section>`;
}

// Verification badge: what the checker looked at, and any issues it found.
export function verifyPill(v) {
  if (!v || typeof v !== 'object') return '<span class="pill">Not verified</span>';
  const issues = Array.isArray(v.issues) ? v.issues : [];
  const ok = v.status === 'verified';
  const major = issues.filter((i) => i.severity === 'major').length;
  const label = ok ? [`Verified`, `${plural(v.claims_checked ?? 0, 'claim', 'claims')} checked`, issues.length ? plural(issues.length, 'note', 'notes') : ''].filter(Boolean).join(' · ')
    : `${plural(major || issues.length, 'issue', 'issues')} found`;
  return `<span class="pill ${ok ? 's-backed' : 's-partial'}">${esc(label)}</span>`;
}
function verification(v) {
  if (!v || typeof v !== 'object') return verifyPill(v);
  const issues = Array.isArray(v.issues) ? v.issues : [];
  const checks = Array.isArray(v.code_checks) ? v.code_checks : [];
  return `<details class="verify ${v.status === 'verified' ? 'ok' : 'issues'}"><summary>${verifyPill(v)}</summary>
    <div class="verify-body small">
      ${issues.length ? `<ul>${issues.map((i) => `<li><strong>${esc(cap(String(i.severity || 'minor')))}:</strong> ${esc(i.problem)}${i.claim ? `<div class="muted">Claim: ${esc(i.claim)}</div>` : ''}</li>`).join('')}</ul>` : ''}
      ${Number.isFinite(v.claims_checked) ? `<p>${plural(v.claims_checked, 'claim', 'claims')} in the answer checked against the tool results.</p>` : ''}
      ${checks.length ? `<p class="label">Checks run in code</p><ul>${checks.map((c) => `<li>${esc(c)}</li>`).join('')}</ul>` : ''}
    </div></details>`;
}

export function renderAnswer(a, run) {
  refs = { run, list: [], index: new Map() };
  loadWikidata();
  const summary = citedText(a.summary);
  const body = (a.sections || []).map((s, i) => section(s, a.section_sources?.[i])).join('');
  const caveats = a.caveats?.length ? `<h4 class="small">Caveats</h4><ul class="caveats">${a.caveats.map((c) => `<li>${citedText(c)}</li>`).join('')}</ul>` : '';
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
    axisY: { titleLimit: 190, labelLimit: 140 }, axisX: { labelLimit: 120 },  // long titles must not run past the plot on phones
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
