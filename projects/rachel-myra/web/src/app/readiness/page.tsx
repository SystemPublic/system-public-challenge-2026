import type { Metadata } from "next";
import { ENV_LABELS } from "@lib/thermal/index.ts";
import { Placeholder } from "@/components/Placeholder";

export const metadata: Metadata = { title: "Heat-Wave Readiness · Cool-Aid" };

export default function ReadinessPage() {
  return (
    <div className="space-y-6">
      <header className="space-y-1">
        <h1 className="text-3xl font-bold">Heat-Wave Readiness</h1>
        <p className="text-ink-muted">Is heat coming, and what happens to our patients&apos; medicines if it does?</p>
      </header>

      <Placeholder title="Heat-wave probability bar + heat context strip" spec="§6.6">
        NOAA forecasts and historical odds; 7-day HeatRisk, overnight low and humidity for the selected ZIP.
      </Placeholder>

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <Placeholder title="Call-first scatter" spec="§4.3">
            Each dot is a synthetic patient: x = personal heat exposure, y = medication heat-risk stack, color = action
            bucket. Shaded &ldquo;call first&rdquo; zone; lasso to send the safety alert.
          </Placeholder>
        </div>
        <Placeholder title="Ranked call list" spec="§4.3">
          Rank, patient, medicines, why, action. Tier bands: call today / this week / routine.
        </Placeholder>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Placeholder title="Heat-wave simulator" spec="§4.3">
          Pick severity and length, or replay a past NYC heat wave.
        </Placeholder>
        <Placeholder title="72-hour playbook" spec="§4.3">
          Where / who / what for the demo ZIPs.
        </Placeholder>
      </div>

      <Placeholder title="3D NYC map" spec="§4.3, §5 #20">
        Needs deck.gl + MapLibre (see web/README.md).
      </Placeholder>

      <section className="rounded-tile border border-line p-4">
        <h2 className="text-lg font-bold">Heat-safe delivery: where a package waits</h2>
        <p className="text-sm text-ink-muted">
          Stage 2 (dispense / ship). Places modeled by the shared thermal engine in <code>lib/thermal</code>; the
          pre-ship check UI is still to come.
        </p>
        <ul className="mt-2 grid gap-1 text-sm sm:grid-cols-2">
          {Object.entries(ENV_LABELS).map(([k, v]) => (
            <li key={k}>{v}</li>
          ))}
        </ul>
      </section>
    </div>
  );
}
