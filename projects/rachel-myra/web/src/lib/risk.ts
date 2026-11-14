// Risk groups (High / Medium / Low) and plain-language "why" sentences.
// Shared by the clinician board, the patient plan and the map.
//
// Source: data/processed/panel_scores_replay.json → patients[].readiness.level
//   low → Low, medium → Medium, high + very_high → High.
// The "why" text only rewords fields already in that file (readiness.drivers,
// stacking, lifestyle); it never adds facts. Safe to import from client code.

export type RiskGroup = "high" | "medium" | "low";

export const RISK_ORDER: RiskGroup[] = ["high", "medium", "low"];

export function riskGroup(level: string | null | undefined): RiskGroup {
  if (level === "high" || level === "very_high") return "high";
  if (level === "medium") return "medium";
  return "low";
}

export const RISK: Record<
  RiskGroup,
  { label: string; action: string; chip: string; solid: string; tint: string; ink: string; dot: string }
> = {
  high: {
    label: "High",
    action: "Check on these patients today",
    chip: "border-risk-high-ink bg-risk-high-tint text-risk-high-ink",
    solid: "bg-risk-high text-risk-high-on",
    tint: "bg-risk-high-tint",
    ink: "text-risk-high-ink",
    dot: "bg-risk-high",
  },
  medium: {
    label: "Medium",
    action: "Send the nearest cool place and safe hours",
    chip: "border-risk-medium-ink bg-risk-medium-tint text-risk-medium-ink",
    solid: "bg-risk-medium text-risk-medium-on",
    tint: "bg-risk-medium-tint",
    ink: "text-risk-medium-ink",
    dot: "bg-risk-medium ring-1 ring-risk-medium-ink",
  },
  low: {
    label: "Low",
    action: "A heads-up is enough",
    chip: "border-risk-low-ink bg-risk-low-tint text-risk-low-ink",
    solid: "bg-risk-low text-risk-low-on",
    tint: "bg-risk-low-tint",
    ink: "text-risk-low-ink",
    dot: "bg-risk-low",
  },
};

/** Minimal shape of a panel_scores patient used here (full type: lib/types/patient.ts). */
export interface RiskInput {
  readiness?: { level: string; drivers: string[] };
  stacking?: {
    mechanisms: { defense: string; label: string; drugs: string[]; stacked: boolean }[];
    maskedSigns?: { sign: string; label: string; drugs: string[]; why: string }[];
  };
  lifestyle?: { category: string; profileLabel: string };
}

/** What a weakened heat defense means, in plain words ("…make it harder to …"). */
export const DEFENSE_PLAIN: Record<string, { effect: string; short: string }> = {
  blood_pressure: { effect: "lower blood pressure (dizziness, fainting)", short: "Low blood pressure" },
  kidney_clearance: { effect: "put strain on the kidneys", short: "Kidney strain" },
  fluid_salt_balance: { effect: "drain water and salt from the body", short: "Dehydration, low salt" },
  alertness: { effect: "make it harder to notice heat and feel thirsty", short: "Drowsy, less thirst" },
  brain_thermostat: { effect: "make it harder for the body to control its temperature", short: "Body can't cool itself" },
  sweating: { effect: "make it harder to sweat and cool down", short: "Can't sweat" },
  blood_sugar: { effect: "make blood sugar harder to control", short: "Blood sugar swings" },
  drug_delivery: { effect: "get absorbed faster in heat", short: "Absorbed faster" },
};

const HOME_PLAIN: Record<string, string> = {
  "no working ac at home": "no working AC at home",
  "lives alone": "lives alone",
  "lives alone and no one checks on them": "lives alone with no one checking in",
  "lives on floor 7 or higher": "lives on a high floor",
  "floor 4+ with no elevator": "lives up several flights of stairs with no elevator",
  "spends the day outdoors or doing physical work": "spends the day outdoors or doing physical work",
  "outdoor work or sports": "works or plays sports outdoors",
  "has ac but cost limits use": "has AC but the cost limits using it",
  "can reach a cool place only with help": "needs help to reach a cool place",
  "cannot get to a cool place": "can't get to a cool place",
  "age 75+": "is 75 or older",
  "home all day without reliable ac": "is home all day without reliable AC",
  "home often gets hot": "home often gets hot",
  "uses power-dependent equipment": "uses medical equipment that needs power",
  schizophrenia: "has schizophrenia, which raises heat risk",
  "child under 5": "is a young child",
  "neighborhood heat vulnerability index 5 (highest)": "lives in one of the most heat-exposed neighborhoods",
  "neighborhood heat vulnerability index 4": "lives in a heat-exposed neighborhood",
};

