// CDS Hooks discovery endpoint. Spec §4.6. Prototype, synthetic patients only.
// The CDS Hooks spec expects discovery at {base}/cds-services; point the
// sandbox at /api/cds-hooks and add a rewrite if it insists on that suffix.
// Service calls: POST /api/cds-hooks/<id> (see ./[service]/route.ts).

export function GET() {
  return Response.json({
    services: [
      {
        hook: "order-select",
        id: "heat-medication-check",
        title: "Cool-Aid: heat and medications",
        description:
          "Prototype. Returns a card when a heat-risk medicine is ordered, or when the synthetic patient is Medium or High heat risk. The card links to the patient's heat plan side panel (/ehr/<patientId>).",
        prefetch: {
          patient: "Patient/{{context.patientId}}",
          medications: "MedicationRequest?patient={{context.patientId}}&status=active",
        },
      },
      {
        hook: "patient-view",
        id: "heat-plan-patient-view",
        title: "Cool-Aid: heat plan",
        description:
          "Prototype. On opening a chart, returns a card for synthetic patients who are Medium or High heat risk, linking to their heat plan side panel.",
        prefetch: {
          medications: "MedicationRequest?patient={{context.patientId}}&status=active",
        },
      },
    ],
  });
}
