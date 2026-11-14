"""Register further-zonej-demand-growth (run once, before any NYISO load values are read)."""
from concord import claims

rec = {
 "id": "further-zonej-demand-growth",
 "kind": "confirmation",
 "statement": "Electricity demand in New York City is growing: weather-normalised annual energy in NYISO Zone J (N.Y.C.) rose by more than 0.5 percent a year over 2015 to 2025, with a 95 percent interval that excludes zero.",
 "edge": {"cause": "time (electrification, new large loads, economic development)", "effect": "weather-normalised electricity demand in Zone J (annual energy; summer peak)"},
 "graph_evidence": [
  {"association_id": "(pending)", "concepts": ["electricity demand", "New York City"], "n_findings": None, "n_studies": None,
   "direction": "?", "summary": "System graph API key is not on this machine. A live lookup of what the graph holds on electricity demand, electrification and load growth is pending; nothing is asserted here.", "pubmed_ids": []}
 ],
 "literature": [
  {"citation": "New York Independent System Operator (2026). 2026 Power Trends, overview (PDF created 7 June 2026).",
   "url": "https://www.nyiso.com/documents/d/guest/2026-power-trends",
   "doi": None,
   "finding": "Verified in the PDF text: \"electricity demand is increasing and becoming more uncertain, shaped by electrified heating and transportation, emerging technologies, and large energy-intensive economic development projects.\" The statement is system-wide, not specific to New York City.",
   "data_used": "NYISO load forecasts and interconnection queue", "data_access": "open"},
  {"citation": "NYISO (2026). 2026 Power Trends, section on planning cycle.",
   "url": "https://www.nyiso.com/documents/d/guest/2026-power-trends", "doi": None,
   "finding": "Verified: the 2025-2034 Comprehensive Reliability Plan \"incorporated updated system assumptions, including a revised demand forecast for New York City\" that mitigated a reliability need identified in the 2024 Reliability Needs Assessment, which had been \"driven by forecasted demand growth\". Direction of the revision is not stated in the sentence.",
   "data_used": "NYISO planning forecasts", "data_access": "open"},
  {"citation": "NYISO, Load & Capacity Data Report (Gold Book), annual editions.",
   "url": "https://www.nyiso.com/load-capacity-data-report-gold-book-", "doi": None,
   "finding": "Existence only; contents not read before registration. Editions 2023, 2024, 2025 and 2026 exist at https://www.nyiso.com/documents/20142/2226333/<year>-Gold-Book-Public.pdf (HTTP 200 checked). Copies of the 2021 and 2022 editions are hosted by the New York State Reliability Council (nysrc.org, found by search, not opened). The Zone J forecast tables have not been read.",
   "data_used": "NYISO Zone J baseline energy and peak forecasts", "data_access": "open"},
  {"citation": "Developments Today (14 May 2026), reporting Con Edison first-quarter 2026 results (second-hand, from the scouting note).",
   "url": None, "doi": None,
   "finding": "Reported: Con Edison weather-adjusted sales down 0.1 percent at CECONY in the first quarter of 2026. Not verified by the registrant.",
   "data_used": "Con Edison sales", "data_access": "unknown"}
 ],
 "prediction": {
  "direction": "+",
  "magnitude": "The claim's direction is +. The registrant's expected value for the weather-normalised Zone J energy trend (primary model, 2015-2025 excluding 2020-03-15 to 2021-06-30) is about 0.0 percent a year, with a plausible range of -0.6 to +0.6. For the weather-normalised summer daily-peak trend the expected value is about 0.0 percent a year, range -0.8 to +0.8. Zone K is expected in the same range, slightly lower.",
  "support_if": "Primary model (below): the energy trend point estimate is greater than +0.5 percent a year AND its 95 percent HAC confidence interval has a lower limit greater than 0 AND the summer-peak trend point estimate is greater than 0. All three must hold.",
  "refute_if": "The upper limit of the 95 percent HAC confidence interval for the energy trend is below +0.5 percent a year (growth, if any, is smaller than the registered threshold). The peak trend does not rescue the claim.",
  "neither": "Anything else (for example the interval straddles +0.5, or energy supports but the peak estimate is not positive) is unsettled.",
  "secondary_gold_book": "Reported and scored separately; it does not decide the verdict. If Zone J tables can be read from at least five editions, forecast growth error = F_e(t)/F_e(b) - R(t)/R(b), where e is the edition, b = e-1 is its last historical year, t is a target year up to 2025, F is the edition's Zone J baseline energy (GWh) and R is the realised weather-normalised energy from the primary model. Forecasts are called biased high if the mean growth error over editions at a three-year horizon is above +1 percentage point with a 95 percent bootstrap interval (over editions) excluding zero, and biased low if below -1 with interval excluding zero. With fewer than five readable editions this part is reported as not done."
 },
 "plan": {
  "data": [
   {"name": "NYISO integrated real-time actual load (PAL), 5-minute, zones N.Y.C. (PTID 61761) and LONGIL (PTID 61762)", "url": "https://mis.nyiso.com/public/csv/pal/YYYYMM01pal_csv.zip, monthly zips from 201501 to 202512", "access": "open", "record": "URL, Last-Modified and fetch time recorded per zip"},
   {"name": "NOAA GHCN-Daily, Central Park USW00094728 (TMAX, TMIN), via concord/noaa.py", "access": "open"},
   {"name": "NYISO Gold Book editions (secondary part)", "access": "open"}
  ],
  "unit": "Zone-day, 1 January 2015 to 31 December 2025. Daily energy (MWh) = sum of 5-minute load x 5/60. Daily peak (MW) = maximum 5-minute load. Days with fewer than 90 percent of the expected 5-minute readings are dropped and counted. Duplicate timestamps (daylight-saving fall-back) are averaged.",
  "weather": "Daily mean temperature T = (TMAX+TMIN)/2 at Central Park. HDD = max(65-T,0); CDD = max(T-65,0) (degrees F). The temperature is converted from deg C to deg F.",
  "primary_model": "OLS on days: ln(E_d) = a + b*t + g1*HDD + g2*HDD^2 + g3*CDD + g4*CDD^2 + g5*CDD_{d-1} + g6*CDD_{d-2 to d-3 mean} + day-of-week effects + US federal holiday indicator + month effects. t is years since 2015-01-01 (continuous). b is the trend; the reported trend is 100*(exp(b)-1) percent a year. 95 percent interval from Newey-West HAC standard errors with 14 lags. Days from 2020-03-15 to 2021-06-30 inclusive are excluded (the pre-specified pandemic rule, chosen as the period of stay-at-home orders and the staged reopening before the 1 July 2021 full reopening).",
  "peak_model": "Summer days (1 June to 30 September): ln(P_d) = a + b*t + CDD, CDD^2, CDD_{d-1}, CDD mean of d-2..d-3 + day-of-week + holiday + month effects, same exclusion and HAC rules. Weather-normalised summer peak for a year = the model's predicted peak on a design day, defined as the weekday in July with CDD at the 90th percentile of July weekday CDD over 2015-2025 (CDD lags set to the same percentile values), for the year's own t. Trend of that series is reported as percent a year.",
  "annual_normalised_energy": "Descriptive: the same energy model with year indicators in place of t; each year's weather-normalised energy is the sum over that year's calendar days of the predicted energy with HDD and CDD (and lags) set to the 2015-2025 mean for the same calendar day (15-day centred window). Years 2020 and 2021 are shown but flagged (pandemic days excluded from the fit, so those years are predicted from their non-excluded days only and marked as less reliable).",
  "sensitivity_checks": [
   "S1 Include all days with a pandemic indicator for 2020-03-15 to 2021-06-30 instead of excluding them.",
   "S2 Exclude all of 2020 and 2021.",
   "S3 Fit 2015-2019 only; and S4 fit 2022-2025 only (post-pandemic).",
   "S5 Cooling base temperature 70 F and heating base 60 F.",
   "S6 LaGuardia (USW00014732) weather in place of Central Park.",
   "S7 Month x CDD interactions added.",
   "S8 Annual moving-block bootstrap (resampling whole years is not feasible with 9 usable years, so 30-day blocks, 2000 draws) as an alternative interval."
  ],
  "placebo": "Zone K (Long Island, LONGIL) through the identical pipeline. Zone K has a different utility, building stock and tariff structure. The comparison is the difference J minus K in trend with a 30-day block bootstrap interval. It is a contrast, not a null: if K shows a trend of similar size, the Zone J result is not specific to New York City. A second placebo: re-run the primary Zone J model with the weather series from the calendar-shifted year (each date's weather taken from the same date three years earlier); the weather coefficients should lose most of their explanatory power (R-squared falls by more than half of the weather-attributable R-squared), which checks that the weather model is doing what is claimed.",
  "confounders": {
   "behind_the_meter_solar": "NYISO load is net of rooftop solar that offsets utility supply, so growth in solar lowers measured load and especially daytime and summer-peak load. Not corrected. Direction of bias: toward lower measured demand. Reported as a limitation; no correction is applied.",
   "efficiency": "Building and appliance efficiency lowers load; it is part of what the claim's 'demand' includes, so not corrected.",
   "pandemic_occupancy": "Office occupancy in Manhattan stayed below 2019 levels after 2021. Handled by the pandemic exclusion window and S1 to S4; the post-2021 baseline may still be lower than 2015-2019, which would put a level shift into the trend. S3 and S4 separate the two halves.",
   "population_and_building_stock": "Population, floor area and electrified heating change over time and are not separated from 'demand'.",
   "data_quality": "PAL real-time data are not settlement-quality and can contain gaps or spikes. Days failing the coverage rule are dropped; daily values above 3 x the zone's median daily value or below 0.3 x are flagged and the model is re-fit without them as a check.",
   "weather_model": "One station, no humidity or cloud cover, so heat-wave response is approximated. Residual weather variation inflates the interval, not necessarily the trend.",
   "load_pocket_definition": "Zone J is NYISO's N.Y.C. zone, which is Con Edison's city load; it does not include Westchester (Zone I)."
  },
  "gold_book": "For each edition from 2019 to 2026 that can be downloaded and parsed, extract the Zone J baseline energy (GWh) and summer coincident peak (MW) forecast tables with pdftotext; check each extracted row against the page text. Editions where extraction cannot be verified are dropped and listed."
 },
 "alternatives": [
  "Flat demand: efficiency, rooftop solar and weaker office occupancy offset electrification, so the weather-normalised trend is within about +-0.5 percent a year of zero.",
  "Growth confined to the post-pandemic recovery: a positive trend from 2021 to 2025 is a rebound to the pre-2020 level, not a new growth path (separated by S3 and S4).",
  "Growth in peak but not energy, or the reverse, caused by changes in solar penetration and load shape.",
  "Growth that is real but is mostly outside Zone J (upstate large loads, data centres), so the system-wide statement does not describe New York City."
 ],
 "prior": 0.2,
 "registrant": "Claude (agent), for Jeff Vernon",
 "seen_before_registration": {
  "project_cache": "Searched data/cache/socrata, analyses/, data/derived/ and docs/ for NYISO, Zone J and electricity. No NYISO or electricity query had been made. Hits were only in the scouting note and unrelated files (graph audit, Red Hook records). data/cache/noaa holds Central Park GHCN-Daily from earlier heat analyses (weather only; no load data).",
  "this_session": "Read the Power Trends 2026 PDF text for the quote; listed the PAL zip's file names, its column header and the zone names (no load values); checked that Gold Book URLs exist (HTTP status only). No load, forecast or Gold Book table value had been read.",
  "background_knowledge": "The registrant has general recollection that NYC load was roughly flat across the 2010s and that the NYISO revised its NYC forecast downward in recent years. This is the basis of the prior of 0.2 and is not data from this project."
 }
}
p = claims.register(rec)
print(p)
