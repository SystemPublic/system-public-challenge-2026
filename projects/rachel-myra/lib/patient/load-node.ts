// Node-only loaders (fs) for scripts and tests. The app can do the same with fetch.
// Everything optional (knowledge base, routed travel times) degrades gracefully and the
// fallback used is reported in `notes`.

import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import type { HealthSystemConfig } from "../types/health-system.ts";
import type { PatientRecord } from "../types/patient.ts";
import type { CoolingPlace } from "./cooling.ts";
import { placesFromGeoJson } from "./cooling.ts";
import { parseCsv } from "./csv.ts";
import type { DrugProfileIndex } from "./drug-profiles.ts";
import { overlayKnowledgeBase, provisionalIndex } from "./drug-profiles.ts";
import type { TravelLookup } from "./escalation.ts";
import type { NeighborhoodData } from "./exposure.ts";
import { patientsFromFhirBundle } from "./fhir.ts";
import type { ForecastInputs } from "./forecast.ts";
import { cpcFromJson, heatRiskFromCurrentJson, heatRiskFromReplayCsv, historyFromCsv } from "./forecast.ts";
import type { SystemPathwayIndex } from "./stacking.ts";

export interface Loaded<T> {
  value: T;
  notes: string[];
}

const read = (root: string, p: string) => readFileSync(join(root, p), "utf8");

export function loadConfig(root: string, id = "sbh"): HealthSystemConfig {
  return JSON.parse(read(root, `config/health-systems/${id}.json`));
}

export function loadPatients(root: string, bundlePath = "data/processed/synthetic/patients_fhir.json"): PatientRecord[] {
  return patientsFromFhirBundle(JSON.parse(read(root, bundlePath)));
}

export function loadDrugIndex(root: string, cfg: HealthSystemConfig): Loaded<DrugProfileIndex> {
  let idx = provisionalIndex();
  const notes: string[] = [];
  const acbPath = cfg.data_sources.knowledge_base.find((p) => /anticholinergic/i.test(p));
  let acbRows: Record<string, string>[] = [];
  if (acbPath && existsSync(join(root, acbPath))) {
    acbRows = parseCsv(read(root, acbPath));
    notes.push(`ACB scores: ${acbPath} (${acbRows.length} rows)`);
  }
  for (const p of cfg.data_sources.knowledge_base.filter((x) => x.endsWith(".json"))) {
    if (!existsSync(join(root, p))) continue;
    try {
      const label = /mock/.test(p) ? "mock_knowledge_base" : "knowledge_base";
      const { index, matched } = overlayKnowledgeBase(idx, JSON.parse(read(root, p)), label, acbRows);
      if (matched > 0) {
        idx = index;
        notes.push(`Drug → heat-defense mapping: ${p} (${matched} drug rows matched)`);
        break; // first (most authoritative) KB that matches wins
      }
      notes.push(`${p} present but no drug rows recognized; kept provisional mapping`);
    } catch (e) {
      notes.push(`${p} unreadable (${(e as Error).message}); kept provisional mapping`);
    }
  }
  if (!idx.sources.some((s) => s !== "provisional")) {
    if (acbRows.length) idx = overlayKnowledgeBase(idx, [], "knowledge_base", acbRows).index;
    notes.push("Drug → heat-defense mapping: PROVISIONAL (lib/patient/provisional-drug-map.ts); knowledge base not available yet");
  }
  return { value: idx, notes };
}

export function loadForecast(root: string, cfg: HealthSystemConfig, mode: "current" | "replay"): ForecastInputs {
  const ds = cfg.data_sources;
  const heatrisk =
    mode === "current"
      ? heatRiskFromCurrentJson(JSON.parse(read(root, ds.heatrisk_current)))
      : heatRiskFromReplayCsv(read(root, ds.heatrisk_replay));
  return {
    heatrisk,
    heatriskLabel:
      mode === "current"
        ? `NWS HeatRisk (${ds.heatrisk_current})`
        : `NWS/WPC HeatRisk archive, day-1 values replayed as the forecast (${ds.heatrisk_replay})`,
    cpc: cpcFromJson(JSON.parse(read(root, ds.cpc_outlook))),
    history: historyFromCsv(read(root, ds.historical_odds), ds.historical_odds_column, ds.historical_within_14d_column),
  };
}

export function loadNeighborhood(root: string, cfg: HealthSystemConfig): NeighborhoodData {
  const ds = cfg.data_sources;
  const hviByZip = new Map<string, number>();
  for (const r of parseCsv(read(root, ds.hvi_by_zip))) {
    const z = r.zcta20 ?? r.modzcta ?? r.zip;
    const v = Number(r.hvi);
    if (z && Number.isFinite(v)) hviByZip.set(z, v);
  }
  const ac = parseCsv(read(root, ds.ac_households));
  const pctNoAcByZip = new Map<string, { pct: number; area: string; approximate: boolean }>();
  for (const [zip, area] of Object.entries(ds.zip_to_ac_area)) {
    const row = ac.find(
      (r) => r.geotype === area.geotype && r.geoid === area.geoid && Number(r.year) === ds.ac_year && r.measure === "pct_households_with_ac",
    );
    if (row) pctNoAcByZip.set(zip, { pct: +(100 - Number(row.value)).toFixed(1), area: `${area.name} (${area.geotype} ${ds.ac_year})`, approximate: area.approximate });
  }
  return { hviByZip, pctNoAcByZip };
}

