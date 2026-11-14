"""Registrations for the busway follow-up: M14 bus speed and pedestrian injuries (run before outcome data)."""
from __future__ import annotations

import json
import sys

from concord import claims
from analyses.street_space.common import DER

bus_d = json.loads((DER / "bus_design.json").read_text())
ped_d = json.loads((DER / "peds_power.json").read_text())

LIT_BUS = [
    {"citation": "NYC DOT / Sam Schwartz Engineering, 14th Street Transit & Truck Priority Pilot preliminary report (fall 2019), as summarised by the Mayor's Office and Streetsblog, 18 December 2019.",
     "doi": None, "finding": "Bus travel times on the 14th Street corridor 22-47% shorter than in May/October 2018 (before the SBS); M14A/D weekday ridership +24%, weekend +30%."},
]
GRAPH_BUS = [{"concepts": "bus lane, bus rapid transit, transit priority", "n_findings": 2, "direction": "none on speed",
              "summary": "Variable search 'bus lane' finds one variable (bus stops on a bus-only lane and pedestrian collisions, Lima, PMID 24357516); 'bus' finds BRT station density and walking (PMID 24096625). No finding on bus speed or travel time (data/derived/street_space/graph_evidence.json).",
              "pubmed_ids": [24357516, 24096625]}]

bus = {
    "id": "street-busway14-m14-speed",
    "kind": "confirmation",
    "statement": ("On weekdays in October 2019 to February 2020 the M14A and M14D Select Bus Service ran at least 4% faster, "
                  "relative to the other Manhattan bus routes, than in July to September 2019, when the SBS ran without the busway."),
    "edge": {"cause": "busway (14th Street closed to through cars)", "effect": "M14 route-average bus speed"},
    "graph_evidence": GRAPH_BUS, "literature": LIT_BUS,
    "prediction": {"direction": "+",
                   "magnitude": ("DiD between +4% and +20%, central +10%. The corridor from 3rd to 9th Avenue is roughly 40% of each route's "
                                 "length and more of its running time; DOT's 22-47% corridor gain includes the SBS of July 2019, which the "
                                 "summer baseline already contains."),
                   "support_if": "DiD >= +4% AND lower 95% bound above 0.",
                   "refute_if": "Upper 95% bound below +4%."},
    "discrimination": {"rule": 8, "se_log_design": round(bus_d["sd_log"], 4), "predicted_log": 0.0953,
                       "D_if_estimate_at_prediction": round((0.0953 / bus_d["sd_log"]) ** 2, 1),
                       "note": f"se from {bus_d['n']} placebo DiDs (each other Manhattan route as if treated, seasons 2021-2023)."},
    "plan": ("analyses/street_space/bus.py (committed before this registration): data.ny.gov cudb-vcni, weekday rows, both periods, "
             "speed = total mileage / total operating time; M14A+ and M14D+ pooled; controls = other Manhattan routes present every month; "
             "DiD of log speed Oct 2019-Feb 2020 against Jul-Sep 2019; 95% interval DiD +/- 1.96 x design sd. No resampling. "
             "Rules 1, 2 and 10 (conditions on bounds)."),
    "alternatives": ["Seasonal differences between the M14 and other routes (the placebo spread covers typical ones).",
                     "SBS learning effects (riders using off-board fare more over time), which would continue after July 2019 without the busway.",
                     "Bus lane camera enforcement on 14th Street, which began with the busway and is part of the treatment.",
                     "L train slowdown (from 27 April 2019), present in both windows; it mainly raised night and weekend M14 loads."],
    "data_seen_before_registration": ["cudb-vcni: route ids, months and dimensions for Manhattan (no speeds of any 2019-20 month); speeds of all non-M14 Manhattan routes, July 2021 to February 2024 (design).",
                                      "No M14 speed has been queried or seen. From the press: DOT's December 2019 summary (22-47%)."],
    "design_file": "data/derived/street_space/bus_design.json",
    "scripts": ["analyses/street_space/bus.py"],
    "prior": 0.75,
    "registrant": "Claude (agent, street-space task), 13 November 2026",
}

