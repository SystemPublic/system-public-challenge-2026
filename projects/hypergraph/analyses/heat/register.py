"""Registrations for the heat topic. Run before any city or NOAA data are queried for these claims.

Usage: python -m analyses.heat.register <id> [<id> ...]
Each id is written by concord.claims.register and then committed by itself (notes/BRIEF.md).
The graph evidence was collected by analyses/heat/graph_evidence.py
(data/derived/heat/graph_evidence.json) and the key abstracts were read in PubMed
(data/derived/heat/abstracts_graph.txt).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from concord import claims

REGISTRANT = "Claude (heat agent), for Jeff Vernon"

# ---------------------------------------------------------------- graph evidence

G_HOMICIDE = {
    "relationship_id": "4FaXcuNJRt|YZku29igbl", "concepts": ["temperature", "homicide"], "n_findings": 4, "n_studies": 2,
    "direction": "+",
    "summary": "Two case-crossover studies. Rahman et al. 2023 (California 2014-2019): homicide odds +4.9% (1.6 to 8.1) per 5 C Tmax lag 0. "
               "Xu et al. 2020 (9 US cities 2007-2017): intentional homicide +9.5% (4.3 to 15.0) per 5 C mean temperature in Chicago and "
               "+8.8% (1.5 to 16.6) in New York, lag 0-7. The graph stores Xu's estimates as odds ratios 0.095 and 0.088 and Rahman's as "
               "odds ratios 4.9 and 6.2; the abstracts give percent changes, so the graph values are mis-extracted (true ORs about 1.095, 1.088, 1.049, 1.062).",
    "pubmed_ids": [36858215, 32738768],
}
G_INJURY = {
    "relationship_id": "4FaXcuNJRt|rULjCt1BqH", "concepts": ["temperature", "injury"], "n_findings": 4, "n_studies": 3,
    "direction": "+",
    "summary": "Girma et al. 2023, New York City ED visits 2005-2011 (SPARCS), warm season: intentional injury among 20-25 year olds OR 1.54 (1.28 to 1.85) "
               "for daily minimum 77 F vs 48 F, lag 0-5. The only NYC violence-temperature finding in the graph.",
    "pubmed_ids": [37448837],
}
G_GUN = {
    "relationship_id": "(concept X7hfhwez9f, 34 relationships)", "concepts": ["gun violence", "temperature"], "n_findings": 0, "n_studies": 0,
    "direction": "0",
    "summary": "The gun violence concept has no relationship with temperature, air temperature, heat wave, hot or extreme heat. "
               "Violence (2qLKgaxkm_), crime, aggression and violent crime have none either. The graph's heat-violence evidence is homicide and injury only.",
    "pubmed_ids": [],
}
G_SUICIDE = {
    "relationship_id": "4FaXcuNJRt|TLeQZQ_leT", "concepts": ["temperature", "suicide"], "n_findings": 12, "n_studies": 8, "direction": "+",
    "summary": "Self-directed violence rises with temperature in 8 studies (e.g. RR 1.35, 1.26 to 1.45, PMID 35394808; per 1 C IRR 1.008, PMID 34034696). Context for the violence claim.",
    "pubmed_ids": [35394808, 34034696, 36858215],
}
G_HEAT_ED = {
    "relationship_id": "wpUeTjUbAc|PtQBvGm5CM", "concepts": ["extreme heat", "heat illness"], "n_findings": 2, "n_studies": 2, "direction": "+",
    "summary": "Sun et al. 2021 (BMJ, 74 million insured US adults, 2010-2019): days at the local 95th percentile of warm-season temperature had 66.3% (60.2 to 72.7) "
               "excess risk of ED visits for heat-related illness, with stronger effects in the Northeast. Stowell et al. 2023 (US children): OR 1.34 (1.16 to 1.56), ages 6-12.",
    "pubmed_ids": [34819309, 36337257],
}
G_HEAT_ED_VAR = {
    "association_id": "variable u7xiLrAgHi", "concepts": ["maximum temperature", "heat-related ED admissions"], "n_findings": 1, "n_studies": 1, "direction": "+",
    "summary": "Kingsley et al. 2016 (Rhode Island 2005-2012): Tmax 75 to 85 F associated with 23.9% higher rates of heat-related ED visits (Poisson). "
               "The graph stores 23.9 as a coefficient without units.",
    "pubmed_ids": [26251954],
}
G_HEAT_MORT = {
    "relationship_id": "wpUeTjUbAc|QPxlNKv3zV", "concepts": ["extreme heat", "mortality rate"], "n_findings": 25, "n_studies": 14, "direction": "+",
    "summary": "Extreme heat raises mortality across 14 studies (RR 1.1 to 1.4 typical). Context; heat mortality in NYC is published only as yearly citywide counts.",
    "pubmed_ids": [39463255, 22340020, 25956805],
}
G_NDVI_LST = {
    "relationship_id": "hsryqxdFzE|PCdVJWVRyS", "concepts": ["NDVI", "thermodynamic temperature"], "n_findings": 1, "n_studies": 1, "direction": "-",
    "summary": "Hasan et al. 2022 (Mymensingh, Bangladesh, Landsat 1988-2016): strong negative correlation of land surface temperature with NDVI. "
               "The graph stores r = -1.0, which is not the reported value (the abstract gives no number). The only vegetation-temperature finding found.",
    "pubmed_ids": [35060045],
}
G_TREE = {
    "relationship_id": "(concepts I2CN3brExA tree, lHLIKbfnYp green space, RF7tCwCaa5 vegetation cover)", "concepts": ["tree", "green space", "heat"],
    "n_findings": 0, "n_studies": 0, "direction": "0",
    "summary": "The tree concept has no relationships. Green space has 14, none with temperature, heat illness or emergency care. "
               "Surface temperature links only to air temperature (r about 0.9, 2 studies), population density (r 0.82) and deforestation (r 0.89). "
               "No finding connects trees or green space to heat-related ED visits.",
    "pubmed_ids": [],
}
G_SURF_AIR = {
    "relationship_id": "sSuplgYnDQ|mUxSLRMwIy", "concepts": ["surface temperature", "air temperature"], "n_findings": 2, "n_studies": 2, "direction": "+",
    "summary": "Satellite surface temperature tracks ground air temperature (r about 0.9; R2 0.9).", "pubmed_ids": [],
}
G_INCOME = {
    "association_id": "variable FWrHgors91 (personal heat exposure)", "concepts": ["income", "personal heat exposure"], "n_findings": 5, "n_studies": 1, "direction": "-",
    "summary": "Bernhard et al. 2015 (Alabama): income above $20K associated with lower personal heat exposure, beta -1.05 C (-1.79 to -0.30), through the home thermal environment.",
    "pubmed_ids": [25617601],
}

# ---------------------------------------------------------------- literature

L_REEPING = {"citation": "Reeping PM, Hemenway D. The association between weather and the number of daily shootings in Chicago (2012-2016). Inj Epidemiol 2020;7:31.",
             "doi": "10.1186/s40621-020-00260-3",
             "finding": "Negative binomial GEE with month and year fixed effects: +34.0% (28.1 to 40.2) shootings per 10 C daily high on weekdays, +41.6% (34.7 to 48.9) on weekends and holidays; per 5 C that is IRR 1.158 and 1.190."}
L_LYONS = {"citation": "Lyons VH, Gause EL, Spangler KR, Wellenius GA, Jay J. Analysis of daily ambient temperature and firearm violence in 100 US cities. JAMA Netw Open 2022;5(12):e2247207.",
           "doi": "10.1001/jamanetworkopen.2022.47207",
           "finding": "Gun Violence Archive 2015-2020, distributed-lag models, lag 0 best: RR 1.17 (1.12 to 1.21) at the 84th percentile of Tmax vs the city median; 6.85% of shootings attributable to days above the median; Northeast attributable fraction 9.54%."}
L_XU = {"citation": "Xu R, Xiong X, Abramson MJ, Li S, Guo Y. Ambient temperature and intentional homicide: a multi-city case-crossover study in the US. Environ Int 2020;143:105992.",
        "doi": "10.1016/j.envint.2020.105992",
        "finding": "New York 2007-2017: +8.8% (1.5 to 16.6) intentional homicide per 5 C daily mean temperature, lag 0-7; 7.1% attributable to temperatures above the median."}
L_RAHMAN = {"citation": "Rahman MM et al. Ambient temperature and air pollution associations with suicide and homicide mortality in California. Sci Total Environ 2023;874:162462.",
            "doi": "10.1016/j.scitotenv.2023.162462",
            "finding": "+4.9% (1.6 to 8.1) homicide per 5 C Tmax lag 0."}
L_SUN = {"citation": "Sun S et al. Ambient heat and risks of emergency department visits among adults in the United States. BMJ 2021;375:e065653.",
         "doi": "10.1136/bmj-2021-065653",
         "finding": "95th vs median warm-season temperature (34.4 C vs 14.9 C national average): heat-related illness ED visits +66.3% (60.2 to 72.7)."}
L_KINGSLEY = {"citation": "Kingsley SL et al. Current and projected heat-related morbidity and mortality in Rhode Island. Environ Health Perspect 2016;124:460-467.",
              "doi": "10.1289/ehp.1408826", "finding": "Tmax 75 to 85 F (5.6 C): heat-related ED visits +23.9%."}
L_MADRIGANO = {"citation": "Madrigano J, Ito K, Johnson S, Kinney PL, Matte T. A case-only study of vulnerability to heat wave-related mortality in New York City (2000-2011). Environ Health Perspect 2015;123:672-678.",
               "doi": "10.1289/ehp.1408178",
               "finding": "Heat-wave deaths in NYC were more likely among Black residents and in areas with less green space and higher surface temperature (case-only design)."}
L_ZITER = {"citation": "Ziter CD, Pedersen EJ, Kucharik CJ, Turner MG. Scale-dependent interactions between tree canopy cover and impervious surfaces reduce daytime urban heat during summer. PNAS 2019;116:7575-7580.",
           "doi": "10.1073/pnas.1817561116",
           "finding": "Bicycle-transect air temperatures in Madison: daytime air temperature falls with canopy cover, nonlinearly, with the largest cooling above about 40% canopy at 60-90 m scales."}
L_HVI = {"citation": "NYC DOHMH Environment and Health Data Portal, Heat Vulnerability Index (NTA); and EHDP-data repository, key-topics/heat-vulnerability-index.",
         "doi": None,
         "finding": "The HVI is built from surface temperature, green space, household air conditioning, poverty or median income and percent Black residents, chosen because they predicted heat-related deaths. Using the HVI as an outcome of trees would be circular."}

# ---------------------------------------------------------------- registrations

REGS = [
 {
  "id": "heat-shootings",
  "kind": "confirmation",
  "statement": "In New York City, the daily number of shooting incidents rises with the day's maximum temperature at Central Park, within month and year, by about 5 to 20 percent per 5 C.",
  "graph_evidence": [G_HOMICIDE, G_INJURY, G_GUN, G_SUICIDE],
  "literature": [L_REEPING, L_LYONS, L_XU, L_RAHMAN],
  "prediction": {
   "direction": "+",
   "magnitude": "IRR per 5 C of Central Park TMAX (lag 0) between 1.05 and 1.20, with month, year and day-of-week terms. The spline curve rises monotonically from the coldest days to about the 85th-95th percentile; RR at the city's 84th percentile TMAX vs the median between 1.05 and 1.25 (Lyons et al. pooled 1.17).",
   "support_if": "lower 95% limit of the IRR per 5 C above 1.00 (confirmed); hit if the estimate lies in 1.05-1.20",
   "refute_if": "upper 95% limit at or below 1.00 (contested); an estimate above 1.00 with a limit below 1.00 is unsettled"
  },
  "plan": "Data: NYPD Shooting Incident Data, 5ucz-vwe8 (Shootings 2006-Present) as primary, count of distinct incident_key per occur_date, 2006-01-01 to the last full month; the archived historic file 833y-fsy8 (to 2024) used to check the counts match. Weather: GHCN-Daily USW00094728 (Central Park) TMAX and PRCP via concord/noaa.py. "
          "Primary model: negative binomial GLM (log link, dispersion by ML) of daily incidents on linear TMAX/5, factors for day of week, calendar month, year, an indicator for federal holidays plus 4 July and 31 December, and an indicator PRCP >= 1 mm. Report IRR per 5 C with 95% CI (robust HC0 SE). "
          "Curve: same model with a natural cubic spline of TMAX (4 df), RR vs the median TMAX; read off the RR at the 84th percentile for comparison with Lyons et al. "
          "Sensitivity, pre-specified: (a) TMAX averaged over lags 0-1; (b) TMIN instead of TMAX; (c) warm season May-September only; (d) 2006-2019 vs 2020-present; (e) murders only (statistical_murder_flag, historic file). "
          "Comparison: literature estimates converted to IRR per 5 C where possible (Reeping weekday and weekend; Xu NYC homicide; Rahman CA homicide; corrected graph values).",
  "alternatives": ["Residual seasonality within month (school calendar, summer youth programmes, daylight) correlated with temperature",
                   "Time outdoors and street encounters as the mechanism (the temperature effect is real but works through routine activity, not physiology); the design cannot separate mechanisms",
                   "Police summer deployments (e.g. Summer All Out) that respond to expected violence",
                   "The 2020-2021 rise in shootings coinciding with summers; handled by year terms but not by year-by-month"],
  "prior": 0.9,
  "registrant": REGISTRANT,
 },
 {
  "id": "heat-ed-syndromic",
  "kind": "confirmation",
  "statement": "In New York City, daily emergency department visits for heat-related illness (DOHMH syndromic surveillance) rise steeply with the day's maximum temperature in the warm season.",
  "graph_evidence": [G_HEAT_ED, G_HEAT_ED_VAR, G_HEAT_MORT],
  "literature": [L_SUN, L_KINGSLEY],
  "prediction": {
   "direction": "+",
   "magnitude": "Warm season (May-September), IRR per 5 C Central Park TMAX between 1.5 and 5. The curve is flat below about 27 C and steep above it; on days at the city's 95th percentile TMAX versus the warm-season median, RR at least 1.66 (Sun et al. national average) and probably above 3, because syndromic counts are near zero on mild days.",
   "support_if": "lower 95% limit of the IRR per 5 C above 1.00 and estimate >= 1.5 (hit); estimate between 1.0 and 1.5 with lower limit above 1 is partial",
   "refute_if": "upper limit at or below 1.00"
  },
  "plan": "Data: EHDP-data GitHub repository (nychealth/EHDP-data, branch production, key-topics/heat-syndrome: previous_years.csv, edheat1720_supp.csv, edheatYYYY_live.csv), daily counts of heat-syndrome ED visits citywide, cited by commit SHA. If no daily series exists, use EHDP indicator 2075 (yearly heat ED visits) and say so. "
          "Weather: NOAA GHCN-Daily Central Park TMAX (the DOHMH file's own LaGuardia heat-index column is used only as a cross-check, not as the exposure). "
          "Model: negative binomial GLM of daily counts, May-September, on linear TMAX/5 with day-of-week, month and year factors; and a natural spline (4 df) for the curve, RR vs the warm-season median TMAX; RR at the 95th percentile compared with Sun et al. "
          "Secondary: EHDP yearly heat ED visits (indicator 2075, citywide) and yearly heat deaths (2074) against the number of days with TMAX >= 32.2 C (90 F) per year, Spearman correlation, descriptive.",
  "alternatives": ["Syndromic case definition changed in 2023 (applied back to all years, per DOHMH)",
                   "Chief-complaint keyword matching may respond to heat warnings and media attention, not only to illness (awareness bias)",
                   "Some residents seek care outside the city; coverage of 100% of NYC EDs only from May 2016"],
  "prior": 0.95,
  "registrant": REGISTRANT,
 },
 {
  "id": "heat-trees-surftemp",
  "kind": "bridge",
  "statement": "Across New York City community districts, more street trees per square kilometre go with a lower daytime summer surface temperature, after adjusting for poverty and percent Black residents.",
  "graph_evidence": [G_NDVI_LST, G_TREE, G_SURF_AIR],
  "literature": [L_ZITER, L_MADRIGANO],
  "prediction": {
   "direction": "-",
   "magnitude": "Per 1 SD of log street-tree density (2015 census, live trees per km2 of land), surface temperature lower by 0.5 to 3 F (Landsat, 17 July 2018). Unadjusted Pearson r between -0.2 and -0.7.",
   "support_if": "adjusted slope negative with upper 95% limit below 0",
   "refute_if": "adjusted slope positive with lower limit above 0"
  },
  "plan": "Unit: 59 community districts. Exposure: 2015 Street Tree Census (uvpi-gqnh), count of status='Alive' by cb_num via SoQL group; land area of each CD from the NYC community district boundary file on NYC Open Data (shape_area, ft2 to km2). Secondary exposure: EHDP vegetative cover (indicator 2143, measure 690). "
          "Outcome: EHDP daytime summer surface temperature (indicator 2141, measure 688, CD). Covariates: percent in poverty and percent Black, averaged over NTAs within each CD from EHDP hvi-nta.csv. "
          "Model: OLS of surface temperature on z(log trees/km2), unadjusted and adjusted; HC3 SE. Secondary unit: NTA2010 (about 190), surface temperature and covariates from hvi-nta.csv, trees by the census nta field, NTA land area from the NTA 2010 boundary file.",
  "alternatives": ["Building density and impervious cover drive both fewer street trees and hotter surfaces (dense Manhattan cores vs low-rise Staten Island)",
                   "Distance to water and parkland (parks are not street trees)",
                   "A single Landsat afternoon (17 July 2018) measures roofs and pavement, not air temperature at street level"],
  "prior": 0.65,
  "registrant": REGISTRANT,
  "chain": ["heat-trees-surftemp"],
 },
 {
  "id": "heat-surftemp-ed",
  "kind": "bridge",
  "statement": "Across New York City community districts, hotter daytime surface temperature goes with a higher rate of heat-stress emergency department visits, and this survives adjustment for poverty, percent Black residents and household air conditioning.",
  "graph_evidence": [G_HEAT_ED, G_INCOME, G_TREE],
  "literature": [L_MADRIGANO, L_HVI, L_SUN],
  "prediction": {
   "direction": "+",
   "magnitude": "Unadjusted: +3% to +15% in the age-adjusted heat ED rate per 1 F of surface temperature. Adjusted for poverty, percent Black and AC: attenuated by at least a third, +0% to +8% per 1 F, with an interval that may include zero.",
   "support_if": "adjusted slope positive with lower 95% limit above 0 (confirmed link)",
   "refute_if": "adjusted slope negative with upper limit below 0"
  },
  "plan": "Unit: 59 community districts. Outcome: EHDP indicator 2443 (heat stress, 5-year ED visits, average annual age-adjusted rate per 100,000, measure 1405, CD), log scale; secondary outcome EHDP 2410 (10-year heat hospitalizations, age-adjusted, measure 1283). Exposure: EHDP 2141 surface temperature (F). "
          "Covariates from hvi-nta.csv averaged to CD: POV_PCT, PCT_BLACK_POP, PCT_HOUSEHOLDS_AC. Model: OLS of log rate on surface temperature, unadjusted and adjusted, HC3 SE; report percent change per 1 F. "
          "Secondary unit: NTA2010, HRI_HOSP_RATE from hvi-nta.csv on SURFACETEMP with the same covariates.",
  "alternatives": ["Poverty and race drive both residence in hot, treeless districts and ED use (insurance, ED as usual source of care, outdoor work)",
                   "Residents are exposed where they work and travel, not only where they live",
                   "ED rates count residents by home address; small counts in some CDs are unstable"],
  "prior": 0.35,
  "registrant": REGISTRANT,
  "chain": ["heat-surftemp-ed"],
 },
 {
  "id": "heat-trees-airtemp-hyperlocal",
  "kind": "bridge",
  "statement": "Within the same neighbourhood and day, NYC hyperlocal sensors with more street trees nearby record lower afternoon air temperature.",
  "graph_evidence": [G_SURF_AIR, G_TREE],
  "literature": [L_ZITER],
  "prediction": {
   "direction": "-",
   "magnitude": "Per 10 additional live street trees within 50 m of a sensor, mean 12:00-18:00 air temperature lower by 0.05 to 0.5 C, within NTA-by-day.",
   "support_if": "slope negative with upper 95% limit (sensor-clustered SE) below 0",
   "refute_if": "slope positive with lower limit above 0"
  },
  "plan": "Data: Hyperlocal Temperature Monitoring (qdq3-9eqn), summers 2018 and 2019, sensor-day mean airtemp over hours 12-18 via SoQL group by sensor_id, day; sensor coordinates, install_type and ntacode. Trees: 2015 Street Tree Census live trees with coordinates (uvpi-gqnh), counted within 50 m (and 100 m, sensitivity) of each sensor using projected coordinates. "
          "Model: OLS of sensor-day afternoon temperature on trees50/10 and install_type, with NTA-by-day fixed effects (comparisons only among sensors in the same NTA on the same day); SE clustered by sensor. Report the slope in C per 10 trees.",
  "alternatives": ["Sensor siting: sensors on light poles vs trees differ in shade and height (install_type is controlled)",
                   "Trees cluster on residential side streets, away from wide arterial roads and heat from traffic",
                   "The 2015 census predates the 2018-2019 readings; plantings and removals in between add noise"],
  "prior": 0.55,
  "registrant": REGISTRANT,
  "chain": ["heat-trees-airtemp-hyperlocal"],
 },
 {
  "id": "heat-trees-ed-chain",
  "kind": "bridge",
  "statement": "Street trees lower heat-stress emergency department visits in New York City through lower neighbourhood temperature: the composed path trees -> surface temperature -> heat ED rate is negative across community districts.",
  "graph_evidence": [G_TREE, G_NDVI_LST, G_HEAT_ED, G_SURF_AIR],
  "literature": [L_MADRIGANO, L_ZITER, L_SUN, L_HVI],
  "prediction": {
   "direction": "-",
   "magnitude": "Indirect effect (a*b, both adjusted for poverty and percent Black; b also for AC and trees) between -0.5% and -5% in the heat ED rate per 1 SD of log street-tree density. The total association of trees with the ED rate, unadjusted, may have either sign, because tree density and poverty are correlated across CDs; the adjusted indirect path is the registered quantity.",
   "support_if": "verdict 'bridged' if links heat-trees-surftemp and heat-surftemp-ed are each confirmed or unsettled with the right sign, and the bootstrap 95% interval of a*b lies below 0",
   "refute_if": "a*b positive with the bootstrap interval above 0, or either link contested"
  },
  "plan": "Compose the two community-district links: a = adjusted slope of surface temperature on z(log trees/km2) (heat-trees-surftemp), b = adjusted slope of log heat ED rate on surface temperature, also adjusted for z(log trees/km2) (heat-surftemp-ed); indirect effect a*b with a nonparametric bootstrap over CDs (5,000 draws). Report also the total association of log ED rate on trees, unadjusted and adjusted. "
          "The hyperlocal within-NTA link (heat-trees-airtemp-hyperlocal) is reported beside the chain as the street-level check on link a. "
          "State which confounders the chain cannot separate (income, race, housing age and AC, building density) and what design would settle it.",
  "alternatives": ["Income and race drive tree cover (historic planting and redlining), surface temperature and ED use together; 59 areal units cannot separate them",
                   "Ecological fallacy: area associations need not hold for individuals",
                   "Street trees are a small part of canopy; parks and backyard trees are omitted",
                   "Reverse placement: MillionTreesNYC targeted low-canopy, high-HVI neighbourhoods after 2007, so planting follows vulnerability"],
  "prior": 0.35,
  "registrant": REGISTRANT,
  "chain": ["heat-trees-surftemp", "heat-surftemp-ed"],
 },
]


def main(ids):
    by = {r["id"]: r for r in REGS}
    for i in ids:
        print(claims.register(by[i]))


if __name__ == "__main__":
    main(sys.argv[1:] or [])
