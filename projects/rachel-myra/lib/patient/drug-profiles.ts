// Drug → heat-defense profiles. Two sources, swappable:
//   1. the knowledge base (data/kb/knowledge_base.json or mock_knowledge_base.json, plus
//      data/kb/anticholinergic_burden.csv) when it is loaded: authoritative;
//   2. PROVISIONAL_DRUG_MAP otherwise (labeled "provisional" everywhere it is used).
// The KB adapter is deliberately tolerant about field names because the KB schema
// (lib/types/knowledge-base.ts) is owned by another agent and may still change.

import type { DrugHeatProfile, HeatDefense } from "../types/patient.ts";
import { NARROW_MARGIN_KIDNEY_CLEARED, PROVISIONAL_DRUG_MAP } from "./provisional-drug-map.ts";

export const DEFENSE_LABELS: Record<HeatDefense, { en: string; es: string; plain: string }> = {
  sweating: { en: "sweating", es: "sudoración", plain: "Sweating (cooling by sweat)" },
  skin_blood_flow: { en: "blood flow to the skin", es: "flujo de sangre a la piel", plain: "Heart and skin blood flow (moving heat out)" },
  fluid_salt_balance: { en: "fluid and salt balance", es: "equilibrio de líquidos y sal", plain: "Fluid and salt balance (dehydration, low sodium)" },
  blood_pressure: { en: "blood pressure", es: "presión arterial", plain: "Blood pressure (dizziness, fainting)" },
  kidney_clearance: { en: "kidney function", es: "función de los riñones", plain: "Kidneys (clearing drugs, kidney stress)" },
  brain_thermostat: { en: "the body's thermostat", es: "el termostato del cuerpo", plain: "Brain thermostat / body heat production" },
  alertness: { en: "alertness and thirst", es: "el estado de alerta y la sed", plain: "Alertness (noticing heat, feeling thirst)" },
  blood_sugar: { en: "blood sugar", es: "azúcar en la sangre", plain: "Blood sugar" },
  drug_delivery: { en: "how fast the medicine is absorbed", es: "la rapidez con que se absorbe la medicina", plain: "Drug delivery (faster absorption in heat)" },
  medicine_storage: { en: "the medicine itself (storage)", es: "la medicina misma (almacenamiento)", plain: "Medicine storage (heat can damage it)" },
};

/** Body defenses; medicine_storage is about the product, not the body, and is counted separately. */
export const BODY_DEFENSES: HeatDefense[] = [
  "sweating",
  "skin_blood_flow",
  "fluid_salt_balance",
  "blood_pressure",
  "kidney_clearance",
  "brain_thermostat",
  "alertness",
  "blood_sugar",
  "drug_delivery",
];

/** Mechanism tag (spec §6.1 groups) → heat defense weakened. Documented rule table. */
export const TAG_TO_DEFENSE: Record<string, HeatDefense> = {
  sweat_blocked: "sweating",
  less_skin_blood_flow: "skin_blood_flow",
  fluid_salt_loss: "fluid_salt_balance",
  more_sweating: "fluid_salt_balance",
  low_sodium: "fluid_salt_balance",
  bp_drop: "blood_pressure",
  kidney_stress: "kidney_clearance",
  kidney_cleared_buildup: "kidney_clearance",
  impaired_thermoregulation: "brain_thermostat",
  heat_production: "brain_thermostat",
  sedation: "alertness",
  low_glucose: "blood_sugar",
  faster_absorption: "drug_delivery",
  storage_sensitive: "medicine_storage",
  // knowledge-base MechanismGroup names (lib/types/knowledge-base.ts)
  thermostat: "brain_thermostat",
  sedation_awareness: "alertness",
  blood_sugar: "blood_sugar",
};

/** Knowledge-base heat_stack keys → defenses (only entries with affected = "yes" count). */
export const KB_STACK_TO_DEFENSE: Record<string, HeatDefense> = {
  sweating: "sweating",
  water_salt: "fluid_salt_balance",
  kidney_clearance: "kidney_clearance",
  blood_pressure: "blood_pressure",
};

const KEYWORD_TO_DEFENSE: [RegExp, HeatDefense][] = [
  [/storage|potency|degrad/i, "medicine_storage"],
  [/sweat|anhidro|anticholin/i, "sweating"],
  [/skin|vasodil|cardiac output|heart rate|blood flow/i, "skin_blood_flow"],
  [/fluid|salt|sodium|volume|dehydrat|diures|hyponat/i, "fluid_salt_balance"],
  [/pressure|hypotens|orthostat|syncope/i, "blood_pressure"],
  [/kidney|renal|aki|clearance|toxicity|level/i, "kidney_clearance"],
  [/thermo|thermostat|heat production|hyperthermi|core temp/i, "brain_thermostat"],
  [/sedat|alert|aware|cogniti|thirst|confus|cns/i, "alertness"],
  [/glucose|sugar|hypoglyc/i, "blood_sugar"],
  [/absorp|delivery|patch|transderm|insulin uptake/i, "drug_delivery"],
];

