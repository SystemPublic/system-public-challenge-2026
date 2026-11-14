"""transfer-chicago-weekday-pattern: Monday/Friday deficit of CTA 'L' station entries, Loop and rest of system.

Registered in claims/registered/transfer-chicago-weekday-pattern.json before any Chicago ridership value was read.
Run: ~/.venvs/nyc-concordance/bin/python -m analyses.transfer.chicago_weekday
"""
from __future__ import annotations

import calendar
import datetime as dt
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

import analyses.transit.weekday_pattern as w  # sets DOMAIN to data.ny.gov on import
import concord.socrata as soc

soc.DOMAIN = "https://data.cityofchicago.org"
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "derived" / "graph" / "transfer_chicago"
OUT.mkdir(parents=True, exist_ok=True)
SEED = 20261112
SRC: list[dict] = []
BOX = (41.8750, 41.8870, -87.6345, -87.6255)
BOX_WIDE = (41.8740, 41.8900, -87.6345, -87.6255)


def stations():
    rows, src = soc.query("8pix-ypme", select="map_id,station_name,location", limit=5000)
    SRC.append(src)
    st = defaultdict(list)
    for r in rows:
        st[(int(r["map_id"]), r["station_name"])].append((float(r["location"]["latitude"]), float(r["location"]["longitude"])))
    tab = {k: (np.mean([a for a, b in v]), np.mean([b for a, b in v])) for k, v in st.items()}

    def pick(b):
        return sorted(k for k, (la, lo) in tab.items() if b[0] <= la <= b[1] and b[2] <= lo <= b[3])
    return pick(BOX), pick(BOX_WIDE)


def per_station_daily(ids, start="2018-01-01", end="2026-12-31"):
    inl = ",".join(str(i) for i in ids)
    rows, src = soc.query_all("5neh-572f", select="date, station_id, rides",
                              where=f"station_id in ({inl}) AND date between '{start}T00:00:00' and '{end}T23:59:59'", order="date,station_id")
    SRC.append(src)
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"]).dt.date
    df["station_id"] = df["station_id"].astype(int)
    df["rides"] = df["rides"].astype(float)
    return df


def system_daily(start="2018-01-01", end="2026-12-31"):
    rows, src = soc.query_all("5neh-572f", select="date, sum(rides) as n, count(distinct station_id) as k",
                              where=f"date between '{start}T00:00:00' and '{end}T23:59:59'", group="date", order="date")
    SRC.append(src)
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"]).dt.date
    return df.set_index("date")


def recent_period(last: dt.date):
    if last >= dt.date(2026, 10, 31):
        return dt.date(2025, 11, 1), dt.date(2026, 10, 31)
    end = last if last.day == calendar.monthrange(last.year, last.month)[1] else dt.date(last.year, last.month, 1) - dt.timedelta(1)
    sy, sm = (end.year, end.month - 11) if end.month > 11 else (end.year - 1, end.month + 1)
    return dt.date(sy, sm, 1), end


