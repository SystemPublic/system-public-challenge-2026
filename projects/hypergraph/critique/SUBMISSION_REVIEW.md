# Submission review: deck, README and pages

Written 13 November 2026 by a reviewer who had not seen the team's reasoning. The deck was read first as a judge would read it, then every number was checked against `claims/outcomes/`, `critique/`, `docs/`, `viz/data/` and `data/cache/sysgraph/`. The pages were opened from `python3 -m http.server` at 1440 by 900 and at about 770 wide. Nothing was edited except this file.

## The ten most important fixes

1. **State the idea on the cover.** The idea (an edge is a continuing meta-analysis, and the city adds a registered test to it) first appears on slide 4. The cover and slide 2 describe a concordance exercise and two organisations. Put the `edgefield` sentence on the cover as the title or subtitle, and move `audiences` to the appendix. Files: `deck/project/slides/cover.html`, `deck/project/deck.json`.

2. **Reword the `edgepanel` title.** The four records are percent changes labelled as odds ratios. Their digits and intervals match the abstracts. "All four stored records are wrong" is true of the label and misdescribes the fault (details in Part 2). Suggested title: "All four records store a percent change as an odds ratio; read correctly, the studies and two cities agree in direction". The city slopes (1.146 and 1.131) lie above the pooled interval (1.039 to 1.092) and are for shootings, so "agree" needs "in direction". Files: `deck/project/slides/edgepanel.html`, and the "record wrong" label in `viz/hypergraph.html`.

3. **Finish the README.** It still has two "[TO BE FILLED IN BY JEFF]" placeholders (members, link to slides). It says "only the two replication packages" and "`replication/`: two packages", while `docs/replication.md` reports ten and the folder holds twelve. Its list of pages omits `viz/hypergraph.html` and `viz/heat_drugs.html`, the two pages the deck leads with. Files: `tools/submission/README.md`, then rebuild `submission/projects/hypergraph/README.md`.

4. **Correct the cover's blanket claims.** "94 predictions registered before the data were read, tested, checked by referees, and packaged for replication" is contradicted by the deck's own `lineage` slide (2 read the outcome first, 11 cannot be shown either way), by the count of outcomes (93), by the referee reports (87 of 93 outcomes have one) and by the packages (10 of 93). The `replication` title "A replication package for every result" has the same fault. Files: `deck/project/slides/cover.html`, `deck/project/slides/replication.html`.

5. **Fix the `power` slide.** It says no test was registered on the cold, asthma and absence chain. `graph-triad-cold-asthma-absence` was registered on it and is in the scorecard as unsettled. It also says the chain explains "under 1%" of the 10% excess; the outcome and the referee say about 8% of the log ratio (0.7% against 10%). File: `deck/project/slides/power.html`. The same two statements are in `docs/what_the_graph_adds.md`, sections 3 and 5.

6. **Make the rule count agree.** `method` says "Eight reading rules", `scorecard` says "Twelve", `selection` cites rule 12. `concord/claims.py` has twelve. File: `deck/project/slides/method.html`.

7. **Qualify the chain on `edgesedges`.** The referee of `bridge-heat-shootings-ems` found that about a third of the endpoint's events are the first link's events, so the endpoint could not have been below 1.054, and that the composed interval is the range of an assumed parameter. The label "bridged" was written after the outcome (rule 7 note in `concord/claims.py`). The slide shows the chain as a clean success. Add one line: "weak test: the endpoint shares events with the first link". File: `deck/project/slides/edgesedges.html`.

8. **Remove or source "All 74 claims export as 313 versioned records".** The repository has 94 registrations, and I found no file that gives 313. File: `deck/project/slides/provenance.html`.

9. **Fix the ambulance row on `next`.** "Traffic at most a third of +2.3 minutes" joins two different results. The registered Manhattan share is 0.331 (0.295 to 0.367) of the rise in travel time, so "about a third", not "at most". The +2.3 minutes is the citywide rise in response time, where traffic is 15% to 30% and the figures are exploratory (`docs/ems_response.md`). File: `deck/project/slides/next.html`.

