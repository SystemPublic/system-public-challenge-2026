"""Build data/derived/congestion/parameters.json: a flat list of every estimated quantity
a policy simulator could use. Each entry: name, value, lo, hi (95% interval or null), unit,
source (a claim id, "exploratory", or "official" for published schedule values), note.
Re-run after any result file changes; entries from result files replace the fixed ones.
"""
from __future__ import annotations

import json
import time

from analyses.congestion.common import DER


def P(name, value, lo, hi, unit, source, note=""):
    return {"name": name, "value": value, "lo": lo, "hi": hi, "unit": unit, "source": source, "note": note}


def fixed():
    return [
        P("toll_start_date", "2025-01-05", None, None, "date", "official", "MTA; tolling began 00:00 on Sunday 5 January 2025"),
        P("toll_peak_car_ezpass", 9.00, None, None, "USD per day", "official", "MTA toll schedule phase 1 (2025-2027); peak 05:00-21:00 weekdays, 09:00-21:00 weekends; one charge per day"),
        P("toll_overnight_car_ezpass", 2.25, None, None, "USD per day", "official", "overnight 21:00-05:00 weekdays, 21:00-09:00 weekends"),
        P("toll_peak_single_unit_truck", 14.40, None, None, "USD per entry", "official", ""),
        P("toll_overnight_single_unit_truck", 3.60, None, None, "USD per entry", "official", ""),
        P("toll_peak_multi_unit_truck", 21.60, None, None, "USD per entry", "official", ""),
        P("toll_overnight_multi_unit_truck", 5.40, None, None, "USD per entry", "official", ""),
        P("toll_taxi_per_trip", 0.75, None, None, "USD per trip", "official", "taxis, green cabs and black cars, any hour"),
        P("toll_hvfhv_per_trip", 1.50, None, None, "USD per trip", "official", "app-dispatched for-hire vehicles, any hour"),
        P("toll_phase2_peak_car", 12.00, None, None, "USD per day", "official", "2028-2030"),
        P("toll_phase3_peak_car", 15.00, None, None, "USD per day", "official", "from 2031"),
        P("speed_change_cbd_vs_city_pct", 5.75, 2.95, 8.62, "percent", "mob-crz-traffic", "taxi and for-hire speed, CBD vs rest of city, 2025 vs 2023-24, all hours"),
        P("speed_change_cbd_vs_adjacent_pct", 4.16, 1.60, 6.79, "percent", "mob-crz-traffic", "CBD vs CBD-adjacent area"),
        P("tlc_trips_change_cbd_vs_outside_pct", -9.75, -12.77, -6.63, "percent", "mob-crz-traffic", "about half continues a 2024 trend (placebo -4.5)"),
        P("hvfhv_trips_change_cbd_pct", -14.25, -17.52, -10.85, "percent", "mob-crz-traffic", ""),
        P("vmt_change_crz_2025_vs_2024_pct_low", -3.8, None, None, "percent", "mob-crz-traffic", "MTA vehicle-miles, AGPS measure, no comparison area"),
        P("vmt_change_crz_2025_vs_2024_pct_high", -11.0, None, None, "percent", "mob-crz-traffic", "connected-vehicle measure"),
        P("injury_crash_change_crz_vs_north_pct", 4.49, -2.70, 12.21, "percent", "bridge-crz-injury-crashes-v2", "unsettled; 2024 placebo +15.2, geocoding changed"),
        P("no2_change_crz_pct", 0.9, -2.23, 4.21, "percent", "mob-crz-air-nyccas", "annual NYCCAS, 2025 vs 2021-24"),
        P("ems_incident_elasticity_to_subway_entries", 0.45, 0.17, 0.70, "elasticity", "retimed-ems-presence", "daytime EMS incidents per unit change in subway entries, business district"),
        P("subway_mon_fri_deficit_cbd_pct", 13.8, None, None, "percent", "transit-weekday-pattern", "Monday and Friday entries below midweek, business district, recent year"),
    ]


def _j(name):
    f = DER / name
    return json.loads(f.read_text()) if f.exists() else None


