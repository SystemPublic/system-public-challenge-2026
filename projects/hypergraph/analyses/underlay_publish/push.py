"""Create the collection built by build.py on the Underlay and push one version.

    python analyses/underlay_publish/push.py --owner <org slug> --yes
    python analyses/underlay_publish/push.py --owner <org slug> --yes --collection claims
    python analyses/underlay_publish/push.py --owner <org slug> --verify-only [--collection claims]

--collection restaurants (the default) pushes the build in ~/opt/nyc-concordance/underlay_publish/;
--collection claims pushes data/derived/underlay_publish/claims/, written by tools/underlay_export.py.
--verify-only repeats the unauthenticated read-back of the version named in push_result.json.

Without both --owner and --yes it prints the plan and exits without contacting the Underlay.
The key is read from ~/.config/underlay/token and is never printed or written anywhere.

Sequence (https://www.underlay.org/docs/api/versions):
  1. GET  /api/collections/:owner/:slug          must be 404 (the collection must not exist)
  2. POST /api/accounts/:owner/collections        {slug, name, description, public: true}
  3. POST /api/collections/:owner/:slug/push      {base: null, message, app_id, metadata, schemas}
  4. POST .../push/:sid/records                   NDJSON batches within limits.batch_lines / batch_bytes
  5. POST .../push/:sid/commit                    {"async": true}; then poll GET .../push/:sid
  6. Read back without authentication: the collection, the version, typeCounts, the ARK,
     the manifest's record hashes against record_hashes.tsv, and each sample record of
     manifest.json through .../versions/:hash/records/:type/:id, comparing its hash and data.
     (The lookup /api/records/:hash/first is listed as not available yet in llms.txt and
     answers 404, so records are resolved through the collection.)
Any error stops the script and prints the status and body. Nothing is retried except the poll.
"""
import argparse
import json
import sys
import time
from pathlib import Path

from urllib.parse import quote

import requests

API = "https://www.underlay.org/api"
ROOT = Path(__file__).resolve().parents[2]
BIG = Path.home() / "opt" / "nyc-concordance" / "underlay_publish"
OUT = ROOT / "data" / "derived" / "underlay_publish"
TOKEN = Path.home() / ".config" / "underlay" / "token"


def die(what, r):
    sys.exit(f"{what} failed: HTTP {r.status_code}\n{r.text[:4000]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--owner", help="organization slug that will own the collection")
    ap.add_argument("--yes", action="store_true", help="actually create and push")
    ap.add_argument("--collection", choices=["restaurants", "claims"], default="restaurants")
    ap.add_argument("--verify-only", action="store_true", help="only read the pushed version back")
    a = ap.parse_args()
    global BIG, OUT
    if a.collection == "claims":
        BIG = OUT = ROOT / "data" / "derived" / "underlay_publish" / "claims"

    col = json.loads((BIG / "collection.json").read_text())
    schemas = json.loads((BIG / "schemas.json").read_text())
    readme = (BIG / "readme.md").read_text()
    manifest = json.loads((OUT / "manifest.json").read_text())
    lines = (BIG / "records.ndjson").read_text(encoding="utf-8").splitlines()
    assert len(lines) == manifest["total_records"], "records.ndjson does not match manifest.json"

    print(f"collection {a.owner or '<owner>'}/{col['slug']} (public), {len(lines):,} records, "
          f"types {manifest['counts']}, build {manifest['build_commit'][:12]}")
    if a.owner and a.verify_only:
        res = json.loads((OUT / "push_result.json").read_text())
        return verify(a.owner, col["slug"], res["result"]["hash"], manifest)
    if not (a.owner and a.yes):
        print("dry run: pass --owner <slug> and --yes to create the collection and push")
        return

    key = TOKEN.read_text().strip()
    auth = {"Authorization": f"Bearer {key}"}
    base = f"{API}/collections/{a.owner}/{col['slug']}"

    # 1-2. create the collection
    r = requests.get(base, timeout=60)
    if r.status_code != 404:
        die("collection must not exist yet; GET", r)
    r = requests.post(f"{API}/accounts/{a.owner}/collections", headers=auth, timeout=60,
                      json={k: col[k] for k in ("slug", "name", "description", "public")})
    if r.status_code != 201:
        die("create collection", r)
    print("created", r.json())

    # 3. open the push session
    meta = dict(col["metadata"], readme=readme)
    r = requests.post(f"{base}/push", headers=auth, timeout=120,
                      json={"base": None, "message": col["message"], "app_id": col["app_id"],
                            "metadata": meta, "schemas": schemas})
    if r.status_code != 200:
        die("open push session", r)
    sess = r.json()
    sid, lim = sess["session_id"], sess["limits"]
    print("session", sid, "limits", lim)

    # 4. upload records in batches
    max_lines, max_bytes = lim["batch_lines"], int(lim["batch_bytes"] * 0.9)
    batch, size, sent = [], 0, 0
    hdr = dict(auth, **{"Content-Type": "application/x-ndjson"})

    def flush():
        nonlocal batch, size, sent
        if not batch:
            return
        rr = requests.post(f"{base}/push/{sid}/records", headers=hdr, timeout=600,
                           data=("\n".join(batch) + "\n").encode("utf-8"))
        if rr.status_code != 200:
            die(f"records batch starting at line {sent + 1}", rr)
        sent += rr.json()["received"]
        print(f"  sent {sent:,}/{len(lines):,}", flush=True)
        batch, size = [], 0

    for ln in lines:
        b = len(ln.encode("utf-8")) + 1
        if len(batch) >= max_lines or size + b > max_bytes:
            flush()
        batch.append(ln)
        size += b
    flush()
    if sent != len(lines):
        sys.exit(f"server received {sent} lines, expected {len(lines)}")

    # 5. commit and poll
    r = requests.post(f"{base}/push/{sid}/commit", headers=auth, json={"async": True}, timeout=600)
    if r.status_code not in (201, 202):
        die("commit", r)
    result = r.json() if r.status_code == 201 else None
    while result is None:
        time.sleep(10)
        p = requests.get(f"{base}/push/{sid}", headers=auth, timeout=60)
        if p.status_code != 200:
            die("poll", p)
        st = p.json()
        print("  status", st["status"], flush=True)
        if st["status"] == "committed":
            result = st["result"]
        elif st["status"] != "committing":
            sys.exit(f"commit ended with status {st['status']}: {json.dumps(st.get('error'))}")
    print("committed", json.dumps(result))
    (OUT / "push_result.json").write_text(json.dumps({"owner": a.owner, "slug": col["slug"], "host": API,
                                                      "result": result}, indent=1))

    # 6. read back without authentication
    verify(a.owner, col["slug"], result["hash"], manifest)


