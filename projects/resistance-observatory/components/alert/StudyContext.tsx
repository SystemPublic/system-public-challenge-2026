"use client";

import { EVIDENCE_TIER, NEXT_STEPS_NOTE, enaUrl, methodText, type GenomeContext, type StudyContextFile } from "@/lib/alert/context";
import { pmidStr, type AbstractPrevalence, type Paper } from "@/lib/alert/pack";
import { glossaryText, pubmedUrl } from "@/lib/alert/receipt";

/** The evidence-tier badge. One per lane, so study types never blur together. */
export function TierBadge({ source, small = false }: { source: keyof typeof EVIDENCE_TIER; small?: boolean }) {
  const tone = source === "genomes" ? "border-fg/50 text-fg" : source === "papers" ? "border-gap/60 text-gap" : "border-drug/60 text-drug";
  return <span className={`inline-block rounded-full border font-mono ${small ? "px-1.5 py-px text-[0.64rem]" : "px-2 py-0.5 text-[0.7rem]"} ${tone}`}>{EVIDENCE_TIER[source]}</span>;
}

/** Tier line for a paper or graph item: the badge and what the source says about its own design. */
export function ItemTier({ source, detail }: { source: "papers" | "graph"; detail: string[] }) {
  return (
    <div className="text-sm">
      <TierBadge source={source} />
      <ul className="mt-2 space-y-0.5 text-[0.82rem]">
        {detail.map((d) => (
          <li key={d}>{d}</li>
        ))}
      </ul>
      <p className="mt-2 text-xs text-muted">
        {source === "papers"
          ? "A figure stated in an abstract comes from that paper’s own design. It is not a genome-surveillance count and is never pooled with one."
          : "A graph finding is a machine-extracted association from one paper. Its study type and population are shown as the graph gives them."}
      </p>
    </div>
  );
}

function Flag({ warn, label, children }: { warn: boolean; label: string; children: React.ReactNode }) {
  return (
    <div className={`rounded-lg border p-2.5 text-[0.82rem] leading-snug ${warn ? "border-signal/60 bg-signal-soft/40" : "border-drug/40 bg-drug-soft/40"}`}>
      <p className="font-semibold">
        <span aria-hidden className="mr-1.5 font-mono">
          {warn ? "⚠" : "✓"}
        </span>
        {label}
      </p>
      <p className="mt-0.5">{children}</p>
    </div>
  );
}

