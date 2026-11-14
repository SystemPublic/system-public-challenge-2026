# Data for the Retrofit Evidence Explorer

Everything here is small enough to commit. The full graph lives in `retrofit.duckdb` (not committed; rebuild with `./setup.sh`), which also contains every table below.

## From the System Public Graph (curated Dataverse CSV v2.1, doi:10.7910/DVN/7V6JDO)

| File | Rows | What it is |
|---|---|---|
| `evidence.csv` | 1,807 | Findings linked to the 8 intervention groups. `relevance` = keep (1,424) or context (383). One row = one statistical finding with its variables, statistic, CI, p-value, study DOI, population. Review columns: `review_status`, `component`, `plain_language`, `notes` |
| `coverage.csv` | 16 | Per group x role (exposure / intervention): findings, studies, studies linked to a health outcome, trial studies, UK studies. Zeros are real "no match under this search" gaps |
| `gap_grid.csv` | ~100 | Distinct studies per group x role x outcome group (asthma, other respiratory, allergy, mental health, cardiovascular, cancer, mortality/hospital use) |
| `name_labels.csv` | 2,180 | Audit trail: every unique matched variable name and its keep / context / drop label |
| `candidates.csv` | 3,705 | Raw keyword + concept matches before labelling |
| `search_log.md`, `qa_summary.md` | | Exact search terms, exclusions, date; precision of each search route |

**The 8 groups:** Moisture & mould remediation; Building fabric (insulation, airtightness); Ventilation & source capture; Particle filtration; Clean cooking; Indoor temperature (heating & cooling); Radon mitigation; Allergen & pest control (household).

**Roles:** `exposure` = the variable is an indoor condition (mould, gas cooking, cold home). `intervention` = the variable names a fix or a type of system (dehumidifier, heat pump, LPG stove). Exposure findings are not evidence that a fix works.

## External UK context (`la_context.csv`, `lsoa_context.csv`, `../external/bre_costs.csv`)

Area data describes need and context. It cannot show the effect of an intervention. See `external_sources.csv` for provenance of every column.

| Column | Source | Geography |
|---|---|---|
| `damp_pct_ehs2023`, `cat1_hazard_pct_ehs2023`, `non_decent_pct_ehs2023` | EHS LA stock condition modelling 2023 (modelled) | 296 LAs |
| `fuel_poverty_pct_2024` | DESNZ sub-regional fuel poverty 2026 (LILEE) | LA + LSOA |
| `imd_score_popweighted`, `living_env_score_popweighted`, `indoors_subdomain_popweighted`, `pct_lsoas_most_deprived_decile` | IoD 2025 File 7 | LSOA; LA = pop-weighted |
| `epc_pct_FG_recent`, `epc_pct_ABC_recent`, `epc_avg_energy_kwh_per_m2_recent`, `epc_avg_co2_t_per_home_recent`, `epc_avg_energy_cost_gbp_per_home_recent` | MHCLG EPC live tables EB1/EB3, last 8 quarters | LA (homes with a new certificate only) |
| `asthma_adm_u19_per100k` | OHID Fingertips 90810 | District/UA |
| `winter_mortality_index` | OHID Fingertips 90360 | District/UA |
| `bre_costs.csv` | BRE Cost of Poor Housing reports, EHS headline | England, hand-entered with source URLs |

Rebuild: `python scripts/build_evidence.py && python scripts/finalize_evidence.py && python scripts/build_external.py` (external downloads: `./external/fetch_external.sh`).

## Provenance and gaps (added 14 Nov, 11:40)

| File | What it is |
|---|---|
| `sources.csv` | Register of every source considered (23): provider, URL, **country and world region**, setting (home / school / workplace), data type (graph-extracted, observed measurement, modelled statistic, survey, published trial), licence, access, ingestion status, which groups and outcomes it informs, and whether it can show an intervention effect |
| `gaps.csv` | Gaps register. (1) Every group x role x outcome cell with its study count, UK study count and status: *no match under this search*, thin, moderate, well studied. (2) Setting gaps (home / school / workplace). (3) Data gaps: no open dataset linking the intervention to outcomes. Each row records the search scope |
| `coverage_by_region.csv`, `coverage_by_setting.csv` | Distinct relevant studies per group by world region and by setting |

`evidence.csv` now also has `study_country`, `study_region` (UK, Europe non-UK, North America, East Asia, South Asia, Africa, Latin America, Oceania, Multi-country, Unknown) and `setting`, parsed from each study's population description. About 27% of studies have no parseable country and are labelled Unknown rather than guessed.

