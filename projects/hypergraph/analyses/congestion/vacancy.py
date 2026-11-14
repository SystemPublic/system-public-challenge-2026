"""crz-storefront-vacancy: storefront vacancy on 31 December, zone against comparison areas.

Data: Storefronts Reported Vacant or Not (92iy-9c3n, Local Law 157 of 2019 registry). Each
reporting year gives the status of each ground- or second-floor storefront on 31 December of
that year (for the two-year labels, the first year: '2022 and 2023' is 31 December 2022).
Only the main annual filing of each year is used (the filing_due_date with the most rows).

  python -m analyses.congestion.vacancy design   years to 2024 only; writes vacancy_design.json
  python -m analyses.congestion.vacancy run      adds reporting year 2025 (31 December 2025)

Estimator: v(area, year) = share of storefronts with vacant_on_12_31 = YES among those
answering YES or NO. DiD = [v(zone, Y) - v(zone, Y-1)] - [v(comp, Y) - v(comp, Y-1)], in
percentage points. Interval: bootstrap over tax lots (bbl) within area, 2,000 draws, seed
20261113, percentile. The comparison pools the three outside areas (north, bklic, rest).
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

from concord import socrata
from analyses.congestion.common import DER, area_of_zip

SEED, DRAWS = 20261113, 2000
YEAR_OF = {"2019 and 2020": 2019, "2020 and 2021": 2020, "2021 and 2022": 2021, "2022 and 2023": 2022,
           "2023": 2023, "2024": 2024, "2025": 2025}


def fetch(labels):
    out, srcs = [], []
    for lab in labels:
        rows, src = socrata.query_all(
            "92iy-9c3n", select="reporting_year, filing_due_date, bbl, borough_block_lot, zip_code, vacant_on_12_31, primary_business_activity",
            where=f"reporting_year='{lab}'", order=":id")
        srcs.append(src)
        out += rows
    df = pd.DataFrame(out)
    df["year"] = df.reporting_year.map(YEAR_OF)
    main = df.groupby(["year", "filing_due_date"]).size().reset_index(name="n").sort_values("n").groupby("year").tail(1)
    df = df.merge(main[["year", "filing_due_date"]], on=["year", "filing_due_date"])
    df["lot"] = df.borough_block_lot.fillna(df.bbl)
    df["area"] = df.zip_code.map(area_of_zip)
    df = df[df.vacant_on_12_31.isin(["YES", "NO"])].copy()
    df["vac"] = (df.vacant_on_12_31 == "YES").astype(int)
    return df[["year", "lot", "zip_code", "area", "vac", "primary_business_activity"]], srcs


def rates(df):
    g = df.groupby(["year", "area"]).vac.agg(["mean", "size"]).reset_index()
    return g


def did(df, y, zone="crz", comp=("north", "bklic", "rest"), rng=None, draws=DRAWS):
    d = df[df.year.isin([y - 1, y])]
    lots = d.groupby(["area", "lot", "year"]).vac.agg(["sum", "size"]).unstack("year", fill_value=0)
    lots.columns = [f"{a}_{b}" for a, b in lots.columns]
    lots = lots.reset_index()
    lots["grp"] = np.where(lots.area == zone, "z", np.where(lots.area.isin(comp), "c", "x"))

    def est(t):
        o = {}
        for gname in ("z", "c"):
            s = t[t.grp == gname]
            o[gname] = (s[f"sum_{y}"].sum() / s[f"size_{y}"].sum()) - (s[f"sum_{y-1}"].sum() / s[f"size_{y-1}"].sum())
        return 100 * (o["z"] - o["c"]), 100 * o["z"], 100 * o["c"]
    e, ez, ec = est(lots)
    rng = rng or np.random.default_rng(SEED)
    zl, cl = lots[lots.grp == "z"], lots[lots.grp == "c"]
    cols = [f"sum_{y}", f"size_{y}", f"sum_{y-1}", f"size_{y-1}"]
    za, ca = zl[cols].to_numpy(float), cl[cols].to_numpy(float)
    bs = np.empty(draws)
    for i in range(draws):
        a = za[rng.integers(0, len(za), len(za))].sum(0)
        b = ca[rng.integers(0, len(ca), len(ca))].sum(0)
        bs[i] = 100 * ((a[0] / a[1] - a[2] / a[3]) - (b[0] / b[1] - b[2] / b[3]))
    return {"year": y, "did_points": e, "lo": float(np.quantile(bs, .025)), "hi": float(np.quantile(bs, .975)),
            "se": float(bs.std()), "zone_change": ez, "comp_change": ec, "n_zone_lots": int(len(zl)), "n_comp_lots": int(len(cl))}


def main(mode):
    labels = [k for k, v in YEAR_OF.items() if v <= (2024 if mode == "design" else 2025)]
    df, srcs = fetch(labels)
    r = rates(df)
    out = {"rates": r.to_dict("records"), "placebo_did": [did(df, y) for y in range(2020, 2025)]}
    for comp, nm in [(("north",), "north"), (("bklic",), "bklic"), (("rest",), "rest")]:
        out[f"placebo_did_{nm}"] = [did(df, y, comp=comp) for y in range(2022, 2025)]
    if mode == "run":
        out["did_2025"] = did(df, 2025)
        for comp, nm in [(("north",), "north"), (("bklic",), "bklic"), (("rest",), "rest")]:
            out[f"did_2025_{nm}"] = did(df, 2025, comp=comp)
        # restaurants and retail separately (exploratory)
        act = df.primary_business_activity.fillna("").str.upper()
        for nm, mask in [("food", act.str.contains("FOOD")), ("retail", act.str.contains("RETAIL"))]:
            pass
        r.to_csv(DER / "vacancy_rates.csv", index=False)
        (DER / "vacancy_sources.json").write_text(json.dumps(srcs, indent=1))
    (DER / f"vacancy_{'design' if mode == 'design' else 'results'}.json").write_text(json.dumps(out, indent=1, default=float))
    print(r.pivot(index="year", columns="area", values="mean").round(4).to_string())
    print(r.pivot(index="year", columns="area", values="size").to_string())
    for k, v in out.items():
        if k.startswith("placebo") or k.startswith("did"):
            for x in (v if isinstance(v, list) else [v]):
                print(k, x["year"], round(x["did_points"], 2), round(x["lo"], 2), round(x["hi"], 2), "se", round(x["se"], 2),
                      "zone", round(x["zone_change"], 2), "comp", round(x["comp_change"], 2))


if __name__ == "__main__":
    main(sys.argv[1])
