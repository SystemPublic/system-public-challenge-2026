"""Outcomes of the restaurant claims, from the result files of the registered scripts.
  python analyses/restaurants/outcomes.py restaurants-nta-harshness
  python analyses/restaurants/outcomes.py restaurants-score-complaints"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from concord import claims  # noqa: E402

DER = ROOT / "data" / "derived" / "restaurants"


def harshness():
    r = json.loads((DER / "evenness_test.json").read_text())
    h, f = r["harshness"], r["frequency"]
    seeds = json.loads((DER / "evenness_seedcheck.json").read_text())
    ex = json.loads((DER / "evenness_explore.json").read_text())
    ps = [s["harshness_p"] for s in seeds]
    return {
        "id": "restaurants-nta-harshness",
        "verdict": "contested",
        "city_effect": {"label": "Between-NTA SD of the adjusted log rate ratio of critical violations per routine initial inspection (tau, method of moments)",
                        "estimate": round(h["tau_log"], 3), "lo": None, "hi": None, "scale": "SD of log rate ratio", "null": 0,
                        "n": h["n_units"], "permutation_p": round(h["p"], 4), "S_over_null_mean": round(h["S_ratio"], 3),
                        "n_ntas": h["n_ntas"], "n_restaurants": h["n_restaurants"]},
        "graph_effect": {"label": "Leinwand 2017 (Philadelphia): chain against non-chain violations per inspection", "estimate": -3.1,
                         "lo": None, "hi": None, "scale": "violations per inspection", "null": 0},
        "sources": [r["source"], {"kind": "nyc-open-data", "dataset": "9nt8-h7nd", "name": "2020 Neighborhood Tabulation Areas (NTAs)",
                                  "url": "https://data.cityofnewyork.us/d/9nt8-h7nd", "file": "data/derived/restaurants/nta2020.geojson"}],
        "prediction_scored": (f"miss. refute_if (permutation p > 0.10) is met: p = {h['p']:.3f} with 10,000 draws; with 100,000 draws and four other "
                              f"seeds p lies in {min(ps):.3f} to {max(ps):.3f}, far from the 0.10 threshold, so rule 9 does not apply. tau = {h['tau_log']:.3f}, "
                              f"below the 0.05 floor of the predicted band. After adjustment the 31 NTAs are as even as a random assignment of restaurants."),
        "settle": ("Inspector identifiers (not published) would separate inspector stringency from place; the NTA effect would then be "
                   "decomposed into inspector and restaurant parts. Restaurant size, seats and age of premises would test whether the raw "
                   "differences are restaurant mix."),
        "research_needed": [
            {"question": "Do individual NYC inspectors differ in stringency, as Jones 2004 found in Tennessee?", "data": "DOHMH inspection records with inspector id (FOIL)",
             "design": "inspector fixed effects with rotation as quasi-random assignment", "priority": "medium"},
            {"question": "Do hearings dismiss violations at different rates by neighbourhood?", "data": "OATH hearings (jz4z-kudi) joined to inspections",
             "design": "dismissal share by NTA, adjusted", "priority": "medium"},
        ],
        "figures": ["figures/restaurants/evenness_map.png"],
        "notes": (f"Raw critical violations per initial inspection range from {ex['raw_range_crit_per_initial'][0]:.2f} (Midtown-Times Square) to "
                  f"{ex['raw_range_crit_per_initial'][1]:.2f} (Chinatown-Two Bridges); unadjusted, the permutation statistic is "
                  f"{ex['initial_none']['S_ratio']:.1f} times its null mean (p < 0.001). Restaurant count alone brings it to "
                  f"{ex['initial_restaurant_count']['S_ratio']:.1f}, cuisine alone to {ex['initial_cuisine_only']['S_ratio']:.1f}, and the registered "
                  f"set to {h['S_ratio']:.2f}. The registered adjustment set accounts for the raw differences; the share due to each covariate was not separated further. "
                  f"Exploratory, not registered (its result was seen during a synthetic-outcome check of the script): routine initial "
                  f"inspections per restaurant-year, adjusted for first score band, cuisine, chain, restaurant count and new status, give p = "
                  f"{f['p']:.3f} and tau = {f['tau_log']:.3f}, detectable but small (adjusted rate ratios {ex['freq_rr_range'][0]:.2f} to "
                  f"{ex['freq_rr_range'][1]:.2f}). Also exploratory: all cycle inspections with stage as covariate, p = "
                  f"{ex['all_cycle_stage_cuisine']['p']:.3f}. Fixed source is the Underlay snapshot because the live table drops closed "
                  f"restaurants and revises recent violations (docs/underlay_drift.md)."),
    }


def complaints():
    r = json.loads((DER / "complaints_test.json").read_text())
    p, q, rat, d, cond = r["primary"], r["placebo_noise"], r["ratio_fp_over_noise"], r["discrimination"], r["conditions"]
    if cond["refute_if_met"]:
        verdict = "contested"
    elif cond["support_if_met"] and not cond["placebo_meets_support"] and cond["rule11_discriminates"]:
        verdict = "confirmed"
    else:
        verdict = "unsettled"
    sec = r["secondary"]
    return {
        "id": "restaurants-score-complaints",
        "verdict": verdict,
        "city_effect": {"label": "IRR of 311 Food Poisoning complaints at the lot in the 365 days after a routine initial inspection, score >= 14 against 0-13",
                        "estimate": round(p["irr"], 3), "lo": round(p["lo"], 3), "hi": round(p["hi"], 3), "scale": "incidence rate ratio", "null": 1,
                        "n": p["n"], "events": p["events"]},
        "graph_effect": {"label": "Firestone 2020: protection-from-contamination violation and outbreak level", "estimate": 4.92, "lo": 1.57, "hi": 15.39,
                         "scale": "odds ratio", "null": 1},
        "sources": r["sources"],
        "prediction_scored": (f"Primary IRR {p['irr']:.2f} ({p['lo']:.2f} to {p['hi']:.2f}); placebo (Noise - Commercial) IRR {q['irr']:.2f} "
                              f"({q['lo']:.2f} to {q['hi']:.2f}); ratio {rat['irr_ratio']:.2f} ({rat['lo']:.2f} to {rat['hi']:.2f}). "
                              f"support_if met: {cond['support_if_met']}; refute_if met: {cond['refute_if_met']}; placebo meets support: "
                              f"{cond['placebo_meets_support']}; D against placebo {d['D_placebo']:.1f}, against no effect {d['D_null']:.1f}."),
        "settle": "Complaints linked to restaurants by name and address in the 311 text, and laboratory-confirmed outbreak attributions (DOHMH Bureau of Communicable Disease), would replace a noisy, self-reported outcome.",
        "research_needed": [
            {"question": "Do routine inspection results predict confirmed restaurant outbreaks in NYC?", "data": "DOHMH outbreak investigations by restaurant (not public)",
             "design": "matched case-control as Irwin 1989, with the last routine inspection before the outbreak", "priority": "high"},
            {"question": "Do Yelp illness reviews track inspection results better than 311 complaints?", "data": "DOHMH Yelp-classifier output (Effland 2018)",
             "design": "the registered design with Yelp reports as outcome", "priority": "medium"},
        ],
        "figures": [],
        "notes": (f"Secondary, deciding nothing: C-range against A IRR {sec['C_vs_A']['irr']:.2f} ({sec['C_vs_A']['lo']:.2f}-{sec['C_vs_A']['hi']:.2f}); "
                  f"per 10 points {sec['per_10_points']['irr']:.2f} ({sec['per_10_points']['lo']:.2f}-{sec['per_10_points']['hi']:.2f}); NTA fixed effects "
                  f"{sec['nta_fe']['irr']:.2f} ({sec['nta_fe']['lo']:.2f}-{sec['nta_fe']['hi']:.2f}); Manhattan only {sec['manhattan']['irr']:.2f} "
                  f"({sec['manhattan']['lo']:.2f}-{sec['manhattan']['hi']:.2f}); complaints in the 365 days before the inspection "
                  f"{sec['pre_window']['irr']:.2f} ({sec['pre_window']['lo']:.2f}-{sec['pre_window']['hi']:.2f}). Cohort {r['cohort']['n']} restaurants, "
                  f"{r['cohort']['fp_events']} food-poisoning and {r['cohort']['noise_events']} noise complaints. Pearson dispersion of the primary model "
                  f"{p['pearson_dispersion']}. The live table omits closed restaurants, which biases towards 1."),
    }


if __name__ == "__main__":
    fn = {"restaurants-nta-harshness": harshness, "restaurants-score-complaints": complaints}[sys.argv[1]]
    print(claims.outcome(fn()))
