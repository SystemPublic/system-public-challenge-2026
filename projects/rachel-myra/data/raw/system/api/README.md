# System Public Graph API pull (overnight run, 2026-11-14)

Spec §8.5a roles 1, 2, 3, 5 and 6. Access date: **2026-11-14**.

## Status: the API key was rejected, so no API data was pulled

Every request to `https://public-api.system.com/v1` with the key in `.env.local` (`SYSTEM_API_KEY`, sent only as the `x-api-key` header) returned **HTTP 403 `{"message":"Forbidden"}`** (`x-amzn-errortype: ForbiddenException`, from AWS API Gateway).

- This includes the example request from System's own docs (`GET /v1/relationships/baOrApp-0F%7Cfo-h4u_aJp`) and `GET /v1/concepts?search=wikidata_label:lithium&limit=1`.
- A request with **no key** gets the same 403, so the gateway is treating the key as invalid, disabled, or not yet attached to a usage plan.
- A quota problem would return 429 instead.
- The request format matches the official docs (`docs.system.com/system/public/v1.0-api-documentation.md`, checked 2026-11-14), so the format is not the cause.
- The 13 Nov run (`docs/graph-check-results.md`) worked. It may have used a different key: `.env.local` was last edited 2026-11-14 01:34 local time.

**What to do:** get a working key from the beta portal (`https://public-beta.system.com`) or from the organizers, put it in `.env.local` as `SYSTEM_API_KEY`, and run the commands below. Everything is cached, so later reruns cost nothing.

**Requests used:** 1 logged in `request_log.csv`, plus about 6 manual diagnostic calls and the auth polls in `auth_poll.log` (polled every 15 min). All got 403. That is far under the budget.

## Scripts (all new, in `scripts/`, documented in their docstrings)

| Script | Task | API calls (estimate) | Outputs (`data/processed/`) |
|---|---|---|---|
| `system_api_client.py` | Cached, rate-limited client. Sleeps 0.25 s between calls, backs off on 429/5xx, and stops at a hard budget of 6,000 per day (`SYSTEM_API_BUDGET`). Caches to `cache/` keyed by path and params, never by the key. Logs each live call to `request_log.csv`. | | |
| `system_api_common.py` | ID normalization (PMID / PMCID / DOI via `literature_id_map.csv`), `system_terms.py` groups, ratio-direction helper, Dataverse cross-check scanner | | |
| `system_api_master_audit.py` | 1: master-list audit. Batched `GET /studies?filter=pubmed_id:A‖B…`, then `doi:` lookups, then `GET /studies/{id}/associations` | about 60–120 | `system_api_master_list_papers.csv`, `system_api_master_list_findings.csv` |
| `system_api_evidence.py` | 3: concept search (about 200 terms), `/concepts/{id}/relationships` (limit 1000), associations behind drug–mediator / mediator–heat / drug–heat edges, a variable-name route (`/variables?search=name:`, then batched `/associations?filter=variable_1_id:a‖b`), pathways, and the rediscovery ranking | about 1,500–4,000. Cap it with `EVID_VAR_CAP` and `EVID_BP_EDGES` | `system_api_relationships.csv`, `system_api_findings.csv`, `system_api_pathways.csv`, `system_api_pathway_drug_summary.csv` |
| `system_api_verify.py` | 2: the five checks and the badges. Makes **no** API calls and reads the outputs above plus the Dataverse CSV | 0 | `system_api_verification.csv`, `system_api_verification_numbers.csv`, `system_api_reverse_check.csv`, `system_api_verification_summary.json` |
| `system_api_graph_check.py` | 4: copy of `graph_check.py api` that writes new files only | about 100–300 | `system_api_graph_coverage.csv`, `system_api_graph_heat_relationships.csv`, `system_api_graph_check_concepts.csv` |
| `system_api_live_layer.py` | 5: live-layer smoke test. Uses 15 anchor concepts and times 3 uncached repeats of each call | about 200 | `system_api_live_layer.json` |
| `system_api_dataverse_fallback.py` | Runs `system_api_verify.py` with Dataverse findings in place of API findings, **because the key failed** | 0 | `*_dataverse_fallback.*` (see below) |

To run once the key works, in this order (about 2,000–4,500 requests in total):
```
cd /Users/myraclark/system-hackathon
U=~/.local/bin/uv
$U run --with requests python scripts/system_api_master_audit.py
$U run --with requests python scripts/system_api_evidence.py
$U run --with requests python scripts/system_api_graph_check.py
$U run --with requests python scripts/system_api_verify.py
$U run --with requests python scripts/system_api_live_layer.py
```

The scripts read the key from `.env.local` themselves; it is never printed or written to disk.

Untested assumptions, because no API response could be observed:
- `||` OR filters work on `pubmed_id` and `variable_1_id`. Both scripts check this against a single-ID call and fall back to single calls if the results differ.
- `limit=1000` works on relationships (the 13 Nov `graph_check.py` run used it).
- `fields=` may be ignored. `system_api_live_layer.py` records whether it was honoured.
- The response shapes follow the documented examples.

## What was produced tonight: Dataverse fallback for tasks 1 and 2

`system_api_dataverse_fallback.py` runs the **same** verification code, with System's findings taken from the public Dataverse release v2.1 (`data/raw/system/dataverse/`, about 2.0M findings, versus about 5.9M via the API). All of these files are labelled `_dataverse_fallback`. **They are not the API result.**

