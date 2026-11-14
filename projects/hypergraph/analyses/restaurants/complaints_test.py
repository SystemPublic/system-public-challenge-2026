"""Registered test restaurants-score-complaints: do restaurants that score worse at a routine
inspection draw more 311 Food Poisoning complaints in the following year?

Fixed before any restaurant-level 311 data were joined to inspection results (rule 9). The model
is a Poisson GLM with HC1 robust standard errors on one row per restaurant, so no resampling and
no seed is involved.

Cohort: every CAMIS whose first Cycle Inspection / Initial Inspection with a score falls in
2023-01-01..2025-06-30 (43nn-pn8j, citywide), whose BBL holds exactly one CAMIS in the live data
from 2022 on (so a complaint at the BBL names this restaurant), and whose BBL is a valid 10-digit
lot. Exposure: score at that inspection, >= 14 (not A-range) against 0-13 (A-range). Outcome: 311
complaints (erm2-nwe9) of type Food Poisoning, location type Restaurant/Bar/Deli/Bakery, at the
BBL, created in the 365 days after the inspection date (day 1 to day 365). Placebo outcome (rule
11): 311 complaints of type Noise - Commercial at the BBL in the same window. Covariates: borough,
cuisine group (20 most common, rest Other), chain (dba with >= 10 CAMIS citywide), inspection
quarter. Secondary (reported, decides nothing): score >= 28 against 0-13; per 10 score points;
NTA fixed effects instead of borough; Manhattan only; the 365 days before the inspection.
"""
from __future__ import annotations

import json
import math

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

import common as c
from power_complaints import cohort

PRED_MID = math.sqrt(1.10 * 1.60)


def complaints(ctype: str, extra: str = ""):
    where = (f"complaint_type='{ctype}' and bbl is not null and created_date between '2022-01-01' and '2026-07-01'" + extra)
    rows, src = c.socrata.query_all(c.SR311, select="unique_key, created_date, bbl", where=where, order="unique_key")
    d = pd.DataFrame(rows)
    d["bbl"] = d["bbl"].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(10)
    d["created"] = pd.to_datetime(d["created_date"].str[:10])
    return d[["bbl", "created"]], src


def count_window(coh: pd.DataFrame, comp: pd.DataFrame, lo: int, hi: int) -> pd.Series:
    m = coh[["camis", "bbl", "inspection_date"]].merge(comp, on="bbl", how="inner")
    dt = (m.created - m.inspection_date).dt.days
    m = m[(dt >= lo) & (dt <= hi)]
    return coh.camis.map(m.groupby("camis").size()).fillna(0).astype(int)


def fit(df: pd.DataFrame, y: str, x: str, fe: str = "C(boro)"):
    ctl = [fe, "C(cuis)", "C(q)"] + (["chain"] if df["chain"].nunique() > 1 else [])
    f = f"{y} ~ {x} + " + " + ".join(ctl)
    m = smf.glm(f, data=df, family=sm.families.Poisson()).fit(cov_type="HC1")
    t = x
    b, se = float(m.params[t]), float(m.bse[t])
    pearson = float(m.pearson_chi2 / m.df_resid)
    return {"term": t, "b": b, "se": se, "irr": math.exp(b), "lo": math.exp(b - 1.96 * se), "hi": math.exp(b + 1.96 * se),
            "n": int(m.nobs), "events": int(df[y].sum()), "pearson_dispersion": round(pearson, 2)}


def main():
    coh, src_i = cohort()
    coh = coh[coh.single_bbl & coh.bbl.str.fullmatch(r"[1-5]\d{9}").fillna(False)].copy()
    coh["notA"] = (coh.score >= 14).astype(int)
    coh["band"] = np.where(coh.score >= 28, "C", np.where(coh.score >= 14, "B", "A"))
    coh["score10"] = coh.score / 10
    coh["cuis"] = c.cuisine_group(coh.cuisine_description)
    # chain flag from all live CAMIS, not only the cohort
    live, _ = c.inspections("inspection_date between '2022-01-01' and '2026-12-31'", "live2022")
    names = c.norm_dba(live.drop_duplicates("camis").dba)
    nchain = names.value_counts()
    coh["chain"] = c.norm_dba(coh.dba).map(nchain).fillna(1).ge(c.CHAIN_MIN).astype(int)
    coh["q"] = coh.inspection_date.dt.to_period("Q").astype(str)
    fp, src_fp = complaints("Food Poisoning", " and location_type='Restaurant/Bar/Deli/Bakery'")
    nz, src_nz = complaints("Noise - Commercial")
    coh["fp"] = count_window(coh, fp, 1, 365)
    coh["noise"] = count_window(coh, nz, 1, 365)
    coh["fp_pre"] = count_window(coh, fp, -365, -1)

    res = {"primary": fit(coh, "fp", "notA"), "placebo_noise": fit(coh, "noise", "notA")}
    p, q = res["primary"], res["placebo_noise"]
    dr = p["b"] - q["b"]
    sr = math.sqrt(p["se"] ** 2 + q["se"] ** 2)
    res["ratio_fp_over_noise"] = {"irr_ratio": math.exp(dr), "lo": math.exp(dr - 1.96 * sr), "hi": math.exp(dr + 1.96 * sr)}
    # rule 8 measure against the band midpoint, with no effect and with the placebo as the null
    z_pred = (p["b"] - math.log(PRED_MID)) / p["se"]
    z_null = p["b"] / p["se"]
    z_pl = dr / sr
    res["discrimination"] = {"z_pred": z_pred, "z_null": z_null, "D_null": z_null ** 2 - z_pred ** 2,
                             "z_placebo": z_pl, "D_placebo": z_pl ** 2 - z_pred ** 2}
    res["secondary"] = {
        "C_vs_A": fit(coh[coh.band != "B"].assign(Cband=lambda d: (d.band == "C").astype(int)), "fp", "Cband"),
        "per_10_points": fit(coh, "fp", "score10"),
        "nta_fe": fit(coh[coh.nta.notna()], "fp", "notA", fe="C(nta)"),
        "manhattan": fit(coh[coh.boro == "Manhattan"], "fp", "notA", fe="1"),
        "pre_window": fit(coh, "fp_pre", "notA"),
    }
    sup = p["lo"] > 1.0 and res["ratio_fp_over_noise"]["lo"] > 1.0
    ref = p["hi"] < 1.10
    placebo_meets = q["lo"] > 1.0
    res["conditions"] = {"support_if_met": sup, "refute_if_met": ref, "placebo_meets_support": placebo_meets,
                         "rule11_discriminates": res["discrimination"]["D_placebo"] >= 4}
    res["cohort"] = {"n": len(coh), "share_notA": float(coh.notA.mean()), "fp_events": int(coh.fp.sum()),
                     "noise_events": int(coh.noise.sum()), "by_band_rate": coh.groupby("band")[["fp", "noise"]].mean().round(4).to_dict()}
    res["sources"] = [src_i, src_fp, src_nz]
    c.write_json("complaints_test.json", res)
    coh[["camis", "boro", "nta", "band", "score", "chain", "cuis", "fp", "noise", "fp_pre"]].to_csv(c.DER / "complaints_cohort.csv", index=False)
    print(json.dumps({k: v for k, v in res.items() if k != "sources"}, indent=1, default=str))


if __name__ == "__main__":
    main()
