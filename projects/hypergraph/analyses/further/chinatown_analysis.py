"""Analysis for further-chinatown-shift. Follows claims/registered/further-chinatown-shift.json.
Run: ~/.venvs/nyc-concordance/bin/python -m analyses.further.chinatown_analysis
Writes data/derived/further/chinatown_results.json"""
import json, math
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "data/derived/further"
EXT = Path.home() / "opt/nyc-concordance/chinatown"
sets = json.load(open(D / "chinatown_sets.json"))
t10 = pd.read_csv(D / "tracts_2010.csv", dtype={"geoid": str}).set_index("geoid")
t20 = pd.read_csv(D / "tracts_2020.csv", dtype={"geoid": str}).set_index("geoid")
acs = pd.read_csv(D / "acs2022_tracts.csv", dtype={"geoid": str}).set_index("geoid")
rel = pd.read_csv(EXT / "tab20_tract20_tract10_natl.txt", sep="|", dtype=str, encoding="utf-8-sig",
                  usecols=["GEOID_TRACT_20", "GEOID_TRACT_10", "AREALAND_TRACT_20", "AREALAND_PART"])
rel = rel[rel.GEOID_TRACT_10.str[:5].isin(["36005", "36047", "36061", "36081", "36085"]) | rel.GEOID_TRACT_20.str[:5].isin(["36005", "36047", "36061", "36081", "36085"])].copy()
rel["a20"] = rel.AREALAND_TRACT_20.astype(float); rel["part"] = rel.AREALAND_PART.astype(float)
rel = rel[rel.a20 > 0]; rel["w"] = rel.part / rel.a20   # share of the 2020 tract lying in the 2010 tract
rng_seed = 20261112

# measures: (2010 series, 2020 decennial series, 2020 ACS series or None)
for d in (t10, t20):
    d["nh_ap"] = d.nh_asian + d.nh_nhpi
acs["nh_ap"] = acs.B03002_E006 + acs.B03002_E007
acs["nh_ap_moe"] = np.sqrt(acs.B03002_M006 ** 2 + acs.B03002_M007 ** 2)
acs["nh_a"] = acs.B03002_E006; acs["nh_a_moe"] = acs.B03002_M006
READ = {  # name: (col2010, col2020 decennial or 'acs', label)
 "D1": ("nh_ap", "acs", "NH Asian+NHPI alone; 2010 census, 2020 ACS 2018-22"),
 "D2": ("nh_ap", "nh_ap", "NH Asian+NHPI alone; 2010 and 2020 census"),
 "D3": ("nh_asian", "acs_a", "NH Asian alone; 2010 census, 2020 ACS"),
 "D4": ("nh_asian", "nh_asian", "NH Asian alone; both census"),
 "D5": ("asian_alone", "asian_alone", "Asian alone any origin; both census"),
}

def s20_m1(s10):
    g = rel[rel.GEOID_TRACT_10.isin(s10)].groupby("GEOID_TRACT_20").w.sum()
    return sorted(g[g >= 0.5].index)

def apportion(series20, s10):
    """M2: 2020 values allocated to 2010 parent tracts by land-area share; returns Series indexed by 2010 tract"""
    r = rel[rel.GEOID_TRACT_10.isin(s10)]
    v = series20.reindex(r.GEOID_TRACT_20).fillna(0).values
    return pd.Series(v * r.w.values, index=r.GEOID_TRACT_10.values).groupby(level=0).sum().reindex(s10).fillna(0)

def value20(name, s20, s10=None, mapping="M1"):
    c20 = READ[name][1]
    if c20 == "acs": ser, moe = acs.nh_ap, acs.nh_ap_moe
    elif c20 == "acs_a": ser, moe = acs.nh_a, acs.nh_a_moe
    else: ser, moe = t20[c20], None
    if mapping == "M1":
        v = ser.reindex(s20).sum(); m = math.sqrt((moe.reindex(s20) ** 2).sum()) if moe is not None else None
    else:
        v = apportion(ser, s10).sum(); m = None
        if moe is not None: m = math.sqrt(sum(apportion(moe ** 2, s10)))
    return float(v), m

