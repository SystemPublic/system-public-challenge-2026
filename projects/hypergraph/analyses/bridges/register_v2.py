"""Registration of bridge-crz-injury-crashes-v2, a re-analysis asked for by the bridge referee
(critique/bridge-crz-injury-crashes.md). Run before any crash data are queried for v2.

Usage: python -m analyses.bridges.register_v2
Reads data/derived/bridges/composed_predictions_v2.json (analyses/bridges/compose_v2.py),
which uses link estimates only. The pre-data power figures below are computed here from the
composed prediction and assumed standard errors; they use no crash data.
"""
from __future__ import annotations

import json

import numpy as np
from scipy.stats import norm

from analyses.bridges.common import DER
from analyses.bridges.register import G_SPEED, LIT_CRASH, REGISTRANT
from concord import claims

CID = "bridge-crz-injury-crashes-v2"
C2 = json.loads((DER / "composed_predictions_v2.json").read_text())
P = C2["primary_independent"]["composed_injury_crashes_pct"]
S = C2["sensitivity_correlated"]["composed_injury_crashes_pct"]


def power_table(mu, sig):
    """For assumed endpoint SEs, the range of observed changes that would meet the bridged
    condition (|z_chain| < 1.96 and D >= 4), and the probability of meeting it if the chain
    is true (endpoint ~ N(mu, sig^2 + se^2)) or if there is no effect (N(0, se^2))."""
    out = []
    x = np.linspace(-0.4, 0.4, 80001)
    for se in (0.03, 0.035, 0.04, 0.045, 0.05):
        sc = np.sqrt(se * se + sig * sig)
        zc, zn = (x - mu) / sc, x / se
        ok = ((zn ** 2 - zc ** 2) >= 4) & (np.abs(zc) < 1.96)
        xs = x[ok]
        out.append({"se_assumed": se,
                    "bridged_if_observed_pct_between": [round(100 * (np.exp(xs.min()) - 1), 1), round(100 * (np.exp(xs.max()) - 1), 1)] if len(xs) else None,
                    "p_bridged_if_chain_true": round(float(np.trapezoid(norm.pdf(x, mu, sc) * ok, x)), 3),
                    "p_bridged_if_no_effect": round(float(np.trapezoid(norm.pdf(x, 0, se) * ok, x)), 4)})
    return out


PT = power_table(P["mean_log"], P["sd_log"])

SEEN = [
    "h9gi-nx95-298b... (fetched 12 Nov 15:31:58, for mob-speedcam-247): citywide monthly crashes and injury crashes by day of week and time band from 2019. No area split.",
    "h9gi-nx95-4c1b..., -e57b... (15:30): a handful of rows from 1-7 August 2022 to check crash_time. No area split of use.",
    "h9gi-nx95-434a..., -4c48... (16:05:32-34, for v1): 53,396 crash rows with coordinates in the box lat 40.69-40.78, lon -74.03 to -73.95, 2022 to August 2026, with injury counts. This box contains the zone and also Manhattan from 60th Street to about 79th to 86th Street, which is part of the v2 comparison area. The rows were assigned only to the zone polygon in v1; no tally of crashes north of 60th Street was made or seen. The cached file is not read by the v2 analysis: v2 uses a new query with a larger box and different fields.",
    "h9gi-nx95-3f9e... (16:05:42, for v1): citywide monthly totals of crashes, injury crashes, persons injured and killed, 2022 to August 2026.",
    "h9gi-nx95-501f... (16:05:44) and -b14f... (16:06:08, for v1): crashes and injury crashes without coordinates by year and by coded borough. Known from these: injury crashes without coordinates were 4,191 of 39,336 (2022), 3,213 of 40,473 (2023), 3,481 of 40,229 (2024) and 973 of 37,426 (2025); records with no borough numbered 12,191 to 14,093 a year in 2022-2024 and 3,173 in 2025; injury crashes coded MANHATTAN numbered 4,353, 4,640, 4,900 and 6,060, of which 233, 104, 104 and 266 lacked coordinates.",
    "The v1 result is known: injury crashes in the zone changed by +1.3% (-4.7 to +7.8) relative to the rest of the city, 2025 against 2022-2024, with a 2024 placebo of +3.8% (-5.4 to +14.0), and the zone recorded 2,581 to 2,763 injury crashes a year in 2022-2024 and 2,726 in 2025. The referee's bias scenarios (+9% and +11.5% after correction) are known.",
    "Not seen: any count of crashes in Manhattan north of 60th Street, or in the 60th-96th Street band, by month or year; any count of crashes by street-name pattern; any monthly series of coordinate coverage.",
]

