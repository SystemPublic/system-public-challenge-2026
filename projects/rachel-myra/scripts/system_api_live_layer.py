"""Task 5 (spec 8.5a role 6, live layer): smoke-test the calls the app can make live per drug card,
measure latency, and write a small JSON spec of those calls.

Per drug (15 in-scope groups), one anchor concept is chosen (first preferred label found by exact
wikidata_label match). Calls tested, each timed WITHOUT the cache (3 repeats) and also cached:
  1. GET /v1/concepts?search=wikidata_label:<label>&limit=10                    -> concept id (build time only)
  2. GET /v1/concepts/{id}/relationships?limit=1&include_total=true&sort=last_published_date:desc
        -> total relationship count + newest-evidence date in ONE call
  3. GET /v1/concepts/{id}/relationships?limit=5&sort=num_studies:desc          -> top edges for the card
  4. GET /v1/relationships/{A%7CB}  (one edge from call 3)                      -> single-edge refresh
Output: data/processed/system_api_live_layer.json (spec + per-drug results + latency stats).
Run:  uv run --with requests python scripts/system_api_live_layer.py
"""
import json, os, statistics, sys, time

sys.path.insert(0, os.path.dirname(__file__))
from system_api_client import Client  # noqa: E402
from system_api_common import PROC, DRUGS15  # noqa: E402

ANCHORS = {
    "lithium": ["lithium carbonate", "lithium"],
    "loop_diuretics": ["furosemide", "loop diuretic"],
    "thiazides": ["hydrochlorothiazide", "thiazide"],
    "acei_arb": ["ACE inhibitor", "lisinopril", "losartan"],
    "sglt2": ["SGLT2 inhibitor", "empagliflozin", "dapagliflozin"],
    "insulin": ["insulin"],
    "metformin": ["metformin"],
    "anticholinergics": ["oxybutynin", "anticholinergic"],
    "antipsychotics": ["antipsychotic", "clozapine", "olanzapine"],
    "ssris": ["selective serotonin reuptake inhibitor", "sertraline"],
    "topiramate_zonisamide": ["topiramate", "zonisamide"],
    "adhd_stimulants": ["methylphenidate", "amphetamine"],
    "beta_blockers": ["beta blocker", "metoprolol", "propranolol"],
    "opioids_fentanyl": ["fentanyl", "opioid"],
    "epinephrine_ai": ["epinephrine", "adrenaline"],
}
REPEATS = int(os.environ.get("LIVE_REPEATS", "3"))


def timed(c, path, **params):
    t = []
    body = None
    for _ in range(REPEATS):
        t0 = time.time()
        body = c.get(path, use_cache=False, **params)
        t.append(round((time.time() - t0) * 1000))
    return body, t


