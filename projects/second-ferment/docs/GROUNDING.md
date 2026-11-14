# Where every part of the app comes from (for Q&A)

Written 2026-11-14 for the demo. "Checked" means we read the paper's abstract and the number matches.

## Data sources

| Source | What we used it for |
|---|---|
| System Public Graph, Dataverse snapshot v2.1 (doi:10.7910/DVN/7V6JDO), 2.0M findings, CC BY-NC 4.0 | Every study count, every drug-side and heat-side link, most study results |
| System Public live API (5.9M findings) | Extra heat findings; always tagged "unvetted: live graph only" |
| PubMed (NCBI E-utilities) | Paper titles, and abstracts to check numbers; abstracts load live in the app |
| 8 heat-health guidance documents (CDC, NYC Health, Arizona, UKHSA, Health Canada, ANSM France, WHO Europe 2026, CALOR) | Guidance text and action sources (teammate's coding) |
| FDA drug labels via openFDA | Label warnings and storage limits (teammate's pull) |
| NYC Heat Vulnerability Index by ZIP | Neighbourhood heat risk in the heat check |
| NWS alerts and Central Park observations (Iowa Environmental Mesonet) | The July and August 2026 NYC heat waves |
| CDC HEAT questionnaire and Five Heat Steps | Intake questions and the patient plan format |

## Evidence atlas, right-hand panel, section by section

| Section | Grounded in | Our judgement or wording |
|---|---|---|
| Headline number (e.g. aOR 2.09) | A real study result; all headline values checked against abstracts | Which study we chose as the headline; the plain-language sentence ("about 2× the odds") is our translation of the number |
| "Every study of this medicine in heat" (forest plot and study cards) | Curated list of graph studies that measured the drug in heat (teammate's list + ours); numbers parsed from the study records; corrections from our abstract checks shown | Not every study's number has been checked against its abstract; unvetted rows are dashed and labelled |
| "Where it acts in the body" (replaced by the body cards) | Our analysis of all 2.0M graph findings: counts of drug-side studies (raised / lowered) and heat-side studies per effect; "Show the studies" lists the actual rows | Which words count as each effect (pattern rules, documented in `docs/MAPPINGS.md`); a shared pathway is a hypothesis, not a measured interaction |
| "What adds to the risk for a patient" | 12 results from 8 papers, every one checked against its abstract (`reference/risk_factors.csv`) | Putting different studies with different outcomes on one plot; the plain sentences are our translation |
| "Potential actions" | Teammate's action list; each tagged Study / Guidance / Label / Mechanism with its sources | Actions tagged "Draft: no source yet" are proposals, not evidence; all wording is for clinician review |
| Circle size in the drug list | — | Our judgement: a 0–5 evidence-strength score per class (`app/src/atlas/headlines.ts`), based on study type, vetting and consistency |
| Body markers | Same counts as "Where it acts" | Marker sizes are scaled from study counts |
| "The short version" | Assembled from the headline study and the strongest body-system links | Template sentences written by us from those facts |
| "How it affects the body in heat" cards | "The drug": mechanism wording from the guidance documents (with the number of documents) and our study counts. "Heat": number of heat studies. "See the evidence": the actual graph rows | The "Heat" description and the "Together" sentence are general physiology as described in CDC, NYC Health, UKHSA and Health Canada guidance, written by us; not from the graph. The strength sentence ("consistent", "well studied") is our rule: ≥60% of drug-side studies raised = consistent; ≥20 heat studies = well studied |

## The risk-factor plot, row by row

| Row | Result | Study | Checked |
|---|---|---|---|
| Working air conditioner | Heat death OR 0.2 (0.1–0.7) | Chicago 1999 heat wave, case-control (Naughton 2002, PMID 11988377) | Yes |
| Air conditioner in the bedroom | Heat-illness admission aOR 0.12 (0.02–0.74) | Adelaide 2009 heat wave, case-control (PMID 27256088) | Yes |
| Living alone | Heat death OR 8.1 (1.4–48.1) | Chicago 1999 (PMID 11988377); OR 2.3 in Chicago 1995 (PMID 8649494) | Yes |
| Not leaving home each day | Heat death OR 5.8 (1.5–22.0) | Chicago 1999 (PMID 11988377) | Yes |
| Social contacts or activities | Admission aOR 0.11 (lower bound 0.02; upper bound not in the abstract) | Adelaide 2009 (PMID 27256088) | Yes, partly |
| Programme to reduce social isolation | Heat-wave mortality in over-80s IRR 0.76 (0.59–0.98) | Italy, ecological study (PMID 34770101) | Yes |
| ZIP code with little green space | Cardiovascular death on extreme-heat days OR 1.17 (1.06–1.29) | Michigan older adults 1990–2007 (PMID 25460667) | Yes |
| Heart disease | Admission aOR 13.56 (1.27–144.86) | Adelaide 2009 (PMID 27256088) | Yes; very wide interval |
| Dementia | Admission aOR 26.43 (1.99–350.73) | Adelaide 2009 (PMID 27256088) | Yes; very wide interval |
| Each additional psychotropic medicine | Death aOR 1.25 (1.21–1.29) | France 2003 heat wave, ages 70–100 (PMID 20104062) | Yes |
| Confined to bed (list only) | Heat death OR 8.2 | Chicago 1995 (PMID 8649494) | Yes |
| Top floor (list only) | Heat death OR 4.7 | Chicago 1995 (PMID 8649494) | Yes |

## Heat check

| Part | Grounded in | Our judgement |
|---|---|---|
| Intake questions | CDC HEAT questionnaire | Wording shortened |
| Neighbourhood score | NYC Heat Vulnerability Index | — |
| Risk points per factor | Factors with a study use its direction and size as a guide | The point values and the Low / Elevated / High / Very high cut-offs are our rule (`app/src/heatcheck/engine.ts`), not a validated score |
| Card colours and order | — | Our rule: mitigation first, intensity from medicine evidence × exposure |
| Card evidence panel | Same sources as the atlas | Bottom-line sentences are our summaries of the cited studies |

## One-line answer for judges

"Every number on screen traces to a study in the System Public Graph or a named public source, and the headline numbers
were checked against the abstracts; what is ours is the selection, the plain-language wording, the evidence-strength
score and the heat-check point rules, and the app labels which is which."

## Labels used in the app (renamed 2026-11-14 for plain language)

| Label | Meaning |
|---|---|
| Direct evidence | A study looked at people taking the drug during hot weather or a heat wave |
| Direct evidence, drug group | Same, but the study looked at a group of drugs together (e.g. blood-pressure medicines) |
| Studied in heat, no clear effect | Studied that way, result indistinguishable from no effect |
| Indirect evidence | Drug and heat each studied separately for the same body effect (previously "shared pathway") |
| No studies | Mentioned in guidance only (previously "guidance only") |

## The graph screen

| Part | Grounded in | Our judgement |
|---|---|---|
| Nodes | Drug classes, body effects and heat are our groupings of graph variables (pattern rules in `docs/MAPPINGS.md`) | The grouping itself |
| Edges | Drug → effect: findings linking a drug variable to an effect variable. Heat → effect: findings linking a heat variable to an effect. Dashed drug ↔ heat: curated direct studies | Edge width scaled from study counts; only direct and indirect links drawn |
| Paper dots and "Findings in the graph" | Every dot is a paper (PubMed ID) with at least one finding on that edge; the panel shows the actual graph rows (variable names, statistic, interval, population, row ID, vetted or not) | Drug-side dots show papers with a finding of raised risk; capped at 32 drug-side and 24 heat-side papers per path |

| Focused path (triangle) | Same rows as above. Medicine–effect side: papers with a raised-risk finding. Heat–effect side: heat papers. Medicine–heat side: the curated direct studies (`reference/direct_evidence.csv`) | Counts are unique papers (PubMed IDs); the "possible pathway, not a measured interaction" note is our framing of indirect evidence |

What the screen does not show: the raw concept graph (Wikidata concepts and the relationships table). The nodes are
our groupings of variables, because concept-level traversal loses the heat context (`docs/DATA.md`, quirk 1).
