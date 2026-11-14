// GET: what the demo phone shows for one patient. Polled every ~2.5 s.
import { connection } from "next/server";
import { inbox } from "@/lib/loop";

// ?lang=en returns English reading copies of the message bodies (see lib/panel englishFor).
export async function GET(req: Request, ctx: { params: Promise<{ id: string }> }) {
  await connection();
  const { id } = await ctx.params;
  const lang = new URL(req.url).searchParams.get("lang");
  return Response.json(inbox(id, lang === "en" || lang === "es" ? lang : undefined));
}
