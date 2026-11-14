#!/usr/bin/env python
"""Export the claim register as an Underlay collection (records.jsonl + schemas).

Nothing is published. The script writes files that a push to an Underlay
registry (https://www.underlay.org, protocol v2) would send, so that Jeff can
decide whether and where to publish:

  data/derived/graph_audit/underlay/schemas.json     {type: JSON Schema draft-07}, from tools/underlay_schema.json
  data/derived/graph_audit/underlay/records.jsonl    one {"id", "type", "data"} per line (NDJSON)
  data/derived/graph_audit/underlay/manifest.json    record count per type and each record's hash
  data/derived/graph_audit/underlay/push_session.json  the body a first push would open with (base: null)

Record types (see tools/underlay_schema.json):
  Claim         a registration from claims/registered/, with its sha256 and the
                git commit that added it, so the order "prediction, then data" can be checked
  Outcome       a verdict from claims/outcomes/, referring to its Claim and to Source records
  GraphEvidence one item of a registration's graph_evidence, with in_csv checked
                against the Dataverse CSV when the DuckDB copy is present
  Source        a dataset version an outcome rests on: Socrata dataset id and
                rowsUpdatedAt, Dataverse DOI + version + file sha256, NOAA file
                Last-Modified, or the System API (which has no version id)
  ResearchNeed  an entry of an outcome's research_needed list

Record hashes follow the Underlay record-hashing rule: SHA-256 over
'{"id":' + JSON(id) + ',"type":' + JSON(type) + ',"data":' + JCS(data) + '}', with
JCS = RFC 8785 canonical JSON. Numbers are written as ECMAScript writes them.

Usage:
  ~/.venvs/nyc-concordance/bin/python tools/underlay_export.py [--out DIR] [--check]
  --check validates every record against its schema (needs the jsonschema package; skipped if absent)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REG = ROOT / "claims" / "registered"
OUTC = ROOT / "claims" / "outcomes"
SCHEMA = ROOT / "tools" / "underlay_schema.json"
DEFAULT_OUT = ROOT / "data" / "derived" / "graph_audit" / "underlay"
DB = Path.home() / "opt" / "nyc-concordance" / "dataverse" / "graph.duckdb"
DATAVERSE_SOURCE_ID = "dataverse:doi:10.7910/DVN/7V6JDO@2.1"


# --------------------------------------------------------------------------- canonical JSON (RFC 8785)

def _num(x) -> str:
    if isinstance(x, bool):
        return "true" if x else "false"
    if isinstance(x, int):
        if abs(x) > 2**53 - 1:
            raise ValueError(f"unsafe integer {x}: write it as a string")
        return str(x)
    if math.isnan(x) or math.isinf(x):
        raise ValueError("NaN and Infinity are not JSON")
    if x == 0:
        return "0"
    if x.is_integer() and abs(x) < 1e21:
        return str(int(x))
    # shortest round-trip digits (Python repr agrees with ECMAScript), ECMAScript layout
    d = Decimal(repr(x))
    sign, digits, exp = d.as_tuple()
    s = "".join(map(str, digits)).rstrip("0") or "0"
    k = len(s)
    n = exp + len(digits)  # position of the decimal point
    if k <= n <= 21:
        out = s + "0" * (n - k)
    elif 0 < n <= 21:
        out = s[:n] + "." + s[n:]
    elif -6 < n <= 0:
        out = "0." + "0" * (-n) + s
    else:
        e = n - 1
        out = s[0] + ("." + s[1:] if k > 1 else "") + "e" + ("+" if e > 0 else "-") + str(abs(e))
    return ("-" if sign else "") + out


def jcs(v) -> str:
    if v is None:
        return "null"
    if isinstance(v, (bool, int, float)):
        return _num(v)
    if isinstance(v, str):
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, (list, tuple)):
        return "[" + ",".join(jcs(x) for x in v) + "]"
    if isinstance(v, dict):
        # RFC 8785 sorts keys by UTF-16 code units
        keys = sorted(v, key=lambda k: k.encode("utf-16-be"))
        return "{" + ",".join(json.dumps(k, ensure_ascii=False) + ":" + jcs(v[k]) for k in keys) + "}"
    raise TypeError(f"not JSON: {type(v)}")


def record_hash(rid: str, rtype: str, data: dict) -> str:
    canon = '{"id":' + json.dumps(rid, ensure_ascii=False) + ',"type":' + json.dumps(rtype, ensure_ascii=False) \
            + ',"data":' + jcs(data) + "}"
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- helpers

def _clean(v):
    """Drop None values from dicts (schemas do not allow null for most fields) and NaN floats."""
    if isinstance(v, dict):
        return {k: _clean(x) for k, x in v.items() if x is not None and not (isinstance(x, float) and math.isnan(x))}
    if isinstance(v, list):
        return [_clean(x) for x in v]
    return v


def git_first_commit(path: Path) -> dict | None:
    try:
        out = subprocess.run(["git", "log", "--diff-filter=A", "--format=%H %cI", "--", str(path.relative_to(ROOT))],
                             cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip().splitlines()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    if not out:
        return None
    h, t = out[-1].split(" ", 1)
    return {"commit": h, "committed_at": t}


def _source_id(s: dict) -> str:
    kind = s.get("kind", "other")
    if kind == "nyc-open-data":
        q = hashlib.sha256(jcs(s.get("query") or {}).encode()).hexdigest()[:12]
        return f"socrata:{s.get('dataset')}@{s.get('rows_updated_at')}#{q}"
    if kind == "sysgraph":
        return "system-api:v1.0#" + hashlib.sha256(jcs(s).encode()).hexdigest()[:12]
    return f"{kind}:" + hashlib.sha256(jcs(s).encode()).hexdigest()[:16]


def source_record(s: dict) -> dict:
    kind = s.get("kind", "other")
    d = {"kind": kind, "raw": s}
    if kind == "nyc-open-data":
        d.update({"dataset": s.get("dataset"), "name": s.get("name"), "url": s.get("url"),
                  "version": s.get("rows_updated_at"), "version_basis": "Socrata rowsUpdatedAt at fetch time",
                  "query": s.get("query"), "fetched": s.get("fetched"), "n_rows": s.get("n_rows")})
    elif kind == "sysgraph":
        d.update({"name": "System Public Graph API", "url": "https://public-api.system.com",
                  "version": "v1.0 (no data version id; responses carry no version)",
                  "version_basis": "API version string only"})
    elif kind == "noaa":
        d.update({"name": s.get("name") or s.get("station"), "url": s.get("url"),
                  "version": s.get("last_modified") or s.get("Last-Modified"),
                  "version_basis": "HTTP Last-Modified of the NCEI file", "fetched": s.get("fetched")})
    else:
        d.update({"name": s.get("name"), "url": s.get("url"), "version": s.get("version")})
    return _clean(d)


def dataverse_source() -> tuple[str, dict]:
    f = ROOT / "data" / "derived" / "graph_audit" / "dataverse_files.json"
    d = json.loads(f.read_text()) if f.exists() else {}
    files = {x["filename"]: x["sha256"] for x in d.get("files", [])}
    return DATAVERSE_SOURCE_ID, _clean({
        "kind": "dataverse", "name": "System Public Graph", "url": "https://doi.org/10.7910/DVN/7V6JDO",
        "dataset": "doi:10.7910/DVN/7V6JDO", "version": d.get("version", "2.1"),
        "version_basis": "Dataverse dataset version; file SHA-256 from the deposit's MANIFEST.json",
        "release_time": d.get("release_time"), "files_sha256": files or None, "license": d.get("license"),
    })


def in_csv_lookup(ids: list[str]) -> dict:
    if not DB.exists() or not ids:
        return {}
    import duckdb
    con = duckdb.connect(str(DB), read_only=True)
    a = {r[0] for r in con.execute("SELECT system_id FROM associations WHERE system_id IN (SELECT unnest(?))", [ids]).fetchall()}
    r = {r[0] for r in con.execute("SELECT relationship_id FROM relationships WHERE relationship_id IN (SELECT unnest(?))", [ids]).fetchall()}
    return {i: (i in a or i in r) for i in ids}


# --------------------------------------------------------------------------- build

def build() -> list[dict]:
    recs: list[dict] = []
    dv_id, dv = dataverse_source()
    sources = {dv_id: dv}
    regs = {f.stem: json.loads(f.read_text()) for f in sorted(REG.glob("*.json"))}
    outs = {f.stem: json.loads(f.read_text()) for f in sorted(OUTC.glob("*.json"))}

    ge_items = []
    for cid, r in regs.items():
        for i, g in enumerate(r.get("graph_evidence") or []):
            ge_items.append((cid, i, g))
    refs = [g.get("association_id") or g.get("relationship_id") for _, _, g in ge_items]
    import re
    idre = re.compile(r"^[A-Za-z0-9_-]{10}(\|[A-Za-z0-9_-]{10})?$")
    lookup = in_csv_lookup([x for x in refs if x and idre.match(x)])

    for cid, r in regs.items():
        gid_list = []
        for i, g in [(i, g) for c, i, g in ge_items if c == cid]:
            gid = f"{cid}/ge{i}"
            gid_list.append(gid)
            ref = g.get("association_id") or g.get("relationship_id")
            recs.append({"id": gid, "type": "GraphEvidence", "data": _clean({
                "claim": cid,
                "relationship_id": g.get("relationship_id"),
                "association_id": g.get("association_id"),
                "concepts": g.get("concepts"),
                "n_findings": g.get("n_findings"), "n_studies": g.get("n_studies"),
                "direction": g.get("direction"), "summary": g.get("summary") or g.get("note"),
                "pubmed_ids": [str(p) for p in (g.get("pubmed_ids") or [])],
                "in_dataverse_csv": lookup.get(ref),
                "source": dv_id,
                "extra": {k: v for k, v in g.items() if k not in {"relationship_id", "association_id", "concepts",
                          "n_findings", "n_studies", "direction", "summary", "note", "pubmed_ids"}} or None,
            })})
        commit = git_first_commit(REG / f"{cid}.json")
        recs.append({"id": cid, "type": "Claim", "data": _clean({
            "kind": r.get("kind"), "statement": r.get("statement"), "prediction": r.get("prediction"),
            "plan": r.get("plan"), "alternatives": r.get("alternatives"), "prior": r.get("prior"),
            "registrant": r.get("registrant"), "registered_at": r.get("registered_at"),
            "registration_sha256": r.get("sha256"), "registration_commit": commit,
            "supersedes": r.get("supersedes"), "chain": r.get("chain") or None,
            "literature": r.get("literature") or None, "graph_evidence": gid_list or None,
        })})

    for cid, o in outs.items():
        sids = []
        for s in o.get("sources") or []:
            sid = _source_id(s)
            sources.setdefault(sid, source_record(s))
            sids.append(sid)
        rn_ids = []
        for i, n in enumerate(o.get("research_needed") or []):
            nid = f"{cid}/need{i}"
            rn_ids.append(nid)
            recs.append({"id": nid, "type": "ResearchNeed", "data": _clean({"outcome": cid, **n})})
        recs.append({"id": cid, "type": "Outcome", "data": _clean({
            "claim": cid, "verdict": o.get("verdict"), "city_effect": o.get("city_effect"),
            "graph_effect": o.get("graph_effect"), "stance": o.get("stance"),
            "prediction_scored": o.get("prediction_scored"), "settle": o.get("settle"),
            "notes": o.get("notes"), "figures": o.get("figures"), "decided_at": o.get("decided_at"),
            "registration_sha256": o.get("registration_sha256"),
            "outcome_commit": git_first_commit(OUTC / f"{cid}.json"),
            "sources": sids, "graph_source": dv_id, "research_needed": rn_ids or None,
        })})
    for sid, d in sources.items():
        recs.append({"id": sid, "type": "Source", "data": d})
    return recs


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--check", action="store_true", help="validate records against the schemas (jsonschema)")
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    schemas = json.loads(SCHEMA.read_text())
    recs = build()
    bad = [r for r in recs if r["type"] not in schemas]
    if bad:
        raise SystemExit(f"records of unknown type: {sorted({r['type'] for r in bad})}")
    if a.check:
        try:
            import jsonschema
        except ImportError:
            print("jsonschema not installed; skipping --check")
        else:
            errs = 0
            for r in recs:
                for e in jsonschema.Draft7Validator(schemas[r["type"]]).iter_errors(r["data"]):
                    errs += 1
                    print(f"{r['type']} {r['id']}: {e.message[:200]}")
            print(f"schema check: {errs} errors in {len(recs)} records")
    with (out / "records.jsonl").open("w") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    (out / "schemas.json").write_text(json.dumps(schemas, indent=1))
    manifest = {"protocol": "underlay v2 (record hash per docs/protocol/records)",
                "counts": {t: sum(r["type"] == t for r in recs) for t in schemas},
                "records": [{"type": r["type"], "id": r["id"], "hash": record_hash(r["id"], r["type"], r["data"])}
                            for r in recs]}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1))
    (out / "push_session.json").write_text(json.dumps({
        "base": None, "message": "nyc-concordance claim register", "app_id": "nyc-concordance",
        "metadata": {"description": "Preregistered claims and outcomes comparing the System Public Graph with "
                                    "New York City open data (System hackathon, Build Challenge 4).",
                     "license": "to be decided"},
        "schemas": schemas}, indent=1))
    print(f"{len(recs)} records: {manifest['counts']}")
    print(f"wrote {out.relative_to(ROOT) if out.is_relative_to(ROOT) else out}/records.jsonl, schemas.json, manifest.json, push_session.json")
    print("Nothing was published. To publish, Jeff needs an Underlay account and a write key; see docs/graph.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
