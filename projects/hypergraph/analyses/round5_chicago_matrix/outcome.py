"""Write the outcome of transfer-chicago-concordance-matrix from results.json and the rule 9 check runs."""
import glob
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from concord import claims  # noqa: E402

OUT = ROOT / "data" / "derived" / "round5" / "chicago_matrix"
R = json.loads((OUT / "results.json").read_text())
AIR = "air, traffic or noise with anything"
c, n, m = R["chicago"], R["new_york_all_pairs"], R["new_york_same_pairs"]
a, am, al = c["groups"][AIR], m["groups"][AIR], c["groups"]["all"]
eo, eom = c["groups"]["exposure with outcome"], m["groups"]["exposure with outcome"]
checks = []
for f in sorted(glob.glob(str(OUT / "results_check_*.json"))):
    k = json.loads(Path(f).read_text())
    checks.append({"file": Path(f).name, "draws": k["draws"], "seed": k["seed"], "air_ci95": [round(x, 3) for x in k["chicago"]["groups"][AIR]["agreement_ci95"]],
                   "verdict": k["prediction_a"]["verdict"], "pm25_poverty_ci95": [round(x, 3) for x in k["chicago"]["pm25_poverty"]["ci95"]]})
assert len(checks) == 6 and all(k["verdict"] == R["prediction_a"]["verdict"] for k in checks), checks
pc, pn = c["pm25_poverty"], n["pm25_poverty"]
d = R["air_share_difference_same_pairs"]
pct = lambda x: f"{100 * x:.1f}%"  # noqa: E731
kinds = {k: f"{v['agree']} of {v['n']}" for k, v in c["groups"].items()}
kinds_ny = {k: f"{v['agree']} of {v['n']}" for k, v in m["groups"].items()}
rec = {
    "id": "transfer-chicago-concordance-matrix",
    "verdict": R["prediction_a"]["verdict"],
    "city_effect": {"label": (f"Share of the {a['n']} qualifying pairs of PM2.5, ozone or traffic with a health outcome whose poverty-partialled Spearman "
                              "correlation across 77 Chicago community areas has the literature's sign (interval: bootstrap of areas); the null is "
                              "New York's 10 of 27"),
                    "estimate": round(a["agreement"], 3), "lo": round(a["agreement_ci95"][0], 3), "hi": round(a["agreement_ci95"][1], 3),
                    "scale": "proportion of pairs", "null": round(10 / 27, 3), "n": a["n"]},
    "graph_effect": {"label": "Literature sign: majority sign of signed API findings per pair, at least 3 studies and 80% consistency; all 15 air and traffic pairs positive",
                     "estimate": None, "lo": None, "hi": None, "scale": "sign", "null": 0},
    "graph_evidence": [{"relationship_id": "the relationships of graph-concordance-matrix, reused", "n_findings": 8792,
                        "summary": "data/derived/graph/concordance/literature_signs.csv and graph_findings.csv; no new graph request"}],
    "sources": json.loads((OUT / "chicago_sources.json").read_text()) + [
        {"kind": "sysgraph-api", "api_version": "v1.0", "fetched": "2026-11-12", "uncached_requests": 0,
         "note": "literature signs reused from graph-concordance-matrix"},
        {"kind": "project", "file": "data/derived/graph/concordance/city_indicators_uhf42.csv", "note": "New York indicators, as fetched for graph-concordance-matrix"}],
    "prediction_scored": (
        f"(a) hit: predicted 60% (40 to 80); observed {a['agree']} of {a['n']}, {pct(a['agreement'])} ({pct(a['agreement_ci95'][0])} to "
        f"{pct(a['agreement_ci95'][1])}). The support condition is met: {a['n']} pairs (at least 12), share at least 60%, lower bootstrap limit "
        f"{pct(a['agreement_ci95'][0])} above New York's 37.0%, and above New York's {am['agree']} of {am['n']} on the same pairs "
        f"(difference {100 * d['chicago_minus_new_york']:.0f} points, {100 * d['ci95'][0]:.0f} to {100 * d['ci95'][1]:.0f}). The condition holds with 20,000 "
        "draws and under five other seeds (rule 9). "
        f"(b) hit: predicted +0.35 (0.10 to 0.60); the Spearman correlation of PM2.5 with poverty is {pc['spearman']:+.2f} ({pc['ci95'][0]:+.2f} to "
        f"{pc['ci95'][1]:+.2f}) in Chicago and {pn['spearman']:+.2f} ({pn['ci95'][0]:+.2f} to {pn['ci95'][1]:+.2f}) in New York. The lower limit is close to "
        "zero (0.03 to 0.05 across seeds). "
        f"(c) within range: overall agreement {al['agree']} of {al['n']}, {pct(al['agreement'])} ({pct(al['agreement_ci95'][0])} to "
        f"{pct(al['agreement_ci95'][1])}), predicted 68% (58 to 78); margin over always-positive {100 * al['margin_over_always_positive']:.1f} points "
        f"({100 * al['margin_ci95'][0]:.1f} to {100 * al['margin_ci95'][1]:.1f}), predicted between -3 and +5."),
    "settle": ("The comparison rests on three exposures measured differently in the two cities, and in Chicago PM2.5 ranges only from 8.6 to 9.3 "
               "micrograms per cubic metre and ozone from 66.7 to 69.4 ppb on a regional model surface. A street-level pollution survey of Chicago "
               "comparable to NYCCAS, NO2 and noise by community area, and a third and fourth city would show whether agreement follows "
               "the sign of the pollution-poverty correlation. Within one city, individual records with pollution at the address would remove sorting directly."),
    "research_needed": [
        {"question": "Does agreement of air pollution pairs with the literature's sign rise with the correlation between pollution and deprivation across cities?",
         "data": "EJSCREEN and CDC PLACES by tract for many US cities, one measurement method throughout", "design": "the same matrix in 20 or more cities, agreement regressed on the pollution-poverty correlation", "priority": "high"},
        {"question": "Do NO2 and street-level PM2.5 in Chicago rank community areas as the EJSCREEN surface does?",
         "data": "Chicago sensor networks (Array of Things successors, Microsoft Eclipse 2021), aggregated to community areas", "design": "rank comparison, then rerun of the fifteen pairs", "priority": "medium"},
    ],
    "figures": ["figures/round5/chicago_matrix_by_kind.png"],
    "notes": (
        f"Thirty-three of the 37 registered Chicago indicators had a period with 70 of 77 areas; serious psychological distress, traffic deaths, hearing "
        f"difficulty and vision difficulty did not and were dropped under the registered rule. {c['n_qualifying']} pairs qualify ({c['n_literature_positive']} "
        f"with a positive literature sign), and the same {R['n_pairs_in_both']} are computable in New York. Agreement by kind in Chicago (deciding): {kinds}. "
        f"New York on the same pairs: {kinds_ny}. Exposure with outcome: Chicago {eo['agree']} of {eo['n']} ({pct(eo['agreement_ci95'][0])} to "
        f"{pct(eo['agreement_ci95'][1])}), margin over always-positive {100 * eo['margin_over_always_positive']:.1f} points; New York {eom['agree']} of {eom['n']}. "
        f"Area-shuffle null 95% range {pct(c['perm_null_area_shuffle']['q025'])} to {pct(c['perm_null_area_shuffle']['q975'])}; sign-shuffle null "
        f"p = {c['perm_null_sign_shuffle']['p_ge_obs']:.3f} (New York 0.14). The margin over always-positive comes from three pairs with a negative literature "
        "sign (exercise with diabetes, walking difficulty and cognitive difficulty), all of which agree in Chicago. "
        "Limits. Within the fifteen air and traffic pairs every literature sign is positive, so agreement equals the always-positive rate and the result "
        "is a difference between cities, not evidence that the graph's signs beat that rule. Three of the twelve agreeing pairs have a correlation "
        "below 0.1 in size (asthma with PM2.5 0.07, asthma with traffic 0.01, low birthweight with traffic 0.01); among pairs with a deciding "
        "correlation of at least 0.2 in size Chicago agrees in 6 of 6 and New York in 4 of 11 (exploratory). PM2.5 pairs changed from 0 of 6 to 5 of 6, "
        "ozone from 5 of 5 to 4 of 5, traffic from 1 of 4 to 3 of 4. Chicago's PM2.5 is highest in low-density areas (Spearman with density -0.53) and "
        "New York's in the dense core, so the cities differ in more than the pollution-poverty correlation, which is +0.29 against +0.11 with "
        "overlapping intervals. Two health outcomes agree less often in Chicago (18 of 27 against 22 of 27) because the CDC PLACES depression estimate "
        "is negatively correlated with most adverse outcomes; depression is in 11 of Chicago's 20 disagreeing pairs. Heat deaths are zero in most areas. "
        f"Rule 9 check runs: {checks}. No new graph request was made."),
}
print(claims.outcome(rec))
