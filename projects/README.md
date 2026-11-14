# Job quality research v02

Open **JobQuality_Research_v02.ipynb** in Colab using File → Upload notebook. Unzip the accompanying CSV-only archive on your computer, run the notebook, and select all CSVs when prompted. Locally, keep `data/` alongside the notebook. No compressed data payload or API credential is embedded.

Start with **SYNTHESIS.md** for findings and **data/study_screening.csv** for paper decisions. Source links, locators, uncertainty and outstanding holds are in the ledgers.

## This pass
- 87 original security/hours publications screened at title/abstract level; 75 provisionally retained, 12 excluded or separated. Ten received targeted methods/results checks. This is not 87 full-text eligibility judgments.
- 24 estimates from ten publications: 20 full-text table checks, four abstract-only. Null-compatible estimates retained; no universal ranking or sex-interaction claim.
- Ten possible overlapping-cohort clusters; nine source/extraction issues logged.
- Expanded vocabulary: 1,004 distinct association records / 653 publication IDs, versus 614 / 418. The 566 publications outside the original priority set remain unscreened.
- Country identified for 66/87 screened publications, including 63/75 retained. Income vintage FY2027, not study-time classification; Taiwan unassigned in lookup.
- ILO 2023 hours retrieved for 15/22 settings; WDI 2023 vulnerable employment retrieved for four. Additional WDI requests failed; three countries currently have both measures. National survey differences remain. Country context is not aligned to every study's historical collection period.
- Eight proposed synthesis groups reviewed for compatibility. None approved for pooling. Bias-domain questions recorded for ten extracted papers; formal risk-of-bias ratings not completed.
- GLD microdata not integrated; source-specific survey access required. Authenticated System API not run.

## Reproduce discovery
Install pandas/matplotlib for analysis; discovery itself uses the Python standard library.

```sh
python3 discover.py --raw /path/to/raw --out baseline_reproduced
python3 expand_search.py --raw /path/to/raw --out expanded_reproduced
```

The scripts download raw files if absent (the association CSV is about 442 MB). Use cached `associations.csv`, `concepts.tsv`, `studies.tsv` to avoid redownloading. The association MD5 is verified; TSV export digests are recorded separately from original tabular-file metadata hashes. Search patterns are fully visible in code and the expanded manifest. Discovery is a reproducible vocabulary scan, not an exhaustive systematic search.

`audit/` preserves the explicit screening decisions and extraction rules used for this pass. Those scripts refer to the original `work/` layout and are audit records, not a standalone automated reviewer. Raw paper abstracts and full texts are not distributed. Public metadata and context dictionaries are in `sources/`.

## Validation and limits
All notebook code cells executed in order locally using the provided CSVs; integrity checks and figure outputs are recorded in `VALIDATION.json`. The interactive Colab file picker has not been tested in a live Colab session. No live authenticated System API request was made. A Colab API secret alone does not run the API.

Independent screening/extraction checks, full-text eligibility, study-period context, formal bias appraisal and access to GLD remain necessary. Publication counts are not independent-cohort counts. No pooled effects, country health rankings or policy effect estimates are supplied.

## Combined graph code added
The two self-contained code cells near the top of the notebook regenerate the combined seven-relationship graph before the CSV-upload step. Inputs, source links and coefficient-to-interval calculations are plain Python. They save PNG and SVG files in `figures/`. The same code is supplied as `combined_relationship_graph.py` for code submission. No encoded payload or pre-rendered image is embedded.

The graph includes follow-up extractions and two primary-paper life-satisfaction supplements; those additions do not change the original v02 screening/extraction counts. See `combined_graph_sources.md` and `data/combined_graph_estimates.csv`.
