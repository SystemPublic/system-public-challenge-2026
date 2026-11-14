"""Outcomes of street-busway14-m14-speed and street-busway14-ped-injuries (from bus_final.json, peds_final.json,
m14_ridership.json)."""
from __future__ import annotations

import json

from concord import claims
from analyses.street_space.common import DER

b = json.loads((DER / "bus_final.json").read_text())
p = json.loads((DER / "peds_final.json").read_text())
rd = json.loads((DER / "m14_ridership.json").read_text())
pr, ps = p["primary"], p["persons"]
m = b["m14_monthly_mph"]

bus = {
    "id": "street-busway14-m14-speed",
    "verdict": "confirmed",
    "city_effect": {"label": "M14A+M14D weekday speed, Oct 2019-Feb 2020 against Jul-Sep 2019, relative to other Manhattan routes",
                    "estimate": b["did_pct"], "lo": b["lo_pct"], "hi": b["hi_pct"], "scale": "% change in speed", "null": 0,
                    "n": b["n_controls"], "se_log": b["se_log"]},
    "graph_effect": None,
    "sources": [b["source"]],
    "prediction_scored": (f"hit. DiD {b['did_pct']}% ({b['lo_pct']} to {b['hi_pct']}). support_if (DiD >= 4% and lower bound above 0) is met; "
                          "the point condition of 4% is met within sampling error, since the interval runs from 1.7% to 9.4% (rule 10). "
                          "The estimate lies in the low part of the predicted range (+4% to +20%, central +10%)."),
    "settle": ("Segment-level bus speeds on 14th Street for 2019 (the MTA segment-speed series begins in 2023) would separate the corridor "
               "from the rest of each route, and a longer SBS-only baseline would separate the busway from continued SBS improvement."),
    "research_needed": [{"question": "How much of the M14 speed gain is the busway and how much is the SBS settling in?",
                         "data": "Segment speeds or AVL bus positions for 14th Street, April 2019 to February 2020.",
                         "design": "Segment-level before-after with the SBS start and the busway start as separate breaks.", "priority": "medium"}],
    "figures": ["figures/street_space/busway_tradeoff.png"],
    "notes": (f"Weekday M14 speed was {b['levels']['jul_sep_2019']['m14_mph']} mph in July to September 2019 and "
              f"{b['levels']['oct19_feb20']['m14_mph']} mph in October 2019 to February 2020; other Manhattan routes averaged "
              f"{b['levels']['jul_sep_2019']['controls_mph']} and {b['levels']['oct19_feb20']['controls_mph']} mph. The M14 was already speeding up "
              f"during the SBS-only summer (July {m['2019-07-01']}, August {m['2019-08-01']}, September {m['2019-09-01']} mph), so part of the "
              "estimate may be SBS improvement continuing; the design's placebo spread does not cover a route-specific trend of this kind. "
              "Route-wide speed dilutes the corridor gain, since each route runs well beyond 14th Street. Exploratory, ridership (MTA Bus Hourly "
              f"Ridership, 98u6-vmgs and kv7t-n8in): weekday M14A+M14D boardings averaged {rd['weekday_mean_oct18_feb19']:.0f} in October 2018 to "
              f"February 2019 and {rd['weekday_mean_oct19_feb20']:.0f} in October 2019 to February 2020 (+{100*(rd['weekday_mean_oct19_feb20']/rd['weekday_mean_oct18_feb19']-1):.0f}%), "
              "which includes the SBS and the L train slowdown; July 2019, the month the SBS began, shows half the usual count and is likely incomplete."),
}

peds = {
    "id": "street-busway14-ped-injuries",
    "verdict": "contested",
    "city_effect": {"label": "Pedestrian-injury crashes on 14th St (9th-3rd Av) relative to 23rd, 34th, 42nd, 57th St; Oct 2019-Sep 2022 against Oct 2014-Sep 2019",
                    "estimate": pr["rr"], "lo": pr["lo"], "hi": pr["hi"], "scale": "ratio of rate ratios", "null": 1,
                    "n": pr["T_pre"] + pr["T_post"] + pr["C_pre"] + pr["C_post"], "se_log": pr["se_log"]},
    "graph_effect": {"label": "Bus stops on bus-only lanes and pedestrian collisions, Lima (PMID 24357516)", "estimate": 2.36, "lo": 1.02, "hi": 5.42,
                     "scale": "odds ratio", "null": 1},
    "sources": [p["source"]],
    "prediction_scored": (f"miss. RR {pr['rr']} ({pr['lo']} to {pr['hi']}). refute_if (lower bound above 0.65) is met by a wide margin. "
                          f"14th Street had {int(pr['T_pre'])} such crashes in the five years before and {int(pr['T_post'])} in the three years after "
                          f"(25.6 and 14.7 a year); the comparison streets had {int(pr['C_pre'])} and {int(pr['C_post'])} (112.8 and 49.0 a year). "
                          "Pedestrian crashes fell on 14th Street, but by less than on the comparison streets."),
    "settle": ("Pedestrian and vehicle volumes on each corridor before and after, which would turn counts into risks per pedestrian. The pandemic "
               "emptied Midtown (34th, 42nd and 57th Streets) more than the residential area around 14th Street, so the comparison is confounded "
               "by exposure in a direction that favours this result."),
    "research_needed": [{"question": "Did risk per pedestrian on 14th Street fall after the busway?",
                         "data": "Pedestrian counts (DOT Bi-Annual Pedestrian Counts include 14th Street sites) and vehicle counts by corridor.",
                         "design": "Crashes per pedestrian-count index, before and after, against comparison corridors.", "priority": "high"}],
    "figures": ["figures/street_space/busway_tradeoff.png"],
    "notes": (f"Persons injured or killed give RR {ps['rr']} ({ps['lo']} to {ps['hi']}). Against each comparison street alone: "
              + "; ".join(f"{c} {v['rr']} ({v['lo']} to {v['hi']})" for c, v in p["by_control"].items())
              + f". In the five months before the pandemic (October 2019 to February 2020 against a year earlier) RR {p['short_window']['rr']} "
              f"({p['short_window']['lo']} to {p['short_window']['hi']}), too few crashes to say anything. Against 23rd Street, the most similar "
              "two-way crosstown street outside Midtown, the ratio is close to 1. The data show no safety gain for pedestrians on 14th Street "
              "relative to other crosstown streets, and they do not show a loss either once Midtown's emptying during the pandemic is considered."),
}

if __name__ == "__main__":
    for o in (bus, peds):
        print(claims.outcome(o))
