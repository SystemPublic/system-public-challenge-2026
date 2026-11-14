"""heat-trees-surftemp, heat-surftemp-ed and heat-trees-ed-chain: street trees -> surface temperature -> heat ED visits,
across NYC community districts (primary) and NTA2010 neighbourhoods (secondary).

Registered plans in claims/registered/. Data:
  2015 Street Tree Census (uvpi-gqnh), live trees by cb_num and nta (SoQL group)
  EHDP-data (nychealth, pinned commit): indicators 2141 surface temperature, 2143 vegetative cover,
    2443 heat-stress ED visits (5-year, age-adjusted rate), 2410 heat hospitalizations (10-year, age-adjusted);
    key-topics/heat-vulnerability-index/hvi-nta.csv (poverty, percent Black, AC, HRI hospitalization rate by NTA2010);
    geography/CD.geojson and NTA2010.topo.json for land area.
Outputs: data/derived/heat/bridge_cd.csv, bridge_nta.csv, bridge_results.json
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from analyses.heat.common import DER
from analyses.heat.ed_syndromic import SHA, source
from concord import socrata

E = DER / "ehdp"
KM_PER_DEG_LAT = 111.32


def ring_area_km2(coords) -> float:
    xy = np.asarray(coords, dtype=float)
    lat0 = np.deg2rad(40.7)
    x = xy[:, 0] * KM_PER_DEG_LAT * np.cos(lat0)
    y = xy[:, 1] * KM_PER_DEG_LAT
    return 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))


def poly_area(rings) -> float:
    return ring_area_km2(rings[0]) - sum(ring_area_km2(r) for r in rings[1:])


def cd_areas() -> pd.Series:
    g = json.loads((E / "CD.geojson").read_text())
    out = {}
    for f in g["features"]:
        geom = f["geometry"]
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        out[int(f["properties"]["GEOCODE"])] = sum(poly_area(p) for p in polys)
    return pd.Series(out, name="area_km2")


def nta_areas() -> pd.Series:
    t = json.loads((E / "NTA2010.topo.json").read_text())
    sx, sy = t["transform"]["scale"]
    tx, ty = t["transform"]["translate"]
    arcs = []
    for a in t["arcs"]:
        q = np.cumsum(np.asarray(a, dtype=float), axis=0)
        arcs.append(np.column_stack([q[:, 0] * sx + tx, q[:, 1] * sy + ty]))

    def ring(idx):
        pts = []
        for i in idx:
            a = arcs[i] if i >= 0 else arcs[~i][::-1]
            pts.extend(a if not pts else a[1:])
        return pts

    out = {}
    for g in list(t["objects"].values())[0]["geometries"]:
        polys = g["arcs"] if g["type"] == "MultiPolygon" else [g["arcs"]]
        out[g["properties"]["NTACode"]] = sum(poly_area([ring(r) for r in p]) for p in polys)
    return pd.Series(out, name="area_km2")


def ehdp(ind: int, measure: int, geotype: str) -> pd.Series:
    d = pd.DataFrame(json.loads((E / f"indicator_{ind}.json").read_text()))
    d = d[(d["MeasureID"] == measure) & (d["GeoType"] == geotype)]
    d = d[d["TimePeriodID"] == d["TimePeriodID"].max()]
    return d.set_index("GeoID")["Value"].astype(float)


def trees():
    rows_cd, src_cd = socrata.query("uvpi-gqnh", select="cb_num, count(*) as n", where="status='Alive'", group="cb_num")
    rows_nta, src_nta = socrata.query("uvpi-gqnh", select="nta, count(*) as n", where="status='Alive'", group="nta")
    cd = pd.Series({int(r["cb_num"]): int(r["n"]) for r in rows_cd}, name="trees")
    nta = pd.Series({r["nta"]: int(r["n"]) for r in rows_nta if r.get("nta")}, name="trees")
    return cd, nta, [src_cd, src_nta]


def z(s):
    return (s - s.mean()) / s.std()


def ols(formula, data):
    return smf.ols(formula, data).fit(cov_type="HC3")


def coef(res, name, exp=False, scale=1.0):
    b, se = res.params[name] * scale, res.bse[name] * scale
    f = (lambda v: 100 * (np.exp(v) - 1)) if exp else (lambda v: v)
    return {"estimate": float(f(b)), "lo": float(f(b - 1.96 * se)), "hi": float(f(b + 1.96 * se)), "p": float(res.pvalues[name]),
            "n": int(res.nobs), "r2": float(res.rsquared)}


def main():
    t_cd, t_nta, src_t = trees()
    hvi = pd.read_csv(E / "hvi-nta.csv", encoding="utf-8-sig")
    # ---------------- community districts
    cd = pd.DataFrame({"area_km2": cd_areas()})
    cd["trees"] = t_cd
    cd["surftemp_f"] = ehdp(2141, 688, "CD")
    cd["vegcover_pct"] = ehdp(2143, 690, "CD")
    cd["hed_rate"] = ehdp(2443, 1405, "CD")
    cd["hosp_rate"] = ehdp(2410, 1283, "CD")
    cov = hvi.groupby("CD")[["POV_PCT", "PCT_BLACK_POP", "PCT_HOUSEHOLDS_AC"]].mean()
    cd = cd.join(cov)
    cd["boro"] = (cd.index // 100).map({1: "MN", 2: "BX", 3: "BK", 4: "QN", 5: "SI"})
    cd["tree_density"] = cd["trees"] / cd["area_km2"]
    cd["ztree"] = z(np.log(cd["tree_density"]))
    cd["log_hed"] = np.log(cd["hed_rate"])
    cd["log_hosp"] = np.log(cd["hosp_rate"])
    cd.index.name = "cd"
    cd.to_csv(DER / "bridge_cd.csv")
    out = {"cd": {"n_cd": int(len(cd)), "n_with_hed": int(cd["hed_rate"].notna().sum()),
                  "suppressed_hed": [int(i) for i in cd.index[cd["hed_rate"].isna()]],
                  "tree_density_sd_log": float(np.log(cd["tree_density"]).std()),
                  "corr": cd[["tree_density", "surftemp_f", "vegcover_pct", "hed_rate", "POV_PCT", "PCT_BLACK_POP", "PCT_HOUSEHOLDS_AC"]]
                  .corr(method="spearman").round(3).to_dict()}}
    adj = " + POV_PCT + PCT_BLACK_POP"
    # link a: trees -> surface temperature
    a_un = ols("surftemp_f ~ ztree", cd)
    a_adj = ols("surftemp_f ~ ztree" + adj, cd)
    a_boro = ols("surftemp_f ~ ztree" + adj + " + C(boro)", cd)
    cd["zveg"] = z(cd["vegcover_pct"])
    a_veg = ols("surftemp_f ~ zveg" + adj, cd)
    out["link_a"] = {"unadjusted": coef(a_un, "ztree"), "adjusted": coef(a_adj, "ztree"),
                     "adjusted_plus_borough": coef(a_boro, "ztree"), "vegcover_adjusted": coef(a_veg, "zveg"),
                     "pearson_r_unadjusted": float(cd[["ztree", "surftemp_f"]].corr().iloc[0, 1]),
                     "scale": "F of surface temperature per 1 SD of log live street trees per km2"}
    # link b: surface temperature -> heat ED rate
    c = cd.dropna(subset=["hed_rate", "surftemp_f", "POV_PCT"])
    b_un = ols("log_hed ~ surftemp_f", c)
    b_adj = ols("log_hed ~ surftemp_f" + adj + " + PCT_HOUSEHOLDS_AC", c)
    b_adj_t = ols("log_hed ~ surftemp_f + ztree" + adj + " + PCT_HOUSEHOLDS_AC", c)
    b_pov = ols("log_hed ~ POV_PCT", c)
    ch = cd.dropna(subset=["hosp_rate", "surftemp_f", "POV_PCT"])
    h_un = ols("log_hosp ~ surftemp_f", ch)
    h_adj = ols("log_hosp ~ surftemp_f + ztree" + adj + " + PCT_HOUSEHOLDS_AC", ch)
    out["link_b"] = {"unadjusted": coef(b_un, "surftemp_f", exp=True), "adjusted": coef(b_adj, "surftemp_f", exp=True),
                     "adjusted_incl_trees": coef(b_adj_t, "surftemp_f", exp=True),
                     "poverty_only_per_10pts": coef(b_pov, "POV_PCT", exp=True, scale=10),
                     "poverty_in_adjusted_per_10pts": coef(b_adj_t, "POV_PCT", exp=True, scale=10),
                     "black_in_adjusted_per_10pts": coef(b_adj_t, "PCT_BLACK_POP", exp=True, scale=10),
                     "hosp_unadjusted": coef(h_un, "surftemp_f", exp=True), "hosp_adjusted": coef(h_adj, "surftemp_f", exp=True),
                     "scale": "percent change in age-adjusted heat-stress ED rate per 1 F surface temperature"}
    # total association trees -> ED
    t_un = ols("log_hed ~ ztree", c)
    t_adj = ols("log_hed ~ ztree" + adj + " + PCT_HOUSEHOLDS_AC", c)
    out["total"] = {"unadjusted": coef(t_un, "ztree", exp=True), "adjusted": coef(t_adj, "ztree", exp=True),
                    "scale": "percent change in heat ED rate per 1 SD log street-tree density"}
    # chain: a*b with bootstrap over CDs
    rng = np.random.default_rng(20261112)
    est = []
    cc = c.reset_index(drop=True)
    for _ in range(5000):
        s = cc.iloc[rng.integers(0, len(cc), len(cc))]
        try:
            ra = smf.ols("surftemp_f ~ ztree" + adj, s).fit()
            rb = smf.ols("log_hed ~ surftemp_f + ztree" + adj + " + PCT_HOUSEHOLDS_AC", s).fit()
            est.append(ra.params["ztree"] * rb.params["surftemp_f"])
        except Exception:
            continue
    est = np.asarray(est)
    a_c = smf.ols("surftemp_f ~ ztree" + adj, cc).fit().params["ztree"]
    b_c = smf.ols("log_hed ~ surftemp_f + ztree" + adj + " + PCT_HOUSEHOLDS_AC", cc).fit().params["surftemp_f"]
    pt = a_c * b_c
    out["chain"] = {"indirect_pct": float(100 * (np.exp(pt) - 1)),
                    "lo": float(100 * (np.exp(np.percentile(est, 2.5)) - 1)), "hi": float(100 * (np.exp(np.percentile(est, 97.5)) - 1)),
                    "n_boot": int(len(est)), "n": int(len(cc)), "a_F_per_sd": float(a_c), "b_log_per_F": float(b_c),
                    "scale": "percent change in heat ED rate per 1 SD log street-tree density, through surface temperature"}
    # ---------------- NTA2010 secondary
    nta = hvi.set_index("NTACode")[["GEONAME", "CD", "POV_PCT", "PCT_BLACK_POP", "GREENSPACE", "SURFACETEMP", "PCT_HOUSEHOLDS_AC", "HRI_HOSP_RATE", "HVI_RANK"]].copy()
    nta = nta.join(nta_areas()).join(t_nta)
    nta["tree_density"] = nta["trees"] / nta["area_km2"]
    nta = nta[nta["tree_density"] > 0]
    nta["ztree"] = z(np.log(nta["tree_density"]))
    nta["log_hosp"] = np.log(nta["HRI_HOSP_RATE"].where(nta["HRI_HOSP_RATE"] > 0))
    nta.index.name = "nta"
    nta.to_csv(DER / "bridge_nta.csv")
    n2 = nta.dropna(subset=["SURFACETEMP", "POV_PCT", "PCT_BLACK_POP"])
    na_un = ols("SURFACETEMP ~ ztree", n2)
    na_adj = ols("SURFACETEMP ~ ztree" + adj, n2)
    nb = n2.dropna(subset=["log_hosp", "PCT_HOUSEHOLDS_AC"])
    nb_un = ols("log_hosp ~ SURFACETEMP", nb)
    nb_adj = ols("log_hosp ~ SURFACETEMP + ztree" + adj + " + PCT_HOUSEHOLDS_AC", nb)
    out["nta"] = {"n": int(len(n2)), "link_a_unadjusted": coef(na_un, "ztree"), "link_a_adjusted": coef(na_adj, "ztree"),
                  "link_b_hosp_unadjusted": coef(nb_un, "SURFACETEMP", exp=True), "link_b_hosp_adjusted": coef(nb_adj, "SURFACETEMP", exp=True),
                  "n_hosp": int(len(nb)), "zero_hosp_rate_ntas": int((nta["HRI_HOSP_RATE"] == 0).sum())}
    out["sources"] = src_t + [source(p) for p in ("indicators/data/2141.json", "indicators/data/2143.json", "indicators/data/2443.json",
                                                   "indicators/data/2410.json", "key-topics/heat-vulnerability-index/hvi-nta.csv",
                                                   "geography/CD.geojson", "geography/NTA2010.topo.json")]
    (DER / "bridge_results.json").write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps({k: v for k, v in out.items() if k not in ("sources",)}, indent=1, default=str))


if __name__ == "__main__":
    main()
