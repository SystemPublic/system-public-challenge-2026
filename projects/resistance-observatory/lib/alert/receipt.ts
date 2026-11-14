/**
 * The Decision Receipt: for one alert, every number, threshold and graph id
 * it rests on, each with a link. The same receipt is rendered in the alert
 * inspector, the email preview and the email that is sent, so no claim goes
 * out uncited.
 *
 * Also here: which graph findings make up the stakes chain for a place, and
 * the email body (text and HTML) built from the same content.
 */
import type { AlertEvent, Watch, WhoBasis } from "./derive";
import { KIND_LABEL, SOURCE_LABEL, ci, frac, pct, type EventCopy } from "./copy";
import { EVIDENCE_TIER, NEXT_STEPS_NOTE, NO_STUDY_TYPE, assayKeywords, enaUrl, methodText, type GenomeContext, type StudyContextFile } from "./context";
import { pmidStr, type AbstractPrevalence, type ClientPack, type GraphFinding, type MarkerDef, type Paper } from "./pack";

export const SOURCES = {
  pf8: { label: "MalariaGEN Pf8, DOI 10.5281/zenodo.18681980", url: "https://zenodo.org/records/18681980" },
  graph: { label: "System Public Graph v2.1, DOI 10.7910/DVN/7V6JDO", url: "https://doi.org/10.7910/DVN/7V6JDO" },
  whoFallback: {
    label: "WHO guidelines for malaria (13 August 2025)",
    url: "https://iris.who.int/server/api/core/bitstreams/26a6af2d-060c-4449-8207-1f25e63c6cc3/content",
  },
} as const;

/** The graph release every tab names. The pack's CSV export is dated a week later; that date stays in the pack metadata. */
export const GRAPH_RELEASE = "System graph v2.1, 1 July 2026";

/**
 * Vetted ids removed after checking against the paper. PEyo2A8Ol0 (PMID 26429700): relative risk 0.32 is
 * dihydroartemisinin-piperaquine IPTp compared against SP IPTp; the graph presents it as an effect of SP.
 */
export const EXCLUDED_AFTER_CHECK: Record<string, string> = {
  PEyo2A8Ol0: "reversed comparison: the paper reports dihydroartemisinin-piperaquine against SP, not an effect of SP",
};

export const PRESET_BADGE = "Project notification preset (no published WHO K540E cut-off for this region)";
export const TIER = {
  checked: "Source-checked against paper",
  unverified: "Reported by System Graph, unverified",
} as const;

export const pubmedUrl = (pmid: string) => `https://pubmed.ncbi.nlm.nih.gov/${encodeURIComponent(pmid)}/`;

/* ------------------------------------------------------ finding wording --- */

const STAT_LABEL: Record<string, string> = {
  mean_difference_unstandardized: "mean difference",
  relative_risk_ratio: "relative risk",
  odds_ratio: "odds ratio",
  hazard_ratio: "hazard ratio",
};

/** The statistic as the graph holds it. No interpretation added. */
export function statText(f: GraphFinding): string | null {
  if (typeof f.statistic_value !== "number") return null;
  const raw = f.statistic_label || f.statistic_type || "statistic";
  const label = STAT_LABEL[raw] ?? raw.replace(/_/g, " ");
  const level = typeof f.ci_level === "number" ? `${f.ci_level <= 1 ? Math.round(f.ci_level * 100) : f.ci_level}% ` : "";
  const interval = typeof f.ci_lower === "number" && typeof f.ci_upper === "number" ? ` (${level}CI ${f.ci_lower} to ${f.ci_upper})` : "";
  const p = typeof f.p_value === "number" ? `, p = ${f.p_value}` : "";
  return `${label} ${f.statistic_value}${interval}${p}`;
}

/** variable_1 and variable_2 are an association pair, not exposure then outcome. */
export const pairText = (f: GraphFinding) => `${f.variable_1 ?? "variable 1"} <-> ${f.variable_2 ?? "variable 2"}`;

/* ---------------------------------------------------------------- stakes --- */

const USE_ORDER: Record<WhoBasis, RegExp[]> = {
  east_southern_africa: [/preg|iptp/i, /infant/i, /season/i, /treat/i],
  central_west_africa: [/season/i, /preg|iptp/i, /infant/i, /treat/i],
  outside_africa: [/treat/i, /preg|iptp/i, /infant/i, /season/i],
};

