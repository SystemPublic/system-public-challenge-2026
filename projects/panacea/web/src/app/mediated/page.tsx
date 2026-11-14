import type { Metadata } from "next";
import { getBundle } from "@/lib/bundle";
import type {
  ConceptDict,
  MediatedChain,
  MediatedEdge,
  MeasureDict,
} from "@/lib/bundle";
import { fmtEffect, fmtInt, deEmdash } from "@/lib/format";

export const metadata: Metadata = { title: "mediated" };

const SANS = "var(--font-sans)";

export default function MediatedPage() {
  const b = getBundle();
  return (
    <div className="mx-auto w-full max-w-[72rem] px-6 sm:px-10">
      <div className="mt-12 max-w-[62rem]">
        <h1 className="text-[clamp(1.8rem,4vw,2.6rem)] leading-tight font-normal">
          Connections no single dataset contains
        </h1>
        <p className="mt-3 text-[1.05rem] leading-relaxed text-[color:var(--chart-ink-2)]">
          Chains assembled from two datasets at once: one hop a documented SPG
          edge, the other carried entirely by NYC data: the endpoints&apos;
          connection doesn&apos;t exist in the research graph at all.
        </p>
      </div>

      <p className="mt-8 max-w-[64rem] font-sans text-[0.72rem] leading-relaxed text-muted">
        These chains are assembled from <b>two different datasets</b>: one hop
        is a documented <b>SPG edge</b> (≥2 findings, ≥2 studies), the other hop
        is carried <b>entirely by NYC data</b>: a district-level correlation
        with |ρ| ≥ 0.45 and <b>no (or negligible) SPG evidence</b> for that same
        link. The assembled connection between the two endpoints{" "}
        <b>does not exist in the research graph at all</b>: graph + city
        together produce a relationship the SPG never contained. This is the
        strongest form of the green-space × emergency-care pattern. Note the
        assembled link is a correlation chain: the direction of the endpoint
        relationship is not established by either hop.
      </p>

      <div className="mt-8 grid max-w-[72rem] gap-y-10">
        {b.mediated.length === 0 && (
          <p className="font-sans text-[0.8rem] text-muted">
            No mixed-evidence chains found at the current thresholds.
          </p>
        )}
        {b.mediated.map((m, i) => (
          <ChainCard
            key={`${m.a}|${m.b}|${i}`}
            m={m}
            measures={b.measures}
            concepts={b.concepts}
          />
        ))}
      </div>
    </div>
  );
}

