// Read-only access to Myra's precomputed panel scores (scripts/compute_panel.ts → lib/patient).
// Every value shown by the core loop comes from these files; nothing is invented here.
//   replay = 2025-06-24 heat wave (HeatRisk 4) — the demo day
//   today  = live NWS HeatRisk (all 0 in November, so no alerts)

import fs from "node:fs";
import path from "node:path";
import type { PatientScore } from "@lib/types/patient.ts";
import { REPO_ROOT } from "@/lib/kb";

export type Scenario = "replay" | "today";

export interface EscalationStep { atMin: number; action: string; to: string }

export interface PanelMessage {
  kind: string;          // heat_card | safety_alert | cooling_place | checkin | contact_check
  language: string;
  audience: string;      // patient | caregiver | trusted_contact
  channel: string;
  text: string;
  needsTranslation?: boolean;
  rulesApplied?: string[];
  safetyIssues?: string[];
}

export interface PanelContact {
  contactId: string;
  name: string;
  relationship: string;
  travelMin: number | null;
  travelMode: string;
  allowedTravelMin: number;
  eligible: boolean;
}

export interface PanelPatient {
  patientId: string;
  synthetic: boolean;
  storyLabel?: string;
  displayName: string;
  age: number;
  zip: string;
  language: string;
  heatriskToday: number;
  rank?: number;
  readiness?: PatientScore["readiness"];
  lifestyle?: PatientScore["lifestyle"];
  stacking?: PatientScore["stacking"];
  meds?: { heatRelevantDrugs?: string[]; defenses?: { defense: string; label: string; drugs: string[] }[] };
  tier?: { tier: string; reasons: string[]; autoSafetyAlert?: boolean; coolingText?: boolean };
  escalation?: {
    enrolled: boolean;
    tMaxMin: number;
    tWaitMin: number;
    contacts: PanelContact[];
    firstContactId: string | null;
    noQualifyingContact: boolean;
    fallback?: string;
    steps: EscalationStep[];
    assumptions?: string[];
  };
  cooling?: {
    best?: CoolingPlace | null;
    alternatives?: CoolingPlace[];
    note?: string;
  };
  messages?: PanelMessage[];
}

export interface CoolingPlace {
  id?: string;
  name: string;
  category?: string;
  address: string;
  lat?: number;
  lon?: number;
  hoursToday?: string;
  leaveBy?: string;
  arriveBy?: string;
  travelMin?: number;
  distanceKm?: number;
  caveats?: string[];
}

export interface CallListRow {
  rank: number;
  patient_id: string;
  story?: string;
  age: number;
  zip: string;
  heatrisk_today: number;
  tier: string;
  tier_label: string;
  why: string[];
  readiness: string;
}

interface PanelFile {
  meta: { as_of: string; scenario: string; note?: string; forecast_source?: string };
  summary: unknown;
  call_list: CallListRow[];
  patients: PanelPatient[];
}

const cache = globalThis as unknown as { __panel?: Map<string, { mtime: number; data: PanelFile; byId: Map<string, PanelPatient> }> };

function file(s: Scenario) {
  return path.join(REPO_ROOT, "data", "processed", `panel_scores_${s}.json`);
}

/** Returns null when the file is missing (the UI then shows a placeholder). */
export function loadPanel(s: Scenario = "replay") {
  cache.__panel ??= new Map();
  const f = file(s);
  if (!fs.existsSync(f)) return null;
  const mtime = fs.statSync(f).mtimeMs;
  const hit = cache.__panel.get(s);
  if (hit && hit.mtime === mtime) return { ...hit, file: path.relative(REPO_ROOT, f) };
  const data = JSON.parse(fs.readFileSync(f, "utf8")) as PanelFile;
  // Plain words on screen (design rule 2): drop the forecast code "(HeatRisk N)" from message text.
  for (const p of data.patients)
    for (const m of p.messages ?? []) if (typeof m.text === "string") m.text = m.text.replace(/\s*\(HeatRisk \d\)/g, "");
  const byId = new Map(data.patients.map((p) => [p.patientId, p]));
  const entry = { mtime, data, byId };
  cache.__panel.set(s, entry);
  return { ...entry, file: path.relative(REPO_ROOT, f) };
}

export function getPanelPatient(id: string, s: Scenario = "replay"): PanelPatient | null {
  return loadPanel(s)?.byId.get(id) ?? null;
}

/** The patient-facing message of a kind (caregiver version if that's who the patient app talks to). */
export function patientMessage(p: PanelPatient, kind: string): PanelMessage | null {
  const ms = p.messages ?? [];
  return ms.find((m) => m.kind === kind && m.audience === "patient")
    ?? ms.find((m) => m.kind === kind && m.audience === "caregiver")
    ?? null;
}

export function contactMessage(p: PanelPatient): PanelMessage | null {
  return (p.messages ?? []).find((m) => m.kind === "contact_check") ?? null;
}

// ---- English reading copies (scripts/compute_messages_en.ts) ----
// Same lib/patient rules with language forced to "en". Used only to let English readers view a
// Spanish-speaking patient's screen (?lang=en). Patients are still sent their own language.

export const EN_MESSAGES_FILE = "data/processed/panel_messages_en_replay.json";
const enCache = globalThis as unknown as { __panelEn?: { mtime: number; byId: Map<string, PanelMessage[]> } };

function englishMessages(patientId: string): PanelMessage[] | null {
  const f = path.join(REPO_ROOT, EN_MESSAGES_FILE);
  if (!fs.existsSync(f)) return null;
  const mtime = fs.statSync(f).mtimeMs;
  if (enCache.__panelEn?.mtime !== mtime) {
    const raw = JSON.parse(fs.readFileSync(f, "utf8")) as { messages: Record<string, PanelMessage[]> };
    for (const ms of Object.values(raw.messages))
      for (const m of ms) if (typeof m.text === "string") m.text = m.text.replace(/\s*\(HeatRisk \d\)/g, "");
    enCache.__panelEn = { mtime, byId: new Map(Object.entries(raw.messages)) };
  }
  return enCache.__panelEn.byId.get(patientId) ?? null;
}

/**
 * English version of a message this patient was sent: find which of their messages the text is
 * (by kind + audience), return the English build of the same one. Null if there's no match or
 * the English file hasn't been generated (callers then keep the original text).
 */
export function englishFor(patientId: string, text: string, s: Scenario = "replay"): string | null {
  const p = getPanelPatient(patientId, s);
  // Messages saved before the "(HeatRisk N)" strip still carry it; ignore it when matching.
  const plain = text.replace(/\s*\(HeatRisk \d\)/g, "");
  const orig = p?.messages?.find((m) => m.text === plain);
  if (!orig) return null;
  const en = englishMessages(patientId)?.find((m) => m.kind === orig.kind && m.audience === orig.audience);
  return en?.text ?? null;
}
