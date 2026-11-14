"""Referee re-estimation for all-boats-trees-rent. Written by the blind referee, not the registrant.

Run from the repository root:
    ~/.venvs/nyc-concordance/bin/python analyses/critique/referee_trees_rent.py

It rebuilds the tree counts from the downloaded tree points and the rent change from the raw
ACS summary files with its own code (it imports nothing from analyses/all_boats or
analyses/neighbourhood), refits the registered model, and runs variants the registrant did not
run. It reads files already on disk, fetches nothing, prints its results and writes no file.
The tree points are in ~/opt/nyc-concordance/all_boats/ (outside Dropbox).
"""
from __future__ import annotations

import io
import warnings
import zipfile
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats
from scipy.spatial import cKDTree

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[2]
BIG = Path.home() / "opt/nyc-concordance/all_boats"
RAW = ROOT / "data/raw/acs"
NB = ROOT / "data/derived/neighbourhood"
AB = ROOT / "data/derived/all_boats"
COUNTIES = ("36005", "36047", "36061", "36081", "36085")
BORO = {"1": "Manhattan", "2": "Bronx", "3": "Brooklyn", "4": "Queens", "5": "Staten Island"}
RHS = "trees05_km + lrent12 + nhw_share12 + ldens12 + C(boro)"


def show(label, est, lo, hi, extra=""):
    print(f"  {label:<58s} {est:8.4f} ({lo:7.4f} to {hi:7.4f}) {extra}")


# ---------------------------------------------------------------- trees
def trees(tr):
    out, info = {}, {}
    for ds, yr in (("29bw-z7pj", 2005), ("uvpi-gqnh", 2015)):
        d = pd.read_csv(BIG / f"{ds}.csv")
        info[yr] = {"rows": len(d), "status": d.status.value_counts().to_dict(),
                    "lon_zero_or_missing": int(((d.longitude == 0) | d.longitude.isna() | (d.latitude == 0)).sum())}
        live = d[d.status != "Dead"] if yr == 2005 else d[d.status == "Alive"]
        g = gpd.GeoDataFrame(live[["tree_dbh"]], geometry=gpd.points_from_xy(live.longitude, live.latitude), crs=4326)
        j = gpd.sjoin(g, tr[["geoid", "geometry"]], predicate="within", how="inner")
        info[yr]["living"] = len(live)
        info[yr]["in_tract"] = len(j)
        out[f"t{yr}"] = j.groupby("geoid").size()
        for cut in (3, 6):
            out[f"young{cut}_{yr}"] = j[j.tree_dbh <= cut].groupby("geoid").size()
        out[f"big_{yr}"] = j[j.tree_dbh >= 12].groupby("geoid").size()
    return pd.DataFrame(out).reindex(tr.geoid).fillna(0).astype(int).rename_axis("geoid").reset_index(), info


# ---------------------------------------------------------------- rent
def rent22():
    rows = []
    with open(RAW / "acsdt5y2022-b25064.dat") as fh:
        fh.readline()
        for line in fh:
            if line.startswith("1400000US36") and line[9:14] in COUNTIES:
                rows.append(line.rstrip("\n").split("|"))
    d = pd.DataFrame(rows, columns=["g", "r22", "m22"])
    d["geoid"] = d.g.str[-11:]
    d[["r22", "m22"]] = d[["r22", "m22"]].apply(pd.to_numeric, errors="coerce")
    d.loc[d.r22 <= 0, "r22"] = np.nan
    d.loc[d.m22 <= 0, "m22"] = np.nan
    return d[["geoid", "r22", "m22"]]


def seq2012(seq, col):
    with zipfile.ZipFile(RAW / f"20125ny{seq:04d}000.zip") as zf:
        e = pd.read_csv(zf.open(f"e20125ny{seq:04d}000.txt"), header=None, dtype=str)
        m = pd.read_csv(zf.open(f"m20125ny{seq:04d}000.txt"), header=None, dtype=str)
    return pd.DataFrame({"LOGRECNO": e[5], "e": pd.to_numeric(e[col - 1], errors="coerce"),
                         "m": pd.to_numeric(m[col - 1], errors="coerce")})