10. **Repair the dashboard's first screen.** `viz/index.html` links to four of the eight pages and omits the heat and medicines page, the levers page and the simulator. Its rows are claim ids such as `construction2-rows-per-job-dobnow`, which is the first row a judge sees. A "Fixture (invented)" button sits beside the real data. Use the claim titles that `viz/evidence.html` already shows, hide the fixture button, and use one navigation bar on every page. `viz/levers.html` shows 1,116 lots that "resemble the Philadelphia trial lots" in its table, while the deck and the referee say 1,087 pass a screen and about a third qualify. Files: `viz/index.html`, `viz/levers.html`, `viz/data/levers.js`.

## Part 1. As a judge with five minutes

### The one idea

The idea is that a link between two variables in the System graph should be treated as an object: a small meta-analysis that keeps growing, to which a city adds its own registered and refereed test, with every number tied to a dataset version. Relations among such links (chains, contradictions, shared papers, modification by a third variable) are the hypergraph.

It is not stated in the first two slides. The cover states a different and weaker idea (what research and city data agree on), and slide 2 is about the organisers. The team name, Hypergraph, appears only in the eyebrow of slide 4.

The parts are not new. Forest plots, living meta-analyses, registered reports and replication packages all exist. What is new is the combination: attaching a locally registered test to each edge of a machine-extracted graph, using the city result to find extraction errors, and drawing the edge rather than the node. That is enough for a hackathon, provided the deck says it in the first thirty seconds.

### What holds attention and what loses it

These hold attention:

- `edgepanel`. Four stored values (4.90, 6.20, 0.088, 0.095), four abstract values, a pooled value and two cities, in one picture. It is concrete and it speaks to all three audiences.
- `heatdrugs`. It answers the World Bank judge's stated interest directly, and the spoke map reads in a few seconds.
- `selection`. A placebo undoing a confirmation is easy to grasp and reflects well on the method.
- `drift`. The three numbers (519, 903, 9th to 17th) make the case for versions without argument.
- `scorecard`. The bar with unsettled as the largest group is credible because it is unflattering.

These lose it:

- `audiences`. It tells the judges who they are.
- `next`. An eight-row table at 26 px. "Contested" in the verdict column means the registered prediction was refuted, which a viewer will read as "the busway is disputed".
- `replication`. Six steps and two cards; the densest slide in the deck.
- `gaps` and `audit`. Each carries five or more unrelated facts.
- `provenance`, `lineage`, `drift` and `replication` in a row. Four slides on record-keeping at the end will run out the clock.

On the pages, `viz/heat_drugs.html` and section B of `viz/hypergraph.html` hold attention. The edge field in section A is too dense to read at laptop width, and the concordance strip on `viz/index.html` opens with rows named by id.

### A cut to ten slides for five minutes

1. `cover` (with the edge sentence added): "The System graph links variables by findings from papers; we treat each link as a running meta-analysis and add a city's registered test to it."
2. `edgefield`: "Here are 69 links with 1,123 findings from 625 papers; each mark is one finding, and the coloured capsule is New York's own estimate on 25 of them."
3. `edgepanel`: "Open temperature and homicide: the graph stores four percent changes as odds ratios, the abstracts give about 6% per 5 °C, and shootings in New York and Chicago rise 15% and 13%."
4. `heatdrugs`: "For heat and medicines the graph holds the conditions but almost none of the drug classes, and New York's open data cannot test it because they give the prescriber's ZIP code, not the patient's."
5. `method`: "Every prediction was hashed and pushed before its outcome data were fetched, and a referee who had not seen the reasoning rebuilt the deciding number."
6. `scorecard`: "Of 93 scored claims, 33 are confirmed, 19 contested and 36 unsettled, and the referees changed eleven verdicts, eight of them toward the middle."
7. `selection`: "A placebo year with no cameras showed the same rise in rear-end crashes as the camera year, so that confirmation was withdrawn, and two turn-calming confirmations are not causal."
8. `lineage`: "The record also shows where we fell short: two claims read their outcome before registering, and eleven more cannot be shown to be blind."
9. `drift`: "In five months the city deleted 519 restaurants from its inspection table and lowered 485 scores, so a result cited by update time cannot be rerun; a versioned collection can."
10. `requests`: "Three changes would make the graph usable for cities: store which variable is the exposure, return every finding the API counts, and give urban exposures their own concepts."

### A cut to six slides for three minutes

