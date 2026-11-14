"""Publish a later version of the claims collection as a delta push, then read the difference back.

Usage: ~/.venvs/nyc-concordance/bin/python -m analyses.underlay_publish.push_delta --owner system-community [--yes]

Follows "Writing Data: The Push Flow" in https://www.underlay.org/llms.txt: read the head, compare the server's
manifest with the local export (tools/underlay_export.py) by (type, id, hash), open a session on the head's
semver, upload the upserts and deletes, commit. Schemas are not sent, so the base's types are kept and the server
assigns a minor version. The key is read from ~/.config/underlay/token and is never printed.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "derived" / "underlay_publish" / "claims"
API = "https://www.underlay.org/api"
TOKEN = Path.home() / ".config" / "underlay" / "token"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--owner", required=True)
    ap.add_argument("--yes", action="store_true")
    a = ap.parse_args()
    col = json.loads((OUT / "collection.json").read_text())
    base = f"{API}/collections/{a.owner}/{col['slug']}"
    auth = {"Authorization": f"Bearer {TOKEN.read_text().strip()}"}
    head = requests.get(f"{base}/versions/latest", timeout=60).json()
    server, cursor = {}, None
    while True:
        m = requests.get(f"{base}/versions/{head['semver']}/manifest", params={"limit": 10000, **({"cursor": cursor} if cursor else {})}, timeout=120).json()
        server.update({(r["type"], r["id"]): r["hash"] for r in m["records"]})
        if not m["pagination"]["hasMore"]:
            break
        cursor = m["pagination"]["nextCursor"]
    local = {}
    for line in (OUT / "record_hashes.tsv").read_text().splitlines()[1:]:
        t, i, h = line.split("\t")
        local[(t, i)] = h
    norm = lambda h: h.split(":")[-1]
    ups = {k for k, h in local.items() if k not in server or norm(server[k]) != norm(h)}
    dels = [k for k in server if k not in local]
    print(f"head {head['semver']} ({len(server)} records); local {len(local)}; upserts {len(ups)}, deletes {len(dels)}")
    for k in sorted(ups):
        print("  upsert", *k)
    if not a.yes:
        print("dry run: pass --yes to push")
        return 0
    lines = [l for l in (OUT / "records.ndjson").read_text(encoding="utf-8").splitlines() if (json.loads(l)["type"], json.loads(l)["id"]) in ups]
    assert len(lines) == len(ups)
    r = requests.post(f"{base}/push", headers=auth, timeout=120, json={"base": head["semver"], "message": col["message"], "app_id": col["app_id"],
                                                               "metadata_patch": {**col["metadata"], "readme": (OUT / "readme.md").read_text()}})
    if r.status_code != 200:
        print("open failed", r.status_code, r.text[:500]); return 1
    sid = r.json()["session_id"]
    rr = requests.post(f"{base}/push/{sid}/records", headers={**auth, "Content-Type": "application/x-ndjson"}, data=("\n".join(lines) + "\n").encode("utf-8"), timeout=600)
    if rr.status_code != 200:
        print("records failed", rr.status_code, rr.text[:800]); return 1
    if dels:
        requests.post(f"{base}/push/{sid}/deletes", headers={**auth, "Content-Type": "application/x-ndjson"}, data=("\n".join(json.dumps({"type": t, "id": i}) for t, i in dels) + "\n").encode(), timeout=600).raise_for_status()
    c = requests.post(f"{base}/push/{sid}/commit", headers=auth, timeout=600)
    if c.status_code not in (201, 202):
        print("commit failed", c.status_code, c.text[:800]); return 1
    res = c.json()
    if c.status_code == 202:
        import time
        for _ in range(120):
            p = requests.get(f"{base}/push/{sid}", headers=auth, timeout=60).json()
            if p["status"] in ("committed", "failed"):
                res = p.get("result") or p; break
            time.sleep(2)
    print("committed", json.dumps(res))
    (OUT / f"push_result_{res.get('semver', 'unknown')}.json").write_text(json.dumps({"base": head["semver"], "result": res}, indent=1))
    d = requests.get(f"{base}/versions/{res['semver']}/diff", params={"from": head["semver"], "limit": 500}, timeout=120).json()
    print("diff", d["from"], "->", d["to"], "added", len(d["added"]), "updated", len(d["updated"]), "removed", len(d["removed"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
