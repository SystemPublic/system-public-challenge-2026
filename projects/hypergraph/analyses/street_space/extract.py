"""Aggregate yellow-taxi trips between the zones of analyses.street_space.common by directed
pair, date and pickup hour. Trip filter (as in analyses/congestion/taxi_speed.py): 0 < miles <= 50,
60 s <= duration <= 3 h, 0.5 <= mph <= 50. Pickup time defines date and hour.

Usage: python -m analyses.street_space.extract FIRST LAST   (months, e.g. 2017-10 2019-09)
Writes ~/opt/nyc-concordance/street_space/pairs_{FIRST}_{LAST}.csv.gz with columns
d, hh, pu, do, n, s_lt (sum log seconds), s_lt2, s_ld (sum log miles), s_ld2, s_mi, s_hr
"""
from __future__ import annotations

import sys

import duckdb
import pandas as pd

from analyses.street_space.common import PAIRS, TLC, GROUPS, pair_group, all_zones


def main(first, last):
    PAIRS.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    z = ",".join(map(str, all_zones()))
    out = []
    for m in [str(p)[:7] for p in pd.period_range(first, last, freq="M")]:
        f = TLC / f"yellow_tripdata_{m}.parquet"
        start = pd.Timestamp(m + "-01")
        end = start + pd.offsets.MonthBegin(1)
        df = con.execute(f"""
          with t as (select PULocationID pu, DOLocationID dol, trip_distance dist, tpep_pickup_datetime ts,
                            date_diff('second', tpep_pickup_datetime, tpep_dropoff_datetime) dur_s
                     from read_parquet('{f}')
                     where tpep_pickup_datetime >= TIMESTAMP '{start}' and tpep_pickup_datetime < TIMESTAMP '{end}'
                       and PULocationID in ({z}) and DOLocationID in ({z}))
          select cast(ts as date) d, hour(ts) hh, pu, dol as "do", count(*) n,
                 sum(ln(dur_s)) s_lt, sum(ln(dur_s)*ln(dur_s)) s_lt2,
                 sum(ln(dist)) s_ld, sum(ln(dist)*ln(dist)) s_ld2,
                 sum(dist) s_mi, sum(dur_s)/3600.0 s_hr
          from t
          where dist > 0 and dist <= 50 and dur_s between 60 and 10800 and dist/(dur_s/3600.0) between 0.5 and 50
          group by 1,2,3,4""").df()
        df["g"] = [pair_group(a, b) for a, b in zip(df.pu, df["do"])]
        df = df[df.g.notna()]
        out.append(df)
        print(m, len(df), int(df.n.sum()), flush=True)
    pd.concat(out).to_csv(PAIRS / f"pairs_{first}_{last}.csv.gz", index=False)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
