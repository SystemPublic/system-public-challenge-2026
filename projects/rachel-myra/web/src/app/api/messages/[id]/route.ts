// GET: the clinician's conversation with one patient (header + thread). Polled every ~2.5 s.
// POST { body }: the clinician texts the patient (simulated; shows on the demo phone too).
import { connection } from "next/server";
import { patientHeader, sendText, thread } from "@/lib/conversation";
import { tick } from "@/lib/loop";

export async function GET(_req: Request, ctx: { params: Promise<{ id: string }> }) {
  await connection();
  const { id } = await ctx.params;
  const header = patientHeader(id);
  if (!header) return Response.json({ ok: false, error: `${id} not found` }, { status: 404 });
  tick();
  return Response.json({ ok: true, header, ...thread(id) });
}

export async function POST(req: Request, ctx: { params: Promise<{ id: string }> }) {
  await connection();
  const { id } = await ctx.params;
  const body = (await req.json().catch(() => ({}))) as { body?: string };
  const res = sendText(id, String(body.body ?? ""));
  return Response.json(res, { status: res.ok ? 200 : 400 });
}
