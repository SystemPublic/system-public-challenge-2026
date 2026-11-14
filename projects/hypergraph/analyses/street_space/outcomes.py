"""Write the outcomes of street-busway14-crosstown-time and street-busway14-crosstown-detour from
data/derived/street_space/test_final.json (registered test) and extras.json (secondary)."""
from __future__ import annotations

import json

import pandas as pd

from concord import claims, sysgraph
from analyses.street_space.common import DER, TLC, TLC_URL

t = json.loads((DER / "test_final.json").read_text())
x = json.loads((DER / "extras.json").read_text())

months = [str(p)[:7] for p in pd.period_range("2016-07", "2020-02", freq="M")]
TLC_SRC = {"kind": "tlc-trip-records", "name": "TLC Yellow Taxi Trip Records (monthly parquet)",
           "url": TLC_URL.replace("{m}", "YYYY-MM"), "months": f"{months[0]} to {months[-1]}",
           "file_bytes": {m: (TLC / f"yellow_tripdata_{m}.parquet").stat().st_size for m in months},
           "fetched": "2026-11-13", "local_copy": "~/opt/nyc-concordance/tlc_yellow_1720/"}
GRAPH_SRC = {"kind": "sysgraph", "api": sysgraph.API_VERSION, "dataset": sysgraph.DATASET_VERSION,
             "files": ["data/derived/street_space/graph_evidence.json", "data/derived/street_space/graph_detail.json"]}
LEV = x["levels_weekday"]
FIGS = ["figures/street_space/busway_registered_estimates.png", "figures/street_space/busway_yoy_monthly.png"]

RESEARCH = [
    {"question": "Did traffic volume on 14th Street fall by more than it rose on 12th, 13th and 15th to 18th Streets (evaporation)?",
     "data": "Automated or manual counts on each crosstown street from 2nd to 10th Avenue for at least two months before and after; DOT's own ATR counts behind the Sam Schwartz reports are not in 7ym2-wayt (four 2019 locations only).",
     "design": "Before-after with control streets in Midtown; publish the counts.", "priority": "high"},
    {"question": "Was the small rise in trip distance a detour caused by the busway or the continuation of a drift that began in 2018?",
     "data": "TLC trip records with GPS traces (not public since mid-2016) or app-company route data; taxi zone pairs at finer scale.",
     "design": "Route-level comparison of the share of crosstown trips using 14th Street before and after.", "priority": "medium"},
    {"question": "Did the busway change injuries on 14th Street and its parallel streets, and NO2 along the corridor?",
     "data": "h9gi-nx95 crashes by street segment; NYCCAS street-level monitors on 14th Street (if any) or low-cost sensors.",
     "design": "Registered before-after with control corridors, segment-level counts.", "priority": "medium"},
    {"question": "The System Public Graph holds no finding on road-space reallocation, traffic evaporation or displaced traffic.",
     "data": "Transport literature (Cairns et al. 1998, 2002; Nello-Deakin 2022; bus-lane evaluations) is outside the graph's health-centred corpus.",
     "design": "Add transport-research studies with travel-time and volume outcomes.", "priority": "medium"},
]

COMMON_NOTES = (
    f"Weekday daytime trips between the treated zones averaged {LEV['t14_pre']['mean_min']} minutes and {LEV['t14_pre']['mean_mi']} miles "
    f"in October 2018 to February 2019 ({LEV['t14_pre']['trips']:,} trips) and {LEV['t14_post']['mean_min']} minutes and "
    f"{LEV['t14_post']['mean_mi']} miles in October 2019 to February 2020 ({LEV['t14_post']['trips']:,} trips). "
    "Control-group sensitivity of the weekday estimate (exploratory): against Midtown pairs only, duration "
    f"{x['control_sensitivity']['c_mid_s_lt']['E_pct']}% ({x['control_sensitivity']['c_mid_s_lt']['lo_pct']} to {x['control_sensitivity']['c_mid_s_lt']['hi_pct']}) "
    f"and distance {x['control_sensitivity']['c_mid_s_ld']['E_pct']}%; against downtown pairs only, duration "
    f"{x['control_sensitivity']['c_down_s_lt']['E_pct']}% ({x['control_sensitivity']['c_down_s_lt']['lo_pct']} to {x['control_sensitivity']['c_down_s_lt']['hi_pct']}) "
    f"and distance {x['control_sensitivity']['c_down_s_ld']['E_pct']}% ({x['control_sensitivity']['c_down_s_ld']['lo_pct']} to {x['control_sensitivity']['c_down_s_ld']['hi_pct']}). "
    "The registered estimator has no resampling, so rule 9 does not apply. Placebo seasons 2017 and 2018 were recomputed with the post months included and are unchanged."
)


def eff(k, label):
    r = t[k]["2019"]
    return {"label": label, "estimate": r["E_pct"], "lo": r["lo_pct"], "hi": r["hi_pct"], "scale": "% change (E, summer-netted year-over-year DiD)",
            "null": 0, "n": LEV["t14_post"]["trips"] + LEV["t14_pre"]["trips"], "se_log": t[k]["se_log"],
            "placebo_2017": t[k]["2017"], "placebo_2018": t[k]["2018"]}


wt, wd = t["weekday_s_lt"]["2019"], t["weekday_s_ld"]["2019"]
dy = x["did_yoy"]
sec_t = {k: t[k]["2019"] for k in ("busway_s_lt", "overnight_s_lt")}
sec_d = {k: t[k]["2019"] for k in ("busway_s_ld", "overnight_s_ld")}

