# System Public Graph: Dataverse extract (overnight run, 2026-11-14)

Spec §8.5a roles 1 (evidence source), 3 (two-hop pathways), 4 (gap finder) and 5 (audit lookups).
No System API key was available, so everything comes from the **public Dataverse bulk release**. No API calls were made.

## Source

- Harvard Dataverse, System Public Graph, doi:10.7910/DVN/7V6JDO, **dataset version 2.1** (released 2026-07-22; MANIFEST generated_at 2026-07-08). Accessed 2026-11-14.
- File list: `https://dataverse.harvard.edu/api/datasets/:persistentId/?persistentId=doi:10.7910/DVN/7V6JDO`
- Downloads: `https://dataverse.harvard.edu/api/access/datafile/{id}` (`?format=original` for the .tab files)

| Table | Dataverse file id | Rows (MANIFEST) | What we did |
|---|---|---|---|
| associations | 14061020 | 1,999,877 | Downloaded (442 MB, md5 matches the manifest), full streaming scan |
| studies | 14061022 (original CSV) | 844,435 | Downloaded (134 MB, md5 matches) |
| concepts | 14061021 (original CSV) | 45,721 | Downloaded (7.8 MB) |
| relationships | 14061025 | 839,872 | **Streamed and filtered without saving** (saves ~395 MB of disk); 31,773 edges kept |
| variables | 14061023 | 1,774,551 | **Not downloaded.** It isn't needed because the associations table already carries variable names and concept ids |
| MANIFEST.json | 14061024 | | Downloaded |

The big files are in `dataverse/` (gitignored), about 557 MB. Nothing was deleted, because free disk stayed at about 3.0 GB. If space gets tight, `dataverse/studies.csv` and `dataverse/associations.csv` can be deleted and downloaded again. The Step 3 API-vs-Dataverse cross-check needs `associations.csv`, so delete it last.

PubMed E-utilities esummary (`https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi`) was used for publication dates and titles, because **the Dataverse studies table has no publication date**. 1,207 PMIDs were looked up, 2026-11-14.

## Scripts (in `scripts/`, all documented in their docstrings)

1. `system_terms.py`: term lists. The 15 drug groups extend `graph_check.py`'s lists. There are 4 comparator groups (NSAIDs, benzodiazepines, sulfonylureas, any diuretic), 6 mediators and 4 heat groups. The lists include exclusion patterns, such as "insulin resistance", "neuroleptic malignant", "sweat chloride" and "methamphetamine".
2. `system_dataverse_scan.py`: one pass over associations, producing `assoc_relevant.csv`, `assoc_master_pmids.csv` and `master_pmids.csv`.
3. `system_relationships_filter.py`: streams relationships from Dataverse and produces `relationships_filtered.csv`.
4. `system_pubmed_dates.py`: produces `pubmed_dates.csv` (cached; can be re-run).
5. `system_build_outputs.py`: builds everything in `data/processed/system_*.csv`.
6. `graph_check.py csv dataverse/associations.csv`: re-run unchanged. It **overwrote `data/graph_coverage.csv`** with its csv-mode output. The earlier API-mode version (13 Nov) is backed up here as `graph_coverage_api_2026-11-13_backup.csv`. The log is in `graph_check_csv_run.log`.

To reproduce:
```
python3 -I scripts/system_dataverse_scan.py data/raw/system/dataverse/associations.csv data/raw/system data/master_list_graph_status.csv "data/Drug heat risk master list.csv"
python3 -I scripts/system_relationships_filter.py data/raw/system/relationships_filtered.csv
python3 -I scripts/system_build_outputs.py data/raw/system --pmids-only data/raw/system/pmids_for_dates.txt
python3 -I scripts/system_pubmed_dates.py data/raw/system/pubmed_dates.csv data/raw/system/pmids_for_dates.txt
python3 -I scripts/system_build_outputs.py data/raw/system data/processed
```
The scripts use only the standard library. `graph_check.py` needs pandas: `uv run --with pandas python scripts/graph_check.py csv ...`.

## Files here (raw, intermediate)

