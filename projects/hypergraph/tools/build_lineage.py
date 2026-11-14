#!/usr/bin/env python
"""Build viz/data/lineage.json (git-derived provenance for each claim) and viz/data/evidence.js.

    ~/.venvs/nyc-concordance/bin/python tools/build_lineage.py [--no-remote]

For each claim in viz/data/claims.json the script records, with real timestamps:

  registration   the commit that added claims/registered/<id>.json, and registered_at from the file
  push           when refs/remotes/origin/prereg/<id> was updated by a push (local reflog), else the
                 commit time of the sha the remote branch points at (git ls-remote), else nothing
  sources        each source's fetch time and the dataset's rowsUpdatedAt (outcome.sources); a source whose fetch
                 time precedes registered_at is marked early and carries its class from the hand audit in
                 data/derived/lineage_audit.json (docs/lineage_audit.md): a exposure, b design or pre-period,
                 c shared cache holding the outcome, d outcome read before registration, e cannot tell,
                 f date-only or misparsed time, or a literature benchmark
  outcome        decided_at of the first scored verdict and each commit that changed the outcome file
  referee        the first commit that added critique/<id>.md
  revisions      each entry of outcome.history and outcome.revision with its time and reason
  replication    for claims with replication/<id>/manifest.json: code commit, Python version, package
                 count, cache hashes and the MATCH / DRIFT status in verify_result.json

It then bundles titles.json, annotations.json and lineage.json into evidence.js
(window.CONCORD_EVIDENCE) so that viz/evidence.html works from file://.
Every path written is relative to the repository.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "viz" / "data"
AUDIT = ROOT / "data" / "derived" / "lineage_audit.json"
GRAPH_KINDS = ("sysgraph", "system-public-graph", "literature")


def before(a: str | None, b: str | None) -> bool:
    """True when time a precedes time b (naive times are read as local time, as the page does)."""
    if not a or not b:
        return False
    da, db = datetime.fromisoformat(a), datetime.fromisoformat(b)
    da = da if da.tzinfo else da.astimezone()
    db = db if db.tzinfo else db.astimezone()
    return da < db


def git(*args: str) -> str:
    r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def iso(t: str | None) -> str | None:
    """Normalise a timestamp to ISO 8601 with offset; None if it cannot be read."""
    if not t:
        return None
    s = str(t).strip().replace("Z", "+00:00")
    if len(s) >= 5 and s[-5] in "+-" and s[-3] != ":":
        s = s[:-2] + ":" + s[-2:]
    try:
        return datetime.fromisoformat(s).isoformat()
    except ValueError:
        return None


def commits(path: str, first_only: bool = False) -> list[dict]:
    out = git("log", "--follow", "--format=%H\t%cI\t%s", "--", path)
    rows = []
    for line in out.splitlines():
        h, t, subj = (line.split("\t", 2) + ["", ""])[:3]
        rows.append({"commit": h, "time": iso(t), "subject": subj[:160]})
    rows.reverse()  # oldest first
    return rows[:1] if first_only else rows


def remote_branches(use_remote: bool) -> dict[str, str]:
    refs = {}
    txt = git("ls-remote", "origin", "refs/heads/prereg/*") if use_remote else ""
    if not txt:  # fall back to remote-tracking refs
        txt = git("for-each-ref", "--format=%(objectname)\t%(refname)", "refs/remotes/origin/prereg/")
    for line in txt.splitlines():
        sha, ref = line.split("\t")
        refs[ref.rsplit("prereg/", 1)[1]] = sha
    return refs


def push_time(cid: str) -> str | None:
    out = git("reflog", "show", "--date=iso-strict", f"refs/remotes/origin/prereg/{cid}")
    times = []
    for line in out.splitlines():
        if "update by push" in line and "@{" in line:
            times.append(iso(line.split("@{", 1)[1].split("}", 1)[0]))
    times = [t for t in times if t]
    return min(times) if times else None


def replication(cid: str) -> dict | None:
    d = ROOT / "replication" / cid
    mf = d / "manifest.json"
    if not mf.exists():
        return None
    m = json.loads(mf.read_text())
    vr = d / "verify_result.json"
    v = json.loads(vr.read_text()) if vr.exists() else {}
    env = m.get("environment", {})
    data = []
    for rec in m.get("data", []):
        data.append({"dataset": rec.get("dataset") or rec.get("kind"),
                     "rows_updated_at": rec.get("rows_updated_at"),
                     "fetched": rec.get("fetched"),
                     "cache_sha256": [cf.get("sha256") for cf in rec.get("cache_files", [])][:3]})
    claim = m.get("claim", {})
    return {
        "manifest": f"replication/{cid}/manifest.json",
        "status": v.get("status"),
        "checked_at": v.get("checked_at"),
        "comparison": [{k: x.get(k) for k in ("key", "recorded", "rerun", "within")} for x in v.get("comparison", [])],
        "code_commit": m.get("code", {}).get("repo_commit"),
        "scripts": [{"path": s.get("path"), "blob": s.get("blob"), "first_commit": s.get("first_commit")}
                    for s in m.get("code", {}).get("scripts", [])],
        "python": (env.get("python") or "").split(" ")[0] or None,
        "venv": env.get("venv"),
        "n_packages": len(env.get("uv_pip_freeze", []) or []),
        "registration_hash_ok": claim.get("registration_hash_ok"),
        "data": data,
        "deciding": {k: m.get("deciding", {}).get(k) for k in ("what", "decides", "tolerance")},
    }


def build(use_remote: bool) -> dict:
    claims = json.loads((DATA / "claims.json").read_text())["claims"]
    audit = json.loads(AUDIT.read_text()) if AUDIT.exists() else {}
    unaudited = []
    branches = remote_branches(use_remote)
    out = {}
    for c in claims:
        cid = c["id"]
        o = c.get("outcome") or {}
        reg = commits(f"claims/registered/{cid}.json", first_only=True)
        sha = branches.get(cid)
        push = {"branch": f"prereg/{cid}", "sha": sha, "time": push_time(cid), "basis": None}
        if push["time"]:
            push["basis"] = "local reflog: update by push"
        elif sha:
            push["time"] = iso(git("show", "-s", "--format=%cI", sha)) or None
            push["basis"] = "commit time of the sha the remote branch points at"
        else:
            push["basis"] = "no prereg branch on the remote"
        sources = []
        for s in o.get("sources", []) or []:
            ds = s.get("dataset") or ", ".join(s.get("datasets", []) or []) or s.get("station") or s.get("kind")
            sources.append({"kind": s.get("kind"), "dataset": ds, "name": s.get("name") or s.get("title"),
                            "fetched": iso(s.get("fetched") or s.get("fetched_first")),
                            "rows_updated_at": iso(s.get("rows_updated_at") or s.get("last_modified")),
                            "version": (str(s.get("version") or s.get("dataset_version") or s.get("vintage") or "")
                                        [:80] or None)})
            src = sources[-1]
            graph = any(k in (src["kind"] or "") for k in GRAPH_KINDS)
            if not graph and before(src["fetched"], iso(c.get("registered_at"))):
                src["early"] = True
                a = next((e for e in audit.get(cid, []) if e["dataset"] == src["dataset"] and e["fetched"] == src["fetched"]), None)
                if a:
                    src["audit"] = {k: a[k] for k in ("class", "evidence", "earlier_claim", "revealed_deciding_number") if a.get(k)}
                else:
                    unaudited.append(f"{cid} {src['dataset']} {src['fetched']}")
        hist = o.get("history") or []
        revisions = [{"verdict": h.get("verdict"), "time": iso(h.get("decided_at")), "kind": "scored"} for h in hist]
        rv = o.get("revision")
        if isinstance(rv, dict):
            revisions.append({"verdict": o.get("verdict"), "time": iso(rv.get("revised_at")), "kind": "revision",
                              "reason": rv.get("reason"), "critique": rv.get("critique")})
        crit = commits(f"critique/{cid}.md", first_only=True)
        out[cid] = {
            "registered_at": iso(c.get("registered_at")),
            "registration_sha256": c.get("sha256"),
            "hash_ok": c.get("hash_ok"),
            "registration_commit": reg[0] if reg else None,
            "push": push,
            "sources": sources,
            "decided_at": iso((hist[0].get("decided_at") if hist else None) or o.get("decided_at")),
            "outcome_commits": commits(f"claims/outcomes/{cid}.json"),
            "referee": ({"path": f"critique/{cid}.md", **crit[0]} if crit else None),
            "revisions": revisions,
            "verdict": o.get("verdict"),
            "first_verdict": (hist[0].get("verdict") if hist else o.get("verdict")),
            "replication": replication(cid),
        }
    if unaudited:
        print(f"warning: {len(unaudited)} early fetches have no audit class (data/derived/lineage_audit.json):",
              *unaudited[:10], sep="\n  ", file=sys.stderr)
    return {"generated": datetime.now().astimezone().isoformat(timespec="seconds"),
            "note": "Git-derived provenance per claim. Push times come from this repository's reflog of "
                    "refs/remotes/origin/prereg/<id>; where none exists, from the commit the remote branch points at. "
                    "A source is early when its fetch time precedes registered_at; its audit class comes from "
                    "data/derived/lineage_audit.json (docs/lineage_audit.md).",
            "audit_classes": {
                "a": "exposure or treatment only, not the outcome",
                "b": "design, power or calibration read, pre-period data or metadata; does not decide the verdict",
                "c": "shared cache: fetched for an earlier claim and holds this claim's outcome",
                "d": "outcome data read for this claim before registration",
                "e": "cannot tell",
                "f": "no early read of city data: date-only or misparsed fetch time, or a literature benchmark"},
            "unaudited_early": unaudited,
            "claims": out}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-remote", action="store_true", help="do not call git ls-remote")
    a = ap.parse_args(argv)
    lin = build(not a.no_remote)
    txt = json.dumps(lin, indent=1, ensure_ascii=False)
    if "/Users/" in txt or "/Volumes/" in txt:
        raise SystemExit("absolute path in lineage data")
    (DATA / "lineage.json").write_text(txt + "\n")
    bundle = {"titles": json.loads((DATA / "titles.json").read_text()),
              "annotations": json.loads((DATA / "annotations.json").read_text()),
              "lineage": lin}
    (DATA / "evidence.js").write_text("window.CONCORD_EVIDENCE=" +
                                      json.dumps(bundle, ensure_ascii=False, separators=(",", ":")) + ";\n")
    n = lin["claims"]
    print(f"lineage: {len(n)} claims; {sum(1 for v in n.values() if v['push']['sha'])} with a prereg branch; "
          f"{sum(1 for v in n.values() if v['replication'])} with a replication package")
    return 0


if __name__ == "__main__":
    sys.exit(main())
