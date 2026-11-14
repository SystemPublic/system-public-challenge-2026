// Customized patient messages (spec §4.4, §4.5, §4.5b): assembled by documented rules from
// pre-written message blocks (knowledge-base blocks when present; provisional blocks below
// otherwise) + the patient's needs. Never generated live. Safety rules enforced by
// checkMessageSafety(): no dose numbers or dose talk, never "stop taking", fluid advice only
// within clinician-set limits, every patient message ends with "talk to your doctor or pharmacist".

import type { HeatRiskLevel } from "../types/health-system.ts";
import type { CoolingPlaceOption, DrugHeatProfile, HeatDefense, MedRiskStack, PatientMessage, QuestionnaireAnswers } from "../types/patient.ts";
import type { DrugProfileIndex } from "./drug-profiles.ts";
import { lookupProfile } from "./drug-profiles.ts";

type Lang = "en" | "es";

export const CLOSING: Record<Lang, string> = {
  en: "Talk to your doctor or pharmacist.",
  es: "Hable con su médico o farmacéutico.",
};

/** Provisional per-defense blocks (template: spec §4.5). Swapped for KB blocks when available. */
export const DEFENSE_BLOCKS: Record<HeatDefense, Record<Lang, { effect: string; why: string; watch: string }>> = {
  sweating: {
    en: { effect: "make it harder to sweat", why: "it blocks the signal that turns sweat on", watch: "hot, dry skin or confusion" },
    es: { effect: "hacer más difícil sudar", why: "bloquea la señal que activa el sudor", watch: "piel caliente y seca o confusión" },
  },
  skin_blood_flow: {
    en: { effect: "make it harder to move heat out through the skin", why: "it slows the heart and blood flow to the skin", watch: "weakness or dizziness" },
    es: { effect: "hacer más difícil sacar el calor por la piel", why: "hace más lento el corazón y el flujo de sangre a la piel", watch: "debilidad o mareo" },
  },
  fluid_salt_balance: {
    en: { effect: "make you lose water and salt faster", why: "it changes how your body holds water and salt", watch: "dizziness, cramps, headache or confusion" },
    es: { effect: "hacerle perder agua y sal más rápido", why: "cambia cómo su cuerpo guarda el agua y la sal", watch: "mareo, calambres, dolor de cabeza o confusión" },
  },
  blood_pressure: {
    en: { effect: "lower your blood pressure more than usual", why: "heat also opens blood vessels", watch: "dizziness or fainting when you stand up" },
    es: { effect: "bajar su presión más de lo normal", why: "el calor también abre los vasos sanguíneos", watch: "mareo o desmayo al levantarse" },
  },
  kidney_clearance: {
    en: { effect: "strain your kidneys or let the medicine build up", why: "the kidneys get less blood when you lose fluid", watch: "less urine, nausea, shakiness or confusion" },
    es: { effect: "forzar sus riñones o hacer que la medicina se acumule", why: "los riñones reciben menos sangre cuando pierde líquido", watch: "orinar menos, náuseas, temblores o confusión" },
  },
  brain_thermostat: {
    en: { effect: "make it harder for your body to control its temperature", why: "it acts on the brain's thermostat or makes more body heat", watch: "feeling very hot, fast heartbeat or confusion" },
    es: { effect: "hacer más difícil que su cuerpo controle su temperatura", why: "actúa sobre el termostato del cerebro o produce más calor", watch: "sentir mucho calor, latidos rápidos o confusión" },
  },
  alertness: {
    en: { effect: "make you sleepy and less likely to notice heat or thirst", why: "it slows the brain down", watch: "drowsiness or confusion" },
    es: { effect: "darle sueño y hacer que no note el calor o la sed", why: "hace más lento el cerebro", watch: "somnolencia o confusión" },
  },
  blood_sugar: {
    en: { effect: "make low blood sugar more likely", why: "heat changes how your body uses sugar", watch: "shakiness, sweating or confusion" },
    es: { effect: "hacer más probable el azúcar baja", why: "el calor cambia cómo su cuerpo usa el azúcar", watch: "temblores, sudor o confusión" },
  },
  drug_delivery: {
    en: { effect: "get into your body faster", why: "warm skin absorbs medicine faster", watch: "unusual sleepiness or shakiness" },
    es: { effect: "entrar a su cuerpo más rápido", why: "la piel caliente absorbe la medicina más rápido", watch: "sueño o temblores fuera de lo normal" },
  },
  medicine_storage: {
    en: { effect: "be damaged by heat", why: "heat can weaken the medicine", watch: "changes in how it looks or works" },
    es: { effect: "dañarse con el calor", why: "el calor puede debilitar la medicina", watch: "cambios en cómo se ve o funciona" },
  },
};

