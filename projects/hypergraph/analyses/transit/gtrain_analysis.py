"""transit-gtrain-substitution: app pickups in G-only zones during the summer 2024 G shutdown.

Follows claims/registered/transit-gtrain-substitution.json. Inputs come from gtrain_fetch.py.
Writes data/derived/transit/gtrain_results.json and gtrain_panel.csv.
"""
from __future__ import annotations

import json

import geopandas as gpd
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from analyses.commuting.common import fetch
from analyses.mobility.common import nys
from analyses.transit.gtrain_common import (AIRPORTS, DER, DROP_DAYS, G_DEPENDENT, G_ONLY, G_SHARED, PHASES,
                                            TREATED, WINDOW)

ZONES = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zones.zip"
SEG = ["G22", "G24", "G26", "G28", "G29", "G30", "G31", "G32", "G33", "G34", "G35", "G36"]  # Court Sq to Fulton St
SHIFT = pd.Timedelta(days=364)


def zone_sets():
    tz = gpd.read_file("zip://" + str(fetch(ZONES, "taxi_zones.zip")) + "!taxi_zones/taxi_zones.shp").to_crs(2263)
    tz["LocationID"] = tz["LocationID"].astype(int)
    tz = tz.dissolve(by="LocationID", aggfunc="first").reset_index()
    rows, _ = nys("39hk-dx4f", select="gtfs_stop_id, complex_id, station_id, line, stop_name, borough, daytime_routes, gtfs_latitude, gtfs_longitude", limit=5000)
    st = pd.DataFrame(rows)
    st = gpd.GeoDataFrame(st, geometry=gpd.points_from_xy(st.gtfs_longitude.astype(float), st.gtfs_latitude.astype(float)), crs=4326).to_crs(2263)
    seg = st[st.gtfs_stop_id.isin(SEG)]
    tz["d_km"] = tz.geometry.centroid.apply(lambda p: seg.distance(p).min()) * 0.3048 / 1000
    notg = tz.borough.isin(["Brooklyn", "Queens"]) & ~tz.LocationID.isin(list(TREATED) + list(G_SHARED) + list(AIRPORTS))
    near = sorted(tz[notg & (tz.d_km <= 5)].LocationID)
    allbq = sorted(tz[notg].LocationID)
    tr = tz[tz.LocationID.isin(TREATED)].geometry.union_all()
    adj = sorted(int(i) for i, g in zip(tz.LocationID, tz.geometry) if i in near and g.intersects(tr))
    return near, allbq, adj, dict(zip(tz.LocationID, tz.zone))


def schedule(z, dates, year=2024):
    """closed_here and cut_elsewhere for zone z on the given (2024-aligned) dates."""
    closed = np.zeros(len(dates), bool)
    for ph in TREATED.get(z, ()):
        a, b = PHASES[ph]
        closed |= (dates >= a) & (dates <= b)
    inside = (dates >= PHASES[1][0]) & (dates <= PHASES[3][1])
    cut = inside & ~closed if z in TREATED else np.zeros(len(dates), bool)
    return closed.astype(float), cut.astype(float)


def panel(trips, zones, year):
    t = trips.copy()
    t["d"] = pd.to_datetime(t["d"])
    if year == 2023:
        t = t[t.d.dt.year == 2023]
        t["d"] = t["d"] + SHIFT          # align days of the week with 2024
    else:
        t = t[t.d.dt.year == 2024]
    t = t[(t.d >= WINDOW[0]) & (t.d <= WINDOW[1]) & ~t.d.isin(pd.to_datetime(list(DROP_DAYS))) & t.zone.isin(zones)]
    w = t.pivot_table(index=["zone", "d"], columns="lic", values="n", aggfunc="sum").fillna(0)
    w["n"] = w.sum(axis=1)
    w = w.rename(columns={"HV0003": "uber", "HV0005": "lyft"}).reset_index()
    full = pd.MultiIndex.from_product([sorted(zones), sorted(w.d.unique())], names=["zone", "d"])
    w = w.set_index(["zone", "d"]).reindex(full, fill_value=0).reset_index()
    w["closed_here"], w["cut_elsewhere"] = 0.0, 0.0
    for z in TREATED:
        m = w.zone == z
        c, e = schedule(z, w.loc[m, "d"].dt.strftime("%Y-%m-%d").values)
        w.loc[m, "closed_here"], w.loc[m, "cut_elsewhere"] = c, e
    return w


def twfe(df, y="ly", x=("closed_here", "cut_elsewhere")):
    """Two-way fixed effects on a balanced panel by demeaning; returns coefficient vector."""
    def dm(v):
        s = df[v]
        return (s - s.groupby(df.zone).transform("mean") - s.groupby(df.d).transform("mean") + s.mean()).values
    X = np.column_stack([dm(c) for c in x])
    return np.linalg.lstsq(X, dm(y), rcond=None)[0]


