"""Before registration: what each heat-solutions test can detect. No dated outcome record is read.

Reads: weather and calendar; the air-conditioning table by community district; the coordinates and
jurisdiction of shooting incidents WITHOUT their dates (to count incidents per district); the count of
EMS incidents with final call type HEAT by community district and by year WITHOUT dates within the year.
Writes data/derived/heat_solutions/prereg_design.json.

1. Air conditioning and the heat slope. Model: binomial GLM of the day's events in low-AC districts
   out of the day's events in all districts, on TMAX/5 and the calendar terms. The coefficient of
   TMAX/5 is the difference between the log rate ratios per 5 C of the two groups of districts.
   Its standard error is taken from the Fisher information with the expected daily total.
   Yardstick: the difference expected if households without air conditioning carried HALF of the
   heat slope (their share of the slope proportional to their share of households), from
   slope_g = s * (0.5 + 0.5 * u_g / u), u_g the share of households without AC in group g.
2. School. Model: negative binomial GLM of weekday shootings within 42 days of the last and first day
   of classes on out-of-school, TMAX/5, a linear trend for each kind of transition, day of week, wet
   and a term for each transition. Standard error from the Fisher information at a constant mean.
3. How far a school effect could bias the heat slope of heat-shootings: the coefficient of TMAX/5 in a
   regression of summer_out on the terms of that model (omitted-variable arithmetic).
"""
from __future__ import annotations

import json
import math

import numpy as np
import pandas as pd
from patsy import dmatrix

from analyses.heat_solutions.common import CONTROLS, DER, SCHOOL_FORM, calendar, cd_table, fix_latlon, to_cd, window
from concord import socrata

SLOPE = math.log(1.146)       # heat-shootings, per 5 C
ALPHA = 0.040                 # dispersion published by heat-shootings


def resid_var_t5(d, weights):
    X = np.asarray(dmatrix(CONTROLS, d, return_type="dataframe"))
    w = np.asarray(weights, float)
    b = np.linalg.lstsq(X * np.sqrt(w)[:, None], d["t5"].values * np.sqrt(w), rcond=None)[0]
    r = d["t5"].values - X @ b
    return float((w * r * r).sum())


def binom_se(d, daily_total, p):
    """SE of the TMAX/5 coefficient in the binomial model; daily_total is the expected events per day."""
    return 1.0 / math.sqrt(p * (1 - p) * resid_var_t5(d, daily_total))


def half_carry(cd, grp, s, weights):
    """Difference of log rate ratios (group 1 minus group 0) if non-AC households carried half of slope s."""
    u = 100 - cd["ac"]
    ubar = float((u * weights).sum() / weights.sum())
    out = {}
    for g in (0, 1):
        m = grp == g
        out[g] = float((u[m] * weights[m]).sum() / weights[m].sum())
    return s * 0.5 * (out[1] - out[0]) / ubar, out, ubar


