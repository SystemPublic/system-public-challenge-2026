"""Test of split-temp-covid-growth (registered before this query; see claims/registered)."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd, statsmodels.api as sm
from scipy.stats import spearmanr
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from concord import socrata, noaa
OUT = ROOT / "data/derived/graph/splits"

def harm(doy, k=2):
    return np.column_stack([f(2 * np.pi * j * doy / 365.25) for j in range(1, k + 1) for f in (np.sin, np.cos)])

def main():
    rows, src = socrata.query("rc75-m7u3", select="date_of_interest, case_count, hospitalized_count", order="date_of_interest")
    d = pd.DataFrame(rows); d["date"] = pd.to_datetime(d.date_of_interest)
    d = d.set_index("date")[["case_count", "hospitalized_count"]].astype(float)
    w, wsrc = noaa.daily("central_park")
    t = ((w.TMAX + w.TMIN) / 2)["2010-01-01":"2025-12-31"].dropna()
    Xh = sm.add_constant(harm(t.index.dayofyear.values))
    normal = sm.OLS(t.values, Xh).fit()
    anom = pd.Series(t.values - normal.predict(Xh), index=t.index)

    def weekly(col, lo, hi, drop=None, start="2020-03-16"):
        wk = d[col].resample("W-SUN").sum()
        wk = wk[wk.index <= d.index.max()]          # drop a trailing partial week
        g = np.log(wk / wk.shift(1)); ok = (wk >= 20) & (wk.shift(1) >= 20)
        df = pd.DataFrame({"g": g, "g1": g.shift(1), "ok": ok})
        thu = df.index - pd.Timedelta(days=3)
        df["a"] = [anom[th - pd.Timedelta(days=hi): th - pd.Timedelta(days=lo)].mean() for th in thu]
        df = df[(df.index - pd.Timedelta(days=6) >= start) & df.ok].dropna()
        if drop: df = df[~drop(df.index)]
        X = pd.get_dummies(df.index.year.astype(str), drop_first=True).astype(float); X.index = df.index
        H = harm((df.index - pd.Timedelta(days=3)).dayofyear.values)
        for i in range(4): X[f"h{i}"] = H[:, i]
        X["a"] = df.a; X["g1"] = df.g1
        m = sm.OLS(df.g, sm.add_constant(X)).fit(cov_type="HAC", cov_kwds={"maxlags": 4})
        b, se = m.params["a"], m.bse["a"]
        return {"est": float(b), "lo": float(b - 1.96 * se), "hi": float(b + 1.96 * se), "n_weeks": int(len(df)),
                "sd_growth": float(df.g.std()), "sd_anomaly": float(df.a.std())}, df

    res = {}
    res["primary"], dfp = weekly("hospitalized_count", 7, 20)
    res["sensitivity"] = {
        "window_0_13": weekly("hospitalized_count", 0, 13)[0], "window_14_27": weekly("hospitalized_count", 14, 27)[0],
        "cases": weekly("case_count", 7, 20)[0],
        "drop_2020": weekly("hospitalized_count", 7, 20, start="2021-01-04")[0],
        "drop_omicron": weekly("hospitalized_count", 7, 20, drop=lambda ix: (ix >= "2021-12-13") & (ix <= "2022-02-13"))[0]}
    # Secondary: raw quarterly correlations, as in the positive studies of the graph
    q = []
    tt = ((w.TMAX + w.TMIN) / 2).reindex(d.index)
    for per, grp in d.groupby(d.index.to_period("Q")):
        if per < pd.Period("2020Q2") or per > pd.Period("2025Q3"): continue
        r, p = spearmanr(tt[grp.index], grp.case_count, nan_policy="omit")
        q.append({"quarter": str(per), "rho": float(r), "p": float(p), "n": int(len(grp))})
    res["quarterly_raw"] = q
    n = len(q)
    res["quarterly_summary"] = {"quarters": n, "sig_pos": sum(x["rho"] > 0 and x["p"] < .05 for x in q),
                                "sig_neg": sum(x["rho"] < 0 and x["p"] < .05 for x in q)}
    # Exploratory: the same raw correlation over the first 30, 60 and 90 days from 1 March 2020
    res["first_wave_raw_exploratory"] = {}
    for days in (30, 45, 60, 90):
        g = d["2020-03-01":str((pd.Timestamp("2020-03-01") + pd.Timedelta(days=days - 1)).date())]
        r, p = spearmanr(tt[g.index], g.case_count)
        res["first_wave_raw_exploratory"][days] = {"rho": float(r), "p": float(p)}
    res["sources"] = [src, wsrc]
    (OUT / "city_covid.json").write_text(json.dumps(res, indent=1))
    dfp[["g", "a"]].to_csv(OUT / "city_covid_weekly.csv")
    print("primary", res["primary"]); print(res["sensitivity"]); print(res["quarterly_summary"])
    print([(x["quarter"], round(x["rho"], 2)) for x in q]); print(res["first_wave_raw_exploratory"])

if __name__ == "__main__":
    main()
