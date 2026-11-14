#!/usr/bin/env python
"""graph-confounders-commute-obesity: the active-commuting and obesity slope across UHF42
under the adjustment set read from the System Public Graph. Registered before the covariates
were queried (claims/registered/graph-confounders-commute-obesity.json).
Run: ~/.venvs/nyc-concordance/bin/python analyses/graph_confounders/reanalysis.py"""
import json
import subprocess
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from analyses.mobility import ehdp  # noqa: E402

DER = ROOT / "data/derived/graph/confounders"
FIG = ROOT / "figures/graph"
ORIG = -5.966838433929027

MEASURES = {  # name: (indicator, measure, periods, label)
    "bike": (2415, 1304, ["2015-19"], "Commuting by bicycle, % of workers (ACS)"),
    "walk": (2415, 1307, ["2015-19"], "Commuting by walking, % of workers (ACS)"),
    "obesity": (2063, 506, ["2017", "2018", "2019"], "Adult obesity, % (CHS)"),
    "poverty": (103, 221, ["2015-19"], "Poverty, % (ACS)"),
    "hs_grad": (2334, 1025, ["2015-19"], "Graduated high school, % (ACS)"),
    "black": (2325, 988, ["2015-19"], "Black alone, % (ACS)"),
    "hispanic": (2325, 989, ["2015-19"], "Hispanic alone, % (ACS)"),
    "asian": (2325, 987, ["2015-19"], "Asian alone, % (ACS)"),
    "walkability": (2133, 673, ["2011"], "Walkability index (Built Environment and Health Project)"),
    "safety": (2073, 1058, ["2015", "2016"], "Perceive neighbourhood as safe, % (CHS)"),
    "park": (2388, 1224, ["2017"], "Within walking distance of a park, %"),
    "unemployment": (2337, 1032, ["2015-19"], "Unemployment, % (ACS)"),
    "exercise": (2060, 500, ["2017", "2018", "2019"], "Recent exercise, % (CHS)"),
}
G = ["poverty", "hs_grad", "black", "hispanic", "asian", "walkability", "safety"]


def slope(d, covs, per=10.0):
    m = smf.ols("obesity ~ active" + "".join(f" + {c}" for c in covs), data=d).fit(cov_type="HC3")
    b, se = m.params["active"], m.bse["active"]
    return {"covariates": covs, "slope": float(b * per), "lo": float((b - 1.96 * se) * per), "hi": float((b + 1.96 * se) * per),
            "half_width": float(1.96 * se * per), "p": float(m.pvalues["active"]), "n": int(m.nobs), "r2": float(m.rsquared),
            "attenuation_vs_original": float(1 - b * per / ORIG),
            "coefficients": {k: [float(m.params[k]), float(m.bse[k])] for k in m.params.index if k != "Intercept"}}


