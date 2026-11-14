"""The registered heat-solutions tests: heat-ac-shootings, heat-ac-heat-calls, heat-school-out.

Fixed before registration and run unchanged afterwards. No resampling and no random numbers in the
tests: all intervals are Wald intervals from HC0 standard errors. `--simulate` replaces every outcome
record with simulated records (seed 1) so the code can be exercised before registration.

Writes data/derived/heat_solutions/results.json, sources.json, district_slopes.csv,
school_window_daily.csv, hourly_under18.csv.
"""
from __future__ import annotations

import json
import sys
import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

from analyses.heat_solutions.common import CONTROLS, DER, END, SCHOOL_FORM, calendar, cd_table, fix_latlon, to_cd, window
from concord import socrata

warnings.filterwarnings("ignore")
LOWER_MANHATTAN = [101, 102, 103, 104, 105, 106]


# ---------------------------------------------------------------- data
def fetch():
    src = []
    rows, s1 = socrata.query_all(
        "5ucz-vwe8", select="incident_key, max(occur_date) as d, max(occur_time) as t, max(latitude) as lat, max(longitude) as lon, "
                            "max(jurisdiction_code) as jur, max(location_desc) as loc",
        where=f"occur_date between '2006-01-01T00:00:00' and '{END}T23:59:59'", group="incident_key", order="incident_key")
    inc = pd.DataFrame(rows)
    rows, s2 = socrata.query_all(
        "833y-fsy8", select="incident_key, occur_date as d, occur_time as t, vic_age_group as age",
        where="occur_date between '2006-01-01T00:00:00' and '2024-12-31T23:59:59'", order="incident_key")
    vic = pd.DataFrame(rows)
    rows, s3 = socrata.query_all(
        "76xm-jjuj", select="incident_datetime as dt, communitydistrict as cd, zipcode", where="final_call_type='HEAT'", order="incident_datetime")
    ems = pd.DataFrame(rows)
    return inc, vic, ems, [s1, s2, s3]


def simulate(cal):
    rng = np.random.default_rng(1)
    c = pd.read_csv(DER / "design_cd_counts.csv")
    d = cal.dropna(subset=["TMAX"])
    lam = 3.2 * np.exp(0.136 * (d["t5"].values - d["t5"].mean()))
    n = rng.poisson(lam)
    dates = np.repeat(d.index.values, n)
    k = len(dates)
    cds = rng.choice(c["cd"].values, size=k, p=c["shootings"].values / c["shootings"].sum())
    inc = pd.DataFrame({"incident_key": np.arange(k), "d": pd.to_datetime(dates).strftime("%Y-%m-%dT00:00:00.000"),
                        "t": [f"{h:02d}:00:00" for h in rng.integers(0, 24, k)], "cd_sim": cds,
                        "jur": rng.choice(["0", "2"], size=k, p=[0.84, 0.16]), "loc": rng.choice(["MULTI DWELL - PUBLIC HOUS", "MULTI DWELL - APT BUILD", None], size=k)})
    vic = inc[inc["d"] < "2025"][["incident_key", "d", "t"]].copy()
    vic["age"] = rng.choice(["<18", "18-24", "25-44", "45-64"], size=len(vic), p=[0.1, 0.37, 0.45, 0.08])
    w = d[d.month.between(5, 9)]
    lam = 3.0 * np.power(4.09, w["t5"].values - w["t5"].mean())
    n = rng.poisson(lam)
    dates = np.repeat(w.index.values, n)
    ems = pd.DataFrame({"dt": pd.to_datetime(dates).strftime("%Y-%m-%dT12:00:00.000"),
                        "cd": rng.choice(c["cd"].values, size=len(dates), p=c["heat_calls"].values / c["heat_calls"].sum()), "zipcode": "10001"})
    return inc, vic, ems, [{"simulated": True}]


# ---------------------------------------------------------------- models
def est(res, name, exp=False):
    b, se = float(res.params[name]), float(res.bse[name])
    f = np.exp if exp else (lambda x: x)
    return {"estimate": float(f(b)), "lo": float(f(b - 1.96 * se)), "hi": float(f(b + 1.96 * se)), "se": se, "p": float(res.pvalues[name])}


def binom(d, a, b, x="t5", extra=""):
    """Binomial GLM of column a out of a + b on x and the calendar terms; the coefficient of x is the
    difference of the two groups' log rate ratios per unit of x."""
    from patsy import dmatrix
    k = d[(d[a] + d[b]) > 0].copy()
    X = dmatrix(f"{x} + {CONTROLS}{extra}", k, return_type="dataframe")
    r = sm.GLM(np.column_stack([k[a].values, k[b].values]), X, family=sm.families.Binomial()).fit(cov_type="HC0")
    o = est(r, x)
    o.update({"events_a": int(k[a].sum()), "events_b": int(k[b].sum()), "days": int(len(k))})
    return o


