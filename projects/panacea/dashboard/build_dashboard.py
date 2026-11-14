#!/usr/bin/env python3
"""Build the dashboard data bundle for the Next.js app (web/).

Stages:
  0. small tables (concept map, connections, bridge selection, measures, domains)
  1. pass A over relationships.csv -> full adjacency for endpoint concepts,
     direct-edge assertions, confirmation-pair relationship counts
  2. pass B -> subgraph among candidate path intermediates
  3. connection subgraphs for the 10 unique bridge concept-set pairs
     (1-step shared connectors + strongest 2-step corridors, per-edge evidence)
  4. associations pass -> per-edge effect aggregates + pubmed samples
  5. JSON bundle -> dashboard/out/bundle.json + web/data/bundle.json
     (the web frontend renders it; the old single-HTML build is retired)

Run: python3 -I dashboard/build_dashboard.py   (~6-9 min: two relationship scans)
"""
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent.parent
DV = BASE / "dataverse_files"
NYC = BASE / "nyc_open_data"
MOUT = BASE / "mapping" / "out"
IOUT = BASE / "insights" / "out"
DOUT = Path(__file__).resolve().parent / "out"
DOUT.mkdir(parents=True, exist_ok=True)
SRC = Path(__file__).resolve().parent / "src"

K_EGO = 12          # top neighbors shown per ego endpoint
KX = 20             # candidate intermediates per endpoint for 2-step paths
MAX_ONE = 40        # 1-step connectors shipped per bridge pair (rest counted)
MAX_TWO = 25        # 2-step corridors shipped per bridge pair
MAX_SHARED = 15     # shared neighbors shipped per confirmation pair

report = {"assertions": {}, "counts": {}}


def log(msg):
    print(msg, flush=True)


def strength(f, st):
    return math.log10(1 + f) + 0.5 * math.log10(1 + st)


# statistic-type families used for direction inference (mean differences and
# bare coefficients are excluded: their sign depends on unstated variable order)
RATIO_TYPES = {"odds_ratio", "adjusted_odds_ratio", "hazard_ratio",
               "adjusted_hazard_ratio", "relative_risk_ratio", "prevalence_ratio",
               "incident_rate_ratio"}
CORR_TYPES = {"pearson_r", "spearman_correlation"}


# ---------------------------------------------------------------- stage 0
log("Stage 0: small tables")
cmap = pd.read_csv(MOUT / "concept_map.csv").fillna("")
measure_to_concepts = defaultdict(set)
concept_to_measures = defaultdict(list)
for _, r in cmap.iterrows():
    measure_to_concepts[r.nyc_id].add(r.spg_system_id)
    concept_to_measures[r.spg_system_id].append(r.nyc_id)
mapped_concepts = set(cmap.spg_system_id)

conn = pd.read_csv(IOUT / "connections.csv")
cross = conn[~conn.self_pair].copy()
report["counts"]["confirmed_pairs"] = len(cross)
report["counts"]["self_pairs_excluded"] = int(conn.self_pair.sum())
report["counts"]["rho_pairs"] = int(cross.city_spearman_uhf42.notna().sum())
report["counts"]["rho_modeled"] = int(cross.city_check_modeled.sum())
conf_pairs = list(cross.itertuples())
pair_fs = {frozenset((r.c1, r.c2)) for r in conf_pairs}
endpoint_concepts = sorted({r.c1 for r in conf_pairs} | {r.c2 for r in conf_pairs})
report["counts"]["endpoint_concepts"] = len(endpoint_concepts)

# the 12 bridge rows: same selection rule as INSIGHTS.md (non-modeled, |rho| desc, stable)
bridges_all = pd.read_csv(IOUT / "bridges.csv")
obs = bridges_all[~(bridges_all.modeled1 | bridges_all.modeled2)]
obs = obs.reindex(obs.city_spearman_uhf42.abs().sort_values(ascending=False, kind="stable").index)
b12 = obs.head(12)


def norm_mid(m):  # bridges.csv uses bare "measure:N"; concept_map uses "ehdp:measure:N"
    return m if m.startswith("ehdp:") else "ehdp:" + m


b12 = b12.assign(m1n=b12.measure1.map(norm_mid), m2n=b12.measure2.map(norm_mid))
missing = [m for m in list(b12.m1n) + list(b12.m2n) if m not in measure_to_concepts]
assert not missing, f"bridge measures not in concept map: {missing}"
report["counts"]["bridge_rows"] = len(b12)

bridge_sets = {}   # key -> {"A": [...], "B": [...], "rows": [...]}
for r in b12.itertuples():
    key = frozenset((tuple(sorted(measure_to_concepts[r.m1n])),
                     tuple(sorted(measure_to_concepts[r.m2n]))))
    e = bridge_sets.setdefault(key, {"A": sorted(measure_to_concepts[r.m1n]),
                                     "B": sorted(measure_to_concepts[r.m2n]),
                                     "rows": []})
    assert e["A"] == sorted(measure_to_concepts[r.m1n])
    e["rows"].append(r)
report["counts"]["bridge_keys"] = len(bridge_sets)
bridge_endpoints = sorted({c for e in bridge_sets.values() for c in e["A"] + e["B"]})
report["counts"]["bridge_endpoints"] = len(bridge_endpoints)
ENDPOINTS = set(endpoint_concepts) | set(bridge_endpoints) | mapped_concepts
bridge_cross_fs = {frozenset((a, b)) for e in bridge_sets.values()
                   for a in e["A"] for b in e["B"]}

nyc = pd.read_csv(MOUT / "nyc_concepts.csv").fillna("")
measures = {}
for _, r in nyc.iterrows():
    yr = str(r.year_range)
    if "-" not in yr:
        yr = f"{yr}-{yr}"
    measures[r.nyc_id] = {
        "l": r.label, "themes": r.themes, "mt": r.measurement_type,
        "yr": yr, "coll": r.collection,
        "mod": bool(re.search(r"Estimated annual", str(r.measurement_type))),
    }

