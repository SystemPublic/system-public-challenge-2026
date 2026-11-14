"""Registration of the held-out FHV replication (run before any FHV trip after September 2019 is read)."""
from __future__ import annotations

import json
import sys

from concord import claims
from analyses.street_space.common import DER

d = json.loads((DER / "fhv_design.json").read_text())
n, s = d["north_s_lt"], d["south_s_lt"]

rec = {
    "id": "street-busway14-fhv-north-south",
    "kind": "confirmation",
    "statement": ("On high-volume for-hire trips (Uber, Lyft and others), weekday daytime trips between East Chelsea and Stuy Town or "
                  "Gramercy (zones on both sides of Fifth Avenue north of 14th Street) lengthened by roughly 3% to 12% after the busway "
                  "began, relative to Midtown and downtown crosstown pairs, while trips between the zones south of 14th Street did not."),
    "edge": {"cause": "busway", "effect": "door-to-door crosstown trip duration for trips exposed to 14th Street"},
    "graph_evidence": [{"concepts": "none", "n_findings": 0, "direction": "none",
                        "summary": "As for street-busway14-crosstown-time: the graph holds no finding on road-space reallocation or displaced traffic."}],
    "literature": [{"citation": "critique/street-busway14-crosstown-time.md (referee, 13 November 2026)", "doi": None,
                    "finding": "Exploratory split of the yellow-taxi data, chosen after the data: the 4 north pairs +7.4% (+2.8 to +12.1), the southern pairs -1.5% (-5.5 to +2.7). This registration tests that split on data nobody has read."},
                   {"citation": "NYC DOT / Sam Schwartz Engineering preliminary report, December 2019", "doi": None,
                    "finding": "17th Street, north of 14th, +3.4 minutes from 3rd to 9th Avenue at weekday peaks; other side streets 0-2 minutes."}],
    "prediction": {
        "direction": "+",
        "magnitude": "North: E between +3% and +12%, central +7%. South: E near 0 (between -3% and +3%).",
        "support_if": "North E >= +3% AND north lower 95% bound above 0 AND south upper 95% bound below +5%.",
        "refute_if": "North upper 95% bound below +7% (the predicted central lengthening is excluded), OR south lower 95% bound above +3%.",
    },
    "discrimination": {"rule": 8, "north_se_log": n["se_log"], "south_se_log": s["se_log"], "predicted_log_north": 0.0677,
                       "D_north_if_estimate_at_prediction": round((0.0677 / n["se_log"]) ** 2, 1),
                       "placebo_yellow_2018_north_pct": n["placebo_yellow_2018_pct"], "placebo_yellow_2018_south_pct": s["placebo_yellow_2018_pct"],
                       "fleet_tracking": {"north_corr": n["corr_monthly_changes_feb_sep19"], "south_corr": s["corr_monthly_changes_feb_sep19"],
                                          "north_r": n["r_fleet"], "south_r": s["r_fleet"]},
                       "note": ("D = 7.8 at the predicted +7% (north). At the low end of the range (+3%) D is 1.5, so a small true effect "
                                "would most likely leave the claim unsettled. The fleet-difference term r is measured on February to September "
                                "2019 and cannot show a fleet difference in the winter-summer swing itself.")},
    "plan": ("analyses/street_space/fhv.py (committed before this registration). Data: TLC fhvhv_tripdata February 2019 to February 2020 "
             "(~/opt/nyc-concordance/fhvhv_1920/, from d37ci6vzurychx.cloudfront.net/trip-data/), fields trip_time and trip_miles, shared "
             "matched rides dropped, same filter, zones, weekday 07-18 sample and pair rule as the yellow tests. E_fhv(g) = FHV winter-minus-"
             "summer swing of the contrast in 2019-20 minus the mean yellow swing of 2016-17 to 2018-19 for the same subgroup; se from the yellow "
             "year-over-year spread and the FHV-yellow month difference; 95% interval E +/- 1.96 se. No resampling. Secondary: log trip_miles; "
             "the pooled t14 group. Rules 1, 2 and 10."),
    "alternatives": ["FHV trips differ from taxi trips in purpose and are routed by apps (Waze-like routing may use side streets differently).",
                     "The FHV seasonal swing may differ from the yellow swing; the design measures month-level fleet differences only.",
                     "Four north pairs carry most of the claim, so a local event in East Chelsea, Gramercy or Stuy Town (construction, the L train work on 14th Street stations) could produce it.",
                     "The yellow swing used as baseline includes years before the January 2019 congestion surcharge."],
    "data_seen_before_registration": ["FHV trips between the listed zones, February to September 2019 (design, data/derived/street_space/fhv_design.json).",
                                      "The FHV files for October 2019 to February 2020 were downloaded but not opened.",
                                      "Yellow-taxi data to February 2020, including the referee's north/south split (the hypothesis comes from it)."],
    "design_file": "data/derived/street_space/fhv_design.json",
    "scripts": ["analyses/street_space/fhv.py"],
    "prior": 0.45,
    "registrant": "Claude (agent, street-space task), 13 November 2026",
}

if __name__ == "__main__":
    rec["script_commit"] = sys.argv[1]
    print(claims.register(rec))
