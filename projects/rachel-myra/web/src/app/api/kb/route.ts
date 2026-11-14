// Read-only knowledge-base index: which file is loaded and which drugs it has.
import { loadKb } from "@/lib/kb";

export function GET() {
  const { kb, source, file } = loadKb();
  return Response.json({
    source,
    file,
    schema_version: kb.schema_version,
    build_id: kb.build_id,
    drugs: kb.drugs.map((d) => ({ id: d.id, name: d.names?.display ?? d.id })),
  });
}
