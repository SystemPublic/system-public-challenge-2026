"""Build the daily-by-hour panels the simulator is fitted on.

Three series for the Manhattan zone south of 60th Street, each by date and hour:
  entries   MTA Congestion Relief Zone vehicle entries (data.ny.gov t6yz-b64h),
            split into taxi and for-hire vehicles and all other classes
  speed     yellow-taxi trips that start and end in the zone (TLC monthly trip
            files, the R1 filter of analyses/reproduction/mmr_cbd_speed.py):
            trips, miles and hours, so speed = miles / hours
  ems       EMS incidents in community districts 101-106 (76xm-jjuj): count and
            mean travel time of the first unit, all incidents and the
            life-threatening segments (initial severity 1 to 3), and cardiac arrests

The period is set on the command line so that the calibration data can be built
without reading the held-out months:
  python -m analyses.simulate.build_data calib     # to 2025-12-31
  python -m analyses.simulate.build_data holdout   # 2026-01-01 to 2026-06-30
Run the second only after claims/registered/sim-crz-holdout-2026.json is pushed.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import duckdb
import pandas as pd

from analyses.mobility.common import nys
from analyses.reproduction.register_mmr_cbd_speed import CBD_ZONES, FEDERAL_HOLIDAYS_OBSERVED
from concord import socrata

ROOT = Path(__file__).resolve().parents[2]
DER = ROOT / "data" / "derived" / "simulate"
TLC = Path.home() / "opt" / "nyc-concordance" / "tlc_yellow"
PERIODS = {"calib": ("2024-01-01", "2026-01-01"), "holdout": ("2026-01-01", "2026-07-01")}
CBD_CD = ("101", "102", "103", "104", "105", "106")


def entries(lo, hi):
    out, srcs = [], []
    for m in pd.period_range(max(lo, "2025-01-01")[:7], pd.Timestamp(hi) - pd.Timedelta(days=1), freq="M"):
        a, b = m.start_time, (m + 1).start_time
        rows, src = nys("t6yz-b64h",
                        select="toll_date, hour_of_day, vehicle_class, sum(crz_entries) as e, sum(excluded_roadway_entries) as x",
                        where=f"toll_date >= '{a:%Y-%m-%d}T00:00:00' and toll_date < '{b:%Y-%m-%d}T00:00:00'",
                        group="toll_date, hour_of_day, vehicle_class", limit=50000)
        out += rows
        srcs.append(src)
    df = pd.DataFrame(out)
    df["date"] = df.toll_date.str[:10]
    df["hour"] = df.hour_of_day.astype(int)
    df["e"] = df.e.astype(float)
    df["tlc"] = df.vehicle_class.str.startswith("TLC")
    df["truck"] = df.vehicle_class.str[0].isin(["2", "3"])
    g = df.groupby(["date", "hour"]).apply(lambda d: pd.Series({
        "entries": d.e.sum(), "entries_tlc": d.e[d.tlc].sum(), "entries_truck": d.e[d.truck].sum(),
        "entries_car": d.e[d.vehicle_class.str[0] == "1"].sum()}), include_groups=False).reset_index()
    return g, srcs


def speed(lo, hi):
    con = duckdb.connect()
    cbd = ",".join(map(str, CBD_ZONES))
    parts = []
    for m in pd.period_range(lo[:7], pd.Timestamp(hi) - pd.Timedelta(days=1), freq="M"):
        f = TLC / f"yellow_tripdata_{m}.parquet"
        a, b = m.start_time, (m + 1).start_time
        parts.append(f"""
          select cast(tpep_pickup_datetime as date) as "date", hour(tpep_pickup_datetime) as "hour",
                 trip_distance as dist, date_diff('second', tpep_pickup_datetime, tpep_dropoff_datetime) as dur_s
          from read_parquet('{f}')
          where tpep_pickup_datetime >= TIMESTAMP '{a}' and tpep_pickup_datetime < TIMESTAMP '{b}'
            and PULocationID in ({cbd}) and DOLocationID in ({cbd})""")
    q = f"""select "date", "hour", count(*) as trips, sum(dist) as miles, sum(dur_s)/3600.0 as "hours"
            from ({' union all '.join(parts)})
            where dist > 0 and dist <= 50 and dur_s between 60 and 10800 and dist / (dur_s / 3600.0) between 0.5 and 50
            group by 1, 2 order by 1, 2"""
    df = con.execute(q).df()
    df["date"] = df.date.astype(str)
    return df, [{"kind": "tlc-trip-record-files", "months": f"{lo[:7]} to {str(pd.Timestamp(hi) - pd.Timedelta(days=1))[:7]}",
                 "url": "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_YYYY-MM.parquet",
                 "filter": "pickup and drop-off in the 38 zone taxi zones; R1 trip filter of repro-mmr-cbd-speed"}]


def ems(lo, hi):
    out, srcs = [], []
    cds = ",".join(f"'{c}'" for c in CBD_CD)
    for m in pd.period_range(lo[:7], pd.Timestamp(hi) - pd.Timedelta(days=1), freq="M"):
        a, b = m.start_time, (m + 1).start_time
        for name, extra in (("all", ""), ("lt", " and initial_severity_level_code in ('1','2','3')"),
                            ("arrest", " and final_call_type = 'ARREST'")):
            rows, src = socrata.query(
                "76xm-jjuj",
                select="date_trunc_ymd(incident_datetime) as d, date_extract_hh(incident_datetime) as h, count(*) as n, "
                       "avg(incident_travel_tm_seconds_qy) as travel_s, avg(incident_response_seconds_qy) as response_s",
                where=f"incident_datetime >= '{a:%Y-%m-%d}T00:00:00' and incident_datetime < '{b:%Y-%m-%d}T00:00:00' "
                      f"and communitydistrict in ({cds}) and valid_incident_rspns_time_indc = 'Y'{extra}",
                group="d, h", limit=50000)
            for r in rows:
                r["kind"] = name
            out += rows
            srcs.append(src)
    df = pd.DataFrame(out)
    df["date"] = df.d.str[:10]
    df["hour"] = df.h.astype(int)
    for c in ("n", "travel_s", "response_s"):
        df[c] = df[c].astype(float)
    w = df.pivot_table(index=["date", "hour"], columns="kind", values=["n", "travel_s", "response_s"])
    w.columns = [f"ems_{a}_{b}" for a, b in w.columns]
    return w.reset_index(), srcs


def main(which):
    lo, hi = PERIODS[which]
    DER.mkdir(parents=True, exist_ok=True)
    e, s1 = entries(lo, hi)
    v, s2 = speed(lo, hi)
    m, s3 = ems(lo, hi)
    df = v.merge(e, on=["date", "hour"], how="outer").merge(m, on=["date", "hour"], how="outer").sort_values(["date", "hour"])
    df["holiday"] = df.date.isin(set(FEDERAL_HOLIDAYS_OBSERVED))
    df.to_csv(DER / f"panel_{which}.csv", index=False)
    slim = lambda ss: [{k: s.get(k) for k in ("dataset", "name", "url", "rows_updated_at", "fetched")} for s in ss[-1:]] \
        + [{"n_queries": len(ss)}]
    (DER / f"panel_{which}_sources.json").write_text(json.dumps(
        {"period": [lo, hi], "entries": slim(s1), "speed": s2, "ems": slim(s3)}, indent=1))
    print(which, len(df), df.date.min(), df.date.max())


if __name__ == "__main__":
    main(sys.argv[1])