1. `edgefield`: "We treat each link in the System graph as a running meta-analysis and add a city's registered test to it; here are 69 links."
2. `edgepanel`: "On temperature and homicide the graph stores four percent changes as odds ratios; read correctly, the studies and two cities agree in direction."
3. `heatdrugs`: "On heat and medicines the graph has the conditions and lacks the drug classes, and the city test needs prescription data by residence."
4. `scorecard`: "Ninety-three registered tests gave 33 confirmations and 36 unsettled results, and blind referees changed eleven verdicts."
5. `drift`: "The city rewrote the table under one analysis within five months, which is why each number cites a fixed version."
6. `requests`: "Our three requests to System are direction, retrievable findings and urban concepts."

### Questions the deck does not answer

System will ask how this scales. The 69 edges were chosen by hand and 139 findings were read by agents against abstracts. The deck does not say whether the percent-as-ratio fault can be detected mechanically across the two million associations (a ratio with an interval that excludes the plausible range, or `ci_level` 0, which all four homicide records have), or what an AI could now do with the graph that it could not do before the audit.

Knowledge Futures will ask what is in the Underlay today. The deck says nothing has been published and that the account lacks an organisation. It does not show the schema of a claim record, a verdict revision as two versions of one record, or one slide number resolved to a version hash. It also does not say how a referee's disagreement would be stored as a contested assertion.

The World Bank judge will ask whether medicines change the effect of heat. The deck says the records are missing. It does not say that the one study that tested the interaction directly (Layton 2020, quoted on `viz/heat_drugs.html`) found none, or that the central power scenario had a negative sign. The judge will also ask where the heat and health result is: `heat-ed-syndromic` (heat-illness emergency visits 4.09 times higher per 5 °C) is confirmed and packaged, and it is on no slide. Shootings carry the heat story instead. A third question is whether any of this transfers to a city without an open data portal.

## Part 2. As a referee

### Mismatches

| Slide | The slide says | The source says | Source |
|---|---|---|---|
| `cover` | 94 predictions registered before the data were read, tested, refereed and packaged | 93 outcomes; 2 claims read the outcome first; 6 outcomes have no referee report; 10 claims packaged | `claims/outcomes/`, `docs/lineage_audit.md`, `critique/`, `docs/replication.md` |
| `method` | Eight reading rules | Twelve | `concord/claims.py`, `PRECEDENCE` |
| `scorecard` | Every outcome was re-estimated by a referee | No report for `construction2-rows-per-job-dobnow`, `construction2-rows-per-job-legacy-2000s`, `further-datacentre-share-manhattan`, `further-repro-dsny-rat-sightings`, `further-tidal-flooding-311`, `transit-fhv-price-subway` | `critique/`; `docs/lineage_audit.md` names the first two |
| `scorecard` | Referees reproduced the deciding numbers | The levers referee rebuilt 1,087 of 2,678, not 1,116 | `claims/outcomes/levers-vacant-lot-trial-match.json` |
| `edgepanel` | All four stored records are wrong | Percent changes labelled as odds ratios; digits and intervals correct | `data/cache/sysgraph/3a1d0e1d5aeb262e41bb17b6.json` |
| `edgepanel` | The abstracts and two cities agree | City slopes 1.146 and 1.131 lie above the pooled 1.039 to 1.092; `prediction_scored` is "partial" | `claims/outcomes/heat-shootings.json` |
| `edgesedges` | Chain shown as a hit without caveat | Endpoint shares about a third of its events with the first link; the test "refutes only for k outside about [-0.08, 1.09]" | `critique/bridge-heat-shootings-ems.md` |
| `heatdrugs` and `audit` | "Between a fifth and a third" of records wrong or lost a qualifier | Heat and medicines: 26 of 62, or 42% | `docs/heat_drugs.md` |
| `audit` (notes) | 114 records, 22% wrong | 6 wrong and 19 lost a qualifier; 22% is the two together | `docs/all_boats.md` |
| `power` | No test was registered on the chain | `graph-triad-cold-asthma-absence` was registered as a bridge | `claims/registered/graph-triad-cold-asthma-absence.json` |
| `power` | The asthma chain explains under 1% of the excess | About 8% of the log ratio | `claims/outcomes/graph-triad-cold-asthma-absence.json` |
| `next` | Traffic at most a third of +2.3 minutes | Share 0.331 (0.295 to 0.367) of the Manhattan travel-time rise; +2.32 minutes is the citywide response-time rise | `claims/outcomes/ems-traffic-share-2019-2026.json`, `docs/ems_response.md` |
| `selection` | A placebo undid two confirmations | The README says three (`rlc-expansion-rearend`, `ems-taxi-2026-onset`, `bridge-crz-injury-crashes`); rule 11 revisions are the first two | `tools/submission/README.md`, outcome `revision` fields |
| `provenance` | All 74 claims export as 313 records | 94 registrations; no source found for 313 | `claims/registered/`; `docs/REPORT.md` line 65 has the stale 74 |
| `drift` | 485 scores lowered, 509 violations removed, all in one direction | All 485 scores fell; 8 violation codes were added and 21 grades moved the other way | `docs/underlay_drift.md` |
| `replication` | A package for every result; the sealed test reproduced "both claims tested" | Ten packaged, all ten sealed; two could not be packaged | `docs/replication.md` |
| `replication` (notes) | Copies up to 20 MB | Cap is now 15 MB; the first two used 20 | `docs/replication.md` |
| `literatures` | City data show the change happened | The weekday deficit is measured; its attribution to hybrid work "was not tested" | `docs/what_the_graph_adds.md` |
| `close` | Credits "Jeff Vernon" on the cover; GitHub path is `jvnickerson` | Confirm the name and that the repository is public | `deck/project/slides/cover.html`, `close.html` |

