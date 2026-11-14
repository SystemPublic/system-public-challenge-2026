"""Yellow-taxi speeds by date, hour and area, from TLC monthly trip files.

Areas (pickup and drop-off both inside): cbd = the 38 MTA CBD taxi zones; north = Manhattan
zones north of 60th Street used by repro-mmr-cbd-speed (MN_NORTH); mn = any Manhattan zone;
bk, qn, bx = both in Brooklyn, Queens (airports 1, 132, 138 excluded) or the Bronx.
A trip may count in cbd, north and mn at once. Trip filter f1 of repro-mmr-cbd-speed:
0 < miles <= 50, 60 s <= duration <= 3 h, 0.5 <= mph <= 50. Files are read from a local
copy in ~/opt/nyc-concordance when present, otherwise remotely (duckdb httpfs reads only the
needed columns). Version records (Last-Modified, ETag, length) come from an HTTP HEAD request.

Usage: python -m analyses.ems_response.taxi_hourly 2017-01 2018-12
Writes data/derived/ems_response/taxi_hourly_{FIRST}_{LAST}.csv and taxi_files_{FIRST}_{LAST}.json
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import duckdb
import pandas as pd
import requests

from analyses.ems_response.common import DER, TLC_LOCAL, TLC_URL
from analyses.reproduction.register_mmr_cbd_speed import CBD_ZONES
from analyses.reproduction.mmr_cbd_speed import MN_NORTH

ZL = TLC_LOCAL[0] / "taxi_zone_lookup.csv"
PARTS = DER / "taxi_parts"
PARTS.mkdir(exist_ok=True)


def zones():
    z = pd.read_csv(ZL)
    by = lambda b: [int(i) for i in z[z.Borough == b].LocationID]
    return {"mn": by("Manhattan"), "bk": by("Brooklyn"),
            "qn": [i for i in by("Queens") if i not in (1, 132, 138)], "bx": by("Bronx")}


def main(first, last):
    con = duckdb.connect()
    con.execute("install httpfs; load httpfs")
    zs = zones()
    L = lambda xs: ",".join(map(str, xs))
    areas = {"cbd": CBD_ZONES, "north": MN_NORTH, **zs}
    out, recs = [], []
    for m in [str(p)[:7] for p in pd.period_range(first, last, freq="M")]:
        name = f"yellow_tripdata_{m}.parquet"
        part = PARTS / f"{m}.csv"
        if part.exists() and (PARTS / f"{m}.json").exists():
            out.append(pd.read_csv(part)); recs.append(json.loads((PARTS / f"{m}.json").read_text()))
            continue
        src = next((str(d / name) for d in TLC_LOCAL if (d / name).exists()), None)
        if src is None:
            dl = TLC_LOCAL[2]; dl.mkdir(parents=True, exist_ok=True)
            subprocess.run(["curl", "-sS", "--fail", "--retry", "5", "--retry-delay", "30", "-o", str(dl / name),
                            "-D", str(dl / (name + ".headers")), TLC_URL + name], check=True)
            src = str(dl / name)
        hf = Path(src + ".headers")
        if hf.exists():
            h = {k.strip(): v.strip() for k, v in (l.split(":", 1) for l in hf.read_text().splitlines() if ":" in l)}
            h = {"Last-Modified": h.get("last-modified"), "ETag": h.get("etag"), "Content-Length": h.get("content-length", 0)}
        else:
            h = {"Last-Modified": None, "ETag": None, "Content-Length": Path(src).stat().st_size}
        recs.append({"kind": "tlc-trip-record-file", "url": TLC_URL + name, "month": m,
                     "last_modified": h.get("Last-Modified"), "etag": h.get("ETag"),
                     "bytes": int(h.get("Content-Length", 0)),
                     "read_from": "local copy in ~/opt/nyc-concordance"})
        start = pd.Timestamp(m + "-01")
        end = start + pd.offsets.MonthBegin(1)
        parts = " union all ".join(
            f"select d, hh, '{a}' area, count(*) n, sum(dist) miles, sum(dur_s)/3600.0 hrs from t "
            f"where pu in ({L(z)}) and dol in ({L(z)}) group by 1,2" for a, z in areas.items())
        df = con.execute(f"""
          with t as (select PULocationID pu, DOLocationID dol, trip_distance dist,
                            cast(tpep_pickup_datetime as date) d, hour(tpep_pickup_datetime) hh,
                            date_diff('second', tpep_pickup_datetime, tpep_dropoff_datetime) dur_s
                     from read_parquet('{src}')
                     where tpep_pickup_datetime >= TIMESTAMP '{start}' and tpep_pickup_datetime < TIMESTAMP '{end}'
                       and trip_distance > 0 and trip_distance <= 50
                       and date_diff('second', tpep_pickup_datetime, tpep_dropoff_datetime) between 60 and 10800
                       and trip_distance / (date_diff('second', tpep_pickup_datetime, tpep_dropoff_datetime)/3600.0) between 0.5 and 50)
          {parts} order by 1,2,3""").df()
        df.to_csv(part, index=False)
        (PARTS / f"{m}.json").write_text(json.dumps(recs[-1]))
        out.append(df)
        print(m, len(df), int(df[df.area == "cbd"].n.sum()), flush=True)
    pd.concat(out).to_csv(DER / f"taxi_hourly_{first}_{last}.csv", index=False)
    (DER / f"taxi_files_{first}_{last}.json").write_text(json.dumps(recs, indent=1))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