export type Stakes = {
  /** Graph findings on a K540E-containing haplotype from this country. */
  local: GraphFinding[];
  /** SP findings grouped by use, ordered to fit the region; checked and same-country findings first. */
  groups: { use: string; findings: GraphFinding[] }[];
  /** The few findings that lead the chain (and go in the email). */
  lead: GraphFinding[];
};

export function pickStakes(pack: ClientPack, area: string, basis: WhoBasis): Stakes {
  const local = pack.graph.haplotype_findings.filter((f) => f.country_iso3 === area);
  const score = (f: GraphFinding) => (f.checked?.country_iso3 === area ? 0 : f.source_checked ? 1 : 2);
  const byUse = new Map<string, GraphFinding[]>();
  const stakesSp = pack.graph.stakes_sp.filter((f) => !(f.system_id in EXCLUDED_AFTER_CHECK));
  for (const f of stakesSp) {
    const use = f.use ?? "Other";
    byUse.set(use, [...(byUse.get(use) ?? []), f]);
  }
  const rank = (use: string) => {
    const i = USE_ORDER[basis].findIndex((re) => re.test(use));
    return i === -1 ? 99 : i;
  };
  const groups = [...byUse.entries()]
    .map(([use, findings]) => ({ use, findings: [...findings].sort((a, b) => score(a) - score(b)) }))
    .sort((a, b) => rank(a.use) - rank(b.use));
  // lead: a same-country checked SP finding if there is one, then the best of the two most relevant uses
  const sameCountry = stakesSp.filter((f) => f.checked?.country_iso3 === area);
  const lead: GraphFinding[] = [...local];
  for (const f of [...sameCountry, ...groups.slice(0, 2).map((g) => g.findings[0])]) {
    if (f && !lead.includes(f) && lead.length < Math.max(3, local.length + 1)) lead.push(f);
  }
  return { local, groups, lead };
}

/* --------------------------------------------------------- study context --- */

/** Tier line for a paper item: what kind of study, where, in whom. From the abstract fields and the title only. */
export function paperTierDetail(paper: Paper | undefined, figure: AbstractPrevalence | undefined): string[] {
  const words = assayKeywords(paper?.title);
  return [
    figure?.site ? `site: ${figure.site}` : null,
    figure?.population ? `population: ${figure.population}` : null,
    words.length ? `title mentions: ${words.join(", ")}` : "assay not named in the title",
  ].filter((x): x is string => Boolean(x));
}

/** Tier line for a graph finding: study type and population, as the graph gives them. */
export function graphTierDetail(f: GraphFinding | undefined): string[] {
  if (!f) return [];
  return [`study type: ${f.study_type ?? NO_STUDY_TYPE}`, f.population ? `population: ${f.population}` : "population not given by the graph"];
}

export function glossaryText(study: StudyContextFile | null | undefined, methods: string[]): string {
  const g = study?._meta?.dna_method_glossary ?? {};
  return methods
    .filter((m) => g[m])
    .map((m) => `${m}: ${g[m]}`)
    .join(" · ");
}

