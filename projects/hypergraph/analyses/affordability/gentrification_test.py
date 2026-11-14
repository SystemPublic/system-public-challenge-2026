"""Registered tests afford-gentrification-prevalence and afford-poor-count-shift.
Fixed before registration (PRECEDENCE rule 9). No resampling and no random numbers in the tests:
intervals are Wilson (proportions), Fisher z (Spearman) and Welch t (difference in means).

Input: data/derived/affordability/furman_panel.csv (built by build_panel.py from the NYU Furman Center
CoreData workbook dated 2026-05-05). Unit: the 55 sub-borough areas (SBA).

Run:  python analyses/affordability/gentrification_test.py            -> data/derived/affordability/gentrification_results.json
      python analyses/affordability/gentrification_test.py --simulate -> replaces every post-2000 value with noise
                                                                         (used before registration to test the code)
"""
import json, math, sys
from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats
ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "data/derived/affordability"
END = ["2022", "2023", "2024"]          # end period: mean of the three annual values
MID = ["2005", "2006", "2007"]          # separate baseline for the regression-to-the-mean check
N_LOW = 22                              # bottom 40% of 55

def wilson(k, n, z=1.959964):
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [c - h, c + h]

def load(simulate=False):
    p = pd.read_csv(D / "furman_panel.csv", dtype={"region_id": str, "year": str})
    p = p[p.region_type.isin(["Sub-Borough Area", "City"])].copy()
    if simulate:
        rng = np.random.default_rng(0); m = p.year != "2000"
        for c in p.columns[4:]:
            p.loc[m, c] = p.loc[m, c] * rng.lognormal(0.3, 0.3, m.sum())
    return p

def wide(p, col, years):
    q = p[p.year.isin(years)].groupby("region_id")[col].mean()
    return q

def table(p):
    names = p.drop_duplicates("region_id").set_index("region_id").region_name
    t = pd.DataFrame({"name": names})
    for col, tag in [("rent_gross_med_adj", "rent"), ("pop_edu_collp_pct", "coll"), ("hh_inc_med_adj", "inc"),
                     ("pop_pov_pct", "pov"), ("pop_num", "pop")]:
        t[tag + "00"] = wide(p, col, ["2000"]); t[tag + "_mid"] = wide(p, col, MID); t[tag + "_end"] = wide(p, col, END)
    t["lowinc_burden_0509"] = wide(p, "rburden_mod_ami_le80", ["2005-2009"])
    t["lowinc_burden_2024"] = wide(p, "rburden_mod_ami_le80", ["2020-2024"])
    t["poor00"] = t.pov00 / 100 * t.pop00; t["poor_end"] = t.pov_end / 100 * t.pop_end
    t["rent_growth"] = t.rent_end / t.rent00 - 1; t["coll_change"] = t.coll_end - t.coll00
    t["rent_growth_mid"] = t.rent_end / t.rent_mid - 1; t["coll_change_mid"] = t.coll_end - t.coll_mid
    return t

def classify(t, city="606"):
    c = t.loc[city]; s = t.drop(index=city).copy()
    s["rent_rank00"] = s.rent00.rank(method="min"); s["rent_rank_end"] = s.rent_end.rank(method="min")
    s["low_start"] = s.rent_rank00 <= N_LOW
    assert int(s.low_start.sum()) == N_LOW, "ties at the cut"
    s["inc_rank00"] = s.inc00.rank(method="min"); s["low_income_start"] = s.inc_rank00 <= N_LOW
    s["gent"] = (s.rent_growth > c.rent_growth) & (s.coll_change > c.coll_change)
    s["gent_mid"] = (s.rent_growth_mid > c.rent_growth_mid) & (s.coll_change_mid > c.coll_change_mid)
    return s, c

def welch(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float)
    d = a.mean() - b.mean(); va, vb = a.var(ddof=1) / len(a), b.var(ddof=1) / len(b); se = math.sqrt(va + vb)
    df = (va + vb) ** 2 / (va ** 2 / (len(a) - 1) + vb ** 2 / (len(b) - 1)); tq = stats.t.ppf(0.975, df)
    return {"diff": d, "lo": d - tq * se, "hi": d + tq * se, "se": se, "df": df, "n_a": len(a), "n_b": len(b),
            "mean_a": a.mean(), "mean_b": b.mean()}

