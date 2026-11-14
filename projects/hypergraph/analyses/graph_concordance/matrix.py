"""Step 4 (after registration): city correlations, agreement with the literature's sign, nulls and intervals."""
import itertools
import json

import numpy as np
import pandas as pd

import common as C
from indicators import BY_KEY, KEYS

RNG = np.random.default_rng(20261112)
NPERM = 2000


def ranks(t):
    return t.rank()


def spearman_matrix(R):
    """Pairwise-complete Spearman on a rank table (re-ranked per pair when values are missing)."""
    return R.corr(method="spearman", min_periods=30)


def partial_matrix(t, z="poverty"):
    """Spearman partial correlation given poverty: correlate the residuals of ranks regressed on poverty's ranks."""
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
    """The registered deciding correlation: poverty-partialled, or raw when poverty is one of the pair."""
    if "poverty" in (a, b):
        return raw.loc[a, b]
    return par.loc[a, b]


def rate(q, raw, par, which):
    v = []
    for a, b, s in q:
        r = raw.loc[a, b] if which == "raw" else decide(a, b, raw, par)
        if np.isnan(r) or r == 0:
            continue
        v.append(np.sign(r) == s)
    return float(np.mean(v)), len(v)


def main():
    t = pd.read_csv(C.OUT / "city_indicators_uhf42.csv", index_col=0)
    t = t[[k for k in KEYS if k in t.columns]]
    L = pd.read_csv(C.OUT / "literature_signs.csv")
    L = L[L["a"].isin(t.columns) & L["b"].isin(t.columns)]
    raw, par = spearman_matrix(t), partial_matrix(t)
    n = t.notna().astype(int).T @ t.notna().astype(int)
    rows = []
    for _, s in L.iterrows():
        a, b = s["a"], s["b"]
        r, p = raw.loc[a, b], (np.nan if "poverty" in (a, b) else par.loc[a, b])
        d = decide(a, b, raw, par)
        rows.append({**s.to_dict(), "n_areas": int(n.loc[a, b]), "rho_raw": r, "rho_partial_poverty": p, "rho_deciding": d,
                     "agree_raw": (np.sign(r) == s["lit_sign"]) if s["qualifies"] else None,
                     "agree_deciding": (np.sign(d) == s["lit_sign"]) if s["qualifies"] else None})
    M = pd.DataFrame(rows)
    M.to_csv(C.OUT / "matrix_pairs.csv", index=False)
    q = [(r["a"], r["b"], r["lit_sign"]) for _, r in M[M["qualifies"]].iterrows()]
    out = {"n_indicators": int(t.shape[1]), "n_areas": int(t.shape[0]), "n_pairs": int(len(M)), "n_qualifying": len(q)}
    for which in ("raw", "deciding"):
        obs, nq = rate(q, raw, par, which)
        # null 1: each indicator's values shuffled across neighbourhoods independently
        null = []
        for _ in range(NPERM):
            tp = t.apply(lambda c: pd.Series(RNG.permutation(c.values), index=c.index))
            if which == "deciding":
                tp["poverty"] = t["poverty"]
            rp = spearman_matrix(tp)
            pp = partial_matrix(tp) if which == "deciding" else None
            null.append(rate(q, rp, pp, which)[0])
        null = np.array(null)
        # null 2: literature signs shuffled among the qualifying pairs (keeps the share of positive signs)
        signs = np.array([s for _, _, s in q])
        null2 = []
        for _ in range(NPERM):
            sp = RNG.permutation(signs)
            null2.append(rate([(a, b, int(x)) for (a, b, _), x in zip(q, sp)], raw, par, which)[0])
        null2 = np.array(null2)
        # interval: bootstrap of neighbourhoods
        boot = []
        for _ in range(NPERM):
            tb = t.iloc[RNG.integers(0, len(t), len(t))].reset_index(drop=True)
            boot.append(rate(q, spearman_matrix(tb), partial_matrix(tb), which)[0])
        boot = np.array(boot)
        out[which] = {"agreement": obs, "n": nq,
                      "bootstrap_ci95": [float(np.quantile(boot, .025)), float(np.quantile(boot, .975))],
                      "perm_null_area_shuffle": {"mean": float(null.mean()), "q025": float(np.quantile(null, .025)), "q975": float(np.quantile(null, .975)),
                                                 "p_ge_obs": float((np.sum(null >= obs) + 1) / (NPERM + 1))},
                      "perm_null_sign_shuffle": {"mean": float(null2.mean()), "q025": float(np.quantile(null2, .025)), "q975": float(np.quantile(null2, .975)),
                                                 "p_ge_obs": float((np.sum(null2 >= obs) + 1) / (NPERM + 1))}}
    Q = M[M["qualifies"]].copy()
    out["share_literature_positive"] = float((Q["lit_sign"] > 0).mean())
    out["share_city_deciding_positive"] = float((Q["rho_deciding"] > 0).mean())
    out["strict"] = {}
    for thr in (0.2, 0.3):
        s = Q[Q["rho_deciding"].abs() >= thr]
        out["strict"][f"abs_rho_ge_{thr}"] = {"n": int(len(s)), "agreement": float(s["agree_deciding"].mean()) if len(s) else None}
    (C.OUT / "results.json").write_text(json.dumps(out, indent=1))
    raw.to_csv(C.OUT / "rho_raw.csv")
    par.to_csv(C.OUT / "rho_partial_poverty.csv")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
