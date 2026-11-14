# The data: System Public Graph

What the dataset is, how it is structured, and what that means for getting from a drug to heat.
Verified against the Dataverse snapshot v2.1 (generated 2026-07-08), loaded on 2026-11-13.

## Source and access

| | |
|---|---|
| Bulk snapshot (what we use) | Harvard Dataverse `doi:10.7910/DVN/7V6JDO`, v2.1, CC BY-NC 4.0 |
| Live API | `https://public-api.system.com/v1/...`, `x-api-key` header. Key is in `.env` (`SYSTEM_API_KEY`, git-ignored) since 2026-11-14. 10,000 requests/day. Closed beta. |
| API docs (link given by the user) | https://docs.system.com/system/public/v1.0-api-documentation |
| Other docs | https://docs.system.com/system/public/overview (data dictionary, limitations, methods are subpages) |
| Local copy | `data/raw/*` (CSV) and `data/graph.db` (SQLite). Git-ignored. Rebuild with `sh scripts/fetch_data.sh`. |

The docs say about 20% of associations returned by the API are inaccurately extracted and recommend
keeping only those that also appear in the Dataverse associations CSV. Working from the CSV satisfies that.

## Tables

All columns are loaded as TEXT in SQLite; cast with `+0` for numeric comparisons.
Dots in the relationships column names become underscores (`source_concept.system_id` → `source_concept_system_id`).

| Table | Rows | One row is | Key columns |
|---|---|---|---|
| `associations` | 1,999,877 | one statistical finding from one paper | `system_id`, `study_id`, `system_statistic_type`, `statistic_value`, `ci_lower`, `ci_upper`, `p_value`, `variable_1_name`, `variable_2_name`, `variable_1_concept_id`, `variable_2_concept_id` |
| `studies` | 844,435 | one source paper | `study_id`, `doi`, `pubmed_id`, `population_string`, `study_type` |
| `variables` | 1,774,551 | a variable as worded in a paper | `system_id`, `name`, `concept_id` |
| `concepts` | 45,721 | a Wikidata concept | `system_id`, `wikidata_id`, `wikidata_label`, `wikidata_aliases`, `wikidata_description` |
| `relationships` | 839,872 | a concept pair, aggregated | `relationship_id` (`source|target`), `num_findings`, `num_studies`, `last_published_date` |

Joins: `associations.study_id → studies.study_id`; `associations.variable_N_id → variables.system_id`;
`associations.variable_N_concept_id → concepts.system_id`; `variables.concept_id → concepts.system_id`;
`relationships.source/target_concept_system_id → concepts.system_id`.

## It is a knowledge graph with two layers

- **Concept layer (the graph).** Nodes = concepts. Edges = `relationships` rows. Good for seeing what connects to what.
- **Finding layer (the evidence).** Each edge is a roll-up of `associations` rows whose two variables are grounded to
  those two concepts. This layer has the paper's wording, the number, and the study.

To expand an edge into its evidence:

```sql
SELECT a.variable_1_name, a.variable_2_name, a.system_statistic_type, a.statistic_value,
       a.ci_lower, a.ci_upper, s.doi, s.population_string
FROM associations a JOIN studies s USING (study_id)
WHERE a.variable_1_concept_id = :source AND a.variable_2_concept_id = :target;
```

## Field completeness

| Field | Filled |
|---|---|
| `statistic_value`, both concept IDs | 100% |
| `ci_lower` / `ci_upper` | 48% |
| `p_value` | 69% |
| `studies.doi` | 100% |
| `studies.population_string` | 97% |
| `studies.study_type` | 11%, and the only value is `Experimental Trial` |

Statistic types (`system_statistic_type`), by count: odds_ratio 578k, mean_difference_unstandardized 445k,
coefficient 282k, hazard_ratio 235k, pearson_r 193k, relative_risk_ratio 104k, adjusted_odds_ratio 83k,
adjusted_hazard_ratio 19k, incident_rate_ratio 18k, spearman_correlation 16k, plus 7 rare types.

