// GET /api/map/place?id=CR00000 → one help place's card fields (community_resources_nyc.geojson).
import { connection } from "next/server";
import { loadHelp } from "@/components/map/data";

export async function GET(req: Request) {
  await connection();
  const id = new URL(req.url).searchParams.get("id");
  const place = id ? loadHelp()?.byId.get(id) : null;
  if (!place) return Response.json({ error: "not found" }, { status: 404 });
  return Response.json(place);
}