const SAFE_ACTION: Record<Lang, { cool: string; keepTaking: string; store: string }> = {
  en: { cool: "stay somewhere cool", keepTaking: "Keep taking your medicines as prescribed.", store: "Keep it cool and out of the sun, a hot car or a mailbox." },
  es: { cool: "quédese en un lugar fresco", keepTaking: "Siga tomando sus medicinas como se las recetaron.", store: "Guárdela en un lugar fresco, lejos del sol, de un carro caliente o del buzón." },
};

/** Fluid-advice rules (spec §4.4 item 10, §4.5b). Clinician-set limits always win. */
export const FLUID_RULES = [
  { id: "fluid_restricted", when: "Clinician set a fluid restriction (questionnaire fluid_restricted)", en: "Stay within the fluid limit your care team set. If you feel dizzy or very thirsty, call them.", es: "No pase del límite de líquidos que le indicó su equipo de salud. Si se siente mareado o con mucha sed, llámelos." },
  { id: "low_sodium_risk", when: "Thiazide + SSRI or another low-sodium combination", en: "Drink when you are thirsty, but don't force down large amounts of plain water. Ask your care team how much is right for you.", es: "Beba cuando tenga sed, pero no tome cantidades muy grandes de agua sola. Pregunte a su equipo de salud cuánto es lo correcto para usted." },
  { id: "ask_fluid_plan", when: "Heart failure or CKD in the record, or on a loop diuretic, with no clinician-set limit on file", en: "Follow the fluid plan your care team gave you, and ask them how much to drink on hot days.", es: "Siga el plan de líquidos que le dio su equipo de salud y pregúnteles cuánto tomar en días de calor." },
  { id: "default_hydrate", when: "Everyone else", en: "Drink water regularly, even if you are not thirsty.", es: "Tome agua con frecuencia, aunque no tenga sed." },
] as const;

const PLAIN_CLASS: [RegExp, Record<Lang, string>][] = [
  [/thiazide|loop diuretic|diuretic/i, { en: "water pill", es: "pastilla para orinar" }],
  [/ace inhibitor|\barb\b|\barni\b/i, { en: "blood pressure medicine", es: "medicina para la presión" }],
  [/beta blocker/i, { en: "heart medicine", es: "medicina para el corazón" }],
  [/antipsychotic/i, { en: "mental health medicine", es: "medicina para la salud mental" }],
  [/bladder|antimuscarinic/i, { en: "bladder medicine", es: "medicina para la vejiga" }],
  [/antihistamine/i, { en: "allergy or sleep medicine", es: "medicina para la alergia o el sueño" }],
  [/ssri|snri|antidepress/i, { en: "mood medicine", es: "medicina para el ánimo" }],
  [/stimulant/i, { en: "ADHD medicine", es: "medicina para el TDAH" }],
  [/insulin/i, { en: "insulin", es: "insulina" }],
  [/nsaid/i, { en: "pain reliever", es: "analgésico" }],
];

export function plainDrugName(p: DrugHeatProfile, lang: Lang): string {
  const name = p.generic.replace(/ mixed salts$/, "");
  if (/lithium/.test(p.generic)) return lang === "es" ? "litio" : "lithium";
  for (const [re, label] of PLAIN_CLASS) if (re.test(`${p.plainClass} ${p.heatClass}`)) return `${label[lang]} (${name})`;
  return name;
}

