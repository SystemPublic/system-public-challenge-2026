"""Step 3 (after registration): the concordance matrix in Chicago, and New York recomputed on the same pairs.

The qualifying rule, the deciding correlation, the always-positive benchmark and the two nulls are those of
analyses/graph_concordance/matrix.py (claim graph-concordance-matrix); spearman_matrix, partial_matrix and decide
are copied from it unchanged. The literature signs are read from data/derived/graph/concordance/literature_signs.csv.
Registered defaults: 2,000 draws, seed 20261113. Other draws and seeds are for the rule 9 check only and write to
a file with a tag.

    python analyses/round5_chicago_matrix/matrix.py [--draws N --seed S --tag T --no-null]
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "analyses" / "graph_concordance"))
from indicators import BY_KEY  # noqa: E402  (New York mapping table: roles, labels)

NY = ROOT / "data" / "derived" / "graph" / "concordance"
OUT = ROOT / "data" / "derived" / "round5" / "chicago_matrix"
AIR = {"pm25", "no2", "black_carbon", "ozone", "traffic", "noise"}
BEHAV = {"smoking", "binge_drinking", "exercise", "sugary_drinks", "walk_commute", "car_commute"}
KINDS = ["air, traffic or noise with anything", "health outcome with health outcome", "behaviour with anything else",
         "social or housing condition with anything else"]
ROLES = ["exposure with outcome", "outcome with outcome", "exposure with exposure"]
NY_AIR = (10, 27)        # graph-concordance-matrix outcome: air, traffic or noise pairs agreeing
MIN_AIR_PAIRS = 12
SUPPORT_SHARE = 0.60


def spearman_matrix(R):
    return R.corr(method="spearman", min_periods=30)


def partial_matrix(t, z="poverty"):
    R = t.rank()
    zr = R[z]
    res = {}
    for c in R.columns:
        if c == z:
            continue
        m = R[c].notna() & zr.notna()
        b = np.polyfit(zr[m], R[c][m], 1)
        res[c] = R[c] - (b[0] * zr + b[1])
    return pd.DataFrame(res).corr(min_periods=30)


def decide(a, b, raw, par):
    if "poverty" in (a, b):
        return raw.loc[a, b]
    return par.loc[a, b]


def kind(a, b):
    if {a, b} & AIR:
        return KINDS[0]
    if BY_KEY[a]["role"] == BY_KEY[b]["role"] == "outcome":
        return KINDS[1]
    if {a, b} & BEHAV:
        return KINDS[2]
    return KINDS[3]


def role(a, b):
    r = sorted([BY_KEY[a]["role"], BY_KEY[b]["role"]])
    return {("exposure", "outcome"): ROLES[0], ("outcome", "outcome"): ROLES[1], ("exposure", "exposure"): ROLES[2]}[tuple(r)]


def rhos(t, pairs):
    raw, par = spearman_matrix(t), partial_matrix(t)
    r = np.array([raw.loc[a, b] for a, b in pairs])
    d = np.array([decide(a, b, raw, par) for a, b in pairs])
    return r, d


def share(d, s, m=None):
    """Share of pairs whose correlation d has sign s; pairs with a missing or zero correlation are skipped."""
    ok = ~np.isnan(d) & (d != 0)
    if m is not None:
        ok = ok & m
    return float(np.mean(np.sign(d[ok]) == s[ok])) if ok.any() else np.nan


def ci(x):
    x = np.asarray(x, float)
    x = x[~np.isnan(x)]
    return [float(np.quantile(x, .025)), float(np.quantile(x, .975))] if len(x) else [None, None]


def block(t, L, rng, draws, null=True, restrict=None):
    """All registered quantities for one city. restrict: an optional set of (a, b) pairs to keep."""
    Q = L[L["qualifies"] & L["a"].isin(t.columns) & L["b"].isin(t.columns)].copy()
    pairs = list(zip(Q["a"], Q["b"]))
    r, d = rhos(t, pairs)
    Q["rho_raw"], Q["rho_deciding"] = r, d
    Q = Q[~np.isnan(d) & (d != 0)]
    if restrict is not None:
        Q = Q[[p in restrict for p in zip(Q["a"], Q["b"])]]
    Q = Q.reset_index(drop=True)
    pairs = list(zip(Q["a"], Q["b"]))
    s = Q["lit_sign"].to_numpy(float)
    r, d = Q["rho_raw"].to_numpy(), Q["rho_deciding"].to_numpy()
    Q["kind"] = [kind(a, b) for a, b in pairs]
    Q["role"] = [role(a, b) for a, b in pairs]
    Q["agree_raw"], Q["agree_deciding"] = np.sign(r) == s, np.sign(d) == s
    masks = {"all": np.ones(len(Q), bool)}
    masks.update({k: (Q["kind"] == k).to_numpy() for k in KINDS})
    masks.update({k: (Q["role"] == k).to_numpy() for k in ROLES})
    for e in sorted(AIR):
        masks["with " + e] = np.array([e in p for p in pairs])
    pos = np.ones(len(Q))
    stat = lambda dd, m: (share(dd, s, m), share(dd, pos, m))  # noqa: E731  agreement, always-positive
    boot = {k: [] for k in masks}
    bpm = []
    for _ in range(draws):
        tb = t.iloc[rng.integers(0, len(t), len(t))].reset_index(drop=True)
        _, db = rhos(tb, pairs)
        for k, m in masks.items():
            boot[k].append(stat(db, m))
        bpm.append(tb["pm25"].corr(tb["poverty"], method="spearman") if "pm25" in tb else np.nan)
    out = {"n_areas": int(len(t)), "n_indicators": int(t.shape[1]), "n_qualifying": int(len(Q)),
           "n_literature_positive": int((s > 0).sum()), "groups": {}}
    for k, m in masks.items():
        if not m.any():
            continue
        b = np.array(boot[k])
        ag, ap = stat(d, m)
        out["groups"][k] = {"n": int(m.sum()), "agree": int((np.sign(d[m]) == s[m]).sum()), "agreement": ag, "agreement_ci95": ci(b[:, 0]),
                            "agree_raw": int((np.sign(r[m]) == s[m]).sum()),
                            "always_positive": ap, "margin_over_always_positive": ag - ap, "margin_ci95": ci(b[:, 0] - b[:, 1])}
    out["boot_air"] = [x[0] for x in boot[KINDS[0]]]
    if "pm25" in t:
        out["pm25_poverty"] = {"spearman": float(t["pm25"].corr(t["poverty"], method="spearman")), "ci95": ci(bpm),
                               "pearson": float(t["pm25"].corr(t["poverty"])), "n": int((t["pm25"].notna() & t["poverty"].notna()).sum())}
    if null:
        obs = share(d, s)
        n1, n2 = [], []
        for _ in range(draws):
            tp = t.apply(lambda c: pd.Series(rng.permutation(c.values), index=c.index))
            tp["poverty"] = t["poverty"]
            n1.append(share(rhos(tp, pairs)[1], s))
            n2.append(share(d, rng.permutation(s)))
        for name, n in (("perm_null_area_shuffle", np.array(n1)), ("perm_null_sign_shuffle", np.array(n2))):
            out[name] = {"mean": float(n.mean()), "q025": float(np.quantile(n, .025)), "q975": float(np.quantile(n, .975)),
                         "p_ge_obs": float((np.sum(n >= obs) + 1) / (draws + 1))}
    return out, Q


def verdict(air):
    """The registered conditions of prediction (a)."""
    if air is None or air["n"] < MIN_AIR_PAIRS:
        return "no_test"
    lo, hi = air["agreement_ci95"]
    thr = NY_AIR[0] / NY_AIR[1]
    if air["agreement"] >= SUPPORT_SHARE and lo > thr:
        return "confirmed"
    if air["agreement"] <= thr and hi < SUPPORT_SHARE:
        return "contested"
    return "unsettled"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--draws", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=20261113)
    ap.add_argument("--tag", default="")
    ap.add_argument("--no-null", action="store_true")
    a = ap.parse_args()
    L = pd.read_csv(NY / "literature_signs.csv")
    L["qualifies"] = L["qualifies"] == True  # noqa: E712
    tc = pd.read_csv(OUT / "chicago_indicators_ca77.csv", index_col=0)
    tn = pd.read_csv(NY / "city_indicators_uhf42.csv", index_col=0)
    chi, Qc = block(tc, L, np.random.default_rng([a.seed, 0]), a.draws, null=not a.no_null)
    ny_all, Qn = block(tn, L, np.random.default_rng([a.seed, 1]), a.draws, null=False)
    both = set(zip(Qc["a"], Qc["b"])) & set(zip(Qn["a"], Qn["b"]))
    ny_m, Qm = block(tn, L, np.random.default_rng([a.seed, 2]), a.draws, null=False, restrict=both)
    air_c = chi["groups"].get(KINDS[0])
    bc, bn = np.array(chi.pop("boot_air")), np.array(ny_m.pop("boot_air"))
    ny_all.pop("boot_air")
    res = {"draws": a.draws, "seed": a.seed, "chicago": chi, "new_york_all_pairs": ny_all, "new_york_same_pairs": ny_m,
           "n_pairs_in_both": len(both),
           "air_share_difference_same_pairs": None if air_c is None or KINDS[0] not in ny_m["groups"] else {
               "chicago_minus_new_york": air_c["agreement"] - ny_m["groups"][KINDS[0]]["agreement"], "ci95": ci(bc - bn)},
           "prediction_a": {"new_york_reference": f"{NY_AIR[0]} of {NY_AIR[1]}", "threshold_share": SUPPORT_SHARE, "min_pairs": MIN_AIR_PAIRS,
                            "verdict": verdict(air_c)}}
    if not a.tag:
        Qc.round(4).to_csv(OUT / "chicago_matrix_pairs.csv", index=False)
        Qm.round(4).to_csv(OUT / "new_york_same_pairs.csv", index=False)
        m = Qc.merge(Qm[["a", "b", "rho_raw", "rho_deciding", "agree_deciding"]], on=["a", "b"], how="left", suffixes=("_chicago", "_new_york"))
        cols = ["a", "b", "kind", "role", "n_signed", "pos", "neg", "n_studies_signed", "lit_sign", "rho_raw_chicago", "rho_deciding_chicago",
                "agree_deciding_chicago", "rho_raw_new_york", "rho_deciding_new_york", "agree_deciding_new_york"]
        m[cols].round(4).to_csv(OUT / "pairs_two_cities.csv", index=False)
    (OUT / f"results{('_' + a.tag) if a.tag else ''}.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
