"""Registered analysis for further-zonej-demand-growth. Follows the registration; no other specifications decide the verdict."""
import json, sys
import numpy as np, pandas as pd, statsmodels.api as sm
from pathlib import Path
from pandas.tseries.holiday import USFederalHolidayCalendar
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from concord import noaa
ROOT = Path(__file__).resolve().parents[2]
D = pd.read_csv(ROOT/"data/derived/further/zonej_daily.csv", parse_dates=["date"])
D = D[D.n >= 0.9*288]
EXCL = (pd.Timestamp("2020-03-15"), pd.Timestamp("2021-06-30"))
HOL = set(USFederalHolidayCalendar().holidays("2014-12-31", "2026-01-01"))
rng = np.random.default_rng(20261112)

def weather(station="central_park", base_c=65, base_h=65, shift_years=0):
    w, src = noaa.daily(station)
    w = w.loc["2011-01-01":"2025-12-31"]
    T = ((w.TMAX + w.TMIN)/2*9/5 + 32).reindex(pd.date_range("2011-01-01", "2025-12-31"))
    T = T.interpolate(limit=3)
    if shift_years:
        T = pd.Series(T.reindex(T.index - pd.DateOffset(years=shift_years)).ffill().values, index=T.index)
    df = pd.DataFrame({"HDD": (base_h - T).clip(lower=0), "CDD": (T - base_c).clip(lower=0)})
    df["CDD1"] = df.CDD.shift(1); df["CDD23"] = (df.CDD.shift(2) + df.CDD.shift(3))/2
    return df.loc["2015-01-01":], src

def design(df, wx, kind="energy", interact=False):
    X = pd.DataFrame(index=df.index)
    d = df.date
    X["t"] = ((d - pd.Timestamp("2015-01-01")).dt.days/365.25).values
    W = wx.reindex(d.values)
    for c in ("HDD","CDD","CDD1","CDD23"): X[c] = W[c].values
    X["HDD2"] = X.HDD**2; X["CDD2"] = X.CDD**2
    X["hol"] = d.isin(HOL).astype(float).values
    X = X.join(pd.get_dummies(d.dt.dayofweek, prefix="dow", drop_first=True).astype(float).set_axis(df.index))
    X = X.join(pd.get_dummies(d.dt.month, prefix="m", drop_first=True).astype(float).set_axis(df.index))
    if interact:
        for m in range(5, 10): X[f"cddxm{m}"] = X.CDD*(d.dt.month == m).values
    if kind == "peak": X = X.drop(columns=["HDD","HDD2"])
    return sm.add_constant(X)

def fit(df, y, X, maxlags=14):
    ok = X.notna().all(axis=1) & df[y].notna()
    m = sm.OLS(np.log(df.loc[ok, y]), X[ok]).fit(cov_type="HAC", cov_kwds={"maxlags": maxlags})
    return m

def pct(b): return 100*(np.exp(b) - 1)
def trend(m):
    b = m.params["t"]; lo, hi = m.conf_int().loc["t"]
    return dict(est=pct(b), lo=pct(lo), hi=pct(hi), n=int(m.nobs))

def prep(zone, excl=True, drop_years=None, years=None, summer=False):
    df = D[D.zone == zone].reset_index(drop=True)
    if excl: df = df[~df.date.between(*EXCL)]
    if drop_years: df = df[~df.date.dt.year.isin(drop_years)]
    if years: df = df[df.date.dt.year.between(*years)]
    if summer: df = df[df.date.dt.month.between(6, 9)]
    return df.reset_index(drop=True)

def run_energy(zone, wx, **kw):
    df = prep(zone, **{k: v for k, v in kw.items() if k in ("excl","drop_years","years")})
    X = design(df, wx, "energy", kw.get("interact", False))
    return fit(df, "energy_mwh", X), df, X

def run_peak(zone, wx, **kw):
    df = prep(zone, summer=True, **{k: v for k, v in kw.items() if k in ("excl","drop_years","years")})
    X = design(df, wx, "peak")
    return fit(df, "peak", X), df, X

wx, wsrc = weather("central_park")
res = {"weather_source": wsrc}
for z in ("N.Y.C.", "LONGIL"):
    mE, dfE, XE = run_energy(z, wx); mP, dfP, XP = run_peak(z, wx)
    res[z] = {"energy": trend(mE), "peak": trend(mP), "r2_energy": mE.rsquared, "r2_peak": mP.rsquared,
              "days_used_energy": int(mE.nobs), "days_used_peak": int(mP.nobs)}
    res[z]["_models"] = (mE, dfE, XE, mP, dfP, XP)

