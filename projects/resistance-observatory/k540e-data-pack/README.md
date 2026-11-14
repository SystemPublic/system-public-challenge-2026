# PfDHPS K540E alert data pack

Prepared 14 November 2026 for the System Public Challenge (Build Challenge 3). Assembled with AI assistance from public sources; include that in the project's AI-use disclosure.

| File | What it holds | Source and licence |
|---|---|---|
| `k540e-genomes.json` | Counts of samples carrying K540E, by country and collection year, 33 countries, 1966-2022, plus the companion markers A581G, A437G and the DHFR/DHPS quintuple haplotype | MalariaGEN Pf8, https://zenodo.org/records/18681980. CC BY 4.0 |
| `k540e-study-context.json` | For each of the 222 K540E country-year cells: partner study codes, Admin-1 sites, DNA preparation method, % callable genome, mixed-genotype and alternative codon-540 (K540N) calls, and up to 5 ENA run accessions for samples carrying K540E | MalariaGEN Pf8 sample metadata and marker genotypes, https://zenodo.org/records/18681980. CC BY 4.0 |
| `k540e-literature.json` | 372 PubMed papers that mention K540E (1997-2026) with publication dates and countries; 55 K540E prevalence figures stated in abstracts; 125 abstract sentences linking K540E or its haplotypes to an outcome; 6 first-report claims | PubMed, searched 14 November 2026. Machine-read, quote-verified, not human-checked |
| `k540e-graph.json` | What the System Public Graph holds: 3 findings on K540E-containing haplotypes, 22 findings on what sulfadoxine-pyrimethamine does for patients, 21 findings the graph extracted from the 10 K540E papers it has read, concept IDs, and the vetted association ID list | System Public Graph, https://doi.org/10.7910/DVN/7V6JDO. Non-commercial use |
| `k540e-thresholds.json` | The marker's WHO status, the WHO SP-resistance categories quoted verbatim with page reference, their history, and this project's notification presets | WHO guidelines for malaria (13 August 2025) and other WHO documents linked inside the file |

## Things to keep true

- A country-year with no row was not sampled. It is missing, not zero.
- Genome counts are convenience samples, not designed prevalence surveys. Mixed-genotype samples are counted as carrying the mutation. They are dated by collection year; there is no per-paper publication date.
- Abstract figures come from different study designs and definitions. Never pool them with each other or with the genome counts.
- Abstract items were extracted by a language model. A program kept only those whose quote appears word for word in the abstract and, for prevalence, contains the number and "540". Nobody checked them by hand, so always show the quote and the link.
- The graph has no finding that names K540E alone. Two graph findings (`489sn1mPQa`, `gD0V6goixf`) were compared against their paper, and one more (`4avf24yKnZ`) among the paper findings; everything else is reported by the graph and unverified.
- The 22 SP findings were hand-selected for readability. They are a sample, not a systematic review. A 23rd, `PEyo2A8Ol0` (PMID 26429700), was removed: its relative risk of 0.32 is dihydroartemisinin-piperaquine compared against SP, which the graph presents in the reverse direction.
- The WHO categories grade resistance in East and Southern Africa by K540E. In Central and West Africa WHO uses A437G instead, so K540E thresholds there are project presets.
- Presets are notification defaults, not clinical or policy rules.

## Citation

System, Inc. (2026). System Public Graph (Version 2.1) [Data set]. DOI: https://doi.org/10.7910/DVN/7V6JDO