// Drivers that matter most in a one-line reason, most important first.
const HOME_PRIORITY = [
  "no working ac at home",
  "cannot get to a cool place",
  "lives alone and no one checks on them",
  "uses power-dependent equipment",
  "can reach a cool place only with help",
  "has ac but cost limits use",
  "lives alone",
  "home all day without reliable ac",
  "spends the day outdoors or doing physical work",
  "outdoor work or sports",
  "age 75+",
  "child under 5",
  "schizophrenia",
  "floor 4+ with no elevator",
  "lives on floor 7 or higher",
  "home often gets hot",
  "neighborhood heat vulnerability index 5 (highest)",
  "neighborhood heat vulnerability index 4",
];

export const cap = (s: string) => (s ? s[0].toUpperCase() + s.slice(1) : s);

export function listJoin(xs: string[]): string {
  if (xs.length <= 1) return xs.join("");
  if (xs.length === 2) return `${xs[0]} and ${xs[1]}`;
  return `${xs.slice(0, -1).join(", ")} and ${xs[xs.length - 1]}`;
}

const NUM = ["", "", "two", "three", "four", "five", "six"];

/** Readable synthetic name: "Imani783 Camara780" → "Imani Camara". */
export function plainName(displayName: string): string {
  return displayName.replace(/\d+/g, "").replace(/\s+/g, " ").trim();
}

function topMechanism(p: RiskInput) {
  const ms = p.stacking?.mechanisms ?? [];
  return ms.filter((m) => m.stacked).sort((a, b) => b.drugs.length - a.drugs.length)[0] ?? ms[0] ?? null;
}

function medsFromDrivers(p: RiskInput): string[] {
  const d = (p.readiness?.drivers ?? []).find((x) => x.startsWith("on "));
  return d ? d.slice(3).split(/,\s*|\s\+\s/) : [];
}

function homeReasons(p: RiskInput, n: number): string[] {
  const drivers = (p.readiness?.drivers ?? []).filter((d) => !d.startsWith("on "));
  return HOME_PRIORITY.filter((k) => drivers.includes(k))
    .map((k) => HOME_PLAIN[k])
    .slice(0, n);
}

/** One plain sentence for the clinician (third person). */
export function clinicianWhy(p: RiskInput): string {
  const parts: string[] = [];
  const m = topMechanism(p);
  if (m && DEFENSE_PLAIN[m.defense]) {
    const drugs = m.drugs.slice(0, 3);
    parts.push(
      drugs.length > 1
        ? `${cap(listJoin(drugs))} ${drugs.length === 2 ? "both" : "all"} ${DEFENSE_PLAIN[m.defense].effect}, and heat does too`
        : `${cap(drugs[0])} can ${DEFENSE_PLAIN[m.defense].effect} in heat`,
    );
  } else {
    const meds = medsFromDrivers(p);
    if (meds.length) parts.push(`Takes ${listJoin(meds)}`);
  }
  const home = homeReasons(p, parts.length ? 2 : 3);
  if (home.length) parts.push(listJoin(home));
  return parts.length ? parts.map((x) => `${cap(x)}.`).join(" ") : "No strong medicine or home reason on file.";
}

/** One plain line for the patient (second person), e.g. "Your two medicines both make it harder to stay cool." */
export function patientWhy(p: RiskInput): string {
  const m = topMechanism(p);
  const sentences: string[] = [];
  if (m && DEFENSE_PLAIN[m.defense]) {
    sentences.push(
      m.stacked && m.drugs.length > 1
        ? `Your ${NUM[m.drugs.length] ?? m.drugs.length} medicines (${listJoin(m.drugs)}) ${m.drugs.length === 2 ? "both" : "all"} ${DEFENSE_PLAIN[m.defense].effect}, and heat does too.`
        : `Your medicine ${m.drugs[0]} can ${DEFENSE_PLAIN[m.defense].effect} in heat.`,
    );
  }
  const drivers = p.readiness?.drivers ?? [];
  if (drivers.includes("no working ac at home")) sentences.push("You have no working AC at home.");
  else if (drivers.includes("has ac but cost limits use")) sentences.push("Running your AC costs a lot.");
  else if (drivers.includes("lives alone")) sentences.push("You live alone.");
  return sentences.join(" ") || "Today is very hot.";
}

