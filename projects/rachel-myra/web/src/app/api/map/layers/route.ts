// GET /api/map/layers → slim heat areas (hvi_nta2020.geojson) + help place points (community_resources_nyc.geojson).
import { connection } from "next/server";
import { FILES, loadHeatAreas, loadHelp } from "@/components/map/data";

export async function GET() {
  await connection();
  const heat = loadHeatAreas();
  const help = loadHelp();
  return Response.json({
    heat: heat ? { type: "FeatureCollection", features: heat.areas } : null,
    help: help ? help.points : null,
    files: { heat: FILES.heat, help: FILES.help },
  });
}
