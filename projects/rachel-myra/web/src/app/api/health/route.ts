// Smoke test for the laptop and the demo phone: server up, SQLite readable, demo clock.
// Open http://<laptop-ip>:3000/api/health on the phone to check the Wi-Fi path.
import { connection } from "next/server";
import { db, demoNow } from "@/lib/db";

export async function GET() {
  await connection(); // always dynamic: never prerender a DB read
  const tables = db()
    .prepare("SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name")
    .all()
    .map((r) => (r as unknown as { name: string }).name);
  return Response.json({ ok: true, tables, demo_time: demoNow().toISOString() });
}
