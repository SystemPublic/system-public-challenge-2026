"""heat-extremes-downturn: the registered test (fixed with the registration; no resampling, no seed).

For each qualifying city (at least 100 days at or above 38 C and 100 days at 32 to 35 C:
Phoenix, Tucson, Dallas, Austin, fixed by power.py from temperatures alone) the rate ratio of
daily aggravated assaults on days at or above 38 C against days at 32 to 35 C is estimated
with the model in model.py, and the four estimates are pooled with DerSimonian-Laird random
effects. The pooled interval decides the verdict.

Run: ~/.venvs/nyc-concordance/bin/python -m analyses.heat_extremes.test
Writes data/derived/heat_extremes/test_results.json
"""
import json

import numpy as np
import pandas as pd

from analyses.heat_extremes import model as m

QUALIFYING = ["phoenix", "tucson", "dallas", "austin"]


def contrast(d, hi_lo, hi_hi, alpha, controls=m.CONTROLS):
    """Rate ratio of days with hi_lo <= TMAX < hi_hi against days at 32 to 35 C (other days keep their primary bins)."""
    d = d.copy()
    d["tb"] = m.bins(d["TMAX"], m.EDGES_PRIMARY)
    t = d["TMAX"]
    d.loc[t >= 35, "tb"] = "other_hot"
    d.loc[(t >= hi_lo) & (t < hi_hi), "tb"] = "target"
    if (d["tb"] == "target").sum() < m.MIN_CURVE_DAYS:
        return None
    return m.fit_bins(d, "n", "tb", m.REF, alpha, controls).get("target")


def main():
    out = {"qualifying": QUALIFYING, "cities": {}, "sensitivity": {}}
    frames, alphas = {}, {}
    for c in m.CITIES:
        d = m.load(c)
        e = m.primary(d)
        if e is None:
            continue
        frames[c], alphas[c] = d, e["alpha"]
        out["cities"][c] = {**m.rr(e), "mean_tmax_38p": float(d.loc[d.TMAX >= 38, "TMAX"].mean()),
                            "mean_tmax_32_35": float(d.loc[(d.TMAX >= 32) & (d.TMAX < 35), "TMAX"].mean())}
    out["pooled"] = m.pool([{"log": np.log(out["cities"][c]["estimate"]), "se": out["cities"][c]["se"]} for c in QUALIFYING])
    p = out["pooled"]["random"]
    out["verdict"] = "confirmed" if p["hi"] < 1 else "contested" if p["lo"] > 1 else "unsettled"

    def pooled(fn):
        es = {c: fn(c) for c in QUALIFYING}
        es = {c: e for c, e in es.items() if e is not None}
        return {"cities": {c: m.rr(e) for c, e in es.items()}, "pooled": m.pool(list(es.values())) if len(es) > 1 else None}

    S = out["sensitivity"]
    S["S1_year_month_strata"] = pooled(lambda c: m.primary(frames[c], controls=m.STRICT, alpha=alphas[c]))
    S["S2_may_sep_only"] = pooled(lambda c: m.primary(frames[c][frames[c]["month"].between(5, 9)], alpha=alphas[c]))
    S["S3_without_2020_2021"] = pooled(lambda c: m.primary(frames[c][~frames[c]["year"].isin([2020, 2021])], alpha=alphas[c]))
    S["S4_35_38_vs_32_35"] = pooled(lambda c: contrast(frames[c], 35, 38, alphas[c]))
    S["S5_38_41_vs_32_35"] = pooled(lambda c: contrast(frames[c], 38, 41, alphas[c]))
    S["S6_41_plus_vs_32_35"] = pooled(lambda c: contrast(frames[c], 41, np.inf, alphas[c]))
    S["S7_fixed_effect_pool"] = out["pooled"]["fixed"]
    # the linear alternative: the slope below 35 C carried to the mean temperature of the >=38 C days
    lin = {}
    for c in QUALIFYING:
        d = frames[c]
        import statsmodels.api as sm
        import statsmodels.formula.api as smf
        r = smf.glm(f"n ~ TMAX + {m.CONTROLS}", d[d.TMAX < 35], family=sm.families.NegativeBinomial(alpha=alphas[c])).fit(cov_type="HC0")
        gap = out["cities"][c]["mean_tmax_38p"] - out["cities"][c]["mean_tmax_32_35"]
        lin[c] = {"slope_per_5C_below_35": float(np.exp(5 * r.params["TMAX"])), "slope_lo": float(np.exp(5 * (r.params["TMAX"] - 1.96 * r.bse["TMAX"]))),
                  "slope_hi": float(np.exp(5 * (r.params["TMAX"] + 1.96 * r.bse["TMAX"]))), "gap_C": float(gap),
                  "linear_prediction": float(np.exp(r.params["TMAX"] * gap)), "log": float(r.params["TMAX"] * gap), "se": float(r.bse["TMAX"] * gap)}
    out["linear_alternative"] = {"cities": lin, "pooled": m.pool([{"log": v["log"], "se": v["se"]} for v in lin.values()])}
    (m.DER / "test_results.json").write_text(json.dumps(out, indent=1))
    print(json.dumps({"cities": {c: {k: round(v, 3) for k, v in e.items() if isinstance(v, float)} for c, e in out["cities"].items()},
                      "pooled_random": p, "pooled_fixed": out["pooled"]["fixed"], "I2": out["pooled"]["I2"], "verdict": out["verdict"]}, indent=1))
    for k, v in S.items():
        if k != "S7_fixed_effect_pool" and v["pooled"]:
            print(k, {c: round(e["estimate"], 3) for c, e in v["cities"].items()}, "pooled", [round(v["pooled"]["random"][x], 3) for x in ("estimate", "lo", "hi")])
    print("linear", {c: (round(v["slope_per_5C_below_35"], 3), round(v["linear_prediction"], 3)) for c, v in lin.items()},
          [round(out["linear_alternative"]["pooled"]["random"][x], 3) for x in ("estimate", "lo", "hi")])


if __name__ == "__main__":
    main()
