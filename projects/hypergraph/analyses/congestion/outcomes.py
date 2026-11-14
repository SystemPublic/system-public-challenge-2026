"""Write the outcomes of bridge-crz-ems-travel and crz-storefront-vacancy from the result files.
The registered conditions are applied literally."""
import json
import sys

import numpy as np

from concord import claims
from analyses.congestion.common import DER


def ems():
    r = json.loads((DER / "ems_results.json").read_text())
    e, f, c = r["endpoint"], r["endpoint_full_period"], r["composed"]
    support = abs(e["z_chain"]) < 1.96 and e["D_vs_proportional"] >= 4
    refute = abs(e["z_chain"]) >= 1.96
    verdict = "confirmed" if support else "contested" if refute else "unsettled"
    g = lambda k, per, w: r[k][per][w]
    s = lambda x: f"{x['pct']:+.1f}% ({x['lo']:+.1f} to {x['hi']:+.1f})"
    srcs = json.loads((DER / "ems_sources.json").read_text())
    fsrcs = json.loads((DER / "fire_sources.json").read_text())
    sources = [x for y in sorted(srcs) for x in srcs[y]] + [x for y in sorted(fsrcs) for x in fsrcs[y]]
    lives = json.loads((DER / "arrest_lives.json").read_text())
    notes = (
        f"Registered endpoint: mean ambulance travel time to incidents in the zone during peak toll hours, relative to all other "
        f"city ZIPs, 5 January to 31 August 2025 against 2023-24: {s(e)}, standard error {e['se']:.4f} on the log scale, 32 months. "
        f"Composed prediction {100*(np.exp(c['mean_log'])-1):+.1f}%; z_chain {e['z_chain']:.2f}; z against the proportional alternative "
        f"(-5.4%) {e['z_prop']:.2f}; D_prop {e['D_vs_proportional']:.1f}. The registered support condition is met: travel time did not "
        f"fall in proportion to the rise in speed. z against no effect is {e['z_null']:.2f} and the interval includes zero, so an "
        f"improvement is not shown; the registration stated in advance that this test could not tell the chain from no effect. "
        f"Whole post-period to September 2026 (secondary): {s(f)}. "
        f"The within-zone control does not support a toll effect. In overnight hours, when the toll is a quarter of the peak toll, the "
        f"zone's relative travel time fell more: {s(g('ems.all.travel.all_outside','overnight','primary_jan_aug_2025'))} to August 2025 and "
        f"{s(g('ems.all.travel.all_outside','overnight','full_to_sep_2026'))} to September 2026. The triple difference (peak minus overnight) "
        f"is {s(g('ems.all.travel.all_outside','triple','primary_jan_aug_2025'))}, with a 2024 placebo of "
        f"{s(g('ems.all.travel.all_outside','triple','placebo_2024'))}. "
        f"Life-threatening incidents (initial severity 1 to 3): {s(g('ems.life_threatening.travel.all_outside','peak','primary_jan_aug_2025'))}, "
        f"but the 2024 placebo is {s(g('ems.life_threatening.travel.all_outside','peak','placebo_2024'))}, so the zone's relative travel time for "
        f"these calls was already rising before the toll. Lower-priority incidents: "
        f"{s(g('ems.lower_priority.travel.all_outside','peak','primary_jan_aug_2025'))}. Total response time (call to arrival), all incidents: "
        f"{s(g('ems.all.response.all_outside','peak','primary_jan_aug_2025'))}. Against Manhattan 60th-110th Street: "
        f"{s(g('ems.all.travel.north','peak','primary_jan_aug_2025'))} (2024 placebo {s(g('ems.all.travel.north','peak','placebo_2024'))}). "
        f"Against downtown Brooklyn and Long Island City: {s(g('ems.all.travel.bklic','peak','primary_jan_aug_2025'))} "
        f"(placebo {s(g('ems.all.travel.bklic','peak','placebo_2024'))}). The 2024 placebo of the primary comparison is "
        f"{s(g('ems.all.travel.all_outside','peak','placebo_2024'))}. "
        f"Fire Incident Dispatch Data, same estimator: travel time {s(g('fire.all.travel.all_outside','peak','primary_jan_aug_2025'))} to August 2025 "
        f"and {s(g('fire.all.travel.all_outside','peak','full_to_sep_2026'))} to September 2026. "
        "Levels: mean EMS travel time in the zone at peak hours was 558 s in 2023, 617 s in 2024, 661 s in 2025 and 712 s in January to "
        "September 2026; in the rest of the city 591, 647, 696 and 772 s. Travel time rose everywhere by about 7% a year, which is "
        "several times any effect of the toll. "
        f"Lives (composition, not a test): with {lives['inputs']['attended_arrests_zone_peak_per_year']:.0f} attended cardiac arrests a year in "
        f"the zone at peak hours, the measured change implies {lives['measured_jan_aug_2025']['lives_per_year_lo_med_hi'][1]:.1f} lives a year "
        f"({lives['measured_jan_aug_2025']['lives_per_year_lo_med_hi'][0]:.1f} to {lives['measured_jan_aug_2025']['lives_per_year_lo_med_hi'][2]:.1f}).")
    rec = {
        "id": "bridge-crz-ems-travel", "verdict": verdict,
        "city_effect": {"label": "EMS mean travel time, zone vs all other city ZIPs, peak toll hours, 5 Jan-31 Aug 2025 vs 2023-24 (DiD on monthly log means, HAC 3)",
                        "estimate": e["pct"], "lo": e["lo"], "hi": e["hi"], "scale": "percent change", "null": 0, "n": e["n_months"]},
        "graph_effect": {"label": "Composed prediction: speed change (mob-crz-traffic) times pre-toll elasticity (200,000 draws); no graph finding enters",
                         "estimate": 100 * (c["ratio_lo_median_hi"][1] - 1), "lo": 100 * (c["ratio_lo_median_hi"][0] - 1),
                         "hi": 100 * (c["ratio_lo_median_hi"][2] - 1), "scale": "percent change", "null": 0},
        "endpoint_test": {k: e[k] for k in ("z_chain", "z_null", "z_prop", "D_vs_null", "D_vs_proportional", "se")} | {
            "support_if_met": support, "refute_if_met": refute, "full_period": {k: f[k] for k in ("pct", "lo", "hi", "z_chain", "z_null", "z_prop")}},
        "stance": claims.endpoint_stance(e["z_chain"], e["z_null"]),
        "sources": sources,
        "prediction_scored": ("hit on the registered condition (less than proportional, compatible with the composed -1.8%); the interval "
                              "includes zero and the overnight control moved further than the peak, so no improvement from the toll is shown"),
        "settle": ("Travel times by unit with the unit's starting location, so that distance can be held fixed; a second year of the MTA "
                   "speed series; dispatch records that mark lights-and-sirens responses."),
        "research_needed": [
            {"question": "How much does general traffic speed change ambulance travel time under lights and sirens?", "data": "AVL traces of ambulances and of general traffic on the same streets", "design": "within-street, within-hour comparison", "priority": "high"},
            {"question": "Did the closure of Mount Sinai Beth Israel change unit availability in the zone?", "data": "unit-level dispatch and hospital destination records", "design": "event study around the closure date", "priority": "medium"}],
        "figures": ["figures/congestion/ems_travel_time.png"],
        "notes": notes,
    }
    p = claims.outcome(rec)
    # stance: rule 7+8 against no effect, as the precedence text defines it
    o = json.loads(p.read_text()); o["stance"] = claims.endpoint_stance(e["z_chain"], e["z_null"]); p.write_text(json.dumps(o, indent=1, ensure_ascii=False))
    print(p, verdict)


