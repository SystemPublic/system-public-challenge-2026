# AI handoff — PATH Visualize 2 (Hackiller)

> **Read this file first, completely, before touching anything.** Two AI agents work on this repo at the
> same time. This document is the single source of truth for context, shared formats, task ownership
> and sync rules. If something here conflicts with another doc, this file wins; then
> `what-works-where/docs/FINDINGS.md`; then `what-works-where/docs/background/final_research_report_zh.md`.

**中文摘要（给人看的）：**
- 两个 AI 并行工作，各自有一个分支和一组只属于自己的目录，互不修改对方的文件。
- 共享的数据格式、字段词表和国家代码都写在第 4 节。
- 任务 A–C 的分工在第 5 节：AI-1 负责证据与整合，AI-2 负责背景数据与全文核验。
- 同步方式和时间节点在第 6 节。
- 截止时间是 15:00 ET。前端开发在 12:45 以后开始。

---

## 1. The project in one paragraph

- **Event:** System Public Challenge 2026, NYC, Saturday 14 Nov 2026.
  - Build window 10:00–15:00 ET.
  - Live 3-minute pitch from 15:00.
- **Challenge:** Visualize 2 (PATH, lead Roberto Amato): *"How does the effect of malaria prevention vary by setting and over time?"*
- **What the brief asks for:** a dashboard comparing the reported effects of **SMC, insecticide-treated nets and malaria vaccines** across countries, study settings and time. It may combine the System Public Graph with other open data; MalariaGEN drug-resistance data is suggested.
- **Judging** (25% each):
  1. meaningful use of the Public Graph
  2. insight / usefulness
  3. technical execution
  4. communication
- **Our thesis:** *Malaria prevention evidence depends on the comparison, the setting and the follow-up period.* The graph almost always has the right number; what it loses is what the number compares. We restore that context, show only checked results as effects, and never pool.

## 2. What exists now (state at 11:25 ET)

| Where | What | Owner of origin |
|---|---|---|
| `main` @ `793892b` | Raw data collection + first-pass cleaning, standard library only (`scripts/clean_data.py`, `scripts/validate_processed.py`, `scripts/restore_system.py`). Outputs in `data/processed/`, reports in `reports/` | teammate (DAzyyyyy, with OpenAI Codex) |
| branch `evidence-pipeline` | Everything on `main` plus `what-works-where/`: evidence pipeline, verified results, review queue, site JSON, docs. Plus this file and `COORDINATION.md` | qianndd (with Claude Code) |

### 2.1 Teammate's data (`main`)

- **`data/raw/system/`**: the full System Public Graph v1 (Dataverse v2.1, CC BY-NC 4.0).
  - Four tables: associations (gz split in 3 parts), studies, variables, concepts.
  - Restore with `python3 scripts/restore_system.py`, which writes to `data/restored/system/` (gitignored) and checks every SHA-256.
- **`data/raw/who/`**: WHO GHO for **BEN and TZA**, all years.
  - Indicators: `MALARIA_ITN_USE`, `MALARIA_ITN_COVERAGE` (both modelled), `MALARIA_EST_INCIDENCE`, `MALARIA_IRS_COVERAGE`.
  - The IRS indicator is a **number of people**, not a percentage.
- **`data/raw/map/`**: Malaria Atlas Project, release **202608**, **BEN and TZA**, 2000–2025.
  - Metrics: `Pf_PR-rate` (children 2–10, a proportion), `Pf_incidence-rate` (per 1,000 per year), `ITN_use-rate` (a proportion).
  - Each comes as mean / lci / uci.
  - Query pattern: `https://data.malariaatlas.org/map-platform-app-backend/api/v1/trends/{malaria|interventions}/{metric}/admin0/{mean|lci|uci}?version=202608&iso3=XXX`
  - Zeros may mean missing.
- **`data/raw/pf8/`**: MalariaGEN Pf8, 33,325 samples, CC BY 4.0.
  - Drug classifications cover: AS-MQ, Artemisinin, Chloroquine, DHA-PPQ, Mefloquine, Piperaquine, Pyrimethamine, SP (IPTp), SP (uncomplicated), Sulfadoxine.
  - **There is no amodiaquine classification.** SMC = SP+AQ, so Pf8 only covers the SP side.
  - Raw crt/mdr1 calls are in `pf8_marker_calls.csv.gz`.