export function normalizeDefense(raw: unknown): HeatDefense | null {
  if (raw && typeof raw === "object") {
    const o = raw as Record<string, unknown>;
    raw = o.id ?? o.key ?? o.defense ?? o.name ?? o.label;
  }
  if (typeof raw !== "string") return null;
  const k = raw.trim().toLowerCase().replace(/[\s-]+/g, "_");
  if ((DEFENSE_LABELS as Record<string, unknown>)[k]) return k as HeatDefense;
  if (TAG_TO_DEFENSE[k]) return TAG_TO_DEFENSE[k];
  for (const [re, d] of KEYWORD_TO_DEFENSE) if (re.test(raw)) return d;
  return null;
}

const SALT_WORDS = /\b(sodium|potassium|carbonate|hydrochloride|hcl|citrate|sulfate|maleate|tartrate|succinate|besylate|mesylate)\b/g;

export function normalizeDrugName(name: string): string {
  const n = name.toLowerCase().replace(/\s*\/\s*/g, "/").trim();
  if (/amphetamine/.test(n) && /dextroamphetamine/.test(n)) return "amphetamine mixed salts";
  const stripped = n.replace(SALT_WORDS, "").replace(/\s+/g, " ").trim();
  return stripped || n;
}

export interface DrugProfileIndex {
  byName: Map<string, DrugHeatProfile>;
  byRxcui: Map<string, DrugHeatProfile>;
  /** Plain-language KB message blocks per drug when the KB provides them. */
  kbMessages: Map<string, Record<string, string>>;
  sources: string[];
}

function provisionalProfile(generic: string): DrugHeatProfile {
  const r = PROVISIONAL_DRUG_MAP[generic];
  const defenses = [...new Set(r.tags.map((t) => TAG_TO_DEFENSE[t]).filter(Boolean))] as HeatDefense[];
  return {
    generic,
    plainClass: r.drugClass,
    heatClass: r.heatClass,
    defenses,
    acb: r.acb,
    narrowMarginKidneyCleared: NARROW_MARGIN_KIDNEY_CLEARED.includes(generic),
    source: "provisional",
  };
}

export function provisionalIndex(): DrugProfileIndex {
  const idx: DrugProfileIndex = { byName: new Map(), byRxcui: new Map(), kbMessages: new Map(), sources: ["provisional"] };
  for (const g of Object.keys(PROVISIONAL_DRUG_MAP)) {
    const p = provisionalProfile(g);
    idx.byName.set(g, p);
    if (PROVISIONAL_DRUG_MAP[g].rxcui) idx.byRxcui.set(PROVISIONAL_DRUG_MAP[g].rxcui, p);
  }
  return idx;
}

function pick(o: Record<string, unknown>, keys: string[]): unknown {
  for (const k of keys) if (o[k] !== undefined && o[k] !== null) return o[k];
  return undefined;
}

function kbDrugRows(kb: unknown): Record<string, unknown>[] {
  if (Array.isArray(kb)) return kb as Record<string, unknown>[];
  if (kb && typeof kb === "object") {
    const o = kb as Record<string, unknown>;
    const d = pick(o, ["drugs", "drug_rows", "medications", "rows", "entries"]);
    if (Array.isArray(d)) return d as Record<string, unknown>[];
    if (d && typeof d === "object")
      return Object.entries(d as Record<string, Record<string, unknown>>).map(([k, v]) => ({ generic: k, ...v }));
  }
  return [];
}

/**
 * Overlay knowledge-base rows (and an optional ACB table) onto an index. Rows the KB
 * doesn't cover keep their provisional profile (and stay labeled provisional).
 * Understands the KB schema in lib/types/knowledge-base.ts (DrugRecord: names.ingredients,
 * mechanism_groups, heat_stack, patient_messages) and, tolerantly, flatter row shapes.
 * Defenses come from mechanism_groups + heat_stack entries marked "yes"; heat_stack.other is
 * descriptive and is not counted.
 */
