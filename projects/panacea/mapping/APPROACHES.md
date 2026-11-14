# Concept-Matching Approaches: NYC Open Data ↔ System Public Graph

How should we match concepts that appear on both sides — NYC's operational indicators and the
System Public Graph's research constructs? This document compares five approaches, states the one
chosen for this phase, and why.

## The objects being matched

| Side | What a "concept" is | Size | Fields available |
|---|---|---|---|
| **SPG** | A Wikidata entity standing for a research construct (e.g. *heat stroke*, *particulates pollution*) | 45,721 total; **473 unique** in challenge domains (486 domain rows) | `wikidata_label`, `wikidata_aliases` (JSON array), `wikidata_description`; **no ontology codes** |
| **NYC** | An operational indicator or controlled value (e.g. *Heat ED visits, Age-adjusted rate (per 100,000)*; cause of death *Diseases of Heart* + ICD-10; 311 complaint condition *NO HEAT*; tree species) | 378 EHDP challenge measures + 37 death causes + 4 complaint conditions + 132 tree species | EHDP: `indicator`, `description`, `measurementType`, `howCalculated`; deaths: `causeName`, `icd10Codes`; trees: `commonName`, `latinName` |

Two structural facts drive everything below:

1. **Construct ≠ indicator.** SPG says *"heat wave"*; NYC says *"Heat ED visits, Age-adjusted
   rate"*. A match is a claim that a research construct and an operational measure refer to the
   same underlying thing — so matches must be **typed** (`equivalent` / `broader-narrower` /
   `related-component` / `no-match`), not binary.
2. **The only shared key is Wikidata's.** SPG concepts carry `wikidata_id` and no MeSH/ICD/UMLS
   codes. NYC data carries no Wikidata ids — except indirectly: death causes carry **ICD-10
   codes**, and Wikidata items carry ICD-10 properties. That makes one deterministic
   crosswalk possible (approach D).

## Approaches

### A. Lexical normalization + alias/string matching
Lowercase, expand abbreviations (ED→emergency department, PM2.5→fine particulate matter), apply a
curated alias table, then exact + fuzzy string scoring (TF-IDF char n-grams, edit distance) over
label + aliases vs indicator name + description.

- ✅ Deterministic and fully explainable — every match can print the rule that produced it.
- ✅ Zero cost, zero dependencies, versionable; fits the challenge's "cite what it rests on".
- ❌ Paraphrase-blind: "tree canopy cover" vs "urban forest" scores near zero.
- ❌ Ambiguous tokens collide: *heat* matches heat exposure, heat ED visits, and NO HEAT
  complaints — three different constructs. Precision depends on the alias list staying current.
- ❌ Long operational measure names overlap weakly with short construct labels → low recall.

### B. Embedding similarity
Embed SPG `label+aliases+description` and NYC `indicator+description+howCalculated` with a
sentence-transformer; cosine top-k above a threshold. (`sentence-transformers` is installed here.)

- ✅ Catches synonyms and paraphrase; offline after one model download; scales to all 45,721 × 900.
- ❌ Topical neighbors score high though the constructs differ — the *heat exposure* /
  *heat ED visits* / *NO HEAT complaint* triple all sit close together in embedding space.
- ❌ Generic models are weak on public-health jargon and acronyms; threshold tuning is fiddly;
  output still needs semantic review downstream (i.e. approach C anyway).

### C. LLM-assisted matching — **chosen for this phase**
Give an LLM both sides with full context and ask for a typed verdict per pair: `match_type`,
`confidence`, and a one-line `rationale`. Scale managed by batching (both sides' challenge-core
vocabularies fit in context together).

- ✅ Best semantic quality: distinguishes "same construct, different operationalization"
  (`broader-narrower`) from "merely same topic" (`related-component`) — exactly the distinction
  the confirm/conflict/bridge analysis depends on.
- ✅ The `rationale` doubles as the audit trail and the dashboard's evidence text.
- ✅ Handles jargon ("UHF42", "age-adjusted rate", "ED visits") natively.
- ❌ Non-deterministic → mitigated by recording rationale per verdict; re-runnable, not replayable.
- ❌ Token cost at full scale (45,721 concepts) — needs candidate pre-generation there.

### D. External-vocabulary anchoring (Wikidata as interlingua)
SPG's only external id is `wikidata_id`. NYC death causes carry ICD-10 codes; Wikidata items carry
ICD-10 properties. Join deaths → Wikidata (by ICD-10) → SPG (by `wikidata_id`) for a deterministic,
citable anchor. For EHDP indicators, Wikidata search can propose candidate Q-ids (best-effort).

- ✅ Exact and reproducible where it works — perfect for the 37 death causes.
- ✅ Uses SPG's native key: no fuzzy step at all on anchored rows.
- ❌ Coverage gaps: EHDP indicators are *measures*, often not Wikidata entities ("Heat ED visits,
  age-adjusted rate" is not a Wikidata item).
- ❌ Disambiguation risk (searching "heat" returns the WWE wrestler); needs network + caching.
- ❌ Complements A–C; cannot match measure-style indicators alone.

### E. Hybrid tiered pipeline
Stack them: D (deterministic anchors) → A (lexical auto-accept) → B (embedding retrieval) →
C (LLM adjudication of candidates) → human review of low confidence.

- ✅ Best overall quality and recall; every tier auditable; the only way to do the full 45k×900 run.
- ❌ Most code and moving parts; thresholds need a validation pass.
- **Status: documented as the follow-up.** If the C-first pass below leaves visible recall gaps,
  add B/A tiers before scaling up.

## Chosen path (this phase)

**C with D as a supporting anchor, at challenge-core scope** — user's call:

1. Build side tables: 473 SPG domain-tagged concepts; NYC = 378 EHDP challenge measures + 37
   death causes + 4 complaint conditions + 132 tree species.
2. Anchor the 37 death causes via ICD-10 → Wikidata → SPG `wikidata_id` (cached).
3. LLM-match every NYC row against the SPG table in context, typed + confidence + rationale.
4. Assemble `concept_map.csv`, a review queue for low-confidence rows, and a coverage report.

Decision rule for the full-scale run later: if review shows misses caused by recall (the right SPG
concept existed but wasn't considered), add B (embeddings) for candidate generation before scaling.

## Scale-up note

Challenge-core matching here costs one LLM pass over ~550 NYC rows against 473 SPG concepts. The
full run (45,721 × ~900) multiplies the SPG side ×97 — that needs approach E's retrieval tiers
first; C alone does not scale to it.
