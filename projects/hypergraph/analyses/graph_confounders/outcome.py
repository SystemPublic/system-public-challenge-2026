#!/usr/bin/env python
"""Write the outcome of graph-confounders-commute-obesity from the re-analysis results."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from concord import claims  # noqa: E402

R = json.loads((ROOT / "data/derived/graph/confounders/commute_obesity_reanalysis.json").read_text())
M = R["models"]
p, f, w, a = M["graph set (primary)"], M["graph set + park + unemployment"], M["graph set without walkability"], M["analyst: poverty"]
fmt = lambda v: f"{v['slope']:+.2f} ({v['lo']:+.2f} to {v['hi']:+.2f})"
REC = {
    "id": "graph-confounders-commute-obesity",
    "verdict": "unsettled",
    "city_effect": {"label": "Adult obesity per 10 points of walk-or-bike commute share, 42 UHF neighbourhoods, adjusted for the graph-derived set (poverty, high-school graduation, percent Black, Hispanic and Asian, walkability, perceived safety), OLS, HC3",
                    "estimate": round(p["slope"], 2), "lo": round(p["lo"], 2), "hi": round(p["hi"], 2),
                    "scale": "percentage points of obesity per 10 points of active commuting", "null": 0, "n": p["n"]},
    "graph_effect": {"label": "Size implied by individual-level research (Flint et al. 2014, about 1 kg/m2 lower BMI in active commuters): below 1 point per 10 points",
                     "estimate": None, "lo": -1.0, "hi": 0.0, "scale": "percentage points of obesity per 10 points", "null": 0},
    "sources": R["sources"] + [{"kind": "sysgraph", "api": "v1.0", "note": "shared neighbours and findings read through the API on 12 November 2026; responses cached in data/cache/sysgraph; the API carries no version identifier", "files": ["data/derived/graph/confounders/shared_active-travel__obesity.json", "data/derived/graph/confounders/links_active-travel__obesity.json"]}],
    "prediction_scored": f"miss. The registered range was -4.0 to -1.0. The primary estimate is {fmt(p)}, an attenuation of {100 * p['attenuation_vs_original']:.0f}% from the poverty-adjusted {a['slope']:+.2f}, short of the one third required, and the interval's half-width is {p['half_width']:.2f}, above the 3.0 limit. Neither support_if nor refute_if is met.",
    "settle": "Area data with 42 units cannot separate walking to work from walkability: the graph-derived covariates explain 80% of the variance of the exposure (variance inflation 5.1). Individual records with commute mode, weight, education, race and neighbourhood (Community Health Survey microdata), or a change design around new bike lanes or Citi Bike stations, would settle the size.",
    "research_needed": [
        {"question": "How large is the association between active commuting and obesity among New York adults after individual education, race and ethnicity, age and neighbourhood walkability?", "data": "NYC Community Health Survey microdata with commute mode (2010-2019 waves that asked it), linked to UHF walkability", "design": "individual-level regression with neighbourhood random effects, mediator (leisure activity) left out", "priority": "high"},
        {"question": "Does the graph's list of shared neighbours, read for role, choose better adjustment sets than an analyst across many pairs?", "data": "System Public Graph and any set of pairs with a known causal estimate", "design": "compare attenuation toward the known estimate under graph-derived and analyst-chosen sets", "priority": "medium"},
    ],
    "figures": ["figures/graph/confounders_commute_obesity.png"],
    "notes": f"All 42 UHFs had every covariate. Secondary results, none deciding: with park access and unemployment added the slope is {fmt(f)}, inside the registered support range; without walkability it is {fmt(w)}; poverty with race and ethnicity alone gives {fmt(M['poverty + race/ethnicity'])}; poverty with education alone {fmt(M['poverty + hs_grad'])}; poverty with perceived safety {fmt(M['poverty + safety'])}. Race and ethnicity move the estimate most among the graph-named variables; education, which the graph ranks highest among them, moves it away from zero. Adding the graph's top-ranked shared concept, physical activity (recent exercise), which is a mediator, gives {fmt(M['graph set + mediator (recent exercise): over-adjusted'])}; an analyst who took the graph's ranked list without reading roles would have reported that figure. Every adjusted estimate remains several times the size individual studies imply. Age structure and sex, which the graph also names, were not available at UHF42 and were left out as registered.",
}
if __name__ == "__main__":
    print(claims.outcome(REC))
