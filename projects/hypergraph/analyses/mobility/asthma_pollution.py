"""mob-asthma-pollution: asthma ED visits (age 5-17) vs NYCCAS NO2 and PM2.5 across UHF42, with poverty."""
from __future__ import annotations

import json

import matplotlib
import matplotlib.ticker
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from analyses.mobility import ehdp
from analyses.mobility.common import DER, savefig

YRS = ["2017", "2018", "2019"]
UG_PER_PPB = 1.88  # NO2 at 25 C


def fit(f, d):
    m = smf.ols(f, data=d).fit(cov_type="HC3")
    return m


def rr(m, term, per=1.0):
    b, se = m.params[term], m.bse[term]
    return {"term": term, "per": per, "rr": float(np.exp(b * per)), "lo": float(np.exp((b - 1.96 * se) * per)),
            "hi": float(np.exp((b + 1.96 * se) * per)), "p": float(m.pvalues[term]), "n": int(m.nobs),
            "r2": float(m.rsquared)}


def main():
    d = pd.DataFrame({
        "asthma_child": ehdp.wide(2379, 1196, YRS),
        "asthma_adult_aa": ehdp.wide(2380, 1199, YRS),
        "no2": ehdp.wide(2025, 1431, YRS),
        "pm25": ehdp.wide(2023, 1425, YRS),
        "poverty": ehdp.wide(103, 221, ["2015-19"]),
    }).dropna()
    d["boro"] = [ehdp.BORO[i // 100] for i in d.index]
    d["log_child"] = np.log(d["asthma_child"])
    d["log_adult"] = np.log(d["asthma_adult_aa"])
    d.to_csv(DER / "asthma_pollution_uhf42.csv", index_label="uhf42")
    res = {}
    for y in ("child", "adult"):
        for pol, per in (("no2", 10.0), ("pm25", 1.0)):
            res[f"{y}_{pol}_unadj"] = rr(fit(f"log_{y} ~ {pol}", d), pol, per)
            res[f"{y}_{pol}_poverty"] = rr(fit(f"log_{y} ~ {pol} + poverty", d), pol, per)
            res[f"{y}_{pol}_poverty_boro"] = rr(fit(f"log_{y} ~ {pol} + poverty + C(boro)", d), pol, per)
        m = fit(f"log_{y} ~ no2 + pm25 + poverty", d)
        res[f"{y}_both_poverty_no2"] = rr(m, "no2", 10.0)
        res[f"{y}_both_poverty_pm25"] = rr(m, "pm25", 1.0)
        res[f"{y}_poverty_only"] = rr(fit(f"log_{y} ~ poverty", d), "poverty", 10.0)
    res["corr"] = d[["no2", "pm25", "poverty", "asthma_child"]].corr().round(3).to_dict()
    res["research"] = {"no2_per_10ppb_khreis": 1.05 ** (10 * UG_PER_PPB / 4), "pm25_per_1ug_khreis": 1.03,
                       "no2_per_10ppb_zheng_short_term": 1.018 ** (10 * UG_PER_PPB / 10),
                       "pm25_per_1ug_zheng_short_term": 1.023 ** 0.1}
    res["ranges"] = d[["no2", "pm25", "poverty", "asthma_child"]].describe().round(2).to_dict()
    srcs = [ehdp.source(2379, 1196, "Asthma ED visits age 5-17, rate per 10,000", YRS),
            ehdp.source(2380, 1199, "Asthma ED visits adults, age-adjusted rate per 10,000", YRS),
            ehdp.source(2025, 1431, "NO2 annual mean (ppb), NYCCAS", YRS),
            ehdp.source(2023, 1425, "PM2.5 annual mean (ug/m3), NYCCAS", YRS),
            ehdp.source(103, 221, "Poverty, percent below FPL (ACS)", ["2015-19"])]
    (DER / "asthma_pollution_results.json").write_text(json.dumps({"results": res, "sources": srcs}, indent=1))
    for k, v in res.items():
        if "rr" in v:
            print(f"{k:28s} RR={v['rr']:.3f} ({v['lo']:.3f}-{v['hi']:.3f}) per {v['per']} p={v['p']:.3g} R2={v['r2']:.2f}")
    print(json.dumps(res["corr"]))

    # figure
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6), sharey=True)
    for ax, pol, per, lab, key in ((axes[0], "no2", 10, "NO2 annual mean, 2017-19 (ppb)", "no2_per_10ppb_khreis"),
                                   (axes[1], "pm25", 1, "PM2.5 annual mean, 2017-19 (ug/m3)", "pm25_per_1ug_khreis")):
        sc = ax.scatter(d[pol], d["asthma_child"], c=d["poverty"], cmap="viridis", s=36, edgecolor="k", lw=0.3)
        for i, r in d.iterrows():
            if r["boro"] == "Manhattan" or r["asthma_child"] > 250:
                ax.annotate(str(i), (r[pol], r["asthma_child"]), fontsize=6, xytext=(3, 2), textcoords="offset points")
        x = np.linspace(d[pol].min(), d[pol].max(), 50)
        m = fit(f"log_child ~ {pol}", d)
        ax.plot(x, np.exp(m.params["Intercept"] + m.params[pol] * x), color="#c0392b", lw=1.2, label="NYC fit, unadjusted")
        rs = np.log(res["research"][key]) / per
        x0, y0 = d[pol].mean(), np.exp(d["log_child"].mean())
        ax.plot(x, y0 * np.exp(rs * (x - x0)), color="k", ls="--", lw=1.2, label="research slope (Khreis 2017) through city mean")
        ax.set_yscale("log")
        ax.set_xlabel(lab)
        ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
        ax.set_yticks([30, 50, 100, 200, 400])
        ax.set_yticklabels(["30", "50", "100", "200", "400"])
        ax.legend(frameon=False, fontsize=7, loc="lower right")
    axes[0].set_ylabel("Asthma ED visits age 5-17, per 10,000 (log scale)")
    cb = fig.colorbar(sc, ax=axes, shrink=0.8)
    cb.set_label("Residents below poverty level, 2015-19 (%)")
    fig.suptitle("42 UHF neighbourhoods (EHDP, NYCCAS, SPARCS); labels mark Manhattan and the highest-rate areas", fontsize=9)
    print(savefig(fig, "asthma_pollution_uhf42.png"))


if __name__ == "__main__":
    main()
