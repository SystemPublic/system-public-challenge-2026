"""Held-out replication of the 14th Street busway result on high-volume for-hire trips (Uber, Lyft, Via,
Juno; TLC fhvhv_tripdata, from February 2019). Fixed before any FHV trip after September 2019 is read.

Subgroups (from the referee's exploratory split of the yellow-taxi data, critique/street-busway14-crosstown-time.md):
  north: directed pairs between East Chelsea (68) and Stuy Town (224) or Gramercy (107), both ways (4 pairs)
  south: directed pairs between {158, 249, 113} and {79, 4}, both ways (12 pairs)
  control: the c_mid and c_down pairs of analyses.street_space.common
Trips: weekday 07-18 (estimate.SAMPLES['weekday']), filter 0 < trip_miles <= 50, 60 s <= trip_time <= 3 h,
0.5-50 mph, shared rides (shared_match_flag = 'Y') dropped. Outcome: log trip_time (and log trip_miles).

Monthly contrast c_m(g) = mean over pairs in g of pair-demeaned mean log outcome, minus the same over
control pairs (pairs need 20 trips in every month of the input).
Swing(t) = mean c_m over October t to February t+1 minus mean c_m over July to September t.
FHV has no year-earlier months, so the seasonal swing is taken from yellow taxis:
  E_fhv(g) = Swing_fhv(2019, g) - mean(Swing_yellow(2016, g), Swing_yellow(2017, g), Swing_yellow(2018, g)).
Standard error: se^2 = (s_y^2 + r^2) * (1/5 + 1/3), where s_y is the sd of the yellow monthly
year-over-year changes of c(g) from July 2017 to September 2019, and r is the sd of the demeaned monthly
difference c_fhv - c_yellow over February to September 2019 (fleet difference). 95% interval E +/- 1.96 se.

Usage:
  python -m analyses.street_space.fhv extract FIRST LAST
  python -m analyses.street_space.fhv design   (pre-busway FHV months only)
  python -m analyses.street_space.fhv final
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from analyses.street_space.common import DER, PAIRS, all_zones, pair_group
from analyses.street_space.estimate import load, SAMPLES

FHV = Path.home() / "opt" / "nyc-concordance" / "fhvhv_1920"
FHV_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data/fhvhv_tripdata_{m}.parquet"
NORTH = {(68, 224), (224, 68), (68, 107), (107, 68)}
SOUTH = {(a, b) for a in (158, 249, 113) for b in (79, 4)} | {(b, a) for a in (158, 249, 113) for b in (79, 4)}
YELLOW = ["pairs_2016-07_2017-09.csv.gz", "pairs_2017-10_2019-09.csv.gz", "pairs_2019-10_2020-02.csv.gz"]
WINTER, SUMMER = [10, 11, 12, 1, 2], [7, 8, 9]


def extract(first, last):
    con = duckdb.connect()
    z = ",".join(map(str, all_zones()))
    out = []
    for m in [str(p)[:7] for p in pd.period_range(first, last, freq="M")]:
        f = FHV / f"fhvhv_tripdata_{m}.parquet"
        start = pd.Timestamp(m + "-01")
        end = start + pd.offsets.MonthBegin(1)
        df = con.execute(f"""
          with t as (select PULocationID pu, DOLocationID dol, trip_miles dist, trip_time dur_s, pickup_datetime ts
                     from read_parquet('{f}')
                     where pickup_datetime >= TIMESTAMP '{start}' and pickup_datetime < TIMESTAMP '{end}'
                       and PULocationID in ({z}) and DOLocationID in ({z})
                       and coalesce(shared_match_flag, 'N') <> 'Y')
          select cast(ts as date) d, hour(ts) hh, pu, dol as "do", count(*) n,
                 sum(ln(dur_s)) s_lt, sum(ln(dist)) s_ld, sum(dist) s_mi, sum(dur_s)/3600.0 s_hr
          from t
          where dist > 0 and dist <= 50 and dur_s between 60 and 10800 and dist/(dur_s/3600.0) between 0.5 and 50
          group by 1,2,3,4""").df()
        df["g"] = [pair_group(a, b) for a, b in zip(df.pu, df["do"])]
        df = df[df.g.notna()]
        out.append(df)
        print(m, len(df), int(df.n.sum()), flush=True)
    pd.concat(out).to_csv(PAIRS / f"fhv_pairs_{first}_{last}.csv.gz", index=False)


def contrast(df, var, sub):
    x = df[SAMPLES["weekday"](df)].copy()
    x["month"] = x.d.dt.to_period("M").dt.to_timestamp()
    s = x.groupby(["month", "pu", "do", "g"])[[var, "n"]].sum().reset_index()
    s = s[s.n >= 20]
    s = s[s.groupby(["pu", "do"]).month.transform("count") == s.month.nunique()]
    s["m"] = s[var] / s.n
    s["dev"] = s.m - s.groupby(["pu", "do"]).m.transform("mean")
    key = list(zip(s.pu, s["do"]))
    s["sub"] = [("t" if k in sub else None) if g == "t14" else "c" for k, g in zip(key, s.g)]
    s = s[s["sub"].notna()]
    c = s.groupby(["month", "sub"]).dev.mean().unstack("sub")
    npairs = s[s["sub"] == "t"].drop_duplicates(["pu", "do"]).shape[0]
    return (c["t"] - c["c"]), npairs


def swing(c, t):
    w = [pd.Timestamp(f"{t if m >= 10 else t + 1}-{m:02d}-01") for m in WINTER]
    s = [pd.Timestamp(f"{t}-{m:02d}-01") for m in SUMMER]
    if any(k not in c.index for k in w + s):
        return None
    return float(c[w].mean() - c[s].mean())


def run(fhv_files, final=False):
    yl = load([PAIRS / f for f in YELLOW])
    if not final:
        yl = yl[yl.d < "2019-10-01"]
    fv = load([PAIRS / f for f in fhv_files])
    pct = lambda v: None if v is None else round(float(100 * (np.exp(v) - 1)), 3)
    out = {}
    for name, sub in (("north", NORTH), ("south", SOUTH)):
        for var in ("s_lt", "s_ld"):
            cy, npy = contrast(yl, var, sub)
            cf, npf = contrast(fv, var, sub)
            cy.index, cf.index = pd.to_datetime(cy.index), pd.to_datetime(cf.index)
            dy = (cy - cy.shift(12, freq="MS").reindex(cy.index)).dropna()
            s_y = float(dy[(dy.index >= "2017-07-01") & (dy.index <= "2019-09-01")].std(ddof=1))
            common = cf.index[(cf.index >= "2019-02-01") & (cf.index <= "2019-09-01")]
            diff = (cf[common] - cy.reindex(common)).dropna()
            r = float((diff - diff.mean()).std(ddof=1))
            corr = float(np.corrcoef(cf[common].diff().dropna(), cy.reindex(common).diff().dropna())[0, 1])
            se = float(np.sqrt((s_y ** 2 + r ** 2) * (1 / 5 + 1 / 3)))
            sw_y = {t: swing(cy, t) for t in (2016, 2017, 2018, 2019)}
            base = np.mean([sw_y[t] for t in (2016, 2017, 2018)])
            res = {"n_pairs_yellow": npy, "n_pairs_fhv": npf, "s_y": round(s_y, 5), "r_fleet": round(r, 5), "corr_monthly_changes_feb_sep19": round(corr, 3),
                   "se_log": round(se, 5), "swing_yellow_pct": {t: pct(v) for t, v in sw_y.items()},
                   "placebo_yellow_2018_pct": pct(sw_y[2018] - np.mean([sw_y[2016], sw_y[2017]])),
                   "c_fhv_pct": {str(k.date()): pct(v) for k, v in cf.items()},
                   "c_yellow_feb_sep19_pct": {str(k.date()): pct(cy[k]) for k in common}}
            if final:
                e = swing(cf, 2019) - base
                res.update({"E_pct": pct(e), "lo_pct": pct(e - 1.96 * se), "hi_pct": pct(e + 1.96 * se), "z": round(e / se, 2),
                            "swing_fhv_2019_pct": pct(swing(cf, 2019))})
            out[f"{name}_{var}"] = res
    return out


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "extract":
        extract(sys.argv[2], sys.argv[3])
    elif cmd == "design":
        res = run(["fhv_pairs_2019-02_2019-09.csv.gz"])
        (DER / "fhv_design.json").write_text(json.dumps(res, indent=1))
        for k, v in res.items():
            print(k, {kk: vv for kk, vv in v.items() if not kk.startswith("c_")})
    elif cmd == "final":
        res = run(["fhv_pairs_2019-02_2019-09.csv.gz", "fhv_pairs_2019-10_2020-02.csv.gz"], final=True)
        (DER / "fhv_final.json").write_text(json.dumps(res, indent=1))
        for k, v in res.items():
            print(k, {kk: vv for kk, vv in v.items() if not kk.startswith("c_")})
