"""commute-time-depression: mean commute time (ACS 2015-19, ZCTA -> UHF42) against adult depression (CHS 2017-18)."""
from __future__ import annotations

import json

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from analyses.commuting import acs_sf
from analyses.commuting.common import DER, fetch, savefig
from analyses.mobility import ehdp

GEO = f"https://raw.githubusercontent.com/nychealth/EHDP-data/{ehdp.SHA}/geography/"


def slope(m, term, per=5.0):
    b, se = m.params[term], m.bse[term]
    return {"term": term, "per": per, "slope": float(b * per), "lo": float((b - 1.96 * se) * per),
            "hi": float((b + 1.96 * se) * per), "p": float(m.pvalues[term]), "n": int(m.nobs), "r2": float(m.rsquared)}


def commute_by_uhf():
    tt, s1 = acs_sf.zcta_2019("B08303", [1, 12, 13])
    ag, s2 = acs_sf.zcta_2019("B08013", [1])
    z = tt.merge(ag[["zcta", "B08013_001"]], on="zcta")
    z = z.rename(columns={"B08303_001": "B08303_001E", "B08303_012": "B08303_012E", "B08303_013": "B08303_013E",
                          "B08013_001": "B08013_001E"})
    vars_ = ["B08303_001E", "B08303_012E", "B08303_013E", "B08013_001E"]
    src = [s1, s2]
    xw = pd.read_csv(fetch(GEO + "zcta_to_uhf.csv", "zcta_to_uhf.csv"), dtype=str)
    zc = [c for c in xw.columns if "zcta" in c.lower() or "zip" in c.lower()][0]
    uc = [c for c in xw.columns if "uhf" in c.lower()][0]
    xw = xw[[zc, uc]].rename(columns={zc: "zcta", uc: "uhf42"}).drop_duplicates()
    m = z.merge(xw, on="zcta")
    g = m.groupby("uhf42")[vars_].sum()
    out = pd.DataFrame({"commute_min": g["B08013_001E"] / g["B08303_001E"],
                        "commute_60plus": 100 * (g["B08303_012E"] + g["B08303_013E"]) / g["B08303_001E"],
                        "workers": g["B08303_001E"]})
    out.index = out.index.astype(int)
    xsrc = {"kind": "ehdp-github", "repo": "github.com/nychealth/EHDP-data", "commit": ehdp.SHA,
            "file": "geography/zcta_to_uhf.csv", "label": "ZCTA to UHF42 crosswalk",
            "n_zcta_matched": int(m["zcta"].nunique())}
    return out, src + [xsrc]


