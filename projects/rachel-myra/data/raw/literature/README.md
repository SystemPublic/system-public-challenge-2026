# Literature search, citation chase and citation verification (raw)

Access date for everything here: **2026-11-14** (overnight run). Spec §8.4 steps 1–2, §8.2a checks 1–2; build-plan Step 2.
No LLM screening or extraction was done; this is collection only. No human review.

## Scripts (all in `scripts/`, run with `uv run --with requests python -I scripts/<file>.py`)
| Script | Does | Outputs |
|---|---|---|
| `lit_search.py` | PubMed + Europe PMC fixed queries, count grid, record fetch | `queries.json`, `query_counts.csv`, `heat_term_grid.csv`, `pubmed_ids/`, `epmc_raw/`, `abstracts.jsonl`, `data/processed/literature_records.csv` |
| `lit_citation_chase.py` | Resolve 5 key reviews, backward + forward citations (OpenAlex, Europe PMC) | `citation_chase/`, `data/processed/citation_chase.csv` |
| `lit_verify_citations.py` | Existence, title/label match, abstract grounding of numbers for every ID in the master list and the report | `citation_check/` (API cache), `data/processed/citation_verification.csv` |
| `lit_id_map.py` | PMID / PMCID / DOI cross-map for all records | `ncbi_idmap/`, `data/processed/literature_id_map.csv` |

## Sources / endpoints
- PubMed E-utilities: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/` (esearch, efetch XML, esummary JSON); `tool=missing-label-hackathon`, no email, no API key, ≤3 req/s.
- Europe PMC REST: `https://www.ebi.ac.uk/europepmc/webservices/rest/search` (resultType=core, cursorMark paging), `/MED/{pmid}/references`, `/MED/{pmid}/citations`.
- OpenAlex: `https://api.openalex.org/works` (no key; 33 calls used; shared free budget $0.10/day, $0.0908 left after the run).
- Crossref: `https://api.crossref.org/works/{doi}` and `?filter=alternative-id:{PII}`.
- **Failure:** the NCBI PMC ID Converter (`https://pmc.ncbi.nlm.nih.gov/tools/idconv/api/v1/articles/`) returned **HTTP 403** to the Python client (it worked from curl). I did not work around it. ID normalisation instead uses PubMed esummary `articleids` (pubmed / pmc / doi), which is the same NCBI ID data, plus esearch `"<doi>"[doi]`.

## 1. Search (evidence funnel)
Exact query strings are in `queries.json`. The heat block for PubMed ORs: `"Hot Temperature"[Mesh]`, `"Heat Stress Disorders"[Mesh]`, `"Heat Stroke"[Mesh]`, `"Extreme Heat"[Mesh]`, `"Hyperthermia"[Mesh]`, `"Hypohidrosis"[Mesh]`, heat wave/heatwave[tiab], high ambient temperature / hot weather / extreme heat / summer heat [tiab], and free-text heat illness terms (heat stroke, heat exhaustion, hyperthermia, an/hypo/oligohidrosis). The Europe PMC version uses `TITLE_ABS:` fields (Europe PMC rejected `MESH_HEADING:` and returned 503 for `sort=RELEVANCE`, so neither is used). Drug blocks use MeSH plus free-text names; lithium excludes battery/cathode/anode/electrode.
- **Retrieval filter:** PubMed retrieval adds the standard animal-only exclusion `NOT ("Animals"[Mesh] NOT "Humans"[Mesh])` to the drug×heat queries. Both counts are saved.
- **Cap:** 2,000 records per query per source. No query hit the cap.
- `heat_term_grid.csv`: drug × each single heat term (9 PubMed + 6 Europe PMC terms), count only, 225 queries.
- `epmc_count_fulltext_incl_oa` in `query_counts.csv` is a count-only Europe PMC search without field restriction (it includes OA full text), for the funnel only. Nothing was retrieved from it.

| Query | PubMed all | PubMed human-filter (retrieved) | Europe PMC title/abstract (retrieved) |
|---|---|---|---|
| lithium | 824 | 768 | 519 |
| loop diuretics | 71 | 48 | 46 |
| thiazides | 54 | 44 | 22 |
| ACE inhibitors/ARBs | 174 | 109 | 68 |
| SGLT2 inhibitors | 9 | 8 | 9 |
| insulin (incl. pumps) | 184 | 130 | 40 |
| metformin | 52 | 41 | 48 |
| anticholinergics (oxybutynin) | 206 | 144 | 121 |
| antipsychotics (incl. clozapine) | 1023 | 779 | 822 |
| SSRIs | 258 | 129 | 167 |
| topiramate/zonisamide | 71 | 61 | 59 |
| ADHD stimulants | 243 | 71 | 24 |
| beta blockers | 440 | 203 | 254 |
| fentanyl/opioid patches | 293 | 206 | 144 |
| epinephrine auto-injectors | 7 | 7 | 1 |
| storage: insulin | 606 | 606 | 521 |
| storage: epinephrine auto-injector | 83 | 83 | 16 |
| storage: inhalers | 269 | 269 | 182 |
| storage: glucose test strips/meters | 260 | 260 | 167 |
| storage: mail-order / delivery temperature | 346 | 346 | 75 |
| storage: medicines in heat (general) | 1290 | 1290 | 25 |

