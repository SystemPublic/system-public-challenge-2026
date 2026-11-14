"""Clean the external UK context datasets into tidy tables.
Outputs:
  data/la_context.csv    one row per English local authority district (damp, hazards, fuel poverty,
                         deprivation, EPC energy/CO2/bills and F-G share, child asthma admissions, winter mortality)
  data/lsoa_context.csv  one row per LSOA (IMD + living-environment/indoors scores, fuel poverty) for maps
  data/external_sources.csv  provenance for every column
"""
import warnings
import pandas as pd
warnings.filterwarnings("ignore")
R = "external/raw/"

def ehs(sheet, col):
    d = pd.read_excel(R + "ehs_la_stock_condition_2023.ods", sheet_name=sheet, header=None, skiprows=4)
    d = d.iloc[:, :5]; d.columns = ["lad_code", "lad_name", "homes", "n", col]
    d = d[d.lad_code.astype(str).str.match(r"E0[6-9]")]
    return d[["lad_code", "lad_name", col]].assign(**{col: lambda x: pd.to_numeric(x[col], errors="coerce")})

la = ehs("AT1_7", "damp_pct_ehs2023").merge(ehs("AT1_4", "cat1_hazard_pct_ehs2023")[["lad_code", "cat1_hazard_pct_ehs2023"]], on="lad_code", how="outer") \
        .merge(ehs("AT1_1", "non_decent_pct_ehs2023")[["lad_code", "non_decent_pct_ehs2023"]], on="lad_code", how="outer")

fp = pd.read_excel(R + "fuel_poverty_subregional_2026.xlsx", sheet_name="Table 2", header=None, skiprows=3).iloc[:, [0, 4, 6]]
fp.columns = ["lad_code", "households", "fuel_poverty_pct_2024"]
fp = fp[fp.lad_code.astype(str).str.match(r"E0[6-9]")]
la = la.merge(fp, on="lad_code", how="outer")

iod = pd.read_csv(R + "iod2025_file7_lsoa.csv")
c = {k: [x for x in iod.columns if x.startswith(k)][0] for k in
     ["LSOA code", "LSOA name", "Local Authority District code", "Local Authority District name",
      "Index of Multiple Deprivation (IMD) Score", "Index of Multiple Deprivation (IMD) Decile",
      "Living Environment Score", "Indoors Sub-domain Score", "Income Deprivation Affecting Children Index (IDACI) Score", "Total population"]}
lsoa = iod[list(c.values())].copy(); lsoa.columns = ["lsoa_code", "lsoa_name", "lad_code", "lad_name", "imd_score", "imd_decile",
                                                  "living_env_score", "indoors_subdomain_score", "idaci_score", "population"]
fpl = pd.read_excel(R + "fuel_poverty_subregional_2026.xlsx", sheet_name="Table 4", header=None, skiprows=3)
fpl = fpl.iloc[:, [0, fpl.shape[1] - 1]]; fpl.columns = ["lsoa_code", "fuel_poverty_pct_2024"]
lsoa = lsoa.merge(fpl, on="lsoa_code", how="left")
lsoa.to_csv("data/lsoa_context.csv", index=False)
w = lambda g, col: (g[col] * g.population).sum() / g.population.sum()
agg = lsoa.groupby("lad_code").apply(lambda g: pd.Series({
    "imd_score_popweighted": w(g, "imd_score"),
    "living_env_score_popweighted": w(g, "living_env_score"),
    "indoors_subdomain_popweighted": w(g, "indoors_subdomain_score"),
    "pct_lsoas_most_deprived_decile": (g.imd_decile == 1).mean() * 100,
    "population_2022": g.population.sum(), "lad_name_iod": g.lad_name.iloc[0]})).reset_index()
la = la.merge(agg, on="lad_code", how="outer")
la["lad_name"] = la.lad_name.fillna(la.lad_name_iod); la = la.drop(columns="lad_name_iod")

def epc(fname, sheet):
    d = pd.read_excel(R + fname, sheet_name=sheet, header=3)
    code = [x for x in d.columns if "Local Authority Code" in str(x)][0]
    d = d.rename(columns={code: "lad_code"})
    q = sorted(d.Quarter.dropna().astype(str).unique())[-8:]          # last 8 quarters = ~2 years of certificates
    return d[d.Quarter.astype(str).isin(q)], q