export function joinList(items: string[], lang: Lang): string {
  const and = lang === "es" ? "y" : "and";
  if (items.length <= 1) return items[0] ?? "";
  return `${items.slice(0, -1).join(", ")} ${and} ${items[items.length - 1]}`;
}

export interface MessageContext {
  patientName: string;
  age: number;
  language: string;
  supportedLanguages: string[];
  fallbackLanguage: string;
  q: QuestionnaireAnswers | null;
  med: MedRiskStack;
  meds: { generic: string; rxcui?: string }[];
  /** Normalized condition keys (heart_failure, ckd, ...) for fluid rules. */
  conditionKeys?: string[];
  idx: DrugProfileIndex;
  heatriskToday: HeatRiskLevel;
  cooling: CoolingPlaceOption | null;
}

function resolveLang(ctx: MessageContext): { lang: Lang; needsTranslation: boolean; rules: string[] } {
  const want = (ctx.q?.preferredLanguage ?? ctx.language ?? "en").toLowerCase();
  if (ctx.supportedLanguages.includes(want) && (want === "en" || want === "es")) return { lang: want, needsTranslation: false, rules: [`language_${want}`] };
  return { lang: ctx.fallbackLanguage as Lang, needsTranslation: true, rules: [`language_fallback_${ctx.fallbackLanguage} (needs ${want} interpreter)`] };
}

export function isCaregiverAudience(ctx: Pick<MessageContext, "age" | "q">): boolean {
  return ctx.age < 18 || ctx.q?.respondent === "parent_or_caregiver";
}

type Who = "self" | "child" | "adult_cg";
function whoOf(ctx: Pick<MessageContext, "age" | "q">): Who {
  return ctx.age < 18 ? "child" : ctx.q?.respondent === "parent_or_caregiver" ? "adult_cg" : "self";
}
/** Audience wording (child → parent; adult with a caregiver respondent → "the person you care for"). */
const W = {
  drugs1: { en: { self: "Your", child: "Your child's", adult_cg: "The person you care for takes" }, es: { self: "Esta medicina suya hace", child: "Esta medicina de su hijo/a hace", adult_cg: "Esta medicina de la persona que usted cuida hace" } },
  drugsN: { es: { self: "Estas medicinas suyas hacen", child: "Estas medicinas de su hijo/a hacen", adult_cg: "Estas medicinas de la persona que usted cuida hacen" } },
  go: { en: { self: "Go", child: "Get your child", adult_cg: "Help the person you care for get" }, es: { self: "Vaya", child: "Lleve a su hijo/a", adult_cg: "Ayude a la persona que usted cuida a ir" } },
  goTo: { en: { self: "Go to", child: "Take your child to", adult_cg: "Help the person you care for get to" }, es: { self: "Vaya a", child: "Lleve a su hijo/a a", adult_cg: "Ayude a la persona que usted cuida a ir a" } },
  card: { en: { self: "", child: "your child's ", adult_cg: "" }, es: { self: "", child: "la medicina de su hijo/a, ", adult_cg: "la medicina de la persona que usted cuida, " } },
  cardSuffix: { en: { self: "", child: "", adult_cg: " (for the person you care for)" }, es: { self: "", child: "", adult_cg: "" } },
};

export function fluidRule(ctx: Pick<MessageContext, "q" | "med" | "conditionKeys" | "meds">): (typeof FLUID_RULES)[number] {
  if (ctx.q?.fluidRestricted) return FLUID_RULES[0];
  if (ctx.med.combinations.some((c) => c.id === "thiazide_plus_ssri")) return FLUID_RULES[1];
  const loop = ctx.meds?.some((m) => /^(furosemide|bumetanide|torsemide)$/.test(m.generic));
  if (loop || (ctx.conditionKeys ?? []).some((k) => k === "heart_failure" || k === "ckd")) return FLUID_RULES[2];
  return FLUID_RULES[3];
}

function profilesFor(ctx: MessageContext): DrugHeatProfile[] {
  const out: DrugHeatProfile[] = [];
  for (const m of ctx.meds) {
    const p = lookupProfile(ctx.idx, m.generic, m.rxcui);
    if (p && p.defenses.length && !out.some((o) => o.generic === p.generic)) out.push(p);
  }
  return out;
}

