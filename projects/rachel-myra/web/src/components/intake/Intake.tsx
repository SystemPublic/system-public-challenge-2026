"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";
import { scoreIntake } from "@/app/phone/signup/actions";
import { RISK, RISK_LABEL_ES } from "@/lib/risk";
import type { IntakeAnswers, IntakeContact, IntakeMed, IntakeResult } from "./types";

// CHILL'D-Out areas (CDC 2024), as listed in research-notes/advisor-models.md.
const AREAS = [
  { key: "C", name: "Cooling" },
  { key: "H", name: "Housing" },
  { key: "I", name: "Isolation" },
  { key: "L", name: "Electricity" },
  { key: "L2", name: "Learning" },
  { key: "D", name: "Drugs" },
  { key: "Out", name: "Outside" },
] as const;
type AreaKey = (typeof AREAS)[number]["key"] | "Contact";

type Opt<V> = { label: string; value: V };
type Choice = {
  kind: "choice";
  area: AreaKey;
  field: keyof IntakeAnswers;
  q: string;
  hint?: string;
  opts: Opt<IntakeAnswers[keyof IntakeAnswers]>[];
  /** Is the pre-filled value one of these options? (floor uses ranges) */
  match?: (v: IntakeAnswers[keyof IntakeAnswers], o: Opt<IntakeAnswers[keyof IntakeAnswers]>) => boolean;
  show?: (a: IntakeAnswers) => boolean;
};
type Step = Choice | { kind: "intro" } | { kind: "meds" } | { kind: "contact" } | { kind: "result" };

const YES_NO = [
  { label: "Yes", value: true },
  { label: "No", value: false },
];

const floorBand = (f: number | null) => (f == null ? null : f >= 7 ? 7 : f >= 4 ? 4 : 1);

const STEPS: Step[] = [
  { kind: "intro" },
  {
    kind: "choice", area: "C", field: "workingAc", q: "Do you have working air conditioning at home?",
    opts: [
      { label: "Yes", value: "yes" },
      { label: "Yes, but it costs too much to run", value: "yes_but_cost_limits_use" },
      { label: "No", value: "no" },
    ],
  },
  {
    kind: "choice", area: "C", field: "homeGetsHot", q: "Does your home get very hot in summer?",
    opts: [
      { label: "Rarely", value: "rarely" },
      { label: "Sometimes", value: "sometimes" },
      { label: "Often", value: "often" },
    ],
  },
  { kind: "choice", area: "H", field: "stableHousing", q: "Do you have a stable place to live?", opts: YES_NO },
  {
    kind: "choice", area: "H", field: "floor", q: "What floor do you live on?",
    opts: [
      { label: "Ground to 3rd floor", value: 1 },
      { label: "4th to 6th floor", value: 4 },
      { label: "7th floor or higher", value: 7 },
    ],
    match: (v, o) => floorBand(v as number | null) === o.value,
  },
  {
    kind: "choice", area: "H", field: "hasElevator", q: "Does your building have an elevator?", opts: YES_NO,
    show: (a) => (a.floor ?? 0) >= 4,
  },
  { kind: "choice", area: "I", field: "livesAlone", q: "Do you live alone?", opts: YES_NO },
  {
    kind: "choice", area: "I", field: "someoneChecksOn", q: "Is there a neighbor, friend or family member who can check on you on hot days?",
    opts: YES_NO,
  },
  {
    kind: "choice", area: "I", field: "canReachCoolPlace", q: "Can you get to a cool place, like a library or cooling center?",
    opts: [
      { label: "Yes, on my own", value: "yes" },
      { label: "Only with help", value: "with_help" },
      { label: "No", value: "no" },
    ],
  },
  {
    kind: "choice", area: "L", field: "powerEquipment", q: "Do you use medical equipment that needs electricity?",
    hint: "For example oxygen, a CPAP machine or a power wheelchair. If heat causes a power outage, you need a plan.",
    opts: YES_NO,
  },
  { kind: "choice", area: "L", field: "fridgeMedicines", q: "Do you keep any medicines in the fridge?", hint: "For example insulin.", opts: YES_NO },
  {
    kind: "choice", area: "L2", field: "checksForecast", q: "Do you check the weather to know the hottest time of day?",
    hint: "We will send you the safest hours on hot days.",
    opts: YES_NO,
  },
  { kind: "choice", area: "L2", field: "knowsHeatIllnessSigns", q: "Do you know the signs of getting sick from heat?", opts: YES_NO },
  { kind: "meds" },
  {
    kind: "choice", area: "Out", field: "dayLocation", q: "Where do you spend most of a summer day?",
    opts: [
      { label: "At home", value: "home" },
      { label: "Indoors somewhere cool (work, school, a center)", value: "indoors_ac" },
      { label: "Outdoors, or doing physical work", value: "outdoors_or_physical_work" },
    ],
  },
  { kind: "choice", area: "Out", field: "outdoorWorkOrSports", q: "Do you work or play sports outdoors on hot days?", opts: YES_NO },
  { kind: "contact" },
  { kind: "result" },
];

