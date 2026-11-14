"""Rank statistics used for every city test."""
import numpy as np
from scipy import stats

from . import config as C


def spearman(x, y):
    r, p = stats.spearmanr(x, y)
    return float(r), float(p)


def partial_spearman(x, y, z):
    """Spearman correlation of x and y after removing the rank-linear effect of z."""
    rx, ry, rz = (stats.rankdata(v) for v in (x, y, z))
    Z = np.column_stack([np.ones_like(rz), rz])
    ex = rx - Z @ np.linalg.lstsq(Z, rx, rcond=None)[0]
    ey = ry - Z @ np.linalg.lstsq(Z, ry, rcond=None)[0]
    r = float(np.corrcoef(ex, ey)[0, 1])
    n = len(x)
    t = r * np.sqrt((n - 3) / max(1e-12, 1 - r * r))
    p = float(2 * stats.t.sf(abs(t), n - 3))
    return r, p


def bootstrap_ci(x, y, n=C.BOOTSTRAP, seed=C.SEED):
    rng = np.random.default_rng(seed)
    x, y = np.asarray(x), np.asarray(y)
    idx = rng.integers(0, len(x), size=(n, len(x)))
    rs = []
    for i in idx:
        xi, yi = x[i], y[i]
        if np.ptp(xi) == 0 or np.ptp(yi) == 0:
            continue
        rs.append(stats.spearmanr(xi, yi)[0])
    lo, hi = np.nanpercentile(rs, [2.5, 97.5])
    return [round(float(lo), 2), round(float(hi), 2)]


def benjamini_hochberg(pvals):
    p = np.asarray(pvals, dtype=float)
    order = np.argsort(p)
    ranked = p[order] * len(p) / (np.arange(len(p)) + 1)
    q = np.minimum.accumulate(ranked[::-1])[::-1]
    out = np.empty_like(q)
    out[order] = np.minimum(q, 1)
    return out
