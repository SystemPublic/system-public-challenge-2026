"""Descriptive results for docs/heat_extremes.md (planned in the registration; none decides the verdict).

1. Dose-response curve of aggravated assaults by 3 C bin of maximum temperature, per city and pooled.
2. The same curve by percentile of each city's own distribution of daily maximum temperature, and a
   comparison of two stacked models: one curve common to all cities in degrees C, one common in percentiles.
3. Piecewise-linear slopes below and above 35 C in the four hot cities.
4. Exploratory: New York shootings and felony assaults by position in a run of days at or above 32 C.

Run after test.py: ~/.venvs/nyc-concordance/bin/python -m analyses.heat_extremes.describe
Writes curves.csv, curves_pct.csv, describe.json in data/derived/heat_extremes/
"""
import json

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

from analyses.heat_extremes import model as m

CURVE_REF = "[20.0, 23.0)"
HOT = ["phoenix", "tucson", "dallas", "austin"]


def mid(lab, lo_default, hi_default):
    a, b = lab.strip("[)").split(", ")
    a = lo_default if a == "-inf" else float(a)
    b = hi_default if b == "inf" else float(b)
    return a, b


def curves():
    rows, rows_p, alphas, frames = [], [], {}, {}
    for c in m.CITIES:
        d = m.load(c)
        d["tb"] = m.bins(d["TMAX"], m.EDGES_CURVE)
        d["pb"] = m.bins(d["pct"], m.PCT_EDGES)
        a = m.nb_alpha(d)
        alphas[c], frames[c] = a, d
        for col, ref, store in (("tb", CURVE_REF, rows), ("pb", m.PCT_REF, rows_p)):
            est = m.fit_bins(d, "n", col, ref, a, min_days=m.MIN_CURVE_DAYS)
            for lev, e in est.items():
                sub = d[d[col] == lev]
                store.append({"city": c, "bin": lev, "days": e["days"], "mean_tmax": float(sub["TMAX"].mean()), "mean_pct": float(sub["pct"].mean()),
                              "raw_mean_count": float(sub["n"].mean()), "log": e["log"], "se": e["se"], **{k: v for k, v in m.rr(e).items() if k in ("estimate", "lo", "hi")}})
    cv, cp = pd.DataFrame(rows), pd.DataFrame(rows_p)
    pooled = []
    for name, group in (("pooled_hot4", HOT), ("pooled_all8", m.CITIES)):
        for lev, g in cv[cv.city.isin(group)].groupby("bin"):
            g = g[g.se > 0]
            if len(g) >= 2:
                p = m.pool(g[["log", "se"]].to_dict("records"))
                pooled.append({"city": name, "bin": lev, "days": int(g.days.sum()), "mean_tmax": float(np.average(g.mean_tmax, weights=g.days)), "k": p["k"], "I2": p["I2"],
                               "log": p["random"]["log"], "se": p["random"]["se"], **{k: p["random"][k] for k in ("estimate", "lo", "hi")}})
    cv = pd.concat([cv, pd.DataFrame(pooled)], ignore_index=True)
    cv.to_csv(m.DER / "curves.csv", index=False)
    cp.to_csv(m.DER / "curves_pct.csv", index=False)
    return cv, cp, alphas, frames


def peak(cv, cp):
    """Where each city's curve is highest, in degrees and in percentile, and the hottest bin against the peak bin."""
    out = {}
    for c in m.CITIES:
        g = cv[cv.city == c].sort_values("mean_tmax")
        gp = cp[cp.city == c].sort_values("mean_pct")
        i, j = g["log"].idxmax(), gp["log"].idxmax()
        out[c] = {"peak_bin_C": g.loc[i, "bin"], "peak_mean_tmax": float(g.loc[i, "mean_tmax"]), "hottest_bin_C": g.iloc[-1]["bin"],
                  "hottest_vs_20_23": [float(g.iloc[-1][k]) for k in ("estimate", "lo", "hi")], "peak_vs_20_23": [float(g.loc[i, k]) for k in ("estimate", "lo", "hi")],
                  "peak_bin_pct": gp.loc[j, "bin"], "top_pct_bin_vs_50_70": [float(gp.iloc[-1][k]) for k in ("estimate", "lo", "hi")],
                  "p90_95_vs_50_70": [float(x) for x in gp[gp.bin == "[90.0, 95.0)"][["estimate", "lo", "hi"]].values[0]],
                  "pct_of_peak_bin_mean_tmax": float(g.loc[i, "mean_pct"])}
    return out


def stacked(frames, alphas):
    """One curve for all cities in degrees C against one curve in percentiles; city-specific calendar terms in both."""
    d = pd.concat([f.assign(city=c)[["n", "city", "tb", "pb", "dow", "month", "year", "hol", "dom1", "wet"]] for c, f in frames.items()])
    d["tb"] = d["tb"].replace({"[41.0, 44.0)": "[38.0, 41.0)", "[44.0, inf)": "[38.0, 41.0)"})  # 10 bins, as many as the percentile model has plus two
    cal = "C(city) + C(city):C(dow) + C(city):C(month) + C(city):C(year) + C(city):hol + C(city):dom1 + C(city):wet"
    a = float(np.median(list(alphas.values())))
    fam = sm.families.NegativeBinomial(alpha=a)
    res = {}
    for name, term in (("none", ""), ("common_degrees", " + C(tb)"), ("common_percentile", " + C(pb)"), ("city_specific_degrees", " + C(city):C(tb)"),
                       ("city_specific_percentile", " + C(city):C(pb)")):
        r = smf.glm("n ~ " + cal + term, d, family=fam).fit()
        res[name] = {"llf": float(r.llf), "df_model": int(r.df_model), "aic": float(r.aic)}
    res["alpha"] = a
    res["n_days"] = int(len(d))
    return res


