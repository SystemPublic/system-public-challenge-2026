"""Exploratory description for docs/affordability.md (not registered; no verdicts).
Reads the Furman panel, the registered classification (sba_table.csv), evictions and Zillow ZORI.
Writes data/derived/affordability/explore.json and sba_now.csv."""
import json, math, os, sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from gentrification_test import welch
D = ROOT / "data/derived/affordability"
p = pd.read_csv(D / "furman_panel.csv", dtype={"region_id": str, "year": str})
s = pd.read_csv(D / "sba_table.csv", dtype={"region_id": str}).set_index("region_id")
sb = p[p.region_type == "Sub-Borough Area"]; city = p[p.region_type == "City"].set_index("year"); cd = p[p.region_type == "Community District"]
def m(col, years, df=sb): return df[df.year.isin(years)].groupby("region_id")[col].mean()
def cm(col, years): return float(city.loc[[y for y in years if y in city.index], col].mean())
out = {}

# 1. affordability now
END = ["2022", "2023", "2024"]; Y10 = ["2009", "2010", "2011"]
now = pd.DataFrame({"name": s.name, "rent": m("rent_gross_med_adj", END), "rent_recent": m("rent_gross_recent_med_adj", ["2020-2024"]),
                    "income": m("hh_inc_med_adj", END), "renter_income": m("hh_inc_rent_med_adj", END),
                    "burden_med": m("rent_burden_med", END), "burden_30_50": m("rent_burden_mod_pct", END), "burden_50": m("rent_burden_sev_pct", ["2020-2024"]),
                    "lowinc_30_50": m("rburden_mod_ami_le80", ["2020-2024"]), "lowinc_50": m("rburden_sev_ami_le80", ["2020-2024"]),
                    "rent10": m("rent_gross_med_adj", Y10), "rent_recent10": m("rent_gross_recent_med_adj", ["2006-2010"]),
                    "burden_med10": m("rent_burden_med", Y10), "burden_med00": m("rent_burden_med", ["2000"]), "income10": m("hh_inc_med_adj", Y10)})
now["rent_to_local_income"] = now.rent * 12 / now.income * 100
now["recent_rent_to_city_income"] = now.rent_recent * 12 / cm("hh_inc_med_adj", END) * 100
now["group"] = np.where(~s.low_start, "other 33", np.where(s.gent, "gentrified", "low start, not gentrified"))
now.reset_index().to_csv(D / "sba_now.csv", index=False)
inc_now, inc10 = cm("hh_inc_med_adj", END), cm("hh_inc_med_adj", Y10)
def count(rent, inc): 
    t = 0.30 * inc / 12
    return {"budget_at_median": t, "n_at_median": int((rent <= t).sum()), "budget_at_half": t / 2, "n_at_half": int((rent <= t / 2).sum()),
            "names_not_affordable_at_median": sorted(s.name[rent.index[rent > t]])}
out["affordability"] = {
    "city_income_2009_11": inc10, "city_income_2022_24": inc_now,
    "city": {k: {y: cm(k, yy) for y, yy in [("2000", ["2000"]), ("2009-11", Y10), ("2022-24", END)]} for k in ["rent_gross_med_adj", "hh_inc_med_adj", "rent_burden_med", "rent_burden_mod_pct"]},
    "city_recent_rent": {"2006-2010": float(city.loc["2006-2010", "rent_gross_recent_med_adj"]) if "2006-2010" in city.index and not math.isnan(city.loc["2006-2010", "rent_gross_recent_med_adj"]) else cm("rent_gross_recent_med_adj", ["2008"]),
                         "2020-2024": float(city.loc["2020-2024", "rent_gross_recent_med_adj"]) if "2020-2024" in city.index and not math.isnan(city.loc["2020-2024", "rent_gross_recent_med_adj"]) else cm("rent_gross_recent_med_adj", ["2022"])},
    "all_tenants_2009_11": count(now.rent10, inc10), "all_tenants_2022_24": count(now.rent, inc_now),
    "recent_movers_2006_10": count(now.rent_recent10, cm("hh_inc_med_adj", ["2006", "2007", "2008", "2009", "2010"])),
    "recent_movers_2020_24": count(now.rent_recent, cm("hh_inc_med_adj", ["2021", "2022", "2023", "2024"])),
    "burden_med_range_now": [float(now.burden_med.min()), float(now.burden_med.max())],
    "highest_burden": now.sort_values("burden_med", ascending=False).head(8)[["name", "burden_med", "rent", "income"]].round(1).values.tolist(),
    "lowest_burden": now.sort_values("burden_med").head(8)[["name", "burden_med", "rent", "income"]].round(1).values.tolist(),
    "n_sba_burden_over_30_now": int((now.burden_med > 30).sum()), "n_sba_burden_over_30_2000": int((now.burden_med00 > 30).sum()),
    "spearman_burden_income": float(now[["burden_med", "income"]].corr(method="spearman").iloc[0, 1]),
    "spearman_burden_rent": float(now[["burden_med", "rent"]].corr(method="spearman").iloc[0, 1])}

