"""Write the outcomes of rlc-expansion-rearend and rlc-expansion-injuries from rlc_did_results.json."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from concord import claims  # noqa: E402

D = ROOT / "data/derived/street_safety"
d = json.loads((D / "rlc_did_results.json").read_text())
ex = json.loads((D / "exploratory_placebo_adjusted.json").read_text())["placebo_adjusted"]
R, P, S = d["results"], d["placebo_one_year_earlier"], d["excluding_sip_sites"]["results"]
site_src = d["site_sources"]
ds = sorted({s["dataset"] for s in site_src})
sources = d["crash_sources"] + [
    {"kind": "nyc-open-data", "datasets": ds, "name": "Parking Violations Issued FY2024-FY2027, violation code 7",
     "n_queries": len(site_src), "rows_updated_at": sorted({s["rows_updated_at"] for s in site_src}),
     "query_example": site_src[-1]["query"], "note": "full list of source records in data/derived/street_safety/rlc_sites.json"},
    {"kind": "nyc-open-data", "dataset": "xc4v-ntf4", "name": "VZV Leading Pedestrian Interval Signals (control pool)"},
    {"kind": "nyc-open-data", "dataset": "shr7-eqdc", "name": "VZV Street Improvement Projects (SIP) Intersections"},
    {"kind": "other", "name": "OpenStreetMap intersections via Overpass API, OSM base 2026-07-24", "licence": "ODbL 1.0"},
    {"kind": "sysgraph", "file": "data/derived/street_safety/graph_check.json"},
]
f = lambda r: f"{r['rr']:.3f} ({r['lo']:.3f}-{r['hi']:.3f})"
rb = lambda o: R[o]["robust_bounds_B20000_seeds1to10"]
common_notes = (
    f"Design: {d['n_treated']} intersections first ticketed January-August 2026, 3 matched LPI intersections each "
    f"(pool {d['n_pool']}), {d['n_crashes']} geolocated crashes January 2023-October 2026. "
    f"All outcomes, ratio of ratios (95% interval): rear-end proxy {f(R['rear_end'])}; persons injured or killed {f(R['injured'])}; "
    f"pedestrians injured or killed {f(R['ped'])}; 'Traffic Control Disregarded' crashes {f(R['tcd'])}; all crashes {f(R['all'])}. "
    f"Registered placebo (same sites and windows one year earlier, before any camera): rear-end {f(P['rear_end'])}; injured {f(P['injured'])}; "
    f"pedestrians {f(P['ped'])}; red-running {f(P['tcd'])}; all crashes {f(P['all'])}. "
    "The placebo shows the design producing ratios of 1.25-1.36 where no camera existed. The likely reason is that controls were "
    "matched on their pre-window crash counts, so controls with unusually high counts were chosen and then fell (regression to the "
    "mean in the controls), while the camera sites, chosen by DOT on other grounds, did not fall in the same way. The design therefore "
    "carries a bias of roughly +25% in every outcome, and the registered estimates must be read against the placebo. "
    f"Excluding the {d['n_treated'] - d['excluding_sip_sites']['n']} sites near a 2024-26 street improvement project changes little: rear-end {f(S['rear_end'])}, injured {f(S['injured'])}. "
    "EXPLORATORY, not a test (rule 4): the ratio of the 2026 estimate to the placebo estimate, with a joint bootstrap, is "
    f"rear-end {ex['rear_end']['ratio']} ({ex['rear_end']['lo']}-{ex['rear_end']['hi']}), persons injured {ex['injured']['ratio']} "
    f"({ex['injured']['lo']}-{ex['injured']['hi']}), pedestrians {ex['ped']['ratio']} ({ex['ped']['lo']}-{ex['ped']['hi']}), "
    f"all crashes {ex['all']['ratio']} ({ex['all']['lo']}-{ex['all']['hi']}). "
    "Read this way, the cameras show no clear rise in rear-end crashes and a fall of about 18% in persons injured, but the adjustment was chosen after the data were seen."
)
research = [
    {"question": "Publish NYC red-light camera locations with coordinates, approach and activation (and warning-period) dates as open data.",
     "data": "NYC DOT camera inventory", "design": "site-level before-after with exact dates; removes ticket-based geocoding (117 of 585 approach names could not be located)", "priority": "high"},
    {"question": "Repeat the test in late 2027 with 18-21 months of post data and a comparison group that is not selected on pre-period counts (for example, later-activated cameras as not-yet-treated controls, or empirical Bayes expected counts).",
     "data": "h9gi-nx95, bm4k-52h4, ticket data through 2027", "design": "staggered difference in differences or empirical Bayes before-after (Hauer)", "priority": "high"},
    {"question": "Which intersections did DOT choose for the 2026 expansion and on what criteria (crash history, violation counts, equity)?",
     "data": "DOT siting memo", "design": "model the selection to correct for it", "priority": "medium"},
    {"question": "The graph has no association between red-light cameras and rear-end or right-angle crashes; add Erke 2009, Hoye 2013 and the Cochrane review. Three of its LPI and traffic-calming records turn percentage reductions into odds ratios or reverse the exposure.",
     "data": "System Public Graph", "design": "curation", "priority": "medium"},
]
o1 = {
    "id": "rlc-expansion-rearend", "verdict": "confirmed",
    "city_effect": {"label": "Rear-end proxy crashes within 50 m, camera intersections vs matched controls, post vs same months of 2024-25 (ratio of ratios)",
                    "estimate": R["rear_end"]["rr"], "lo": R["rear_end"]["lo"], "hi": R["rear_end"]["hi"], "scale": "ratio of ratios", "null": 1, "n": d["n_treated"]},
    "graph_effect": {"label": "Not in the graph. Meta-analyses: rear-end crashes +40% (Erke 2009, n.s.), +39% (Hoye 2013); NYC DOT reports rear-end injury crashes -60% at old sites",
                     "estimate": 1.39, "lo": None, "hi": None, "scale": "ratio", "null": 1},
    "sources": sources,
    "prediction_scored": (f"hit on the registered condition, weak as evidence of a camera effect. Ratio of ratios {f(R['rear_end'])}; lower bound above 1.00 under the registered "
        f"seed and under seeds 1-10 with 20,000 draws (lower bounds {min(x[0] for x in rb('rear_end')):.3f}-{max(x[0] for x in rb('rear_end')):.3f}); rule 8 D = {R['rear_end']['rule8']['D']} (>= 4). "
        f"Under rule 1 the verdict is confirmed. But the registered placebo year gives {f(P['rear_end'])}, almost the same, so the design cannot separate a camera effect from "
        "the bias it shows without cameras (named alternative: regression to the mean). The estimate contradicts NYC DOT's report of fewer rear-end crashes; it does not show that the cameras caused an increase."),
    "settle": "A comparison that does not select controls on pre-period counts (not-yet-treated camera sites, or empirical Bayes expected counts), exact activation dates, and a longer post period.",
    "research_needed": research, "figures": ["figures/street_safety/rlc_ratio_of_ratios.png", "figures/street_safety/rlc_feb_cohort_quarterly.png", "figures/street_safety/rlc_sites_map.png"],
    "notes": common_notes,
}
o2 = {
    "id": "rlc-expansion-injuries", "verdict": "unsettled",
    "city_effect": {"label": "Persons injured or killed within 50 m, camera intersections vs matched controls, post vs same months of 2024-25 (ratio of ratios)",
                    "estimate": R["injured"]["rr"], "lo": R["injured"]["lo"], "hi": R["injured"]["hi"], "scale": "ratio of ratios", "null": 1, "n": d["n_treated"]},
    "graph_effect": {"label": "Hu and Cicchino 2017 (graph, PMID 28454859): fatal crashes at signalized intersections -14% after activation; Cochrane 2005 injury crashes RR 0.71 (0.55-0.92)",
                     "estimate": 0.71, "lo": 0.55, "hi": 0.92, "scale": "rate ratio", "null": 1},
    "sources": sources,
    "prediction_scored": (f"miss on the registered conditions, neither met. Ratio of ratios {f(R['injured'])}: the upper bound is not below 1.00 and the lower bound is not above 0.95 "
        f"(robust lower bounds {min(x[0] for x in rb('injured')):.3f}-{max(x[0] for x in rb('injured')):.3f}). Rule 8 D = {R['injured']['rule8']['D']}. "
        f"Pedestrians (secondary, not deciding): {f(R['ped'])}, placebo {f(P['ped'])}. Against the placebo year ({f(P['injured'])}) the injured estimate is lower, "
        "which points to a reduction, but that comparison was not registered."),
    "settle": "As for rlc-expansion-rearend: a comparison group not selected on pre-period counts, exact activation dates, and 18 months or more of post data.",
    "research_needed": research, "figures": ["figures/street_safety/rlc_ratio_of_ratios.png", "figures/street_safety/rlc_feb_cohort_quarterly.png"],
    "notes": common_notes,
}
for o in (o1, o2):
    print(claims.outcome(o))
