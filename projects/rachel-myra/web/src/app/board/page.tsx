import type { Metadata } from "next";
import { Placeholder } from "@/components/Placeholder";
import { primaryBucket } from "@/lib/kb";
import { loadPanel } from "@/lib/panel";
import { clinicianWhy, plainName, riskGroup, whyBullets } from "@/lib/risk";
import { callInsteadIds, kbDrugFor, QUESTIONNAIRE_FILE } from "@/lib/synthetic";
import { Board, type BoardRow } from "./Board";

export const metadata: Metadata = { title: "Patients · Cool-Aid" };

// Clinician side: synthetic patients in High / Medium / Low risk groups.
// Groups and reasons: data/processed/panel_scores_replay.json (readiness, stacking, lifestyle).
export default function BoardPage() {
  const panel = loadPanel("replay");
  if (!panel) {
    return (
      <Placeholder title="Patients" spec="§4.0">
        Data goes here: data/processed/panel_scores_replay.json (run scripts/compute_panel.ts).
      </Placeholder>
    );
  }
  const callOnly = new Set(callInsteadIds());
  const rows: BoardRow[] = panel.data.patients.map((p) => {
    const meds = p.meds?.heatRelevantDrugs ?? [];
    return {
      id: p.patientId,
      name: plainName(p.displayName),
      age: p.age,
      zip: p.zip,
      group: riskGroup(p.readiness?.level),
      why: clinicianWhy(p),
      callInstead: callOnly.has(p.patientId),
      detail: {
        bullets: whyBullets(p),
        meds: meds.map((m) => {
          const d = kbDrugFor(m);
          return {
            name: m,
            kbId: d?.id ?? null,
            kbName: d?.names?.display ?? null,
            bucket: d ? primaryBucket(d) : null,
            line: d?.label_line ?? null,
            sources: (d?.claims ?? [])
              .filter((c) => c.source?.url)
              .slice(0, 2)
              .map((c) => ({ label: c.source.label, url: c.source.url as string })),
          };
        }),
        pathways: (p.stacking?.mechanisms ?? [])
          .filter((m) => m.system.length)
          .map((m) => ({
            label: m.label,
            drugs: m.drugs,
            stacked: m.stacked,
            system: m.system.map((s) => ({
              mediator: s.mediatorLabel,
              heatStudies: s.heatLegStudies,
              drugLegs: s.drugLegs,
            })),
            note: m.graphNote,
          })),
        systemSource: p.stacking?.systemSource ?? null,
        caveat: p.stacking?.caveat ?? null,
      },
    };
  });
  return <Board rows={rows} source={panel.file} questionnaireFile={QUESTIONNAIRE_FILE} asOf={panel.data.meta.as_of} />;
}
