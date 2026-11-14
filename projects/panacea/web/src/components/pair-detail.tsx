"use client";

// The expanding panel that opens just below a clicked confirmations/contested
// row: the pair's district correlation maps (bridges style), the 1-hop
// research graph in the bridges connection-graph style, and the pair's
// evidence summary. Shared by both tables.

import type {
  ConceptDict,
  ConfirmationRow,
  District,
  DistrictValue,
  Ego,
  MeasureDict,
} from "@/lib/bundle";
import { fmtInt, fmtMed, deEmdash } from "@/lib/format";
import { RhoPill } from "@/components/rho-pill";
import { DirBadge, AgreeBadge } from "@/components/dir-badge";
import { PairGraph } from "@/components/pair-graph";
import { DistrictMaps } from "@/components/bridges/district-maps";

export function PairDetailPanel({
  pair,
  concepts,
  measures,
  egos,
  districts,
  values,
  onClose,
}: {
  pair: ConfirmationRow;
  concepts: ConceptDict;
  measures: MeasureDict;
  egos: Record<string, Ego>;
  districts: District[];
  values: Record<string, Record<string, DistrictValue>>;
  onClose: () => void;
}) {
  const mlabel = (mid: string) => measures[mid]?.l ?? mid;
  const label = (cid: string) => concepts[cid]?.l || cid;
  const e1 = egos[pair.c1];
  const e2 = egos[pair.c2];
  if (!e1 || !e2) return null;

  return (
    <section
      className="animate-[fade-up_0.35s_ease-out] border-b-2 border-[color:var(--ink)] bg-[color:var(--paper)] px-5 py-6 sm:px-7"
      aria-label={`Pair detail: ${label(pair.c1)} and ${label(pair.c2)}`}
    >
      <div className="flex items-baseline justify-between gap-4">
        <h3 className="text-[1.3rem] font-normal leading-snug">
          {label(pair.c1)} <span className="text-muted">×</span> {label(pair.c2)}
          {pair.rho !== null && (
            <span className="ml-3 inline-flex align-middle">
              <RhoPill rho={pair.rho} mod={pair.mod} digits={3} />
            </span>
          )}
        </h3>
        <button
          onClick={onClose}
          title="Exit pair detail"
          className="shrink-0 rounded-full border border-rule px-3 py-1 font-sans text-[0.75rem] text-muted hover:border-ink hover:text-ink"
        >
          ✕ exit
        </button>
      </div>

      {/* the district correlation — the city, district by district */}
      {pair.rho !== null && pair.chk ? (
        <div className="mt-5">
          <h4 className="label">the district correlation (42 neighborhoods)</h4>
          <div className="mt-3">
            <DistrictMaps
              districts={districts}
              values={values}
              xMeasure={pair.chk[0]}
              yMeasure={pair.chk[1]}
              measures={measures}
              rho={pair.rho}
            />
          </div>
        </div>
      ) : (
        <p className="mt-5 max-w-[60rem] font-sans text-[0.78rem] leading-relaxed text-[color:var(--chart-ink-2)]">
          <span className="label mr-2">the district correlation</span>
          {pair.note
            ? deEmdash(pair.note)
            : "No co-observable district measures on both sides (e.g. a death cause is citywide-only)."}
        </p>
      )}

      {/* the research graph around the pair + the evidence, side by side */}
      <div className="mt-8 grid gap-8 lg:grid-cols-[1.5fr_1fr]">
        <div>
          <h4 className="label">what the studies connect through</h4>
          <div className="mt-3">
            <PairGraph pair={pair} concepts={concepts} egos={egos} />
          </div>
          <div className="mt-2 flex flex-wrap gap-x-6 gap-y-1 font-sans text-[0.72rem] text-[color:var(--chart-ink-2)]">
            <span className="inline-flex items-center gap-1.5">
              <span className="inline-block h-2.5 w-2.5 rounded-full bg-[color:var(--s-blue)]" />
              endpoints / NYC-mapped
            </span>
            <span className="inline-flex items-center gap-1.5">
              <span className="inline-block h-2.5 w-2.5 rounded-full bg-[color:var(--s-aqua)]" />
              shared connectors
            </span>
            <span className="inline-flex items-center gap-1.5">
              <span className="inline-block h-2.5 w-2.5 rounded-full bg-[color:var(--s-deemph)]" />
              other research neighbors
            </span>
            <span className="inline-flex items-center gap-1.5">
              <span className="inline-block h-[3px] w-5 rounded-full bg-[color:var(--dir-up)]" />
              studies find them rise together
            </span>
            <span className="inline-flex items-center gap-1.5">
              <span className="inline-block h-[3px] w-5 rounded-full bg-[color:var(--dir-down)]" />
              one goes up as the other goes down
            </span>
            <span className="inline-flex items-center gap-1.5">
              <span className="inline-block h-[3px] w-5 rounded-full bg-[color:var(--chart-grid)]" />
              studies name the pair but give no number
            </span>
          </div>
        </div>

        <div>
          <h4 className="label">research-graph evidence</h4>
          <dl className="mt-2 grid grid-cols-[auto_1fr] gap-x-6 gap-y-1 font-sans text-[0.78rem]">
            <dt className="text-muted">Associations</dt>
            <dd>{fmtInt(pair.na)}</dd>
            <dt className="text-muted">Studies</dt>
            <dd>{fmtInt(pair.np)}</dd>
            <dt className="text-muted">Relationship edge</dt>
            <dd>
              {pair.rel
                ? `${fmtInt(pair.rel.f)} findings · ${fmtInt(pair.rel.st)} studies`
                : "none"}
            </dd>
            <dt className="text-muted">Median effect</dt>
            <dd>
              {fmtMed(pair.med)}{" "}
              <span className="text-muted">
                ({pair.et.join(", ") || "mixed types"}): direction only
              </span>
            </dd>
            {pair.pms.length > 0 && (
              <>
                <dt className="text-muted">PubMed</dt>
                <dd className="flex flex-wrap gap-x-2">
                  {pair.pms.map((p) => (
                    <a
                      key={p}
                      href={`https://pubmed.ncbi.nlm.nih.gov/${p}/`}
                      target="_blank"
                      rel="noreferrer"
                    >
                      {p}
                    </a>
                  ))}
                </dd>
              </>
            )}
          </dl>

          <h4 className="label mt-6">direction check</h4>
          <dl className="mt-2 grid grid-cols-[auto_1fr] gap-x-6 gap-y-1 font-sans text-[0.78rem]">
            <dt className="text-muted">SPG direction</dt>
            <dd>
              <DirBadge dir={pair.dir} nsigns={pair.nsigns} />
            </dd>
            {pair.rho !== null && (
              <>
                <dt className="text-muted">City ρ</dt>
                <dd>
                  <RhoPill rho={pair.rho} mod={pair.mod} digits={3} />
                  <span className="text-muted">
                    {" "}
                    over {fmtInt(pair.nd ?? 0)} districts
                  </span>
                </dd>
                {pair.dir !== null && Math.abs(pair.rho) >= 0.1 && (
                  <>
                    <dt className="text-muted">Verdict</dt>
                    <dd>
                      <AgreeBadge agree={pair.agree} />
                    </dd>
                  </>
                )}
                {pair.mod && (
                  <>
                    <dt className="text-muted" aria-hidden />
                    <dd className="text-muted">
                      <span className="rho-pill warn">modeled</span> the check
                      includes a modeled burden measure: treat as neighborhood
                      structure, not observed outcome
                    </dd>
                  </>
                )}
              </>
            )}
          </dl>

          <h4 className="label mt-6">NYC measures mapped to these concepts</h4>
          {[pair.m1, pair.m2].map((side, i) => {
            const SHOW = 4;
            const shown = side.slice(0, SHOW);
            const rest = side.slice(SHOW);
            const chip = (m: string) => (
              <span
                key={m}
                className="chip"
                title={deEmdash(
                  `${m} · ${measures[m]?.mt ?? ""} · ${measures[m]?.yr ?? ""} · ${measures[m]?.themes ?? ""}`,
                )}
              >
                {mlabel(m)}
              </span>
            );
            return (
              <div key={i} className="mt-2">
                <div className="flex flex-wrap gap-1.5">
                  <span className="dom-note">{i === 0 ? "concept 1" : "concept 2"}</span>
                  {shown.map(chip)}
                </div>
                {rest.length > 0 && (
                  <details className="mt-1">
                    <summary className="cursor-pointer font-sans text-[0.72rem] text-muted hover:text-ink">
                      show {rest.length} more
                    </summary>
                    <div className="mt-1.5 flex flex-wrap gap-1.5">{rest.map(chip)}</div>
                  </details>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {pair.note && pair.rho !== null && pair.chk && (
        <p className="mt-5 max-w-[60rem] font-sans text-[0.72rem] leading-relaxed text-muted">
          {deEmdash(pair.note)}
        </p>
      )}
    </section>
  );
}
