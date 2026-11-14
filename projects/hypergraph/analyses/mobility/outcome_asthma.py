"""Outcome for mob-asthma-pollution."""
import json

from concord import claims
from analyses.mobility.common import DER

R = json.loads((DER / "asthma_pollution_results.json").read_text())
r = R["results"]
u, a, ab = r["child_no2_unadj"], r["child_no2_poverty"], r["child_no2_poverty_boro"]
pm = r["child_pm25_poverty"]
pov = r["child_poverty_only"]
kh = r["research"]["no2_per_10ppb_khreis"]
f = lambda x: f"{x['rr']:.2f} ({x['lo']:.2f}-{x['hi']:.2f})"

rec = {
    "id": "mob-asthma-pollution",
    "verdict": "unsettled",
    "city_effect": {"label": "Asthma ED visits age 5-17 per 10 ppb NO2, poverty-adjusted, 42 UHF neighbourhoods, 2017-19",
                    "estimate": round(a["rr"], 3), "lo": round(a["lo"], 3), "hi": round(a["hi"], 3),
                    "scale": "rate ratio per 10 ppb NO2", "null": 1, "n": a["n"]},
    "graph_effect": {"label": "Khreis et al. 2017 pooled asthma incidence, NO2 1.05 per 4 ug/m3, converted to 10 ppb",
                     "estimate": round(kh, 3), "lo": round(1.02 ** (18.8 / 4), 3), "hi": round(1.07 ** (18.8 / 4), 3),
                     "scale": "rate ratio per 10 ppb NO2", "null": 1},
    "sources": R["sources"] + [{"kind": "sysgraph", "file": "data/derived/mobility/graph_evidence.json",
                                "relationships": ["DC_F0GO0WQ|EAshH_Ko3h", "gX6h_gZWHH|EAshH_Ko3h", "P6IzhScRdx|EAshH_Ko3h"]}],
    "prediction_scored": (f"miss on the mechanism, unsettled on the test. I predicted a strong unadjusted association (1.3-3 per "
                          f"10 ppb) carried by poverty, which would shrink by more than half on adjustment. The unadjusted "
                          f"estimate is {f(u)}, imprecise, and adjustment moved it only to {f(a)}, because NO2 and poverty are "
                          f"almost uncorrelated across UHF neighbourhoods (r = {r['corr']['no2']['poverty']:.2f}). Poverty alone "
                          f"gives {f(pov)} per 10 percentage points and explains {100 * pov['r2']:.0f}% of the variance in log "
                          f"rates; NO2 alone explains {100 * u['r2']:.0f}%."),
    "settle": ("A neighbourhood cross-section with 42 units cannot detect an effect of the size the research reports "
               f"(about {kh:.2f} per 10 ppb), because poverty-linked variation in asthma ED use is far larger. A within-"
               "neighbourhood design would settle it: daily or weekly asthma ED counts by UHF (SPARCS or DOHMH syndromic "
               "surveillance) against daily NYCCAS or AQS concentrations, in a case-crossover or time-series model, so that "
               "each neighbourhood is its own control. A cohort with address-level NO2 (as in the NYC birth cohort studies) "
               "would test the long-term link."),
    "research_needed": [
        {"question": "Does the short-term NO2/PM2.5 to asthma ED association in NYC match the pooled estimates (Zheng 2015)?",
         "data": "SPARCS daily ED visits by ZIP or UHF; NYCCAS/AQS daily concentrations", "design": "time-stratified case-crossover", "priority": "high"},
        {"question": "Why are pollution and poverty uncorrelated across UHF42 while asthma follows poverty so closely?",
         "data": "NYCCAS 300 m surfaces, ACS, housing code violations (HPD), pest complaints", "design": "finer geography (NTA or census tract) with housing covariates", "priority": "medium"},
        {"question": "Graph curation: many associations mix short-term and long-term designs and increments; a standardised effect per unit would make city comparison possible.",
         "data": "System graph associations for NO2/particulates -> asthma", "design": "extract exposure increment and design type", "priority": "medium"},
    ],
    "figures": ["figures/mobility/asthma_pollution_uhf42.png"],
    "notes": (f"With borough fixed effects the NO2 ratio is {f(ab)}. PM2.5 adjusted for poverty: {f(pm)} per 1 ug/m3 "
              f"(research, Khreis 2017: 1.03 per 1 ug/m3). For adults (age-adjusted ED rate) the NO2 ratio adjusted for "
              f"poverty is {f(r['adult_no2_poverty'])}. NO2 and PM2.5 are correlated at r = {r['corr']['no2']['pm25']:.2f} "
              "across UHFs, so the two-pollutant model cannot separate them. The highest NO2 and PM2.5 are in midtown and "
              "lower Manhattan (UHF 306-310), where child asthma ED rates are low; the highest rates are in the South Bronx "
              "and East and Central Harlem (UHF 105-107, 302-303), where pollution is middling and poverty is high. The "
              "research slope drawn through the city mean is almost the same as the NYC unadjusted fit; the city data are "
              "consistent with the research but cannot confirm it. The EHDP 'asthma ED visits due to PM2.5' indicator was not "
              "used because it is computed from research concentration-response functions."),
}
print(claims.outcome(rec))