export function overlayKnowledgeBase(
  base: DrugProfileIndex,
  kb: unknown,
  label: "knowledge_base" | "mock_knowledge_base",
  acbRows: Record<string, string>[] = [],
): { index: DrugProfileIndex; matched: number } {
  const idx: DrugProfileIndex = {
    byName: new Map(base.byName),
    byRxcui: new Map(base.byRxcui),
    kbMessages: new Map(base.kbMessages),
    sources: [...new Set([...base.sources, label])],
  };
  const acb = new Map<string, number>();
  for (const r of acbRows) {
    const name = pick(r, ["drug_generic", "generic", "generic_name", "drug", "name", "ingredient"]);
    const score = Number(pick(r, ["acb_score", "acb", "score", "anticholinergic_burden"]));
    if (typeof name === "string" && Number.isFinite(score)) acb.set(normalizeDrugName(name), score);
  }
  let matched = 0;
  for (const row of kbDrugRows(kb)) {
    const names = row.names as Record<string, any> | undefined;
    const ingredients: { name: string; rxcui?: string | null; acb_score?: number | null }[] = Array.isArray(names?.ingredients)
      ? names!.ingredients
      : [];
    const nameRaw = pick(row, ["generic", "generic_name", "ingredient", "name", "drug"]) ?? (ingredients.length ? undefined : row.id);
    const entries = ingredients.length ? ingredients : typeof nameRaw === "string" ? [{ name: nameRaw, rxcui: (pick(row, ["rxcui", "rxnorm_rxcui"]) as string) ?? null, acb_score: null }] : [];
    if (!entries.length) continue;

    const rawDef = pick(row, ["mechanism_groups", "heat_defenses", "defenses", "heat_defenses_weakened", "defenses_weakened", "mechanisms", "mechanism_tags"]);
    const defList = Array.isArray(rawDef) ? rawDef : typeof rawDef === "string" ? rawDef.split(/[;,|]/) : [];
    const defs = new Set(defList.map(normalizeDefense).filter(Boolean) as HeatDefense[]);
    const stack = row.heat_stack as Record<string, any> | undefined;
    if (stack) for (const [k, v] of Object.entries(stack)) if (KB_STACK_TO_DEFENSE[k] && v?.affected === "yes") defs.add(KB_STACK_TO_DEFENSE[k]);
    const kbClass = [names?.class_label, typeof row.id === "string" ? row.id.replace(/_/g, " ") : ""].filter(Boolean).join(" / ");
    const msgs = Array.isArray(row.patient_messages) ? (row.patient_messages as Record<string, string>[]) : [];
    const msg = msgs.find((m) => m.situation === "heat_forecast") ?? msgs.find((m) => m.situation === "heat_day");
    const allNames = entries.map((e) => normalizeDrugName(e.name));

    for (const ing of entries) {
      const generic = normalizeDrugName(ing.name);
      const prior = idx.byName.get(generic);
      if (!defs.size && !prior) continue;
      const rowAcb = Number(pick(row, ["acb", "acb_score"]));
      const p: DrugHeatProfile = {
        generic,
        // keep the drug-specific provisional class (e.g. benztropine is not a bladder medicine)
        plainClass: prior?.plainClass || String(names?.class_label ?? pick(row, ["plain_class", "drug_class", "class"]) ?? ""),
        heatClass: prior?.heatClass || kbClass,
        defenses: defs.size ? [...defs] : prior!.defenses,
        acb: typeof ing.acb_score === "number" ? ing.acb_score : acb.get(generic) ?? (Number.isFinite(rowAcb) ? rowAcb : prior?.acb ?? 0),
        narrowMarginKidneyCleared:
          Boolean(pick(row, ["narrow_therapeutic_index", "narrow_margin", "nti"])) || NARROW_MARGIN_KIDNEY_CLEARED.includes(generic),
        source: label,
      };
      idx.byName.set(generic, p);
      if (ing.rxcui) idx.byRxcui.set(String(ing.rxcui), p);
      for (const [k, v] of idx.byRxcui) if (v === prior) idx.byRxcui.set(k, p);
      if (msg) {
        // Use a class message only if it doesn't name a different ingredient than this patient's drug.
        const otherNamed = allNames.some((n) => n !== generic && new RegExp(`\\b${n}\\b`, "i").test(msg.en ?? ""));
        if (!otherNamed) idx.kbMessages.set(generic, { en: msg.en, es: msg.es, es_status: msg.es_status ?? "", situation: msg.situation, kb_id: String(row.id ?? "") });
      } else {
        const flat = pick(row, ["patient_message", "patient_wording", "plain_language"]);
        if (flat && typeof flat === "object") idx.kbMessages.set(generic, flat as Record<string, string>);
        else if (typeof flat === "string") idx.kbMessages.set(generic, { en: flat });
      }
      matched++;
    }
  }
  // ACB table overlay (the KB's sourced scale beats the provisional recalled scores).
  for (const [g, p] of idx.byName) {
    const score = acb.get(g);
    if (score !== undefined && p.acb !== score) idx.byName.set(g, { ...p, acb: score });
    else if (score === undefined && acbRows.length && p.acb > 0 && p.source === "provisional") idx.byName.set(g, { ...p, acb: 0 });
  }
  for (const [k, v] of idx.byRxcui) {
    const cur = idx.byName.get(v.generic);
    if (cur && cur !== v) idx.byRxcui.set(k, cur);
  }
  return { index: idx, matched };
}

export function lookupProfile(idx: DrugProfileIndex, generic: string, rxcui?: string): DrugHeatProfile | null {
  return idx.byName.get(normalizeDrugName(generic)) ?? (rxcui ? idx.byRxcui.get(rxcui) ?? null : null);
}