function ChainCard({
  m,
  measures,
  concepts,
}: {
  m: MediatedChain;
  measures: MeasureDict;
  concepts: ConceptDict;
}) {
  const mlabel = (mid: string) => measures[mid]?.l ?? mid;
  const curated = Boolean(m.curated);
  const spgHop = m.edges.find((e) => e.kind === "spg");
  const nycHop = m.edges.find((e) => e.kind === "nyc");
  const spgStrength =
    spgHop && spgHop.kind === "spg"
      ? Math.log10(1 + spgHop.f) + 0.5 * Math.log10(1 + spgHop.st)
      : null;
  const nodeLabel = (cid: string) => concepts[cid]?.l || cid;
  const nodeDomain = (cid: string) => concepts[cid]?.dm || "beyond the mapped concepts";

  return (
    <section
      className="border-t border-rule pt-4"
      aria-label={`${m.l1} to ${m.l2} chain`}
    >
      <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1">
        <h2 className="text-[1.15rem] font-medium">
          {curated && <span title="Curated flagship: the original pattern">★ </span>}
          {m.l1} <span className="text-muted">⟶</span> {m.lx}
          {curated && <span className="text-muted"> ⟶ … ⟶</span>}{" "}
          <span className="text-muted">⟶</span> {m.l2}
        </h2>
        {!curated && spgStrength !== null && (
          <span
            className="font-sans text-[0.72rem] text-muted"
            title="weakest-link evidence score of the SPG hop: log₁₀(1+findings) + ½·log₁₀(1+studies)"
          >
            graph hop strength {spgStrength.toFixed(2)}
          </span>
        )}
      </div>

      {curated && m.note && (
        <p className="mt-2 max-w-[64rem] font-sans text-[0.75rem] leading-relaxed text-[color:var(--chart-ink-2)]">
          {deEmdash(m.note)}
        </p>
      )}

      {/* hop chips */}
      <div className="mt-3 flex flex-wrap gap-1.5">
        {curated ? (
          <>
            <span
              className="chip"
              style={{ borderColor: "var(--color-rule)", color: "var(--color-muted)" }}
              title="The direct green-space → emergency-department link: 0 SPG associations; city ρ=0.02 between the endpoint measures."
            >
              direct link: 0 SPG associations · city ρ=0.02
            </span>
            <span
              className="chip endpoint"
              title={`NYC-only link: grass/tree cover × surface temperature, ρ=−0.396 (no SPG edge for this pair).`}
            >
              NYC hop: ρ=−0.396 (cover → surface temp)
            </span>
            <span
              className="chip"
              style={{ borderColor: "var(--color-rule)", color: "var(--color-muted)" }}
              title="Physical mechanism: hot surfaces drive heat exposure. Assumed, not separately evidenced in either dataset here."
            >
              mechanistic hop: surface temp → extreme heat
            </span>
            {spgHop && spgHop.kind === "spg" && (
              <span
                className="chip endpoint"
                title={`SPG edges: extreme heat → hospitalization (${spgHop.f} findings / ${spgHop.st} studies) and hospitalization → emergency department.`}
              >
                SPG hops: {fmtInt(spgHop.f)}f + … (heat → hosp → ED)
              </span>
            )}
          </>
        ) : (
          <>
            {spgHop && spgHop.kind === "spg" && (
              <span
                className="chip endpoint"
                title={`SPG edge: ${spgHop.f} findings, ${spgHop.st} studies` +
                  (spgHop.med !== null
                    ? `, median effect ${fmtEffect(spgHop.med, spgHop.et)} (direction only)`
                    : "")}
              >
                SPG hop: {fmtInt(spgHop.f)} findings / {fmtInt(spgHop.st)} studies
              </span>
            )}
            {nycHop && nycHop.kind === "nyc" && (
              <span
                className="chip"
                title={`NYC-only link: ρ=${nycHop.rho.toFixed(2)} across UHF42 districts ` +
                  (m.graph_fb > 0
                    ? `(only ${m.graph_fb} SPG finding for this link)`
                    : `(no SPG edge for this link at all)`) +
                  `. Measured by: ${m.r_hop_measures.map(mlabel).join(" × ")}.`}
              >
                NYC hop ρ={nycHop.rho.toFixed(2)}:{" "}
                {m.graph_fb > 0 ? "weak SPG evidence" : "no SPG evidence"}
              </span>
            )}
            {m.r_ab !== null ? (
              <span
                className="chip"
                style={{ borderColor: "var(--color-rule)", color: "var(--color-muted)" }}
                title="City correlation between the two endpoints themselves: context for the assembled link."
              >
                assembled endpoints ρ={m.r_ab.toFixed(2)}
              </span>
            ) : (
              <span
                className="chip"
                style={{ borderColor: "var(--color-rule)", color: "var(--color-muted)" }}
              >
                endpoints: no co-observable city measures
              </span>
            )}
          </>
        )}
      </div>

      <div className="mt-2">
        <ChainPath
          m={m}
          measures={measures}
          nodeLabel={nodeLabel}
          nodeDomain={nodeDomain}
        />
      </div>
    </section>
  );
}

/** Linear endpoint-to-endpoint diagram: solid SPG edges, dashed NYC edges,
    dotted mechanistic hops. <title> tooltips; no client JS. */