/** The drugs to name in short messages: drugs in level-raising combos first, then the rest. */
function keyDrugs(ctx: MessageContext, n: number): DrugHeatProfile[] {
  const ps = profilesFor(ctx);
  const combo = new Set(ctx.med.combinations.filter((c) => c.raisesLevel).flatMap((c) => c.drugs));
  const body = (p: DrugHeatProfile) => p.defenses.filter((d) => d !== "medicine_storage").length;
  // Narrow-margin drugs (lithium) and antipsychotics first, then drugs in level-raising combos, then the rest.
  const headline = (p: DrugHeatProfile) => (p.narrowMarginKidneyCleared ? 2 : /antipsychotic/i.test(`${p.plainClass} ${p.heatClass}`) ? 1 : 0);
  return [...ps]
    .sort((a, b) => headline(b) - headline(a) || Number(combo.has(b.generic)) - Number(combo.has(a.generic)) || body(b) - body(a))
    .slice(0, n);
}

function finish(text: string, lang: Lang): string {
  return `${text.trim()} ${CLOSING[lang]}`;
}

function channelFor(q: QuestionnaireAnswers | null): string {
  return q?.alertChannel === "voice_call" ? "voice call (read aloud) + SMS" : q?.alertChannel === "sms_only" ? "SMS" : "app push + SMS";
}

export function safetyAlert(ctx: MessageContext): PatientMessage {
  const { lang, needsTranslation, rules } = resolveLang(ctx);
  const caregiver = isCaregiverAudience(ctx);
  const who = whoOf(ctx);
  const drugs = keyDrugs(ctx, 2).map((p) => plainDrugName(p, lang));
  const place = ctx.cooling ? ` (${ctx.cooling.name})` : "";
  const fr = fluidRule(ctx);
  let text: string;
  if (lang === "es") {
    text =
      `Peligro por calor hoy. ` +
      (drugs.length
        ? `${drugs.length === 1 ? W.drugs1.es[who] : W.drugsN.es[who]} el calor más peligroso: ${joinList(drugs, "es")}. `
        : "") +
      `${W.go.es[who]} a un lugar fresco antes de las 11 AM${place}. ${fr.es} Responda OK.`;
  } else {
    text =
      `Heat danger today. ` +
      (drugs.length
        ? who === "adult_cg"
          ? `The person you care for takes ${joinList(drugs, "en")}, which make${drugs.length === 1 ? "s" : ""} heat riskier. `
          : `${W.drugs1.en[who]} ${joinList(drugs, "en")} make${drugs.length === 1 ? "s" : ""} heat riskier. `
        : "") +
      `${W.go.en[who]} somewhere cool by 11 AM${place}. ${fr.en} Reply OK.`;
  }
  return {
    kind: "safety_alert",
    language: lang,
    needsTranslation,
    audience: caregiver ? "caregiver" : "patient",
    channel: channelFor(ctx.q),
    text: finish(text, lang),
    blocks: ["alert_header", ...keyDrugs(ctx, 2).map((p) => `drug:${p.generic}`), ctx.cooling ? "cooling_place" : "cool_generic", `fluid:${fr.id}`],
    rulesApplied: [...rules, `audience_${who}`, `fluid:${fr.id}`, "no_dose_advice", "closing_line"],
  };
}