def verify(owner, slug, vhash, manifest):
    base = f"{API}/collections/{owner}/{slug}"
    c = requests.get(base, timeout=60)
    v = requests.get(f"{base}/versions/{vhash}", timeout=60)
    if c.status_code != 200 or v.status_code != 200:
        die("public read of collection or version", c if c.status_code != 200 else v)
    c, v = c.json(), v.json()
    tc = v.get("typeCounts")
    tc = {x["type"]: x["count"] for x in tc} if isinstance(tc, list) else tc
    expected = {}
    for ln in (BIG / "record_hashes.tsv").read_text().splitlines()[1:]:
        t, i, h = ln.split("\t")
        expected[(t, i)] = h
    got, cursor = {}, None
    while True:
        params = {"limit": 25000}
        if cursor:
            params["cursor"] = cursor
        m = requests.get(f"{base}/versions/{vhash}/manifest", params=params, timeout=300)
        if m.status_code == 429:
            time.sleep(60)
            continue
        if m.status_code != 200:
            die("manifest page", m)
        m = m.json()
        for e in m["records"]:
            got[(e["type"], e["id"])] = e["hash"]
        if not m["pagination"]["hasMore"]:
            break
        cursor = m["pagination"]["nextCursor"]
        time.sleep(1.1)
    mismatch = sum(1 for k, h in expected.items() if got.get(k) != h) + len(set(got) - set(expected))
    local = {}
    want = {(s["type"], s["id"]) for s in manifest["sample_hashes"]}
    with open(BIG / "records.ndjson", encoding="utf-8") as fh:
        for ln in fh:
            r = json.loads(ln)
            if (r["type"], r["id"]) in want:
                local[(r["type"], r["id"])] = r["data"]
    samples = []
    for s in manifest["sample_hashes"]:
        f = requests.get(f"{base}/versions/{vhash}/records/{quote(s['type'], safe='')}/{quote(s['id'], safe='')}",
                         timeout=60)
        j = f.json() if f.status_code == 200 else {}
        samples.append({"type": s["type"], "id": s["id"], "hash": s["hash"], "status": f.status_code,
                        "hash_matches": j.get("hash") == s["hash"],
                        "data_matches": j.get("data") == local.get((s["type"], s["id"])),
                        "error": None if f.status_code == 200 else f.text[:300]})
        time.sleep(1.1)
    report = {"collection_public": c.get("public"), "head": c.get("head"), "collection_ark": c.get("ark"),
              "version_hash": v.get("hash"), "version_hash_matches": v.get("hash") == vhash,
              "version_ark": v.get("ark"), "semver": v.get("semver"), "typeCounts": tc,
              "typeCounts_match": tc == manifest["counts"], "manifest_records": len(got),
              "manifest_hash_mismatches": mismatch,
              "samples_resolved": sum(x["hash_matches"] and x["data_matches"] for x in samples),
              "samples": samples, "read_without_authentication": True,
              "checked_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    (OUT / "readback.json").write_text(json.dumps(report, indent=1))
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
