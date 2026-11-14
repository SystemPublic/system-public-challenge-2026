// POST { patientIds: string[], scenario?: "replay" | "today", mode?: "text" | "call" } → send each their group message.
import { connection } from "next/server";
import { sendAlert, type SendMode } from "@/lib/loop";
import type { Scenario } from "@/lib/panel";

export async function POST(req: Request) {
  await connection();
  const body = (await req.json().catch(() => ({}))) as { patientIds?: string[]; scenario?: Scenario; mode?: SendMode };
  const ids = Array.isArray(body.patientIds) ? body.patientIds : [];
  if (!ids.length) return Response.json({ ok: false, error: "patientIds required" }, { status: 400 });
  const scenario: Scenario = body.scenario === "today" ? "today" : "replay";
  return Response.json({ ok: true, results: ids.map((id) => ({ id, ...sendAlert(id, scenario, body.mode === "call" ? "call" : "text") })) });
}