| File | Rows | Content |
|---|---|---|
| `assoc_relevant.csv` | 94,340 | Every association where either variable name matches any drug, mediator or heat term, plus 6 match columns |
| `assoc_master_pmids.csv` | 19 | Every association whose PMID is cited in the two master lists |
| `master_pmids.csv` | 51 PMIDs + 16 DOIs | IDs pulled from `data/master_list_graph_status.csv` and `data/Drug heat risk master list.csv` |
| `relationships_filtered.csv` | 31,773 | Relationship edges where either concept **label** matches a drug, mediator or heat term |
| `pubmed_dates.csv` | 1,207 | pmid, pubdate, sortpubdate, year, title, journal |
| `graph_coverage_api_2026-11-13_backup.csv` | | Old API-mode coverage file |

## Processed outputs (`data/processed/`)

| File | Rows | What it is |
|---|---|---|
| `system_drug_mediator_findings.csv` | 1,835 (1,644 findings, 1,082 studies) | One row per association × drug group × mediator. Columns: effect size, CI, p, statistic type, study id, PMID, DOI, PubMed date and title, population_string, study_type, plus `auto_flags_heuristic` |
| `system_heat_mediator_findings.csv` | 104 (101 findings, 71 studies; 80 rows unflagged) | Heat-variable × mediator-variable findings |
| `system_drug_heat_direct_findings.csv` | 18 (14 studies) | Direct drug × heat. `matched_by` says whether the row came from our HEAT terms or only from graph_check's core terms (body temperature, sweating) |
| `system_pathways.csv` | 114 | 19 drug groups × 6 mediators: findings and distinct studies per leg, heat-leg breakdown, direct findings, concept-level relationship totals, and a score of sqrt(drug-leg studies × heat-leg studies) |
| `system_pathway_drug_summary.csv` | 19 | Per-drug rollup for validation. Three rankings: total score, score without blood pressure, and **share of the drug's studies that reach a non-BP mediator** (a specificity measure) |
| `system_hidden_drug_candidates.csv` | 262 (224 not in our 15) | **UNVALIDATED raw candidates.** Drug-like concepts (Wikidata description heuristic) that link to mediators in association rows. Includes an inpatient/procedural heuristic flag |
| `system_master_list_study_findings.csv` | 81 | Per master-list PMID/DOI: in Dataverse? number of findings, the finding rows, and the earlier API status for comparison |
| `system_relationships_subset.csv` | 932 | Concept-level edges where both ends are drug, mediator or heat concepts: num_findings, num_studies, last_published_date |
| `system_untested_links.csv` | 316 | Drug group (or candidate) → mediator and mediator ← heat both present. `untested=True` means no direct drug × heat finding at all |

## Headline numbers

- **Direct drug × heat:** graph_check csv mode gives 13 core-heat findings in 10 studies across the 18 groups. With our extended heat terms, there are 18 rows in 14 studies. Only 9 of those (7 studies) are in-scope findings without a heuristic flag. The flagged ones include "sweat chloride", "clozapine level in sweat", "night sweats" and fever. Real examples:
  - lithium dose-level ratio vs. mean daily temperature (PMID 25163443)
  - monthly **thiazide-induced hyponatraemia** cases vs. air temperature (PMID 16911573)
  - opioid overdose ED visits vs. daily ambient temperature (PMID 37897873)
- **Drug → mediator:** 1,644 findings in 1,082 studies across all 19 groups. For the 15 in-scope groups: 1,473 findings in 972 studies, of which **only 337 findings (227 studies) are non-blood-pressure**. BP rows are mostly antihypertensive efficacy trials.
- **Heat → mediator:** 101 findings in 71 studies, mostly ambient temperature → body temperature, AKI and BP. About a quarter are flagged as cold contrasts or animal studies.
- **Concept-level relationships:** **zero** drug ↔ heat concept edges, and only 10 heat ↔ mediator concept edges (for example, heat stroke → AKI, 2 studies). Grounding is thin, so association-level name matching carries the pathways.

### Validation: are known heat drugs rediscovered?

Ranked by the share of a drug's studies that hit a non-BP mediator (19 groups):

