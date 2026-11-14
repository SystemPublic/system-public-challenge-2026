"""Analysis for further-tidal-flooding-trend, as registered (claims/registered/further-tidal-flooding-trend.json)."""
import json, sys, warnings
from pathlib import Path
import numpy as np, pandas as pd
import statsmodels.api as sm
from scipy import stats
warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "data" / "derived" / "round2" / "tidal_trend"
TIDAL = ["11414", "11691", "11692", "11693", "11694", "11697", "11231", "11224"]
BROAD = sorted(set(TIDAL + ["10464", "11413", "11422", "10305", "10306", "10301", "10310", "10312", "10034"]))
KNOT = 0.35
NB_BOOT = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
NB_CHK = int(sys.argv[2]) if len(sys.argv) > 2 else 300
rng = np.random.default_rng(20261113)

T = json.load(open(D / "battery_daily_max_mhhw.json"))
tide = pd.Series(T["daily_max_m_mhhw"]); tide.index = pd.to_datetime(tide.index)
cp = pd.read_csv(D / "prcp_central_park.csv", index_col=0, parse_dates=True)["PRCP"]
jfk = pd.read_csv(D / "prcp_jfk.csv", index_col=0, parse_dates=True)["PRCP"]
days = pd.date_range("2010-01-01", "2025-12-31")
df = pd.DataFrame(index=days)
df["H"] = tide.reindex(days); df["cp"], df["jfk"] = cp.reindex(days), jfk.reindex(days)
def dry(th):
    ok = df[["cp", "jfk"]].notna().all(axis=1) & df[["cp", "jfk"]].shift(1).notna().all(axis=1)
    return ok & (df.cp < th) & (df.jfk < th) & (df.cp.shift(1) < th) & (df.jfk.shift(1) < th)
df["dry"], df["dry01"] = dry(1.0), dry(0.1)
df["rain10"] = df[["cp", "jfk"]].max(axis=1) >= 10
df["sandy"] = (df.index >= "2012-10-29") & (df.index <= "2012-11-30")
def xk(H, k=KNOT): return np.maximum(0, (H - k) / 0.1)
df["x"] = xk(df.H); df["xlin"] = (df.H - df.H.mean()) / 0.1
for k in (0.30, 0.40, 0.45): df[f"x{int(k*100)}"] = xk(df.H, k)
df["E563"] = (df.H >= 0.563).astype(float)
df["xs7"], df["xs100"] = df.x.shift(-7), df.x.shift(-100)
df["year"], df["month"], df["dow"] = df.index.year, df.index.month, df.index.dayofweek
df["blk"] = np.arange(len(df)) // 14
bands = pd.cut(df.H, [-9, 0.30, 0.35, 0.40, 0.45, 9], right=False, labels=False)
for b in range(1, 5): df[f"band{b}"] = (bands == b).astype(float)

C = json.load(open(D / "complaints_by_day_zip.json"))
RA = pd.DataFrame(C["C4desc_A"]); RA["d"] = pd.to_datetime(RA["d"]).dt.normalize(); RA["n"] = RA["n"].astype(int)
RA["zip"] = RA["zip"].fillna("").astype(str)
du, cu = RA.descriptor.fillna("").str.upper(), RA.complaint_type.fillna("").str.upper()
RA["C1"] = du.str.startswith("STREET FLOODING") | cu.str.contains("STREET FLOOD")
RA["C3"] = RA.C1 | du.str.startswith("CATCH BASIN CLOGGED")
RA["C4"] = RA.C3 | du.str.startswith("SEWER BACKUP")
def series(key, zips=None, exclude=None):
    if key.endswith("_B"):
        r = pd.DataFrame(C[key]); r["d"] = pd.to_datetime(r["d"]).dt.normalize(); r["n"] = r["n"].astype(int)
        r["zip"] = r["zip"].fillna("").astype(str)
    else:
        r = RA[RA[key[:2]]]
    if zips is not None: r = r[r.zip.isin(zips)]
    if exclude is not None: r = r[~r.zip.isin(exclude)]
    return r.groupby("d").n.sum().reindex(days).fillna(0)
