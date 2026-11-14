"""mob-active-commute-obesity: walk-or-bike commute share vs adult obesity across UHF42, adjusted for poverty."""
from __future__ import annotations

import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from analyses.mobility import ehdp
from analyses.mobility.common import DER, savefig


def slope(m, term, per=10.0):
    b, se = m.params[term], m.bse[term]
    return {"term": term, "per": per, "slope": float(b * per), "lo": float((b - 1.96 * se) * per),
            "hi": float((b + 1.96 * se) * per), "p": float(m.pvalues[term]), "n": int(m.nobs), "r2": float(m.rsquared)}


def main():
    d = pd.DataFrame({
        "bike": ehdp.wide(2415, 1304, ["2015-19"]),
        "walk": ehdp.wide(2415, 1307, ["2015-19"]),
        "obesity": ehdp.wide(2063, 506, ["2017", "2018", "2019"]),
        "poverty": ehdp.wide(103, 221, ["2015-19"]),
    }).dropna()
    d["active"] = d["bike"] + d["walk"]
    d["boro"] = [ehdp.BORO[i // 100] for i in d.index]
    d.to_csv(DER / "active_commute_obesity_uhf42.csv", index_label="uhf42")
    fit = lambda f, data=d: smf.ols(f, data=data).fit(cov_type="HC3")
    res = {
        "unadjusted": slope(fit("obesity ~ active"), "active"),
        "poverty": slope(fit("obesity ~ active + poverty"), "active"),
        "poverty_boro": slope(fit("obesity ~ active + poverty + C(boro)"), "active"),
        "poverty_no_manhattan": slope(fit("obesity ~ active + poverty", d[d["boro"] != "Manhattan"]), "active"),
        "bike_only_poverty": slope(fit("obesity ~ bike + poverty"), "bike", per=1.0),
        "poverty_coef": slope(fit("obesity ~ active + poverty"), "poverty"),
        "corr": d[["active", "bike", "walk", "obesity", "poverty"]].corr().round(3).to_dict(),
        "ranges": d[["active", "bike", "walk", "obesity", "poverty"]].describe().round(2).to_dict(),
    }
    for k, v in res.items():
        if "slope" in v:
            print(f"{k:22s} {v['slope']:+.2f} ({v['lo']:+.2f} to {v['hi']:+.2f}) per {v['per']} pts  p={v['p']:.3g} R2={v['r2']:.2f} n={v['n']}")
    print(res["corr"]["active"])
    srcs = [ehdp.source(2415, 1304, "Commuting by bicycle, % of workers (ACS)", ["2015-19"]),
            ehdp.source(2415, 1307, "Commuting by walking, % of workers (ACS)", ["2015-19"]),
            ehdp.source(2063, 506, "Adult obesity, % (CHS, self-reported BMI >= 30)", ["2017", "2018", "2019"]),
            ehdp.source(103, 221, "Poverty, % below FPL (ACS)", ["2015-19"])]
    (DER / "active_commute_results.json").write_text(json.dumps({"results": res, "sources": srcs}, indent=1))

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
    ax = axes[0]
    sc = ax.scatter(d["active"], d["obesity"], c=d["poverty"], cmap="viridis", s=36, edgecolor="k", lw=0.3)
    for i, r in d.iterrows():
        if r["boro"] == "Manhattan":
            ax.annotate(str(i), (r["active"], r["obesity"]), fontsize=6, xytext=(3, 2), textcoords="offset points")
    m0 = fit("obesity ~ active")
    x = np.linspace(d["active"].min(), d["active"].max(), 50)
    ax.plot(x, m0.params["Intercept"] + m0.params["active"] * x, color="#c0392b", lw=1.2, label="unadjusted fit")
    ax.set_xlabel("Workers who walk or cycle to work, 2015-19 (%)")
    ax.set_ylabel("Adults with obesity, 2017-19 (%)")
    ax.set_title("(a) UHF42 neighbourhoods; labels mark Manhattan", fontsize=10)
    ax.legend(frameon=False, fontsize=8)
    cb = fig.colorbar(sc, ax=ax)
    cb.set_label("Below poverty level (%)")
    ax = axes[1]
    # partial regression: residualise both on poverty
    ra = smf.ols("active ~ poverty", d).fit().resid
    ro = smf.ols("obesity ~ poverty", d).fit().resid
    ax.scatter(ra, ro, c=["#c0392b" if b == "Manhattan" else "#2c3e50" for b in d["boro"]], s=30)
    b = np.polyfit(ra, ro, 1)
    xx = np.linspace(ra.min(), ra.max(), 50)
    ax.plot(xx, np.polyval(b, xx), color="k", lw=1)
    ax.axhline(0, color="#aaa", lw=0.5)
    ax.axvline(0, color="#aaa", lw=0.5)
    ax.set_xlabel("Walk-or-bike share, residual after poverty (points)")
    ax.set_ylabel("Obesity, residual after poverty (points)")
    ax.set_title(f"(b) Adjusted for poverty: {res['poverty']['slope']:+.1f} points per 10 (red = Manhattan)", fontsize=10)
    fig.suptitle("Active commuting and adult obesity (EHDP: ACS commute mode, Community Health Survey)", fontsize=9)
    fig.tight_layout()
    print(savefig(fig, "active_commute_obesity_uhf42.png"))


if __name__ == "__main__":
    main()