# ZORI (asking rents by ZIP, nominal dollars); 2015 dollars are raised to 2024 dollars with the national CPI-U ratio 313.689/237.017
z = pd.read_csv(os.path.expanduser("~/opt/nyc-concordance/affordability/zillow/Zip_zori.csv"))
z = z[(z.State == "NY") & (z.City == "New York")]
dates = [c for c in z.columns if c[:2] == "20"]
last12 = dates[-12:]; y15 = [c for c in dates if c.startswith("2015")]
zz = pd.DataFrame({"zip": z.RegionName, "county": z.CountyName, "now": z[last12].mean(axis=1, skipna=True), "n_now": z[last12].notna().sum(axis=1),
                   "y15": z[y15].mean(axis=1, skipna=True) * 313.689 / 237.017, "n15": z[y15].notna().sum(axis=1)})
zz.to_csv(D / "zori_zip.csv", index=False)
a = zz[zz.n_now >= 6]; b = zz[(zz.n15 >= 6) & (zz.n_now >= 6)]
t_now = 0.30 * cm("hh_inc_med_adj", ["2024"]) / 12; t15 = 0.30 * cm("hh_inc_med_adj", ["2015"]) / 12
out["zori"] = {"last_month": dates[-1], "window_now": [last12[0], last12[-1]], "n_zip_now": len(a), "median_asking_now": float(a.now.median()),
               "budget_now": t_now, "n_at_median_now": int((a.now <= t_now).sum()), "n_at_half_now": int((a.now <= t_now / 2).sum()),
               "min_asking_now": float(a.now.min()), "cheapest": a.sort_values("now").head(6)[["zip", "county", "now"]].round(0).values.tolist(),
               "same_zips": {"n": len(b), "budget_2015": t15, "n_at_median_2015": int((b.y15 <= t15).sum()), "n_at_median_now": int((b.now <= t_now).sum()),
                             "median_2015_in_2024_dollars": float(b.y15.median()), "median_now": float(b.now.median())},
               "note": "Zillow Observed Rent Index, all homes and multifamily, smoothed; nominal dollars. 2015 values multiplied by 1.3235 (national CPI-U, 2015 to 2024). The income is the 2024 city median; the rents are later, so the count for now is slightly too favourable to rents if incomes rose since."}

# 2. outcomes by group among the 22 low-start areas
low = s[s.low_start]; g, ng = low.index[low.gent], low.index[~low.gent]
ev = pd.read_csv(D / "evictions_sba_year.csv", dtype={"sba": str, "yr": str})
renters = m("unit_num", END) * (1 - m("unit_occ_own_pct", END) / 100)
def evr(years): return ev[ev.yr.isin(years)].groupby("sba").n.sum() / len(years) / renters * 1000
# crime: community district to SBA (simple mean of the merged districts)
CD2SBA = {"101": "101", "102": "101", "103": "102", "104": "103", "105": "103", "106": "104", "107": "105", "108": "106", "109": "107", "110": "108", "111": "109", "112": "110",
          "201": "201", "202": "201", "203": "202", "206": "202", "204": "203", "205": "204", "207": "205", "208": "206", "209": "207", "210": "208", "211": "209", "212": "210"}
