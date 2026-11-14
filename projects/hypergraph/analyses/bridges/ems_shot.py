"""Link and endpoint tests for the heat-violence bridge (registered plans in claims/registered/).

bridge-shot-ems-link       daily SHOT dispatches on daily NYPD shooting incidents (OLS, HAC 7)
bridge-heat-shootings-ems  daily SHOT dispatches on Central Park TMAX/5 (NB GLM as in heat-shootings)
Outputs: data/derived/bridges/ems_daily.csv, ems_results.json
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from analyses.bridges.common import DER
from analyses.heat.shootings import END, FORM, build, irr, nb_fit
from concord import socrata


def ems_daily():
    rows, src = socrata.query_all(
        "76xm-jjuj", order="d, initial_call_type",
        select="date_trunc_ymd(incident_datetime) as d, initial_call_type, count(*) as n",
        where=f"incident_datetime between '2006-01-01' and '{END}T23:59:59' and initial_call_type in ('SHOT', 'T-SHOT', 'STAB')",
        group="d, initial_call_type")
    e = pd.DataFrame(rows)
    e["d"] = pd.to_datetime(e["d"])
    e["n"] = e["n"].astype(int)
    w = e.pivot_table(index="d", columns="initial_call_type", values="n", aggfunc="sum").fillna(0).astype(int)
    return w, src


def compat(obs_log, obs_se, mean_log, sd_log):
    D = obs_log - mean_log
    se = float(np.sqrt(obs_se ** 2 + sd_log ** 2))
    return {"D": float(D), "se": se, "z": float(D / se), "compatible": bool(abs(D / se) < 1.96)}


def main():
    df, srcs = build()
    w, src_e = ems_daily()
    for c in ("SHOT", "T-SHOT", "STAB"):
        df[c] = w[c].reindex(df.index).fillna(0).astype(int) if c in w else 0
    df["SHOT_ALL"] = df["SHOT"] + df["T-SHOT"]
    df = df.dropna(subset=["TMAX"])
    df.to_csv(DER / "ems_daily.csv")
    comp = json.loads((DER / "composed_predictions.json").read_text())["bridge-heat-shootings-ems"]["composed_irr_per5C"]
    res = {"n_days": int(len(df)), "annual_SHOT": df.groupby("year")["SHOT"].sum().to_dict(),
           "annual_NYPD": df.groupby("year")["n"].sum().to_dict()}

    # link: dispatches per NYPD incident
    m = smf.ols("SHOT ~ n + C(dow) + C(month) + C(year) + hol", data=df).fit(cov_type="HAC", cov_kwds={"maxlags": 7})
    b, se = float(m.params["n"]), float(m.bse["n"])
    res["link_dispatches_per_incident"] = {"estimate": b, "lo": b - 1.96 * se, "hi": b + 1.96 * se, "se": se, "n": int(m.nobs)}

    # endpoint
    r, alpha = nb_fit(FORM.format(x="t5").replace("n ~", "SHOT ~"), df)
    e = irr(r, "t5")
    e["log"], e["se"], e["alpha"] = float(r.params["t5"]), float(r.bse["t5"]), alpha
    res["endpoint_SHOT_irr_per5C"] = e
    res["compatibility"] = compat(e["log"], e["se"], comp["mean_log"], comp["sd_log"])
    # the link estimate on the same sample, for the figure
    r0, _ = nb_fit(FORM.format(x="t5"), df)
    res["nypd_irr_same_sample"] = irr(r0, "t5")

    sens = {}
    warm = df[df["month"].between(5, 9)]
    sens["warm_season"] = irr(nb_fit(FORM.format(x="t5").replace("n ~", "SHOT ~"), warm)[0], "t5")
    early = df[df["year"] <= 2019]
    sens["2006_2019"] = irr(nb_fit(FORM.format(x="t5").replace("n ~", "SHOT ~"), early)[0], "t5")
    sens["SHOT_plus_T-SHOT"] = irr(nb_fit(FORM.format(x="t5").replace("n ~", "SHOT_ALL ~"), df)[0], "t5")
    sens["STAB_contrast"] = irr(nb_fit(FORM.format(x="t5").replace("n ~", "STAB ~"), df)[0], "t5")
    res["sensitivity"] = sens

    (DER / "ems_results.json").write_text(json.dumps({"results": res, "composed": comp,
                                                      "sources": srcs + [src_e]}, indent=1, default=float))
    print(json.dumps({k: v for k, v in res.items() if not k.startswith("annual")}, indent=1, default=float))
    print(pd.DataFrame({"SHOT": res["annual_SHOT"], "NYPD": res["annual_NYPD"]}))


if __name__ == "__main__":
    main()