full = pd.read_csv(DV / "system-public-graph-v1-concepts-1.csv", dtype=str).fillna("")
concept_meta = {s: (lab, d[:140])
                for s, lab, d in zip(full.system_id, full.wikidata_label,
                                     full.wikidata_description)}
dom = pd.read_csv(MOUT / "spg_concepts.csv").fillna("")
domains = dict(zip(dom.system_id, dom.domains))

spot = pd.read_csv(IOUT / "spot_checks.csv")

# ---------------------------------------------------------------- pass A
log("Pass A over relationships.csv (egos + bridge adjacency + assertions)...")
adj = {c: {} for c in ENDPOINTS}          # cid -> {nbr: (findings, studies)}
pair_rel = {}                             # confirmation frozenset -> (f, st)
bridge_cross_hits = 0
dup_disagree = dup_total = 0
use = ["source_concept.system_id", "target_concept.system_id",
       "num_findings", "num_studies"]
for ch in pd.read_csv(DV / "system-public-graph-v1-relationships.csv",
                      usecols=use, dtype=str, chunksize=400_000):
    s_arr = ch["source_concept.system_id"].to_numpy()
    t_arr = ch["target_concept.system_id"].to_numpy()
    f_arr = ch["num_findings"].astype(float).to_numpy()
    st_arr = ch["num_studies"].astype(float).to_numpy()
    for s, t, f, st in zip(s_arr, t_arr, f_arr, st_arr):
        if s == t:
            continue
        f, st = int(f), int(st)
        if frozenset((s, t)) in bridge_cross_fs:
            bridge_cross_hits += 1
        if s in ENDPOINTS:
            d = adj[s].get(t)
            if d is None:
                adj[s][t] = (f, st)
            else:
                dup_total += 1
                if (f, st) != d:
                    dup_disagree += 1
                if (f, st) > d:
                    adj[s][t] = (f, st)
        if t in ENDPOINTS:
            d = adj[t].get(s)
            if d is None:
                adj[t][s] = (f, st)
            else:
                if (f, st) > d:
                    adj[t][s] = (f, st)
        fs = frozenset((s, t))
        if fs in pair_fs and fs not in pair_rel:
            pair_rel[fs] = (f, st)

report["assertions"]["bridge_direct_relationships"] = bridge_cross_hits
assert bridge_cross_hits == 0, "bridge premise broken: direct relationship edges exist"
report["counts"]["both_direction_pairs_seen"] = dup_total
report["counts"]["both_direction_disagreeing"] = dup_disagree
missing_rel = sum(1 for fs in pair_fs if fs not in pair_rel)
report["counts"]["confirmed_pairs_without_relationship_edge"] = missing_rel
log(f"  direct bridge edges: {bridge_cross_hits}; dup-direction rows: {dup_total} "
    f"({dup_disagree} disagreeing); confirmed pairs w/o rel edge: {missing_rel}")

# ---------------------------------------------------------------- pass B
log("Pass B: candidate intermediates + subgraph scan...")
cand = set(mapped_concepts)
shared_full = {}
for key, e in bridge_sets.items():
    Na, Nb = set(), set()
    for a in e["A"]:
        Na |= set(adj[a])
    for b in e["B"]:
        Nb |= set(adj[b])
    sh = (Na & Nb) - set(e["A"]) - set(e["B"])
    shared_full[key] = sh
    for a in e["A"]:
        top = sorted(adj[a].items(), key=lambda kv: -strength(*kv[1]))[:KX]
        cand.update(n for n, _ in top)
    for b in e["B"]:
        top = sorted(adj[b].items(), key=lambda kv: -strength(*kv[1]))[:KX]
        cand.update(n for n, _ in top)
    cand.update(sh)
report["counts"]["candidate_nodes"] = len(cand)

cadj = defaultdict(dict)
for ch in pd.read_csv(DV / "system-public-graph-v1-relationships.csv",
                      usecols=use, dtype=str, chunksize=400_000):
    for s, t, f, st in zip(ch["source_concept.system_id"].to_numpy(),
                           ch["target_concept.system_id"].to_numpy(),
                           ch["num_findings"].astype(float).to_numpy(),
                           ch["num_studies"].astype(float).to_numpy()):
        if s == t or s not in cand or t not in cand:
            continue
        f, st = int(f), int(st)
        d = cadj[s].get(t)
        if d is None or (f, st) > d:
            cadj[s][t] = (f, st)
            cadj[t][s] = (f, st)
report["counts"]["subgraph_edges"] = sum(len(v) for v in cadj.values()) // 2
log(f"  candidates: {len(cand)}, subgraph edges: {report['counts']['subgraph_edges']}")

# ---------------------------------------------------------------- subgraphs
log("Connection subgraphs for bridge pairs...")


def best_endpoint_edge(A, x):
    """strongest edge from any endpoint concept in A to x -> (score, a, f, st)"""
    best = None
    for a in A:
        if a == x:
            continue
        d = adj[a].get(x)  # adj is complete from the endpoint side (both directions recorded)
        if d is None:
            continue
        sc = strength(*d)
        if best is None or sc > best[0]:
            best = (sc, a, d[0], d[1])
    return best


def top_candidates(Bset, Na=None):
    """top-KX neighbors (union over the side's endpoints) by score"""
    pool = {}
    for e in Bset:
        for n, (f, st) in adj[e].items():
            sc = strength(f, st)
            if n not in pool or sc > pool[n][0]:
                pool[n] = (sc, f, st)
    ranked = sorted(pool.items(), key=lambda kv: -kv[1][0])[:KX]
    return [n for n, _ in ranked]