for k in ("C3", "C1", "C4"):
    df[f"{k}_t"] = series(f"{k}_A", TIDAL); df[f"{k}_b"] = series(f"{k}_A", BROAD); df[f"{k}_p"] = series(f"{k}_A", exclude=BROAD)
# 2020-2025 for part 2b (C3 from erm2-nwe9)
b3t, b3p = series("C3_B", TIDAL), series("C3_B", exclude=BROAD)
df.loc[df.year >= 2020, "C3_t"] = b3t[df.year >= 2020]; df.loc[df.year >= 2020, "C3_p"] = b3p[df.year >= 2020]

def design(d, xs):
    X = pd.get_dummies(d[["year", "month", "dow"]].astype(str), drop_first=True).astype(float)
    for i, x in enumerate(xs): X.insert(i, x, d[x].values)
    X.insert(0, "const", 1.0)
    return X.loc[:, (X != 0).any(axis=0) | (X.columns == "const")]

def fit(d, y, xs, model="nb"):
    xs = [xs] if isinstance(xs, str) else xs
    X = design(d, xs); yy = d[y].values
    try:
        p = sm.GLM(yy, X, family=sm.families.Poisson()).fit()
        if model == "poisson": return p.params[xs[0]], p.bse[xs[0]]
        r = sm.NegativeBinomial(yy, X).fit(start_params=np.r_[p.params.values, 0.5], disp=0, maxiter=200, method="bfgs")
        return r.params[xs[0]], r.bse[xs[0]]
    except Exception:
        return np.nan, np.nan

def boot(sub, specs, nboot, model="nb"):
    groups = sub.groupby("blk").indices
    keys = np.array(list(groups.keys())); idx = {k: sub.index[v] for k, v in groups.items()}
    out = []
    for _ in range(nboot):
        ks = rng.choice(keys, len(keys))
        d = pd.concat([sub.loc[idx[k]] for k in ks])
        out.append([fit(d, y, x, model)[0] for (y, x) in specs.values()])
    return np.array(out)

def summ(b, point):
    b = b[~np.isnan(b)]
    return {"rr": float(np.exp(point)), "lo": float(np.exp(np.percentile(b, 2.5))), "hi": float(np.exp(np.percentile(b, 97.5))), "n_boot": int(len(b))}

res = {}
def run(name, sub, ycols, x, nboot, model="nb"):
    yt, yp = ycols
    bt = fit(sub, yt, x, model)[0]; bp = fit(sub, yp, x, model)[0]
    B = boot(sub, {"t": (yt, x), "p": (yp, x)}, nboot, model); ok = ~np.isnan(B).any(axis=1)
    r = {"tidal": summ(B[ok, 0], bt), "placebo": summ(B[ok, 1], bp), "ratio": summ(B[ok, 0] - B[ok, 1], bt - bp),
         "n_days": int(len(sub)), "complaints_tidal": int(sub[yt].sum()), "complaints_placebo": int(sub[yp].sum())}
    res[name] = r
    print(name, {k: tuple(round(r[k][q], 3) for q in ("rr", "lo", "hi")) for k in ("tidal", "placebo", "ratio")}, r["n_days"], r["complaints_tidal"], flush=True)
    json.dump(res, open(D / "results.json", "w"), indent=1, default=float)

held = df[(df.year <= 2019) & df.dry & df.H.notna() & ~df.sandy].copy()
n_hi = int((held.H >= KNOT).sum()); n_c = int(held.C3_t.sum())
res["_sample"] = {"dry_days": int(len(held)), "dry_days_H_ge_knot": n_hi, "dry_days_H_ge_563": int((held.H >= 0.563).sum()),
                  "c3_tidal": n_c, "c3_placebo": int(held.C3_p.sum()), "c1_tidal": int(held.C1_t.sum()), "c4_tidal": int(held.C4_t.sum()),
                  "min_data_rule_met": bool(n_hi >= 150 and n_c >= 1500)}
