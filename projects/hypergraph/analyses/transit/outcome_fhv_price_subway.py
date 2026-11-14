"""Write the outcome for transit-fhv-price-subway from data/derived/transit/fhv_price_subway_results.json.
Usage: python -m analyses.transit.outcome_fhv_price_subway"""
import json
import math
from pathlib import Path

from concord import claims

ROOT = Path(__file__).resolve().parents[2]
P = ROOT / "data" / "derived" / "transit" / "fhv_price_subway_results.json"
R = json.loads(P.read_text())
A, FS, S, X = R["primary_2019"], R["first_stage_2019"], R["secondary_2025"], R["exploratory_first_stage_touching_trips"]
p, pl = A["primary"], A["placebo_2018_vs_2017"]
f = lambda r: f"{r['pct']:+.2f}% ({r['lo']:+.2f} to {r['hi']:+.2f})"

# EXPLORATORY composition: year-over-year change in trips touching the zone, no comparison area.
t = X["fhv_and_taxi"]
yoy = math.log(t["touch_per_weekday_2019_post"] / t["touch_per_weekday_2019_pre"]) - math.log(t["touch_per_weekday_2018_post"] / t["touch_per_weekday_2018_pre"])
dT = t["touch_per_weekday_2019_pre"] * (1 - math.exp(yoy))
Ein, Eout = p["entries_inside_y1_pre"], p["entries_outside_y1_pre"]
comp = {}
for name, (o, d, s) in {"p_lo": (1.1, 0.10, 0.6), "p_c": (1.3, 0.25, 0.75), "p_hi": (1.5, 0.50, 1.0)}.items():
    comp[name] = round(max(100 * (s * o * d * dT / Ein - (1 - s) * o * d * dT / Eout), 0), 3)
EXP = {"label": "EXPLORATORY, not registered", "touching_trips_change_vs_2018_pattern_pct": round(100 * (math.exp(yoy) - 1), 2),
       "trips_lost_per_weekday": round(dT), **comp, "min_detectable_effect_pct": R["rule8"]["min_detectable_effect_pct"],
       "se_pct": R["rule8"]["se_pct"], "se_needed_for_D4_at_p_c_pct": round(comp["p_c"] / 2, 3)}
R["exploratory_composition"] = EXP
P.write_text(json.dumps(R, indent=1, default=str))

src = []
seen = {}
for s in R["sources"]:  # one record per dataset, with the number of queries; full list in the results file
    k = s.get("dataset") or s.get("url")
    if s.get("kind") == "tlc-trip-record-file":
        src.append(s)
    elif k not in seen:
        seen[k] = {**s, "n_queries": 1}
    else:
        seen[k]["n_queries"] += 1
for v in seen.values():
    if v["n_queries"] > 1:
        v["query"] = {"note": "weekly queries of the same form over the registered windows; every query with its fetch time is in data/derived/transit/fhv_price_subway_results.json", "example": v.get("query")}
    src.append(v)
src.append({"kind": "sysgraph", "note": "No live lookup: the API key is not on this machine. Cached evidence (data/derived/commuting/graph_evidence.json) has no concept for ride-hailing, taxis or the subway. Live lookup pending."})

