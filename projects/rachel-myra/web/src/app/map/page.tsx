import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { ClinicianMap } from "@/components/map/ClinicianMap";
import { FILES, loadMapPatients } from "@/components/map/data";
import { Timelapse } from "@/components/replay/Timelapse";
import { loadReplay } from "@/lib/replay";

export const metadata: Metadata = { title: "Heat map · Cool-Aid" };

const VIEWS = [
  { id: "forecast", label: "Who is at risk today" },
  { id: "hours", label: "Hour by hour (time-lapse)" },
] as const;
type View = (typeof VIEWS)[number]["id"];

// Clinician heat + help map, with the heat-day time-lapse as a second view (?view=hours).
// Patients load server-side (small); heat areas and help places are fetched by the client
// from /api/map/layers.
export default function MapPage({ searchParams }: { searchParams: Promise<{ view?: string }> }) {
  return (
    <Suspense fallback={<div className="h-[60vh] animate-pulse rounded-xl bg-surface" />}>
      <MapBody searchParams={searchParams} />
    </Suspense>
  );
}

async function MapBody({ searchParams }: { searchParams: Promise<{ view?: string }> }) {
  const { view: v } = await searchParams;
  const view: View = v === "hours" ? "hours" : "forecast";

  return (
    <div className="space-y-4">
      <header className="flex flex-wrap items-end justify-between gap-x-6 gap-y-1">
        <div className="space-y-1">
          <h1 className="text-2xl font-bold sm:text-3xl">Who is at risk in the heat, and where to cool off</h1>
          <p className="text-[var(--ui-ink-muted,#4b5563)]">Each person icon is a patient&apos;s home. Click one or a neighborhood.</p>
        </div>
        <nav aria-label="Other views" className="flex gap-4 text-sm text-[var(--ui-ink-muted,#4b5563)]">
          <Link href="/board" className="underline-offset-2 hover:underline">Clinician list</Link>
          <Link href="/phone" className="underline-offset-2 hover:underline">Patient app</Link>
        </nav>
      </header>

      <nav aria-label="Map view" className="inline-flex rounded-full border border-line bg-surface p-1 text-sm font-semibold">
        {VIEWS.map((x) => (
          <Link
            key={x.id}
            href={x.id === "forecast" ? "/map" : `/map?view=${x.id}`}
            aria-current={view === x.id ? "page" : undefined}
            className={
              view === x.id
                ? "rounded-full bg-[var(--bucket-store-solid,#0e7c86)] px-4 py-1.5 text-white"
                : "rounded-full px-4 py-1.5 text-ink-muted hover:text-ink"
            }
          >
            {x.label}
          </Link>
        ))}
      </nav>

      {view === "hours" ? <HoursView /> : <ForecastView />}
    </div>
  );
}

function ForecastView() {
  const patients = loadMapPatients();
  return patients.length ? (
    <ClinicianMap patients={patients} files={{ panel: FILES.panel, patients: FILES.patients }} />
  ) : (
    <p className="rounded-xl border border-dashed p-4 text-sm">
      Patients go here: {FILES.panel} and {FILES.patients} (not found).
    </p>
  );
}

function HoursView() {
  const data = loadReplay();
  return data ? (
    <Timelapse data={data} embedded />
  ) : (
    <p className="rounded-xl border border-dashed p-4 text-sm">
      Data goes here: data/processed/replay_heatwave_hourly.csv, hvi_modzcta.geojson, synthetic/patients.csv,
      panel_scores_replay.json (not found).
    </p>
  );
}