print(res["_sample"], flush=True)
if res["_sample"]["min_data_rule_met"]:
    run("primary", held, ("C3_t", "C3_p"), "x", NB_BOOT)
    run("placebo_shift7", held[held.xs7.notna()], ("C3_t", "C3_p"), "xs7", NB_BOOT)
    run("placebo_shift100", held[held.xs100.notna()], ("C3_t", "C3_p"), "xs100", NB_BOOT)
    for k in (30, 40, 45): run(f"check_knot_{k}", held, ("C3_t", "C3_p"), f"x{k}", NB_CHK)
    run("check_loglinear_all_days_per10cm", held, ("C3_t", "C3_p"), "xlin", NB_CHK)
    run("check_C1", held, ("C1_t", "C1_p"), "x", NB_CHK)
    run("check_C4", held, ("C4_t", "C4_p"), "x", NB_CHK)
    run("check_broad", held, ("C3_b", "C3_p"), "x", NB_CHK)
    run("check_sandy_kept", df[(df.year <= 2019) & df.dry & df.H.notna()].copy(), ("C3_t", "C3_p"), "x", NB_CHK)
    run("check_poisson", held, ("C3_t", "C3_p"), "x", NB_CHK, "poisson")
    run("check_dry_under_0.1mm", df[(df.year <= 2019) & df.dry01 & df.H.notna() & ~df.sandy].copy(), ("C3_t", "C3_p"), "x", NB_CHK)
    run("check_rainy_days", df[(df.year <= 2019) & df.rain10 & df.H.notna() & ~df.sandy].copy(), ("C3_t", "C3_p"), "x", NB_CHK)
    run("check_NOS_minor_indicator", held, ("C3_t", "C3_p"), "E563", NB_CHK)
    run("check_bands", held, ("C3_t", "C3_p"), ["band1", "band2", "band3", "band4"], 0) if False else None
    # bands: report coefficients for tidal and placebo (point estimates with model-based SE), no bootstrap
    for g, y in (("tidal", "C3_t"), ("placebo", "C3_p")):
        X = design(held, ["band1", "band2", "band3", "band4"]); p = sm.GLM(held[y].values, X, family=sm.families.Poisson()).fit()
        r = sm.NegativeBinomial(held[y].values, X).fit(start_params=np.r_[p.params.values, 0.5], disp=0, maxiter=300, method="bfgs")
        res[f"bands_{g}"] = {b: {"rr": float(np.exp(r.params[b])), "lo": float(np.exp(r.params[b] - 1.96 * r.bse[b])), "hi": float(np.exp(r.params[b] + 1.96 * r.bse[b])),
                                 "n_days": int(held[b].sum())} for b in ["band1", "band2", "band3", "band4"]}
    ly = {}
    for y in range(2010, 2020):
        sub = held[held.year != y]; ly[y] = float(np.exp(fit(sub, "C3_t", "x")[0]))
    res["leave_one_year_out_tidal_rr"] = ly
    # in-sample comparison 2020-2025 (not held out)
    ins = df[(df.year >= 2020) & df.dry & df.H.notna()].copy(); ins["C3_t"] = ins.C3_t; 
    run("comparison_2020_2025_not_held_out", ins, ("C3_t", "C3_p"), "x", NB_CHK)
    # descriptive means by band
    held["band"] = bands.reindex(held.index)
    res["means_by_band"] = {g: held.groupby("band")[c].mean().to_dict() for g, c in (("tidal", "C3_t"), ("placebo", "C3_p"))}
    res["days_by_band"] = held.groupby("band").size().to_dict()

