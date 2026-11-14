// POST { patientId, status: "ok" | "unwell" | "no_ac" } — a tap on the demo phone.
import { connection } from "next/server";
import { checkin, type CheckinStatus } from "@/lib/loop";

const VALID: CheckinStatus[] = ["ok", "unwell", "no_ac"];

export async function POST(req: Request) {
  await connection();
  const body = (await req.json().catch(() => ({}))) as { patientId?: string; status?: CheckinStatus };
  if (!body.patientId || !body.status || !VALID.includes(body.status)) {
    return Response.json({ ok: false, error: "patientId and status (ok|unwell|no_ac) required" }, { status: 400 });
  }
  return Response.json(checkin(body.patientId, body.status));
}