def vacancy():
    r = json.loads((DER / "vacancy_results.json").read_text())
    d = r["did_2025"]
    support = d["did_points"] <= 0.5 and d["hi"] < 1.2
    refute = d["lo"] > 0
    verdict = "confirmed" if support else "contested" if refute else "unsettled"
    pl = [x["did_points"] for x in r["placebo_did"] if x["year"] in (2022, 2023, 2024)]
    rates = {(x["year"], x["area"]): x for x in r["rates"]}
    s = lambda x: f"{x['did_points']:+.2f} ({x['lo']:+.2f} to {x['hi']:+.2f})"
    notes = (
        f"Vacancy in the zone was {100*rates[(2024,'crz')]['mean']:.2f}% of {rates[(2024,'crz')]['size']} storefronts on 31 December 2024 and "
        f"{100*rates[(2025,'crz')]['mean']:.2f}% of {rates[(2025,'crz')]['size']} on 31 December 2025, a change of {d['zone_change']:+.2f} points. "
        f"Outside the zone it changed by {d['comp_change']:+.2f} points. The difference is {s(d)} points; both registered conditions for "
        f"support are met (estimate at most +0.5, upper bound below +1.2). "
        f"The same difference was {pl[0]:+.2f}, {pl[1]:+.2f} and {pl[2]:+.2f} in the three earlier years, mean {np.mean(pl):+.2f}, so the "
        f"2025 value is {d['did_points']-np.mean(pl):+.2f} points above that mean and equal to the 2024 value: the zone's faster recovery "
        f"continued at its 2024 pace and slower than in 2022-23. Vacancy rose slightly in the zone and rose more elsewhere. "
        f"Against Manhattan 60th-110th Street: {s(r['did_2025_north'])}. Against downtown Brooklyn and Long Island City: {s(r['did_2025_bklic'])} "
        f"(about 2,100 storefronts; vacancy there fell). Against the rest of the city: {s(r['did_2025_rest'])}. "
        "The test excludes a rise of 1.2 points (about 180 storefronts) in the zone's relative vacancy. It cannot detect a smaller rise, and "
        "one year may be too soon for leases to show an effect.")
    rec = {
        "id": "crz-storefront-vacancy", "verdict": verdict,
        "city_effect": {"label": "Change in storefront vacancy share, 31 Dec 2025 vs 31 Dec 2024, zone minus all other city ZIPs (bootstrap over tax lots)",
                        "estimate": d["did_points"], "lo": d["lo"], "hi": d["hi"], "scale": "percentage points", "null": 0,
                        "n": d["n_zone_lots"] + d["n_comp_lots"]},
        "graph_effect": None,
        "sources": json.loads((DER / "vacancy_sources.json").read_text()),
        "prediction_scored": "hit: the estimate is inside the predicted range of -1.5 to +0.5 and the upper bound (+0.17) is below +1.2",
        "settle": "The filing for 31 December 2026; taxable sales by ZIP or by borough, which the state does not publish; card-spending data by district.",
        "research_needed": [
            {"question": "Did retail and restaurant sales in the zone change?", "data": "taxable sales below the city level (the state publishes New York City as one jurisdiction)", "design": "difference-in-differences by district and industry", "priority": "high"}],
        "figures": ["figures/congestion/business.png"],
        "notes": notes,
    }
    print(claims.outcome(rec), verdict)


if __name__ == "__main__":
    {"ems": ems, "vacancy": vacancy}[sys.argv[1]]()