/** Routed travel times when the routing agent has produced them; else the naive placeholder. */
export function loadTravel(root: string, cfg: HealthSystemConfig): Loaded<TravelLookup> {
  const r = cfg.data_sources.routing;
  const out: TravelLookup = new Map();
  const notes: string[] = [];
  if (existsSync(join(root, r.contacts_routed))) {
    const rows = parseCsv(read(root, r.contacts_routed));
    const prefs = [
      ...(r.contact_travel_columns ?? []),
      ...["best_travel_min", "routed_travel_min", "travel_min", "travel_time_min", "duration_min"].map((m) => ({ minutes: m, mode: "mode", why: "generic" })),
    ].filter((c) => rows[0] && c.minutes in rows[0]);
    if (prefs.length && rows[0] && "contact_id" in rows[0]) {
      const used: Record<string, number> = {};
      for (const row of rows) {
        const c = prefs.find((c) => row[c.minutes] !== "" && Number.isFinite(Number(row[c.minutes])));
        if (!c) continue;
        used[c.minutes] = (used[c.minutes] ?? 0) + 1;
        const engine = row.routing_engine ? `, ${row.routing_engine}` : "";
        out.set(row.contact_id, { minutes: Number(row[c.minutes]), mode: `${row[c.mode] || "routed"}${engine}`, source: "routed" });
      }
      notes.push(`Contact travel: ROUTED (${r.contacts_routed}; columns used: ${Object.entries(used).map(([k, v]) => `${k} ×${v}`).join(", ")})`);
    } else notes.push(`${r.contacts_routed} present but columns not recognized; using naive placeholder`);
  }
  // Fill any contact without a routed time from the naive placeholder (labeled).
  const naivePath = "data/processed/synthetic/contacts.csv";
  if (existsSync(join(root, naivePath))) {
    let n = 0;
    for (const row of parseCsv(read(root, naivePath))) {
      if (out.has(row.contact_id)) continue;
      const v = Number(row.naive_travel_min);
      if (!Number.isFinite(v)) continue;
      out.set(row.contact_id, { minutes: v, mode: row.naive_travel_mode, source: "naive_placeholder" });
      n++;
    }
    if (n) notes.push(`Contact travel: NAIVE placeholder for ${n} contacts (${r.fallback})`);
  }
  return { value: out, notes };
}

export function loadPlaces(root: string, cfg: HealthSystemConfig): CoolingPlace[] {
  return placesFromGeoJson(JSON.parse(read(root, cfg.data_sources.cooling_places.file)));
}

/** System graph pathway counts (drug group × mediator) for stacking.ts. Optional. */
export function loadSystemPathways(root: string, p = "data/processed/system_pathways.csv"): Loaded<SystemPathwayIndex | null> {
  if (!existsSync(join(root, p))) return { value: null, notes: [`System pathways: not loaded (${p} not present)`] };
  const idx: SystemPathwayIndex = new Map();
  for (const r of parseCsv(read(root, p))) {
    const row = {
      drugGroup: r.drug_group,
      mediator: r.mediator,
      mediatorLabel: r.mediator_label,
      drugLegStudies: Number(r.drug_leg_studies) || 0,
      heatLegStudies: Number(r.heat_leg_studies) || 0,
    };
    const m = idx.get(row.drugGroup) ?? new Map();
    m.set(row.mediator, row);
    idx.set(row.drugGroup, m);
  }
  return { value: idx, notes: [`System pathways: ${p} (${idx.size} drug groups; Dataverse v2.1)`] };
}

export function loadRoutedCooling(root: string, cfg: HealthSystemConfig): Loaded<Map<string, Record<string, string>[]> | undefined> {
  const p = cfg.data_sources.routing.cooling_match;
  if (!existsSync(join(root, p))) return { value: undefined, notes: [`Cooling match: FALLBACK nearest-place matcher (${p} not present)`] };
  const rows = parseCsv(read(root, p));
  if (!rows[0] || !("patient_id" in rows[0])) return { value: undefined, notes: [`${p} present but has no patient_id column; using fallback matcher`] };
  const m = new Map<string, Record<string, string>[]>();
  for (const r of rows) m.set(r.patient_id, [...(m.get(r.patient_id) ?? []), r]);
  return { value: m, notes: [`Cooling match: ROUTED (${p}, ${m.size} patients)`] };
}