def main():
    d = pd.DataFrame({k: ehdp.wide(i, m, p) for k, (i, m, p, _) in MEASURES.items()})
    d["active"] = d["bike"] + d["walk"]
    d["boro"] = [ehdp.BORO[i // 100] for i in d.index]
    print(d.notna().sum().to_dict())
    DER.mkdir(parents=True, exist_ok=True)
    d.to_csv(DER / "commute_obesity_uhf42_covariates.csv", index_label="uhf42")
    c = d.dropna(subset=["obesity", "active"] + G)
    res = {"original_poverty_adjusted": ORIG, "models": {}}
    M = res["models"]
    M["unadjusted"] = slope(c, [])
    M["analyst: poverty"] = slope(c, ["poverty"])
    M["analyst: poverty + borough"] = slope(c, ["poverty", "C(boro)"])
    M["graph set (primary)"] = slope(c, G)
    full = d.dropna(subset=["obesity", "active", "park", "unemployment"] + G)
    M["graph set + park + unemployment"] = slope(full, G + ["park", "unemployment"])
    for v in G:
        M[f"graph set without {v}"] = slope(c, [x for x in G if x != v])
    M["graph set without race/ethnicity"] = slope(c, [x for x in G if x not in ("black", "hispanic", "asian")])
    for v in ["hs_grad", "walkability", "safety"]:
        M[f"poverty + {v}"] = slope(c, ["poverty", v])
    M["poverty + race/ethnicity"] = slope(c, ["poverty", "black", "hispanic", "asian"])
    ex = d.dropna(subset=["obesity", "active", "exercise"] + G)
    M["graph set + mediator (recent exercise): over-adjusted"] = slope(ex, G + ["exercise"])
    aux = smf.ols("active ~ " + " + ".join(G), data=c).fit()
    res["collinearity"] = {"r2_active_on_graph_set": float(aux.rsquared), "vif_active": float(1 / (1 - aux.rsquared)),
                           "r2_active_on_poverty": float(smf.ols("active ~ poverty", data=c).fit().rsquared)}
    res["corr_with_active"] = c[G + ["park", "unemployment", "exercise", "obesity"]].corrwith(c["active"]).round(3).to_dict()
    res["corr_with_obesity"] = c[G + ["park", "unemployment", "exercise", "active"]].corrwith(c["obesity"]).round(3).to_dict()
    res["sources"] = [ehdp.source(i, m, lab, p) for k, (i, m, p, lab) in MEASURES.items()]
    (DER / "commute_obesity_reanalysis.json").write_text(json.dumps(res, indent=1))
    for k, v in M.items():
        print(f"{k:55s} {v['slope']:+6.2f} ({v['lo']:+6.2f} to {v['hi']:+6.2f}) hw={v['half_width']:.2f} n={v['n']} R2={v['r2']:.2f}")
    print(res["collinearity"]); print(res["corr_with_active"]); print(res["corr_with_obesity"])

    order = ["unadjusted", "analyst: poverty", "analyst: poverty + borough", "poverty + hs_grad", "poverty + race/ethnicity",
             "poverty + walkability", "poverty + safety", "graph set (primary)", "graph set + park + unemployment",
             "graph set without walkability", "graph set without race/ethnicity", "graph set without hs_grad",
             "graph set + mediator (recent exercise): over-adjusted"]
    lab = {"graph set + mediator (recent exercise): over-adjusted": "graph set + recent exercise (a mediator)", "poverty + hs_grad": "poverty + education", "poverty + safety": "poverty + perceived safety",
           "graph set without hs_grad": "graph set without education"}
    fig, ax = plt.subplots(figsize=(10.5, 5.6))
    y = np.arange(len(order))[::-1]
    for yi, k in zip(y, order):
        v = M[k]
        col = "#1f5f8b" if k.startswith("graph set") else "#8a8a8a" if "analyst" in k or k == "unadjusted" else "#4f9d69"
        if "mediator" in k:
            col = "#b5651d"
        ax.plot([v["lo"], v["hi"]], [yi, yi], color=col, lw=2, solid_capstyle="round")
        ax.plot(v["slope"], yi, "o", color=col, ms=7 if k == "graph set (primary)" else 5)
        ax.text(v["hi"] + 0.25, yi, f"{v['slope']:+.1f}", va="center", fontsize=8, color="#333")
    ax.axvline(0, color="#444", lw=0.8)
    ax.axvspan(-4.0, 0.5, color="#1f5f8b", alpha=0.07, lw=0)
    ax.axvline(ORIG, color="#8a8a8a", lw=0.8, ls=":")
    ax.axvspan(-1.0, 0, color="#c0392b", alpha=0.10, lw=0)
    ax.set_yticks(y)
    ax.set_yticklabels([lab.get(k, k) for k in order], fontsize=8.5)
    ax.set_xlabel("Adult obesity, points per 10 points of walk-or-bike commute share (95% CI)")
    fig.suptitle("Active commuting and obesity across 42 UHF neighbourhoods, by adjustment set", fontsize=10.5, x=0.02, ha="left")
    ax.text(-3.9, len(order) - 0.55, "registered\nsupport range", fontsize=7.5, color="#1f5f8b", va="top")
    ax.text(-1.1, -0.75, "size implied by\nindividual studies", fontsize=7.5, color="#c0392b", va="top", ha="right")
    ax.set_ylim(-1.6, len(order) - 0.2)
    ax.set_xlim(-11.5, 1.6)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    FIG.mkdir(parents=True, exist_ok=True)
    f = FIG / "confounders_commute_obesity.png"
    fig.savefig(f, dpi=200)
    subprocess.run(["sips", "--embedProfile", "/System/Library/ColorSync/Profiles/sRGB Profile.icc", str(f)], capture_output=True)
    print(f.relative_to(ROOT))


if __name__ == "__main__":
    main()