| File | Rows | What it is |
|---|---|---|
| `data/processed/system_api_master_list_findings_dataverse_fallback.csv` | 97 | One row per cited paper (and per Dataverse finding) |
| `data/processed/system_api_verification_dataverse_fallback.csv` | 228 | One row per citation claim, with badges |
| `data/processed/system_api_verification_numbers_dataverse_fallback.csv` | 105 | One row per claimed number |
| `data/processed/system_api_reverse_check_dataverse_fallback.csv` | 37 | Check 5 |
| `data/processed/system_api_verification_summary_dataverse_fallback.json` | | Counts and funnel |
| `fallback/*.csv` | | Intermediate files (Dataverse rows for cited studies, the evidence index, relationship edges) |

**Paper funnel (Dataverse):** 83 distinct cited papers. This covers the master list, `master_list_graph_status.csv` and the report, normalized to 82 PMIDs plus 1 DOI-only.
- 7 are in the Dataverse studies table, and all 7 have findings (21 findings in total).
- 4 papers have a System finding that matches our claimed number.
- 0 mislabels are detectable, because the Martin-Latry findings (PMID 17513091) are **not** in Dataverse.

**Numbers:** 105 claimed numbers were checked (years are excluded; integers get the abstract check only).
- 5 are shared with System and all 5 agree on number and meaning:
  - Mangoni OR 1.02
  - voriconazole RR 1.72 (counted twice: once from the master list, once from the report)
  - Cincinnati 1999 mental illness OR 14.0 (PMID 11563746)
  - dialysis extreme heat RR 1.31
- There are **0 conflicts** and **0 direction conflicts**.
- The dialysis RR 1.27 is in the API (13 Nov pilot) but not in Dataverse.

**Badges (228 claim rows):**

| Badge | Count |
|---|---|
| ✓✓ | 5 |
| ✓ | 36 |
| ✓ (partial) | 10 |
| ? | 7 |
| ? ↗ | 1 |
| – (no number claimed) | 167 |
| – ↗ | 2 |

Per number: ✓✓ 5, ✓ 74, ? 26.

**Corroboration (↗):** 3 claims, based on Dataverse name-matched findings:
- loop diuretics → dehydration
- thiazides + SSRIs → hyponatremia (counted twice)

20 claims have any System concept edge.

**Reverse check:**
- 17 Dataverse findings on our cited papers are not used by any claim.
- 20 drug × mediator links with at least 5 studies are not in the master list. Most are blood pressure. Others: loop diuretics → AKI (35 studies), SGLT2 → AKI (28 studies, mostly protective), opioids → AKI, antipsychotics → hyponatremia (6 studies, 9 of 9 ratio findings up).

## Method notes (apply to both API and fallback runs)

- **Claims** are the 228 rows of `citation_verification.csv`. For master-list rows, the drug is the row's "Drug or class" and the expected direction comes from "Evidence direction" ("Supports harm" means a ratio above 1 is expected). For report rows, the drug is the nearest drug named before the number in the same sentence.
- **Check 1 (same number):** match to `statistic_value` at the claim's own precision (minimum tolerance 0.005). CI-bound matches are counted separately. Derived matches (the difference of two claimed numbers) are allowed only against System "difference" statistics. Integers are never matched to System values, because they are mostly counts and sample sizes. "Conflict" is **not** inferred automatically: an unmatched number is reported as `paper_in_system_number_not_extracted`.
- **Check 2 (same meaning):** compare the drug group in the claim with the drug group named in System's variable names (`system_terms.py`), or a literal drug-name match.
  - A broader class word ("psychotropic", "antihypertensive", "diuretic", "antidiabetic") that covers the claim's group is recorded as `broader_label` and still counts as a match.
  - A class word that does not cover the group is recorded as `mislabel`. For example, "psychotropic drugs" for anticholinergics, which is exactly the Martin-Latry case; an offline test reproduced it as ⚠.
  - For ratios, the direction must agree.
- **Check 3 (corroboration):** other studies, excluding the cited paper's own study, with the same drug group × outcome group in name-matched findings. Requires at least 2 studies and at least 50% of ratio findings in the claimed direction. Only claims expecting harm are scored.
- **Check 4 (API vs Dataverse):** the matched finding is looked up in `dataverse/associations.csv` by association id, or else by study + variable names + value. `badge_strict_dataverse` demotes ✓✓ to ✓ when the System match exists only in the API.
- **Check 5 (reverse):** unused System findings on cited papers, plus strong System drug × mediator links (at least 5 studies) whose drug × outcome pair does not appear in the master list.

## Caveats

- **No API data.** Every API-based number in the task list (the indexed/findings funnel via the API, ~5.9M findings, concept edges, the rediscovery re-run, live-layer latency) is still **pending a working key**. The pilot numbers in `docs/system-verification.md` (8 papers with API findings, 0 conflicts, the Martin-Latry mislabel) remain the latest API evidence.
- **The rediscovery validation was not redone.** The Dataverse result in `../README.md` stands: diuretics are ranks 1–3, lithium is 7th, antipsychotics 11th and anticholinergics 15th.
- Name matching has false positives and false negatives. The combination rows (e.g. "Thiazides + SSRIs") pool the corroboration of both drugs.
- No human review was done.
