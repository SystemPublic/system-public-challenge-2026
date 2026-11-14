"""Write the outcomes of the heat claims from the derived results (concord.claims.outcome)."""
from __future__ import annotations

import json

from analyses.heat.common import DER
from concord import claims

R = lambda f: json.loads((DER / f).read_text())  # noqa: E731

GRAPH_SRC = [{"kind": "sysgraph", "api": "System Public Graph v1.0", "dataset": "Dataverse v2.1, doi:10.7910/DVN/7V6JDO",
              "file": "data/derived/heat/graph_evidence.json", "audit": "data/derived/heat/graph_audit_heat.json"}]


def main():
    s, e, ey, b, h = R("shootings_results.json"), R("ed_results.json"), R("ehdp_yearly_results.json"), R("bridge_results.json"), R("hyperlocal_results.json")

    p = s["primary"]
    claims.outcome({
        "id": "heat-shootings",
        "verdict": "confirmed",
        "city_effect": {"label": "NYC shooting incidents per day, Central Park TMAX lag 0, NB GLM with DOW, month, year, holiday, rain",
                        "estimate": p["estimate"], "lo": p["lo"], "hi": p["hi"], "scale": "IRR per 5 C", "null": 1, "n": s["n_days"]},
        "graph_effect": {"label": "Temperature -> homicide, Xu 2020 NYC (abstract value; graph row 0.088 is mis-extracted and absent from the Dataverse CSV)",
                         "estimate": 1.088, "lo": 1.015, "hi": 1.166, "scale": "OR per 5 C daily mean, lag 0-7", "null": 1},
        "sources": s["sources"] + GRAPH_SRC,
        "prediction_scored": "partial: the IRR per 5 C (1.146, 1.130 to 1.163) lies in the registered 1.05-1.20 range, but the spline RR at the 84th percentile "
                             f"({s['curve']['rr_p84']['rr']:.2f}, {s['curve']['rr_p84']['lo']:.2f} to {s['curve']['rr_p84']['hi']:.2f}) exceeds the registered 1.05-1.25, "
                             "and the curve keeps rising to 35 C rather than peaking at the 85th-95th percentile.",
        "settle": "The direction is settled. The size of the hot-day excess in NYC relative to the 100-city pooled estimate (1.42 vs 1.17 at the 84th percentile) "
                  "would be settled by fitting the Lyons et al. distributed-lag model to the NYPD series (same exposure metric and reference), and by "
                  "the NYC row of their eTable 2. Mechanism (time outdoors vs physiology) needs data on street activity, e.g. hourly pedestrian counts or mobility traces by temperature.",
        "research_needed": [
            {"question": "Does the temperature effect on shootings in NYC work through time spent outdoors?", "data": "NYPD shootings by hour and location type (inside/outside), pedestrian counts, cell-phone mobility",
             "design": "Mediation with daily outdoor activity; compare indoor vs outdoor shootings", "priority": "high"},
            {"question": "Is the NYC temperature-shooting slope steeper than the US average, and why?", "data": "Gun Violence Archive and NYPD, 100 cities",
             "design": "Harmonised multi-city DLNM with NYC as a named city", "priority": "medium"},
            {"question": "Do cooling interventions (open pools, cooling centres, summer programmes) reduce hot-day shootings?", "data": "Parks pool openings, SYEP dates, NYPD by precinct",
             "design": "Difference-in-differences across precincts by opening dates", "priority": "high"},
        ],
        "figures": ["figures/heat/heat_shootings_curve.png"],
        "notes": f"{s['n_incidents']} shooting incidents on {s['n_days']} days, 2006-01-01 to 2026-08-31 (5ucz-vwe8, one row per incident). "
                 f"The archived file 833y-fsy8 agrees to within 2 incidents for 2006-2024 ({s['check_vs_historic']}). "
                 "Sensitivity analyses all lie between 1.11 and 1.17 per 5 C (lag 0-1, TMIN, May-September, 2006-2019, 2020-2026, murder incidents). "
                 "The graph has no relationship between gun violence and temperature; its temperature-homicide rows contain two mis-extractions: "
                 "Xu 2020 percent increases stored as odds ratios 0.095 and 0.088 (absent from the Dataverse CSV) and Rahman 2023 percent increases stored as odds ratios 4.9 and 6.2 "
                 "(present in the CSV). The NYC estimate lies between the homicide estimates (1.05-1.10) and the Chicago shootings estimates (1.16-1.19).",
    })

    pe = e["primary"]
    claims.outcome({
        "id": "heat-ed-syndromic",
        "verdict": "confirmed",
        "city_effect": {"label": "NYC syndromic heat ED visits per day, May-Sep 2017-2026, Central Park TMAX lag 0, NB GLM with DOW, month, year, holiday",
                        "estimate": pe["estimate"], "lo": pe["lo"], "hi": pe["hi"], "scale": "IRR per 5 C", "null": 1, "n": e["n_days"]},
        "graph_effect": {"label": "Extreme heat (local 95th percentile vs reference day, 34.4 C vs 14.9 C national average) -> heat-related illness ED visits, Sun 2021 US adults", "estimate": 1.663, "lo": 1.602, "hi": 1.727,
                         "scale": "RR 95th percentile vs reference day", "null": 1},
        "sources": e["sources"] + ey["sources"] + GRAPH_SRC,
        "prediction_scored": f"hit: IRR per 5 C {pe['estimate']:.2f} ({pe['lo']:.2f} to {pe['hi']:.2f}) lies in the registered 1.5-5 range; RR at the 95th percentile "
                             f"({e['curve']['p95_tmax_c']:.1f} C) vs the median ({e['curve']['median_tmax_c']:.1f} C) is {e['curve']['rr_p95']['rr']:.1f}, above 3 as predicted. "
                             f"The registered yearly secondary was weak: Spearman rho of yearly SPARCS heat ED visits with days >= 90 F was {ey['heat_ed_visits']['rho_days_90f']:.2f} "
                             f"(p {ey['heat_ed_visits']['p']:.2f}, {ey['heat_ed_visits']['n']} years); with days >= 95 F (not registered) it was {ey['heat_ed_visits']['rho_days_95f']:.2f}.",
        "settle": "The daily relation is settled. Its size relative to the literature is not comparable as published: the NYC syndromic series counts chief-complaint matches "
                  "and is near zero on mild days, whereas Sun 2021 used claims diagnoses and a contrast of the local 95th percentile against a cooler reference day (not the median, as the registration assumed). A daily SPARCS series of heat-illness ED visits "
                  "by NYC neighbourhood (not public) would settle the size and allow the neighbourhood analysis that the bridge needs.",
        "research_needed": [
            {"question": "What is the daily heat ED exposure-response by neighbourhood in NYC?", "data": "Daily syndromic or SPARCS heat ED visits by ZCTA or UHF (DOHMH, restricted)",
             "design": "Case-crossover by neighbourhood with effect modification by tree canopy and AC", "priority": "high"},
            {"question": "Why did syndromic heat visits rise in 2025-2026 on few 90 F days?", "data": "Syndromic case definition logs, heat warning dates, ED census",
             "design": "Interrupted time series around heat advisories and the 2023 definition change", "priority": "medium"},
        ],
        "figures": ["figures/heat/heat_ed_curve.png"],
        "notes": f"{e['n_visits']} syndromic heat ED visits on {e['n_days']} warm-season days. previous_years.csv (revised 2023 definition) and the older supplement correlate "
                 f"r = {e['check_previous_vs_supp_2017_2020']['corr']:.3f} by day, with {e['check_previous_vs_supp_2017_2020']['sum_previous']} vs "
                 f"{e['check_previous_vs_supp_2017_2020']['sum_supp']} visits in 2017-2020. Piecewise: below 27 C IRR {e['piecewise_27c']['below']['estimate']:.2f} per 5 C; "
                 f"above 27 C a further factor {e['piecewise_27c']['above_extra']['estimate']:.2f}. Heat deaths (EHDP 2074) correlate with days >= 95 F, rho "
                 f"{ey['heat_deaths']['rho_days_95f']:.2f} (1999-2020). No daily heat mortality series is public; no heat or syndromic dataset was found on NYC Open Data.",
    })

    a = b["link_a"]["adjusted"]
    claims.outcome({
        "id": "heat-trees-surftemp",
        "verdict": "unsettled",
        "city_effect": {"label": "Surface temperature (Landsat 17 Jul 2018) on z(log live street trees per km2), CD, adjusted for poverty and percent Black",
                        "estimate": a["estimate"], "lo": a["lo"], "hi": a["hi"], "scale": "F per SD", "null": 0, "n": a["n"]},
        "graph_effect": {"label": "NDVI -> land surface temperature (Hasan 2022, Bangladesh): negative, no value in the abstract; graph r = -1.0 is absent from the Dataverse CSV",
                         "estimate": None, "lo": None, "hi": None, "scale": "direction only", "null": 0},
        "sources": b["sources"] + GRAPH_SRC,
        "prediction_scored": f"miss: the adjusted slope is positive ({a['estimate']:+.2f} F, {a['lo']:+.2f} to {a['hi']:+.2f}), not negative. At NTA level (n=194) it is positive with the interval above 0 "
                             f"({b['nta']['link_a_adjusted']['estimate']:+.2f}, {b['nta']['link_a_adjusted']['lo']:+.2f} to {b['nta']['link_a_adjusted']['hi']:+.2f}). "
                             f"Vegetative cover (grass and trees, EHDP 2143) has the predicted negative slope ({b['link_a']['vegcover_adjusted']['estimate']:+.2f} F per SD, "
                             f"{b['link_a']['vegcover_adjusted']['lo']:+.2f} to {b['link_a']['vegcover_adjusted']['hi']:+.2f}).",
        "settle": "Street-tree density per km2 measures how much of an area is street grid, not how much of it is shaded: dense grids (Manhattan, inner Brooklyn) have many street trees per km2 "
                  "and hot roofs and pavement, while parks, cemeteries and low-rise yards are cool but have few street trees. A canopy measure that includes park and yard trees "
                  "(LiDAR canopy at tract level, or street trees per km of street), with impervious cover and building density as covariates, would settle whether street trees cool surfaces.",
        "research_needed": [
            {"question": "Do street trees lower surface temperature once impervious cover and building height are held fixed?", "data": "NYC 2017 LiDAR land cover (6 in), Landsat/ECOSTRESS LST, street tree census, PLUTO",
             "design": "Block-level regression with street-segment fixed effects", "priority": "high"},
        ],
        "figures": ["figures/heat/heat_bridge_chain.png"],
        "notes": "The registered verdict rule gives 'unsettled' because the CD interval includes zero; the NTA secondary would be 'contested'. Adding borough terms (not registered) makes the CD "
                 f"slope positive with the interval above 0 ({b['link_a']['adjusted_plus_borough']['estimate']:+.2f} F). Four CDs lack HVI covariates (CD aggregation of NTAs) and drop from adjusted models.",
    })

    bb = b["link_b"]["adjusted"]
    claims.outcome({
        "id": "heat-surftemp-ed",
        "verdict": "contested",
        "city_effect": {"label": "Log age-adjusted heat-stress ED rate (EHDP 2443, 5-year) on surface temperature, CD, adjusted for poverty, percent Black, AC",
                        "estimate": bb["estimate"], "lo": bb["lo"], "hi": bb["hi"], "scale": "% per 1 F", "null": 0, "n": bb["n"]},
        "graph_effect": {"label": "No graph finding links area surface temperature to heat ED rates; Madrigano 2015 (literature) links higher surface temperature to heat-wave death in NYC",
                         "estimate": None, "lo": None, "hi": None, "scale": "", "null": 0},
        "sources": b["sources"] + GRAPH_SRC,
        "prediction_scored": f"miss: the adjusted slope is negative ({bb['estimate']:+.1f}% per F, {bb['lo']:+.1f} to {bb['hi']:+.1f}); unadjusted {b['link_b']['unadjusted']['estimate']:+.1f}% "
                             f"({b['link_b']['unadjusted']['lo']:+.1f} to {b['link_b']['unadjusted']['hi']:+.1f}). For heat hospitalizations by NTA (HVI file) the adjusted slope is also negative "
                             f"({b['nta']['link_b_hosp_adjusted']['estimate']:+.1f}%, {b['nta']['link_b_hosp_adjusted']['lo']:+.1f} to {b['nta']['link_b_hosp_adjusted']['hi']:+.1f}).",
        "settle": "The cross-sectional association of one afternoon's surface temperature with five-year ED rates is not a dose-response. Hot-surface districts are central (Manhattan, "
                  "northwest Brooklyn), where residents have lower heat ED rates for reasons the covariates do not capture (age structure is age-adjusted; occupation, housing type, "
                  "ED access and where people spend hot days are not). Individual-level data linking residence, daily exposure at home and ED visits, or daily ED counts by neighbourhood "
                  "analysed as a case-crossover with neighbourhood heat as an effect modifier, would settle it.",
        "research_needed": [
            {"question": "Does neighbourhood surface or air temperature modify the daily heat-ED response?", "data": "Daily heat ED visits by ZCTA (DOHMH), hyperlocal sensors, ECOSTRESS",
             "design": "Case-crossover with interaction by neighbourhood temperature", "priority": "high"},
            {"question": "Which residents in central hot districts avoid heat illness, and how?", "data": "NYCHVS AC, occupation (ACS), cooling centre use",
             "design": "Multilevel model of heat ED by individual and area traits", "priority": "medium"},
        ],
        "figures": ["figures/heat/heat_bridge_chain.png"],
        "notes": f"CDs 101 and 105 have suppressed ED rates; 54 CDs have all covariates. Percent Black is the strongest adjusted predictor of the heat ED rate "
                 f"({b['link_b']['black_in_adjusted_per_10pts']['estimate']:+.1f}% per 10 points, {b['link_b']['black_in_adjusted_per_10pts']['lo']:+.1f} to {b['link_b']['black_in_adjusted_per_10pts']['hi']:+.1f}). "
                 "Covariates are unweighted means of NTA values within each CD.",
    })

    hp = h["primary_trees50"]
    claims.outcome({
        "id": "heat-trees-airtemp-hyperlocal",
        "verdict": "confirmed" if hp["hi"] < 0 else ("contested" if hp["lo"] > 0 else "unsettled"),
        "city_effect": {"label": "Sensor afternoon (12-18h) air temperature on live street trees within 50 m, NTA-by-day fixed effects, install type, SE clustered by sensor",
                        "estimate": hp["estimate"], "lo": hp["lo"], "hi": hp["hi"], "scale": "C per 10 trees", "null": 0, "n": hp["n"]},
        "graph_effect": {"label": "No graph finding on trees and air temperature (tree concept has no relationships)", "estimate": None, "lo": None, "hi": None, "scale": "", "null": 0},
        "sources": h["sources"] + GRAPH_SRC,
        "prediction_scored": HYPER_SCORE(hp, h),
        "settle": "Sensors were placed in a few neighbourhoods (Cool Neighborhoods NYC) on poles and trees, not at random. A sensor network sited by design across tree-density "
                  "strata within blocks, or bicycle-transect air temperature (as in Ziter 2019) through NYC streets, would settle the size of street-level cooling.",
        "research_needed": [
            {"question": "How much do street trees cool air at pedestrian height in NYC?", "data": "Mobile transects with canopy from 2017 LiDAR", "design": "Ziter-style transects across canopy gradients", "priority": "high"},
        ],
        "figures": ["figures/heat/heat_bridge_chain.png"],
        "notes": f"{h['sensors']} sensors, {h['sensor_days']} sensor-days in {h['nta_days']} NTA-days with at least two sensors, {h['ntas']} NTAs, summers 2018-2019. "
                 f"Within 100 m: {h['sens_trees100']['estimate']:+.3f} C per 10 trees ({h['sens_trees100']['lo']:+.3f} to {h['sens_trees100']['hi']:+.3f}). "
                 f"Light-pole sensors read {hp['light_pole_vs_tree_c']:+.2f} C relative to tree-mounted sensors in the same NTA-day.",
    })

    ch = b["chain"]
    claims.outcome({
        "id": "heat-trees-ed-chain",
        "verdict": "contested",
        "city_effect": {"label": "Composed a*b, trees -> surface temperature -> log heat ED rate, CD, bootstrap 5000",
                        "estimate": ch["indirect_pct"], "lo": ch["lo"], "hi": ch["hi"], "scale": "% per SD log street-tree density", "null": 0, "n": ch["n"]},
        "graph_effect": {"label": "No graph path: tree and green space have no relationship to temperature or heat ED; extreme heat -> heat illness ED exists (Sun 2021)",
                         "estimate": None, "lo": None, "hi": None, "scale": "", "null": 0},
        "sources": b["sources"] + h["sources"] + GRAPH_SRC,
        "prediction_scored": f"miss: the registered refute_if is met because link heat-surftemp-ed is contested. The composed estimate is negative ({ch['indirect_pct']:+.1f}%, "
                             f"{ch['lo']:+.1f} to {ch['hi']:+.1f}) only because both links have the wrong sign (a = {ch['a_F_per_sd']:+.2f} F per SD, b = {100*ch['b_log_per_F']:+.1f}% per F). "
                             f"The total association of street-tree density with the heat ED rate is negative ({b['total']['adjusted']['estimate']:+.1f}% per SD, "
                             f"{b['total']['adjusted']['lo']:+.1f} to {b['total']['adjusted']['hi']:+.1f}) but does not pass through surface temperature.",
        "settle": "Income and race drive tree planting history, building form, AC and ED use together, and 54 districts cannot separate them. Three designs would: "
                  "(1) within-neighbourhood variation, e.g. block-level canopy and residence-level heat illness from individual records; "
                  "(2) MillionTreesNYC (2007-2015) planting timing as an instrument, comparing blocks planted early and late (Forestry Tree Points hn5i-inap carries planteddate) "
                  "against later heat ED visits, with the caveat that planting targeted high-HVI areas; "
                  "(3) a daily case-crossover of heat ED visits by ZCTA with canopy as an effect modifier, which compares each area with itself.",
        "research_needed": [
            {"question": "Did MillionTreesNYC plantings reduce local heat illness?", "data": "Forestry Tree Points planteddate (hn5i-inap), DOHMH heat ED by ZCTA, 2007-2025",
             "design": "Staggered difference-in-differences or instrument from planting schedule by block", "priority": "high"},
            {"question": "Does canopy modify the daily heat-ED response within the same neighbourhood?", "data": "Daily heat ED by ZCTA, LiDAR canopy", "design": "Case-crossover with interaction", "priority": "high"},
            {"question": "What does the graph lack?", "data": "Published studies of urban tree canopy and heat morbidity (e.g. Ziter 2019, Madrigano 2015) are not linked in the System graph",
             "design": "Add tree/canopy -> air temperature and green space -> heat illness findings to the graph", "priority": "medium"},
        ],
        "figures": ["figures/heat/heat_bridge_chain.png"],
        "notes": "Confounders the chain cannot separate: household income and poverty, race (percent Black residents is the strongest predictor of heat ED rates here), "
                 "AC ownership, housing age and type, building density and impervious cover, age structure beyond age adjustment, occupation, ED access. "
                 "The HVI is not used as an outcome because it is built from surface temperature and green space. The street-level link (hyperlocal sensors) is reported beside the chain.",
    })


def HYPER_SCORE(hp, h):
    if hp["hi"] < 0:
        lab = "hit" if -0.5 <= hp["estimate"] <= -0.05 else "partial"
    else:
        lab = "miss"
    return (f"{lab}: {hp['estimate']:+.3f} C per 10 trees within 50 m ({hp['lo']:+.3f} to {hp['hi']:+.3f}); registered range -0.05 to -0.5 C.")


if __name__ == "__main__":
    main()
