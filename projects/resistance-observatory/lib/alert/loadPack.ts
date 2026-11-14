/**
 * Server-only: read the data pack from disk. The Alert page is prerendered,
 * so this runs at build time; the System route also reads the vetted id list
 * at request time. Returns null when the pack is not installed, and the tab
 * says so rather than showing anything invented.
 */
import { readFile } from "node:fs/promises";
import path from "node:path";
import type { StudyContextFile } from "./context";
import type { ClientPack, GenomesFile, GraphFile, LiteratureFile, Pack, ThresholdsFile } from "./pack";

const dir = () => process.env.ALERT_PACK_DIR || path.join(process.cwd(), "k540e-data-pack");

async function json<T>(name: string): Promise<T> {
  return JSON.parse(await readFile(path.join(dir(), name), "utf8")) as T;
}

let cached: Promise<Pack | null> | null = null;

export function loadPack(): Promise<Pack | null> {
  cached ??= (async () => {
    try {
      const [genomes, literature, graph, thresholds] = await Promise.all([
        json<GenomesFile>("k540e-genomes.json"),
        json<LiteratureFile>("k540e-literature.json"),
        json<GraphFile>("k540e-graph.json"),
        json<ThresholdsFile>("k540e-thresholds.json"),
      ]);
      // optional: the tab works without it and says the context is not recorded
      const studyContext = await json<StudyContextFile>("k540e-study-context.json").catch(() => null);
      return { genomes, literature, graph, thresholds, studyContext };
    } catch {
      return null;
    }
  })();
  return cached;
}

export function toClientPack(pack: Pack): ClientPack {
  const { vetted_association_ids, ...graph } = pack.graph;
  return { ...pack, graph: { ...graph, vetted_count: vetted_association_ids?.length ?? 0 } };
}

export async function vettedIds(): Promise<Set<string> | null> {
  const pack = await loadPack();
  const ids = pack?.graph.vetted_association_ids;
  return Array.isArray(ids) ? new Set(ids.map(String)) : null;
}
