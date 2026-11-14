import type { Metadata } from "next";
import { Dash } from "@/components/badges";
import { KbSourceBanner } from "@/components/KbSourceBanner";
import { loadKb, primaryBucket } from "@/lib/kb";
import { BUCKETS } from "@/lib/ui";

export const metadata: Metadata = { title: "My Medicine Cabinet · Cool-Aid" };

// Patient side: large type, high contrast, simple words, big tap targets (spec §3.3).
// Demo cabinet = first few KB medicines until the synthetic panel is wired in.
export default function PatientPage() {
  const { kb, source, file } = loadKb();
  const meds = kb.drugs.slice(0, 6);

  return (
    <div className="mx-auto max-w-3xl space-y-8 text-patient-base leading-relaxed">
      <header className="space-y-2">
        <h1 className="text-patient-2xl font-bold leading-tight">My Medicine Cabinet</h1>
        <p className="text-ink-muted">Your medicines, and what to do when it gets hot.</p>
        <p className="text-base text-ink-muted">Example cabinet for the demo. Not a real patient.</p>
      </header>
      <KbSourceBanner source={source} file={file} />

      <section aria-label="Cabinet shelf" className="rounded-tile border-4 border-ink bg-surface p-5">
        <ul className="grid grid-cols-2 gap-5 sm:grid-cols-3">
          {meds.map((d) => {
            const bucket = primaryBucket(d);
            const b = bucket ? BUCKETS[bucket] : null;
            return (
              <li key={d.id} className="flex flex-col items-center gap-2 text-center">
                <div
                  aria-hidden
                  className={`flex h-28 w-20 flex-col items-center justify-center rounded-b-xl rounded-t-md border-4 text-patient-xl font-bold ${
                    b ? b.solid : "border-line-strong bg-page"
                  }`}
                >
                  {b?.letter ?? "?"}
                </div>
                <span className="font-semibold">{d.names?.plain || d.names?.display || d.id}</span>
                <span className="text-base text-ink-muted">{b?.label ?? "—"}</span>
              </li>
            );
          })}
        </ul>
      </section>

      <section className="space-y-4">
        <h2 className="text-patient-xl font-bold">If heat is coming</h2>
        {meds.map((d) => {
          const msg = d.patient_messages?.find((m) => m.situation === "heat_forecast") ?? d.patient_messages?.[0];
          return (
            <article key={d.id} className="rounded-tile border-2 border-line-strong p-4">
              <h3 className="text-patient-lg font-bold">{d.names?.plain || d.names?.display}</h3>
              <p>{msg?.en ?? <Dash what="Message not written yet" />}</p>
            </article>
          );
        })}
        <p className="font-semibold">Talk to your doctor or pharmacist before changing any medicine.</p>
      </section>

      <section className="grid gap-3 sm:grid-cols-2">
        <button type="button" className="min-h-tap rounded-tile bg-primary px-5 font-bold text-primary-foreground" disabled>
          I&apos;m OK
        </button>
        <button type="button" className="min-h-tap rounded-tile border-4 border-ink px-5 font-bold" disabled>
          I feel unwell
        </button>
        <p className="text-base text-ink-muted sm:col-span-2">Check-in buttons are not connected yet (simulated in the demo).</p>
      </section>
    </div>
  );
}
