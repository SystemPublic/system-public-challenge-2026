// Server-only: assembles the EHR side-panel plan and the CDS Hooks card for one
// synthetic patient. Nothing is invented; every field comes from:
//   group, why, meds, cool place  data/processed/panel_scores_replay.json
//   safe hours                    data/processed/replay_heatwave_hourly.csv
//   medicine heat lines           data/kb/knowledge_base.json (label_line, claims)
import { placeNote, tidyAddress, tidyPlaceName } from "@/lib/placeName";
import { HOT_FEELS_LIKE_F } from "@/components/map/patientPlanData";
import type { DrugRecord } from "@lib/types/knowledge-base.ts";
import { getDrugs } from "@/lib/kb";
import { getPanelPatient, loadPanel, type PanelPatient } from "@/lib/panel";
import { clinicianWhy, plainName, RISK, riskGroup, whyBullets, type RiskGroup } from "@/lib/risk";
import { hourlyHeat, kbDrugFor } from "@/lib/synthetic";

export const PANEL_FILE = "data/processed/panel_scores_replay.json";
export const KB_FILE = "data/kb/knowledge_base.json";

const hourLong = (h: number) => (h === 0 || h === 24 ? "midnight" : h < 12 ? `${h} AM` : h === 12 ? "noon" : `${h - 12} PM`);
const clock = (hhmm: string) => {
  const [h, m] = hhmm.split(":").map(Number);
  if (Number.isNaN(h)) return hhmm;
  return `${h % 12 === 0 ? 12 : h % 12}:${String(m ?? 0).padStart(2, "0")} ${h < 12 ? "AM" : "PM"}`;
};

// Technical caveats (routing engine, walk speed) stay behind "See the evidence".
const isTechnical = (c: string) => /routed|osrm|m\/s/i.test(c);

export interface EhrMed { name: string; kbId: string | null; kbName: string | null; line: string | null }
export interface EhrPlan {
  id: string;
  name: string;
  age: number;
  zip: string;
  asOf: string;
  group: RiskGroup;
  why: string;
  todo: string[];
  cool: { name: string; address: string; note: string | null; walkMin: number | null; leaveBy: string | null; hours: string | null; notes: string[] } | null;
  meds: EhrMed[];
  evidence: {
    bullets: string[];
    combos: { label: string; evidence: string }[];
    sources: { label: string; url: string }[];
    coolNote: string | null;
    coolTechnical: string[];
  };
}

