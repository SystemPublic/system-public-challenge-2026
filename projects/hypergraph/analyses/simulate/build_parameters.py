"""Write data/derived/simulate/parameters.json, the only input of the simulator (sim/).

Each parameter has a central value, a low and a high bound, a distribution, a source type and a source:
  a  estimated in this project (a claim outcome, or a fit in analyses/simulate/)
  b  a finding in the System Public Graph, read against its PubMed abstract
  c  an assumption, with a wide range
Distributions: 'uniform' between lo and hi; 'loguniform' between lo and hi; 'normal' with lo and hi
the 2.5% and 97.5% points. No draw is truncated, and the central value of every parameter is the
median of its draws (checked here and by `python -m sim check`). A range crosses zero wherever the
evidence does not fix the sign of the parameter; the field `sign` says which case applies.
Baselines by weekday and band are measured means for non-holiday weekdays of 2025.

Measured values of the congestion analysis are loaded from data/derived/congestion/parameters.json
through the table CONGESTION_MAP below, and from nowhere else. Each row names the entry of that
file, the claim or source it comes from, the simulator quantity it sets and the transformation.
A row whose entry is missing stops the build. The sha256 of the congestion file and every value
loaded are written into meta, so a later change of that file is detected by `python -m sim check`
and cannot change the simulator's results without a rebuild.

Run: python -m analyses.simulate.build_parameters
"""
from __future__ import annotations

import hashlib
import json
import math
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DER = ROOT / "data" / "derived" / "simulate"
CONG = ROOT / "data" / "derived" / "congestion" / "parameters.json"

# (entry in the congestion file, its source there, simulator quantity it sets, how it is used)
CONGESTION_MAP = [
    ("toll_peak_car_ezpass", "official", "current_toll.am, current_toll.mid, current_toll.pm",
     "the value, dollars"),
    ("toll_overnight_car_ezpass", "official", "current_toll.night", "the value, dollars"),
    ("toll_phase2_peak_car", "official", "constants.phase2_peak_toll (the uniform scenario)", "the value, dollars"),
    ("vmt_change_crz_2025_vs_2024_pct_low", "mob-crz-traffic", "k_toll.lo",
     "k = -ln(1 - r / (1 - s)) / peak toll, r the fall in vehicle-miles, s the taxi and for-hire share of entries"),
    ("vmt_change_crz_2025_vs_2024_pct_high", "mob-crz-traffic", "k_toll.hi", "the same"),
    ("crz_entries_share_taxi_fhv_pct", "exploratory", "k_toll.lo, k_toll.hi", "s in the formula above"),
    ("elasticity_ems_travel_time_to_taxi_speed", "bridge-crz-ems-travel", "theta_ems.hi",
     "its upper bound is the upper bound of theta_ems; the lower bound is that of the 2025 day-level fit"),
    ("odds_ratio_survival_per_minute_shorter_response", "exploratory (five graph findings read against abstracts)",
     "surv_per_min", "natural log of the odds ratio and of its bounds; the central value is the middle of the log range"),
    ("baseline_survival_to_discharge_cardiac_arrest", "exploratory (an assumed range)", "base_survival",
     "value, lo and hi"),
]
# entries of the congestion file compared with a simulator baseline and not loaded (different definitions)
CONGESTION_CHECKS = [
    ("crz_entries_share_taxi_fhv_pct", "taxi and for-hire share of baseline entries, %"),
    ("cardiac_arrest_calls_attended_zone_peak_per_year", "baseline cardiac-arrest calls a year, weekdays, 05:00-20:59"),
    ("ems_incident_elasticity_to_subway_entries", "retail_per_visit (an assumption informed by this value, not set by it)"),
]


def median_of(p: dict) -> float:
    if p["dist"] == "uniform":
        return (p["lo"] + p["hi"]) / 2
    if p["dist"] == "loguniform":
        return math.sqrt(p["lo"] * p["hi"])
    if p["dist"] == "normal":
        return (p["lo"] + p["hi"]) / 2
    raise ValueError(p["dist"])


