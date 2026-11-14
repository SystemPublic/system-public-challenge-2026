"""Write the three outcomes from the result files."""
import json, math, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from concord import claims
D = ROOT / "data/derived/round2/retimed_consequences"
L = lambda n: json.load(open(D / n))
iv = lambda x, d=3: f"{x['estimate']:.{d}f} ({x['lo']:.{d}f} to {x['hi']:.{d}f})"
pc = lambda x: f"{100*(math.exp(x['estimate'])-1):+.1f}% ({100*(math.exp(x['lo'])-1):+.1f} to {100*(math.exp(x['hi'])-1):+.1f})"
FIG = ["figures/round2/retimed_consequences.png"]
GRAPH = {"kind": "sysgraph", "note": "variable searches, API v1.0, 12 Nov 2026; data/derived/round2/retimed_consequences/graph_gap_check.json and graph_leads.json; 20 uncached requests"}
DOSE = {"kind": "derived", "path": "data/derived/transit/dose_map_long.csv", "sources": "data/derived/transit/dose_map_sources.json"}

t, te = L("taxi_results.json"), L("taxi_exploratory.json")
p = t["primary"]
claims.outcome({
 "id": "retimed-taxi-fhv-pickups", "verdict": "unsettled",
 "city_effect": {"label": "Slope of the change in Monday-and-Friday relative pickups on the change in Monday-and-Friday relative subway entries, across taxi zones, Feb-Mar 2019 to Feb-Mar 2026",
                 "estimate": p["slope"]["estimate"], "lo": p["slope"]["lo"], "hi": p["slope"]["hi"], "scale": "elasticity (log-log slope)", "null": 0, "n": p["n_zones"]},
 "graph_effect": None,
 "sources": L("taxi_sources.json") + [DOSE, GRAPH],
 "prediction_scored": f"partial. The slope, {iv(p['slope'],2)}, is inside the registered range of 0.3 to 1.0 and its interval is above zero. The second condition is not met: pickups in the most-thinned third of zones against the least-thinned third changed by {pc(p['hi_minus_lo'])}, an interval that includes zero. Neither refutation condition is met.",
 "settle": "Twelve months of trip records in each period, so that zone-level ratios rest on 40 weeks and not 6 or 7, and a registered split of zones into the business district and residential zones, where the exploratory results have opposite signs.",
 "research_needed": [{"question": "How much taxi and ride-hail demand follows office attendance, and how much moves to the home end on days worked at home?", "data": "TLC trip records by zone, weekday and hour, full years 2019 and 2025-26; office occupancy by building", "design": "Registered difference-in-differences with business-district and residential zones as separate groups", "priority": "medium"}],
 "figures": FIG,
 "notes": (f"Yellow taxi and high-volume for-hire pickups, 06:00-19:59, {p['n_zones']} zones, weeks {t['weeks_2019']} and {t['weeks_2026']} (the weeks of Presidents' Day and of the 23 February 2026 storm are dropped). "
           f"Mean weekday pickups in these zones were {p['daily_pickups'][0]:,.0f} in 2019 and {p['daily_pickups'][1]:,.0f} in 2026. Weighted by 2019 pickups the slope is {p['slope_weighted_by_2019_pickups']:.2f}. "
           f"Yellow only ({t['yellow_only']['n_zones']} zones): slope {iv(t['yellow_only']['slope'],2)}, contrast {pc(t['yellow_only']['hi_minus_lo'])}. For-hire only: slope {iv(t['fhvhv_only']['slope'],2)}, contrast {pc(t['fhvhv_only']['hi_minus_lo'])}. "
           f"Zones outside the business district ({t['outside_cbd']['n_zones']}): slope {iv(t['outside_cbd']['slope'],2)}, contrast {pc(t['outside_cbd']['hi_minus_lo'])}, the opposite sign. "
           f"Placebo, yellow 2018 against 2019: slope {iv(t['placebo_yellow_2018_vs_2019']['slope'],2)}. "
           f"Exploratory, not registered: pooled over the {te['n']['cbd']} business-district zones the Monday-and-Friday ratio changed by {pc(te['Y_cbd'])}; outside it, the half of zones whose stations thinned more changed by {pc(te['noncbd_more_thinning_minus_noncbd_less_thinning'])} relative to the other half. "
           "The positive slope therefore comes from the difference between the business district and everywhere else; within residential zones the relation runs the other way. The registered thirds mix the two, which is why the contrast is near zero. "
           "The standard error of the slope (0.17) is close to the 0.15 expected from the 2018 design check. Green taxis and other for-hire bases are not counted. The 2026 for-hire months were read by a remote column scan of the TLC parquet files; nothing was saved except the zone-day counts.")})

