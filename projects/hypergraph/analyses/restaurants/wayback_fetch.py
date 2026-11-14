"""Older copies of the DOHMH restaurant inspection export (43nn-pn8j) from the Internet Archive.

The live dataset holds mainly recent inspections of restaurants that are open now. Each archived
CSV export holds the inspections (about three years back) of the restaurants open on its capture
date, so a set of captures spread over 2015-2026 gives inspections back to about 2012 and lets the
same year be compared across copies taken at different dates.

The CDX listing is saved to data/derived/restaurants/wayback_cdx.json. One capture per calendar
year (the latest one with status 200 and a CSV body) is downloaded, raw (the id_ form of the
Wayback URL), to ~/opt/nyc-concordance/restaurants_wayback/<timestamp>.csv (outside Dropbox).
A capture is cited by its Wayback URL, which is stable.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = Path.home() / "opt" / "nyc-concordance" / "restaurants_wayback"
DER = ROOT / "data" / "derived" / "restaurants"
CDX = "https://web.archive.org/cdx/search/cdx"
PATTERN = "data.cityofnewyork.us/api/views/43nn-pn8j/rows.csv*"
UA = {"User-Agent": "research-data-client/1.0"}


def cdx() -> list[dict]:
    for i in range(10):
        try:
            r = requests.get(CDX, params={"url": PATTERN, "output": "json", "limit": 500,
                                          "fl": "timestamp,original,statuscode,mimetype,length,digest"},
                             headers=UA, timeout=60)
            rows = r.json()
            keys = rows[0]
            return [dict(zip(keys, x)) for x in rows[1:]]
        except Exception as e:  # archive is often briefly offline
            print("cdx retry", i, e, file=sys.stderr)
            time.sleep(10 * (i + 1))
    raise SystemExit("CDX unavailable")


def choose(rows: list[dict]) -> list[dict]:
    ok = [r for r in rows if r["statuscode"] == "200" and "csv" in r["mimetype"]]
    by_year = {}
    for r in sorted(ok, key=lambda r: (r["timestamp"], -int(r["length"]))):
        by_year[r["timestamp"][:4]] = r  # latest capture in the year
    return [by_year[y] for y in sorted(by_year)]


def download(r: dict) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    f = OUT / f"{r['timestamp']}.csv"
    if f.exists() and f.stat().st_size > 1_000_000:
        return f
    url = f"https://web.archive.org/web/{r['timestamp']}id_/{r['original']}"
    for i in range(8):
        try:
            with requests.get(url, stream=True, headers=UA, timeout=300) as g:
                g.raise_for_status()
                tmp = f.with_suffix(".part")
                with tmp.open("wb") as h:
                    for chunk in g.iter_content(1 << 20):
                        h.write(chunk)
                tmp.rename(f)
                return f
        except Exception as e:
            print("download retry", r["timestamp"], i, e, file=sys.stderr)
            time.sleep(15 * (i + 1))
    raise RuntimeError(f"failed {url}")


def main():
    DER.mkdir(parents=True, exist_ok=True)
    rows = cdx()
    pick = choose(rows)
    (DER / "wayback_cdx.json").write_text(json.dumps({"pattern": PATTERN, "fetched": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                                                       "captures": rows, "chosen": pick}, indent=1))
    for r in pick:
        f = download(r)
        print(r["timestamp"], f.stat().st_size, flush=True)


if __name__ == "__main__":
    main()
