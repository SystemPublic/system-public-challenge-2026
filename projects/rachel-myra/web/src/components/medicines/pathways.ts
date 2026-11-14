// Server-only loader for the "How heat and medicine add up" picture (P5).
// Reads the full System API run (data/processed/system_api_pathways.csv) and,
// for example study titles, data/processed/system_drug_mediator_findings.csv.

import fs from "node:fs";
import path from "node:path";
import { REPO_ROOT } from "@/lib/kb";

export const PATHWAYS_FILE = "data/processed/system_api_pathways.csv";
export const FINDINGS_FILE = "data/processed/system_drug_mediator_findings.csv";

/** System pathway drug groups → knowledge-base drug ids (names and links). */
const GROUP_TO_KB: Record<string, string> = {
  anticholinergics: "anticholinergics_oxybutynin",
  antipsychotics: "antipsychotics_clozapine",
  ssris: "ssri",
  epinephrine_ai: "epinephrine_autoinjector",
  opioids_fentanyl: "opioid_patches_fentanyl",
};

/** Plain words for each body effect. Order = top to bottom in the picture. */
export const EFFECTS: { id: string; label: string }[] = [
  { id: "dehydration", label: "Dehydration" },
  { id: "hyponatremia", label: "Low salt" },
  { id: "aki", label: "Kidney strain" },
  { id: "sweating", label: "Can't sweat" },
  { id: "body_temp", label: "Body overheats" },
  { id: "bp_hypotension", label: "Low blood pressure" },
];

export interface PathwayLink {
  drug: string; // KB id
  effect: string;
  drugStudies: number;
  drugFindings: number;
  directStudies: number;
  examples: { title: string; year: string; pmid: string }[];
}

export interface PathwayData {
  drugs: { id: string; label: string }[];
  effects: { id: string; label: string; heatStudies: number }[];
  links: PathwayLink[];
  ok: boolean;
}

function parseCsv(text: string): Record<string, string>[] {
  const rows: string[][] = [];
  let row: string[] = [];
  let cur = "";
  let q = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (q) {
      if (c === '"' && text[i + 1] === '"') {
        cur += '"';
        i++;
      } else if (c === '"') q = false;
      else cur += c;
    } else if (c === '"') q = true;
    else if (c === ",") {
      row.push(cur);
      cur = "";
    } else if (c === "\n" || c === "\r") {
      if (c === "\r" && text[i + 1] === "\n") i++;
      row.push(cur);
      rows.push(row);
      row = [];
      cur = "";
    } else cur += c;
  }
  if (cur || row.length) {
    row.push(cur);
    rows.push(row);
  }
  const [head, ...body] = rows;
  if (!head) return [];
  return body.filter((r) => r.length > 1).map((r) => Object.fromEntries(head.map((h, i) => [h, r[i] ?? ""])));
}

function read(rel: string): Record<string, string>[] {
  try {
    return parseCsv(fs.readFileSync(path.join(REPO_ROOT, rel), "utf8"));
  } catch {
    return [];
  }
}

const num = (s: string | undefined) => {
  const n = Number(s);
  return Number.isFinite(n) ? n : 0;
};

export function loadPathways(kbDrugs: { id: string; label: string }[]): PathwayData {
  const rows = read(PATHWAYS_FILE).filter((r) => r.in_15 === "True");
  const findings = read(FINDINGS_FILE);
  const kbIds = new Set(kbDrugs.map((d) => d.id));
  const toKb = (g: string) => GROUP_TO_KB[g] ?? g;

  const heat = new Map<string, number>();
  const links: PathwayLink[] = [];
  for (const r of rows) {
    const drug = toKb(r.drug_group);
    if (!kbIds.has(drug)) continue;
    heat.set(r.mediator, Math.max(heat.get(r.mediator) ?? 0, num(r.heat_leg_studies)));
    const drugStudies = num(r.drug_leg_studies);
    if (drugStudies <= 0) continue;
    const seen = new Set<string>();
    const examples = findings
      .filter((f) => f.drug_group === r.drug_group && f.mediator_group === r.mediator && f.title_pubmed)
      .sort((a, b) => num(b.pub_year) - num(a.pub_year))
      .filter((f) => (seen.has(f.pubmed_id) ? false : (seen.add(f.pubmed_id), true)))
      .slice(0, 3)
      .map((f) => ({ title: f.title_pubmed, year: f.pub_year, pmid: f.pubmed_id }));
    links.push({
      drug,
      effect: r.mediator,
      drugStudies,
      drugFindings: num(r.drug_leg_findings),
      directStudies: num(r.direct_drug_heat_studies),
      examples,
    });
  }

  return {
    drugs: kbDrugs,
    effects: EFFECTS.filter((e) => heat.has(e.id)).map((e) => ({ ...e, heatStudies: heat.get(e.id) ?? 0 })),
    links,
    ok: rows.length > 0,
  };
}
