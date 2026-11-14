"""Outcomes of the two Chicago transfer claims. Run after chicago_heat, chicago_weekday and the graph scripts.
    ~/.venvs/nyc-concordance/bin/python -m analyses.transfer.outcomes
"""
import json
from collections import defaultdict
from pathlib import Path

from concord import claims

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "data" / "derived" / "graph" / "transfer_chicago"


def sources(res, portal):
    by = defaultdict(list)
    for s in res["sources"]:
        by[s.get("dataset") if s.get("kind") != "noaa-ghcnd" else "noaa:" + s["station"]].append(s)
    out = []
    for k, v in by.items():
        s = v[0]
        if s.get("kind") == "noaa-ghcnd":
            out.append({**{x: s[x] for x in ("kind", "station", "url", "last_modified", "fetched", "dataset")}, "data_access": "open"})
        else:
            out.append({"kind": "socrata (recorded by concord/socrata.py as nyc-open-data)", "portal": portal, "dataset": k, "name": s.get("name"), "url": s.get("url"),
                        "rows_updated_at": s.get("rows_updated_at"), "n_queries": len(v), "fetched_first": v[0]["fetched"], "fetched_last": v[-1]["fetched"],
                        "example_query": s.get("query"), "data_access": "open"})
    return out


GE = [
    {"relationship_id": "4FaXcuNJRt|14UOQBVakG", "concepts": ["temperature", "firearm"], "n_findings": 1, "n_studies": 1, "direction": "+",
     "summary": "Lyons et al. 2022, 100 US cities 2015-2020, RR 1.17 (1.12 to 1.21) for the 84th percentile of daily maximum temperature against the city median; matches the abstract (PMID 36525273, read 12 Nov 2026). The only gun-violence temperature finding in the graph; it covers Chicago and New York but reports no city-specific estimate.",
     "pubmed_ids": [36525273], "in_dataverse_csv": None},
    {"relationship_id": "4FaXcuNJRt|YZku29igbl", "concepts": ["temperature", "homicide"], "n_findings": 4, "n_studies": 2, "direction": "+",
     "summary": "Xu et al. 2020 (PMID 32738768) gives intentional homicide +9.5% (4.3 to 15.0) per 5 C in Chicago and +8.8% (1.5 to 16.6) in New York, lag 0-7; the graph stores these as odds ratios 0.095 and 0.088 (the abstract gives percent increases, so the stored values are mis-scaled). Rahman et al. 2023, California, +4.9% (PMID 36858215). This is the graph's one direct two-city comparison, and it shows Chicago and New York within 1 point of each other.",
     "pubmed_ids": [32738768, 36858215], "in_dataverse_csv": None},
    {"relationship_id": "ungrounded variable: violent crime counts | daily summer temperature", "concepts": ["violent crime", "temperature"], "n_findings": 2, "n_studies": 1, "direction": "+",
     "summary": "Heo et al. 2024, South Korea, warm months 2016-2020: RR 1.11 (1.09 to 1.15) at the 70th percentile and 1.04 (1.01 to 1.07) at the 90th, against the 10th percentile; matches the abstract (PMID 38331944). Found only by variable-name search; neither variable is grounded to a concept, so the concept-level relationship does not exist.",
     "pubmed_ids": [38331944], "in_dataverse_csv": None},
]