export function heatCard(ctx: MessageContext): PatientMessage {
  const { lang, needsTranslation, rules } = resolveLang(ctx);
  const caregiver = isCaregiverAudience(ctx);
  const who = whoOf(ctx);
  const ps = keyDrugs(ctx, 3);
  const lines: string[] = [];
  const blocks: string[] = [];
  const applied = [...rules, `audience_${who}`];
  const combos = ctx.med.combinations.filter((c) => c.raisesLevel);
  if (combos.length) {
    const c = combos[0];
    const names = c.drugs.map((g) => {
      const p = lookupProfile(ctx.idx, g);
      return p ? plainDrugName(p, lang) : g;
    });
    lines.push(
      lang === "es"
        ? `Juntas, ${joinList(names, "es")} aumentan el riesgo con el calor.`
        : `Together, ${joinList(names, "en")} raise the risk in heat.`,
    );
    blocks.push(`combo:${c.id}`);
    applied.push("combined_warning");
  }
  for (const p of ps) {
    const kbm = ctx.idx.kbMessages.get(p.generic);
    const kb = kbm?.[lang];
    if (kb && lines.some((l) => l === kb.replace(CLOSING[lang], "").trim())) continue; // same class block already used
    if (kb) {
      // KB blocks carry their own closing line; strip it so the card ends with exactly one.
      lines.push(kb.replace(CLOSING[lang], "").trim());
      blocks.push(`kb:${kbm.kb_id || p.generic}:${kbm.situation ?? ""}`);
      if (lang === "es" && kbm.es_status) applied.push(`kb_es_status: ${kbm.es_status}`);
      continue;
    }
    const body = p.defenses.filter((d) => d !== "medicine_storage");
    const d = body[0] ?? p.defenses[0];
    const b = DEFENSE_BLOCKS[d][lang];
    const name = plainDrugName(p, lang);
    const intro = lang === "es" ? `Aviso de calor para ${W.card.es[who]}${name}` : `Heat warning for ${W.card.en[who]}${name}${W.cardSuffix.en[who]}`;
    lines.push(
      lang === "es"
        ? `${intro}: con calor puede ${b.effect} porque ${b.why}. Esté atento a ${b.watch}, y ${SAFE_ACTION.es.cool}.`
        : `${intro}: in hot weather it can ${b.effect} because ${b.why}. Watch for ${b.watch}, and ${SAFE_ACTION.en.cool}.`,
    );
    blocks.push(`defense:${d}:${p.generic}`);
    if (p.defenses.includes("medicine_storage")) {
      lines.push(SAFE_ACTION[lang].store);
      blocks.push(`storage:${p.generic}`);
    }
  }
  const fr = fluidRule(ctx);
  lines.push(fr[lang]);
  applied.push(`fluid:${fr.id}`);
  lines.push(SAFE_ACTION[lang].keepTaking);
  applied.push("no_dose_advice", "closing_line");
  return {
    kind: "heat_card",
    language: lang,
    needsTranslation,
    audience: caregiver ? "caregiver" : "patient",
    channel: "app card + mailed/printed card (non-urgent)",
    text: finish(lines.join(" "), lang),
    blocks: [...blocks, `fluid:${fr.id}`],
    rulesApplied: applied,
  };
}

export function coolingPlaceText(ctx: MessageContext): PatientMessage | null {
  const c = ctx.cooling;
  if (!c) return null;
  const { lang, needsTranslation, rules } = resolveLang(ctx);
  const caregiver = isCaregiverAudience(ctx);
  const who = whoOf(ctx);
  const how =
    c.travelMode === "walk" || c.travelMode === "routed"
      ? lang === "es" ? `a unos ${c.travelMin} min caminando` : `about ${c.travelMin} min walk`
      : lang === "es" ? `a unos ${c.travelMin} min en transporte` : `about ${c.travelMin} min by bus or train`;
  const hours = c.hoursToday ? (lang === "es" ? ` Horario hoy: ${c.hoursToday}.` : ` Open today: ${c.hoursToday}.`) : "";
  const leave = c.leaveBy ? (lang === "es" ? ` Salga antes de las ${c.leaveBy} para llegar antes de las 11 AM, antes del calor fuerte.` : ` Leave by ${c.leaveBy} to get there before 11 AM, before it gets really hot.`) : "";
  const callAhead = c.caveats.some((x) => /call ahead/i.test(x)) ? (lang === "es" ? " Llame antes para confirmar." : " Call ahead to confirm.") : "";
  const text =
    lang === "es"
      ? `Hoy hace mucho calor. ${W.goTo.es[who]} ${c.name}${c.address ? `, ${c.address}` : ""}: tiene aire acondicionado y otras personas, ${how}.${hours}${leave}${callAhead}`
      : `Hot day today. ${W.goTo.en[who]} ${c.name}${c.address ? `, ${c.address}` : ""}: air-conditioned, with other people around, ${how}.${hours}${leave}${callAhead}`;
  return {
    kind: "cooling_place",
    language: lang,
    needsTranslation,
    audience: caregiver ? "caregiver" : "patient",
    channel: "SMS (morning)",
    text: finish(text, lang),
    blocks: ["cooling_header", `place:${c.id}`, c.leaveBy ? "leave_by" : "no_leave_by"],
    rulesApplied: [...rules, "arrive_before_11", "closing_line"],
  };
}

