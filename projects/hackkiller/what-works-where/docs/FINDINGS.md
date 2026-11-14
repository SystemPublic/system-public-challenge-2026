# Findings: malaria prevention evidence in the System Public Graph

Working notes for the team and the pitch. Every number below comes from files in this repository
(`site/data/*.json`, `data/verified/*.csv`, `data/review/review_queue.csv`) and can be re-run with
`pipeline/run_all.sh`. Data pulled 14 Nov 2026.

## 1. The evidence funnel

| Step | Count | Unit |
|---|---:|---|
| Associations in the fixed graph snapshot (Dataverse v2.1) | 1,999,877 | associations |
| Papers in the snapshot with malaria context (malaria, Plasmodium, Anopheles, mosquito, parasite, ITN, LLIN) | 2,745 | papers |
| Candidates naming a net, SMC or a malaria vaccine (our rule ∪ teammate's rule; all 331 teammate ids included) | 481 | associations, from 273 papers |
| …that are intervention effects or use-as-exposure (not uptake/behaviour) | 333 | associations, from 208 papers |
| Graph rows pre-checked against the abstract (priority 1–2) | 142 | associations; 125 have the value and CI in the abstract |
| Graph rows reviewed by hand against the abstract | 33 | associations; 19 needed context restored or a correction |
| Paper-verified anchor results (nets, SMC, vaccines) | 20 | results, from 7 trials and 9 papers |

Candidates by intervention: nets 212 papers, SMC 14, vaccines 12, RTS,S + SMC combination 1.

Where the candidate papers come from (study population first, then title): Ethiopia 44, Nigeria 19,
Uganda 17, Kenya 15, Tanzania 15, Malawi 13, Burkina Faso 11, Ghana 10, Mali 9, Cameroon 8, Benin 8.
Country unknown for 22 of 239 papers.

Publication years: 13 papers up to 2005, 18 in 2006–10, 57 in 2011–15, 81 in 2016–20, 70 in 2021–25.

## 2. How the graph sees malaria

Concepts the graph links directly to `malaria` (concept 7xpZryeSKE, Wikidata Q12156), ranked by
supporting studies (`/v1/concepts/{id}/relationships?sort=num_studies:desc`).

- Upstream factors with the most studies:
  - insecticide-treated bednet 63
  - gender 42
  - age group 42
  - educational stage 38
  - insecticide 35
  - HIV 27
  - rural area 25
  - rain 24
  - temperature 23
  - mosquito net 21
- Bed nets are the most-studied intervention linked to malaria.
- Climate and environment are among the most-studied settings: rain 24, temperature 23, humidity 10, forest 10.
- The `mosquito net` concept has 33 relationships; `malaria vaccine` has 27, and many of those are uptake topics (vaccine hesitancy, vaccination coverage, literacy).
- There is no `seasonal malaria chemoprevention` concept. SMC exists in the graph only as ungrounded variable names, which is why string search is required.

## 3. Where the landmark trials sit (three layers)

| Paper | API study record | API associations | Filtered snapshot rows |
|---|---|---:|---:|
| Pryce 2018 Cochrane (ITN vs no net) | yes | 0 | 0 |
| ACCESS-SMC 2020 Lancet | yes | 2 (drug-resistance markers, not the effect) | 0 |
| Chandramohan 2021 NEJM (RTS,S ± SMC) | yes | 1 | 0 |
| Mosha 2022 Lancet (Tanzania, 24 mo) | yes | 3 | 0 |
| Mali 5th SMC round 2023 | yes | 2 | 0 |
| Accrombessi 2023 Lancet (Benin, years 1–2) | yes | 2 | 1 |
| Mosha 2024 (Tanzania, 36 mo) | yes | 3 | 0 |
| Datoo 2024 Lancet (R21 Phase 3) | yes | 0 | 0 |
| Accrombessi 2024 (Benin, year 3) | yes | 0 | 0 |

Every trial is in the graph as a study. Six of the nine have no usable findings in the filtered snapshot, and three have no findings even in the Beta API. Their results in the dashboard come from the papers and are labelled "from paper".

## 4. What gets lost between paper and graph (catalogue)

The graph almost always has the right number. What it loses is what the number compares. This matches the structural failure modes described by Tan & D'Souza (2026, arXiv 2602.10881): role reversal, binding drift across analyses, instance compression and numeric misattribution.

| Failure | Example (graph id / PMID) | What happened | Count found |
|---|---|---|---:|
| Arm labels swapped | v_jYJO5RWB, lTQMC2ZnYM, MrlZri8wZD / 37776879 | Three Tanzania 36-month comparisons carry the wrong net type | 3 |
| Arm missing | 3 rows / 35339225 | Three net comparisons share one variable, "use of study LLINs" | 3 |
| Comparator lost | 32822362 | IRR 0.13 compares "dose within 28 days" with "dose more than 35 days ago"; the graph says only "SMC" | 1 |
| Before–after shown as an effect | 36328000; 33278936 | Prevalence ratio 0.27 is 2018 vs 2016 in SMC districts, not SMC vs no SMC | 3 |
| Time point lost | 32252774, 35589153, 36704118 | Year 1 vs year 2; 1 vs 2 months after SMC; November vs December round | 8 |
| Percentage stored as a ratio | 26488565 | Vaccine efficacy 62.7% stored as "hazard_ratio = 62.7" | 1 (3 rows over 20 flagged) |
| Immune correlate stored as a vaccine effect | 21998698; owr0kFL1O8 / 34894221 | T-cell or antibody high-vs-low comparisons among vaccinees | 2 |
| Exposure is the absence of the intervention | 29 rows, e.g. 32840203 | "no ITN use" → OR 30.1; the direction is the reverse of an intervention effect | 29 |
| Contradictory direction within one paper | 36221068 | "non-use of ITN" appears with OR 2.13 and with OR 0.26 | 1 paper |
| Duplicate rows | 34662864 | The same RR 0.81 (0.71–0.93) stored 3 times | several |
| No confidence interval | — | Cannot be plotted honestly | 75 |
| API `ci_level` = 0 | Beta API | Snapshot shows 0.95 for the same row; API 17 of 18 sampled rows show 0 | — |

We built a verification layer, not a critique. System's own documentation estimates that about 20% of Beta API associations have extraction-accuracy issues and recommends cross-checking against the Dataverse snapshot. Every correction above keeps the original graph label, the corrected label and the reason.

## 5. Evidence stories (all checked against papers or abstracts)

### Nets: the same trial, three years

| Trial | Outcome | Chlorfenapyr net | PBO net | Pyriproxyfen net |
|---|---|---|---|---|
| Tanzania, 24 mo | infection, aOR | **0.45 (0.30–0.67)** | 0.99 (0.67–1.45) | 0.79 (0.54–1.17) |
| Tanzania, 36 mo | infection, OR | **0.57 (0.38–0.86)** | 0.95 (0.64–1.42) | 0.82 (0.55–1.23) |
| Benin, years 1–2 | clinical cases, HR | **0.54 (0.42–0.70)** | — | 0.86 (0.65–1.14) |
| Benin, year 3 | clinical cases, HR | 0.80 (0.56–1.17) | — | 1.02 (0.71–1.44) |

- The chlorfenapyr net outperformed the standard net in both trials in the first two years.
- By year 3 in Benin the interval crosses 1.
- Tanzania measured infection and Benin measured clinical cases, so the two trials are shown side by side, never pooled.

### SMC: protection depends on time since the dose and on the country

| Context | Result | Source |
|---|---|---|
| Within 28 days of a dose vs more than 35 days ago | Hospitalisation or death IRR **0.13 (0.08–0.20)** | Burkina Faso and Mali, 32822362 |
| Infection during the SMC campaign | Burkina Faso OR **0.28 (0.21–0.37)**; Nigeria OR **0.40 (0.30–0.55)** | 35589153 |
| 1 month after a round | Burkina Faso OR **0.29 (0.12–0.72)**; Nigeria **0.49 (0.23–1.05)**, interval crosses 1 | 35589153 |
| 2 months after a round | Burkina Faso **0.33 (0.17–0.64)** | 35589153 |
| Year after stopping IPTc | IRR **1.09 (0.99–1.21)**: no significant rebound | Mali, 21858096 |
| Individual vs population level | 28-day protective effectiveness 88.2% (78.7–93.4), but outpatient cases fell 25.5% in Nigeria vs 55.2% in The Gambia | ACCESS-SMC |
| Routine programme, before–after | HR 0.27 (year 1) and 0.23 (year 2) | Mali, 32252774 |
| Routine programme, modelled | RR 0.81 | Chad, 34662864 |

### Vaccines: the setting and the comparator matter

| Comparison | Result | Source |
|---|---|---|
| R21 at seasonal vs standard sites, 12 months | HR 0.25 (0.21–0.29) vs 0.32 (0.26–0.39), i.e. VE 75% vs 68% | Datoo 2024 |
| RTS,S + SMC vs SMC alone, 3 years | PE 62.8% (58.4–66.8) | Chandramohan 2021 |
| RTS,S alone vs SMC alone | HR 0.92 (0.84–1.01): non-inferior; the comparator is SMC, not placebo | Chandramohan 2021 |
| RTS,S/AS02 over time | Effect strongest in the first 3 months (HR 0.62) and weakens | Kenya re-analysis, 32536547 |
| RTS,S by parasite genotype | VE 62.7% vs parasites matching the vaccine, 54.2% vs mismatched | 26488565, after correcting the graph's "HR 62.7" |

### Nets beyond the two dual-AI trials (added 11:50, abstract-checked)
- Uganda LLINEUP (cRCT, 48 districts): PBO vs conventional LLINs, parasite prevalence PR **0.80 (0.69–0.93)** at 25 months; within the PBO arm prevalence fell 28.8% → 12.0% by 6 months (PR 0.43). Graph row had lost the non-PBO comparator.
- ITN → child mortality: Kenya cRCT infants HR **0.78 (0.67–0.90)**; Kenya longitudinal 1–59 mo rate ratio **0.56 (0.33–0.96)**; Malawi ownership HR **0.75 (0.62–0.90)**; Congo ownership RR **0.76 (0.64–0.90)**; Tanzania HDSS per +10% village ownership IRR 0.946 (Rufiji) / 0.899 (Ifakara).
- Over time: Burkina Faso birth cohort, ITN from birth vs from 6 months, mortality rate ratio **1.05 (0.89–1.24)** after a median 8.3 years, i.e. no late rebound.
- Setting / age: Cambodia cRCT, the effect on prevalence was larger in under-5s (OR 0.63) than older ages (interaction p=0.042).
- Two graph labels corrected: "malaria transmission and child mortality" was actually Anopheles per house (RR 0.23); "malaria morbidity and mortality" was clinical P. falciparum incidence.

## 6. Lines for the pitch

- "The graph almost always has the right number. What it loses is what the number compares."
- "Malaria prevention evidence depends on the comparison, the setting and the follow-up period."
- "Of 33 graph findings we checked against the source, 19 needed their comparator, time point or label restored before they could be shown."
- "SMC's protection lives in the 28 days after a dose: hospitalisation IRR 0.13 vs children dosed more than 35 days earlier."
- "In the graph, the most-studied factors around malaria are bed nets, rain and temperature: prevention and climate in the same network."

## 7. Limits

- Open-access literature only. Keyword discovery can miss studies.
- Abstract checks confirm that a number exists. They do not assess risk of bias.
- Before–after, modelled and observational studies are labelled as such and never mixed with randomised results in one panel.
- A significant result in one country and a non-significant one in another is not evidence of a difference between countries.