def norm_cdf(z):
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def main():
    cd = cd_table()
    cal = calendar()
    cal = cal.dropna(subset=["TMAX"])
    out = {"ac_table": {"n_districts": int(len(cd)), "ac_median": float(cd["ac"].median()),
                        "ac_mean_low": float(cd.loc[cd.low_ac == 1, "ac"].mean()), "ac_mean_high": float(cd.loc[cd.low_ac == 0, "ac"].mean()),
                        "spearman_ac_income": float(cd[["ac", "income"]].corr(method="spearman").iloc[0, 1]),
                        "low_ac_and_low_income": int(((cd.low_ac == 1) & (cd.low_income == 1)).sum()),
                        "low_ac_and_high_income": int(((cd.low_ac == 1) & (cd.low_income == 0)).sum()),
                        "high_ac_and_low_income": int(((cd.low_ac == 0) & (cd.low_income == 1)).sum())}}
    cd.to_csv(DER / "cd_table.csv", index=False)

    # shootings: coordinates and jurisdiction only, no dates
    rows, src = socrata.query_all("5ucz-vwe8", select="incident_key, max(latitude) as lat, max(longitude) as lon, max(jurisdiction_code) as jur",
                                  group="incident_key", order="incident_key")
    s = pd.DataFrame(rows)
    s[["lat", "lon"]] = s[["lat", "lon"]].astype(float)
    s = s.dropna(subset=["lat", "lon"])
    s["lat"], s["lon"] = fix_latlon(s["lat"].values, s["lon"].values)
    s["cd"] = to_cd(s["lat"].values, s["lon"].values)
    tot = s[s.cd > 0].groupby("cd").size().reindex(cd["cd"]).fillna(0).values
    cd["shootings"] = tot
    n_all = float(tot.sum())
    n_days = len(cal)
    res = {"n_incidents_with_coordinates": int(len(s)), "n_in_a_district": int(n_all), "n_days": n_days}
    for name, grp, keep in (("halves", cd["low_ac"].values, np.ones(len(cd), bool)),
                            ("terciles_bottom_vs_top", (cd["ac_tert"].values == 1).astype(int), cd["ac_tert"].values != 2),
                            ("low_income_districts_only", cd["low_ac"].values, cd["low_income"].values == 1)):
        c = cd[keep]
        g = grp[keep]
        w = c["shootings"].values
        n = float(w.sum())
        p = float(w[g == 1].sum() / n)
        se = binom_se(cal, np.full(n_days, n / n_days), p)
        hc, u, ubar = half_carry(c.reset_index(drop=True), g, SLOPE, w)
        res[name] = {"events": int(n), "share_in_low_ac": p, "se_diff_log_rr_per_5c": se, "mde_80pct": 2.8 * se,
                     "no_ac_share_low_group_pct": u[1], "no_ac_share_high_group_pct": u[0], "no_ac_share_all_pct": ubar,
                     "diff_if_no_ac_households_carry_half": hc, "diff_if_they_carry_all": 2 * hc,
                     "D_half": (hc / se) ** 2, "p_refute_if_no_difference": norm_cdf(hc / se - 1.96),
                     "p_support_if_half": norm_cdf(hc / se - 1.96)}
    jur = s["jur"].astype(str).str[:1].value_counts().to_dict()
    res["jurisdiction_counts"] = jur
    nh = float(jur.get("2", 0))
    ph = nh / len(s)
    res["housing_vs_other"] = {"share_housing": ph, "se_diff_log_rr_per_5c": binom_se(cal, np.full(n_days, len(s) / n_days), ph)}
    out["shootings_ac"] = res
    cd[["cd", "CDTACode", "ac", "income", "low_ac", "ac_tert", "low_income", "shootings"]].to_csv(DER / "design_cd_shootings.csv", index=False)

    # EMS HEAT calls: totals by district and by year
    rows, src_e = socrata.query("76xm-jjuj", select="communitydistrict, count(*) as n", where="final_call_type='HEAT'",
                                group="communitydistrict", limit=500)
    e = pd.DataFrame(rows)
    e["cd"] = pd.to_numeric(e["communitydistrict"], errors="coerce")
    e["n"] = e["n"].astype(int)
    rows, _ = socrata.query("76xm-jjuj", select="date_extract_y(incident_datetime) as y, count(*) as n", where="final_call_type='HEAT'",
                            group="y", order="y", limit=100)
    by_year = {int(r["y"]): int(r["n"]) for r in rows}
    cd["heat_calls"] = e.dropna(subset=["cd"]).groupby("cd")["n"].sum().reindex(cd["cd"]).fillna(0).values
    years = [y for y in by_year if by_year[y] > 0]
    ws = cal[(cal.month.between(5, 9)) & (cal.year >= min(years)) & (cal.year <= max(years))]
    # expected daily total proportional to the published warm-season curve of heat ED visits (4.09 per 5 C)
    lam = np.power(4.09, ws["t5"].values - ws["t5"].mean())
    eres = {"by_year": by_year, "n_total": int(e["n"].sum()), "n_in_a_district": int(cd["heat_calls"].sum()), "warm_season_days": int(len(ws))}
    for name, grp, keep in (("halves", cd["low_ac"].values, np.ones(len(cd), bool)),
                            ("low_income_districts_only", cd["low_ac"].values, cd["low_income"].values == 1)):
        c = cd[keep]
        g = grp[keep]
        w = c["heat_calls"].values
        n = float(w.sum()) * 0.9      # about nine tenths of calls fall in May to September (assumed)
        p = float(w[g == 1].sum() / w.sum())
        se = binom_se(ws, lam / lam.sum() * n, p)
        eres[name] = {"events": int(n), "share_in_low_ac": p, "se_diff_log_rr_per_5c": se, "mde_80pct": 2.8 * se}
    out["heat_calls_ac"] = eres
    cd[["cd", "CDTACode", "ac", "income", "low_ac", "low_income", "shootings", "heat_calls"]].to_csv(DER / "design_cd_counts.csv", index=False)

    # school
    full = calendar()
    sres = {}
    for half in (21, 42):
        k = window(full, half)
        X = dmatrix(SCHOOL_FORM, k, return_type="dataframe")
        for label, mu, alpha in (("all_shootings", 4.2, ALPHA), ("victims_under_18", 0.45, 0.0), ("victims_18_24", 1.8, ALPHA)):
            w = mu / (1 + alpha * mu)
            V = np.linalg.pinv(np.asarray(X).T @ np.asarray(X) * w)
            se = float(np.sqrt(V[list(X.columns).index("out"), list(X.columns).index("out")]))
            sres[f"{label}_half{half}"] = {"weekdays": int(len(k)), "days_out": int(k.out.sum()), "assumed_mean_per_day": mu, "se_log_irr": se,
                                           "mde_irr_80pct": math.exp(2.8 * se), "D_for_irr_1.10": (math.log(1.10) / se) ** 2,
                                           "D_for_irr_1.25": (math.log(1.25) / se) ** 2}
    # omitted-variable arithmetic for the heat-shootings slope
    d = cal.copy()
    X = dmatrix("t5 + " + CONTROLS, d, return_type="dataframe")
    b = np.linalg.lstsq(np.asarray(X), d["summer_out"].values, rcond=None)[0]
    delta = float(b[list(X.columns).index("t5")])
    sres["bias_arithmetic"] = {"delta_summer_out_per_t5": delta,
                               "bias_in_log_slope_if_out_raises_shootings_10pct": math.log(1.10) * delta,
                               "share_of_slope_if_10pct": math.log(1.10) * delta / SLOPE,
                               "share_of_slope_if_25pct": math.log(1.25) * delta / SLOPE,
                               "irr_out_needed_for_a_tenth_of_slope": math.exp(0.1 * SLOPE / delta) if delta > 0 else None,
                               "days_summer_out": int(d.summer_out.sum()),
                               "months_with_variation": sorted(set(d.groupby(["year", "month"]).summer_out.mean().pipe(lambda x: x[(x > 0) & (x < 1)]).index.get_level_values(1)))}
    out["school"] = sres
    (DER / "prereg_design.json").write_text(json.dumps(out, indent=1, default=float))
    print(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    main()