76% of relationships rest on a single study.

## What is NOT in the data

- No paper title, abstract, full text, authors, or journal. Only DOI and PubMed ID.
- No publication year per study (`relationships.last_published_date` is the newest study per concept pair only).
- No structured sex, age, country, dose, or sample size. These appear only inside `population_string` or a variable name.
- No study design beyond "Experimental Trial" vs blank.
- No guidance documents, drug labels, or pharmacology references. Peer-reviewed findings only.
- Titles, abstracts and years can be fetched by DOI/PMID from PubMed, Europe PMC or OpenAlex. Not done yet.

## Quirks that affect traversal

1. **Context lives in variable names, not concepts.** "mortality (among patients with heatstroke)" is grounded to the
   concept `mortality rate`. A concept-only traversal loses the heat context. Detect the drug side and the heat side by
   **name**, and use concepts only for the node in the middle.
2. **Grounding is noisy.** Examples seen: heat-wave variables grounded to `heat stroke`; "winter" grounded to
   `Winteraceae` (a plant family); "survival" to `survival skill`; many heat variables to a concept labelled `hot`.
   See `reference/heat_concepts.csv`.
3. **Direction is unreliable.** The extractor can swap cause and effect; both `A|B` and `B|A` relationships often exist.
   Treat edges as undirected evidence unless the source is checked.
4. **Self-loops exist** (e.g. `lithium|lithium`): two variables of the same concept. Skip them when drawing.
5. **Comparators are in brackets** in names, e.g. `Paracetamol group [vs Saline group]`.
6. **Name matching produces false positives.** Seen: "ARB" = a river basin; "insulin" as a biomarker rather than a
   therapy; epinephrine as an ICU vasopressor; fever control counted as "temperature". Always read the matched rows.
7. **Absence is not evidence of absence.** Results reported only in tables are under-extracted. Well-known heat-wave
   case-control studies of psychotropics and diuretics are missing from the graph.
8. **The drug can be in the population, not the variables.** PMID 38060348 studies heat and hypoglycemia in insulin
   users; neither variable name mentions insulin. Search `population_string` as well.
9. **A row's number can be right and its label wrong.** Seen four times now (C10, C15, C16). The abstract settles it.

## Live API (tested 2026-11-14)

Base `https://public-api.system.com/v1`. Closed beta; shapes may change.

| Resource | API total | CSV rows | Note |
|---|---|---|---|
| associations | 5,944,001 | 1,999,877 | API includes ungrounded variables and rows removed from the CSV for quality |
| variables | 5,654,715 | 1,774,551 | API includes variables with no `concept_id` |
| concepts | 108,624 | 45,721 | |
| relationships | 626,265 | 839,872 | API has fewer; not investigated |
| studies | 40,307,952 | 844,435 | most presumably have no findings; not investigated |

Endpoints used and how they behave:

| Call | Behaviour observed |
|---|---|
| `GET /variables?search=name:<text>&limit=1000&offset=N` | Returns matching variables. `limit=1000` works. Matching rules undocumented; filter results locally. |
| `GET /variables/{id}/associations?limit=1000` | All findings where the variable is on either side. |
| `GET /associations?filter=variable_2_name:<exact name>` | Exact-name filter works. `search` on names is **not** allowed for associations (IDs only). |
| `GET /studies?filter=pubmed_id:<pmid>` | Returns `study_id`, `doi`, `population` (note: not `population_string`), `study_type`. |
| `GET /relationships?search=source_concept.wikidata_label:<text>&sort=num_studies:desc` | Per docs; nested fields use dot syntax. |
| any list call with `include_total=true` | `total` is the whole table size and **ignores `search`**. Count the rows instead. |

Other rules: filter syntax is `field:value`, `||` for OR; relationship IDs need `|` encoded as `%7C`; null fields are
omitted from the JSON; AND filters and comparison operators are undocumented.

**Trust tags for API rows** (column `api_status` in `data/api/*.csv`):