### 1. The temperature and homicide records

The cached response for relationship `4FaXcuNJRt|YZku29igbl` holds four associations, all with `statistic_type` "odds_ratio":

- 4.9 (1.6 to 8.1), PMID 36858215
- 6.2 (1.6 to 11.0), PMID 36858215
- 0.095 (0.043 to 0.15), PMID 32738768
- 0.088 (0.015 to 0.166), PMID 32738768

The registration quotes the abstracts as +4.9% (1.6 to 8.1) per 5 °C for Rahman 2023, and +9.5% (4.3 to 15.0) and +8.8% (1.5 to 16.6) for Xu 2020. So every value and every interval in the graph is a faithful copy of the paper's number. Rahman's are stored as percents and Xu's as fractions, and both are labelled odds ratios.

The verdict is that they are percent changes mislabelled as odds ratios, not wrong numbers. Read as stored, the records are badly misleading: 0.088 as an odds ratio is a 91% fall and reverses the sign, and 4.9 is nearly a fivefold rise. So "wrong" can be defended, but the slide should name the fault. Naming it is more useful to System, because a unit fault with two conventions in one relationship is a pattern that can be searched for. The speaker notes already say this; the title should too.

The pooled value checks: a fixed-effect inverse-variance pool of 1.049, 1.088 and 1.095 gives 1.065 (1.039 to 1.092). The third Rahman record (6.2) has no matching interval in the registration's quotation and is left out of the pool, which the slide's alt text states.

### 2. Counts

- `scorecard`: 33, 1, 36, 19 and 4 match `claims/outcomes/` (93 of 94; `construction-2022-rush-units-2027` has no outcome). Eleven verdicts changed: eight toward unsettled, one away (`mob-crz-air-nyccas`), two sideways (`bridge-heat-shootings-ems` to bridged, `mob-crz-air` to no test). Twelve rules is right.
- `review`: 11, 8, 1 and 2 match the outcome histories.
- `lineage`: 33 of 46, 11 (ten in class c and one in class e) and 2 match `docs/lineage_audit.md`. The slide omits that the 46 are out of 84 claims with a recorded fetch time.
- `drift`: 519, 24, 903, 485, 509, 9th to 17th, 31,482, 92,745, 287,728 and 2,388 match `docs/underlay_drift.md` and `docs/underlay_publish.md`. Only "all in one direction" overstates.
- `next`: twenty claims were registered from 11:54 to 14:18 on 13 November and all twenty have `notes_referee`. The rows match their outcomes except the ambulance row above.
- `levers`: 0.57, −6.8%, 0.78, 68,746, 855, 9,392, 85,306, 1,087, 1,409, 36%, 3%, 1.6% and 17% match `docs/levers.md`.
- `edgefield` and `edgesedges`: 69, 1,123, 625, 25, 44, 20 of 615 and 117 match `viz/data/hypergraph.json`.
- `heatdrugs`: 62, 36, 12, 14, 4.6, 6.0 and D = 2.1 match `docs/heat_drugs.md`.
- `gaps`, `simulator`, `shape`, `replication` step numbers: all match their sources.