function ChainPath({
  m,
  measures,
  nodeLabel,
  nodeDomain,
}: {
  m: MediatedChain;
  measures: MeasureDict;
  nodeLabel: (cid: string) => string;
  nodeDomain: (cid: string) => string;
}) {
  const W = 940;
  const H = 120;
  const boxW = 150;
  const xEnd1 = boxW / 2 + 16;
  const xEnd2 = W - boxW / 2 - 16;
  const n = m.nodes.length;
  const xMid = (i: number) => xEnd1 + ((xEnd2 - xEnd1) * i) / (n - 1);

  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      className="mt-3 w-full h-auto"
      role="img"
      aria-label={`Assembled chain from ${m.l1} through ${m.lx} to ${m.l2}`}
    >
      {/* endpoint group boxes */}
      <rect x={12} y={28} width={boxW + 10} height={62} rx={10} fill="none"
        stroke="var(--s-blue)" strokeWidth={1.5} opacity={0.8} />
      <rect x={W - boxW - 22} y={28} width={boxW + 10} height={62} rx={10} fill="none"
        stroke="var(--s-blue)" strokeWidth={1.5} opacity={0.8} />

      {m.edges.map((e, i) => {
        const x1 = xMid(i);
        const x2 = xMid(i + 1);
        const cx = (x1 + x2) / 2;
        const isNYC = e.kind === "nyc";
        const isMech = e.kind === "mech";
        const stroke = isNYC
          ? "var(--s-blue)"
          : isMech
            ? "var(--color-muted)"
            : "var(--s-aqua)";
        const dash = isNYC ? "5,4" : isMech ? "2,4" : undefined;
        return (
          <g key={i}>
            <line x1={x1 + 10} x2={x2 - 10} y1={59} y2={59} stroke={stroke}
              strokeWidth={2} strokeDasharray={dash} />
            <text x={cx} y={40} textAnchor="middle" fontSize={10.5}
              fill="var(--chart-ink-2)" fontFamily={SANS}>
              {edgeLabel(e)}
            </text>
            <rect x={x1 + 8} y={30} width={Math.max(x2 - x1 - 16, 1)} height={56} fill="transparent">
              <title>{edgeTip(e, m, measures)}</title>
            </rect>
          </g>
        );
      })}

      {m.nodes.map((cid, i) => {
        const x = xMid(i);
        const isEnd = i === 0 || i === n - 1;
        const lab = nodeLabel(cid);
        return (
          <g key={`${cid}-${i}`}>
            <circle cx={x} cy={59} r={isEnd ? 11 : 8}
              fill={isEnd ? "var(--s-blue)" : "var(--s-aqua)"}
              stroke="var(--paper)" strokeWidth={2}>
              <title>{`${lab}\n${nodeDomain(cid)}`}</title>
            </circle>
            <text x={x} y={isEnd ? 20 : 86} textAnchor="middle" fontSize={10.5}
              fontWeight={isEnd ? 600 : 400} fill="var(--ink)" fontFamily={SANS}>
              {lab.length > 24 ? lab.slice(0, 23) + "…" : lab}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

function edgeLabel(e: MediatedEdge): string {
  if (e.kind === "mech") return "mechanistic link";
  if (e.kind === "nyc") {
    return (
      `NYC-only link · ρ=${e.rho.toFixed(2)}` +
      (e.graph_f ? ` · weak SPG (${e.graph_f}f)` : " · no SPG edge")
    );
  }
  const eff = fmtEffect(e.med, e.et);
  return `f=${e.f} · st=${e.st}` + (eff ? ` · ${eff}` : " · no associations");
}

function edgeTip(e: MediatedEdge, m: MediatedChain, measures: MeasureDict): string {
  if (e.kind === "mech") {
    return `${m.lx} → heat exposure: physical mechanism (hot surfaces drive heat exposure). Assumed, not separately evidenced in either dataset here.`;
  }
  if (e.kind === "nyc") {
    return (
      `${m.lx} → ${m.l2}: carried by NYC data (ρ=${e.rho.toFixed(2)} across UHF42 districts); ` +
      (e.graph_f ? `only ${e.graph_f} SPG finding` : `no SPG edge at all`) +
      (m.r_hop_measures
        ? `. Measured by ${m.r_hop_measures.map((mid) => measures[mid]?.l ?? mid).join(" × ")}.`
        : "")
    );
  }
  return (
    `${m.l1} → ${m.lx}: ${e.f} findings, ${e.st} studies` +
    (e.med !== null
      ? `, median effect ${fmtEffect(e.med, e.et)} (direction only)`
      : ", no associations in the deposit")
  );
}
