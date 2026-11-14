"""Power of the registered complaint test (restaurants-score-complaints), computed before any
restaurant-level 311 data are joined to inspection results.

Inputs are marginal counts only:
  - the exposure cohort from 43nn-pn8j: each restaurant's first Cycle Inspection / Initial
    Inspection from 2023-01-01 to 2025-06-30, its score band, and whether its BBL holds exactly
    one CAMIS in the live data (the linkage rule);
  - the yearly number of 311 Food Poisoning complaints (erm2-nwe9) with location type
    Restaurant/Bar/Deli/Bakery and a BBL, citywide, as an aggregate count.
The expected rate of linked complaints per restaurant-year is the yearly complaint count divided
by the number of restaurants inspected in 2023-2025, which assumes complaints fall on single-
restaurant BBLs in proportion to their share of restaurants. Overdispersion phi = 1.5 and 2.5 are
assumptions. var(log IRR) ~ phi * (1/E1 + 1/E0).
"""
from __future__ import annotations

import math

import pandas as pd

import common as c

BAND = (1.10, 1.60)  # literature-predicted IRR, not-A-range vs A-range initial score


def cohort():
    df, src = c.inspections("inspection_date between '2022-01-01' and '2026-12-31'", "live2022")
    ci = df[(df.itype == "Cycle Inspection / Initial Inspection") & df.score.notna()
            & (df.inspection_date >= "2023-01-01") & (df.inspection_date <= "2025-06-30")]
    first = ci.sort_values("inspection_date").groupby("camis").head(1).copy()
    bbl_n = df[df.bbl.notna() & (df.bbl.str.len() == 10)].groupby("bbl")["camis"].nunique()
    first["single_bbl"] = first.bbl.map(bbl_n).fillna(0).eq(1)
    first.attrs["n_open"] = int(df[(df.inspection_date >= "2023-01-01") & (df.inspection_date <= "2025-12-31")].camis.nunique())
    return first, src


def main():
    first, src = cohort()
    rows, src311 = c.socrata.query(c.SR311, select="date_extract_y(created_date) as y, count(*) as n",
                                   where="complaint_type='Food Poisoning' and location_type='Restaurant/Bar/Deli/Bakery' "
                                         "and bbl is not null and created_date between '2023-01-01' and '2025-12-31'",
                                   group="y", order="y")
    per_year = sum(int(r["n"]) for r in rows) / len(rows)
    n_open = first.attrs["n_open"]  # restaurants inspected in 2023-2025, the denominator of the rate
    lam = per_year / n_open
    lin = first[first.single_bbl]
    out = {"cohort_restaurants": int(len(first)), "restaurants_inspected_2023_2025": n_open, "single_bbl_restaurants": int(len(lin)),
           "share_not_A": round(float((lin.score >= 14).mean()), 3), "share_C": round(float((lin.score >= 28).mean()), 3),
           "fp_complaints_with_bbl_per_year": round(per_year, 1), "rate_per_restaurant_year": round(lam, 4),
           "band": BAND}
    E = len(lin) * lam  # one-year window
    for contrast, share in (("notA_vs_A", out["share_not_A"]), ("C_vs_A", out["share_C"])):
        e1 = E * share
        e0 = E * (1 - out["share_not_A"]) if contrast == "C_vs_A" else E * (1 - share)
        for phi in (1.5, 2.5):
            se = math.sqrt(phi * (1 / e1 + 1 / e0))
            mid = math.sqrt(BAND[0] * BAND[1])
            out[f"{contrast}_phi{phi}"] = {
                "expected_events_exposed": round(e1, 1), "expected_events_reference": round(e0, 1),
                "se_log_irr": round(se, 3), "half_width_ratio": round(math.exp(1.96 * se), 3),
                "z_if_mid_true": round(math.log(mid) / se, 2), "z_if_low_true": round(math.log(BAND[0]) / se, 2),
                # rule 8 style: D for an estimate at the band midpoint, chain = midpoint, null = 1
                "D_if_mid_true": round((math.log(mid) / se) ** 2, 2),
                "power_lower_bound_gt_1_if_mid": round(_phi_cdf(math.log(mid) / se - 1.96), 3),
            }
    out["sources"] = [src, src311]
    c.write_json("power_complaints.json", out)
    print(pd.Series({k: v for k, v in out.items() if k != "sources"}).to_string())


def _phi_cdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


if __name__ == "__main__":
    main()
