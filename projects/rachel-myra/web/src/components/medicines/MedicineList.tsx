// Grouped medicine list for /medicines (P4). Outcome first: one plain line per
// medicine; the full evidence lives on /drug/[id] behind "See the evidence".

import Link from "next/link";
import type { Bucket, DrugRecord } from "@lib/types/knowledge-base.ts";
import { BUCKETS, BUCKET_ORDER, METER } from "@/lib/ui";
import { GROUP_HEADER, guidanceSaysWhatToDo, labelWarnsAboutHeat, prescriberText } from "./plain";

export interface MedicineRow {
  drug: DrugRecord;
  bucket: Bucket | null;
}

function YesNo({ value, yes, no }: { value: boolean | null; yes: string; no: string }) {
  if (value === null)
    return (
      <span className="text-sm text-missing" title="Not checked yet">
        —<span className="sr-only">Not checked yet</span>
      </span>
    );
  // Yes = teal (Store-cool) chip; No = orange (Hold) chip: a missing warning is the problem.
  return value ? (
    <span className="inline-flex items-center gap-1 rounded-full border-2 border-store-ink bg-store-tint px-2.5 py-0.5 text-sm font-semibold text-store-ink">
      <span aria-hidden>✓</span>
      {yes}
    </span>
  ) : (
    <span className="inline-flex items-center gap-1 rounded-full border-2 border-hold-ink bg-hold-tint px-2.5 py-0.5 text-sm font-semibold text-hold-ink">
      <span aria-hidden>✗</span>
      {no}
    </span>
  );
}

function Strength({ meter }: { meter: DrugRecord["evidence"]["meter"] | undefined }) {
  if (!meter || !METER[meter]) return <span className="text-sm text-missing">—</span>;
  const m = METER[meter];
  return (
    <span className="inline-flex items-center gap-1.5 whitespace-nowrap text-sm font-semibold text-hold-ink">
      <span aria-hidden className="inline-flex gap-1">
        {[1, 2, 3].map((i) => (
          <span
            key={i}
            className={`h-3 w-3 rounded-full border-2 ${i <= m.filled ? "border-hold-ink bg-hold-solid" : "border-line bg-page"}`}
          />
        ))}
      </span>
      {m.label}
    </span>
  );
}

/** Heat Dose Compass (knowledge base `compass`): does heat make this medicine act stronger or weaker?
 *  Direction only, never a dose. The chip's tooltip is the compass "meaning" line from the knowledge base. */
function HeatDirection({ compass }: { compass: DrugRecord["compass"] | undefined }) {
  if (!compass?.arrow) return <span className="text-sm text-missing">—</span>;
  const mattersMore = /^effect matters more/i.test(compass.meaning ?? "");
  const kind =
    compass.arrow === "up"
      ? { cls: "border-hold-ink bg-hold-tint text-hold-ink", text: mattersMore ? "↑ Matters more" : "↑ Stronger" }
      : compass.arrow === "down"
        ? { cls: "border-store-ink bg-store-tint text-store-ink", text: "↓ Weaker" }
        : { cls: "border-monitor-ink bg-monitor-tint text-monitor-ink", text: "↕ Depends" };
  return (
    <span
      title={compass.meaning}
      className={`inline-flex items-center whitespace-nowrap rounded-full border-2 px-2.5 py-0.5 text-sm font-semibold ${kind.cls}`}
    >
      {kind.text}
    </span>
  );
}

const COLS = "md:grid md:grid-cols-[minmax(0,2.2fr)_minmax(0,1fr)_minmax(0,0.9fr)_minmax(0,1.2fr)_minmax(0,0.9fr)_minmax(0,0.9fr)] md:gap-4";

const BAR: Record<string, string> = { hold_or_substitute: "hold", adjust_dose: "adjust", monitor: "monitor", storage: "store" };