def count_fit(d, y, form):
    """Negative binomial GLM with dispersion by maximum likelihood; Poisson if that fails or gives no overdispersion."""
    alpha = None
    try:
        ml = smf.negativebinomial(f"{y} ~ {form}", d).fit(disp=0, maxiter=300)
        a = float(ml.params["alpha"])
        alpha = a if np.isfinite(a) and a > 1e-4 else None
    except Exception:
        alpha = None
    fam = sm.families.NegativeBinomial(alpha=alpha) if alpha else sm.families.Poisson()
    return smf.glm(f"{y} ~ {form}", d, family=fam).fit(cov_type="HC0"), alpha


def group_slopes(d, cols):
    out = {}
    for c in cols:
        r, a = count_fit(d, c, "t5 + " + CONTROLS)
        out[c] = {**est(r, "t5", exp=True), "alpha": a, "events": int(d[c].sum())}
    return out


def daily_by_group(ev, cal, cd, col="cd"):
    """Daily counts in low-AC and other districts, bottom and top tercile, and by income half."""
    m = ev.merge(cd[["cd", "low_ac", "ac_tert", "low_income"]], on="cd", how="inner")
    d = cal.copy()

    def cnt(mask):
        return m[mask].groupby("date").size().reindex(d.index).fillna(0).astype(int)
    d["low"], d["high"] = cnt(m.low_ac == 1), cnt(m.low_ac == 0)
    d["t1"], d["t3"] = cnt(m.ac_tert == 1), cnt(m.ac_tert == 3)
    d["li_low"], d["li_high"] = cnt((m.low_ac == 1) & (m.low_income == 1)), cnt((m.low_ac == 0) & (m.low_income == 1))
    d["hi_low"], d["hi_high"] = cnt((m.low_ac == 1) & (m.low_income == 0)), cnt((m.low_ac == 0) & (m.low_income == 0))
    return d, m


def district_slopes(m, cal, cd, min_events, label):
    rows = []
    for c, g in m.groupby("cd"):
        if len(g) < min_events:
            continue
        d = cal.copy()
        d["y"] = g.groupby("date").size().reindex(d.index).fillna(0).astype(int)
        try:
            r = smf.glm("y ~ t5 + " + CONTROLS, d, family=sm.families.Poisson()).fit(cov_type="HC0")
            rows.append({"cd": int(c), "events": int(len(g)), "slope": float(r.params["t5"]), "se": float(r.bse["t5"])})
        except Exception:
            continue
    s = pd.DataFrame(rows).merge(cd[["cd", "ac", "income", "black"]], on="cd")
    s = s[np.isfinite(s["slope"]) & (s["se"] > 0) & (s["se"] < 5)]
    s["outcome"] = label
    s["ac10"] = (s["ac"] - s["ac"].mean()) / 10
    s["linc"] = np.log(s["income"]) - np.log(s["income"]).mean()
    res = {"n_districts": int(len(s)), "min_events": min_events}
    for name, form in (("ac_only", "slope ~ ac10"), ("ac_and_income", "slope ~ ac10 + linc")):
        r = smf.wls(form, s, weights=1 / s["se"] ** 2).fit(cov_type="HC1")
        res[name] = {k: est(r, k) for k in r.params.index if k != "Intercept"}
    return s, res


def ac_tests(ev, cal, cd, label, min_events, hot=27.0):
    d, m = daily_by_group(ev, cal, cd)
    out = {"n_events_in_districts": int(len(m)), "period": [str(cal.index.min().date()), str(cal.index.max().date())], "days": int(len(cal))}
    out["primary_low_vs_high_half"] = binom(d, "low", "high")
    out["slopes_by_half"] = group_slopes(d, ["low", "high"])
    out["terciles_bottom_vs_top"] = binom(d, "t1", "t3")
    out["low_income_districts_only"] = binom(d, "li_low", "li_high")
    out["high_income_districts_only"] = binom(d, "hi_low", "hi_high")
    h = d[d["TMAX"] >= hot]
    out["days_tmax_27_or_more"] = binom(h, "low", "high")
    s, res = district_slopes(m, cal, cd, min_events, label)
    out["district_slopes_on_ac_per_10_points"] = res
    return out, d, m, s


