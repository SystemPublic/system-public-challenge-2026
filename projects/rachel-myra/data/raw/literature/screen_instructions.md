# Instructions given to each LLM screening subagent (verbatim brief)

Repo: /Users/myraclark/system-hackathon. You screen + extract literature records for "The Missing Label" (which common medications make heat more dangerous). Fully automated, no human review.

1. Read the fixed rules: data/raw/literature/screening_rules.md (do NOT change them).
2. For each assigned chunk data/raw/literature/screen_chunks/chunk_NNN.jsonl (one JSON record per line: record_id, year, title, journal, pub_types, mesh, abstract (may be truncated at 2500 chars), query_classes = which drug query found it ("storage" = storage query), text_drug_classes = regex guess, may be wrong), read it in parts with the Read tool (e.g. 40 lines at a time) and decide include/exclude for EVERY record per the rules.
3. After finishing each chunk, write two CSVs with Python's csv module (never hand-format CSV), e.g. `python3 - <<'EOF' ... EOF` with a list of dicts:
   - data/raw/literature/screen_results/chunk_NNN.csv — one row per record in the chunk (all of them), columns:
     `record_id,decision,reason,drug_class,outcome_type,design`
     decision = include|exclude. reason = rule code (I1/I2 or E2–E8) + short text (≤15 words); prefix `uncertain:` when you include on doubt. Use only the controlled values for drug_class / outcome_type / design listed in the rules (drug_class `multiple` when several of the 15; `none` for excluded records with no relevant drug).
   - data/raw/literature/screen_results/extract_NNN.csv — one row per INCLUDED record (and per distinct drug if a record reports separate results for several of the 15 drugs), columns:
     `record_id,drug,drug_class,outcome,population,design,heat_definition,direction,effect_type,effect_value,ci_lower,ci_upper,effect_text,notes`
     - drug: the specific drug/class as named in the abstract. population: short (e.g. "adults ≥65, Ontario", "healthy volunteers n=10", "lab: insulin vials").
     - heat_definition: how heat was defined, quoted/condensed from the abstract (e.g. "heat wave: ≥3 days Tmax ≥32°C", "storage at 37°C for 4 weeks"), or "not stated".
     - direction: harm | null | protective | mixed | not_stated (harm = drug increases heat-related risk, or heat degrades the drug).
     - effect_type: OR, RR, HR, IRR, RER, %change, mean difference, potency %, etc., or blank.
     - effect_value / ci_lower / ci_upper: copy the number EXACTLY as written in the abstract (same digits and decimals). If the abstract gives no number, leave blank. NEVER compute, round, convert or infer a number. Pick the single main drug × heat result.
     - effect_text: the shortest verbatim substring of the abstract containing the number (≤200 chars), copied exactly.
4. Keep CSV text ASCII-safe where possible; no newlines inside fields.
5. Only write those two files per chunk. Do not edit any other file, do not git commit. Do not re-read rules between chunks.
6. When done, report briefly: chunks done, n include / n exclude per chunk, any problems.

## Conventions added after wave 1 (chunks 001–008), applied to later chunks
- Self-controlled case series → design `case_crossover` (tier 2), note "SCCS".
- Illicit methamphetamine → `adhd_stimulants` (note "illicit").
- Keep the abstract's exact characters (non-breaking spaces, "·" decimals) in effect_text so the verbatim check passes.
- Ranges with no single number ("3- to 5-fold") → leave effect_value blank, describe in notes.