- **`data/raw/literature/`**:
  - Europe PMC core metadata for 11 target PMIDs.
  - **Full-text XML for 8 papers:** PMC8971961 (Tanzania 24 mo, PMID 35339225), PMC7618965 (R21, 38310910), PMC7718580 (ACCESS-SMC, 33278936), PMC9871299 (Mali 5th SMC round, 36704118), PMC6418392 (Cochrane ITN, 30398672), PMC5119693 (Senegal SMC, 27875528), PMC9464075 (RTS,S antibody, 34894221), PMC8457484 (identify).
- **`data/processed/`**:
  - `system_candidates` (331 rows, 203 study records, all `pending_source_review`), `system_review_queue`, `system_study_lookup`
  - `who_context`, `map_context`
  - `pf8_resistance_context`, `pf8_country_year_resistance`
  - `pf8_samples`, `pf8_drug_classifications` (large)
  - Strengths: raw files are never modified, there is a SHA-256 manifest, and there are validation assertions.

### 2.2 Our evidence work (`what-works-where/`)

- **`pipeline/` steps 00–08** (`run_all.sh`):
  1. download the snapshot
  2. extract candidates (416 rows, 239 papers)
  3. classify: intervention subtype, outcome tier, role, statistic family, QC flags
  4. enrich: PubMed title/year/DOI + System study population; country from population, else title
  5. graph context: the `malaria` concept neighbourhood plus 3-layer coverage of the landmark trials
  6. site JSON
  7. review queue
  8. Europe PMC abstract pre-check with quotes, then the hand-reviewed graph rows
- **`data/verified/evidence_verified.csv`**: **20 anchor results from 7 trials**, every number checked against the paper.
- **`data/verified/evidence_graph_checked.csv`**: **20 graph rows reviewed against the abstract**; 11 needed their comparator, time point or label restored (or were excluded).
- **`data/review/review_queue.csv`**: 416 rows with priority 1–4, abstract quotes for priority 1–2 (125 of 142 have the value and CI in the abstract), and blank `verify_*` columns.
- **`site/data/*.json`**: front-end inputs (`verified`, `graph_checked`, `graph`, `context`). `site/index.html` and `site/styles.css` are an **unfinished draft**; ignore them until 12:45.
- **`docs/FINDINGS.md`**: all numbers, the failure catalogue and pitch lines. **`docs/DATA_DICTIONARY.md`**: field definitions.

### 2.3 Overlap and gaps between the two candidate sets

- **283** associations are in both sets.
- **48 are only in the teammate's set** (37 nets, 11 vaccines). The teammate's context rule treats `ITN/LLIN` and `parasite` as malaria context.
  - Important rows in that 48: PMID **36174592** (PBO vs non-PBO LLINs → parasite prevalence, 5 rows), **18461178** (ITN in *low-transmission* areas, 6 rows), 17889242 and 34051817 (ITN → under-5 mortality), and candidate vaccines (PEV3B, ME-TRAP, PfSPZ).
- **133 are only in our set**: mostly net ownership/use or use-as-exposure (observational) rows.

## 3. Fixed facts (do not re-derive; cite these)

**Funnel**

| Step | Count |
|---|---|
| Snapshot associations | 1,999,877 |
| Candidates (ours) | 416 rows / 239 papers |
| Effect or use-as-exposure rows | 333 / 208 papers |
| Rows pre-checked against the abstract | 142 |
| Rows hand-checked against the abstract | 20 (11 needed fixes) |
| Paper-verified anchors | 20 results / 7 trials / 9 papers |

**Verified anchors** (ratio scale; below 1 means fewer events with the intervention)

