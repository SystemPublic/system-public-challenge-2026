"""Yellow-taxi trip speeds by date, hour and area from the TLC monthly parquet files in
~/opt/nyc-concordance/tlc_yellow/ (July 2023 to June 2026; the files and their version
records are those of repro-mmr-cbd-speed, data/derived/reproduction/mmr_cbd_speed_files.json).

Areas: cbd = pickup and drop-off both in the 38 MTA CBD taxi zones; north = both in Manhattan
zones north of 60th Street. Speed of a cell = total miles / total hours. Trip filter f1 of the
reproduction: 0 < miles <= 50, 60 s <= duration <= 3 h, 0.5 <= mph <= 50.

Usage: python -m analyses.congestion.taxi_speed FIRST LAST   (months, e.g. 2023-07 2024-12)
Writes data/derived/congestion/taxi_speed_{FIRST}_{LAST}.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import duckdb
import pandas as pd

from analyses.congestion.common import DER
from analyses.reproduction.register_mmr_cbd_speed import CBD_ZONES
from analyses.reproduction.mmr_cbd_speed import MN_NORTH, TLC


def main(first, last):
    con = duckdb.connect()
    cbd, mn = ",".join(map(str, CBD_ZONES)), ",".join(map(str, MN_NORTH))
    out = []
    for m in [str(p)[:7] for p in pd.period_range(first, last, freq="M")]:
        f = TLC / f"yellow_tripdata_{m}.parquet"
        start = pd.Timestamp(m + "-01")
        end = start + pd.offsets.MonthBegin(1)
        df = con.execute(f"""
          with t as (select PULocationID pu, DOLocationID dol, trip_distance dist, tpep_pickup_datetime ts,
                            date_diff('second', tpep_pickup_datetime, tpep_dropoff_datetime) dur_s
                     from read_parquet('{f}')
                     where tpep_pickup_datetime >= TIMESTAMP '{start}' and tpep_pickup_datetime < TIMESTAMP '{end}')
          select cast(ts as date) d, hour(ts) hh,
                 case when pu in ({cbd}) and dol in ({cbd}) then 'cbd' else 'north' end area,
                 count(*) n, sum(dist) miles, sum(dur_s)/3600.0 hrs
          from t
          where ((pu in ({cbd}) and dol in ({cbd})) or (pu in ({mn}) and dol in ({mn})))
            and dist > 0 and dist <= 50 and dur_s between 60 and 10800 and dist/(dur_s/3600.0) between 0.5 and 50
          group by 1,2,3 order by 1,2,3""").df()
        out.append(df)
        print(m, len(df), flush=True)
    pd.concat(out).to_csv(DER / f"taxi_speed_{first}_{last}.csv", index=False)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
