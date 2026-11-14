"""Registrations for the bridge claims. Run before the endpoint data are queried.

Usage: python -m analyses.bridges.register <id> [<id> ...]
The composed predictions come from analyses/bridges/compose.py
(data/derived/bridges/composed_predictions.json), which reads no endpoint data.
Graph abstracts read in PubMed: data/derived/bridges/abstracts_graph.txt.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from concord import claims
from analyses.bridges.common import DER

REGISTRANT = "Claude (bridges agent), for Jeff Vernon"
C = json.loads((DER / "composed_predictions.json").read_text())
B1 = C["bridge-crz-injury-crashes"]["composed_injury_crashes_pct"]
B1F = C["bridge-crz-injury-crashes"]["composed_fatal_pct"]
B2 = C["bridge-heat-shootings-ems"]["composed_irr_per5C"]

G_SPEED = [
    {"association_id": "(PMID 26759927)", "concepts": ["speed", "pedestrian collision"], "n_findings": 1, "n_studies": 1,
     "direction": "+", "summary": "Rothman et al. 2016 (Toronto, child pedestrian-motor vehicle collisions): higher speed roads IRR 1.27 (1.13 to 1.44). Abstract read.",
     "pubmed_ids": [26759927]},
    {"association_id": "(PMID 21399547)", "concepts": ["speed", "injury severity"], "n_findings": 1, "n_studies": 1,
     "direction": "+", "summary": "Moped and scooter crashes: driving speeds above 20 mph OR 2.02 (1.73 to 2.36) for severe or lethal injury. Abstract read.",
     "pubmed_ids": [21399547]},
    {"association_id": "(PMID 23411678)", "concepts": ["motor vehicle speed", "cyclist injury"], "n_findings": 1, "n_studies": 1,
     "direction": "+", "summary": "Teschke et al. 2012 (Toronto and Vancouver cyclists, case-crossover): motor vehicle speeds below 30 km/h adjusted OR 0.52 (0.29 to 0.92) for injury. Abstract read.",
     "pubmed_ids": [23411678]},
    {"association_id": "(search)", "concepts": ["traffic volume", "crash"], "n_findings": 0, "n_studies": 0, "direction": "0",
     "summary": "No finding in the graph links traffic volume, vehicle-miles or congestion to crashes or injuries. The graph holds no power-model (Nilsson, Elvik) findings and no road-pricing findings (see docs/mobility.md).",
     "pubmed_ids": []},
]

LIT_CRASH = [
    {"citation": "Elvik R (2009). The Power Model of the relationship between speed and road safety: update and new analyses. TOI Report 1034/2009, Oslo.",
     "doi": None, "finding": "Exponents for urban and residential roads: 1.2 for injury accidents, 1.4 for injured persons, 2.6 for fatal accidents, 3.0 for persons killed (rural: 1.6, 2.2, 4.1, 4.6). The urban estimates rest on few studies (summary by ONISR, 14 May 2014)."},
    {"citation": "Nilsson G (2004). Traffic safety dimensions and the Power Model to describe the effect of speed on safety. Lund Bulletin 221.",
     "doi": None, "finding": "Exponent 2 for injury accidents, 3 for fatal and serious, 4 for fatal accidents."},
    {"citation": "Elvik R (2013). A re-parameterisation of the Power Model of the relationship between the speed of traffic and the number of accidents and accident victims. Accident Analysis and Prevention 50:854-860.",
     "doi": "10.1016/j.aap.2012.07.012", "finding": "Exponential form; the effective exponent depends on the initial speed and is lower at low speeds."},
    {"citation": "Green CP, Heywood JS, Navarro M (2016). Traffic accidents and the London congestion charge. Journal of Public Economics 133:11-22.",
     "doi": "10.1016/j.jpubeco.2015.10.005", "finding": "London's charge (2003), with network speeds of 8.6 mph before it and vehicle-km in the zone down about 12 to 34 percent, reduced accidents in the zone by roughly 38 to 40 percent and serious-and-fatal accidents by 46 a year, against 20 British cities. The authors note that higher speeds could raise severity in theory; they found declines in serious and fatal accidents."},
]

REGS = {}

REGS["bridge-crz-crash-link"] = {
    "id": "bridge-crz-crash-link",
    "kind": "bridge",
    "statement": "Research link for the congestion-pricing bridge: on urban roads, injury crashes change with mean speed as (v1/v0)^E with E about 1.2 (Elvik 2009), and with traffic volume with an elasticity of about 0.9.",
    "graph_evidence": G_SPEED,
    "literature": LIT_CRASH,
    "prediction": {"direction": "+",
                   "magnitude": "E_speed for injury crashes 1.2 (drawn as N(1.2, 0.5), truncated at 0); E_speed for fatal crashes 2.6 (N(2.6, 0.8)); volume elasticity 0.9 (N(0.9, 0.2)).",
                   "support_if": "Not testable with city data apart from the endpoint of bridge-crz-injury-crashes; this link is tested only through that endpoint.",
                   "refute_if": "As above."},
    "plan": "No separate city test. The link's distributions enter analyses/bridges/compose.py. Its outcome will be no_test, with the literature values as graph_effect.",
    "alternatives": ["At network speeds of 8 to 9 mph, the power model may not apply: crash risk in congested streets depends on conflicts (turns, double parking, pedestrians crossing between stopped cars) more than on speed.",
                     "The volume elasticity may exceed 1 in congested networks (London's accident decline was about three times its vehicle-km decline)."],
    "prior": None,
    "registrant": REGISTRANT,
    "chain": ["bridge-crz-crash-link"],
}

REGS["bridge-crz-injury-crashes"] = {
    "id": "bridge-crz-injury-crashes",
    "kind": "bridge",
    "statement": "Composed from faster speeds (mob-crz-traffic) and fewer vehicles in the Congestion Relief Zone, with the research link between speed, volume and crashes (bridge-crz-crash-link), the predicted change in injury crashes in the zone relative to the rest of the city in 2025 against 2022-2024 is the endpoint observed in the NYPD crash records.",
    "graph_evidence": G_SPEED,
    "literature": LIT_CRASH,
    "chain": ["mob-crz-traffic", "bridge-crz-crash-link"],
    "composed_prediction": {
        "scale": "percent change in monthly injury crashes, zone vs rest of city, 2025 vs 2022-2024",
        "median": round(B1["median"], 2), "lo": round(B1["lo"], 2), "hi": round(B1["hi"], 2),
        "mean_log": B1["mean_log"], "sd_log": B1["sd_log"],
        "fatal_crashes_median": round(B1F["median"], 2), "fatal_lo": round(B1F["lo"], 2), "fatal_hi": round(B1F["hi"], 2),
        "file": "data/derived/bridges/composed_predictions.json",
        "speed_term_pct": "+6.7 (+1.4 to +15.0)", "volume_term_pct": "-6.7 (-12.4 to -2.3)",
    },
    "prediction": {
        "direction": "-",
        "magnitude": f"Composed: {B1['median']:+.1f}% ({B1['lo']:+.1f} to {B1['hi']:+.1f}). The speed term (+6.7%) and the volume term (-6.7%) nearly cancel. The registrant's directional bet is negative, between -2% and -15%. Reasons: (1) the power model was fitted to speed changes on roads that are not congested, and Elvik (2013) finds lower effective exponents at low initial speeds, so the speed term is probably overstated at 8 to 9 mph; (2) London's charge, with the same pre-charge network speed (8.6 mph), reduced accidents far more than its volume change alone predicts; (3) the registrant recalls, without having checked them, statements by the MTA and the city in 2025 that traffic injuries in the zone fell. Persons killed: composed +7% (-4 to +23), too few deaths in the zone to test.",
        "support_if": "Endpoint compatible with the chain: with D = log(observed ratio) - mean_log(composed) and SE = sqrt(se_observed^2 + sd_log(composed)^2), |D| < 1.96 SE, and the 2024 placebo interval includes zero. Verdict confirmed.",
        "refute_if": "|D| >= 1.96 SE with the 2024 placebo interval including zero: the endpoint is incompatible with the composed chain. Verdict contested.",
        "unsettled_if": "The 2024 placebo (false start January 2024, data 2022-2024) has an interval that excludes zero, so the zone had a pre-existing differential trend that the design cannot separate.",
        "directional_bet": "Scored separately in prediction_scored: hit if the observed interval lies below zero, miss if above zero, partial otherwise.",
    },
    "plan": "Endpoint: NYPD Motor Vehicle Collisions - Crashes (h9gi-nx95), crash_date 2022-01-01 to 2025-12-31. Zone: the largest polygon of the MTA CBD geofence (data.ny.gov srxy-5nxn), which is the tolled zone without the FDR Drive and West Side Highway strips (the other six polygons). Crash rows with coordinates inside the bounding box lat 40.69-40.78, lon -74.03 to -73.95 are fetched and assigned by point in polygon; citywide monthly totals are fetched for crashes with valid coordinates (lat 40.45-40.95, lon -74.30 to -73.65); rest of city = city minus zone. Injury crash = persons injured > 0 or persons killed > 0. Model as in mob-crz-traffic: OLS of log monthly count on area, calendar month, year and zone x post (post from January 2025), HAC standard errors with 3 lags, 96 area-months. Placebo: false start January 2024 on 2022-2024. Secondary, reported but not deciding: Poisson GLM of the same; persons injured; pedestrians plus cyclists injured; all crashes; persons killed (Poisson, zone vs rest); zone including the excluded highway polygons; January-August 2026 added as a second post year.",
    "alternatives": [
        "Pre-existing differential trend in the zone (tested by the 2024 placebo).",
        "Changes in crash reporting or geocoding that differ between Manhattan and the rest of the city (share of crashes without coordinates is reported by year).",
        "Changes in pedestrian and cyclist volumes in the zone after pricing (more walking and cycling would raise exposure).",
        "Spillover of traffic to streets just outside the zone, which would bias the rest-of-city comparison only slightly because the rest of the city is large.",
        "Other 2025 changes specific to Manhattan below 60th Street (enforcement, street redesigns, the 2025 citywide speed-limit and daylighting work).",
    ],
    "prior": 0.45,
    "registrant": REGISTRANT,
}

REGS["bridge-shot-ems-link"] = {
    "id": "bridge-shot-ems-link",
    "kind": "bridge",
    "statement": "Second link of the heat-violence bridge: FDNY EMS dispatches with initial call type SHOT rise with the day's NYPD shooting incidents, by about one dispatch per incident.",
    "graph_evidence": [
        {"association_id": "(PMID 33838402)", "concepts": ["firearm injury", "emergency department visit"], "n_findings": 1, "n_studies": 1, "direction": "+",
         "summary": "Kentucky counties: firearm-associated ED visits correlate with opioid overdose ED visits (rho 0.29). The graph's only finding naming firearm ED visits as a measured outcome; it establishes the variable, not the link.", "pubmed_ids": [33838402]},
        {"association_id": "(search)", "concepts": ["gun violence", "emergency medical services"], "n_findings": 0, "n_studies": 0, "direction": "0",
         "summary": "No graph finding links shootings to EMS dispatch or ED volume as a count relationship. The link rests on the structure of the records: a person shot in NYC is normally reached by an ambulance.", "pubmed_ids": []},
    ],
    "literature": [],
    "prediction": {"direction": "+",
                   "magnitude": "0.6 to 1.6 additional SHOT dispatches per NYPD shooting incident on the same day.",
                   "support_if": "Coefficient between 0.6 and 1.6 and its interval excludes zero.",
                   "refute_if": "Interval entirely below 0.6 or entirely above 1.6."},
    "plan": "Daily counts 2006-01-01 to 2026-08-31 of FDNY EMS Incident Dispatch Data (76xm-jjuj) with initial_call_type = 'SHOT', by date of incident_datetime; NYPD incidents per day as in heat-shootings. OLS of daily SHOT dispatches on NYPD incidents, day of week, month, year and holiday, HAC 7 lags. This uses the endpoint dataset's daily levels but not its relation to temperature.",
    "alternatives": ["Many SHOT dispatches are reports of shots fired with no victim, so the intercept and the noise are large.",
                     "Multiple callers can create separate EMS incidents for one shooting."],
    "prior": 0.7,
    "registrant": REGISTRANT,
    "chain": ["bridge-shot-ems-link"],
}

REGS["bridge-heat-shootings-ems"] = {
    "id": "bridge-heat-shootings-ems",
    "kind": "bridge",
    "statement": "Composed from heat and shootings (heat-shootings, NYPD) and the share of EMS gunshot dispatches that are shooting victims (bridge-shot-ems-link), daily FDNY EMS dispatches for gunshot wounds rise with the day's maximum temperature by the composed rate ratio.",
    "graph_evidence": [
        {"relationship_id": "4FaXcuNJRt|rULjCt1BqH", "concepts": ["temperature", "injury"], "n_findings": 4, "n_studies": 3, "direction": "+",
         "summary": "Girma et al. 2023, NYC ED visits 2005-2011: intentional injury among 20-25 year olds OR 1.54 (1.28 to 1.85) for daily minimum 77 F vs 48 F. Used for direction only; it is an ED measure, not EMS, and not firearm-specific.", "pubmed_ids": [37448837]},
    ],
    "literature": [{"citation": "Reeping PM, Hemenway D (2020). The association between weather and the number of daily shootings in Chicago (2012-2016). Injury Epidemiology 7:31.",
                    "doi": "10.1186/s40621-020-00260-3", "finding": "Shootings +34.0% (weekdays) and +41.6% (weekends) per 10 C."}],
    "chain": ["heat-shootings", "bridge-shot-ems-link"],
    "composed_prediction": {"scale": "IRR per 5 C of daily maximum temperature, Central Park",
                            "median": round(B2["median"], 4), "lo": round(B2["lo"], 4), "hi": round(B2["hi"], 4),
                            "mean_log": B2["mean_log"], "sd_log": B2["sd_log"],
                            "file": "data/derived/bridges/composed_predictions.json"},
    "prediction": {
        "direction": "+",
        "magnitude": f"Composed IRR {B2['median']:.3f} ({B2['lo']:.3f} to {B2['hi']:.3f}) per 5 C. Below the shootings IRR (1.146) because victim dispatches are only 25 to 50 percent of SHOT dispatches (NYPD recorded 974 shooting incidents in 2023; SHOT dispatches numbered 3,159 that year, a level seen before registration) and the other dispatches are assumed to follow temperature less, between not at all and as much as shootings.",
        "support_if": "With D = log(observed IRR) - mean_log(composed) and SE = sqrt(se_observed^2 + sd_log(composed)^2), |D| < 1.96 SE. Verdict confirmed.",
        "refute_if": "|D| >= 1.96 SE. Verdict contested. An observed IRR above the composed range would mean that the non-victim dispatches follow heat more than shootings do; below it, that the chain overstates.",
    },
    "plan": "Daily counts 2006-01-01 to 2026-08-31 of 76xm-jjuj with initial_call_type = 'SHOT'. Weather and calendar terms built exactly as in analyses/heat/shootings.py (Central Park TMAX/5, day of week, month, year, holiday, rain >= 1 mm). Negative binomial GLM, alpha by ML, HC0 errors. Secondary, reported but not deciding: warm season May-September; 2006-2019 only; STAB dispatches as a contrast outside the chain; SHOT plus T-SHOT.",
    "alternatives": ["Fireworks around 4 July are reported as shots; holidays are in the model, and the warm-season sensitivity checks the rest.",
                     "EMS call-type coding changed over the period; year terms absorb level changes but not changes in seasonal coding.",
                     "Heat raises outdoor presence and hence the number of people who report shots, independent of shootings."],
    "prior": 0.6,
    "registrant": REGISTRANT,
}


if __name__ == "__main__":
    for cid in sys.argv[1:]:
        print(claims.register(REGS[cid]))