| Trial (registration) | Setting | Outcome / measure | Chlorfenapyr net | PBO net | Pyriproxyfen net |
|---|---|---|---|---|---|
| Tanzania, NCT03554616 | Misungwi, children 6 mo–14 y, 24 mo | infection, aOR | 0.45 (0.30–0.67) | 0.99 (0.67–1.45) | 0.79 (0.54–1.17) |
| Tanzania, NCT03554616 | Misungwi, 36 mo | infection, OR | 0.57 (0.38–0.86) | 0.95 (0.64–1.42) | 0.82 (0.55–1.23) |
| Benin, NCT03931473 | Zou, children 6 mo–10 y, years 1–2 | clinical cases, HR | 0.54 (0.42–0.70) | — | 0.86 (0.65–1.14) |
| Benin, NCT03931473 | Zou, year 3 | clinical cases, HR | 0.80 (0.56–1.17) | — | 1.02 (0.71–1.44) |

- **R21 Phase 3** (NCT04704830; Burkina Faso, Kenya, Mali, Tanzania; children 5–36 mo; 12 months): HR (= 1 − VE) seasonal 0.25 (0.21–0.29), standard 0.32 (0.26–0.39).
- **RTS,S + SMC** (NCT03143218; Burkina Faso, Mali; 3 years):
  - combination vs SMC alone: PE 62.8% (58.4–66.8)
  - RTS,S alone vs SMC alone: HR 0.92 (0.84–1.01), non-inferiority comparison
- **ACCESS-SMC** (7 Sahel countries, under-5s): 28-day protective effectiveness 88.2% (78.7–93.4); population outpatient-case reduction Nigeria 25.5% (6.1–40.9), The Gambia 55.2% (42.0–65.3).
- **Graph-sourced SMC time evidence** (abstract-checked):
  - Burkina Faso + Mali: dose ≤28 days vs >35 days, hospitalisation/death IRR 0.13 (0.08–0.20).
  - Burkina Faso: infection OR 0.29 at 1 month, 0.33 at 2 months; Nigeria 0.49 (0.23–1.05) at 1 month.
  - Mali: no rebound in the year after IPTc stopped, IRR 1.09 (0.99–1.21).
- **Graph neighbourhood of `malaria`** (concept 7xpZryeSKE): top upstream factors are insecticide-treated bednet 63 studies, rain 24, temperature 23, mosquito net 21. There is **no SMC concept** in the graph; SMC exists only as variable names.

**Showcase geography (agreed proposal)**

| Region code | Countries |
|---|---|
| `east_africa_perennial` | TZA |
| `west_africa_coastal` | BEN |
| `sahel_seasonal` | BFA, MLI, NGA |
| supporting, evidence index only | GHA, GMB, TCD, UGA, KEN, SEN |

## 4. Shared formats (both agents MUST use these exactly)

**IDs**

| ID | Meaning |
|---|---|
| `system_id` | System association |
| `pmid` | Paper |
| `trial_family_id` | One trial = one family; use the registration where known, else a slug like `tanzania-misungwi-dualAI` |
| `result_id` | Our row id in verified tables |
| `iso3` | Country: ISO 3166 alpha-3, uppercase. Multi-country values are `;`-joined, e.g. `BFA;MLI` |

**Vocabularies**

| Field | Allowed values |
|---|---|
| `intervention_class` | `nets` · `smc` · `vaccines` · `combination` |
| `outcome_tier` | `vector / entomological` · `infection` · `clinical malaria` · `severe / hospital` · `anaemia & growth` · `mortality` · `other` |
| `role` | `effect on outcome` · `use or coverage as exposure (observational)` · `uptake / behaviour` |
| `verification_status` | `pending_source_review` · `checked against abstract` · `checked against full text` · `checked against paper` · `label corrected` · `comparator restored` · `time point restored` · `paper supplement` · `excluded: not an intervention effect` |
| `estimate_type` (context data) | `modelled` · `reported_programme` · `survey_observed` · `sampled_cases` |
| `region` | `east_africa_perennial` · `west_africa_coastal` · `sahel_seasonal` · `other` |
| `showcase` | `core` · `supporting` · `index_only` |

**File contracts** (AI-2 produces, AI-1 consumes). Paths are relative to the repo root.

1. `what-works-where/data/context/countries.csv` — one row per country.
   `iso3,name,region,seasonality,showcase,in_who,in_map,in_pf8,notes`
   - `seasonality` is `seasonal` · `perennial` · `mixed`
   - `in_*` are `true` / `false`