bridge_results = []
for key, e in bridge_sets.items():
    A, B = e["A"], e["B"]
    Aset, Bset = set(A), set(B)

    # --- 1-step: every shared connector, with ALL its edges to both sides
    one = []
    for x in shared_full[key]:
        ea = []
        for a in A:
            d = adj[a].get(x)
            if d:
                ea.append({"a": a, "f": d[0], "st": d[1]})
        eb = []
        for b in B:
            d = adj[b].get(x)
            if d:
                eb.append({"b": b, "f": d[0], "st": d[1]})
        if not ea or not eb:
            continue
        s = max(strength(d["f"], d["st"]) for d in ea + eb)
        one.append({"id": x, "s": s, "ea": ea, "eb": eb})
    one.sort(key=lambda c: (-c["s"], c["id"]))
    n_one = len(one)
    one = one[:MAX_ONE]

    # --- 2-step corridors through the strongest intermediates
    X = [x for x in top_candidates(A) if x not in Aset | Bset]
    Y = [y for y in top_candidates(B) if y not in Aset | Bset]
    two = []
    n_two = 0
    for x in X:
        for y in Y:
            if x == y:
                continue
            dxy = cadj[x].get(y)
            if dxy is None:
                continue
            ea = best_endpoint_edge(A, x)
            eb = best_endpoint_edge(B, y)
            if not ea or not eb or ea[1] == eb[1] or ea[1] == y or eb[1] == x:
                continue
            n_two += 1
            score = min(ea[0], strength(*dxy), eb[0])
            two.append({"x": x, "y": y, "s": score,
                        "ea": (ea[1], ea[2], ea[3]),
                        "xy": dxy, "eb": (eb[1], eb[2], eb[3])})
    two.sort(key=lambda c: (-c["s"], -(c["ea"][1] + c["xy"][0] + c["eb"][1]),
                            c["x"], c["y"]))
    two = two[:MAX_TWO]
    bridge_results.append({"key": key, "A": A, "B": B, "rows": e["rows"],
                           "one": one, "n_one": n_one,
                           "two": two, "n_two": n_two,
                           "n_shared": len(shared_full[key])})
    log(f"  {A[0]}.. x {B[0]}..: shared={len(shared_full[key])} "
        f"(ship {len(one)}) 2hop={n_two} (ship {len(two)})")

# ---------------------------------------------------------------- city rho matrix
# Spearman across UHF42 districts for every measure pair mapped to mapped concepts —
# used to score "city support" anywhere on a mediated chain.
log("City rho matrix (EHDP UHF42, mapped measures)...")
import gzip
_mids = sorted({m[len("ehdp:"):] for c in mapped_concepts for m in concept_to_measures[c]
                if m.startswith("ehdp:")})
recs = []
with gzip.open(NYC / "data" / "environment-health" /
               "environment-health.v1.0.0.records.ndjson.gz", "rt") as fh:
    for line in fh:
        if '"type":"Observation"' not in line:
            continue
        d = json.loads(line)["data"]
        if d.get("geoType") == "UHF42" and isinstance(d.get("value"), (int, float)):
            recs.append((d["measureId"], d["geographyId"], d["value"]))
_piv = pd.DataFrame(recs, columns=["m", "g", "v"]).pivot_table(
    index="g", columns="m", values="v", aggfunc="first")
keep = [m for m in _mids if m in _piv.columns]
sub = _piv[keep]
_rho_cols = {}
for i, a in enumerate(keep):
    for b in keep[i + 1:]:
        j = sub[[a, b]].dropna()
        if len(j) < 25:
            continue
        r = j.corr(method="spearman").iloc[0, 1]
        if pd.notna(r):
            _rho_cols[frozenset((a, b))] = float(r)


def rho_cc(c1, c2):
    """max |rho| across any measure pair mapped to the two concepts, excluding
    functional duplicates (|rho| >= 0.95) and same-theme pairs.
    -> (rho, m1, m2) or None."""
    best = None
    for m1 in concept_to_measures[c1]:
        if not m1.startswith("ehdp:"):
            continue
        for m2 in concept_to_measures[c2]:
            if not m2.startswith("ehdp:"):
                continue
            r = _rho_cols.get(frozenset((m1[len("ehdp:"):], m2[len("ehdp:"):])))
            if r is None or abs(r) >= 0.95:
                continue  # |rho| ~ 1 = functional duplicate (complementary percents etc.)
            if best is None or abs(r) > abs(best[0]):
                best = (r, m1, m2)
    return best


# ---------------------------------------------------------------- mediated search
# Mixed-evidence chains: ONE hop is a documented SPG edge (>=2 findings, >=2 studies);
# the OTHER hop is carried entirely by NYC data (|rho| >= 0.45 across UHF42 districts)
# with no -- or only negligible (<2 findings) -- SPG evidence for that same link.
# The assembled connection a->b does not exist in the SPG at all: graph + city together
# produce a relationship the graph never contained.
log("Mixed-chain search (SPG hop + NYC hop) over mapped concept pairs...")
CITY_MIN = 0.45
mapped_list = sorted(mapped_concepts)
mapped_set = set(mapped_list)


def cthemes(c):
    t = set()
    for m in concept_to_measures[c]:
        t.update(s for s in str(measures[m]["themes"]).split(";") if s)
    return t


n_pair_direct = 0
mixed = []
for a in mapped_list:
    na_mapped = [x for x in adj[a] if x in mapped_set]
    for b in mapped_list:
        if b == a:
            continue
        if b in adj[a]:
            n_pair_direct += 1
            continue
        for x in na_mapped:
            if x == b or x == a:
                continue
            fa, sta = adj[a][x]
            if fa < 2 or sta < 2:
                continue  # graph hop must be a real, documented edge
            fb = adj[x].get(b)          # x is mapped -> x is an adjacency key
            if fb is not None and fb[0] >= 2:
                continue  # the "city hop" already has real SPG evidence -> not mixed
            r = rho_cc(x, b)
            if r is None or abs(r[0]) < CITY_MIN:
                continue
            if cthemes(x) & cthemes(b):
                continue  # same indicator family -> city hop is measure redundancy
            mixed.append({"a": a, "x": x, "b": b,
                          "f": fa, "st": sta,
                          "r_hop": r[0], "r_hop_m": (r[1], r[2]),
                          "graph_fb": (fb[0] if fb else 0),
                          "r_ab": rho_cc(a, b)})
