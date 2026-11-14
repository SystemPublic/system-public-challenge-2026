"""Write the outcome of transit-weekday-pattern from data/derived/transit/weekday_pattern.json.

    ~/.venvs/nyc-concordance/bin/python -m analyses.transit.outcome_weekday_pattern
"""
import json
from collections import defaultdict
from pathlib import Path

from concord import claims

ROOT = Path(__file__).resolve().parents[2]
r = json.loads((ROOT / "data/derived/transit/weekday_pattern.json").read_text())
src = json.loads((ROOT / "data/derived/transit/weekday_pattern_sources.json").read_text())

by = defaultdict(list)
for s in src:
    by[s["dataset"]].append(s)
sources = []
for d, v in by.items():
    sources.append({"kind": "ny-state-open-data (recorded by concord/socrata.py as nyc-open-data)", "portal": "data.ny.gov", "dataset": d,
                    "name": v[0]["name"], "url": v[0]["url"], "rows_updated_at": v[0]["rows_updated_at"], "data_access": "open",
                    "n_queries": len(v), "fetched_first": min(x["fetched"] for x in v), "fetched_last": max(x["fetched"] for x in v),
                    "example_query": v[0]["query"], "all_queries": "data/derived/transit/weekday_pattern_sources.json"})

p, rec, y19 = r["primary"], r["primary"]["recent"], r["primary"]["y2019"]
pl = r["placebo_2019_minus_2018"]["delta"]
b = r["bands"]
f1 = lambda x: round(x, 1)

