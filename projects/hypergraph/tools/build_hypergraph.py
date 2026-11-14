"""Build viz/data/hypergraph.js and .json for viz/hypergraph.html.

Usage:
  ~/.venvs/nyc-concordance/bin/python tools/build_hypergraph.py

The page treats a link between two variables as an object with its own
contents: the findings the System Public Graph holds for it, what this project
read in their abstracts, and the city test registered on it. This script
assembles those contents. Every number comes from the sysgraph cache
(data/cache/sysgraph/), the claims (claims/registered, claims/outcomes) or
data/derived/. Nothing is typed in here except (a) which edges are shown and in
which group, (b) which registered claim tests which edge, and (c) one set of
corrected values for temperature and homicide, copied from the registration of
heat-shootings, which records the abstract values beside the graph's.

Sources of each field
  finding value, interval, p, PMID, variables   graph association record
  population, DOI, study_type                  graph study record
  first author, year, journal                  PubMed esummary (bibliographic only)
  design                                       graph study_type where present; otherwise
                                               this project's reading of the abstract
                                               (all_boats verification.csv, retimed_week
                                               abstract_checks.json, levers, single-paper
                                               summaries in registrations); otherwise
                                               "not recorded by the graph"
  record correct / qualifier lost / wrong      the same reading files

Graph-derived data are CC BY-NC 4.0 (System Public Graph, Dataverse v2.1,
doi:10.7910/DVN/7V6JDO).
"""
from __future__ import annotations

import csv
import json
import math
import re
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from concord import sysgraph as S  # noqa: E402

OUT = ROOT / "viz" / "data"
DER = ROOT / "data" / "derived"
T = "4FaXcuNJRt"  # temperature