type Lang = "en" | "es";

// Spanish (usted form) for the fixed UI. Machine-style translation, shown with a "por revisar" note.
const AREA_ES: Record<string, string> = {
  C: "Fresco", H: "Vivienda", I: "Aislamiento", L: "Electricidad", L2: "Aprendizaje", D: "Medicinas", Out: "Afuera",
};
const Q_ES: Partial<Record<keyof IntakeAnswers, { q: string; hint?: string }>> = {
  workingAc: { q: "¿Tiene aire acondicionado que funcione en casa?" },
  homeGetsHot: { q: "¿Su casa se pone muy caliente en verano?" },
  stableHousing: { q: "¿Tiene un lugar estable donde vivir?" },
  floor: { q: "¿En qué piso vive?" },
  hasElevator: { q: "¿Su edificio tiene ascensor?" },
  livesAlone: { q: "¿Vive solo/a?" },
  someoneChecksOn: { q: "¿Hay un vecino, amigo o familiar que pueda ir a verle en los días de calor?" },
  canReachCoolPlace: { q: "¿Puede llegar a un lugar fresco, como una biblioteca o un centro de enfriamiento?" },
  powerEquipment: {
    q: "¿Usa equipo médico que necesita electricidad?",
    hint: "Por ejemplo oxígeno, una máquina CPAP o una silla de ruedas eléctrica. Si el calor causa un apagón, necesita un plan.",
  },
  fridgeMedicines: { q: "¿Guarda alguna medicina en el refrigerador?", hint: "Por ejemplo insulina." },
  checksForecast: {
    q: "¿Revisa el pronóstico del tiempo para saber la hora de más calor?",
    hint: "En los días de calor le enviaremos las horas más seguras.",
  },
  knowsHeatIllnessSigns: { q: "¿Conoce las señales de que el calor le está enfermando?" },
  dayLocation: { q: "¿Dónde pasa la mayor parte de un día de verano?" },
  outdoorWorkOrSports: { q: "¿Trabaja o hace deporte al aire libre en los días de calor?" },
};
const OPT_ES: Record<string, string> = {
  true: "Sí",
  false: "No",
  "workingAc:yes": "Sí",
  "workingAc:yes_but_cost_limits_use": "Sí, pero cuesta mucho usarlo",
  "workingAc:no": "No",
  "homeGetsHot:rarely": "Casi nunca",
  "homeGetsHot:sometimes": "A veces",
  "homeGetsHot:often": "A menudo",
  "floor:1": "Planta baja al 3er piso",
  "floor:4": "Del 4to al 6to piso",
  "floor:7": "7mo piso o más alto",
  "canReachCoolPlace:yes": "Sí, por mi cuenta",
  "canReachCoolPlace:with_help": "Solo con ayuda",
  "canReachCoolPlace:no": "No",
  "dayLocation:home": "En casa",
  "dayLocation:indoors_ac": "Adentro en un lugar fresco (trabajo, escuela, un centro)",
  "dayLocation:outdoors_or_physical_work": "Afuera, o haciendo trabajo físico",
};
const optLabel = (lang: Lang, field: keyof IntakeAnswers, o: Opt<IntakeAnswers[keyof IntakeAnswers]>) =>
  lang === "es" ? (OPT_ES[`${field}:${String(o.value)}`] ?? OPT_ES[String(o.value)] ?? o.label) : o.label;