def main():
    h = json.loads((D / "heat_results.json").read_text())
    w = json.loads((D / "weekday_results.json").read_text())
    ex = json.loads((D / "weekday_exploratory_no_polar_vortex_week.json").read_text())
    p = h["primary"]
    claims.outcome({
        "id": "transfer-chicago-heat-shootings", "verdict": "confirmed",
        "city_effect": {"label": "Chicago daily gunshot-injury cases (gumc-mgzr), Midway TMAX lag 0, NB GLM with DOW, month, year, holiday, rain",
                        "estimate": p["estimate"], "lo": p["lo"], "hi": p["hi"], "scale": "IRR per 5 C", "null": 1, "n": h["n_days"]},
        "graph_effect": {"label": "Xu et al. 2020 Chicago homicide, per 5 C mean temperature lag 0-7 (graph stores 0.095 as an odds ratio)", "estimate": 1.095, "lo": 1.043, "hi": 1.150, "scale": "OR per 5 C", "null": 1},
        "graph_evidence": GE,
        "sources": sources(h, "data.cityofchicago.org"),
        "prediction_scored": ("hit: the registered band was 1.110 to 1.183 with lower limit above 1; the Chicago estimate is 1.131 (1.120 to 1.143), inside the band and "
                              "overlapping New York's interval (1.130 to 1.163) in the range 1.130 to 1.143. The registered magnitude 1.10 to 1.20 also holds. The estimate is 0.015 below New York's, about 10% of New York's excess."),
        "components": {"n_cases": h["n_cases"], "period": h["period"], "station": h["station_used"], "tmax_missing_share": h["tmax_missing_share"], "sensitivity": h["sensitivity"],
                       "reeping_hemenway_per_5C": {"weekday": 1.158, "weekend_holiday": 1.190},
                       "note": "Chicago's weekday (1.126, 1.114 to 1.138) and weekend/holiday (1.140, 1.127 to 1.154) estimates lie below Reeping and Hemenway's 1.158 and 1.190 and their intervals do not include them. In their 2012-2016 window the same model gives 1.146 (1.126 to 1.167), which includes 1.158."},
        "settle": "The transfer is shown for one outcome definition and one weather station. A hospital-based injury series would test whether the result depends on police recording.",
        "research_needed": [{"question": "Does the temperature slope differ by neighbourhood heat exposure and air-conditioning use inside each city?", "data": "Shooting locations (both portals give block or coordinates) joined to land surface temperature", "design": "Case-crossover by community area or precinct", "priority": "medium"}],
        "figures": ["figures/graph/transfer_chicago.png"],
        "notes": "Same negative binomial model as heat-shootings, fitted to 6,085 days and 41,063 cases in Chicago from 2010 (when the portal's non-fatal shooting series begins) to 31 August 2026. Midway TMAX was missing on 0.03% of days. Within-city seasonality is absorbed by month and year terms, so the estimate describes day-to-day deviations from the month's level.",
    })
    d = w["loop"]["delta"]
    claims.outcome({
        "id": "transfer-chicago-weekday-pattern", "verdict": "contested",
        "city_effect": {"label": "Change in the Monday/Friday deficit of Chicago Loop 'L' entries, Sep 2025-Aug 2026 minus 2019", "estimate": d["estimate"], "lo": d["lo"], "hi": d["hi"],
                        "scale": "percentage points of the Tue-Thu mean", "null": 0, "n": f"{w['n_weeks']['recent']} weeks recent, {w['n_weeks']['2019']} weeks 2019, {w['n_loop']} Loop stations"},
        "graph_effect": None,
        "graph_evidence": [{"note": "Concept and variable searches found no finding on the day-of-week pattern of transit use. Variable search for ridership gives 11 studies, none a ridership time series of a US city (see docs/graph_discovery.md).", "n_findings": 0}],
        "sources": sources(w, "data.cityofchicago.org"),
        "prediction_scored": ("miss on size, hit on sign: registered refute_if (Delta above 13.1 points) is met by 15.9 (12.0 to 22.7). The sign, the midweek plateau (Loop recent midweek range {:.1f} points) and "
                              "Loop-above-rest ordering transfer; the size is about 1.8 times New York's.").format(w["loop"]["recent"]["range"]),
        "components": {"loop_recent_mf_deficit_pct": [w["loop"]["recent"]["mf"], *w["loop"]["recent"]["mf_ci"]], "loop_2019_mf_deficit_pct": [w["loop"]["y2019"]["mf"], *w["loop"]["y2019"]["mf_ci"]],
                       "loop_recent_monday_friday_pct": [w["loop"]["recent"]["def_mon"], w["loop"]["recent"]["def_fri"]], "rest_delta_points": w["rest"]["delta"],
                       "rest_recent_mf_pct": w["rest"]["recent"]["mf"], "loop_minus_rest_delta": w["loop_minus_rest_delta"], "placebo_2019_minus_2018": w["placebo_2019_minus_2018"]["delta"],
                       "sensitivity": {k: w[k]["delta"] if isinstance(w[k].get("delta"), dict) else w[k].get("delta") for k in ("S1_median", "S3_calendar_2025", "S4_no_strike_weeks", "S6_wide_box")} | {"S2_days_only": w["S2_days_only"]["delta"]},
                       "exploratory_no_polar_vortex_week_2019_01_28": ex,
                       "note": "The 2019 baseline mean is distorted by the week of 28 January 2019 (polar vortex; Wednesday entries 27% of the week's Tue-Thu mean). The registered primary keeps that week. Without it the Loop Delta is 12.9 (11.6 to 14.2), just under the refutation limit; the placebo year difference (-3.5, -10.2 to 0.3) fails the registered 1.5-point check for the same reason. Exploratory; it does not decide the verdict (precedence rule 4)."},
        "settle": "A registered week-level treatment of weather outliers (for example dropping weeks with a day below 50% of the week's median), written before data are seen, would settle whether the Loop size is 12.9 or 15.9. Chicago office-badge data (Kastle) by weekday would show whether the CTA pattern reflects workplace attendance.",
        "research_needed": [{"question": "Why is the Friday deficit in the Loop (20.1%) larger than the Monday deficit (16.4%) when New York shows the reverse?", "data": "Metra and CTA ridership by day for the same weeks; employer schedule surveys", "design": "Descriptive comparison with Kastle weekday occupancy", "priority": "medium"}],
        "figures": ["figures/graph/transfer_chicago.png"],
        "notes": f"Data end 2026-08-31, so the recent period is the registered fallback, 1 September 2025 to 31 August 2026. The Loop rule selected {w['n_loop']} station ids. Loop mean weekday entries fell from {w['levels_mean_weekday_entries']['loop_2019']:.0f} in 2019 to {w['levels_mean_weekday_entries']['loop_recent']:.0f}; the whole 'L' system from {w['levels_mean_weekday_entries']['system_2019']:.0f} to {w['levels_mean_weekday_entries']['system_recent']:.0f}. Rest of system: Delta {w['rest']['delta']['estimate']:.1f} ({w['rest']['delta']['lo']:.1f} to {w['rest']['delta']['hi']:.1f}) against New York's 4.2; it lies above the registered range of 2 to 7 points, with an interval (5.1 to 15.3) that overlaps it.",
    })


if __name__ == "__main__":
    main()
