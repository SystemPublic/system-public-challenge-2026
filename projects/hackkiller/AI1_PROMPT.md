# Prompt for AI-1 ("Evidence & Integration")

You are **AI-1 ("Evidence & Integration")**. You own the evidence pipeline in `what-works-where/`, on branch `evidence-pipeline`. AI-2 works in parallel on branch `context-data` (see `AI2_PROMPT.md`). `AI_HANDOFF.md` §4 (formats) and §7 (science rules) bind you too.

**Deadline:** every task below is pushed by **12:30 ET**. Finishing the work correctly matters more than adding extra.

## Goal

Make the evidence layer:
- **reproducible offline**: it runs from the teammate's restored System tables, with no per-row API calls;
- **complete**: no candidate the teammate found is missing;
- **uniform**: ISO3 country codes and one shared set of QC flags;
- **reviewable once**: a single merged review queue;
- **self-checking**: a validation script.

Then verify **at least 10 more** high-value graph rows against their source.

## Tasks

### A1 — Read the System tables offline

- **Inputs:**
  - `data/restored/system/system-public-graph-v1-{associations,studies,variables,concepts}.csv`, produced by `scripts/restore_system.py`, which checks every file against the publisher's SHA-256.
- **Pipeline changes:**
  - `pipeline/common.py` uses the restored associations CSV when it exists. Otherwise it falls back to `data/raw/` and the Dataverse download.
  - `03_enrich.py` takes `population`, `study_type` and `doi` from the offline `studies` table. PubMed stays the source for title, journal and year.
  - The System API is used **only** for graph-level questions: the concept neighbourhood and the coverage of the landmark trials (`04_graph_context.py`).
- **Done when:**
  - a full run makes 0 per-study API calls, which you can check in `data/request_log.jsonl`;
  - the snapshot row count is 1,999,877.

### A2 — Recall: adopt the teammate's context rule

- A row is a candidate if **either** rule matches.
  1. **Our rule.** An intervention term appears, and the paper has malaria context.
  2. **The teammate's rule** (`scripts/clean_data.py` `PATTERNS` + `MALARIA`). An intervention pattern and the context pattern match the row text. The context pattern counts `ITN`/`LLIN` as malaria context, and the extended context also includes `parasite`.
- Record `match_rule` ∈ {`ours`, `teammate`, `both`}.
- **Done when:** every one of the teammate's 331 `system_id`s is in our candidates (assert this). Report how many rows were added.

### A3 — One country code, one set of QC flags

- **Countries:**
  - Add `iso3` to every graph row (`;`-joined for multi-country papers; empty if unknown) and keep `country_source`.
  - Names map to ISO 3166 alpha-3. `sub-Saharan Africa` and `Sahel` stay as region notes, not ISO codes.
- **QC flags.** Add the teammate's flags next to ours, using their names:
  - `exact_duplicate_rows` and `conflicting_association_id` (same `system_id`, different content, anywhere in the snapshot)
  - `partial_ci`, `reversed_ci`, `estimate_outside_ci`, `nonpositive_ratio`
  - `ci_level_out_of_range`, `p_value_out_of_range`, `p_operator_unspecified`
  - `study_pmid_mismatch`, `study_lookup_missing`
- **Done when:** `graph.json` rows have `iso3`, `qc_flags` (ours) and `teammate_flags` (theirs, recomputed).

### A4 — One review queue

- `data/review/review_queue.csv` becomes the **only** queue. It is keyed by `system_id`.
- It merges:
  - our classification (subtype, role, outcome tier, priority, abstract quote);
  - the teammate's `candidate_classes`, `match_terms`, `content_hints`, `country_hints` and flags;
  - a column `in_teammate_queue` (Y/N).
- Keep the blank `verify_*` columns.
- The teammate's `data/processed/system_review_queue.*` is **not** edited; it belongs to AI-2. We supersede it by documenting that in our README.
- **Done when:** the queue's row count equals our candidate count, and all 331 teammate ids are present.

### A5 — `pipeline/validate.py`

It must fail loudly. It asserts:

1. The snapshot has 1,999,877 rows. The 331 teammate ids are a subset of our candidates. Candidates have unique `system_id`s.
2. Every vocabulary value (`intervention_class`, `outcome_tier`, `role`, `verification_status`) is in the allowed set in `AI_HANDOFF.md` §4.
3. Every `iso3` token is a 3-letter uppercase code.
4. `plottable_ratio` rows have value > 0, 0 < lo ≤ value ≤ hi, and value ≤ 20.
5. Every row in `evidence_verified.csv` and `evidence_graph_checked.csv`:
   - has a `source_url` and a `verification_status`;
   - estimates are positive with ordered CIs;
   - every `graph_association_id` exists in the snapshot candidates (where given);
   - abstract-checked rows have a non-empty `source_quote`.
6. `site/data/*.json` exist, each file is under 25 MB, and no file contains an API key pattern.
7. If AI-2's `data/context/*.csv` exist, their headers match the contracts exactly.

It prints a one-line summary and exits non-zero on any failure.

### C2 — Verify ≥10 new high-value rows

Using Europe PMC abstracts (`07_abstract_check.py`), check:

- **PMID 36174592**: PBO vs non-PBO LLINs → parasite prevalence.
- **PMID 18461178**: ITNs in low-transmission areas → infection.
- **ITN → under-5 mortality** rows (17889242, 34051817, 15173148 and any others found).
- Then priority-1 net rows not yet reviewed.

For each row:
- restore the intervention, comparator, outcome, time point, country (ISO3) and population;
- quote the source sentence;
- set `verification_status` from the vocabulary;
- **exclude** rows that are not intervention effects, and say why.

Append to `evidence_graph_checked.csv` (via `08_graph_checked.py`) and rebuild the site data.

## Rules

- Never edit AI-2's paths: `scripts/`, `data/raw/`, `data/processed/`, `reports/`, `metadata/`, `what-works-where/data/context/`, `fulltext_checks.csv`.
- Commit with the prefix `[AI-1]`, push after each task, and update the AI-1 row in `COORDINATION.md`.
- Never force-push. Never commit keys, `data/restored/`, or files over 25 MB.
- Keep the graph's original labels next to every correction. No pooling, no voting by significance.

## Final report to the user

- Rows added in A2.
- QC flag counts.
- Queue size.
- Validation result.
- New verified rows, and what they show.