export function StudyContextPanel({
  ctx,
  mutation,
  study,
  matched,
  papers,
}: {
  ctx: GenomeContext;
  mutation: string;
  study: StudyContextFile | null;
  matched: AbstractPrevalence[];
  papers: Map<string, Paper>;
}) {
  const c = ctx.cell;
  return (
    <div className="space-y-3">
      <p className="flex flex-wrap items-center gap-x-2 gap-y-1">
        <TierBadge source="genomes" />
        <span className="font-mono text-[0.72rem] text-muted">{ctx.tierDetail}</span>
      </p>

      <div className="space-y-2">
        {ctx.flags.map((f) => (
          <Flag key={f.label} warn={f.tone === "warn"} label={f.label}>
            {f.text}
          </Flag>
        ))}
      </div>

      {/* cutoff beside observed */}
      <div>
        <div className="grid gap-2 sm:grid-cols-2">
          <div className="rounded-lg border border-line-strong bg-bg p-2.5">
            <p className="font-mono text-[0.62rem] uppercase tracking-[0.14em] text-muted">Cutoff · {ctx.cutoff.published ? "published by WHO" : "project rule or preset"}</p>
            <p className="mt-1 font-mono text-lg font-semibold leading-tight">{ctx.cutoff.value != null ? `${ctx.cutoff.value}%` : "none"}</p>
            <p className="mt-1 text-xs text-muted">{ctx.cutoff.text}</p>
          </div>
          <div className="rounded-lg border border-line-strong bg-bg p-2.5">
            <p className="font-mono text-[0.62rem] uppercase tracking-[0.14em] text-muted">Observed · this cell</p>
            <p className="mt-1 font-mono text-lg font-semibold leading-tight">{ctx.observed.split(",")[0]}</p>
            <p className="mt-1 text-xs text-muted">{ctx.observed.split(", ").slice(1).join(", ")}</p>
          </div>
        </div>
        {ctx.relation ? <p className="mt-1.5 text-xs">{ctx.relation}</p> : null}
      </div>

      {/* proportional bar for action */}
      <div>
        <p className="text-xs font-medium">Next steps a reviewer would look for</p>
        <ol className="mt-1 list-decimal space-y-0.5 pl-5 text-[0.82rem]">
          {ctx.prior.steps.map((s) => (
            <li key={s}>{s}</li>
          ))}
        </ol>
        <p className="mt-1.5 text-xs text-muted">{NEXT_STEPS_NOTE}</p>
      </div>

      {c ? (
        <details className="text-sm">
          <summary className="cursor-pointer text-muted hover:text-fg">
            Partner studies, sites, DNA preparation and raw reads ({c.study_count} stud{c.study_count === 1 ? "y" : "ies"}, {c.admin1_count} Admin-1 area{c.admin1_count === 1 ? "" : "s"})
          </summary>
          <div className="mt-2 space-y-3 rounded-lg border border-line bg-bg p-3 text-[0.8rem]">
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <caption className="mb-1 text-left font-mono text-[0.62rem] uppercase tracking-[0.14em] text-muted">MalariaGEN partner studies in this cell</caption>
                <thead className="font-mono text-[0.66rem] text-muted">
                  <tr>
                    <th scope="col" className="pr-3 font-normal">
                      Study
                    </th>
                    <th scope="col" className="pr-3 font-normal">
                      {mutation} / tested
                    </th>
                    <th scope="col" className="pr-3 font-normal">
                      Admin-1 sites
                    </th>
                    <th scope="col" className="font-normal">
                      DNA prep · callable
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {c.studies.map((s) => (
                    <tr key={s.study_id} className="border-t border-line align-top">
                      <th scope="row" className="py-1 pr-3 font-mono text-[0.72rem] font-medium">
                        {s.study_id}
                      </th>
                      <td className="py-1 pr-3 font-mono text-[0.72rem] tabular-nums">
                        {s.k}/{s.n} ({s.pct}%)
                      </td>
                      <td className="py-1 pr-3">{s.admin1.map((a) => `${a.name} ${a.k}/${a.n}`).join(", ")}</td>
                      <td className="py-1 font-mono text-[0.72rem]">
                        {methodText(s.dna_method)}
                        {s.median_callable_pct != null ? ` · ${s.median_callable_pct}%` : ""}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {ctx.geo && !ctx.geo.flag ? <p>{ctx.geo.text}</p> : null}

            {ctx.measure ? (
              <div>
                <p className="font-mono text-[0.62rem] uppercase tracking-[0.14em] text-muted">How the genomes were measured</p>
                <p className="mt-1">
                  All samples: <span className="font-mono text-[0.74rem]">{methodText(c.dna_method_all)}</span>.
                  {c.k > 0 ? (
                    <>
                      {" "}
                      Carrying {mutation}: <span className="font-mono text-[0.74rem]">{methodText(c.dna_method_mutants)}</span>.
                    </>
                  ) : null}{" "}
                  {ctx.measure.note}
                </p>
                <p className="mt-1">Genome callability: {ctx.measure.callable}.</p>
                <p className="mt-1 text-xs text-muted">{glossaryText(study, ctx.measure.all.map(([m]) => m))}</p>
              </div>
            ) : null}

            {ctx.codon ? (
              <div>
                <p className="font-mono text-[0.62rem] uppercase tracking-[0.14em] text-muted">Within-host clonality and codon-540 alleles</p>
                <p className="mt-1">{ctx.codon.text}</p>
              </div>
            ) : null}

            {ctx.runs.length ? (
              <div>
                <p className="font-mono text-[0.62rem] uppercase tracking-[0.14em] text-muted">Raw sequencing reads, samples carrying {mutation}</p>
                <ul className="mt-1 space-y-0.5">
                  {ctx.runs.map((r) => (
                    <li key={r.sample} className="font-mono text-[0.72rem]">
                      <a href={enaUrl(r.ena as string)} target="_blank" rel="noopener noreferrer" className="text-drug underline underline-offset-2">
                        ENA {r.ena} ↗
                      </a>{" "}
                      <span className="text-muted">
                        {r.sample} · {r.dna_method} · {r.admin1}
                        {r.callable_pct != null ? ` · ${r.callable_pct}% callable` : ""} · call {r.call540}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            ) : c.k > 0 ? (
              <p className="text-xs text-muted">No ENA run accession is recorded for the positive samples in this cell.</p>
            ) : null}

            {study?._meta?.url ? (
              <p className="text-xs text-muted">
                Site, study and method fields:{" "}
                <a href={study._meta.url} target="_blank" rel="noopener noreferrer" className="text-drug underline underline-offset-2">
                  {study._meta.source ?? "MalariaGEN Pf8"} ↗
                </a>
                {study._meta.license ? `, ${study._meta.license}` : ""}. Sites are attributed to MalariaGEN, not to the System graph.
              </p>
            ) : null}
          </div>
        </details>
      ) : (
        <p className="text-xs text-muted">No study-level context is recorded for this cell.</p>
      )}

      {matched.length ? (
        <div>
          <p className="flex flex-wrap items-center gap-2 text-xs font-medium">
            Papers stating a figure for the same country and collection years <TierBadge source="papers" small />
          </p>
          <ul className="mt-1.5 space-y-1.5">
            {matched.map((f, i) => {
              const id = pmidStr(f.pmid);
              const p = papers.get(id);
              return (
                <li key={`${id}-${i}`} className="rounded-lg border border-line bg-surface p-2.5 text-[0.8rem]">
                  <p className="font-medium leading-snug">{p?.title ?? "Title not recorded"}</p>
                  <p className="mt-0.5 text-xs text-muted">
                    {[f.site ? `site: ${f.site}` : null, f.population ? `population: ${f.population}` : null].filter(Boolean).join(" · ") || "site and population not stated in the abstract fields"}
                  </p>
                  <p className="mt-1 border-l-2 border-gap/60 pl-2 italic">“{f.quote}”</p>
                  <p className="mt-1 font-mono text-[0.68rem] text-muted">
                    <a href={p?.url ?? pubmedUrl(id)} target="_blank" rel="noopener noreferrer" className="text-drug underline underline-offset-2">
                      PMID {id} ↗
                    </a>{" "}
                    · machine-read, not checked by hand · shown beside the genome count, never pooled with it
                  </p>
                </li>
              );
            })}
          </ul>
        </div>
      ) : null}
    </div>
  );
}