def main():
    c, csrc = commute_by_uhf()
    d = pd.DataFrame({
        "commute_min": c["commute_min"], "commute_60plus": c["commute_60plus"],
        "depression": ehdp.wide(2417, 1324, ["2017-18"]),
        "no_exercise": 100 - ehdp.wide(2060, 500, ["2017", "2018", "2019"]),
        "obesity": ehdp.wide(2063, 506, ["2017", "2018", "2019"]),
        "poverty": ehdp.wide(103, 221, ["2015-19"]),
        "subway_access": ehdp.wide(2391, 1227, ["2018"]),
    })
    print(d.isna().sum().to_dict())
    d = d.dropna(subset=["commute_min", "depression", "poverty", "subway_access"])
    d["boro"] = [ehdp.BORO[i // 100] for i in d.index]
    d.to_csv(DER / "commute_depression_uhf42.csv", index_label="uhf42", float_format="%.3f")
    fit = lambda f, data=d: smf.ols(f, data=data).fit(cov_type="HC3")
    adj = "poverty + subway_access"
    res = {
        "primary": slope(fit(f"depression ~ commute_min + {adj}"), "commute_min"),
        "unadjusted": slope(fit("depression ~ commute_min"), "commute_min"),
        "poverty_only": slope(fit("depression ~ commute_min + poverty"), "commute_min"),
        "boro_fe": slope(fit(f"depression ~ commute_min + {adj} + C(boro)"), "commute_min"),
        "exposure_60plus_per10": slope(fit(f"depression ~ commute_60plus + {adj}"), "commute_60plus", per=10.0),
        "no_exercise": slope(fit(f"no_exercise ~ commute_min + {adj}", d.dropna(subset=["no_exercise"])), "commute_min"),
        "obesity": slope(fit(f"obesity ~ commute_min + {adj}", d.dropna(subset=["obesity"])), "commute_min"),
        "poverty_coef_per10": slope(fit(f"depression ~ commute_min + {adj}"), "poverty", per=10.0),
        "corr": d[["commute_min", "commute_60plus", "depression", "no_exercise", "obesity", "poverty", "subway_access"]].corr().round(3).to_dict(),
        "describe": d.describe().round(2).to_dict(),
    }
    for k, v in res.items():
        if "slope" in v:
            print(f"{k:22s} {v['slope']:+.2f} ({v['lo']:+.2f} to {v['hi']:+.2f}) per {v['per']}  p={v['p']:.3g} R2={v['r2']:.2f} n={v['n']}")
    print("corr commute:", res["corr"]["commute_min"])
    srcs = csrc + [ehdp.source(2417, 1324, "Depression (adults), age-adjusted % (CHS)", ["2017-18"]),
                   ehdp.source(2060, 500, "Exercise in past 30 days, % (CHS); outcome is 100 minus this", ["2017", "2018", "2019"]),
                   ehdp.source(2063, 506, "Adult obesity, % (CHS)", ["2017", "2018", "2019"]),
                   ehdp.source(103, 221, "Poverty, % below FPL (ACS)", ["2015-19"]),
                   ehdp.source(2391, 1227, "Residents within 1/4 mile of a subway entrance, %", ["2018"])]
    (DER / "commute_depression_results.json").write_text(json.dumps({"results": res, "sources": srcs}, indent=1))

    # figure: (a) map of mean commute, (b) partial regression
    uhf = gpd.read_file(fetch(GEO + "UHF42.geojson", "UHF42.geojson"))
    idc = [col for col in uhf.columns if col.lower() in ("geocode", "uhfcode", "id", "uhf", "geoid")]
    uhf["uhf42"] = pd.to_numeric(uhf[idc[0]], errors="coerce")
    uhf = uhf.merge(d, left_on="uhf42", right_index=True, how="left")
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.4), gridspec_kw={"width_ratios": [1, 1.05]})
    ax = axes[0]
    uhf.plot(column="commute_min", cmap="viridis", ax=ax, edgecolor="white", lw=0.4, legend=True,
             legend_kwds={"label": "Mean travel time to work, minutes (ACS 2015-19)", "shrink": 0.7},
             missing_kwds={"color": "#ddd"})
    ax.set_axis_off()
    ax.set_title("(a) Mean one-way commute by UHF42 neighbourhood", fontsize=10)
    ax = axes[1]
    rc = smf.ols(f"commute_min ~ {adj}", d).fit().resid
    rd = smf.ols(f"depression ~ {adj}", d).fit().resid
    cols = {"Bronx": "#c0392b", "Brooklyn": "#2c3e50", "Manhattan": "#e67e22", "Queens": "#16a085", "Staten Island": "#8e44ad"}
    for b, col in cols.items():
        k = d["boro"] == b
        ax.scatter(rc[k], rd[k], s=30, color=col, label=b)
    bb = np.polyfit(rc, rd, 1)
    xx = np.linspace(rc.min(), rc.max(), 50)
    ax.plot(xx, np.polyval(bb, xx), color="k", lw=1, label=f"adjusted fit, {res['primary']['slope']:+.2f} pts per 5 min")
    ax.plot(xx, xx * 0.3 / 5, color="#999", lw=1, ls="--", label="upper research-implied slope, +0.3 per 5 min")
    ax.axhline(0, color="#ccc", lw=0.5)
    ax.axvline(0, color="#ccc", lw=0.5)
    ax.set_xlabel("Mean commute, residual after poverty and subway access (minutes)")
    ax.set_ylabel("Depression (age-adjusted %), residual (points)")
    ax.set_title("(b) Commute time and adult depression, adjusted", fontsize=10)
    ax.legend(frameon=False, fontsize=7.5)
    fig.suptitle("Commute time and depression across 42 UHF neighbourhoods (ACS 2015-19; NYC Community Health Survey 2017-18)", fontsize=9)
    fig.tight_layout()
    print(savefig(fig, "commute_time_depression_uhf42.png"))


if __name__ == "__main__":
    main()
