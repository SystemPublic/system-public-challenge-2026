# System Public Graph — EDA notes (2026-11-13)

Data: Harvard Dataverse deposit `doi:10.7910/DVN/7V6JDO` (v2), loaded into `data/graph.duckdb` via `eda/load.sql`.
License CC BY-NC 4.0. Do not commit `data/`.

## What the data is
A graph of quantitative findings extracted from peer-reviewed papers.

| Table | Dataverse rows | API rows | One row is |
|---|---:|---:|---|
| associations | 2.0M | 5.94M | one statistical result: var1 ↔ var2, effect size, CI, p |
| variables | 1.77M | 5.65M | a variable *as worded in a paper* |
| concepts | 45.7K | 108.6K | Wikidata-grounded concept that variables map to |
| relationships | 840K | 626K | concept → concept edge, rolled up (num_findings, num_studies) |
| studies | 844K | 40.3M | paper: DOI, PMID, free-text population |

Join keys: `associations.variable_{1,2}_concept_id → concepts.system_id`, `associations.study_id → studies.study_id`,
`relationship_id = "<source concept id>|<target concept id>"`.

## Key findings
- **Dataverse is the grounded, cleaned subset.** Every CSV association has both concept IDs; the API also has ungrounded ones.
  Per concept, the API holds ~1.5–2.5× the CSV (asthma 12.4K vs 23.6K, malaria 2.6K vs 5.2K).
  Docs: ~20% of API associations are mis-extracted and were dropped from the CSV → use CSV as the trusted set, API for breadth.
- **Effect sizes are mixed types.** odds ratio 29%, unstandardized mean difference 22%, regression coefficient 14%,
  hazard ratio 12%, Pearson r 10%. Use `system_statistic_type` (18 clean values), not `statistic_type` (9.4K raw spellings).
  Don't pool across types; ratios (OR/HR/RR) are the most comparable family.
- **Uncertainty is patchy.** CI missing for 52% overall (94% for mean differences, 98% for Pearson r); p-value missing 31%.
  `ci_level` is often missing/0 even when a CI exists.
- **Outliers exist.** Values up to 5.6e75; 820 ratios ≤ 0; 175 values outside their own CI. Filter before plotting.
- **Evidence is long-tailed.** 76% of relationships rest on a single study; median 1. Top edges: radiotherapy→survival (945 studies),
  BMI→mortality (795).
- **Strong biomedical skew.** Most-studied concepts: mortality, survival, BMI, depression, length of stay, stroke, blood pressure.
- **Variable wording is fragmented.** "mortality rate" has 52K distinct variable names. Count by concept, not by variable.
- **Grounding noise.** e.g. "survival skill" (should be survival), "female organism" (sex), 7.6K self-loop relationships (asthma→asthma).
- **No study metadata.** `study_type` is only "Experimental Trial" or null (89% null). No year/title/country —
  pull from PubMed/OpenAlex via PMID/DOI. `relationships.last_published_date` gives a rough time axis (peaks 2022).

## Coverage by challenge topic (associations, CSV / API)
| Concept | CSV | API |
|---|---:|---:|
| asthma | 12,418 | 23,574 |
| malaria | 2,564 | 5,244 |
| endometriosis | 2,237 | 4,029 |
| ventilation (incl. ICU!) | 1,825 | 3,773 |
| unemployment | 1,816 | 2,893 |
| menopause | 1,585 | 2,627 |
| air pollution | 1,120 | 2,734 |
| shift work | 949 | 1,474 |
| job satisfaction | 847 | 1,578 |
| lithium | 504 | 986 |
| heat stroke | 114 | 211 |
| wage | 26 | 47 |
| artemisinin | 3 | 5 |

Thin spots (wage, artemisinin, heat) are themselves a finding — several challenges reward mapping gaps.
Counts are for one exact concept; related concepts (salary, income, ACT drugs, …) need grouping.

## Neo4j (local, Docker)
Container `spg-neo4j` (neo4j:5-community), DB files in `data/neo4j/data`, built by `eda/neo4j_export.sql` + `neo4j-admin database import full`.
Browser: http://localhost:7474 → connect `neo4j://localhost:7687`, no password (bound to localhost only).
Start/stop: `docker start spg-neo4j` / `docker stop spg-neo4j`. Starter Cypher: `eda/starter_queries.cypher`.
Visual EDA report: https://claude.ai/artifact/TpvEqPtPM5F8M5SnVYh9hP

## Challenge profiles
Sub-topic search terms per challenge: `eda/challenge_terms.csv` (regex on variable + concept names; `rx2` = must also match, `exclude` = drop).
Metrics: `eda/challenge_profiles.sql` (~8 min). Results are in the dashboard's Challenge explorer.