# --------------------------------------------------------------------------- edge list
# (group, relationship id, label a, label b). Labels are the graph's concept labels.
GROUPS = [
    ("heat", "Heat and temperature", "Edges that share temperature or heat as one end. Shootings, emergency visits, sleep, walking and mortality are the ends this project tested."),
    ("asthma", "Asthma", "Edges that share asthma as one end. These are the best-populated edges behind a claim."),
    ("activity", "Walking, activity and weight", "The edges read for the commuting and obesity claims."),
    ("commute", "Commuting and working at home", "Edges found by variable name, because the graph has no concept for commuting or telework."),
    ("modify", "Heat, modified by a medicine or a condition", "Each row is a relation among three variables: heat, a medicine or condition, and heat illness or death. Read from abstracts in docs/heat_drugs.md. A dashed mark is a study that the graph does not hold."),
    ("levers", "City interventions", "Edges found by variable name for an intervention and an outcome domain (docs/all_boats.md)."),
    ("other", "Noise and construction", "Other edges cited in a registration."),
]
CONCEPT_EDGES = [
    ("heat", f"{T}|YZku29igbl", "temperature", "homicide"),
    ("heat", f"{T}|14UOQBVakG", "temperature", "firearm"),
    ("heat", f"{T}|rULjCt1BqH", "temperature", "injury"),
    ("heat", f"{T}|QmevDxhzPZ", "temperature", "intimate partner violence"),
    ("heat", f"{T}|TLeQZQ_leT", "temperature", "suicide"),
    ("heat", f"{T}|-0HrxUPkp2", "temperature", "mental disorder"),
    ("heat", f"{T}|N5xiUDm5Jr", "temperature", "alcohol consumption"),
    ("heat", f"{T}|nDIFXeS4Xr", "temperature", "sleep"),
    ("heat", f"{T}|aeY3nW1sT_", "temperature", "sleep quality"),
    ("heat", "k4RCuWBkJ3|y83mBL5cYb", "sleep duration", "aggression"),
    ("heat", f"{T}|_2dhcsFISl", "temperature", "walking"),
    ("heat", f"{T}|dPeET-pgVN", "temperature", "physical activity"),
    ("heat", f"{T}|9xkOyRJxD9", "temperature", "physical exercise"),
    ("heat", f"{T}|gILy0ZWbmD", "temperature", "emergency medical services"),
    ("heat", "wpUeTjUbAc|PtQBvGm5CM", "extreme heat", "heat illness"),
    ("heat", f"PtQBvGm5CM|{T}", "heat illness", "temperature"),
    ("heat", f"{T}|rYCo7LTyzN", "temperature", "heat stroke"),
    ("heat", "wpUeTjUbAc|QPxlNKv3zV", "extreme heat", "mortality rate"),
    ("heat", f"{T}|QPxlNKv3zV", "temperature", "mortality rate"),
    ("heat", f"{T}|oEWjV89s3H", "temperature", "all-cause mortality"),
    ("heat", f"{T}|DZBybMvxDI", "temperature", "COVID-19"),
    ("heat", "sSuplgYnDQ|mUxSLRMwIy", "surface temperature", "air temperature"),
    ("heat", "hsryqxdFzE|PCdVJWVRyS", "vegetation index (NDVI)", "temperature (thermodynamic)"),
    ("heat", "WLNXo1tGFr|sSuplgYnDQ", "population density", "surface temperature"),
    ("asthma", f"{T}|EAshH_Ko3h", "temperature", "asthma"),
    ("asthma", "DC_F0GO0WQ|EAshH_Ko3h", "nitrogen dioxide", "asthma"),
    ("asthma", "gX6h_gZWHH|EAshH_Ko3h", "particulates", "asthma"),
    ("asthma", "oG8Da1gCE9|EAshH_Ko3h", "traffic-related pollution", "asthma"),
    ("asthma", "P6IzhScRdx|EAshH_Ko3h", "air pollution", "asthma"),
    ("activity", "dPeET-pgVN|cj7G775u_Q", "physical activity", "obesity"),
    ("activity", "_2dhcsFISl|cj7G775u_Q", "walking", "obesity"),
    ("activity", "_2dhcsFISl|dPeET-pgVN", "walking", "physical activity"),
    ("activity", "6DTj2ennMm|_2dhcsFISl", "park", "walking"),
    ("activity", "6DTj2ennMm|cj7G775u_Q", "park", "obesity"),
    ("activity", "MA8xf-tUNR|_2dhcsFISl", "built environment", "walking"),
    ("activity", "V7ImOTxbql|_2dhcsFISl", "crime", "walking"),
    ("activity", "_zLVUxvG7F|cj7G775u_Q", "socioeconomic status", "obesity"),
    ("other", "cEPG6i4Yq1|fo-h4u_aJp", "traffic noise", "arterial hypertension"),
    ("other", "cEPG6i4Yq1|nDIFXeS4Xr", "traffic noise", "sleep"),
    ("other", "cEPG6i4Yq1|XW9F7OPopQ", "traffic noise", "stroke"),
    ("other", "B0QiEej1E1|COEFxSZVXO", "population growth", "construction"),
]
# Variable-level edges from the re-timed week search (data/derived/graph/retimed_week).
COMMUTE_OUTCOMES = ["sleep", "mental health", "musculoskeletal pain", "fatigue and work functioning", "sitting and inactivity"]
# Variable-level edges from the all_boats search: (intervention, domain, label a, label b).
LEVER_EDGES = [
    ("air_conditioning", "mortality", "air conditioning", "mortality"),
    ("vacant_lot_greening", "crime_safety", "vacant lot greening", "crime and safety"),
    ("traffic_calming", "crime_safety", "traffic calming", "crime and safety (injury)"),
    ("housing_repair", "physical_health", "housing repair and insulation", "physical health"),
    ("street_trees", "mental_health", "street trees and canopy", "mental health"),
    ("street_trees", "housing_cost", "street trees and canopy", "housing cost"),
    ("supermarkets", "physical_health", "supermarkets", "physical health"),
]
# Heat by medicine or condition: nodes of viz/data/heat_drugs.js shown as edges (read only).
MODIFIERS = ["antipsychotic", "anticholinergic", "diuretic", "insulin", "lithium", "psychotropic", "anymed", "schizophrenia", "mental", "diabetes", "kidney"]
# Which registered claim tests which edge (the estimate is drawn on the edge).
EDGE_TESTS = {
    f"{T}|YZku29igbl": ["heat-shootings", "transfer-chicago-heat-shootings"],
    f"{T}|14UOQBVakG": ["heat-shootings"],
    f"{T}|rULjCt1BqH": ["bridge-heat-shootings-ems"],
    f"{T}|nDIFXeS4Xr": ["heat-night-minimum"],
    "k4RCuWBkJ3|y83mBL5cYb": ["heat-night-minimum"],
    f"{T}|_2dhcsFISl": ["heat-mech-outdoors"],
    f"{T}|N5xiUDm5Jr": ["heat-mech-intox"],
    "wpUeTjUbAc|PtQBvGm5CM": ["heat-ed-syndromic"],
    f"{T}|DZBybMvxDI": ["split-temp-covid-growth"],
    f"{T}|EAshH_Ko3h": ["split-temp-asthma-ems"],
    "sSuplgYnDQ|mUxSLRMwIy": ["heat-trees-airtemp-hyperlocal"],
    "hsryqxdFzE|PCdVJWVRyS": ["heat-trees-surftemp", "heat-trees-canopy-within-nta"],
    "WLNXo1tGFr|sSuplgYnDQ": ["graph-confounders-trees-surftemp"],
    "DC_F0GO0WQ|EAshH_Ko3h": ["mob-asthma-pollution"],
    "gX6h_gZWHH|EAshH_Ko3h": ["mob-asthma-pollution"],
    "oG8Da1gCE9|EAshH_Ko3h": ["mob-crz-air"],
    "dPeET-pgVN|cj7G775u_Q": ["mob-active-commute-obesity"],
    "_2dhcsFISl|cj7G775u_Q": ["mob-active-commute-obesity", "graph-confounders-commute-obesity"],
    "cEPG6i4Yq1|fo-h4u_aJp": ["nbhd-noise311-exposure"],
    "var:commute time|mental health": ["commute-time-depression"],
    "var:air_conditioning|mortality": ["heat-ac-heat-calls"],
    "var:vacant_lot_greening|crime_safety": ["nbhd-vacant-shootings", "levers-vacant-lot-trial-match"],
    "var:traffic_calming|crime_safety": ["turn-calming-ped"],
    "var:street_trees|housing_cost": ["all-boats-trees-rent"],
    "var:supermarkets|physical_health": ["food-supermarket-diabetes-zcta"],
}
# Cells of the 25 x 8 matrix on which a claim is registered.
MATRIX_TESTS = {
    ("street_trees", "housing_cost"): ["all-boats-trees-rent"],
    ("street_trees", "physical_health"): ["heat-trees-ed-chain"],
    ("air_conditioning", "mortality"): ["heat-ac-heat-calls"],
    ("air_conditioning", "crime_safety"): ["heat-ac-shootings"],
    ("vacant_lot_greening", "crime_safety"): ["nbhd-vacant-shootings", "levers-vacant-lot-trial-match"],
    ("traffic_calming", "crime_safety"): ["turn-calming-ped", "turn-calming-leftturn"],
    ("supermarkets", "physical_health"): ["food-supermarket-diabetes-zcta"],
    ("congestion_low_emission", "physical_health"): ["mob-crz-air"],
    ("congestion_low_emission", "crime_safety"): ["bridge-crz-injury-crashes-v2"],
    ("congestion_low_emission", "income_employment"): ["crz-storefront-vacancy"],
}
# Corrected values for temperature | homicide, copied from the graph_evidence summary of
# claims/registered/heat-shootings.json: the abstracts give percent changes and the graph
# stores them as odds ratios.
CORRECTIONS = {
    (36858215, 4.9): dict(value=1.049, lo=1.016, hi=1.081),
    (36858215, 6.2): dict(value=1.062, lo=None, hi=None),
    (32738768, 0.095): dict(value=1.095, lo=1.043, hi=1.150),
    (32738768, 0.088): dict(value=1.088, lo=1.015, hi=1.166),
}
CORRECTION_NOTE = ("The abstract gives a percent change and the graph stores it as an odds ratio; corrected value from "
                   "claims/registered/heat-shootings.json. Case-crossover study.")
