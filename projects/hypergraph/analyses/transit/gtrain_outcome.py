"""Outcome for transit-gtrain-substitution, from data/derived/transit/gtrain_results.json."""
import json

from concord import claims
from analyses.transit.gtrain_common import DER

r = json.loads((DER / "gtrain_results.json").read_text())
src = json.loads((DER / "gtrain_sources.json").read_text())
e, fs, dv = r["estimates"], r["first_stage"], r["diversion"]
p = e["primary"]


def f(k):
    v = e[k]
    return f"{v['estimate']:+.3f} ({v['lo']:+.3f} to {v['hi']:+.3f})"


support = {"a_first_stage": fs["passes"], "b_clustered_interval_excludes_0": p["lo"] > 0,
           "c_permutation_p_below_0.05": p["permutation_p"] < 0.05,
           "d_placebo_2023": e["placebo_2023"]["lo"] < 0 < e["placebo_2023"]["hi"]}
refute = fs["passes"] and p["hi"] < 0.02
verdict = "no_test" if not fs["passes"] else "confirmed" if all(support.values()) else "contested" if refute else "unsettled"
assert verdict == "unsettled", verdict

pm = src["portal_metadata"]
sources = src["trips"] + src["subway"] + [
    {"kind": "nyc-open-data", "dataset": k, "name": m["name"], "url": m["url"], "rows_updated_at_epoch": m["rowsUpdatedAt"],
     "data_access": "open",
     "note": "Portal copy of the trip records. A one-month count by day and zone timed out on the server (six attempts of 180 s, 12 Nov 2026), so the registered fallback (TLC parquet files of the same records) supplied the counts."}
    for k, m in pm.items()] + [
    {"kind": "ny-open-data", "dataset": "39hk-dx4f", "name": "MTA Subway Stations", "url": "https://data.ny.gov/d/39hk-dx4f",
     "data_access": "open", "note": "Lookup read before registration through concord.socrata with DOMAIN https://data.ny.gov."},
    {"kind": "tlc-taxi-zones", "url": "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zones.zip", "data_access": "open"},
]