export function contactCheckText(patientFirstName: string, contactLang: string | undefined, supported: string[], fluidRestricted: boolean): PatientMessage {
  const lang: Lang = contactLang === "es" && supported.includes("es") ? "es" : "en";
  const text =
    lang === "es"
      ? `Por favor vaya a ver a ${patientFirstName} en persona o llame. No ha respondido a un aviso de calor. Fíjese si hay: confusión, piel caliente y seca, desmayo o vómito. Qué hacer: llévele a un lugar fresco, refrésquele con agua y un ventilador${fluidRestricted ? "" : ", dele sorbos de agua si está despierto/a"}. Si está confundido/a o no responde, llame al 911. Responda OK cuando lo haya visto.`
      : `Please check on ${patientFirstName} in person or by phone. They haven't answered a heat alert. Look for: confusion, hot dry skin, fainting or vomiting. What to do: move them somewhere cool, cool them with water and a fan${fluidRestricted ? "" : ", give sips of water if they're awake"}. If they are confused or won't wake up, call 911. Reply OK once you've checked.`;
  return {
    kind: "contact_check",
    language: lang,
    needsTranslation: false,
    audience: "trusted_contact",
    channel: "SMS + call",
    text,
    blocks: ["contact_request", "look_for_checklist", "what_to_do_checklist", fluidRestricted ? "no_water_sips (fluid restricted)" : "water_sips"],
    rulesApplied: [`language_${lang}`, fluidRestricted ? "fluid:fluid_restricted" : "fluid:default"],
  };
}

export function checkinText(ctx: MessageContext): PatientMessage {
  const { lang, needsTranslation, rules } = resolveLang(ctx);
  const text =
    lang === "es"
      ? "Control de calor: responda OK si está bien, o AYUDA si necesita ayuda."
      : "Heat check-in: reply OK if you're all right, or HELP if you need help.";
  return { kind: "checkin", language: lang, needsTranslation, audience: isCaregiverAudience(ctx) ? "caregiver" : "patient", channel: channelFor(ctx.q), text: finish(text, lang), blocks: ["checkin"], rulesApplied: [...rules, "closing_line"] };
}

// ---------------------------------------------------------------- guardrails

const FORBIDDEN: [RegExp, string][] = [
  [/\bstop(ping)? (taking|your)\b/i, "tells the patient to stop a medicine"],
  [/\bdej(e|a|ar) de tomar\b/i, "tells the patient to stop a medicine (es)"],
  [/\b(skip|double|halve|reduce|increase)\b[^.]*\b(dose|pill|medicine|medication)/i, "dose change"],
  [/\b\d+(\.\d+)?\s?(mg|mcg|µg|ml|mL|units?|unidades)\b/i, "dose number"],
  [/\bdos(e|is|age|ing)\b/i, "dose talk"],
];

/** Returns a list of problems; empty = passes. Contact messages don't need the closing line. */
export function checkMessageSafety(m: Pick<PatientMessage, "text" | "language" | "audience">): string[] {
  const issues: string[] = [];
  for (const [re, why] of FORBIDDEN) if (re.test(m.text)) issues.push(why);
  if (m.audience !== "trusted_contact") {
    const closing = CLOSING[(m.language as Lang) in CLOSING ? (m.language as Lang) : "en"];
    if (!m.text.trim().endsWith(closing)) issues.push("missing closing line");
  }
  return issues;
}
