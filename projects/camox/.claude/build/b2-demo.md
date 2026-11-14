# B2 demo layer: Jobs Evidence Map (14 Nov)

Read `.claude/AGENTS.md` and `build/spec.md` first. This file is the **thin demo layer** on top of the general product. It keeps the submission inside the rules of Build Challenge 2 (World Bank, jobs agenda). It must not change the general layer's design. Anything B2-specific is content (a profile, a role file, demo questions, a write-up), never a hard-coded branch in tools, prompts or schemas.

Product owner for B2: Vishnu. His full brief is `docs/BUILD_BRIEF.md` in the hackathon folder. This file is the cut of it that fits before the 14:00 freeze.

## The challenge in one line

Take a World Bank indicator. Show what published evidence links it to, how strong each link is, and which *other* World Bank indicators measure those linked things, especially ones in a different dataset. Show where the evidence runs out.

## Product rules (from Vishnu's brief, apply to the demo)

1. **Start from the question, not the dataset.** The user types a topic and never needs to know what WDI or WBL is.
2. **Less obvious first.** Rank links that cross datasets above expected ones.
3. **Gaps are a result.** Thin evidence and "no indicator measures this" are shown as findings, never hidden.
4. **Every link ends in data you can pull.** The answer names indicator ids the user can download.

Plus: use "linked to" and "associated with". The graph's variable_1 → variable_2 order follows how each paper worded it, not cause → effect, so the demo shows one "Linked to X" list, not "what affects X".

## Measured coverage (12:30, local graph + Data360 search)

| Group | Seed | Graph concept (studies) | World Bank datasets the search returns |
|---|---|---|---|
| Outcome | unemployment | unemployment (1279) | WDI |
| Outcome | income | income (2278), household income (1255) | WDI |
| Outcome | informal employment | informal economy (25) | WDI |
| Pillar 1 | internet use | Internet use (382), Internet (179) | WDI, FINDEX |
| Pillar 1 | life expectancy | life expectancy (190) | WDI |
| Pillar 2 | maternity / parental leave | parental leave (54) | WBL, HNP, GS |
| Pillar 2 | childcare | child care (108), day care (142) | WBL |
| Pillar 2 | labor regulation | none found for "labor law" | B-READY (search "business ready labor regulation"), ES |
| Pillar 3 | access to finance | none found | ES, FINDATA, WDI |
| Pillar 3 | foreign investment | foreign direct investment (44) | WDI |
| Public sector | public-sector pay | public sector (37), government employee (36) | WWBI, BOOST |

Early read: outcomes and Pillar 1 are well covered, and Pillars 2 and 3 are thin. This is the headline for guidance question 3. Re-check it with the real runs before it goes in the pitch.

## What the general layer must already do (check, don't build new)

1. **Dataset on each indicator.** `search_worldbank_indicators` returns a `database` field (WB_WDI, WB_WBL, WB_ES, WB_BREADY, ...). **Bug:** some hits return `database: None`. Drop those hits or label them "unknown dataset", so the cross-dataset flag never compares against None.
2. **Gaps render as results.** A thin link and a concept with no matching indicator each get a visible, labelled state on the card (see `skills/agent-ux`).
3. **Undirected wording.** No "affects" / "drives" anywhere in B2 output.
4. **Indicator export.** The answer's indicator ids, names, datasets and the evidence behind each (concept, study count) can be downloaded as CSV. This is the one piece that may be missing. Smallest version: a "Download indicators" button on the answer that builds the CSV in the browser from the answer JSON.
5. **Replayable runs.** One finished run per demo question, replayable through `/api/runs/{id}/events` if the network is slow.

## One drop-in specialist: `agents/roles/indicator-map.md`

Only if the dev agrees it fits the general layer. It is general: it works for any World Bank indicator, not just jobs.

- **description** (what the planner reads): "Given a World Bank indicator or topic, finds what published evidence links it to and which other World Bank indicators measure those linked things, flagging links that cross datasets and gaps."
- **section:** reuse an existing type if one fits (evidence cards with an indicator per card, or policy links). A new `indicator_map` section needs the lead's OK, a contract and a renderer.
- **Steps for the prompt:**
  1. Find the seed indicator with `search_worldbank_indicators`; note its dataset.
  2. Match it to graph concepts with `search_concepts` and `search_variables`. Record the match as exact, narrower, broader or proxy, with one sentence why. This answers guidance question 2.
  3. Take the strongest `neighbours` (by studies). For the top ones, get counts from `summarise_evidence`.
  4. For each neighbour, `search_worldbank_indicators` with the neighbour's label. Mark it **different dataset** when the dataset differs from the seed's. Mark it **data gap** when the evidence is moderate or strong but no indicator matches.
  5. Order links: different-dataset first, then by study count. Keep 5–8 links.
  6. Name the gaps and where to look next.

## Demo path (3 runs, about 2 minutes of the pitch)

| # | Query (World Bank jobs analyst profile) | Must show |
|---|---|---|
| 1 | "What is internet use linked to, and which World Bank data measures it?" | A strong concept match; at least one link to an indicator in a different dataset (e.g. WDI → FINDEX or WBL); one data gap; then the CSV download |
| 2 | "What does the evidence say about maternity leave and women's employment?" | A WBL indicator; thin or moderate evidence shown honestly with study counts |
| 3 | "Which parts of the jobs agenda does the evidence cover well?" | The coverage contrast: outcomes and Pillar 1 strong, Pillars 2–3 thin, with Enterprise Surveys or B-READY named as thin |

Last 20 seconds: one non-jobs query (e.g. the malaria hypothesis) to show the same layer is general.

Expected results go into the test loop in `skills/agent-workflow`. If a run contradicts the coverage table above, trust the run and update this file.

## Guidance questions and where each answer comes from

| Question | Source |
|---|---|
| 1. Linked indicators in other datasets? | Demo run 1: the different-dataset links |
| 2. How well do indicator definitions match graph concepts? | Match types recorded in step 2 across the demo runs; a short count (exact / narrower / broader / proxy / none) in the README |
| 3. What does the evidence cover well or poorly? | The coverage table above, confirmed by run 3 |
| 4. Where to look next, where the evidence runs out? | The gaps on every card |

Answers go in the README's "How we used the System Public Graph" and "Limitations" sections, and on the slides.

## Out of scope today

Separate Streamlit app, local embeddings, a 50-pair gold set with precision and recall, ILOSTAT, the Global Labor Database, multi-hop paths, fetching data in the pull list. Mention them in the pitch as next steps.

## Open questions

- Dev: does `indicator-map` fit as a role, and which section type does it reuse?
- Dev: is the CSV export in scope before 14:00?
- Vishnu: are demo queries 2 and 3 the ones he wants? Who presents?
