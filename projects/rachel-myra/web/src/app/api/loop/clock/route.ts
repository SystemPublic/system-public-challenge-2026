// POST { minutes: number } fast-forwards the demo clock; POST { reset: true } wipes live state.
import { connection } from "next/server";
import { demoNow, fastForward, resetDemo } from "@/lib/db";

export async function POST(req: Request) {
  await connection();
  const body = (await req.json().catch(() => ({}))) as { minutes?: number; reset?: boolean };
  if (body.reset) {
    resetDemo();
    return Response.json({ ok: true, reset: true, demo_time: demoNow().toISOString() });
  }
  const m = Number(body.minutes);
  if (!Number.isFinite(m) || m <= 0 || m > 24 * 60) {
    return Response.json({ ok: false, error: "minutes must be between 0 and 1440" }, { status: 400 });
  }
  return Response.json({ ok: true, demo_time: fastForward(m).toISOString() });
}