# keep the strongest chain per ordered (a, b) assembled pair
best_by_pair = {}
for m in mixed:
    k = (m["a"], m["b"])
    cur = best_by_pair.get(k)
    if cur is None or (abs(m["r_hop"]), strength(m["f"], m["st"])) > \
            (abs(cur["r_hop"]), strength(cur["f"], cur["st"])):
        best_by_pair[k] = m
mixed = sorted(best_by_pair.values(),
               key=lambda m: (-abs(m["r_hop"]), -strength(m["f"], m["st"])))
MEDIATED_TOP = 30
mediated_top = mixed[:MEDIATED_TOP]
report["counts"]["assembled_pairs_no_direct_edge"] = len(best_by_pair)
report["counts"]["mixed_chains_found"] = len(mixed)
report["counts"]["mediated_shipped"] = len(mediated_top)
log(f"  assembled pairs (no direct SPG edge): {len(best_by_pair)}; "
    f"mixed chains: {len(mixed)}; shipping top {len(mediated_top)}")
x_hops_city_only = sum(1 for m in mediated_top if m["graph_fb"] == 0)
log(f"  shipped chains whose city hop has NO spg edge at all: {x_hops_city_only}")

# ---------------------------------------------------------------- associations
log("Associations pass (edge effect sizes + pubmed samples + direction stats)...")
subgraph_pairs = {frozenset((s, t)) for s, nbrs in cadj.items() for t in nbrs}
mediated_edges = {frozenset((m["a"], m["x"])) for m in mediated_top}
mediated_edges |= {frozenset((m["x"], m["b"])) for m in mediated_top}
# curated flagship chain (green-space x emergency-care) SPG hops
FLAGSHIP_SPG = [("wpUeTjUbAc", "Gl-I4wBZ5r"), ("Gl-I4wBZ5r", "nS9fqJ01TW")]
mediated_edges |= {frozenset(p) for p in FLAGSHIP_SPG}
# every ego edge the popup graph draws: the row-detail view colors these by
# effect direction and prints the median effect, so they need aggregates too
ego_edges = {frozenset((cid, n))
             for cid in endpoint_concepts
             for n in list(adj[cid])[:K_EGO]}
agg = {fs: {"vals": [], "pms": set(), "types": Counter(), "vsamples": []}
       for fs in subgraph_pairs | mediated_edges | ego_edges}
conf_pms = {fs: set() for fs in pair_fs}
conf_stats = {fs: [] for fs in pair_fs}   # (statistic_value, type) for direction
direct_assoc = 0
use = ["pubmed_id", "system_statistic_type", "statistic_value",
       "variable_1_concept_id", "variable_2_concept_id",
       "variable_1_name", "variable_2_name"]
for ch in pd.read_csv(DV / "system-public-graph-v1-associations.csv",
                      usecols=use, chunksize=400_000):
    v1 = ch["variable_1_concept_id"].to_numpy()
    v2 = ch["variable_2_concept_id"].to_numpy()
    n1 = ch["variable_1_name"].fillna("").to_numpy()
    n2 = ch["variable_2_name"].fillna("").to_numpy()
    for s, t, pm, st, val, nm1, nm2 in zip(
            v1, v2,
            ch["pubmed_id"].to_numpy(),
            ch["system_statistic_type"].to_numpy(),
            ch["statistic_value"].astype(float).to_numpy(),
            n1, n2):
        fs = frozenset((s, t)) if s != t else None
        if fs is None:
            continue
        if fs in bridge_cross_fs:
            direct_assoc += 1
        if fs in conf_pms:
            # direction stats collect every signable effect — pmid or not
            if len(conf_stats[fs]) < 600:
                conf_stats[fs].append((val, st))
            if len(conf_pms[fs]) < 12:
                pm_s = str(pm).strip()
                if pm_s.endswith(".0"):
                    pm_s = pm_s[:-2]
                if pm_s not in ("", "nan", "None"):
                    conf_pms[fs].add(pm_s)
        pm_s = str(pm).strip()
        if pm_s.endswith(".0"):
            pm_s = pm_s[:-2]
        if pm_s in ("", "nan", "None"):
            continue
        a = agg.get(fs)
        if a is not None and len(a["vals"]) < 5000:
            a["vals"].append(val)
            a["types"][st] += 1
            if len(a["pms"]) < 12:
                a["pms"].add(pm_s)
            if len(a["vsamples"]) < 2:
                nm1s, nm2s = str(nm1).strip(), str(nm2).strip()
                pair_s = f"{nm1s} vs {nm2s}"
                if (nm1s and nm2s and "nan" not in pair_s.lower()
                        and pair_s not in a["vsamples"]):
                    a["vsamples"].append(pair_s[:120])

report["assertions"]["bridge_direct_associations"] = direct_assoc
report["counts"]["bridge_direct_associations"] = direct_assoc
assert direct_assoc == 0, "bridge premise broken: direct associations exist"
log(f"  direct bridge associations: {direct_assoc}")

# ---------------------------------------------------------------- bundle
log("Assembling bundle...")
# shared connectors per confirmed pair (before building the node table: they must ship)
pair_shared = {}
for r in cross.itertuples():
    sh = (set(adj[r.c1]) & set(adj[r.c2])) - {r.c1, r.c2}
    pair_shared[frozenset((r.c1, r.c2))] = sorted(
        sh, key=lambda x: (-strength(*adj[r.c1].get(x, (0, 0))), x))

used_concepts = set(endpoint_concepts) | set(bridge_endpoints) | mapped_concepts
for e in bridge_results:
    for c in e["one"]:
        used_concepts.add(c["id"])
    for c in e["two"]:
        used_concepts.update((c["x"], c["y"], c["ea"][0], c["eb"][0]))
for cid in endpoint_concepts:
    used_concepts.update(list(adj[cid])[:K_EGO])
for sh in pair_shared.values():
    used_concepts.update(sh[:MAX_SHARED])
for m in mediated_top:
    used_concepts.add(m["x"])

