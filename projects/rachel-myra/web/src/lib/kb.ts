// Data-access layer for the shared knowledge base (spec §3.1: one KB feeds
// clinician card, patient text and labels).
//
// Load order:
//   1. ../data/kb/knowledge_base.json       (real, built by the pipeline)
//   2. ../data/kb/mock_knowledge_base.json  (mock for UI work, same shape)
//   3. INLINE_FALLBACK below                (1 drug, qualitative only, so the
//                                            app still builds on a fresh clone)
//
// Server-only: uses node:fs. Pages read it at render time; under Cache
// Components, readFileSync is "predictable I/O", so pages are prerendered at
// build and re-read in dev on every request. Rebuild after the KB changes.
//
// Types come from the repo-root contract: lib/types/knowledge-base.ts.

import fs from "node:fs";
import path from "node:path";
import type {
  Bucket,
  DrugRecord,
  KnowledgeBase,
} from "@lib/types/knowledge-base.ts";

export type KbSource = "knowledge_base" | "mock_knowledge_base" | "inline_fallback";

export interface LoadedKb {
  kb: KnowledgeBase;
  source: KbSource;
  /** Repo-relative path that was read, or null for the inline fallback. */
  file: string | null;
}

/** Repo root = parent of web/. `next dev` / `next build` run with cwd = web/. */
export const REPO_ROOT = path.resolve(process.cwd(), "..");
const KB_DIR = path.join(REPO_ROOT, "data", "kb");
const PROCESSED_DIR = path.join(REPO_ROOT, "data", "processed");

const CANDIDATES: { source: KbSource; name: string }[] = [
  { source: "knowledge_base", name: "knowledge_base.json" },
  { source: "mock_knowledge_base", name: "mock_knowledge_base.json" },
];

function readJson<T>(file: string): T | null {
  try {
    return JSON.parse(fs.readFileSync(file, "utf8")) as T;
  } catch {
    return null;
  }
}

function isKb(x: unknown): x is KnowledgeBase {
  return (
    typeof x === "object" &&
    x !== null &&
    Array.isArray((x as { drugs?: unknown }).drugs)
  );
}

export function loadKb(): LoadedKb {
  for (const c of CANDIDATES) {
    const full = path.join(KB_DIR, c.name);
    if (!fs.existsSync(full)) continue;
    const parsed = readJson<unknown>(full);
    if (isKb(parsed) && parsed.drugs.length > 0) {
      return { kb: parsed, source: c.source, file: `data/kb/${c.name}` };
    }
  }
  return { kb: INLINE_FALLBACK, source: "inline_fallback", file: null };
}

export function getDrugs(): DrugRecord[] {
  return loadKb().kb.drugs;
}

export function getDrug(id: string): DrugRecord | null {
  return getDrugs().find((d) => d.id === id) ?? null;
}

/** Primary bucket (the tile color). Falls back to the first listed bucket. */
export function primaryBucket(d: DrugRecord): Bucket | null {
  const b = d.buckets?.find((x) => x.primary) ?? d.buckets?.[0];
  return b?.bucket ?? null;
}

/** Read a JSON file from ../data/processed/, or null if absent/invalid. */
export function readProcessedJson<T = unknown>(name: string): T | null {
  return readJson<T>(path.join(PROCESSED_DIR, path.basename(name)));
}

/** Files currently present in ../data/processed/ (name + size), for nerd stats. */
export function listProcessedFiles(): { name: string; bytes: number }[] {
  try {
    return fs
      .readdirSync(PROCESSED_DIR, { withFileTypes: true })
      .filter((e) => e.isFile())
      .map((e) => ({
        name: e.name,
        bytes: fs.statSync(path.join(PROCESSED_DIR, e.name)).size,
      }))
      .sort((a, b) => a.name.localeCompare(b.name));
  } catch {
    return [];
  }
}

// ---------------------------------------------------------------------------
// Inline fallback: ONE drug, wording from spec §4.2 / §6.2 only. No study
// numbers, no claims, no guidance coding. Every page shows a banner when this
// is in use. Delete once data/kb/ always has a KB file.
// ---------------------------------------------------------------------------
const FALLBACK_DISCLAIMER =
  "Prototype. Considerations for clinicians, not instructions.";

const INLINE_FALLBACK: KnowledgeBase = {
  schema_version: "inline-fallback",
  build_id: "inline-fallback",
  disclaimer: FALLBACK_DISCLAIMER,
  inputs: [],
  evidence_model: {
    formula: "",
    design_weights: {},
    population_match: {},
    meter_thresholds: { strong: 0, some: 0 },
    flag_change_rules: "",
  },
  anticholinergic_scale: { name: "", source: "", url: "", input_file: "" },
  combination_rules: [],
  drugs: [
    {
      id: "lithium",
      scope: "core15",
      names: {
        display: "Lithium",
        plain: "Lithium",
        class_label: "Mood stabilizer",
        examples: ["lithium carbonate"],
        ingredients: [],
        master_list_rows: [],
      },
      buckets: [
        {
          bucket: "monitor",
          primary: true,
          rationale: "Placeholder until the knowledge base is built.",
        },
      ],
      mechanism_groups: ["kidney_cleared_buildup"],
      label_line:
        "During a heat wave, check lithium levels: dehydration can push them into the toxic range.",
      evidence: {
        meter: "early_signs",
        meter_label: "Early signs",
        tier: { code: 8, label: "Not yet graded (placeholder)" },
        literature_score: 0,
        components: {
          design_weight: 0,
          independent_studies: 0,
          study_factor: 0,
          consistency: 0,
          population_match: 0,
        },
        direction: "evidence_gap",
        null_or_conflicting: [],
        plain_summary: "Evidence not loaded yet.",
      },
      flag: {
        level: "low",
        plain_label: "Check on this person",
        rationale: "Not scored yet (placeholder).",
        drivers: [],
      },
      change: {
        level: "low",
        plain_label: "Rethink the medicine",
        rationale: "Not scored yet (placeholder).",
        drivers: [],
      },
      compass: {
        arrow: "up",
        symbol: "↑",
        meaning: "Drug acts stronger in heat",
        mechanism: "Dehydration reduces kidney clearance, so lithium builds up.",
        triggers: ["forecast heat"],
        monitor: ["lithium levels"],
        evidence_meter: "early_signs",
        source_claim_ids: [],
        note: "Direction only, not doses.",
      },
      heat_stack: {
        sweating: { affected: "no", how: "" },
        water_salt: { affected: "possible", how: "" },
        kidney_clearance: { affected: "yes", how: "" },
        blood_pressure: { affected: "no", how: "" },
        other: [],
      },
      prescribers: ["psychiatry", "primary care"],
      higher_risk_groups: [],
      pediatric_note: null,
      guidance: {
        n_jurisdictions: 0,
        jurisdictions_mentioning: 0,
        jurisdictions_specific_action: 0,
        gap: false,
        gap_reason: "Guidance not coded yet (placeholder).",
        by_source: [],
        input_file: "",
      },
      fda_label: {
        class_status: "not audited",
        plain: "",
        ingredients: [],
        input_file: "",
      },
      faers: null,
      graph: {
        source: "",
        pathways: [],
        direct_findings: [],
        untested_links: [],
        validation_rank_nonbp: null,
        api: null,
        input_files: [],
      },
      claims: [],
      alternatives: [],
      combinations: [],
      timeline: [],
      patient_messages: [],
      storage: null,
      gaps: ["Knowledge base not built yet: this card is a layout placeholder."],
      disclaimer: FALLBACK_DISCLAIMER,
    },
  ],
};
