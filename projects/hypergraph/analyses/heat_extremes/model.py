"""Model code for heat-extremes-downturn (fixed with the registration).

Per city: a negative binomial GLM of the daily count on indicator terms for bins of daily
maximum temperature, with day of week, month, year, holiday, first day of the month and wet
day (the calendar terms of heat-shootings plus the first-of-month term, because several
portals date incidents of unknown day to the first). The dispersion alpha is estimated once
per city by maximum likelihood with a linear temperature term, then held fixed; standard
errors are HC0.

Primary contrast: days with TMAX >= 38.0 C against days with 32.0 <= TMAX < 35.0 C.
Pooling: inverse-variance fixed effect and DerSimonian-Laird random effects on the log scale.
"""
from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[2]
DER = ROOT / "data" / "derived" / "heat_extremes"
CITIES = ["phoenix", "tucson", "dallas", "austin", "los_angeles", "philadelphia", "chicago", "new_york"]
LABEL = {"phoenix": "Phoenix", "tucson": "Tucson", "dallas": "Dallas", "austin": "Austin", "los_angeles": "Los Angeles",
         "philadelphia": "Philadelphia", "chicago": "Chicago", "new_york": "New York"}
CONTROLS = "C(dow) + C(month) + C(year) + hol + dom1 + wet"
STRICT = "C(dow) + C(ym) + hol + dom1 + wet"
# primary bins: everything at or above 38 C is one bin
EDGES_PRIMARY = [-np.inf, 8, 14, 20, 23, 26, 29, 32, 35, 38, np.inf]
# curve bins: 3 C steps to 47 C
EDGES_CURVE = [-np.inf, 8, 14, 20, 23, 26, 29, 32, 35, 38, 41, 44, np.inf]
REF = "[32.0, 35.0)"
MIN_DAYS = 100  # a city enters the pooled test with at least this many days in each of the two bins
MIN_CURVE_DAYS = 20  # a curve bin is reported with at least this many days
PCT_EDGES = [0, 25, 50, 70, 80, 90, 95, 98, 100.0001]
PCT_REF = "[50.0, 70.0)"


def load(city: str, y: str = "n") -> pd.DataFrame:
    d = pd.read_csv(DER / f"daily_{city}.csv", parse_dates=["date"]).set_index("date")
    d = d.dropna(subset=[y, "TMAX"]).copy()
    d["wet"] = d["wet"].fillna(0)
    d[y] = d[y].astype(int)
    d["ym"] = d["year"] * 100 + d["month"]
    d["t5"] = d["TMAX"] / 5.0
    d["pct"] = d["TMAX"].rank(pct=True, method="average") * 100
    return d


def bins(x, edges) -> pd.Series:
    return pd.cut(x, edges, right=False).astype(str)


def day_counts(d: pd.DataFrame) -> dict:
    t = d["TMAX"]
    return {"days": int(len(d)), "d32_35": int(((t >= 32) & (t < 35)).sum()), "d35_38": int(((t >= 35) & (t < 38)).sum()),
            "d38p": int((t >= 38).sum()), "d41p": int((t >= 41).sum()), "d44p": int((t >= 44).sum()),
            "p50": float(t.quantile(.5)), "p90": float(t.quantile(.9)), "p95": float(t.quantile(.95)), "p99": float(t.quantile(.99)),
            "max": float(t.max()), "mean_38p": float(t[t >= 38].mean()) if (t >= 38).any() else None,
            "mean_32_35": float(t[(t >= 32) & (t < 35)].mean()) if ((t >= 32) & (t < 35)).any() else None}


def nb_alpha(d: pd.DataFrame, y: str = "n", default: float = 0.05) -> float:
    try:
        a = float(smf.negativebinomial(f"{y} ~ t5 + {CONTROLS}", d).fit(disp=0, maxiter=300).params["alpha"])
        return a if np.isfinite(a) and a > 1e-4 else default if not np.isfinite(a) else max(a, 1e-4)
    except Exception:
        return default


def fit_bins(d: pd.DataFrame, y: str, col: str, ref: str, alpha: float, controls: str = CONTROLS, min_days: int = 1):
    """Rate ratios of each level of d[col] against ref. Levels with under min_days days are dropped from the output."""
    d = d.copy()
    n = d[col].value_counts()
    r = smf.glm(f"{y} ~ C({col}, Treatment(reference='{ref}')) + {controls}", d,
                family=sm.families.NegativeBinomial(alpha=alpha)).fit(cov_type="HC0")
    out = {}
    for lev in n.index:
        if lev == ref:
            out[lev] = {"log": 0.0, "se": 0.0, "days": int(n[lev])}
            continue
        k = f"C({col}, Treatment(reference='{ref}'))[T.{lev}]"
        if k in r.params.index and n[lev] >= min_days:
            out[lev] = {"log": float(r.params[k]), "se": float(r.bse[k]), "days": int(n[lev])}
    return out


def rr(e: dict) -> dict:
    return {"estimate": float(np.exp(e["log"])), "lo": float(np.exp(e["log"] - 1.96 * e["se"])), "hi": float(np.exp(e["log"] + 1.96 * e["se"])),
            **{k: v for k, v in e.items() if k not in ("log",)}}


def primary(d: pd.DataFrame, y: str = "n", controls: str = CONTROLS, alpha: float | None = None) -> dict | None:
    d = d.copy()
    d["tb"] = bins(d["TMAX"], EDGES_PRIMARY)
    if (d["tb"] == "[38.0, inf)").sum() < 5 or (d["tb"] == REF).sum() < 5:
        return None
    alpha = nb_alpha(d, y) if alpha is None else alpha
    e = fit_bins(d, y, "tb", REF, alpha, controls).get("[38.0, inf)")
    if e is None:
        return None
    return {**e, "alpha": alpha, "days_ref": int((d["tb"] == REF).sum())}


def pool(ests: list[dict]) -> dict:
    b = np.array([e["log"] for e in ests]); v = np.array([e["se"] for e in ests]) ** 2
    w = 1 / v
    fe = float((w * b).sum() / w.sum()); fe_se = float(np.sqrt(1 / w.sum()))
    k = len(b)
    Q = float((w * (b - fe) ** 2).sum())
    c = w.sum() - (w ** 2).sum() / w.sum()
    tau2 = max(0.0, (Q - (k - 1)) / c) if k > 1 and c > 0 else 0.0
    wr = 1 / (v + tau2)
    re = float((wr * b).sum() / wr.sum()); re_se = float(np.sqrt(1 / wr.sum()))
    f = lambda m, s: {"estimate": float(np.exp(m)), "lo": float(np.exp(m - 1.96 * s)), "hi": float(np.exp(m + 1.96 * s)), "log": m, "se": s}
    return {"k": k, "fixed": f(fe, fe_se), "random": f(re, re_se), "Q": Q, "tau2": tau2,
            "I2": float(max(0.0, (Q - (k - 1)) / Q)) if Q > 0 and k > 1 else 0.0}
