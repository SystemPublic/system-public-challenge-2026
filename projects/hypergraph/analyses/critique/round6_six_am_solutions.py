"""Round 6 answer, exploratory check: the heat-solutions estimates on a day from 06:00 to 05:59.

Three referee reports of 13 Nov 2026 found that counting an event before 06:00 on its calendar
date changes results, because the maximum of that date comes hours later. This script refits
every estimate of heat-ac-shootings, heat-ac-heat-calls and heat-school-out that
docs/heat_solutions.md quotes, twice: with events counted on the calendar date (as registered)
and with events before 06:00 counted on the previous date. It uses the functions of the
registered run.py and of exploratory.py and changes only the date an event is counted on. The
calendar-date column must equal data/derived/heat_solutions/results.json and exploratory.json;
the script asserts this for the deciding numbers. It decides no verdict (PRECEDENCE rule 4): the
registered measure is the calendar date.

Run from the repository root:
    ~/.venvs/nyc-concordance/bin/python analyses/critique/round6_six_am_solutions.py
Reads the cached queries of run.py. Writes data/derived/round6_heat/six_am_solutions.json.
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from analyses.heat_solutions import exploratory as X  # noqa: E402
from analyses.heat_solutions import run  # noqa: E402
from analyses.heat_solutions.common import CONTROLS, DER, SCHOOL_FORM, calendar, cd_table, fix_latlon, to_cd, window  # noqa: E402

warnings.filterwarnings("ignore")
OUT = ROOT / "data/derived/round6_heat"
OUT.mkdir(parents=True, exist_ok=True)


def keep(o):
    return {k: o[k] for k in ("estimate", "lo", "hi") if k in o} | {k: o[k] for k in ("days", "weekdays", "shootings", "victims", "events_a", "events_b") if k in o}


def shootings(inc, cal, cd):
    """The estimates of heat-ac-shootings; `inc` has the column `date` an incident is counted on."""
    inc = inc[inc["date"].isin(cal.index)]
    d, m = run.daily_by_group(inc, cal, cd)
    R = {"incidents_in_districts": int(len(m))}
    R["primary"] = keep(run.binom(d, "low", "high"))
    s = run.group_slopes(d, ["low", "high"])
    R["slope_low_half"], R["slope_high_half"] = keep(s["low"]), keep(s["high"])
    R["terciles"] = keep(run.binom(d, "t1", "t3"))
    R["low_income_half"] = keep(run.binom(d, "li_low", "li_high"))
    R["high_income_half"] = keep(run.binom(d, "hi_low", "hi_high"))
    a, b = run.binom(d, "li_low", "li_high"), run.binom(d, "hi_low", "hi_high")
    w = np.array([1 / a["se"] ** 2, 1 / b["se"] ** 2])
    e, se = float((w * [a["estimate"], b["estimate"]]).sum() / w.sum()), float(1 / np.sqrt(w.sum()))
    R["income_halves_pooled"] = {"estimate": e, "lo": e - 1.96 * se, "hi": e + 1.96 * se}
    R["days_27_or_more"] = keep(run.binom(d[d["TMAX"] >= 27.0], "low", "high"))
    R["may_to_september"] = keep(run.binom(d[d.month.between(5, 9)], "low", "high"))
    R["2006_2019"] = keep(run.binom(d[d.year <= 2019], "low", "high"))
    R["2020_2026"] = keep(run.binom(d[d.year >= 2020], "low", "high"))
    p = X.piecewise(d, "low", "high")
    R["piecewise_below_27"], R["piecewise_above_27"] = keep(p["below_27"]), keep(p["above_27"])
    dn, _ = run.daily_by_group(inc[inc["hour"] < 6], cal, cd)
    R["incidents_00_to_06_only"] = keep(run.binom(dn, "low", "high"))
    j = cal.copy()
    jur = inc["jur"].astype(str).str[:1]
    j["housing"] = inc[jur == "2"].groupby("date").size().reindex(j.index).fillna(0).astype(int)
    j["other"] = inc[jur != "2"].groupby("date").size().reindex(j.index).fillna(0).astype(int)
    R["housing_jurisdiction_vs_other"] = keep(run.binom(j, "housing", "other"))
    loc = inc["loc"].fillna("").str.upper()
    j["pub"] = inc[loc == "MULTI DWELL - PUBLIC HOUS"].groupby("date").size().reindex(j.index).fillna(0).astype(int)
    j["apt"] = inc[loc == "MULTI DWELL - APT BUILD"].groupby("date").size().reindex(j.index).fillna(0).astype(int)
    R["public_housing_building_vs_apartment"] = keep(run.binom(j, "pub", "apt"))
    p = X.piecewise(j, "pub", "apt")
    R["public_housing_building_below_27"], R["public_housing_building_above_27"] = keep(p["below_27"]), keep(p["above_27"])
    return R


def heat_calls(ems, cal, cd):
    y0, y1 = int(ems["date0"].dt.year.min()), int(ems["date0"].dt.year.max())
    wcal = cal[(cal.month.between(5, 9)) & (cal.year >= max(y0, 2006)) & (cal.year <= y1)]
    e = ems[ems["date"].isin(wcal.index)]
    d, m = run.daily_by_group(e, wcal, cd)
    R = {"calls_in_districts": int(len(m))}
    R["primary"] = keep(run.binom(d, "low", "high"))
    R["terciles"] = keep(run.binom(d, "t1", "t3"))
    R["low_income_half"] = keep(run.binom(d, "li_low", "li_high"))
    R["high_income_half"] = keep(run.binom(d, "hi_low", "hi_high"))
    R["days_27_or_more"] = keep(run.binom(d[d["TMAX"] >= 27.0], "low", "high"))
    R["without_manhattan_below_59th_street"] = keep(run.binom(run.daily_by_group(e[~e.cd.isin(run.LOWER_MANHATTAN)], wcal, cd)[0], "low", "high"))
    for g in ("low", "high"):
        R[f"slope_{g}_half_poisson"] = keep(X.pois(d, g, "t5 + " + CONTROLS, "t5"))
    return R


def school(inc, vic, full):
    full = full.copy()
    full["n"] = inc.groupby("date").size().reindex(full.index).fillna(0).astype(int)
    for g in ("u18", "a1824", "a25"):
        full["v_" + g] = vic[vic.grp == g].groupby("date").size().reindex(full.index).fillna(0).astype(int)
    S = {}
    k42, k21 = window(full, 42), window(full, 21)
    r, _ = run.count_fit(k42, "n", SCHOOL_FORM)
    S["primary"] = {**keep(run.est(r, "out", exp=True)), "weekdays": int(len(k42)), "shootings": int(k42.n.sum())}
    r, _ = run.count_fit(k21, "n", SCHOOL_FORM)
    S["window_21_days"] = {**keep(run.est(r, "out", exp=True)), "weekdays": int(len(k21)), "shootings": int(k21.n.sum())}
    # without the weekday after a public holiday (referee's variant; on the 06:00 day that weekday no longer carries the holiday night)
    hol = set(full.index[full["hol"] == 1])
    after = k42["date"].map(lambda t: (t - pd.Timedelta(days=1)) in hol)
    r, _ = run.count_fit(k42[~after], "n", SCHOOL_FORM)
    S["without_weekday_after_public_holiday"] = {**keep(run.est(r, "out", exp=True)), "weekdays": int((~after).sum())}
    kv = k42[k42["date"] <= "2024-12-31"].copy()
    for g in ("u18", "a1824", "a25"):
        r, _ = run.count_fit(kv, "v_" + g, SCHOOL_FORM)
        S[f"victims_{g}"] = {**keep(run.est(r, "out", exp=True)), "victims": int(kv["v_" + g].sum())}
    dd = full.dropna(subset=["TMAX"])
    r0, _ = run.count_fit(dd, "n", "t5 + " + CONTROLS)
    r1, _ = run.count_fit(dd, "n", "t5 + summer_out + " + CONTROLS)
    S["heat_slope_without_recess_term"] = keep(run.est(r0, "t5", exp=True))
    S["heat_slope_with_recess_term"] = keep(run.est(r1, "t5", exp=True))
    S["recess_term"] = keep(run.est(r1, "summer_out", exp=True))
    S["share_of_log_slope_removed"] = float(1 - r1.params["t5"] / r0.params["t5"])
    for lab, lo, hi in (("00-05", 0, 5), ("06-14", 6, 14), ("15-19", 15, 19), ("20-23", 20, 23)):
        s = inc[(inc.hour >= lo) & (inc.hour <= hi)].groupby("date").size()
        k42["y"] = k42["date"].map(s).fillna(0).astype(int).values
        S[f"hour_block_{lab}"] = {**keep(X.pois(k42, "y", SCHOOL_FORM, "out")), "shootings": int(k42["y"].sum())}
        s = inc[(inc.hour >= lo) & (inc.hour <= hi)].groupby("date").size()
        k = k42[~after].copy()
        k["y"] = k["date"].map(s).fillna(0).astype(int).values
        S[f"hour_block_{lab}_without_weekday_after_holiday"] = keep(X.pois(k, "y", SCHOOL_FORM, "out"))
    vw = vic.merge(kv[["date", "out"]], on="date")  # as in run.py: the 184 dates that lie in two windows count twice on both sides of the ratio
    nd = kv.groupby("out").size()
    u = vw[vw.grp == "u18"]
    S["under_18_per_100_weekdays"] = {
        f"{lab}_{'out' if o else 'school'}": float(100 * ((u.hour >= lo) & (u.hour <= hi) & (u.out == o)).sum() / nd[o])
        for lab, lo, hi in (("00-07", 0, 7), ("15-19", 15, 19)) for o in (0, 1)}
    return S


def main():
    cd = cd_table()
    cal = calendar().dropna(subset=["TMAX"])
    full = calendar()
    inc, vic, ems, _ = run.fetch()
    inc["date0"] = pd.to_datetime(inc["d"]).dt.normalize()
    inc["hour"] = inc["t"].str.split(":").str[0].astype(int)
    inc[["lat", "lon"]] = inc[["lat", "lon"]].astype(float)
    inc = inc.dropna(subset=["lat", "lon"]).copy()
    inc["lat"], inc["lon"] = fix_latlon(inc["lat"].values, inc["lon"].values)
    inc["cd"] = to_cd(inc["lat"].values, inc["lon"].values)
    vic["date0"] = pd.to_datetime(vic["d"]).dt.normalize()
    vic["hour"] = vic["t"].str.split(":").str[0].astype(int)
    vic["grp"] = np.where(vic["age"] == "<18", "u18", np.where(vic["age"] == "18-24", "a1824", np.where(vic["age"].isin(["25-44", "45-64", "65+"]), "a25", "unk")))
    ems["dt"] = pd.to_datetime(ems["dt"])
    ems["date0"] = ems["dt"].dt.normalize()
    ems["hour"] = ems["dt"].dt.hour
    ems["cd"] = pd.to_numeric(ems["cd"], errors="coerce")
    ems = ems.dropna(subset=["cd"]).copy()
    ems["cd"] = ems["cd"].astype(int)

    res = {"note": "Exploratory, run after the outcomes; decides no verdict (rule 4). calendar = event counted on its calendar date "
                   "(as registered); six_am = event before 06:00 counted on the previous date.",
           "share_before_06": {"shooting_incidents": float((inc.hour < 6).mean()), "heat_calls": float((ems.hour < 6).mean()),
                               "victims": float((vic.hour < 6).mean())}}
    for name in ("calendar", "six_am"):
        for df in (inc, vic, ems):
            df["date"] = df["date0"] - pd.to_timedelta(((df["hour"] < 6) & (name == "six_am")).astype(int), unit="D")
        res[name] = {"heat_ac_shootings": shootings(inc, cal, cd), "heat_ac_heat_calls": heat_calls(ems, cal, cd),
                     "heat_school_out": school(inc[inc["date"].isin(full.index)], vic, full)}
    # the calendar column must be the registered results
    reg = json.loads((DER / "results.json").read_text())
    c = res["calendar"]
    for mine, theirs in ((c["heat_ac_shootings"]["primary"], reg["heat_ac_shootings"]["primary_low_vs_high_half"]),
                         (c["heat_ac_heat_calls"]["primary"], reg["heat_ac_heat_calls"]["primary_low_vs_high_half"]),
                         (c["heat_school_out"]["primary"], reg["heat_school_out"]["primary_out_of_school_irr"]),
                         (c["heat_school_out"]["recess_term"], reg["heat_school_out"]["recess_term_irr"])):
        assert all(abs(mine[k] - theirs[k]) < 1e-9 for k in ("estimate", "lo", "hi")), (mine, theirs)
    (OUT / "six_am_solutions.json").write_text(json.dumps(res, indent=1, default=float))
    for claim in ("heat_ac_shootings", "heat_ac_heat_calls", "heat_school_out"):
        print("==", claim)
        for k, v in res["calendar"][claim].items():
            w = res["six_am"][claim][k]
            if isinstance(v, dict) and "estimate" in v:
                print(f"  {k:52s} {v['estimate']:.3f} ({v['lo']:.3f} to {v['hi']:.3f})   |   {w['estimate']:.3f} ({w['lo']:.3f} to {w['hi']:.3f})   n {v.get('days', v.get('weekdays', ''))} | {w.get('days', w.get('weekdays', ''))}")
            else:
                print(f"  {k:52s} {v}   |   {w}")


if __name__ == "__main__":
    main()
