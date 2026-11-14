"""Round 5 answer, exploratory check: do the earlier calendar-day heat claims change when a
shooting is assigned to the "night of" day (06:00 on date d to 05:59 on d+1)?

The referee of heat-night-minimum found that calendar-day counts include shootings from 00:00
to 05:59, which precede the day's maximum that they are regressed on. This script refits the
registered models of heat-shootings, transfer-chicago-heat-shootings and heat-mech-outdoors,
and the hot-end contrast of 33 against 27 C, on night-of counts. It decides no verdict
(PRECEDENCE rule 4): the registered measures are the calendar-day ones.

Run from the repository root:
    ~/.venvs/nyc-concordance/bin/python analyses/critique/round5_night_of_check.py
Reads data/derived/round5/heat_night/{new_york,chicago}_daily.csv (written by the registered
run.py) and data/derived/graph/heat_mechanisms/mediators_daily.csv. Makes two Socrata queries
(311 street-noise complaints created before 06:00, by date). Writes
data/derived/round5/heat_night/night_of_check.json.
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from analyses.graph import heat_mechanisms_city as HM  # noqa: E402
from analyses.heat import shootings as HS  # noqa: E402
from analyses.round2.hot_end import model as M  # noqa: E402
from concord import socrata  # noqa: E402

warnings.filterwarnings("ignore")
DER = ROOT / "data/derived/round5/heat_night"


def irr(d, y):
    r, _ = HS.nb_fit(f"{y} ~ t5 + C(dow) + C(month) + C(year) + hol + wet", d)
    return HS.irr(r, "t5")


def hot_end(d, y):
    import statsmodels.api as sm
    yy, X, sc, basis = M.design(d, y)
    r = sm.GLM(yy, X, family=sm.families.NegativeBinomial(alpha=M.nb_alpha(y, d))).fit(cov_type="HC0")
    x = M.cvec(basis, 33, 27)
    e, s = float(x @ r.params[sc].values), float(np.sqrt(x @ r.cov_params().loc[sc, sc].values @ x))
    return {"estimate": float(np.exp(e)), "lo": float(np.exp(e - 1.96 * s)), "hi": float(np.exp(e + 1.96 * s))}


def early_noise():
    """311 street-noise complaints created from 00:00 to 05:59, by calendar date."""
    out, srcs = {}, []
    for ds, a, b in (("76ig-c548", "2010-01-01", "2019-12-31"), ("erm2-nwe9", "2020-01-01", "2026-08-31")):
        rows, src = socrata.query_all(
            ds, select="date_trunc_ymd(created_date) as d, count(*) as n",
            where=f"complaint_type = 'Noise - Street/Sidewalk' and created_date between '{a}T00:00:00' and '{b}T23:59:59' "
                  "and date_extract_hh(created_date) < 6", group="d", order="d")
        srcs.append(src)
        out.update({pd.Timestamp(r["d"]): int(r["n"]) for r in rows})
    return pd.Series(out).sort_index(), srcs


def cubic_hot_end(m, ny):
    """Rise in shootings from 27 to 33 C with the 4-df cubic spline of heat-mech-outdoors, all days from 2006."""
    a = m.copy()
    a["shootings"] = a["n"]
    b = m.loc[:"2026-08-30"].copy()
    b["shootings"] = ny["n"].reindex(b.index).values
    return {"calendar_day": HM.first_link(a, "shootings")[0]["rr_33_vs_27"],
            "night_of": HM.first_link(b, "shootings")[0]["rr_33_vs_27"]}


def att(d, **kw):
    r = HM.attenuation(d, "noise_street", **kw)
    return {k: r.get(k) for k in ("n_days", "attenuation", "attenuation_lo", "attenuation_hi", "base_irr_per_5C",
                                  "adjusted_irr_per_5C", "mediator_coef_log1p")}


def main():
    res = {"note": "Exploratory, run after the outcomes; decides no verdict (rule 4)."}
    for city in ("new_york", "chicago"):
        d = pd.read_csv(DER / f"{city}_daily.csv", index_col=0, parse_dates=True).dropna(subset=["TMAX"])
        d["t5"] = d["TMAX"] / 5
        res[city] = {"n_days": int(len(d)), "calendar_incidents": int(d["n_cal"].sum()), "night_of_incidents": int(d["n"].sum()),
                     "share_00_06": float(d["n_00_06"].sum() / d["n"].sum()),
                     "irr_per_5c_calendar_day": irr(d, "n_cal"), "irr_per_5c_night_of": irr(d, "n"),
                     "rr_33_vs_27_calendar_day": hot_end(d, "n_cal"), "rr_33_vs_27_night_of": hot_end(d, "n")}
        print(city, json.dumps(res[city], indent=1))

    m = pd.read_csv(ROOT / "data/derived/graph/heat_mechanisms/mediators_daily.csv", index_col=0, parse_dates=True)
    ny = pd.read_csv(DER / "new_york_daily.csv", index_col=0, parse_dates=True)
    res["new_york"]["rr_33_vs_27_cubic_spline"] = cubic_hot_end(m, ny)
    m = m.dropna(subset=["noise_street"])
    out = {"as_registered": att(m, boot=HM.NBOOT)}
    k = m.loc[:"2026-08-30"].copy()
    k["n"] = ny["n"].reindex(k.index).values
    out["shootings_night_of"] = att(k, boot=HM.NBOOT)
    out["shootings_night_of_year_by_month"] = att(k, controls=HM.CONTROLS_YM, boot=HM.NBOOT)
    try:
        early, srcs = early_noise()
        e = early.reindex(pd.date_range("2010-01-01", "2026-08-31", freq="D")).fillna(0)
        k2 = k.copy()
        k2["noise_street"] = (k2["noise_street"] - e.reindex(k2.index).values + e.shift(-1).reindex(k2.index).values)
        out["early_noise_share"] = float(e.loc[k.index].sum() / k["noise_street"].sum())
        out["both_night_of"] = att(k2, boot=HM.NBOOT)
        out["both_night_of_year_by_month"] = att(k2, controls=HM.CONTROLS_YM, boot=HM.NBOOT)
        fl, _ = HM.first_link(k2, "noise_street")
        out["both_night_of_first_link_irr"] = fl["irr_per_5C"]
        out["sources"] = srcs
    except Exception as ex:  # the complaint shift is reported as not done if the query fails
        out["both_night_of"] = {"not_done": str(ex)[:300]}
    res["heat_mech_outdoors"] = out
    print(json.dumps({k_: v for k_, v in out.items() if k_ != "sources"}, indent=1))
    (DER / "night_of_check.json").write_text(json.dumps(res, indent=1, default=str))


if __name__ == "__main__":
    main()
