"""Shared model code for transfer-chicago-hot-end.

A negative binomial GLM of a daily count on a natural cubic spline of maximum temperature
(patsy cr, df=4, centred; knots at quantiles of the fitted days) with the calendar terms of
heat-shootings (day of week, month, year, holiday, wet day), HC0 standard errors. The
functions give the change in the count between two temperatures, with and without
log(1 + proxy) in the model, and the share of the log change that the proxy removes,
with intervals from resampled calendar weeks.
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from patsy import build_design_matrices, dmatrices, dmatrix

warnings.filterwarnings("ignore")
CONTROLS = "C(dow) + C(month) + C(year) + hol + wet"
RANGES = ((21, 15), (27, 21), (33, 27))
# "lin": piecewise linear with knots at 15, 21 and 27 C (the registered primary basis; the
#        rise from 27 to 33 C is six times the slope above 27 C).
# "q4":  the New York exploratory basis (natural cubic, 4 df, knots at quantiles).
# "k":   natural cubic with inner knots fixed at 9, 15, 21 and 27 C.
SPLINES = {"q4": "cr(x, df=4, constraints='center') - 1",
           "k": "cr(x, knots=[9, 15, 21, 27], constraints='center') - 1"}
SPLINE = "lin"
KNOTS = (15.0, 21.0, 27.0)
GRID = np.arange(-5, 36.5, 1.0)


class Basis:
    def __init__(self, x):
        self.kind = SPLINE
        if self.kind != "lin":
            self.dm = dmatrix(SPLINES[self.kind], {"x": np.asarray(x, float)})
        self.B = self(x)

    def __call__(self, t):
        t = np.atleast_1d(np.asarray(t, float))
        if self.kind == "lin":
            return np.column_stack([t] + [np.clip(t - k, 0, None) for k in KNOTS])
        return np.asarray(build_design_matrices([self.dm.design_info], {"x": t})[0])


def nb_alpha(y: str, d: pd.DataFrame, default=0.05) -> float:
    try:
        a = float(smf.negativebinomial(f"{y} ~ t5 + {CONTROLS}", d).fit(disp=0, maxiter=300).params["alpha"])
        return a if np.isfinite(a) and a > 0 else default
    except Exception:
        return default


def design(d: pd.DataFrame, y: str, proxy: str | None = None):
    basis = Basis(d["TMAX"].values)
    B = basis.B
    yy, X = dmatrices(f"{y} ~ {CONTROLS}", d, return_type="dataframe")
    sc = [f"s{i}" for i in range(B.shape[1])]
    for i, c in enumerate(sc):
        X[c] = B[:, i]
    if proxy:
        X["lm"] = np.log1p(d[proxy].values)
    return yy.iloc[:, 0], X, sc, basis


def cvec(basis, t1, t0):
    return basis(t1)[0] - basis(t0)[0]


def curve_fit(d, y, alpha, proxy=None):
    """Contrasts for RANGES and the curve relative to 15 C."""
    yy, X, sc, basis = design(d, y, proxy)
    r = sm.GLM(yy, X, family=sm.families.NegativeBinomial(alpha=alpha)).fit(cov_type="HC0")
    bb, V = r.params[sc].values, r.cov_params().loc[sc, sc].values
    out = {}
    for t1, t0 in RANGES:
        x = cvec(basis, t1, t0)
        e, s = float(x @ bb), float(np.sqrt(x @ V @ x))
        out[f"rr_{t1}_vs_{t0}"] = {"estimate": float(np.exp(e)), "lo": float(np.exp(e - 1.96 * s)),
                                   "hi": float(np.exp(e + 1.96 * s)), "log": e, "se": s}
    D = np.vstack([cvec(basis, t, 15) for t in GRID])
    eta, se = D @ bb, np.sqrt(np.einsum("ij,jk,ik->i", D, V, D))
    cur = pd.DataFrame({"tmax_c": GRID, "rr": np.exp(eta), "lo": np.exp(eta - 1.96 * se), "hi": np.exp(eta + 1.96 * se)})
    if proxy:
        out["proxy_coef_log1p"] = {"estimate": float(r.params["lm"]), "se": float(r.bse["lm"])}
    return out, cur


def shares(d, y, proxy, alpha, boot=500, seed=1, removed=False):
    """Share of the log change in y over each range that disappears when the proxy is added."""
    yy, X0, sc, basis = design(d, y)
    X1 = X0.copy()
    X1["lm"] = np.log1p(d[proxy].values)
    C = np.vstack([cvec(basis, t1, t0) for t1, t0 in RANGES])
    j = [list(X0.columns).index(c) for c in sc]
    fam = lambda: sm.families.NegativeBinomial(alpha=alpha)

    def one(idx):
        p0 = sm.GLM(yy.values[idx], X0.values[idx], family=fam()).fit().params[j]
        p1 = sm.GLM(yy.values[idx], X1.values[idx], family=fam()).fit().params[j]
        return C @ p0, C @ p1

    a0, a1 = one(np.arange(len(d)))
    est = 1 - a1 / a0
    wk = ((d.index - pd.Timestamp("2006-01-02")).days // 7).values
    groups: dict = {}
    for i, w in enumerate(wk):
        groups.setdefault(w, []).append(i)
    keys = list(groups)
    rng = np.random.default_rng(seed)
    S, L1, R = [], [], []
    for _ in range(boot):
        idx = np.concatenate([groups[k] for k in rng.choice(keys, len(keys))])
        try:
            b0, b1 = one(idx)
            S.append(1 - b1 / b0)
            L1.append(b1)
            R.append(b0 - b1)
        except Exception:
            pass
    S, L1 = np.array(S), np.array(L1)
    out = {}
    for k, (t1, t0) in enumerate(RANGES):
        out[f"share_{t1}_vs_{t0}"] = {"estimate": float(est[k]), "lo": float(np.percentile(S[:, k], 2.5)),
                                      "hi": float(np.percentile(S[:, k], 97.5)), "n_boot": int(len(S))}
        if removed:  # log rise without the proxy minus log rise with it
            Rk = np.array(R)[:, k]
            out[f"removed_log_{t1}_vs_{t0}"] = {"estimate": float(a0[k] - a1[k]), "lo": float(np.percentile(Rk, 2.5)),
                                                "hi": float(np.percentile(Rk, 97.5))}
    return out