peds = {
    "id": "street-busway14-ped-injuries",
    "kind": "confirmation",
    "statement": ("In the three years after the busway began (October 2019 to September 2022), crashes injuring or killing a pedestrian on "
                  "14th Street between Ninth and Third Avenues fell by about a third relative to 23rd, 34th, 42nd and 57th Streets over the "
                  "same avenues, compared with the five years before."),
    "edge": {"cause": "busway (through car traffic removed)", "effect": "pedestrian injury crashes on the corridor"},
    "graph_evidence": [{"concepts": "pedestrian injury, traffic volume, bus lane", "n_findings": 1, "direction": "against (bus stops on bus lanes)",
                        "summary": "The graph has many pedestrian-injury variables but none for a bus-only street or volume reduction; the nearest is Lima, where crossings at bus stops on bus-only lanes had more pedestrian collisions, OR 2.36 (1.02-5.42) (PMID 24357516, abstract read). Busways concentrate buses and bus stops, which this finding links to more collisions.",
                        "pubmed_ids": [24357516]}],
    "literature": [{"citation": "Cairns et al. 2002 (as in street-busway14-crosstown-time)", "doi": "10.1680/muen.2002.151.1.13",
                    "finding": "Traffic on a treated street falls substantially after reallocation; pedestrian crashes scale with vehicle volume."}],
    "prediction": {"direction": "-",
                   "magnitude": "Ratio of rate ratios 0.65 (range 0.45 to 0.85).",
                   "support_if": "RR <= 0.85 AND upper 95% bound below 1.",
                   "refute_if": "Lower 95% bound above 0.65 (the predicted central fall is excluded)."},
    "discrimination": {"rule": 8, "pre_counts_per_year_treated": round(ped_d["treated_per_year"], 1),
                       "pre_counts_per_year_controls": round(ped_d["controls_per_year"], 1),
                       "se_log_expected": ped_d["mde"]["post3.00y_pre5y"]["se_log_poisson"],
                       "D_if_estimate_at_prediction": round((0.431 / ped_d["mde"]["post3.00y_pre5y"]["se_log_poisson"]) ** 2, 1),
                       "note": ("Power from persons injured 2014-2018 (peds_power.json); the test counts crashes, slightly fewer, so the se will be "
                                "a little larger. A five-month post window (Oct 2019-Feb 2020) has a minimum detectable change of about 48% and is "
                                "secondary only. Year-to-year sd of the log ratio 2013-2018 was 0.15, consistent with Poisson noise.")},
    "plan": ("analyses/street_space/peds_test.py and peds_common.py (committed before this registration): h9gi-nx95 crashes with a pedestrian "
             "injured or killed, located within 30 m of each corridor segment between the 9th and 3rd Avenue intersections; pre Oct 2014-Sep 2019, "
             "post Oct 2019-Sep 2022; ratio of rate ratios with Poisson interval. Rules 1, 2 and 10."),
    "alternatives": ["The pandemic changed traffic and walking differently in Midtown (offices, theatres) and around 14th Street (residential, Union Square).",
                     "Other street changes on the control corridors (for example 34th Street and 42nd Street bus lanes, Open Streets).",
                     "Geocoding changes in the NYPD data over time, common to all corridors.",
                     "Pedestrian volumes on 14th Street rose after the busway, which would raise exposure and hide a fall in risk per pedestrian."],
    "data_seen_before_registration": ["h9gi-nx95: pedestrian-injury crashes in the bounding box, January 2013 to 30 September 2019 (design, peds_power.json); "
                                      "crash locations at 9th and 3rd Avenue intersections before October 2019 (geometry). No crash after 30 September 2019 has been queried."],
    "design_file": "data/derived/street_space/peds_power.json",
    "scripts": ["analyses/street_space/peds_test.py", "analyses/street_space/peds_common.py", "analyses/street_space/peds_power.py"],
    "prior": 0.35,
    "registrant": "Claude (agent, street-space task), 13 November 2026",
}

if __name__ == "__main__":
    rec = {"bus": bus, "peds": peds}[sys.argv[1]]
    rec["script_commit"] = sys.argv[2]
    print(claims.register(rec))
