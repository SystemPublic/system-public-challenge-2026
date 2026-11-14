# Insights: connections that emerge from the concept map

Sources: SPG v1 associations/concepts (Dataverse deposit); NYC open data v1.0.0 collections on Underlay (environment-health, heat-complaints, leading-causes-of-death, street-trees). Concept map: `mapping/out/concept_map.csv`.

## Confirmed — research and the city describe the same links

1132 concept pairs have published associations in the SPG *and* map to measurable NYC indicators (1047 distinct construct pairs; self-pairs from a concept's own measures excluded below). Strongest cross-concept pairs by evidence volume:

| SPG concept pair (domains) | assoc | studies | median effect | city UHF42 rho | NYC measures (first each side) |
|---|---|---|---|---|---|
| **body mass index** (beyond-473) × **arterial hypertension** (Cardiovascular) | 348 | 214 | 1.52 | — | Overweight, Number ↔ Essential Hypertension and Renal Diseases |
| **cardiovascular disease** (Cardiovascular) × **body mass index** (beyond-473) | 226 | 130 | 1.43 | 0.692⚠ | Diseases of Heart ↔ Overweight, Number |
| **stroke** (Cardiovascular) × **arterial hypertension** (Cardiovascular) | 211 | 166 | 1.90 | — | Cerebrovascular Disease ↔ Essential Hypertension and Renal Diseases |
| **asthma** (Respiratory) × **body mass index** (beyond-473) | 187 | 106 | 1.39 | 0.833⚠ | Asthma (youth), Number ↔ Overweight, Number |
| **cardiovascular disease** (Cardiovascular) × **arterial hypertension** (Cardiovascular) | 140 | 90 | 1.79 | — | Diseases of Heart ↔ Essential Hypertension and Renal Diseases |
| **stroke** (Cardiovascular) × **body mass index** (beyond-473) | 122 | 80 | 1.21 | — | Cerebrovascular Disease ↔ Overweight, Number |
| **diabetes** (beyond-473) × **body mass index** (beyond-473) | 119 | 85 | 1.90 | 0.841 | Diabetes Mellitus ↔ Overweight, Number |
| **diabetes** (beyond-473) × **stroke** (Cardiovascular) | 110 | 90 | 1.71 | — | Diabetes Mellitus ↔ Cerebrovascular Disease |
| **asthma** (Respiratory) × **obesity** (beyond-473) | 107 | 66 | 1.68 | 0.767⚠ | Asthma (youth), Number ↔ Overweight or obesity (youth), Number |
| **HIV** (beyond-473) × **tuberculosis** (beyond-473) | 105 | 83 | 3.66 | — | Human Immunodeficiency Virus Disease ↔ Tuberculosis |
| **arterial hypertension** (Cardiovascular) × **overweight** (beyond-473) | 95 | 72 | 2.00 | — | Essential Hypertension and Renal Diseases ↔ Overweight, Number |
| **asthma** (Respiratory) × **air pollution** (Air pollution) | 89 | 40 | 1.17 | 0.556⚠ | Asthma (youth), Number ↔ Deaths from PM2.5, Estimated annual number (age 30+) |
| **asthma** (Respiratory) × **particulates** (beyond-473) | 87 | 53 | 1.14 | 0.551 | Asthma (youth), Number ↔ Citywide PM2.5, PM2.5 annual average |
| **cardiovascular disease** (Cardiovascular) × **diabetes** (beyond-473) | 82 | 69 | 1.75 | 0.639⚠ | Diseases of Heart ↔ Diabetes Mellitus |
| **body mass index** (beyond-473) × **overweight** (beyond-473) | 75 | 53 | 2.10 | 1.0 | Overweight, Number ↔ Overweight, Number |

ρ⚠ = the city check's best-correlating measure pair includes a modeled burden measure (e.g. 'PM2.5 health burden (heart)') — such ρ reflect neighborhood structure shared by two modeled/survey layers, not observed disease; the exact measure pair behind every ρ is in `city_check_measures` in `out/connections.csv`. Self-pairs (a concept associated with its own measures) and all 85 remaining pairs: `out/connections.csv`.

## Bridged — links no single dataset holds alone

Cross-theme pairs of mapped NYC measures (|Spearman| ≥ 0.5 across UHF42 districts, different indicator themes, no shared label family) where the SPG holds **no direct association** between their mapped concepts. The strongest observed (non-modeled) candidates:

| NYC measure pair (concepts) | city UHF42 rho | vintages | caveat |
|---|---|---|---|
| Nitrogen dioxide, Winter mean (nitrogen dioxide) × Walkability, Score (physical activity) | **0.895** | 2009-2025 / 2011-2011 | — |
| Death before 65, Number (Mortality, Premature) × Difficulty walking, Number (mobility disability) | **0.887** | 2014-2020 / 2008-2019 | — |
| Nitrogen dioxide, Annual mean (nitrogen dioxide) × Walkability, Score (physical activity) | **0.886** | 2009-2025 / 2011-2011 | — |
| Owner-occupied homes, Percent (housing) × Mice or rats (outside), Percent (rodent control; Murinae) | **-0.88** | 2007-2019 / 2004-2020 | — |
| Death before 65, Number (Mortality, Premature) × Poverty, Number (poverty) | **0.875** | 2014-2020 / 2007-2019 | — |
| Nitrogen dioxide, Summer mean (nitrogen dioxide) × Walkability, Score (physical activity) | **0.874** | 2009-2025 / 2011-2011 | — |
| Death (perinatal), Number (perinatal mortality; perinatal death) × Poverty, Number (poverty) | **0.874** | 1998-2011 / 2007-2019 | — |
| Child poverty, Percent (child poverty) × Households with AC, Percent (with AC) (air conditioning) | **-0.866** | 2007-2017 / 2014-2023 | — |
| Housing problems, Percent (housing quality) × Households with AC, Percent (with AC) (air conditioning) | **-0.864** | 2014-2023 / 2014-2023 | — |
| Death (neonatal), Number (neonatal mortality) × Asthma hospitalizations (age 4 and under), Number (hospitalization; childhood asthma; asthma) | **0.857** | 1998-2020 / 1998-2023 | — |
| Death (neonatal), Number (neonatal mortality) × Asthma ED visits (age 4 and under), Number (emergency department; childhood asthma; asthma) | **0.857** | 1998-2020 / 2005-2023 | — |
| Poverty, Percent (poverty) × Households with AC, Percent (with AC) (air conditioning) | **-0.856** | 2007-2019 / 2014-2023 | — |

Observed (non-modeled) bridge candidates: 645; modeled-attribution pairs excluded above because EHDP burden measures share estimation machinery and correlate by construction. Full list: `out/bridges.csv`.

## Contested — where research and city data disagree or misalign

1. **Green space × emergency care — absent in research, mediated in the city.** SPG holds **0 associations** between green-space and emergency-care concepts. The city's own data shows *why a naive check fails and what the real link is*: vegetation cover does not correlate directly with heat ED visits across UHF42 districts (rho ≈ 0.02, see spot-checks) — but it clearly depresses surface temperature (rho = -0.40), and the graph itself supplies 70 heat × emergency-care associations. So the chain cover → cooler surfaces → fewer heat outcomes is supported piecewise by the two datasets together, while the direct edge is untested in the literature. That is precisely the 'link neither dataset holds alone' — and a research target.

2. **Vintage misalignment.** Street-tree census is 2015; vegetation cover 2010-2017; surface temperature a single day (2018); heat outcomes 2000-2022; 311 complaints 2024-2026. Cross-dataset claims must state which years each leg rests on — the map carries year ranges on every row.

3. **Modeled vs observed.** EHDP 'burden' measures (PM2.5 asthma ED visits, deaths from PM2.5/ozone, heat vulnerability index) are modeled attributions (`howCalculated`), not observations. Confirmations that use them as endpoints reproduce the model, not the city — flagged `modeled1/2` in `out/bridges.csv`.

4. **Counts vs rates vs age-adjusted rates.** The same EHDP indicator appears as Number, Percent, rate and age-adjusted rate measures; SPG associations mix OR/RR/r with 89% null study_type. Comparing effect magnitudes across that boundary is not valid — compare directions only.

5. **Construct ≠ operationalization.** 'Heat ED visits' counts heat-stress visits during warm months (May-September, ICD-coded); SPG heat concepts span heat wave, extreme heat, heat stroke, heat illness. The map types these as broader-narrower/related-component so downstream claims inherit the right caveats.

## Research needed — the gap map

**NYC concepts with no research-graph counterpart** (research the graph hasn't absorbed):

- Citi Bike stations ×4
- Average Citi Bike availability ×3
- Work-related deaths (construction industry) ×3
- Supplemental heat ×2
- Home fall ED visits ×2
- Home fall hospitalizations ×2
- Neighborhood safety ×2
- Work-related deaths (all industries) ×2
- Children in homes with visible mold or mildew (age 1-13) ×2
- Mold ×2
- Homes with mold ×1
- Bike lanes ×1
- Insitu or Benign / Uncertain Neoplasms ×1
- street-tree species ×132 (no species-level research concepts exist; street trees as a construct connect through the EHDP vegetation/tree-shade measures, which ARE mapped)

**SPG challenge-domain concepts with no NYC measurable counterpart** (what the city doesn't measure — where city data collection could grow):

- **Air pollution**: smog, ozone layer, radioactive air pollutants, occupational air pollutants, Air Pollution, Radioactive, ozone depletion, air pollutant, indoor air pollution
- **Cardiovascular**: Masked Hypertension, out-of-hospital cardiac arrest, cardiovascular tuberculosis, artificial heart, sudden cardiac death, cardiac valve annuloplasty, management of hypertension, heart septal defect, blunt cardiac injury, cardiac catheterization … +129 more
- **Emergency care**: ambulance, Ambulance Diversion, Insurance, Hospitalization, length of stay
- **Flooding & storms**: radio immunoprecipitation assay, flooding, precipitation, immunoprecipitation, precipitation, Fractional Precipitation, rainfall intensity, flood disaster
- **Green space**: forestry, forest, tree ring, Kyasanur forest disease
- **Heat & temperature**: thermoregulation, heat shock proteins, Heat shock protein family A (Hsp70) member 5, body temperature, sea surface temperature, human body temperature, HSP72 Heat-Shock Proteins, Transition temperature, hyperthermia therapy, Heat shock transcription factor family … +16 more
- **Housing & energy**: homeless person, cooling down, housing cooperative, public housing
- **Mental health**: long-term depression, Cortical spreading depression, psychotic depression, Mental Health Associations, death anxiety, psychiatric somatotherapy, community mental health service, test anxiety, psychological theory, involuntary psychiatric treatment … +54 more
- **Mortality**: Excess mortality, sudden cardiac death, death anxiety, sudden unexpected death in epilepsy, fetal death, stages of death, cell death, COVID-19 mortality, Death effector domain, parental death … +21 more
- **Respiratory**: bovine respiratory disease complex, giant-cell carcinoma of the lung, pulmonary surfactant, bronchopulmonary dysplasia, Aortopulmonary septal defect, lung, total lungs capacity, non-small-cell lung carcinoma, idiopathic pulmonary fibrosis, pulmonary echinococcosis … +105 more
- **Socioeconomic**: socioeconomic status, income inequality, sensory deprivation, income, food deprivation, Employee Retirement Income Security Act of 1974, personal income, social deprivation, psychosocial deprivation, net income … +20 more

**What would settle the contests:**

- Green space → ED visits: a cohort or quasi-experimental study (tree planting natural experiments) estimating green-space effects on acute care use, measured at the neighborhood level NYC already publishes.

- Vintage alignment: a refreshed tree census aligned to EHDP outcome years, or EHDP vegetation layers extended past 2017.

- Modeled burden: publish the attribution-model covariates so city-side correlations can be adjusted for shared estimation inputs.

## Quantitative spot-checks (UHF42 cross-section)

Direction checks only — not epidemiology; cross-sectional correlations across 42 districts.

| check | rho | n | expectation from SPG |
|---|---|---|---|
| surface temperature vs heat ED visits (rate) (measure:688 vs measure:537) | **0.256** | 42 | SPG: heat x emergency care = 70 associations with positive effect sizes; expect rho > 0 |
| grass and tree cover vs surface temperature (measure:690 vs measure:688) | **-0.396** | 42 | SPG: green space x heat = 12 associations; expect rho < 0 (cover cools surfaces) |
| grass and tree cover vs heat ED visits (rate) (measure:690 vs measure:537) | **0.024** | 42 | SPG: green space x emergency care = 0 associations; naive cross-sectional rho near 0 would show the link is mediated (via heat), not direct - i.e. exactly what a study needs to untangle |