# annual weather-normalised energy: year indicators, climatology weather
def annual_norm(zone, wx):
    df = prep(zone); X = design(df, wx, "energy").drop(columns=["t"])
    yrs = pd.get_dummies(df.date.dt.year, prefix="y", drop_first=True).astype(float).set_axis(df.index)
    X = X.join(yrs); m = fit(df, "energy_mwh", X)
    cal = pd.DataFrame({"date": pd.date_range("2015-01-01", "2025-12-31")})
    clim = wx.loc["2015-01-01":"2025-12-31"].copy()
    doy = clim.index.dayofyear.where(~((clim.index.month == 2) & (clim.index.day == 29)), 59)
    out = {}
    clim["doy"] = doy
    mean_doy = clim.groupby("doy")[["HDD","CDD"]].mean()
    ext = pd.concat([mean_doy.iloc[-15:], mean_doy, mean_doy.iloc[:15]]).rolling(31, center=True).mean().iloc[15:-15]
    ext.index = mean_doy.index
    cl = pd.DataFrame(index=cal.date)
    dd = cal.date.dt.dayofyear.where(~((cal.date.dt.month == 2) & (cal.date.dt.day == 29)), 59).values
    cl["HDD"] = ext.loc[dd, "HDD"].values; cl["CDD"] = ext.loc[dd, "CDD"].values
    cl["CDD1"] = cl.CDD.shift(1).bfill(); cl["CDD23"] = (cl.CDD.shift(2) + cl.CDD.shift(3)).div(2).bfill()
    Xc = design(cal, cl, "energy").drop(columns=["t"])
    for y in range(2015, 2026):
        row = Xc.copy()
        for yy in range(2016, 2026): row[f"y_{yy}"] = float(y == yy)
        row = row[X.columns]
        mask = (cal.date.dt.year == y).values
        sm_ = np.exp(row[mask].values @ m.params.values)  # no smearing correction; levels are relative
        out[y] = sm_.sum()/1e6   # TWh
    return pd.Series(out)

def design_day_peak(m, df, wx, zone):
    jul = wx[(wx.index.month == 7) & (wx.index.dayofweek < 5)].loc["2015":"2025"].dropna()
    q = jul.quantile(0.9)
    x = pd.Series(0.0, index=m.params.index); x["const"] = 1
    for c in ("CDD","CDD1","CDD23"): x[c] = q[c]
    x["CDD2"] = q["CDD"]**2
    if "m_7" in x.index: x["m_7"] = 1
    out = {}
    for y in range(2015, 2026):
        v = x.copy(); v["t"] = (pd.Timestamp(f"{y}-07-15") - pd.Timestamp("2015-01-01")).days/365.25
        out[y] = float(np.exp(v.values @ m.params.values))
    return pd.Series(out), q

ann = {z: annual_norm(z, wx) for z in ("N.Y.C.", "LONGIL")}
dd = {}
for z in ("N.Y.C.", "LONGIL"):
    mP, dfP, XP = res[z]["_models"][3:]
    dd[z], q = design_day_peak(mP, dfP, wx, z)
def slope(s):
    X = sm.add_constant(np.array(s.index, float) - 2015); m = sm.OLS(np.log(s.values), X).fit()
    return pct(m.params[1])
for z in ann:
    res[z]["annual_norm_twh"] = {int(k): round(v, 3) for k, v in ann[z].items()}
    res[z]["annual_norm_slope_pct_yr_descriptive"] = slope(ann[z])
    res[z]["design_day_peak_mw"] = {int(k): round(v, 1) for k, v in dd[z].items()}
res["design_day_cdd"] = {k: float(v) for k, v in q.items()}

# Sensitivity checks (Zone J and K, energy and peak)
def tr_of(fun, z, wxx, **kw):
    m, _, _ = fun(z, wxx, **kw); return trend(m)
wx70, _ = weather("central_park", base_c=70, base_h=60)
wxlg, lgsrc = weather("laguardia"); res["laguardia_source"] = lgsrc
S = {"S1_include_all_with_indicator": None}
sens = {}
for z in ("N.Y.C.", "LONGIL"):
    s = {}
    # S1: all days with pandemic indicator
    df = prep(z, excl=False); X = design(df, wx, "energy"); X["pandemic"] = df.date.between(*EXCL).astype(float).values
    s["S1_energy"] = trend(fit(df, "energy_mwh", X))
    df = prep(z, excl=False, summer=True); X = design(df, wx, "peak"); X["pandemic"] = df.date.between(*EXCL).astype(float).values
    s["S1_peak"] = trend(fit(df, "peak", X))
    for nm, kw in (("S2_drop_2020_2021", dict(excl=False, drop_years=[2020, 2021])),
                   ("S3_2015_2019", dict(excl=False, years=(2015, 2019))),
                   ("S4_2022_2025", dict(excl=False, years=(2022, 2025)))):
        s[nm+"_energy"] = tr_of(run_energy, z, wx, **kw); s[nm+"_peak"] = tr_of(run_peak, z, wx, **kw)
    s["S5_base70_60_energy"] = tr_of(run_energy, z, wx70); s["S5_base70_60_peak"] = tr_of(run_peak, z, wx70)
    s["S6_laguardia_energy"] = tr_of(run_energy, z, wxlg); s["S6_laguardia_peak"] = tr_of(run_peak, z, wxlg)
    s["S7_month_x_cdd_energy"] = tr_of(run_energy, z, wx, interact=True)
    sens[z] = s
