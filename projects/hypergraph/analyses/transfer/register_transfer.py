"""Registration of the two Chicago transfer claims. Run once, before any Chicago value is queried.

    ~/.venvs/nyc-concordance/bin/python -m analyses.transfer.register_transfer
"""
import json
from pathlib import Path

from concord import claims

ROOT = Path(__file__).resolve().parents[2]
HS = json.loads((ROOT / "claims" / "registered" / "heat-shootings.json").read_text())

SEEN = (
    "No value from the Chicago portal (data.cityofchicago.org) had been queried by this project: data/cache/socrata holds "
    "no Chicago file and no script in analyses/ names a Chicago dataset. Before registering, this agent read (1) the catalog "
    "search results (dataset id, name, update time) for the four datasets named below, (2) the column lists and descriptions of "
    "gumc-mgzr, 5neh-572f, 8pix-ypme and ijzp-q8t2, and (3) for the CTA stops table 8pix-ypme the station names and coordinates "
    "of the 144 stations (used to fix the Loop rule; no ridership value). No row count, date range, shooting count, ridership "
    "value or temperature value for Chicago was read, and the Midway and O'Hare weather files were not opened. The NYC side was "
    "already known: the NYC estimates in the prediction are the project's own outcomes (heat-shootings, transit-weekday-pattern). "
    "For the weekday claim the agent also recomputed, from cached NYC queries only, the NYC Delta for the rest of the subway "
    "system (all complexes outside the CBD): 4.2 points (2.2 to 6.6), recent Monday/Friday deficit 7.3%, 2019 deficit 3.1%. "
    "The registrant knows from general reading that Chicago shootings peak in summer, that Chicago downtown office occupancy has "
    "recovered less than New York's, and the abstract of Reeping and Hemenway (2020)."
)

GRAPH_PROC = (
    "Descriptive, run after the city test and not part of the verdict. For temperature concepts paired with violence-side "
    "concepts (homicide, assault, aggression, violent crime, suicide, injury, gun violence) and for telework or commuting "
    "variables, list every study behind the relationships (sysgraph.relationship_studies, sysgraph.study) and tabulate the "
    "population field by country and by setting. Predicted before the lookup: fewer than 25% of studies with a readable "
    "population name a US city or a US metropolitan area, fewer than 5 studies name Chicago or New York, and the telework and "
    "commuting findings are dominated by non-US samples (UK, Netherlands, China, Australia). The graph's population field is "
    "free text and sparse, so the share with a readable population is reported with the shares."
)