export function MedicineList({ rows }: { rows: MedicineRow[] }) {
  const groups: { bucket: Bucket | null; rows: MedicineRow[] }[] = [
    ...BUCKET_ORDER.map((b) => ({ bucket: b as Bucket | null, rows: rows.filter((r) => r.bucket === b) })),
    { bucket: null, rows: rows.filter((r) => !r.bucket) },
  ].filter((g) => g.rows.length > 0);

  return (
    <div className="space-y-3">
      {groups.map((g, gi) => {
        const b = g.bucket ? BUCKETS[g.bucket] : null;
        return (
          <details
            key={g.bucket ?? "none"}
            open={gi === 0}
            className="group/d overflow-hidden rounded-tile border-2 bg-page"
            style={{ borderColor: g.bucket ? `var(--bucket-${BAR[g.bucket] ?? "hold"}-ink)` : "var(--ui-line-strong)" }}
          >
            <summary className={`flex cursor-pointer list-none items-center gap-3 px-4 py-3 ${b ? b.tint : "bg-surface"} [&::-webkit-details-marker]:hidden`}>
              <span
                aria-hidden
                className={`inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-md border text-sm font-bold ${b ? b.solid : "border-line-strong"}`}
              >
                {b?.letter ?? "?"}
              </span>
              <h2 id={`grp-${g.bucket ?? "none"}`} className="text-lg font-semibold">
                {g.bucket ? GROUP_HEADER[g.bucket] : "Not grouped yet"}
                <span className="ml-2 text-sm font-normal">
                  {g.rows.length}
                </span>
              </h2>
              <span aria-hidden className="ml-auto text-xl transition group-open/d:rotate-180">⌄</span>
            </summary>

            <div className={`hidden border-b border-line px-4 py-1.5 text-xs font-semibold text-ink-muted ${COLS}`}>
              <span>Medicine</span>
              <span title="Heat Dose Compass: does heat make it act stronger or weaker? Direction only, no doses.">In heat</span>
              <span>Evidence</span>
              <span>Prescriber</span>
              <span>Label warns?</span>
              <span>Guidance?</span>
            </div>
            <ul className="divide-y divide-line text-ink">
              {g.rows.map(({ drug: d }) => (
                <li key={d.id}>
                  <Link
                    href={`/drug/${encodeURIComponent(d.id)}`}
                    className={`group block px-4 py-3 hover:bg-surface focus-visible:bg-surface ${COLS} md:items-center`}
                  >
                    <div className="min-w-0">
                      <p className="font-semibold text-ink underline-offset-2 group-hover:underline">
                        {d.names?.display ?? d.id}
                        <span aria-hidden className="ml-1 text-ink-muted">
                          ›
                        </span>
                      </p>
                      <p className="truncate text-sm text-ink-muted" title={d.label_line || undefined}>{d.label_line || "—"}</p>
                    </div>
                    <dl className="mt-2 grid grid-cols-2 gap-x-4 gap-y-1.5 md:contents">
                      <div>
                        <dt className="text-xs text-ink-muted md:sr-only">In heat</dt>
                        <dd>
                          <HeatDirection compass={d.compass} />
                        </dd>
                      </div>
                      <div className="md:block">
                        <dt className="text-xs text-ink-muted md:sr-only">Evidence</dt>
                        <dd>
                          <Strength meter={d.evidence?.meter} />
                        </dd>
                      </div>
                      <div>
                        <dt className="text-xs text-ink-muted md:sr-only">Prescriber</dt>
                        <dd className="text-sm">{prescriberText(d) || "—"}</dd>
                      </div>
                      <div>
                        <dt className="text-xs text-ink-muted md:sr-only">Label warns?</dt>
                        <dd>
                          <YesNo value={labelWarnsAboutHeat(d)} yes="Yes" no="No" />
                        </dd>
                      </div>
                      <div>
                        <dt className="text-xs text-ink-muted md:sr-only">Guidance?</dt>
                        <dd>
                          <YesNo value={guidanceSaysWhatToDo(d)} yes="Yes" no="No" />
                        </dd>
                      </div>
                    </dl>
                  </Link>
                </li>
              ))}
            </ul>
          </details>
        );
      })}
    </div>
  );
}