CORRECTION_PMIDS = {36858215: "cohort", 32738768: "cohort"}

POOLABLE = {f"{T}|YZku29igbl": "All three are percent changes in homicide per 5 °C, as read from the abstracts (claims/registered/heat-shootings.json). "
                                 "Rahman 2023 uses the daily maximum at lag 0 and Xu 2020 the daily mean over lags 0 to 7; the two Xu values are Chicago and New York."}
RATIO = re.compile(r"(ratio|odds|hazard)", re.I)
UNSIGNED = re.compile(r"(determination|r_squared|chi|f_stat|anova|eta|t_test|gini|auc)", re.I)
DESIGN_LABEL = {"trial": "experiment or trial", "quasi": "quasi-experiment", "cohort": "cohort, case-control or case-crossover",
                "cross": "cross-section", "unknown": "design not recorded by the graph"}
KW = [
    ("trial", r"randomi[sz]ed|\brct\b|cluster trial|controlled trial"),
    ("quasi", r"quasi|difference.in.difference|natural experiment|before.and.after|interrupted|controlled study|matched time series"),
    ("cohort", r"cohort|case.control|case.crossover|longitudinal|within.person|fixed effects|time.series|panel|prospective|follow.up|self.controlled|sequence symmetry"),
    ("cross", r"cross.sectional|survey|ecological|records"),
]


def design_from_text(t: str) -> str | None:
    t = (t or "").lower()
    for cls, pat in KW:
        if re.search(pat, t):
            return cls
    return None


def pmid_of(v) -> int | None:
    try:
        return int(float(v)) if v not in (None, "") else None
    except (TypeError, ValueError):
        return None


def num(v):
    try:
        x = float(v)
        return x if math.isfinite(x) else None
    except (TypeError, ValueError):
        return None


# --------------------------------------------------------------------------- cache index
def index_cache():
    assoc, rels, labels, by_id = defaultdict(dict), {}, {}, {}
    for f in S.CACHE.glob("*.json"):
        d = json.loads(f.read_text())
        p, r = d["path"], d["response"]
        if not isinstance(r, dict):
            continue
        m = re.match(r"/v1/relationships/([^/]+)/associations$", p)
        if m:
            rid = urllib.parse.unquote(m.group(1))
            for a in r.get("data", []):
                assoc[rid][a["system_id"]] = a
                by_id[a["system_id"]] = a
            continue
        if p.endswith("/associations") or p == "/v1/associations":
            for a in r.get("data", []):
                if isinstance(a, dict) and a.get("system_id"):
                    by_id.setdefault(a["system_id"], a)
            continue
        m = re.match(r"/v1/concepts/([^/]+)/relationships$", p)
        if m:
            for x in r.get("data", []):
                rels[x["relationship_id"]] = x
                for k in ("source_concept", "target_concept"):
                    c = x.get(k) or {}
                    if c.get("system_id"):
                        labels[c["system_id"]] = c.get("wikidata_label")
            continue
        m = re.match(r"/v1/relationships/([^/]+)$", p)
        if m and r.get("relationship_id"):
            rels.setdefault(r["relationship_id"], r)
    return assoc, rels, labels, by_id


# --------------------------------------------------------------------------- readings
def load_readings():
    """pmid -> {record, design, design_text, source, note}. Later sources do not overwrite a coded record."""
    R: dict[int, dict] = {}

    def put(pmid, **kw):
        if pmid is None:
            return
        cur = R.setdefault(pmid, {})
        for k, v in kw.items():
            if v and not cur.get(k):
                cur[k] = v

    for row in csv.DictReader(open(DER / "all_boats" / "verification.csv")):
        pm = pmid_of(row["pubmed_id"])
        rec = {"yes": "correct", "partial": "qualifier-lost", "no": "wrong"}.get(row["record_ok"])
        des = design_from_text(row["design"]) or {"experimental": "trial", "longitudinal": "cohort", "cross-sectional": "cross"}.get(row["design_class"])
        put(pm, record=rec, design=des, design_text=row["design"] or row["design_class"],
            source="data/derived/all_boats/verification.csv", note=row["note"])
    for c in json.load(open(DER / "graph" / "retimed_week" / "abstract_checks.json"))["checks"]:
        v = c["verdict"].lower()
        rec = "correct" if v.startswith("match") else "wrong" if v.startswith("error") else "qualifier-lost"
        put(pmid_of(c["pmid"]), record=rec, design=design_from_text(c["abstract"]), design_text=c["abstract"],
            source="data/derived/graph/retimed_week/abstract_checks.json", note=c["verdict"] + ". " + c["abstract"])
    src = (ROOT / "viz" / "data" / "levers.js").read_text()
    for lv in json.loads(src[src.index("["):src.rindex("]") + 1]):
        e = lv.get("effect") or {}
        d = {"experiment": "trial"}.get(e.get("design")) or design_from_text((e.get("design") or "") + " " + (e.get("study") or ""))
        put(pmid_of(e.get("pmid")), design=d, design_text=e.get("study"), source="viz/data/levers.js")
    for pm, des in CORRECTION_PMIDS.items():
        R[pm] = dict(record="read", design=des, design_text="case-crossover", source="claims/registered/heat-shootings.json", note=CORRECTION_NOTE)
    # A registration that cites one paper in an entry read that paper's abstract.
    for f in sorted((ROOT / "claims" / "registered").glob("*.json")):
        c = json.loads(f.read_text())
        for g in c.get("graph_evidence") or []:
            if not isinstance(g, dict):
                continue
            pms = [pmid_of(x) for x in (g.get("pubmed_ids") or [])]
            if len(pms) == 1 and pms[0] and g.get("summary"):
                put(pms[0], record="read", design=design_from_text(g["summary"]), design_text=g["summary"],
                    source=f"claims/registered/{f.name}", note=g["summary"])
    return R