function studyRows(args: {
  e: AlertEvent;
  pack: ClientPack;
  marker: MarkerDef;
  paper?: Paper;
  figure?: AbstractPrevalence;
  graphFinding?: GraphFinding;
  ctx?: GenomeContext | null;
  matched?: AbstractPrevalence[];
  papers?: Map<string, Paper>;
}): ReceiptRow[] {
  const { e, ctx } = args;
  const rows: ReceiptRow[] = [];
  if (e.source === "papers") {
    rows.push({ label: "Evidence tier", text: [EVIDENCE_TIER.papers, ...paperTierDetail(args.paper, args.figure)].join(" · "), badge: { text: "machine-read abstract", tone: "unverified" } });
    rows.push({ label: "Not the same as", text: "A genome-surveillance count or a graph extraction. A figure stated in an abstract comes from that paper’s own design and is never pooled." });
    return rows;
  }
  if (e.source === "graph") {
    rows.push({ label: "Evidence tier", text: [EVIDENCE_TIER.graph, ...graphTierDetail(args.graphFinding)].join(" · ") });
    return rows;
  }
  if (!ctx) return rows;
  const meta = args.pack.studyContext?._meta;
  const src: ReceiptLink[] = meta?.url ? [{ label: "MalariaGEN Pf8 sample metadata", url: meta.url }] : [];
  rows.push({ label: "Evidence tier", text: `${ctx.tier} · ${ctx.tierDetail}`, links: src });
  const c = ctx.cell;
  if (c) {
    for (const s of c.studies) {
      rows.push({
        label: "Partner study",
        text: `${s.study_id} · ${s.k}/${s.n} (${s.pct}%) · ${s.admin1.map((a) => `${a.name} ${a.k}/${a.n}`).join(", ")} · ${methodText(s.dna_method)}${s.median_callable_pct != null ? ` · median ${s.median_callable_pct}% callable` : ""}`,
      });
    }
    if (ctx.geo) rows.push({ label: "Geographic scope", text: ctx.geo.text, badge: ctx.geo.flag ? { text: ctx.geo.flag, tone: "preset" } : undefined });
    if (ctx.measure) {
      const names = ctx.measure.all.map(([m]) => m);
      rows.push({
        label: "DNA preparation",
        text: `All samples: ${methodText(c.dna_method_all)}.${c.k > 0 ? ` Carrying ${args.marker.mutation}: ${methodText(c.dna_method_mutants)}.` : ""}${ctx.measure.note ? ` ${ctx.measure.note}` : ""} ${glossaryText(args.pack.studyContext, names)}`.trim(),
      });
      rows.push({ label: "Genome callability", text: `${ctx.measure.callable}.` });
    }
    if (ctx.codon) {
      rows.push({ label: "Codon 540 calls", text: ctx.codon.text });
      if (ctx.codon.altWarning) rows.push({ label: "Warning", text: ctx.codon.altWarning, badge: { text: "Alternative codon-540 allele", tone: "preset" } });
    }
    if (ctx.runs.length) {
      rows.push({
        label: "Raw reads",
        text: `Sequencing runs for ${ctx.runs.length} sample${ctx.runs.length === 1 ? "" : "s"} carrying ${args.marker.mutation}: ${ctx.runs.map((r) => `${r.sample} (${r.dna_method}, ${r.admin1}${r.callable_pct != null ? `, ${r.callable_pct}% callable` : ""})`).join("; ")}.`,
        links: ctx.runs.map((r) => ({ label: `ENA ${r.ena}`, url: enaUrl(r.ena as string) })),
      });
    }
  }
  rows.push({ label: "Local prior", text: ctx.prior.detail, badge: { text: ctx.prior.label, tone: ctx.prior.kind === "zero" ? "preset" : "checked" } });
  rows.push({
    label: "Cutoff | observed",
    text: `Cutoff: ${ctx.cutoff.text} | Observed: ${ctx.observed}.${ctx.relation ? ` ${ctx.relation}` : ""}`,
    badge: ctx.cutoff.published ? { text: "Published by WHO", tone: "who" } : { text: "Project rule or preset", tone: "preset" },
  });
  rows.push({ label: "Next steps", text: `${ctx.prior.steps.map((s, i) => `${i + 1}) ${s}`).join(" ")} ${NEXT_STEPS_NOTE}` });
  for (const f of args.matched ?? []) {
    const p = args.papers?.get(pmidStr(f.pmid));
    rows.push({
      label: "Same place, same years",
      text: `${EVIDENCE_TIER.papers}: ${p?.title ?? "title not recorded"}${f.site ? ` · site: ${f.site}` : ""}${f.population ? ` · population: ${f.population}` : ""} · “${f.quote}” Shown beside the genome count, never pooled with it.`,
      links: [{ label: `PMID ${pmidStr(f.pmid)}`, url: p?.url ?? pubmedUrl(pmidStr(f.pmid)) }],
      badge: { text: "machine-read abstract", tone: "unverified" },
    });
  }
  return rows;
}

/* --------------------------------------------------------------- receipt --- */

export type ReceiptLink = { label: string; url: string };
export type ReceiptRow = { label: string; text: string; links?: ReceiptLink[]; badge?: { text: string; tone: "who" | "preset" | "checked" | "unverified" } };
export type ReceiptSection = { title: string; rows: ReceiptRow[] };

