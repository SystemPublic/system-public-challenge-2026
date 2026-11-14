"""Registered tests graph-triad-hot-asthma-absence and graph-triad-cold-asthma-absence.
Citywide daily school absence against Central Park temperature, model as registered."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
import statsmodels.formula.api as smf
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from concord import socrata, noaa
OUT = ROOT / "data" / "derived" / "graph" / "triads"
DS = ["xwxx-rnki", "wpqj-3buw", "pffu-gbfi", "3y5p-x48f", "x3bb-kg5j"]

def load():
    frames, sources = [], []
    for ds in DS:
        try:
            rows, src = socrata.query(ds, select="date, sum(absent) as absent, sum(enrolled) as enrolled, sum(present) as present, count(*) as schools", group="date", limit=5000)
        except RuntimeError:  # one file stores the counts as text
            rows, src = socrata.query(ds, select="date, sum(absent::number) as absent, sum(enrolled::number) as enrolled, sum(present::number) as present, count(*) as schools", group="date", limit=5000)
        sources.append(src)
        d = pd.DataFrame(rows)
        d["date"] = pd.to_datetime(d["date"], format="%m/%d/%Y" if "/" in str(d["date"].iloc[0]) else "%Y%m%d")
        for c in ("absent", "enrolled", "present", "schools"):
            d[c] = pd.to_numeric(d[c])
        d["dataset"] = ds
        frames.append(d)
    a = pd.concat(frames).sort_values("date").drop_duplicates("date", keep="last").set_index("date")
    w, wsrc = noaa.daily("central_park")
    a = a.join(w[["TMAX", "TMIN", "PRCP", "SNOW"]])
    a["sy"] = np.where(a.index.month >= 8, a.index.year, a.index.year - 1)
    return a, sources + [wsrc]

def prepare(a):
    n0 = len(a)
    a = a[a.index.dayofweek < 5].copy()
    med = a.groupby("sy")["enrolled"].transform("median")
    a["rate"] = a["absent"] / a["enrolled"]
    excl_enrol = int((a["enrolled"] < 0.8 * med).sum()); excl_rate = int(((a["enrolled"] >= 0.8 * med) & (a["rate"] > 0.30)).sum())
    a = a[(a["enrolled"] >= 0.8 * med) & (a["rate"] <= 0.30) & (a["rate"] > 0)].copy()
    days = a.index
    prev_bd = days - pd.tseries.offsets.BDay(1); next_bd = days + pd.tseries.offsets.BDay(1)
    a["adjacent"] = (~prev_bd.isin(days) | ~next_bd.isin(days)).astype(int)
    a["rank_from_end"] = a.groupby("sy").cumcount(ascending=False)
    a["last5"] = (a["rank_from_end"] < 5).astype(int)
    a["y"] = np.log(a["rate"]); a["dow"] = a.index.dayofweek; a["week"] = a.index.isocalendar().week.astype(int).values
    a["wet"] = (a["PRCP"] >= 10).astype(int)
    snow = (a["SNOW"].fillna(0) > 0)
    a["snow"] = (snow | snow.shift(1, fill_value=False)).astype(int)
    for k in (0, 1, 2):
        a[f"TMAX_l{k}"] = a["TMAX"].shift(k)
    return a, {"rows_before": n0, "excluded_low_enrolment": excl_enrol, "excluded_rate_above_30pct": excl_rate, "school_days_kept": len(a)}

def fit(d, expo, extra):
    f = f"y ~ {expo} + C(sy) + C(dow) + C(week) + adjacent + last5 + {extra}"
    m = smf.ols(f, data=d).fit(cov_type="HAC", cov_kwds={"maxlags": 5})
    b, se = m.params[expo], m.bse[expo]
    return {"ratio": float(np.exp(b)), "lo": float(np.exp(b - 1.96 * se)), "hi": float(np.exp(b + 1.96 * se)), "log": float(b), "se_log": float(se),
            "n": int(m.nobs), "n_exposed": int(d[expo].sum()) if d[expo].max() <= 1 else None}

if __name__ == "__main__":
    a, sources = load()
    a, counts = prepare(a)
    res = {"counts": counts, "span": [str(a.index.min().date()), str(a.index.max().date())], "mean_absence_rate": float(a["rate"].mean())}
    hot = a[a.index.month.isin([5, 6, 9])].copy(); cold = a[a.index.month.isin([12, 1, 2])].copy()
    hot["x"] = (hot["TMAX"] >= 30).astype(int); cold["x"] = (cold["TMAX"] <= 0).astype(int)
    hot["x02"] = ((hot[["TMAX_l0", "TMAX_l1", "TMAX_l2"]] >= 30).any(axis=1)).astype(int); cold["x02"] = ((cold[["TMAX_l0", "TMAX_l1", "TMAX_l2"]] <= 0).any(axis=1)).astype(int)
    hot["t5"] = hot["TMAX"] / 5; cold["t5"] = cold["TMAX"] / 5
    res["hot"] = {"primary": fit(hot, "x", "wet"), "lag0_2": fit(hot, "x02", "wet"), "per_5C": fit(hot, "t5", "wet"),
                  "without_last_two_weeks_of_June": fit(hot[~((hot.index.month == 6) & (hot.index.day >= 15))], "x", "wet"),
                  "mean_rate_exposed": float(hot.loc[hot.x == 1, "rate"].mean()), "mean_rate_other": float(hot.loc[hot.x == 0, "rate"].mean())}
    res["cold"] = {"primary": fit(cold, "x", "wet + snow"), "lag0_2": fit(cold, "x02", "wet + snow"), "per_5C": fit(cold, "t5", "wet + snow"),
                   "without_snow_days": fit(cold[cold.snow == 0], "x", "wet"),
                   "mean_rate_exposed": float(cold.loc[cold.x == 1, "rate"].mean()), "mean_rate_other": float(cold.loc[cold.x == 0, "rate"].mean())}
    res["sources"] = sources
    (OUT / "absence_test.json").write_text(json.dumps(res, indent=1, default=str))
    a[["absent", "enrolled", "rate", "TMAX", "TMIN", "PRCP", "SNOW", "sy", "adjacent", "last5", "snow"]].to_csv(OUT / "absence_daily.csv")
    print(json.dumps({k: v for k, v in res.items() if k != "sources"}, indent=1))