def acs12():
    geo = pd.read_csv(RAW / "g20125ny.csv", header=None, dtype=str, encoding="latin-1")
    geo = geo[geo[2] == "140"][[4, 48]].rename(columns={4: "LOGRECNO", 48: "G"})
    geo["g10"] = geo.G.str[-11:]
    geo = geo[geo.g10.str[:5].isin(COUNTIES)]
    r = seq2012(105, 54).rename(columns={"e": "r12", "m": "m12"})
    p = seq2012(3, 130).rename(columns={"e": "pop12"})[["LOGRECNO", "pop12"]]
    t = seq2012(5, 38).rename(columns={"e": "tot12"})[["LOGRECNO", "tot12"]]
    w = seq2012(5, 40).rename(columns={"e": "nhw12"})[["LOGRECNO", "nhw12"]]
    d = geo.merge(r, on="LOGRECNO").merge(p, on="LOGRECNO").merge(t, on="LOGRECNO").merge(w, on="LOGRECNO")
    d.loc[d.r12 <= 0, ["r12", "m12"]] = np.nan
    d.loc[d.m12 <= 0, "m12"] = np.nan
    return d


def crosswalk(a):
    rel = pd.read_csv(RAW / "tab20_tract20_tract10_st36.txt", sep="|", dtype=str)
    rel = rel[rel.GEOID_TRACT_20.str[:5].isin(COUNTIES)].copy()
    for c in ("AREALAND_PART", "AREALAND_TRACT_10", "AREALAND_TRACT_20"):
        rel[c] = pd.to_numeric(rel[c])
    rel["w10"] = rel.AREALAND_PART / rel.AREALAND_TRACT_10.replace(0, np.nan)
    rel["w20"] = rel.AREALAND_PART / rel.AREALAND_TRACT_20.replace(0, np.nan)
    m = rel.merge(a, left_on="GEOID_TRACT_10", right_on="g10", how="left")
    ok = m.r12.notna()
    m["rw"] = (m.w20 * m.r12).where(ok)
    m["wn"] = m.w20.where(ok)
    m["vw"] = ((m.w20 * m.m12 / 1.645) ** 2).where(ok)
    for c in ("pop12", "tot12", "nhw12"):
        m[c] = m[c] * m.w10
    # population-weighted alternative for the median rent (weights: 2010-tract population in the part)
    m["pw"] = (m.pop12).where(ok)
    m["prw"] = m.pw * m.r12
    g = m.groupby("GEOID_TRACT_20").agg(rw=("rw", "sum"), wn=("wn", "sum"), vw=("vw", "sum"), pop12=("pop12", "sum"),
                                        tot12=("tot12", "sum"), nhw12=("nhw12", "sum"), maxw20=("w20", "max"),
                                        maxw10=("w10", "max"), nparts=("w20", lambda s: int((s > 0.01).sum())),
                                        pw=("pw", "sum"), prw=("prw", "sum"))
    g["r12"] = g.rw / g.wn.replace(0, np.nan)
    g["se12"] = np.sqrt(g.vw) / g.wn.replace(0, np.nan)
    g["r12_popw"] = g.prw / g.pw.replace(0, np.nan)
    g["same"] = (g.maxw20 > 0.98) & (g.nparts == 1)
    return g.rename_axis("geoid").reset_index()[["geoid", "r12", "se12", "r12_popw", "pop12", "tot12", "nhw12", "same", "maxw10"]]


# ---------------------------------------------------------------- estimation helpers
def ols(d, x="dt100", rhs=RHS, y="dlr", groups="nta2020"):
    m = smf.ols(f"{y} ~ {x} + {rhs}", d).fit(cov_type="cluster", cov_kwds={"groups": d[groups]})
    lo, hi = m.conf_int().loc[x]
    return m.params[x], lo, hi, m.bse[x], m


