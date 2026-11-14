"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import {
  countryCells,
  deriveAlerts,
  firedCount,
  type AlertEvent,
  type Trigger,
  type Watch,
  type WhoBasis,
} from "@/lib/alert/derive";
import { KIND_LABEL, SOURCE_LABEL, TRIGGER_LABEL, eventCopy, thresholdBasis, watchSentence } from "@/lib/alert/copy";
import { markerFromUrlId, pmidStr, toAlertData, type ClientPack, type Paper } from "@/lib/alert/pack";
import { EvidenceChart } from "./EvidenceChart";
import { Timeline, type GraphTick, type PaperTick, type WhoYear } from "./Timeline";
import { GraphPanel, type ConceptRef } from "./GraphPanel";
import { AlertDetail } from "./AlertDetail";
import { CountryPicker, type CountryRow } from "./CountryPicker";
import { CurationQueue } from "./CurationQueue";
import { SendTestAlert } from "./SendTestAlert";
import { GRAPH_RELEASE } from "@/lib/alert/receipt";
import { RULE_TRIGGER, eventIdFor, getDefaultMapAlerts } from "@/lib/alert/mapAlerts";
import { EVIDENCE_TIER, NO_STUDY_TYPE, assayKeywords, geoScope, localPrior, methodText, studyCellFor } from "@/lib/alert/context";
import { KindGlyph, SourceGlyph, SOURCE_TONE } from "./glyphs";
import css from "./alert.module.css";

/* ---------------------------------------------------------- watch state --- */

const TRIG_CODE: Record<Trigger, string> = {
  who_band: "band",
  rise: "rise",
  fall: "fall",
  change: "change",
  first_detection: "first",
  very_high_combo: "combo",
};
const CODE_TRIG = Object.fromEntries(Object.entries(TRIG_CODE).map(([k, v]) => [v, k])) as Record<string, Trigger>;

type Defaults = Pick<Watch, "trigger" | "level" | "points" | "minN">;

/** Defaults follow the region. Lines outside East and Southern Africa are the pack's presets: ours, not WHO's. */
function defaultsFor(basis: WhoBasis, presets: ClientPack["thresholds"]["presets"]): Defaults {
  const minN = presets?.min_samples ?? 20;
  const points = presets?.change_points ?? 20;
  if (basis === "east_southern_africa") return { trigger: "who_band", level: 60, points, minN };
  if (basis === "central_west_africa") return { trigger: "first_detection", level: presets?.central_west_africa?.threshold_pct ?? 5, points, minN };
  return { trigger: "change", level: presets?.outside_africa?.threshold_pct ?? 50, points, minN };
}

const BASIS_LABEL: Record<WhoBasis, string> = {
  east_southern_africa: "East and Southern Africa",
  central_west_africa: "Central and West Africa",
  outside_africa: "Outside Africa",
};

type Example = { label: string; note: string; qs: Record<string, string> };
const EXAMPLES: Example[] = [
  { label: "Kenya · WHO bands", note: "climbs from the low band to near-universal", qs: { area: "KEN", trig: "band" } },
  { label: "Tanzania · “very high” combination", note: "holds, then lapses when A581G falls", qs: { area: "TZA", trig: "combo" } },
  { label: "DR Congo · emergence", note: "rising where it was once absent", qs: { area: "COD", trig: "rise", level: "20" } },
  { label: "Vietnam · falling", note: "a marker in retreat", qs: { area: "VNM", trig: "fall", level: "50" } },
];

type Saved = { name: string; qs: string };

const WATCH_PARAMS = ["area", "trig", "level", "pts", "n"] as const;

/* ------------------------------------------------------------ component --- */

