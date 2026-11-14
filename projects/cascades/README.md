# Airways for Impact

**Team:** Cascades
**Members:** Eric Liu, Christina Hart
**Challenge:** Explore Challenge 1: Which interventions in the indoor spaces people live, learn and work improve their health, how strong is the evidence, and, combining with external datasets, what co-benefits do they deliver for carbon, household costs, climate resilience and inequality?
**Pitch slides:** https://docs.google.com/presentation/d/1Q6poHskWIA0ZXq7GOc8BRKFeWasyBeIYui-tbhbejwU/edit?usp=sharing
**Live app:** https://liueric-dev.github.io/Airways/

## What it does

An evidence explorer for funders and policymakers deciding which indoor air quality interventions to invest in. For 8 interventions (damp and mould remediation, insulation, ventilation, filtration, combustion source control, radon mitigation, allergen control, heating and thermal comfort) it shows how strong the evidence is that the problem harms health, how much evidence there is that the fix works, and where the gaps are worth funding.

## How we used the System Public Graph

- **Findings:** we used statistical associations (variable pairs with effect size, confidence interval, p-value and statistic type), plus study country, setting, DOI and System's experimental-trial flag. Relationship study counts were used as a cross-check.
- **What counted as evidence:** 841 curated studies. Findings were matched to interventions with keyword rules on the variable text (see `data/search_log.md` and `data/name_labels.csv`). We did not rely on concept grounding, because its biomedical vocabulary often misfiles building terms; misclassifications were corrected by hand (`scripts/fix_outcomes.py`).
- **Two kinds of evidence:**
  - *Problem evidence:* exposure → health (damp, combustion pollution, radon, allergens, stale air, crowding).
  - *Fix evidence:* the intervention itself → health.
- **Strength rating:** a finding is significant if its CI excludes the null (1 for ratios, 0 otherwise), else p < 0.05.
  - Problem evidence: Strong = 20+ studies and 60%+ significant; Moderate = 5+ studies and 40%+; otherwise Limited.
  - Fix evidence: Strong = 5+ trials and 50%+ significant; Moderate = 5+ studies and 40%+; otherwise Limited.
  - Under 5 studies we show "too few studies to judge".
- **Excluded:** falls and other non-air-quality topics. Missing country or setting is shown as "not recorded", never imputed.
- **Other data combined with it:** UK housing, deprivation, health and overcrowding statistics for context, and cited reviews and reports for co-benefits, costs and trade-offs (see Data sources).

## How to run it

The app is a static site with the data embedded, so no API key is needed.

1. Open `index.html` in a browser (or visit the live app above). `graph.html?a=0` opens one intervention; `graph.html?a=0,2,4` opens a package.
2. To rebuild the data from scratch (optional):
   1. Install requirements: `pip install pandas numpy duckdb pycountry` and `brew install duckdb`
   2. `./setup.sh` downloads the System Public Graph CSVs from Harvard Dataverse and builds `retrofit.duckdb`
   3. `external/fetch_external*.sh` download the external datasets
   4. The Python scripts in `scripts/` build the curated evidence tables, `data/graph.json` and `data/evidence_strength.json`
   5. `app/src/` holds the graph code (`graph.js`, `graph.css`) and the scripts that embed the data into the pages

No API keys are used or committed.

## Data sources

- System Public Graph v2.1, Harvard Dataverse, https://doi.org/10.7910/DVN/7V6JDO (CC BY-NC 4.0)
- English Housing Survey local authority stock condition modelling 2023 (MHCLG, OGL v3): https://www.gov.uk/government/statistics/english-housing-survey-local-authority-housing-stock-condition-modelling-2023
- English Housing Survey 2023-24 health and housing tables (MHCLG, OGL v3): https://www.gov.uk/government/statistics/english-housing-survey-2023-to-2024-health-and-housing-fact-sheet
- Sub-regional fuel poverty 2026 (DESNZ, OGL v3): https://www.gov.uk/government/statistics/sub-regional-fuel-poverty-data-2026-2024-data
- English Indices of Deprivation 2025 (MHCLG, OGL v3): https://www.gov.uk/government/statistics/english-indices-of-deprivation-2025
- EPC live tables (MHCLG, OGL v3): https://www.gov.uk/government/statistical-data-sets/live-tables-on-energy-performance-of-buildings-certificates
- Fingertips asthma admissions and winter mortality (OHID, OGL v3): https://fingertips.phe.org.uk/
- Pupil absence by characteristics (DfE, OGL v3): https://explore-education-statistics.service.gov.uk/data-catalogue/data-set/a5f750db-286a-4d63-a31b-d2a5c1d6d7e0
- Census 2021 TS052 occupancy rating (ONS, OGL v3): https://www.ons.gov.uk/datasets/TS052
- Seven occupied homes in England: IEQ and ventilation (Mendeley Data, CC BY 4.0): https://data.mendeley.com/datasets/47gjkbm29h/2
- US Residential Energy Consumption Survey 2020 (EIA, public domain): https://www.eia.gov/consumption/residential/data/2020/index.php?view=microdata
- BRE Cost of Poor Housing reports (cited figures): https://bregroup.com/the-cost-of-poor-housing
- Cited reviews and reports for co-benefits, costs and caveats, including Cochrane reviews (damp and mould, housing warmth, dust mites), WHO Housing and Health Guidelines, NICE NG6 and NG149, the HAPIN and HAPI trials, and radon cost-effectiveness studies. Full list with links in `data/sources.csv`.

## Limitations

- Findings are associations extracted from papers by a language model, not causal estimates; high significance rates likely partly reflect publication bias.
- Fix evidence is thin: about 82 studies and 15 trials, against about 500 problem studies. Radon has no fix studies.
- Only 2% of studies are from the UK, 28.4% don't record a country and 37.5% don't record a setting.
- The strength rating is our own rule of thumb from study counts, share significant and trials; it does not weight study quality or effect size.
- Keyword matching can miss synonyms or catch irrelevant uses of a term.
- Co-benefits and costs come from cited reports, not the graph. Combined effects of packages are not assessed, and a study can count under more than one intervention.

## AI coding tools

Yes: Claude (Anthropic) and PineComputer's LLMs, for data processing, analysis and code.

## Screenshot

Live app: https://liueric-dev.github.io/Airways/
