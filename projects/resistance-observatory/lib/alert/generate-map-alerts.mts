// Generates data/alerts.json: the Alert tab's default alerts for every
// country, for the Forecast map. Run: node lib/alert/generate-map-alerts.mts
//
// Each country is judged by its region's default rule, on genome counts only:
//   East and Southern Africa -> moves into a new WHO band (published 40% / 60% lines)
//   Central and West Africa  -> first detection (may use cells under 20 samples, badged weak)
//   outside Africa           -> change of at least the preset number of points
// Cells need at least `min_samples` (20) to count, except first detections.
import { readFileSync, writeFileSync } from "node:fs";
import { deriveAlerts, type AlertEvent, type Cell, type Trigger, type Watch } from "./derive.ts";

const root = new URL("../../", import.meta.url);
const read = (f: string) => JSON.parse(readFileSync(new URL(`k540e-data-pack/${f}`, root), "utf8"));

export const MARKER_ID = "pfdhps-K540E";
const MARKER_KEY = "dhps_K540E";
const DEFAULT_TRIGGER: Record<string, Trigger> = {
  east_southern_africa: "who_band",
  central_west_africa: "first_detection",
  outside_africa: "change",
};
const BAND: Record<string, string> = { low: "low", medium: "medium", high: "high", very_high: "very high" };

export type MapAlert = { id: string; marker_id: string; country_iso3: string; year: number; rule: string; headline: string };

const p1 = (v: number) => `${v.toFixed(1)}%`;

function headline(e: AlertEvent, country: string, minN: number): string {
  const c = e.cell!;
  const count = `${c.x} of ${c.n} samples, ${p1(c.pct)}`;
  if (e.rule === "band_change") {
    return `${country}, collected ${c.year}: K540E moves from the ${BAND[e.prevBand!]} to the ${BAND[e.band!]} WHO band (${count}; previous sampled year ${e.prev!.year}: ${p1(e.prev!.pct)})`;
  }
  if (e.rule === "first_detection") {
    const weak = e.strength === "weak" ? "single positive sample" : e.belowMinN ? `fewer than ${minN} samples` : null;
    return `${country}, collected ${c.year}: K540E first detected (${count}) after none in ${e.priorNegative!.lastTested} samples in ${e.priorNegative!.lastYear}${weak ? ` — weak signal: ${weak}` : ""}`;
  }
  const d = e.delta!;
  return `${country}, collected ${c.year}: K540E ${d > 0 ? "up" : "down"} ${Math.abs(d).toFixed(1)} points in ${e.yearsApart} year${e.yearsApart === 1 ? "" : "s"} (${count}; ${e.prev!.year}: ${p1(e.prev!.pct)}) — project preset, no published threshold`;
}

export function buildMapAlerts(): MapAlert[] {
  const genomes = read("k540e-genomes.json");
  const presets = read("k540e-thresholds.json").presets;
  const cells = (key: string): Cell[] => genomes.observations[key].map(([iso3, year, x, n]: [string, number, number, number]) => ({ iso3, year, x, n }));
  const data = { cells: cells(MARKER_KEY), a581g: cells("dhps_A581G") };
  const out: MapAlert[] = [];
  for (const iso3 of Object.keys(genomes.countries).sort()) {
    const info = genomes.countries[iso3];
    const watch: Watch = { marker: MARKER_KEY, area: iso3, trigger: DEFAULT_TRIGGER[info.who_basis], level: 60, points: presets.change_points, minN: presets.min_samples };
    for (const e of deriveAlerts(watch, data)) {
      if (!e.fired || e.source !== "genomes") continue;
      out.push({ id: `k540e-${iso3}-${e.year}-${e.rule}`, marker_id: MARKER_ID, country_iso3: iso3, year: e.year, rule: e.rule, headline: headline(e, info.country, watch.minN) });
    }
  }
  return out.sort((a, b) => a.year - b.year || a.country_iso3.localeCompare(b.country_iso3));
}

if (process.argv[1] && import.meta.url.endsWith(process.argv[1].split("/").pop()!)) {
  const alerts = buildMapAlerts();
  writeFileSync(new URL("data/alerts.json", root), JSON.stringify(alerts, null, 2) + "\n");
  console.log(`wrote data/alerts.json: ${alerts.length} alerts in ${new Set(alerts.map((a) => a.country_iso3)).size} countries`);
}
