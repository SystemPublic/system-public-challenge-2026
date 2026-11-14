"""Register the two city tests of the split-literature study. Run once, before any outcome query.
Usage: register.py asthma | covid"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from concord import claims

SEEN = ("Disclosure of what the project had seen before this registration. Graph side: all findings of both relationships "
        "and their PubMed abstracts were read (data/derived/graph/splits/findings.json, abstracts.json). City side: "
        "Central Park daily temperature (NOAA GHCN-Daily) has been used with shootings, heat-illness ED visits and EMS "
        "dispatches of type SHOT, STAB, DRUG, DRUGFC, EDP, EDPC, EDPM. For EMS dispatches (76xm-jjuj) the project has seen "
        "the count of every initial_call_type for calendar 2023 (ASTHMB 7,130; ASTHFC 2,813) and the date range of the file "
        "(2005-01-01 to 2026-09-30). No daily series of asthma dispatches has been queried by any agent "
        "(data/cache/socrata holds four 76xm-jjuj queries, none with an asthma code). For the COVID-19 daily counts "
        "(rc75-m7u3) I queried the column list and the first and last date (2020-02-29, 2025-10-13; 2,054 rows) and "
        "nothing else; no other agent has queried it.")

ASTHMA = {
 "id": "split-temp-asthma-ems",
 "kind": "confirmation",
 "statement": ("In New York City, within the same month and year, days in the cool half of the year (October to March) "
               "that are colder have more FDNY EMS dispatches for asthma, and the slope is more positive (or less "
               "negative) in the warm half of the year (April to September)."),
 "graph_evidence": [{
   "relationship_id": "4FaXcuNJRt|EAshH_Ko3h", "concepts": ["temperature", "asthma"],
   "n_findings": 30, "n_studies": 17, "sign_split": {"plus": 22, "minus": 8, "sig_plus": 16, "sig_minus": 4},
   "direction": "split",
   "summary": ("The graph's 22 positive and 8 negative findings do not disagree about temperature level once the variable "
               "names and abstracts are read. I recoded each finding by what was measured. 17 findings are short-term "
               "effects of temperature level; 16 of them (7 studies: Taipei, Hong Kong twice, Hefei, Lanzhou, a US "
               "emergency department, the Bronx) say colder days or falling temperatures bring more asthma visits or "
               "admissions, and they are stored with a positive sign because the variable is named 'low temperature' or "
               "'cold (5th percentile)'; one (Guangzhou-type subtropical city, respiratory morbidity) says heat. 9 findings "
               "are about temperature change or variability, not level, and disagree by season: in Shanghai a day-to-day "
               "rise raises childhood asthma visits in the warm season (RR 1.98) and a drop lowers them (RR 0.31), with "
               "no effect in the cool season; Hefei and a dry-climate city find variability effects mainly in the cool "
               "season; a US case-crossover study finds a negligible inverse effect. 3 are cross-sectional comparisons of "
               "climates (prevalence is higher in warmer places in China, Costa Rica and Italy), a different question. "
               "One is an interaction with air quality. Eight of the 30 rows are four results from PMID 35817164 stored twice."),
   "pubmed_ids": [24932702, 30641275, 35817164, 36240934, 39251927, 20708875, 30207818, 31651344, 33230642, 34599899,
                  36435499, 23035136, 21432566, 29529393, 7889426, 14982513, 32213400]}],
 "literature": [],
 "prediction": {
   "direction": "-",
   "magnitude": ("Cool half-year: incidence rate ratio of asthma dispatches per 5 C higher mean temperature over lags 0 to 3 "
                 "days between 0.95 and 0.99. Warm half-year: rate ratio between 1.00 and 1.05. Difference of log rate "
                 "ratios (warm minus cool) positive."),
   "support_if": "The cool half-year rate ratio per +5 C is below 1 and its 95% interval excludes 1.",
   "refute_if": "The cool half-year rate ratio per +5 C is above 1 and its 95% interval excludes 1.",
   "moderator_prediction": ("Secondary, scored separately and not deciding the verdict: the warm-minus-cool difference of "
                            "log rate ratios is positive with a 95% interval excluding 0. Reasoning from the moderators: "
                            "the cold effect in the literature is a cool-season, low-percentile effect, and the only "
                            "seasonal analysis of rises (Shanghai) finds them harmful in the warm season only.")},
 "plan": ("Outcome: daily count of FDNY EMS Incident Dispatch Data (76xm-jjuj) rows with initial_call_type in ('ASTHMB','ASTHFC'), "
          "by date of incident_datetime, 2006-01-01 to 2026-08-31, one SoQL group-by query through concord/socrata.py. "
          "Exposure: Central Park (USW00094728) daily mean temperature (TMAX+TMIN)/2 from concord/noaa.py, averaged over the "
          "day and the three days before it, in units of 5 C. Model: Poisson regression of the daily count on the exposure, "
          "with fixed effects for each year-month (so that season and trend are removed and only day-to-day variation within "
          "a month is used), day of week and US federal holidays; standard errors Newey-West with 7 lags. The model is "
          "fitted separately to October-March and April-September, and once to all days with an exposure-by-half-year "
          "interaction for the difference. Sensitivity, reported but not deciding: final_call_type instead of initial; "
          "lag 0 only; lags 0 to 7; excluding March 2020 to June 2021; daily minimum temperature. Exploratory: slope by "
          "calendar month. " + SEEN),
 "alternatives": [
   "Respiratory infections: cold spells coincide with influenza and RSV weeks; month fixed effects remove only part of this. Named, not separated.",
   "Call-taking behaviour: on very cold or very hot days people call EMS for different reasons or call types are assigned differently; the difficulty-breathing codes (DIFFBR, RESPIR) could absorb asthma calls.",
   "Air pollution: ozone on hot days and particulates on stagnant cold days; not adjusted, so the estimate is the total effect of weather.",
   "Pollen: warm spring days release tree pollen (the Bronx study in the graph, PMID 30207818), which would make April-May slopes positive for a reason other than temperature."],
 "prior": 0.45,
 "registrant": "Claude (split-literature study, graph discovery)",
}

COVID = {
 "id": "split-temp-covid-growth",
 "kind": "confirmation",
 "statement": ("In New York City, 2020 to 2025, weeks that follow warmer-than-normal weather for the time of year have "
               "slower growth of COVID-19 hospital admissions; and the raw correlation between daily temperature and "
               "daily case counts within single quarters, the design behind most positive findings in the graph, takes "
               "both signs depending on where the quarter falls in an epidemic wave."),
 "graph_evidence": [{
   "relationship_id": "4FaXcuNJRt|DZBybMvxDI", "concepts": ["temperature", "COVID-19"],
   "n_findings": 43, "n_studies": 29, "sign_split": {"plus": 26, "minus": 17, "sig_plus": 16, "sig_minus": 14},
   "direction": "split",
   "summary": ("The positive findings are mostly unadjusted Spearman or Pearson correlations between daily temperature and "
               "daily or cumulative case counts in one place over the first weeks or months of 2020, when cases and spring "
               "temperatures rose together (Jakarta, Oslo, India, Russia, Jordan, Korea, Pakistan). The negative findings "
               "mostly model transmission (reproduction number, growth, lagged incidence) with distributed lags, "
               "case-crossover designs or controls for government response (Wuhan and Hubei cities, four European "
               "countries, 153 countries above the turning point, US temperate regions, Mexico City, a meta-analysis). "
               "Four positive rows are not positive in substance: PMID 34189495 is '1 C decrease' and case fatality, "
               "PMID 34966171 is the relative risk at the 1st temperature percentile (cold raises transmissibility), "
               "PMID 35257688 says in its abstract that higher temperature goes with lower reproduction although the row "
               "is +0.875, and PMID 34375443 is body temperature (fever thresholds) grounded to 'temperature'. So the "
               "moderator is design and outcome: raw count correlations in a growth phase give either sign; models of "
               "transmission give negative."),
   "pubmed_ids": [32298883, 32492607, 32837322, 32948946, 33420694, 33727663, 33786420, 32389157, 32837623, 33307083,
                  34637125, 36107871, 34957431, 37500034, 35996423, 34189495, 34966171, 35257688, 34375443]}],
 "literature": [],
 "prediction": {
   "direction": "-",
   "magnitude": ("Change in the weekly log growth rate of hospital admissions per 1 C of temperature anomaly averaged over "
                 "days 7 to 20 before the week's midpoint: between -0.030 and -0.003. Raw quarterly Spearman correlations "
                 "of daily mean temperature with daily confirmed cases: at least 25% of quarters significantly positive "
                 "and at least 25% significantly negative (p < 0.05, ignoring autocorrelation, as the source studies did)."),
   "support_if": "The growth-rate coefficient is negative and its 95% interval excludes 0.",
   "refute_if": "The growth-rate coefficient is positive and its 95% interval excludes 0.",
   "moderator_prediction": ("Secondary, scored separately and not deciding the verdict: among calendar quarters from 2020 Q2 "
                            "to 2025 Q3, at least a quarter have a significantly positive raw correlation and at least a "
                            "quarter a significantly negative one.")},
 "plan": ("Outcome: COVID-19 Daily Counts of Cases, Hospitalizations, and Deaths (rc75-m7u3), columns date_of_interest, "
          "case_count, hospitalized_count, all rows (2020-02-29 to 2025-10-13), through concord/socrata.py. Weeks are "
          "Monday to Sunday; H_t is the weekly sum of hospitalized_count; g_t = log(H_t / H_{t-1}); weeks from 2020-03-16 "
          "with H_t and H_{t-1} at least 20. Exposure: Central Park daily mean temperature (TMAX+TMIN)/2 minus its "
          "day-of-year normal (two-harmonic fit to 2010-2025), averaged over days 7 to 20 before the Thursday of week t. "
          "Model: OLS of g_t on the anomaly, g_{t-1}, year fixed effects and two annual harmonic pairs; Newey-West standard "
          "errors with 4 lags. Sensitivity, reported but not deciding: anomaly window days 0 to 13 and days 14 to 27; "
          "cases instead of admissions; dropping 2020; dropping the Omicron weeks (2021-12-13 to 2022-02-13). Secondary: "
          "for each calendar quarter from 2020 Q2 to 2025 Q3, Spearman correlation of daily mean temperature with daily "
          "case_count. " + SEEN),
 "alternatives": [
   "Behaviour: warm anomalies move people outdoors and cold ones indoors; this is part of the weather effect and is not separated from virus survival.",
   "Variant waves: growth is dominated by variant arrivals, which are unrelated to two-week weather anomalies and add noise but not bias.",
   "Reporting: hospitalisation definitions and testing changed over time (cases after 2022 are undercounted); year fixed effects and the use of growth rates absorb level changes only.",
   "Holidays: Thanksgiving to New Year gatherings fall in a season with specific anomalies in some years; harmonics remove the average seasonal pattern only."],
 "prior": 0.35,
 "registrant": "Claude (split-literature study, graph discovery)",
}

if __name__ == "__main__":
    rec = {"asthma": ASTHMA, "covid": COVID}[sys.argv[1]]
    print(claims.register(rec))