TOL = dict(n10=(52613, .05), n20=(41024, .05), pct=(-22, 3))
def in_tol(n10, n20, pct):
    ok10 = abs(n10 / 52613 - 1) <= .05; ok20 = abs(n20 / 41024 - 1) <= .05; okp = abs(pct - (-22)) <= 3
    return ok10, ok20, okp

res = {}
# ---------------- Part A: reproduction grid
grid = []
for B in ("chinatown_B1", "chinatown_B2", "chinatown_B3"):
    s10 = sets[B]; s20 = s20_m1(s10)
    for rd, (c10, c20, lab) in READ.items():
        for mp in (("M1", "M2") if (B == "chinatown_B1" and rd == "D1") or True else ("M1",)):
            n10 = float(t10.loc[s10, c10].sum()); n20, moe = value20(rd, s20, s10, mp)
            pct = (n20 / n10 - 1) * 100
            ok = in_tol(n10, n20, pct)
            row = dict(boundary=B[-2:], reading=rd, mapping=mp, label=lab, n_tracts_2010=len(s10), n_tracts_2020=len(s20),
                       n2010=round(n10), n2020=round(n20), moe2020=round(moe) if moe else None, pct=round(pct, 2),
                       gap10=round(n10 - 52613), gap20=round(n20 - 41024), gap_pct=round(pct + 22, 2),
                       ok2010=bool(ok[0]), ok2020=bool(ok[1]), ok_pct=bool(ok[2]), reproduces=bool(all(ok)))
            if moe:
                lo, hi = n20 - moe, n20 + moe; row["pct_at_moe_ends"] = [round((lo / n10 - 1) * 100, 2), round((hi / n10 - 1) * 100, 2)]
            grid.append(row)
res["grid"] = grid
prim = [g for g in grid if g["boundary"] == "B1" and g["reading"] == "D1" and g["mapping"] == "M1"][0]
res["primary"] = prim
res["n_readings_reproduce"] = sum(g["reproduces"] for g in grid)
res["n_readings"] = len(grid)
res["readings_that_reproduce"] = [(g["boundary"], g["reading"], g["mapping"]) for g in grid if g["reproduces"]]
# diagnostics for B1: total and other groups vs AALDEF table (primary D1 mapping M1)
s10 = sets["chinatown_B1"]; s20 = s20_m1(s10)
diag = {"total_2010": int(t10.loc[s10, "total"].sum()), "total_2020_census": int(t20.loc[s20, "total"].sum()),
        "total_2020_acs": float(acs.loc[s20, "B03002_E001"].sum()),
        "nh_white_2010": int(t10.loc[s10, "nh_white"].sum()), "nh_white_2020_census": int(t20.loc[s20, "nh_white"].sum()), "nh_white_2020_acs": float(acs.loc[s20, "B03002_E003"].sum()),
        "nh_black_2010": int(t10.loc[s10, "nh_black"].sum()), "nh_black_2020_census": int(t20.loc[s20, "nh_black"].sum()), "nh_black_2020_acs": float(acs.loc[s20, "B03002_E004"].sum()),
        "hisp_2010": int(t10.loc[s10, "hisp"].sum()), "hisp_2020_census": int(t20.loc[s20, "hisp"].sum()), "hisp_2020_acs": float(acs.loc[s20, "B03002_E012"].sum())}
res["diag_B1"] = diag

# ---------------- bootstrap helpers
def boot(strata, n=5000, seed=rng_seed):
    """strata: dict name -> (a10 array, a20 array) per parent tract. returns dict of pct change and differences"""
    r = np.random.default_rng(seed)
    out = {k: [] for k in strata}
    for _ in range(n):
        for k, (a, b) in strata.items():
            i = r.integers(0, len(a), len(a)); out[k].append((b[i].sum() / a[i].sum() - 1) * 100 if a[i].sum() > 0 else np.nan)
    return {k: np.array(v) for k, v in out.items()}

