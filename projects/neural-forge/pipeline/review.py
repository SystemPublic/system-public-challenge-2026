"""Make review/to_check.csv: the findings worth checking by hand, most influential first, in plain English.

    python -m pipeline.review

Open each paper link, find the result, and type ok or wrong in the `decision` column (with a reason if wrong).
Re-running keeps decisions already typed. `python -m pipeline.build` then drops every finding marked wrong.
"""
import csv

import pandas as pd

from . import config as C

OUT = C.PROJECT / "review" / "to_check.csv"
STAT = {"odds_ratio": "odds ratio", "adjusted_odds_ratio": "adjusted odds ratio", "hazard_ratio": "hazard ratio",
        "adjusted_hazard_ratio": "adjusted hazard ratio", "relative_risk_ratio": "relative risk",
        "incident_rate_ratio": "rate ratio", "prevalence_ratio": "prevalence ratio", "pearson_r": "correlation r",
        "spearman_correlation": "Spearman correlation", "coefficient": "regression coefficient",
        "mean_difference_unstandardized": "mean difference", "mean_difference_standardized": "standardized difference",
        "risk_difference": "risk difference"}
# claims whose verdict can move if a few findings are wrong come first
PRIORITY = {"ac-protects": 1, "older-alone-heat-ed": 1, "poverty-heat-ed": 1, "canopy-cools": 2,
            "bridge-no-heat-cold-ed": 2, "hot-districts-asthma": 3, "bridge-trees-heat-ed": 4,
            "hot-summers-hospitalizations": 5, "hot-districts-heat-ed": 5, "trees-cool": 9, "greenery-cools-cd": 9}


def sentence(r):
    a, b = r["name_a"], r["name_b"]
    if r["sign"] == 1:
        meaning = f"MORE \"{a}\" goes with MORE \"{b}\""
    elif r["sign"] == -1:
        meaning = f"MORE \"{a}\" goes with LESS \"{b}\""
    elif r["sign"] == 0:
        meaning = f"no clear link between \"{a}\" and \"{b}\" (not significant)"
    else:
        meaning = "direction unreadable (ignored)"
    ci = f" [{r['ci_lower']:g} to {r['ci_upper']:g}]" if pd.notna(r["ci_lower"]) and pd.notna(r["ci_upper"]) else ""
    p = f", p={r['p_value']:g}" if pd.notna(r["p_value"]) else ""
    stat = STAT.get(r["system_statistic_type"], r["system_statistic_type"])
    return f"{stat} {r['statistic_value']:g}{ci}{p}", f"We read this as: {meaning}."


def main():
    df = pd.read_csv(C.OUT / "review_sheet.csv")
    df = df[df["sign"].isin([1, -1])]  # only findings that vote on a direction can change a verdict
    df["priority"] = df["claim"].map(PRIORITY).fillna(9).astype(int)
    df = df.sort_values(["priority", "claim", "system_id"]).drop_duplicates("system_id")
    df = df[df["priority"] <= 4]
    old = {}
    if OUT.exists():
        with open(OUT) as f:
            old = {r["system_id"]: r for r in csv.DictReader(f)}
    rows = []
    for _, r in df.iterrows():
        stat, meaning = sentence(r)
        prev = old.get(r["system_id"], {})
        rows.append({"decision": prev.get("decision", ""), "reason": prev.get("reason", ""),
                     "priority": r["priority"], "claim": r["claim"], "graph_says": stat, "we_read_it_as": meaning,
                     "variable_a": r["name_a"], "variable_b": r["name_b"],
                     "open_this": r["pubmed"] if isinstance(r["pubmed"], str) and r["pubmed"] else r["paper"],
                     "doi": r["paper"], "study_population": r["population_string"], "system_id": r["system_id"]})
    OUT.parent.mkdir(exist_ok=True)
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    done = sum(1 for r in rows if r["decision"])
    print(f"{len(rows)} findings to check ({done} done) → {OUT}")
    print(pd.DataFrame(rows).groupby(["priority", "claim"]).size().to_string())


if __name__ == "__main__":
    main()