b, bc = L("burglary_results.json"), L("burglary_bootstrap_check.json")
q = b["primary"]; Y = q["Y_all"]
claims.outcome({
 "id": "retimed-daytime-burglary", "verdict": "contested",
 "city_effect": {"label": "Ratio of the Monday-and-Friday to Tuesday-to-Thursday ratio of daytime residential burglaries, 2023 to September 2026 over 2015-2019, citywide",
                 "estimate": math.exp(Y["estimate"]), "lo": math.exp(Y["lo"]), "hi": math.exp(Y["hi"]), "scale": "ratio of ratios", "null": 1, "n": int(sum(q["counts"]["all"]))},
 "graph_effect": None,
 "sources": L("burglary_sources.json") + [{"kind": "nyc-open-data-boundary", "dataset": "5crt-au7u", "name": "Community Districts", "path": "data/cache/boundaries/5crt-au7u.geojson"}, DOSE, GRAPH],
 "prediction_scored": f"miss. The registered fall of 5% to 10% did not appear: the ratio is {math.exp(Y['estimate']):.3f} ({math.exp(Y['lo']):.3f} to {math.exp(Y['hi']):.3f}). The lower bound is above 0.95, so the second refutation condition is met, by 0.003. That margin is within the Monte Carlo error of 2,000 bootstrap draws: a check with 20,000 draws, run after the result was seen, gives a lower bound of {bc['ratio'][1]:.4f}. The verdict follows the registered procedure; the plain reading is that there is no sign of a fall and a fall of more than about 5% is excluded.",
 "settle": "Burglary records with the time the victim left and returned, or with a flag for whether someone was at home, and the count of households at home by day from a time-use or mobility source. The district contrast should be registered as a primary test on data from 2027 onward.",
 "research_needed": [{"question": "Does working at home lower daytime burglary of the worker's own home, and does it displace burglary to neighbouring districts or days?", "data": "NYPD complaints with occupancy at the time; household-level work-at-home days (American Time Use Survey or mobile-device home dwell time) by district", "design": "District-by-weekday panel with a registered contrast between districts by change in daytime occupancy", "priority": "high"}],
 "figures": FIG,
 "notes": (f"{b['n_records']:,} complaints on weekdays, of which {int(q['counts']['all'][0]):,} fall in the 209 retained baseline weeks and {int(q['counts']['all'][1]):,} in the 152 retained recent weeks; {b['n_without_district']} had no usable coordinates. "
           f"Friday is the peak day in both periods (index {b['weekday_index']['base']['index'][4]:.2f} and {b['weekday_index']['rec']['index'][4]:.2f} of midweek). Monday changed by {100*(math.exp(b['by_day']['Mon'])-1):+.1f}% and Friday by {100*(math.exp(b['by_day']['Fri'])-1):+.1f}% relative to midweek. "
           f"Secondary, registered as not deciding: in the 24 districts that send more commuters the ratio changed by {pc(q['Y_hi'])}, in the 24 that send fewer by {pc(q['Y_lo'])}; the difference is {pc(q['hi_minus_lo'])}. The sign is the one registered, but the difference comes from a rise in the lower-sending districts and not from a fall in the higher-sending ones, and the registration gave this contrast a D of 1.3. "
           f"The same difference in the placebo (2015-17 against 2018-19) is {pc(b['placebo_2015_17_vs_2018_19']['hi_minus_lo'])}; with a 2017-19 baseline it is {pc(b['sens_baseline_2017_19']['hi_minus_lo'])}; for complaints ending the day they began {pc(b['sens_same_day_end']['hi_minus_lo'])}; for completed burglaries {pc(b['sens_completed_only']['hi_minus_lo'])}. "
           f"Citywide sensitivity: placebo {pc(b['placebo_2015_17_vs_2018_19']['Y_all'])}; baseline 2017-19 {pc(b['sens_baseline_2017_19']['Y_all'])}; same-day end {pc(b['sens_same_day_end']['Y_all'])}; completed only {pc(b['sens_completed_only']['Y_all'])}. "
           f"In the six business-district community districts the ratio changed by {pc(q['Y_cbd'])} on {int(sum(q['counts']['cbd'])):,} complaints. "
           "The yearly ratio of Monday-and-Friday to midweek burglaries ranges from 1.05 to 1.20 with no trend (by_year in burglary_results.json). The recorded day is the start of the period in which the burglary could have happened, as reported by the victim.")})

