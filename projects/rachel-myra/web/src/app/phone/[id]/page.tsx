import { Suspense } from "react";
import Link from "next/link";
import { PatientPlanMapView, PatientPlanMore } from "@/components/map/PatientPlanMapView";
import { getPatientPlanMapData, HOT_FEELS_LIKE_F } from "@/components/map/patientPlanData";
import { Placeholder } from "@/components/Placeholder";
import { getPanelPatient } from "@/lib/panel";
import { MASKED_WHY_ES, patientWhy, patientWhyEs, plainName, RISK, RISK_LABEL_ES, riskGroup, SIGN_ES } from "@/lib/risk";
import { HOURLY_FILE, hourlyHeat } from "@/lib/synthetic";
import { HourByHour } from "./HourByHour";
import { HelpContacts } from "@/components/help/HelpContacts";
import { HELP_FILE, helpContactsFor } from "@/lib/helpContacts";
import { Phone } from "./Phone";
import { MedicineCabinet, type CabinetEffect } from "@/components/cabinet/MedicineCabinet";

/** "Blood pressure (dizziness, fainting)" → title + signs */
function splitLabel(label: string): { title: string; signs: string | null } {
  const m = /^(.*?)\s*\((.*)\)\s*$/.exec(label);
  return m ? { title: m[1], signs: m[2] } : { title: label, signs: null };
}

// Patient "my heat plan" (P3). Everything comes from panel_scores_replay.json,
// replay_heatwave_hourly.csv and the map component's files. Map first: "where do I go?"
// ?lang=en|es overrides the patient's language (same rule as /phone/signup), so English readers
// can see a Spanish-speaking patient's screen. Message texts switch to the English build
// (data/processed/panel_messages_en_replay.json, scripts/compute_messages_en.ts).
type SearchParams = Promise<{ lang?: string }>;

export default function PhonePage({ params, searchParams }: { params: Promise<{ id: string }>; searchParams: SearchParams }) {
  return (
    <Suspense fallback={<p className="text-ink-muted">Loading…</p>}>
      <PhoneForPatient params={params} searchParams={searchParams} />
    </Suspense>
  );
}

const cap = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);
const hourLong =(h: number) => (h === 0 || h === 24 ? "midnight" : h < 12 ? `${h} AM` : h === 12 ? "noon" : `${h - 12} PM`);
const hourLongEs = (h: number) =>
  h === 0 || h === 24 ? "la medianoche" : h === 12 ? "el mediodía" : `${h % 12 === 1 ? "la" : "las"} ${h % 12} ${h < 12 ? "a.m." : "p.m."}`;

// Fixed UI labels. Spanish is a machine-style translation, noted under "More".
const T = {
  en: {
    risk: "Your heat risk today:",
    eyebrow: "Heat wave · June 24",
    synthetic: "Synthetic patient",
    replay: "Heat wave replay, June 24, 2025.",
    safest: "Stay inside",
    // Heading says "Stay inside", so this line is just the hours ("11 AM to 7 PM.").
    stayInside: (a: number, b: number) => cap(`${hourLong(a)} to ${hourLong(b)}.`),
    noHot: "No very hot hours today.",
    noRisk: "No heat risk today",
    hourly: "Hourly heat today",
    hourByHour: "Hour by hour",
    feels: (h: number, f: number) => `${hourLong(h)}: feels like ${f}°F`,
    ok: "OK",
    stayIn: "Stay in",
    watch: "Watch for",
    mayNot: (l: string) => `${l} may not happen:`,
    checkIn: "We will check in with you today.",
    contact: (n: string) => ` If you don't answer, we will ask ${n} to check on you.`,
    talk: "Talk to your doctor or pharmacist.",
    more: "More",
    update: "Update my answers",
    note: null as string | null,
  },
  es: {
    risk: "Su riesgo por calor hoy:",
    eyebrow: "Ola de calor · 24 de junio",
    synthetic: "Paciente de prueba",
    replay: "Repetición de la ola de calor, 24 de junio de 2025.",
    safest: "Quédese adentro",
    stayInside: (a: number, b: number) => cap(`De ${hourLongEs(a)} a ${hourLongEs(b)}.`.replace(/\.\.$/, ".")),
    noHot: "Hoy no hay horas de mucho calor.",
    noRisk: "Hoy no hay riesgo por calor",
    hourly: "Calor por hora hoy",
    hourByHour: "Hora por hora",
    feels: (h: number, f: number) => `${hourLongEs(h)}: se siente como ${f}°F`,
    ok: "Puede salir",
    stayIn: "Quédese adentro",
    watch: "Señales de alerta",
    mayNot: (l: string) => `${l} (puede no aparecer):`,
    checkIn: "Hoy le vamos a preguntar cómo está.",
    contact: (n: string) => ` Si no contesta, le pediremos a ${n} que vaya a verle.`,
    talk: "Hable con su médico o farmacéutico.",
    more: "Más",
    update: "Actualizar mis respuestas",
    note: "Traducción automática — por revisar" as string | null,
  },
};

