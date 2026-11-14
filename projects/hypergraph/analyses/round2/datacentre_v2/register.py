"""Register further-datacentre-share-manhattan-v2 (run once, before the v2 quantities are computed)."""
from concord import claims

LIST = ("60 Hudson Street (Western Union Building, BBL 1001440040), 111 Eighth Avenue (1007390001), 32 Sixth Avenue / 32 Avenue of the Americas (1001920001), "
        "325 Hudson Street (1005970062), 375 Pearl Street (1001137501), 85 Tenth Avenue (1006870029), 75 Broad Street (1000290070), "
        "33 Whitehall Street (1000100014), 32 Old Slip (1000350001), 150 Varick Street (1005050001). This is the list of the first registration, unchanged; "
        "no building was added, because the web search made for this registration confirmed 60 Hudson, 111 Eighth, 32 Avenue of the Americas, 85 Tenth and 75 Broad "
        "only and did not confirm 25 Broadway, 55 Broad Street or 799 Broadway.")

rec = {
 "id": "further-datacentre-share-manhattan-v2",
 "kind": "conflict",
 "supersedes": "further-datacentre-share-manhattan",
 "statement": ("In calendar year 2024, the electricity allocated to data-centre use in Manhattan, estimated as reported IT site energy times a PUE of 1.4 to 2.0 (low figure) "
               "and, for named carrier hotels, the excess of the building's electricity intensity over the median Manhattan office intensity (high figure), is a smaller share "
               "of Manhattan electricity than the 4.4 percent of US electricity that data centres used in 2023, and lies in the registered range of roughly 1 to 3.5 percent."),
 "edge": {"cause": "data centres", "effect": "share of a city district's electricity use"},
 "graph_evidence": [
  {"concepts": ["data centers", "electricity consumption"], "n_findings": 0, "n_studies": 0, "direction": None,
   "summary": "The System Public Graph is silent on this topic. Concept searches for 'data center', 'data centre' and 'server farm' returned no concept (3 uncached requests, 12 Nov 2026); the earlier registration also found none. No graph evidence is cited.",
   "pubmed_ids": []}
 ],
 "literature": [
  {"citation": "Lawrence Berkeley National Laboratory for the US Department of Energy, 2024 United States Data Center Energy Usage Report (Shehabi et al.), December 2024; summary page dated 17 January 2025.",
   "url": "https://energyanalysis.lbl.gov/news/berkeley-lab-report-evaluates-increase-electricity-demand-data-centers",
   "finding": "\"Data centers consumed about 4.4% of total U.S. electricity in 2023\"; total data-centre use rose from 58 TWh in 2014 to 176 TWh in 2023. Both sentences re-read at the LBNL summary page by this agent on 12 Nov 2026; the report PDF was not opened.",
   "data_used": "Bottom-up model of server shipments and power draw; national scope", "data_access": "partly_open"},
  {"citation": "Electric Power Research Institute, Powering Intelligence: Analyzing Artificial Intelligence and Data Center Energy Consumption, 2024 white paper (product 3002028905).",
   "url": "https://restservice.epri.com/publicdownload/000000003002028905/0/Product",
   "finding": "\"data centers estimated to comprise a quarter of Virginia's electric load in 2023\"; \"fifteen states account for 80% of the national data center load\". Text of the executive summary read in the PDF by this agent on 12 Nov 2026. The figure is for the state of Virginia; the concentration in Northern Virginia is higher, but that figure was not read. Secondary coverage gives 25.59 percent; not verified in the report's tables.",
   "data_used": "Utility and market-intelligence data; state scope", "data_access": "partly_open"},
 ],
 "prediction": {
  "direction": "-",
  "magnitude": ("Against D1 (all Manhattan LL84 grid electricity, 2024): low figure S_low (reported IT site energy times PUE 1.4, each building capped at its own grid electricity) 1.0 to 1.3 percent; "
                "high figure S_high (IT times PUE 2.0, or for listed buildings the larger of that and the carrier-hotel excess over the median office intensity) 1.8 to 3.5 percent. "
                "The first run's 0.83 percent for IT energy (seen) fixes S_low near 1.16 percent before the cap and S_high_IT near 1.66 percent; the unseen part of S_high is the carrier-hotel excess. "
                "Against D2 (Con Edison non-residential electricity in Manhattan ZIP codes, 16.03 TWh seen) the shares are about 6 percent larger than against D1. "
                "The carrier-hotel excess of the listed buildings exceeds the 97.5th percentile of the same quantity for 2000 size-matched sets of ordinary Manhattan offices."),
  "support_if": ("All four hold: (a) S_high is below 4.4 percent against D1 and against D2; (b) S_low against D1 is between 1.0 and 1.3 percent; (c) S_high against D1 is between 1.8 and 3.5 percent; "
                 "(d) the listed buildings' summed excess intensity exceeds the 97.5th percentile of the size-matched office placebo."),
  "refute_if": "S_high is at or above 4.4 percent against both D1 and D2.",
  "verdict_rule": ("concord.claims.PRECEDENCE rule 1: support_if met -> confirmed; refute_if met -> contested; (a) met but at least one of (b), (c), (d) missed -> unsettled, "
                   "and the miss is reported in prediction_scored; the registered test not run as planned -> no_test. Point estimates decide, not intervals."),
 },
 "plan": (
  "SCOPE AND DATA. Manhattan rows (borough MANHATTAN) of NYC Local Law 84 'Energy and Water Data Disclosure for Local Law 84 2023 to Present (Data for Calendar Year 2022-Present)', Socrata 5zyy-y8am on data.cityofnewyork.us, rowsUpdatedAt 2025-11-25 (checked 12 Nov 2026 in the Socrata catalog: it is the current dataset; the 2022 and earlier calendar years are in 7x5e-2fxh, usc3-8zwd and older ids; monthly data are fvp3-gcb2; no calendar-year 2025 file exists). "
  "report_year 2024 is primary and report_year 2023 is a sensitivity year; the cached file data/derived/further/ll84_mn_bx.csv (query logged in datacentre_sources.json) is reused, so no new LL84 query is made. "
  "Fields: electricity_use_grid_purchase_1 (kWh), property_gfa_calculated (fallback property_gfa_self_reported), data_center_gross_floor_area, data_center_it_site_energy (kWh), data_center_pue, largest_property_use_type, nyc_borough_block_and_lot, parent_property_id, alert and estimated flags.\n"
  "DENOMINATORS. D1 = sum of grid electricity over all Manhattan LL84 rows with usable electricity, built as in the first registration (listed buildings without a 2024 row taken from the latest earlier year). D2 = Utility Energy Registry g2x3-izm4 (data.ny.gov), Con Edison, non-residential consumption (2_nat_consumption), Manhattan ZIP codes 100, 101, 102, 2024; the cached file uer_mn.csv is reused. "
  "Borough total D3 (sensitivity, not decisive) = NYISO Zone J (N.Y.C.) 2024 energy summed from the cached data/derived/further/zonej_daily.csv, multiplied by Manhattan's share of Con Edison delivered electricity, which is UER total consumption (3_nat_consumption) in Manhattan ZIP codes over UER total consumption in all New York City ZIP codes (prefixes 100 to 104 and 110 to 116; one new data.ny.gov query for the non-Manhattan ZIP codes, a denominator query that contains no data-centre field). The Zone J load includes losses and so exceeds delivered electricity; D3 is therefore the largest denominator and gives the smallest shares.\n"
  "ESTIMATOR A (IT times PUE). For each Manhattan building in 2024 with data_center_it_site_energy greater than 0: A_low = min(IT x 1.4, building grid kWh), A_high = min(IT x 2.0, building grid kWh). The cap is stated because IT meters may record tenant-metered or on-site energy that the landlord's grid figure does not contain; the uncapped sums are reported as well. Reported PUE (2 values in the whole file as seen in the first run) is not used except as a sensitivity.\n"
  "ESTIMATOR B (carrier-hotel excess). Median office intensity m = median of grid kWh per square foot over Manhattan 2024 rows with largest_property_use_type 'Office', property GFA of at least 50,000 square feet, positive electricity, parent_property_id not applicable, data_center_gross_floor_area not positive, not on the list, and not flagged for estimated values or a data-centre alert. For each listed building with a usable row (latest earlier year if none in 2024, as before): B = max(0, intensity - m) x GFA. B is an upper figure for the carrier-hotel load because it counts all excess over a typical office as data-centre use (cooling, telecom equipment, but also any non-data-centre excess).\n"
  f"LIST (fixed here, unchanged from the first registration; the rows were selected from public sources before any electricity value was read in the first run): {LIST}\n"
  "COMBINATION. Per building, S_low = A_low. S_high = max(A_high, B) for listed buildings and A_high for other buildings, so IT and excess are not added twice for the same building. S_low and S_high are summed over buildings and divided by D1, D2 and D3. A building can be both listed and IT-reporting.\n"
  "INTERVAL. 2000 bootstrap resamples of the non-listed, non-IT buildings in the denominator (numerator buildings fixed), 2.5th and 97.5th percentiles, as in the first run; a separate range over PUE 1.4 to 2.0 is the S_low to S_high range itself. The intervals do not include reporting error.\n"
  "PLACEBO P_B. 2000 draws, from the Manhattan office pool defined for m (excluding the median-defining restrictions' complement, i.e. the same pool), of one building within 25 percent of GFA for each listed building that has a usable row; compute the same summed excess over m; the 97.5th percentile is the threshold in (d). Also reported: the percentile of the listed set among the draws. P_A: the same A estimator for the Bronx (expected near zero; first run saw zero IT energy there).\n"
  "SENSITIVITY (reported, not decisive). 2023 report_year; uncapped A; use of building-reported PUE where present; median over all Manhattan offices at least 25,000 square feet; dropping rows with estimated-value or alert flags from D1; D3; flagged buildings (data-centre floor area positive, not listed, not reporting IT) allocated area-proportional electricity as in L2 of the first run; and the reverse bound R = 4.4 / S_high, the factor by which unreported data-centre load would have to exceed the allocated load for the share to reach 4.4 percent.\n"
  "MINIMUM DETECTABLE EFFECT AND WHETHER THE TEST CAN FAIL. The refute condition (S_high at or above 4.4 percent) can fail the national comparison only if S_high exceeds the sum of the two first-run numbers already seen: IT energy 0.83 percent of D1 times 2.0 is 1.66 percent, and the whole-building electricity of the whole listed set is 2.23 percent, which bounds B from above; their sum is 3.9 percent, below 4.4. The registrant therefore judges the probability that refute_if is met at about 0.03, and says that condition (a) alone is close to uninformative, which is the defect of the first test in the other direction. The informative conditions are (b), (c) and (d): (b) and (c) fail if the cap binds, if the median office intensity is high relative to the hotels, or if IT-reporting buildings differ from what the first run's totals suggest (registrant's probability that (b) fails 0.25, that (c) fails 0.4); (d) fails if the listed hotels are not distinguishable from ordinary large offices on intensity, which the landlord-reporting caveat makes plausible (probability 0.25). Each of (b), (c), (d) is a range or threshold with a stated alternative outcome, so the test can return unsettled. The bootstrap interval for D1 shares in the first run was about 0.1 to 0.2 percentage points wide for the IT share; this is much narrower than the 0.5 point gap between the ranges, so sampling error does not blur the ranges; reporting error does, and is not in the interval.\n"
  "CONTEXT NOT TESTED. The comparison with Northern Virginia (EPRI: a quarter of Virginia's load in 2023) is stated for the public perception only; a Manhattan figure far below it is expected and is not a registered condition.\n"
  "VERDICT. As in prediction. Anything not named here is exploratory and cannot decide the verdict."),
 "alternatives": [
  "Tenants of carrier hotels meter their own electricity, so the landlord-reported figures (A cap and B) understate the data-centre load; the allocated share would then be a lower bound and a larger true share is compatible with the result.",
  "The IT meter, where present, may belong to enterprise data rooms in offices and hospitals, not to colocation; A then measures server rooms, not carrier hotels.",
  "A median-office baseline is too low for buildings whose telecom and trading tenants use more electricity per square foot than a typical office, so B overstates data-centre use for them.",
  "The 4.4 percent national figure and the Manhattan figure have different denominators (all US electricity versus a dense office and apartment district), so the two are not expected to be equal.",
  "Manhattan data centres draw from Con Edison networks not captured by LL84, such as buildings under 25,000 or 50,000 square feet.",
 ],
 "prior": 0.5,
 "registrant": "Claude (agent), for Jeff Vernon",
 "data_seen_before": {
  "this_agent": ("Before registering this agent read the first claim's registration and outcome and docs/further.md. It therefore knows these results for calendar year 2024: D1 17.06 TWh over 10,647 Manhattan rows; D2 16.03 TWh and UER total 18.33 TWh; reported IT energy 0.14 TWh from 26 buildings, 0.83 percent of D1 (0.79 to 0.86) and 0.88 percent of D2; reported data-centre floor area 0.39 percent of floor area; the ten listed buildings hold 0.38 TWh whole-building, 2.2 percent of D1; the whole-building bound over listed and flagged buildings 16.2 percent; 2023 and 2022 variants; the size-matched office placebo (0.62 percent of D1) and the laboratory and Bronx placebos; that 60 Hudson Street's own row is missing for 2024 and the lot join returns the 56 Hudson Street property; that 2024 rows carry no PUE. "
                "This agent did not open ll84_mn_bx.csv, uer_mn.csv, datacentre_results.json or any per-building value in this session. Office intensities, per-building IT values, per-building excess, the capped and uncapped A sums, the Zone J and five-borough denominators, and the placebo distribution for B have not been seen. "
                "The IT-times-PUE figure is nearly arithmetic on the seen 0.83 percent; the new, unseen quantity is the carrier-hotel excess and the capped allocation, and the placebo for B."),
  "project": ("data/cache/socrata holds four cached queries of 5zyy-y8am (the first claim's fetch and its identifier and metadata queries) and the first claim's outcome is the only claim or outcome on the same data. No other claim in claims/ uses 5zyy-y8am. data/derived has no office-intensity table. The Zone J daily file (data/derived/further/zonej_daily.csv) was built for another claim (further-zonej-demand) and its 2024 values have not been read by this agent."),
  "general_knowledge": "The registrant knows from general knowledge that Manhattan carrier hotels are large and mostly tenant-metered, and holds no value for any building's electricity intensity.",
 },
}
print(claims.register(rec))