claims.outcome({
    "id": "transit-weekday-pattern",
    "verdict": "confirmed",
    "city_effect": {"label": "Change in the Monday/Friday deficit of CBD subway entries, Nov 2025-Oct 2026 minus 2019",
                    "estimate": round(p["delta"]["estimate"], 2), "lo": round(p["delta"]["lo"], 2), "hi": round(p["delta"]["hi"], 2),
                    "scale": "percentage points of the Tue-Thu mean", "null": 0, "n": f"{rec['n_weeks']} weeks recent, {y19['n_weeks']} weeks 2019, 65 station complexes"},
    "graph_effect": None,
    "components": {
        "recent_mf_deficit_pct": [f1(rec["mf"])] + [f1(x) for x in rec["mf_ci"]],
        "recent_monday_deficit_pct": [f1(rec["def_mon"])] + [f1(x) for x in rec["def_mon_ci"]],
        "recent_friday_deficit_pct": [f1(rec["def_fri"])] + [f1(x) for x in rec["def_fri_ci"]],
        "recent_midweek_range_points": [round(rec["range"], 2)] + [round(x, 2) for x in rec["range_ci"]],
        "y2019_mf_deficit_pct": [f1(y19["mf"])] + [f1(x) for x in y19["mf_ci"]],
        "y2019_midweek_range_points": [round(y19["range"], 2)] + [round(x, 2) for x in y19["range_ci"]],
        "placebo_2019_minus_2018_points": [round(pl["estimate"], 2), round(pl["lo"], 2), round(pl["hi"], 2)],
        "trajectory_mf_deficit_pct": {k: f1(v["mf"]) for k, v in r["trajectory"].items()},
        "delta_by_hour_band_points": {k: [round(v["delta"][x], 1) for x in ("estimate", "lo", "hi")] for k, v in b.items()},
        "outer_borough_am_peak_delta_points": [round(r["outer_am"]["delta"][x], 1) for x in ("estimate", "lo", "hi")],
        "sensitivity_delta_points": {"S1 office core (25 complexes)": round(r["S1_office_core"]["delta"]["estimate"], 1),
                                     "S2 median": round(r["S2_median"]["delta"]["estimate"], 1),
                                     "S3 holidays only": round(r["S3_days_only"]["delta"], 1),
                                     "S4 calendar 2025": round(r["S4_calendar_2025"]["delta"]["estimate"], 1),
                                     "S5 mean over complexes": round(r["S5_complex_level"]["delta_mean"], 1)},
        "sensitivity_recent_midweek_range_points": {"S2 median": round(r["S2_median"]["recent"]["range"], 2), "S3 holidays only": round(r["S3_days_only"]["recent"]["range"], 2),
                                                    "S4 calendar 2025": round(r["S4_calendar_2025"]["recent"]["range"], 2), "S1 office core": round(r["S1_office_core"]["recent"]["range"], 2)},
        "ranking": {k: r["ranking"][k] for k in ("spearman_all", "n_complexes", "top20_overlap", "top20_cbd_2019", "top20_cbd_recent")},
    },
    "sources": sources,
    "prediction_scored": (
        "hit. All three registered conditions are met: (a) the recent Monday/Friday deficit is 13.8% (interval 12.3 to 15.9), Monday 16.4% and "
        "Friday 11.2%; (b) the recent midweek range is 2.77 points, under the 3-point limit; (c) the deficit grew by 8.7 points (6.9 to 10.9) "
        "from 5.1% in 2019. The placebo (2019 minus 2018) is 0.74 points (-0.82 to 2.53), inside the 1.5-point limit. The magnitudes fall in the "
        "registered ranges except Monday, which at 16.4% is above the 7-13% range. Condition (b) is met by a small margin: the interval of the range "
        "runs from 1.8 to 4.1 points. The separately scored sub-question is answered no: the gap was not absent before 2020 (5.1%, interval 4.3 to 6.0), "
        "as predicted. Secondary predictions: the largest change was in the AM peak (15.2 points), not the PM peak (12.5), a miss; the Friday evening "
        "deficit is 0.5% in 2019 and -9.2% recently, a hit; the outer-borough AM-peak change is 9.4 points, smaller than the CBD PM peak as predicted but "
        "above the 2-6 range, a partial hit; 19 of the top 20 complexes are the same and the Spearman correlation is 0.98, hits; 17 of the top 20 are CBD "
        "complexes against 16 in 2019, a miss."
    ),
    "settle": (
        "The day-of-week pattern is settled for fare-paid entries. What the design does not settle is the cause. Three kinds of data would: "
        "office occupancy by weekday for the same buildings before and after 2020 (Kastle and similar series are proprietary and begin in 2020); "
        "origin-destination or exit counts, to separate commuters from visitors (the MTA publishes an estimated origin-destination table, not used here); "
        "and scheduled service by weekday, to test whether the MTA's Monday and Friday service reductions from 2023 lowered entries independently of demand."
    ),
    "research_needed": [
        {"question": "Does retail and restaurant revenue in the CBD follow the same Monday/Friday deficit as subway entries?",
         "data": "Card-transaction or sales-tax data by day of week and small area. No open NYC dataset has this: sales-tax data are quarterly and by industry, and card panels (Mastercard, Affinity, Placer) are proprietary.",
         "design": "The same weekly ratio by block or business district, 2019 against a recent year, set beside station entries.", "priority": "high"},
        {"question": "How many of the people entering CBD stations are office workers on a given weekday?",
         "data": "Building access-control counts or employer attendance records by weekday, with a 2019 baseline.",
         "design": "Regress station-level weekday deficits on nearby office floor area and occupancy by weekday.", "priority": "high"},
        {"question": "Is there a peer-reviewed measurement of the post-2020 weekday pattern in fare-collection data against a pre-2020 baseline?",
         "data": "Open hourly ridership from the MTA and comparable agencies (CTA, WMATA, BART, TfL).",
         "design": "The same within-week ratio across agencies. Our search found agency statements and trade reports but no such paper.", "priority": "medium"},
        {"question": "Does the System graph hold any finding linking telework to transit use by day of the week?",
         "data": "System Public Graph API and Dataverse deposit.", "design": "Live lookup of telework, remote work and transit ridership concepts; it was not possible on this machine.", "priority": "medium"},
        {"question": "Why did CBD morning entries on Fridays fall furthest (31% below midweek, against 13% in 2019)?",
         "data": "Commuter-rail arrivals at Penn Station and Grand Central by weekday (MTA LIRR and Metro-North ridership), PATH turnstile counts.",
         "design": "Compare the weekday pattern of rail arrivals with subway entries at the terminal complexes.", "priority": "low"},
    ],
    "figures": ["figures/transit/weekday_pattern.png"],
    "notes": (
        "Subway entries are fare-paid entries at station complexes, a proxy for people present and not a count of pedestrians. Exits are not recorded. "
        "The mean Monday deficit in the recent period includes two Mondays, 26 January and 23 February 2026, on which CBD entries were 38% and 20% of that "
        "week's midweek mean. The cause was not checked; the size suggests a system-wide disruption such as a storm. With the median over weeks (S2) the recent Monday deficit is "
        "12.9%, the Monday/Friday deficit 12.0% and the change from 2019 7.5 points (6.7 to 8.3). The verdict is the same under S1 to S5. "
        "The deficit was 10.4% in 2022, 14.1% in 2023, 13.0% in 2024 and 12.7% in 2025, so it has been stable for three years. "
        "Mean CBD entries per retained weekday were 2.34 million in 2019 and 1.76 million in the recent period. "
        "Plan deviations, none of which changes a registered definition: the borough-level hourly queries were run only for 2019, 2025 and 2026 because "
        "the half-year queries on the 2020-2024 dataset took several minutes each; the 2025 dataset was queried by month and the complex-by-day totals by "
        "week, because longer queries timed out. The graph side is empty: no live lookup was possible and the cache holds nothing on this edge."
    ),
})
print("outcome written")