2. `what-works-where/data/context/context_country_year.csv` — long format, one row per country × year × indicator.
   `iso3,year,source,indicator,value,lower,upper,unit,estimate_type,release,flags`
   - `source` is `WHO` · `MAP`
   - `indicator` keeps the source code, e.g. `MALARIA_ITN_USE`, `ITN_use-rate`, `Pf_PR-rate`, `Pf_incidence-rate`, `MALARIA_EST_INCIDENCE`
   - `unit` is `percent` · `proportion` · `per_1000_at_risk` · `per_1000_per_year` · `people`
   - Keep units as published. Blank means missing; never fill with 0.
3. `what-works-where/data/context/pf8_sp_country_year.csv`
   `iso3,year,drug,n_determined,n_resistant,n_sensitive,n_undetermined,resistant_share,scope`
   - `drug` ∈ `Sulfadoxine`, `Pyrimethamine`, `SP (uncomplicated)`, `SP (IPTp)`
   - `scope` is always `sampled_cases_not_prevalence`
4. `what-works-where/data/verified/fulltext_checks.csv`
   `result_id,pmid,pmcid,location,quoted_text,value_found,ci_found,matches_our_value,discrepancy_note,checked_by,checked_at`
   - `location` examples: `Table 2`, `Results para 3`, `Abstract`
   - `value_found`, `ci_found`, `matches_our_value` are `Y` / `N`
   - `checked_at` is ISO time

AI-1 owns and produces `site/data/*.json`, `data/review/review_queue.csv`, `data/verified/evidence_*.csv`.

## 5. Task split

### AI-1 — "Evidence & Integration" (Claude Code, this session)

- **Branch:** `evidence-pipeline`
- **Owns:**
  - `what-works-where/pipeline/`
  - `what-works-where/data/{interim,graph,review}/`
  - `what-works-where/data/verified/evidence_*.csv`
  - `what-works-where/site/`
  - `what-works-where/docs/` (except `background/`)
  - `AI_HANDOFF.md`

| Task | What | Done when |
|---|---|---|
| A1 | Read the System tables offline from `data/restored/system/` (run `scripts/restore_system.py`). Use the `studies` table for population, study type and DOI. Keep the API only for the concept neighbourhood and coverage | `run_all.sh` works without `00_download_snapshot.py` when restored files exist |
| A2 | Adopt the context rule (ITN/LLIN/parasite count as malaria context) | ~48 new rows, re-classified |
| A3 | Add the teammate's QC flags (exact/conflicting duplicate ids, `partial_ci`, `p_operator_unspecified`, `ci_level` out of range, study PMID mismatch) and `iso3` from `countries.csv` | flags and `iso3` present in `graph.json` |
| A4 | Merge the two review queues into one `review_queue.csv` keyed by `system_id` (our classification + their flags + `content_hints` + abstract quote) | one queue; the teammate's 331 are all present |
| A5 | `pipeline/validate.py` assertions (verified rows have a source location; plotted rows are positive ratios with ordered CIs; no unknown vocabulary values) | passes |
| C2 | Review the new rows: 36174592 (PBO), 18461178 (low transmission), ITN → under-5 mortality; then priority-1 net rows. Append to `evidence_graph_checked.csv` | ≥10 more checked rows |
| I1 | Integrate AI-2's files into `site/data/context.json` and `verified.json` (attach `fulltext_checks`) | site JSON rebuilt |

### AI-2 — "Context & Full text" (second agent)

