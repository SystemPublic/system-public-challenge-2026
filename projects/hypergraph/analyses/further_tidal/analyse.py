"""Analysis for further-tidal-flooding-311, as registered (claims/registered/further-tidal-flooding-311.json)."""
import json, sys, warnings
from pathlib import Path
import numpy as np, pandas as pd
import statsmodels.api as sm
warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "data" / "derived" / "further_tidal"
TIDAL = ["11414", "11691", "11692", "11693", "11694", "11697", "11231", "11224"]
BROAD = sorted(set(TIDAL + ["10464", "11413", "11422", "10305", "10306", "10301", "10310", "10312", "10034"]))
THR = 2.104
NB_BOOT = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
NB_BOOT_CHK = 300
rng = np.random.default_rng(20261112)

tide = pd.Series(json.load(open(D / "battery_daily_max.json"))["daily_max_m_mllw"]); tide.index = pd.to_datetime(tide.index)
cp = pd.read_csv(D / "prcp_central_park.csv", index_col=0, parse_dates=True)["PRCP"]
jfk = pd.read_csv(D / "prcp_jfk.csv", index_col=0, parse_dates=True)["PRCP"]
days = pd.date_range("2020-01-01", "2026-10-31")
df = pd.DataFrame(index=days)
df["H"] = tide.reindex(days)
df["cp"], df["jfk"] = cp.reindex(days), jfk.reindex(days)
for lag in (0, 1):
    pass
def rainfree(th):
    ok = df[["cp", "jfk"]].notna().all(axis=1) & df[["cp", "jfk"]].shift(1).notna().all(axis=1)
    return ok & (df.cp < th) & (df.jfk < th) & (df.cp.shift(1) < th) & (df.jfk.shift(1) < th)
df["rf1"], df["rf01"] = rainfree(1.0), rainfree(0.1)
df["rain10"] = (df[["cp", "jfk"]].max(axis=1) >= 10)
df["E1"] = (df.H >= THR).astype(float); df.loc[df.H.isna(), "E1"] = np.nan
df["E2"] = df.H * 10 - THR * 10 # in decimetres? scaled: units of 10 cm relative to threshold
df["E2"] = (df.H - THR) / 0.1
df["E1lag"] = df.E1.shift(1)
for s in (7, 100):
    df[f"E1s{s}"] = df.E1.shift(-s)
