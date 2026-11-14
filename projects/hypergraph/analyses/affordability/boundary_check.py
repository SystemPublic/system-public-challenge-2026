"""Exploratory check, written after the outcome: the 2022 ACS moved to 2020 public-use microdata areas, and the
population of 28 of 55 sub-borough areas in the Furman file changes by more than 8% between 2021 and 2022.
Repeats both registered measures with the end period 2017-2019 (before the break) and reports the break itself.
Writes data/derived/affordability/boundary_check.json."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats
sys.path.insert(0, str(Path(__file__).resolve().parent))
from gentrification_test import welch
ROOT = Path(__file__).resolve().parents[2]; D = ROOT / "data/derived/affordability"
p = pd.read_csv(D / "furman_panel.csv", dtype={"region_id": str, "year": str})
s = pd.read_csv(D / "sba_table.csv", dtype={"region_id": str}).set_index("region_id")
q = p[p.region_type.isin(["Sub-Borough Area", "City"])]
def m(col, years): return q[q.year.isin(years)].groupby("region_id")[col].mean()
out = {}
pop = q[q.year.str.len() == 4].pivot(index="region_id", columns="year", values="pop_num").drop(index="606")
j22 = np.log(pop["2022"] / pop["2021"]); j12 = np.log(pop["2012"] / pop["2011"]); typ = np.log(pop["2018"] / pop["2017"])
out["break"] = {"n_abs_jump_over_8pct_2021_22": int((j22.abs() > 0.08).sum()), "n_2011_12": int((j12.abs() > 0.08).sum()), "n_2017_18": int((typ.abs() > 0.08).sum()),
                "largest_2021_22": {s.name[i]: round(float(np.expm1(j22[i]) * 100)) for i in j22.abs().sort_values().index[-10:]},
                "gentrified_2021_22": {s.name[i]: round(float(np.expm1(j22[i]) * 100)) for i in s.index[s.low_start & s.gent]}}
for tag, E in [("end_2017_19", ["2017", "2018", "2019"]), ("end_2019_2021", ["2018", "2019", "2021"])]:
    rg = m("rent_gross_med_adj", E) / m("rent_gross_med_adj", ["2000"]) - 1; cc = m("pop_edu_collp_pct", E) - m("pop_edu_collp_pct", ["2000"])
    gent = ((rg > rg["606"]) & (cc > cc["606"])).drop("606")
    low = s.index[s.low_start]
    poor = np.log(m("pop_pov_pct", E) * m("pop_num", E) / (m("pop_pov_pct", ["2000"]) * m("pop_num", ["2000"])))
    rho = stats.spearmanr(rg.drop("606"), cc.drop("606")).statistic
    g_reg, n_reg = s.index[s.low_start & s.gent], s.index[s.low_start & ~s.gent]
    g2, n2 = [i for i in low if gent[i]], [i for i in low if not gent[i]]
    pr = m("pop_pov_pct", E) - m("pop_pov_pct", ["2000"])
    out[tag] = {"k": int(gent[low].sum()), "gentrified": sorted(s.name[g2]), "changed_vs_registered": sorted(set(s.name[g2]) ^ set(s.name[g_reg])), "spearman": float(rho),
                "k_other_33": int(gent[s.index[~s.low_start]].sum()),
                "poor_count_registered_groups": welch(poor[g_reg], poor[n_reg]), "poor_count_groups_reclassified": welch(poor[g2], poor[n2]),
                "poverty_rate_points_registered_groups": welch(pr[g_reg], pr[n_reg]),
                "totals_pct": {"gentrified": float((np.exp(poor[g_reg]) * s.poor00[g_reg]).sum() / s.poor00[g_reg].sum() - 1) * 100,
                               "other_low": float((np.exp(poor[n_reg]) * s.poor00[n_reg]).sum() / s.poor00[n_reg].sum() - 1) * 100,
                               "other_33": float((np.exp(poor.drop("606")[~s.low_start]) * s.poor00[~s.low_start]).sum() / s.poor00[~s.low_start].sum() - 1) * 100}}
(D / "boundary_check.json").write_text(json.dumps(out, indent=1, default=float)); print(json.dumps(out, indent=1, default=float))