/** Plain bullet list for the "Why?" panel. */
export function whyBullets(p: RiskInput): string[] {
  const out: string[] = [];
  for (const m of (p.stacking?.mechanisms ?? []).filter((x) => x.stacked)) {
    const e = DEFENSE_PLAIN[m.defense];
    if (e) out.push(`${cap(listJoin(m.drugs))} ${m.drugs.length === 2 ? "both" : "all"} ${e.effect}, and heat does too.`);
  }
  for (const s of p.stacking?.maskedSigns ?? []) out.push(`${s.label} may not show up as a warning: ${s.why}.`);
  for (const h of homeReasons(p, 6)) out.push(`${cap(h)}.`);
  if (p.lifestyle?.profileLabel) out.push(`Daily routine: ${p.lifestyle.profileLabel}.`);
  return out;
}

// ---- Spanish (patient side). Machine-style translation, flagged "por revisar" in the UI. ----

export const RISK_LABEL_ES: Record<RiskGroup, string> = { high: "Alto", medium: "Medio", low: "Bajo" };

const DEFENSE_ES: Record<string, string> = {
  blood_pressure: "bajan la presión arterial (mareos, desmayos)",
  kidney_clearance: "fuerzan los riñones",
  fluid_salt_balance: "hacen perder agua y sal del cuerpo",
  alertness: "hacen más difícil notar el calor y sentir sed",
  brain_thermostat: "hacen más difícil que el cuerpo controle su temperatura",
  sweating: "hacen más difícil sudar y refrescarse",
  blood_sugar: "hacen más difícil controlar el azúcar en la sangre",
  drug_delivery: "se absorben más rápido con el calor",
};
// Singular verb forms for one medicine.
const DEFENSE_ES_ONE: Record<string, string> = {
  blood_pressure: "bajar la presión arterial (mareos, desmayos)",
  kidney_clearance: "forzar los riñones",
  fluid_salt_balance: "hacer perder agua y sal del cuerpo",
  alertness: "hacer más difícil notar el calor y sentir sed",
  brain_thermostat: "hacer más difícil que el cuerpo controle su temperatura",
  sweating: "hacer más difícil sudar y refrescarse",
  blood_sugar: "hacer más difícil controlar el azúcar en la sangre",
  drug_delivery: "absorberse más rápido",
};
const NUM_ES = ["", "", "dos", "tres", "cuatro", "cinco", "seis"];
const listJoinEs = (xs: string[]) => (xs.length <= 1 ? xs.join("") : `${xs.slice(0, -1).join(", ")} y ${xs[xs.length - 1]}`);

/** Spanish version of patientWhy. */
export function patientWhyEs(p: RiskInput): string {
  const m = topMechanism(p);
  const out: string[] = [];
  if (m && DEFENSE_ES[m.defense]) {
    out.push(
      m.stacked && m.drugs.length > 1
        ? `Sus ${NUM_ES[m.drugs.length] ?? m.drugs.length} medicinas (${listJoinEs(m.drugs)}) ${DEFENSE_ES[m.defense]}, y el calor también.`
        : `Su medicina ${m.drugs[0]} puede ${DEFENSE_ES_ONE[m.defense]} con el calor.`,
    );
  }
  const drivers = p.readiness?.drivers ?? [];
  if (drivers.includes("no working ac at home")) out.push("No tiene aire acondicionado que funcione en casa.");
  else if (drivers.includes("has ac but cost limits use")) out.push("Usar el aire acondicionado le cuesta mucho.");
  else if (drivers.includes("lives alone")) out.push("Vive solo/a.");
  return out.join(" ") || "Hoy hace mucho calor.";
}

export const SIGN_ES: Record<string, string> = {
  hot_dry_skin: "Piel caliente, roja y seca",
  headache: "Dolor de cabeza",
  muscle_cramps: "Calambres musculares",
  tiredness: "Cansancio o debilidad",
  heavy_sweating: "Sudar mucho",
  nausea: "Náuseas o vómitos",
  confusion: "Confusión",
  high_body_temp: "Temperatura del cuerpo alta",
  fainting: "Desmayos",
  dizziness: "Mareos",
};

export const MASKED_WHY_ES: Record<string, string> = {
  confusion: "la somnolencia o pensar más lento puede ocultar la confusión temprana, y puede que no sienta sed",
  heavy_sweating: "la medicina reduce el sudor, así que la señal de 'sudar mucho' puede no aparecer",
};