const TXT = {
  en: {
    banner: "Prototype · synthetic patient · answers are not saved",
    hi: (n: string) => `Hi ${n}. Let\u2019s get you ready for hot days.`,
    count: "About 15 short questions about your home, the people around you and your medicines. Tap an answer to go on.",
    basedOn: "Based on CDC\u2019s CHILL\u2019D-Out heat questions. We filled in what your clinic already has; tap to change anything.",
    start: "Start",
    another: "Try another synthetic patient",
    prefilled: (f: string) => `Pre-filled from your clinic record (synthetic, ${f}) where it had an answer.`,
    medsQ: "Are these still your medicines?",
    medsFrom: (f: string) => `From your clinic\u2019s medicine list (synthetic, ${f}). Tap one you no longer take.`,
    noMeds: "No medicines on file.",
    dontStop: "Don\u2019t stop or change a medicine on your own. Talk to your doctor or pharmacist.",
    next: "Next",
    contactQ: "Who should we call if you don\u2019t answer on a hot day?",
    contactFrom: (f: string) => `Pre-filled from ${f} (synthetic). Not saved in this prototype.`,
    name: "Name",
    rel: "How you know them",
    phone: "Phone",
    textQ: "Can we text you on hot days?",
    textYes: "Yes, text me",
    textNo: "No, call me",
    working: "Working it out\u2026",
    seeResult: "See my result",
    back: "\u2190 Back",
    keep: "Keep this answer \u2192",
    yourContact: "Your contact",
    of: (n: number, t: number) => `${n} of ${t}`,
    qOf: (n: number, t: number) => `Question ${n} of ${t}`,
    howMatch: "How these questions match our data",
    howIntro: (f: string) => `The 7 CHILL\u2019D-Out areas and the columns already in ${f} that answer them:`,
    group: "Your heat risk group",
    riskLabel: (g: IntakeResult["group"]) => RISK[g].label,
    changed: (g: string) =>
      `Your clinic record (synthetic) had you in the ${g} group. Your new answers changed that. The heat plan below still uses the clinic record, because this prototype does not save answers.`,
    high: "On hot days we will text you a plan, check in with you, and call your contact if you don't answer.",
    medium: "On hot days we will text you the nearest cool place and the safest hours to go out.",
    low: "On hot days we will send you a heads-up.",
    talk: "Talk to your doctor or pharmacist.",
    seePlan: "See my heat plan",
    startOver: "Start over",
    how: "Your group comes from your medicines and your home, the same way your clinic\u2019s list does. Prototype; not medical advice.",
    note: null as string | null,
  },
  es: {
    banner: "Prototipo · paciente sintético · las respuestas no se guardan",
    hi: (n: string) => `Hola, ${n}. Vamos a prepararle para los días de calor.`,
    count: "Unas 15 preguntas cortas sobre su casa, las personas a su alrededor y sus medicinas. Toque una respuesta para seguir.",
    basedOn: "Basado en las preguntas sobre el calor CHILL\u2019D-Out de los CDC. Ya llenamos lo que su clínica tiene; toque para cambiar lo que quiera.",
    start: "Empezar",
    another: "Probar otro paciente sintético",
    prefilled: (f: string) => `Lo llenamos con su expediente de la clínica (sintético, ${f}) cuando tenía una respuesta.`,
    medsQ: "¿Todavía toma estas medicinas?",
    medsFrom: (f: string) => `De la lista de medicinas de su clínica (sintética, ${f}). Toque la que ya no toma.`,
    noMeds: "No hay medicinas en su expediente.",
    dontStop: "No deje ni cambie una medicina por su cuenta. Hable con su médico o farmacéutico.",
    next: "Siguiente",
    contactQ: "¿A quién llamamos si usted no contesta en un día de calor?",
    contactFrom: (f: string) => `Lo llenamos con ${f} (sintético). No se guarda en este prototipo.`,
    name: "Nombre",
    rel: "Relación con usted",
    phone: "Teléfono",
    textQ: "¿Le podemos enviar mensajes de texto en los días de calor?",
    textYes: "Sí, por texto",
    textNo: "No, llámenme",
    working: "Calculando\u2026",
    seeResult: "Ver mi resultado",
    back: "\u2190 Atrás",
    keep: "Dejar esta respuesta \u2192",
    yourContact: "Su contacto",
    of: (n: number, t: number) => `${n} de ${t}`,
    qOf: (n: number, t: number) => `Pregunta ${n} de ${t}`,
    howMatch: "Cómo estas preguntas se relacionan con nuestros datos",
    howIntro: (f: string) => `Las 7 áreas de CHILL\u2019D-Out y las columnas que ya están en ${f} que las responden:`,
    group: "Su grupo de riesgo por calor",
    riskLabel: (g: IntakeResult["group"]) => RISK_LABEL_ES[g],
    changed: (g: string) =>
      `Su expediente de la clínica (sintético) le tenía en el grupo ${g}. Sus nuevas respuestas lo cambiaron. El plan de calor de abajo todavía usa el expediente de la clínica, porque este prototipo no guarda respuestas.`,
    high: "En los días de calor le enviaremos un plan por texto, le preguntaremos cómo está y llamaremos a su contacto si no contesta.",
    medium: "En los días de calor le enviaremos por texto el lugar fresco más cercano y las horas más seguras para salir.",
    low: "En los días de calor le enviaremos un aviso.",
    talk: "Hable con su médico o farmacéutico.",
    seePlan: "Ver mi plan para el calor",
    startOver: "Empezar de nuevo",
    how: "Su grupo sale de sus medicinas y de su casa, igual que en la lista de su clínica. Prototipo; no es consejo médico.",
    note: "Traducción automática — por revisar" as string | null,
  },
};
type Txt = (typeof TXT)["en"];

