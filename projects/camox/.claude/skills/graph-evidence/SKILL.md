---
name: graph-evidence
description: Use when querying the System Public Graph (DuckDB), testing a hypothesis or building evidence cards, or adding or changing a tool in agent/tools.py.
---

# Graph evidence

## The data

`data/graph.duckdb` holds the cleaned Dataverse subset of the System Public Graph (doi:10.7910/DVN/7V6JDO). About 20% of raw API findings are mis-extracted. This subset removes them, so use it for anything numeric.

| Table | Rows | Key columns |
|---|---:|---|
| `associations` | 2.0M | `system_id`, `study_id`, `system_statistic_type`, `statistic_value`, `ci_lower`, `ci_upper`, `p_value`, `variable_{1,2}_id`, `variable_{1,2}_concept_id`, `variable_{1,2}_name` |
| `studies` | 844k | `study_id`, `doi`, `pubmed_id`, `population_string`, `study_type` |
| `variables` | 1.77M | `system_id`, `name`, `concept_id` |
| `concepts` | 46k | `system_id`, `wikidata_id`, `wikidata_label`, `wikidata_aliases`, `wikidata_description` |
| `relationships` | 840k | `num_studies`, `num_findings`, `"source_concept.system_id"`, `"target_concept.system_id"`, `"source_concept.wikidata_label"`, ... |

Join keys: `associations.variable_{1,2}_concept_id = concepts.system_id`, `associations.study_id = studies.study_id`, `variables.concept_id = concepts.system_id`. Relationship columns contain dots, so always quote them.

### Pitfalls

- **Wording carries direction.** "gender (being male)", "gender of children" and "malaria infection → gender" put the reference group in different places. Read both variable names before you say which way an effect points. If you can't tell, say so.
- **Never pool effect families.** Only compare values within one family:
  - ratio (null 1): `odds_ratio`, `adjusted_odds_ratio`, `hazard_ratio`, `adjusted_hazard_ratio`, `relative_risk_ratio`, `incident_rate_ratio`, `prevalence_ratio`
  - difference (null 0): `mean_difference_unstandardized`, `mean_difference_standardized`, `coefficient`, `risk_difference`, `elasticity`
  - correlation (null 0): `pearson_r`, `spearman_correlation`
  - everything else (`t_test`, `gini_coefficient`, `coefficient_of_determination`) stays out of summaries.
- **Many findings have no CI.** Count them as direction only, never as significant.
- **Search is substring matching.** "damp housing" finds nothing. Try short terms and synonyms, then `search_variables` for wording that has no concept (e.g. "mold" maps to the concept "fungus").
- **`population_string` is free text.** Filter with short fragments ("child", "Uganda", "pregnant"), and report the actual strings, not your guess.
- **Relationship counts are approximate.** `neighbours` and `paths` add A→B and B→A, which can count a study twice. Use them to find links, and `summarise_evidence` for the numbers you report.
- **Single-study links** are common. Flag them; never call one study "supported".

### Tools (`agent/tools.py`)

- `search_concepts(text)`: entry points. Exact label first, then most-studied.
- `search_variables(text)`: raw paper wording, and the concepts it is grounded to.
- `neighbours(concept_id)`: the strongest linked concepts. Use it to expand a topic.
- `paths(concept_a, concept_b)`: direct, 2-hop and 3-hop chains. Use it for mediators and theory-of-change links.
- `get_findings(concepts_a, concepts_b, ...)`: the actual effects with DOIs and populations, CI-bearing rows first.
- `summarise_evidence(...)`: direction and CI counts and medians per family, computed in code.
- `sql(query)`: a read-only escape hatch, capped at 50 rows.

## Evidence cards

1. Break the question into 2–4 testable sub-claims. Write each so data could prove it wrong.
2. For each sub-claim, collect entry concepts with `search_concepts` and `search_variables`, trying several synonyms. Group synonym concept ids into one list.
3. Call `get_findings`, filtered by population or wording when the user's population is specific. Then call `summarise_evidence` with **the same filters**. The card's numbers come from the summary only.
4. Read the variable wording on the findings you cite. Report who was studied and say where that differs from the user's population.
5. Search for synonyms before you write "no evidence". Name the gap and where to look next.

The verdict rules (supported / contested / mixed / thin / no evidence) live in `agent/system_prompt.md`. That file is the single source; change them there, not here.

## Adding a tool

- Write one plain, read-only function in `agent/tools.py` and add it to `TOOLS`. No classes, no wrappers.
- Use only these type hints: `str`, `int`, `float`, `bool`, `list[str]`, and `X | None` for optional arguments. `agent.py` builds the OpenAI schema from them. Any other type breaks the schema.
- The docstring is what the model reads. Say what the tool returns and when to use it, in two or three lines.
- Return small JSON: cap rows, and include a `total` when you truncate. Query through `_rows()`, with `$name` parameters, never f-strings with user text.
- Smoke-test from `projects/camox`:
  ```bash
  .venv/bin/python -c "import sys; sys.path.insert(0,'agent'); import tools; print(tools.search_concepts('malaria', k=3))"
  ```