e1, q1 = epc("epc_eb1_existing_dwellings.ods", "EB1_by_LA")
b = e1.groupby("lad_code")[["A", "B", "C", "D", "E", "F", "G"]].sum()
b["epc_pct_FG_recent"] = (b.F + b.G) / b.sum(axis=1) * 100
b["epc_pct_ABC_recent"] = (b.A + b.B + b.C) / b[["A", "B", "C", "D", "E", "F", "G"]].sum(axis=1) * 100
la = la.merge(b[["epc_pct_FG_recent", "epc_pct_ABC_recent"]].reset_index(), on="lad_code", how="left")
e3, q3 = epc("epc_eb3_existing_dwellings.ods", "EB3_by_LA")
cols = {k: [x for x in e3.columns if str(x).startswith(k)][0] for k in
        ["Number Lodgements", "Energy Consumption Current", "Carbon Dioxide Emissions Current", "Heating Cost Current", "Hot Water Cost Current", "Lighting Cost Current"]}
s = e3.groupby("lad_code")[list(cols.values())].sum()
n = s[cols["Number Lodgements"]]
s2 = pd.DataFrame({"epc_avg_energy_kwh_per_m2_recent": s[cols["Energy Consumption Current"]] / n,
                   "epc_avg_co2_t_per_home_recent": s[cols["Carbon Dioxide Emissions Current"]] / n,
                   "epc_avg_energy_cost_gbp_per_home_recent": (s[cols["Heating Cost Current"]] + s[cols["Hot Water Cost Current"]] + s[cols["Lighting Cost Current"]]) / n})
la = la.merge(s2.reset_index(), on="lad_code", how="left")

def ft(fname, col):
    d = pd.read_csv(R + fname, low_memory=False)
    d = d[d["Area Type"].isin(["District", "UA"]) & (d.Sex == "Persons")]
    latest = d.sort_values("Time period Sortable").groupby("Area Code").tail(1)
    return latest[["Area Code", "Value", "Time period"]].rename(columns={"Area Code": "lad_code", "Value": col, "Time period": col + "_period"})
la = la.merge(ft("fingertips_90810_asthma_admissions_u19.csv", "asthma_adm_u19_per100k"), on="lad_code", how="left")
la = la.merge(ft("fingertips_90360_excess_winter_deaths.csv", "winter_mortality_index"), on="lad_code", how="left")
la = la[la.lad_code.astype(str).str.match(r"E0[6-9]")].sort_values("lad_code")
la.to_csv("data/la_context.csv", index=False)

src = pd.DataFrame([
 ("damp_pct_ehs2023 / cat1_hazard_pct_ehs2023 / non_decent_pct_ehs2023", "EHS local authority stock condition modelling 2023 (modelled)", "https://www.gov.uk/government/statistics/english-housing-survey-local-authority-housing-stock-condition-modelling-2023", "LA (2023 boundaries)", "modelled estimate"),
 ("fuel_poverty_pct_2024", "DESNZ sub-regional fuel poverty 2026 (2024 data), LILEE", "https://www.gov.uk/government/statistics/sub-regional-fuel-poverty-data-2026-2024-data", "LA and LSOA", "modelled estimate"),
 ("imd_* / living_env_* / indoors_* / idaci_score", "English Indices of Deprivation 2025, File 7", "https://www.gov.uk/government/statistics/english-indices-of-deprivation-2025", "LSOA 2021; LA = population-weighted mean", "official statistics"),
 ("epc_*_recent", "MHCLG EPC live tables EB1 and EB3 (existing dwellings), last 8 quarters: " + ", ".join(q1[:1] + q1[-1:]), "https://www.gov.uk/government/statistical-data-sets/live-tables-on-energy-performance-of-buildings-certificates", "LA", "modelled (SAP) at certificate level; homes with new certificates only"),
 ("asthma_adm_u19_per100k", "OHID Fingertips 90810: hospital admissions for asthma (under 19 years)", "https://fingertips.phe.org.uk/", "District/UA", "observed (HES)"),
 ("winter_mortality_index", "OHID Fingertips 90360: winter mortality index", "https://fingertips.phe.org.uk/", "District/UA", "observed (ONS deaths)"),
], columns=["columns", "source", "url", "geography", "type"])
src.to_csv("data/external_sources.csv", index=False)
print("la_context:", la.shape, "| lsoa_context:", lsoa.shape)
print(la.notna().mean().round(2).to_string())
print(la.describe().T[["mean", "min", "max"]].round(1).to_string())
