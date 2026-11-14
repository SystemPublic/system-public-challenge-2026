#!/usr/bin/env python
"""graph-confounders-trees-surftemp and graph-confounders-surftemp-ed.

Re-estimates the two community-district heat links (analyses/heat/bridge.py) with the covariates that
the System Public Graph names as common causes: population density, built-up area and road area for
street trees and surface temperature; older adults living alone for surface temperature and heat illness.
Written before registration; run only after both registrations were committed and pushed.

Run: ~/.venvs/nyc-concordance/bin/python -m analyses.round2_heat_confounders.reanalysis
Outputs: data/derived/round2/heat_confounders/{cd.csv,nta.csv,tracts.csv,results.json}
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from statsmodels.stats.outliers_influence import variance_inflation_factor

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from analyses.heat import bridge  # noqa: E402
from analyses.mobility import ehdp  # noqa: E402
from concord import socrata  # noqa: E402

OUT = ROOT / "data" / "derived" / "round2" / "heat_confounders"
OUT.mkdir(parents=True, exist_ok=True)
FT2_PER_KM2 = 10763910.4
ACS = ["2015-19"]
SEED = 20261113
NBOOT = 5000


def pluto(group: str):
    """Tax-lot sums by `group`: lot area (not submerged), footprint (bldgarea/numfloors), floor area."""
    lots, s1 = socrata.query("64uk-42ks", select=f"{group}, sum(lotarea) as lot_ft2, count(*) as lots",
                             where="lottype != '9' OR lottype IS NULL", group=group)
    blds, s2 = socrata.query("64uk-42ks", select=f"{group}, sum(bldgarea/numfloors) as foot_ft2, sum(bldgarea) as floor_ft2",
                             where="numfloors > 0 AND bldgarea > 0", group=group)
    ver, s3 = socrata.query("64uk-42ks", select="version, count(*)", group="version")
    keys = [g.strip() for g in group.split(",")]
    a = pd.DataFrame(lots).dropna(subset=keys).set_index(keys).astype(float)  # lots with no district or tract are left out
    b = pd.DataFrame(blds).dropna(subset=keys).set_index(keys).astype(float)
    return a.join(b, how="left").fillna(0.0), [s1, s2], ver


def vif(data: pd.DataFrame, cols: list[str]) -> dict:
    X = data[cols].astype(float).to_numpy()
    X = np.column_stack([np.ones(len(X)), X])
    return {c: float(variance_inflation_factor(X, i + 1)) for i, c in enumerate(cols)}


def fit(formula, data):
    return smf.ols(formula, data).fit(cov_type="HC3")


def est(res, name, pct=False):
    b, se = res.params[name], res.bse[name]
    f = (lambda v: 100 * (np.exp(v) - 1)) if pct else (lambda v: v)
    return {"estimate": float(f(b)), "lo": float(f(b - 1.96 * se)), "hi": float(f(b + 1.96 * se)), "se_raw": float(se),
            "n": int(res.nobs), "r2": float(res.rsquared)}


def change(data, y, x, base, extra, pct=False):
    """Change in the coefficient of x when `extra` is added to `base`, same rows, paired bootstrap over units."""
    f0 = f"{y} ~ {x} + " + " + ".join(base)
    f1 = f0 + " + " + " + ".join(extra)
    d = data.dropna(subset=[y, x] + base + extra).reset_index(drop=True)
    r0, r1 = fit(f0, d), fit(f1, d)
    tr = (lambda v: 100 * (np.exp(v) - 1)) if pct else (lambda v: v)
    rng = np.random.default_rng(SEED)
    diffs, b1s = [], []
    for _ in range(NBOOT):
        s = d.iloc[rng.integers(0, len(d), len(d))]
        try:
            a0 = smf.ols(f0, s).fit().params[x]
            a1 = smf.ols(f1, s).fit().params[x]
        except Exception:
            continue
        diffs.append(tr(a1) - tr(a0))
        b1s.append(tr(a1))
    diffs = np.asarray(diffs)
    v = vif(d, [x] + base + extra)
    out = {"original": est(r0, x, pct), "graph_set": est(r1, x, pct),
           "change": {"estimate": float(tr(r1.params[x]) - tr(r0.params[x])), "lo": float(np.percentile(diffs, 2.5)),
                      "hi": float(np.percentile(diffs, 97.5)), "boot_se": float(diffs.std()), "n_boot": int(len(diffs))},
           "graph_set_boot_ci": [float(np.percentile(b1s, 2.5)), float(np.percentile(b1s, 97.5))],
           "vif": v, "max_vif": float(max(v.values())),
           "covariate_coefs": {k: {"b": float(r1.params[k]), "se": float(r1.bse[k]), "p": float(r1.pvalues[k])} for k in extra},
           "partial_r2_exposure_on_extra": float(1 - fit(f"{x} ~ " + " + ".join(base + extra), d).ssr / fit(f"{x} ~ " + " + ".join(base), d).ssr),
           "formula_original": f0, "formula_graph_set": f1, "n": int(len(d))}
    return out


def main():
    res = {}
    sources = []
    cd = pd.read_csv(ROOT / "data/derived/heat/bridge_cd.csv").set_index("cd")
    # ---- covariates, community districts
    p, src, ver = pluto("cd")
    sources += src
    res["pluto_version"] = ver
    p.index = p.index.astype(float).astype(int)
    cd = cd.join(p)
    cd["pop"] = ehdp.wide(2325, 992, ACS, "CD")
    cd["alone65"] = ehdp.wide(2146, 693, ACS, "CD")
    cd["traffic"] = ehdp.wide(2112, 643, ["2019"], "CD")
    cd["log_popdens"] = np.log(cd["pop"] / cd["area_km2"])
    cd["built_share"] = 100 * cd["foot_ft2"] / FT2_PER_KM2 / cd["area_km2"]
    cd["road_share"] = 100 * (1 - cd["lot_ft2"] / FT2_PER_KM2 / cd["area_km2"])
    cd["log_far"] = np.log(cd["floor_ft2"] / FT2_PER_KM2 / cd["area_km2"])
    cd["log_traffic"] = np.log(cd["traffic"])
    cd.to_csv(OUT / "cd.csv")
    G = ["log_popdens", "built_share", "road_share"]
    A0 = ["POV_PCT", "PCT_BLACK_POP"]
    B0 = A0 + ["PCT_HOUSEHOLDS_AC"]
    res["cd_describe"] = cd[G + ["alone65", "log_far", "log_traffic", "ztree", "surftemp_f"]].describe().round(3).to_dict()
    res["cd_corr"] = cd[["ztree", "surftemp_f", "log_hed", "vegcover_pct"] + G + ["alone65", "log_far", "log_traffic"] + B0].corr().round(3).to_dict()
    res["road_share_out_of_range"] = [int(i) for i in cd.index[(cd["road_share"] < 0) | (cd["road_share"] > 60)]]
    # ---- claim A
    A = {"primary": change(cd, "surftemp_f", "ztree", A0, G)}
    for k, extra in {"popdens_only": ["log_popdens"], "built_only": ["built_share"], "road_only": ["road_share"],
                     "popdens_built": ["log_popdens", "built_share"], "far_in_place_of_built": ["log_popdens", "log_far", "road_share"],
                     "traffic_in_place_of_road": ["log_popdens", "built_share", "log_traffic"]}.items():
        A[k] = change(cd, "surftemp_f", "ztree", A0, extra)
    cd["zveg"] = bridge.z(cd["vegcover_pct"])
    A["vegcover_exposure"] = change(cd, "surftemp_f", "zveg", A0, G)
    res["A_cd"] = A
    # ---- claim B
    B = {"primary": change(cd, "log_hed", "surftemp_f", B0, ["alone65"], pct=True),
         "plus_built_form": change(cd, "log_hed", "surftemp_f", B0, ["alone65"] + G, pct=True),
         "built_form_only": change(cd, "log_hed", "surftemp_f", B0, G, pct=True)}
    res["B_cd"] = B
    # ---- NTA2010 secondary
    nta = pd.read_csv(ROOT / "data/derived/heat/bridge_nta.csv").set_index("nta")
    t, src_t, _ = pluto("borocode, ct2010")
    sources += src_t
    eq, src_eq = socrata.query("8ius-dhrr", select="_2010_nyc_borough_code as b, _2010_census_tract as t, neighborhood_tabulation_area_nta_code as nta")
    sources.append(src_eq)
    eqm = {(str(int(float(r["b"]))), str(r["t"]).strip().zfill(6)): r["nta"] for r in eq}

    def tract_key(b, ct):
        ct = str(ct).strip()
        if "." in ct:
            a, f = ct.split(".")
            ct = a.zfill(4) + f.ljust(2, "0")[:2]
        else:
            ct = ct.zfill(4) + "00"
        return (str(int(float(b))), ct)

    t = t.reset_index()
    t["nta"] = [eqm.get(tract_key(b, c)) for b, c in zip(t["borocode"], t["ct2010"])]
    res["tract_match"] = {"tracts": int(len(t)), "matched": int(t["nta"].notna().sum()),
                          "lot_area_share_matched": float(t.loc[t["nta"].notna(), "lot_ft2"].sum() / t["lot_ft2"].sum())}
    t.to_csv(OUT / "tracts.csv", index=False)
    agg = t.dropna(subset=["nta"]).groupby("nta")[["lot_ft2", "foot_ft2", "floor_ft2"]].sum()
    nta = nta.join(agg)
    pop = ehdp.measure(2325, 992, "NTA2010")
    alone = ehdp.measure(2146, 693, "NTA2010")
    geo = pd.read_csv(ROOT / "data/derived/heat/ehdp/hvi-nta.csv", encoding="utf-8-sig").drop_duplicates("GEOCODE").set_index("GEOCODE")["NTACode"]
    nta["pop"] = pop[pop["period"].isin(ACS)].set_index("GeoID")["Value"].rename(index=geo).groupby(level=0).mean()
    nta["alone65"] = alone[alone["period"].isin(ACS)].set_index("GeoID")["Value"].rename(index=geo).groupby(level=0).mean()
    nta["log_popdens"] = np.log(nta["pop"].where(nta["pop"] > 0) / nta["area_km2"])
    nta["built_share"] = 100 * nta["foot_ft2"] / FT2_PER_KM2 / nta["area_km2"]
    nta["road_share"] = 100 * (1 - nta["lot_ft2"] / FT2_PER_KM2 / nta["area_km2"])
    nta.to_csv(OUT / "nta.csv")
    res["A_nta"] = {"primary": change(nta, "SURFACETEMP", "ztree", A0, G),
                    "popdens_only": change(nta, "SURFACETEMP", "ztree", A0, ["log_popdens"]),
                    "road_only": change(nta, "SURFACETEMP", "ztree", A0, ["road_share"]),
                    "built_only": change(nta, "SURFACETEMP", "ztree", A0, ["built_share"])}
    res["nta_corr"] = nta[["ztree", "SURFACETEMP", "GREENSPACE"] + G + ["alone65"] + B0].corr().round(3).to_dict()
    res["B_nta_hosp"] = {"primary": change(nta, "log_hosp", "SURFACETEMP", ["ztree"] + B0, ["alone65"], pct=True)}
    # ---- how much of built form lies between NTAs (what an NTA fixed effect removes), tract level, descriptive
    tt = t.dropna(subset=["nta"]).copy()
    tt = tt[tt["lot_ft2"] > 0]
    tt["built_per_lot"] = 100 * tt["foot_ft2"] / tt["lot_ft2"]
    tt["log_far_lot"] = np.log((tt["floor_ft2"] / tt["lot_ft2"]).where(tt["floor_ft2"] > 0))
    dec = {}
    for c in ("built_per_lot", "log_far_lot"):
        s = tt.dropna(subset=[c])
        s = s[s.groupby("nta")[c].transform("size") >= 2]
        tot = ((s[c] - s[c].mean()) ** 2).sum()
        within = ((s[c] - s.groupby("nta")[c].transform("mean")) ** 2).sum()
        dec[c] = {"tracts": int(len(s)), "ntas": int(s["nta"].nunique()), "share_between_nta": float(1 - within / tot),
                  "sd_total": float(s[c].std()), "sd_within_nta": float(np.sqrt(within / (len(s) - s["nta"].nunique())))}
    res["built_form_between_nta"] = dec
    res["sources"] = sources + [ehdp.source(2325, 992, "Total population (ACS)", ACS) | {"geotype": "CD, NTA2010"},
                                ehdp.source(2146, 693, "Older adults living alone (65+), percent (ACS)", ACS) | {"geotype": "CD, NTA2010"},
                                ehdp.source(2112, 643, "Traffic density, million vehicle miles per square mile", ["2019"]) | {"geotype": "CD"}]
    (OUT / "results.json").write_text(json.dumps(res, indent=1, default=str))
    show = {k: {m: {q: v[q] for q in ("original", "graph_set", "change", "max_vif", "n")} for m, v in res[k].items()} for k in ("A_cd", "B_cd", "A_nta", "B_nta_hosp")}
    print(json.dumps(show, indent=1, default=lambda o: round(o, 3)))
    print(json.dumps({k: res[k] for k in ("tract_match", "built_form_between_nta", "road_share_out_of_range")}, indent=1))


if __name__ == "__main__":
    main()
