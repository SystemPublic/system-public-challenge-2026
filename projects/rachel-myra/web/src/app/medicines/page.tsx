import type { Metadata } from "next";
import { KbSourceBanner } from "@/components/KbSourceBanner";
import { HeatMedicinePicture } from "@/components/medicines/HeatMedicinePicture";
import { MedicineList, type MedicineRow } from "@/components/medicines/MedicineList";
import { loadPathways, PATHWAYS_FILE } from "@/components/medicines/pathways";
import { loadKb, primaryBucket } from "@/lib/kb";
import { MedicineCabinet, type CabinetEffect } from "@/components/cabinet/MedicineCabinet";

// Body effects for the clinician cabinet: the KB's heat_stack (affected = "yes") plus its "other" defenses.
// Signs are the heat-illness warning signs each effect shares (CDC list), as on the patient side.
// "drug integrity" (storage) is left out: it is about the medicine, not the body.
const EFFECTS: { key: string; title: string; signs: string | null }[] = [
  { key: "sweating", title: "Sweating (cooling off)", signs: "hot, dry skin; overheating" },
  { key: "water_salt", title: "Water and salt", signs: "dizziness, confusion, cramps" },
  { key: "kidney_clearance", title: "Kidneys (medicine builds up)", signs: "confusion, nausea, tiredness" },
  { key: "blood_pressure", title: "Blood pressure", signs: "dizziness, fainting" },
  { key: "awareness", title: "Noticing heat and thirst", signs: "confusion, drowsiness" },
  { key: "thermostat", title: "Body temperature control", signs: "overheating" },
  { key: "heat production", title: "Body makes more heat", signs: "overheating" },
  { key: "absorption", title: "Medicine absorbed faster", signs: "medicine acts stronger" },
  { key: "blood sugar", title: "Blood sugar", signs: "shakiness, confusion" },
  { key: "skin", title: "Skin blood flow", signs: null },
];

function cabinetEffects(drugs: ReturnType<typeof loadKb>["kb"]["drugs"]): CabinetEffect[] {
  const by = new Map<string, Set<string>>();
  for (const d of drugs) {
    const name = d.names?.display ?? d.id;
    const hs = d.heat_stack as unknown as Record<string, { affected?: string } | undefined> & { other?: { defense: string }[] };
    for (const k of ["sweating", "water_salt", "kidney_clearance", "blood_pressure"])
      if (hs?.[k]?.affected === "yes") by.set(k, (by.get(k) ?? new Set()).add(name));
    for (const o of hs?.other ?? []) by.set(o.defense, (by.get(o.defense) ?? new Set()).add(name));
  }
  return EFFECTS.filter((e) => by.get(e.key)?.size).map((e) => ({ id: e.key, title: e.title, signs: e.signs, drugs: [...by.get(e.key)!] }));
}

export const metadata: Metadata = { title: "Medicines · Cool-Aid" };

export default function MedicinesPage() {
  const { kb, source, file } = loadKb();
  const rows: MedicineRow[] = kb.drugs.map((d) => ({ drug: d, bucket: primaryBucket(d) }));
  const pathways = loadPathways(kb.drugs.map((d) => ({ id: d.id, label: d.names?.display ?? d.id })));

  // Short title; the takeaway (which body effects most medicines share with heat) is in the picture itself.
  const title = "Heat and these medicines hit the same weak spots";

  return (
    <div className="space-y-10">
      <h1 className="text-3xl font-semibold tracking-tight">Medicines in the heat</h1>
      <HeatMedicinePicture data={pathways} title={title} source={PATHWAYS_FILE} />
      <MedicineCabinet
        effects={cabinetEffects(kb.drugs)}
        title="Combine medicines: what adds up in the heat"
        hint="Click two or more medicines. Effects they share light up as “Adds up”, with the warning signs to watch for."
        addsUp="Adds up"
        compact
      />
      <section className="space-y-3">
        <h2 className="text-xl font-semibold">What to do, by medicine</h2>
        <MedicineList rows={rows} />
      </section>
      <KbSourceBanner source={source} file={file} />
      <details className="text-xs text-ink-muted">
        <summary className="cursor-pointer">Sources</summary>
        <p className="mt-1">
          Medicines: {file ?? "inline fallback"}. &ldquo;Label warns about heat&rdquo;: data/processed/fda_label_heat_audit_summary_v2.csv.
          &ldquo;Guidance says what to do&rdquo;: data/processed/guidance_matrix.csv (at least one guidance document gives a
          drug-specific action). Picture: {PATHWAYS_FILE} and data/processed/system_drug_mediator_findings.csv.
        </p>
      </details>
    </div>
  );
}