def main():
    rng = np.random.default_rng(SEED)
    loop, wide = stations()
    (OUT / "loop_stations.json").write_text(json.dumps({"rule_box_lat_lon": BOX, "loop": [[i, n] for i, n in loop],
                                                         "wide_box": BOX_WIDE, "wide": [[i, n] for i, n in wide]}, indent=1))
    ids_wide = sorted({i for i, _ in wide})
    ids_loop = sorted({i for i, _ in loop})
    PS = per_station_daily(ids_wide)
    SYS = system_daily()
    last = max(SYS.index)
    recent = recent_period(last)
    loop_daily = PS[PS.station_id.isin(ids_loop)].groupby("date")["rides"].sum()
    wide_daily = PS.groupby("date")["rides"].sum()
    tot = SYS["n"].astype(float)
    rest = tot - loop_daily.reindex(tot.index).fillna(0)
    periods = {"2018": (dt.date(2018, 1, 1), dt.date(2018, 12, 31)), "2019": (dt.date(2019, 1, 1), dt.date(2019, 12, 31)),
               "2025": (dt.date(2025, 1, 1), dt.date(2025, 12, 31)), "recent": recent}
    W = {k: w.retained_weeks(*v) for k, v in periods.items()}
    out = {"stations_loop": [[i, n] for i, n in loop], "n_loop": len(ids_loop), "data_last_date": str(last), "recent_period": [str(recent[0]), str(recent[1])],
           "n_weeks": {k: len(v) for k, v in W.items()}, "n_stations_total_by_year": {}}

    def mat(series, per):
        M = w.week_matrix(series, W[per])
        if np.isnan(M).any():
            raise RuntimeError(f"missing days {per}: {int(np.isnan(M).sum())}")
        return M
    D, s_rec, s_19 = w.delta(mat(loop_daily, "recent"), mat(loop_daily, "2019"), rng)
    out["loop"] = {"recent": s_rec, "y2019": s_19, "delta": D}
    P, _, s_18 = w.delta(mat(loop_daily, "2019"), mat(loop_daily, "2018"), rng)
    out["placebo_2019_minus_2018"] = {"delta": P, "y2018": s_18}
    R, r_rec, r_19 = w.delta(mat(rest, "recent"), mat(rest, "2019"), rng)
    out["rest"] = {"recent": r_rec, "y2019": r_19, "delta": R}
    A, a_rec, a_19 = w.delta(mat(tot, "recent"), mat(tot, "2019"), rng)
    out["system"] = {"recent": a_rec, "y2019": a_19, "delta": A}
    # Loop minus rest difference in Delta (bootstrap, independent resamples)
    bl = (w.boot(mat(loop_daily, "recent"), rng)["mf"] - w.boot(mat(loop_daily, "2019"), rng)["mf"]) * 100
    br = (w.boot(mat(rest, "recent"), rng)["mf"] - w.boot(mat(rest, "2019"), rng)["mf"]) * 100
    out["loop_minus_rest_delta"] = {"estimate": D["estimate"] - R["estimate"], "ci": w.ci(bl - br)}
    out["trajectory"] = {k: w.summarise(mat(loop_daily, k), rng)[0] for k in ("2018", "2019", "2025", "recent")}
    out["trajectory_rest"] = {k: w.summarise(mat(rest, k), rng)[0] for k in ("2018", "2019", "2025", "recent")}
    # sensitivities
    d, a, c = w.delta(mat(loop_daily, "recent"), mat(loop_daily, "2019"), rng, agg=np.median)
    out["S1_median"] = {"recent": a, "y2019": c, "delta": d}
    s2 = {}
    for k in ("recent", "2019"):
        a0, b0 = periods[k]
        days = [x for x in loop_daily.index if a0 <= x <= b0 and x.weekday() < 5 and not w.excluded_day(x)]
        m = pd.Series({x: loop_daily[x] for x in days}).groupby(lambda x: x.weekday()).mean()
        mid = m[[1, 2, 3]].mean()
        s2[k] = {"n_days": len(days), "mf": float(100 * (1 - (m[0] + m[4]) / (2 * mid)))}
    s2["delta"] = s2["recent"]["mf"] - s2["2019"]["mf"]
    out["S2_days_only"] = s2
    d, a, c = w.delta(mat(loop_daily, "2025"), mat(loop_daily, "2019"), rng)
    out["S3_calendar_2025"] = {"recent": a, "y2019": c, "delta": d}
    strike = {m for m in W["2019"] if not any(dt.date(2019, 10, 17) <= m + dt.timedelta(i) <= dt.date(2019, 11, 1) for i in range(5))}
    keep = [i for i, m in enumerate(W["2019"]) if m in strike]
    M19 = mat(loop_daily, "2019")[keep]
    d, a, c = w.delta(mat(loop_daily, "recent"), M19, rng)
    out["S4_no_strike_weeks"] = {"n_weeks_2019": len(keep), "delta": d, "y2019": c}
    # S5 station-level
    per = {}
    for k in ("2019", "recent"):
        per[k] = {}
        piv = PS[PS.station_id.isin(ids_loop)].pivot_table(index="date", columns="station_id", values="rides", aggfunc="sum")
        for sid in ids_loop:
            if sid in piv:
                M = w.week_matrix(piv[sid], W[k])
                ok = ~np.isnan(M).any(axis=1) & (M[:, 1:4].mean(axis=1) > 0)
                if ok.sum() >= 20:
                    per[k][sid] = w.stats(M[ok])["mf"] * 100
    both = sorted(set(per["2019"]) & set(per["recent"]))
    rr, bb = np.array([per["recent"][s] for s in both]), np.array([per["2019"][s] for s in both])
    names = {i: n for i, n in loop}
    out["S5_station_level"] = {"n": len(both), "recent_median": float(np.median(rr)), "recent_iqr": [float(np.percentile(rr, 25)), float(np.percentile(rr, 75))],
                               "y2019_median": float(np.median(bb)), "y2019_iqr": [float(np.percentile(bb, 25)), float(np.percentile(bb, 75))],
                               "n_delta_positive": int(((rr - bb) > 0).sum()),
                               "by_station": {names[s]+f" ({s})": {"y2019": round(per["2019"][s], 2), "recent": round(per["recent"][s], 2)} for s in both}}
    d, a, c = w.delta(mat(wide_daily, "recent"), mat(wide_daily, "2019"), rng)
    out["S6_wide_box"] = {"n_stations": len(ids_wide), "recent": a, "y2019": c, "delta": d}
    out["levels_mean_weekday_entries"] = {"loop_recent": float(mat(loop_daily, "recent").mean()), "loop_2019": float(mat(loop_daily, "2019").mean()),
                                          "system_recent": float(mat(tot, "recent").mean()), "system_2019": float(mat(tot, "2019").mean())}
    out["sources"] = SRC
    (OUT / "weekday_results.json").write_text(json.dumps(out, indent=1, default=str))
    pd.DataFrame({"loop": loop_daily, "system": tot, "rest": rest}).to_csv(OUT / "chicago_daily_entries.csv")
    print(json.dumps({k: v for k, v in out.items() if k not in ("sources", "S5_station_level", "stations_loop")}, indent=1, default=str)[:7000])


if __name__ == "__main__":
    main()