concepts = {}
for cid in sorted(used_concepts):
    lab, d = concept_meta.get(cid, ("", ""))
    concepts[cid] = {"l": lab, "d": d, "dm": domains.get(cid, ""),
                     "nyc": cid in mapped_concepts}

egos = {}
ego_stats = {}   # frozenset((endpoint, nbr)) -> association aggregate, for edge chips


def _edge_agg(fs):
    a = agg.get(fs)
    if not a or not a["vals"]:
        return {"na": None, "med": None, "et": None}
    return {"na": int(len(a["vals"])),
            "med": float(np.median(a["vals"])),
            "et": (a["types"].most_common(1)[0][0] if a["types"] else None)}


for cid in endpoint_concepts:
    nbr_items = sorted(adj[cid].items(),
                       key=lambda kv: (-strength(*kv[1]), kv[0]))[:K_EGO]
    egos[cid] = {
        "deg": len(adj[cid]),
        "nbrs": [{"id": n, "f": f, "st": st, "nyc": n in mapped_concepts,
                  **_edge_agg(frozenset((cid, n)))}
                 for n, (f, st) in nbr_items],
    }

def expected_direction(fs):
    """Expected sign of the city correlation from the SPG effects.
    Ratio types: value > 1 = positive dependence, < 1 = negative (protective).
    Correlation types: sign of the value. Mean differences/coefficients excluded
    (sign depends on unstated variable coding). Majority vote, >=3 signs and
    >=60% share required, else None (ambiguous)."""
    signs = []
    for val, st in conf_stats.get(fs, ()):
        if st in RATIO_TYPES and val > 0:
            signs.append(1 if val > 1 else -1)
        elif st in CORR_TYPES:
            signs.append(1 if val > 0 else -1)
    if len(signs) < 3:
        return None, len(signs)
    pos = sum(1 for s in signs if s > 0)
    if max(pos, len(signs) - pos) / len(signs) < 0.6:
        return None, len(signs)
    return (1 if pos >= len(signs) - pos else -1), len(signs)


confirmations = []
for r in cross.itertuples():
    fs = frozenset((r.c1, r.c2))
    rel = pair_rel.get(fs)
    f, st = rel if rel else (0, 0)
    m1 = sorted(concept_to_measures[r.c1])
    m2 = sorted(concept_to_measures[r.c2])
    sh_sorted = pair_shared[fs]
    dexp, n_signs = expected_direction(fs)
    rho = float(r.city_spearman_uhf42) if pd.notna(r.city_spearman_uhf42) else None
    if rho is None:
        agree = "no_rho"
    elif abs(rho) < 0.1:
        agree = "flat"
    elif dexp is None:
        agree = "ambiguous"
    else:
        agree = "same" if (rho > 0) == (dexp > 0) else "opposite"
    chk = None
    if isinstance(r.city_check_measures, str) and r.city_check_measures:
        parts = r.city_check_measures.split(" x ")
        chk = [p.strip() for p in parts] if len(parts) == 2 else None
    confirmations.append({
        "c1": r.c1, "c2": r.c2,
        "na": int(r.n_assocs), "np": int(r.n_pubmeds),
        "med": float(r.median_effect) if pd.notna(r.median_effect) else None,
        "et": [t for t in str(r.effect_types).split("; ") if t and t != "nan"][:5],
        "rho": rho,
        "nd": int(r.city_n_districts) if pd.notna(r.city_n_districts) else None,
        "dir": dexp, "nsigns": n_signs, "agree": agree,
        "chk": chk, "mod": bool(r.city_check_modeled),
        "note": r.note if isinstance(r.note, str) else "",
        "rel": {"f": int(f), "st": int(st)} if rel else None,
        "pms": sorted(conf_pms.get(fs, set())),
        "m1": m1, "m2": m2,
        "sh": sh_sorted[:MAX_SHARED], "nsh": len(sh),
    })

# ------------------------------------------------- per-connection narratives
def clab(cid):
    return concept_meta.get(cid, (cid, ""))[0] or cid


def cdesc(cid, cap=110):
    d = concept_meta.get(cid, ("", ""))[1]
    if not d:
        return None
    d = d.strip().rstrip(".")
    return d[: cap - 1] + "…" if len(d) > cap else d


STAT_WORDS = {
    "odds_ratio": "odds ratio",
    "adjusted_odds_ratio": "adjusted odds ratio",
    "hazard_ratio": "hazard ratio",
    "adjusted_hazard_ratio": "adjusted hazard ratio",
    "risk_ratio": "risk ratio",
    "relative_risk": "relative risk",
    "rate_ratio": "rate ratio",
    "incident_rate_ratio": "incidence rate ratio",
    "pearson_r": "correlation",
    "spearman_r": "correlation",
    "correlation_coefficient": "correlation",
    "coefficient": "regression slope",
}


def fmt_effect(med, et):
    if med is None or et is None:
        return None
    word = STAT_WORDS.get(et, et.replace("_", " "))
    return f"{word} ≈ {med:.2f}"


def effect_dir_word(med, et):
    if med is None or et is None:
        return None
    additive = et in ("pearson_r", "spearman_r", "correlation_coefficient",
                      "coefficient") or et.startswith("mean_difference")
    if additive:
        return "rise together" if med > 0 else "move in opposite directions"
    return "rise together" if med > 1 else "move in opposite directions"


