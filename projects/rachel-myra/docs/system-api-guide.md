# How to use the System Public Graph

Written 13 Nov 2026 from the official docs at docs.system.com. The API is in **closed beta**, so field names may change.

## Two ways in

| | API | Bulk CSV download |
|---|---|---|
| Needs a key? | **Yes**. Requests without one get `403 Forbidden` (tested). | **No** |
| Where | `https://public-api.system.com/v1` | Harvard Dataverse, [doi:10.7910/DVN/7V6JDO](https://doi.org/10.7910/DVN/7V6JDO) (dataset v2.1, July 2026) |
| Best for | Quick lookups, live features in the app | Counting, cleaning and joining everything offline |
| Limits | 10,000 requests/day per key | About 1.1 GB total |
| License | CC BY-NC 4.0 (non-commercial; credit System) | Same |

**Getting a key:** keys come from System's "beta portal," and the docs don't explain how to sign up. Ask the organizers in the hackathon Slack: *"Where do participants get a System Public Graph API key?"* Participants almost certainly get one.

**Don't wait for the key.** The CSVs hold the same data and need no key.

## What's in the data

The atomic unit is a **finding** (an "association"): one statistical result extracted from one paper.

| Table | One row is | Key columns |
|---|---|---|
| **Associations** (442 MB) | one finding | `variable_1_name`, `variable_2_name`, `statistic_type`, `statistic_value`, `ci_lower`, `ci_upper`, `p_value`, `study_id`, `pubmed_id` |
| **Variables** (136 MB) | a variable as worded in a paper (e.g., "lithium serum level") | `system_id`, `name`, `concept_id` |
| **Concepts** (8 MB) | a standardized concept, linked to Wikidata | `system_id`, `wikidata_label`, `wikidata_aliases` |
| **Relationships** (395 MB) | a concept-to-concept edge with totals | `relationship_id` (`conceptA|conceptB`), `num_findings`, `num_studies`, `last_published_date` |
| **Studies** (139 MB) | one paper | `study_id`, `doi`, `pubmed_id`, `population_string`, `study_type` |

How the tables join:
- `Associations.study_id` → `Studies.study_id`
- `Associations.variable_1_id` / `variable_2_id` → `Variables.system_id`
- `Variables.concept_id` → `Concepts.system_id`

## API basics

Every request needs the header `x-api-key: YOUR_KEY`.

| Want | Request |
|---|---|
| Find a concept | `GET /v1/concepts?search=wikidata_label:lithium` |
| Find variables by wording | `GET /v1/variables?search=name:furosemide` |
| All findings involving a variable | `GET /v1/variables/{id}/associations` |
| A concept's edges | `GET /v1/concepts/{id}/relationships?sort=num_studies:desc` |
| Findings behind an edge | `GET /v1/relationships/{A%7CB}/associations` (the `|` must be written as `%7C`) |
| Paper details | `GET /v1/studies/{study_id}` |

Query parameters:
- **Pagination:** `offset`, `limit` (default 10), and `include_total=true` to get a count.
- **Filters:** `filter=field:value`. Use `||` for OR.
- **Sorting:** `sort=field:desc`.

```bash
curl -H "x-api-key: $SYSTEM_API_KEY" "https://public-api.system.com/v1/concepts?search=wikidata_label:lithium&limit=5"
```

## Gotchas (they matter for scoring)

1. **About 20% of associations are extracted inaccurately**, according to System's own docs. They recommend keeping only API associations that also appear in the Dataverse associations CSV. Do that, and say so on the Methods page.
2. **Direction errors happen.** The extraction model sometimes swaps cause and effect.
3. **Grounding is incomplete.** Some variables have no concept, so concept-only queries miss them. That's why the script matches on variable **names**.
4. **Sex and population aren't structured.** `population_string` is free text, so search it for words like "women," "older adults" or "elderly."
5. **Effect sizes come in mixed types** (odds ratios, hazard ratios, correlations). Don't average across `statistic_type`.
6. **Publication bias:** significant results are over-represented.

## The go/no-go check

`scripts/graph_check.py` counts findings and distinct studies for 18 drug groups × 7 heat outcomes and writes `data/graph_coverage.csv`.

**Option A, no key (recommended now):**
1. Download `system-public-graph-v1-associations.csv` (442 MB) from the Dataverse page above.
2. Save it in a new `raw/` folder in this project.
3. Run:

```bash
py -3 scripts/graph_check.py csv raw/system-public-graph-v1-associations.csv
```

**Option B, with a key:**

```bash
SYSTEM_API_KEY=your_key py -3 scripts/graph_check.py api
```

**Reading the result:**
- The summary line counts only the core heat outcomes: heat illness, body temperature, ambient heat, sweating.
- Dehydration, hyponatremia and AKI are counted separately, because they're not heat-specific.
- Open `data/graph_coverage.csv` and spot-check the `example_variable_pairs` column for false matches before quoting any number.

**Status:** the matching logic was tested on sample rows. The script has **not** yet been run against the real API or CSV.