# --------------------------------------------------------------------------- pubmed (bibliographic)
def pubmed_summaries(pmids: list[int]) -> dict:
    cache = ROOT / "data" / "cache" / "pubmed" / "esummary.json"
    have = json.loads(cache.read_text()) if cache.exists() else {}
    need = [p for p in pmids if str(p) not in have]
    for i in range(0, len(need), 150):
        batch = need[i:i + 150]
        url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&retmode=json&id=" + ",".join(map(str, batch))
        req = urllib.request.Request(url, headers={"User-Agent": "research-script/1.0"})
        try:
            res = json.loads(urllib.request.urlopen(req, timeout=60).read())["result"]
        except Exception as e:  # network: the page then shows PMIDs without author and year
            print("pubmed esummary failed:", e)
            break
        for p in batch:
            r = res.get(str(p)) or {}
            have[str(p)] = {"author": (r.get("sortfirstauthor") or "").rsplit(" ", 1)[0], "year": (r.get("pubdate") or "")[:4],
                            "journal": r.get("source"), "title": r.get("title"), "pubtype": r.get("pubtype") or []}
        time.sleep(0.4)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(have))
    return have


# --------------------------------------------------------------------------- findings
def make_finding(a: dict, R: dict, studies: dict, edge_id: str = "") -> dict:
    """a: a graph association in API form, or a row of a derived CSV mapped to the same keys."""
    st = a.get("system_statistic_type") or a.get("statistic_type") or ""
    v, lo, hi, p = num(a.get("statistic_value")), num(a.get("ci_lower")), num(a.get("ci_upper")), num(a.get("p_value"))
    pm = pmid_of(a.get("pubmed_id"))
    f = {"id": a.get("system_id"), "v1": a.get("variable_1_name"), "v2": a.get("variable_2_name"), "stat": st,
         "value": v, "lo": lo, "hi": hi, "p": p, "pmid": pm, "study": a.get("study_id"), "flags": []}
    if lo is not None and hi is not None and lo > hi:
        lo, hi = hi, lo
        f["lo"], f["hi"] = lo, hi
        f["flags"].append("interval bounds stored in reverse order")
    read = R.get(pm) or {}
    corr = CORRECTIONS.get((pm, v)) if edge_id == f"{T}|YZku29igbl" else None
    if edge_id == f"{T}|YZku29igbl" and pm in CORRECTION_PMIDS:
        read = {**read, "record": "wrong"}
    if corr:
        f["stored"] = {"value": v, "lo": lo, "hi": hi}
        v, lo, hi = corr["value"], corr["lo"], corr["hi"]
        f["value"], f["lo"], f["hi"] = v, lo, hi
        f["corrected"] = True
    ratio = bool(RATIO.search(st))
    null = 1.0 if ratio else 0.0
    f["scale"] = "ratio" if ratio else "unsigned" if UNSIGNED.search(st) else "other"
    if v is None or f["scale"] == "unsigned":
        f["sign"] = "?"
    else:
        f["sign"] = "+" if v > null else "-" if v < null else "0"
    sig = None
    if lo is not None and hi is not None and (lo != 0 or hi != 0):
        if lo <= (v if v is not None else lo) <= hi:
            sig = not (lo <= null <= hi)
        else:
            f["flags"].append("stored value lies outside its stored interval")
    if sig is None and p is not None:
        sig = p < 0.05
    f["sig"] = sig
    if ratio and v is not None and v > 0:
        f["x"] = math.log(v)
        if lo is not None and hi is not None and lo > 0 and hi > 0 and sig is not None and "outside" not in " ".join(f["flags"]):
            f["xlo"], f["xhi"] = math.log(lo), math.log(hi)
        if not corr and (v > 20 or v < 0.05):
            f["flags"].append("ratio outside 0.05 to 20 as stored")
    elif ratio:
        f["flags"].append("ratio stored as zero or negative")
    s = studies.get(a.get("study_id")) or {}
    f["population"] = s.get("population")
    f["doi"] = s.get("doi")
    gtype = s.get("study_type")
    gdes = "trial" if isinstance(gtype, str) and re.search(r"trial|experiment", gtype, re.I) else None
    if gdes:
        f["design"], f["design_src"], f["design_text"] = gdes, "graph study_type", gtype
    elif read.get("design"):
        f["design"], f["design_src"], f["design_text"] = read["design"], read["source"], (read.get("design_text") or "")[:160]
    else:
        f["design"], f["design_src"] = "unknown", None
    f["record"] = read.get("record") or "unread"
    if read.get("record"):
        f["read_src"] = read["source"]
        f["read_note"] = (read.get("note") or "")[:420]
    return f


