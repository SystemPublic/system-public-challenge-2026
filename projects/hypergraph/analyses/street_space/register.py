"""Registrations for the 14th Street busway claims (run once, before any trip after September 2019 is read)."""
from __future__ import annotations

import json

from concord import claims
from analyses.street_space.common import DER

design = json.loads((DER / "test_design.json").read_text())
wt, wd = design["weekday_s_lt"], design["weekday_s_ld"]

GRAPH = [{
    "concepts": "traffic volume, bus lane, pedestrian street, road closure, travel time, congestion",
    "n_findings": 4,
    "direction": "none on this link",
    "summary": ("System Public Graph variable searches (data/derived/street_space/graph_evidence.json, graph_detail.json). "
                "No variable for busway, transit priority, road-space reallocation, traffic evaporation or displaced traffic; "
                "'road closure' and 'street closure' match nothing relevant; 'travel time' matches travel to health care. "
                "Nearest findings, abstracts read: Peace Bridge traffic fell 50% after 11 September 2001 with respiratory "
                "admissions nearly significant (PMID 14743825; the graph stores the 50% as a mean difference of 50); Busan "
                "traffic control in 2002 lowered pollutants 1-25%, childhood asthma RR 0.73 (0.49-1.11) (PMID 17824287); "
                "bus stops on a bus-only lane in Lima, pedestrian collision OR 2.36 (1.02-5.42) (PMID 24357516). None bears on "
                "travel time or displacement."),
    "pubmed_ids": [14743825, 17824287, 24357516],
}]
LIT = [
    {"citation": "Cairns S, Atkins S, Goodwin P (2002). Disappearing traffic? The story so far. Proceedings of the ICE - Municipal Engineer 151(1):13-22.",
     "doi": "10.1680/muen.2002.151.1.13",
     "finding": "Over 70 case studies of road-space reallocation in eleven countries; predicted traffic problems were often not realised and overall traffic often fell (secondary summaries give a mean reduction near 16-25% on treated roads or areas; not re-read)."},
    {"citation": "NYC DOT / Sam Schwartz Engineering, 14th Street Transit & Truck Priority Pilot preliminary report (fall 2019), as summarised by the Mayor's Office and Streetsblog, 18 December 2019.",
     "doi": None,
     "finding": "Bus travel times on 14th Street fell 22-47%; car travel times on 12th to 19th Streets rose 0-2 minutes in weekday peaks, 17th Street 3.4 minutes from 3rd to 9th Avenue; most avenues changed by under 1 minute, 3rd Avenue +1.6 minutes. Probe-vehicle runs on single streets, not door-to-door trips."},
    {"citation": "INRIX blog, first week of the 14th Street busway (October 2019).", "doi": None,
     "finding": "No discernible change in performance on neighbouring roads in the first week."},
]
ALT = [
    "Year-to-year drift of the contrast between the 14th Street corridor and the control corridors (seen in the design run: +3.4% from 2017-18 to 2018-19 in the plain year-over-year DiD), which the summer-netted estimator is meant to remove.",
    "The L train weeknight and weekend slowdown (27 April 2019 to 26 April 2020), present in both July-September 2019 and October 2019-February 2020; the primary sample is weekday daytime when the L ran normally.",
    "The M14 Select Bus Service (1 July 2019), present in both netted periods.",
    "Changes in which trips taxis serve (shorter or longer trips within a zone pair), which would move duration and distance together.",
    "Construction or events specific to one corridor in autumn 2019 (for example Hudson Yards in the control-adjacent West Chelsea zone, which is excluded from every group).",
    "October 2019 includes 1-2 October, before the busway, which dilutes the October month by about 6%.",
]
COMMON_PLAN = ("Data: TLC yellow-taxi trip records (monthly parquet, d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_YYYY-MM.parquet), "
               "July 2016 to February 2020, held in ~/opt/nyc-concordance/tlc_yellow_1720/. Scripts: analyses/street_space/common.py "
               "(zones, windows), extract.py (aggregation by directed pair, date and hour; filter 0<mi<=50, 60 s to 3 h, 0.5-50 mph), "
               "series.py (monthly contrast c_m: treated pairs minus control pairs of pair-demeaned mean log outcome; pairs with at least "
               "20 trips in every month), test.py (the estimator E and its standard error), all committed before this registration. "
               "Treated: directed pairs between {Meatpacking/West Village West 158, West Village 249, East Chelsea 68, Greenwich Village North 113} "
               "and {East Village 79, Stuy Town 224, Alphabet City 4, Gramercy 107}. Control: the same kind of east-west pairs in Midtown "
               "({48, 50, 100, 230} with {170, 162, 233, 229}) and downtown ({231, 125, 211} with {148, 232, 144, 45}). "
               "Sample: weekdays except federal holidays, pickup hour 07 to 18. d_m = c_m - c_(m-12). "
               "E = mean d_m over October 2019 to February 2020 minus mean d_m over July to September 2019. "
               "se = s*sqrt(1/5+1/3), s = sd of d_m from July 2017 to September 2019; 95% interval E +/- 1.96 se; percent = 100(exp(.)-1). "
               "No resampling, so no seed enters the verdict. Verdict by PRECEDENCE rules 1 and 2; conditions are on interval bounds (rule 10). "
               "Secondary, not deciding: all-day busway hours (06-21) and overnight (22-05) samples; the plain year-over-year DiD with a "
               "day bootstrap (estimate.py, 2,000 draws, seed 20261113); per-pair changes; a monthly event-study figure. "
               "The pair set is fixed by the 20-trips-every-month rule over the whole input, so adding the post months may drop a pair "
               "and move the placebo values slightly; the outcome reports both.")

