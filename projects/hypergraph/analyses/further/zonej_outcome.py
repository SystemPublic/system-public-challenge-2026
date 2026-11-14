import json
from pathlib import Path
from concord import claims
ROOT = Path(__file__).resolve().parents[2]
R = json.loads((ROOT/"data/derived/further/zonej_results.json").read_text())
GB = json.loads((ROOT/"data/derived/further/zonej_goldbook_summary.json").read_text())
PS = json.loads((ROOT/"data/derived/further/zonej_pal_sources.json").read_text())
lm = sorted({v.get("last_modified") for v in PS.values() if v.get("last_modified")})
j, k = R["N.Y.C."], R["LONGIL"]
rec = {
 "id": "further-zonej-demand-growth",
 "verdict": "contested",
 "city_effect": {"label": "Zone J weather-normalised annual energy trend, 2015-2025, pandemic days 2020-03-15 to 2021-06-30 excluded", "estimate": round(j["energy"]["est"], 3), "lo": round(j["energy"]["lo"], 3), "hi": round(j["energy"]["hi"], 3), "scale": "percent a year (OLS on daily ln energy, Newey-West 14 lags, 95% interval)", "null": 0, "n": j["energy"]["n"]},
 "secondary_effects": {
  "zone_J_summer_peak_trend": {**{x: round(j["peak"][x], 3) for x in ("est","lo","hi","n")}, "scale": "percent a year"},
  "zone_K_energy_trend_placebo": {**{x: round(k["energy"][x], 3) for x in ("est","lo","hi","n")}, "scale": "percent a year"},
  "zone_K_summer_peak_trend": {**{x: round(k["peak"][x], 3) for x in ("est","lo","hi","n")}, "scale": "percent a year"},
  "J_minus_K_energy_trend": {**{x: round(R["placebo_K_contrast_J_minus_K_energy"][x], 3) for x in ("est","lo","hi")}, "scale": "percentage points a year, 30-day block bootstrap"},
  "S8_block_bootstrap_J_energy": R["S8_block_bootstrap_energy"]["N.Y.C."],
  "annual_weather_normalised_energy_twh_J": j["annual_norm_twh"],
  "design_day_peak_mw_J": j["design_day_peak_mw"],
  "sensitivity": R["sensitivity"]["N.Y.C."],
  "sensitivity_zone_K": R["sensitivity"]["LONGIL"],
  "placebo_shifted_weather": R["placebo_shifted_weather"],
  "gold_book": GB,
  "unregistered_annual_level_interval": "Descriptive only (rule 4): a t-interval on the 11 annual normalised values gives -0.77 percent a year (-1.11 to -0.42); excluding 2020 and 2021, -0.74 (-1.10 to -0.38). Wider than the daily-model HAC interval because only 9 to 11 independent years inform the trend."
 },
 "sources": [
  {"kind": "nyiso-pal", "name": "NYISO integrated real-time actual load (PAL), 5-minute, zones N.Y.C. and LONGIL", "url": "https://mis.nyiso.com/public/csv/pal/YYYYMM01pal_csv.zip", "files": "132 monthly zips, 201501 to 202512", "last_modified_range": [lm[0], lm[-1]], "fetched": "2026-11-12/13", "version_record": "data/derived/further/zonej_pal_sources.json", "data_access": "open"},
  R["weather_source"] | {"data_access": "open"},
  R["laguardia_source"] | {"data_access": "open", "use": "sensitivity S6"},
  {"kind": "nyiso-goldbook", "name": "NYISO Load & Capacity Data Report (Gold Book) 2021-2026, Tables I-2 and I-3a", "urls": ["https://www.nyiso.com/documents/20142/2226333/<2023..2026>-Gold-Book-Public.pdf", "https://www.nysrc.org/wp-content/uploads/2023/11/I.3-R2-Load-and-Capacity-Gold-Book-2022.pdf", "https://nysrc.org/wp-content/uploads/2023/04/2021-April-Load-and-Capacity-Gold-Book.pdf"], "extracted": "data/derived/further/zonej_goldbook.csv", "data_access": "open", "note": "The 2021 and 2022 editions are copies hosted by the New York State Reliability Council, not NYISO's own files."},
  {"kind": "nyiso-power-trends", "url": "https://www.nyiso.com/documents/d/guest/2026-power-trends", "data_access": "open", "note": "quote verified in the PDF text"}
 ],
 "prediction_scored": "partial. The claim's direction (+) and the +0.5 percent threshold were not met; the refutation condition was met (upper limit -0.67 percent a year against a threshold of +0.5). The registrant's expected value of about 0.0 (range -0.6 to +0.6) was too high: the estimate of -0.75 lies just outside the range. The Gold Book part (registered as secondary) neither showed forecasts biased high nor biased low.",
 "settle": "The full-period trend is dominated by a level shift between 2019 and 2021-2022 (normalised energy 51.8 TWh in 2019, 49.2 in 2021) that coincides with the pandemic and the exclusion window; the pre-pandemic years are flat (-0.09 percent a year, -0.30 to +0.11) and 2022-2025 rises (+0.56, +0.32 to +0.81). Whether Zone J demand is growing now is better answered by 2022-2026 data with an occupancy covariate (building access or transit ridership), by behind-the-meter solar output for Zone J to add back to net load, and by Con Edison's weather-adjusted sales by class. Those data would separate a lasting drop in commercial load from a recovery.",
 "research_needed": [
  {"question": "How much of the post-2019 drop in Zone J load is lasting loss of office and commercial load, and how much is behind-the-meter solar and efficiency?", "data": "Con Edison sales by class; NYSERDA behind-the-meter solar by zone; building occupancy (Kastle, MTA ridership); LL84 benchmarked electricity by year", "design": "Decompose weather-normalised Zone J load by customer class and add back behind-the-meter generation", "priority": "high"},
  {"question": "Is the 2022-2025 increase (+0.56 percent a year in this analysis) a recovery or a new growth path?", "data": "NYISO PAL load through 2026 and later; Gold Book 2027", "design": "Pre-register a trend test on 2022 onward with an occupancy control", "priority": "high"},
  {"question": "Does the system-wide statement of rising demand apply to any zone other than the upstate zones with large-load proposals?", "data": "Gold Book Table I-2 by zone, PAL by zone", "design": "Run the same pipeline in every zone and compare with the interconnection queue by zone", "priority": "medium"}
 ],
 "figures": ["figures/further/zonej_demand_growth.png"],
 "notes": "Verdict follows PRECEDENCE rule 1: the registered refute_if (upper 95 percent limit of the energy trend below +0.5 percent a year) is met in the primary model and in every sensitivity check that uses the whole period (S1, S2, S5, S6, S7, S8). Zone K shows a similar decline (-0.86), so the Zone J result is not specific to New York City; Zone J is 0.11 points a year higher than Zone K (0.02 to 0.19). The shifted-weather placebo removed almost all of the weather-attributable R-squared (0.238 to 0.004), so the weather model captures real temperature dependence. PAL annual totals match the Gold Book's own historical Zone J energy within 1 percent in every year 2016 to 2025. Measured load is net of behind-the-meter solar, which rises over the period and lowers measured load; it is not corrected. Gold Book comparison used editions 2021 to 2025 (the 2026 edition has no past target years); at a three-year horizon only three editions apply (2021, 2022, 2023), with forecast-growth errors +3.0, -1.9 and -4.0 points, mean -1.0 (bootstrap -4.0 to +3.0), so neither registered bias condition is met. The 2021 edition's base year, 2020, is a pandemic year, and the normalised value for 2020 and 2021 is less reliable because most of those years' days were excluded from the fit. Exploratory and unregistered: against the Gold Book's own later historical values, forecast growth at three years was 2.6 points too low on average (-1.5, -3.1, -3.3). The HAC intervals are narrow because the daily model has thousands of days, but the trend rests on 9 to 11 years; the unregistered annual-level interval is wider but also excludes zero."
}
print(claims.outcome(rec))
