"""Cross-checks for repro-mmr-cbd-speed: Socrata copies of the 2024 and 2025 trip
records against the parquet files, and the MTA monthly CBD speed series (6p29-6xqn).

Run after mmr_cbd_speed.py:
  ~/.venvs/nyc-concordance/bin/python -m analyses.reproduction.mmr_cbd_speed_checks
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from concord import socrata
from analyses.mobility import common
from analyses.reproduction.register_mmr_cbd_speed import CBD_ZONES

ROOT = Path(__file__).resolve().parents[2]
DER = ROOT / "data" / "derived" / "reproduction"
DATASETS = {"2024": "rwwi-khbc", "2025": "irx2-vgm4"}


def socrata_check():
    zones = ",".join(f"'{z}'" for z in CBD_ZONES)
    out, srcs = [], []
    for year, ds in DATASETS.items():
        where = (f"tpep_pickup_datetime >= '{year}-01-01T00:00:00' and tpep_pickup_datetime < '{int(year)+1}-01-01T00:00:00' "
                 f"and pulocationid in ({zones}) and dolocationid in ({zones}) "
                 "and date_extract_dow(tpep_pickup_datetime) between 1 and 5 "
                 "and date_extract_hh(tpep_pickup_datetime) between 8 and 17")
        rows, src = socrata.query(ds, select="date_trunc_ym(tpep_pickup_datetime) as month, count(*) as n, sum(trip_distance) as miles",
                                  where=where, group="month", order="month")
        for r in rows:
            out.append({"month": r["month"][:7], "n_socrata": int(r["n"]), "miles_socrata": float(r["miles"])})
        srcs.append(src)
    soc = pd.DataFrame(out)
    pq = pd.read_csv(DER / "mmr_cbd_speed_parquet_daily_check.csv").groupby("month")[["n", "miles"]].sum().reset_index()
    pq.columns = ["month", "n_parquet", "miles_parquet"]
    m = soc.merge(pq, on="month", how="outer")
    m["n_diff_pct"] = 100 * (m.n_socrata / m.n_parquet - 1)
    m["miles_diff_pct"] = 100 * (m.miles_socrata / m.miles_parquet - 1)
    m.to_csv(DER / "mmr_cbd_speed_socrata_check.csv", index=False)
    return m, srcs


def mta_series():
    rows, src = common.nys("6p29-6xqn", select="month, zone, zonal_speed", order="month", limit=50000)
    df = pd.DataFrame(rows)
    df["zonal_speed"] = df.zonal_speed.astype(float)
    df["month"] = df.month.str[:7]
    df.to_csv(DER / "mta_6p29_monthly.csv", index=False)
    return df, src


def main():
    m, srcs = socrata_check()
    print(m.to_string())
    mta, src = mta_series()
    print(mta.zone.unique())
    sel = mta[(mta.month >= "2023-07") & (mta.month <= "2026-06")].copy()
    sel["fy"] = sel.month.map(lambda s: f"FY{(int(s[:4]) + (1 if int(s[5:7]) >= 7 else 0)) % 100:02d}")
    print(sel.groupby(["zone", "fy"]).zonal_speed.agg(["mean", "count"]).round(3))
    print("last month in 6p29:", mta.month.max())
    (DER / "mmr_cbd_speed_check_sources.json").write_text(json.dumps({"socrata": srcs, "mta": src}, indent=1))


if __name__ == "__main__":
    main()