heat = {
    "id": "transfer-chicago-heat-shootings",
    "kind": "confirmation",
    "transfer": {"from_city": "New York City", "to_city": "Chicago", "from_claim": "heat-shootings",
                 "nyc_estimate": {"irr_per_5C": 1.1462, "lo": 1.1297, "hi": 1.1629}},
    "statement": ("In Chicago, the daily number of shooting incidents with a gunshot injury rises with the day's maximum temperature "
                  "at Midway Airport by about the same proportion as in New York (IRR 1.146 per 5 C, 1.130 to 1.163), under the same "
                  "model, so that the New York result transfers."),
    "graph_evidence": HS["graph_evidence"],
    "graph_evidence_note": ("Copied from heat-shootings. The graph holds no temperature-gun violence finding; its Chicago evidence is "
                            "Xu et al. 2020 (homicide, +9.5% per 5 C mean temperature, 4.3 to 15.0). " + GRAPH_PROC),
    "literature": [x for x in HS["literature"] if "Reeping" in x["citation"] or "Lyons" in x["citation"] or "Xu R" in x["citation"]],
    "prediction": {
        "direction": "+",
        "magnitude": "Chicago IRR per 5 C of Midway TMAX (lag 0) between 1.10 and 1.20, point estimate near 1.14.",
        "transfers_band": ("The result transfers if the Chicago point estimate lies within 25% of New York's excess over 1, "
                           "that is between 1.110 and 1.183 (0.146 x 0.75 and x 1.25), and the lower 95% limit exceeds 1.00."),
        "support_if": "Chicago primary IRR per 5 C in [1.110, 1.183] and its lower 95% limit above 1.00 (verdict confirmed = transfers).",
        "refute_if": ("Chicago primary IRR per 5 C below 1.073 or above 1.219 (outside 50% of New York's excess), or its lower 95% limit at "
                      "or below 1.00 (verdict contested = does not transfer)."),
        "otherwise": "A point estimate in [1.073, 1.110) or (1.183, 1.219], with lower limit above 1.00, gives unsettled (partial transfer).",
        "reeping_comparison": ("Reported without a verdict: Chicago IRR per 5 C against Reeping and Hemenway's 1.158 (weekdays) and "
                               "1.190 (weekends and holidays) from the exploratory split, and the primary model restricted to 2012-2016."),
    },
    "plan": {
        "datasets": {"gumc-mgzr": "Violence Reduction - Victims of Homicides and Non-Fatal Shootings (data.cityofchicago.org)",
                     "ijzp-q8t2": "Crimes - 2001 to Present (sensitivity only)"},
        "access": "concord/socrata.py with concord.socrata.DOMAIN = https://data.cityofchicago.org set in the script; the source records say kind nyc-open-data and carry the Chicago url.",
        "outcome_unit": ("Daily count of distinct case_number among rows of gumc-mgzr with gunshot_injury_i in ('Y','YES'), by date "
                         "(date_trunc_ymd). A case can have several victims; New York's unit is the distinct incident_key, so the case is the "
                         "analogous unit. Non-fatal shootings begin in 2010 in this dataset, so the period is 2010-01-01 to 2026-08-31 "
                         "(the end date used for New York), with days without rows counted as zero."),
        "weather": ("GHCN-Daily USW00014819 (Chicago Midway), TMAX and PRCP, via concord/noaa.py. Midway is nearer the south and west "
                    "sides, where most shootings occur, than O'Hare. If Midway TMAX is missing on more than 5% of days in the period, O'Hare "
                    "(USW00094846) becomes primary and the registration's primary reading is taken to be that file."),
        "model": ("The same as heat-shootings: negative binomial GLM, log link, dispersion by maximum likelihood, robust HC0 standard "
                  "errors; n ~ TMAX/5 + C(day of week) + C(month) + C(year) + holiday + (PRCP >= 1 mm). Holidays are the federal holidays "
                  "plus 1 January, 4 July and 31 December (analyses.heat.common.holidays). IRR per 5 C with a 95% interval."),
        "sensitivity": [
            "S1 TMAX averaged over lags 0-1", "S2 TMIN instead of TMAX", "S3 May-September only",
            "S4 2010-2019 and 2020 onward separately", "S5 O'Hare TMAX in place of Midway",
            "S6 the 2012-2016 window of Reeping and Hemenway",
            "S7 homicide victims only (victimization_primary = 'HOMICIDE'), distinct case_number",
            "S8 Crimes (ijzp-q8t2): daily count of primary_type = 'HOMICIDE' plus primary_type = 'BATTERY' with description containing 'AGGRAVATED' and 'HANDGUN' or 'FIREARM'",
            "S9 exploratory, not decisive: temperature interacted with a weekend-or-holiday indicator, for comparison with Reeping and Hemenway",
        ],
        "figure": "figures/graph/transfer_chicago.png: NYC and Chicago side by side for both results.",
    },
    "alternatives": [
        "Different seasonal structure: Chicago's colder winters and larger seasonal range change how much of the temperature signal month terms absorb.",
        "Different reporting: gunshot victimization is recorded by victim in the Chicago dataset; case-level counting merges victims of one event.",
        "Different policing and gang-conflict dynamics, and the 2016 Chicago shooting spike, which year terms absorb only in level.",
        "Temperature measured at an airport 13 km from the Loop, with a lake-breeze gradient that Central Park does not have in the same degree.",
        "Time outdoors as the mechanism; the design cannot separate it from physiology in either city.",
    ],
    "prior": 0.6,
    "prior_note": "The Chicago literature (Reeping and Hemenway, 1.158 and 1.190) lies inside the band, but their models differ and the band is narrow.",
    "seen_before_registration": SEEN,
    "registrant": "Claude (agent), for Jeff Vernon",
}