export function buildReceipt(args: {
  e: AlertEvent;
  watch: Watch;
  basis: WhoBasis;
  marker: MarkerDef;
  country: string;
  pack: ClientPack;
  paper?: Paper;
  figure?: AbstractPrevalence;
  thresholdPublished: boolean;
  thresholdText: string;
  stakes: Stakes;
  extracted: GraphFinding[];
  graphFinding?: GraphFinding;
  /** Genome alerts: the triggering-study context joined from the Pf8 sample metadata. */
  ctx?: GenomeContext | null;
  /** Abstract figures whose stated place and collection years cover this cell. Shown beside it, never pooled. */
  matched?: AbstractPrevalence[];
  papers?: Map<string, Paper>;
}): ReceiptSection[] {
  const { e, pack, marker, country } = args;
  const who = pack.thresholds.who_categories?.sources?.[0];
  const whoLink: ReceiptLink = { label: who?.name ?? SOURCES.whoFallback.label, url: who?.url ?? SOURCES.whoFallback.url };
  const concept = (id: string | null | undefined) => {
    if (!id) return null;
    const c = pack.graph.concepts.find((x) => x.system_id === id);
    return c ? `${c.label} ${id}` : id;
  };

  /* 1. surveillance math */
  const math: ReceiptRow[] = [];
  if (e.cell) {
    math.push({ label: "This cell", text: `${frac(e.cell)} carrying / tested · ${pct(e.cell.pct)} · Wilson ${ci(e.cell)} · ${country} · collected ${e.cell.year}` });
    if (e.prev) math.push({ label: "Compared with", text: `${frac(e.prev)} · ${pct(e.prev.pct)} · Wilson ${ci(e.prev)} · collected ${e.prev.year}` });
    if (e.a581g) math.push({ label: "A581G, same cell", text: `${frac(e.a581g)} · ${pct(e.a581g.pct)} · Wilson ${ci(e.a581g)}` });
    else if (e.a581gUnjudged) math.push({ label: "A581G, same cell", text: "not tested, or under the minimum: “very high” cannot be judged" });
    math.push({ label: "Dataset", text: "Genome counts by country and collection year; convenience samples; intervals computed here.", links: [SOURCES.pf8] });
  } else if (args.graphFinding) {
    const f = args.graphFinding;
    math.push({ label: "Graph finding", text: `${pairText(f)}. ${statText(f) ?? ""}`.trim() });
    if (f.pubmed_id) math.push({ label: "Paper", text: `${f.paper_title ?? ""} ${f.journal ?? ""} ${f.pub_year ?? ""}`.trim(), links: [{ label: `PMID ${f.pubmed_id}`, url: f.pubmed_url ?? pubmedUrl(pmidStr(f.pubmed_id)) }] });
  } else if (e.pmid) {
    if (e.quote) math.push({ label: "Abstract quote", text: `“${e.quote}”` });
    const fig = args.figure;
    if (fig) {
      const bits = [
        fig.prevalence_pct != null ? `${fig.prevalence_pct}% as stated` : null,
        fig.numerator != null && fig.denominator != null ? `${fig.numerator} of ${fig.denominator}` : null,
        fig.site ? `site: ${fig.site}` : null,
        fig.year_start ? `collected ${fig.year_start}${fig.year_end && fig.year_end !== fig.year_start ? ` to ${fig.year_end}` : ""}` : null,
        fig.population ? `population: ${fig.population}` : null,
      ].filter(Boolean);
      if (bits.length) math.push({ label: "As stated", text: bits.join(" · ") });
    }
    math.push({
      label: "Paper",
      text: `${args.paper?.title ?? ""} ${args.paper?.journal ?? ""}, published ${args.paper?.pub_year ?? e.year}. Machine-read, quote-verified, not checked by hand.`.trim(),
      links: [{ label: `PMID ${e.pmid}`, url: args.paper?.url ?? pubmedUrl(e.pmid) }],
    });
  }

  /* 2. triggering-study context */
  const study = studyRows(args);

  /* 3. threshold authority */
  const authority: ReceiptRow[] = [];
  if (e.source !== "genomes") {
    authority.push({ label: "Threshold", text: "None applied: this item is dated evidence quoted from a paper or held by the graph, not a threshold decision." });
  } else if (args.thresholdPublished) {
    authority.push({
      label: "Band cut-offs",
      text: "WHO SP-resistance categories, East and Southern Africa: PDF page 105.",
      links: [whoLink],
      badge: { text: "Published by WHO", tone: "who" },
    });
  } else {
    authority.push({ label: "Threshold", text: `${args.thresholdText}.`, badge: { text: PRESET_BADGE, tone: "preset" } });
  }
  if (args.basis === "east_southern_africa") {
    authority.push({
      label: "Continuing IPTp-SP",
      text: "WHO: SP in pregnancy should continue to be used in areas of high SP resistance: PDF pages 104 and 107–108.",
      links: [whoLink],
    });
  }

  /* 4. graph and literature ids */
  const ids: ReceiptRow[] = [];
  const row = (f: GraphFinding, label: string, lead?: string): ReceiptRow => ({
    label,
    text: [
      lead ?? null,
      `system_id ${f.system_id}`,
      f.study_id ? `study_id ${f.study_id}` : null,
      [concept(f.variable_1_concept_id), concept(f.variable_2_concept_id)].filter(Boolean).join(" | ") || null,
    ]
      .filter(Boolean)
      .join(" · "),
    links: f.pubmed_id ? [{ label: `PMID ${f.pubmed_id}`, url: f.pubmed_url ?? pubmedUrl(pmidStr(f.pubmed_id)) }] : undefined,
    badge: f.source_checked ? { text: TIER.checked, tone: "checked" } : { text: TIER.unverified, tone: "unverified" },
  });
  if (args.graphFinding) ids.push(row(args.graphFinding, "This finding"));
  for (const f of args.stakes.lead) if (f !== args.graphFinding) ids.push(args.stakes.local.includes(f) ? row(f, "Haplotype finding", country) : row(f, "Stakes finding", f.use ?? "SP"));
  for (const f of args.extracted.slice(0, 4)) ids.push(row(f, "Extracted", "from this paper"));
  const drug = pack.graph.concepts.filter((c) => /^(sulfadoxine|pyrimethamine)$/i.test(c.label));
  if (drug.length) ids.push({ label: "Drug concepts", text: drug.map((c) => `${c.label} ${c.system_id}`).join(" · ") });
  ids.push({
    label: "Marker in graph",
    text: `No graph finding names ${marker.mutation} on its own (${pack.literature.papers.filter((p) => p.in_graph).length} of ${pack.literature.papers.length} ${marker.mutation} papers read).`,
    links: [SOURCES.graph],
  });

  return [
    { title: "Surveillance math", rows: math },
    { title: "Triggering study: scope, method and bar for action", rows: study },
    { title: "Threshold authority", rows: authority },
    { title: "System Graph and literature IDs", rows: ids },
  ];
}