res["sensitivity"] = sens

# data-quality check: drop days beyond 3x / 0.3x of median
for z in ("N.Y.C.", "LONGIL"):
    df = prep(z); med = df.energy_mwh.median()
    bad = ((df.energy_mwh > 3*med) | (df.energy_mwh < 0.3*med)).sum()
    keep = df[(df.energy_mwh <= 3*med) & (df.energy_mwh >= 0.3*med)].reset_index(drop=True)
    X = design(keep, wx); res[z]["dq_flagged_days"] = int(bad); res[z]["dq_refit_energy"] = trend(fit(keep, "energy_mwh", X))

# S8 moving-block bootstrap (30-day blocks, 2000 draws), energy trend, joint for J and K
def boot_trend(zones, B=2000, L=30):
    dfs, Xs, ys = {}, {}, {}
    base = D[D.zone == "N.Y.C."].reset_index(drop=True); base = base[~base.date.between(*EXCL)].reset_index(drop=True)
    common = base.date
    for z in zones:
        df = prep(z); df = df[df.date.isin(common)].reset_index(drop=True)
        dfs[z] = df
    common = sorted(set.intersection(*[set(d.date) for d in dfs.values()]))
    for z in zones:
        df = dfs[z][dfs[z].date.isin(common)].reset_index(drop=True); X = design(df, wx)
        ok = X.notna().all(axis=1).values
        dfs[z] = df[ok].reset_index(drop=True); Xs[z] = X[ok].values; ys[z] = np.log(df.energy_mwh[ok].values)
    n = min(len(v) for v in ys.values())
    cols = list(design(dfs[zones[0]], wx).columns); ti = cols.index("t")
    out = {z: [] for z in zones}
    nb = int(np.ceil(n/L))
    for _ in range(B):
        starts = rng.integers(0, n - L, nb); idx = np.concatenate([np.arange(s, s+L) for s in starts])[:n]
        for z in zones:
            b = np.linalg.lstsq(Xs[z][idx], ys[z][idx], rcond=None)[0]; out[z].append(b[ti])
    return {z: np.array(v) for z, v in out.items()}
bt = boot_trend(["N.Y.C.", "LONGIL"])
q = lambda a: [float(np.percentile(pct(a), 2.5)), float(np.percentile(pct(a), 97.5))]
res["S8_block_bootstrap_energy"] = {"N.Y.C.": q(bt["N.Y.C."]), "LONGIL": q(bt["LONGIL"])}
diff = pct(bt["N.Y.C."]) - pct(bt["LONGIL"])
pt = res["N.Y.C."]["energy"]["est"] - res["LONGIL"]["energy"]["est"]
res["placebo_K_contrast_J_minus_K_energy"] = {"est": pt, "lo": float(np.percentile(diff, 2.5) + (pt - np.mean(diff))), "hi": float(np.percentile(diff, 97.5) + (pt - np.mean(diff)))}

# Placebo 2: weather shifted by 3 years
wxs, _ = weather("central_park", shift_years=3)
mE, dfE, XE = res["N.Y.C."]["_models"][:3]
wcols = ["HDD","CDD","CDD1","CDD23","HDD2","CDD2"]
def r2_weather(wxx):
    df = prep("N.Y.C."); X = design(df, wxx); full = fit(df, "energy_mwh", X)
    nw = X.drop(columns=wcols); red = sm.OLS(np.log(df.energy_mwh), nw).fit()
    return full.rsquared, red.rsquared
rt, rn = r2_weather(wx), None
r_true = r2_weather(wx); r_shift = r2_weather(wxs)
res["placebo_shifted_weather"] = {"true_full_r2": r_true[0], "true_noweather_r2": r_true[1], "shift_full_r2": r_shift[0], "shift_noweather_r2": r_shift[1],
    "attributable_true": r_true[0]-r_true[1], "attributable_shift": r_shift[0]-r_shift[1]}

# coefficient on weather, for reporting
mE = res["N.Y.C."]["_models"][0]
res["N.Y.C."]["weather_coefs"] = {k: float(mE.params[k]) for k in wcols if k in mE.params}
for z in ("N.Y.C.", "LONGIL"): res[z].pop("_models")
Path(ROOT/"data/derived/further/zonej_results.json").write_text(json.dumps(res, indent=1, default=float))
print(json.dumps({k: v for k, v in res.items() if k not in ("weather_source","laguardia_source")}, indent=1, default=float))
