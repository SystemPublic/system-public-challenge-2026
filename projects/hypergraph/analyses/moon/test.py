"""Full moon and daily emergencies in New York City (claim moon-full-emergencies).

Usage: python -m analyses.moon.test
Fixed with the registration (rule 9): this script is committed before it is first run.

Exposure. The full-moon instants come from PyEphem (ephem.next_full_moon, UTC) and are converted to the
New York calendar date. F = 1 on that date and on the day before and the day after (3 days per cycle).
Placebo. P = 1 on a 3-day window that recurs every 23 days from 10 January 2006. No effect can exist.
Model. Poisson regression of the daily count on F (or P), day of week, year-by-month fixed effects, a
holiday indicator, daily maximum temperature (linear and squared) and a wet-day indicator.
Newey-West standard errors with 7 lags. Intervals are 95%; the refutation rule uses 98.3% (three outcomes).
Outcomes. (a) shooting incidents, 2006-2025; (b) all EMS incidents, 2017-01-01 to 2026-08-31;
(c) crashes with at least one person injured, 2014-2025.
"""
from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import ephem
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "derived" / "moon"
CRASHES = Path.home() / "opt" / "nyc-concordance" / "turn_restrictions" / "crashes.csv"
BOUNDS = {"shootings": (0.93, 1.07), "ems": (0.98, 1.02), "injury_crashes": (0.97, 1.03)}


def full_moon_dates(start="2005-12-01", end="2026-12-31") -> list[pd.Timestamp]:
    out, d = [], ephem.Date(start.replace("-", "/"))
    stop = ephem.Date(end.replace("-", "/"))
    ny = ZoneInfo("America/New_York")
    while d < stop:
        d = ephem.next_full_moon(d)
        utc = ephem.Date(d).datetime().replace(tzinfo=ZoneInfo("UTC"))
        out.append(pd.Timestamp(utc.astimezone(ny).date()))
        d = ephem.Date(d + 1)
    return out


def exposure(dates: pd.DatetimeIndex) -> pd.DataFrame:
    fm = full_moon_dates()
    win = {m + timedelta(days=k) for m in fm for k in (-1, 0, 1)}
    exact = set(fm)
    k = (dates - pd.Timestamp("2006-01-10")).days % 23
    return pd.DataFrame({"F": [int(d in win) for d in dates], "F0": [int(d in exact) for d in dates],
                         "P": (k < 3).astype(int)}, index=dates)


def load() -> dict[str, pd.DataFrame]:
    w = pd.read_csv(ROOT / "data/derived/heat/shootings_daily.csv", parse_dates=["date"]).set_index("date")
    cov = w[["TMAX", "PRCP", "dow", "month", "year", "hol", "wet"]]
    sh = cov.join(w["n"].rename("y")).loc["2006-01-01":"2025-12-31"]
    e = pd.read_csv(ROOT / "data/derived/health_gaps/ems_daily.csv", parse_dates=["d"])
    e = e.groupby("d")["n_all"].sum().rename("y")
    ems = cov.join(e, how="inner").loc["2017-01-01":"2026-08-31"]
    c = pd.read_csv(CRASHES, usecols=["crash_date", "number_of_persons_injured"])
    c = c[pd.to_numeric(c.number_of_persons_injured, errors="coerce") > 0]
    cd = pd.to_datetime(c.crash_date.str[:10]).value_counts().rename("y")
    cr = cov.join(cd, how="left").loc["2014-01-01":"2025-12-31"]
    cr["y"] = cr["y"].fillna(0)
    return {"shootings": sh, "ems": ems, "injury_crashes": cr}


def fit(df: pd.DataFrame, x: str) -> dict:
    d = df.dropna(subset=["y", "TMAX"]).copy()
    d = d.join(exposure(d.index))
    d["ym"] = d.year.astype(str) + "-" + d.month.astype(str)
    m = smf.glm(f"y ~ {x} + C(dow) + C(ym) + hol + TMAX + I(TMAX**2) + wet", d, family=sm.families.Poisson()).fit(
        cov_type="HAC", cov_kwds={"maxlags": 7})
    b, se = m.params[x], m.bse[x]
    z95, z983 = stats.norm.ppf(0.975), stats.norm.ppf(1 - 0.0167 / 2)
    return {"x": x, "n_days": int(len(d)), "n_exposed_days": int(d[x].sum()), "events": float(d.y.sum()),
            "rr": float(np.exp(b)), "lo": float(np.exp(b - z95 * se)), "hi": float(np.exp(b + z95 * se)),
            "lo983": float(np.exp(b - z983 * se)), "hi983": float(np.exp(b + z983 * se)), "se_log": float(se)}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    res = {}
    for name, df in load().items():
        r = {"full_moon": fit(df, "F"), "placebo_23_day": fit(df, "P"), "full_moon_day_only": fit(df, "F0"),
             "bounds": BOUNDS[name], "first": str(df.index.min().date()), "last": str(df.index.max().date())}
        f = r["full_moon"]
        r["inside_bounds"] = bool(f["lo"] >= BOUNDS[name][0] and f["hi"] <= BOUNDS[name][1])
        r["excludes_one_983"] = bool(f["lo983"] > 1 or f["hi983"] < 1)
        r["placebo_includes_one"] = bool(r["placebo_23_day"]["lo"] <= 1 <= r["placebo_23_day"]["hi"])
        res[name] = r
        print(name, {k: round(v, 4) if isinstance(v, float) else v for k, v in f.items()}, "placebo",
              round(r["placebo_23_day"]["rr"], 4), round(r["placebo_23_day"]["lo"], 4), round(r["placebo_23_day"]["hi"], 4))
    (OUT / "results.json").write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
