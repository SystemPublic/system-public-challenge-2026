"""Heat and shootings inside against outside (claim heat-inside-outside-2006).

Usage: python -m analyses.heat_inside.test_2006
Committed with the registration, before the dated counts by location are fetched (rule 9).

Data. NYPD shooting incidents with LOC_OF_OCCUR_DESC (INSIDE or OUTSIDE), which 5ucz-vwe8 fills for every year from 2006:
833y-fsy8 (historic) and 5ucz-vwe8 (year to date). Distinct incident keys by date and location.
Weather and calendar terms come from data/derived/heat/shootings_daily.csv (Central Park, GHCN-Daily).
Primary model. Binomial regression of the number of inside incidents out of all located incidents on a day,
on t5 (daily maximum / 5 C), day of week, year, month, holiday and wet day; robust (HC1) errors.
exp(coefficient of t5) is the ratio of the inside to the outside rate ratio per 5 C.
Secondary. Poisson regressions of the inside and the outside daily counts on the same terms.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from concord import socrata  # noqa: E402

OUT = ROOT / "data" / "derived" / "heat_inside_2006"


def fetch() -> tuple[pd.DataFrame, list]:
    frames, srcs = [], []
    for ds in ("833y-fsy8", "5ucz-vwe8"):
        rows, src = socrata.query_all(ds, select="date_trunc_ymd(occur_date) as d, loc_of_occur_desc as loc, count(distinct incident_key) as n",
                                      where="occur_date >= '2006-01-01T00:00:00' and loc_of_occur_desc in ('INSIDE','OUTSIDE')",
                                      group="d, loc", order="d, loc")
        f = pd.DataFrame(rows)
        if len(f):
            f["ds"] = ds
            frames.append(f)
        srcs.append(src)
    f = pd.concat(frames)
    f["d"] = pd.to_datetime(f.d.str[:10])
    f["n"] = f.n.astype(int)
    f = f.sort_values("ds", ascending=False).drop_duplicates(["d", "loc"])  # historic file wins where both have a date
    w = f.pivot(index="d", columns="loc", values="n").fillna(0)
    return w, srcs


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    w, srcs = fetch()
    cov = pd.read_csv(ROOT / "data/derived/heat/shootings_daily.csv", parse_dates=["date"]).set_index("date")
    d = cov.loc["2006-01-01":, ["t5", "dow", "month", "year", "hol", "wet"]].join(w).dropna(subset=["t5"])
    d = d.loc[:w.index.max()]
    d[["INSIDE", "OUTSIDE"]] = d[["INSIDE", "OUTSIDE"]].fillna(0)
    d.to_csv(OUT / "daily.csv")
    rhs = "t5 + C(dow) + C(year) + C(month) + hol + wet"
    dd = d[(d.INSIDE + d.OUTSIDE) > 0].copy()
    dd["share"] = dd.INSIDE / (dd.INSIDE + dd.OUTSIDE)
    b = smf.glm(f"share ~ {rhs}", dd, family=sm.families.Binomial(), freq_weights=(dd.INSIDE + dd.OUTSIDE)).fit(cov_type="HC1")

    def ci(m, k="t5"):
        e, se = m.params[k], m.bse[k]
        return {"estimate": float(np.exp(e)), "lo": float(np.exp(e - 1.96 * se)), "hi": float(np.exp(e + 1.96 * se)), "se_log": float(se)}

    res = {"ratio_inside_to_outside": ci(b), "n_days": int(len(d)), "inside": int(d.INSIDE.sum()), "outside": int(d.OUTSIDE.sum()),
           "first": str(d.index.min().date()), "last": str(d.index.max().date())}
    for k in ("INSIDE", "OUTSIDE"):
        m = smf.glm(f"{k} ~ {rhs}", d, family=sm.families.Poisson()).fit(cov_type="HC1")
        res[k.lower() + "_irr_per_5c"] = ci(m)
    (OUT / "results.json").write_text(json.dumps(res, indent=1))
    (OUT / "sources.json").write_text(json.dumps(srcs, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
