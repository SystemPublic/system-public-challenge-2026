# Processed data, first pass

Run `python3 scripts/clean_data.py`, then `python3 scripts/validate_processed.py` from the repository root. No external Python packages or live APIs are needed. Original files remain unchanged.

| File base name | Grain / purpose |
|---|---|
| `system_candidates` | One retained association row. Candidate classes and matched terms are lexical search hints, not source-verified intervention effects. |
| `system_study_lookup` | Existing System study records for candidate associations. This is an internal ID lookup only; no new literature links were created. |
| `system_review_queue` | All candidates awaiting context/source review. |
| `system_candidate_summary` | Candidate classes; class memberships can overlap. Study records are not independent trials. |
| `who_context` | Country/year/indicator/source dimensions; original units retained. |
| `map_context` | Country/year/metric/release; mean and uncertainty bounds aligned by dimensions. |
| `pf8_samples` | All original samples with typed QC/year/location, case groups and aggregation eligibility. |
| `pf8_drug_classifications` | Sample/drug-combination publisher classification, without new biological inference. |
| `pf8_resistance_context` | Country/admin1/year/drug, counts and sampled-case resistant share among determined calls. |
| `pf8_country_year_resistance` | Country/year/drug; sums counts across admin1 before calculating a proportion, never averages percentages. |
| `pf8_marker_calls.csv.gz` | Sample/marker raw and normalized calls. Mixed calls and missing calls are explicit; no resistance rules inferred. |

Most tables have both CSV and typed JSON. CSV blanks and JSON `null` mean unavailable; zero is retained when it is a valid value. List columns in CSV are JSON-encoded arrays. IDs are text. JSON booleans are typed. Preserve `source_row`, source file, flags and publisher identifiers when further transforming data.

## Interpretation boundaries

- No paper linking, comparator recovery, follow-up extraction, source verification, meta-analysis or treatment ranking has been performed.
- System `numeric_check_status=passed` means only that the selected numerical checks found no blocking problem. It does not establish valid clinical interpretation. `country_hints` come from population text and are not confirmed sites.
- `content_hints` are nonexclusive keyword labels for behaviour/acceptance, immunology, entomology and human health outcomes. They do not establish the outcome or study design. All System `effect_display_eligible` values remain false until source review.
- No relationships between individual System results and background datasets are inferred. Context tables remain separate. Match geography, years and populations explicitly in the next stage.
- Pf8 uses one QC-pass sample per same-case group, highest callable fraction then sample ID. Conflicting location/year groups are excluded from summaries. All original samples remain in `pf8_samples`.
- `resistant_proportion_among_determined = n_resistant / (n_resistant + n_sensitive)`. Undetermined, missing and invalid statuses are separately counted, never treated as sensitive. All sample counts are visible; no minimum-sample cutoff is imposed. These are sampled cases, not population prevalence.
- MAP raw zeros are flagged because the source says zeros may represent missing estimates. Corresponding cleaned bounds/means remain unavailable until reviewed. See the retained raw columns.
- WHO units and MAP units are not automatically harmonized: percent and proportion remain distinct. Their geographies and denominators may differ.

Rules and search patterns are versioned in `scripts/clean_data.py`. Quality counts and output hashes are in `reports/`. The search is deliberately scoped to nets, seasonal malaria chemoprevention and malaria vaccines; it does not claim systematic-review completeness.
