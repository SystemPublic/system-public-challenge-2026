"""Outcome for bridge-crz-injury-crashes-v2, and the revision of the v1 outcome it bears on.

Scored against the v2 registration (claims/registered/bridge-crz-injury-crashes-v2.json) and
concord.claims.PRECEDENCE. Run after crz_crashes_v2.py and figures_v2.py.
"""
from __future__ import annotations

import json

from analyses.bridges.common import DER, ROOT
from concord import claims

CID = "bridge-crz-injury-crashes-v2"
V1 = "bridge-crz-injury-crashes"
FIG = "figures/bridges/bridge_crz_injury_crashes_v2.png"


def f(r, k="pct"):
    return f"{r[k]:+.1f}% ({r['lo']:+.1f} to {r['hi']:+.1f})"


def main():
    cr = json.loads((DER / "crz_crashes_v2_results.json").read_text())
    R, cp = cr["results"], cr["composed"]
    p, pl, C, bi = R["primary"], R["placebo_2024"], R["corrected"], R["bias_inputs"]
    an = R["annual_injury_crashes"]
    verdict = R["verdict_by_rule"]
    st = dict(R["stance"])
    st["value"] = abs(st["value"]) if st["value"] == 0 else st["value"]

    zline = " ".join(f"{k}: {C[k]['pct']:+.1f}%, z_chain {C[k]['z_chain']:+.2f}, z_null {C[k]['z_null']:+.2f}, D {C[k]['D']:.2f} ({C[k]['condition']})."
                     for k in ("B0", "B1", "B2", "B3", "B4", "B_up", "B_down"))
    claims.outcome({
        "id": CID,
        "verdict": verdict,
        "city_effect": {"label": "Endpoint: NYPD injury crashes in the CBD geofence vs Manhattan north of 60th St, 2025 vs 2022-24 (OLS log monthly count, HAC 3)",
                        "estimate": p["pct"], "lo": p["lo"], "hi": p["hi"], "scale": "percent change", "null": 0, "n": p["n"]},
        "graph_effect": {"label": "Composed prediction, v2 (speed link CBD vs CBD Adjacent; Monte Carlo, 200,000 draws)",
                         "estimate": cp["median"], "lo": cp["lo"], "hi": cp["hi"], "scale": "percent change", "null": 0},
        "endpoint_test": {
            "z_chain": p["z_chain"], "z_null": p["z_null"], "D": p["D"], "se_log": p["se"],
            "composed_mean_log": cp["mean_log"], "composed_sd_log": cp["sd_log"],
            "placebo_2024_pct": [pl["pct"], pl["lo"], pl["hi"]],
            "bias_bounds": {k: {"pct": C[k]["pct"], "lo": C[k]["lo"], "hi": C[k]["hi"], "z_chain": C[k]["z_chain"],
                                "z_null": C[k]["z_null"], "D": C[k]["D"], "condition": C[k]["condition"]} for k in C},
            "conditions_deciding": R["conditions"],
        },
        "sources": cr["sources"],
        "prediction_scored": (
            f"uninformative. The registered test cannot decide: the 2024 placebo, {f(pl)}, excludes zero, so the zone and Manhattan north of 60th St "
            f"were already moving apart before pricing, and under the registered rule the verdict is unsettled whatever the 2025 estimate. "
            f"The 2025 estimate, {f(p)}, lies about as far from the composed {cp['median']:+.1f}% (z_chain {p['z_chain']:.2f}) as from no effect "
            f"(z_null {p['z_null']:.2f}); D = {p['D']:.2f}, far below the 4 that rule 8 requires. At the upward bias bound it is "
            f"{f(C['B_up'])}, incompatible with the chain (z_chain {C['B_up']['z_chain']:.2f}); at the downward bound it is {f(C['B_down'])}. "
            "The registrant expected an unsettled verdict; the reason is the pre-trend more than the lack of discrimination."),
        "settle": (
            "Two things would settle it. First, the crash records without coordinates in 2022-2024 (about 3,000 injury crashes a year with no borough and no "
            "coordinates) would need to be geocoded from their street names, so that the zone, the rest of Manhattan and the rest of the city are counted "
            "the same way in every year; this removes the bias bounds. Second, the 2024 divergence between the zone and upper Manhattan needs an explanation "
            "(a fall in injury crashes north of 60th St in 2024, from 3,181 to 2,795, while the zone rose slightly) before any comparison area can be trusted. "
            "Even then, a composed prediction of about -2% cannot be told from zero with monthly area counts; segment-level speeds, volumes and crashes "
            "inside the zone would test the two link terms separately."),
        "research_needed": [
            {"question": "Why did injury crashes in Manhattan north of 60th St fall in 2024 relative to the zone (placebo +15%)?", "data": "NYPD crashes by precinct and street; DOT street projects and enforcement 2023-2025",
             "design": "Precinct-level series; check of 2024 reporting changes in upper Manhattan precincts", "priority": "high"},
            {"question": "Where do the 2022-2024 crash records without coordinates or borough fall?", "data": "h9gi-nx95 street-name fields for records without coordinates",
             "design": "Geocode on_street_name, cross_street_name and off_street_name with the city's Geosupport; recount by area and year", "priority": "high"},
            {"question": "Do the speed and volume effects on crashes cancel, or are both near zero at 8 to 9 mph?", "data": "MTA or DOT segment speeds and counts inside the zone; geocoded crashes",
             "design": "Segment panel, 2023-2026", "priority": "medium"},
        ],
        "figures": [FIG],
        "notes": (
            f"Annual geocoded injury crashes (zone / Manhattan north of 60th St): "
            + ", ".join(f"{y} {v['zone']:,} / {v['north']:,}" for y, v in an.items() if y != "2026")
            + f"; January-August 2026 {an['2026']['zone']:,} / {an['2026']['north']:,}. "
            f"Bias bound inputs: the zone's share of geocoded injury crashes in the two areas, 2022-2024, w = {bi['w_zone_share_2022_24']:.3f}; "
            f"citywide share of injury crashes without coordinates {100 * bi['missing_share_2022_24']:.2f}% (2022-24) and {100 * bi['missing_share_2025']:.2f}% (2025), "
            f"a fall of {100 * bi['D_new_citywide']:.2f} points; rise among Manhattan-coded injury crashes {100 * bi['e_manhattan_coded_rise']:.2f} points. "
            f"Estimates by assumption: {zline} "
            f"Reported, not deciding: if every newly geocoded Manhattan record fell in the zone the estimate would be {C['extreme_all_in_zone']['pct']:+.1f}%, "
            f"and if every one fell north of 60th St it would be {C['extreme_all_in_north']['pct']:+.1f}%. "
            f"Secondary results (registered, not deciding): zone against the 60th-96th St band {f(R['secondary_area_60_96'])}, with its own 2024 placebo "
            f"{f(R['secondary_area_60_96_placebo_2024'])}; Poisson GLM with area-by-month terms {f(R['poisson_area_by_month'])}; "
            f"with January-August 2026 added {f(R['through_aug_2026'])} (z_chain {R['through_aug_2026']['z_chain']:.2f}, z_null {R['through_aug_2026']['z_null']:.2f}); "
            f"against the correlated composition z_chain {R['correlated_composition']['z_chain']:.2f}; against the v1 composition (-0.4%) z_chain {R['v1_composition']['z_chain']:.2f}. "
            f"Stable-coverage restrictions: {R['stable_class_restriction'] if isinstance(R['stable_class_restriction'], str) else 'run'}. "
            "Coverage of injury crashes by record class, 2022 to 2025: intersection records "
            + " / ".join(f"{100 * v:.1f}%" for v in R["coverage_by_class"]["intersection"]["coverage"].values())
            + ", address records " + " / ".join(f"{100 * v:.1f}%" for v in R["coverage_by_class"]["address"]["coverage"].values())
            + ", other records " + " / ".join(f"{100 * v:.1f}%" for v in R["coverage_by_class"]["other"]["coverage"].values())
            + f". Month restriction: {R['stable_month_restriction'] if isinstance(R['stable_month_restriction'], str) else 'run'} "
            f"(2025 mean coverage {100 * R['coverage_2025_mean']:.1f}%; the months within 2 points are {', '.join(R['stable_pre_months'])}). "
            "Monthly coverage (share of injury crashes with coordinates, citywide) was 82 to 95 percent from January 2022 to October 2024, with a dip "
            "to 82-89 percent from July to October 2024, and 96.5 to 98.0 percent in every month from November 2024 on. The change in geocoding came in "
            "November 2024, two months before pricing. Exploratory, not registered: the July-October 2024 dip falls inside the placebo's post period, "
            "and if it removed more records north of 60th St than in the zone it would produce part of the placebo difference. "
            "The MTA does not publish the boundary of its CBD Adjacent area, so the speed link of the composition (CBD vs CBD Adjacent, +4.2%) is only "
            "a stand-in for the contrast with Manhattan north of 60th St. "
            "Data seen before registration are listed in the registration (data_seen_before_registration). The registration was committed in ce3586a and "
            "pushed to GitHub at about 00:32 UTC on 13 November 2026; the crash queries for v2 were made from 00:35 UTC."),
        "critique": {"report": "critique/bridge-crz-injury-crashes.md", "answer": "This claim is the re-analysis the referee asked for."},
    })
    o = ROOT / "claims" / "outcomes" / f"{CID}.json"
    d = json.loads(o.read_text())
    d["stance"] = st
    d["stance_note"] = ("Rules 7 and 8, named in the registration before the data: endpoint_stance(z_chain, z_null) at the primary estimate. "
                        "D < 0, so the stance is 0.")
    o.write_text(json.dumps(d, indent=1, ensure_ascii=False))

    # revise v1
    old = json.loads((ROOT / "claims" / "outcomes" / f"{V1}.json").read_text())
    note = (
        f"\n\nAfter the re-analysis (bridge-crz-injury-crashes-v2, registered and pushed to GitHub before its data were queried): "
        f"against Manhattan north of 60th St, which shares the zone's geocoding regime, injury crashes in the zone changed by {f(p)} in 2025, "
        f"with z {p['z_chain']:.2f} from the v2 composed prediction ({cp['median']:+.1f}%) and z {p['z_null']:.2f} from no effect. "
        f"Its 2024 placebo, {f(pl)}, excludes zero, so that comparison has its own pre-trend and v2 is unsettled. Under the registered "
        f"bias bounds for the geocoding change the v2 estimate ranges from {C['B_down']['pct']:+.1f}% to {C['B_up']['pct']:+.1f}%. "
        "Neither comparison area gives a test that separates the chain from no effect. The v1 verdict stays unsettled. "
        "The geocoding bias in v1 (zone against the rest of the city) is not resolved by v2: v2 changes the comparison area and so cannot correct the v1 estimate.")
    claims.revise(V1, {
        "notes": old["notes"] + note,
        "stance_rule_note": ("The v1 outcome was decided under rules 1-6 (verdict confirmed, weakest-link stance 0.963). Rule 7, which relabelled the verdict "
                             "bridged and replaced the stance with endpoint agreement (0.903), was committed in 3d8ac0d at 16:12:16 on 12 November 2026, "
                             "30 seconds after this outcome (f024acb, 16:11:46). The rule 7 stance was therefore chosen after the data were seen and, "
                             "under rule 4, decides nothing for this claim. The current stance (rules 7 and 8) is kept for display only, beside the "
                             "pre-registered weakest-link stance in history."),
        "stance": {**old["stance"], "chosen_after_data": True},
        "reanalysis": {"id": CID, "verdict": verdict, "estimate_pct": p["pct"], "lo": p["lo"], "hi": p["hi"],
                       "z_chain": p["z_chain"], "z_null": p["z_null"], "placebo_2024_pct": [pl["pct"], pl["lo"], pl["hi"]]},
        "figures": old.get("figures", []) + [FIG],
    }, reason=("Re-analysis bridge-crz-injury-crashes-v2 done as the referee asked; verdict unchanged (unsettled). The rule 7 stance is marked as "
               "chosen after the data were seen, as the referee asked."),
        critique="critique/bridge-crz-injury-crashes.md")


if __name__ == "__main__":
    main()
