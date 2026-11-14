import type { Metadata } from "next";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Placeholder } from "@/components/Placeholder";
import { loadPanel } from "@/lib/panel";
import { patientWhy, plainName, RISK, riskGroup } from "@/lib/risk";

export const metadata: Metadata = { title: "Patient app · Cool-Aid" };

// Pick which synthetic patient the patient app plays. Story patients first (S01–S10).
export default function PhonePicker() {
  const panel = loadPanel("replay");
  if (!panel) {
    return <Placeholder title="Patient app">Data goes here: data/processed/panel_scores_replay.json</Placeholder>;
  }
  const story = panel.data.patients.filter((p) => p.storyLabel).sort((a, b) => a.patientId.localeCompare(b.patientId));
  return (
    <div className="mx-auto max-w-2xl space-y-8">
      <header className="space-y-3 text-center">
        <p className="text-sm font-medium text-muted-foreground">Patient app · Heat wave · June 24</p>
        <h1 className="text-3xl font-semibold tracking-tight">Your heat plan</h1>
        <p className="text-lg text-muted-foreground">Pick a patient to see their plan for today. All patients are synthetic.</p>
        <Button asChild size="lg" className="h-12 text-base">
          <Link href="/phone/signup">New here? Get your heat plan</Link>
        </Button>
      </header>
      <Card className="overflow-hidden"><ul className="divide-y divide-border">
        {story.map((p) => {
          const g = riskGroup(p.readiness?.level);
          return (
            <li key={p.patientId}>
              <Link href={`/phone/${p.patientId}`} className="block min-h-tap px-4 py-3 hover:bg-accent">
                <span className="flex flex-wrap items-center gap-2">
                  <span className="font-semibold">{plainName(p.displayName)}</span>
                  <span className="text-sm text-muted-foreground">· {p.age}</span>
                  <span className={`inline-flex items-center whitespace-nowrap rounded-full border px-2.5 py-0.5 text-xs font-semibold ${RISK[g].chip}`}>{RISK[g].label} risk</span>
                </span>
                <span className="mt-0.5 block text-sm text-muted-foreground">{patientWhy(p)}</span>
              </Link>
            </li>
          );
        })}
      </ul></Card>
    </div>
  );
}