### 3. Wording stronger than `notes_referee` or `verdict_note` allows

- `edgesedges`, the chain (above).
- `simulator`: "The fitted link did not transfer." The verdict note says two storm days carry 84% of the identifying variation, that day-level data cannot identify the relation in either year, and that "the level miss cannot be assigned to the link".
- `simulator`: storefront vacancy "did not rise by 1.2 points relative to the rest of the city" is the registered comparison and is worded correctly. It should not be shortened in speech to "vacancy did not rise".
- `next`: "Supermarkets and diabetes: confirmed null". The referee adds that the outcome tracks poverty and access to care and that the lower bound is 0.88 in two variants.
- `next`: "M14 bus speed, confirmed" carries "mostly before opening", which is the referee's point. This row is fair.
- `levers` (slide) is fair; `viz/levers.html` is not (fix 10).
- `shape`: "Counting them by calendar date changed three results." No verdict was revised (rule 4); "would change" is accurate.

### Class-d claims

No slide names `afford-gentrification-prevalence`, and the `lineage` slide and the README both say neither class-d claim is a blind test. Two things still need attention. `shape` uses the `heat-extremes-downturn` result ("In four hot cities assaults stop rising at about 35 °C and do not fall") with no mark that it was not blind, inside a deck whose `cover` and `method` say every prediction was written before its data were read. Its lower limit above 1.00 is also fragile under seven variants, though "stop rising and do not fall" is the wording the referee approved. And both claims are inside the scorecard's 33 confirmed and 19 contested without a footnote. Add "(not a blind test)" to the sentence on `shape` and a footnote to `scorecard`.

## Part 3. The pages

No relative `src` or `href` in the five pages is broken, and none passes through a symbolic link. Links to `../critique/*.md` and `../docs/*.md` open as raw Markdown text in a browser. The dashboard and explorer need cdnjs for D3, so they fail without a network.

Fixes, ranked by how much they matter in a 60-second look:

1. `viz/index.html`: rows are labelled with claim ids, and the default order puts two construction bookkeeping claims first. Show titles, and open on the heat claims or on the order by kind.
2. `viz/index.html`: the navigation has four links. `viz/explorer.html` and `viz/explore.html` have the same four. A judge who starts at the dashboard cannot reach heat and medicines, levers or the simulator. `viz/evidence.html` and `viz/levers.html` lack the link to heat and medicines. Labels differ between pages ("Levers" and "City levers", "Toll simulator" and "Policy simulator").
3. `viz/hypergraph.html`: section A at laptop width draws 69 rows in two columns with marks a few pixels wide. Labels are cut ("temperature (therm…", "street trees and can…", "heat × anticholinerg…"). Notes such as "graph counts 2, returns 0" overlap the bars. Open the page with one group expanded, or lead with section B, which is the readable part.
4. `viz/hypergraph.html`: 49 console errors on each load, `<circle> attribute cx: Expected length, "NaN"`, from the mark template at line 153. Findings with no position on the ratio axis are being drawn. The page still renders.
5. `viz/hypergraph.html`, section B: the column "Statistic as stored" prints "OR 4.90" in black and the abstract value in small orange text under it, with "record wrong" at the far right. A first-time viewer reads 4.90 as the finding. Strike through the stored value or put the abstract value first.
6. `viz/index.html`: the "Fixture (invented)" button invites the thought that some data are invented. Hide it unless `?fixture=1`.
7. `viz/levers.html`: the table says 1,116 lots "resemble the Philadelphia trial lots (registered test)". The referee's figure is 1,087 that pass a screen, with 28 of 40 checked not vacant blighted land. The caveat is lower on the page; the table cell is what is read.
8. `viz/evidence.html`: it opens on `?claim=rlc-expansion-rearend` with no explanation of why that claim, and axis text is 8.5 px. The page is 9,800 px tall; the filter "With a placebo" is the best 60-second view and could be the default.
9. `viz/heat_drugs.html`: clear on first view. The tile "18 of 40 findings drawn that the graph lacks" reads awkwardly; "18 of the 40 findings drawn are not in the graph" is plainer. Mark size is the log of the ratio "capped at 1.4", which a viewer will not guess; a one-line size legend beside the map would help.
10. On a narrow window (about 770 px) the headers of `viz/hypergraph.html` wrap to eight lines before any graphic appears. This matters only if a judge opens the page on a tablet.
