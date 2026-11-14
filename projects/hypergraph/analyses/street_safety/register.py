"""Register the two red-light camera claims. Run once, after power.py and before rlc_did.py."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from concord import claims  # noqa: E402

power = json.loads((ROOT / "data/derived/street_safety/power.json").read_text())
gc = json.loads((ROOT / "data/derived/street_safety/graph_check.json").read_text())
SCRIPT_COMMIT = sys.argv[1]

graph = [{
    "note": "Variable search (analyses/street_safety/graph_collect.py). Red-light camera associations come from two studies; none concerns rear-end or right-angle crashes. Abstracts checked: data/derived/street_safety/graph_check.json (13 of 21 relied-on records correct, 7 wrong, 1 unverifiable).",
    "findings": [
        {"pubmed_id": 28454859, "variable_1_name": "activating red light cameras", "variable_2_name": "all fatal crashes at signalized intersections", "statistic_type": "percent change", "statistic_value": -14, "abstract_check": "correct"},
        {"pubmed_id": 28454859, "variable_1_name": "activating red light cameras", "variable_2_name": "fatal red light running crashes", "statistic_type": "percent change", "statistic_value": -21, "abstract_check": "correct"},
        {"pubmed_id": 28454859, "variable_1_name": "Removing red light cameras (2010-2014)", "variable_2_name": "all fatal crashes at signalized intersections", "statistic_type": "percent change", "statistic_value": 8, "abstract_check": "wrong: abstract gives +16% for these 14 cities; +8% is for all 19"},
        {"pubmed_id": 32195995, "variable_1_name": "Red light camera laws", "variable_2_name": "motor vehicle crash fatality rate", "statistic_type": "coefficient", "statistic_value": -0.06, "abstract_check": "direction correct; value not in abstract"},
    ]}]
lit = [
    {"citation": "Erke A (2009). Red light for red-light cameras? A meta-analysis of the effects of red-light cameras on crashes. Accid Anal Prev 41(5):897-905.", "doi": "10.1016/j.aap.2008.08.011",
     "finding": "In the best-controlled studies, rear-end crashes about +40% and right-angle crashes about -10%; all crashes about +15%; none significant. Results are more favourable without control for regression to the mean."},
    {"citation": "Hoye A (2013). Still red light for red light cameras? An update. Accid Anal Prev 55:77-89.", "doi": "10.1016/j.aap.2013.02.017",
     "finding": "Right-angle crashes -13%, rear-end +39%; right-angle injury crashes -33%, rear-end injury crashes +19%."},
    {"citation": "Hu W, Cicchino JB (2017). Effects of turning on and off red light cameras on fatal crashes in large U.S. cities. J Safety Res 61:141-148.", "doi": "10.1016/j.jsr.2017.02.019",
     "finding": "Fatal crashes at signalized intersections 14% lower after activation; 16% higher after removal (2010-2014 removals)."},
    {"citation": "Aeron-Thomas AS, Hess S (2005). Red-light cameras for the prevention of road traffic crashes. Cochrane Database Syst Rev CD003862.", "doi": "10.1002/14651858.CD003862.pub2",
     "finding": "Injury crashes RR 0.71 (0.55-0.92) in a small number of controlled before-after studies; rear-end effects inconsistent."},
    {"citation": "NYC DOT (2025-2026). NYC Red Light Camera Program addendum and press release of October 2026.", "doi": None,
     "finding": "At existing camera intersections, right-angle injury collisions -70% and rear-end injury collisions about -60% against a pre-installation average. No control group; this disagrees in sign with the meta-analyses on rear-end crashes."},
]
common_alt = [
    "Regression to the mean: new camera sites were chosen for high crash or violation counts; matching on pre-period crash counts and the two-year pre window reduce, but do not remove, this bias.",
    "Concurrent treatments at the same intersections in 2025-26 (street improvement projects, LPIs, daylighting, signal retiming); the SIP-excluded check addresses part of this.",
    "Traffic diverted from camera intersections to nearby streets; controls are at least 300 m from every camera, which limits but does not exclude spillover.",
    "A warning or test period before the first ticket, or tickets dated after the violation, shifting the true activation month.",
    "Changes in police crash reporting or geocoding in 2026 that differ between camera and control intersections.",
]
plan_common = (f"Analysis script analyses/street_safety/rlc_did.py at commit {SCRIPT_COMMIT} (B = 2000 bootstrap draws, seed 20261113; "
    "robustness rerun with B = 20000 and seeds 1-10). Treatment data: red-light camera intersections and the first month with "
    "tickets, from Parking Violations Issued FY2024-FY2027 (8zf9-spf8, m5vz-tzqv, 9mwx-gamw, pvqr-7yc4; violation code 7, sampled "
    "on the 1st and 15th of each month; analyses/street_safety/rlc_sites.py), geocoded to OpenStreetMap intersections and the LPI "
    "gazetteer (geocode_sites.py). Treated: intersections first ticketed January-August 2026 with no ticket in earlier sampled months. "
    "Post window: months a+1 to a+9 (a = first month), ending October 2026; pre window: the same calendar months in 2024 and 2025. "
    "Controls: 3 LPI intersections (xc4v-ntf4, LPI before 2024) per treated site, same borough, at least 300 m from any camera, "
    "matched on the pre-window count of all crashes. Crashes (h9gi-nx95, with vehicles bm4k-52h4) within 50 m. Estimator: ratio of "
    "ratios (treated post/pre over control post/pre); 95% percentile interval from a cluster bootstrap over matched sets. "
    "Secondary: placebo one year earlier; SIP sites (shr7-eqdc, 2024-2026) excluded. "
    f"Expected discrimination before data (power.py, assumed rates): {json.dumps({k: power[k] for k in ('n_treated', 'post_site_years')})}.")

r1 = {
    "id": "rlc-expansion-rearend",
    "kind": "conflict",
    "statement": "At the intersections where New York City switched on red-light cameras in January-August 2026, rear-end crashes rose relative to matched signalized intersections, as the meta-analyses predict and contrary to NYC DOT's report of fewer rear-end injury crashes at its camera sites.",
    "graph_evidence": graph,
    "literature": lit,
    "prediction": {"direction": "+",
        "magnitude": "Ratio of ratios for the rear-end proxy (crashes citing 'Following Too Closely', or with an in-traffic vehicle struck at 'Center Back End') between 1.10 and 1.60.",
        "support_if": "The 95% interval of the ratio of ratios lies above 1.00 and the test discriminates (rule 8: D >= 4 against the band's geometric centre, 1.33).",
        "refute_if": "The upper 95% bound is below 1.10 (the city data exclude the meta-analytic increase; a decrease as NYC DOT reports would fall here).",
        "rule8": power["rear_end"]},
    "plan": plan_common + " Primary outcome: rear-end proxy count. Secondary (reported, not deciding): crashes citing 'Traffic Control Disregarded' (red-running proxy), predicted ratio 0.50-0.85.",
    "alternatives": common_alt + ["More traffic or congestion at camera sites in 2026 raising all crash types; the all-crash ratio is reported to show this."],
    "prior": 0.3,
    "registrant": "street-safety agent (Claude Opus 5.5), for J. Vernon",
}
r2 = {
    "id": "rlc-expansion-injuries",
    "kind": "confirmation",
    "statement": "At the intersections where New York City switched on red-light cameras in January-August 2026, persons injured or killed in crashes fell relative to matched signalized intersections.",
    "graph_evidence": graph,
    "literature": lit,
    "prediction": {"direction": "-",
        "magnitude": "Ratio of ratios for persons injured or killed between 0.70 and 0.95. Pedestrians injured or killed: predicted 0.75-0.95, a pre-specified secondary outcome that is not expected to discriminate (see rule8_ped).",
        "support_if": "The upper 95% bound of the ratio of ratios for persons injured or killed is below 1.00 and the test discriminates (rule 8: D >= 4 against the band's geometric centre, 0.815).",
        "refute_if": "The lower 95% bound is above 0.95 (the city data exclude a reduction of 5% or more).",
        "rule8": power["injured"], "rule8_ped": power["ped"]},
    "plan": plan_common + " Primary outcome: persons injured plus persons killed. Secondary (reported, not deciding): pedestrians injured or killed; all crashes.",
    "alternatives": common_alt,
    "prior": 0.3,
    "registrant": "street-safety agent (Claude Opus 5.5), for J. Vernon",
}
for r in (r1, r2):
    print(claims.register(r))
