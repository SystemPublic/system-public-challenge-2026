# Seven relationships: graph provenance

The notebook combines the seven arrows in the user-provided diagram into one PNG/SVG graph. This provenance note covers the underlying follow-up extractions, including estimates used in the separate relationship graphs. They show selected study estimates, not a comprehensive meta-analysis or the strength of the entire literature.

## Search
The supplied System Public Graph Dataverse v2.1 association file was scanned in full: 1,999,877 records. Broader salary, earnings, income, employment stability and life-satisfaction/well-being terms, in variable names and linked concept labels, returned 1,572 candidate records across 1,130 publication IDs. These are unvalidated broad matches, many concerning household income, clinical populations or unrelated uses of words such as “contract.” The separate `seven_relationship_graphs` package contains `targeted_snapshot_candidates.csv` (raw matches) and `snapshot_search.py` (search code). Run from the original workspace with the three source files in `work/`.

Dataset: https://doi.org/10.7910/DVN/7V6JDO . Authenticated live System API not run. The provided ILO and World Bank files are national labor-market context, not individual worker health or life-satisfaction effect estimates; they were not used to calculate these effects. GLD remains unintegrated.

## What changed
The salary-grade mortality paper was found in the expanded snapshot search. Four Graph records were matched numerically to its abstract and assigned the correct cause-of-death labels. Its confidence intervals and adjustment model are not verified, so no interval is drawn. Salary grade is a socioeconomic-status proxy and cannot establish a causal effect of pay.

The Finnish working-conditions paper was a Graph seed. Its mental-health estimates and its null-compatible work-unit physical-health estimate were extracted from the same paper. The individual physical-health estimate differs between abstract (1.32) and Results (1.31), with the same interval; the graph visibly flags this issue. These are overlapping samples within one cohort. No results are pooled.

The Whitehall hours estimates come from the prior paper check. The German insecurity/depression estimates come from v02 Tables 5–6 extraction; they were added from a Graph-discovered paper, not claimed as direct numeric matches to its original Graph rows.

Two exact life-satisfaction relationships required primary-paper supplements after searching the supplied snapshot. Neither supplement's DOI occurs in the snapshot study metadata. They are explicitly labeled as supplements, not System Graph observations. Job satisfaction, happiness at work, WHO-5 well-being and children's oral-health quality of life are not substituted for global life satisfaction.

## Transformations
For Clark et al. (2024), the hourly-pay doubling associations equal the published log-wage coefficient multiplied by ln(2). Confidence limits are approximate normal intervals: (coefficient ± 1.96 × robust standard error) × ln(2). US life satisfaction was rescaled by the authors to 0–10. UK and US samples/designs differ; no country ranking is inferred.

For Helbling and Kanji, intervals equal coefficient ± 1.96 × reported SE, using rounded published inputs. The job-worry coefficient is conditional on permanent-contract status because the model includes an interaction. It describes initial life satisfaction, not annual change. M1 and M2 are alternative models with different sample sizes, not independent replications. The adjusted interval includes zero.

## Sources
- Salary and mortality: https://pubmed.ncbi.nlm.nih.gov/10746109/
- Conditions and disability pension: https://www.sjweh.fi/show_abstract.php?abstract_id=3402&fullText=1
- Hours and depression: https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0030719
- Insecurity and depression: https://pmc.ncbi.nlm.nih.gov/articles/PMC8949946/
- Wages and life satisfaction: https://onlinelibrary.wiley.com/doi/10.1111/ecca.12516
- Insecurity and life satisfaction: https://pmc.ncbi.nlm.nih.gov/articles/PMC5984641/

All findings are observational. Independent extraction verification and formal risk-of-bias assessment remain pending. The graphs do not estimate policy effects or rank job attributes. Reviewed 14 November 2026.
