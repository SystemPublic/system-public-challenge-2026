"""Heat and shootings inside against outside in Chicago (claim transfer-chicago-inside-outside).

Usage: python -m analyses.heat_inside.test_chicago
Committed with the registration, before the dated counts by location are fetched (rule 9).

Data. Chicago "Violence Reduction - Victims of Homicides and Non-Fatal Shootings" (gumc-mgzr), gunshot victims,
2010-01-01 to 2026-08-31, distinct case numbers by date and location_description. Weather and calendar terms
come from data/derived/graph/transfer_chicago/chicago_heat_daily.csv (built for transfer-chicago-heat-shootings).
Location classes, fixed before any dated count was seen:
  inside   description matches INSIDE_RX
  outside  description matches OUTSIDE_RX and not INSIDE_RX
  excluded everything else (vehicles, transit property, unclassified, blank)
Primary model. Quasi-binomial regression of the daily count of inside incidents out of inside plus outside on t5
(daily maximum / 5 C), day of week, year, month, holiday and wet day; the scale is the Pearson chi-square, so the
errors allow overdispersion with the day as the unit. exp(coefficient of t5) is the ratio of the inside to the
outside rate ratio per 5 C. Secondary: Poisson slopes for each class with HC1 errors, and the primary model with
PORCH moved to excluded.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import concord.socrata as soc  # noqa: E402

soc.DOMAIN = "https://data.cityofchicago.org"
OUT = ROOT / "data" / "derived" / "heat_inside_chicago"
INSIDE_RX = re.compile(r"APARTMENT|HOUSE|RESIDENCE|HALLWAY|BASEMENT|VESTIBULE|STAIRWELL|LOBBY|STORE|RESTAURANT|TAVERN|\bBAR\b|SHOP|SALON|OFFICE|CLUB|HOTEL|MOTEL|HOSPITAL|GARAGE|BUILDING|LAUNDRY|ELEVATOR|ROOM|BANK|CHURCH|LIBRARY|NURSING")
OUTSIDE_RX = re.compile(r"STREET|ALLEY|SIDEWALK|PORCH|YARD|PARKING LOT|PARK PROPERTY|VACANT LOT|GROUNDS|GAS STATION|GANGWAY|DRIVEWAY|RAILROAD|BRIDGE|HIGHWAY|EXPRESSWAY|LAKEFRONT|FOREST PRESERVE|PLAYGROUND|CONSTRUCTION SITE")
RHS = "t5 + C(dow) + C(year) + C(month) + hol + wet"


def classify(desc: str | None, porch_out: bool = True) -> str:
    d = (desc or "").upper()
    if not porch_out and "PORCH" in d:
        return "excluded"
    if INSIDE_RX.search(d):
        return "inside"
    if OUTSIDE_RX.search(d):
        return "outside"
    return "excluded"


def ci(m, k="t5"):
    e, se = m.params[k], m.bse[k]
    return {"estimate": float(np.exp(e)), "lo": float(np.exp(e - 1.96 * se)), "hi": float(np.exp(e + 1.96 * se)), "se_log": float(se)}


def ratio(d: pd.DataFrame) -> dict:
    dd = d[(d.inside + d.outside) > 0]
    y = np.column_stack([dd.inside, dd.outside])
    X = smf.glm(f"inside ~ {RHS}", dd, family=sm.families.Poisson()).fit().model.exog
    m = sm.GLM(y, X, family=sm.families.Binomial()).fit(scale="X2")
    names = smf.glm(f"inside ~ {RHS}", dd, family=sm.families.Poisson()).fit().model.exog_names
    i = names.index("t5")
    e, se = m.params[i], m.bse[i]
    return {"estimate": float(np.exp(e)), "lo": float(np.exp(e - 1.96 * se)), "hi": float(np.exp(e + 1.96 * se)), "se_log": float(se), "dispersion": float(m.scale)}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows, src = soc.query_all("gumc-mgzr", select="date_trunc_ymd(date) as d, location_description as loc, count(distinct case_number) as n",
                              where="date between '2010-01-01T00:00:00' and '2026-08-31T23:59:59' AND gunshot_injury_i in ('Y','YES')",
                              group="d, loc", order="d, loc")
    f = pd.DataFrame(rows)
    f["d"] = pd.to_datetime(f.d.str[:10])
    f["n"] = f.n.astype(int)
    f["loc"] = f.get("loc")
    cov = pd.read_csv(ROOT / "data/derived/graph/transfer_chicago/chicago_heat_daily.csv", parse_dates=["date"]).set_index("date")[["t5", "dow", "month", "year", "hol", "wet"]]
    res = {"classes": f.assign(c=f["loc"].map(classify)).groupby("c").n.sum().to_dict(),
           "descriptions": {c: g.groupby("loc").n.sum().sort_values(ascending=False).head(12).to_dict() for c, g in f.assign(c=f["loc"].map(classify)).fillna({"loc": "(blank)"}).groupby("c")}}
    for label, porch_out in (("primary", True), ("porch_excluded", False)):
        g = f.assign(c=f["loc"].map(lambda s: classify(s, porch_out)))
        w = g[g.c != "excluded"].pivot_table(index="d", columns="c", values="n", aggfunc="sum").fillna(0)
        d = cov.join(w).dropna(subset=["t5"])
        d[["inside", "outside"]] = d[["inside", "outside"]].fillna(0)
        r = {"ratio_inside_to_outside": ratio(d), "n_days": int(len(d)), "inside": int(d.inside.sum()), "outside": int(d.outside.sum())}
        for k in ("inside", "outside"):
            r[k + "_irr_per_5c"] = ci(smf.glm(f"{k} ~ {RHS}", d, family=sm.families.Poisson()).fit(cov_type="HC1"))
        res[label] = r
        if label == "primary":
            d.to_csv(OUT / "daily.csv")
    (OUT / "results.json").write_text(json.dumps(res, indent=1))
    (OUT / "sources.json").write_text(json.dumps([src], indent=1))
    print(json.dumps({k: res[k] for k in ("classes", "primary", "porch_excluded")}, indent=1))


if __name__ == "__main__":
    main()