def main(sim=False):
    cd = cd_table()
    cal = calendar().dropna(subset=["TMAX"])
    inc, vic, ems, sources = simulate(cal) if sim else fetch()
    R = {"simulated": sim}

    # ---- shooting incidents
    inc["date"] = pd.to_datetime(inc["d"]).dt.normalize()
    inc["hour"] = inc["t"].str.split(":").str[0].astype(int)  # changed after registration: some times are not zero-padded
    if sim:
        inc["cd"] = inc["cd_sim"]
    else:
        inc[["lat", "lon"]] = inc[["lat", "lon"]].astype(float)
        inc = inc.dropna(subset=["lat", "lon"]).copy()
        inc["lat"], inc["lon"] = fix_latlon(inc["lat"].values, inc["lon"].values)
        inc["cd"] = to_cd(inc["lat"].values, inc["lon"].values)
    inc = inc[inc["date"].isin(cal.index)]
    A, d, m, s_sh = ac_tests(inc, cal, cd, "shootings", 150)
    night = inc[inc["hour"] < 6]
    dn, _ = daily_by_group(night, cal, cd)
    A["hours_00_to_06"] = binom(dn, "low", "high")
    A["warm_season"] = binom(d[d.month.between(5, 9)], "low", "high")
    A["2006_2019"] = binom(d[d.year <= 2019], "low", "high")
    A["2020_2026"] = binom(d[d.year >= 2020], "low", "high")
    # public housing: Housing Bureau jurisdiction against all other incidents, and public-housing buildings against other apartment buildings
    j = cal.copy()
    jur = inc["jur"].astype(str).str[:1]
    j["housing"] = inc[jur == "2"].groupby("date").size().reindex(j.index).fillna(0).astype(int)
    j["other"] = inc[jur != "2"].groupby("date").size().reindex(j.index).fillna(0).astype(int)
    A["housing_jurisdiction_vs_other"] = binom(j, "housing", "other")
    A["housing_slopes"] = group_slopes(j, ["housing", "other"])
    loc = inc["loc"].fillna("").str.upper()
    j["pub"] = inc[loc == "MULTI DWELL - PUBLIC HOUS"].groupby("date").size().reindex(j.index).fillna(0).astype(int)
    j["apt"] = inc[loc == "MULTI DWELL - APT BUILD"].groupby("date").size().reindex(j.index).fillna(0).astype(int)
    A["public_housing_building_vs_apartment_building"] = binom(j, "pub", "apt")
    # housing jurisdiction against other incidents in the same districts: add district composition by restricting to low-AC districts
    jl = cal.copy()
    il = inc.merge(cd[["cd", "low_ac"]], on="cd")
    il = il[il.low_ac == 1]
    jl["housing"] = il[il["jur"].astype(str).str[:1] == "2"].groupby("date").size().reindex(jl.index).fillna(0).astype(int)
    jl["other"] = il[il["jur"].astype(str).str[:1] != "2"].groupby("date").size().reindex(jl.index).fillna(0).astype(int)
    A["housing_vs_other_within_low_ac_districts"] = binom(jl, "housing", "other")
    R["heat_ac_shootings"] = A

    # ---- EMS heat calls, May to September
    ems["date"] = pd.to_datetime(ems["dt"]).dt.normalize()
    ems["cd"] = pd.to_numeric(ems["cd"], errors="coerce")
    ems = ems.dropna(subset=["cd"])
    ems["cd"] = ems["cd"].astype(int)
    y0, y1 = int(ems["date"].dt.year.min()), int(ems["date"].dt.year.max())
    wcal = cal[(cal.month.between(5, 9)) & (cal.year >= max(y0, 2006)) & (cal.year <= y1)]
    e = ems[ems["date"].isin(wcal.index)]
    B, de, me, s_ems = ac_tests(e, wcal, cd, "heat_calls", 100)
    B["without_manhattan_below_59th_street"] = binom(daily_by_group(e[~e.cd.isin(LOWER_MANHATTAN)], wcal, cd)[0], "low", "high")
    B["share_of_all_heat_calls_in_may_to_september"] = float(len(e) / max(1, len(ems[ems["date"] >= "2006-01-01"])))
    R["heat_ac_heat_calls"] = B
    pd.concat([s_sh, s_ems]).to_csv(DER / "district_slopes.csv", index=False)

    # ---- school
    full = calendar()
    full["n"] = inc.groupby("date").size().reindex(full.index).fillna(0).astype(int)
    vic["date"] = pd.to_datetime(vic["d"]).dt.normalize()
    vic["hour"] = vic["t"].str.split(":").str[0].astype(int)  # changed after registration, as above
    vic["grp"] = np.where(vic["age"] == "<18", "u18", np.where(vic["age"] == "18-24", "a1824", np.where(vic["age"].isin(["25-44", "45-64", "65+"]), "a25", "unk")))
    for g in ("u18", "a1824", "a25"):
        full["v_" + g] = vic[vic.grp == g].groupby("date").size().reindex(full.index).fillna(0).astype(int)
    S = {}
    k42, k21 = window(full, 42), window(full, 21)
    r, a = count_fit(k42, "n", SCHOOL_FORM)
    S["primary_out_of_school_irr"] = {**est(r, "out", exp=True), "alpha": a, "weekdays": int(len(k42)), "days_out": int(k42.out.sum()), "shootings": int(k42.n.sum()),
                                      "t5_irr_in_window": est(r, "t5", exp=True)}
    r, a = count_fit(k21, "n", SCHOOL_FORM)
    S["window_21_days"] = {**est(r, "out", exp=True), "weekdays": int(len(k21)), "shootings": int(k21.n.sum())}
    k42["q_end"], k42["q_start"] = k42["trend_end"] ** 2, k42["trend_start"] ** 2
    r, a = count_fit(k42, "n", SCHOOL_FORM + " + q_end + q_start")
    S["quadratic_trends"] = est(r, "out", exp=True)
    for kind in ("end", "start"):
        kk = k42[k42.kind == kind]
        r, a = count_fit(kk, "n", f"out + t5 + trend_{kind} + C(dow) + wet + C(wy)")
        S[f"{kind}_of_term_only"] = {**est(r, "out", exp=True), "weekdays": int(len(kk))}
    kv = k42[k42["date"] <= "2024-12-31"].copy()
    for g in ("u18", "a1824", "a25"):
        r, a = count_fit(kv, "v_" + g, SCHOOL_FORM)
        S[f"victims_{g}"] = {**est(r, "out", exp=True), "victims": int(kv["v_" + g].sum()), "weekdays": int(len(kv))}
    kv["v_other"] = kv["v_a1824"] + kv["v_a25"]
    kk = kv[(kv.v_u18 + kv.v_other) > 0].copy()
    from patsy import dmatrix
    X = dmatrix("out + t5 + trend_end + trend_start + C(dow) + wet + C(year)", kk, return_type="dataframe")
    r = sm.GLM(np.column_stack([kk.v_u18.values, kk.v_other.values]), X, family=sm.families.Binomial()).fit(cov_type="HC0")
    S["under_18_share_odds_ratio"] = est(r, "out", exp=True)
    # hours of under-18 victims on school weekdays and out-of-school weekdays in the window
    vw = vic.merge(kv[["date", "out"]], on="date")
    vw["block"] = pd.cut(vw["hour"], [-1, 7, 14, 19, 23], labels=["00-07", "08-14", "15-19", "20-23"])
    tab = vw.groupby(["grp", "out", "block"], observed=False).size().rename("victims").reset_index()
    nd = kv.groupby("out").size()
    tab["per_100_weekdays"] = 100 * tab["victims"] / tab["out"].map(nd)
    tab.to_csv(DER / "hourly_under18.csv", index=False)
    # the heat-shootings model with and without a term for the summer recess
    dd = full.dropna(subset=["TMAX"])
    r0, a0 = count_fit(dd, "n", "t5 + " + CONTROLS)
    r1, a1 = count_fit(dd, "n", "t5 + summer_out + " + CONTROLS)
    S["heat_slope_without_recess_term"] = est(r0, "t5", exp=True)
    S["heat_slope_with_recess_term"] = est(r1, "t5", exp=True)
    S["recess_term_irr"] = est(r1, "summer_out", exp=True)
    S["share_of_log_slope_removed"] = float(1 - r1.params["t5"] / r0.params["t5"])
    # weekdays only, months May to October, month-by-year terms: school days against other weekdays at the same temperature
    R["heat_school_out"] = S
    k42[["date", "kind", "rel", "out", "TMAX", "n"] + [c for c in k42 if c.startswith("v_")]].to_csv(DER / "school_window_daily.csv", index=False)
    name = "results_simulated.json" if sim else "results.json"
    (DER / name).write_text(json.dumps(R, indent=1, default=float))
    if not sim:
        (DER / "sources.json").write_text(json.dumps(sources + [calendar().attrs["source"]], indent=1, default=str))
    print(json.dumps(R, indent=1, default=float)[:6000])


if __name__ == "__main__":
    main(sim="--simulate" in sys.argv)