def main():
    c = Client(sleep=0.3)
    lat = {"concept_search": [], "count_and_newest": [], "top_edges": [], "single_edge": []}
    drugs = {}
    for g, labels in ANCHORS.items():
        anchor = None
        for lab in labels:
            body = c.get("/concepts", search=f"wikidata_label:{lab}", limit=10) or {}
            ex = [x for x in body.get("data", []) if (x.get("wikidata_label") or "").lower() == lab.lower()]
            if ex:
                anchor = ex[0]
                break
        if not anchor:
            drugs[g] = {"label": DRUGS15[g]["label"], "anchor": None, "note": "no exact concept label found"}
            continue
        cid = anchor["system_id"]
        _, t = timed(c, "/concepts", search=f"wikidata_label:{anchor['wikidata_label']}", limit=10)
        lat["concept_search"] += t
        b2, t = timed(c, f"/concepts/{cid}/relationships", limit=1, include_total="true", sort="last_published_date:desc",
                      fields="relationship_id,num_findings,num_studies,last_published_date")
        lat["count_and_newest"] += t
        fields_ok = bool(b2 and b2.get("data") and "source_concept" not in b2["data"][0])
        if not (b2 and b2.get("data")):
            b2 = c.get(f"/concepts/{cid}/relationships", limit=1, include_total="true", sort="last_published_date:desc",
                       drop_keys=("wikidata_aliases",))
        b3, t = timed(c, f"/concepts/{cid}/relationships", limit=5, sort="num_studies:desc")
        lat["top_edges"] += t
        top = [{"relationship_id": r["relationship_id"], "other": (r["target_concept"] if r["source_concept"]["system_id"] == cid else r["source_concept"]).get("wikidata_label"),
                "num_studies": r.get("num_studies"), "num_findings": r.get("num_findings"),
                "last_published_date": r.get("last_published_date")} for r in (b3 or {}).get("data", [])]
        if top:
            _, t = timed(c, "/relationships/" + top[0]["relationship_id"].replace("|", "%7C"))
            lat["single_edge"] += t
        newest = ((b2 or {}).get("data") or [{}])[0].get("last_published_date")
        drugs[g] = {"label": DRUGS15[g]["label"], "anchor": {"system_id": cid, "wikidata_label": anchor["wikidata_label"],
                                                            "wikidata_id": anchor.get("wikidata_id")},
                    "total_relationships": (b2 or {}).get("total"), "newest_evidence_date": newest,
                    "newest_evidence_year": newest[:4] if newest else None, "fields_param_honoured": fields_ok,
                    "top_edges_by_studies": top}
        print(g, drugs[g]["total_relationships"], drugs[g]["newest_evidence_year"], c.stats())
    def st(v):
        return {"n": len(v), "median_ms": statistics.median(v) if v else None,
                "p90_ms": sorted(v)[int(0.9 * (len(v) - 1))] if v else None, "max_ms": max(v) if v else None}
    spec = {
        "generated": "2026-11-14", "base_url": "https://public-api.system.com/v1",
        "auth": "header x-api-key (server-side only; never ship the key to the browser - proxy through an API route)",
        "rate_limit": "10,000 requests/day per key; cache responses (e.g. 24 h) and refresh counts only",
        "calls": [
            {"name": "count_and_newest", "purpose": "relationship count + newest-evidence date for a drug card (1 call)",
             "request": "GET /concepts/{concept_id}/relationships?limit=1&include_total=true&sort=last_published_date:desc",
             "use_fields": ["total", "data[0].last_published_date"]},
            {"name": "top_edges", "purpose": "strongest edges for the card",
             "request": "GET /concepts/{concept_id}/relationships?limit=5&sort=num_studies:desc",
             "use_fields": ["data[].relationship_id", "data[].num_studies", "data[].num_findings", "data[].last_published_date",
                            "data[].source_concept.wikidata_label", "data[].target_concept.wikidata_label"]},
            {"name": "single_edge", "purpose": "refresh one claim's edge (e.g. thiazide -> hyponatremia)",
             "request": "GET /relationships/{A}%7C{B}", "use_fields": ["num_studies", "num_findings", "last_published_date", "last_updated"]},
            {"name": "concept_search", "purpose": "resolve concept ids at BUILD time, not live",
             "request": "GET /concepts?search=wikidata_label:{label}&limit=10", "use_fields": ["data[].system_id", "data[].wikidata_label"]},
        ],
        "latency_uncached": {k: st(v) for k, v in lat.items()},
        "drugs": drugs,
        "requests_this_script": c.live,
        "caveats": ["closed beta: fields may change", "last_published_date is often null on relationships",
                    "relationship counts include all concepts linked to the drug, not only heat-relevant ones",
                    "about 20% of API associations are extraction errors (System); live layer shows counts only, claims come from the verified knowledge base"],
    }
    json.dump(spec, open(os.path.join(PROC, "system_api_live_layer.json"), "w", encoding="utf-8"), indent=1)
    print(json.dumps(spec["latency_uncached"], indent=1))
    print(c.stats())


if __name__ == "__main__":
    main()