time_out = {
    "id": "street-busway14-crosstown-time",
    "verdict": "contested",
    "city_effect": eff("weekday_s_lt", "Weekday crosstown taxi trip duration, 14th Street pairs minus control pairs"),
    "graph_effect": None,
    "sources": [TLC_SRC, GRAPH_SRC],
    "prediction_scored": (f"miss. E = {wt['E_pct']}% ({wt['lo_pct']} to {wt['hi_pct']}). refute_if (upper bound below +5.0%) is met, by 0.68 "
                          "points, which is less than one standard error (1.7 points), so it is met within sampling error (rule 10). "
                          "support_if (E >= 2% and lower bound above 0) is not met. The predicted lengthening of about 5%, about 35 seconds "
                          "on an 11.5-minute trip, is excluded; a lengthening of up to 4.3% (about 30 seconds) is not."),
    "settle": ("Corridor-level volume counts on 12th to 18th Streets before and after, and a second winter (2020-21 is unusable because "
               "of the pandemic), would separate a small lengthening from none. Door-to-door times answer the traveller's question; "
               "DOT's probe runs on single streets answer the street's question, and the two agree that the change was small."),
    "research_needed": RESEARCH,
    "figures": FIGS,
    "notes": (
        "The claim was registered as a conflict: it bet that removing through traffic from 14th Street would lengthen crosstown trips "
        "by about 5%, against the evaporation literature and DOT's summary. The verdict 'contested' means that bet lost: the data "
        "agree with the research side. Secondary estimates, not deciding: all busway hours (06-21, every day) "
        f"{sec_t['busway_s_lt']['E_pct']}% ({sec_t['busway_s_lt']['lo_pct']} to {sec_t['busway_s_lt']['hi_pct']}); overnight (22-05, busway not in force) "
        f"{sec_t['overnight_s_lt']['E_pct']}% ({sec_t['overnight_s_lt']['lo_pct']} to {sec_t['overnight_s_lt']['hi_pct']}). The plain year-over-year DiD with "
        f"a day bootstrap gives {dy['weekday_s_lt']['did_pct']}% ({dy['weekday_s_lt']['lo_pct']} to {dy['weekday_s_lt']['hi_pct']}) on weekdays; the same "
        "estimator gave +3.4% in the placebo year 2017-18 to 2018-19, so its bootstrap interval understates the year-to-year noise. "
        "Exploratory: the monthly year-over-year contrast was +4.4% in October 2019 and +3.0% in November, then -2.8%, -1.3% and -1.1% "
        "in December to February. The pre-busway monthly values have a standard deviation of 2.3%, so the pattern of early lengthening "
        "followed by adaptation is suggestive and not established. " + COMMON_NOTES),
}

det_out = {
    "id": "street-busway14-crosstown-detour",
    "verdict": "contested",
    "city_effect": eff("weekday_s_ld", "Weekday crosstown taxi metered distance, 14th Street pairs minus control pairs"),
    "graph_effect": None,
    "sources": [TLC_SRC, GRAPH_SRC],
    "prediction_scored": (f"miss. E = {wd['E_pct']}% ({wd['lo_pct']} to {wd['hi_pct']}). refute_if (upper bound below +1.5%) is met, by 0.34 "
                          "points, less than one standard error (0.50 points), so within sampling error (rule 10). support_if is not met. "
                          "A detour of 1.5% (about 0.02 miles, 100 feet, per trip) is excluded under the registered estimator; one of up to 1.2% is not."),
    "settle": ("The registered estimator nets out the year-over-year change of the preceding summer. That summer (July to September 2019) "
               "already showed a rise in the treated pairs' distance (+1.3%, +0.8%, +0.6% against a year earlier), when the M14 SBS began "
               "and the busway's August start was stopped by a court order. If drivers changed routes in that summer, the netting removes "
               "part of the effect. Route-level data (which street a trip used) would settle it."),
    "research_needed": RESEARCH,
    "figures": FIGS,
    "notes": (
        "Secondary estimates, not deciding: all busway hours "
        f"{sec_d['busway_s_ld']['E_pct']}% ({sec_d['busway_s_ld']['lo_pct']} to {sec_d['busway_s_ld']['hi_pct']}); overnight "
        f"{sec_d['overnight_s_ld']['E_pct']}% ({sec_d['overnight_s_ld']['lo_pct']} to {sec_d['overnight_s_ld']['hi_pct']}). The plain year-over-year DiD "
        f"on weekdays gives {dy['weekday_s_ld']['did_pct']}% ({dy['weekday_s_ld']['lo_pct']} to {dy['weekday_s_ld']['hi_pct']}), against +0.59% "
        "(0.14 to 1.04) for the same estimator in the placebo year, so about half of it is drift that predates the busway. "
        "Exploratory: every one of the five post-busway months shows a year-over-year rise in the contrast (+0.8% to +1.4%, rising "
        "month by month), against a pre-busway monthly standard deviation of 0.7%; a detour of about 0.5% to 1% (35 to 65 feet per trip) "
        "is the most likely size, and the registered test cannot separate it from drift. "
        f"Exploratory, evaporation of taxi demand: weekday trip counts in the treated pairs relative to control changed by "
        f"{x['trip_count_E_pct']['2019']}% on the same summer-netted estimator (placebo seasons {x['trip_count_E_pct']['placebo']['2017']}% and "
        f"{x['trip_count_E_pct']['placebo']['2018']}%, monthly sd {x['trip_count_E_pct']['sd_monthly_yoy_pct']}%), so taxi demand in the corridor did not "
        "visibly fall. " + COMMON_NOTES),
}

if __name__ == "__main__":
    for o in (time_out, det_out):
        print(claims.outcome(o))
