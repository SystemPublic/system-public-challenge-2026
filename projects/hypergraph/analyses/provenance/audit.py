"""Provenance audit: does the record show each prediction before its data?

For every registration in claims/registered/ this script checks
  1. that the stored sha256 matches the file's content (concord.claims._hash);
  2. the commit that added the registration and the commit that added its outcome;
  3. that the registration commit is an ancestor of the outcome commit, and earlier in time;
  4. whether the registration file was changed by any later commit;
  5. which push to GitHub first carried each commit, from the server-side push
     times saved in data/derived/provenance/github_pushes.json.

Commit times are written by the committer's machine and can be set at will. Push times are
recorded by GitHub. Only the second kind is evidence that a third party can check.

Writes data/derived/provenance/registrations.csv and summary.json. Uses git and the standard
library only. Run from the repo root with the full history (not a shallow clone):
  python analyses/provenance/audit.py
"""
from __future__ import annotations

import csv
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from concord import claims  # noqa: E402

D = ROOT / "data" / "derived" / "provenance"


def git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True, check=True).stdout.strip()


def is_ancestor(a: str, b: str) -> bool:
    return subprocess.run(["git", "-C", str(ROOT), "merge-base", "--is-ancestor", a, b]).returncode == 0


def commits_touching(path: str) -> list[tuple[str, str]]:
    out = git("log", "--format=%H %cI", "--", path)
    return [tuple(line.split(" ", 1)) for line in reversed(out.splitlines()) if line]


def first_push(commit: str, pushes: list[dict]) -> dict | None:
    for p in pushes:
        if is_ancestor(commit, p["after"]):
            return p
    return None


def utc(iso: str) -> datetime:
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(timezone.utc)


def parse_local(s: str) -> datetime | None:
    """Parse a time such as 2026-11-12T15:21:22-0500. Date-only values return None."""
    try:
        return datetime.strptime(s.replace("Z", "+0000"), "%Y-%m-%dT%H:%M:%S%z")
    except ValueError:
        return None


def main() -> None:
    if git("rev-parse", "--is-shallow-repository") == "true":
        sys.exit("shallow clone: fetch the full history first")
    pushes = json.loads((D / "github_pushes.json").read_text())
    rows = []
    for f in sorted(claims.REG.glob("*.json")):
        cid = f.stem
        reg = json.loads(f.read_text())
        rpath = f"claims/registered/{cid}.json"
        opath = f"claims/outcomes/{cid}.json"
        rc = commits_touching(rpath)
        oc = commits_touching(opath) if (claims.OUT / f"{cid}.json").exists() else []
        r_commit, r_time = rc[0]
        row = {
            "id": cid,
            "hash_ok": reg.get("sha256") == claims._hash(reg),
            "registered_at_field": reg.get("registered_at"),
            "reg_commit": r_commit[:7],
            "reg_commit_time": r_time,
            "reg_later_commits": len(rc) - 1,
            "out_commit": oc[0][0][:7] if oc else "",
            "out_commit_time": oc[0][1] if oc else "",
            "out_revisions": len(oc) - 1 if oc else 0,
        }
        if oc:
            row["reg_ancestor_of_out"] = is_ancestor(r_commit, oc[0][0]) and r_commit != oc[0][0]
            row["minutes_reg_to_out"] = round((utc(oc[0][1]) - utc(r_time)).total_seconds() / 60, 1)
        else:
            row["reg_ancestor_of_out"] = ""
            row["minutes_reg_to_out"] = ""
        # sources cited by the outcome that were fetched before the registration time
        n_timed, early = 0, []
        if oc:
            o = json.loads((claims.OUT / f"{cid}.json").read_text())
            rt = parse_local(reg.get("registered_at", ""))
            for s in o.get("sources", []):
                t = parse_local(s.get("fetched", "")) if isinstance(s, dict) else None
                if t is None or rt is None:
                    continue
                n_timed += 1
                if t < rt:
                    early.append(f"{s.get('dataset') or s.get('kind')} ({round((rt - t).total_seconds() / 60, 1)} min)")
        row["sources_with_fetch_time"] = n_timed
        row["sources_fetched_before_registration"] = "; ".join(early)
        rp = first_push(r_commit, pushes)
        op = first_push(oc[0][0], pushes) if oc else None
        row["reg_first_push_utc"] = rp["timestamp"] if rp else ""
        row["out_first_push_utc"] = op["timestamp"] if op else ""
        row["push_separates"] = bool(rp and op and rp["timestamp"] < op["timestamp"]) if oc else ""
        rows.append(row)

    D.mkdir(parents=True, exist_ok=True)
    with open(D / "registrations.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    with_out = [r for r in rows if r["out_commit"]]
    summary = {
        "audited_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "head": git("rev-parse", "HEAD")[:7],
        "registrations": len(rows),
        "with_outcome": len(with_out),
        "hash_ok": sum(r["hash_ok"] for r in rows),
        "registration_changed_after_commit": [r["id"] for r in rows if r["reg_later_commits"]],
        "registration_before_outcome_in_history": sum(r["reg_ancestor_of_out"] is True for r in with_out),
        "same_commit_or_out_of_order": [r["id"] for r in with_out if r["reg_ancestor_of_out"] is not True],
        "minutes_reg_to_out_min": min(r["minutes_reg_to_out"] for r in with_out) if with_out else None,
        "minutes_reg_to_out_median": sorted(r["minutes_reg_to_out"] for r in with_out)[len(with_out) // 2] if with_out else None,
        "push_separates_reg_from_out": sum(r["push_separates"] is True for r in with_out),
        "outcomes_with_timed_sources": sum(1 for r in with_out if r["sources_with_fetch_time"]),
        "outcomes_citing_a_source_fetched_before_registration": [r["id"] for r in with_out if r["sources_fetched_before_registration"]],
        "outcomes_revised":sum(1 for r in with_out if r["out_revisions"]),
        "without_outcome": [r["id"] for r in rows if not r["out_commit"]],
        "pushes": pushes,
    }
    (D / "summary.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps({k: v for k, v in summary.items() if k != "pushes"}, indent=1))


if __name__ == "__main__":
    main()