const areaOf = (s: Step): AreaKey | null => (s.kind === "choice" ? s.area : s.kind === "meds" ? "D" : s.kind === "contact" ? "Contact" : null);

// How the existing questionnaire.csv columns feed each area (shown on the last screen).
const MAPPING: { area: string; cols: string }[] = [
  { area: "C · Cooling", cols: "q1_working_ac, home_gets_hot" },
  { area: "H · Housing", cols: "stable_housing, q3_floor, building_has_elevator" },
  { area: "I · Isolation & mobility", cols: "q4_lives_alone, someone_checks_on_them, q5_can_reach_cool_place" },
  { area: "L · eLectricity", cols: "power_dependent_equipment, fridge_medicines" },
  { area: "L · Learning", cols: "knows_heat_illness_signs (the forecast question is new: no column yet, not scored)" },
  { area: "D · Drugs", cols: "medications.csv (generic_name, status), not a yes/no question" },
  { area: "Out · Outside", cols: "q2_day_location, outdoor_work_or_sports" },
  { area: "Contact", cols: "contacts.csv; alert_opt_in" },
];

export function Intake({
  patientId,
  lang = "en",
  firstName,
  initial,
  meds: initialMeds,
  contact: initialContact,
  story,
  files,
}: {
  patientId: string;
  lang?: Lang;
  firstName: string;
  initial: IntakeAnswers;
  meds: IntakeMed[];
  contact: IntakeContact;
  story: { id: string; name: string }[];
  files: { questionnaire: string; meds: string; contacts: string };
}) {
  const router = useRouter();
  const t = TXT[lang];
  const [i, setI] = useState(0);
  const [a, setA] = useState<IntakeAnswers>(initial);
  const [meds, setMeds] = useState(initialMeds);
  const [contact, setContact] = useState(initialContact);
  const [result, setResult] = useState<IntakeResult | { error: string } | null>(null);
  const [pending, start] = useTransition();

  const visible = STEPS.filter((s) => s.kind !== "choice" || !s.show || s.show(a));
  const step = visible[Math.min(i, visible.length - 1)];
  const questionSteps: Step[] = visible.filter((s) => s.kind !== "intro" && s.kind !== "result");
  const qIndex = questionSteps.indexOf(step);
  const current = areaOf(step);

  const next = () => setI((x) => Math.min(x + 1, visible.length - 1));
  const back = () => setI((x) => Math.max(x - 1, 0));

  const finish = () => {
    start(async () => {
      const r = await scoreIntake(patientId, a, meds.filter((m) => m.taking).map((m) => m.id), lang);
      setResult(r);
      next();
    });
  };

  const choose = (field: keyof IntakeAnswers, value: IntakeAnswers[keyof IntakeAnswers]) => {
    setA((prev) => ({ ...prev, [field]: value }));
    setTimeout(next, 180);
  };

  return (
    // Full-screen so the clinician header is hidden on the demo phone.
    <div className="fixed inset-0 z-50 overflow-auto bg-page text-patient-base leading-relaxed">
      <div className="mx-auto flex min-h-full max-w-md flex-col gap-5 px-4 py-5">
        <p className="rounded-full border border-line bg-surface px-3 py-1 text-center text-sm text-ink-muted">
          {t.banner}
        </p>
        {t.note && <p className="text-center text-xs text-ink-muted">{t.note}</p>}

        {step.kind !== "intro" && step.kind !== "result" && (
          <Progress t={t} lang={lang} current={current} n={qIndex + 1} total={questionSteps.length} />
        )}

        {step.kind === "intro" && (
          <section className="flex flex-1 flex-col gap-5">
            <div className="space-y-2 text-center">
              <p className="text-base font-medium text-muted-foreground">{lang === "es" ? "Su plan para el calor" : "Your heat plan"}</p>
              <h1 className="text-patient-xl font-semibold leading-tight tracking-tight">{t.hi(firstName)}</h1>
              <p className="text-muted-foreground">{t.count}</p>
            </div>
            <p className="text-base text-muted-foreground">{t.basedOn}</p>
            <BigButton onClick={next} primary>
              {t.start}
            </BigButton>
            <label className="mt-auto block text-sm text-ink-muted">
              {t.another}{" "}
              <select
                className="ml-1 rounded-md border border-line bg-page px-2 py-1 text-sm text-ink"
                value={patientId}
                onChange={(e) => router.push(`/phone/signup?patient=${e.target.value}`)}
              >
                {story.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.id} · {s.name}
                  </option>
                ))}
              </select>
            </label>
          </section>
        )}

        {step.kind === "choice" && (
          <section className="flex flex-1 flex-col gap-4">
            <h1 className="text-patient-xl font-bold leading-snug">{lang === "es" ? (Q_ES[step.field]?.q ?? step.q) : step.q}</h1>
            {step.hint && <p className="text-base text-ink-muted">{lang === "es" ? (Q_ES[step.field]?.hint ?? step.hint) : step.hint}</p>}
            <div className="flex flex-col gap-3">
              {step.opts.map((o) => {
                const v = a[step.field];
                const on = v != null && (step.match ? step.match(v, o) : v === o.value);
                return (
                  <BigButton key={String(o.value)} selected={on} onClick={() => choose(step.field, step.field === "floor" && on ? v : o.value)}>
                    {optLabel(lang, step.field, o)}
                  </BigButton>
                );
              })}
            </div>
            {a[step.field] != null && a[step.field] === initial[step.field] && (
              <p className="text-sm text-ink-muted">{t.prefilled(files.questionnaire)}</p>
            )}
          </section>
        )}

        {step.kind === "meds" && (
          <section className="flex flex-1 flex-col gap-4">
            <h1 className="text-patient-xl font-bold leading-snug">{t.medsQ}</h1>
            <p className="text-base text-ink-muted">{t.medsFrom(files.meds)}</p>
            {meds.length ? (
              <ul className="flex flex-col gap-3">
                {meds.map((m, k) => (
                  <li key={m.id}>
                    <button
                      type="button"
                      aria-pressed={m.taking}
                      onClick={() => setMeds((xs) => xs.map((x, j) => (j === k ? { ...x, taking: !x.taking } : x)))}
                      className={`flex min-h-tap w-full items-start gap-3 rounded-2xl border-2 p-4 text-left ${
                        m.taking ? "border-ink bg-surface" : "border-line text-ink-muted"
                      }`}
                    >
                      <span aria-hidden className={`mt-1 flex h-6 w-6 shrink-0 items-center justify-center rounded-md border-2 ${m.taking ? "border-primary bg-primary text-primary-foreground" : "border-line-strong"}`}>
                        {m.taking ? "✓" : ""}
                      </span>
                      <span>
                        <span className={`block font-semibold capitalize ${m.taking ? "" : "line-through"}`}>{m.generic}</span>
                        <span className="block text-base text-ink-muted">{m.plainClass}</span>
                        {m.heatLine && m.taking && <span className="mt-1 block text-base">{m.heatLine}</span>}
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            ) : (
              <p>{t.noMeds}</p>
            )}
            <p className="font-semibold">{t.dontStop}</p>
            <BigButton primary onClick={next}>
              {t.next}
            </BigButton>
          </section>
        )}

        {step.kind === "contact" && (
          <section className="flex flex-1 flex-col gap-4">
            <h1 className="text-patient-xl font-bold leading-snug">{t.contactQ}</h1>
            <p className="text-base text-ink-muted">{t.contactFrom(files.contacts)}</p>
            <Field label={t.name} value={contact.name} onChange={(v) => setContact({ ...contact, name: v })} />
            <Field label={t.rel} value={contact.relationship} onChange={(v) => setContact({ ...contact, relationship: v })} />
            <Field label={t.phone} value={contact.phone} type="tel" onChange={(v) => setContact({ ...contact, phone: v })} />
            <p className="mt-2 font-semibold">{t.textQ}</p>
            <div className="grid grid-cols-2 gap-3">
              {YES_NO.map((o) => (
                <BigButton key={String(o.value)} selected={a.alertOptIn === o.value} onClick={() => setA({ ...a, alertOptIn: o.value })}>
                  {o.value ? t.textYes : t.textNo}
                </BigButton>
              ))}
            </div>
            <BigButton primary onClick={finish} disabled={pending}>
              {pending ? t.working : t.seeResult}
            </BigButton>
          </section>
        )}

        {step.kind === "result" && <Result t={t} result={result} patientId={patientId} restart={() => { setResult(null); setI(0); }} />}

        {step.kind !== "intro" && step.kind !== "result" && (
          <div className="flex items-center justify-between pt-2">
            <button type="button" onClick={back} className="min-h-tap px-2 text-base underline">
              {t.back}
            </button>
            {step.kind === "choice" && a[step.field] != null && (
              <button type="button" onClick={next} className="min-h-tap px-2 text-base underline">
                {t.keep}
              </button>
            )}
          </div>
        )}

        {step.kind === "result" && (
          <details className="rounded-2xl border border-line p-4 text-base">
            <summary className="cursor-pointer font-semibold">{t.howMatch}</summary>
            <p className="mt-2 text-sm text-ink-muted">{t.howIntro(files.questionnaire)}</p>
            <dl className="mt-2 space-y-1 text-sm">
              {MAPPING.map((m) => (
                <div key={m.area}>
                  <dt className="inline font-semibold">{m.area}: </dt>
                  <dd className="inline font-mono text-xs">{m.cols}</dd>
                </div>
              ))}
            </dl>
          </details>
        )}
      </div>
    </div>
  );
}

function Progress({ t, lang, current, n, total }: { t: Txt; lang: Lang; current: AreaKey | null; n: number; total: number }) {
  const areaName = (k: AreaKey | null) => (k === "Contact" ? t.yourContact : k ? (lang === "es" ? AREA_ES[k] : AREAS.find((x) => x.key === k)?.name) : "");
  return (
    <div className="space-y-2" aria-label={t.qOf(n, total)}>
      <div className="flex gap-1" aria-hidden>
        {AREAS.map((ar) => (
          <span
            key={ar.key}
            className={`flex-1 rounded-full py-0.5 text-center text-xs font-bold ${
              current === ar.key ? "bg-primary text-primary-foreground" : "bg-surface text-ink-muted"
            }`}
          >
            {ar.key === "L2" ? "L" : ar.key}
          </span>
        ))}
      </div>
      <div className="flex items-baseline justify-between text-sm text-ink-muted">
        <span>{areaName(current)}</span>
        <span>{t.of(n, total)}</span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-surface">
        <div className="h-full rounded-full bg-primary transition-all" style={{ width: `${(n / total) * 100}%` }} />
      </div>
    </div>
  );
}

function BigButton({
  children,
  onClick,
  selected,
  primary,
  disabled,
}: {
  children: React.ReactNode;
  onClick: () => void;
  selected?: boolean;
  primary?: boolean;
  disabled?: boolean;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      aria-pressed={primary ? undefined : !!selected}
      className={`min-h-tap w-full rounded-lg border px-4 py-3 font-semibold transition-colors disabled:opacity-60 ${
        primary
          ? "border-primary bg-primary text-center text-primary-foreground"
          : selected
            ? "border-primary bg-primary/5 text-left"
            : "border-border bg-card text-left hover:bg-accent"
      }`}
    >
      {selected && !primary && <span aria-hidden className="mr-2">✓</span>}
      {children}
    </button>
  );
}

function Field({ label, value, onChange, type = "text" }: { label: string; value: string; onChange: (v: string) => void; type?: string }) {
  return (
    <label className="block">
      <span className="block text-base font-semibold">{label}</span>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="mt-1 min-h-tap w-full rounded-xl border-2 border-line bg-page px-3 text-patient-base focus:border-ink focus:outline-none"
      />
    </label>
  );
}

function Result({
  t,
  result,
  patientId,
  restart,
}: {
  t: Txt;
  result: IntakeResult | { error: string } | null;
  patientId: string;
  restart: () => void;
}) {
  if (!result) return null;
  if ("error" in result) return <p className="rounded-2xl border border-line p-4">{result.error}</p>;
  const r = RISK[result.group];
  return (
    <section className="flex flex-col gap-5">
      <div className={`rounded-2xl border-2 p-5 ${r.chip}`}>
        <p className="text-base font-semibold">{t.group}</p>
        <p className="mt-1 flex items-center gap-3">
          <span className={`rounded-full px-4 py-1 text-patient-xl font-bold ${r.solid}`}>{t.riskLabel(result.group)}</span>
        </p>
        <p className="mt-3 text-ink">{result.why}</p>
      </div>
      {!result.sameAsRecord && result.recordGroup && (
        <p className="text-base text-ink-muted">
          {t.changed(t.riskLabel(result.recordGroup))}
        </p>
      )}
      <p className="text-base">
        {result.group === "high" ? t.high : result.group === "medium" ? t.medium : t.low}
      </p>
      <p className="font-bold">{t.talk}</p>
      <Link href={`/phone/${patientId}`} className="min-h-tap flex items-center justify-center rounded-2xl border-2 border-primary bg-primary px-4 py-3 font-semibold text-primary-foreground">
        {t.seePlan}
      </Link>
      <button type="button" onClick={restart} className="min-h-tap text-base underline">
        {t.startOver}
      </button>
      <p className="text-xs text-ink-muted">{t.how}</p>
    </section>
  );
}
