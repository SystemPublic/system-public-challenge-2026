# Cut lists for the talk

These two orders come from `critique/SUBMISSION_REVIEW.md` (Part 1). Each line gives the slide file and one sentence to say. The sentences are corrected for the edits of 13 November: the cover now states the idea, and the counts are 94 registered, 93 scored, 87 with a referee report and twelve packaged for replication. The full deck order is in `deck/project/deck.json`; `audiences` is now an appendix after `close`.

## Ten slides, five minutes

Revised on 14 November after the strips were added. These are the first ten slides of the deck, in order; `close` follows them and everything after it is backup.

1. `cover`: "The System graph links variables by findings from papers; we treat each link as a running meta-analysis and add a city's registered test to it."
2. `edgefield`: "Here are 69 links with 1,123 findings from 625 papers; each mark is one finding, and the coloured capsule is New York's own estimate on 25 of them."
3. `edgepanel`: "Open temperature and homicide: the graph stores four percent changes as odds ratios, the abstracts pool to about 6.5% per 5 °C, and shootings in New York and Chicago rise 15% and 13%, so they agree in direction."
4. `stripheat`: "A link changes, so we draw it as a strip: the graph's edge, then two cities' tests, then three tested steps of which people outdoors removes 44% of the slope, then a conjecture about medicines that nobody has tested."
5. `striprivals`: "A strip can also hold rival conjectures: five reasons heat might raise shootings, two through behaviour and three through the body; some of them disagree about shootings indoors, so we registered that test this morning: shootings rise 17% per 5 °C outside and not at all inside, which rules out an effect that follows people indoors."
6. `method`: "Each prediction was hashed and committed before it was scored, and a referee who had not seen the reasoning rebuilt the deciding number for 87 of the 93 outcomes."
7. `scorecard`: "Of 93 scored claims, 33 are confirmed, 19 contested and 36 unsettled; the referees changed eleven verdicts, eight of them toward unsettled, and two claims were not blind tests."
8. `stripcameras`: "Here is one withdrawal as a strip: the camera test gave 1.33, the same test a year earlier with no cameras gave 1.25, and the arrow turns grey."
9. `drift`: "In five months the city deleted 519 restaurants from its inspection table and lowered 485 scores, so a result cited by update time cannot be rerun; a versioned collection can."
10. `requests`: "Three changes would make the graph usable for cities and would let strips be drawn from its version history: store which variable is the exposure, return every finding the API counts, and give urban exposures their own concepts."

On 14 November `striprivals` replaced `heatdrugs` as slide 5; `heatdrugs` and `stripmoon` are in backup. If a slide must go, drop `drift`.

## Six slides, three minutes

1. `edgefield`: "We treat each link in the System graph as a running meta-analysis and add a city's registered test to it; here are 69 links."
2. `edgepanel`: "On temperature and homicide the graph stores four percent changes as odds ratios; read correctly, the studies and two cities agree in direction."
3. `heatdrugs`: "On heat and medicines the graph has the conditions and lacks most of the drug classes, and the city test needs prescription data by residence."
4. `scorecard`: "Ninety-three scored tests gave 33 confirmations and 36 unsettled results, and blind referees changed eleven verdicts."
5. `drift`: "The city rewrote the table under one analysis within five months, which is why each number cites a fixed version."
6. `requests`: "Our three requests to System are direction, retrievable findings and urban concepts."

## Notes

- The three-minute order has no cover. Say the team name and the idea over `edgefield`.
- `replication` is in neither cut. If asked, twelve claims are packaged and all twelve reproduced in a sealed test.
- `power`, `provenance` and `next` were corrected on 13 November and can be shown in questions.

## The deck of 14 November (`deck2/`), ten slides, five minutes

This deck leads with the process: how a new piece of evidence changes the reading of an old one. It is a separate artifact, and the deck above is kept.

1. `cover`: "A graph of findings is never finished; we built a procedure and a drawing for what happens when new evidence arrives."
2. `edgefield`: "Each link in the System graph is a running meta-analysis; here are 69 links with 1,123 findings, and New York's own estimate on 25 of them."
3. `stripheat`: "One link as a strip: the graph says 7% more homicide per 5 °C, two cities' shootings say 15% and 13%, and of three steps we tested, people outdoors carries 44% of the slope."
4. `striprivals`: "The literature gives five reasons; some disagree about shootings indoors, so this morning we registered that test: 17% outside, 1% inside, on 24,000 shootings."
5. `stripmedicine`: "Yesterday we had our own conjecture, about medicines; the evidence counts against it, so the arrow is red, and the health risk stays."
6. `stripcameras`: "The same thing happens to confirmed results: the camera test gave 1.33, the same test a year earlier with no cameras gave 1.25, and the confirmation was withdrawn."
7. `stripair`: "And to our tests when a new paper arrives: a 2025 study outside the graph finds what our district test did not, and the strip ends on the measurement that would decide."
8. `record`: "Ninety-six scored predictions: 36 confirmed, 36 unsettled, 19 contested; referees changed eleven verdicts, and one corrected us this morning within the hour."
9. `use`: "What a city can use: heat acts on shootings outdoors, safety evaluations need a placebo year, and results need a fixed version of the data."
10. `requests`: "Three fields would let any collection draw its own strips: direction and design, withdrawal records, and version differences."

If a slide must go, drop `stripair`.
