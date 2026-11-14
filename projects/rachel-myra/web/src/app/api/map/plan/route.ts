// GET /api/map/plan?id=S01 → data for the patient "where to go" map (see components/map/patientPlanData.ts).
import { connection } from "next/server";
import { getPatientPlanMapData } from "@/components/map/patientPlanData";

export async function GET(req: Request) {
  await connection();
  const id = new URL(req.url).searchParams.get("id");
  if (!id) return Response.json({ error: "id required" }, { status: 400 });
  return Response.json(getPatientPlanMapData(id));
}
