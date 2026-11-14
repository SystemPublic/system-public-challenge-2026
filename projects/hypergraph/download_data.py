"""Fetch the city and weather data that the claims rest on.

The repository's cache of NYC Open Data and NOAA responses (data/cache/, about
3 GB) is not included in this folder. Each claim outcome lists its sources in
claims/outcomes/<id>.json under `sources`. This script reads those records and
re-runs the queries that need no key:

  - NYC Open Data and data.ny.gov (Socrata) queries, with the exact SoQL that
    was recorded, through concord/socrata.py, into data/cache/socrata/;
  - NOAA GHCN-Daily station files, through concord/noaa.py, into data/cache/noaa/.

Other sources (TLC trip-record files, Census bulk files, EHDP files at a pinned
GitHub commit, NAIP images, NYISO files and others) are listed with their URLs
by --list; the analysis scripts in analyses/ download them when they need them,
or the URL can be fetched by hand. The analysis scripts use a cached response
when its query matches theirs and otherwise send the query themselves.

The city rewrites its tables in place, so a re-fetched table can differ from
the one a claim used. Each source record keeps `rows_updated_at` from the time
of the original fetch; this script prints the current value next to it. The two
replication packages in replication/ hold pinned copies of their inputs.

No key is needed. Usage:

  python download_data.py --list                 # every source, grouped by kind
  python download_data.py --claim heat-shootings # fetch one claim's sources
  python download_data.py --all                  # fetch every Socrata and NOAA source
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.parse
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

SOCRATA_KINDS = {"nyc-open-data", "ny-open-data", "data.ny.gov", "health.data.ny.gov"}


def load_sources(claim: str | None = None) -> list[tuple[str, dict]]:
    out = []
    for f in sorted((ROOT / "claims" / "outcomes").glob("*.json")):
        if claim and f.stem != claim:
            continue
        d = json.loads(f.read_text())
        for s in d.get("sources") or []:
            if isinstance(s, dict):
                out.append((f.stem, s))
    if claim and not out:
        raise SystemExit(f"no outcome with sources for claim {claim!r}")
    return out


def kind_of(s: dict) -> str:
    k = str(s.get("kind") or "unlabelled")
    if k.startswith("socrata") or k.startswith("ny-state-open-data"):
        return "nyc-open-data"
    return k


def socrata_host(s: dict) -> str:
    for key in ("url", "portal"):
        v = s.get(key)
        if v:
            host = urllib.parse.urlparse(v if "://" in v else "https://" + v).netloc
            if host:
                return "https://" + host
    return "https://data.cityofnewyork.us"


def fetch_socrata(s: dict) -> str:
    from concord import socrata
    q = s.get("query")
    if not isinstance(q, dict) or not s.get("dataset"):
        return "skipped: no recorded SoQL"
    socrata.DOMAIN = socrata_host(s)
    try:
        if "$order" in q and "$offset" not in q:
            # concord.socrata.query_all pages with $offset and drops it from the
            # recorded query; paging the same way reproduces its cache files.
            rest = {k.lstrip("$"): v for k, v in q.items() if k != "$limit"}
            rows, src = socrata.query_all(s["dataset"], page=int(q.get("$limit", 50000)), **rest)
        else:
            rows, src = socrata.query(s["dataset"], **q)
    finally:
        socrata.DOMAIN = "https://data.cityofnewyork.us"
    then, now = s.get("rows_updated_at"), src.get("rows_updated_at")
    note = "same table version" if then == now else f"table updated since: recorded {then}, now {now}"
    return f"{len(rows)} rows; {note}"


def fetch_noaa(s: dict) -> str:
    from concord import noaa
    df, src = noaa.daily(s.get("station", "central_park"))
    return f"{len(df)} days; Last-Modified now {src['last_modified']}, recorded {s.get('last_modified')}"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--list", action="store_true", help="list every source by kind")
    g.add_argument("--claim", help="fetch the Socrata and NOAA sources of one claim")
    g.add_argument("--all", action="store_true", help="fetch every Socrata and NOAA source")
    a = ap.parse_args(argv)

    if a.list:
        by = defaultdict(list)
        for cid, s in load_sources():
            by[kind_of(s)].append((cid, s))
        for k in sorted(by, key=lambda k: -len(by[k])):
            how = "fetched by this script" if k in SOCRATA_KINDS | {"noaa-ghcnd"} else "listed only"
            print(f"\n{k}: {len(by[k])} records ({how})")
            seen = set()
            for cid, s in by[k]:
                label = s.get("dataset") or s.get("station") or s.get("url") or s.get("file") or s.get("name") or s.get("note")
                if (label, cid) in seen:
                    continue
                seen.add((label, cid))
                print(f"  {cid:40s} {str(label)[:110]}")
        return 0

    todo = load_sources(a.claim)
    done, failed = set(), 0
    for cid, s in todo:
        k = kind_of(s)
        if k in SOCRATA_KINDS:
            key = ("s", s.get("dataset"), json.dumps(s.get("query"), sort_keys=True))
            fn = fetch_socrata
        elif k == "noaa-ghcnd":
            key = ("n", s.get("station"))
            fn = fetch_noaa
        else:
            continue
        if key in done:
            continue
        done.add(key)
        label = s.get("dataset") or s.get("station")
        try:
            print(f"{cid}  {k}  {label}: {fn(s)}", flush=True)
        except Exception as e:  # network errors and odd records are reported, not fatal
            failed += 1
            print(f"{cid}  {k}  {label}: FAILED {e}", flush=True)
        time.sleep(0.2)
    print(f"\n{len(done)} sources fetched or found in data/cache/, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