/* ----------------------------------------------------------------- email --- */

export type EmailList = { title: string; note?: string; items: { text: string; link?: ReceiptLink }[] };

/** Digest layers added to an alert email: live graph check, recent papers, curation queue, deep links. */
export type EmailExtras = {
  /** Added inside the subject's source tag, e.g. "Live System Graph". */
  subjectTag?: string;
  /** Papers published since the cell was collected. Shown beside the count, never pooled. */
  recent?: EmailList;
  /** What the live System API said just now, including the quarantine count. */
  graphLive?: string[];
  /** Unread papers for the country: the curation queue. */
  queue?: EmailList;
  /** Per finding id: the result of the live check, e.g. "live check: matches snapshot". */
  liveChecked?: Record<string, string>;
  links?: ReceiptLink[];
};

export type EmailParts = {
  e: AlertEvent;
  copy: EventCopy;
  watchText: string;
  marker: string;
  country: string;
  stakesIntro: string;
  stakes: GraphFinding[];
  stakesCaveat: string;
  graphLine: string;
  whoStatus: string[];
  receipt: ReceiptSection[];
  /** Subject line: evidence source, study scope and assay first. */
  subject: string;
  /** How much weight to give the signal: tier, flags, cutoff beside observed, next steps. */
  weight: { tier: string; lines: { label: string; text: string; warn?: boolean }[]; steps: string[]; stepsNote: string | null };
  /** Three or four lines under the headline: observed, cutoff, prior, scope. */
  glance?: string[];
  limits: string[];
  link: string;
  asOf: string;
  extras?: EmailExtras;
};

