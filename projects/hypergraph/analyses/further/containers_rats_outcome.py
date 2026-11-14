import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(ROOT))
from concord import claims
r = json.load(open(ROOT/"data/derived/further/results.json")); srcs = r["sources"]
p, pl, dh, dp = r["primary"], r["placebo_year"], r["dohmh_primary"], r["dohmh_placebo_year"]
S = [dict(s, data_access="open") for s in srcs]
claims.outcome({
 "id": "further-containers-rats-cd9", "verdict": "unsettled",
 "city_effect": {"label": "CD9 relative to CD7/10/11/12, 311 Rat Sighting counts, Jun 2025-May 2026 vs Jun 2024-May 2025", "estimate": p["R"], "lo": p["lo"], "hi": p["hi"], "scale": "rate ratio (difference in differences)", "null": 1,
                 "n": f"CD9 {int(p['t_post'])} vs {int(p['t_pre'])}; comparison {int(p['c_post'])} vs {int(p['c_pre'])} sightings"},
 "sources": S, "data_access": "open",
 "prediction_scored": "miss: the point estimate is 1.02 (CD9 fell 22.8%, the comparison districts 24.1%), outside the predicted 0.75-0.95; support_if (a) fails because the upper bound is 1.23, and refute_if is not met because the lower bound 0.86 is below 0.90. The placebo-year interval (1.08, 0.89-1.36) includes 1. The DOHMH odds ratio point estimate is 1.09 (0.90-1.36), above 1, so condition (c) also fails. Verdict unsettled by rule 2.",
 "settle": "The design has little power: about 380 CD9 sightings a year. Settling it needs sightings by block with bin locations (the DSNY Empire Bin list or mitigation-zone boundary), a longer post period with several containerised districts (Brooklyn CD2 in 2026), and a measure of rats not tied to calls, such as DOHMH inspections with fixed effort or tracking-powder surveys.",
 "research_needed": [
  {"question": "Where exactly were Empire Bins and the fully containerised area, and when did each building start?", "data": "DSNY bin location list or records request", "design": "block-level event study of 311 and DOHMH results against bin start date", "priority": "high"},
  {"question": "Do 311 rat sightings track rat activity when containers change reporting behaviour?", "data": "DOHMH inspection with fixed effort, tracking powder or camera surveys", "design": "paired survey and 311 in treated and untreated blocks", "priority": "high"},
  {"question": "Does the effect appear in Brooklyn CD2 (containerised in 2026) and other districts?", "data": "311, DOHMH", "design": "staggered difference in differences with several treated districts", "priority": "medium"}],
 "figures": ["figures/further/containers_rats_cd9.png"],
 "secondary": {"placebo_year": pl, "dohmh_primary": dh, "dohmh_placebo_year": dp, "other": "See data/derived/further/results.json: 6-month, 17-month, single and leave-one-out comparison districts, all other Manhattan districts, all Rodent descriptors (R 1.26, 1.02-1.59), Noise - Residential placebo (R 1.07, 0.99-1.15)."},
 "notes": "311 counts measure complaints. The data show that CD9 complaints fell about as much as in neighbouring districts after June 2025 (and that all of them fell by roughly a quarter against the year before), which is consistent with a citywide change in reporting or rats and gives no evidence of an extra effect of containers in CD9. They do not show that bins had no effect: the interval allows an additional fall of 14% or a rise of 23%. The DOHMH active-sign share fell in CD9 (15.3% to 14.8% of initial inspections) but fell more in the comparison districts (19.7% to 17.7%); inspection counts in the comparison districts fell 6% while CD9's were flat, so effort differs. Several of the single-district comparisons point either way (CD11 0.85, CD12 1.19). Comparison districts were fixed in advance, not matched on pre-period level; CD9 started the placebo period lower than the comparison and was higher later (event series), so pre-trends are not parallel. Data fetched 12 Nov 2026; the table's last month (Nov 2026) is incomplete and was not used.",
})
cr = r["repro"]; R1 = cr["R1"]
claims.outcome({
 "id": "further-repro-dsny-rat-sightings", "verdict": "unsettled",
 "city_effect": {"label": "Recomputed Dec 2024-Nov 2025 vs Dec 2023-Nov 2024 311 Rat Sightings under R1, percent change", "estimate": R1["decline_pct"], "lo": None, "hi": None, "scale": "percent change; stated -20.6", "null": 0, "n": f"{R1['y1']} and {R1['y2']} (stated 25,230 and 20,025)"},
 "sources": S, "data_access": "open",
 "prediction_scored": f"partial: under R1 the first count is {R1['y1']} (+{100*R1['rel_err1']:.2f}% from 25,230, outside the 1% tolerance by 0.15 points) and the second is {R1['y2']} (+{100*R1['rel_err2']:.2f}% from 20,025, inside). The decline is {R1['decline_pct']:.1f}% against a stated 20.6%, within 0.5 points. R1 reproduces one count only, so the verdict is unsettled by the registered clause. No other reading is closer (R4 is the same as R1; R2 and R3 are 22% and 60% too high).",
 "settle": "DSNY's query or the 311 snapshot date; table revisions since December 2025 plausibly add about 1% of records.",
 "research_needed": [{"question": "Which 311 snapshot and filter produced 25,230 and 20,025?", "data": "DSNY or 311 data team", "design": "ask for the query", "priority": "low"}],
 "figures": [],
 "secondary": {"monthly_R1_prior_year_vs_year": r["repro_monthly_R1"], "all_12_months_lower": all(v[1] < v[0] for v in r["repro_monthly_R1"].values()), "ytd_percent_change_R1": r["repro_ytd"], "note": "Mayor's Office 16.4 percent year to date: Jan-Jul 2025 gives -16.6, Jan-Aug -17.0 (window unstated)."},
 "notes": "The citywide figures are reproduced to about 1% and all twelve monthly comparisons are lower, as stated. The registered 1% tolerance was missed by 0.15 points on the first count.",
})