export function AlertTab({ pack }: { pack: ClientPack }) {
  const router = useRouter();
  const pathname = usePathname();
  const sp = useSearchParams();
  const marker = markerFromUrlId(sp.get("marker"));

  /* countries with data for this marker */
  const rows = pack.genomes.observations[marker.key] ?? [];
  const countryStats = useMemo(() => {
    const m = new Map<string, { cells: number; samples: number; first: number; last: number }>();
    for (const [iso, year, , n] of rows) {
      if (n <= 0) continue;
      const s = m.get(iso) ?? { cells: 0, samples: 0, first: year, last: year };
      s.cells++;
      s.samples += n;
      s.first = Math.min(s.first, year);
      s.last = Math.max(s.last, year);
      m.set(iso, s);
    }
    return m;
  }, [rows]);
  const countryName = useCallback((iso: string) => pack.genomes.countries[iso]?.country ?? iso, [pack.genomes.countries]);
  const isoList = useMemo(
    () => [...countryStats.keys()].sort((a, b) => countryName(a).localeCompare(countryName(b))),
    [countryStats, countryName],
  );

  const paperCounts = useMemo(() => {
    const m = new Map<string, number>();
    for (const p of pack.literature.papers) for (const iso of p.countries_iso3 ?? []) m.set(iso, (m.get(iso) ?? 0) + 1);
    return m;
  }, [pack.literature.papers]);

  const areaParam = (sp.get("area") ?? "").toUpperCase();
  const area = countryStats.has(areaParam) ? areaParam : countryStats.has("KEN") ? "KEN" : (isoList[0] ?? "");
  const basis: WhoBasis = pack.genomes.countries[area]?.who_basis ?? "outside_africa";
  const defaults = defaultsFor(basis, pack.thresholds.presets);
  const intParam = (k: string, lo: number, hi: number) => {
    const v = Number(sp.get(k));
    return sp.get(k) !== null && Number.isFinite(v) ? Math.min(hi, Math.max(lo, v)) : null;
  };
  const watch: Watch = useMemo(
    () => ({
      marker: marker.key,
      area,
      trigger: CODE_TRIG[sp.get("trig") ?? ""] ?? defaults.trigger,
      level: intParam("level", 0, 100) ?? defaults.level,
      points: intParam("pts", 1, 100) ?? defaults.points,
      minN: intParam("n", 1, 1000) ?? defaults.minN,
    }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [sp, marker.key, area, defaults.trigger, defaults.level, defaults.points, defaults.minN],
  );

  const replaceParams = useCallback(
    (mutate: (q: URLSearchParams) => void) => {
      const q = new URLSearchParams(sp.toString());
      mutate(q);
      if (!q.get("marker")) q.set("marker", marker.urlId);
      router.replace(`${pathname}?${q.toString()}`, { scroll: false });
    },
    [sp, router, pathname, marker.urlId],
  );
  const setWatch = (patch: Partial<Record<(typeof WATCH_PARAMS)[number], string | null>>) =>
    replaceParams((q) => {
      for (const [k, v] of Object.entries(patch)) (v === null ? q.delete(k) : q.set(k, v));
      q.delete("finding");
    });
  const setArea = (iso: string) =>
    replaceParams((q) => {
      // a new country starts from its own region's defaults
      for (const k of WATCH_PARAMS) q.delete(k);
      q.set("area", iso);
      q.delete("finding");
    });
  const applyQs = (qs: Record<string, string>) =>
    replaceParams((q) => {
      for (const k of WATCH_PARAMS) q.delete(k);
      for (const [k, v] of Object.entries(qs)) q.set(k, v);
      q.delete("finding");
    });
  const selectedId = sp.get("finding");
  const select = (id: string | null) => replaceParams((q) => (id ? q.set("finding", id) : q.delete("finding")));

  /* write the marker + area into the URL once, so the nav carries them to the other tabs */
  /* incoming /alert?alert=<id> from the Forecast map: rebuild that alert's watch and open its inspector */
  const alertParam = sp.get("alert");
  useEffect(() => {
    if (!alertParam) return;
    const a = getDefaultMapAlerts().find((x) => x.id === alertParam);
    replaceParams((q) => {
      q.delete("alert");
      if (!a) return;
      for (const k of WATCH_PARAMS) q.delete(k);
      q.set("marker", a.marker_id);
      q.set("area", a.country_iso3);
      q.set("trig", TRIG_CODE[RULE_TRIGGER[a.rule] ?? "who_band"]);
      q.set("finding", eventIdFor(a));
    });
    if (a) setTimeout(() => document.getElementById("alert-detail")?.scrollIntoView({ block: "start" }), 400);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [alertParam]);

  useEffect(() => {
    if (alertParam) return;
    if (area && (sp.get("marker") !== marker.urlId || sp.get("area") !== area)) {
      replaceParams((q) => {
        q.set("marker", marker.urlId);
        q.set("area", area);
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [area, marker.urlId, alertParam]);

  const pickerRows: CountryRow[] = useMemo(
    () =>
      isoList.map((iso) => ({
        iso3: iso,
        name: countryName(iso),
        basis: pack.genomes.countries[iso]?.who_basis ?? "outside_africa",
        cells: countryStats.get(iso)?.cells ?? 0,
        qualifying: rows.filter((r) => r[0] === iso && r[3] >= watch.minN).length,
        papers: paperCounts.get(iso) ?? 0,
      })),
    [isoList, countryName, pack.genomes.countries, countryStats, rows, watch.minN, paperCounts],
  );

  /* derivation */
  const data = useMemo(() => toAlertData(marker, pack), [marker, pack]);
  const events = useMemo(() => deriveAlerts(watch, data), [watch, data]);
  const cells = useMemo(() => countryCells(data.cells, area), [data.cells, area]);
  const companion = useMemo(() => countryCells(data.a581g, area), [data.a581g, area]);
  const papers = useMemo(() => new Map<string, Paper>(pack.literature.papers.map((p) => [pmidStr(p.pmid), p])), [pack.literature.papers]);
  const country = countryName(area);

  /* triggering-study context, as short notes for the feed, the timeline hovers and the year under the playhead */
  const cellNote = useCallback(
    (year: number): string => {
      const c = studyCellFor(pack.studyContext, area, year);
      if (!c) return "";
      const alt = c.codon540_breakdown.alt_mutant_540N;
      return `${EVIDENCE_TIER.genomes}: ${c.study_count} stud${c.study_count === 1 ? "y" : "ies"} (${c.studies.map((s) => s.study_id).join(", ")}) · ${geoScope(c, marker.mutation).short.replace(/ \([^)]*\)$/, "")} · ${methodText(c.dna_method_all)}${
        alt > 0 ? ` · K540N also called in ${alt} of ${c.n}` : ""
      }`;
    },
    [pack.studyContext, area, marker.mutation],
  );
  const chipsFor = useCallback(
    (e: AlertEvent): { text: string; warn?: boolean }[] => {
      if (e.source === "papers") {
        const words = assayKeywords(e.pmid ? papers.get(e.pmid)?.title : null);
        return [{ text: EVIDENCE_TIER.papers }, ...(words.length ? [{ text: `title mentions ${words.join(", ")}` }] : [])];
      }
      if (e.source === "graph") {
        const f = e.graphFindingId ? pack.graph.haplotype_findings.find((x) => x.system_id === e.graphFindingId) : undefined;
        return [{ text: EVIDENCE_TIER.graph }, ...(f ? [{ text: f.study_type ?? NO_STUDY_TYPE }] : [])];
      }
      const out: { text: string; warn?: boolean }[] = [{ text: EVIDENCE_TIER.genomes }];
      if (!e.cell) return out;
      const c = studyCellFor(pack.studyContext, area, e.cell.year);
      if (c) {
        const g = geoScope(c, marker.mutation);
        out.push({ text: `${c.study_count} stud${c.study_count === 1 ? "y" : "ies"} · ${methodText(c.dna_method_all)}` });
        if (g.kind === "single_site") out.push({ text: `single-site: ${g.site}`, warn: true });
        if (g.kind === "clustered") out.push({ text: `all positives in ${g.site}`, warn: true });
        if (c.codon540_breakdown.alt_mutant_540N > 0) out.push({ text: `K540N in ${c.codon540_breakdown.alt_mutant_540N} of ${c.n}`, warn: true });
      }
      const prior = localPrior(data.cells, area, e.cell.year);
      out.push({ text: prior.kind === "zero" ? "zero local prior" : "established local prior", warn: prior.kind === "zero" });
      return out;
    },
    [pack.studyContext, pack.graph.haplotype_findings, area, marker.mutation, data.cells, papers],
  );

  /* replay */
  const lastYear = useMemo(
    () => Math.max(...pack.literature.papers.map((p) => p.pub_year), ...rows.map((r) => r[1]), 0),
    [pack.literature.papers, rows],
  );
  const firstPaperYear = useMemo(
    () => (pack.literature.papers.length ? Math.min(...pack.literature.papers.map((p) => p.pub_year)) : (rows.length ? Math.min(...rows.map((r) => r[1])) : lastYear)),
    [pack.literature.papers, rows, lastYear],
  );
  const firstYear = Math.min(cells[0]?.year ?? firstPaperYear, firstPaperYear) - 1;
  const [replayYear, setReplayYear] = useState(lastYear);
  const [playing, setPlaying] = useState(false);
  const [freshYear, setFreshYear] = useState<number | null>(null);
  useEffect(() => {
    setReplayYear(lastYear);
    setPlaying(false);
    setFreshYear(null);
  }, [area, lastYear]);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);
  useEffect(() => {
    if (!playing) return;
    timer.current = setInterval(() => {
      setReplayYear((y) => {
        if (y >= lastYear) {
          setPlaying(false);
          return y;
        }
        setFreshYear(y + 1);
        return y + 1;
      });
    }, 650);
    return () => {
      if (timer.current) clearInterval(timer.current);
    };
  }, [playing, lastYear]);
  const togglePlay = () => {
    if (!playing && replayYear >= lastYear) {
      setReplayYear(firstYear);
      setFreshYear(null);
    }
    setPlaying((p) => !p);
  };

  const [showUnplaced, setShowUnplaced] = useState(false);
  const [feedSource, setFeedSource] = useState<"all" | AlertEvent["source"]>("all");
  const visible = events.filter((e) => e.year <= replayYear);
  const placed = visible.filter((e) => !e.noCountryGiven);
  const unplaced = visible.filter((e) => e.noCountryGiven);
  const feed = [...(showUnplaced ? visible : placed)].filter((e) => feedSource === "all" || e.source === feedSource).sort((a, b) => b.year - a.year || Number(b.fired) - Number(a.fired));
  const genomeEvents = events.filter((e) => e.source === "genomes");
  const genomeFiredAll = firedCount(genomeEvents);
  const genomeFiredNow = firedCount(genomeEvents.filter((e) => e.year <= replayYear));
  const otherFiredAll = firedCount(events.filter((e) => e.source !== "genomes"));
  const otherFiredNow = firedCount(placed.filter((e) => e.source !== "genomes"));
  const selected = events.find((e) => e.id === selectedId) ?? null;

  /* timeline lanes */
  const paperTicks: PaperTick[] = useMemo(() => {
    const m = new Map<number, PaperTick>();
    for (const p of pack.literature.papers) {
      const t = m.get(p.pub_year) ?? { year: p.pub_year, total: 0, inCountry: 0 };
      t.total++;
      if ((p.countries_iso3 ?? []).includes(area)) t.inCountry++;
      m.set(p.pub_year, t);
    }
    return [...m.values()].sort((a, b) => a.year - b.year);
  }, [pack.literature.papers, area]);
  const graphTicks: GraphTick[] = useMemo(
    () => [
      ...pack.literature.papers
        .filter((p) => p.in_graph)
        .map((p) => ({
          year: p.pub_year,
          key: `paper-${pmidStr(p.pmid)}`,
          inCountry: (p.countries_iso3 ?? []).includes(area),
          label: `Graph has read (published ${p.pub_year}): ${p.title}`,
        })),
      ...data.graphFindings!.map((f) => ({
        year: f.pubYear,
        key: `finding-${f.id}`,
        inCountry: f.iso3 === area,
        label: `Graph haplotype finding ${f.id}, published ${f.pubYear}${f.sourceChecked ? ", checked against the paper" : ", unverified"}`,
      })),
    ].sort((a, b) => a.year - b.year),
    [pack.literature.papers, data.graphFindings, area],
  );
  const whoYears: WhoYear[] = useMemo(() => {
    const out: WhoYear[] = (pack.thresholds.history ?? []).map((h) => ({ year: h.year, label: h.text }));
    const src = pack.thresholds.who_categories?.sources?.[0]?.name;
    const y = src ? Number(/(\d{4})\s*$/.exec(src)?.[1]) : NaN;
    if (src && Number.isFinite(y)) out.push({ year: y, label: `${src}: the SP-resistance categories used here` });
    return out.sort((a, b) => a.year - b.year);
  }, [pack.thresholds]);

  /* coverage readout */
  const papersByNow = pack.literature.papers.filter((p) => p.pub_year <= replayYear);
  const inGraphAll = pack.literature.papers.filter((p) => p.in_graph).length;

  const concepts: ConceptRef[] = useMemo(() => {
    // lead with the two drug concepts; DHPS follows and its sparse neighbourhood is shown as it is
    const order = ["sulfadoxine", "pyrimethamine", "dihydropteroate synthase", "low birth weight infant"];
    return order.flatMap((label) => {
      const c = pack.graph.concepts.find((x) => x.label.toLowerCase() === label);
      return c ? [{ key: c.system_id, id: c.system_id, label: c.label }] : [];
    });
  }, [pack.graph.concepts]);

  /* email status */
  const [emailStatus, setEmailStatus] = useState<{ configured: boolean; from: string } | null>(null);
  useEffect(() => {
    fetch("/api/alert/email")
      .then((r) => r.json())
      .then(setEmailStatus)
      .catch(() => setEmailStatus({ configured: false, from: "" }));
  }, []);

  /* saved watches: in memory for this visit only (no browser storage). The URL always holds the current watch. */
  const [saved, setSaved] = useState<Saved[]>([]);
  const persist = (next: Saved[]) => setSaved(next);
  const [urlCopied, setUrlCopied] = useState(false);
  const copyWatchUrl = async () => {
    const q = new URLSearchParams(currentQs());
    q.set("marker", marker.urlId);
    try {
      await navigator.clipboard.writeText(`${window.location.origin}${pathname}?${q.toString()}`);
      setUrlCopied(true);
      setTimeout(() => setUrlCopied(false), 1800);
    } catch {
      /* clipboard unavailable: the address bar holds the same link */
    }
  };
  const currentQs = () => {
    const q = new URLSearchParams();
    q.set("area", area);
    q.set("trig", TRIG_CODE[watch.trigger]);
    q.set("level", String(watch.level));
    q.set("pts", String(watch.points));
    q.set("n", String(watch.minN));
    return q.toString();
  };
  const saveWatch = () => {
    const tail = watch.trigger === "rise" || watch.trigger === "fall" ? ` ${watch.level}%` : watch.trigger === "change" ? ` ${watch.points} pts` : "";
    const name = `${country} · ${TRIGGER_LABEL[watch.trigger].replace("moves into a new WHO resistance band", "WHO band").replace("reaches the WHO “very high” combination with A581G", "“very high” combination")}${tail}`;
    const qs = currentQs();
    if (!saved.some((s) => s.qs === qs)) persist([...saved, { name, qs }]);
  };

  const tb = thresholdBasis(watch, basis);
  const fmtDate = (iso: string | undefined) => {
    const m = iso ? /(\d{4})-(\d{2})-(\d{2})/.exec(iso) : null;
    return m ? `${Number(m[3])} ${["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"][Number(m[2]) - 1]} ${m[1]}` : null;
  };
  const lastCollection = rows.reduce((mx, r) => Math.max(mx, r[1]), 0);
  const graphDate = fmtDate(pack.graph._meta?.snapshot_generated_at as string | undefined);
  const pubmedDate = fmtDate(pack.literature._meta?.source as string | undefined);
  const asOfLine = `Data as of: genome counts, MalariaGEN Pf8, collections to ${lastCollection}; papers, PubMed searched ${pubmedDate ?? "date not stated"}; ${GRAPH_RELEASE}.`;
  const snapshotLabel = GRAPH_RELEASE;

  const linkTo = (path: string) => `${path}?marker=${encodeURIComponent(marker.urlId)}&area=${encodeURIComponent(area)}`;
  const needsLevel = watch.trigger === "rise" || watch.trigger === "fall";
  const esa = basis === "east_southern_africa";
  const cs = countryStats.get(area);
  const qualCells = cells.filter((c) => c.n >= watch.minN).length;

  return (
    <div className="mx-auto max-w-[1400px] px-4 pb-20 pt-8 sm:px-6">
      {/* identity strip: the marker is fixed, and always named with its drug */}
      <header className="mb-5 flex flex-wrap items-end justify-between gap-x-8 gap-y-3">
        <div>
          <p className="font-mono text-xs uppercase tracking-[0.18em] text-muted">Alert · evidence watch</p>
          <h1 className="mt-1 font-display text-3xl font-semibold tracking-tight sm:text-4xl">
            <span className="text-signal">{marker.label}</span> <span className="font-normal text-muted">and</span>{" "}
            <span className="text-drug">{marker.drug}</span>
          </h1>
        </div>
        <p className="max-w-md text-xs leading-relaxed text-muted">
          A replay of the historical record, not live surveillance and not clinical guidance. {asOfLine}
        </p>
      </header>

      <SendTestAlert
        pack={pack}
        marker={marker}
        data={data}
        papers={papers}
        asOfLine={asOfLine}
        configured={emailStatus ? emailStatus.configured : null}
        onJump={(qs) =>
          replaceParams((q) => {
            for (const k of WATCH_PARAMS) q.delete(k);
            for (const [k, v] of Object.entries(qs)) q.set(k, v);
          })
        }
      />

      <GraphPanel
        marker={marker.label}
        mutation={marker.mutation}
        probes={marker.probes}
        concepts={concepts}
        replayYear={replayYear}
        lastYear={lastYear}
        papersTotal={pack.literature.papers.length}
        papersByNow={papersByNow.length}
        inGraphTotal={inGraphAll}
        inGraphByNow={papersByNow.filter((p) => p.in_graph).length}
        haplotypeFindings={pack.graph.haplotype_findings.length}
        checkedFindings={pack.graph.haplotype_findings.filter((f) => f.source_checked === true).length}
        vettedCount={pack.graph.vetted_count}
        snapshotLabel={snapshotLabel}
      />

      {/* the watch, written as a sentence */}
      <section aria-labelledby="watch-h" className="mt-6 grid gap-6 xl:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]">
        <div className="rounded-[var(--radius)] border border-line bg-surface p-5 shadow-[var(--shadow)]">
          <h2 id="watch-h" className="font-mono text-xs uppercase tracking-[0.18em] text-muted">
            Your watch
          </h2>
          <p className="mt-3 font-display text-[1.45rem] leading-[1.75] tracking-tight sm:text-[1.65rem]">
            Tell me when <strong className="font-semibold">{marker.label}</strong> in{" "}
            <CountryPicker rows={pickerRows} value={area} minN={watch.minN} onChange={setArea} />{" "}
            <TokenSelect label="Trigger" shown={TRIGGER_LABEL[watch.trigger]} value={watch.trigger} onChange={(v) => setWatch({ trig: TRIG_CODE[v as Trigger] })}>
              {(Object.keys(TRIGGER_LABEL) as Trigger[]).map((t) => (
                <option key={t} value={t}>
                  {TRIGGER_LABEL[t]}
                </option>
              ))}
            </TokenSelect>
            {needsLevel ? (
              <>
                {" "}
                <input
                  aria-label="Level, percent"
                  type="number"
                  min={0}
                  max={100}
                  className={css.token}
                  value={watch.level}
                  onChange={(e) => setWatch({ level: e.target.value === "" ? null : e.target.value })}
                />
                %
              </>
            ) : null}
            {watch.trigger === "change" ? (
              <>
                {" "}
                <input
                  aria-label="Change, percentage points"
                  type="number"
                  min={1}
                  max={100}
                  className={css.token}
                  value={watch.points}
                  onChange={(e) => setWatch({ pts: e.target.value === "" ? null : e.target.value })}
                />{" "}
                points
              </>
            ) : null}
            , counting samples of at least{" "}
            <input
              aria-label="Minimum samples per cell"
              type="number"
              min={1}
              max={1000}
              className={css.token}
              value={watch.minN}
              onChange={(e) => setWatch({ n: e.target.value === "" ? null : e.target.value })}
            />
            .
          </p>

          <p className="mt-3 flex flex-wrap items-center gap-2 text-xs">
            <span className={`rounded-full border px-2 py-0.5 font-mono text-[0.7rem] ${tb.published ? "border-drug/60 text-drug" : "border-gap/60 text-gap"}`}>
              {tb.published ? "published by WHO" : "preset"}
            </span>
            <span className="text-muted">{tb.text}</span>
            {needsLevel && esa
              ? [40, 60].map((l) => (
                  <button key={l} type="button" onClick={() => setWatch({ level: String(l) })} className="rounded-full border border-line px-2 py-0.5 font-mono text-[0.7rem] text-muted hover:text-fg">
                    WHO {l}%
                  </button>
                ))
              : null}
          </p>
          <p className="mt-1.5 text-xs text-muted">
            {country} is graded here as <strong className="font-medium text-fg">{BASIS_LABEL[basis]}</strong>
            {esa ? ", where WHO grades SP resistance by K540E." : basis === "central_west_africa" ? ", where WHO grades SP resistance by a different mutation; K540E lines here are presets." : "; WHO’s K540E bands do not apply, so lines here are presets."}{" "}
            The region grouping is our approximation of WHO’s wording.
          </p>

          {/* live counter */}
          <div className="mt-5 flex items-end gap-4 border-t border-line pt-4">
            <p className="font-display text-6xl font-semibold leading-none tracking-tight tabular-nums text-signal" aria-live="polite">
              {genomeFiredAll}
            </p>
            <p className="pb-1 text-sm leading-snug">
              time{genomeFiredAll === 1 ? "" : "s"} this watch would have fired on the genome counts
              <span className="block text-xs text-muted">
                {cs ? `${cs.cells} sampled year${cs.cells === 1 ? "" : "s"} from ${cs.first} to ${cs.last}; ${qualCells} with at least ${watch.minN} samples` : "no cells"}
                {otherFiredAll > 0 ? ` · plus ${otherFiredAll} dated paper and graph item${otherFiredAll === 1 ? "" : "s"} for ${country}` : ""}
              </span>
            </p>
          </div>

          {/* examples + saved */}
          <div className="mt-5 border-t border-line pt-4">
            <p className="mb-2 font-mono text-[0.7rem] uppercase tracking-[0.16em] text-muted">Examples</p>
            <ul className="grid gap-1.5 sm:grid-cols-2">
              {EXAMPLES.filter((ex) => countryStats.has(ex.qs.area)).map((ex) => {
                const active = ex.qs.area === area && CODE_TRIG[ex.qs.trig] === watch.trigger;
                return (
                  <li key={ex.label}>
                    <button
                      type="button"
                      onClick={() => applyQs(ex.qs)}
                      aria-pressed={active}
                      className={`w-full rounded-lg border px-3 py-2 text-left text-sm transition-colors ${active ? "border-fg bg-surface-2" : "border-line hover:border-line-strong hover:bg-surface-2"}`}
                    >
                      <span className="font-medium">{ex.label}</span>
                      <span className="block text-xs text-muted">{ex.note}</span>
                    </button>
                  </li>
                );
              })}
            </ul>
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <button type="button" onClick={saveWatch} className="rounded-full border border-line-strong px-3 py-1 text-xs font-medium hover:bg-surface-2">
                + Save this watch
              </button>
              <button type="button" onClick={copyWatchUrl} className="rounded-full border border-line-strong px-3 py-1 text-xs font-medium hover:bg-surface-2">
                <span aria-live="polite">{urlCopied ? "Copied" : "Copy watch URL"}</span>
              </button>
              {saved.map((s) => (
                <span key={s.qs} className="inline-flex items-center rounded-full border border-line text-xs">
                  <button type="button" className="rounded-l-full py-1 pl-3 pr-1.5 hover:text-signal" onClick={() => applyQs(Object.fromEntries(new URLSearchParams(s.qs)))}>
                    {s.name}
                  </button>
                  <button type="button" aria-label={`Remove saved watch ${s.name}`} className="rounded-r-full py-1 pl-1 pr-2.5 text-muted hover:text-signal" onClick={() => persist(saved.filter((x) => x.qs !== s.qs))}>
                    ×
                  </button>
                </span>
              ))}
              <span className="text-[0.7rem] text-muted">Kept for this visit only; nothing is stored in the browser. The watch URL restores it anywhere.</span>
            </div>
          </div>
        </div>

        <div className="rounded-[var(--radius)] border border-line bg-surface p-5 shadow-[var(--shadow)]">
          <div className="mb-2 flex flex-wrap items-baseline justify-between gap-2">
            <h2 className="text-sm font-semibold">
              {marker.label} among genome samples collected in {country}
            </h2>
            <p className="font-mono text-[0.7rem] text-muted">MalariaGEN counts · convenience samples · not national prevalence</p>
          </div>
          <EvidenceChart
            country={country}
            marker={marker.label}
            cells={cells}
            companion={companion}
            watch={watch}
            basis={basis}
            events={genomeEvents}
            replayYear={replayYear}
            freshYear={freshYear}
            selectedId={selectedId}
            onSelect={select}
          />
        </div>
      </section>

      {/* timeline + replay */}
      <section aria-labelledby="tl-h" className="mt-6 rounded-[var(--radius)] border border-line bg-surface p-5 shadow-[var(--shadow)]">
        <div className="mb-2 flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1">
          <h2 id="tl-h" className="text-sm font-semibold">
            How the evidence on {country} built up
          </h2>
          <ul className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted">
            {(["prevalence_shift", "new_signal", "association"] as const).map((k) => (
              <li key={k} className="flex items-center gap-1.5">
                <span className="text-signal">
                  <KindGlyph event={{ kind: k, direction: "up" }} size={14} />
                </span>
                {KIND_LABEL[k]}
              </li>
            ))}
            <li className="font-mono text-[0.7rem]">dotted line = year WHO’s position changed (context)</li>
          </ul>
        </div>
        <Timeline
          domain={[firstYear, lastYear]}
          replayYear={replayYear}
          onReplayYear={(y) => {
            setPlaying(false);
            setFreshYear(null);
            setReplayYear(y);
          }}
          playing={playing}
          onTogglePlay={togglePlay}
          country={country}
          minN={watch.minN}
          cells={cells}
          cellNote={cellNote}
          eventNote={(e) => `${eventCopy(e, watch, marker.label, country).title}. ${e.source === "genomes" ? cellNote(e.year) : chipsFor(e).map((c) => c.text).join(" · ")}`}
          papers={paperTicks}
          graph={graphTicks}
          events={events.filter((e) => !e.noCountryGiven)}
          whoYears={whoYears}
          selectedId={selectedId}
          onSelect={select}
          freshYear={freshYear}
        />
        <p className="mt-2 text-xs text-muted">
          By {replayYear}: <strong className="text-fg">{genomeFiredNow}</strong> of {genomeFiredAll} genome alert{genomeFiredAll === 1 ? "" : "s"} and{" "}
          <strong className="text-fg">{otherFiredNow}</strong> of {otherFiredAll} paper and graph item{otherFiredAll === 1 ? "" : "s"} for {country} existed. Genome counts sit at
          their collection year; they reached the public later, with each data release.
        </p>
        {cells.some((c) => c.year === replayYear) && cellNote(replayYear) ? (
          <p className="mt-1.5 text-xs" aria-live="polite">
            <span className="font-mono text-[0.68rem] uppercase tracking-[0.12em] text-muted">Collected {replayYear} · study behind the cell</span>{" "}
            {cellNote(replayYear)}
          </p>
        ) : null}
      </section>

      {/* feed + detail */}
      <section aria-labelledby="feed-h" className="mt-6 grid items-start gap-6 xl:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]">
        <div>
          <div className="mb-2 flex items-baseline justify-between gap-2">
            <h2 id="feed-h" className="text-sm font-semibold">
              Feed <span className="font-normal text-muted">· what existed by {replayYear}</span>
            </h2>
            {unplaced.length > 0 ? (
              <button type="button" className="text-xs text-muted underline underline-offset-2 hover:text-fg" onClick={() => setShowUnplaced((s) => !s)} aria-pressed={showUnplaced}>
                {showUnplaced ? "Hide" : "Show"} {unplaced.length} with no country stated
              </button>
            ) : null}
          </div>
          <div className="mb-3 flex flex-wrap gap-1" role="group" aria-label="Filter the feed by evidence source">
            {(["all", "genomes", "papers", "graph"] as const).map((k) => {
              const n = k === "all" ? placed.length : placed.filter((e) => e.source === k).length;
              return (
                <button
                  key={k}
                  type="button"
                  onClick={() => setFeedSource(k)}
                  aria-pressed={feedSource === k}
                  className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs ${feedSource === k ? "bg-fg text-bg" : "border border-line text-muted hover:text-fg"}`}
                >
                  {k !== "all" ? <SourceGlyph source={k} size={10} /> : null}
                  {k === "all" ? "All" : SOURCE_LABEL[k]} <span className="tabular-nums opacity-70">{n}</span>
                </button>
              );
            })}
          </div>
          {feed.length === 0 ? (
            <div className="rounded-[var(--radius)] border border-dashed border-line-strong p-6 text-sm text-muted">
              {replayYear < lastYear ? (
                <>Nothing for {country} had been collected or published by {replayYear}. Move the scrubber forward or press Play.</>
              ) : cells.length === 0 ? (
                <>No genome counts for {country}. Not sampled is not the same as absent.</>
              ) : (
                <>
                  This watch never fires on the record for {country}, and no dated paper or graph item names it. Try a lower minimum sample size or a different trigger.
                </>
              )}
            </div>
          ) : (
            <ol className="max-h-[85vh] space-y-2 overflow-y-auto pr-1">
              {feed.map((e) => (
                <FeedItem
                  key={e.id}
                  e={e}
                  watch={watch}
                  marker={marker.label}
                  country={country}
                  paper={e.pmid ? papers.get(e.pmid) : undefined}
                  chips={chipsFor(e)}
                  selected={e.id === selectedId}
                  fresh={freshYear === e.year && e.fired}
                  onSelect={() => select(e.id === selectedId ? null : e.id)}
                />
              ))}
            </ol>
          )}
        </div>

        <div id="alert-detail" className="scroll-mt-20 xl:sticky xl:top-20">
          {selected ? (
            <AlertDetail
              event={selected}
              watch={watch}
              marker={marker}
              country={country}
              basis={basis}
              pack={pack}
              cells={data.cells}
              papers={papers}
              asOfLine={asOfLine}
              emailConfigured={emailStatus ? emailStatus.configured : null}
              emailFrom={emailStatus?.from ?? null}
              links={{ forecast: `/forecast?country=${encodeURIComponent(area)}&marker=${encodeURIComponent(marker.urlId)}`, learn: linkTo("/learn") }}
              onClose={() => select(null)}
            />
          ) : (
            <div className="grid min-h-48 place-items-center rounded-[var(--radius)] border border-dashed border-line-strong p-8 text-center text-sm text-muted">
              <p className="max-w-sm">
                Open an alert from the feed, the chart or the timeline to check it: the stakes according to the graph, what changed, the counts, the threshold and its basis, what
                it cannot tell you, and the email a subscriber would get.
              </p>
            </div>
          )}
        </div>
      </section>
      <CurationQueue pack={pack} marker={marker} area={area} country={country} replayYear={replayYear} />
    </div>
  );
}

/* --------------------------------------------------------- sentence token --- */

/** A choice inside the sentence: reads as underlined text, opens the native picker (keyboard and screen-reader friendly). */
function TokenSelect({ label, shown, value, onChange, children }: { label: string; shown: string; value: string; onChange: (v: string) => void; children: React.ReactNode }) {
  return (
    <span className={css.tokenWrap}>
      <span aria-hidden className={css.tokenText}>
        {shown}
        {"\u00A0"}
        <span className={css.tokenCaret}>▼</span>
      </span>
      <select aria-label={label} className={css.tokenSelect} value={value} onChange={(e) => onChange(e.target.value)}>
        {children}
      </select>
    </span>
  );
}

/* ------------------------------------------------------------ feed item --- */

function witness(e: AlertEvent, paper: Paper | undefined): { text: string; tone: string } {
  if (e.source === "graph") return { text: e.sourceChecked ? "graph finding · checked against the paper" : e.rule === "graph_paper" ? "graph has read this paper" : "graph finding · unverified", tone: "border-drug/60 text-drug" };
  if (e.source === "genomes") return { text: "genome counts · the graph holds none", tone: "border-line-strong text-muted" };
  return paper?.in_graph ? { text: "graph has read this paper", tone: "border-drug/60 text-drug" } : { text: "graph has not read this paper", tone: "border-gap/60 text-gap" };
}

function FeedItem({
  e,
  watch,
  marker,
  country,
  paper,
  chips,
  selected,
  fresh,
  onSelect,
}: {
  e: AlertEvent;
  watch: Watch;
  marker: string;
  country: string;
  paper: Paper | undefined;
  chips: { text: string; warn?: boolean }[];
  selected: boolean;
  fresh: boolean;
  onSelect: () => void;
}) {
  const copy = eventCopy(e, watch, marker, country);
  const w = witness(e, paper);
  return (
    <li>
      <button
        type="button"
        onClick={onSelect}
        aria-expanded={selected}
        className={`group flex w-full gap-3 rounded-[var(--radius)] border p-3.5 text-left transition-colors ${fresh ? css.fresh : ""} ${
          selected ? "border-fg bg-surface" : e.fired ? "border-line bg-surface hover:border-line-strong" : "border-transparent bg-transparent hover:border-line"
        }`}
      >
        <span className="w-11 shrink-0 pt-0.5 text-right font-mono text-sm font-semibold tabular-nums">{e.year}</span>
        <span className={`pt-0.5 ${e.fired ? "text-signal" : "text-muted"}`}>
          <KindGlyph event={e} size={18} quiet={!e.fired} />
        </span>
        <span className="min-w-0 flex-1">
          <span className={`block leading-snug ${e.fired ? "font-semibold" : "text-muted"}`}>{copy.title}</span>
          {e.fired ? <span className="mt-1 block text-[0.82rem] leading-snug text-muted line-clamp-3">{e.quote ? `“${e.quote}”` : copy.statement}</span> : null}
          <span className="mt-1.5 flex flex-wrap items-center gap-x-2 gap-y-1 font-mono text-[0.68rem] text-muted">
            <span className={`inline-flex items-center gap-1 ${SOURCE_TONE[e.source]}`}>
              <SourceGlyph source={e.source} size={10} />
              {SOURCE_LABEL[e.source]} · {e.dateBasis === "collection" ? "collected" : "published"}
            </span>
            {e.strength ? <span className={e.strength === "strong" ? "text-signal" : ""}>{e.strength === "strong" ? "strong signal" : e.strength === "weak" ? "weak signal" : "signal"}</span> : null}
            <span className={`rounded-full border px-1.5 py-px ${w.tone}`}>{w.text}</span>
            {e.noCountryGiven ? <span>no country stated</span> : null}
          </span>
          <span className="mt-1 flex flex-wrap items-center gap-1 font-mono text-[0.64rem] text-muted">
            {chips.map((c) => (
              <span key={c.text} className={`rounded-full border px-1.5 py-px ${c.warn ? "border-signal/60 text-signal" : "border-line"}`}>
                {c.warn ? "⚠ " : ""}
                {c.text}
              </span>
            ))}
          </span>
        </span>
      </button>
    </li>
  );
}