| Tag | Meaning | Share of 6,335 heat findings |
|---|---|---|
| `in_csv` | Also in the quality-filtered CSV | 2,085 |
| `api_only_ungrounded` | A variable has no concept, so the row is outside the CSV's scope. Unverified, not flagged. | 3,683 |
| `api_only_grounded_suspect` | Both variables grounded, yet absent from the CSV: removed for quality, or added after July 2026 | 567 |

## Paper abstracts

Abstracts are not in the graph but are one request away:
`https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=<pmid,pmid>&rettype=abstract&retmode=text`.
Use this to check any extracted value that will be shown prominently.

## HeatRx bundle (added 2026-11-14)

`bundle/evidence.json` is the single file the app reads. Rebuild, from the repo root:

```
python3 -I scripts/evidence.py data/graph.db data/api reference data/derived/evidence bundle/evidence.json
python3 -I scripts/pubmed_meta.py data/derived/evidence/pmids.txt data/pubmed/summaries.json
python3 -I scripts/merge_papers.py bundle/evidence.json data/pubmed/summaries.json
```

`evidence.py` scans all 2.0M findings (about 7 minutes) and lists the PMIDs; `pubmed_meta.py` fetches titles
(NCBI esummary, cached in `data/pubmed/`); `merge_papers.py` adds them to the bundle in seconds.

| Key | Contents |
|---|---|
| `meta` | date, source and licence, tier rules, counts |
| `classes` | 16 classes: id, label, named in brief, member drugs, evidence totals |
| `hubs`, `effects` | body systems and effects, each effect with its hub |
| `links` | every class × effect with any evidence: tier, drug-arm study counts by direction, finding ids, heat-arm size, direct ids |
| `heat_arms` | per effect: heat-side studies by direction, explicitly-high-heat studies, finding ids |
| `direct` | curated direct findings with the abstract's wording, statistic, scope, provenance, check status, heat-level bands |
| `findings` | every referenced graph row: names as worded, statistic, CI, direction, source tag, DOI, population, correction |
| `papers` | PMID → title, journal, year, first author |

`bundle/check.html` renders the class × effect table from the bundle. `merge_papers.py` generates it from
`scripts/check_template.html` with the data inlined, so it opens anywhere (including the app's file pane, which shows
HTML as a snapshot without neighbouring files). `bundle/evidence.js` holds the same data as `window.HEATRX_BUNDLE`.
Row-level CSVs for reading: `data/derived/evidence/{drug_arm_rows,heat_arm_rows,direct_candidates,links}.csv`.

### Outside sources (phase 2)

After the graph build, `scripts/merge_outside.py bundle/evidence.json reference` adds data from outside the graph:

| Key | Source | File |
|---|---|---|
| `guidance` | 8 heat-health guidance documents, read and coded by hand | `reference/guidance/documents.csv`, `class_mentions.csv`, `actions.csv` |
| `effect_actions` | Which action bucket each body effect points to, from guidance wording | `reference/effect_actions.csv` |
| `classes[].specialties`, `specialties` | CMS Medicare Part D Prescribers by Provider and Drug, data year 2024 (data.cms.gov API, dataset 9552739e-3d05-4c1b-8eff-ecabf391e2e5), claims by prescriber type | `scripts/medicare_specialty.py` → `reference/medicare_specialty.json`, cache `data/medicare/` |
| `scenarios` | NWS alerts for zone NYZ072 and Central Park daily observations, via the Iowa Environmental Mesonet | `scripts/nyc_scenario.py` → `reference/nyc_heat_scenarios.json`, raw `data/weather/` |
| `gaps` | Evidence vs guidance per class and per class × effect | computed in `merge_outside.py` |
| `links[].guidance_docs`, tier `guidance_only` | Guidance documents naming each class × effect; links named only by guidance | computed |

Rerun order after any graph rebuild: `evidence.py` → `pubmed_meta.py` → `merge_papers.py` → `merge_outside.py`.

Population strings exist only for CSV studies; API-only rows have no population locally.
The bundle is derived from CC BY-NC 4.0 data; keep the attribution in `meta.source`.
