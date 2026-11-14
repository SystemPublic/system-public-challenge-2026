"""Join name-level relevance labels onto candidates and rebuild the curated outputs.
Inputs : data/candidates.csv (all keyword+concept matches), data/name_labels.csv (keep/context/drop per unique name)
Outputs: data/evidence.csv (keep + context rows, with label), data/coverage.csv, data/gap_grid.csv, data/qa_summary.md
"""
import pandas as pd

ev = pd.read_csv("data/candidates.csv")
lab = pd.read_csv("data/name_labels.csv", keep_default_na=False)
ev["name_key"] = ev.matched_variable.astype(str).str.lower().str.strip()
ev = ev.merge(lab[["group", "role", "match_method", "name_key", "label", "role_override", "group_override"]],
              on=["group", "role", "match_method", "name_key"], how="left")
ev["role"] = ev.role_override.where(ev.role_override.astype(str) != "", ev.role)
ev["group"] = ev.group_override.where(ev.group_override.astype(str) != "", ev.group)
ev = ev.drop(columns=["role_override", "group_override"]).drop_duplicates(["group", "association_id"])

cur = ev[ev.label.isin(["keep", "context"])].copy()
cur["relevance"] = cur.pop("label")
cur.to_csv("data/evidence.csv", index=False)

k = cur[cur.relevance == "keep"]
health = k[~k.outcome_group.isin(["Other", "Indoor exposure measured"])]
def nuniq_if(df, flag):
    return df[df[flag]].groupby(["group", "role"]).study_id.nunique()
cov = (k.groupby(["group", "role"]).agg(findings=("association_id", "count"), studies=("study_id", "nunique"))
       .join(health.groupby(["group", "role"]).study_id.nunique().rename("health_linked_studies"))
       .join(nuniq_if(k, "is_trial").rename("trial_studies"))
       .join(nuniq_if(k, "is_uk").rename("uk_studies"))
       .fillna(0).astype(int).reset_index())
# make sure every group x role appears, so gaps show as explicit zeros
groups = sorted(ev.group.unique())
full = pd.MultiIndex.from_product([groups, ["exposure", "intervention"]], names=["group", "role"]).to_frame(index=False)
cov = full.merge(cov, how="left").fillna(0)
cov[cov.columns[2:]] = cov[cov.columns[2:]].astype(int)
cov.to_csv("data/coverage.csv", index=False)

grid = k.groupby(["group", "role", "outcome_group"]).study_id.nunique().rename("studies").reset_index()
grid.to_csv("data/gap_grid.csv", index=False)

# QA: how much did each search route contribute, and how precise was it
q = lab.groupby("match_method").label.value_counts().unstack(fill_value=0)
q["precision_keep"] = (q["keep"] / q.sum(axis=1)).round(2)
rows = ev.groupby("match_method").label.value_counts().unstack(fill_value=0)
with open("data/qa_summary.md", "w") as f:
    f.write("# Filter QA\n\nEvery unique matched variable name (n=%d) was labelled keep / context / drop by reading it with its paired variable.\n\n" % len(lab))
    f.write("## By unique name\n\n" + q.to_markdown() + "\n\n## By finding (row)\n\n" + rows.to_markdown() + "\n")
print(q.to_string()); print(); print(rows.to_string()); print()
print(cov.to_string(index=False))
print("\nevidence.csv rows:", len(cur), "| keep:", len(k), "| context:", (cur.relevance == "context").sum())