- **Branch:** `context-data` (already created from `evidence-pipeline`)
- **Owns:**
  - `scripts/`, `data/raw/`, `data/processed/`, `reports/`, `metadata/` (the teammate's pipeline)
  - `what-works-where/data/context/`
  - `what-works-where/data/verified/fulltext_checks.csv`

| Task | What | Done when |
|---|---|---|
| B1 | Write `countries.csv` for the 5 core + 6 supporting countries (region, seasonality, showcase) | file matches contract 1 |
| B2 | Fetch MAP release 202608 for **BFA, MLI, NGA** (same 3 metrics, mean/lci/uci). Save raw unchanged, extend `clean_map` and the manifest | `map_context` covers 5 countries |
| B3 | Fetch WHO (same 4 indicators) for **BFA, MLI, NGA**; extend `clean_who` | `who_context` covers 5 countries |
| B4 | Export the long table `context_country_year.csv` (WHO + MAP, 5 core countries) | matches contract 2 |
| B5 | Export the Pf8 SP table for BFA, MLI, NGA, GHA, GMB, TZA, BEN (+ KEN) | matches contract 3; note in `notes` that AQ is not classified |
| C1 | Full-text checks: for every `result_id` in `evidence_verified.csv` whose PMID has an XML (35339225, 38310910, 33278936, 36704118, 30398672), plus the abstract-checked rows for 27875528 and 34894221 if present, locate the number in the full text and tables and quote it. Report any mismatch; never silently fix | `fulltext_checks.csv` matches contract 4 |
| B6 (P2) | If time: crt K76T / mdr1 N86Y share by country-year from `pf8_marker_calls` (amodiaquine-related markers), labelled `sampled_cases_not_prevalence` | optional CSV + note |

## 6. Sync protocol

1. **Never edit files you do not own.** Need a change elsewhere? Add a line under *Requests* in `COORDINATION.md` and push.
2. **Commit small, push often**, with a prefix: `[AI-1]` or `[AI-2]`. Never force-push. Never commit `.env`, API keys, `data/restored/`, or any file over 25 MB.
3. **Status:** update your own row in `COORDINATION.md` at every checkpoint (status, last commit, blockers).
4. **Checkpoints (ET):**

   | Time | What happens |
   |---|---|
   | **12:00** | Contract files exist, even partial; push |
   | **12:30** | A–C done; push |
   | **12:35** | AI-1 merges `context-data` into `evidence-pipeline` (only `what-works-where/data/context/` and `data/verified/fulltext_checks.csv` touch our tree) and rebuilds site data |
   | **12:45** | Front end starts (AI-1); AI-2 switches to QA and pitch data checks |
   | **13:45** | Feature freeze |
   | **14:15** | Copy `what-works-where/` into the official fork `SystemPublic/system-public-challenge-2026` under `projects/<team-name>/` |
   | **14:45** | PR opened; link pasted into Devpost |

5. If a contract must change, the requester proposes it in `COORDINATION.md`; AI-1 updates section 4 of this file. Both re-read section 4 after any change.

## 7. Science rules (both agents)

- Keep each result's own effect measure (OR, aOR, HR, IRR, rate ratio). Percentages converted to ratios say so, e.g. "HR (from VE = 1 − HR)". **No pooling, no ranking, no voting by significance.**
- Keep the graph's original label next to any correction, with the reason.
- Follow-up time ≠ publication year. Store both.
- Country comes from the study site or population, never from author affiliations.
- Context data is **modelled** (WHO ITN, MAP) or **sampled cases** (Pf8). It is never a cause of a trial result, never national prevalence, and never SMC efficacy.
- Different outcomes and different effect measures go in different panels. Tanzania (infection, OR) and Benin (clinical, HR) sit side by side and are never combined.
- One country significant and another not is **not** evidence that the countries differ.
- When unsure, mark the row `pending_source_review` and move on. Do not guess.

## 8. Environment notes

- The System API key goes in `what-works-where/.env` as `SYSTEM_API_KEY=...` (gitignored). AI-2 does not need it.
- Python 3.11+. The teammate's scripts use the standard library only; ours use pandas + requests (`what-works-where/requirements.txt`).
- Network hosts used:
  - `public-api.system.com`
  - `dataverse.harvard.edu`
  - `eutils.ncbi.nlm.nih.gov`
  - `www.ebi.ac.uk` (Europe PMC)
  - `ghoapi.azureedge.net` (WHO)
  - `data.malariaatlas.org` (MAP)
- Licences: System-derived data is CC BY-NC 4.0; Pf8 is CC BY 4.0. Code is MIT. `docs/background/` is private material; do **not** copy it into the public submission.
