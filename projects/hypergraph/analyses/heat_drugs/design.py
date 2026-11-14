"""Before any registration: can a New York test of heat x antipsychotic prescribing discriminate? No dated outcome
record is read.

Reads: Central Park weather (concord.noaa); the ZIP exposure table from exposure.py; the count of EMS incidents of
the psychiatric call types (EDP family) and of HEAT by ZIP code WITHOUT dates; the count of EDP-family incidents
by year WITHOUT dates within the year. Writes data/derived/heat_drugs/prereg_design.json.

Design examined (A). Warm-season days, May to September 2006-2025. Outcome: the day's EDP-family calls in the ZIP codes
in the top third of antipsychotic share of Part D claims, out of the day's EDP-family calls in the top and bottom
thirds. Model: binomial GLM on hot (Central Park TMAX >= 32.2 C, 90 F) + C(dow) + C(month) + C(year) + hol + wet.
The coefficient of hot is the difference between the hot-day log rate ratios of the two thirds. Its standard error
is taken from the Fisher information with the expected daily total (no overdispersion, which favours the test).

Yardstick. Group hot-day rate ratio RR_g = (1 - f_g) R0 + f_g R1, where f_g is the share of the group's EDP calls
made by or for people taking an antipsychotic, R1 their hot-day rate ratio and R0 everyone else's. The predicted
difference is ln(RR_top / RR_bottom). f_g is set to f_bar * a_g / a_bar, with a_g the call-weighted antipsychotic
share of claims in the group: that assumes prescriber location stands in fully for where patients live, which
favours the test. Scenarios:
  central   R0 = 1.08 (any mental-health ED visit on extreme-heat days), R1 = 1.05 (schizophrenia), Nori-Sarma 2022;
            f_bar = 0.35.
  generous  R0 = 1.08, R1 = 1 + 3.07 * 0.08 = 1.246 (the excess tripled, after the schizophrenia odds ratio of
            Lee 2023 in the 2021 British Columbia heat dome); f_bar = 0.35.
  extreme   as generous with f_bar = 0.5 and R1 = 1 + 5 * 0.08.
Design (B). HEAT calls, the share in the top third against the bottom third, cross-sectional. Users' rate ratio for
heat-related hospitalisation 1.37 (antipsychotics, Layton 2020); share of residents taking an antipsychotic e_g =
e_bar * a_g / a_bar with e_bar = 0.015 (generous: 0.03).
D = (predicted / SE)^2 under rule 8; a test is registered only if D >= 4 under the central scenario.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from patsy import dmatrix

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from analyses.heat.common import holidays  # noqa: E402
from concord import noaa, socrata  # noqa: E402

DER = ROOT / "data/derived/heat_drugs"
EDP = ["EDP", "EDPC", "EDPM", "EDPT", "EDPE", "EDPW", "T-EDP"]
CONTROLS = "C(dow) + C(month) + C(year) + hol + wet"
HOT = 32.2


def calendar():
    w, src = noaa.daily("central_park")
    idx = pd.date_range("2006-01-01", "2025-12-31", freq="D")
    d = pd.DataFrame(index=idx).join(w[["TMAX", "PRCP"]])
    d = d[d.index.month.isin([5, 6, 7, 8, 9])].dropna(subset=["TMAX"])
    d["dow"], d["month"], d["year"] = d.index.day_of_week, d.index.month, d.index.year
    d["hol"] = d.index.isin(holidays("2006-01-01", "2025-12-31")).astype(int)
    d["wet"] = (d["PRCP"].fillna(0) >= 1.0).astype(int)
    d["hot"] = (d["TMAX"] >= HOT).astype(float)
    return d, src


def resid_var(d, col, weights):
    X = np.asarray(dmatrix(CONTROLS, d, return_type="dataframe"))
    w = np.asarray(weights, float)
    b = np.linalg.lstsq(X * np.sqrt(w)[:, None], d[col].values * np.sqrt(w), rcond=None)[0]
    r = d[col].values - X @ b
    return float((w * r * r).sum())


def main():
    d, wsrc = calendar()
    z = pd.read_csv(DER / "zip_exposure.csv", dtype={"zip": str})
    z = z[(z["all_clms"] >= 1000)].copy()
    where_edp = "final_call_type in(" + ",".join(f"'{c}'" for c in EDP) + ")"
    rows, s1 = socrata.query("76xm-jjuj", select="zipcode, count(*) as n", where=where_edp, group="zipcode", order="zipcode", limit=5000)
    edp = pd.Series({r.get("zipcode"): int(r["n"]) for r in rows if r.get("zipcode")})
    rows, s2 = socrata.query("76xm-jjuj", select="zipcode, count(*) as n", where="final_call_type='HEAT'", group="zipcode", order="zipcode", limit=5000)
    heat = pd.Series({r.get("zipcode"): int(r["n"]) for r in rows if r.get("zipcode")})
    rows, s3 = socrata.query("76xm-jjuj", select="date_extract_y(incident_datetime) as y, count(*) as n", where=where_edp,
                             group="y", order="y", limit=100)
    by_year = {int(r["y"]): int(r["n"]) for r in rows}
    z["edp"] = z["zip"].map(edp).fillna(0)
    z["heat"] = z["zip"].map(heat).fillna(0)
    z = z[z["edp"] > 0].copy()
    z["third"] = pd.qcut(z["ap_share"].rank(method="first"), 3, labels=[1, 2, 3]).astype(int)
    g = z.groupby("third").apply(lambda t: pd.Series({
        "zips": len(t), "edp": t["edp"].sum(), "heat": t["heat"].sum(),
        "ap_share_callweighted": float((t["ap_share"] * t["edp"]).sum() / t["edp"].sum()),
        "ap_share_median": float(t["ap_share"].median())}))
    a_bar = float((z["ap_share"] * z["edp"]).sum() / z["edp"].sum())
    a_lo, a_hi = g.loc[1, "ap_share_callweighted"], g.loc[3, "ap_share_callweighted"]
    p = g.loc[3, "edp"] / (g.loc[3, "edp"] + g.loc[1, "edp"])
    share_tb = (g.loc[3, "edp"] + g.loc[1, "edp"]) / z["edp"].sum()
    # expected daily total of EDP calls in the two thirds, by year (warm-season days at the year's mean rate)
    d["total"] = [by_year.get(y, np.nan) / 365.25 * share_tb for y in d["year"]]
    d = d.dropna(subset=["total"])
    se = 1.0 / math.sqrt(p * (1 - p) * resid_var(d, "hot", d["total"]))
    scen = {}
    for name, R0, R1, fbar in (("central", 1.08, 1.05, 0.35), ("generous", 1.08, 1 + 3.07 * 0.08, 0.35),
                               ("extreme", 1.08, 1.40, 0.5)):
        f_hi, f_lo = min(1, fbar * a_hi / a_bar), min(1, fbar * a_lo / a_bar)
        delta = math.log(((1 - f_hi) * R0 + f_hi * R1) / ((1 - f_lo) * R0 + f_lo * R1))
        scen[name] = {"R0": R0, "R1": R1, "f_bar": fbar, "f_top": f_hi, "f_bottom": f_lo, "predicted": delta,
                      "D": (delta / se) ** 2}
    # design B: HEAT calls, cross-sectional share
    hb = {}
    n_hi, n_lo = g.loc[3, "heat"], g.loc[1, "heat"]
    se_b = math.sqrt(1 / n_hi + 1 / n_lo) if n_hi and n_lo else None
    for name, ebar in (("central", 0.015), ("generous", 0.03)):
        e_hi, e_lo = ebar * a_hi / a_bar, ebar * a_lo / a_bar
        delta = math.log((1 + 0.37 * e_hi) / (1 + 0.37 * e_lo))
        hb[name] = {"e_top": e_hi, "e_bottom": e_lo, "predicted": delta, "D": (delta / se_b) ** 2 if se_b else None}
    out = {"hot_threshold_C": HOT, "n_warm_days": int(len(d)), "n_hot_days": int(d["hot"].sum()),
           "zips_used": int(len(z)), "thirds": g.reset_index().to_dict(orient="records"), "a_bar": a_bar,
           "p_top_of_top_plus_bottom": p, "edp_calls_by_year": by_year,
           "design_A_edp": {"se": se, "scenarios": scen},
           "design_B_heat": {"se": se_b, "heat_calls_top": n_hi, "heat_calls_bottom": n_lo, "scenarios": hb},
           "sources": [wsrc, s1, s2, s3]}
    (DER / "prereg_design.json").write_text(json.dumps(out, indent=1, default=float))
    print(json.dumps({k: out[k] for k in ("n_hot_days", "zips_used", "a_bar", "p_top_of_top_plus_bottom",
                                          "design_A_edp", "design_B_heat")}, indent=1, default=float))
    print(g)


if __name__ == "__main__":
    main()
