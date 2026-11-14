// Preview of the patient "where to go" map on its own (the patient app embeds the same component).
import { Suspense } from "react";
import PatientPlanMap from "@/components/map/PatientPlanMap";

export const metadata = { title: "Where to go · Cool-Aid" };

async function Plan({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <PatientPlanMap patientId={id} height={340} />;
}

export default function PlanPreviewPage({ params }: { params: Promise<{ id: string }> }) {
  return (
    <div className="mx-auto max-w-md space-y-4">
      <h1 className="text-3xl font-bold">Where to go</h1>
      <Suspense fallback={<p className="text-lg">Loading…</p>}>
        <Plan params={params} />
      </Suspense>
    </div>
  );
}