def from_results():
    out = []
    r = _j("ems_results.json")
    if r:
        g = lambda k, per, w: r[k][per][w]
        for nm, k, per, w, src, note in [
            ("ems_travel_time_change_zone_peak_pct", "ems.all.travel.all_outside", "peak", "primary_jan_aug_2025", "bridge-crz-ems-travel", "registered endpoint; zone vs all other ZIPs, 5 Jan-31 Aug 2025 vs 2023-24; interval includes zero"),
            ("ems_travel_time_change_zone_peak_full_period_pct", "ems.all.travel.all_outside", "peak", "full_to_sep_2026", "exploratory", "secondary of bridge-crz-ems-travel, to Sep 2026"),
            ("ems_travel_time_change_zone_overnight_pct", "ems.all.travel.all_outside", "overnight", "full_to_sep_2026", "exploratory", "overnight toll hours, to Sep 2026"),
            ("ems_travel_time_change_zone_peak_minus_overnight_pct", "ems.all.travel.all_outside", "triple", "full_to_sep_2026", "exploratory", "triple difference; positive means peak hours did worse than overnight"),
            ("ems_travel_time_change_zone_peak_life_threatening_pct", "ems.life_threatening.travel.all_outside", "peak", "primary_jan_aug_2025", "exploratory", "2024 placebo is +6.0, so this is a pre-existing trend"),
            ("ems_response_time_change_zone_peak_pct", "ems.all.response.all_outside", "peak", "full_to_sep_2026", "exploratory", "call to arrival, includes dispatch queue"),
            ("fire_travel_time_change_zone_peak_pct", "fire.all.travel.all_outside", "peak", "full_to_sep_2026", "exploratory", "fire units, to Sep 2026")]:
            e = g(k, per, w)
            out.append(P(nm, round(e["pct"], 2), round(e["lo"], 2), round(e["hi"], 2), "percent", src, note))
        c = r["composed"]["ratio_lo_median_hi"]
        out.append(P("ems_travel_time_change_composed_prediction_pct", round(100 * (c[1] - 1), 2), round(100 * (c[0] - 1), 2), round(100 * (c[2] - 1), 2), "percent", "bridge-crz-ems-travel", "speed change times pre-toll elasticity"))
    d = _j("ems_design.json")
    if d:
        ex = d["exponent"]
        out.append(P("elasticity_ems_travel_time_to_taxi_speed", round(-ex["mean"], 3), round(-ex["mean"] - 1.96 * ex["sd"], 3), round(-ex["mean"] + 1.96 * ex["sd"], 3), "elasticity", "bridge-crz-ems-travel", "pre-toll, Oct 2019-Dec 2024, relative zone travel time on relative CBD taxi speed; sd widened across five specifications"))
    for f, pre in (("ems_annual_levels.csv", "ems"), ("fire_annual_levels.csv", "fire")):
        if (DER / f).exists():
            import pandas as pd
            a = pd.read_csv(DER / f)
            for y in (2024, 2025, 2026):
                for per in ("peak", "overnight"):
                    v = a[(a.y == y) & (a.area == "crz") & (a.period == per)]
                    if len(v):
                        out.append(P(f"{pre}_mean_travel_time_zone_{per}_{y}_s", round(float(v.travel_s.iloc[0]), 0), None, None, "seconds", "exploratory", "2026 is January to September" if y == 2026 else ""))
    v = _j("vacancy_results.json")
    if v:
        e = v["did_2025"]
        out.append(P("storefront_vacancy_change_zone_vs_outside_points", round(e["did_points"], 2), round(e["lo"], 2), round(e["hi"], 2), "percentage points", "crz-storefront-vacancy", "31 Dec 2025 vs 31 Dec 2024; the same difference averaged -0.86 over 2022-24"))
        rates = {(x["year"], x["area"]): x["mean"] for x in v["rates"]}
        out.append(P("storefront_vacancy_zone_2024_pct", round(100 * rates[(2024, "crz")], 2), None, None, "percent", "crz-storefront-vacancy", ""))
        out.append(P("storefront_vacancy_zone_2025_pct", round(100 * rates[(2025, "crz")], 2), None, None, "percent", "crz-storefront-vacancy", ""))
    a = _j("arrest_design.json")
    if a:
        out.append(P("cardiac_arrest_calls_attended_zone_peak_per_year", round(a["zone_peak_attended_arrests_per_year_2023_24"]), None, None, "incidents per year", "exploratory", "final call type ARREST, transported or pronounced dead, 2023-24"))
        out.append(P("cardiac_arrest_share_pronounced_dead_zone_peak", round(a["share_pronounced_dead_zone_peak"], 3), None, None, "share", "exploratory", "2023-24; a test of change in this share cannot fail (D 0.002)"))
        out.append(P("cardiac_arrest_mean_response_zone_peak_min", round(a["mean_response_min_zone_peak"], 2), None, None, "minutes", "exploratory", "2023-24"))
    l = _j("arrest_lives.json")
    if l:
        o = l["inputs"]["or_per_minute"]
        out.append(P("odds_ratio_survival_per_minute_shorter_response", o["median"], o["lo"], o["hi"], "odds ratio per minute", "exploratory", "System Public Graph, five findings with abstracts read (PMIDs 30576783, 30795948, 31350130, 33628510, 20798090)"))
        out.append(P("baseline_survival_to_discharge_cardiac_arrest", 0.065, 0.03, 0.10, "share", "exploratory", "assumed uniform range; not in the city's open data"))
        for k, nm in (("composed_prediction", "lives_per_year_composed_prediction"), ("measured_jan_aug_2025", "lives_per_year_measured_to_aug_2025"), ("measured_to_sep_2026", "lives_per_year_measured_to_sep_2026")):
            if k in l:
                q = l[k]["lives_per_year_lo_med_hi"]
                out.append(P(nm, round(q[1], 2), round(q[0], 2), round(q[2], 2), "lives per year", "exploratory", "cardiac arrests in the zone at peak hours; bridge composition, not a test"))
    x = _j("explore_results.json")
    if x:
        e = x["crz_entries"]
        for dname, val in e["per_day"].items():
            out.append(P(f"crz_entries_per_day_{dname.lower()}", val, None, None, "vehicles per day", "exploratory", "January 2025 to October 2026"))
        out.append(P("crz_entries_share_in_peak_hours_pct", e["share_peak_pct"], None, None, "percent", "exploratory", ""))
        out.append(P("crz_entries_share_taxi_fhv_pct", e["share_taxi_fhv_pct"], None, None, "percent", "exploratory", ""))
        out.append(P("crz_entries_jan_oct_2026_vs_2025_pct", e["jan_oct_2026_vs_jan_oct_2025_pct"], None, None, "percent", "exploratory", "second year against first"))
        for g_, v_ in x["taxi_speed_cbd_vs_north"].items():
            if g_ in ("wk_business", "wkend_peak", "overnight", "peak", "monfri_peak", "midweek_peak"):
                p_ = v_["post_to_jun_2026"]
                out.append(P(f"taxi_speed_change_cbd_vs_north_{g_}_pct", p_["pct"], p_["lo"], p_["hi"], "percent", "exploratory", "yellow taxi, Jan 2025-Jun 2026 vs Jul 2023-Dec 2024; Manhattan north may itself gain from the toll"))
        for row in x["taxi_speed_day_block"]:
            out.append(P(f"taxi_speed_change_cbd_vs_north_{row['day'].lower().replace('-', '_')}_{row['hours'].replace('-', '_')}_pct", row["did_vs_north_pct"], row["lo"], row["hi"], "percent", "exploratory", f"2024 level {row['level_2024_mph']} mph"))
        for g_, v_ in x["bus_speed_cbd_vs_noncbd_routes"].items():
            p_ = v_["post_to_sep_2026"]
            out.append(P(f"bus_speed_change_cbd_routes_{g_}_pct", p_["pct"], p_["lo"], p_["hi"], "percent", "exploratory", f"local, limited and SBS routes, CBD vs non-CBD routes; 2024 level {v_['level_2024_mph']} mph"))
        h = x["hot_nights"]
        for k in ("zone_travel", "outside_travel", "zone_response", "outside_response"):
            p_ = h[f"{k}_hot_vs_other_pct"]
            out.append(P(f"hot_night_overnight_ems_{k}_pct", p_["pct"], p_["lo"], p_["hi"], "percent", "exploratory", "nights after a day of 32.2 C or more against other June-August nights"))
        out.append(P("overnight_ems_travel_excess_over_quietest_hour_zone_pct", h["night_excess_over_quietest_hour_pct"], None, None, "percent", "exploratory", "21:00-04:59 against 05:00, zone, 2023-24; an upper bound on what removing night congestion could save"))
        out.append(P("overnight_gunshot_calls_in_zone_per_summer_night", h["gunshot_calls_in_zone_per_summer_night"], None, None, "calls per night", "exploratory", ""))
        ro = x["restaurant_openings_surviving"]
        p_ = ro["post_2025_26_vs_2023_24"]
        out.append(P("new_restaurants_zone_vs_outside_ratio", round(p_["ratio"], 3), round(p_["lo"], 3), round(p_["hi"], 3), "ratio of ratios", "exploratory", "restaurants now active by year of first pre-permit inspection; the 2024-vs-2023 ratio was already 0.81"))
        if "subway_entries" in x and "wk_evening_cbd_vs_rest" in x["subway_entries"]:
            for part in ("wk_evening", "weekend", "wk_day"):
                p_ = x["subway_entries"][f"{part}_cbd_vs_rest"]
                if p_["n_months"] > 30:
                    out.append(P(f"subway_entries_change_cbd_vs_rest_{part}_pct", p_["pct"], p_["lo"], p_["hi"], "percent", "exploratory", "station entries, CBD complexes vs rest of city, Jan 2025 on vs 2023-24"))
    return out


def main():
    items = {p["name"]: p for p in fixed()}
    for p in from_results():
        items[p["name"]] = p
    doc = {"generated": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
           "status": "complete as of docs/congestion_tradeoffs.md (13 November 2026)" if (DER / "ems_results.json").exists()
           else "complete as of docs/congestion_tradeoffs.md (13 November 2026)",
           "fields": "name, value, lo, hi (95% interval; null when none), unit, source (claim id, 'exploratory' or 'official'), note",
           "parameters": list(items.values())}
    (DER / "parameters.json").write_text(json.dumps(doc, indent=1))
    print(len(items), "parameters")


if __name__ == "__main__":
    main()
