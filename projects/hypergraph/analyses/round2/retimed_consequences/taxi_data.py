"""Daily pickups by taxi zone, 06:00-19:59, from TLC trip records (yellow taxi and high-volume for-hire).

Local parquet files (downloaded earlier by the project from the TLC trip-record site) are read where they
exist; other months are read with a remote column scan of the same files, without saving them.
"""
import json, sys, time
from pathlib import Path
import duckdb, pandas as pd

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "data/derived/round2/retimed_consequences"
OPT = Path.home() / "opt/nyc-concordance"
URL = "https://d37ci6vzurychx.cloudfront.net/trip-data/{kind}_tripdata_{ym}.parquet"
COL = {"yellow": ("tpep_pickup_datetime", "PULocationID"), "fhvhv": ("pickup_datetime", "PULocationID"),
       "fhv": ("pickup_datetime", "PUlocationID")}


def daily(kind: str, ym: str) -> tuple[pd.DataFrame, dict]:
    f = OUT / "taxi_cache" / f"{kind}_{ym}.csv"
    s = f.with_suffix(".source.json")
    if f.exists():
        return pd.read_csv(f), json.loads(s.read_text())
    f.parent.mkdir(parents=True, exist_ok=True)
    local = [p for p in (OPT / "tlc_yellow" / f"{kind}_tripdata_{ym}.parquet", OPT / "tlc_2019" / f"{kind}_tripdata_{ym}.parquet") if p.exists()]
    url = URL.format(kind=kind, ym=ym)
    con = duckdb.connect()
    if local:
        src = str(local[0]); how = "local copy of the file at the URL"
    else:
        con.execute("INSTALL httpfs; LOAD httpfs;"); src = url; how = "remote column scan"
    t, z = COL[kind]
    y, m = ym.split("-")
    q = (f"select cast({t} as date) as date, cast({z} as integer) as unit, count(*) as n from parquet_scan('{src}') "
         f"where hour({t}) between 6 and 19 and year({t})={int(y)} and month({t})={int(m)} group by 1,2 order by 1,2")
    df = con.execute(q).df()
    df.to_csv(f, index=False)
    rec = {"kind": "tlc-trip-records", "name": f"{kind} trip records {ym}", "url": url, "read": how,
           "query": q.replace(src, "<file>"), "n_trips": int(df.n.sum()), "fetched": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    h = local[0].with_suffix(".parquet.headers") if local else None
    if h and h.exists():
        rec["headers_file"] = h.read_text()[:600]
    s.write_text(json.dumps(rec, indent=1))
    return df, rec


def panel(kinds, months):
    parts, recs = [], []
    for k in kinds:
        for ym in months:
            d, r = daily(k, ym); parts.append(d); recs.append(r)
    p = pd.concat(parts).groupby(["date", "unit"], as_index=False).n.sum()
    return p, recs