def place(name, core, per, col10="asian_alone", col20="asian_alone", seed=rng_seed):
    out = {}
    allt = sorted(set(core) | set(per or []))
    def parts(s10):
        a = t10.loc[s10, col10].values.astype(float); b = apportion(t20[col20], s10).values
        return a, b
    sets_ = {"core": core, "periphery": per, "all": allt} if per is not None else {"all": allt}
    # M1 point estimates
    for k, s in sets_.items():
        s20 = s20_m1(s); n10 = float(t10.loc[s, col10].sum()); n20 = float(t20.loc[s20, col20].sum())
        out[k] = dict(n_tracts_2010=len(s), n_tracts_2020=len(s20), n2010=int(n10), n2020=int(n20), pct_M1=round((n20 / n10 - 1) * 100, 2))
        a, b = parts(s); out[k]["n2020_M2"] = round(float(b.sum()), 1); out[k]["pct_M2"] = round((b.sum() / a.sum() - 1) * 100, 2)
    r = np.random.default_rng(seed); N = 5000
    P = {k: parts(s) for k, s in sets_.items()}
    bs = {k: [] for k in sets_}; diff = []
    for _ in range(N):
        v = {}
        for k, (a, b) in P.items():
            i = r.integers(0, len(a), len(a)); v[k] = (b[i].sum() / a[i].sum() - 1) * 100
            bs[k].append(v[k])
        if per is not None: diff.append(v["core"] - v["periphery"])
    for k in sets_:
        out[k]["boot95"] = [round(float(np.percentile(bs[k], 2.5)), 2), round(float(np.percentile(bs[k], 97.5)), 2)]
    if per is not None:
        out["diff_M1"] = round(out["core"]["pct_M1"] - out["periphery"]["pct_M1"], 2)
        out["diff_M2"] = round(out["core"]["pct_M2"] - out["periphery"]["pct_M2"], 2)
        out["diff_boot95"] = [round(float(np.percentile(diff, 2.5)), 2), round(float(np.percentile(diff, 97.5)), 2)]
    return out

sp_core, sp_per = sets["sunset_park_core"], sets["sunset_park_periphery"]
fl_core, fl_per = sets["flushing_core"], sets["flushing_periphery"]
res["sunset_asian"] = place("sp", sp_core, sp_per)
res["flushing_asian"] = place("fl", fl_core, fl_per)
res["chinatown_B1_asian_alone"] = place("ct", sets["chinatown_B1"], None)
res["chinatown_B1_nhap_census"] = place("ct", sets["chinatown_B1"], None, "nh_ap", "nh_ap")
# placebo (a)
res["placebo_sunset_hispanic"] = place("sp", sp_core, sp_per, "hisp", "hisp")
res["placebo_sunset_total"] = place("sp", sp_core, sp_per, "total", "total")
res["flushing_hispanic"] = place("fl", fl_core, fl_per, "hisp", "hisp")
# Manhattan-wide Asian change (comparison) with M1-free tract totals
man10 = t10[t10.index.str.startswith("36061")]; man20 = t20[t20.index.str.startswith("36061")]
res["manhattan_asian_alone"] = dict(n2010=int(man10.asian_alone.sum()), n2020=int(man20.asian_alone.sum()), pct=round((man20.asian_alone.sum() / man10.asian_alone.sum() - 1) * 100, 2))
res["nyc_asian_alone"] = dict(n2010=int(t10.asian_alone.sum()), n2020=int(t20.asian_alone.sum()), pct=round((t20.asian_alone.sum() / t10.asian_alone.sum() - 1) * 100, 2))

