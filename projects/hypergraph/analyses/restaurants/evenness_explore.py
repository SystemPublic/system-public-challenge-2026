"""Exploratory checks around restaurants-nta-harshness (decide nothing): the same permutation
statistic with fewer adjustments (none; restaurant count only), and on all cycle inspections
(initial and re-inspection). Writes evenness_explore.json."""
import json
import numpy as np
import evenness_test as e
import common as c

R, I = e.load_snapshot()
Rn = e.assign_nta(R)
counts = Rn.groupby("nta2020").size()
Rn = Rn[Rn.nta2020.isin(counts[counts >= e.MIN_REST].index)].copy()
Rn["log_nta_rest"] = np.log(Rn.nta2020.map(counts))
Rn["cuis"] = c.cuisine_group(Rn.cuisine)
out = {}
ci = I[I.itype == "Cycle Inspection / Initial Inspection"].merge(Rn, on="camis")
for name, cols, cat in (("none", [], []), ("restaurant_count", ["log_nta_rest"], []), ("cuisine_only", ["cuis"], ["cuis"])):
    X = e.design(ci, cols, cat) if cols else e.sm.add_constant(np.zeros((len(ci), 0)), has_constant="add")
    r, _ = e.permutation(ci, "n_crit", X)
    out[f"initial_{name}"] = {k: r[k] for k in ("S_ratio", "p")}
cy = I[I.itype.str.startswith("Cycle Inspection")].merge(Rn, on="camis")
cy["stage"] = cy.itype.str.split(" / ").str[1]
r, _ = e.permutation(cy, "n_crit", e.design(cy, ["stage", "cuis", "log_nta_rest"], ["stage", "cuis"]))
out["all_cycle_stage_cuisine"] = {k: r[k] for k in ("S_ratio", "p")}
t = __import__("pandas").read_csv(c.DER / "evenness_nta.csv")
out["raw_range_crit_per_initial"] = [float(t.crit_per_initial_raw.min()), float(t.crit_per_initial_raw.max())]
out["adj_rr_range"] = [float(t.harsh_rr_adj.min()), float(t.harsh_rr_adj.max())]
out["freq_rr_range"] = [float(t.freq_rr_adj.min()), float(t.freq_rr_adj.max())]
out["freq_raw_range"] = [float(t.freq_ci_per_rest_year_raw.min()), float(t.freq_ci_per_rest_year_raw.max())]
c.write_json("evenness_explore.json", out)
print(json.dumps(out, indent=1))