## Round 2 tables (loaded Nov 14, ~12:40)
- `seven_homes_summary` (data/seven_homes_summary.csv): 7 English homes (London + Oxford), 2019-2022, one row per sensor transmitter. Median / p95 CO2, PM2.5, PM10, NO2, RH, temp; % time CO2 >1000/1500 ppm; % days PM2.5 >15 (WHO 24-h guideline); % time RH >70%. Room labels are NOT in the raw file: `likely_outdoor` = lowest-CO2 unit (heuristic); units with CO2/T/RH only are probably bedrooms. NO2 is an uncalibrated low-cost sensor (ppm, can be negative). Do not treat as representative; it is exposure context, not intervention evidence. Built from raw CSVs only (the dataset's .pkl files were not opened).
- `ehs_health_housing` (data/ehs_health_housing_long.csv): EHS 2023-24 health & housing annex AT7-AT16, long format (table, title, block = tenure/income group, row, column, value; thousands of households + sample size). Damp, keeping warm, Category 1 hazards, overcrowding × household/child illness, by tenure and income. Cross-sectional association only.
- `pupil_absence_la` (data/pupil_absence_la.csv): England upper-tier LA (153), 2016/17-2024/25, all phases: illness absence % = authorised illness sessions / possible sessions. Upper-tier codes, so it does not join directly to `la_context` (lower-tier LADs).
- `recs2020_state` (data/recs2020_state_cooking_heating.csv): US RECS 2020 weighted share of households cooking with natural gas and using wood for heating, by state. National: gas cooking 38.1%, propane 4.7%, wood heating 8.9%, induction 3.2%.

## Crowding (added Nov 14, ~12:45) — team decision: an EXPOSURE linked to Ventilation and Moisture & mould, not a 9th intervention
- `evidence` rows with `group = 'Crowding (exposure)'`, `role = 'exposure'`, new column `linked_groups = 'Ventilation & source capture; Moisture & mould remediation'` (blank for all other rows).
- `relevance = keep`: true crowding measures (overcrowding, persons per room, bedroom sharing) — 108 studies, only 5 UK. `relevance = context`: household-size proxies with no room denominator — 247 studies, treat as weak.
- New outcome label `Infection` (TB, RSV, H. pylori, otitis, diarrhoea, etc.) used for crowding rows; this is the largest crowding outcome.
- Frontend suggestion: show crowding inside the Ventilation and Moisture & mould panels as "makes this worse", not as its own tile.
- UK numbers: `ehs_health_housing` AT10 (overcrowded 55.2% vs 38.1% households with long-term illness). Area data: `overcrowded_pct_census2021` column will be added to `la_context`/`lsoa_context` by `scripts/build_census_crowding.py` after `fetch_external3.sh` runs.

## gaps.csv refresh (Nov 14, ~12:50)
- New `air_quality_priority` column: core | core (exposure) [crowding] | air-quality trade-off [building fabric] | secondary (parked) [indoor temperature] | cross-cutting.
- New outcome `Infection` in the group x role x outcome grid; crowding intervention cells are `not applicable` (not a building intervention).
- New gap_type `evidence: low certainty or null result` (7 rows: Cochrane mould, dust mite, HAPIN, HEPA, school ventilation, radon, insulation targeting), each with source_id in brackets.
- 5 new data gaps: UK crowding evidence, UK gas-cooking share, California range-hood data, retrofit quality (NAO), NICE NG149 research recommendations.

## graph.json (for the graph view; Nov 14 ~13:00)
`data/graph.json` = `{meta, nodes, edges}`. Rebuild: `python3 scripts/export_graph.py`.
- nodes (26): `intervention:<group>` (8), `exposure:<group>` (9 incl. Crowding), `outcome:<outcome>` (8 health outcomes + "Indoor exposure measured"). Fields: label, group, color, air_quality_priority, studies, uk_studies, findings, context_studies, regions{}, settings{}, certainty_notes[], data_gaps[], source_ids[].
- edges (125): `acts_on` intervention->exposure (8); `worsens` crowding->ventilation/moisture exposure (2); `evidence` (115) intervention|exposure -> outcome with studies, uk_studies, findings_total, status, is_gap, findings[] (up to 30, UK and trials first: statistic, CI, p, population, country, DOI, PubMed).
- 43 gap edges (`is_gap: true`) = intervention -> outcome with no study found; draw dashed.
- Pipeline order if rebuilding everything: build_evidence -> apply_labels -> finalize_evidence -> tag_crowding -> tag_regions -> fix_outcomes -> build_gaps -> export_graph.
- Fix applied: outcomes containing cancer terms now go to Cancer (148 rows; e.g. radon -> lung cancer was in Other respiratory).
- graph.json v2 (Nov 14 ~13:05): intervention nodes add `action_label` ("Fix damp & mould") and `co_benefits[]` ({kind: co_benefit|trade_off|data_gap, text, source_id}); intervention->outcome evidence edges add `expected_via_exposure_studies` (studies linking that group's exposure to the outcome) for the 2-step "expected health gain" view.
