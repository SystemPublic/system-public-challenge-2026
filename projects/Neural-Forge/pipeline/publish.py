"""Publish our verdicts as an Underlay collection. Every Claim record cites the exact input versions and records.

    python -m pipeline.publish            # local: write out/underlay/ (records, schemas, record hashes)
    python -m pipeline.publish --push     # push to Underlay (needs UNDERLAY_API_KEY with write scope)

First push becomes v1.0.0. After review/excluded_findings.csv changes, rebuild and push again: the server
assigns v1.1.0 and its compare page shows exactly which verdicts changed.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys

import requests

from . import config as C

STR = {"type": "string"}
NUM_OR_NULL = {"type": ["number", "null"]}
STR_OR_NULL = {"type": ["string", "null"]}
INPUT = {
    "type": "object",
    "description": "Cross-collection citation: the exact records of an exact version this verdict rests on.",
    "required": ["collection", "version"],
    "properties": {
        "collectionId": STR_OR_NULL, "collection": STR,
        "version": {"type": "string", "pattern": "^ulv3:[0-9a-f]{64}$"}, "semver": STR,
        "recordType": STR, "recordIds": {"type": "array", "items": STR},
        "query": STR_OR_NULL, "label": STR_OR_NULL, "period": STR_OR_NULL, "role": STR_OR_NULL,
    },
}
SCHEMAS = {
    "Claim": {
        "$schema": "http://json-schema.org/draft-07/schema#", "type": "object",
        "required": ["title", "kind", "verdict", "inputs"],
        "properties": {
            "title": STR, "kind": {"enum": ["direct", "bridge"]},
            "verdict": {"enum": ["confirmed", "contested", "bridged", "inconclusive"]},
            "triage": {"type": "array", "items": STR}, "settle": STR_OR_NULL, "resolution": STR_OR_NULL,
            "bridgeNote": STR_OR_NULL, "chain": {"type": "array", "items": STR},
            "research": {"type": "object", "properties": {
                "direction": STR_OR_NULL, "studies": {"type": "integer"}, "findings": {"type": "integer"},
                "excludedAfterReview": {"type": "integer"}, "evidenceFit": NUM_OR_NULL,
                "nycStudies": {"type": "integer"}, "dois": {"type": "array", "items": STR}}},
            "city": {"type": "object", "properties": {
                "x": STR, "y": STR, "unit": STR, "n": {"type": "integer"}, "rho": NUM_OR_NULL, "p": NUM_OR_NULL,
                "q": NUM_OR_NULL, "ci": {"type": ["array", "null"]}, "partialRhoPoverty": NUM_OR_NULL}},
            "inputs": {"type": "array", "items": INPUT},
            "code": {"type": "object", "properties": {"repo": STR_OR_NULL, "commit": STR_OR_NULL}},
        },
    },
    "DistrictNeed": {
        "$schema": "http://json-schema.org/draft-07/schema#", "type": "object",
        "required": ["name", "needScore", "inputs"],
        "properties": {
            "name": STR, "borough": STR_OR_NULL, "needScore": {"type": "number"}, "needRank": {"type": "integer"},
            "topNeedClaim": STR_OR_NULL, "missingStudy": STR_OR_NULL,
            "heatEdRate": NUM_OR_NULL, "povertyPct": NUM_OR_NULL, "olderAlonePct": NUM_OR_NULL,
            "surfaceTempF": NUM_OR_NULL, "inputs": {"type": "array", "items": INPUT},
        },
    },
}


def _git_commit():
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=C.PROJECT, text=True,
                                       stderr=subprocess.DEVNULL).strip()
    except Exception:
        return None


def _cite(src, role=None):
    return {"collectionId": src.get("collection_id"), "collection": src["collection"], "version": src["hash"],
            "semver": src["semver"], "recordType": src.get("record_type", ""),
            "recordIds": src.get("record_ids", []), "query": src.get("query"), "label": src.get("label"),
            "period": src.get("period"), "role": role}


def records(gt):
    code = {"repo": os.environ.get("CODE_URL"), "commit": _git_commit()}
    graph = next(i for i in gt["meta"]["inputs"] if i["collection"] == "system/public-graph")
    out = []
    for c in gt["claims"]:
        r, cty = c["research"], c["city"]
        inputs = [_cite(s, "city") for s in cty["sources"]]
        for l in r.get("links", []):
            for s in (l.get("city_fill") or {}).get("sources", []):
                inputs.append(_cite(s, "city link in bridge"))
        inputs.append(_cite({**graph, "record_type": "Association", "record_ids": r["association_ids"]}, "research"))
        out.append({"id": c["id"], "type": "Claim", "data": {
            "title": c["title"], "kind": c["kind"], "verdict": c["verdict"], "triage": c["triage"],
            "settle": c["settle"], "resolution": c.get("resolution"), "bridgeNote": c.get("bridge_note"),
            "chain": [e["label"] for e in c["chain"]],
            "research": {"direction": r["direction"], "studies": r["n_studies"], "findings": r["n_findings"],
                         "excludedAfterReview": r.get("n_excluded_after_review", 0),
                         "evidenceFit": r["evidence_fit"], "nycStudies": r.get("population", {}).get("nyc", 0),
                         "dois": r["dois"]},
            "city": {"x": cty["x_label"], "y": cty["y_label"], "unit": cty["unit"], "n": cty["n"], "rho": cty["rho"],
                     "p": cty["p"], "q": cty.get("q"), "ci": cty.get("ci"),
                     "partialRhoPoverty": cty.get("partial_rho_poverty")},
            "inputs": inputs, "code": code}})
    eh = next(i for i in gt["meta"]["inputs"] if i["collection"] == "nyc/environment-health")
    for d in gt["districts"]:
        out.append({"id": d["id"], "type": "DistrictNeed", "data": {
            "name": d["name"], "borough": d.get("borough"), "needScore": d["need_score"], "needRank": d["need_rank"],
            "topNeedClaim": d.get("top_need_claim"), "missingStudy": d.get("missing_study"),
            "heatEdRate": d.get("heat_ed_rate"), "povertyPct": d.get("poverty_pct"),
            "olderAlonePct": d.get("older_alone_pct"), "surfaceTempF": d.get("surface_temp_f"),
            "inputs": [_cite({**eh, "record_type": "Observation", "record_ids": [],
                              "query": f"Observations for geography {d['id']}: heat ED (measure 1405), poverty (221), "
                                       f"older adults alone (693), surface temperature (688)"}, "city")]}})
    return out


def _jcs(v):
    """RFC 8785 canonical JSON (enough for our data: ASCII keys, finite numbers)."""
    if isinstance(v, bool) or v is None:
        return json.dumps(v)
    if isinstance(v, float):
        if v != v or v in (float("inf"), float("-inf")):
            raise ValueError("non-finite number")
        return json.dumps(int(v)) if v.is_integer() and abs(v) < 2 ** 53 else repr(v)
    if isinstance(v, (int, str)):
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, list):
        return "[" + ",".join(_jcs(x) for x in v) + "]"
    return "{" + ",".join(json.dumps(k, ensure_ascii=False) + ":" + _jcs(v[k])
                          for k in sorted(v, key=lambda s: s.encode("utf-16-be"))) + "}"


def record_hash(r):
    canon = '{"id":' + json.dumps(r["id"], ensure_ascii=False) + ',"type":' + json.dumps(r["type"]) + \
            ',"data":' + _jcs(r["data"]) + "}"
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()


def metadata(gt):
    inputs = "\n".join(f"| `{i['collection']}` | {i['semver']} | `{i['hash']}` |" for i in gt["meta"]["inputs"])
    rules = "\n".join(f"- {r}" for r in gt["meta"]["rules"])
    h = gt["headline"]
    readme = f"""# Ground Truth: heat research tested against New York City's own data

