"""heat-night-minimum: the registered analysis. Fixed and committed with the registration.

Run: ~/.venvs/nyc-concordance/bin/python -m analyses.round5.heat_night.run
No resampling and no random numbers are used; every interval is a Wald interval from HC0
standard errors. Thresholds are read from data/derived/round5/heat_night/prereg_design.json,
which was written before the registration.

Day. A shooting day d runs from 06:00 on date d to 05:59 on date d+1. Day shootings are those
from 06:00 to 17:59 on d, night shootings those from 18:00 on d to 05:59 on d+1. TMAX is the
GHCN-Daily maximum of date d. The preceding night's minimum is the GHCN-Daily TMIN of date d
(the minimum usually falls near dawn of d, before the shooting day begins). The following
night's minimum is TMIN of date d+1. Calendar terms (day of week, month, year, holiday, wet
day) are those of date d.

(a) On shooting days with TMAX >= 27 C: negative binomial GLM, log link, HC0, of the count on
    TMAX/5 (linear; on these days the registered piecewise-linear spline with knots at 15, 21
    and 27 C has one free slope) + preceding TMIN/5 + C(dow) + C(month) + C(year) + hol + wet.
    Dispersion by maximum likelihood from the same model without TMIN (model.nb_alpha).
(b) On all shooting days: the same model with the piecewise-linear TMAX spline and no TMIN,
    for day shootings and night shootings separately; the ratio 33 C against 27 C for each.
    The ratio of the two ratios comes from a binomial GLM (HC0) of night shootings out of all
    shootings of the shooting day on the same terms.
(c) The same in Chicago.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from patsy import dmatrices

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import concord.socrata as soc  # noqa: E402
from analyses.heat.common import holidays  # noqa: E402
from analyses.round2.hot_end import model as M  # noqa: E402
from concord import noaa  # noqa: E402

assert M.SPLINE == "lin" and M.KNOTS == (15.0, 21.0, 27.0)
DER = ROOT / "data/derived/round5/heat_night"
CONTROLS = M.CONTROLS
HOT = 27.0
LAST_DAY = "2026-08-30"  # the last shooting day whose night ends inside the fetched range
CITIES = {
    "new_york": {"domain": "https://data.cityofnewyork.us", "dataset": "5ucz-vwe8", "station": "central_park", "start": "2006-01-01",
                 "soql": {"select": "incident_key, min(occur_date) as d, min(occur_time) as t", "group": "incident_key",
                          "order": "incident_key"}},
    "chicago": {"domain": "https://data.cityofchicago.org", "dataset": "gumc-mgzr", "station": "USW00014819", "start": "2010-01-01",
                "soql": {"select": "case_number, min(date) as ts",
                         "where": "date between '2010-01-01T00:00:00' and '2026-08-31T23:59:59' AND gunshot_injury_i in ('Y','YES')",
                         "group": "case_number", "order": "case_number"}},
}
BLOCKS = {"06-12": (6, 12), "12-18": (12, 18), "18-24": (18, 24), "00-06": (0, 6)}


def incidents(c) -> tuple[pd.Series, dict]:
    soc.DOMAIN = c["domain"]
    rows, src = soc.query_all(c["dataset"], **c["soql"])
    df = pd.DataFrame(rows)
    if "ts" in df:
        ts = pd.to_datetime(df["ts"])
    else:
        ts = pd.to_datetime(df["d"].str[:10] + " " + df["t"].str[:8])
    return ts.dropna(), src


def frame(name: str):
    c = CITIES[name]
    ts, src = incidents(c)
    w, srcw = noaa.daily(c["station"])
    sd = (ts - pd.Timedelta(hours=6)).dt.floor("D")
    hr = ts.dt.hour
    idx = pd.date_range(c["start"], LAST_DAY, freq="D")
    d = pd.DataFrame(index=idx)
    cnt = lambda mask, key=sd: key[mask].value_counts().reindex(idx).fillna(0).astype(int)
    d["n"] = cnt(np.ones(len(ts), bool))
    d["n_day"] = cnt(((hr >= 6) & (hr < 18)).values)
    d["n_night"] = d["n"] - d["n_day"]
    for k, (a, b) in BLOCKS.items():
        d[f"n_{k.replace('-', '_')}"] = cnt(((hr >= a) & (hr < b)).values)
    d["n_cal"] = cnt(np.ones(len(ts), bool), ts.dt.floor("D"))
    d = d.join(w[["TMAX", "TMIN", "PRCP"]])
    d["TMIN_next"] = w["TMIN"].shift(-1).reindex(idx)
    d["TMAX_prev"] = w["TMAX"].shift(1).reindex(idx)
    d["dow"], d["month"], d["year"] = d.index.day_of_week, d.index.month, d.index.year
    d["hol"] = d.index.isin(holidays(c["start"], "2026-08-31")).astype(int)
    d["wet"] = (d["PRCP"] >= 1.0).astype(int)
    d["t5"], d["tminp5"], d["tminn5"], d["tprev5"] = d["TMAX"] / 5, d["TMIN"] / 5, d["TMIN_next"] / 5, d["TMAX_prev"] / 5
    d.index.name = "date"
    hours = pd.DataFrame({"hour": hr.values, "tmax": w["TMAX"].reindex(sd.values).values})
    return d, hours, [src, srcw]


def rr(res, term, scale=1.0):
    b, s = float(res.params[term]) * scale, float(res.bse[term]) * scale
    return {"estimate": float(np.exp(b)), "lo": float(np.exp(b - 1.96 * s)), "hi": float(np.exp(b + 1.96 * s)), "log": b, "se": s}


def nb(d, y, terms, controls=CONTROLS):
    alpha = M.nb_alpha(y, d)
    yy, X = dmatrices(f"{y} ~ {terms} + {controls}", d, return_type="dataframe")
    return sm.GLM(yy.iloc[:, 0], X, family=sm.families.NegativeBinomial(alpha=alpha)).fit(cov_type="HC0"), alpha


def part_a(d):
    h = d[(d["TMAX"] >= HOT)].dropna(subset=["TMAX", "TMIN", "TMIN_next", "TMAX_prev"]).copy()
    out = {"n_days": int(len(h)), "n_shootings": int(h["n"].sum()),
           "tmin_mean_sd": [float(h["TMIN"].mean()), float(h["TMIN"].std())]}
    r, alpha = nb(h, "n", "t5 + tminp5")
    out["primary"] = {**rr(r, "tminp5"), "alpha": alpha, "tmax_per_5c": rr(r, "t5"), "scale": "rate ratio per 5 C of the preceding night's TMIN"}
    s = {}
    for y in ("n_day", "n_night", "n_cal"):
        s[f"{y}_preceding"] = rr(nb(h, y, "t5 + tminp5")[0], "tminp5")
    r2 = nb(h, "n", "t5 + tminp5 + tminn5")[0]
    s["both_nights_preceding"], s["both_nights_following"] = rr(r2, "tminp5"), rr(r2, "tminn5")
    s["following_only"] = rr(nb(h, "n", "t5 + tminn5")[0], "tminn5")
    for y in ("n_day", "n_night"):
        s[f"{y}_following"] = rr(nb(h, y, "t5 + tminn5")[0], "tminn5")
    s["with_previous_day_tmax"] = rr(nb(h, "n", "t5 + tminp5 + tprev5")[0], "tminp5")
    s["tmax_ge_30"] = rr(nb(h[h["TMAX"] >= 30], "n", "t5 + tminp5")[0], "tminp5")
    s["june_to_august"] = rr(nb(h[h["month"].between(6, 8)], "n", "t5 + tminp5")[0], "tminp5")
    out["secondary"] = s
    return out


def spline_fit(d, y, extra=None):
    """Registered spline model on all days; optional extra columns. Returns the 33 vs 27 contrast and extra terms."""
    yy, X, sc, basis = M.design(d, y)
    for e in extra or []:
        X[e] = d[e].values
    r = sm.GLM(yy, X, family=sm.families.NegativeBinomial(alpha=M.nb_alpha(y, d))).fit(cov_type="HC0")
    x = M.cvec(basis, 33, 27)
    e_, s_ = float(x @ r.params[sc].values), float(np.sqrt(x @ r.cov_params().loc[sc, sc].values @ x))
    out = {"rr_33_vs_27": {"estimate": float(np.exp(e_)), "lo": float(np.exp(e_ - 1.96 * s_)), "hi": float(np.exp(e_ + 1.96 * s_)),
                           "log": e_, "se": s_}}
    for e in extra or []:
        out[e] = rr(r, e)
    return out


def part_b(d):
    a = d.dropna(subset=["TMAX", "TMIN", "TMIN_next"]).copy()
    out = {"n_days": int(len(a)), "n_day_shootings": int(a["n_day"].sum()), "n_night_shootings": int(a["n_night"].sum())}
    for y in ("n", "n_day", "n_night"):
        _, cur = M.curve_fit(a, y, M.nb_alpha(y, a))
        cur.insert(0, "series", y)
        out.setdefault("_curves", []).append(cur)
        out[y] = spline_fit(a, y)["rr_33_vs_27"]
    for k in BLOCKS:
        out[f"block_{k}"] = spline_fit(a, f"n_{k.replace('-', '_')}")["rr_33_vs_27"]
    # ratio of ratios: night share of the shooting day's shootings
    p = a[a["n"] > 0]
    yy, X, sc, basis = M.design(p, "n")
    r = sm.GLM(np.column_stack([p["n_night"].values, p["n_day"].values]), X, family=sm.families.Binomial()).fit(cov_type="HC0")
    x = M.cvec(basis, 33, 27)
    e_, s_ = float(x @ r.params[sc].values), float(np.sqrt(x @ r.cov_params().loc[sc, sc].values @ x))
    out["night_over_day_ratio_of_ratios"] = {"estimate": float(np.exp(e_)), "lo": float(np.exp(e_ - 1.96 * s_)),
                                             "hi": float(np.exp(e_ + 1.96 * s_)), "log": e_, "se": s_}
    # how much of the hot-day excess TMIN takes when added to the all-day spline model
    out["excess_with_preceding_tmin"] = spline_fit(a, "n", ["tminp5"])
    out["excess_with_both_tmin"] = spline_fit(a, "n", ["tminp5", "tminn5"])
    return out


def scored(a, design):
    p = a["primary"]
    half = design["rr_carrying_half_the_excess"]
    return {"support": bool(p["lo"] > 1.0), "refute": bool(p["hi"] < half and p["lo"] <= 1.0), "refute_threshold": half}


def main():
    design = json.loads((DER / "prereg_design.json").read_text())
    res, sources, curves, hourly = {}, [], [], []
    for name in CITIES:
        d, hours, src = frame(name)
        d.to_csv(DER / f"{name}_daily.csv")
        a, b = part_a(d), part_b(d)
        for cur in b.pop("_curves"):
            cur.insert(0, "city", name)
            curves.append(cur)
        hours["band"] = pd.cut(hours["tmax"], [21, 27, 30, 60], right=False, labels=["21-27", "27-30", "30+"])
        t = hours.dropna().groupby(["band", "hour"], observed=True).size().rename("n").reset_index()
        t.insert(0, "city", name)
        hourly.append(t)
        res[name] = {"part_a": a, "part_b": b, "scored": scored(a, design[name])}
        sources += src
    la, lb = (res[c]["part_a"]["primary"] for c in CITIES)
    wa, wb = 1 / la["se"] ** 2, 1 / lb["se"] ** 2
    e, s = (wa * la["log"] + wb * lb["log"]) / (wa + wb), (wa + wb) ** -0.5
    res["pooled_two_cities"] = {"estimate": float(np.exp(e)), "lo": float(np.exp(e - 1.96 * s)), "hi": float(np.exp(e + 1.96 * s)),
                                "log": float(e), "se": float(s), "method": "inverse-variance mean of the two log rate ratios"}
    ny = res["new_york"]["scored"]
    res["verdict"] = "confirmed" if ny["support"] else "contested" if ny["refute"] else "unsettled"
    pd.concat(curves).to_csv(DER / "curves.csv", index=False)
    pd.concat(hourly).to_csv(DER / "hourly_by_tmax_band.csv", index=False)
    (DER / "results.json").write_text(json.dumps(res, indent=1))
    (DER / "sources.json").write_text(json.dumps(sources, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