const esc = (s: string) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

/* Email colours. Gmail and Apple Mail drop <style> blocks and <body> backgrounds, so every
 * background and text colour is set inline on the table cell or element that needs it. */
const C = { page: "#050d17", card: "#0d2233", panel: "#16344a", line: "#2a4558", fg: "#f5f4ef", body: "#dfe5ea", muted: "#b0bdcb", link: "#8ff0dc", warn: "#f2bd76" } as const;
const SANS = "-apple-system,'Segoe UI',Helvetica,Arial,sans-serif";
const MONO = "ui-monospace,Menlo,Consolas,monospace";

export function buildEmail(a: EmailParts): { subject: string; text: string; html: string } {
  const { e, copy } = a;
  const x = a.extras ?? {};
  const subject = x.subjectTag ? a.subject.replace(/\]/, ` + ${x.subjectTag}]`) : a.subject;
  const meta = `${KIND_LABEL[e.kind]} · ${SOURCE_LABEL[e.source]} · ${e.dateBasis === "collection" ? "collected" : "published"} ${e.year}${e.fired ? "" : " · context, not an alert"}`;
  const live = (f: GraphFinding) => x.liveChecked?.[f.system_id];
  const tierOf = (f: GraphFinding) => `${f.source_checked ? TIER.checked : TIER.unverified}${live(f) ? `; ${live(f)}` : ""}`;
  const stakeLine = (f: GraphFinding) =>
    `[${f.study_type ?? NO_STUDY_TYPE}] ${pairText(f)}. ${statText(f) ?? ""} Population: ${f.population ?? "not given by the graph"} [system_id ${f.system_id}; ${tierOf(f)}${f.pubmed_id ? `; ${f.pubmed_url ?? pubmedUrl(pmidStr(f.pubmed_id))}` : ""}]`;
  const listText = (l: EmailList | undefined, heading: string) =>
    l && l.items.length ? ["", heading, l.title, ...l.items.map((i) => `- ${i.text}${i.link ? ` ${i.link.label} <${i.link.url}>` : ""}`), ...(l.note ? [l.note] : [])] : [];

  const text = [
    `Subject: ${subject}`,
    "",
    `Your watch: ${a.watchText}`,
    "",
    copy.title.toUpperCase(),
    meta,
    ...(a.glance?.length ? ["", "AT A GLANCE", ...a.glance.map((g) => `- ${g}`)] : []),
    "",
    "WHAT CHANGED",
    copy.statement,
    `Comparison basis: ${copy.basis}`,
    "",
    "HOW MUCH WEIGHT TO GIVE THIS: THE TRIGGERING STUDY",
    `Evidence tier: ${a.weight.tier}`,
    ...a.weight.lines.map((l) => `${l.warn ? "! " : "- "}${l.label}: ${l.text}`),
    ...(a.weight.steps.length ? ["Next steps a reviewer would look for:", ...a.weight.steps.map((s, i) => `  ${i + 1}. ${s}`), a.weight.stepsNote ?? ""] : []),
    ...listText(x.recent, "PUBLISHED SINCE THIS COLLECTION"),
    "",
    "WHY IT MATTERS (ACCORDING TO THE SYSTEM GRAPH)",
    a.stakesIntro,
    ...a.stakes.map((f) => `- ${stakeLine(f)}`),
    a.stakesCaveat,
    "",
    "WHAT THE SYSTEM GRAPH HAS ON IT",
    a.graphLine,
    ...(x.graphLive ?? []).map((l) => `- ${l}`),
    ...listText(x.queue, "CURATION QUEUE: NOT YET READ BY THE GRAPH"),
    "",
    "WHO STATUS OF THE MARKER",
    ...a.whoStatus,
    "",
    "DECISION RECEIPT",
    ...a.receipt.flatMap((s) => [
      `${s.title}:`,
      ...s.rows.map((r) => `  ${r.label}: ${r.text}${r.badge ? ` [${r.badge.text}]` : ""}${r.links?.length ? ` ${r.links.map((l) => `${l.label} <${l.url}>`).join(" ")}` : ""}`),
    ]),
    "",
    "WHAT THIS ALERT CANNOT TELL YOU",
    ...a.limits.map((s) => `- ${s}`),
    "",
    `Open this alert: ${a.link}`,
    ...(x.links ?? []).map((l) => `${l.label}: ${l.url}`),
    "",
    `${a.asOf} A replay of the historical record: not live surveillance, not clinical guidance.`,
  ].join("\n");

  /* HTML: tables with inline colours on every cell, so it reads the same in Gmail, Apple Mail and Outlook. */
  const h = (t: string) =>
    `<p style="font:700 11px/1.4 ${SANS};letter-spacing:.12em;text-transform:uppercase;color:${C.muted};margin:24px 0 8px;padding-top:14px;border-top:1px solid ${C.line}">${esc(t)}</p>`;
  const para = (t: string, color: string = C.body) => `<p style="margin:0 0 8px;color:${color}">${esc(t)}</p>`;
  const small = (t: string) => `<p style="margin:0 0 8px;color:${C.muted};font-size:13px">${esc(t)}</p>`;
  const link = (l: ReceiptLink) => `<a href="${esc(l.url)}" style="color:${C.link};text-decoration:underline">${esc(l.label)}</a>`;
  const pill = (t: string, color: string = C.muted) =>
    `<span style="display:inline-block;border:1px solid ${color};color:${color};border-radius:9px;padding:0 7px;font-size:11px;line-height:17px;white-space:nowrap">${esc(t)}</span>`;
  const list = (l: EmailList | undefined, heading: string) =>
    l && l.items.length
      ? `${h(heading)}${para(l.title)}<ul style="margin:0 0 8px;padding-left:18px;color:${C.body}">${l.items
          .map((i) => `<li style="margin-bottom:6px;color:${C.body}">${esc(i.text)}${i.link ? ` ${link(i.link)}` : ""}</li>`)
          .join("")}</ul>${l.note ? small(l.note) : ""}`
      : "";
  const cell = `padding:6px 9px;border-top:1px solid ${C.line};background-color:${C.card};vertical-align:top;font-size:12.5px;line-height:1.5`;

  const html = `<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="${C.page}" style="background-color:${C.page};margin:0;padding:0"><tr><td align="center" bgcolor="${C.page}" style="background-color:${C.page};padding:16px 8px">
<table role="presentation" width="640" cellpadding="0" cellspacing="0" border="0" bgcolor="${C.card}" style="background-color:${C.card};max-width:640px;width:100%;border:1px solid ${C.line};border-radius:9px"><tr><td bgcolor="${C.card}" style="background-color:${C.card};color:${C.body};font:15px/1.55 ${SANS};padding:20px">
<p style="font:12px ${MONO};color:${C.muted};margin:0 0 6px">${esc(a.watchText)}</p>
<p style="font:11px ${MONO};color:${C.link};margin:0 0 4px">${esc(subject.match(/^\[[^\]]*\]/)?.[0] ?? "")}</p>
<h2 style="font:700 22px/1.25 ${SANS};color:${C.fg};margin:4px 0 6px">${esc(`${a.marker}, ${a.country}: ${copy.title}`)}</h2>
<p style="font:12px ${MONO};color:${C.warn};margin:0 0 10px">${esc(meta)}</p>
${
  a.glance?.length
    ? `<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="${C.panel}" style="background-color:${C.panel};border-radius:7px"><tr><td bgcolor="${C.panel}" style="background-color:${C.panel};color:${C.fg};padding:10px 14px;font:14px/1.6 ${SANS}">${a.glance
        .map((g, i) => `<div style="color:${C.fg};${i === 0 ? "font-weight:700;font-size:16px" : ""}">${esc(g)}</div>`)
        .join("")}</td></tr></table>`
    : ""
}
${h("What changed")}
${para(e.quote ? copy.statement.split(" Its abstract says:")[0] : copy.statement, C.fg)}
${e.quote ? `<p style="margin:0 0 8px;padding:2px 0 2px 12px;border-left:3px solid ${C.muted};color:${C.fg}">“${esc(e.quote)}”</p>` : ""}
<p style="margin:0 0 8px;color:${C.muted};font-size:13px"><strong style="color:${C.fg}">Comparison basis.</strong> ${esc(copy.basis)}</p>
${h("How much weight to give this: the triggering study")}
<p style="margin:0 0 10px;color:${C.link}">${pill(a.weight.tier, C.link)}</p>
${a.weight.lines
  .map(
    (l) =>
      `<p style="margin:0 0 7px;font-size:13.5px;color:${C.body};${l.warn ? `border-left:3px solid ${C.warn};padding-left:9px` : ""}"><strong style="color:${l.warn ? C.warn : C.fg}">${l.warn ? "⚠ " : ""}${esc(l.label)}.</strong> ${esc(l.text)}</p>`,
  )
  .join("")}
${
  a.weight.steps.length
    ? `<p style="margin:10px 0 4px;font-size:13px;color:${C.fg}"><strong style="color:${C.fg}">Next steps a reviewer would look for</strong></p><ol style="margin:0 0 6px;padding-left:20px;font-size:13px;color:${C.body}">${a.weight.steps
        .map((s) => `<li style="color:${C.body}">${esc(s)}</li>`)
        .join("")}</ol><p style="margin:0 0 8px;color:${C.muted};font-size:12px">${esc(a.weight.stepsNote ?? "")}</p>`
    : ""
}
${list(x.recent, "Published since this collection")}
${h("Why it matters, according to the System graph")}
${para(a.stakesIntro)}
<ul style="margin:0 0 8px;padding-left:18px;color:${C.body}">${a.stakes
    .map(
      (f) =>
        `<li style="margin-bottom:8px;color:${C.body}">${pill(f.study_type ?? NO_STUDY_TYPE, f.study_type ? C.fg : C.muted)} ${esc(pairText(f))}. <strong style="color:${C.fg}">${esc(statText(f) ?? "")}</strong><br><span style="color:${C.muted}">Population: ${esc(f.population ?? "not given by the graph")}</span><br><span style="font:11px ${MONO};color:${C.muted}">system_id ${esc(f.system_id)} · ${esc(tierOf(f))}${
          f.pubmed_id ? ` · ${link({ label: `PMID ${f.pubmed_id}`, url: f.pubmed_url ?? pubmedUrl(pmidStr(f.pubmed_id)) })}` : ""
        }</span></li>`,
    )
    .join("")}</ul>
${small(a.stakesCaveat)}
${h("What the System graph has on it")}
${para(a.graphLine)}
${(x.graphLive ?? []).map((l) => `<p style="margin:0 0 6px;font-size:13.5px;color:${C.body};border-left:3px solid ${C.link};padding-left:9px">${esc(l)}</p>`).join("")}
${list(x.queue, "Curation queue: not yet read by the graph")}
${h("WHO status of the marker")}
${a.whoStatus.map((s) => `<p style="margin:0 0 8px;color:${C.body};word-break:break-word">${esc(s)}</p>`).join("")}
${h("Decision receipt")}
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="${C.card}" style="background-color:${C.card};border:1px solid ${C.line};border-collapse:collapse">${a.receipt
    .map(
      (s) =>
        `<tr><td colspan="2" bgcolor="${C.panel}" style="background-color:${C.panel};color:${C.fg};padding:6px 9px;font:700 11px ${SANS};letter-spacing:.08em;text-transform:uppercase">${esc(s.title)}</td></tr>` +
        s.rows
          .map(
            (r) =>
              `<tr><td width="112" bgcolor="${C.card}" style="${cell};color:${C.muted}">${esc(r.label)}</td><td bgcolor="${C.card}" style="${cell};color:${C.body};word-break:break-word">${esc(r.text)}${r.badge ? ` ${pill(r.badge.text)}` : ""}${
                r.links?.length ? ` ${r.links.map(link).join(" · ")}` : ""
              }</td></tr>`,
          )
          .join(""),
    )
    .join("")}</table>
${h("What this alert cannot tell you")}
<ul style="margin:0 0 8px;padding-left:18px;color:${C.muted};font-size:13px">${a.limits.map((l) => `<li style="color:${C.muted}">${esc(l)}</li>`).join("")}</ul>
<p style="margin:18px 0 6px;color:${C.body}">${[{ label: "Open this alert", url: a.link }, ...(x.links ?? [])].map(link).join(" &nbsp;·&nbsp; ")}</p>
<p style="font-size:12px;color:${C.muted};margin:0">${esc(a.asOf)} A replay of the historical record: not live surveillance, not clinical guidance.</p>
</td></tr></table>
</td></tr></table>`;

  return { subject, text, html };
}
