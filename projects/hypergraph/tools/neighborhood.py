"""Write the graph neighbourhood of one concept as JSON for the explorer.

Usage:
  python tools/neighborhood.py k9BAffdSqv            # a concept id
  python tools/neighborhood.py "air pollution"       # a search term
  python tools/neighborhood.py --defaults            # the pre-built set
  options: --top-edges N (edges whose associations are sampled, default 12)
           --max-rels N  (relationships read, default 1500)
           --budget N    (stop sampling when this many uncached calls are spent)

Output: viz/data/graph/<slug>.json and an updated viz/data/graph/index.json.

The subgraph holds the concept, its concept-to-concept relationships
(num_findings, num_studies, last_published_date) and, for the top edges by
num_findings, a sample of associations with their signed statistics and
PubMed ids. The graph's relationship aggregates carry no sign, so the sign of
each association is read from its statistic: ratio statistics are compared
with 1, differences and coefficients with 0. An association whose interval
crosses the null, or whose p value is above 0.05, is counted as null. A
statistic whose sign cannot be read (chi-square, F, a bare p value) is counted
as unknown. The sign is relative to the variables as the study named them,
which may be reversed ("lack of green space"), so the shares are a reading
aid, not an effect estimate.

All responses go through concord/sysgraph.py, which caches them under
data/cache/sysgraph/. The script counts the uncached calls it makes.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from concord import sysgraph as sg  # noqa: E402

OUTDIR = ROOT / "viz" / "data" / "graph"

DEFAULTS = [
    ("heat wave", "k9BAffdSqv"),
    ("gun violence", "X7hfhwez9f"),
    ("green space", "lHLIKbfnYp"),
    ("urban heat island", "UbF0-c8zHb"),
    ("air pollution", "P6IzhScRdx"),
    ("asthma", "EAshH_Ko3h"),
    ("noise pollution", "36gde7OoEQ"),
    ("air temperature", "mUxSLRMwIy"),
]

RATIO = re.compile(r"(ratio|^or$|^rr$|^hr$|^irr$|relative_risk|odds|hazard|rate_ratio|fold)", re.I)
SIGNED = re.compile(r"(pearson|spearman|kendall|correlation|_r$|^r$|beta|coefficient|difference|"
                    r"slope|t_stat|z_score|z_stat|percent_change|effect_size|cohen|hedges|smd|"
                    r"standardized|regression|estimate|change)", re.I)


_CALLS = {"uncached": 0, "all": 0}
_orig_get = sg.get


def _counting_get(path, params=None, **kw):
    """sg.get, counting calls whose response is not yet in the cache. Other
    agents write to the same cache, so counting files would overstate this."""
    import hashlib
    import urllib.parse
    p = {k: v for k, v in (params or {}).items() if v is not None}
    q = urllib.parse.urlencode(sorted(p.items()), doseq=True)
    sig = hashlib.sha256(f"{path}?{q}".encode()).hexdigest()[:24]
    _CALLS["all"] += 1
    if kw.get("refresh") or not (sg.CACHE / f"{sig}.json").exists():
        _CALLS["uncached"] += 1
    return _orig_get(path, params, **kw)


sg.get = _counting_get


UNSIGNED = re.compile(r"(determination|r_squared|r2|chi|f_stat|anova|eta|p_value|auc|i_squared)", re.I)


def uncached_count() -> int:
    return _CALLS["uncached"]


def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "concept"


def resolve(term: str) -> dict:
    """A concept id, or a search term resolved to the exact label if present."""
    if re.fullmatch(r"[A-Za-z0-9_-]{10}", term) and " " not in term:
        d = sg.concept(term)
        if d and d.get("system_id"):
            return d
    for q in [term] + term.split():
        hits = sg.concepts(q, 20)
        exact = [h for h in hits if h["wikidata_label"].lower() == term.lower()]
        if exact:
            return exact[0]
        if hits and q == term:
            return hits[0]
    raise SystemExit(f"no concept found for {term!r}")


def sign_of(a: dict) -> str:
    """'pos', 'neg', 'null' or 'unknown' for one association."""
    st = (a.get("system_statistic_type") or a.get("statistic_type") or "").strip()
    v = a.get("statistic_value")
    if v is None or not st or UNSIGNED.search(st):
        return "unknown"
    if RATIO.search(st):
        null = 1.0
        if v <= 0:
            return "unknown"
    elif SIGNED.search(st):
        null = 0.0
    else:
        return "unknown"
    lo, hi = a.get("ci_lower"), a.get("ci_upper")
    if lo is not None and hi is not None and lo <= null <= hi:
        return "null"
    p = a.get("p_value")
    if isinstance(p, (int, float)) and p > 0.05 and (lo is None or hi is None):
        return "null"
    if v > null:
        return "pos"
    if v < null:
        return "neg"
    return "null"


def other(rel: dict, cid: str) -> dict:
    s, t = rel["source_concept"], rel["target_concept"]
    return t if s["system_id"] == cid else s


def build(term: str, *, top_edges: int = 12, max_rels: int = 1500, sample: int = 12,
          study_cap: int = 20, budget: int | None = None) -> Path:
    start = uncached_count()
    start_all = _CALLS["all"]
    c = resolve(term)
    cid = c["system_id"]
    rels = sg.concept_relationships(cid, max_items=max_rels)
    rels.sort(key=lambda r: (-(r.get("num_findings") or 0), -(r.get("num_studies") or 0)))

    nodes = {cid: {"id": cid, "label": c["wikidata_label"], "wikidata_id": c.get("wikidata_id"),
                   "description": c.get("wikidata_description"), "center": True}}
    edges = []
    studies_looked = 0
    for i, r in enumerate(rels):
        o = other(r, cid)
        nodes.setdefault(o["system_id"], {"id": o["system_id"], "label": o["wikidata_label"],
                                          "wikidata_id": o.get("wikidata_id"),
                                          "description": o.get("wikidata_description")})
        e = {"id": r["relationship_id"], "source": r["source_concept"]["system_id"],
             "target": r["target_concept"]["system_id"], "num_findings": r.get("num_findings"),
             "num_studies": r.get("num_studies"), "last_published_date": (r.get("last_published_date") or "")[:10],
             "signs": None, "findings": None}
        over = budget is not None and uncached_count() - start >= budget
        if i < top_edges and not over:
            assoc = sg.relationship_associations(r["relationship_id"], max_items=200)
            signs = Counter(sign_of(a) for a in assoc)
            e["signs"] = {k: signs.get(k, 0) for k in ("pos", "neg", "null", "unknown")}
            e["n_sampled"] = len(assoc)
            fs = []
            for a in assoc[:sample]:
                f = {"association_id": a.get("system_id"), "variable_1": a.get("variable_1_name"),
                     "variable_2": a.get("variable_2_name"), "statistic_type": a.get("statistic_type"),
                     "value": a.get("statistic_value"), "ci_lower": a.get("ci_lower"),
                     "ci_upper": a.get("ci_upper"), "p_value": a.get("p_value"),
                     "pubmed_id": a.get("pubmed_id"), "study_id": a.get("study_id"), "sign": sign_of(a)}
                if not f["pubmed_id"] and f["study_id"] and studies_looked < study_cap:
                    st = sg.study(f["study_id"])
                    studies_looked += 1
                    f["pubmed_id"] = st.get("pubmed_id")
                    f["doi"] = st.get("doi")
                fs.append(f)
            e["findings"] = fs
        edges.append(e)

    calls = uncached_count() - start
    slug = slugify(c["wikidata_label"])
    out = {
        "concept": nodes[cid],
        "query": term,
        "nodes": list(nodes.values()),
        "edges": edges,
        "provenance": {
            "api": f"{sg.BASE} {sg.API_VERSION}",
            "dataset_version": sg.DATASET_VERSION,
            "built": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "relationships_read": len(rels),
            "relationships_cap": max_rels,
            "edges_sampled": sum(1 for e in edges if e["findings"] is not None),
            "api_responses": _CALLS["all"] - start_all,
            "uncached_calls_this_build": calls,
            "sign_rule": "ratio statistics vs 1, coefficients and differences vs 0; "
                         "interval crossing the null or p > 0.05 counts as null; other statistics unknown",
        },
    }
    OUTDIR.mkdir(parents=True, exist_ok=True)
    f = OUTDIR / f"{slug}.json"
    f.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
    _update_index()
    print(f"{c['wikidata_label']} ({cid}): {len(rels)} relationships, "
          f"{out['provenance']['edges_sampled']} edges sampled, {calls} uncached calls -> {f.relative_to(ROOT)}")
    return f


def _update_index():
    items = []
    for f in sorted(OUTDIR.glob("*.json")):
        if f.name == "index.json":
            continue
        d = json.loads(f.read_text())
        items.append({"file": f"data/graph/{f.name}", "label": d["concept"]["label"], "id": d["concept"]["id"],
                      "n_edges": len(d["edges"]), "built": d["provenance"]["built"]})
    (OUTDIR / "index.json").write_text(json.dumps({"subgraphs": items}, indent=1, ensure_ascii=False))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("term", nargs="?")
    ap.add_argument("--defaults", action="store_true")
    ap.add_argument("--top-edges", type=int, default=12)
    ap.add_argument("--max-rels", type=int, default=1500)
    ap.add_argument("--budget", type=int, default=None)
    a = ap.parse_args(argv)
    if not a.term and not a.defaults:
        ap.error("give a concept id or search term, or --defaults")
    terms = [cid for _, cid in DEFAULTS] if a.defaults else [a.term]
    start = uncached_count()
    for t in terms:
        build(t, top_edges=a.top_edges, max_rels=a.max_rels, budget=a.budget)
    print(f"total uncached System API calls: {uncached_count() - start}")


if __name__ == "__main__":
    main()
