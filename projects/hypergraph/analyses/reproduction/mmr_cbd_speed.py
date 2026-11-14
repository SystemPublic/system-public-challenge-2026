"""Compute repro-mmr-cbd-speed under the registered readings R1-R9.

Registration: claims/registered/repro-mmr-cbd-speed.json (committed and pushed
before this script was written). Trip data: TLC yellow taxi monthly parquet
files, July 2023 to June 2026, downloaded to ~/opt/nyc-concordance/tlc_yellow/
(outside Dropbox; fetched by `fetch()` if absent). Writes
data/derived/reproduction/mmr_cbd_speed_*.csv and .json.

Run: ~/.venvs/nyc-concordance/bin/python -m analyses.reproduction.mmr_cbd_speed
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import duckdb
import pandas as pd

from analyses.reproduction.register_mmr_cbd_speed import CBD_ZONES, FEDERAL_HOLIDAYS_OBSERVED, MAJOR6

ROOT = Path(__file__).resolve().parents[2]
DER = ROOT / "data" / "derived" / "reproduction"
DER.mkdir(parents=True, exist_ok=True)
TLC = Path.home() / "opt" / "nyc-concordance" / "tlc_yellow"
BASE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data/"
MONTHS = [str(p)[:7] for p in pd.period_range("2023-07", "2026-06", freq="M")]

# Manhattan zones north of 60th St (descriptive comparison only; parks and islands left out)
MN_NORTH = [24, 41, 42, 74, 75, 116, 120, 127, 140, 141, 142, 143, 151, 152, 153, 166,
            236, 237, 238, 239, 243, 244, 262, 263]


def fetch() -> list[dict]:
    """Download missing monthly files and return a version record for each."""
    TLC.mkdir(parents=True, exist_ok=True)
    recs = []
    for m in MONTHS:
        name = f"yellow_tripdata_{m}.parquet"
        f = TLC / name
        if not f.exists():
            subprocess.run(["curl", "-sS", "-o", str(f), "-D", str(f) + ".headers", BASE_URL + name], check=True)
        hdr = {}
        h = Path(str(f) + ".headers")
        if h.exists():
            for line in h.read_text().splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    hdr[k.strip().lower()] = v.strip()
        recs.append({"kind": "tlc-trip-record-file", "url": BASE_URL + name, "month": m,
                     "last_modified": hdr.get("last-modified"), "etag": hdr.get("etag"),
                     "bytes": f.stat().st_size, "fetched_local_copy": "~/opt/nyc-concordance/tlc_yellow/" + name})
    return recs


def fy(month: str) -> str:
    y, m = int(month[:4]), int(month[5:7])
    return f"FY{(y + 1 if m >= 7 else y) % 100:02d}"


def build(con):
    """One table of weekday 08-17h pickups, all zones, with flags. Holidays are flagged, not dropped."""
    files = [str(TLC / f"yellow_tripdata_{m}.parquet") for m in MONTHS]
    parts = []
    for m, f in zip(MONTHS, files):
        start = pd.Timestamp(m + "-01")
        end = start + pd.offsets.MonthBegin(1)
        parts.append(f"""
          select '{m}' as month, PULocationID pu, DOLocationID dol, passenger_count pax, trip_distance dist,
                 date_diff('second', tpep_pickup_datetime, tpep_dropoff_datetime) dur_s,
                 cast(tpep_pickup_datetime as date) d
          from read_parquet('{f}')
          where tpep_pickup_datetime >= TIMESTAMP '{start}' and tpep_pickup_datetime < TIMESTAMP '{end}'
            and dayofweek(tpep_pickup_datetime) between 1 and 5
            and hour(tpep_pickup_datetime) between 8 and 17""")
    con.execute("create or replace table t as " + " union all ".join(parts))
    fed = ",".join(f"DATE '{d}'" for d in FEDERAL_HOLIDAYS_OBSERVED)
    maj = ",".join(f"DATE '{d}'" for d in MAJOR6)
    cbd = ",".join(map(str, CBD_ZONES))
    mn = ",".join(map(str, MN_NORTH))
    con.execute(f"""create or replace table t2 as select *,
        d in ({fed}) as hol_fed, d in ({maj}) as hol_maj6,
        pu in ({cbd}) as pu_cbd, dol in ({cbd}) as do_cbd,
        pu in ({mn}) as pu_mn, dol in ({mn}) as do_mn,
        case when dur_s > 0 then dist / (dur_s / 3600.0) end as mph,
        (dist > 0 and dist <= 50 and dur_s between 60 and 10800 and dist / (dur_s / 3600.0) between 0.5 and 50) as f1,
        (dist > 0 and dur_s > 0 and dist / (dur_s / 3600.0) < 100) as f0,
        (dist between 0.2 and 20 and dur_s between 120 and 5400 and dist / (dur_s / 3600.0) between 1 and 35) as f2
      from t""")


READINGS = {
    "R1": "pu_cbd and do_cbd and not hol_fed and f1",
    "R2": "pu_cbd and do_cbd and not hol_fed and f1",
    "R3": "pu_cbd and do_cbd and not hol_fed and f1",
    "R4": "pu_cbd and not hol_fed and f1",
    "R5": "(pu_cbd or do_cbd) and not hol_fed and f1",
    "R6": "pu_cbd and do_cbd and not hol_fed and f0",
    "R7": "pu_cbd and do_cbd and not hol_fed and f2",
    "R8": "pu_cbd and do_cbd and not hol_maj6 and f1 and pax >= 1",
    "R9": "pu_cbd and do_cbd and not hol_fed and f1",
    # descriptive comparison areas (not readings)
    "MN_NORTH": "pu_mn and do_mn and not hol_fed and f1",
    "REST": "not pu_cbd and not do_cbd and pu < 264 and dol < 264 and not hol_fed and f1",
}


def compute(con):
    monthly = []
    for r, w in READINGS.items():
        if r in ("R2", "R3", "R9"):
            continue
        df = con.execute(f"""select month, count(*) as n, sum(dist) as miles, sum(dur_s)/3600.0 as hours,
                                    avg(mph) as mean_mph, median(mph) as median_mph
                             from t2 where {w} group by month order by month""").df()
        df["area"] = r
        monthly.append(df)
    monthly = pd.concat(monthly)
    monthly["ratio_mph"] = monthly.miles / monthly.hours
    monthly["fy"] = monthly.month.map(fy)

    rows = []
    for r, w in READINGS.items():
        src = "R1" if r in ("R2", "R3", "R9") else r
        sub = monthly[monthly.area == src]
        for f, g in sub.groupby("fy"):
            if r == "R2":
                v = con.execute(f"select avg(mph) from t2 where {w} and month in ({','.join(repr(m) for m in g.month)})").fetchone()[0]
            elif r == "R3":
                v = con.execute(f"select median(mph) from t2 where {w} and month in ({','.join(repr(m) for m in g.month)})").fetchone()[0]
            elif r == "R9":
                v = g.ratio_mph.mean()
            else:
                v = g.miles.sum() / g.hours.sum()
            rows.append({"reading": r, "fy": f, "mph": round(float(v), 3), "n_trips": int(g.n.sum())})
    fyt = pd.DataFrame(rows)

    # halves of FY25 and calendar years, R1 and comparisons
    halves = []
    for a in ("R1", "MN_NORTH", "REST"):
        sub = monthly[monthly.area == a]
        for lab, ms in {
            "FY24 H1 (Jul-Dec 2023)": [m for m in MONTHS if "2023-07" <= m <= "2023-12"],
            "FY24 H2 (Jan-Jun 2024)": [m for m in MONTHS if "2024-01" <= m <= "2024-06"],
            "FY25 H1 (Jul-Dec 2024, untolled)": [m for m in MONTHS if "2024-07" <= m <= "2024-12"],
            "FY25 H2 (Jan-Jun 2025, tolled)": [m for m in MONTHS if "2025-01" <= m <= "2025-06"],
            "FY26 H1 (Jul-Dec 2025)": [m for m in MONTHS if "2025-07" <= m <= "2025-12"],
            "FY26 H2 (Jan-Jun 2026)": [m for m in MONTHS if "2026-01" <= m <= "2026-06"],
            "CY2024": [m for m in MONTHS if m.startswith("2024")],
            "CY2025": [m for m in MONTHS if m.startswith("2025")],
        }.items():
            g = sub[sub.month.isin(ms)]
            halves.append({"area": a, "period": lab, "mph": round(g.miles.sum() / g.hours.sum(), 3), "n_trips": int(g.n.sum())})
    halves = pd.DataFrame(halves)
    return monthly, fyt, halves


def parquet_check(con) -> pd.DataFrame:
    """Unfiltered counts and miles for the Socrata comparison (CBD both ends, weekday 08-17h, no holiday rule)."""
    return con.execute("""select month, d, count(*) as n, sum(dist) as miles from t2
                          where pu_cbd and do_cbd and month >= '2024-01' and month <= '2025-12'
                          group by month, d order by d""").df()


def main():
    recs = fetch()
    con = duckdb.connect()
    build(con)
    monthly, fyt, halves = compute(con)
    chk = parquet_check(con)
    monthly.to_csv(DER / "mmr_cbd_speed_monthly.csv", index=False)
    fyt.to_csv(DER / "mmr_cbd_speed_fy.csv", index=False)
    halves.to_csv(DER / "mmr_cbd_speed_periods.csv", index=False)
    chk.to_csv(DER / "mmr_cbd_speed_parquet_daily_check.csv", index=False)
    (DER / "mmr_cbd_speed_files.json").write_text(json.dumps(recs, indent=1))
    print(fyt.pivot(index="reading", columns="fy", values="mph"))
    print(halves.pivot(index="period", columns="area", values="mph"))


if __name__ == "__main__":
    main()