def compose_story_one(rank, c, A_lab, B_lab, rho, m1_lab, m2_lab):
    """Plain-language story for a one-step connector, with [n] citation
    markers resolved against the returned pmid list."""
    xlab = clab(c["id"])
    edges = sorted(
        [(d, "A") for d in c["ea"]] + [(d, "B") for d in c["eb"]],
        key=lambda t: -t[0]["f"])
    best = edges[0][0]
    pms = []
    for d, _ in edges:
        for p in d.get("pms", []):
            if p not in pms:
                pms.append(p)

    def cite(d):
        for p in d.get("pms", []):
            if p in pms:
                return f" [{pms.index(p) + 1}]"
        return ""

    s = [f"{xlab} is the hinge."]
    xdesc = cdesc(c["id"])
    if xdesc:
        s.append(f'It stands for "{xdesc.lower()}" — a concept that published '
                 "studies keep returning to on both sides.")
    eff = fmt_effect(best["med"], best["et"])
    dword = effect_dir_word(best["med"], best["et"])
    tail = ""
    if eff:
        tail = f", typical {eff}"
    s.append(f"The stronger side carries {best['f']} findings from "
             f"{best['st']} studies{tail}{cite(best)}.")
    if dword:
        s.append(f"In those studies, the two ideas {dword}.")
    if best.get("vars"):
        s.append(f'One typical pairing in the papers: "{best["vars"][0]}".')
    if rho is not None:
        together = "rise and fall together" if rho >= 0 else "move in opposite directions"
        s.append(f"City-side, {m1_lab} and {m2_lab} {together} across the 42 "
                 f"health districts (ρ {rho:+.2f}).")
    s.append("These are links in published studies, not proof of cause — and "
             "the numbers come from different kinds of studies, so compare "
             "directions, not sizes.")
    text = " ".join(s)
    return text[0].upper() + text[1:], pms


def compose_story_two(c, A_lab, B_lab, rho):
    xlab, ylab = clab(c["x"]), clab(c["y"])
    alab = clab(c["ea"]["a"])
    blab = clab(c["eb"]["b"])
    pms = []
    for d in (c["ea"], c["xy"], c["eb"]):
        for p in d.get("pms", []):
            if p not in pms:
                pms.append(p)

    def cite(d):
        for p in d.get("pms", []):
            if p in pms:
                return f" [{pms.index(p) + 1}]"
        return ""

    xdesc = cdesc(c["x"])
    ydesc = cdesc(c["y"])
    s = [f"The strongest chain between {A_lab} and {B_lab} runs {alab} → "
         f"{xlab} → {ylab} → {blab}."]
    if xdesc or ydesc:
        parts = []
        if xdesc:
            parts.append(f'"{xdesc.lower()}"')
        if ydesc:
            parts.append(f'"{ydesc.lower()}"')
        s.append(f"The two stepping stones are {parts[0]}" +
                 (f" and {parts[1]}" if len(parts) > 1 else "") + ".")
    legs = [
        (alab, xlab, c["ea"], cite(c["ea"])),
        (xlab, ylab, c["xy"], cite(c["xy"])),
        (ylab, blab, c["eb"], cite(c["eb"])),
    ]
    leg_lines = []
    for from_lab, to_lab, d, ct in legs:
        eff = fmt_effect(d["med"], d["et"])
        base = f"{from_lab} to {to_lab}: {d['f']} findings"
        if eff:
            dword = effect_dir_word(d["med"], d["et"])
            leg_lines.append(f"{base} ({eff} — they {dword}){ct}")
        else:
            leg_lines.append(f"{base}, no numbers in the studies{ct}")
    s.append("; ".join(leg_lines) + ".")
    if rho is not None:
        together = "rise and fall together" if rho >= 0 else "move in opposite directions"
        s.append(f"City-side, the measures {together} across the 42 health "
                 f"districts (ρ {rho:+.2f}).")
    s.append("Each step is thin, and thin steps compound — but the chain "
             "exists, which the direct edge cannot say. A chain is a "
             "hypothesis: it tells you which study to run next.")
    text = " ".join(s)
    return text[0].upper() + text[1:], pms

bridge_bundle = []
for e in bridge_results:
    rows = []
    for r in e["rows"]:
        rows.append({"m1": r.m1n, "m2": r.m2n, "rho": float(r.city_spearman_uhf42),
                     "yr1": measures[r.m1n]["yr"], "yr2": measures[r.m2n]["yr"],
                     "l1": measures[r.m1n]["l"], "l2": measures[r.m2n]["l"]})

    def assoc_pack(u, v):
        a = agg.get(frozenset((u, v)))
        if a and a["vals"]:
            return {"na": int(len(a["vals"])),
                    "med": (float(np.median(a["vals"])) if a["vals"] else None),
                    "et": (a["types"].most_common(1)[0][0] if a["types"] else None),
                    "pms": sorted(a["pms"])[:4],
                    "vars": list(a["vsamples"])[:2]}
        return {"na": None, "med": None, "et": None, "pms": [], "vars": []}

    one = [{"id": c["id"],
            "ea": [{**d, **assoc_pack(d["a"], c["id"])} for d in c["ea"]],
            "eb": [{**d, **assoc_pack(d["b"], c["id"])} for d in c["eb"]]}
           for c in e["one"]]
    two = []
    for c in e["two"]:
        a, fa, sta = c["ea"]
        b, fb, stb = c["eb"]
        fxy, stxy = c["xy"]
        two.append({"x": c["x"], "y": c["y"], "s": round(c["s"], 3),
                    "ea": {"a": a, "f": fa, "st": sta, **assoc_pack(a, c["x"])},
                    "xy": {"f": fxy, "st": stxy, **assoc_pack(c["x"], c["y"])},
                    "eb": {"b": b, "f": fb, "st": stb, **assoc_pack(c["y"], b)}})

    A_lab = clab(e["A"][0])
    B_lab = clab(e["B"][0])
    rho0 = rows[0]["rho"] if rows else None
    for rank, packed in enumerate(one):
        story, pms = compose_story_one(rank, packed, A_lab, B_lab,
                                       rho0 if rho0 is not None else 0.0,
                                       rows[0]["l1"].split(",")[0] if rows else "",
                                       rows[0]["l2"].split(",")[0] if rows else "")
        best_f = max(d["f"] for d in packed["ea"] + packed["eb"])
        packed["head"] = (f"h: {clab(packed['id'])} bridges them directly · "
                          f"{best_f} findings")
        packed["story"] = story
        packed["pms"] = pms
    for packed in two:
        story, pms = compose_story_two(packed, A_lab, B_lab,
                                       rho0 if rho0 is not None else 0.0)
        packed["head"] = (f"h: {clab(packed['x'])} → {clab(packed['y'])} "
                          f"chains them · strength {packed['s']:.2f}")
        packed["story"] = story
        packed["pms"] = pms

    la = clab(e["A"][0]) + (f" +{len(e['A']) - 1}" if len(e["A"]) > 1 else "")
    lb = clab(e["B"][0]) + (f" +{len(e['B']) - 1}" if len(e["B"]) > 1 else "")
    parts = [f"No study directly links {la} to {lb}."]
    if e["n_one"]:
        shown = f" — top {len(one)} shown" if e["n_one"] > len(one) else ""
        parts.append(f"{e['n_one']} concepts bridge them in one step{shown}.")
    else:
        parts.append("Their literatures don't touch within two steps.")
    if e["n_two"]:
        shown = f" — top {len(two)} shown" if e["n_two"] > len(two) else ""
        parts.append(f"{e['n_two']} chains connect them in two steps{shown}.")
    rho = rows[0]["rho"] if rows else None
    if rho is not None:
        word = "rise and fall together" if rho >= 0 else "move in opposite directions"
        parts.append(f"Across 42 city health districts the measures {word} "
                     f"(ρ={rho:+.2f}).")
    cap = " ".join(parts)
    assert len(cap) <= 250, f"caption too long ({len(cap)}): {cap}"
    bridge_bundle.append({"A": e["A"], "B": e["B"], "rows": rows,
                          "nsh": e["n_shared"], "n_one": e["n_one"],
                          "n_two": e["n_two"], "one": one, "two": two,
                          "cap": cap})

