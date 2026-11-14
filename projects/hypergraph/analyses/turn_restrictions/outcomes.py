"""Write the outcomes of turn-calming-ped, turn-calming-leftturn and turn-calming-displacement from
data/derived/turn_restrictions/did_results.json (registered) and did_explore.json (exploratory)."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from concord import claims

D = ROOT / "data/derived/turn_restrictions"
r = json.loads((D / "did_results.json").read_text())
x = json.loads((D / "did_explore.json").read_text())
fs = json.loads((D / "fetch_sources.json").read_text())
sites = json.loads((D / "sites.json").read_text())
SOURCES = [sites["source"], fs["crashes"], fs["left_vehicles"]]
FIGS = ["figures/turn_restrictions/event_time.png", "figures/turn_restrictions/forest.png",
        "figures/turn_restrictions/sites_map.png"]
GRAPH = {"label": "No graph evaluation of turn calming or turn bans. Nearest: traffic-calming measures on local-road "
         "intersections, Montreal, collisions IRR 0.31 (0.12-0.86), weak evidence overall (PMID 37288501). "
         "Literature outside the graph: NYC DOT uncontrolled before-after, pedestrian injuries -18% (turn calming), "
         "left-turn pedestrian and bicyclist injuries -41% (51 left-turn restrictions, 2016 study).",
         "estimate": 0.82, "lo": None, "hi": None, "scale": "ratio, DOT turn-calming page (-18%)", "null": 1}
RN = [
    {"question": "Does turn calming reduce pedestrian injuries once the pre-installation decline at selected sites is "
                 "accounted for?", "data": "sm2x-35i7 install dates; h9gi-nx95; DOT's site-selection crash windows",
     "design": "Register a model with site-specific pre-trends or an empirical Bayes before-after with a safety "
               "performance function fitted on untreated signalized intersections (FHWA method), so that "
               "regression to the mean is modelled rather than assumed away", "priority": "high"},
    {"question": "Do left-turn bans (not calming) reduce pedestrian injuries, and where do the turns go?",
     "data": "A dated list of left-turn prohibitions (DOT sign orders or the CSCL/LION turn-restriction layer by "
             "date), which is not on NYC Open Data", "design": "Staggered DiD as here, with a displacement ring along "
             "the detour route", "priority": "high"},
    {"question": "What does a turn ban or calming do to vehicle throughput at the intersection?",
     "data": "Signal-timing and turning-movement counts at treated intersections (DOT ATR or video counts); "
             "i4gi-tjb9 covers highways only", "design": "Before-after counts at treated and comparison intersections",
     "priority": "medium"},
]


def ce(o, label):
    p = r["primary"][o]
    return {"label": label, "estimate": p["ror"], "lo": p["lo"], "hi": p["hi"], "scale": "ratio of ratios", "null": 1,
            "n": p["n_treated_sites"]}


def note(o):
    e = x[o]
    return (f"Exploratory, written after the registered result was seen (analyses/turn_restrictions/did_explore.py): a "
            f"placebo installation 12 months early gives a ratio of {e['placebo_12m_early']['ror']} "
            f"({e['placebo_12m_early']['lo']}-{e['placebo_12m_early']['hi']}), so treated sites were already declining "
            f"relative to later-treated sites before installation. Extending that pre-installation trend gives a "
            f"trend-adjusted ratio of {e['trend_adjusted']['ror']} ({e['trend_adjusted']['lo']}-"
            f"{e['trend_adjusted']['hi']}). The likely cause is the comparison group: DOT chooses sites after crash "
            f"clusters, so treated sites are past their peak while later-treated sites in the same calendar months "
            f"are still approaching theirs. The registered ratio therefore mixes any treatment effect with regression "
            f"to the mean in opposite directions in the two groups. Checks fixed in did.py: 30 m radius "
            f"{r['checks'][o + '_r30']['ror'] if o + '_r30' in r['checks'] else 'n/a'}; cohorts avoiding March-June "
            f"2020 {r['checks'][o + '_avoid2020']['ror']} ({r['checks'][o + '_avoid2020']['lo']}-"
            f"{r['checks'][o + '_avoid2020']['hi']}).")


SETTLE = ("A design that separates the treatment from regression to the mean: empirical Bayes before-after with a "
          "safety performance function, or a comparison group of untreated signalized intersections matched on the "
          "crash history DOT used for selection, registered before the data are read. DOT's site-selection lists "
          "(which crash years it used) would let the selection window be excluded.")

OUT = [
    {"id": "turn-calming-ped", "verdict": "confirmed",
     "city_effect": ce("ped", "Pedestrians injured or killed within 40 m, 24 months after vs 24 months before "
                       "installation, treated vs later-treated calming sites, stacked cohorts 2016Q3-2023Q2"),
     "prediction_scored": "hit: ratio 0.848 (0.779-0.924) lies inside the predicted 0.80-0.97 and the upper bound is "
                          "below 1.00, so support_if is met by 0.076 on the upper bound. The causal reading is not "
                          "supported by the exploratory placebo (see notes).",
     "notes": note("ped") + " Treated sites: 1,966 pedestrians injured or killed before, 1,706 after.",
     "prior": 0.35},
    {"id": "turn-calming-leftturn", "verdict": "confirmed",
     "city_effect": ce("lt", "Crashes with a vehicle 'Making Left Turn' within 40 m, 24 months after vs before, "
                       "treated vs later-treated calming sites"),
     "prediction_scored": "hit: ratio 0.904 (0.847-0.965) inside 0.70-0.95 with upper bound below 1.00 (margin 0.035). "
                          "The placebo makes the causal reading doubtful (see notes).",
     "notes": note("lt") + " Treated sites: 3,242 left-turn crashes before, 2,683 after. 'Making Left Turn' records "
              "halve citywide from 2019 to 2020 (24,582 to 12,636 vehicles); calendar-matched controls absorb this.",
     "prior": 0.45},
    {"id": "turn-calming-displacement", "verdict": "unsettled",
     "city_effect": ce("ped_ring", "Pedestrians injured or killed 50-200 m from the site (excluding crashes within "
                       "40 m of any calming site), treated vs later-treated"),
     "prediction_scored": "miss: ratio 0.923 (0.876-0.973) is below the predicted 0.93-1.07, and the interval's lower "
                          "bound 0.876 falls 0.004 outside the 0.88-1.12 required by support_if; refute_if (lower bound "
                          "above 1.00, displacement) is not met. No displacement was found; the ring declined too.",
     "notes": note("ped_ring") + f" Secondary: left-turn crashes in the ring {r['primary']['lt_ring']['ror']} "
              f"({r['primary']['lt_ring']['lo']}-{r['primary']['lt_ring']['hi']}). The ring falls with the site, "
              "which fits either a spillover benefit along calmed corridors or the same selection artefact at area "
              "level; the placebo for the ring (0.935) favours the artefact.",
     "prior": 0.5},
]

for o in OUT:
    o.pop("prior")
    o.update({"graph_effect": GRAPH, "sources": SOURCES, "settle": SETTLE, "research_needed": RN, "figures": FIGS})
    print(claims.outcome(o))