week = {
    "id": "transfer-chicago-weekday-pattern",
    "kind": "confirmation",
    "transfer": {"from_city": "New York City", "to_city": "Chicago", "from_claim": "transit-weekday-pattern",
                 "nyc_estimate": {"delta_points": 8.7, "lo": 6.9, "hi": 10.9, "recent_mf_deficit_pct": 13.8,
                                  "y2019_mf_deficit_pct": 5.1, "rest_of_system_delta_points": 4.2,
                                  "rest_of_system_lo": 2.2, "rest_of_system_hi": 6.6}},
    "statement": ("In the Chicago Loop, the Monday/Friday deficit in 'L' station entries, relative to Tuesday to Thursday, rose from 2019 "
                  "to the 12 months to October 2026 by about as many percentage points as the New York CBD deficit did (8.7 points, 6.9 to 10.9), "
                  "and rose more in the Loop than in the rest of the 'L' system."),
    "graph_evidence": [{"note": ("The graph is expected to hold no finding on the day-of-week pattern of transit ridership; see transit-weekday-pattern. "
                                 + GRAPH_PROC),
                        "n_findings": 0, "live_lookup": "pending"}],
    "literature": [x for x in json.loads((ROOT / "claims/registered/transit-weekday-pattern.json").read_text())["literature"]
                   if "Metra" in x["citation"] or "Barrero" in x["citation"] or "Kastle" in x["citation"]],
    "prediction": {
        "direction": "+",
        "definitions": ("As in transit-weekday-pattern: R[w,d] is the sum of rides over the stations of the area for week w and weekday d; "
                        "I[w,d] = R[w,d] / mean(R[w,Tue], R[w,Wed], R[w,Thu]); Deficit(d) = 1 - mean over weeks of I[w,d]; MF deficit = "
                        "(Deficit(Mon) + Deficit(Fri)) / 2; Delta = MF deficit in the recent period minus MF deficit in 2019, in percentage "
                        "points; 95% percentile intervals from 10,000 bootstrap resamples of weeks, separately in each period (seed 20261112)."),
        "magnitude": ("Loop Delta between 5 and 12 points, near 8. Loop recent MF deficit 10% to 18%; Loop 2019 MF deficit 3% to 8%; "
                      "Loop midweek range at most 4 points; rest-of-system Delta between 2 and 7 points and smaller than the Loop's."),
        "transfers_band": "Loop Delta within 25% of New York's 8.7 points, that is between 6.5 and 10.9 points, with an interval that excludes 0.",
        "support_if": "Loop Delta in [6.5, 10.9] points and its 95% interval excludes 0 (verdict confirmed = transfers).",
        "refute_if": "Loop Delta below 4.4 or above 13.1 points (outside 50% of New York's), or its 95% interval includes 0 (verdict contested = does not transfer).",
        "otherwise": "A Loop Delta in [4.4, 6.5) or (10.9, 13.1], with interval excluding 0, gives unsettled (partial transfer).",
        "secondary_not_decisive": ("(i) rest-of-system Delta smaller than the Loop's with non-overlapping point and interval midpoint; "
                                   "(ii) Loop recent midweek range <= 4 points; (iii) placebo 2019 minus 2018 within 1.5 points; "
                                   "(iv) sign agreement of the Loop and rest-of-system Delta with New York's."),
    },
    "plan": {
        "datasets": {"5neh-572f": "CTA - Ridership - 'L' Station Entries - Daily Totals (data.cityofchicago.org)",
                     "8pix-ypme": "CTA - System Information - List of 'L' Stops (coordinates for the Loop rule)"},
        "access": "concord/socrata.py with concord.socrata.DOMAIN = https://data.cityofchicago.org set in the script.",
        "measure": "Sum of `rides` (turnstile entries) by date over the stations of an area. Entries only; the dataset has no hours.",
        "area": ("Loop: the station map_ids in 8pix-ypme whose mean stop coordinates lie within latitude 41.8750 to 41.8870 and longitude "
                 "-87.6345 to -87.6255 (this box holds the elevated Loop stations and the State and Dearborn subway stations from Lake to "
                 "LaSalle/Van Buren; 15 stations). Rest of system: every other station_id in 5neh-572f. The list of station ids is written to "
                 "the derived data before ridership is queried."),
        "periods": ("Recent: 2025-11-01 to 2026-10-31, or, if the dataset ends earlier, the latest twelve full calendar months it holds. "
                    "Baseline: 2019-01-01 to 2019-12-31. Placebo year 2018."),
        "unit_and_exclusions": ("Identical to transit-weekday-pattern: a week (Monday to Sunday) is dropped if any day is an observed US "
                                "federal holiday (Juneteenth from 2021), falls from 24 December to 1 January, or if its five weekdays are not all "
                                "in the period. Dates are calendar dates."),
        "model": "Ratios as defined, with a week bootstrap. No regression model.",
        "sensitivity": [
            "S1 median across weeks in place of the mean",
            "S2 drop only the holidays and 24 December to 1 January, keeping the rest of those weeks",
            "S3 recent period = calendar 2025",
            "S4 2019 baseline without the weeks of the Chicago Teachers Union strike (17 to 31 October 2019)",
            "S5 station-level: the MF deficit computed for each Loop station, median and interquartile range",
            "S6 Loop box widened to latitude 41.8740 to 41.8900 (adds Harrison, Grand/State)",
        ],
        "figure": "figures/graph/transfer_chicago.png",
    },
    "alternatives": [
        "A Monday/Friday deficit before 2020 that differs between the cities for institutional reasons (office hours, schedules, school calendars).",
        "CTA service levels on Mondays and Fridays and the 2019 teachers' strike, which affect entries independently of demand.",
        "Different composition of the Loop: more tourists, Millennium Park and lakefront events, and student travel, which are spread differently over the week.",
        "Station entries count transfers between lines only where a fare gate is crossed; the Loop's elevated stations have no free transfers between them.",
        "Chicago's downtown has recovered less than New York's in level, so a given absolute remote-work day shifts the ratios more.",
        "Weather, strikes and events that fall on particular weekdays by chance.",
    ],
    "prior": 0.4,
    "prior_note": "The band is narrow and Chicago's level of office return is lower; the sign is likely right, the size less so.",
    "seen_before_registration": SEEN,
    "registrant": "Claude (agent), for Jeff Vernon",
}

if __name__ == "__main__":
    for r in (heat, week):
        print(claims.register(r))