/** First sentence only, so the headline reason stays one short line. */
const firstSentence = (s: string) => (/^.*?[.!?](\s|$)/.exec(s)?.[0] ?? s).trim();

async function PhoneForPatient({ params, searchParams }: { params: Promise<{ id: string }>; searchParams: SearchParams }) {
  const { id } = await params;
  const { lang: langParam } = await searchParams;
  const p = getPanelPatient(id, "replay");
  if (!p) {
    return <Placeholder title={`Demo phone: ${id}`}>Patient not found in data/processed/panel_scores_replay.json</Placeholder>;
  }
  const name = plainName(p.displayName);
  const g = riskGroup(p.readiness?.level);
  const heat = hourlyHeat();
  const hours = (heat?.hours ?? []).filter((h) => h.hour >= 6 && h.hour <= 22);
  const hot = hours.filter((h) => (h.heatIndexF ?? h.tempF) >= HOT_FEELS_LIKE_F);
  const symptoms = [...(p.stacking?.symptoms ?? [])].sort((a, b) => Number(b.stacked) - Number(a.stacked)).slice(0, 4);
  const masked = p.stacking?.maskedSigns ?? [];
  const contact = p.escalation?.contacts?.find((c) => c.contactId === p.escalation?.firstContactId);
  const es = (langParam === "en" || langParam === "es" ? langParam : p.language) === "es";
  const t = es ? T.es : T.en;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const mechanisms = ((p as any).stacking?.mechanisms ?? []) as { defense: string; label: string; drugs: string[] }[];
  const cabinet: CabinetEffect[] = mechanisms
    .filter((m) => m.drugs?.length)
    .map((m) => ({ id: m.defense, ...splitLabel(m.label), drugs: m.drugs }));
  const lang = es ? "es" : "en";
  const mapData = getPatientPlanMapData(p.patientId);
  const why = es ? patientWhyEs(p) : patientWhy(p);

  const plan = (
    <div className="space-y-8">
      {/* Language switch: shown when the patient's language isn't English, or when it's been overridden. */}
      {(p.language !== "en" || langParam) && (
        <p className="-mb-4 text-right text-base">
          <Link href={`/phone/${p.patientId}?lang=${es ? "en" : "es"}`} className="underline underline-offset-4 text-muted-foreground hover:text-ink">
            {es ? "Read in English" : "Ver en español"}
          </Link>
        </p>
      )}
      {/* 1. Risk headline (hero, same style as the home hero) + the map: "where do I go?" first */}
      <section className="space-y-2 text-center">
        <p className="text-base font-medium text-muted-foreground">{t.eyebrow}</p>
        <h2 className="text-patient-xl font-semibold leading-tight tracking-tight">
          {t.risk}{" "}
          <span className={`inline-block whitespace-nowrap rounded-full px-3 ${RISK[g].tint} ${RISK[g].ink}`}>{es ? RISK_LABEL_ES[g] : RISK[g].label}</span>
        </h2>
        <p className="text-muted-foreground">{firstSentence(why)}</p>
      </section>

      <PatientPlanMapView data={mapData} height={320} lang={lang} variant="patient" />

      <HelpContacts contacts={helpContactsFor(p.patientId)} lang={lang} sourceFile={HELP_FILE} />

      {/* 2. Stay inside: the hot hours, hour by hour (same hourly data as the time-lapse) */}
      <section className="space-y-3 rounded-lg border border-border bg-card p-4">
        {/* Hot hours → "Stay inside" + the hours. No hot hours → "No heat risk today" (no contradiction). */}
        <h2 className="text-patient-lg font-semibold tracking-tight">{hours.length && !hot.length ? t.noRisk : t.safest}</h2>
        {hours.length ? (
          <>
            <p className="font-semibold">{hot.length ? t.stayInside(hot[0].hour, hot[hot.length - 1].hour + 1) : t.noHot}</p>
            <div aria-label={t.hourByHour}>
              <HourByHour
                hours={hours.map((h) => ({ hour: h.hour, f: h.heatIndexF ?? h.tempF }))}
                hotF={HOT_FEELS_LIKE_F}
                lang={lang}
                startHour={hot[0]?.hour ?? 14}
              />
            </div>
          </>
        ) : (
          <Placeholder title="Hourly heat">Data goes here: {HOURLY_FILE}</Placeholder>
        )}
      </section>

      {/* 3. Medicine cabinet (visual) */}
      <MedicineCabinet
        effects={cabinet}
        title={es ? "Sus medicinas y el calor" : "Your medicines in the heat"}
        hint={es ? "Toque sus medicinas." : "Tap your medicines."}
        addsUp={es ? "Se suman" : "Adds up"}
      />

      {/* What to watch for (max 4): in a dropdown */}
      {symptoms.length > 0 && (
        <details className="rounded-lg border border-border bg-card p-4">
          <summary className="cursor-pointer text-patient-lg font-semibold tracking-tight">{t.watch}</summary>
          <ul className="mt-2 list-disc space-y-1 pl-6">
            {symptoms.map((s) => (
              <li key={s.sign}>{es ? SIGN_ES[s.sign] ?? s.label : s.label}</li>
            ))}
          </ul>
        </details>
      )}
    </div>
  );

  const footer = (
    <div className="space-y-4 pb-4">
      <p className="text-patient-lg font-semibold">{t.talk}</p>
      <details className="text-base text-muted-foreground">
        <summary className="flex min-h-tap cursor-pointer items-center font-semibold text-foreground">{t.more}</summary>
        <div className="space-y-2 pt-2">
          {why !== firstSentence(why) && <p>{why}</p>}
          {masked.map((m) => (
            <p key={m.sign}>
              <b>{t.mayNot(es ? SIGN_ES[m.sign] ?? m.label : m.label)}</b> {es ? MASKED_WHY_ES[m.sign] ?? m.why : m.why}.
            </p>
          ))}
          <PatientPlanMore data={mapData} lang={lang} />
          <p>{t.synthetic}. {t.replay}</p>
          {t.note && <p className="italic">{t.note}</p>}
          <Link href={`/phone/signup?patient=${p.patientId}`} className="inline-flex min-h-tap items-center underline">
            {t.update}
          </Link>
        </div>
      </details>
    </div>
  );

  return (
    <Phone
      patientId={p.patientId}
      firstName={name}
      language={lang}
      badge={t.synthetic}
      checkInNote={g === "high" ? t.checkIn + (contact ? t.contact(plainName(contact.name)) : "") : null}
      footer={footer}
    >
      {plan}
    </Phone>
  );
}