# PART 2a
all_dry = df[df.dry & df.H.notna()]
N = all_dry[all_dry.H >= KNOT].groupby("year").size().reindex(range(2010, 2026)).fillna(0)
N_all = df[df.H >= KNOT].groupby("year").size().reindex(range(2010, 2026)).fillna(0)
yrs = np.arange(2010, 2026)
def ols(y):
    r = stats.linregress(yrs, y); t = stats.t.ppf(0.975, len(yrs) - 2)
    return {"slope": r.slope, "lo": r.slope - t * r.stderr, "hi": r.slope + t * r.stderr, "se": r.stderr}
res["part2a"] = {"N_by_year": N.astype(int).to_dict(), "ols": ols(N.values), "implied": 0.553, "implied_poisson_interval": [0.465, 0.642]}
# Poisson / quasi-Poisson
Xp = sm.add_constant(yrs - 2017.5); pf = sm.GLM(N.values, Xp, family=sm.families.Poisson()).fit(scale="X2")
res["part2a"]["quasi_poisson_log_slope"] = {"est": float(pf.params[1]), "lo": float(pf.conf_int()[1][0]), "hi": float(pf.conf_int()[1][1]),
                                            "per_year_days_at_mean": float(pf.params[1] * N.mean())}
# Theil-Sen with bootstrap over years
ts = stats.theilslopes(N.values, yrs); bs = []
for _ in range(2000):
    i = rng.integers(0, len(yrs), len(yrs))
    if len(set(yrs[i])) > 2: bs.append(stats.theilslopes(N.values[i], yrs[i])[0])
res["part2a"]["theil_sen"] = {"slope": float(ts[0]), "lo": float(np.percentile(bs, 2.5)), "hi": float(np.percentile(bs, 97.5))}
res["part2a"]["all_days_N_by_year"] = N_all.astype(int).to_dict(); res["part2a"]["all_days_ols"] = ols(N_all.values)
# detrended null: remove 2.95 mm/yr from H, recount
Hd = df.H - 0.00295 * (df.index.year + (df.index.dayofyear - 1) / 365.25 - 2017.5)
Nd = df[df.dry & df.H.notna()].assign(Hd=Hd).query("Hd >= @KNOT").groupby("year").size().reindex(range(2010, 2026)).fillna(0)
res["part2a"]["detrended_N_by_year"] = Nd.astype(int).to_dict(); res["part2a"]["detrended_ols"] = ols(Nd.values)
res["part2a"]["mean_annual_N"] = float(N.mean()); res["part2a"]["total_N"] = int(N.sum())
# observed trend in H itself (annual mean of daily max), mm/yr
ymean = df.groupby("year").H.mean().reindex(range(2010, 2026))
res["part2a"]["annual_mean_daily_max_slope_mm_per_yr"] = float(stats.linregress(yrs, ymean.values).slope * 1000)
print("2a", json.dumps(res["part2a"], default=float)[:1500], flush=True)

# PART 2b (descriptive)
d = df[df.dry & df.H.notna()].copy()
A = d.groupby("year").agg(t=("C3_t", "sum"), p=("C3_p", "sum"), n_dry=("dry", "sum")).reindex(range(2010, 2026))
A["ratio"] = A.t / A.p; A["N"] = N.values
rho = stats.spearmanr(A.N, A.ratio)
Xb = sm.add_constant(A.N.values); pb = sm.GLM(A.t.values, Xb, family=sm.families.Poisson(), offset=np.log(A.p.values)).fit(scale="X2")
res["part2b"] = {"table": A.reset_index().to_dict("records"), "spearman_rho": float(rho[0]), "spearman_p": float(rho[1]),
                 "log_rate_per_tide_day": float(pb.params[1]), "lo": float(pb.conf_int()[1][0]), "hi": float(pb.conf_int()[1][1])}
print("2b", res["part2b"]["spearman_rho"], res["part2b"]["spearman_p"], res["part2b"]["log_rate_per_tide_day"], flush=True)
json.dump(res, open(D / "results.json", "w"), indent=1, default=float)
df.to_csv(D / "daily_panel.csv")