df["year"], df["month"], df["dow"] = df.index.year, df.index.month, df.index.dayofweek
df["blk"] = (np.arange(len(df)) // 14)

C = json.load(open(D / "complaints_by_day_zip.json"))
def series(key, zips=None, exclude=None):
    r = pd.DataFrame(C[key]["rows"]); r["d"] = pd.to_datetime(r["d"]).dt.normalize(); r["n"] = r["n"].astype(int)
    r["zip"] = r["zip"].fillna("").astype(str)
    if zips is not None: r = r[r.zip.isin(zips)]
    if exclude is not None: r = r[~r.zip.isin(exclude)]
    return r.groupby("d").n.sum().reindex(days).fillna(0)
for k in ("C1", "C2"):
    df[f"{k}_t"] = series(k, TIDAL); df[f"{k}_b"] = series(k, BROAD); df[f"{k}_p"] = series(k, exclude=BROAD)
    df[f"{k}_p"] = series(k, exclude=BROAD)

def design(d, x):
    X = pd.get_dummies(d[["year", "month", "dow"]].astype(str), drop_first=True).astype(float)
    X.insert(0, x, d[x].values); X.insert(0, "const", 1.0)
    X = X.loc[:, (X != 0).any(axis=0) | (X.columns == "const")]
    return X

def fit(d, y, x, model="nb"):
    X = design(d, x); yy = d[y].values
    try:
        if model == "poisson":
            r = sm.GLM(yy, X, family=sm.families.Poisson()).fit()
            return r.params[x], r.bse[x]
        p = sm.GLM(yy, X, family=sm.families.Poisson()).fit()
        r = sm.NegativeBinomial(yy, X).fit(start_params=np.r_[p.params.values, 0.5], disp=0, maxiter=300, method="bfgs")
        return r.params[x], r.bse[x]
    except Exception:
        return np.nan, np.nan

def boot(sub, specs, nboot, model="nb"):
    """specs: dict name -> (y, x). Block bootstrap over 14-day calendar blocks; returns array (nboot, len(specs))."""
    blocks = sub.groupby("blk").indices
    keys = np.array(list(blocks.keys())); idx = {k: sub.index[v] for k, v in blocks.items()}
    out = []
    for _ in range(nboot):
        ks = rng.choice(keys, len(keys))
        d = sub.loc[np.concatenate([idx[k] for k in ks])] if False else pd.concat([sub.loc[idx[k]] for k in ks])
        out.append([fit(d, y, x, model)[0] for (y, x) in specs.values()])
    return np.array(out)

def summ(b, point):
    b = b[~np.isnan(b)]
    return {"rr": float(np.exp(point)), "lo": float(np.exp(np.percentile(b, 2.5))), "hi": float(np.exp(np.percentile(b, 97.5))), "n_boot": int(len(b))}

res = {}
def run(name, sub, ycols, x, nboot, model="nb"):
    """ycols: (tidal_y, placebo_y). Reports tidal RR, placebo RR and the ratio."""
    yt, yp = ycols
    bt = fit(sub, yt, x, model)[0]; bp = fit(sub, yp, x, model)[0]
    B = boot(sub, {"t": (yt, x), "p": (yp, x)}, nboot, model)
    ok = ~np.isnan(B).any(axis=1)
    res[name] = {"tidal": summ(B[ok, 0], bt), "placebo": summ(B[ok, 1], bp), "ratio": summ(B[ok, 0] - B[ok, 1], bt - bp),
                 "n_days": int(len(sub)), "n_flood_days": int(np.nansum(sub[x])) if x.startswith("E1") else None,
                 "complaints_tidal": int(sub[yt].sum()), "complaints_placebo": int(sub[yp].sum())}
    r = res[name]; print(name, {k: (round(v["rr"], 3), round(v["lo"], 3), round(v["hi"], 3)) for k, v in r.items() if isinstance(v, dict) and "rr" in v}, r["n_days"], r["n_flood_days"], r["complaints_tidal"], flush=True)

rf = df[df.rf1 & df.E1.notna()].copy()
n_flood, n_c1 = int(rf.E1.sum()), int(rf.C1_t.sum())
print("rain-free days", len(rf), "flood days", n_flood, "C1 tidal complaints", n_c1, "C2 tidal", int(rf.C2_t.sum()))
res["_sample"] = {"rain_free_days": int(len(rf)), "rain_free_flood_days": n_flood, "c1_tidal": n_c1, "c2_tidal": int(rf.C2_t.sum()),
                  "c1_placebo": int(rf.C1_p.sum()), "all_days": int(len(df)), "flood_days_all": int(df.E1.sum())}
primary = "C1" if n_c1 >= 100 else "C2"
res["_sample"]["primary_complaint_set"] = primary
res["_sample"]["min_data_rule_met"] = bool(n_flood >= 30 and rf[f"{primary}_t"].sum() >= 100)
if not res["_sample"]["min_data_rule_met"]:
    # Registered rule: the verdict is no_test. The estimates below are still computed and reported, labelled as not decisive.
    json.dump(res, open(D / "results.json", "w"), indent=1); print("MIN DATA RULE NOT MET: estimates below do not decide the verdict")
P = primary
yt, yp = f"{P}_t", f"{P}_p"
run("primary_E1", rf, (yt, yp), "E1", NB_BOOT)
run("placebo_shift7", rf[rf.E1s7.notna()], (yt, yp), "E1s7", NB_BOOT)
run("placebo_shift100", rf[rf.E1s100.notna()], (yt, yp), "E1s100", NB_BOOT)
n = NB_BOOT_CHK
run("check_E2_continuous_per10cm", rf, (yt, yp), "E2", n)
run("check_E1_lag1", rf[rf.E1lag.notna()], (yt, yp), "E1lag", n)
other = "C2" if P == "C1" else "C1"
run("check_other_complaint_set_" + other, rf, (f"{other}_t", f"{other}_p"), "E1", n)
run("check_broad_zip_set", rf, (f"{P}_b", f"{P}_p"), "E1", n)
rf01 = df[df.rf01 & df.E1.notna()].copy()
run("check_rain_under_0.1mm", rf01, (yt, yp), "E1", n)
run("check_poisson", rf, (yt, yp), "E1", n, "poisson")
for y in sorted(rf.year.unique()):
    sub = rf[rf.year != y]
    bt = fit(sub, yt, "E1")[0]; res[f"leave_out_{y}"] = {"tidal_rr": float(np.exp(bt)), "n_flood_days": int(sub.E1.sum())}
rain = df[df.rain10 & df.E1.notna() & df.cp.notna()].copy()
run("check_rainy_days_E1", rain, (yt, yp), "E1", n)
# reference: rain slope (all days with data): indicator of rain>=10 mm today
al = df[df.cp.notna() & df.jfk.notna() & df.E1.notna()].copy(); al["R10"] = al.rain10.astype(float)
run("reference_rain10mm_all_days", al, (yt, yp), "R10", n)
# descriptive: mean daily complaints by E1 on rain-free days
res["_means"] = {g: {str(int(e)): float(rf.loc[rf.E1 == e, c].mean()) for e in (0, 1)} for g, c in (("tidal", yt), ("placebo", yp))}
# tide quintiles
rf["Hq"] = pd.qcut(rf.H, 5, labels=False, duplicates="drop")
res["_quintile_means"] = {g: rf.groupby("Hq")[c].mean().tolist() for g, c in (("tidal", yt), ("placebo", yp))}
res["_quintile_H"] = rf.groupby("Hq").H.mean().tolist()
res["_sample"]["by_year_flood_days_all"] = df.groupby("year").E1.sum().to_dict()
res["_sample"]["by_year_flood_days_rainfree"] = rf.groupby("year").E1.sum().to_dict()
json.dump(res, open(D / "results.json", "w"), indent=1, default=float)
df.to_csv(D / "daily_panel.csv")

# FloodNet secondary
try:
    F = json.load(open(D / "floodnet.json"))
    sens = pd.DataFrame(F["sensors"]); ev = pd.DataFrame(F["events"])
    sens["start"] = pd.to_datetime(sens.date_installed).dt.normalize()
    sens["end"] = pd.to_datetime(sens.get("date_removed")).dt.normalize().fillna(pd.Timestamp("2026-10-31"))
    ev["day"] = pd.to_datetime(ev.flood_start_time, utc=True).dt.tz_convert("America/New_York").dt.tz_localize(None).dt.normalize()
    ev = ev.merge(sens[["sensor_id", "tidally_influenced"]], on="sensor_id", how="left")
    out = {}
    for g in ("Yes", "No"):
        s = sens[sens.tidally_influenced == g]
        act = pd.Series(0, index=days)
        for a, b in zip(s.start, s.end):
            act.loc[max(a, days[0]):min(b, days[-1])] += 1
        e = ev[ev.tidally_influenced == g].groupby("day").size().reindex(days).fillna(0)
        for lab, m in (("E1=1", rf.E1 == 1), ("E1=0", rf.E1 == 0)):
            idx = rf.index[m]
            out[f"{g}|{lab}"] = {"events": int(e.loc[idx].sum()), "sensor_days": int(act.loc[idx].sum()), "days": int((act.loc[idx] > 0).sum())}
    def rr(g):
        a, b = out[f"{g}|E1=1"], out[f"{g}|E1=0"]
        if min(a["events"], b["events"]) == 0 or a["sensor_days"] == 0: return None
        est = (a["events"] / a["sensor_days"]) / (b["events"] / b["sensor_days"]); se = np.sqrt(1 / a["events"] + 1 / b["events"])
        return {"rr": est, "lo": est * np.exp(-1.96 * se), "hi": est * np.exp(1.96 * se)}
    out["rr_tidal"], out["rr_nontidal"] = rr("Yes"), rr("No")
    out["n_sensors"] = sens.tidally_influenced.value_counts().to_dict(); out["n_events"] = int(len(ev))
    res["floodnet"] = out; json.dump(res, open(D / "results.json", "w"), indent=1, default=float); print("FloodNet", out)
except Exception as ex:
    print("FloodNet failed", ex)
