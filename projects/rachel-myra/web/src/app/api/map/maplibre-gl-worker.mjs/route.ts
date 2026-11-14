// Serves MapLibre's web worker. Turbopack bundles maplibre-gl.mjs into a chunk, so its default
// worker URL (next to import.meta.url) 404s; DeckMap points setWorkerUrl here instead.
import fs from "node:fs";
import path from "node:path";

let cached: string | null = null;

export async function GET() {
  if (!cached) {
    const f = path.join(process.cwd(), "node_modules", "maplibre-gl", "dist", "maplibre-gl-worker.mjs");
    cached = fs.readFileSync(f, "utf8");
  }
  return new Response(cached, { headers: { "content-type": "text/javascript; charset=utf-8", "cache-control": "public, max-age=86400" } });
}