# placebo (b): random sets of 23 Manhattan tracts south of 96th St (lat < 40.7956)
def gaz(fn):
    g = {}
    with open(EXT / fn, encoding="utf-8-sig") as f:
        h = [x.strip() for x in f.readline().split("\t")]
        for l in f:
            r = dict(zip(h, [x.strip() for x in l.split("\t")]))
            if r["GEOID"][:5] in ("36061", "36047", "36081"): g[r["GEOID"]] = (float(r["INTPTLAT"]), float(r["INTPTLONG"]))
    return g
g10, g20 = gaz("Gaz_tracts_national.txt"), gaz("2020_Gaz_tracts_national.txt")
south = [g for g in t10.index if g.startswith("36061") and g in g10 and g10[g][0] < 40.7956 and t10.loc[g, "total"] > 0]
A10 = t10.loc[south, "asian_alone"].values.astype(float); A20 = apportion(t20.asian_alone, south).values
r = np.random.default_rng(rng_seed); draws = []
for _ in range(2000):
    i = r.choice(len(south), 23, replace=False)
    if A10[i].sum() > 0: draws.append((A20[i].sum() / A10[i].sum() - 1) * 100)
draws = np.array(draws)
obs = res["chinatown_B1_asian_alone"]["all"]["pct_M2"]
res["placebo_random23"] = dict(n_tracts_pool=len(south), mean=round(float(draws.mean()), 2), p05=round(float(np.percentile(draws, 5)), 2), p95=round(float(np.percentile(draws, 95)), 2),
                               observed_B1_pct_M2=obs, share_of_draws_at_or_below_observed=round(float((draws <= obs).mean()), 4))

# ---------------- sensitivity: noise and undercount on primary set (D2 census, B1, M1) and Sunset
rn = np.random.default_rng(rng_seed)
def noisy_pct(s10, sd, col="nh_ap", reps=2000):
    s20 = s20_m1(s10); n10 = t10.loc[s10, col].sum(); v = t20.loc[s20, col].values.astype(float)
    return [(np.maximum(v + rn.normal(0, sd, len(v)), 0).sum() / n10 - 1) * 100 for _ in range(reps)]
sens = {}
for sd in (5, 20):
    x = noisy_pct(sets["chinatown_B1"], sd); sens[f"noise_sd{sd}_B1_D2"] = [round(float(np.percentile(x, 2.5)), 2), round(float(np.percentile(x, 97.5)), 2)]
    # difference in pct change core-periphery
    def dn(core, per):
        c20, p20 = s20_m1(core), s20_m1(per); c10, p10 = t10.loc[core, "asian_alone"].sum(), t10.loc[per, "asian_alone"].sum()
        cv, pv = t20.loc[c20, "asian_alone"].values.astype(float), t20.loc[p20, "asian_alone"].values.astype(float)
        return [((np.maximum(cv + rn.normal(0, sd, len(cv)), 0).sum() / c10 - 1) - (np.maximum(pv + rn.normal(0, sd, len(pv)), 0).sum() / p10 - 1)) * 100 for _ in range(2000)]
    x = dn(sp_core, sp_per); sens[f"noise_sd{sd}_sunset_diff"] = [round(float(np.percentile(x, 2.5)), 2), round(float(np.percentile(x, 97.5)), 2)]
us = {}
for up in (0, .03, .05):
    s10 = sets["chinatown_B1"]; s20 = s20_m1(s10)
    us[f"B1_D2_+{int(up*100)}%"] = round((t20.loc[s20, "nh_ap"].sum() * (1 + up) / t10.loc[s10, "nh_ap"].sum() - 1) * 100, 2)
    c20, p20 = s20_m1(sp_core), s20_m1(sp_per)
    us[f"sunset_diff_+{int(up*100)}%"] = round(((t20.loc[c20, "asian_alone"].sum() * (1 + up) / t10.loc[sp_core, "asian_alone"].sum()) - (t20.loc[p20, "asian_alone"].sum() * (1 + up) / t10.loc[sp_per, "asian_alone"].sum())) * 100, 2)
