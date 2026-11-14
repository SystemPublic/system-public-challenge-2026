"""Write the outcomes of the two registered tests from absence_test.json."""
import json, math, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from concord import claims
OUT = ROOT / "data" / "derived" / "graph" / "triads"
res = json.loads((OUT / "absence_test.json").read_text())
for arm in ("hot", "cold"):
    cid = f"graph-triad-{arm}-asthma-absence"
    reg = json.loads((ROOT / "claims" / "registered" / f"{cid}.json").read_text())
    lo_c, med_c, hi_c = reg["composition"]["composed_ratio_lo_median_hi"]
    p = res[arm]["primary"]
    up, down = p["lo"] > 1, p["hi"] < 1
    verdict = "confirmed" if up else "contested" if down else "unsettled"
    share = math.log(med_c) / p["log"] if up else None
    sec = {k: {x: round(v[x], 4) for x in ("ratio", "lo", "hi")} | {"n": v["n"]} for k, v in res[arm].items() if isinstance(v, dict) and k != "primary"}
    if arm == "cold":
        scored = (f"partial. The direction composed from the triad is supported: the ratio is {p['ratio']:.3f} ({p['lo']:.3f} to {p['hi']:.3f}). The size is not the chain's: the interval lies wholly above the composed interval "
                  f"({lo_c:.4f} to {hi_c:.4f}), and above the registrant's expected range of 1.00 to 1.08 at the point estimate. The asthma path accounts for about {100*share:.0f}% of the log ratio "
                  f"({100*math.log(lo_c)/p['log']:.0f}% to {100*math.log(hi_c)/p['log']:.0f}% over the composed interval).")
        settle = "Absence by reason (illness against other), or absence among pupils with and without asthma, on cold days; daily asthma emergency visits of school-age children as the middle term; an influenza control (weekly influenza-like illness)."
    else:
        scored = (f"partial. The ratio is {p['ratio']:.3f} ({p['lo']:.3f} to {p['hi']:.3f}), inside the registrant's expected range and containing the composed interval ({lo_c:.4f} to {hi_c:.4f}), but the interval includes 1, as the discrimination check said it would.")
        settle = "More exposed days (the 2021-22 and later files are not on the portal by school day), school-level data with air-conditioning status, or absence by reason. An endpoint with a standard error near 0.001 would be needed to test the composed size."
    rec = {
     "id": cid, "verdict": verdict,
     "city_effect": {"label": f"citywide absence rate on {arm} school days against other school days of the same week of the year", "estimate": p["ratio"], "lo": p["lo"], "hi": p["hi"],
                     "scale": "ratio of absence rates", "null": 1, "n": p["n"], "n_exposed": p["n_exposed"]},
     "graph_effect": {"label": "composed through asthma: RR(asthma exacerbation) ^ share of absences attributable to asthma", "estimate": med_c, "lo": lo_c, "hi": hi_c, "scale": "ratio of absence rates", "null": 1},
     "graph_evidence": reg["graph_evidence"],
     "sources": res["sources"] + [{"kind": "sysgraph", "api": "v1.0", "relationships": [r for e in reg["graph_evidence"] for r in (e["relationship_id"] or [])], "fetched": "2026-11-12",
                                   "note": "API responses carry no version; findings read through data/cache/sysgraph"}],
     "prediction_scored": scored, "settle": settle,
     "mediated_share": share,
     "research_needed": [{"question": f"How much of the {arm}-day rise in school absence passes through asthma?", "data": "DOE absence by reason or by pupil health status; DOHMH syndromic asthma visits ages 5-17 by day",
                          "design": "mediation analysis by day with asthma visits as the middle term", "priority": "medium"}],
     "figures": ["figures/graph/triads_network.png"],
     "notes": (f"Model as registered; {res['counts']['school_days_kept']} school days from {res['span'][0]} to {res['span'][1]} after excluding {res['counts']['excluded_low_enrolment']} days with low citywide enrolment "
               f"(mostly Regents examination weeks in late January and June) and {res['counts']['excluded_rate_above_30pct']} days with absence above 30%. Mean absence rate {100*res['mean_absence_rate']:.1f}%. "
               f"Secondary estimates, none deciding: {json.dumps(sec)}. Influenza is not controlled, and in the cold arm it is the main rival. The test was registered knowing it could not detect the composed size (D below 4)."),
    }
    print(claims.outcome(rec), verdict, round(p["ratio"], 4), share)
