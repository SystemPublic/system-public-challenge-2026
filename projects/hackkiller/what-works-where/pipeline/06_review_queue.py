"""Build a prioritised human-review queue from the classified graph candidates.

Priority 1  SMC, vaccine and combination effect rows; new-generation nets (PBO / chlorfenapyr / pyriproxyfen)
Priority 2  standard-net effect rows from experimental trials, or with a full CI
Priority 3  observational net-use rows; anything flagged
Priority 4  uptake / behaviour rows (kept for completeness, not effect evidence)

Reviewers fill the blank verify_* columns against the paper (abstract first, full text if needed).
"""
from __future__ import annotations

import json

import pandas as pd

from common import DATA, SITE_DATA, TEAM_PROCESSED

g = pd.DataFrame(json.loads((SITE_DATA / "graph.json").read_text()))


def priority(r) -> int:
    if r["role"] == "uptake / behaviour":
        return 4
    if r["intervention_class"] in ("smc", "vaccines", "combination") or "standard" not in r["intervention_subtype"]:
        return 1 if r["role"] == "effect on outcome" else 3
    if r["role"] == "effect on outcome" and (r["study_type"] == "Experimental Trial" or r["plottable_ratio"]):
        return 2
    return 3


g["review_priority"] = g.apply(priority, axis=1)
g["countries"] = g["countries"].apply(lambda xs: "; ".join(xs or []))
# merge the teammate's queue/candidates (read-only) so there is one queue keyed by system_id
team = pd.DataFrame(json.loads((TEAM_PROCESSED / "system_candidates.json").read_text()))
team_cols = {"candidate_classes": "teammate_candidate_classes", "match_terms": "teammate_match_terms",
             "content_hints": "teammate_content_hints", "country_hints": "teammate_country_hints",
             "flags": "teammate_flags_original", "numeric_check_status": "teammate_numeric_check"}
team = team[["system_id", *team_cols]].rename(columns=team_cols)
for c in team_cols.values():
    team[c] = team[c].apply(lambda v: "; ".join(v) if isinstance(v, list) else v)
g = g.merge(team, on="system_id", how="left")
g["in_teammate_queue"] = g["teammate_candidate_classes"].notna().map({True: "Y", False: "N"})
assert set(team.system_id) <= set(g.system_id), "teammate ids missing from merged queue"

cols = ["review_priority", "in_teammate_queue", "match_rule", "intervention_class", "intervention_subtype", "role", "outcome_tier",
        "pubmed_id", "year", "iso3", "countries", "country_source", "title", "doi", "study_type", "population",
        "system_id", "intervention_text", "outcome_text", "system_statistic_type", "statistic_value",
        "ci_lower", "ci_upper", "ci_level", "p_value", "p_value_equality", "qc_flags", "teammate_flags", "in_verified_set",
        *team_cols.values()]
q = g[cols].sort_values(["review_priority", "intervention_class", "intervention_subtype", "pubmed_id"])
for c in ["verify_intervention", "verify_comparator", "verify_outcome_definition", "verify_effect_measure",
          "verify_estimate", "verify_ci", "verify_followup_months", "verify_country_site", "verify_population",
          "include_in_dashboard (Y/N)", "exclusion_reason", "source_location (e.g. Abstract, Table 2)",
          "reviewer", "review_note"]:
    q[c] = ""
out = DATA / "review" / "review_queue.csv"
out.parent.mkdir(parents=True, exist_ok=True)
q.to_csv(out, index=False)
print(q.groupby(["review_priority", "intervention_class"]).agg(rows=("system_id", "size"),
                                                               papers=("pubmed_id", "nunique")).to_string())
