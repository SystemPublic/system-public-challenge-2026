SCIENCE.md

Domain reference. Agents: do not invent malaria biology. If a fact is not here, it is not established for this project — ask, don't generate.

VERIFY BEFORE USE. Every factual claim below is written from general knowledge and must be checked against the source literature or the WHO compendium by the science lead before it appears in the UI, deck or README.

The one-paragraph version

Malaria is caused by Plasmodium parasites, most dangerously P. falciparum. Specific mutations in parasite genes reduce how well particular drugs work. Those mutations are tracked as resistance markers. New findings about them are published continuously across thousands of papers. A researcher tracking a marker has no simple way to know when the evidence has shifted enough to matter. That gap is what this project addresses.

Demo marker
<!-- FREEZE AT KICKOFF, based on the coverage check, not preference. -->
Gene / alteration: TBD
Drug context: TBD
Chosen because: TBD — must include: the graph has enough findings, and those findings carry resolvable pubmed_id or doi.
Candidate markers
Gene	Key alteration(s)	Drug
pfdhps	A437G, K540E, A581G	sulfadoxine (with pyrimethamine, as SP)
pfdhfr	S108N, N51I, C59R, I164L	pyrimethamine (as SP)
pfcrt	K76T	chloroquine
pfmdr1	N86Y, Y184F, D1246Y	partner drugs; direction varies
kelch13 / K13	C580Y, R561H, P441L, A675V	artemisinin partial resistance

Antifolate (dhfr/dhps) resistance accumulates in a roughly known order, and the literature uses named combinations — triple mutant (dhfr N51I + C59R + S108N), quintuple (dhfr triple + dhps A437G + K540E), sextuple (quintuple + dhps A581G). If the demo marker is one of these, the Learn diagram can show that accumulation. This is a teaching visual only.

Hard constraint: a combination is a property of an individual parasite. Never infer a combination from separate single-mutation findings in different papers.

Search synonyms

GET /v1/variables?search=name:<term>&limit=50&include_total=true, one term at a time. Only name is searchable on variables.

Two grounding caveats from System's own docs, both of which bite here:

Variables that failed to ground to a Wikidata concept were removed from the public release entirely (2.48M of them). A codon-level mutation may simply not be present.
Known failure mode: a SNP matched to its associated gene. K540E may have been collapsed into dhps. Match on variable name text as well as concept ID.

Marker side: dhps, pfdhps, dihydropteroate synthase, dihydropteroate synthetase, dhfr, pfdhfr, dihydrofolate reductase, pfcrt, crt, kelch13, K13, and codon forms K540E, 540E, A437G, A581G, S108N, N51I, C59R, I164L, K76T, C580Y.

Partner side (an association needs two variables): treatment failure, therapeutic efficacy, parasite clearance, recrudescence, parasitaemia, parasitemia, malaria, Plasmodium falciparum, chloroquine, sulfadoxine-pyrimethamine, artemisinin, SP, IPTp, SMC.

American spellings generally return more than British.

Coverage check results
<!-- PASTE REAL IDS AND NAMES HERE. These become graphVariableIds. -->
marker id	graph variable_id	graph variable_name	assoc count
			
What we may and may not claim

May:

This mutation is associated with reduced efficacy of this drug, per this source.
This association was reported with this statistic and effect size, in this paper, which we link to.
This finding was published on this date, so a researcher watching this marker would have learned of it then.
Prior findings on this pair pointed one way; this one points the other.
Our matcher detected this, for this stated reason.

May not:

That a marker's presence means a patient's treatment will fail.
That a divergent finding is wrong, refuted, or an error. Studies differ for good reasons. We flag disagreement; we do not adjudicate.
Any prevalence figure. The graph holds statistical associations, not prevalence measurements.
Any geographic claim sourced to the System graph. The graph has no geography field. Map data comes from a separate source and is attributed to it.
Any numerical forecast. No model has been evaluated.
Comparison of effect sizes across different statistic types.
That absence of evidence is evidence of absence. The graph's own docs say a missing relationship may reflect extraction gaps, grounding failures, or no published study.
Any WHO endorsement, integration or operational readiness.
Any treatment recommendation, for anyone, ever.
Front-page and Data-tab figures

Every number on the Home and Data pages — death tolls, case counts, dates a drug was introduced, when resistance was first reported — must be sourced by a human before it ships. Until then it is a named PLACEHOLDER_* constant in lib/stats.ts and appears in the README TODO block.

Good sources: WHO World Malaria Report, WHO compendium of molecular markers, the original papers. Never a number from memory.

Fill in as sourced:

constant	value	source	checked by
PLACEHOLDER_ANNUAL_DEATHS			
PLACEHOLDER_ANNUAL_CASES			
PLACEHOLDER_SHARE_UNDER_5			
PLACEHOLDER_SHARE_AFRICA			
PLACEHOLDER_DRUG_INTRODUCED_YEAR			
PLACEHOLDER_RESISTANCE_FIRST_REPORTED			
Vocabulary for the pitch
Marker — a mutation tracked as a resistance signal.
Association — the graph's atomic unit: two variables linked by a statistic. This, not prevalence, is what we alert on.
Partial resistance — the correct term for artemisinin. Slowed clearance, not outright treatment failure.
Replay — playing real publication history forward to test the matcher.
Divergence — a new finding pointing the opposite way from prior findings on the same variable pair and statistic type.