rec = {
    "id": "transit-fhv-price-subway",
    "verdict": "no_test",
    "city_effect": {"label": "Weekday subway entries south of 96th St vs outside, 8 weeks after 2 Feb 2019 vs 3 weeks before, less the same in 2018 (not decisive: the registered first-stage gate failed)",
                    "estimate": p["pct"], "lo": p["lo"], "hi": p["hi"], "scale": "percent change in entries", "null": 0,
                    "n": p["n_inside"] + p["n_outside"]},
    "graph_effect": {"label": "No graph findings on ride-hail and transit. Literature: transit ridership +5% two years after Uber entry (Hall et al. 2018) against -1.3% a year for heavy rail (Graehler et al. 2019) and -8.9% (Diao et al. 2021)",
                     "estimate": None, "lo": None, "hi": None, "scale": "percent change in transit ridership", "null": 0},
    "sources": src,
    "prediction_scored": (
        "not scored. The registration made the test conditional on a first stage: FHV and taxi pickups inside the area had to fall "
        "relative to outside, with an interval excluding zero. More than 10% of FHV trips had no pickup zone in three of the four windows "
        f"(19.3% and 18.3% in 2018, 10.9% in January 2019), so by the registered rule the gate used taxis alone, and taxi pickups changed by {f(FS['taxi'])}. "
        f"The combined series gives {f(FS['fhv_and_taxi'])} and FHV alone {f(FS['fhv'])}. The gate failed, so the verdict is no_test. "
        f"The registered subway estimate is {f(p)}, with a placebo of {f(pl)}; had the gate passed, the verdict would have been unsettled."),
    "settle": ("Two things. First, a first stage that measures the treatment: the surcharge applies to any trip that touches the area, so a trip from an "
               "airport to Midtown is charged although its pickup is outside. Trips touching the area need a comparison that is not charged, for example "
               "trips of similar length wholly outside it, from records with complete zones (the high-volume files from February 2019 are complete; the "
               "2018 FHV files are not). Second, a subway measure that can see an effect of a few tenths of a percent: entries by hour and fare type at "
               "stations nearest the places where short for-hire trips fell most, or the MTA origin-destination estimates, which begin only in 2021 and "
               "so cover the 2025 toll but not the 2019 surcharge."),
    "research_needed": [
        {"question": "How many of the trips priced off by the 2019 surcharge moved to the subway?",
         "data": "A rider survey or panel of app users before and after February 2019; none is public. TLC trip records show the trips lost, not where the riders went.",
         "design": "panel of riders, or a station-level design with exposure measured by lost short trips near each station", "priority": "medium"},
        {"question": "Is there a peer-reviewed estimate of the subway effect of the 2019 surcharge? The only study found is an undergraduate thesis (Dilworth 2023), which also finds no significant rise.",
         "data": "MTA Subway Hourly Ridership 2017-2019 (t69i-h2me), TLC trip records", "design": "synthetic control at station level with line-level service controls", "priority": "low"},
        {"question": "The System graph has no findings linking ride-hail prices or availability to transit ridership. Add Hall et al. 2018, Graehler et al. 2019, Diao et al. 2021, Erhardt et al. 2022 and Li and Vignon 2024.",
         "data": "the transport literature", "design": "graph curation", "priority": "high"},
        {"question": "Did subway entries rise with the 2025 zone toll once riders who board outside the zone are counted at their destination?",
         "data": "MTA Subway Origin-Destination Ridership Estimates 2024 and 2025 (jsu2-fbtj, y2qv-fytt)", "design": "difference in differences on trips ending in the zone", "priority": "medium"},
    ],
    "figures": ["figures/transit/fhv_price_subway.png"],
    "notes": (
        f"Subway, 2019 (registered): {p['n_inside']} complexes inside and {p['n_outside']} outside, {p['n_clusters']} grid cells; mean weekday entries in the 2019 pre window "
        f"{Ein:,} inside and {Eout:,} outside. Sensitivities: control Manhattan north of 96th St {f(A['S1_control_manhattan_north'])}; control Bronx, Brooklyn and Queens "
        f"{f(A['S2_control_bronx_brooklyn_queens'])}; unweighted {f(A['S3_unweighted'])}; with the 96 St complexes {f(A['S4_with_96_st_complexes'])}; without L complexes "
        f"{f(A['S5_without_L_complexes'])}; 16-week post window {f(A['S6_post_16_weeks'])}; nights 20:00-04:00 {f(A['S7_night_20_to_04'])} with a night placebo of "
        f"{f(A['S7_placebo_night'])}; weekends {f(A['S8_weekends'])}; 2019 alone {f(A['S9_2019_only'])}. The standard error is {R['rule8']['se_pct']} log points x 100, so the "
        f"smallest effect the test could detect with 80% power is about {R['rule8']['min_detectable_effect_pct']}%, above the +1.3% registered as the largest plausible effect. "
        "The registered composed range could not be computed as planned because the gate series did not fall. "
        f"Exploratory, not registered: FHV and taxi trips touching the area were {t['touch_per_weekday_2019_pre']:,} a weekday before and {t['touch_per_weekday_2019_post']:,} after, "
        f"against {t['touch_per_weekday_2018_pre']:,} and {t['touch_per_weekday_2018_post']:,} in the same weeks of 2018, a change of {EXP['touching_trips_change_vs_2018_pattern_pct']}% "
        f"with no comparison area (about {EXP['trips_lost_per_weekday']:,} trips a weekday). With the registered constants this would add {comp['p_c']}% to zone entries "
        f"(range {comp['p_lo']}% to {comp['p_hi']}%), which the subway test cannot distinguish from zero. Li and Vignon (2024) report larger falls (11% ride-hail, 8% taxi). "
        f"Secondary, 2025 zone toll (descriptive): entries at CBD complexes against all others, January-March 2025 against autumn 2024, less the same a year earlier, {f(S['estimate'])}; "
        f"placebo {f(S['placebo_2024_vs_2023'])}; against Manhattan north of 60th St {f(S['control_manhattan_north_of_60'])}; nights {f(S['night'])}. "
        "Entries are counted where riders board, so a commuter who leaves a car at home adds an entry outside the zone in the morning and one inside in the evening. "
        "One week of 2019 ridership (13-19 May, used only by the 16-week sensitivity) timed out as a weekly query and was fetched day by day. "
        "Two-week queries cached before the chunk size was changed are not used."),
    "exploratory": EXP,
}
print(claims.outcome(rec))