# contested static panels
vintage_ids = []
for s in spot.measure1.tolist() + spot.measure2.tolist():
    vintage_ids.append("ehdp:" + s)
for e in bridge_bundle:
    for row in e["rows"]:
        vintage_ids += [row["m1"], row["m2"]]
vintage_ids += ["trees:acer", "complaints:NO HEAT",
                "deaths:diseases of heart", "deaths:diabetes mellitus",
                "ehdp:measure:535", "ehdp:measure:537", "ehdp:measure:690"]
vintage = []
seen_v = set()
for mid in vintage_ids:
    if mid in seen_v or mid not in measures:
        continue
    seen_v.add(mid)
    vintage.append({"id": mid, **{k: measures[mid][k] for k in
                                  ("l", "coll", "yr", "mod")}})

modeled_confirm = cross[cross.city_check_modeled]
bundle_measures = {m: {k: measures[m][k] for k in ("l", "mt", "yr", "coll", "themes", "mod")}
                   for m in sorted({m for c in confirmations for m in c["m1"] + c["m2"]}
                                   | set(vintage_ids))}
report["counts"]["agree_same"] = sum(1 for c in confirmations if c["agree"] == "same")
report["counts"]["agree_opposite"] = sum(1 for c in confirmations if c["agree"] == "opposite")
report["counts"]["agree_flat"] = sum(1 for c in confirmations if c["agree"] == "flat")
report["counts"]["agree_ambiguous"] = sum(1 for c in confirmations if c["agree"] == "ambiguous")
report["counts"]["bundle_concepts"] = len(concepts)
report["counts"]["bundle_measures"] = len(bundle_measures)
manifest = json.loads((DV / "MANIFEST.json").read_text())
concepts_sha = next(f["checksums"]["sha256"][:12] for f in manifest["files"]
                    if "concepts" in f["filename"])
citations = (f"SPG v1 (Dataverse deposit; concepts sha256:{concepts_sha}, relationships, "
             f"associations, studies) · NYC Open Data on Underlay v1.0.0 "
             f"(environment-health, leading-causes-of-death, heat-complaints, street-trees)")
mediated_bundle = []
for m in mediated_top:
    a_agg = agg.get(frozenset((m["a"], m["x"])))
    b_agg = agg.get(frozenset((m["x"], m["b"])))
    mediated_bundle.append({
        "a": m["a"], "x": m["x"], "b": m["b"],
        "nodes": [m["a"], m["x"], m["b"]],
        "edges": [
            {"kind": "spg", "f": m["f"], "st": m["st"],
             "na": (int(len(a_agg["vals"])) if a_agg and a_agg["vals"] else None),
             "med": (float(np.median(a_agg["vals"])) if a_agg and a_agg["vals"] else None),
             "et": (a_agg["types"].most_common(1)[0][0] if a_agg and a_agg["types"] else None)},
            {"kind": "nyc", "rho": round(m["r_hop"], 3), "graph_f": m["graph_fb"],
             "na": (int(len(b_agg["vals"])) if b_agg and b_agg["vals"] else 0)},
        ],
        "r_hop": round(abs(m["r_hop"]), 3),
        "r_hop_measures": [m["r_hop_m"][0], m["r_hop_m"][1]],
        "r_ab": (round(m["r_ab"][0], 3) if m["r_ab"] else None),
        "graph_fb": m["graph_fb"],
        "l1": concept_meta.get(m["a"], ("?",))[0],
        "l2": concept_meta.get(m["b"], ("?",))[0],
        "lx": concept_meta.get(m["x"], ("?",))[0],
    })