**Unique records: 5,995.** 5,812 come from PubMed efetch and 183 are Europe PMC-only (no PMID: preprints, AGRICOLA, etc.). 5,355 have an abstract. 3,160 were found by a drug×heat query and 2,896 by a storage query. The records are in `abstracts.jsonl` and in `data/processed/literature_records.csv` (`found_by` lists every query that hit the record).

**Known noise for the screening step:**
- Lithium: "high temperature" still catches lithium chemistry and materials papers. 543 of the 824 PubMed lithium hits come from the high-ambient-temperature term.
- Antipsychotics and SSRIs: hits are dominated by neuroleptic malignant syndrome and serotonin syndrome.
- Fentanyl: hits include anesthesia and hyperthermia papers.
- "storage: medicines in heat (general)": 1,290 hits, broad.

## 2. Citation chase
Each seed was resolved by an OpenAlex title search and accepted only if the DOI matched the DOI the repo cites.

| Seed | OpenAlex ID | DOI | How resolved | OA refs | OA cited-by | EPMC refs | EPMC cites |
|---|---|---|---|---|---|---|---|
| Hospers 2024 | W4403730929 | 10.1016/j.eclinm.2024.102886 | title search, DOI match | 77 (of 80) | 73 | 71 | 36 |
| Tews 2026 | W7162091437 | 10.3390/pharmacy14030074 | title search, DOI match | 74 | 4 | 75 | 1 |
| Kalisch Ellett 2016 | W2468721541 | 10.1111/jcpt.12418 | **DOI lookup** (not in title-search top 5) | 23 | 48 | 27 | 33 |
| Layton 2020 | W3111886642 | 10.1371/journal.pone.0243665 | title search, DOI match | 45 | 128 | 35 | 79 |
| Schizophrenia review 2025 | W4412707851 | via Crossref PII S0048969725016055: "Susceptibility of persons with schizophrenia to extreme heat: A critical review" (Sci Total Environ) | title search, DOI match | 543 (of 547) | 14 | 570 | 9 |

`data/processed/citation_chase.csv` has 1,965 rows, about 1,750 distinct works. About 119 of them are already in the search set. No seed was skipped.

## 3. Citation verification (`data/processed/citation_verification.csv`)
There are 228 citation instances: 90 from the master list and 138 from the report. They cover **105 unique IDs** (52 PMID, 40 DOI, 13 PMCID). **All 105 exist.** 101 have an abstract. The 4 without one are PMID 19424950, PMID 14258922, PMID 5547594 and DOI 10.3181/00379727-115-29082.

**PMID 42710533 (Harley 2026) is indexed in PubMed:**
- Title: "Antihypertensive Medications and Risk of Heat-Related Illness During Heatwaves: Self-Controlled Case…"
- Pharmacoepidemiol Drug Saf 2026; DOI 10.1002/pds.70447; PMCID PMC13553137
- The PMID is correct. "Not indexed" applies only to System's graph.

Verdicts (per instance):

| Verdict | Count |
|---|---|
| exists_no_numbers_claimed | 162 |
| numbers_all_in_abstract | 46 |
| numbers_partly_in_abstract | 5 |
| numbers_not_in_abstract | 6 |
| exists_no_abstract | 9 |
| id_not_found | 0 |

In total, 95 scorable numbers were attached to citations and 80 were found verbatim.

Numbers that were missing (11 instances, 15 numbers; likely full-text-only or secondary-source numbers):
- Layton 2020: RR 1.54, 1.64, 1.84 for the loop-diuretic subgroups (master R25 and report line 18)
- Hospers 2024: 35 trials, 0.4 °C, 0.1 °C
- Low 2004: 4,600 patient-years
- Rachid 2016: 78% (master R56 and report line 85)
- Grant 1994: 0.1 mg/mL
- Henkel 2020: 45 °C
- Front Sports Act Living 2022: 39 °C
- Tews 2026: 37

Flags:
- `label_mismatch` = 0. 148 instances had a scorable label: 145 scored ≥0.8 and 3 scored 0.78 (Kongmalai, because of the long journal-name label).
- `no_heat_terms` = 23. These are mostly papers deliberately cited for non-heat facts: skin cancer, Fanconi syndrome, outages, SGLT2.
- `drug_terms_absent` = 13.
- `doi_title_differs_from_pubmed` = 1. This is Allen & Cross 2014: the Crossref title is truncated, not a real mismatch.

Heuristics (also in the script docstring):
- Report numbers are taken from the text between the previous link or ID and the citation.
- Years and integers below 10 are not scored.
- Matching is verbatim after normalizing "·" and thousands separators.

## 4. ID map (`data/processed/literature_id_map.csv`)
6,835 papers across search, citation check and chase. 6,609 have a PMID, 1,620 a PMCID and 5,934 a DOI. 6 have conflicting IDs, all alias DOIs (Compr Physiol double DOIs, a JAMA Arch Intern Med legacy DOI, and a `//` DOI variant).

## Size
`data/raw/literature/` is about 56 MB.
