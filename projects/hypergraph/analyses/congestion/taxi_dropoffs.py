"""Yellow-taxi drop-offs by date, hour and destination area (any pickup), July 2023 to June 2026,
from the parquet files in ~/opt/nyc-concordance/tlc_yellow/. Exploratory measure of people
arriving in the zone by taxi. Areas: cbd = 38 MTA CBD taxi zones; north = Manhattan zones north
of 60th Street; other = everywhere else. Writes data/derived/congestion/taxi_dropoffs.csv."""
import duckdb
import pandas as pd

from analyses.congestion.common import DER
from analyses.reproduction.register_mmr_cbd_speed import CBD_ZONES
from analyses.reproduction.mmr_cbd_speed import MN_NORTH, TLC

con = duckdb.connect()
cbd, mn = ",".join(map(str, CBD_ZONES)), ",".join(map(str, MN_NORTH))
out = []
for m in [str(p)[:7] for p in pd.period_range("2023-07", "2026-06", freq="M")]:
    start = pd.Timestamp(m + "-01")
    end = start + pd.offsets.MonthBegin(1)
    out.append(con.execute(f"""
      select cast(tpep_dropoff_datetime as date) d, hour(tpep_dropoff_datetime) hh,
             case when DOLocationID in ({cbd}) then 'cbd' when DOLocationID in ({mn}) then 'north' else 'other' end area,
             count(*) n
      from read_parquet('{TLC / f"yellow_tripdata_{m}.parquet"}')
      where tpep_pickup_datetime >= TIMESTAMP '{start}' and tpep_pickup_datetime < TIMESTAMP '{end}'
        and tpep_dropoff_datetime >= TIMESTAMP '{start}' and tpep_dropoff_datetime < TIMESTAMP '{end}' + INTERVAL 1 DAY
      group by 1,2,3 order by 1,2,3""").df())
pd.concat(out).groupby(["d", "hh", "area"], as_index=False).n.sum().to_csv(DER / "taxi_dropoffs.csv", index=False)
print("done")