def conley(m, d, xy, cut_km):
    X = m.model.exog
    e = m.resid.values
    D = np.sqrt(((xy[:, None, :] - xy[None, :, :]) ** 2).sum(-1)) / 1000.0
    K = np.clip(1 - D / cut_km, 0, None)
    Xe = X * e[:, None]
    meat = Xe.T @ K @ Xe
    bread = np.linalg.inv(X.T @ X)
    V = bread @ meat @ bread
    i = m.model.exog_names.index("dt100")
    return float(np.sqrt(V[i, i]))


def moran(v, xy, k=6, draws=999, seed=1):
    _, idx = cKDTree(xy).query(xy, k=k + 1)
    idx = idx[:, 1:]
    z = (v - v.mean()) / v.std()
    stat = float((z[:, None] * z[idx]).mean())
    rng = np.random.default_rng(seed)
    perm = [float((zp[:, None] * zp[idx]).mean()) for zp in (rng.permutation(z) for _ in range(draws))]
    return stat, float((np.sum(np.abs(perm) >= abs(stat)) + 1) / (draws + 1))


def iv(d, x, z, rhs=RHS, y="dlr"):
    import patsy
    Y, X = patsy.dmatrices(f"{y} ~ {x} + {rhs}", d, return_type="dataframe")
    Z = X.copy()
    Z[x] = d[z].values
    Xv, Zv, yv = X.values, Z.values, Y.values[:, 0]
    A = np.linalg.inv(Zv.T @ Xv)
    b = A @ Zv.T @ yv
    e = yv - Xv @ b
    meat = np.zeros((Xv.shape[1],) * 2)
    for _, ix in d.reset_index(drop=True).groupby("nta2020").indices.items():
        s = Zv[ix].T @ e[ix]
        meat += np.outer(s, s)
    V = A @ meat @ A.T
    i = list(X.columns).index(x)
    se = float(np.sqrt(V[i, i]))
    return float(b[i]), float(b[i] - 1.96 * se), float(b[i] + 1.96 * se), se


def eiv(d, su2):
    """Moment correction for classical error of variance su2 in lrent12, which also enters the
    outcome with the opposite sign (d_logrent = log rent22 - log rent12)."""
    import patsy
    Y, X = patsy.dmatrices(f"dlr ~ dt100 + {RHS}", d, return_type="dataframe")
    Xv, yv = X.values, Y.values[:, 0]
    k = list(X.columns).index("lrent12")
    n = len(yv)
    S = np.zeros((Xv.shape[1],) * 2)
    S[k, k] = n * su2
    s = np.zeros(Xv.shape[1])
    s[k] = n * su2
    b = np.linalg.solve(Xv.T @ Xv - S, Xv.T @ yv + s)
    return float(b[list(X.columns).index("dt100")]), float(b[k])


