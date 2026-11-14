"""Fetch inputs for transit-gtrain-substitution (run after registration).

Trips: the portal could not aggregate bqxa-629f on the server (a one-month group-by timed out after
six attempts of 180 s on 12 Nov 2026), so the registered fallback is used: the TLC monthly parquet files
of the same records, read remotely with DuckDB (only three columns are transferred) and counted by
pickup day, pickup zone and company. Subway entries: data.ny.gov wujg-7c2s through concord.socrata.
"""
from __future__ import annotations

import json
import time

import duckdb
import pandas as pd
import requests

from analyses.mobility.common import nys
from concord import socrata
from analyses.transit.gtrain_common import DER, G_ONLY

TLC = "https://d37ci6vzurychx.cloudfront.net/trip-data/fhvhv_tripdata_{m}.parquet"
# 2023 runs to October because the placebo window, moved back 364 days, ends on 2 October 2023.
MONTHS = [f"2023-{m:02d}" for m in (6, 7, 8, 9, 10)] + [f"2024-{m:02d}" for m in (6, 7, 8, 9)]
UA = {"User-Agent": "research-client"}


def trips():
    out, srcs = [], []
    con = duckdb.connect()
    con.execute("INSTALL httpfs; LOAD httpfs;")
    for m in MONTHS:
        f = DER / f"gtrain_pickups_{m}.csv"
        url = TLC.format(m=m)
        sf = DER / f"gtrain_pickups_{m}.source.json"
        if not f.exists():
            h = requests.head(url, headers=UA, timeout=60).headers
            q = (f"select cast(pickup_datetime as date) as d, PULocationID as zone, hvfhs_license_num as lic, count(*) as n "
                 f"from parquet_scan('{url}') group by 1, 2, 3 order by 1, 2, 3")
            df = con.execute(q).df()
            df.to_csv(f, index=False)
            sf.write_text(json.dumps({"kind": "tlc-trip-records", "name": f"High Volume FHV trip records {m}", "url": url,
                                      "etag": h.get("ETag"), "last_modified": h.get("Last-Modified"),
                                      "bytes": int(h.get("Content-Length", 0)), "query": q.replace(url, "<url>"),
                                      "n_trips": int(df["n"].sum()), "fetched": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                                      "data_access": "open",
                                      "note": "Same records as NYC Open Data bqxa-629f (2024) and u253-aew4 (2023)."}, indent=1))
        out.append(pd.read_csv(f))
        srcs.append(json.loads(sf.read_text()))
        print(m, srcs[-1]["n_trips"], flush=True)
    return pd.concat(out), srcs


def subway():
    srcs, out = [], []
    ids = ", ".join(f"'{i}'" for i in G_ONLY)
    for y in (2023, 2024):
        rows, src = nys("wujg-7c2s", select="date_trunc_ymd(transit_timestamp) as d, station_complex_id, station_complex, sum(ridership) as entries",
                        where=f"station_complex_id in ({ids}) and transit_timestamp >= '{y}-06-01T00:00:00' and transit_timestamp < '{y}-10-08T00:00:00'",
                        group="d, station_complex_id, station_complex", order="d, station_complex_id")
        src["domain"] = "data.ny.gov (concord.socrata.DOMAIN set to https://data.ny.gov for this query)"
        src["data_access"] = "open"
        srcs.append(src)
        out.append(pd.DataFrame(rows))
        print("subway", y, len(rows), flush=True)
    df = pd.concat(out)
    df["entries"] = df["entries"].astype(float)
    df.to_csv(DER / "gtrain_subway_entries.csv", index=False)
    return df, srcs


if __name__ == "__main__":
    s_df, s_src = subway()
    t_df, t_src = trips()
    t_df.to_csv(DER / "gtrain_pickups_zone_day.csv", index=False)
    meta = {m: socrata.metadata(m) for m in ("bqxa-629f", "u253-aew4")}
    (DER / "gtrain_sources.json").write_text(json.dumps({"trips": t_src, "subway": s_src, "portal_metadata": meta}, indent=1))
