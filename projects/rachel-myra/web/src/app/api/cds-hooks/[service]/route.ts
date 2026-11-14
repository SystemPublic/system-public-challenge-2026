// CDS Hooks service call (prototype, synthetic patients only).
//
// POST /api/cds-hooks/heat-medication-check   (hooks: order-select, order-sign, medication-prescribe)
// POST /api/cds-hooks/heat-plan-patient-view  (hook: patient-view)
//
// Returns one card when either:
//   - a heat-risk medicine (data/kb/knowledge_base.json, matched by RxNorm code or name)
//     appears in context.draftOrders / context.medications / prefetch, or
//   - context.patientId is a synthetic patient whose risk group is Medium or High
//     (data/processed/panel_scores_replay.json → readiness.level).
// The card links to the EHR side panel /ehr/<patientId> as an "absolute" link.
// (A real deployment would use a "smart" link to a SMART on FHIR launch URL
// so the panel opens inside the EHR with the patient in context.)
import { placeNote, tidyAddress, tidyPlaceName } from "@/lib/placeName";
import { randomUUID } from "node:crypto";
import { heatDrugsInRequest, KB_FILE, PANEL_FILE, patientFor } from "@/components/ehr/ehrPlan";
import { clinicianWhy, RISK, riskGroup } from "@/lib/risk";

const SERVICES = new Set(["heat-medication-check", "heat-plan-patient-view"]);

export async function POST(req: Request, ctx: RouteContext<"/api/cds-hooks/[service]">) {
  const { service } = await ctx.params;
  if (!SERVICES.has(service)) {
    return Response.json({ error: `Unknown service: ${service}` }, { status: 404 });
  }
  let body: { hook?: string; context?: Record<string, unknown>; prefetch?: Record<string, unknown> };
  try {
    body = await req.json();
  } catch {
    return Response.json({ error: "Body must be JSON (a CDS Hooks request)." }, { status: 400 });
  }

  const p = patientFor(body.context?.patientId);
  const g = p ? riskGroup(p.readiness?.level) : null;
  const drugs = heatDrugsInRequest(body);
  if (!drugs.length && g !== "high" && g !== "medium") return Response.json({ cards: [] });

  // Prefer the Host header: under `next dev` req.url can report 0.0.0.0.
  const host = req.headers.get("x-forwarded-host") ?? req.headers.get("host");
  const proto = req.headers.get("x-forwarded-proto") ?? new URL(req.url).protocol.replace(":", "");
  const origin = host ? `${proto}://${host}` : new URL(req.url).origin;
  const drugNames = drugs.map((d) => d.drug.names?.display ?? d.drug.id);
  const summary = (
    drugs.length
      ? `Heat wave: ${drugNames.join(", ")} ${drugNames.length > 1 ? "raise" : "raises"} heat risk${g ? ` (patient: ${RISK[g].label} risk)` : ""}`
      : `Heat wave: this patient is ${RISK[g!].label} heat risk`
  ).slice(0, 139);

  const detail = [
    ...drugs.map((d) => `- **${d.drug.names?.display ?? d.drug.id}**${d.ordered ? ` (ordered: ${d.ordered})` : ""}: ${d.drug.label_line ?? ""}`),
    p ? `\n**Why this patient (synthetic):** ${clinicianWhy(p)}` : "",
    p?.cooling?.best
      ? `\n**Nearest cool place:** ${tidyPlaceName(p.cooling.best.name)}${p.cooling.best.address ? ` (${tidyAddress(p.cooling.best.address)})` : ""}${placeNote(p.cooling.best.name) ? ` (${placeNote(p.cooling.best.name)})` : ""}${p.cooling.best.travelMin != null ? `, about ${p.cooling.best.travelMin} min walk` : ""}.`
      : "",
    "\nMedicine changes are the prescriber's decision. No dose advice is given.",
  ]
    .filter(Boolean)
    .join("\n");

  const card = {
    uuid: randomUUID(),
    summary,
    indicator: g === "high" ? "warning" : "info",
    detail,
    source: {
      label: "Cool-Aid (prototype, synthetic patients)",
      url: `${origin}/medicines`,
      topic: { system: "urn:the-missing-label:topic", code: "heat-medication", display: "Medicines in heat" },
    },
    links: p
      ? [{ label: "Open the heat plan (side panel)", url: `${origin}/ehr/${p.patientId}`, type: "absolute" }]
      : drugs.map((d) => ({ label: `What ${d.drug.names?.display ?? d.drug.id} does in heat`, url: `${origin}/drug/${d.drug.id}`, type: "absolute" })),
  };

  return Response.json({
    cards: [card],
    // Non-standard, for reviewers: where each part of the card comes from.
    _sources: [PANEL_FILE, KB_FILE],
  });
}