def main():
    tr = gpd.read_file(NB / "tracts.geojson")
    tr["geoid"] = tr.geoid.astype(str)
    cen = tr.to_crs(2263).geometry.centroid
    tr["cx"], tr["cy"] = cen.x * 0.3048, cen.y * 0.3048
    tr["km2"] = tr.to_crs(2263).geometry.area * 0.09290304 / 1e6
    tc, info = trees(tr)
    print("== 1. Tree files")
    for yr, i in info.items():
        print(" ", yr, i)
    reg = pd.read_csv(AB / "tree_counts_tracts.csv", dtype={"geoid": str})
    chk = tc.merge(reg, on="geoid")
    print("  my counts equal the registrant's in every tract:", bool((chk.t2005 == chk.trees2005).all() and (chk.t2015 == chk.trees2015).all()))

    acs = pd.read_csv(NB / "tracts_acs.csv", dtype={"GEOID": str}).rename(columns={"GEOID": "geoid"})
    x = crosswalk(acs12())
    r22 = rent22()
    d = tr[["geoid", "cx", "cy", "km2"]].merge(tc, on="geoid").merge(x, on="geoid", how="left").merge(r22, on="geoid", how="left")
    d = d.merge(acs[["geoid", "borocode", "nta2020", "pop", "poverty", "rent12", "rent22", "d_logrent", "land_km2", "pop12", "nhw_share12"]].rename(
        columns={"pop12": "pop12_reg", "nhw_share12": "nhw_reg"}), on="geoid", how="left")
    print("\n== 2. Rent rebuilt from the raw ACS files")
    both = d[d.rent12.notna() & d.r12.notna()]
    print("  max abs difference, my 2008-12 rent against the registrant's:", float((both.r12 - both.rent12).abs().max()))
    print("  max abs difference, 2018-22 rent:", float((d.r22 - d.rent22).abs().max()))
    d["boro"] = d.borocode.astype(str)
    d["nhw_share12"] = d.nhw12 / d.tot12.replace(0, np.nan)
    full = d.copy()
    d = d[(d["pop"] >= 500) & d.r12.notna() & d.r22.notna() & (d.r12 < 2000) & (d.r22 < 3500) & (d.pop12 > 0) & (d.km2 > 0)].copy()
    d["dt100"] = (d.t2015 - d.t2005) / 100
    d["trees05_km"] = d.t2005 / d.land_km2 / 1000
    d["lrent12"] = np.log(d.r12)
    d["ldens12"] = np.log(d.pop12 / d.land_km2)
    d["dlr"] = np.log(d.r22) - np.log(d.r12)
    d = d.reset_index(drop=True)
    print("  n =", len(d), " tracts excluded as top-coded:", int(((full.r12 >= 2000) | (full.r22 >= 3500)).sum()))

    print("\n== 3. Registered model refitted (slope per 100 trees, 95% interval)")
    b, lo, hi, se, m0 = ols(d)
    show("primary, clustered by NTA", b, lo, hi, f"se {se:.4f} clusters {d.nta2020.nunique()}")
    print(f"  z against no effect {b/se:.2f}; against 0.044 {(b-0.044)/se:.2f}; against 0.018 {(b-0.018)/se:.2f}; against 0.009 {(b-0.009)/se:.2f}")
    print(f"  D (0.044 against none) {(b/se)**2-((b-0.044)/se)**2:.1f}; D (0.018 against none) {(b/se)**2-((b-0.018)/se)**2:.1f}")
    print("  unsettled band for the estimate at this se: %.4f to %.4f" % (0.018 - 1.96 * se, 0.009 + 1.96 * se))
    for nm, mu in (("none", 0), ("0.018", 0.018), ("0.044", 0.044)):
        print(f"  if the true slope is {nm}: P(support) {1-stats.norm.cdf((0.009+1.96*se-mu)/se):.3f}  P(refute) {stats.norm.cdf((0.018-1.96*se-mu)/se):.3f}")
    show("no baseline rent", *ols(d, rhs=RHS.replace("lrent12 + ", ""))[:3])

    print("\n== 4. Is the tree change a real change? By borough, all tracts")
    f = full.copy()
    f["boro"] = f.geoid.str[2:5].map({"061": "1", "005": "2", "047": "3", "081": "4", "085": "5"})
    g = f.groupby("boro").agg(t2005=("t2005", "sum"), t2015=("t2015", "sum"), young3=("young3_2015", "sum"), young6=("young6_2015", "sum"),
                              y3_05=("young3_2005", "sum"), big05=("big_2005", "sum"), big15=("big_2015", "sum"))
    g["change_pct"] = 100 * (g.t2015 / g.t2005 - 1)
    g["big_change_pct"] = 100 * (g.big15 / g.big05 - 1)
    g.index = g.index.map(BORO)
    print(g.to_string(float_format=lambda v: f"{v:.1f}"))
    print("  total living trees in a tract: 2005", int(f.t2005.sum()), " 2015", int(f.t2015.sum()))
    d["gain"] = d.t2015 - d.t2005
    for cut in (3, 6):
        d[f"unexpl{cut}"] = (d.gain - d[f"young{cut}_2015"]).clip(lower=0)
    pos = d[d.gain > 0]
    print("  sample tracts with a net gain:", len(pos), "of", len(d), "; with a net loss:", int((d.gain < 0).sum()))
    print("  share of the summed net gains that exceeds the count of trees of 3 in or less in 2015: %.2f; of 6 in or less: %.2f"
          % (pos.unexpl3.sum() / pos.gain.sum(), pos.unexpl6.sum() / pos.gain.sum()))
    print("  tracts where the gain exceeds the trees of 6 in or less by 50 or more:", int((d.unexpl6 >= 50).sum()))
    bb = d.groupby("boro").apply(lambda q: pd.Series({"n": len(q), "mean_gain": q.gain.mean(), "sd_gain": q.gain.std(), "share_gaining": (q.gain > 0).mean(),
                                                     "mean_young6": q.young6_2015.mean(), "unexplained6_share": q.unexpl6.sum() / q.gain.clip(lower=0).sum(),
                                                     "corr_gain_young6": q.gain.corr(q.young6_2015), "big_change": q.big_2015.sum() / q.big_2005.sum() - 1}))
    bb.index = bb.index.map(BORO)
    print(bb.to_string(float_format=lambda v: f"{v:.2f}"))
    print("  correlation of net gain with trees of 3 in or less in 2015: %.2f; 6 in or less: %.2f; with 2005 count: %.2f"
          % (d.gain.corr(d.young3_2015), d.gain.corr(d.young6_2015), d.gain.corr(d.t2005)))
    xy = d[["cx", "cy"]].values
    print("  Moran's I (6 nearest tracts) of the tree change: %.3f (p %.3f)" % moran(d.dt100.values, xy))
    # change in trees of 12 in diameter or more: such trees cannot be planted in ten years
    d["dbig100"] = (d.big_2015 - d.big_2005) / 100
    d["dsmall100"] = d.dt100 - d.dbig100
    print("  sd of the change in trees of 12 in or more (hundreds): %.2f; of the change in smaller trees: %.2f; correlation %.2f"
          % (d.dbig100.std(), d.dsmall100.std(), d.dbig100.corr(d.dsmall100)))

    print("\n== 5. Exposure variants (slope per 100 trees)")
    d["y3"], d["y6"] = d.young3_2015 / 100, d.young6_2015 / 100
    show("trees of 3 in or less in 2015 (new plantings)", *ols(d, x="y3")[:3])
    show("trees of 6 in or less in 2015", *ols(d, x="y6")[:3])
    show("net change instrumented by trees of 3 in or less", *iv(d, "dt100", "y3")[:3])
    show("net change instrumented by trees of 6 in or less", *iv(d, "dt100", "y6")[:3])
    m2 = smf.ols(f"dlr ~ dsmall100 + dbig100 + {RHS}", d).fit(cov_type="cluster", cov_kwds={"groups": d.nta2020})
    for v in ("dsmall100", "dbig100"):
        show(f"joint model: {v}", m2.params[v], *m2.conf_int().loc[v])
    lo_, hi_ = d.dt100.quantile([0.01, 0.99])
    d["dt_w"] = d.dt100.clip(lo_, hi_)
    show("net change winsorised at 1% and 99%", *ols(d, x="dt_w")[:3])
    for cut in (2, 3, 5):
        q = d[d.dt100.abs() < cut]
        show(f"tracts with |change| under {cut*100} trees", *ols(q)[:3], f"n {len(q)}")
    ext = d[d.dt100.abs() >= 3]
    print("  tracts with |change| of 300 or more by borough:", ext.boro.map(BORO).value_counts().to_dict(),
          "; gains", int((ext.dt100 > 0).sum()), "losses", int((ext.dt100 < 0).sum()),
          "; median land area km2 %.2f against %.2f in the sample" % (ext.land_km2.median(), d.land_km2.median()))
    d["rank_dt"] = d.dt100.rank() / len(d)
    show("exposure as rank (0 to 1) of the tree change", *ols(d, x="rank_dt")[:3])
    show("tracts where gain does not exceed young trees by 50", *ols(d[d.unexpl6 < 50])[:3], f"n {int((d.unexpl6 < 50).sum())}")
    d["dt_km"] = (d.t2015 - d.t2005) / d.land_km2 / 1000
    show("change per km2 (thousands of trees per km2)", *ols(d, x="dt_km")[:3])
    print("  at the median tract area (%.3f km2) 100 trees are %.2f thousand per km2, so the per-area slope corresponds to %.4f per 100 trees there"
          % (d.land_km2.median(), 0.1 / d.land_km2.median(), ols(d, x="dt_km")[0] * 0.1 / d.land_km2.median()))
    show("change per km2, adding log land area", *ols(d, x="dt_km", rhs=RHS + " + np.log(land_km2)")[:3])
    show("net change in hundreds, adding log land area", *ols(d, rhs=RHS + " + np.log(land_km2)")[:3])
    print("  by borough (separate models without the borough term):")
    for bcode, nm in BORO.items():
        q = d[d.boro == bcode]
        show("   " + nm, *ols(q, rhs=RHS.replace(" + C(boro)", ""))[:3], f"n {len(q)}")
    for bcode, nm in BORO.items():
        show("   without " + nm, *ols(d[d.boro != bcode])[:3])

    print("\n== 6. Rent: crosswalk and margins of error")
    d["se22l"], d["se12l"] = d.m22 / 1.645 / d.r22, d.se12 / d.r12
    ev = (d.se22l ** 2 + d.se12l ** 2)
    print("  median standard error of log rent: 2008-12 %.3f, 2018-22 %.3f" % (d.se12l.median(), d.se22l.median()))
    print("  variance of the rent change %.4f; mean sampling variance %.4f (share %.2f); median share %.2f" % (
        d.dlr.var(), ev.mean(), ev.mean() / d.dlr.var(), ev.median() / d.dlr.var()))
    su2 = float((d.se12l ** 2).mean())
    print("  reliability of log rent 2008-12: %.2f (mean), %.2f (median error variance)" % (1 - su2 / d.lrent12.var(), 1 - (d.se12l ** 2).median() / d.lrent12.var()))
    print("  coefficient on log rent 2008-12 in the primary model: %.3f" % m0.params["lrent12"])
    for lab, s in (("mean error variance", su2), ("median error variance", float((d.se12l ** 2).median()))):
        b_e, g_e = eiv(d, s)
        rng = np.random.default_rng(7)
        ntas = d.nta2020.unique()
        idx = d.groupby("nta2020").indices
        bs = []
        for _ in range(400):
            q = d.iloc[np.concatenate([idx[n] for n in rng.choice(ntas, len(ntas))])]
            bs.append(eiv(q, s)[0])
        show(f"error-corrected baseline rent ({lab})", b_e, *np.percentile(bs, [2.5, 97.5]), f"baseline coef {g_e:.3f}")
    tau2 = max(d.dlr.var() - ev.mean(), 0.005)
    d["w"] = 1 / (tau2 + ev.fillna(ev.median()))
    mw = smf.wls(f"dlr ~ dt100 + {RHS}", d, weights=d.w).fit(cov_type="cluster", cov_kwds={"groups": d.nta2020})
    show("weighted by precision of the rent change", mw.params["dt100"], *mw.conf_int().loc["dt100"])
    q = d[ev < ev.median()]
    show("tracts with below-median sampling variance", *ols(q)[:3], f"n {len(q)}")
    print("  tracts whose 2020 boundary equals one 2010 tract: %d of %d" % (int(d.same.sum()), len(d)))
    show("unchanged tracts only", *ols(d[d.same])[:3], f"n {int(d.same.sum())}")
    import statsmodels.api as sm
    rl = smf.rlm(f"dlr ~ dt100 + {RHS}", d, M=sm.robust.norms.HuberT()).fit()
    show("Huber robust regression (no clustering)", rl.params["dt100"], *rl.conf_int().loc["dt100"])
    q = d[d.dlr.between(*d.dlr.quantile([0.01, 0.99]))]
    show("rent change trimmed at 1% and 99%", *ols(q)[:3], f"n {len(q)}")
    d["drent"] = d.r22 - d.r12
    show("outcome in dollars of monthly rent per 100 trees", *ols(d, y="drent")[:3])

    print("\n== 7. Spatial dependence and the standard error")
    print("  Moran's I (6 nearest tracts) of the primary residuals: %.3f (p %.3f)" % moran(m0.resid.values, xy))
    hc = smf.ols(f"dlr ~ dt100 + {RHS}", d).fit(cov_type="HC1")
    print("  se: HC1 %.4f; NTA clusters %.4f" % (hc.bse["dt100"], se))
    for cut in (1, 2, 5, 10):
        s = conley(m0, d, xy, cut)
        print("  Conley se, Bartlett kernel to %2d km: %.4f  interval %.4f to %.4f" % (cut, s, b - 1.96 * s, b + 1.96 * s))
    d["cd"] = d.nta2020.str[:4]
    bcd, lcd, hcd, scd, _ = ols(d, groups="cd")
    show("clustered by the first four characters of the NTA code", bcd, lcd, hcd, f"se {scd:.4f} clusters {d.cd.nunique()}")
    show("NTA fixed effects", *ols(d, rhs=RHS.replace("C(boro)", "C(nta2020)"))[:3])
    show("district (four-character) fixed effects", *ols(d, rhs=RHS.replace("C(boro)", "C(cd)"))[:3])
    a = d.groupby("nta2020").apply(lambda q: pd.Series({"dlr": np.average(q.dlr), "dt100": q.dt100.mean(), "trees05_km": q.trees05_km.mean(),
                                                       "lrent12": q.lrent12.mean(), "nhw_share12": q.nhw_share12.mean(), "ldens12": q.ldens12.mean(),
                                                       "boro": q.boro.iloc[0], "n": len(q)})).reset_index()
    a = a[a.n >= 3]
    ma = smf.wls(f"dlr ~ dt100 + {RHS}", a, weights=a.n).fit(cov_type="HC1")
    show("NTA means (3 or more tracts), mean change per tract", ma.params["dt100"], *ma.conf_int().loc["dt100"], f"n {len(a)}")

    print("\n== 8. Selection of planting and timing")
    d["dlogpop"] = np.log(d["pop"] / d.pop12)
    for v in ("lrent12", "nhw_share12", "poverty", "ldens12", "trees05_km", "dlogpop", "dlr"):
        print("  Spearman of the tree change with %-12s %.2f; of trees of 3 in or less with it %.2f" % (
            v, stats.spearmanr(d.dt100, d[v], nan_policy="omit")[0], stats.spearmanr(d.y3, d[v], nan_policy="omit")[0]))
    show("adding log population change", *ols(d, rhs=RHS + " + dlogpop")[:3])
    show("adding poverty 2018-22 and log population change", *ols(d[d.poverty.notna()], rhs=RHS + " + dlogpop + poverty")[:3])
    show("adding squared baseline rent and white share", *ols(d, rhs=RHS + " + I(lrent12**2) + I(nhw_share12**2)")[:3])
    show("borough by baseline rent interaction", *ols(d, rhs=RHS + " + C(boro):lrent12")[:3])
    print("  2000 census rent is not among the files on disk (data/raw/acs holds ACS 2008-12 and 2018-22 only).")

    print("\n== 9. Scale of the prediction")
    print("  mean living trees per sample tract 2005: %.0f; 2015: %.0f; median 2020 population %.0f" % (d.t2005.mean(), d.t2015.mean(), d["pop"].median()))
    print("  sd of the tree change in hundreds %.2f; mean %.2f; mean rent change %.3f log points" % (d.dt100.std(), d.dt100.mean(), d.dlr.mean()))
    print("  implied rent difference for one sd of tree change: %.4f log points; under the prediction: %.4f" % (b * d.dt100.std(), 0.044 * d.dt100.std()))
    for price in (150000, 200000, 300000, 400000):
        print("  Portland 131 dollars (53 to 210) per tree on a median price of %d: %.3f (%.3f to %.3f) per 100 trees" % (
            price, 13100 / price, 5300 / price, 21000 / price))


if __name__ == "__main__":
    main()