e = L("ems_results.json")
r = e["primary"]; C = r["cbd_minus_rest"]; el = e["elasticity"]; s = e["secondary"]
claims.outcome({
 "id": "retimed-ems-presence", "verdict": "confirmed",
 "city_effect": {"label": "Elasticity of daytime EMS incidents to subway entries: the business-district-minus-rest change in the Monday-and-Friday ratio of incidents, divided by the same difference for entries (-0.0639)",
                 "estimate": el["estimate"], "lo": el["lo"], "hi": el["hi"], "scale": "elasticity", "null": 0, "n": r["n_units"]},
 "graph_effect": None,
 "sources": L("ems_sources.json") + [DOSE, GRAPH],
 "prediction_scored": f"hit. The contrast is {iv(C)} on the log scale, {pc(C)}, inside the registered range of -0.013 to -0.064, and its interval is below zero. The elasticity is {iv(el,2)}, near the 0.4 I expected. The interval excludes 1, so incidents did not fall in proportion to entries.",
 "settle": "A count of people present by district and day (mobile-device or turnstile exits) to replace entries as the denominator, and the incident location type, to separate calls from workplaces from calls from homes, streets and stations.",
 "research_needed": [{"question": "How does emergency call volume scale with the daytime population of a business district, by call type?", "data": "EMS incidents with location type; daytime population by district and weekday", "design": "Weekday panel across cities with different returns to the office", "priority": "medium"}],
 "figures": FIG,
 "notes": (f"Incidents between 06:00 and 19:59, {r['n_weeks'][0]} retained weeks in 2018-19 and {r['n_weeks'][1]} from October 2024 to September 2026; {r['daily_cbd'][0]:.0f} and {r['daily_cbd'][1]:.0f} a weekday in the six business-district districts, {r['daily_rest'][0]:.0f} and {r['daily_rest'][1]:.0f} in the other 48. "
           f"The Monday-and-Friday ratio changed by {pc(r['Y_cbd'])} in the business district and by {pc(r['Y_rest'])} in the rest. The rest of the city did not gain incidents on those days, so the contrast is a fall in the business district and not a rise elsewhere. "
           f"Friday changed more than Monday in the business district ({100*(math.exp(e['by_day']['Fri']['Y_cbd'])-1):+.1f}% against {100*(math.exp(e['by_day']['Mon']['Y_cbd'])-1):+.1f}%). "
           f"Placebo (2016-17 against 2018-19): {iv(e['placebo_2016_17_vs_2018_19']['cbd_minus_rest'])}. With 2019 and the last 12 months only: {iv(e['sens_2019_vs_last12m']['cbd_minus_rest'])}. "
           f"By hours: 06-09 {iv(s['hours_06_09']['cbd_minus_rest'])}, 10-15 {iv(s['hours_10_15']['cbd_minus_rest'])}, 16-19 {iv(s['hours_16_19']['cbd_minus_rest'])}. High-severity incidents (initial severity 1 to 3): {iv(s['high_severity']['cbd_minus_rest'])}. "
           f"The slope across the 54 districts is {iv(r['slope'],2)}, which the registration said could not be estimated well. The standard error of the contrast, {C['se']:.4f}, matches the 0.009 expected from the design check. "
           "Entries are fare-paid boardings and miss people who walk, drive or arrive by commuter rail, so the elasticity is per unit of subway thinning and not per person.")})
print("ok")
