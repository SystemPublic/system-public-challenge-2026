#!/usr/bin/env python
"""Export the claim register as an Underlay collection.

Default: the collection `nyc-concordance-claims`, three record types, written to
data/derived/underlay_publish/claims/ for analyses/underlay_publish/push.py --collection claims:

  Claim     one per registration in claims/registered/ (all of them, with or without an
            outcome): the registration as registered, the exact text of its file, its sha256,
            the commit that added it, the prereg/<id> branch on the remote, the lineage-audit
            class (data/derived/lineage_audit.json) and the replication package if one exists
            (replication/<id>/manifest.json and verify_result.json)
  Outcome   one per file in claims/outcomes/: the current verdict, city_effect, sources with
            their dataset versions, stance, notes_referee, the referee report, and the placebo
            estimate and referee's value from viz/data/annotations.json
  Revision  one per entry of an outcome's `history`: the outcome as it stood before the
            revision, with the reason and the critique path. The outcome file keeps only the
            last revision's reason; earlier ones are read from the git history of the file.

  records.ndjson, record_hashes.tsv, schemas.json, readme.md, collection.json, manifest.json

Nothing is published by this script. --graph-audit writes the older five-type export
(Claim, Outcome, GraphEvidence, Source, ResearchNeed; schemas in tools/underlay_schema.json)
to data/derived/graph_audit/underlay/.

Record hashes follow the Underlay record-hashing rule: SHA-256 over
'{"id":' + JSON(id) + ',"type":' + JSON(type) + ',"data":' + JCS(data) + '}', with
JCS = RFC 8785 canonical JSON. Numbers are written as ECMAScript writes them.

Usage:
  ~/.venvs/nyc-concordance/bin/python tools/underlay_export.py            (validates; needs jsonschema)
  ~/.venvs/nyc-concordance/bin/python tools/underlay_export.py --graph-audit [--out DIR] [--check]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
import time
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REG = ROOT / "claims" / "registered"
OUTC = ROOT / "claims" / "outcomes"
SCHEMA = ROOT / "tools" / "underlay_schema.json"
DEFAULT_OUT = ROOT / "data" / "derived" / "graph_audit" / "underlay"
COLLECTION_OUT = ROOT / "data" / "derived" / "underlay_publish" / "claims"
DB = Path.home() / "opt" / "nyc-concordance" / "dataverse" / "graph.duckdb"
DATAVERSE_SOURCE_ID = "dataverse:doi:10.7910/DVN/7V6JDO@2.1"
OWNER = "system-community"
SLUG = "nyc-concordance-claims"
PR_URL = "https://github.com/SystemPublic/system-public-challenge-2026/pull/3"
PR_PREFIX = "projects/hypergraph/"
SERIOUS = ["d", "e", "c", "a", "b", "f"]  # docs/lineage_audit.md, most serious first
CLASS_TEXT = {
    "a": "exposure or treatment only, not the outcome",
    "b": "a design, power or calibration read, pre-period data, or metadata",
    "c": "a shared cache: the query was fetched for an earlier claim and holds this claim's outcome",
    "d": "the outcome data were read for this claim before registration",
    "e": "cannot tell",
    "f": "no early read of city data (date-only or misparsed fetch time, or a published benchmark)",
    "none": "the audit found no city-data source fetched before registration",
}


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

def build_graph_audit() -> list[dict]:
    recs: list[dict] = []
    dv_id, dv = dataverse_source()
    sources = {dv_id: dv}
    regs = {f.stem: json.loads(f.read_text()) for f in sorted(REG.glob("*.json"))}
    outs = {f.stem: json.loads(f.read_text()) for f in sorted(OUTC.glob("*.json"))}

    ge_items = []
    for cid, r in regs.items():
        for i, g in enumerate(r.get("graph_evidence") or []):
            ge_items.append((cid, i, g))
    def _ref(g):
        x = g.get("association_id") or g.get("relationship_id")
        return x if isinstance(x, str) else None  # some registrations give a list of ids
    refs = [_ref(g) for _, _, g in ge_items]
    import re
    idre = re.compile(r"^[A-Za-z0-9_-]{10}(\|[A-Za-z0-9_-]{10})?$")
    lookup = in_csv_lookup([x for x in refs if x and idre.match(x)])

    for cid, r in regs.items():
        gid_list = []
        for i, g in [(i, g) for c, i, g in ge_items if c == cid]:
            gid = f"{cid}/ge{i}"
            gid_list.append(gid)
            ref = _ref(g)
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



# --------------------------------------------------------------------------- the published collection

def _git(*args) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout


def _nonan(v, where=""):
    """Outcomes are kept as written (nulls included); only NaN and Infinity, which are not JSON, become null."""
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    if isinstance(v, dict):
        return {k: _nonan(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_nonan(x) for x in v]
    return v


def _drop_none(d: dict) -> dict:
    return {k: v for k, v in d.items() if v is not None}


def prereg_branches() -> dict:
    """{claim id: sha} for refs/heads/prereg/* on origin (git ls-remote; falls back to local remote refs)."""
    try:
        out = subprocess.run(["git", "ls-remote", "origin", "refs/heads/prereg/*"], cwd=ROOT, capture_output=True,
                             text=True, check=True, timeout=60).stdout
        return {ln.split("\t")[1].removeprefix("refs/heads/prereg/"): ln.split("\t")[0] for ln in out.splitlines()}
    except Exception:
        out = _git("for-each-ref", "--format=%(objectname)\t%(refname)", "refs/remotes/origin/prereg")
        return {ln.split("\t")[1].removeprefix("refs/remotes/origin/prereg/"): ln.split("\t")[0]
                for ln in out.splitlines()}


def revisions_in_git(cid: str) -> list[dict]:
    """Every distinct `revision` the outcome file has held, oldest first, each with the commit that first shows it."""
    rel = f"claims/outcomes/{cid}.json"
    commits = _git("log", "--reverse", "--format=%H", "--", rel).split()
    seen, out = set(), []
    for c in commits:
        try:
            o = json.loads(_git("show", f"{c}:{rel}"))
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            continue
        r = o.get("revision")
        if isinstance(r, dict) and r.get("revised_at") not in seen:
            seen.add(r.get("revised_at"))
            out.append(dict(r, _commit=c, _n_history=len(o.get("history") or [])))
    return out


OUTCOME_NAMED = ["verdict", "city_effect", "graph_effect", "stance", "prediction_scored", "settle", "notes",
                 "notes_referee", "verdict_note", "stance_note", "sources", "research_needed", "figures",
                 "decided_at", "registration_sha256", "critique"]


def build_collection() -> tuple[list[dict], dict]:
    regs = {f.stem: f for f in sorted(REG.glob("*.json"))}
    outs = {f.stem: json.loads(f.read_text()) for f in sorted(OUTC.glob("*.json"))}
    lineage = json.loads((ROOT / "data" / "derived" / "lineage_audit.json").read_text())
    ann = json.loads((ROOT / "viz" / "data" / "annotations.json").read_text())["claims"]
    branches = prereg_branches()
    recs, notes = [], {"revision_reasons_from_git": 0, "revision_reasons_missing": []}

    for cid, f in regs.items():
        text = f.read_text(encoding="utf-8")
        r = json.loads(text)
        body = {k: v for k, v in r.items() if k not in ("sha256", "registered_at")}
        if hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest() != r.get("sha256"):
            raise SystemExit(f"{cid}: registration does not match its sha256")
        early = lineage.get(cid) or []
        classes = sorted({e["class"] for e in early}, key=SERIOUS.index)
        lin = {"class": classes[0] if classes else "none",
               "class_meaning": CLASS_TEXT[classes[0] if classes else "none"],
               "classes": classes, "early_sources": early,
               "audit": "docs/lineage_audit.md; data/derived/lineage_audit.json"}
        d = {"kind": r["kind"], "statement": r["statement"],
             "prior": r.get("prior") if isinstance(r.get("prior"), (int, float)) else None,
             "registrant": r.get("registrant"), "registered_at": r["registered_at"],
             "registration_sha256": r["sha256"],
             "registration_file_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
             "registration_path": f"claims/registered/{cid}.json",
             "registration_commit": git_first_commit(f),
             "prereg_branch": ({"name": f"prereg/{cid}", "sha": branches[cid]} if cid in branches else None),
             "supersedes": r.get("supersedes"),
             "has_outcome": cid in outs, "outcome": cid if cid in outs else None,
             "lineage": lin, "registration": _nonan(r), "registration_text": text}
        man = ROOT / "replication" / cid / "manifest.json"
        if man.exists():
            m = json.loads(man.read_text())
            vr = ROOT / "replication" / cid / "verify_result.json"
            v = json.loads(vr.read_text()) if vr.exists() else {}
            dec = m.get("deciding") or {}
            d["replication"] = _drop_none({
                "package": f"replication/{cid}/", "manifest": f"replication/{cid}/manifest.json",
                "manifest_sha256": hashlib.sha256(man.read_bytes()).hexdigest(),
                "built_at": (m.get("package") or {}).get("built_at"),
                "status": v.get("status"), "checked_at": v.get("checked_at"),
                "status_from": f"replication/{cid}/verify_result.json" if v else None,
                "deciding_number": dec.get("what"), "decides": dec.get("decides"),
                "recorded": _nonan(dec.get("recorded")), "tolerance": _nonan(dec.get("tolerance")),
                "inputs_copied": (v.get("inputs") or {}).get("copied"),
                "tables_not_rebuilt": len(m.get("not_rebuilt") or [])})
        recs.append({"id": cid, "type": "Claim", "data": _drop_none(d)})

    for cid, o in outs.items():
        o = _nonan(o)
        hist = o.get("history") or []
        rev_ids = [f"{cid}/r{i + 1}" for i in range(len(hist))]
        a = ann.get(cid) or {}
        rep = ROOT / "critique" / f"{cid}.md"
        crit = o.get("critique") if isinstance(o.get("critique"), dict) else None
        d = {"claim": cid}
        for k in OUTCOME_NAMED:
            d[k] = o.get(k)
        d["critique"] = crit
        d["referee_report"] = ({"path": f"critique/{cid}.md", "sha256": hashlib.sha256(rep.read_bytes()).hexdigest()}
                               if rep.exists() else None)
        d["placebo_estimate"] = a.get("placebo")
        d["referee_value"] = a.get("referee")
        d["outcome_path"] = f"claims/outcomes/{cid}.json"
        d["outcome_file_sha256"] = hashlib.sha256((OUTC / f"{cid}.json").read_bytes()).hexdigest()
        d["outcome_commit"] = git_first_commit(OUTC / f"{cid}.json")
        d["revisions"] = rev_ids
        d["last_revision"] = o.get("revision")
        extra = {k: v for k, v in o.items() if k not in set(OUTCOME_NAMED) | {"id", "history", "revision"}}
        d["extra"] = extra or None
        recs.append({"id": cid, "type": "Outcome", "data": _drop_none(d)})

        if not hist:
            continue
        gitrev = revisions_in_git(cid)
        # revision k turned history[k-1] into the next state; the file's own `revision` is the last one
        by_seq = {}
        if len(gitrev) == len(hist):
            by_seq = {i + 1: g for i, g in enumerate(gitrev)}
        else:
            for g in gitrev:
                if 1 <= g["_n_history"] <= len(hist):
                    by_seq.setdefault(g["_n_history"], g)
        for i, h in enumerate(hist):
            seq = i + 1
            last = seq == len(hist)
            after = (hist[i + 1] if not last else o).get("verdict")
            rv = o.get("revision") if last else None
            src = "the outcome file's `revision` field"
            if rv is None and seq in by_seq:
                rv = by_seq[seq]
                src = f"git history of {d['outcome_path']} (commit {rv['_commit']})"
                notes["revision_reasons_from_git"] += 1
            if rv is None:
                notes["revision_reasons_missing"].append(f"{cid}/r{seq}")
                src = "not recorded: a later revision overwrote the field and no commit shows it"
                rv = {}
            recs.append({"id": f"{cid}/r{seq}", "type": "Revision", "data": _drop_none({
                "claim": cid, "seq": seq, "of": len(hist),
                "reason": rv.get("reason"), "critique": rv.get("critique"), "revised_at": rv.get("revised_at"),
                "rule": rv.get("rule"), "reason_source": src,
                "verdict_before": h.get("verdict"), "verdict_after": after,
                "verdict_changed": h.get("verdict") != after,
                "before": h})})
    return recs, notes


_OBJ = {"type": "object"}
_COMMIT = {"type": "object", "required": ["commit", "committed_at"], "additionalProperties": False,
           "properties": {"commit": {"type": "string", "pattern": "^[0-9a-f]{40}$"},
                          "committed_at": {"type": "string"}}}
_SHA = {"type": "string", "pattern": "^[0-9a-f]{64}$"}
_VERDICT = {"enum": ["confirmed", "contested", "unsettled", "bridged", "no_test"]}
_EFFECT = {"type": ["object", "null"], "description": "{label, estimate, lo, hi, scale, null (the no-effect value), n}",
           "properties": {"label": {"type": ["string", "null"]}, "estimate": {"type": ["number", "null"]},
                          "lo": {"type": ["number", "null"]}, "hi": {"type": ["number", "null"]},
                          "scale": {"type": ["string", "null"]}}}

COLLECTION_SCHEMAS = {
    "Claim": {
        "$schema": "http://json-schema.org/draft-07/schema#", "title": "Claim", "type": "object",
        "description": "A hypothesis registered before the city data that test it were read. The id is the claim id.",
        "additionalProperties": False,
        "required": ["kind", "statement", "registered_at", "registration_sha256", "registration_file_sha256",
                     "registration_path", "has_outcome", "lineage", "registration", "registration_text"],
        "properties": {
            "kind": {"enum": ["confirmation", "conflict", "bridge", "reproduction"]},
            "statement": {"type": "string"},
            "prior": {"type": "number", "minimum": 0, "maximum": 1,
                      "description": "Registrant's probability of a confirmed verdict; absent where the registration gives none or gives text."},
            "registrant": {"type": "string"},
            "registered_at": {"type": "string", "description": "Time written into the registration file when it was hashed."},
            "registration_sha256": dict(_SHA, description="The registration's own sha256 field: SHA-256 of Python json.dumps(registration without sha256 and registered_at, sort_keys=True). Recompute it from registration_text."),
            "registration_file_sha256": dict(_SHA, description="SHA-256 of registration_text as UTF-8 bytes, which are the bytes of the file."),
            "registration_path": {"type": "string", "description": "Path in the repository."},
            "registration_commit": dict(_COMMIT, description="The git commit that added the registration file on main."),
            "prereg_branch": {"type": "object", "required": ["name", "sha"], "additionalProperties": False,
                              "description": "The prereg/<id> branch on the remote, pushed at registration. Absent for claims registered before the project pushed such branches.",
                              "properties": {"name": {"type": "string"}, "sha": {"type": "string", "pattern": "^[0-9a-f]{40}$"}}},
            "supersedes": {"type": "string", "description": "Id of the Claim this registration replaces."},
            "has_outcome": {"type": "boolean"},
            "outcome": {"type": "string", "description": "Id of the Outcome record (the same as the claim id)."},
            "lineage": {"type": "object", "required": ["class", "class_meaning", "classes", "early_sources"],
                        "additionalProperties": False,
                        "description": "Result of the audit of data fetched before registration.",
                        "properties": {"class": {"enum": ["a", "b", "c", "d", "e", "f", "none"],
                                                 "description": "Most serious class among the claim's early fetches, in the order d, e, c, a, b, f; none if the audit found no early fetch."},
                                       "class_meaning": {"type": "string"},
                                       "classes": {"type": "array", "items": {"enum": ["a", "b", "c", "d", "e", "f"]}},
                                       "early_sources": {"type": "array", "items": {
                                           "type": "object", "required": ["dataset", "fetched", "class", "evidence"]}},
                                       "audit": {"type": "string"}}},
            "replication": {"type": "object", "required": ["package", "manifest", "manifest_sha256"],
                            "description": "The claim's replication package, if one was built: copies of the inputs, the code and a rerun of the deciding number.",
                            "properties": {"package": {"type": "string"}, "manifest": {"type": "string"},
                                           "manifest_sha256": _SHA, "built_at": {"type": "string"},
                                           "status": {"enum": ["MATCH", "DRIFT", "MISMATCH", "NO_RERUN"]},
                                           "checked_at": {"type": "string"}, "status_from": {"type": "string"},
                                           "deciding_number": {"type": "string"}, "decides": {"type": "string"},
                                           "recorded": _OBJ, "tolerance": _OBJ,
                                           "inputs_copied": {"type": "integer"},
                                           "tables_not_rebuilt": {"type": "integer"}}},
            "registration": {"type": "object", "required": ["id", "kind", "statement", "prediction", "plan", "sha256"],
                             "description": "The registration file, parsed. Field names are the registrant's; prediction holds direction, magnitude, support_if and refute_if."},
            "registration_text": {"type": "string", "description": "The exact text of the registration file."},
        }},
    "Outcome": {
        "$schema": "http://json-schema.org/draft-07/schema#", "title": "Outcome", "type": "object",
        "description": "The current verdict on a Claim, scored against its registration. The id is the claim id.",
        "additionalProperties": False,
        "required": ["claim", "verdict", "sources", "prediction_scored", "settle", "notes", "registration_sha256",
                     "decided_at", "revisions", "outcome_path", "outcome_file_sha256"],
        "properties": {
            "claim": {"type": "string", "description": "Id of the Claim."},
            "verdict": _VERDICT,
            "city_effect": dict(_EFFECT), "graph_effect": dict(_EFFECT),
            "stance": {"type": "object", "description": "Agreement of the city evidence with the research direction, in [-1, 1], with an interval where one is defined.",
                       "properties": {"value": {"type": ["number", "null"]}, "lo": {"type": ["number", "null"]},
                                      "hi": {"type": ["number", "null"]}}},
            "prediction_scored": {"type": "string"}, "settle": {"type": "string"}, "notes": {"type": "string"},
            "notes_referee": {"type": "string", "description": "What the referee reproduced or found."},
            "verdict_note": {}, "stance_note": {},
            "sources": {"type": "array", "description": "Source records. An NYC Open Data source gives the dataset id, rows_updated_at, the query and the fetch time.",
                        "items": {"type": "object"}},
            "research_needed": {"type": "array", "items": {}},
            "figures": {"type": "array", "items": {}},
            "decided_at": {"type": "string"},
            "registration_sha256": dict(_SHA, description="The sha256 of the registration the outcome was scored against."),
            "critique": {"type": "object", "description": "{report, answer}: the referee report's path and the answer to it."},
            "referee_report": {"type": "object", "required": ["path", "sha256"], "additionalProperties": False,
                               "properties": {"path": {"type": "string"}, "sha256": _SHA}},
            "placebo_estimate": {"type": "object", "description": "From viz/data/annotations.json: {est, lo, hi, registered, label, src}, in city_effect units. registered says whether the placebo was named in the registration.",
                                 "properties": {"est": {"type": ["number", "null"]}, "lo": {"type": ["number", "null"]},
                                                "hi": {"type": ["number", "null"]}, "registered": {"type": "boolean"},
                                                "label": {"type": "string"}, "src": {"type": "string"}}},
            "referee_value": {"type": "object", "description": "From viz/data/annotations.json: {v, label, src}, the referee's own value in city_effect units.",
                              "properties": {"v": {"type": ["number", "null"]}, "label": {"type": "string"},
                                             "src": {"type": "string"}}},
            "outcome_path": {"type": "string"}, "outcome_file_sha256": _SHA,
            "outcome_commit": dict(_COMMIT, description="The git commit that added the outcome file."),
            "revisions": {"type": "array", "items": {"type": "string"}, "description": "Ids of the Revision records, oldest first."},
            "last_revision": {"type": "object", "description": "{reason, critique, revised_at, rule} of the latest revision."},
            "extra": {"type": "object", "description": "Other fields of the outcome file, under the names the analyst gave them."},
        }},
    "Revision": {
        "$schema": "http://json-schema.org/draft-07/schema#", "title": "Revision", "type": "object",
        "description": "One change to an Outcome after criticism. The id is <claim id>/r<seq>.",
        "additionalProperties": False,
        "required": ["claim", "seq", "of", "reason_source", "verdict_before", "verdict_after", "verdict_changed", "before"],
        "properties": {
            "claim": {"type": "string"}, "seq": {"type": "integer", "minimum": 1}, "of": {"type": "integer", "minimum": 1},
            "reason": {"type": "string"},
            "critique": {"type": "string", "description": "Path of the referee report that led to the revision."},
            "revised_at": {"type": "string"},
            "rule": {"type": "string"},
            "reason_source": {"type": "string", "description": "Where the reason was read from."},
            "verdict_before": _VERDICT, "verdict_after": _VERDICT, "verdict_changed": {"type": "boolean"},
            "before": {"type": "object", "description": "The outcome's verdict, city_effect, stance, decided_at and prediction_scored before this revision."},
        }},
}


def collection_readme(counts, stats, head, claims_commit) -> str:
    v = stats["verdicts"]
    lc = stats["lineage"]
    return f"""# NYC Concordance: registered claims and their outcomes

This collection holds the claim register of team Hypergraph (Jeff Nickerson and Ida Benedetto) for the System Public Challenge of November 2026, Build Challenge 4. The challenge asks what published research, as held in the System Public Graph, and New York City's own data can confirm, question and connect. Each claim is a prediction about city data that was written down and committed before the data were read. The collection belongs to the Underlay organization `{OWNER}` (System Inc. Community), where the challenge's teams publish their work.

| Type | Records | Id |
|---|---|---|
| Claim | {counts['Claim']} | the claim id, for example `heat-shootings` |
| Outcome | {counts['Outcome']} | the claim id |
| Revision | {counts['Revision']} | claim id, `/r` and a sequence number, for example `heat-shootings/r1` |

One claim, `construction-2022-rush-units-2027`, has no outcome yet: it is a prospective claim about completions by 30 June 2027. The current verdicts are {v.get('confirmed', 0)} confirmed, {v.get('contested', 0)} contested, {v.get('unsettled', 0)} unsettled, {v.get('bridged', 0)} bridged and {v.get('no_test', 0)} no_test.

## Registration before data

A registration states the hypothesis, the research evidence, the predicted direction and size, what result would support it (`support_if`), what result would refute it (`refute_if`), the rival explanations and the registrant's prior. It was written before any city data were queried for the claim. The registering code wrote the time and a hash into the file, and the file was committed at once. A registration is never edited. A changed plan is a new claim that names the old one in `supersedes`.

A Claim record gives four ways to check the order. `registration_text` is the exact text of the file and `registration_file_sha256` is the SHA-256 of that text. `registration_sha256` is the hash the code wrote into the file: the SHA-256 of Python's `json.dumps(d, sort_keys=True)`, where `d` is the parsed file without its `sha256` and `registered_at` fields. Every Outcome repeats the hash of the registration it was scored against. `registration_commit` is the git commit that added the file. `prereg_branch` is a branch named `prereg/<id>` that was pushed to the remote at registration, with its commit; {stats['with_branch']} of the {counts['Claim']} claims have one, and the others were registered before the project pushed such branches.

## Verdicts

An Outcome's `verdict` is confirmed, contested, unsettled, bridged or no_test. The rules are the text `PRECEDENCE` in `concord/claims.py`, at commit `{claims_commit}` of the working repository. Rule 1: the registration's own `support_if` and `refute_if` decide the verdict when they are met, even when the city interval includes zero. Rule 2: when neither is met, the verdict is unsettled. Rule 3: when the registered test could not be run as planned, the verdict is no_test. Rule 4: a measure chosen after the data were seen never decides a verdict. Later rules cover bridges (the stance of a chain is that of its weakest link), the cases where no stance is defined, and placebos (when a registered placebo shows an effect as large as the estimate, the verdict is unsettled). Rules added after the first verdicts say so in the text and name the verdicts they changed.

`city_effect` is the estimate that was scored, with its interval, scale and no-effect value. `stance` is a number between -1 and 1 for the agreement of the city evidence with the research direction. `sources` lists the data each outcome rests on. A New York City Open Data source gives the dataset id, `rows_updated_at`, the exact query and the fetch time. The city rewrites many tables daily, so `rows_updated_at` names a table state that the city no longer publishes.

## Referees and revisions

Outcomes were given to an independent referee, an agent that had not done the analysis and that reran the deciding number where it could. `referee_report` gives the report's path and SHA-256, `critique` gives the answer, and `notes_referee` gives what the referee found, where it was recorded. {stats['with_report']} of the {counts['Outcome']} outcomes have a referee report. `placebo_estimate` ({stats['with_placebo']} outcomes) and `referee_value` ({stats['with_referee_value']} outcomes) are in the units of `city_effect`; `placebo_estimate.registered` says whether the placebo was named in the registration.

A Revision record is one change to an outcome after criticism. `before` holds the verdict, city effect, stance and scoring as they stood, and `reason` and `critique` say why the outcome changed and which report led to it. Of the {counts['Revision']} revisions, {stats['verdict_changed']} changed the verdict. The outcome file keeps the reason of its latest revision only; {stats['from_git']} earlier reasons were read from the git history of the file{stats['missing_text']}.

## Lineage audit

An audit on 13 November 2026 compared the fetch time of every city-data source with the time of registration (`docs/lineage_audit.md`). In {stats['audited']} claims at least one source was fetched before the claim was registered. `lineage.class` gives the most serious class among a claim's early fetches, and `lineage.early_sources` gives each one with the evidence for its class.

| Class | Meaning | Claims |
|---|---|---|
| d | the outcome data were read for this claim before registration | {lc.get('d', 0)} |
| e | cannot tell | {lc.get('e', 0)} |
| c | a shared cache: the query was fetched for an earlier claim and holds this claim's outcome | {lc.get('c', 0)} |
| a | exposure or treatment only, not the outcome | {lc.get('a', 0)} |
| b | a design, power or calibration read, pre-period data, or metadata | {lc.get('b', 0)} |
| f | no early read of city data (a date-only or misparsed fetch time, or a published benchmark) | {lc.get('f', 0)} |
| none | the audit found no early fetch | {lc.get('none', 0)} |

Two claims read their outcome data first. For `afford-gentrification-prevalence` (confirmed), a faulty simulation multiplied the real later-year values by noise and the registrant read its output; the registration discloses this. For `heat-extremes-downturn` (contested), the four deciding series were built before registration; the registrant states that only yearly totals and mean daily counts were read. A fetch time shows that the data were on disk. It does not show whether anyone looked at them.

## Replication packages

{stats['with_replication']} claims have a replication package, named in the Claim's `replication` field. A package copies the inputs of the deciding number, pins each by SHA-256, and reruns the number from the copies. `status` is the result of that rerun: MATCH means the rerun gave the recorded number within the stated tolerance. All {stats['match']} packages gave MATCH when checked on 13 November 2026 (`docs/replication.md`).

## Code and provenance

The code, the register, the referee reports and the replication packages are in the public pull request {PR_URL}, under `{PR_PREFIX}`. Paths in the records are relative to that folder. The working repository, nyc-concordance on GitHub, is private for now; the commit hashes and `prereg/` branches in the records refer to it and can be checked when it is opened. This version was built by `tools/underlay_export.py` at commit `{head}` of the working repository.

## Licence

The registrations, outcomes and reports are the team's own work and are offered under CC BY 4.0. The city data they describe are public records of the City of New York and are not included here. The System Public Graph, which the registrations quote, is licensed CC BY-NC 4.0 by System Inc.
"""


def write_collection(out: Path) -> int:
    import jsonschema
    status = _git("status", "--porcelain", "--", "claims", "tools/underlay_export.py", "concord/claims.py",
                  "data/derived/lineage_audit.json", "viz/data/annotations.json", "replication").strip()
    if status:
        raise SystemExit("commit these first, so that the build commit names what was exported:\n" + status)
    head = _git("rev-parse", "HEAD").strip()
    claims_commit = _git("log", "-1", "--format=%H", "--", "concord/claims.py").strip()
    recs, notes = build_collection()
    schemas = COLLECTION_SCHEMAS
    for t, sc in schemas.items():
        jsonschema.Draft7Validator.check_schema(sc)
    errs, seen = [], set()
    for r in recs:
        if (r["type"], r["id"]) in seen:
            errs.append(f"duplicate {r['type']} {r['id']}")
        seen.add((r["type"], r["id"]))
        for e in jsonschema.Draft7Validator(schemas[r["type"]]).iter_errors(r["data"]):
            errs.append(f"{r['type']} {r['id']}: {'/'.join(map(str, e.path))} {e.message[:160]}")
    ids = {t: {r["id"] for r in recs if r["type"] == t} for t in schemas}
    for r in recs:
        d = r["data"]
        if r["type"] != "Claim" and d["claim"] not in ids["Claim"]:
            errs.append(f"{r['type']} {r['id']}: no Claim {d['claim']}")
        if r["type"] == "Claim" and d.get("supersedes") and d["supersedes"] not in ids["Claim"]:
            errs.append(f"Claim {r['id']}: supersedes unknown {d['supersedes']}")
        if r["type"] == "Outcome":
            errs += [f"Outcome {r['id']}: no Revision {x}" for x in d["revisions"] if x not in ids["Revision"]]
            c = next(x for x in recs if x["type"] == "Claim" and x["id"] == d["claim"])["data"]
            if c["registration_sha256"] != d["registration_sha256"]:
                errs.append(f"Outcome {r['id']}: registration_sha256 differs from the Claim's")
    if errs:
        print("\n".join(errs[:60]))
        raise SystemExit(f"{len(errs)} validation errors; nothing written")

    counts = {t: sum(r["type"] == t for r in recs) for t in schemas}
    claims = [r["data"] for r in recs if r["type"] == "Claim"]
    outc = [r["data"] for r in recs if r["type"] == "Outcome"]
    revs = [r["data"] for r in recs if r["type"] == "Revision"]
    from collections import Counter
    missing = notes["revision_reasons_missing"]
    stats = {"verdicts": dict(Counter(o["verdict"] for o in outc)),
             "lineage": dict(Counter(c["lineage"]["class"] for c in claims)),
             "audited": sum(c["lineage"]["class"] != "none" for c in claims),
             "with_branch": sum("prereg_branch" in c for c in claims),
             "with_report": sum("referee_report" in o for o in outc),
             "with_placebo": sum("placebo_estimate" in o for o in outc),
             "with_referee_value": sum("referee_value" in o for o in outc),
             "with_replication": sum("replication" in c for c in claims),
             "match": sum(c.get("replication", {}).get("status") == "MATCH" for c in claims),
             "verdict_changed": sum(r["verdict_changed"] for r in revs),
             "from_git": notes["revision_reasons_from_git"], "reasons_missing": missing,
             "missing_text": (f", and {len(missing)} could not be recovered and have no `reason`" if missing else "")}
    readme = collection_readme(counts, stats, head, claims_commit)
    desc = ("Preregistered claims comparing the System Public Graph with New York City open data: each registration "
            "with its sha256, the outcomes, their revisions, referee reports, lineage audit and replication status.")
    collection = {"slug": SLUG, "name": "NYC Concordance: registered claims and outcomes", "public": True,
                  "description": desc,
                  "message": f"{counts['Claim']} claims, {counts['Outcome']} outcomes, {counts['Revision']} revisions; register at {head[:12]}",
                  "app_id": "nyc-concordance/underlay_export",
                  "metadata": {"description": desc, "license": "CC BY 4.0 (registrations, outcomes and reports)",
                               "tags": ["Research", "Government"], "buildCommit": head,
                               "verdictRules": f"concord/claims.py PRECEDENCE at {claims_commit}",
                               "code": PR_URL, "codePath": PR_PREFIX}}
    out.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(r, ensure_ascii=False) for r in recs]
    blob = ("\n".join(lines) + "\n").encode("utf-8")
    (out / "records.ndjson").write_bytes(blob)
    hashes = [(r["type"], r["id"], record_hash(r["id"], r["type"], r["data"])) for r in recs]
    (out / "record_hashes.tsv").write_text("type\tid\thash\n" + "".join(f"{t}\t{i}\t{h}\n" for t, i, h in hashes))
    (out / "schemas.json").write_text(json.dumps(schemas, indent=1))
    (out / "readme.md").write_text(readme)
    (out / "collection.json").write_text(json.dumps(collection, indent=1))
    want = {"Claim": ["heat-shootings", "afford-gentrification-prevalence", "construction-2022-rush-units-2027"],
            "Outcome": ["heat-shootings", "rlc-expansion-rearend", "heat-extremes-downturn"],
            "Revision": [next((i for t, i, _ in hashes if t == "Revision"), None),
                         "bridge-crz-injury-crashes/r1", "rlc-expansion-rearend/r1"]}
    sample = [{"type": t, "id": i, "hash": h} for t, i, h in hashes if i in want.get(t, [])]
    manifest = {"collection_slug": SLUG, "owner": OWNER, "build_commit": head,
                "built": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "verdict_rules": {"file": "concord/claims.py", "name": "PRECEDENCE", "commit": claims_commit},
                "counts": counts, "total_records": len(recs),
                "records_file": "data/derived/underlay_publish/claims/records.ndjson",
                "records_sha256": hashlib.sha256(blob).hexdigest(), "records_bytes": len(blob),
                "schema_hashes": {t: hashlib.sha256(jcs(sc).encode()).hexdigest() for t, sc in schemas.items()},
                "validation": {"schema_errors": 0, "duplicate_ids": 0, "references_resolve": True,
                               "registration_hashes_recomputed": counts["Claim"]},
                "stats": {k: v for k, v in stats.items() if k != "missing_text"},
                "sample_hashes": sample}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1))
    print(f"{len(recs)} records: {counts}; {len(blob):,} bytes; 0 validation errors")
    print(json.dumps(manifest["stats"]))
    print(f"wrote {out.relative_to(ROOT)}/; nothing was published")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--graph-audit", action="store_true", help="write the older five-type export instead")
    ap.add_argument("--out", default=None)
    ap.add_argument("--check", action="store_true", help="with --graph-audit: validate records (jsonschema)")
    a = ap.parse_args(argv)
    if not a.graph_audit:
        return write_collection(Path(a.out) if a.out else COLLECTION_OUT)
    out = Path(a.out or DEFAULT_OUT)
    out.mkdir(parents=True, exist_ok=True)
    schemas = json.loads(SCHEMA.read_text())
    recs = build_graph_audit()
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
    print("Nothing was published.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
