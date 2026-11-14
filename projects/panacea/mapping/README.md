# Concept Map: NYC Open Data ↔ System Public Graph

Typed, cited mapping between NYC operational indicators and SPG research
constructs. Feeds the confirm/conflict/bridge analysis in `../insights/`.

## The map

- **`out/concept_map.csv`** — 668 rows, one per (NYC row, SPG concept) match.
  Columns: NYC id/label/collection, SPG id/wikidata_id/label/domains,
  `match_type` (`equivalent` | `broader-narrower` | `related-component`),
  `confidence`, `method` (`anchor` = ICD-10→Wikidata→SPG join, `llm` =
  in-session LLM adjudication), `rationale`, and dataset-version citations.
- **`out/review_queue.csv`** — 164 rows to eyeball (low confidence, or medium
  related-component).
- **`out/unmatched_nyc.csv`** — 159 NYC rows with no SPG counterpart
  (research-gap seed). Street-tree species are unmatched *by design*: SPG has
  no species-level concepts; street trees connect via the EHDP
  grass-and-tree-cover measure instead.
- **`out/report.md`** — coverage and counts. Coverage: EHDP 93%, complaints
  100%, death causes 97%, trees 0% (by design).

## Pipeline

1. `build_side_tables.py` — SPG: the 473 challenge-domain concepts (from
   `eda/out/domain_concepts.csv`) enriched with aliases/descriptions. NYC:
   378 EHDP challenge measures + 31 canonical death causes (label-level,
   ICD-10, spelling variants merged) + 4 complaint conditions + 132 tree
   species.
2. `wikidata_anchors.py` — deaths: ICD-10 → Wikidata (P494, SPARQL batch +
   name search, claims-verified) → SPG `wikidata_id` join against the FULL
   45,721-concept set. Cached in `cache/wikidata/`.
3. `emit_batches.py` — compact adjudication batches; lexical (TF-IDF char
   n-gram) supplement candidates from the wider concept set so recall isn't
   bounded by the 473.
4. LLM matching (in-session): family-level verdicts for EHDP
   (`expand_adjudications_ehdp.py`), row-level for deaths/complaints
   (`expand_adjudications_rest.py`), including explicit rejection of noisy
   anchors. SPG ids used beyond the 473 were individually verified to exist
   in the full concept set.
5. `make_outputs.py` — assembles the map, review queue, unmatched list, and
   report.

## Choices worth knowing

- **Typed matches, not binary.** SPG holds *constructs* ("heat illness");
  NYC holds *operational measures* ("Heat ED visits, Age-adjusted rate").
  ~90 equivalent / 412 broader-narrower / 166 related-component rows.
- **Deaths are matched at cause level.** DOHMH's cause labels carry
  near-duplicate spellings ("Posioning", "Nephrisis") and year-varying ICD
  definitions; causes are canonicalized by casefolded label with code
  variants recorded.
- **Anchor rejections are recorded**, not silently dropped
  (`adjudications_rest.jsonl`, `action: reject_anchor`) — e.g. 'gangrene'
  matched to I70.2 for atherosclerosis, parent classes marked equivalent.
- **Wikidata anchoring is a bonus tier, not the backbone.** Wikidata search
  surfaces related-but-wrong items (early-onset Alzheimer's, "obsolete
  benign hypertensive heart disease"), and the SPG concept space is
  study-specific, so canonical items are often absent. It anchored 6 rows
  after adjudication; LLM matching covers the rest.
- **Only surfaced SPG ids are used.** Verdicts may cite concepts outside the
  473, but each such id was verified to exist in the full concept CSV
  (e.g. `amXWjMd84N` Lyme disease, `DQbECFISI6` diabetes).

## Re-run

```bash
python3 -I mapping/build_side_tables.py        # ~4 min (streams two large ndjson.gz)
python3 -I mapping/wikidata_anchors.py         # cached; only new causes hit the network
python3 -I mapping/emit_batches.py             # regenerate batch files
# ... adjudication edits in expand_adjudications_*.py ...
python3 -I mapping/expand_adjudications_ehdp.py
python3 -I mapping/expand_adjudications_rest.py
python3 -I mapping/make_outputs.py
```

`APPROACHES.md` documents the five candidate matching approaches and why
LLM-first (with Wikidata anchors) was chosen for this phase.
