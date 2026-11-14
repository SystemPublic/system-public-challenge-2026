"""bridge-crz-ems-travel: does EMS travel time in the Congestion Relief Zone follow the
speed change, and by how much?

  python -m analyses.congestion.ems_bridge design   pre-toll data only (through Dec 2024):
        link 2 (elasticity of relative EMS travel time to relative taxi speed), placebo
        standard errors, the composed prediction and the discrimination check.
        Writes data/derived/congestion/ems_design.json. Run BEFORE registration.
  python -m analyses.congestion.ems_bridge run      after registration, with 2025-26 data.
        Writes data/derived/congestion/ems_results.json.

Fixed: seed 20261113, 200,000 composition draws, HAC 3 lags, pre-period Jan 2023 - Dec 2024,
primary post-period 5 Jan - 31 Aug 2025 (the months for which link 1 was measured).
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

sys.path.insert(0, str(__import__("pathlib").Path.home() / "Dropbox" / "projects" / "concordance-kit"))
from kit import bridge  # noqa: E402

from analyses.congestion.common import DER, ROOT
from analyses.congestion import ems_lib as L

SEED, DRAWS = 20261113, 200_000
PRE_FROM, START, PRIMARY_TO = "2023-01-01", "2025-01-01", "2025-08-01"
ALL = ("north", "bklic", "rest")
# link 1: mob-crz-traffic, CBD vs Greater NYC taxi and for-hire speed, Jan-Aug 2025 vs 2023-24
SPEED = {"estimate": 1.0575, "lo": 1.0295, "hi": 1.0862}


def elasticity():
    """Link 2 from pre-toll months only (Oct 2019 - Dec 2024)."""
    p = L.panel(L.load("ems", range(2019, 2025)))
    sp = pd.read_csv(ROOT / "data/derived/mobility/crz_speeds_monthly.csv")
    sp["month"] = pd.to_datetime(sp.month)
    w = sp.pivot(index="month", columns="area", values="speed")
    w = w[w.index < "2025-01-01"]
    d = L.series(p, comp=ALL, period="peak")
    x = pd.DataFrame({"d": d, "s": np.log(w["CBD"] / w["Greater NYC"])}).dropna()
    x["calm"], x["t"] = x.index.month, np.arange(len(x))
    specs = {}
    for name, f, sub in [("levels", "d ~ s", x), ("calendar_month", "d ~ s + C(calm)", x),
                         ("calendar_month_trend", "d ~ s + C(calm) + t", x),
                         ("calendar_month_2022_24", "d ~ s + C(calm)", x[x.index >= "2022-01-01"])]:
        m = smf.ols(f, data=sub).fit(cov_type="HAC", cov_kwds={"maxlags": 3})
        specs[name] = {"b": float(m.params["s"]), "se": float(m.bse["s"]), "n": int(m.nobs)}
    dx = x[["d", "s"]].diff(12).dropna()
    m = smf.ols("d ~ s", data=dx).fit(cov_type="HAC", cov_kwds={"maxlags": 3})
    specs["twelve_month_difference"] = {"b": float(m.params["s"]), "se": float(m.bse["s"]), "n": int(m.nobs)}
    return specs


def design():
    out = {"elasticity_specs": elasticity()}
    bs = [v["b"] for v in out["elasticity_specs"].values()]
    # the exponent: registered spec is calendar_month over the full pre-toll series; its
    # uncertainty is widened to the spread across specifications
    mean = -out["elasticity_specs"]["calendar_month"]["b"]
    sd = float(max(np.std(bs, ddof=1), out["elasticity_specs"]["calendar_month"]["se"]))
    out["exponent"] = {"mean": mean, "sd": sd}
    # placebo standard errors for an 8-month post-period and a 24-month pre-period
    p = L.panel(L.load("ems", range(2019, 2025)))
    pl = {}
    for comp, nm in [(ALL, "all_outside"), (("north",), "north"), (("rest",), "rest"), (("bklic",), "bklic")]:
        d = L.series(p, comp=comp)
        pl[nm] = {"jan_aug_2024_vs_2022_23": L.did(d, "2024-01-01", "2022-01-01", "2024-08-01"),
                  "2024_vs_2023": L.did(d, "2024-01-01", "2023-01-01"),
                  "jan_aug_2019_vs_2017_18": None}
        t = L.triple(p, comp=comp)
        pl[nm]["triple_jan_aug_2024_vs_2022_23"] = L.did(t, "2024-01-01", "2022-01-01", "2024-08-01")
    out["placebos"] = pl
    se = pl["all_outside"]["jan_aug_2024_vs_2022_23"]["se"]
    out["expected_endpoint_se"] = se
    inv = {"name": "time per mile (1/speed), mob-crz-traffic", "estimate": 1 / SPEED["estimate"],
           "lo": 1 / SPEED["hi"], "hi": 1 / SPEED["lo"], "exponent": out["exponent"]}
    comp = bridge.compose([inv], draws=DRAWS, seed=SEED)
    out["composed"] = comp["composed"]
    c = comp["composed"]
    out["discrimination_vs_no_effect"] = bridge.discrimination(c["mean_log"], c["sd_log"], se)
    prop = float(np.log(1 / SPEED["estimate"]))
    out["proportional_log"] = prop
    # if the chain is true, the endpoint sits at the composed mean: distance from proportional
    out["discrimination_vs_proportional"] = {"z_prop_if_chain_true": (c["mean_log"] - prop) / se,
                                             "D_expected": ((c["mean_log"] - prop) / se) ** 2}
    out["pre_levels"] = {}
    (DER / "ems_design.json").write_text(json.dumps(out, indent=1, default=float))
    print(json.dumps({k: out[k] for k in ("exponent", "expected_endpoint_se", "composed", "discrimination_vs_no_effect",
                                          "discrimination_vs_proportional")}, indent=1, default=float))
    print(json.dumps(out["elasticity_specs"], indent=1))
    print(json.dumps({k: {kk: (round(vv["pct"], 2), round(vv["se"], 4)) for kk, vv in v.items() if vv} for k, v in pl.items()}))


def score(est_log, se, comp):
    m, s = comp["mean_log"], comp["sd_log"]
    tot = float(np.hypot(s, se))
    prop = float(np.log(1 / SPEED["estimate"]))
    z_chain, z_null, z_prop = (est_log - m) / tot, est_log / se, (est_log - prop) / se
    return {"z_chain": z_chain, "z_null": z_null, "z_prop": z_prop, "D_vs_null": z_null ** 2 - z_chain ** 2,
            "D_vs_proportional": z_prop ** 2 - z_chain ** 2}


def run():
    des = json.loads((DER / "ems_design.json").read_text())
    comp = des["composed"]
    res = {"composed": comp, "seed": SEED, "draws": DRAWS}
    for kind in ("ems", "fire"):
        yrs = range(2019, 2027)
        df = L.load(kind, yrs)
        if kind == "fire":
            df = df.groupby(["d", "hh", "area", "peak", "period", "month"], as_index=False)[["n", "travel", "response"]].sum()
        variants = {"all": None}
        if kind == "ems":
            variants.update({"life_threatening": lambda x: x.sev == "hi", "lower_priority": lambda x: x.sev == "lo"})
        for vn, wh in variants.items():
            for value in (("travel", "response", "dispatch") if kind == "ems" else ("travel", "response")):
                p = L.panel(df, value=value, where=wh)
                for comp_areas, nm in [(ALL, "all_outside"), (("north",), "north"), (("bklic",), "bklic"), (("rest",), "rest")]:
                    key = f"{kind}.{vn}.{value}.{nm}"
                    r = {}
                    for per in ("peak", "overnight"):
                        d = L.series(p, comp=comp_areas, period=per, value=value)
                        r[per] = {"primary_jan_aug_2025": L.did(d, START, PRE_FROM, PRIMARY_TO),
                                  "full_to_sep_2026": L.did(d, START, PRE_FROM),
                                  "placebo_2024": L.did(d, "2024-01-01", PRE_FROM, "2024-12-01")}
                    t = L.triple(p, comp=comp_areas, value=value)
                    r["triple"] = {"primary_jan_aug_2025": L.did(t, START, PRE_FROM, PRIMARY_TO),
                                   "full_to_sep_2026": L.did(t, START, PRE_FROM),
                                   "placebo_2024": L.did(t, "2024-01-01", PRE_FROM, "2024-12-01")}
                    res[key] = r
        # within-zone, no comparison: peak minus overnight
        p = L.panel(df)
        own = (L.series(p, comp=("crz",), period="peak") * 0)  # placeholder index
        z = p[p.area == "crz"].pivot(index="month", columns="period", values="y")
        w = (z["peak"] - z["overnight"]).dropna()
        res[f"{kind}.within_zone_peak_minus_overnight"] = {"primary_jan_aug_2025": L.did(w, START, PRE_FROM, PRIMARY_TO),
                                                          "full_to_sep_2026": L.did(w, START, PRE_FROM),
                                                          "placebo_2024": L.did(w, "2024-01-01", PRE_FROM, "2024-12-01")}
        # annual level table
        yr = df.assign(y=df.d.dt.year).groupby(["y", "area", "period"])[["travel", "response", "n"]].sum()
        yr["travel_s"], yr["response_s"] = yr.travel / yr.n, yr.response / yr.n
        yr.reset_index()[["y", "area", "period", "n", "travel_s", "response_s"]].to_csv(DER / f"{kind}_annual_levels.csv", index=False)
        mm = L.panel(df)
        mm["travel_s"] = np.exp(mm.y)
        mm[["month", "area", "period", "n", "travel_s"]].to_csv(DER / f"{kind}_monthly_travel.csv", index=False)
    prim = res["ems.all.travel.all_outside"]["peak"]["primary_jan_aug_2025"]
    res["endpoint"] = {**prim, **score(prim["log"], prim["se"], comp)}
    full = res["ems.all.travel.all_outside"]["peak"]["full_to_sep_2026"]
    res["endpoint_full_period"] = {**full, **score(full["log"], full["se"], comp)}
    (DER / "ems_results.json").write_text(json.dumps(res, indent=1, default=float))
    print(json.dumps(res["endpoint"], indent=1, default=float))


if __name__ == "__main__":
    {"design": design, "run": run}[sys.argv[1]]()
