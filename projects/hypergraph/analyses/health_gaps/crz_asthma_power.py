"""Power of a before-and-after test of the congestion toll on asthma emergency department visits.

Uses only pre-toll data (EHDP annual asthma ED counts by UHF42, 2005-2023) to measure how much a
zone-minus-rest difference in differences moves from year to year without any toll, and compares
that noise with the change the graph's concentration-response findings predict from the measured
change in NO2 and PM2.5 (claim mob-crz-air-nyccas). No post-toll health data are read; none are public.
Writes data/derived/health_gaps/crz_asthma_power.json.
"""
from __future__ import annotations
import json
import numpy as np
from analyses.mobility import ehdp
from analyses.health_gaps.common import DER

ZONE = [306, 307, 308, 309, 310]
MANH = [301, 302, 303, 304, 305, 306, 307, 308, 309, 310]
PPB_TO_UG = 1.88  # NO2 at 25 C, 1 atm

# measured air change, mob-crz-air-nyccas outcome (DiD 2025 vs 2021-24, percent, placebo-in-space interval)
NO2_DID = (0.9, -2.23, 4.21)
NO2_ZONE_PPB = 20.5  # zone mean 2024-25
# concentration-response, from the registrations of mob-asthma-pollution (graph + literature)
CR = {
    "short_term_Zheng2015_NO2": (1.018, 10.0),   # RR per 10 ug/m3, asthma ED/admissions, time series
    "long_term_Khreis2017_NO2": (1.05, 4.0),     # RR per 4 ug/m3, asthma incidence (upper bound use)
    "graph_median_ratio_NO2": (1.16, 18.8),      # graph median ratio 1.16, read per 10 ppb (18.8 ug/m3), mixed designs
}


def series(ind, meas):
    d = ehdp.measure(ind, meas, "UHF42")
    d = d[d["period"].str.fullmatch(r"\d{4}")].copy()
    d["year"] = d["period"].astype(int)
    return d.pivot_table(index="year", columns="GeoID", values="Value")


def did_noise(w):
    rest = [c for c in w.columns if c not in MANH and c < 600]
    z = np.log(w[ZONE].sum(axis=1)) - np.log(w[rest].sum(axis=1))
    diffs = z.diff().dropna()
    return z, diffs


def main():
    out = {"groups": {}, "predictions": {}}
    for label, ind, meas in [("age 5-17", 2379, 1195), ("adults", 2380, 1197), ("age 0-4", 2048, 459)]:
        try:
            w = series(ind, meas)
        except Exception as e:
            out["groups"][label] = {"error": str(e)}
            continue
        z, diffs = did_noise(w)
        noncovid = diffs[[y for y in diffs.index if y not in (2020, 2021)]]
        zone_n = w[ZONE].sum(axis=1)
        # one post year against a mean of four pre years: var = s^2 * (1 + 1/4) for level noise;
        # we use the observed sd of one-year changes as the per-year standard error of a DiD.
        se = float(np.std(diffs, ddof=1)) if len(diffs) > 1 else None
        se_nc = float(np.std(noncovid, ddof=1)) if len(noncovid) > 1 else None
        pois = float(np.sqrt(1 / zone_n.iloc[-1] * 2)) if len(zone_n) else None
        out["groups"][label] = {
            "years": [int(y) for y in w.index], "zone_counts": {int(k): float(v) for k, v in zone_n.items()},
            "log_ratio_zone_rest": {int(k): round(float(v), 4) for k, v in z.items()},
            "one_year_change": {int(k): round(float(v), 4) for k, v in diffs.items()},
            "sd_one_year_change_all": se, "sd_one_year_change_excl_2020_21": se_nc,
            "poisson_floor_se": pois,
        }
    # predicted changes
    d_ppb = [NO2_ZONE_PPB * x / 100 for x in NO2_DID]
    scen = {"measured": d_ppb, "registered_best_case_-10pct": [NO2_ZONE_PPB * -0.10] * 3,
            "registered_mid_-5pct": [NO2_ZONE_PPB * -0.05] * 3}
    for sname, dp in scen.items():
        for cname, (rr, per) in CR.items():
            pct = [100 * (rr ** (x * PPB_TO_UG / per) - 1) for x in dp]
            out["predictions"][f"{sname}|{cname}"] = {"delta_no2_ppb": [round(x, 3) for x in dp],
                                                      "pct_change_asthma_ed": [round(x, 3) for x in pct]}
    # discrimination: D = (pred/se)^2, MDE80 = 2.8 se
    ref = out["groups"].get("age 5-17", {})
    se_ref = ref.get("sd_one_year_change_excl_2020_21") or ref.get("sd_one_year_change_all")
    summ = {}
    for k, v in out["predictions"].items():
        p = v["pct_change_asthma_ed"][0] / 100
        summ[k] = {"pred_pct": v["pct_change_asthma_ed"][0], "D_vs_null": round((p / se_ref) ** 2, 4)}
    out["discrimination"] = {"se_used_log": se_ref, "mde80_pct": round(100 * 2.8 * se_ref, 1), "by_scenario": summ}
    (DER / "crz_asthma_power.json").write_text(json.dumps(out, indent=1))
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk.startswith('sd') or kk == 'zone_counts' or kk=='poisson_floor_se'} for k, v in out["groups"].items()}, indent=1))
    print(json.dumps(out["discrimination"], indent=1))


if __name__ == "__main__":
    main()
