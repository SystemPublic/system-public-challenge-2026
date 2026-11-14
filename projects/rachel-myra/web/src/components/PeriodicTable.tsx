"use client";

// Evidence Map "periodic table" (spec §4.1). One tile per drug or class.
// Tile color = action bucket; fill = evidence strength (solid / pale / outline);
// corner = evidence tier; chips = prescribers; dashed ring + "!" = guidance gap.

import Link from "next/link";
import { useMemo, useState } from "react";
import type { Bucket, Meter } from "@lib/types/knowledge-base.ts";
import { BUCKET_ORDER, BUCKETS, METER, prescriberAbbr } from "@/lib/ui";
import { Dash, EvidenceMeter, GapBadge } from "./badges";

export interface TileData {
  id: string;
  name: string;
  classLabel: string | null;
  bucket: Bucket | null;
  meter: Meter | null;
  tierCode: number | null;
  tierLabel: string | null;
  prescribers: string[];
  gap: boolean;
  pediatric: boolean;
}

function Tile({ t }: { t: TileData }) {
  const b = t.bucket ? BUCKETS[t.bucket] : null;
  const fill = t.meter ? METER[t.meter]?.fill : "outline";
  const colorCls = b ? b[fill ?? "outline"] : "bg-page text-ink border-line-strong";
  const ring = t.gap ? "outline-2 outline-offset-2 outline-dashed outline-gap-ring" : "";
  return (
    <Link
      href={`/drug/${encodeURIComponent(t.id)}`}
      className={`relative flex min-h-36 flex-col justify-between rounded-tile border-2 p-3 transition hover:-translate-y-0.5 hover:shadow-md ${colorCls} ${ring}`}
    >
      <div className="flex items-start justify-between gap-2">
        <span aria-hidden className="text-xs font-bold opacity-90">
          {b?.letter ?? "?"}
        </span>
        <span className="flex items-center gap-1">
          {t.gap && <GapBadge />}
          <span className="rounded bg-page/90 px-1 text-[11px] font-semibold text-ink" title={t.tierLabel ?? "Tier not graded"}>
            {t.tierCode ? `T${t.tierCode}` : "T—"}
          </span>
        </span>
      </div>
      <div>
        <div className="text-base font-bold leading-tight">{t.name}</div>
        <div className="text-xs leading-snug opacity-90">{t.classLabel ?? ""}</div>
      </div>
      <div className="mt-2 flex flex-wrap items-center gap-1">
        <span className="rounded bg-page/90 px-1 py-0.5 text-ink">
          <EvidenceMeter meter={t.meter} />
        </span>
        {t.prescribers.slice(0, 3).map((p) => (
          <span key={p} className="rounded bg-page/90 px-1 py-0.5 text-[11px] font-medium text-ink" title={p}>
            {prescriberAbbr(p)}
          </span>
        ))}
        {t.prescribers.length > 3 && (
          <span className="rounded bg-page/90 px-1 py-0.5 text-[11px] text-ink">+{t.prescribers.length - 3}</span>
        )}
      </div>
    </Link>
  );
}

export function PeriodicTable({ tiles }: { tiles: TileData[] }) {
  const [buckets, setBuckets] = useState<Set<Bucket>>(new Set(BUCKET_ORDER));
  const [prescriber, setPrescriber] = useState<string>("all");
  const [gapOnly, setGapOnly] = useState(false);

  const prescribers = useMemo(
    () => Array.from(new Set(tiles.flatMap((t) => t.prescribers))).sort(),
    [tiles],
  );

  const visible = tiles.filter(
    (t) =>
      (!t.bucket || buckets.has(t.bucket)) &&
      (prescriber === "all" ||
        (prescriber === "__peds" ? t.pediatric : t.prescribers.includes(prescriber))) &&
      (!gapOnly || t.gap),
  );

  const toggle = (b: Bucket) =>
    setBuckets((prev) => {
      const next = new Set(prev);
      if (next.has(b)) next.delete(b);
      else next.add(b);
      return next;
    });

  const groups: { key: string; bucket: Bucket | null; tiles: TileData[] }[] = [
    ...BUCKET_ORDER.map((b) => ({ key: b, bucket: b as Bucket | null, tiles: visible.filter((t) => t.bucket === b) })),
    { key: "none", bucket: null, tiles: visible.filter((t) => !t.bucket) },
  ].filter((g) => g.tiles.length > 0);

  return (
    <div className="space-y-6">
      <fieldset className="flex flex-wrap items-center gap-2 rounded-tile border border-line bg-surface p-3 text-sm">
        <legend className="sr-only">Filters</legend>
        {BUCKET_ORDER.map((b) => {
          const s = BUCKETS[b];
          const on = buckets.has(b);
          return (
            <button
              key={b}
              type="button"
              aria-pressed={on}
              onClick={() => toggle(b)}
              className={`inline-flex items-center gap-1.5 rounded-full border-2 px-2.5 py-1 font-semibold ${
                on ? s.tint : "border-line bg-page text-ink-muted line-through"
              }`}
            >
              <span aria-hidden className={`inline-flex h-4 w-4 items-center justify-center rounded-sm text-[10px] ${s.solid}`}>
                {s.letter}
              </span>
              {s.label}
            </button>
          );
        })}
        <label className="ml-auto inline-flex items-center gap-1.5">
          Prescriber
          <select
            value={prescriber}
            onChange={(e) => setPrescriber(e.target.value)}
            className="rounded border border-line-strong bg-page px-2 py-1"
          >
            <option value="all">All</option>
            <option value="__peds">Pediatrics lens</option>
            {prescribers.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
        </label>
        <label className="inline-flex items-center gap-1.5">
          <input type="checkbox" checked={gapOnly} onChange={(e) => setGapOnly(e.target.checked)} />
          Guidance gaps only
        </label>
      </fieldset>

      {groups.length === 0 && (
        <p className="text-ink-muted">
          No medicines match these filters. <Dash />
        </p>
      )}

      {groups.map((g) => (
        <section key={g.key} aria-labelledby={`bucket-${g.key}`}>
          <h2 id={`bucket-${g.key}`} className="mb-2 flex items-baseline gap-2">
            <span className="text-lg font-bold">{g.bucket ? BUCKETS[g.bucket].label : "No bucket yet"}</span>
            <span className="text-sm text-ink-muted">{g.bucket ? BUCKETS[g.bucket].plain : ""}</span>
          </h2>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
            {g.tiles.map((t) => (
              <Tile key={t.id} t={t} />
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}

/** Legend explaining color, fill, ring and corner tier. */
export function MapLegend() {
  return (
    <div className="flex flex-wrap gap-x-6 gap-y-2 rounded-tile border border-line p-3 text-xs">
      <div className="flex items-center gap-2">
        <span className="font-semibold">Fill = evidence:</span>
        <span className="rounded border-2 border-monitor-solid bg-monitor-solid px-1.5 text-monitor-on">Strong</span>
        <span className="rounded border-2 border-monitor-ink bg-monitor-tint px-1.5 text-monitor-ink">Some</span>
        <span className="rounded border-2 border-monitor-ink bg-page px-1.5 text-monitor-ink">Early signs</span>
      </div>
      <div className="flex items-center gap-2">
        <span className="inline-block h-4 w-6 rounded outline-2 outline-dashed outline-gap-ring" aria-hidden />
        <GapBadge /> Guidance gap
      </div>
      <div>
        <span className="font-semibold">T1–T8</span> = best evidence tier (T1 strongest). Letters A / H / M / S repeat the color.
      </div>
    </div>
  );
}