def slopes(frames, alphas):
    out = {}
    for c in HOT:
        d = frames[c].copy()
        d["s20"] = np.clip(d["TMAX"] - 20, 0, None)
        d["s35"] = np.clip(d["TMAX"] - 35, 0, None)
        r = smf.glm(f"n ~ TMAX + s20 + s35 + {m.CONTROLS}", d, family=sm.families.NegativeBinomial(alpha=alphas[c])).fit(cov_type="HC0")
        b, V = r.params, r.cov_params()
        def comb(names):
            e = sum(b[n] for n in names)
            s = float(np.sqrt(sum(V.loc[i, j] for i in names for j in names)))
            return {"log": float(5 * e), "se": float(5 * s), "estimate": float(np.exp(5 * e)), "lo": float(np.exp(5 * (e - 1.96 * s))), "hi": float(np.exp(5 * (e + 1.96 * s)))}
        out[c] = {"per5C_20_to_35": comb(["TMAX", "s20"]), "per5C_above_35": comb(["TMAX", "s20", "s35"]),
                  "change_in_slope_p": float(r.pvalues["s35"])}
    out["pooled_above_35"] = m.pool([out[c]["per5C_above_35"] for c in HOT])
    out["pooled_20_to_35"] = m.pool([out[c]["per5C_20_to_35"] for c in HOT])
    return out


def ny_heatwaves():
    res = {}
    for y in ("shoot", "n"):
        d = m.load("new_york", y)
        hot = (d["TMAX"] >= 32.0).astype(int)
        run = (hot != hot.shift()).cumsum()
        pos = hot.groupby(run).cumsum()
        length = hot.groupby(run).transform("sum")
        d["pos"] = "not_hot"
        d.loc[(hot == 1) & (length == 1), "pos"] = "isolated"
        d.loc[(hot == 1) & (length >= 2) & (pos == 1), "pos"] = "day1"
        d.loc[(hot == 1) & (pos == 2), "pos"] = "day2"
        d.loc[(hot == 1) & (pos == 3), "pos"] = "day3"
        d.loc[(hot == 1) & (pos >= 4), "pos"] = "day4plus"
        for k in (15, 21, 27):
            d[f"s{k}"] = np.clip(d["TMAX"] - k, 0, None)
        a = m.nb_alpha(d, y)
        r = smf.glm(f"{y} ~ C(pos, Treatment(reference='isolated')) + TMAX + s15 + s21 + s27 + {m.CONTROLS}", d,
                    family=sm.families.NegativeBinomial(alpha=a)).fit(cov_type="HC0")
        tab = {}
        for lev in ("isolated", "day1", "day2", "day3", "day4plus"):
            sub = d[d.pos == lev]
            k = f"C(pos, Treatment(reference='isolated'))[T.{lev}]"
            e = {"log": float(r.params[k]), "se": float(r.bse[k])} if lev != "isolated" else {"log": 0.0, "se": 0.0}
            tab[lev] = {"days": int(len(sub)), "events": int(sub[y].sum()), "raw_mean": float(sub[y].mean()), "mean_tmax": float(sub["TMAX"].mean()),
                        **{k2: v for k2, v in m.rr(e).items() if k2 in ("estimate", "lo", "hi")}}
        # days 2 and later of a run together against isolated days and first days together
        d["later"] = d["pos"].isin(["day2", "day3", "day4plus"]).astype(int)
        d["hotday"] = (d["pos"] != "not_hot").astype(int)
        r2 = smf.glm(f"{y} ~ hotday + later + TMAX + s15 + s21 + s27 + {m.CONTROLS}", d, family=sm.families.NegativeBinomial(alpha=a)).fit(cov_type="HC0")
        tab["later_vs_first_or_isolated"] = {k2: v for k2, v in m.rr({"log": float(r2.params["later"]), "se": float(r2.bse["later"])}).items() if k2 in ("estimate", "lo", "hi")}
        tab["period"] = [str(d.index.min().date()), str(d.index.max().date())]
        tab["hot_days"] = int(hot.sum())
        tab["runs_of_3_or_more"] = int((length[hot == 1].groupby(run[hot == 1]).first() >= 3).sum())
        res["shootings" if y == "shoot" else "felony_assaults"] = tab
    return res


def main():
    cv, cp, alphas, frames = curves()
    out = {"alphas": alphas, "peak": peak(cv, cp), "stacked": stacked(frames, alphas), "slopes": slopes(frames, alphas), "ny_heatwaves": ny_heatwaves()}
    (m.DER / "describe.json").write_text(json.dumps(out, indent=1))
    pd.set_option("display.width", 250)
    print(cv.pivot_table(index="bin", columns="city", values="estimate").round(3))
    print(cp.pivot_table(index="bin", columns="city", values="estimate").round(3))
    print(json.dumps({k: out[k] for k in ("peak", "stacked", "slopes", "ny_heatwaves")}, indent=1)[:9000])


if __name__ == "__main__":
    main()
