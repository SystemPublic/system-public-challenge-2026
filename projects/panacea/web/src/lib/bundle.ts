import { readFileSync } from "node:fs";
import path from "node:path";

// Types for dashboard/out/bundle.json, produced by dashboard/build_dashboard.py.
// One concept/measure dict entry per id; lookups everywhere else key off those.

export type ConceptMeta = { l: string; d: string; dm: string; nyc: boolean };
export type MeasureMeta = {
  l: string;
  themes: string;
  mt: string;
  yr: string;
  coll: string;
  mod: boolean;
};
export type ConceptDict = Record<string, ConceptMeta>;
export type MeasureDict = Record<string, MeasureMeta>;

export type ConfirmationRow = {
  c1: string;
  c2: string;
  na: number;
  np: number;
  med: number | null;
  et: string[];
  rho: number | null;
  nd: number | null;
  /** expected sign of the city correlation from the SPG effects: 1 up, −1 down, null ambiguous */
  dir: number | null;
  /** how many signable effects backed `dir` */
  nsigns: number;
  /** how the city ρ compares to `dir`: same / opposite / flat / ambiguous / no_rho */
  agree: "same" | "opposite" | "flat" | "ambiguous" | "no_rho";
  chk: [string, string] | null;
  mod: boolean;
  note: string;
  rel: { f: number; st: number } | null;
  pms: string[];
  m1: string[];
  m2: string[];
  sh: string[];
  nsh: number;
};

export type Ego = {
  deg: number;
  nbrs: {
    id: string;
    f: number;
    st: number;
    nyc: boolean;
    /** association aggregate for this edge, when the deposit has any */
    na?: number | null;
    med?: number | null;
    et?: string | null;
  }[];
};

/** Association aggregates for one relationship edge, where they exist. */
export type AssocStats = { na: number | null; med: number | null; et: string | null };

export type BridgeOneStep = {
  id: string;
  /** edges to each concept on the A side */
  ea: ({ a: string; f: number; st: number } & AssocStats & { pms?: string[] })[];
  /** edges to each concept on the B side */
  eb: ({ b: string; f: number; st: number } & AssocStats & { pms?: string[] })[];
  /** hypothesis-chip headline */
  head: string;
  /** short narrative with [n] citation markers into `pms` */
  story: string;
  /** PubMed IDs backing the story's citations */
  pms: string[];
};

export type BridgeTwoStep = {
  x: string;
  y: string;
  /** weakest-edge path score */
  s: number;
  ea: { a: string; f: number; st: number } & AssocStats & { pms?: string[] };
  xy: { f: number; st: number } & AssocStats & { pms?: string[] };
  eb: { b: string; f: number; st: number } & AssocStats & { pms?: string[] };
  head: string;
  story: string;
  pms: string[];
};

export type BridgeRow = {
  m1: string;
  m2: string;
  rho: number;
  yr1: string;
  yr2: string;
  l1: string;
  l2: string;
};

export type Bridge = {
  A: string[];
  B: string[];
  rows: BridgeRow[];
  nsh: number;
  n_one: number;
  n_two: number;
  one: BridgeOneStep[];
  two: BridgeTwoStep[];
  /** ≤250-char plain-language caption generated at build time */
  cap: string;
};

export type Contested = {
  cards: { t: string; b: string }[];
  spot: {
    check: string;
    measure1: string;
    measure2: string;
    spearman_uhf42: number;
    n_districts: number;
    expectation: string;
  }[];
  vintage: { id: string; l: string; coll: string; yr: string; mod: boolean }[];
  modeled: { conf_modeled: number; conf_observed: number; conf_no_rho: number };
};

/** One hop of a mediated chain. */
export type MediatedEdge =
  | {
      /** documented SPG edge (findings/studies/associations + median effect) */
      kind: "spg";
      f: number;
      st: number;
      na: number | null;
      med: number | null;
      et: string | null;
    }
  | {
      /** hop carried entirely by NYC district data, no/negligible SPG edge */
      kind: "nyc";
      rho: number;
      graph_f: number;
      na: number;
      /** only on the curated flagship: the measures behind this hop */
      measures?: string[];
    }
  | {
      /** assumed physical mechanism, not separately evidenced in either dataset */
      kind: "mech";
    };

/** A mixed-evidence chain: SPG hop + NYC hop assembling a link the graph lacks. */
export type MediatedChain = {
  a: string;
  x: string;
  b: string;
  /** concept ids along the chain, endpoint to endpoint */
  nodes: string[];
  edges: MediatedEdge[];
  /** |ρ| of the NYC hop */
  r_hop: number;
  /** the two measures behind the NYC hop */
  r_hop_measures: string[];
  /** city ρ between the assembled endpoints themselves, or null */
  r_ab: number | null;
  /** SPG findings for the city hop's link (0 = none at all) */
  graph_fb: number;
  l1: string;
  lx: string;
  l2: string;
  /** present only on the curated flagship */
  curated?: boolean;
  note?: string;
};

export type Bundle = {
  meta: Record<string, string | number> & { citations: string };
  concepts: ConceptDict;
  measures: MeasureDict;
  confirmations: ConfirmationRow[];
  egos: Record<string, Ego>;
  bridges: Bridge[];
  mediated: MediatedChain[];
  contested: Contested;
};

/** web/data/districts.json, produced by dashboard/build_districts.py */
export type District = {
  id: string;
  name: string;
  lat: number;
  lon: number;
  /** polygons -> rings -> [lon, lat] */
  polys: number[][][][];
};
export type DistrictValue = { v: number; tp: string; rel: string };
export type Districts = {
  districts: District[];
  values: Record<string, Record<string, DistrictValue>>;
};

let bundleCache: Bundle | null = null;

export function getBundle(): Bundle {
  if (!bundleCache) {
    bundleCache = JSON.parse(
      readFileSync(path.join(process.cwd(), "data", "bundle.json"), "utf8"),
    ) as Bundle;
  }
  return bundleCache;
}

let districtsCache: Districts | null = null;

export function getDistricts(): Districts {
  if (!districtsCache) {
    districtsCache = JSON.parse(
      readFileSync(path.join(process.cwd(), "data", "districts.json"), "utf8"),
    ) as Districts;
  }
  return districtsCache;
}
