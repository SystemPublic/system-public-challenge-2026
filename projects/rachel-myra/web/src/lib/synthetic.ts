// Server-only readers for the synthetic-patient CSVs and the replay hourly heat.
//   data/processed/synthetic/questionnaire.csv  (alert_opt_in, q5_can_reach_cool_place, ...)
//   data/processed/replay_heatwave_hourly.csv   (LaGuardia hourly temp + heat index)
// Read-only; nothing here invents values.

import fs from "node:fs";
import path from "node:path";
import type { DrugRecord } from "@lib/types/knowledge-base.ts";
import { REPO_ROOT, getDrugs } from "@/lib/kb";

export function parseCsv(text: string): Record<string, string>[] {
  const rows: string[][] = [];
  let row: string[] = [];
  let cell = "";
  let q = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (q) {
      if (c === '"' && text[i + 1] === '"') { cell += '"'; i++; }
      else if (c === '"') q = false;
      else cell += c;
    } else if (c === '"') q = true;
    else if (c === ",") { row.push(cell); cell = ""; }
    else if (c === "\n" || c === "\r") {
      if (c === "\r" && text[i + 1] === "\n") i++;
      row.push(cell); cell = "";
      if (row.length > 1 || row[0] !== "") rows.push(row);
      row = [];
    } else cell += c;
  }
  if (cell || row.length) { row.push(cell); rows.push(row); }
  const [head, ...body] = rows;
  return body.map((r) => Object.fromEntries(head.map((h, i) => [h, r[i] ?? ""])));
}

const cache = globalThis as unknown as { __csv?: Map<string, Record<string, string>[]> };

function readCsv(rel: string): Record<string, string>[] | null {
  cache.__csv ??= new Map();
  const hit = cache.__csv.get(rel);
  if (hit) return hit;
  const f = path.join(REPO_ROOT, rel);
  if (!fs.existsSync(f)) return null;
  const rows = parseCsv(fs.readFileSync(f, "utf8"));
  cache.__csv.set(rel, rows);
  return rows;
}

export const QUESTIONNAIRE_FILE = "data/processed/synthetic/questionnaire.csv";
export const HOURLY_FILE = "data/processed/replay_heatwave_hourly.csv";

export function questionnaire(): Map<string, Record<string, string>> {
  return new Map((readCsv(QUESTIONNAIRE_FILE) ?? []).map((r) => [r.patient_id, r]));
}

/** Patient ids with alert_opt_in = false (they get a call, not a text). */
export function callInsteadIds(): string[] {
  return [...questionnaire().values()].filter((r) => r.alert_opt_in === "false").map((r) => r.patient_id);
}

export interface HourHeat { hour: number; tempF: number; heatIndexF: number | null }

/** Hourly heat for one replay day (default: the demo day 2025-06-24). */
export function hourlyHeat(date = "2025-06-24"): { station: string; hours: HourHeat[] } | null {
  const rows = readCsv(HOURLY_FILE);
  if (!rows) return null;
  const day = rows.filter((r) => r.date_local === date);
  const byHour = new Map<number, HourHeat>();
  for (const r of day) {
    const h = Number(r.hour_local);
    if (byHour.has(h) || r.temp_f === "") continue;
    byHour.set(h, { hour: h, tempF: Number(r.temp_f), heatIndexF: r.heat_index_f === "" ? null : Number(r.heat_index_f) });
  }
  return { station: day[0]?.station_name ?? "", hours: [...byHour.values()].sort((a, b) => a.hour - b.hour) };
}

/** Knowledge-base record for a medicine name as it appears in panel_scores (e.g. "furosemide"). */
export function kbDrugFor(name: string): DrugRecord | null {
  const n = name.toLowerCase();
  for (const d of getDrugs()) {
    const names = [
      d.id,
      d.names?.display,
      ...(d.names?.examples ?? []),
      ...((d.names as unknown as { ingredients?: { name: string }[] } | undefined)?.ingredients ?? []).map((i) => i.name),
    ]
      .filter(Boolean)
      .map((x) => String(x).toLowerCase());
    if (names.some((x) => x === n || x.startsWith(n + " ") || n.startsWith(x + " "))) return d;
  }
  return null;
}
