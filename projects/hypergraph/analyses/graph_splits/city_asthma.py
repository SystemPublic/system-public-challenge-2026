"""Test of split-temp-asthma-ems (registered before this query; see claims/registered)."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd, statsmodels.api as sm
from pandas.tseries.holiday import USFederalHolidayCalendar
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from concord import socrata, noaa
OUT = ROOT / "data/derived/graph/splits"

def series(col):
    rows, src = socrata.query("76xm-jjuj", select=f"date_trunc_ymd(incident_datetime) as d, count(*) as n",
        where=f"incident_datetime between '2006-01-01' and '2026-08-31T23:59:59' and {col} in ('ASTHMB','ASTHFC')",
        group="d", order="d")
    s = pd.Series({pd.Timestamp(r["d"]): int(r["n"]) for r in rows})
    return s.reindex(pd.date_range("2006-01-01", "2026-08-31"), fill_value=0), src

def fit(df, xcol, mask=None, interact=False):
    d = df if mask is None else df[mask]
    d = d[d.groupby("ym")["n"].transform("sum") > 0]  # a month with no dispatches at all cannot be fitted
    X = pd.get_dummies(d[["ym", "dow"]].astype(str), drop_first=True).astype(float)
    X["hol"] = d["hol"].astype(float); X["x"] = d[xcol]
    if interact:
        X["x_warm"] = d[xcol] * d["warm"]
    X = X.loc[:, X.abs().sum() > 0]  # e.g. no federal holiday in a single-month subset
    X = sm.add_constant(X)
    m = sm.GLM(d["n"], X, family=sm.families.Poisson()).fit(cov_type="HAC", cov_kwds={"maxlags": 7})
    def rr(k):
        b, se = m.params[k], m.bse[k]
        return {"log": float(b), "se": float(se), "irr": float(np.exp(b)), "lo": float(np.exp(b - 1.96 * se)), "hi": float(np.exp(b + 1.96 * se))}
    out = {"n_days": int(len(d)), "mean_count": float(d["n"].mean()), "x": rr("x")}
    if interact:
        b, se = m.params["x_warm"], m.bse["x_warm"]
        out["warm_minus_cool_log"] = {"est": float(b), "lo": float(b - 1.96 * se), "hi": float(b + 1.96 * se)}
    return out

def main():
    y, src = series("initial_call_type")
    yf, srcf = series("final_call_type")
    w, wsrc = noaa.daily("central_park")
    t = ((w.TMAX + w.TMIN) / 2).reindex(pd.date_range("2005-12-01", "2026-08-31"))
    df = pd.DataFrame({"n": y, "nf": yf})
    df["t03"] = t.rolling(4).mean().reindex(df.index) / 5
    df["t0"] = t.reindex(df.index) / 5
    df["t07"] = t.rolling(8).mean().reindex(df.index) / 5
    df["tmin03"] = w.TMIN.reindex(t.index).rolling(4).mean().reindex(df.index) / 5
    df["ym"] = df.index.strftime("%Y-%m"); df["dow"] = df.index.dayofweek
    hol = USFederalHolidayCalendar().holidays("2006-01-01", "2026-12-31")
    df["hol"] = df.index.isin(hol)
    df["warm"] = df.index.month.isin([4, 5, 6, 7, 8, 9]).astype(float)
    df = df.dropna()
    # The asthma call types first appear on 2006-09-28; the registered start (2006-01-01) has no such rows.
    # The analysis starts at the first full month, 2006-10-01 (deviation from the registration, forced by the data).
    df = df[df.index >= "2006-10-01"]
    cool, warm = df.warm == 0, df.warm == 1
    res = {"primary_cool": fit(df, "t03", cool), "warm": fit(df, "t03", warm), "all_interaction": fit(df, "t03", None, True),
           "all_days": fit(df, "t03")}
    sens = {}
    for name, (xc, d2) in {"final_call_type": ("t03", df.assign(n=df.nf)), "lag0": ("t0", df), "lag0_7": ("t07", df),
                           "tmin_lag0_3": ("tmin03", df),
                           "excl_2020-03_2021-06": ("t03", df[(df.index < "2020-03-01") | (df.index > "2021-06-30")])}.items():
        sens[name] = {"cool": fit(d2, xc, d2.warm == 0)["x"], "warm": fit(d2, xc, d2.warm == 1)["x"]}
    res["sensitivity"] = sens
    res["by_month_exploratory"] = {int(mo): fit(df, "t03", df.index.month == mo)["x"] for mo in range(1, 13)}
    res["totals"] = {"dispatches_initial": int(df.n.sum()), "dispatches_final": int(df.nf.sum()), "days": int(len(df))}
    res["sources"] = [src, srcf, wsrc]
    (OUT / "city_asthma.json").write_text(json.dumps(res, indent=1))
    df[["n", "nf", "t03"]].assign(t03_c=lambda d: d.t03 * 5).drop(columns="t03").to_csv(OUT / "city_asthma_daily.csv")
    for k in ("primary_cool", "warm", "all_days"):
        r = res[k]["x"]; print(k, res[k]["n_days"], round(res[k]["mean_count"], 1), f"IRR {r['irr']:.4f} ({r['lo']:.4f}-{r['hi']:.4f})")
    print("warm-cool", res["all_interaction"]["warm_minus_cool_log"])
    for k, v in sens.items(): print(k, {s: f"{v[s]['irr']:.3f} ({v[s]['lo']:.3f}-{v[s]['hi']:.3f})" for s in v})
    print({m: f"{v['irr']:.3f} ({v['lo']:.3f}-{v['hi']:.3f})" for m, v in res["by_month_exploratory"].items()})

if __name__ == "__main__":
    main()