# Curated flagship: the original green-space x emergency-care chain, assembled
# explicitly because its links do not all clear the automated per-pair gates
# (the green->heat link has no per-concept-pair SPG edge, and the city evidence
# runs through surface temperature while the SPG route runs through extreme heat).
med_eh_hosp = agg.get(frozenset(("wpUeTjUbAc", "Gl-I4wBZ5r")))
med_hosp_ed = agg.get(frozenset(("Gl-I4wBZ5r", "nS9fqJ01TW")))
flagship = {
    "curated": True,
    "nodes": ["RF7tCwCaa5", "sSuplgYnDQ", "wpUeTjUbAc", "Gl-I4wBZ5r", "nS9fqJ01TW"],
    "edges": [
        {"kind": "nyc", "rho": -0.396, "graph_f": 0, "na": 0,
         "measures": ["ehdp:measure:690", "ehdp:measure:688"]},
        {"kind": "mech"},
        {"kind": "spg", "f": 6, "st": 4,
         "na": (int(len(med_eh_hosp["vals"])) if med_eh_hosp and med_eh_hosp["vals"] else 6),
         "med": (float(np.median(med_eh_hosp["vals"])) if med_eh_hosp and med_eh_hosp["vals"] else None),
         "et": (med_eh_hosp["types"].most_common(1)[0][0] if med_eh_hosp and med_eh_hosp["types"] else None)},
        {"kind": "spg", "f": 4, "st": 4,
         "na": (int(len(med_hosp_ed["vals"])) if med_hosp_ed and med_hosp_ed["vals"] else 4),
         "med": (float(np.median(med_hosp_ed["vals"])) if med_hosp_ed and med_hosp_ed["vals"] else None),
         "et": (med_hosp_ed["types"].most_common(1)[0][0] if med_hosp_ed and med_hosp_ed["types"] else None)},
    ],
    "r_ab": 0.024,
    "l1": concept_meta.get("RF7tCwCaa5", ("vegetation cover",))[0],
    "lx": concept_meta.get("sSuplgYnDQ", ("surface temperature",))[0],
    "l2": concept_meta.get("nS9fqJ01TW", ("emergency department",))[0],
    "note": ("Curated flagship — the original pattern. Direct link: 0 SPG associations, "
             "city ρ=0.02. Hop 1 is carried by NYC (vegetation cover cools surfaces); "
             "hop 2 is the physical mechanism (hot surfaces → heat exposure), assumed, "
             "not separately evidenced in either dataset here; hops 3-4 are documented "
             "SPG edges (heat → hospitalization → emergency department)."),
}
mediated_bundle.insert(0, flagship)
report["counts"]["mediated_shipped_final"] = len(mediated_bundle)

bundle = {
    "meta": {"built": "see build_report.json", "citations": citations,
             **report["counts"]},
    "concepts": concepts,
    "measures": bundle_measures,
    "confirmations": confirmations,
    "egos": egos,
    "bridges": bridge_bundle,
    "mediated": mediated_bundle,
    "contested": {
        "cards": [
            {"t": "Green space × emergency care",
             "b": "SPG holds 0 associations between green-space and emergency-care concepts. "
                  "The naive city check agrees (ρ≈0.02 cover→heat ED) — but vegetation cover "
                  "clearly depresses surface temperature (ρ=−0.396), and the graph itself "
                  "supplies 70 heat×emergency-care associations. The chain cover → cooler "
                  "surfaces → fewer heat outcomes is supported piecewise by the two datasets "
                  "together; the direct edge is untested in the literature — the research target."},
            {"t": "Vintage misalignment",
             "b": "Street-tree census is 2015; vegetation cover 2010–2017; surface temperature "
                  "a single day (2018); heat outcomes 2000–2022; 311 complaints 2024–2026. "
                  "Cross-dataset claims must state which years each leg rests on — every "
                  "concept-map row carries year ranges."},
            {"t": "Modeled vs observed",
             "b": "EHDP 'burden' measures (PM2.5 asthma ED visits, deaths from PM2.5/ozone, "
                  "heat vulnerability index) are modeled attributions, not observations. City "
                  "checks that use them reproduce the model, not the city — flagged ρ⚠ in the "
                  "confirmations table."},
            {"t": "Counts vs rates",
             "b": "The same EHDP indicator appears as Number, Percent, rate and age-adjusted "
                  "rate; SPG associations mix OR/RR/r with 89% null study_type. Compare "
                  "directions only, never magnitudes across that boundary."},
            {"t": "Construct ≠ operationalization",
             "b": "'Heat ED visits' counts heat-stress visits during warm months (ICD-coded); "
                  "SPG heat concepts span heat wave, extreme heat, heat stroke, heat illness. "
                  "Matches are typed broader-narrower/related-component so claims inherit the "
                  "right caveats."},
        ],
        "spot": spot.to_dict(orient="records"),
        "vintage": vintage,
        "modeled": {"conf_modeled": len(modeled_confirm),
                    "conf_observed": int((cross.city_spearman_uhf42.notna()
                                          & ~cross.city_check_modeled).sum()),
                    "conf_no_rho": int(cross.city_spearman_uhf42.isna().sum())},
    },
}

# resolve all shipped ids
for c in bundle["confirmations"]:
    for cid in [c["c1"], c["c2"]] + c["sh"] + c["m1"] + c["m2"]:
        assert cid in concepts or cid in measures, f"unresolved id {cid}"
    for cid in c["sh"]:
        assert cid in concepts, f"shared node missing from concepts: {cid}"
for e in bundle["bridges"]:
    for c in e["one"]:
        assert c["id"] in concepts, f"connector missing: {c['id']}"
    for c in e["two"]:
        for nid in (c["x"], c["y"], c["ea"]["a"], c["eb"]["b"]):
            assert nid in concepts, f"corridor node missing: {nid}"
for m in bundle["mediated"]:
    for nid in m["nodes"]:
        assert nid in concepts, f"mediated node missing: {nid}"
    if m.get("curated"):
        continue
    assert m["b"] not in adj[m["a"]], "assembled link exists in SPG — premise broken"
    fb = adj[m["x"]].get(m["b"])
    assert fb is None or fb[0] < 2, "city hop has substantial SPG evidence — not mixed"
    assert m["edges"][0]["kind"] == "spg" and m["edges"][1]["kind"] == "nyc"

# ---------------------------------------------------------------- write bundle
log("Writing bundle...")
(DOUT / "bundle.json").write_text(json.dumps(bundle, indent=1))
web_data = BASE / "web" / "data"
web_data.mkdir(parents=True, exist_ok=True)
(web_data / "bundle.json").write_text(json.dumps(bundle, indent=1))
(DOUT / "build_report.json").write_text(json.dumps(report, indent=2))
log(f"Done: dashboard/out/bundle.json + web/data/bundle.json "
    f"({report['counts']['bundle_concepts']} concepts)")
