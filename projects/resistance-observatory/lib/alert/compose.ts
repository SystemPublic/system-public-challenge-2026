/**
 * Everything an alert's inspector and its email are built from, composed in
 * one place so the on-screen alert, the per-alert email and the test digest
 * can never disagree. Pure: templates filled from the pack, no language model.
 */
import type { AlertEvent, Cell, Watch, WhoBasis } from "./derive";
import { EVIDENCE_TIER, NEXT_STEPS_NOTE, genomeContext, genomeSubject, itemSubject, matchingFigures, methodText } from "./context";
import { eventCopy, limits, thresholdBasis, watchSentence } from "./copy";
import { pmidStr, type AbstractPrevalence, type ClientPack, type GraphFinding, type MarkerDef, type Paper } from "./pack";
import { SOURCES, TIER, buildEmail, buildReceipt, graphTierDetail, paperTierDetail, pickStakes, type EmailExtras } from "./receipt";

export type ComposeArgs = {
  e: AlertEvent;
  watch: Watch;
  marker: MarkerDef;
  country: string;
  basis: WhoBasis;
  pack: ClientPack;
  /** Every genome cell for the marker, any country. */
  cells: Cell[];
  papers: Map<string, Paper>;
};

export function composeAlert({ e, watch, marker, country, basis, pack, cells, papers }: ComposeArgs) {
  const copy = eventCopy(e, watch, marker.label, country);
  const tb = thresholdBasis(watch, basis);
  const lim = limits(e, basis, marker.label, marker.drugShort);
  const paper = e.pmid ? papers.get(e.pmid) : undefined;
  const figure: AbstractPrevalence | undefined =
    e.rule === "abstract_figure" ? pack.literature.abstract_prevalence.find((f) => pmidStr(f.pmid) === e.pmid && f.quote === e.quote) : undefined;

  const stakes = pickStakes(pack, watch.area, basis);

  /* what the graph has on it */
  const extracted: GraphFinding[] = e.pmid ? pack.graph.findings_from_k540e_papers.filter((f) => pmidStr(f.pubmed_id) === e.pmid) : [];
  const graphFinding = e.graphFindingId ? pack.graph.haplotype_findings.find((f) => f.system_id === e.graphFindingId) : undefined;
  const countryPapers = pack.literature.papers.filter((x) => (x.countries_iso3 ?? []).includes(watch.area));
  const countryInGraph = countryPapers.filter((x) => x.in_graph);

  let graphLine: string;
  if (graphFinding) {
    graphLine = `The graph holds this finding (system_id ${graphFinding.system_id}) on a haplotype that contains ${marker.mutation}. ${graphFinding.source_checked ? TIER.checked : TIER.unverified}.`;
  } else if (e.pmid) {
    graphLine = paper?.in_graph
      ? `The graph has read this paper (PMID ${e.pmid}) and extracted ${extracted.length} finding${extracted.length === 1 ? "" : "s"} from it. None names ${marker.mutation} on its own.`
      : `The graph has not read this paper (PMID ${e.pmid}). It is in the ready-to-ingest queue below.`;
  } else if (stakes.local.length > 0) {
    graphLine = `The graph has ${stakes.local.length} finding${stakes.local.length === 1 ? "" : "s"} from ${country} on a haplotype containing ${marker.mutation} (shown in the stakes chain). It holds no genome counts, so this change comes from the genome data alone.`;
  } else {
    graphLine = `The graph has no finding that bears on this. It has read ${countryInGraph.length} of the ${countryPapers.length} ${marker.mutation} papers that name ${country}, and it holds no genome counts.`;
  }

  /* WHO status and wording */
  const th = pack.thresholds;
  const whoStatus = [th.marker?.who_classification_alone ? `${marker.mutation} alone: ${th.marker.who_classification_alone}.` : null, th.marker?.who_classification_haplotype ? `${th.marker.who_classification_haplotype}.` : null].filter(
    (x): x is string => Boolean(x),
  );
  const v = th.who_categories?.verbatim;
  const whoSource = pack.thresholds.who_categories?.sources?.[0] ?? { name: SOURCES.whoFallback.label, url: SOURCES.whoFallback.url };
  const esa = basis === "east_southern_africa";
  const emailWho = esa && v?.continue_quote ? [...whoStatus, `WHO on SP in pregnancy: “${v.continue_quote}” (${v.continue_where})`] : whoStatus;

  /* triggering-study context: scope, method, local prior, cutoff beside observed */
  const ctx = genomeContext({ e, watch, basis, cells: cells, study: pack.studyContext, country, mutation: marker.mutation });
  const matched = ctx && e.cell ? matchingFigures(pack.literature.abstract_prevalence, watch.area, e.cell.year) : [];
  const itemDetail = e.source === "papers" ? paperTierDetail(paper, figure) : e.source === "graph" ? (graphFinding ? graphTierDetail(graphFinding) : ["a paper the graph has read; what it extracted is listed below"]) : [];
  const subject = ctx
    ? genomeSubject({ e, ctx, country, mutation: marker.mutation, drugShort: marker.drugShort })
    : itemSubject({
        tier: e.source === "papers" ? `${EVIDENCE_TIER.papers}, machine-read abstract` : EVIDENCE_TIER.graph,
        scope: itemDetail,
        country,
        mutation: marker.mutation,
        drugShort: marker.drugShort,
        title: copy.title,
        fired: e.fired,
      });
  const weight = ctx
    ? {
        tier: `${ctx.tier} · ${ctx.tierDetail}`,
        lines: [
          ...ctx.flags.map((f) => ({ label: f.label, text: f.text, warn: f.tone === "warn" })),
          ...(ctx.cell
            ? [
                { label: "Partner studies", text: ctx.cell.studies.map((s) => `${s.study_id} ${s.k}/${s.n} (${s.pct}%)`).join("; ") },
                ...(ctx.geo && !ctx.geo.flag ? [{ label: "Geographic scope", text: ctx.geo.text }] : []),
                {
                  label: "DNA preparation",
                  text: `all samples ${methodText(ctx.cell.dna_method_all)}${ctx.cell.k > 0 ? `; carrying ${marker.mutation} ${methodText(ctx.cell.dna_method_mutants)}` : ""}. ${ctx.measure?.note ?? ""} Genome callability: ${ctx.measure?.callable}.`,
                },
                { label: "Codon 540 calls", text: ctx.codon?.text ?? "" },
              ]
            : []),
          { label: "Cutoff", text: ctx.cutoff.text },
          { label: "Observed", text: `${ctx.observed}.${ctx.relation ? ` ${ctx.relation}` : ""}` },
        ],
        steps: ctx.prior.steps,
        stepsNote: NEXT_STEPS_NOTE,
      }
    : { tier: e.source === "papers" ? EVIDENCE_TIER.papers : EVIDENCE_TIER.graph, lines: itemDetail.map((d) => ({ label: d.split(": ")[0], text: d.split(": ").slice(1).join(": ") || d })), steps: [], stepsNote: null };

  const receipt = buildReceipt({
    e,
    watch,
    basis,
    marker,
    country,
    pack,
    paper,
    figure,
    thresholdPublished: tb.published,
    thresholdText: tb.text,
    stakes,
    extracted,
    graphFinding,
    ctx,
    matched,
    papers: papers,
  });

  const stakesIntro = `${marker.label} is a mutation in the parasite's ${marker.gene} gene associated with reduced susceptibility to sulfadoxine, one half of ${marker.drug}. What the System graph holds on ${marker.drugShort} and on haplotypes containing ${marker.mutation}:`;
  const stakesCaveat = `This describes what ${marker.drugShort} achieves and what the haplotype has been associated with. It does not claim that ${marker.mutation} in ${country} will reverse those outcomes.`;

  /* at a glance: observed beside the cutoff, the prior, the scope flag */
  const glance = ctx
    ? [`Observed: ${ctx.observed}`, `Watch cutoff: ${ctx.cutoff.short}${ctx.relation ? `. ${ctx.relation}` : ""}`, ctx.prior.label, ...(ctx.geo?.flag ? [`${ctx.geo.flag}${ctx.geo.site ? `: ${ctx.geo.site}` : ""}`] : []), ...(ctx.codon?.altWarning ? ["Alternative codon-540 allele (K540N) present"] : [])]
    : [];
  const policyRef = `Policy reference: ${whoSource.name}. SP-resistance categories: PDF page 105; continuing IPTp-SP: PDF pages 104 and 107–108. ${
    esa ? "" : "WHO does not grade this region by K540E, so any line used here is this project’s preset. "
  }${whoSource.url}`;

  return { copy, tb, lim, paper, figure, stakes, extracted, graphFinding, graphLine, whoStatus, emailWho: [...emailWho, policyRef], ctx, matched, itemDetail, subject, weight, receipt, stakesIntro, stakesCaveat, glance };
}

export type Composed = ReturnType<typeof composeAlert>;

/** The email for a composed alert. `extras` adds the digest layers (live graph check, recent papers, queue, links). */
export function composeEmail(c: Composed, a: Pick<ComposeArgs, "e" | "watch" | "marker" | "country"> & { link: string; asOf: string; extras?: EmailExtras }) {
  return buildEmail({
    e: a.e,
    copy: c.copy,
    watchText: watchSentence(a.watch, a.marker.label, a.country),
    marker: a.marker.label,
    country: a.country,
    stakesIntro: c.stakesIntro,
    stakes: c.stakes.lead,
    stakesCaveat: c.stakesCaveat,
    graphLine: c.graphLine,
    whoStatus: c.emailWho,
    receipt: c.receipt,
    subject: c.subject,
    weight: c.weight,
    glance: c.glance,
    limits: c.lim,
    link: a.link,
    asOf: a.asOf,
    extras: a.extras,
  });
}