cd = cd.assign(sba=[CD2SBA.get(r, r) for r in cd.region_id])
def cdm(col, years): return cd[cd.year.isin(years)].groupby("sba")[col].mean()
ch = pd.DataFrame({
    "real median household income, % change 2000 to 2022-24": (m("hh_inc_med_adj", END) / m("hh_inc_med_adj", ["2000"]) - 1) * 100,
    "real median renter income, % change 2006-08 to 2022-24": (m("hh_inc_rent_med_adj", END) / m("hh_inc_rent_med_adj", ["2006", "2007", "2008"]) - 1) * 100,
    "real median gross rent, % change 2000 to 2022-24": (m("rent_gross_med_adj", END) / m("rent_gross_med_adj", ["2000"]) - 1) * 100,
    "recent-mover rent, % change 2006-10 to 2020-24": (m("rent_gross_recent_med_adj", ["2020-2024"]) / m("rent_gross_recent_med_adj", ["2006-2010"]) - 1) * 100,
    "poverty rate, change in points 2000 to 2022-24": m("pop_pov_pct", END) - m("pop_pov_pct", ["2000"]),
    "poor residents, % change 2000 to 2022-24": (s.poor_end / s.poor00 - 1) * 100,
    "population, % change 2000 to 2022-24": (s.pop_end / s.pop00 - 1) * 100,
    "college share, change in points 2000 to 2022-24": s.coll_change,
    "white share, change in points 2000 to 2022-24": m("pop_race_white_pct", END) - m("pop_race_white_pct", ["2000"]),
    "black share, change in points 2000 to 2022-24": m("pop_race_black_pct", END) - m("pop_race_black_pct", ["2000"]),
    "hispanic share, change in points 2000 to 2022-24": m("pop_race_hisp_pct", END) - m("pop_race_hisp_pct", ["2000"]),
    "born in New York State, change in points 2005-07 to 2022-24": m("pop_bornstate_pct", END) - m("pop_bornstate_pct", ["2005", "2006", "2007"]),
    "median rent burden, change in points 2000 to 2022-24": m("rent_burden_med", END) - m("rent_burden_med", ["2000"]),
    "low-income renters paying 30-50%, change in points 2005-09 to 2020-24": m("rburden_mod_ami_le80", ["2020-2024"]) - m("rburden_mod_ami_le80", ["2005-2009"]),
    "low-income renters paying over 50%, change in points 2005-09 to 2020-24": m("rburden_sev_ami_le80", ["2020-2024"]) - m("rburden_sev_ami_le80", ["2005-2009"]),
    "all renters paying over 50%, change in points 2000 to 2020-24": m("rent_burden_sev_pct", ["2020-2024"]) - m("rent_burden_sev_pct", ["2000"]),
    "eviction filings per 100 private rentals, 2010-12": m("priv_evic_filing_rt", ["2010", "2011", "2012"]),
    "eviction filings per 100 private rentals, 2023-25": m("priv_evic_filing_rt", ["2023", "2024", "2025"]),
    "eviction filings, % change 2010-12 to 2023-25": (m("priv_evic_filing_rt", ["2023", "2024", "2025"]) / m("priv_evic_filing_rt", ["2010", "2011", "2012"]) - 1) * 100,
    "executed evictions per 1,000 renter households a year, 2017-19": evr(["2017", "2018", "2019"]),
    "executed evictions per 1,000 renter households a year, 2023-25": evr(["2023", "2024", "2025"]),
    "serious crimes per 1,000 residents, 2006-08": cdm("crime_all_rt", ["2006", "2007", "2008"]),
    "serious crimes per 1,000 residents, 2023-25": cdm("crime_all_rt", ["2023", "2024", "2025"]),
    "serious crime rate, % change 2006-08 to 2023-25": (cdm("crime_all_rt", ["2023", "2024", "2025"]) / cdm("crime_all_rt", ["2006", "2007", "2008"]) - 1) * 100,
    "violent crime rate, % change 2006-08 to 2023-25": (cdm("crime_viol_rt", ["2023", "2024", "2025"]) / cdm("crime_viol_rt", ["2006", "2007", "2008"]) - 1) * 100,
    "serious housing code violations per 1,000 rentals, % change 2006-08 to 2023-25": (cdm("serious_viol_rate", ["2023", "2024", "2025"]) / cdm("serious_viol_rate", ["2006", "2007", "2008"]) - 1) * 100,
    "house price index (2000 = 100), 2025": cdm("hpi_al", ["2025"]),
    "share of rentals in public housing, 2025 (%)": m("rent_pct_nycha", ["2025"]),
    "share of rentals rent-stabilised, 2025 (%)": cdm("rs_unit_share", ["2025"]),
})
ch.assign(name=s.name, group=now.group).reset_index().to_csv(D / "sba_changes.csv", index=False)
rows = {}
oth = s.index[~s.low_start]
for c in ch.columns:
    w = welch(ch.loc[g, c].dropna(), ch.loc[ng, c].dropna())
    rows[c] = {"gentrified_mean": w["mean_a"], "not_gentrified_mean": w["mean_b"], "diff": w["diff"], "lo": w["lo"], "hi": w["hi"],
               "other_33_mean": float(ch.loc[oth, c].mean()), "n": [w["n_a"], w["n_b"]]}
out["outcomes_by_group"] = rows
# 3. where the poor count rose
dp = (s.poor_end - s.poor00).sort_values()
out["poor_count"] = {"largest_falls": [[s.name[i], round(float(dp[i]))] for i in dp.index[:10]], "largest_rises": [[s.name[i], round(float(dp[i]))] for i in dp.index[::-1][:10]],
                     "n_sba_rise": int((dp > 0).sum()), "sum_rises": float(dp[dp > 0].sum()), "sum_falls": float(dp[dp < 0].sum()),
                     "fall_in_gentrified": float(dp[g].sum()), "spearman_rent_growth_vs_log_poor_change_55": float(pd.Series(np.log(s.poor_end / s.poor00)).corr(s.rent_growth, method="spearman")),
                     "spearman_low_start_22": float(pd.Series(np.log(low.poor_end / low.poor00)).corr(low.rent_growth, method="spearman"))}
# 4. rank mobility
out["rank"] = {"moves_ge_15_up": sorted(s.name[(s.rent_rank_end - s.rent_rank00) >= 15]), "moves_ge_10_down": sorted(s.name[(s.rent_rank_end - s.rent_rank00) <= -10]),
               "low_start_rank_changes": {s.name[i]: [int(s.rent_rank00[i]), int(s.rent_rank_end[i])] for i in low.index}}
(D / "explore.json").write_text(json.dumps(out, indent=1, default=float))
print(json.dumps({k: out[k] for k in ("affordability", "zori", "poor_count", "rank")}, indent=1, default=float)[:7000])
for c, r in rows.items(): print(f"{c[:72]:72s} {r['gentrified_mean']:8.1f} {r['not_gentrified_mean']:8.1f} {r['diff']:7.1f} ({r['lo']:.1f} to {r['hi']:.1f})  other33 {r['other_33_mean']:.1f}")