def summarise(fs: list[dict], pool_note: str | None = None) -> dict:
    signed = [f for f in fs if f["sign"] in ("+", "-")]
    plus, minus = sum(f["sign"] == "+" for f in signed), sum(f["sign"] == "-" for f in signed)
    sig_plus = sum(f["sign"] == "+" and f["sig"] is True for f in fs)
    sig_minus = sum(f["sign"] == "-" and f["sig"] is True for f in fs)
    des = Counter(f["design"] for f in fs)
    rec = Counter(f["record"] for f in fs)
    out = {"n": len(fs), "studies": len({f["study"] or f["pmid"] for f in fs}), "plus": plus, "minus": minus,
           "sig_plus": sig_plus, "sig_minus": sig_minus, "unsigned": len(fs) - len(signed),
           "n_ratio": sum("x" in f for f in fs), "design": dict(des), "record": dict(rec),
           "share_exp": (des["trial"] + des["quasi"]) / len(fs) if fs else 0,
           "disagree": min(plus, minus) / (plus + minus) if plus + minus else 0}
    # Pooling. The graph does not record the exposure contrast (per degree, per quintile, high against low)
    # or the reference group, so findings of one statistic type do not in general share a scale. A pooled
    # value is given only for an edge in POOLABLE, where this project's reading of the abstracts found a
    # common contrast. It uses the corrected values with intervals.
    out["pool"] = None
    if pool_note:
        best = [f for f in fs if "xlo" in f]
        if len(best) >= 2:
            w = [1 / (((f["xhi"] - f["xlo"]) / 3.92) ** 2) for f in best]
            m = sum(wi * f["x"] for wi, f in zip(w, best)) / sum(w)
            se = math.sqrt(1 / sum(w))
            out["pool"] = {"k": len(best), "est": math.exp(m), "lo": math.exp(m - 1.96 * se), "hi": math.exp(m + 1.96 * se),
                           "method": "fixed effect, inverse variance, log scale", "note": pool_note}
    out["absent"] = sum(f["record"] == "absent" for f in fs)
    xs = sorted(f["x"] for f in fs if "x" in f and f["record"] != "wrong" and not any("outside 0.05" in g for g in f["flags"]))
    if xs:
        out["ratio_range"] = {"k": len(xs), "median": math.exp(xs[len(xs) // 2] if len(xs) % 2 else (xs[len(xs) // 2 - 1] + xs[len(xs) // 2]) / 2),
                              "min": math.exp(xs[0]), "max": math.exp(xs[-1])}
    return out


# --------------------------------------------------------------------------- claims
def load_claims():
    reg, out = {}, {}
    for f in (ROOT / "claims" / "registered").glob("*.json"):
        c = json.loads(f.read_text())
        reg[c["id"]] = c
    for f in (ROOT / "claims" / "outcomes").glob("*.json"):
        c = json.loads(f.read_text())
        out[c["id"]] = c
    return reg, out


def source_versions(o: dict) -> list[str]:
    seen, res = set(), []
    for s in o.get("sources") or []:
        if not isinstance(s, dict):
            continue
        name = s.get("name") or s.get("station") or s.get("api") or s.get("kind") or ""
        ver = s.get("rows_updated_at") or s.get("last_modified") or s.get("dataset_version") or (s.get("dataset") if s.get("kind") != "nyc-open-data" else "") or s.get("version") or ""
        ds = s.get("dataset") if s.get("kind") == "nyc-open-data" else ""
        t = " · ".join(str(x) for x in (name, ds, ver) if x)
        if t and t not in seen:
            seen.add(t)
            res.append(t)
    return res[:8]


def test_record(cid: str, reg: dict, out: dict) -> dict | None:
    r, o = reg.get(cid), out.get(cid)
    if not r:
        print("  !! claim not found:", cid)
        return None
    t = {"claim": cid, "kind": r.get("kind"), "statement": r.get("statement"), "prior": r.get("prior"),
         "verdict": (o or {}).get("verdict") or "registered", "predicted": (r.get("prediction") or {}).get("direction")}
    if o:
        ce = o.get("city_effect") or {}
        est, lo, hi, null = num(ce.get("estimate")), num(ce.get("lo")), num(ce.get("hi")), num(ce.get("null"))
        t.update(label=ce.get("label"), est=est, lo=lo, hi=hi, scale=ce.get("scale"), null=null, n=ce.get("n"),
                 verdict_note=o.get("verdict_note"), scored=o.get("prediction_scored"), versions=source_versions(o))
        if est is not None and null is not None:
            t["sign"] = "+" if est > null else "-" if est < null else "0"
        if null == 1 and est and est > 0 and re.search(r"ratio|irr|\bor\b|\brr\b|\bhr\b", (ce.get("scale") or "") + " " + (ce.get("label") or ""), re.I):
            t["x"] = math.log(est)
            if lo and hi and lo > 0 and hi > 0:
                t["xlo"], t["xhi"] = math.log(lo), math.log(hi)
        crit = o.get("critique")
        rep = f"critique/{cid}.md" if (ROOT / "critique" / f"{cid}.md").exists() else None
        if not rep and isinstance(crit, dict):
            rep = crit.get("report")
        if rep and (ROOT / rep).exists():
            t["referee"] = rep
            if isinstance(crit, dict):
                t["referee_answer"] = crit.get("answer")
    return t


# --------------------------------------------------------------------------- main
def main():
    before = len(list(S.CACHE.glob("*.json")))
    assoc, rels, labels, by_id = index_cache()
    R = load_readings()
    reg, out = load_claims()
    studies: dict[str, dict] = {}

    def fetch_studies(rid=None, sids=()):
        if rid:
            for s in S.relationship_studies(rid):
                studies[s["study_id"]] = {**studies.get(s["study_id"], {}), **s}
        for sid in sids:
            if sid and "study_type" not in studies.get(sid, {}):
                s = S.study(sid)
                if isinstance(s, dict) and s.get("study_id"):
                    studies[sid] = {**studies.get(sid, {}), **s}

    edges = []
    # concept edges
    for group, rid, la, lb in CONCEPT_EDGES:
        a, b = rid.split("|")
        rows = dict(assoc.get(rid, {}))
        rev = f"{b}|{a}"
        n_rev = 0
        if rev not in {e[1] for e in CONCEPT_EDGES}:
            for k, v in assoc.get(rev, {}).items():
                if k not in rows:
                    rows[k] = v
                    n_rev += 1
        rel = rels.get(rid) or S.relationship(rid) or {}
        fetch_studies(rid)
        if n_rev:
            fetch_studies(rev)
        fetch_studies(sids=[x.get("study_id") for x in rows.values() if x.get("study_id") not in studies or "study_type" not in studies[x.get("study_id")]][:40])
        edges.append({"id": rid, "kind": "concept", "group": group, "a": la, "b": lb,
                      "graph_labels": [labels.get(a), labels.get(b)], "n_graph": rel.get("num_findings"),
                      "n_studies_graph": rel.get("num_studies"), "last_published": (rel.get("last_published_date") or "")[:10],
                      "n_reverse": n_rev, "_rows": list(rows.values())})
    # commuting and telework edges
    cf = list(csv.DictReader(open(DER / "graph" / "retimed_week" / "consequence_findings.csv")))
    counts = {(r["consequence"], r["channel"]): r for r in csv.DictReader(open(DER / "graph" / "retimed_week" / "consequence_counts.csv"))}
    for outc in COMMUTE_OUTCOMES:
        for ch in ("commute time", "telework"):
            rows = []
            for r in cf:
                if r["channel"] == ch and r["consequence"] == outc:
                    g = by_id.get(r["association_id"])
                    rows.append(g or {"system_id": r["association_id"], "variable_1_name": r["exposure_variable"], "variable_2_name": r["outcome_variable"],
                                      "statistic_type": r["statistic"], "statistic_value": r["value"], "ci_lower": r["ci_lower"], "ci_upper": r["ci_upper"],
                                      "p_value": r["p"], "pubmed_id": r["pubmed_id"], "study_id": r["study_id"]})
            fetch_studies(sids=[x.get("study_id") for x in rows])
            cnt = counts.get((outc, ch), {})
            edges.append({"id": f"var:{ch}|{outc}", "kind": "variable", "group": "commute", "a": "commute time" if ch == "commute time" else "working at home",
                          "b": outc, "found_by": "variable-name search, data/derived/graph/retimed_week/consequence_findings.csv",
                          "direction_after_reading": cnt.get("direction_after_reading") or None, "_rows": rows})
    # all_boats edges
    ab = list(csv.DictReader(open(DER / "all_boats" / "associations_classified.csv")))
    for iv, dom, la, lb in LEVER_EDGES:
        rows = []
        for r in ab:
            if r["intervention"] == iv and r["domain"] == dom:
                g = by_id.get(r["association_id"])
                rows.append(g or {"system_id": r["association_id"], "variable_1_name": r["exposure_var"], "variable_2_name": r["outcome_var"],
                                  "statistic_type": r["statistic"], "statistic_value": r["value"], "ci_lower": r["ci_lower"], "ci_upper": r["ci_upper"],
                                  "p_value": r["p"], "pubmed_id": r["pubmed_id"], "study_id": r["study_id"]})
        fetch_studies(sids=[x.get("study_id") for x in rows])
        edges.append({"id": f"var:{iv}|{dom}", "kind": "variable", "group": "levers", "a": la, "b": lb,
                      "found_by": "variable-name search, data/derived/all_boats/associations_classified.csv", "_rows": rows})

    # heat by medicine or condition (viz/data/heat_drugs.js, written by analyses/heat_drugs; read only)
    hdjs = ROOT / "viz" / "data" / "heat_drugs.js"
    hd_design = json.loads((DER / "heat_drugs" / "prereg_design.json").read_text()) if (DER / "heat_drugs" / "prereg_design.json").exists() else None
    HD = None
    if hdjs.exists():
        t = hdjs.read_text()
        HD = json.loads(t[t.index("{"):t.rindex("}") + 1])
        nodes = {n["id"]: n for n in HD["nodes"]}
        for nid in MODIFIERS:
            n = nodes[nid]
            extra = []
            for h in HD["findings"]:
                if h["node"] != nid:
                    continue
                ratio = h["measure"] != "r"
                m = re.match(r"(.*?)\s+(\d{4})$", h["cite"])
                f = {"id": f"hd:{nid}:{h['pmid']}:{h['est']}:{len(extra)}", "v1": f"heat with {n['label'].lower()}", "v2": h["outcome"], "stat": h["measure"],
                     "value": h["est"], "lo": h.get("lo"), "hi": h.get("hi"), "p": None, "pmid": h["pmid"], "study": str(h["pmid"]), "flags": [],
                     "scale": "ratio" if ratio else "other", "sign": h["dir"] if h["dir"] in ("+", "-") or h["est"] is None else ("+" if h["est"] > 1 else "-"),
                     "sig": (not (h["lo"] <= 1 <= h["hi"])) if h.get("lo") is not None and h.get("hi") is not None else None,
                     "population": h["outcome"], "doi": None, "design": design_from_text(h["design"]) or "unknown", "design_src": "viz/data/heat_drugs.js",
                     "design_text": h["design"], "record": {"correct": "correct", "partial": "qualifier-lost", "absent": "absent", "wrong": "wrong"}[h["graph"]],
                     "read_src": "docs/heat_drugs.md", "read_note": h.get("note"), "interaction": h.get("interaction"),
                     "author": m.group(1) if m else h["cite"], "year": m.group(2) if m else None}
                if ratio and h["est"] and h["est"] > 0:
                    f["x"] = math.log(h["est"])
                    if h.get("lo") and h.get("hi"):
                        f["xlo"], f["xhi"] = math.log(h["lo"]), math.log(h["hi"])
                extra.append(f)
            edges.append({"id": f"mod:{nid}", "kind": "modifier", "group": "modify", "a": f"heat × {n['label'].lower()}", "b": "heat illness or death",
                          "modifier": n["label"], "modifier_kind": n["kind"], "mechanism": n.get("mechanism"), "page": "heat_drugs.html",
                          "found_by": "abstracts read for docs/heat_drugs.md; viz/data/heat_drugs.js", "not_found": HD["not_found"].get(nid),
                          "no_test": ("No city test was registered. The power check gave D = %.1f, where registration requires 4, and the prescriber's ZIP code does not show where patients live (docs/heat_drugs.md)." % hd_design["design_A_edp"]["scenarios"]["central"]["D"]) if hd_design else None,
                          "_rows": [], "_extra": extra})

    # findings, tests, summaries
    pmids = sorted({pmid_of(r.get("pubmed_id")) for e in edges for r in e["_rows"]} - {None})
    bib = pubmed_summaries(pmids)
    for e in edges:
        fs = [make_finding(r, R, studies, e["id"]) for r in e.pop("_rows")] + e.pop("_extra", [])
        for f in fs:
            b = bib.get(str(f["pmid"])) or {}
            f["author"], f["year"], f["journal"] = f.get("author") or b.get("author") or None, f.get("year") or b.get("year") or None, b.get("journal")
            f["pubtype"] = [t for t in (b.get("pubtype") or []) if t not in ("Journal Article",) and not t.startswith("Research Support")][:3]
        fs.sort(key=lambda f: (f.get("x") is None, f.get("x") or 0))
        e["findings"] = fs
        e["sum"] = summarise(fs, POOLABLE.get(e["id"]))
        e["tests"] = [t for t in (test_record(c, reg, out) for c in EDGE_TESTS.get(e["id"], [])) if t]
        cited = sorted({c["id"] for c in reg.values() for g in (c.get("graph_evidence") or []) if isinstance(g, dict)
                        and (g.get("relationship_id") == e["id"] or e["id"] in (g.get("relationship_ids") or []))})
        e["cited_by"] = cited
        if e["kind"] == "concept" and e["n_graph"] is not None and e["n_graph"] != e["sum"]["n"] - e.get("n_reverse", 0):
            e["count_note"] = f"The relationship record counts {e['n_graph']} findings; the association endpoint returned {e['sum']['n'] - e.get('n_reverse', 0)}."

    # ---------------------------------------------------------------- relations among edges
    idx = {e["id"]: e for e in edges}
    hs_r, hs_o = reg["heat-shootings"], out["heat-shootings"]
    link_o, br_r, br_o = out["bridge-shot-ems-link"], reg["bridge-heat-shootings-ems"], out["bridge-heat-shootings-ems"]
    cp = br_r["composed_prediction"]
    chain = {
        "claim": "bridge-heat-shootings-ems", "verdict": br_o["verdict"], "statement": br_r["statement"],
        "nodes": ["daily maximum temperature", "shooting incidents", "EMS dispatches for gunshot wounds"],
        "links": [
            {"claim": "heat-shootings", "verdict": hs_o["verdict"], "edge": f"{T}|YZku29igbl", "est": hs_o["city_effect"]["estimate"],
             "lo": hs_o["city_effect"]["lo"], "hi": hs_o["city_effect"]["hi"], "scale": hs_o["city_effect"]["scale"], "ratio": True,
             "graph": "4 findings in the graph (temperature and homicide), 1 on firearms"},
            {"claim": "bridge-shot-ems-link", "verdict": link_o["verdict"], "edge": None, "est": link_o["city_effect"]["estimate"],
             "lo": link_o["city_effect"]["lo"], "hi": link_o["city_effect"]["hi"], "scale": link_o["city_effect"]["scale"], "ratio": False,
             "graph": "no finding in the graph links shootings to EMS dispatches"},
        ],
        "composed": {"est": cp["median"], "lo": cp["lo"], "hi": cp["hi"], "scale": cp["scale"], "file": cp["file"]},
        "endpoint": {"est": br_o["city_effect"]["estimate"], "lo": br_o["city_effect"]["lo"], "hi": br_o["city_effect"]["hi"],
                     "scale": br_o["city_effect"]["scale"], "z": br_o["endpoint_test"]["z"], "compatible": br_o["endpoint_test"]["compatible"],
                     "label": br_o["city_effect"]["label"]},
        "versions": source_versions(br_o),
    }
    contradiction = {"rows": [], "source": "data/derived/graph/retimed_week/consequence_findings.csv; docs/graph_experiments.md",
                     "claim": "transit-weekday-pattern", "claim_verdict": out["transit-weekday-pattern"]["verdict"]}
    for outc in COMMUTE_OUTCOMES:
        row = {"outcome": outc}
        for key, ch in (("commute", "commute time"), ("telework", "telework")):
            e = idx[f"var:{ch}|{outc}"]
            row[key] = {"edge": e["id"], "n": e["sum"]["n"], "plus": e["sum"]["plus"], "minus": e["sum"]["minus"],
                        "studies": e["sum"]["studies"], "design": e["sum"]["design"], "read": e.get("direction_after_reading")}
        contradiction["rows"].append(row)
    # shared studies: a paper whose findings sit on two or more edges
    by_paper = defaultdict(lambda: defaultdict(int))
    for e in edges:
        for f in e["findings"]:
            if f["pmid"]:
                by_paper[f["pmid"]][e["id"]] += 1
    shared = []
    for pm, es in by_paper.items():
        if len(es) >= 2:
            b = bib.get(str(pm)) or next(({"author": f["author"], "year": f["year"]} for e in edges for f in e["findings"] if f["pmid"] == pm), {})
            shared.append({"pmid": pm, "author": b.get("author"), "year": b.get("year"), "journal": b.get("journal"), "title": b.get("title"),
                           "edges": dict(es), "record": (R.get(pm) or {}).get("record")})
    shared.sort(key=lambda s: (-len(s["edges"]), -sum(s["edges"].values())))
    n_multi = len(shared)
    ac_o = out["heat-ac-shootings"]
    drugs = None
    if HD:
        drugs = {"page": "heat_drugs.html", "doc": "docs/heat_drugs.md", "tally": HD["tally"], "edges": [f"mod:{m}" for m in MODIFIERS],
                 "search": HD.get("graph_search"), "D": hd_design["design_A_edp"]["scenarios"]["central"]["D"] if hd_design else None}
    modification = {
        "edge": f"{T}|YZku29igbl", "modifier": "household air conditioning", "claim": "heat-ac-shootings", "verdict": ac_o["verdict"],
        "est": ac_o["city_effect"]["estimate"], "lo": ac_o["city_effect"]["lo"], "hi": ac_o["city_effect"]["hi"], "scale": ac_o["city_effect"]["scale"],
        "label": ac_o["city_effect"]["label"], "note": ac_o.get("verdict_note"), "referee": "critique/heat-ac-shootings.md",
        "graph": next((g["summary"] for g in reg["heat-ac-shootings"]["graph_evidence"] if g.get("direction") == "0"), None),
        "drugs": drugs,
    }

    # ---------------------------------------------------------------- matrix
    mrows = list(csv.DictReader(open(DER / "all_boats" / "matrix_verified.csv")))
    ivs, doms, cells = [], [], []
    for r in mrows:
        if r["intervention"] not in [i["id"] for i in ivs]:
            ivs.append({"id": r["intervention"], "label": r["label"]})
        if r["domain"] not in doms:
            doms.append(r["domain"])
        tests = [{"claim": c, "verdict": (out.get(c) or {}).get("verdict", "registered")} for c in MATRIX_TESTS.get((r["intervention"], r["domain"]), []) if c in reg]
        cells.append({"i": r["intervention"], "d": r["domain"], "n": int(r["n_studies_graph"] or 0), "read": int(r["n_read"] or 0),
                      "status": r["status"], "benefit": r["benefit_design"] or None, "harm": r["harm_design"] or None, "tests": tests})
    matrix = {"interventions": ivs, "domains": doms, "cells": cells, "source": "data/derived/all_boats/matrix_verified.csv"}

    allf = [f for e in edges for f in e["findings"]]
    meta = {
        "generated": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "dataset": S.DATASET_VERSION, "api": S.API_VERSION,
        "licence": "Graph-derived data: CC BY-NC 4.0, System Public Graph",
        "n_edges": len(edges), "n_findings": len(allf), "n_findings_unique": len({f["id"] for f in allf}),
        "n_papers": len({f["pmid"] for f in allf if f["pmid"]}),
        "n_tested": sum(bool(e["tests"]) for e in edges), "n_empty": sum(e["sum"]["n"] == 0 for e in edges),
        "design": dict(Counter(f["design"] for f in allf)), "record": dict(Counter(f["record"] for f in allf)),
        "design_src": dict(Counter(f["design_src"] or "none" for f in allf)),
        "with_interval": sum("xlo" in f or (f["lo"] is not None and f["hi"] is not None) for f in allf),
        "with_population": sum(bool(f["population"]) for f in allf), "with_year": sum(bool(f["year"]) for f in allf),
        "on_ratio_axis": sum("x" in f for f in allf), "flagged": sum(bool(f["flags"]) for f in allf),
        "graph_study_type_present": sum(1 for s in studies.values() if s.get("study_type")), "studies_looked_up": len(studies),
        "papers_on_two_or_more_edges": n_multi, "design_labels": DESIGN_LABEL,
        "uncached_requests": len(list(S.CACHE.glob("*.json"))) - before,
    }
    data = {"meta": meta, "groups": [{"id": g, "label": l, "note": n} for g, l, n in GROUPS], "edges": edges,
            "relations": {"chain": chain, "contradiction": contradiction, "shared": shared[:14], "modification": modification},
            "matrix": matrix}
    OUT.mkdir(parents=True, exist_ok=True)
    js = json.dumps(data, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    (OUT / "hypergraph.json").write_text(json.dumps(data, ensure_ascii=False, indent=1, allow_nan=False))
    (OUT / "hypergraph.js").write_text(
        "// Built by tools/build_hypergraph.py. Graph-derived data (findings, variables, study records) are from the\n"
        "// System Public Graph, " + S.DATASET_VERSION + ", licensed CC BY-NC 4.0. City estimates are this project's.\n"
        "window.CONCORD_HYPERGRAPH = " + js + ";\n")
    print(json.dumps(meta, indent=1))
    for e in edges:
        s = e["sum"]
        print(f"{e['group']:8} {e['a'][:26]:26} | {e['b'][:28]:28} n={s['n']:3} graph={e.get('n_graph')} ratio={s['n_ratio']:3} +{s['plus']} -{s['minus']} "
              f"des={s['design']} rec={s['record']} tests={[(t['claim'], t['verdict'], round(t['est'], 3) if t.get('est') is not None else None, 'x' in t) for t in e['tests']]}")


if __name__ == "__main__":
    main()
