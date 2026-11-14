#!/usr/bin/env python
"""Write the outcomes of the two heat re-analyses from results.json."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from concord import claims  # noqa: E402

R = json.loads((ROOT / "data/derived/round2/heat_confounders/results.json").read_text())
FIG = ["figures/round2/heat_confounders.png"]
SG = {"kind": "sysgraph", "api": "System Public Graph v1.0", "dataset": "Dataverse v2.1, doi:10.7910/DVN/7V6JDO (API only)",
      "file": "data/derived/graph/confounders/links_green__temperature.json, links_temperature__heat-illness.json"}
HEAT = {"kind": "derived", "file": "data/derived/heat/bridge_cd.csv, bridge_nta.csv", "note": "outcome, exposure and original covariates; sources listed in the outcomes of heat-trees-surftemp and heat-surftemp-ed"}


def f(e, d=2):
    return f"{e['estimate']:+.{d}f} ({e['lo']:+.{d}f} to {e['hi']:+.{d}f})"


a = R["A_cd"]
p = a["primary"]
claims.outcome({
    "id": "graph-confounders-trees-surftemp",
    "verdict": "unsettled",
    "city_effect": {"label": "Change in the slope of surface temperature on z(log street trees per km2) when log population density, building footprint share and road share are added to poverty and percent Black; community districts; paired bootstrap interval",
                    "estimate": p["change"]["estimate"], "lo": p["change"]["lo"], "hi": p["change"]["hi"], "scale": "F per SD", "null": 0, "n": p["n"]},
    "graph_effect": {"label": "Change implied by the graph's population density and surface temperature correlation of 0.8, for a tree-density and population-density correlation of 0.3 to 0.6",
                     "estimate": -0.75, "lo": -1.1, "hi": -0.4, "scale": "F per SD", "null": 0},
    "sources": R["sources"] + [HEAT, SG],
    "prediction_scored": f"partial: the change is {f(p['change'])} F per SD, inside the predicted band of -0.3 to -1.2, and the slope under the graph set is {f(p['graph_set'])}, inside -0.7 to +0.2. Support condition (a) is met and (c) is met (largest VIF {p['max_vif']:.2f}); (b) is not, because the bootstrap interval of the change includes zero. The route was not the one derived from the graph: population density has a correlation of {R['cd_corr']['surftemp_f']['log_popdens']:+.2f} with surface temperature across districts, not 0.8, and adding it alone moves the slope up by {f(a['popdens_only']['change'])}. Road share alone accounts for the fall ({f(a['road_only']['change'])}).",
    "settle": "The fall in the slope comes from road share, which also turns the exposure into trees per unit of street. A tree measure that does not scale with street area (canopy share from LiDAR or NAIP by district, or street trees per km of kerb) with the same covariates would separate removed confounding from a changed exposure. With vegetative cover as the exposure the graph set gives " + f(a["vegcover_exposure"]["graph_set"]) + " F per SD.",
    "research_needed": [{"question": "Does street-tree canopy lower district surface temperature when street area, building footprint and density are held fixed?",
                         "data": "NYC LiDAR land cover 2017, Landsat or ECOSTRESS scenes over several summers, PLUTO of the same year",
                         "design": "Tract-level regression with canopy share as the exposure and built form of the same year as covariates", "priority": "medium"}],
    "figures": FIG,
    "notes": f"n = {p['n']} districts. Original refitted on the same rows: {f(p['original'])}. Graph set: {f(p['graph_set'])}. VIFs: " + ", ".join(f"{k} {v:.2f}" for k, v in p["vif"].items()) + f". Coefficients in the graph-set model: log population density {p['covariate_coefs']['log_popdens']['b']:+.2f} F per log unit (SE {p['covariate_coefs']['log_popdens']['se']:.2f}), footprint share {p['covariate_coefs']['built_share']['b']:+.3f} F per point (SE {p['covariate_coefs']['built_share']['se']:.3f}), road share {p['covariate_coefs']['road_share']['b']:+.3f} F per point (SE {p['covariate_coefs']['road_share']['se']:.3f}). Secondary models, not deciding (slope, then change): population density alone {f(a['popdens_only']['graph_set'])}, {f(a['popdens_only']['change'])}; footprint share alone {f(a['built_only']['graph_set'])}, {f(a['built_only']['change'])}; road share alone {f(a['road_only']['graph_set'])}, {f(a['road_only']['change'])}; floor area in place of footprint {f(a['far_in_place_of_built']['graph_set'])} with largest VIF {a['far_in_place_of_built']['max_vif']:.1f}; traffic density in place of road share {f(a['traffic_in_place_of_road']['graph_set'])}. At NTA2010 (n = {R['A_nta']['primary']['n']}, 189 distinct NTAs; the five that span two districts appear twice, as in the original) the graph set moves the slope the other way: {f(R['A_nta']['primary']['original'])} to {f(R['A_nta']['primary']['graph_set'])}, change {f(R['A_nta']['primary']['change'])}, largest VIF {R['A_nta']['primary']['max_vif']:.2f}; road share alone changes it by {f(R['A_nta']['road_only']['change'])}. District 414 has a computed road share below zero (waterfront lots extend past the shoreline used for land area). PLUTO is version 26v2, eight years after the Landsat scene. Two lines of the script were changed after registration to drop lots with no district code and duplicate NTA rows; the models are as registered.",
})

b = R["B_cd"]
p = b["primary"]
c = p["covariate_coefs"]["alone65"]
claims.outcome({
    "id": "graph-confounders-surftemp-ed",
    "verdict": "unsettled",
    "city_effect": {"label": "Change in the percent change of the heat-stress ED rate per 1 F of surface temperature when the share of older adults living alone is added to poverty, percent Black and AC; community districts; paired bootstrap interval",
                    "estimate": p["change"]["estimate"], "lo": p["change"]["lo"], "hi": p["change"]["hi"], "scale": "percentage points per 1 F", "null": 0, "n": p["n"]},
    "graph_effect": {"label": "Change derived from living-alone odds ratios 8.1 and 42.3 (PMIDs 11988377, 27221967)", "estimate": -0.5, "lo": -2.5, "hi": 0.5,
                     "scale": "percentage points per 1 F", "null": 0},
    "sources": R["sources"] + [HEAT, SG],
    "prediction_scored": f"partial: the change is small, as predicted, {f(p['change'])} points, but its sign is positive and it falls 0.09 outside the registered band of -2.5 to +0.5, so support condition (a) is not met. Conditions (b), (c) and (d) are met: the bootstrap interval lies inside -5.2 to +5.2, the slope under the graph set is {f(p['graph_set'], 1)} with its upper limit below zero, and the largest VIF is {p['max_vif']:.2f}. The refutation condition is not met. The sign was wrong because the share of older adults living alone has a correlation of {R['cd_corr']['surftemp_f']['alone65']:+.2f} with surface temperature, not a positive one.",
    "settle": "Living alone does not account for the negative district association. The three built-form covariates do in a secondary model that does not decide this verdict: with them the slope is " + f(b["built_form_only"]["graph_set"], 1) + "% per F. A registered test of that set on an outcome not yet seen (the yearly heat ED rates by district, or heat hospitalizations) would settle whether heat-surftemp-ed should remain contested.",
    "research_needed": [{"question": "Is the negative district association between surface temperature and heat ED visits produced by street area and built form?",
                         "data": "EHDP heat ED and hospitalization rates by district, PLUTO, Landsat scenes from several summers",
                         "design": "Registered replication with road share, footprint share and density as covariates, on an outcome period not used here", "priority": "high"}],
    "figures": FIG,
    "notes": f"n = {p['n']} districts. Original refitted: {f(p['original'], 1)}% per F. The coefficient of living alone is {c['b']:+.4f} log rate per percentage point (SE {c['se']:.4f}), which as a point estimate lies in the range of 0.003 to 0.008 derived from the graph's odds ratios, with an interval of {c['b'] - 1.96 * c['se']:+.3f} to {c['b'] + 1.96 * c['se']:+.3f} that includes zero. Its partial R2 with surface temperature is {p['partial_r2_exposure_on_extra']:.2f}. Secondary models, not deciding: built-form covariates without living alone {f(b['built_form_only']['graph_set'], 1)}, change {f(b['built_form_only']['change'], 1)}; living alone with built form {f(b['plus_built_form']['graph_set'], 1)}, change {f(b['plus_built_form']['change'], 1)}, in which road share has a coefficient of {b['plus_built_form']['covariate_coefs']['road_share']['b'] * 100:+.1f}% per point (p = {b['plus_built_form']['covariate_coefs']['road_share']['p']:.3f}). At NTA2010, for heat hospitalizations, living alone has a negative coefficient ({R['B_nta_hosp']['primary']['covariate_coefs']['alone65']['b']:+.4f}, SE {R['B_nta_hosp']['primary']['covariate_coefs']['alone65']['se']:.4f}) and the temperature slope moves from {f(R['B_nta_hosp']['primary']['original'], 1)} to {f(R['B_nta_hosp']['primary']['graph_set'], 1)}.",
})
print("outcomes written")