SEEN = [
    "All yellow-taxi trips between the listed zones from July 2016 to September 2019, aggregated (design run: data/derived/street_space/design.json, test_design.json, series_pre.csv).",
    "The parquet files for October 2019 to February 2020 were downloaded but not opened or read; no trip after 30 September 2019 has been aggregated or seen.",
    "From the press: DOT's December 2019 summary (side streets +0 to 2 minutes) and INRIX's first-week note, as listed in literature.",
    "ATVC (7ym2-wayt) row counts for 12th to 18th Streets 2017-2021 (counts only, no volumes): only four count locations, all in October 2019, so no volume test of evaporation is possible.",
]

time_rec = {
    "id": "street-busway14-crosstown-time",
    "kind": "conflict",
    "statement": ("After the 14th Street busway began on 3 October 2019, weekday daytime yellow-taxi trips between zones on the west and east "
                  "sides of the 14th Street corridor lengthened by about 5% relative to comparable crosstown zone pairs in Midtown and "
                  "downtown, net of the same comparison in the preceding summer."),
    "edge": {"cause": "busway (removal of through car traffic from 14th Street)", "effect": "door-to-door crosstown taxi trip duration"},
    "graph_evidence": GRAPH, "literature": LIT,
    "prediction": {
        "direction": "+",
        "magnitude": ("E between +2% and +10%, central +5%. Reasoning: DOT's probe runs found 0-2 minutes added on parallel streets "
                      "over 3rd to 9th Avenue (roughly 0-20% of a 10-minute peak run); a door-to-door taxi trip between these zones spends "
                      "perhaps half its time on the crosstown leg, and some through traffic evaporates or shifts. The kind is 'conflict' "
                      "because the evaporation literature (Cairns et al.) and DOT's summary lead to an expectation of little or no "
                      "lengthening, and this registration bets against them."),
        "support_if": "E >= +2.0% AND the lower 95% bound of E is above 0.",
        "refute_if": "The upper 95% bound of E is below +5.0% (the predicted central lengthening is excluded).",
    },
    "discrimination": {
        "rule": 8, "se_log_design": wt["se_log"], "predicted_log": 0.0488,
        "D_if_estimate_at_prediction": round((0.0488 / wt["se_log"]) ** 2, 2),
        "placebo_E_pct": {"2017": wt["2017"]["E_pct"], "2018": wt["2018"]["E_pct"]},
        "note": ("With the design se of 1.69% (log), an estimate at the predicted +5% is 2.9 se from zero (D = 8.4 >= 4); a true effect "
                 "of zero meets refute_if with probability about 0.83, and a true +5% meets support_if with probability about 0.82. "
                 "Both placebo seasons (2017, 2018) lie inside +/-1.3%."),
    },
    "plan": COMMON_PLAN + " Outcome: log trip duration (s_lt).",
    "alternatives": ALT,
    "data_seen_before_registration": SEEN,
    "design_file": "data/derived/street_space/test_design.json",
    "scripts": ["analyses/street_space/common.py", "analyses/street_space/extract.py", "analyses/street_space/series.py",
                "analyses/street_space/test.py", "analyses/street_space/estimate.py"],
    "seed": 20261113, "draws": 2000,
    "prior": 0.35,
    "registrant": "Claude (agent, street-space task), 13 November 2026",
}

dist_rec = {
    "id": "street-busway14-crosstown-detour",
    "kind": "confirmation",
    "statement": ("After the 14th Street busway began, weekday daytime yellow-taxi trips between the west and east sides of the 14th "
                  "Street corridor became about 1.5% longer in metered distance relative to comparable crosstown pairs, net of the "
                  "preceding summer: displaced cars drove further, not only slower."),
    "edge": {"cause": "busway", "effect": "crosstown taxi trip distance (detour, added vehicle-miles)"},
    "graph_evidence": GRAPH, "literature": LIT,
    "prediction": {
        "direction": "+",
        "magnitude": ("E between +0.5% and +4%, central +1.5%. Reasoning: trips that used 14th Street must use one-way side streets "
                      "(12th, 13th, 15th, 16th, 17th) or turn off at the next avenue; a detour of a block or two on a 1.5-mile trip is "
                      "3-7% for the trips affected, perhaps a third to a half of them."),
        "support_if": "E >= +0.5% AND the lower 95% bound of E is above 0.",
        "refute_if": "The upper 95% bound of E is below +1.5% (the predicted central detour is excluded).",
    },
    "discrimination": {
        "rule": 8, "se_log_design": wd["se_log"], "predicted_log": 0.0149,
        "D_if_estimate_at_prediction": round((0.0149 / wd["se_log"]) ** 2, 2),
        "placebo_E_pct": {"2017": wd["2017"]["E_pct"], "2018": wd["2018"]["E_pct"]},
        "note": "Design se 0.50% (log); an estimate at +1.5% is 3.0 se from zero (D = 9.0).",
    },
    "plan": COMMON_PLAN + " Outcome: log metered trip distance (s_ld).",
    "alternatives": ALT,
    "data_seen_before_registration": SEEN,
    "design_file": "data/derived/street_space/test_design.json",
    "scripts": time_rec["scripts"],
    "seed": 20261113, "draws": 2000,
    "prior": 0.45,
    "registrant": "Claude (agent, street-space task), 13 November 2026",
}

if __name__ == "__main__":
    import sys
    rec = {"time": time_rec, "detour": dist_rec}[sys.argv[1]]
    rec["script_commit"] = sys.argv[2]
    print(claims.register(rec))
