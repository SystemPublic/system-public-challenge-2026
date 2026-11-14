"""Exploratory checks run after the registered results were read. Nothing here decides a verdict.

1. The two halves' heat-call slopes refitted as Poisson (the registered negative binomial fit for the
   high-AC half did not converge to a usable covariance).
2. Calibration of the hot-day contrast: the registered binomial model on days of 27 C or more, refitted
   on 200 sets of simulated incidents in which districts have identical slopes (seed 1).
3. The low-AC against high-AC contrast below and above 27 C in one model (piecewise linear in TMAX).
4. Rate of events per 100,000 residents is not available by district in this folder; shares are reported.
5. Shootings by hour block and school status, with temperature held fixed (count models by block).
Writes data/derived/heat_solutions/exploratory.json.
"""
from __future__ import annotations

import json
import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from patsy import dmatrix

from analyses.heat_solutions import run
from analyses.heat_solutions.common import CONTROLS, DER, SCHOOL_FORM, calendar, cd_table, fix_latlon, to_cd, window

warnings.filterwarnings("ignore")


def pois(d, y, form, name, exp=True):
    r = smf.glm(f"{y} ~ {form}", d, family=sm.families.Poisson()).fit(cov_type="HC0")
    return run.est(r, name, exp=exp)


def piecewise(d, a, b, knot=27.0):
    k = d[(d[a] + d[b]) > 0].copy()
    k["below"] = np.minimum(k["TMAX"], knot) / 5
    k["above"] = np.clip(k["TMAX"] - knot, 0, None) / 5
    X = dmatrix("below + above + " + CONTROLS, k, return_type="dataframe")
    r = sm.GLM(np.column_stack([k[a].values, k[b].values]), X, family=sm.families.Binomial()).fit(cov_type="HC0")
    return {"below_27": run.est(r, "below"), "above_27": run.est(r, "above")}


def main():
    cd = cd_table()
    cal = calendar().dropna(subset=["TMAX"])
    inc, vic, ems, _ = run.fetch()
    inc["date"] = pd.to_datetime(inc["d"]).dt.normalize()
    inc["hour"] = inc["t"].str.split(":").str[0].astype(int)
    inc[["lat", "lon"]] = inc[["lat", "lon"]].astype(float)
    inc = inc.dropna(subset=["lat", "lon"]).copy()
    inc["lat"], inc["lon"] = fix_latlon(inc["lat"].values, inc["lon"].values)
    inc["cd"] = to_cd(inc["lat"].values, inc["lon"].values)
    inc = inc[inc["date"].isin(cal.index)]
    d, m = run.daily_by_group(inc, cal, cd)
    ems["date"] = pd.to_datetime(ems["dt"]).dt.normalize()
    ems["cd"] = pd.to_numeric(ems["cd"], errors="coerce")
    ems = ems.dropna(subset=["cd"])
    ems["cd"] = ems["cd"].astype(int)
    wcal = cal[(cal.month.between(5, 9))]
    e = ems[ems["date"].isin(wcal.index)]
    de, me = run.daily_by_group(e, wcal, cd)
    X = {}
    X["heat_call_slopes_poisson"] = {g: pois(de, g, "t5 + " + CONTROLS, "t5") for g in ("low", "high")}
    X["heat_calls_piecewise"] = piecewise(de, "low", "high")
    X["shootings_piecewise"] = piecewise(d, "low", "high")
    X["shootings_piecewise_night_00_06"] = piecewise(run.daily_by_group(inc[inc.hour < 6], cal, cd)[0], "low", "high")
    # public-housing buildings against apartment buildings: is the location field filled evenly over the years?
    loc = inc["loc"].fillna("").str.upper()
    yr = inc["date"].dt.year
    X["location_desc_by_year"] = {int(y): {"public_housing": int(((loc == "MULTI DWELL - PUBLIC HOUS") & (yr == y)).sum()),
                                           "apartment": int(((loc == "MULTI DWELL - APT BUILD") & (yr == y)).sum()),
                                           "blank": int(((loc == "") | (loc == "(NULL)")) [yr == y].sum()), "all": int((yr == y).sum())} for y in sorted(yr.unique())}
    j = cal.copy()
    j["pub"] = inc[loc == "MULTI DWELL - PUBLIC HOUS"].groupby("date").size().reindex(j.index).fillna(0).astype(int)
    j["apt"] = inc[loc == "MULTI DWELL - APT BUILD"].groupby("date").size().reindex(j.index).fillna(0).astype(int)
    j["rest"] = inc[~loc.isin(["MULTI DWELL - PUBLIC HOUS", "MULTI DWELL - APT BUILD"])].groupby("date").size().reindex(j.index).fillna(0).astype(int)
    X["public_housing_building_vs_apartment_piecewise"] = piecewise(j, "pub", "apt")
    X["building_slopes"] = {g: pois(j, g, "t5 + " + CONTROLS, "t5") for g in ("pub", "apt", "rest")}
    X["public_housing_building_vs_apartment_2006_2019"] = run.binom(j[j.year <= 2019], "pub", "apt")
    X["public_housing_building_vs_apartment_2020_2026"] = run.binom(j[j.year >= 2020], "pub", "apt")
    # calibration of the hot-day contrast under equal slopes
    rng = np.random.default_rng(1)
    share = m.groupby("low_ac").size()
    p_low = float(share[1] / share.sum())
    h = d[d["TMAX"] >= 27].copy()
    tot = (h["low"] + h["high"]).values
    est, cover = [], 0
    for _ in range(200):
        h["a"] = rng.binomial(tot, p_low)
        h["b"] = tot - h["a"]
        o = run.binom(h, "a", "b")
        est.append(o["estimate"])
        cover += int(o["lo"] <= 0 <= o["hi"])
    X["hot_day_contrast_calibration"] = {"sims": 200, "mean_estimate": float(np.mean(est)), "sd_estimate": float(np.std(est)), "coverage_of_zero": cover / 200}
    # leave one borough out, primary shootings contrast
    X["shootings_leave_one_borough_out"] = {}
    for b, name in ((1, "Manhattan"), (2, "Bronx"), (3, "Brooklyn"), (4, "Queens"), (5, "Staten Island")):
        dd, _ = run.daily_by_group(inc[inc.cd // 100 != b], cal, cd)
        X["shootings_leave_one_borough_out"][name] = run.binom(dd, "low", "high")
    # school: shootings by hour block, days out against school days, temperature held fixed
    full = calendar()
    k = window(full, 42)
    X["school_by_hour_block"] = {}
    for lab, lo, hi in (("00-05", 0, 5), ("06-14", 6, 14), ("15-19", 15, 19), ("20-23", 20, 23)):
        s = inc[(inc.hour >= lo) & (inc.hour <= hi)].groupby("date").size()
        k["y"] = k["date"].map(s).fillna(0).astype(int).values
        X["school_by_hour_block"][lab] = {**pois(k, "y", SCHOOL_FORM, "out"), "shootings": int(k["y"].sum())}
    # school: placebo transitions four weeks before the real ones (all days are school days or all are recess on both sides)
    (DER / "exploratory.json").write_text(json.dumps(X, indent=1, default=float))
    print(json.dumps(X, indent=1, default=float))
    d[["TMAX", "low", "high", "t1", "t3"]].to_csv(DER / "shootings_daily_by_ac_half.csv")
    de[["TMAX", "low", "high"]].to_csv(DER / "heat_calls_daily_by_ac_half.csv")


if __name__ == "__main__":
    main()