def fit(df, y="ly", term="closed_here", extra=""):
    m = smf.ols(f"{y} ~ closed_here + cut_elsewhere{extra} + C(zone) + C(dstr)", data=df).fit(
        cov_type="cluster", cov_kwds={"groups": df["zone"]})
    b, se = m.params[term], m.bse[term]
    return {"estimate": float(b), "lo": float(b - 1.96 * se), "hi": float(b + 1.96 * se), "se": float(se),
            "p": float(m.pvalues[term]), "n_obs": int(m.nobs), "n_zones": int(df.zone.nunique()),
            "cut_elsewhere": float(m.params["cut_elsewhere"])}


def prep(w, keep):
    df = w[w.zone.isin(keep)].copy()
    df["ly"] = np.log(df["n"].clip(lower=1))
    df["dstr"] = df.d.dt.strftime("%Y-%m-%d")
    return df


def main():
    near, allbq, adj, names = zone_sets()
    trips = pd.read_csv(DER / "gtrain_pickups_zone_day.csv")
    everything = sorted(set(allbq) | set(TREATED))
    w24, w23 = panel(trips, everything, 2024), panel(trips, everything, 2023)
    june = w24[(w24.d >= "2024-06-01") & (w24.d <= "2024-06-27")].groupby("zone")["n"].mean()
    big = set(june[june >= 200].index)
    dropped = sorted(set(near + list(TREATED)) - big)
    treated = [z for z in TREATED if z in big]
    ctrl = [z for z in near if z in big]
    res = {"zones": {"treated": {int(z): names[z] for z in treated}, "controls": {int(z): names[z] for z in ctrl},
                     "dropped_by_volume_rule": {int(z): names[z] for z in dropped}, "adjacent_controls": adj,
                     "june_mean_daily_pickups": {int(z): round(float(june[z]), 1) for z in treated + ctrl}}}

    # ---- first stage -------------------------------------------------------------------------------------
    s = pd.read_csv(DER / "gtrain_subway_entries.csv", dtype={"station_complex_id": str})
    s["d"] = pd.to_datetime(s["d"])
    fs, tot_base, tot_closed, lost_station_days = {}, 0.0, 0.0, 0.0
    for year in (2024, 2023):
        sy = s[s.d.dt.year == year].copy()
        if year == 2023:
            sy["d"] = sy["d"] + SHIFT
        for cid, (nm, zone, phases) in G_ONLY.items():
            x = sy[sy.station_complex_id == cid].set_index("d")["entries"]
            x = x.reindex(pd.date_range("2024-06-01", "2024-09-30"), fill_value=0)   # a day with no rows has no entries
            base = x["2024-06-01":"2024-06-27"].mean()
            row = {"station": nm, "zone": zone, "june_mean": round(float(base), 1)}
            for ph, (a, b) in PHASES.items():
                row[f"phase{ph}_mean"] = round(float(x[a:b].mean()), 1)
                row[f"phase{ph}_change_pct"] = round(100 * float(x[a:b].mean() / base - 1), 1)
                if year == 2024 and ph in phases:
                    n = len(x[a:b])
                    tot_base += base * n
                    tot_closed += x[a:b].sum()
            row["sept_change_pct"] = round(100 * float(x["2024-09-04":"2024-09-30"].mean() / base - 1), 1)
            row["coded_closed_in"] = list(phases)
            fs.setdefault(str(year), {})[cid] = row
    fall = 1 - tot_closed / tot_base
    res["first_stage"] = {"pooled_fall_pct": round(100 * fall, 1), "passes": bool(fall >= 0.70),
                          "lost_entries_total": round(tot_base - tot_closed), "stations": fs}

    # ---- primary and sensitivities ------------------------------------------------------------------------
    df = prep(w24, treated + ctrl)
    est = {"primary": fit(df)}
    rng = np.random.default_rng(20241112)
    cdf = df[df.zone.isin(ctrl)].copy()
    dates = np.array(sorted(cdf.dstr.unique()))
    scheds = [schedule(z, dates) for z in treated]
    cdf = cdf.sort_values(["zone", "dstr"]).reset_index(drop=True)
    zc = sorted(ctrl)
    draws = []
    for _ in range(2000):
        pick = rng.choice(len(zc), size=len(treated), replace=False)
        c = np.zeros((len(zc), len(dates)))
        e = np.zeros((len(zc), len(dates)))
        for k, i in enumerate(pick):
            c[i], e[i] = scheds[k]
        cdf["closed_here"], cdf["cut_elsewhere"] = c.ravel(), e.ravel()
        draws.append(twfe(cdf)[0])
    draws = np.array(draws)
    est["primary"]["permutation_p"] = float((np.abs(draws) >= abs(est["primary"]["estimate"])).mean())
    est["primary"]["permutation_sd"] = float(draws.std())
    est["primary"]["permutation_95"] = [float(np.quantile(draws, 0.025)), float(np.quantile(draws, 0.975))]

    p23 = prep(w23, treated + ctrl)
    est["placebo_2023"] = fit(p23)

    sub = [z for z in treated if z in G_DEPENDENT]
    est["g_dependent"] = fit(prep(w24, sub + ctrl))
    est["g_dependent_placebo_2023"] = fit(prep(w23, sub + ctrl))
    for ph, (a, b) in PHASES.items():
        d2 = df.copy()
        inph = ((d2.dstr >= a) & (d2.dstr <= b)).astype(float)
        d2["closed_ph"] = d2.closed_here * inph
        d2["closed_other"] = d2.closed_here * (1 - inph)
        m = smf.ols("ly ~ closed_ph + closed_other + cut_elsewhere + C(zone) + C(dstr)", data=d2).fit(
            cov_type="cluster", cov_kwds={"groups": d2["zone"]})
        est[f"phase{ph}"] = {"estimate": float(m.params["closed_ph"]), "lo": float(m.conf_int().loc["closed_ph", 0]),
                             "hi": float(m.conf_int().loc["closed_ph", 1])}
    for z in treated:
        r = fit(prep(w24, [z] + ctrl))
        r["placebo_2023"] = fit(prep(w23, [z] + ctrl))["estimate"]
        est[f"zone_{z}"] = r
    pm = smf.glm("n ~ closed_here + cut_elsewhere + C(zone) + C(dstr)", data=df, family=__import__("statsmodels.api").api.families.Poisson()).fit(
        cov_type="cluster", cov_kwds={"groups": df["zone"]})
    ci = pm.conf_int().loc["closed_here"]
    est["poisson"] = {"estimate": float(pm.params["closed_here"]), "lo": float(ci[0]), "hi": float(ci[1])}
    # triple difference: log 2024 minus log 2023 on the aligned day, zone and day fixed effects
    dd = df.merge(p23[["zone", "dstr", "ly"]], on=["zone", "dstr"], suffixes=("", "_23"))
    dd["ly"] = dd["ly"] - dd["ly_23"]
    est["triple_difference"] = fit(dd)
    allc = [z for z in allbq if z in big]
    est["controls_all_bk_qn"] = fit(prep(w24, treated + allc))
    est["controls_drop_adjacent"] = fit(prep(w24, treated + [z for z in ctrl if z not in adj]))
    wk = df[pd.to_datetime(df.dstr).dt.dayofweek < 5]
    est["weekdays"] = fit(wk)
    for co in ("uber", "lyft"):
        d3 = df.copy()
        d3["ly"] = np.log(d3[co].clip(lower=1))
        est[co] = fit(d3)
    res["estimates"] = est

    # ---- implied diversion ---------------------------------------------------------------------------------
    b = est["primary"]["estimate"]
    obs = df.loc[df.closed_here == 1, "n"].sum()
    extra = obs * (1 - np.exp(-b))
    res["diversion"] = {"treated_zone_days": int((df.closed_here == 1).sum()), "pickups_on_closed_days": int(obs),
                        "extra_pickups": round(float(extra)), "extra_pickups_lo": round(float(obs * (1 - np.exp(-est['primary']['lo'])))),
                        "extra_pickups_hi": round(float(obs * (1 - np.exp(-est['primary']['hi'])))),
                        "lost_entries": res["first_stage"]["lost_entries_total"],
                        "extra_pickups_per_100_lost_entries": round(100 * float(extra) / res["first_stage"]["lost_entries_total"], 2)}
    (DER / "gtrain_results.json").write_text(json.dumps(res, indent=1))
    out = pd.concat([df.assign(year=2024), p23.assign(year=2023)])[["year", "zone", "dstr", "n", "uber", "lyft", "closed_here", "cut_elsewhere"]]
    out.to_csv(DER / "gtrain_panel.csv", index=False)
    np.save(DER / "gtrain_permutation_draws.npy", draws)

    print(json.dumps(res["zones"]["dropped_by_volume_rule"]), len(treated), len(ctrl))
    print("first stage", res["first_stage"]["pooled_fall_pct"], res["first_stage"]["passes"])
    for y in ("2024", "2023"):
        for cid, r in fs[y].items():
            print(y, cid, r)
    for k, v in est.items():
        print(f"{k:28s} {v['estimate']:+.4f} ({v['lo']:+.4f} to {v['hi']:+.4f})", {a: round(c, 4) for a, c in v.items() if a in ("p", "permutation_p", "n_zones", "cut_elsewhere", "placebo_2023")})
    print(res["diversion"])


if __name__ == "__main__":
    main()