REG = {
    "id": CID,
    "kind": "bridge",
    "reanalysis_of": "bridge-crz-injury-crashes",
    "critique": "critique/bridge-crz-injury-crashes.md",
    "statement": ("Re-analysis of bridge-crz-injury-crashes with a comparison area that shares the zone's geocoding regime: the change in injury crashes in the "
                  "Congestion Relief Zone relative to Manhattan north of 60th Street, 2025 against 2022-2024, is compared with the change composed from faster "
                  "speeds and fewer vehicles (mob-crz-traffic) and the speed-volume-crash link (bridge-crz-crash-link), and with no change."),
    "graph_evidence": G_SPEED,
    "literature": LIT_CRASH,
    "chain": ["mob-crz-traffic", "bridge-crz-crash-link"],
    "data_seen_before_registration": SEEN,
    "composed_prediction": {
        "scale": "percent change in monthly injury crashes, zone vs Manhattan north of 60th St, 2025 vs 2022-2024",
        "median": round(P["median"], 2), "lo": round(P["lo"], 2), "hi": round(P["hi"], 2),
        "mean_log": P["mean_log"], "sd_log": P["sd_log"],
        "speed_link": "mob-crz-traffic, CBD vs CBD Adjacent: +4.16% (1.60 to 6.79); the MTA does not publish the Adjacent boundary, and it is taken as the nearest measured stand-in for Manhattan north of 60th St",
        "volume_link": "-7.6% (-3 to -12), as in v1; no volume measure exists for the comparison area",
        "exponents": "as in v1: E_speed N(1.2, 0.5) truncated at 0; volume elasticity N(0.9, 0.2) truncated at 0",
        "sensitivity_correlated_rho_-0.5": {"median": round(S["median"], 2), "lo": round(S["lo"], 2), "hi": round(S["hi"], 2),
                                            "mean_log": S["mean_log"], "sd_log": S["sd_log"]},
        "v1_composed_for_reference": "-0.4% (-8.2 to +8.7), vs rest of city",
        "file": "data/derived/bridges/composed_predictions_v2.json",
    },
    "prediction": {
        "direction": "-",
        "magnitude": (f"Composed: {P['median']:+.1f}% ({P['lo']:+.1f} to {P['hi']:+.1f}). The registrant does not make a directional bet beyond the composition. "
                      "Knowing the v1 result, the registrant expects the v2 estimate to lie near zero and the verdict to be unsettled under rule 8."),
        "support_if": ("Verdict bridged if, in the primary estimate and at both bias bounds (B_up and B_down below): |z_chain| < 1.96, D = z_null^2 - z_chain^2 >= 4 "
                       "(PRECEDENCE rule 8), and the 2024 placebo interval includes zero. "
                       "z_chain = (b - mean_log_composed) / sqrt(se_b^2 + sd_log_composed^2); z_null = b / se_b; b is the zone-by-2025 coefficient on the log scale."),
        "refute_if": ("Verdict contested if |z_chain| >= 1.96 with the same sign in the primary estimate and at both bias bounds, and the 2024 placebo interval includes zero. "
                      "This would say the endpoint is incompatible with the composed chain, whatever its distance from zero."),
        "unsettled_if": ("Any other case: compatible with the chain but D < 4 at any of the three points; incompatible at one point but not at all three; "
                         "or the 2024 placebo interval excludes zero."),
        "no_test_if": "The crash rows cannot be fetched, or Manhattan north of 60th St has fewer than 1,000 geocoded injury crashes in any year 2022-2025.",
        "pre_data_power": {"note": ("Computed before data from the composed prediction alone. The bridged condition can be met only by an observed change of "
                                    "roughly -6% to -13%, and its probability is low even if the chain is true. An unsettled verdict is the expected result. "
                                    "The test can still refute the chain."),
                           "table": PT},
        "stance": ("Report z_chain and z_null side by side, at the primary estimate and at both bias bounds. The dashboard stance is "
                   "concord.claims.endpoint_stance(z_chain, z_null) at the primary estimate (rules 7 and 8)."),
    },
    "plan": (
        "Endpoint data: NYPD Motor Vehicle Collisions - Crashes (h9gi-nx95), queried through concord/socrata.py so that each source record keeps rowsUpdatedAt, the SoQL and the fetch time. "
        "Q1 (rows): collision_id, crash_date, latitude, longitude, borough, on_street_name, cross_street_name, off_street_name, number_of_persons_injured, number_of_persons_killed, "
        "where crash_date 2022-01-01 to 2026-08-31 and (persons injured > 0 or persons killed > 0) and latitude 40.68-40.89 and longitude -74.03 to -73.90, paged by collision_id. "
        "Q2 (coverage by record class, citywide, injury crashes): by year 2022-2025 and class, count and count without coordinates (latitude null or 0). Classes: intersection "
        "(on_street_name and cross_street_name both present), address (off_street_name present, not intersection), other. "
        "Q3 (coverage by month, citywide, injury crashes): count and count without coordinates by month, 2022-2025. Q2 and Q3 have no area split. "
        "Areas. Zone: the largest polygon of the MTA CBD geofence (srxy-5nxn, the cached copy fetched 12 Nov 16:01, as in v1). Manhattan: the union of UHF42 neighbourhoods 301-310 "
        "(data/raw/ehdp/UHF42.geojson) buffered by 0.0005 degrees, excluding points inside any non-Manhattan UHF polygon. North of 60th: Manhattan points outside every geofence polygon "
        "and north of 60th Street, using the avenue-axis projection in analyses/mobility/crz_air.py (south_of_60th). Primary comparison area: all of Manhattan north of 60th St. "
        "Secondary comparison area: Manhattan from 60th to 96th St (the projection value at 5th Ave and 96th St), a stand-in for the MTA's CBD Adjacent area, whose boundary is not published. "
        "Injury crash = persons injured > 0 or persons killed > 0. "
        "Primary model, unchanged from v1 apart from the comparison area: OLS of log monthly injury crashes on area, calendar month, year and zone x post (post from January 2025), "
        "HAC standard errors with 3 lags, 2022-01 to 2025-12, 96 area-months. Placebo: false start January 2024 on 2022-2024. "
        "Bias bounds. Let w be the zone's share of geocoded injury crashes in zone plus north area in 2022-2024 (from Q1), D_new the citywide fall in the share of injury crashes without "
        "coordinates from 2022-2024 pooled to 2025 (from Q2 totals), and e the rise in the share without coordinates among injury crashes coded MANHATTAN, 2022-2024 pooled to 2025 "
        "(from the cached v1 counts: 441 of 13,893 to 266 of 6,060, 1.22 points). Assumptions on the missing records: "
        "B0, missing records fall in zone and north area in proportion to geocoded ones (bias 0; the primary estimate). "
        "B1, records newly geocoded in 2025 are twice as frequent per crash in the zone as in the north area: r_N = D_new/(1+w), r_Z = 2 r_N, bias = log(1+r_Z) - log(1+r_N). "
        "B2, twice as frequent in the north area: r_Z = D_new/(2-w), r_N = 2 r_Z, same formula. "
        "B3, the rise e in Manhattan-coded records without coordinates falls wholly in the zone: bias = log(1 - e/w). "
        "B4, wholly in the north area: bias = -log(1 - e/(1-w)). "
        "Corrected estimate = b - bias, with se_b unchanged. B_up = B2 and B3 together (the largest upward correction); B_down = B1 and B4 together (the largest downward correction). "
        "Reported, not deciding: the extreme case in which every newly geocoded Manhattan record falls in one area (r_Z = D_new/w, r_N = 0, and the reverse). "
        "Stable-coverage restriction (secondary, not deciding). Records: a class from Q2 is stable if its share with coordinates varies by less than 2 percentage points across 2022, 2023, "
        "2024 and 2025; the primary model is re-run on Q1 rows of the stable classes only. If no class is stable, this analysis is not run and that is reported. "
        "Months: pre-period months whose citywide coverage (Q3) is within 2 points of the 2025 mean coverage; if at least 12 such months exist, the primary model is re-run with only those "
        "pre-period months; otherwise it is not run and that is reported. "
        "Other secondary results, reported and not deciding: the secondary comparison area; Poisson GLM with area x calendar month terms (quasi-Poisson scale); the composed prediction "
        "with correlated links; the v1 composed prediction (-0.4%) against the v2 endpoint; January-August 2026 added as a second post year. "
        "Outcome: claims/outcomes/bridge-crz-injury-crashes-v2.json with the Q1-Q3 source records; figure in figures/bridges/ in the style of the v1 figure. "
        "The v1 outcome is then revised through concord.claims.revise, keeping its history."
    ),
    "alternatives": [
        "Differential geocoding between the zone and the north area (bounded by B1-B4).",
        "Spillover: traffic diverted from the zone onto streets north of 60th St would raise crashes there and make the zone look better; the composition does not model the comparison area's volume.",
        "Pre-existing differential trend between the zone and the north area (2024 placebo).",
        "Other 2025 changes that differ between lower and upper Manhattan (street redesigns, enforcement, the citywide daylighting work).",
        "No effect of pricing on injury crashes, which the composed prediction lies close to (rule 8).",
    ],
    "prior": 0.05,
    "registrant": REGISTRANT,
}


if __name__ == "__main__":
    print(claims.register(REG))
    print(json.dumps(PT, indent=1))
