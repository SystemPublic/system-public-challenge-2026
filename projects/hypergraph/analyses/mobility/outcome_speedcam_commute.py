"""Outcomes for mob-speedcam-247 and mob-active-commute-obesity."""
import json

import pandas as pd

from concord import claims
from analyses.mobility.common import DER

S = json.loads((DER / "speedcam_results.json").read_text())
r = S["results"]
f = lambda x: f"{x['ratio']:.3f} ({x['lo']:.3f}-{x['hi']:.3f})"
g = pd.read_csv(DER / "speedcam_monthly_by_group.csv", parse_dates=["m"])
p = g.pivot(index="m", columns="group", values="injury_crashes")
share = lambda a, b: 100 * p.loc[a:b, "new"].sum() / p.loc[a:b].sum().sum()
SH = {k: round(share(*k.split("/")), 1) for k in ("2019-01/2019-12", "2020-08/2021-07", "2021-08/2022-07", "2022-08/2023-07", "2023-08/2024-07")}


def night_share(rows):
    tot = sum(int(x["n"]) for x in rows)
    night = sum(int(x["n"]) for x in rows if (x["ap"] == "P" and x["hh"] in ("10", "11")) or
                (x["ap"] == "A" and x["hh"] in ("12", "01", "02", "03", "04", "05")))
    return round(100 * night / tot, 1), tot


NJ, TJ = night_share(S["mechanism"]["2022-07"])
NS, TS = night_share(S["mechanism"]["2022-09"])

speed = {
    "id": "mob-speedcam-247",
    "verdict": "unsettled",
    "city_effect": {"label": "Injury crashes, new hours vs old hours, Aug 2022-Jul 2023 vs Aug 2021-Jul 2022 (ratio of ratios), citywide",
                    "estimate": round(r["injury_crashes"]["ratio"], 3), "lo": round(r["injury_crashes"]["lo"], 3),
                    "hi": round(r["injury_crashes"]["hi"], 3), "scale": "ratio of ratios", "null": 1,
                    "n": r["injury_crashes"]["n"]},
    "graph_effect": {"label": "Graph findings near camera sites: Barcelona RR 0.73 (0.63-0.85) collisions; South Wales injurious crashes 0.49 (0.42-0.57)",
                     "estimate": 0.73, "lo": 0.63, "hi": 0.85, "scale": "rate ratio, camera sites", "null": 1},
    "sources": S["sources"] + [{"kind": "sysgraph", "file": "data/derived/mobility/graph_evidence.json", "note": "speed camera variable associations"}],
    "prediction_scored": (f"partial. The estimate {f(r['injury_crashes'])} is inside the registered range (0.92-1.00) but its "
                          "interval crosses 1, so the support condition is not met and the refutation condition is not met "
                          f"either. Persons injured: {f(r['injured'])}; pedestrians injured: {f(r['ped_injured'])}; persons "
                          f"killed: {f(r['killed'])}. The placebo year (fake start 1 Aug 2021) gives {f(r['injury_crashes_placebo2021'])}."),
    "settle": ("Crashes geocoded within about 250 m of each camera, compared by hour group before and after August 2022, with "
               "nearby non-camera road segments as a second control. This needs the camera locations, which NYC DOT does not "
               "publish as open data (the ticket data carry no coordinates). Hourly traffic volumes by hour group would remove "
               "the main confounder, the post-pandemic shift of travel between night and day."),
    "research_needed": [
        {"question": "Publish NYC school-zone speed camera locations and activation dates as open data.",
         "data": "NYC DOT camera inventory", "design": "site-level DiD with distance bands", "priority": "high"},
        {"question": "Did the share of travel at night and on weekends change in 2022-23 relative to weekdays?",
         "data": "MTA bridge and tunnel hourly crossings, DOT traffic speeds and counts by hour", "design": "exposure denominators by hour group", "priority": "medium"},
        {"question": "The graph holds 7 speed-camera associations from 6 studies, one of them mis-extracted; add the Cochrane review and US automated enforcement studies.",
         "data": "Wilson et al. 2010 Cochrane review; IIHS studies", "design": "graph curation", "priority": "medium"},
    ],
    "figures": ["figures/mobility/speedcam_247_new_vs_old_hours.png"],
    "notes": (f"The mechanism is visible: in July 2022, {NJ}% of school-zone speed camera tickets ({TJ:,} in all) were issued "
              f"between 10 pm and 6 am; in September 2022, {NS}% ({TS:,}) were (Open Parking and Camera Violations, nc67-uf89; "
              "weekend tickets are not separated here). The share of injury crashes that fall in the new hours was "
              f"{SH['2019-01/2019-12']}% in 2019, rose to {SH['2020-08/2021-07']}% and {SH['2021-08/2022-07']}% in the two "
              f"pandemic-affected years, and was {SH['2022-08/2023-07']}% and {SH['2023-08/2024-07']}% in the two years after "
              "the change. The fall after August 2022 is a return to the 2019 share, which the design cannot separate from the "
              "end of pandemic-era travel patterns. NYC DOT reports about 7.6% fewer injuries in the new hours at camera "
              "locations; a citywide effect of that size diluted by unaffected streets would be smaller than the interval here "
              "can resolve. Graph check: PMID 17666698 has a second association (RR 0.99) that is the comparison roads, not the "
              "cameras, so the graph mis-extracts it as a camera effect."),
}