REC = {
    "id": "transit-gtrain-substitution",
    "verdict": verdict,
    "city_effect": {"label": "change in daily Uber and Lyft pickups in seven taxi zones on days when their G-only station had no service, against 32 nearby zones (zone and date fixed effects)",
                    "estimate": round(p["estimate"], 4), "lo": round(p["lo"], 4), "hi": round(p["hi"], 4),
                    "scale": "log points (0.043 is about 4.4%)", "null": 0, "n": p["n_obs"],
                    "interval": "zone-clustered 95%, as registered; with seven treated zones it is too narrow",
                    "permutation_p": p["permutation_p"], "permutation_sd": round(p["permutation_sd"], 4)},
    "graph_effect": None,
    "conditions": {"support_if": support, "refute_if": bool(refute)},
    "sources": sources,
    "prediction_scored": (
        f"partial: the estimate is {f('primary')} log points, inside the predicted +0.02 to +0.12, and the 2023 placebo is "
        f"{f('placebo_2023')}, inside its predicted band. Support conditions (a), (b) and (d) are met. Condition (c) is not: "
        f"the placebo-in-space permutation p-value is {p['permutation_p']:.2f} (required below 0.05). The refutation condition "
        f"is not met either, because the upper end of the interval ({p['hi']:+.3f}) is above +0.02. The verdict is unsettled."),
    "settle": (
        "The zone-day counts cannot separate a 4% rise in seven zones from ordinary differences between neighbourhood summers: "
        f"random sets of seven control zones given the same schedules produce coefficients with a standard deviation of {p['permutation_sd']:.3f}. "
        "Three kinds of information would settle it. Pickup coordinates or pickups within a few hundred metres of each closed station entrance, "
        "which TLC holds but publishes only by zone, would raise the share of affected trips in the treated unit. Hourly counts would allow a test "
        "confined to the hours when the displaced riders travel. A second event of the same kind gives an out-of-sample test: the G was cut again "
        "between Court Sq and Bedford-Nostrand Avs on nights and weekends from 14 July to 18 August 2025, and the registered model can be run on it "
        "with the Greenpoint and Clinton Hill effects as the prediction."),
    "research_needed": [
        {"question": "Do app pickups rise within walking distance of a closed subway station, and at the hours the station is normally used?",
         "data": "TLC trip records with pickup coordinates or census-block pickup counts (held by TLC, not published); hourly zone counts are public",
         "design": "registered event study by distance band from the station entrance and by hour, same phases", "priority": "high"},
        {"question": "Does the Greenpoint result (+0.12) replicate in the 2025 night and weekend G closures?",
         "data": "2025 High Volume FHV Trip Data (NYC Open Data nt46-nv3c) by zone and hour; MTA hourly ridership from 2025",
         "design": "new registration before querying: same model restricted to closure hours, prediction taken from this outcome", "priority": "high"},
        {"question": "Where did the other displaced riders go: shuttle bus, another subway line, Citi Bike, or no trip?",
         "data": "MTA bus ridership for the B94 and B98 shuttles (not in the open hourly bus file as far as we found), Citi Bike trip records, entries at neighbouring L, 7, C, J and M stations",
         "design": "accounting of entries lost at closed stations against gains on each alternative, by phase", "priority": "medium"},
        {"question": "The System graph has no concepts for ride-hailing or subway service; a live lookup was not possible on this machine",
         "data": "System Public Graph", "design": "repeat the lookup with the API key; add the transport literature cited in the registration", "priority": "low"},
    ],
    "figures": ["figures/transit/gtrain_shutdown_pickups.png"],
    "notes": (
        f"First stage: entries at the G-only stations coded closed fell {fs['pooled_fall_pct']}% from their 1 to 27 June mean during their closed phase "
        f"({fs['lost_entries_total']:,} entries over the shutdown); every station coded closed fell by at least 97%, and Nassau Av and Bedford-Nostrand Avs, coded as terminals, kept their entries. "
        "In 2023, on the same days moved back 364 days, no station shows a closure. Stations on the open part of the line lost 15% to 60% of their entries while the line was cut elsewhere. "
        "The reference period is not clean: on Saturday 8 and Sunday 9 June 2024 entries at the ten stations fell by about three quarters, which indicates a weekend closure before the shutdown; the coding was not changed. "
        f"Sample: 7 treated and 32 control zones, 120 days, {p['n_obs']} zone-days; Astoria Park, Green-Wood Cemetery and Saint Michaels Cemetery/Woodside were dropped by the volume rule. "
        f"Registered secondary and sensitivities, in log points: G-dependent zones (Greenpoint, Bedford, Clinton Hill) {f('g_dependent')}, 2023 placebo for them {f('g_dependent_placebo_2023')}; "
        f"phase 1 {f('phase1')}, phase 2 {f('phase2')}, phase 3 {f('phase3')}; triple difference with 2023 {f('triple_difference')}; Poisson on counts {f('poisson')}; "
        f"all Brooklyn and Queens controls {f('controls_all_bk_qn')}; controls not touching a treated zone {f('controls_drop_adjacent')}; weekdays {f('weekdays')}; "
        f"Uber {f('uber')}; Lyft {f('lyft')}. By zone (one treated zone each, so the intervals are not reported): Greenpoint {e['zone_112']['estimate']:+.3f}, "
        f"Long Island City/Hunters Point {e['zone_145']['estimate']:+.3f}, Clinton Hill {e['zone_49']['estimate']:+.3f}, Bedford {e['zone_17']['estimate']:+.3f}, "
        f"Fort Greene {e['zone_97']['estimate']:+.3f}, East Williamsburg {e['zone_80']['estimate']:+.3f}, Williamsburg South Side {e['zone_256']['estimate']:+.3f}. "
        "The effect is largest where the G is the only line in the zone (Greenpoint) and absent where the L is at the same complex (Williamsburg South Side), which is the pattern substitution predicts, but this ordering was not a registered test. "
        f"Implied diversion: about {dv['extra_pickups']:,} extra pickups over {dv['treated_zone_days']} treated zone-days against {dv['lost_entries']:,} entries lost at the closed stations, "
        f"or {dv['extra_pickups_per_100_lost_entries']:.1f} pickups per 100 lost entries (0.2 to 9.3 from the clustered interval). Entries lost at a closed station overstate trips lost, since many riders entered at another station. "
        "Relation to commute-fhv-subway-distance (contested): that claim found fewer app pickups per resident in zones farther from the subway (elasticity -0.30) in the 2024 cross-section. "
        "This claim removes subway service from the same zones for weeks and finds a rise of about 4% that is not established. The two do not conflict: the cross-section compares places that differ in density and car ownership, "
        "and the shutdown measures the short-run response of people who already live without a car near a station. At most about one displaced entry in twenty became an app trip, so the subway and app trips are weak substitutes at this margin. "
        "Deviations from the task text, all fixed in the registration before any data were queried: the shutdown was in 2024, not 2023, so the trip data are 2024 with 2023 as the placebo year; phase 3 ran to Church Av with the F serving the shared stations. "
        "A wording error in the registration: Court Sq is served by the 7, E, F and G in the station table, not the 7, E and M. "
        "The trip counts came from the TLC parquet files (the registered fallback), read remotely with DuckDB; nothing was stored outside the repository. "
        "The graph evidence rests on cached responses; a live lookup is pending."),
}

if __name__ == "__main__":
    print(claims.outcome(REC))
