import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Placeholder } from "@/components/Placeholder";
import { StageViews } from "@/components/StageViews";
import { STAGES } from "@/lib/journey";

export function generateStaticParams() {
  return STAGES.map((s) => ({ stage: s.id }));
}

export async function generateMetadata({ params }: PageProps<"/journey/[stage]">): Promise<Metadata> {
  const { stage } = await params;
  const s = STAGES.find((x) => x.id === stage);
  return { title: `${s?.name ?? "Journey"} · Cool-Aid` };
}

export default async function StagePage({ params }: PageProps<"/journey/[stage]">) {
  const { stage } = await params;
  const i = STAGES.findIndex((x) => x.id === stage);
  if (i < 0) notFound();
  const s = STAGES[i];
  const prev = STAGES[i - 1];
  const next = STAGES[i + 1];

  return (
    <div className="space-y-6">
      <header className="space-y-1">
        <p className="text-sm font-semibold text-ink-muted">
          Step {s.n} of {STAGES.length}
        </p>
        <h1 className="text-3xl font-bold">{s.name}</h1>
        <p className="text-lg">{s.heat}</p>
      </header>

      <div className="grid gap-4 md:grid-cols-2">
        <section className="rounded-tile border border-line p-4">
          <h2 className="font-bold">Clinicians and health systems</h2>
          <p className="text-sm">{s.clinician}</p>
        </section>
        <section className="rounded-tile border border-line p-4">
          <h2 className="font-bold">Patients and caregivers</h2>
          <p className="text-sm">{s.patient}</p>
        </section>
      </div>

      <div className="flex flex-wrap gap-2">
        {s.links.map((l) => (
          <Link key={l.href + l.label} href={l.href} className="rounded border-2 border-ink px-3 py-1.5 text-sm font-semibold">
            {l.label} →
          </Link>
        ))}
      </div>

      <StageViews
        panels={{
          map: <Placeholder title={`3D NYC map: ${s.name}`} spec="§4.3" />,
          graph: <Placeholder title={`Node graph: ${s.name}`} spec="§5 #4" />,
          patient: <Placeholder title={`Patient view: ${s.name}`} spec="§4.5" />,
        }}
      />

      <nav className="flex justify-between border-t border-line pt-4 text-sm" aria-label="Journey steps">
        {prev ? <Link href={`/journey/${prev.id}`}>← {prev.name}</Link> : <span />}
        {next ? <Link href={`/journey/${next.id}`}>{next.name} →</Link> : <span />}
      </nav>
    </div>
  );
}