C = json.loads((DER / "active_commute_results.json").read_text())
c = C["results"]
h = lambda x: f"{x['slope']:+.2f} ({x['lo']:+.2f} to {x['hi']:+.2f})"
commute = {
    "id": "mob-active-commute-obesity",
    "verdict": "confirmed",
    "city_effect": {"label": "Adult obesity (percentage points) per 10 points of walk-or-bike commute share, poverty-adjusted, 42 UHF neighbourhoods",
                    "estimate": round(c["poverty"]["slope"], 2), "lo": round(c["poverty"]["lo"], 2), "hi": round(c["poverty"]["hi"], 2),
                    "scale": "percentage points of obesity per 10 points of active commuting", "null": 0, "n": c["poverty"]["n"]},
    "graph_effect": {"label": "Flint et al. 2014: active commuters' BMI about 1 kg/m2 lower than car commuters (individual level); graph physical activity -> obesity findings split in sign",
                     "estimate": None, "lo": None, "hi": None, "scale": "kg/m2", "null": 0},
    "sources": C["sources"] + [{"kind": "sysgraph", "file": "data/derived/mobility/graph_evidence.json",
                                "relationships": ["dPeET-pgVN|cj7G775u_Q", "_2dhcsFISl|cj7G775u_Q"]}],
    "prediction_scored": (f"partial: direction hit, magnitude miss. The poverty-adjusted slope is {h(c['poverty'])} points per 10 "
                          "points, larger than the registered range (-0.5 to -4). Unadjusted it is "
                          f"{h(c['unadjusted'])}; with borough effects {h(c['poverty_boro'])}; without Manhattan {h(c['poverty_no_manhattan'])}."),
    "settle": ("The association is too large to be the effect of commuting on body weight. If active commuters weigh about "
               "1 kg/m2 less (Flint et al. 2014), moving 10% of workers from other modes to walking or cycling would lower "
               "neighbourhood obesity by well under one percentage point, while the slope here is about six. The rest is "
               "composition and selection: income above the poverty line, education, race and ethnicity, age, and who chooses "
               "walkable neighbourhoods. Individual-level data (CHS microdata with commute mode, or a cohort) and a change "
               "design, such as obesity before and after new bike lanes or Citi Bike stations arrive in a neighbourhood, would "
               "settle the causal question."),
    "research_needed": [
        {"question": "Does obesity change in neighbourhoods after the bicycle network or Citi Bike expands into them?",
         "data": "EHDP bicycle network coverage (indicator 2390), Citi Bike station dates, CHS obesity by year", "design": "staggered DiD by UHF", "priority": "medium"},
        {"question": "Individual-level association of commute mode with BMI in NYC, adjusted for income, education and race",
         "data": "CHS microdata (public-use file) if it records commute mode", "design": "survey-weighted regression", "priority": "high"},
        {"question": "The graph has no concept for cycling or active commuting; add them, and code the sign of activity vs inactivity exposures consistently.",
         "data": "System graph", "design": "graph curation", "priority": "medium"},
    ],
    "figures": ["figures/mobility/active_commute_obesity_uhf42.png"],
    "notes": (f"Walking dominates the measure (r = {c['corr']['active']['walk']:.3f} with the combined share). Poverty and active "
              f"commuting are almost uncorrelated across UHFs (r = {c['corr']['active']['poverty']:.2f}), so adjusting for poverty "
              "changes little; poverty is not the confounder that matters here. Each extra percentage point of cycling alone goes "
              f"with {h(c['bike_only_poverty'])} points of obesity, an implausible causal size. This is best read as a bridge "
              "that is confirmed in sign at the neighbourhood level and unsettled as a causal link."),
}

if __name__ == "__main__":
    print(claims.outcome(speed))
    print(claims.outcome(commute))