sens["undercount_scenarios_pct"] = us
res["sensitivity"] = sens
# required Asian undercount to bring B1 D2 change to -19%
s10 = sets["chinatown_B1"]; s20 = s20_m1(s10)
need = (0.81 * t10.loc[s10, "nh_ap"].sum() / t20.loc[s20, "nh_ap"].sum() - 1) * 100
res["undercount_needed_pct_for_minus19_B1_D2"] = round(float(need), 2)

# ---------------- centroids and northern edge
def centroid(tracts, w, g):
    lat = np.array([g[t][0] for t in tracts]); lon = np.array([g[t][1] for t in tracts]); w = np.array(w, float)
    return float((lat * w).sum() / w.sum()), float((lon * w).sum() / w.sum())
def hav(a, b):
    R = 6371000; p = math.pi / 180
    x = math.sin((b[0] - a[0]) * p / 2) ** 2 + math.cos(a[0] * p) * math.cos(b[0] * p) * math.sin((b[1] - a[1]) * p / 2) ** 2
    return 2 * R * math.asin(math.sqrt(x))
LAT14 = 40.7365
cen = {}
def manh_south(t, g):  return [x for x in t.index if x.startswith("36061") and x in g and g[x][0] < LAT14]
for nm, t, g in (("2010", t10, g10), ("2020", t20, g20)):
    ts = manh_south(t, g); cen[nm] = dict(centroid=centroid(ts, t.loc[ts, "asian_alone"], g), n_tracts=len(ts), asian=int(t.loc[ts, "asian_alone"].sum()))
    maj = [x for x in ts if t.loc[x, "total"] > 0 and t.loc[x, "asian_alone"] / t.loc[x, "total"] >= 0.5]
    cen[nm]["majority_asian_tracts"] = len(maj); cen[nm]["majority_asian_pop"] = int(t.loc[maj, "asian_alone"].sum()) if maj else 0
    if maj:
        ix = max(maj, key=lambda x: g[x][0]); cen[nm]["northern_edge_lat"] = g[ix][0]; cen[nm]["northern_edge_tract"] = ix
        ix = min(maj, key=lambda x: g[x][0]); cen[nm]["southern_edge_lat"] = g[ix][0]
        # 5 northernmost majority tracts' Asian-weighted lat for robustness
cen["shift_m"] = round(hav(cen["2010"]["centroid"], cen["2020"]["centroid"]), 1)
cen["shift_dlat_m"] = round((cen["2020"]["centroid"][0] - cen["2010"]["centroid"][0]) * 111195, 1)
cen["shift_dlon_m"] = round((cen["2020"]["centroid"][1] - cen["2010"]["centroid"][1]) * 111195 * math.cos(math.radians(40.72)), 1)
if "northern_edge_lat" in cen["2010"] and "northern_edge_lat" in cen["2020"]:
    cen["northern_edge_shift_m"] = round((cen["2020"]["northern_edge_lat"] - cen["2010"]["northern_edge_lat"]) * 111195, 1)
res["centroid_manhattan_south_14th"] = cen
cc = {}
for nm, allk, g in (("sunset_all", sets["sunset_park_all"], None), ("flushing_all", sets["flushing_all"], None)):
    s10 = allk; s20 = s20_m1(s10)
    c0 = centroid(s10, t10.loc[s10, "asian_alone"], g10); c1 = centroid(s20, t20.loc[s20, "asian_alone"], g20)
    cc[nm] = dict(c2010=c0, c2020=c1, shift_m=round(hav(c0, c1), 1), dlat_m=round((c1[0] - c0[0]) * 111195, 1), dlon_m=round((c1[1] - c0[1]) * 111195 * math.cos(math.radians(c0[0])), 1))
res["centroids_other"] = cc
res["fetch_meta"] = json.load(open(D / "data_sources.json"))
json.dump(res, open(D / "chinatown_results.json", "w"), indent=1, default=float)
print(json.dumps({k: res[k] for k in ("primary", "n_readings_reproduce", "n_readings", "readings_that_reproduce", "diag_B1")}, indent=1))