def main(simulate=False):
    s, c = classify(table(load(simulate)))
    low = s[s.low_start]
    k = int(low.gent.sum()); k2 = int(low.gent_mid.sum())
    rho = stats.spearmanr(s.rent_growth, s.coll_change).statistic; n = len(s)
    z = math.atanh(rho); se = math.sqrt(1.06 / (n - 3)); rho_ci = [math.tanh(z - 1.959964 * se), math.tanh(z + 1.959964 * se)]
    if k >= 12 and k2 >= 11 and rho_ci[0] > 0: reading = "common"
    elif k <= 1 or rho_ci[1] < 0: reading = "myth"
    elif 4 <= k <= 11 and k2 >= 3 and rho_ci[0] > 0: reading = "real but a minority"
    else: reading = "undecided"
    verdict1 = {"real but a minority": "confirmed", "common": "contested", "myth": "contested", "undecided": "unsettled"}[reading]
    hi = s[~s.low_start]
    lowinc = s[s.low_income_start]
    r1 = {"n_sba": n, "n_low_start": N_LOW, "k": k, "k_wilson": wilson(k, N_LOW), "k2_mid_baseline": k2,
          "spearman_rent_growth_college_change": rho, "spearman_ci": rho_ci, "reading": reading, "verdict": verdict1,
          "city": {"rent_growth": c.rent_growth, "coll_change": c.coll_change, "rent_growth_mid": c.rent_growth_mid,
                   "coll_change_mid": c.coll_change_mid, "rent00": c.rent00, "rent_end": c.rent_end},
          "gentrified_low_start": sorted(low[low.gent].name), "not_gentrified_low_start": sorted(low[~low.gent].name),
          "secondary": {"k_among_other_33": int(hi.gent.sum()),
                        "k_low_income_start_definition": int(lowinc.gent.sum()),
                        "low_start_rent_faster_than_city": int((low.rent_growth > c.rent_growth).sum()),
                        "low_start_college_faster_than_city": int((low.coll_change > c.coll_change).sum()),
                        "low_start_now_in_top_half_of_rent": sorted(low[low.rent_rank_end >= n - 26].name),
                        "spearman_rent_rank_2000_vs_end": stats.spearmanr(s.rent00, s.rent_end).statistic}}
    # claim 2: poor count
    g, ng = low[low.gent], low[~low.gent]
    r2 = {"n_gent": len(g), "n_not": len(ng)}
    if len(g) < 3 or len(ng) < 3:
        r2["verdict"] = "no_test"
    else:
        dl = lambda x: np.log(x.poor_end / x.poor00)
        w = welch(dl(g), dl(ng)); r2["log_change_poor_count_gent_minus_not"] = w
        r2["verdict"] = "confirmed" if w["hi"] < 0 else "contested" if w["lo"] > 0 else "unsettled"
        r2["secondary_lowinc_rent_burden_change_pp"] = welch(g.lowinc_burden_2024 - g.lowinc_burden_0509, ng.lowinc_burden_2024 - ng.lowinc_burden_0509)
        tot = lambda x: {"poor00": float(x.poor00.sum()), "poor_end": float(x.poor_end.sum()), "pct": float(x.poor_end.sum() / x.poor00.sum() - 1) * 100,
                         "pop00": float(x.pop00.sum()), "pop_end": float(x.pop_end.sum())}
        r2["totals"] = {"gentrified_low_start": tot(g), "other_low_start": tot(ng), "other_33": tot(hi), "all_55": tot(s)}
    out = {"simulated": simulate, "claim1": r1, "claim2": r2}
    name = "gentrification_results_SIMULATED.json" if simulate else "gentrification_results.json"
    (D / name).write_text(json.dumps(out, indent=1, default=float))
    if not simulate:
        s.reset_index().to_csv(D / "sba_table.csv", index=False)
    print(json.dumps(out, indent=1, default=float)[:3000] if simulate else "written " + name)

if __name__ == "__main__":
    main("--simulate" in sys.argv)