Each `Claim` is one relationship from published research (System Public Graph) tested against NYC data on
Underlay: **confirmed**, **contested**, **bridged** or **inconclusive**, with what data would settle it.
Each `DistrictNeed` scores one community district for how much new heat research it needs.

Every record's `inputs` cites the exact collection, version id and record ids it rests on.

**Whose evidence:** {h['studies_total']} heat-and-health studies in the graph; {h['studies_nyc']} are about New York
City; {h['studies_name_low_income']} name low-income people; {h['studies_name_black_or_hispanic']} name Black or
Hispanic people; {h['studies_non_human']} are animal studies.

## Inputs

| Collection | Version | Id |
|---|---|---|
{inputs}

## Rules

{rules}

Built for the System Public Challenge 2026, Build Challenge 4. Derived from the System Public Graph
({C.GRAPH_CITATION}), so this collection is CC BY-NC 4.0.
"""
    return {"description": "Heat research from the System Public Graph tested against NYC data on Underlay, "
                           "district by district, with version-pinned citations.",
            "readme": readme, "license": "CC BY-NC 4.0", "tags": ["Research", "Government", "Health"]}


def write_local(recs, meta):
    d = C.OUT / "underlay" / C.CLAIMS_SLUG
    d.mkdir(parents=True, exist_ok=True)
    with open(d / "records.ndjson", "w") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n")
    (d / "schemas.json").write_text(json.dumps(SCHEMAS, indent=1))
    (d / "metadata.json").write_text(json.dumps(meta, indent=1))
    (d / "hashes.json").write_text(json.dumps({f"{r['type']}/{r['id']}": record_hash(r) for r in recs}, indent=1))
    return d


def push(recs, meta):
    key = os.environ.get("UNDERLAY_API_KEY")
    if not key:
        sys.exit("Set UNDERLAY_API_KEY (write scope) in .env first.")
    H = {"Authorization": f"Bearer {key}"}
    base = f"{C.UNDERLAY_API}/collections/{C.CLAIMS_OWNER}/{C.CLAIMS_SLUG}"
    r = requests.get(base, headers=H, timeout=30)
    if r.status_code == 404:
        r = requests.post(f"{C.UNDERLAY_API}/accounts/{C.CLAIMS_OWNER}/collections", headers=H, timeout=30,
                          json={"slug": C.CLAIMS_SLUG, "name": "Ground Truth: heat claims for NYC",
                                "description": meta["description"], "public": True})
        if r.status_code >= 300:
            sys.exit(f"could not create collection: {r.status_code} {r.text}")
        print("created collection", r.json().get("id"))
    head = requests.get(f"{base}/versions/latest", headers=H, timeout=30)
    head_semver = head.json()["semver"] if head.status_code == 200 else None

    deletes = []
    if head_semver:  # anything in the head that we no longer produce gets deleted
        mine = {(x["type"], x["id"]) for x in recs}
        cursor = None
        while True:
            m = requests.get(f"{base}/versions/{head_semver}/manifest", headers=H, timeout=60,
                             params={"cursor": cursor} if cursor else {}).json()
            deletes += [{"type": e["type"], "id": e["id"]} for e in m["records"] if (e["type"], e["id"]) not in mine]
            if not m["pagination"]["hasMore"]:
                break
            cursor = m["pagination"]["nextCursor"]

    s = requests.post(f"{base}/push", headers=H, timeout=60, json={
        "base": head_semver, "message": os.environ.get("PUSH_MESSAGE", "Ground Truth verdicts"),
        "app_id": "ground-truth", "schemas": SCHEMAS, "metadata": meta})
    if s.status_code >= 300:
        sys.exit(f"open session failed: {s.status_code} {s.text}")
    sid = s.json()["session_id"]
    body = "\n".join(json.dumps(x, ensure_ascii=False, separators=(",", ":")) for x in recs) + "\n"
    r = requests.post(f"{base}/push/{sid}/records", headers={**H, "Content-Type": "application/x-ndjson"},
                      data=body.encode("utf-8"), timeout=120)
    if r.status_code >= 300:
        sys.exit(f"upload failed: {r.status_code} {r.text[:2000]}")
    if deletes:
        requests.post(f"{base}/push/{sid}/deletes", headers={**H, "Content-Type": "application/x-ndjson"},
                      data="\n".join(json.dumps(x) for x in deletes) + "\n", timeout=60).raise_for_status()
    c = requests.post(f"{base}/push/{sid}/commit", headers=H, timeout=300)
    if c.status_code == 409 and "No changes" in c.text:
        print("no changes since", head_semver)
        return
    if c.status_code >= 300:
        sys.exit(f"commit failed: {c.status_code} {c.text[:2000]}")
    res = c.json().get("result", c.json())
    print(f"published {C.CLAIMS_OWNER}/{C.CLAIMS_SLUG} {res.get('semver')} {res.get('hash')}")
    print(f"{C.UNDERLAY_WEB}/{C.CLAIMS_OWNER}/{C.CLAIMS_SLUG}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--push", action="store_true")
    args = ap.parse_args()
    gt = json.loads((C.WEB_DATA / "ground_truth.json").read_text())
    if gt["meta"].get("mock"):
        sys.exit("ground_truth.json is mock data; run `python -m pipeline.build` first.")
    recs, meta = records(gt), metadata(gt)
    d = write_local(recs, meta)
    print(f"{len(recs)} records ({sum(r['type'] == 'Claim' for r in recs)} claims) written to {d}")
    if args.push:
        push(recs, meta)


if __name__ == "__main__":
    main()