def main():
    fits = json.loads((DER / "fits_calib.json").read_text())
    hold = json.loads((DER / "holdout_result.json").read_text())
    pooled = json.loads((DER / "fit_pooled.json").read_text())      # analyses/simulate/fit_pooled.py
    zs = json.loads((DER / "zone_shootings.json").read_text())
    raw = CONG.read_bytes()
    cfile = json.loads(raw)
    cong = {p["name"]: p for p in cfile["parameters"]}
    missing = [m[0] for m in CONGESTION_MAP + CONGESTION_CHECKS if m[0] not in cong]
    if missing:
        raise SystemExit(f"entries named in the mapping are missing from {CONG.relative_to(ROOT)}: {missing}")
    cv = lambda name: cong[name]["value"]

    b, th = fits["speed_flow_pooled"], fits["ambulance_speed"]
    hb, ha = hold["slopes"]["speed_primary_pooled"], hold["slopes"]["ambulance"]
    bp, bh = pooled["pooled_without_low_days"], pooled["holdout_without_low_days"]

    # toll -> entries, from the measured fall in vehicle-miles at the one observed price
    toll_peak, toll_night = cv("toll_peak_car_ezpass"), cv("toll_overnight_car_ezpass")
    s_taxi = cv("crz_entries_share_taxi_fhv_pct") / 100
    r = sorted(abs(cv(k)) / 100 / (1 - s_taxi) for k in ("vmt_change_crz_2025_vs_2024_pct_low", "vmt_change_crz_2025_vs_2024_pct_high"))
    k_lo, k_hi = (-math.log(1 - x) / toll_peak for x in r)
    # speed -> ambulance: the span of the two measured intervals
    e_month = cong["elasticity_ems_travel_time_to_taxi_speed"]
    th_lo, th_hi = th["est"] - 1.96 * th["se"], th["est"] + 1.96 * th["se"]
    theta_lo, theta_hi = min(th_lo, e_month["lo"]), max(th_hi, e_month["hi"])
    # ambulance time -> survival: log odds ratio per minute
    orr = cong["odds_ratio_survival_per_minute_shorter_response"]
    g_lo, g_hi = math.log(orr["lo"]), math.log(orr["hi"])
    bs = cong["baseline_survival_to_discharge_cardiac_arrest"]
    # the January 2025 step read as an elasticity, for the source text of beta_speed only
    sp = cong["speed_change_cbd_vs_city_pct"]
    step = sorted(math.log(1 + sp["value"] / 100) / math.log(1 - abs(cv(k)) / 100)
                  for k in ("vmt_change_crz_2025_vs_2024_pct_low", "vmt_change_crz_2025_vs_2024_pct_high"))
    north = cong["taxi_speed_change_cbd_vs_north_peak_pct"]

    P = {
        "k_toll": dict(lo=k_lo, hi=k_hi, dist="uniform", type="c", sign="assumed", unit="per dollar",
                       label="Toll to entries: share of toll-paying entries removed per dollar of car toll",
                       source=f"Assumption anchored on one price point, computed from data/derived/congestion/parameters.json: MTA "
                              f"vehicle-miles in the zone were {abs(cv('vmt_change_crz_2025_vs_2024_pct_low'))}% to "
                              f"{abs(cv('vmt_change_crz_2025_vs_2024_pct_high'))}% lower in 2025 than in 2024 after a ${toll_peak:g} toll "
                              f"(mob-crz-traffic; no comparison area), which is {100 * r[0]:.0f}% to {100 * r[1]:.0f}% of the entries that "
                              f"are not taxis or for-hire vehicles ({100 * s_taxi:.1f}% are). The exponential form, the equal treatment "
                              "of vehicle-miles and entries, and the attribution of the whole fall to the toll are assumed. The sign "
                              "is assumed: a higher toll lowers entries in every draw. No count of entries before the toll is public, "
                              "and the response to a second price has not been observed."),
        "k_shift": dict(lo=0.0, hi=0.012, dist="uniform", type="c", sign="assumed", unit="per dollar",
                        label="Retiming: extra shift of entries from dearer to cheaper days or hours, per dollar of difference",
                        source="Assumption, including the sign. No estimate of substitution between weekdays exists for New York; the "
                               "entries data could give one for hours, from bunching at the 05:00 and 21:00 rate changes."),
        "beta_speed": dict(lo=bp["lo"], hi=bp["hi"], dist="normal", type="a", sign="open", unit="elasticity",
                           label="Entries to speed: % change in zone taxi speed per 1% more vehicle entries",
                           source=f"Day-level fit on {bp['n_days']} ordinary weekdays of 2025 and January-June 2026 together "
                                  f"(analyses/simulate/fit_pooled.py, exploratory): {bp['est']:.2f} (se {bp['se']:.2f}), without the four "
                                  "held-out days whose entries were under 0.80 of the median. The range crosses zero because the "
                                  f"evidence does not fix the sign. The fit on 2025 alone was {b['est']:.2f} ({b['est'] - 1.96 * b['se']:.2f} to "
                                  f"{b['est'] + 1.96 * b['se']:.2f}); the registered held-out test sim-crz-holdout-2026 gave "
                                  f"{hb['slope'] * b['est']:.2f} ({hb['hi'] * b['est']:.2f} to {hb['lo'] * b['est']:.2f}), contested, a value fixed "
                                  f"by two storm days; the held-out days without the four low days give {bh['est']:+.2f} (se {bh['se']:.2f}). "
                                  "Entries vary by about 3% within the fixed effects, and the 2025 coefficient is -0.09 (se 0.11) with the "
                                  "number of taxi trips in the zone in the model (critique/sim-crz-holdout-2026.md). The January 2025 step "
                                  f"read as an elasticity gives {step[0]:.1f} to {step[1]:.1f} from the speed change against the rest of the "
                                  f"city (+{sp['value']}%, mob-crz-traffic) and about zero from the change against Manhattan north of 60th "
                                  f"Street ({north['value']:+}%, {north['lo']} to {north['hi']}, exploratory). One value is used in every band; "
                                  "the 2025 fits by band run from -0.10 (se 0.24) in the evening to -0.56 at midday."),
        "theta_ems": dict(lo=theta_lo, hi=theta_hi, dist="uniform", type="a", sign="measured", unit="elasticity",
                          label="Speed to ambulance: % change in EMS travel time (life-threatening calls) per 1% more speed",
                          source=f"The span of two measured intervals. Day-level fit on 2025 weekdays: {th['est']:.2f} ({th_lo:.2f} to "
                                 f"{th_hi:.2f}); its held-out slope in January-June 2026 was {ha['slope']:.2f} ({ha['lo']:.2f} to {ha['hi']:.2f}) "
                                 "of the fitted value and does not depend on the storm days (sim-crz-holdout-2026; within weeks or on dry "
                                 f"days the held-out value is about -0.4). Monthly pre-toll estimate, all incidents: {e_month['value']} "
                                 f"({e_month['lo']} to {e_month['hi']}), loaded from data/derived/congestion/parameters.json "
                                 "(bridge-crz-ems-travel, unsettled; its referee found the monthly slope unstable, -0.32 to -1.13 by "
                                 "period). The sign is negative in every estimate."),
        "surv_per_min": dict(lo=g_lo, hi=g_hi, dist="normal", type="b", sign="measured", unit="per minute",
                             label="Ambulance time to survival: fall in the log odds of surviving a cardiac arrest per minute of delay",
                             source=f"Loaded from data/derived/congestion/parameters.json: odds ratio {orr['value']} ({orr['lo']} to "
                                    f"{orr['hi']}) per minute of shorter response, the median and range of five System graph findings read "
                                    "against their abstracts (PMIDs 30576783, 30795948, 31350130, 33628510, 20798090). The natural log is "
                                    "used, and at a survival of 3% to 10% the odds ratio is close to the ratio of survival shares. The "
                                    "findings are observational gradients over minutes of response time, none is from New York, and the "
                                    "simulator applies them to changes of a few seconds."),
        "base_survival": dict(lo=bs["lo"], hi=bs["hi"], dist="uniform", type="c", sign="assumed", unit="share",
                              label="Share of cardiac arrests attended by EMS who survive to discharge",
                              source="Assumption, loaded from data/derived/congestion/parameters.json so that both analyses use one "
                                     "range. The open EMS data do not record outcomes."),
        "car_share": dict(lo=0.07, hi=0.20, dist="uniform", type="c", sign="assumed", unit="share",
                          label="Share of people entering the zone on a weekday who arrive in a toll-paying vehicle",
                          source="Assumption built from measured counts: about 320,000 non-taxi vehicle entries a weekday (t6yz-b64h) at 1.2 to 1.4 "
                                 "people each, against 1.76 million subway entries in the district (transit-weekday-pattern) plus rail, bus, "
                                 "ferry, taxi, cycling and walking, which the open data do not total."),
        "diversion": dict(lo=0.3, hi=0.95, dist="uniform", type="c", sign="assumed", unit="share",
                          label="Share of deterred car trips still made to the zone by another mode",
                          source="Assumption. No New York estimate; a survey of deterred drivers would give it."),
        "spend_ratio": dict(lo=0.5, hi=2.0, dist="loguniform", type="c", sign="assumed", unit="ratio",
                            label="Spending per car visitor relative to the average visitor",
                            source="Assumption: between half and twice, with equal weight on either side of 1."),
        "retail_per_visit": dict(lo=0.3, hi=1.0, dist="uniform", type="c", sign="assumed", unit="elasticity",
                                 label="Visits to retail and restaurant activity",
                                 source="Assumption informed by two project results on activity per person present: taxi pickups follow subway "
                                        "entries with a slope of 0.50 (0.13 to 0.81; retimed-taxi-fhv-pickups, unsettled) and daytime EMS incidents "
                                        "with 0.45 (0.17 to 0.70; retimed-ems-presence). The graph holds no finding on footfall and sales."),
        "amenity": dict(lo=-0.1, hi=0.2, dist="uniform", type="c", sign="open", unit="elasticity",
                        label="Visits gained per 1% more traffic speed (quieter streets, faster buses)",
                        source="Assumption. Nothing in the project or the graph measures it, so the range crosses zero."),
        "charge_factor": dict(lo=0.55, hi=0.85, dist="uniform", type="c", sign="assumed", unit="ratio",
                              label="Toll revenue per non-taxi entry as a multiple of the car toll",
                              source="Assumption. Cars are charged once a day, trucks pay 1.6 to 2.4 times the car rate, and tunnel credits and "
                                     "discounts apply; the entries data do not say which entries were charged."),
        "crash_volume": dict(lo=0.5, hi=1.2, dist="uniform", type="c", sign="assumed", unit="exponent",
                             label="Injury crashes per 1% more vehicle entries",
                             source="Assumption carried from bridge-crz-crash-link."),
        "crash_speed": dict(lo=0.22, hi=2.18, dist="normal", type="c", sign="assumed", unit="exponent",
                            label="Injury crashes per 1% more speed (power model, urban roads)",
                            source="Literature value used as an assumption: Elvik 2009 as carried in bridge-crz-crash-link, 1.2 with sd 0.5; the endpoint "
                                   "test of that chain in New York was unsettled (bridge-crz-injury-crashes-v2: observed +4.5%, -2.7 to +12.2, "
                                   "against a composed -2.2%)."),
    }
    for name, p in P.items():
        p["value"] = median_of(p)                       # the central value is the median of the draws
        P[name] = {k: p[k] for k in ("value", "lo", "hi", "dist", "type", "sign", "unit", "label", "source")}

    bands = {"night": {"hours": "21:00-04:59", "n_hours": 8}, "am": {"hours": "05:00-09:59", "n_hours": 5},
             "mid": {"hours": "10:00-15:59", "n_hours": 6}, "pm": {"hours": "16:00-20:59", "n_hours": 5}}
    base = fits["baseline"]
    q = sum(base[bn][str(w)]["entries"] for bn in bands for w in range(5))
    qx = sum(base[bn][str(w)]["entries_tlc"] for bn in bands for w in range(5))
    arr_day = sum(base[bn][str(w)]["ems_arrest_per_day"] for bn in ("am", "mid", "pm") for w in range(5)) * 50
    ours = {"crz_entries_share_taxi_fhv_pct": round(100 * qx / q, 1),
            "cardiac_arrest_calls_attended_zone_peak_per_year": round(arr_day),
            "ems_incident_elasticity_to_subway_entries": P["retail_per_visit"]["value"]}
    why = {"crz_entries_share_taxi_fhv_pct": "the congestion value covers all days and hours of January 2025 to October 2026; the "
                                             "baseline covers non-holiday weekdays of 2025",
           "cardiac_arrest_calls_attended_zone_peak_per_year": "the congestion value counts calls transported or pronounced dead, all "
                                                               "seven days, zone by ZIP, 2023-24; the baseline counts calls typed as "
                                                               "arrest, weekdays, community districts 101-106, 2025",
           "ems_incident_elasticity_to_subway_entries": "an elasticity of EMS incidents, not of sales"}
    out = {
        "meta": {
            "generated": time.strftime("%Y-%m-%d"),
            "what": "Parameters of the congestion-toll schedule simulator (sim/). Rebuild with analyses/simulate/build_parameters.py.",
            "source_types": {"a": "estimated in this project", "b": "System graph finding checked against its abstract",
                             "c": "assumption with a wide range"},
            "sign_types": {"measured": "every estimate has this sign", "open": "the evidence does not fix the sign and the range crosses zero",
                           "assumed": "the sign is an assumption"},
            "central_values": "Each central value is the median of its draws. No distribution is truncated.",
            "congestion_file": {"path": "data/derived/congestion/parameters.json", "generated": cfile.get("generated"),
                                "n_entries": len(cfile["parameters"]), "sha256": hashlib.sha256(raw).hexdigest()},
            "loaded_from_congestion_file": [
                {"entry": n, "source": src, "sets": sets, "use": use,
                 "value": cong[n]["value"], "lo": cong[n].get("lo"), "hi": cong[n].get("hi"), "unit": cong[n].get("unit")}
                for n, src, sets, use in CONGESTION_MAP],
            "compared_not_loaded": [{"entry": n, "simulator_quantity": what, "congestion_value": cong[n]["value"],
                                     "simulator_value": ours[n], "why_not_loaded": why[n]} for n, what in CONGESTION_CHECKS],
            "measured_parameters": [k for k, p in P.items() if p["type"] in ("a", "b")],
            "assumptions": [k for k, p in P.items() if p["type"] == "c"],
            "seed": 20261113, "draws": 10000,
        },
        "bands": bands,
        "current_toll": {"night": toll_night, "am": toll_peak, "mid": toll_peak, "pm": toll_peak},
        "constants": {
            "weeks_per_year": 50,
            "phase2_peak_toll": cv("toll_phase2_peak_car"),
            "zone_injury_crashes_per_year": 2726,
            "zone_injury_crashes_source": "NYPD crashes inside the zone, 2025 (bridge-crz-injury-crashes-v2), all days",
            "hot_days_per_year": 43, "hot_weekdays_per_year": 30.5,
            "hot_day_definition": "Central Park daily maximum at or above 30 C, mean of 2015-2024",
            "shootings_per_5c": {"value": 1.146, "lo": 1.130, "hi": 1.163, "source": "heat-shootings (confirmed), citywide"},
            "zone_shootings_per_year": zs["zone_shootings"] / zs["years"],
            "zone_night_shootings_per_year": zs["zone_night_shootings"] / zs["years"],
            "zone_hot_night_shootings_per_year": zs["zone_night_shootings_after_hot_day"] / zs["years"],
            "zone_night_shooting_fatal_share": round(zs["night_fatal_share"], 3),
            "city_shootings_per_year": 1364,
            "gunshot_survival_per_min": {"lo": 0.0, "hi": 0.05, "type": "c",
                                         "source": "Assumption: relative fall in survival of a gunshot victim per minute of ambulance travel"},
            "zone_shootings_source": "NYPD Shooting Incident Data (833y-fsy8), precincts 1, 5, 6, 7, 9, 10, 13, 14, 17, 18, 2015-2024; "
                                     "night is 21:00-04:59; data/derived/simulate/zone_shootings.json",
        },
        "baseline_source": "Means over non-holiday weekdays, 6 January to 23 December 2025: MTA zone entries (t6yz-b64h), "
                           "yellow-taxi trips inside the zone (TLC trip records), EMS incidents in community districts 101-106 (76xm-jjuj). "
                           "analyses/simulate/fit_links.py, function baseline.",
        "baseline_caveat": "The baselines are 2025 means. In January to June 2026 taxi speed in the zone was about 7% lower and ambulance "
                           "travel time to life-threatening calls about 11% higher, with weather controlled, for reasons the chain does "
                           "not contain (critique/sim-crz-holdout-2026.md). Levels in mph and seconds are out of date; outputs are "
                           "stated as changes from the current schedule.",
        "baseline": base,
        "parameters": P,
    }
    (DER / "parameters.json").write_text(json.dumps(out, indent=1))
    print("wrote parameters.json")
    for k, p in P.items():
        print(f"  {k:17s} [{p['type']}] {p['dist']:10s} {p['value']:+.4f} ({p['lo']:+.4f} to {p['hi']:+.4f})  sign {p['sign']}")
    print("loaded from the congestion file:", ", ".join(m[0] for m in CONGESTION_MAP))
    print("assumptions:", ", ".join(out["meta"]["assumptions"]))


if __name__ == "__main__":
    main()
