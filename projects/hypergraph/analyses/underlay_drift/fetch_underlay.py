"""Download every record of nyc/restaurant-inspections v1.0.0 from the Underlay,
with the collection, version, schema and readme metadata. Read-only; no auth.

Output goes to ~/opt/nyc-concordance/underlay/ (outside Dropbox). The script
checks the stream against X-Underlay-Record-Count and checks each record's
hash as SHA-256 of its canonical line {"id","type","data"}.
"""
import hashlib
import json
import sys
from pathlib import Path

import requests

API = "https://www.underlay.org/api/collections/nyc/restaurant-inspections"
VERSION = "v1.0.0"
EXPECT_HASH = "ulv2:07a7f08a0d5c85649920f8adc6946d27c17f5e2d75e9ee07c0ad4ae0fcc6739c"
OUT = Path.home() / "opt" / "nyc-concordance" / "underlay"


def sort_keys(o):
    """Canonical form for these records: keys id, type, data in that order; keys inside data sorted."""
    if isinstance(o, dict):
        return {k: sort_keys(o[k]) for k in sorted(o)}
    if isinstance(o, list):
        return [sort_keys(x) for x in o]
    return o


def get_json(url, **params):
    r = requests.get(url, params=params, timeout=120)
    r.raise_for_status()
    return r.json()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    meta = {
        "collection": get_json(API),
        "versions": get_json(f"{API}/versions"),
        "version": get_json(f"{API}/versions/{VERSION}"),
        "schemas": get_json(f"{API}/schemas", version=VERSION, raw="true"),
    }
    assert meta["version"]["hash"] == EXPECT_HASH, meta["version"]["hash"]
    (OUT / "metadata_v1.0.0.json").write_text(json.dumps(meta, indent=1))
    (OUT / "README_v1.0.0.md").write_text(meta["version"]["metadata"]["readme"])

    dest = OUT / "records_v1.0.0.ndjson"
    n, bad_hash, counts = 0, 0, {}
    with requests.get(f"{API}/versions/{EXPECT_HASH}/records.ndjson", stream=True, timeout=600) as r:
        r.raise_for_status()
        expected = int(r.headers.get("X-Underlay-Record-Count", -1))
        with dest.open("w") as f:
            for raw in r.iter_lines():
                line = raw.decode("utf-8")
                if not line:
                    continue
                rec = json.loads(line)
                canon = json.dumps({"id": rec["id"], "type": rec["type"], "data": sort_keys(rec["data"])},
                                   separators=(",", ":"), ensure_ascii=False)
                if hashlib.sha256(canon.encode()).hexdigest() != rec.get("hash"):
                    bad_hash += 1
                counts[rec["type"]] = counts.get(rec["type"], 0) + 1
                f.write(line + "\n")
                n += 1
    report = {"records": n, "expected_header": expected, "type_counts": counts,
              "hash_mismatch": bad_hash,
              "version_hash": EXPECT_HASH}
    (OUT / "download_check.json").write_text(json.dumps(report, indent=1))
    derived = Path(__file__).resolve().parents[2] / "data" / "derived" / "underlay_drift"
    derived.mkdir(parents=True, exist_ok=True)
    for name in ("metadata_v1.0.0.json", "download_check.json"):
        (derived / name).write_text((OUT / name).read_text())
    print(json.dumps(report, indent=1))
    if n != expected:
        sys.exit("incomplete stream")


if __name__ == "__main__":
    main()