| Drug group | Rank | Rediscovered? |
|---|---|---|
| Loop diuretics | 1 | Yes |
| Diuretics (any) | 2 | Yes |
| Thiazides | 3 | Yes |
| Lithium | 7 | Middle |
| Antipsychotics | 11 | No |
| Anticholinergics | 15 | No (3 mediator findings in total) |

So the diuretics are rediscovered, while lithium sits in the middle and antipsychotics and anticholinergics are not. **3 of 6 known heat-drug groups (all the diuretics) land in the top 3.** The failures make sense: their heat mechanism (less sweating, thermoregulation) is barely represented, with 6 drug → sweating and 6 drug → body-temperature findings in the whole release. That is itself a graph-gap finding.

On the plain score (sqrt of studies), heavily studied antihypertensives (ACEi/ARB, beta blockers) rank at the top because of BP. Don't use the plain score for the validation claim.

### Hidden-drug candidates (raw, unvalidated)

262 drug-like concepts link to a mediator; 224 are outside our 15. The top non-15 candidates are dominated by inpatient nephrotoxins (vancomycin, piperacillin/tazobactam, hydroxyethyl starch, polymyxins). These are flagged `inpatient_or_procedural_heuristic`.

There are 34 non-inpatient candidates outside our 15 with ≥3 non-BP mediator studies. Plausible outpatient ones include:
- proton-pump inhibitors (AKI 21 studies)
- tolvaptan (hyponatremia 14)
- simvastatin (AKI 14)
- aspirin
- spironolactone / antimineralocorticoids
- calcium channel blockers
- tramadol (hyponatremia 4)
- desmopressin (hyponatremia 4)
- mirtazapine (hyponatremia 3)
- trimethoprim-sulfamethoxazole
- fluoroquinolones

### Untested links

29 drug-group × mediator pathways have both legs but no direct drug × heat finding; 20 of these are in-scope. Examples:
- loop diuretics → AKI (35 drug-leg studies) ← heat (12)
- SGLT2 → AKI (28) ← heat (12)
- insulin, metformin, stimulants, anticholinergics, epinephrine

There are also 236 candidate-concept × mediator links with no direct heat finding.

### Master-list audit (role 5)

Of the 51 master-list PMIDs, **only 5 are in the Dataverse studies table**, with 19 findings in total:

| PMID | Findings |
|---|---|
| 29116624 | 2 |
| 29217346 | 4 |
| 29613996 | 6 |
| 30130598 | 3 |
| 31397862 | 4 (the API showed 7) |

**None of the 16 DOIs match.** The API check on 13 Nov reported 50 indexed and 8 with findings. The Dataverse release appears to hold only studies with findings in the v2.1 snapshot, and it is a smaller release (2.0M associations vs. 5.9M via the API).

Important for the §8.2 rule "keep API findings only if they also appear in the Dataverse CSV": the following are **absent from Dataverse**, so under System's own rule they would be dropped:
- the **Martin-Latry 2007 findings (PMID 17513091)**
- 35977265
- the insulin-pen finding (36585035)

## Caveats

- Matching is on free-text variable names, as `graph_check.py` does. There are false positives and false negatives.
  - The `auto_flags_heuristic` column catches some false positives automatically (cold contrasts, non-human, sweat as a specimen, night sweats, fever, endogenous insulin). **No human has reviewed it.**
  - "Antidepressant" is included in the SSRI group.
  - "Opioid" includes opioid use and overdose, not only patches.
  - Epinephrine auto-injector terms are strict, so there are almost no hits.
- A pair is counted only when the drug term and the mediator or heat term are in **different** variables. Findings that name both in one variable (e.g. "furosemide-induced hyponatremia") count only if the other variable matches.
- The BP mediator mixes "hypotension" (heat-relevant) with BP-lowering efficacy. Use the non-BP numbers for heat-risk claims.
- Effect sizes come in mixed statistic types and directions, and about 20% of extractions are wrong (System's own estimate). Nothing here has been verified against abstracts.
- `published_date_pubmed` comes from PubMed `sortpubdate`, not System. The relationship-level `last_published_date` comes from System and is often blank.
- Hidden-drug "drug-likeness" uses Wikidata descriptions plus a hand-written exclusion list, so it misses ungrounded variables. Candidates are **not validated** and must not be shown as findings.