export function buildEhrPlan(id: string): EhrPlan | null {
  const p = getPanelPatient(id, "replay");
  if (!p) return null;
  const g = riskGroup(p.readiness?.level);
  const heat = hourlyHeat();
  const hot = (heat?.hours ?? []).filter((h) => h.hour >= 6 && h.hour <= 22 && (h.heatIndexF ?? h.tempF) >= HOT_FEELS_LIKE_F);
  const best = p.cooling?.best ?? null;
  const caveats = best?.caveats ?? [];
  const needsHelp = caveats.some((c) => /needs help/i.test(c));
  const contact = p.escalation?.contacts?.find((c) => c.contactId === p.escalation?.firstContactId);

  // High: the check-in line below replaces the generic group action.
  const todo: string[] = g === "high" ? [] : [RISK[g].action.replace("these patients", "this patient") + "."];
  if (hot.length) {
    todo.push(
      `Advise staying inside from ${hourLong(hot[0].hour)} to ${hourLong(hot[hot.length - 1].hour + 1)} (feels like ${HOT_FEELS_LIKE_F}°F or more); go out early in the morning.`,
    );
  }
  if (best) {
    todo.push(
      `Share the nearest cool place${best.travelMin != null ? ` (about ${best.travelMin} min walk` : ""}${best.leaveBy ? `, leave by ${clock(best.leaveBy)}` : ""}${best.travelMin != null ? ")" : ""}.`,
    );
  }
  if (needsHelp) todo.push("Needs help getting to a cool place: offer a ride or a delivery instead.");
  if (g === "high") {
    todo.push(
      contact
        ? `Check in today. If no answer, ask ${plainName(contact.name)} to check on them.`
        : p.escalation?.contacts?.length
          ? "Check in today. No contact on file lives close enough to check on them; ask for a closer contact or a buddy."
          : "Check in today. No emergency contact on file.",
    );
  }
  todo.push("Medicine changes are the prescriber's decision; tell the patient to talk to their doctor or pharmacist.");

  const meds = (p.meds?.heatRelevantDrugs ?? []).map((m) => {
    const d = kbDrugFor(m);
    return { name: m, kbId: d?.id ?? null, kbName: d?.names?.display ?? null, line: d?.label_line ?? null };
  });

  const sources: { label: string; url: string }[] = [];
  for (const m of meds) {
    const d = m.kbId ? getDrugs().find((x) => x.id === m.kbId) : null;
    for (const c of (d?.claims ?? []).filter((c) => c.source?.url).slice(0, 2)) {
      if (!sources.some((s) => s.url === c.source.url)) sources.push({ label: c.source.label, url: c.source.url as string });
    }
  }
  const combos = ((p.meds as { combinations?: { label: string; evidence: string }[] } | undefined)?.combinations ?? []).map(
    (c) => ({ label: c.label, evidence: c.evidence }),
  );

  return {
    id: p.patientId,
    name: plainName(p.displayName),
    age: p.age,
    zip: p.zip,
    asOf: loadPanel("replay")?.data.meta.as_of ?? "",
    group: g,
    why: clinicianWhy(p),
    todo,
    cool: best
      ? {
          name: tidyPlaceName(best.name),
          address: tidyAddress(best.address),
          note: caveats.some((c) => /older adults/i.test(c)) ? null : placeNote(best.name),
          walkMin: best.travelMin ?? null,
          leaveBy: best.leaveBy ? clock(best.leaveBy) : null,
          hours: best.hoursToday ?? null,
          notes: caveats.filter((c) => !isTechnical(c)),
        }
      : null,
    meds,
    evidence: {
      bullets: whyBullets(p),
      combos,
      sources,
      coolNote: p.cooling?.note ?? null,
      coolTechnical: caveats.filter(isTechnical),
    },
  };
}

// ---- CDS Hooks matching ----

/** Medication names/codes pulled from FHIR MedicationRequest / MedicationStatement resources. */
function medTerms(resource: unknown): { codes: string[]; texts: string[] } {
  const r = resource as {
    resourceType?: string;
    medicationCodeableConcept?: { text?: string; coding?: { code?: string; display?: string }[] };
    medication?: { concept?: { text?: string; coding?: { code?: string; display?: string }[] } };
  };
  const cc = r?.medicationCodeableConcept ?? r?.medication?.concept;
  if (!cc) return { codes: [], texts: [] };
  return {
    codes: (cc.coding ?? []).map((c) => c.code ?? "").filter(Boolean),
    texts: [cc.text, ...(cc.coding ?? []).map((c) => c.display)].filter((x): x is string => !!x),
  };
}

/** Walks a FHIR Bundle, array or single resource and returns every resource inside. */
function resources(x: unknown): unknown[] {
  if (!x || typeof x !== "object") return [];
  if (Array.isArray(x)) return x.flatMap(resources);
  const o = x as { resourceType?: string; entry?: { resource?: unknown }[] };
  if (o.resourceType === "Bundle") return (o.entry ?? []).map((e) => e.resource).filter(Boolean);
  return [o];
}

/** Knowledge-base records for heat-risk drugs found in the request (by RxNorm code, then by name). */
export function heatDrugsInRequest(body: { context?: Record<string, unknown>; prefetch?: Record<string, unknown> }) {
  const all = [
    ...resources(body.context?.draftOrders),
    ...resources(body.context?.medications),
    ...Object.values(body.prefetch ?? {}).flatMap(resources),
  ];
  const found = new Map<string, { drug: DrugRecord; ordered: string }>();
  for (const res of all) {
    const { codes, texts } = medTerms(res);
    let d: DrugRecord | null =
      getDrugs().find((k) => (k.names as unknown as { ingredients?: { rxcui?: string }[] })?.ingredients?.some((i) => i.rxcui && codes.includes(i.rxcui))) ?? null;
    let ordered = texts[0] ?? codes[0] ?? "";
    if (!d) {
      for (const t of texts) {
        const words = t.toLowerCase().split(/[^a-z]+/).filter((w) => w.length > 3);
        for (const w of [t.toLowerCase(), ...words]) {
          d = kbDrugFor(w);
          if (d) {
            ordered = t;
            break;
          }
        }
        if (d) break;
      }
    }
    if (d && !found.has(d.id)) found.set(d.id, { drug: d, ordered });
  }
  return [...found.values()];
}

export function patientFor(id: unknown): PanelPatient | null {
  return typeof id === "string" ? getPanelPatient(id.replace(/^Patient\//, ""), "replay") : null;
}
