"""Exploratory summaries after the registered test (not tests): agreement by pair type, sensitivities, gaps."""
import json

import numpy as np
import pandas as pd

import common as C
from indicators import BY_KEY, KEYS

M = pd.read_csv(C.OUT / "matrix_pairs.csv")
t = pd.read_csv(C.OUT / "city_indicators_uhf42.csv", index_col=0)
F = pd.read_csv(C.OUT / "graph_findings.csv")
Q = M[M["qualifies"] == True].copy()  # noqa: E712
Q["agree"] = np.sign(Q["rho_deciding"]) == Q["lit_sign"]
Q["agree_raw"] = np.sign(Q["rho_raw"]) == Q["lit_sign"]
AIR = {"pm25", "no2", "black_carbon", "ozone", "traffic", "noise"}
BEHAV = {"smoking", "binge_drinking", "exercise", "sugary_drinks", "walk_commute", "car_commute"}


def kind(r):
    ra, rb = BY_KEY[r["a"]]["role"], BY_KEY[r["b"]]["role"]
    if {r["a"], r["b"]} & AIR:
        return "air, traffic or noise with anything"
    if ra == rb == "outcome":
        return "health outcome with health outcome"
    if {r["a"], r["b"]} & BEHAV:
        return "behaviour with anything else"
    return "social or housing condition with anything else"


Q["kind"] = Q.apply(kind, axis=1)
out = {"by_kind": {k: {"n": int(len(s)), "agree_deciding": int(s["agree"].sum()), "agree_raw": int(s["agree_raw"].sum())} for k, s in Q.groupby("kind")}}
out["always_positive_benchmark"] = {"raw": float((Q["rho_raw"] > 0).mean()), "deciding": float((Q["rho_deciding"] > 0).mean())}
seen = {("asthma_adult", "no2"), ("asthma_adult", "pm25"), ("asthma_adult", "cockroaches"), ("asthma_adult", "poverty"), ("asthma_adult", "asthma_child")}
R = Q[~Q.apply(lambda r: (r["a"], r["b"]) in seen, axis=1)]
out["without_previously_analysed"] = {"n": int(len(R)), "deciding": float(R["agree"].mean()), "raw": float(R["agree_raw"].mean())}

# sensitivity 1: no negation rule (sign = raw direction x polarities)
F2 = F.dropna(subset=["indicator_sign"]).copy()
F2["plain"] = np.where(F2["raw_direction"] == "+", 1, -1) * F2["a"].map(lambda k: BY_KEY[k]["polarity"]) * F2["b"].map(lambda k: BY_KEY[k]["polarity"])
g = F2.groupby(["a", "b"]).agg(pos=("plain", lambda x: (x > 0).sum()), n=("plain", "size"), st=("study_id", "nunique")).reset_index()
g["cons"] = np.maximum(g["pos"], g["n"] - g["pos"]) / g["n"]
g = g[(g["st"] >= 3) & (g["cons"] >= 0.8)]
g["lit"] = np.where(g["pos"] * 2 > g["n"], 1, -1)
g = g.merge(M[["a", "b", "rho_deciding", "rho_raw"]], on=["a", "b"])
out["no_negation_rule"] = {"n": int(len(g)), "deciding": float((np.sign(g["rho_deciding"]) == g["lit"]).mean()), "raw": float((np.sign(g["rho_raw"]) == g["lit"]).mean()),
                           "negative_literature_pairs": int((g["lit"] < 0).sum()), "findings_flipped_by_rule": int((F2["plain"] != F2["indicator_sign"]).sum()), "signed_findings": int(len(F2))}

# sensitivity 2: partial for poverty and population density
R_ = t.rank()
Z = np.column_stack([np.ones(len(R_)), R_["poverty"], R_["pop_density"]])
res = {}
for c in R_.columns:
    y = R_[c].fillna(R_[c].mean())
    res[c] = y - Z @ np.linalg.lstsq(Z, y, rcond=None)[0]
P2 = pd.DataFrame(res).corr()
Q["rho_pov_density"] = [P2.loc[a, b] for a, b in zip(Q["a"], Q["b"])]
S = Q[~Q["a"].isin(["poverty", "pop_density"]) & ~Q["b"].isin(["poverty", "pop_density"])]
out["partial_poverty_and_density"] = {"n": int(len(S)), "agreement": float((np.sign(S["rho_pov_density"]) == S["lit_sign"]).mean()),
                                      "same_pairs_poverty_only": float(S["agree"].mean()),
                                      "air_pairs": {"n": int((S["kind"] == "air, traffic or noise with anything").sum()),
                                                    "agree": int(((np.sign(S["rho_pov_density"]) == S["lit_sign"]) & (S["kind"] == "air, traffic or noise with anything")).sum())}}
# ranges of the air measures
out["ranges"] = {k: [float(t[k].min()), float(t[k].median()), float(t[k].max())] for k in ("pm25", "no2", "ozone", "black_carbon")}

# gaps
nc = [k for k in KEYS if not BY_KEY[k]["concepts"]]
out["gaps"] = {"indicators_without_concept": nc, "pairs_with_an_unmapped_end": int((~M["mappable"]).sum()),
               "mappable_pairs": int(M["mappable"].sum()), "mappable_no_findings": int((M["mappable"] & (M["n_findings"] == 0)).sum()),
               "with_findings_below_threshold": int(((M["n_findings"] > 0) & (M["n_studies_signed"] < 3)).sum()),
               "three_studies_but_mixed_signs": int(((M["n_studies_signed"] >= 3) & (M["qualifies"] != True)).sum())}  # noqa: E712
G = M[(M["n_findings"] == 0)].copy()
G["abs"] = G["rho_deciding"].abs()
G["mappable"] = G["mappable"].astype(bool)
G.sort_values("abs", ascending=False)[["a", "b", "mappable", "rho_raw", "rho_partial_poverty", "rho_deciding"]].round(3).to_csv(C.OUT / "gaps_unstudied_pairs.csv", index=False)
out["unstudied_pairs_abs_rho_ge_0.5"] = int((G["abs"] >= 0.5).sum())
Q["score"] = Q["rho_deciding"] * Q["lit_sign"]
cols = ["a", "b", "kind", "n_signed", "pos", "neg", "n_studies_signed", "lit_sign", "rho_raw", "rho_partial_poverty", "rho_deciding", "rho_pov_density", "agree"]
Q.sort_values("score")[cols].round(3).to_csv(C.OUT / "qualifying_pairs_ranked.csv", index=False)
(C.OUT / "explore.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
print(Q.sort_values("score")[["a", "b", "rho_deciding", "rho_pov_density"]].head(12).round(2).to_string())
