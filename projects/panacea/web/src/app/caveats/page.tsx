import type { Metadata } from "next";
import { getBundle } from "@/lib/bundle";
import { deEmdash } from "@/lib/format";
import {
  ModeledBar,
  SpotChart,
  VintageChart,
  VintageLegend,
} from "@/components/caveats/charts";

export const metadata: Metadata = { title: "caveats" };

export default function CaveatsPage() {
  const c = getBundle().contested;
  const m = c.modeled;
  return (
    <div className="mx-auto w-full max-w-[72rem] px-6 sm:px-10">
      <div className="mt-12 max-w-[62rem]">
        <h1 className="text-[clamp(1.8rem,4vw,2.6rem)] leading-tight font-normal">
          Caveats the cross-dataset claims must carry
        </h1>
        <p className="mt-3 text-[1.05rem] leading-relaxed text-[color:var(--chart-ink-2)]">
          Five caveats the concept map forces on every claim, the flagship
          direction spot-checks, and the measurement vintages underneath.
        </p>
      </div>

      {/* the five contested findings */}
      <div className="mt-10 grid max-w-[62rem] gap-x-10 gap-y-8 md:grid-cols-2">
        {c.cards.map((card) => (
          <section key={card.t} className="border-t border-rule pt-4">
            <h2 className="text-[1.15rem] font-medium">{card.t}</h2>
            <p className="mt-2 text-[0.95rem] leading-relaxed text-[color:var(--chart-ink-2)]">
              {deEmdash(card.b)}
            </p>
          </section>
        ))}

        {/* spot checks */}
        <section className="border-t border-rule pt-4 md:col-span-2">
          <h2 className="text-[1.15rem] font-medium">
            Spot-check direction tests (ρ, UHF42)
          </h2>
          <SpotChart spot={c.spot} />
          <p className="mt-2 max-w-[60rem] font-sans text-[0.72rem] text-muted">
            Cross-sectional across 42 districts: directional evidence only.
            Hover a bar for the expectation behind each check.
          </p>
        </section>

        {/* modeled vs observed */}
        <section className="border-t border-rule pt-4 md:col-span-2">
          <h2 className="text-[1.15rem] font-medium">
            City correlation checks: modeled vs observed
          </h2>
          <div className="max-w-[560px]">
            <ModeledBar modeled={m} />
          </div>
          <p className="mt-2 max-w-[60rem] font-sans text-[0.72rem] leading-relaxed text-muted">
            {m.conf_modeled} of {m.conf_observed + m.conf_modeled} computed
            checks include a modeled burden measure; {m.conf_no_rho} confirmed
            pairs have no district-level check (death causes are
            citywide-only).
          </p>
        </section>

        {/* vintages */}
        <section className="border-t border-rule pt-4 md:col-span-2">
          <h2 className="text-[1.15rem] font-medium">
            Measurement vintages: why cross-dataset claims must cite years
          </h2>
          <VintageChart vintage={c.vintage} />
          <VintageLegend />
          <p className="mt-2 max-w-[60rem] font-sans text-[0.72rem] text-muted">
            Reduced-opacity bars are modeled attributions, not observations.
            Hover a bar for collection and year range.
          </p>
        </section>
      </div>
    </div>
  );
}
