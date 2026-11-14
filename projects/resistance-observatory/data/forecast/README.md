# Forecast tab data

Pinned evidence layers for one marker: K540E in the parasite gene pfdhps (*Plasmodium falciparum*). The marker is associated with reduced efficacy of sulfadoxine, one half of sulfadoxine-pyrimethamine (SP). Nothing here is a prediction or a prevalence estimate. Typed access: `lib/forecast/data.ts` (contract in `lib/forecast/types.ts`).

| File | What | Shape |
|---|---|---|
| `genome-k540e.json` | MalariaGEN Pf8 calls at pfdhps codon 540, by country and sample collection year | `GenomeDataset` |
| `graph-findings.json` | System Public Graph findings about SP or explicit 540E that name a country | `GraphDataset` |
| `papers.json` | 372 PubMed papers that mention K540E, from the Alert tab's data pack (publication clock) | `PapersDataset` |
| `graph-vetted.json` | For each of our 498 pulled Graph records: is it in System's vetted associations CSV (true) or served by the API only (false) | `{source, file, checksum, method, checkedAt, ids}` |
| `policy-milestones.json` | WHO policy milestones copied verbatim from the Alert tab's pack (`k540e-thresholds.json` `history`, commit a1cc503). No thresholds, categories or presets are copied | `{source, items: PolicyMilestone[]}` |
| `alerts.placeholder.json` | Two badged placeholder alerts for layout only, used until `data/alerts.json` (the Alert tab) exists | `AlertRecord[]` |
| `raw/graph/` | 284 cached System API responses (checked: none contains the API key), `work/` stage outputs, `sp_findings.json` (recon output), `dataverse-studies-subset.tsv` | |
| `raw/openalex/` | Raw OpenAlex responses used for publication dates and titles | |

## Source 1: MalariaGEN Pf8 (genome layer)

- Landing page: https://www.malariagen.net/resource/36/
- Files (not committed; downloaded 2026-11-14T16:04:38Z):

| File | URL | Lines (incl. header) | SHA-256 |
|---|---|---|---|
| Pf8_drug_resistance_marker_genotypes.tsv | https://pf8-release.cog.sanger.ac.uk/Pf8_drug_resistance_marker_genotypes.tsv | 24,410 (24,409 samples) | `866450e8b32a5f6433f813932565579512cc5e0424b999d6769818988840e4ed` |
| Pf8_samples.txt | https://pf8-release.cog.sanger.ac.uk/metadata/Pf8_samples.txt | 33,326 (33,325 samples) | `50b7dcf2d0ffea0ef429f62801a0e184ab4da4d22708f9ec685652062c8dadb0` |
| Pf8_README.txt | https://pf8-release.cog.sanger.ac.uk/Pf8_README.txt | | `c20655313e89cb66c3156be060532fb111c2d48d153e23ed7df6d7f446f2821d` |

- Licence (verbatim from Pf8_README.txt): "These data are available open access under the terms of the Creative Commons Attribution 4.0 International license (CC-BY 4.0). Publications using these data should acknowledge and cite the source of the data."
- Citation (verbatim from Pf8_README.txt): "This publication uses data from MalariaGEN as described in 'Pf8: An open dataset of Plasmodium falciparum genome variation in 33,325 worldwide samples', MalariaGEN et al., Wellcome Open Research, 2025; 10: 325 DOI: 10.12688/wellcomeopenres.24031.1"

### Counting rules (column `dhps_540[K]`, QC-pass samples, metadata `Country` and `Year`)
- `kOnly`: every haplotype is K (`K`, `K,K`). No mutation at codon 540.
- `eOnly`: `E`. Carries K540E.
- `mixedWithE`: a mixed call including E (`K,E`, `E,K`, `E,N`, `N,E`). Counted as carrying K540E, kept separate.
- `other`: a usable call with no E that is not K only (`N`, `Y`, `K,N`, `N,K`, `K,Y`, `Y,K`). Tested, but not K540E.
- `missing`: `-`, or any value containing `*` (9 calls: `E,N*` 5, `N,E*` 3, `K,D*` 1). The Pf8 README says `*` calls "are perhaps best considered missing". Not part of `tested`.
- `tested = kOnly + eOnly + mixedWithE + other`; `withE = eOnly + mixedWithE`.
- A country-year appears only if it has at least one genotyped sample. A missing year means not sampled, never zero.

33 countries have genotyped samples (1966 to 2022). The ISO3 lookup in the script lists 34 names: Honduras is in the Pf8 metadata (8 samples) but has no row in the genotype file, so it has no data here.

Reconciliation: identical to the Alert tab's data pack at commit a1cc503 for all 222 country-years (pack `observations.dhps_K540E` numerator/denominator = our `withE`/`tested`).

### Known limits
- Samples come from partner studies, not national surveys: counts are not national prevalence.
- Country is where the sample was collected; the clock is collection year, not publication year.

### Regenerate
```sh
python3 -I scripts/forecast/pf8_k540e.py <Pf8_drug_resistance_marker_genotypes.tsv> <Pf8_samples.txt> 2026-11-14T16:04:38Z data/forecast/genome-k540e.json
```

## Source 2: System Public Graph (graph layer)

- System Public Graph v2.1, snapshot 2026-07-01, CC BY-NC 4.0. Citation (verbatim, as in the Alert tab's data pack): "System, Inc. (2026). System Public Graph (Version 2.1) [Data set]. DOI: https://doi.org/10.7910/DVN/7V6JDO". API v1.0, https://public-api.system.com/v1/. Responses retrieved 2026-11-14 between 16:02 and 16:05 UTC (file times of `raw/graph/`).
- Work deriving from the Graph inherits CC BY-NC 4.0.
- Selection rule: see `selectionRule` in `graph-findings.json` (from the recon summary). Kinds: `sp` = a variable name refers to SP; `codon540` = a variable name explicitly includes 540E. Other dhps findings (44) are dropped.
- Totals, computed from all 454 SP and 540E records: SP 443 (139 name a country, 255 have no study record); codon540 11 (11 name a country, 8 papers). `findings` lists the 150 that name a country.
- Four codon540 findings stay in `graph-findings.json` and `graph-verification.json` but are hidden in the app (`MIS_EXTRACTED_IDS` in `lib/forecast/data.ts`): `paFNq6MPX5` and `AeI-laBxXr` (PMID 25564249), `iD_4aq3uIs` (PMID 29854394, Cameroon) and `QIrkddNp_j` (PMID 16023986, Nigeria). Each was checked against its source paper and found mis-extracted: the first two by a human check of the abstract plus the vetted CSV, the last two by the AI-assisted spot-check. Same exclusion as the Data tab (`data/graph-stats.json`, `marker.associations` with `vetted: false`). The ids are hardcoded in `data.ts` (that file is not imported by the app); `check-data.mjs` fails if they drift from `graph-stats.json`. Every count over displayed findings excludes them.

## Used by other tabs

`data/forecast/graph-verification.json` is imported read-only by `lib/findings.ts` (Learn, Data, Overview). Its path and the fields `checkedBy`, `records[].systemId`, `records[].status`, `records[].where` and `records[].note` must not change. `check-data.mjs` checks that shape.
- `spLooksLikeUptake` is a name-based hint only (the SP variable name looks like an uptake or coverage measure).
- `dataverse-studies-subset.tsv` holds the 57 study rows used from the Dataverse studies table (the upstream file is comma-separated despite its `.tsv` name; the subset keeps that format). The other 12 study records came from the API (`raw/graph/studies_*.json`).

### Known limits
- The Graph has no geography field: countries are matched from the free text of each study's population description (161 finding-country matches among the 150 kept findings) or a variable name (2).
- The Graph has no per-finding publication date or title: those come from OpenAlex.
- System's documentation says about 20% of associations served by the API are known-bad extractions. These findings have not been checked against the papers.
- 255 SP findings have no study record, so their country is unknown and they are not in `findings`.

### Regenerate
```sh
# re-fetch only if needed (needs SYSTEM_API_KEY in the environment; cached responses are reused)
set -a; source .env.local; set +a; python3 -I scripts/forecast/graph/fetch.py <stage>
# offline: recon output (set DATAVERSE_STUDIES=<full studies.tsv> to use the full table)
python3 -I scripts/forecast/graph/analyze.py
# OpenAlex (network, no key, no email) then the pinned layer
python3 -I scripts/forecast/graph/build_layer.py openalex data/forecast/raw/graph/sp_findings.json data/forecast/raw/openalex
python3 -I scripts/forecast/graph/build_layer.py build data/forecast/raw/graph/sp_findings.json data/forecast/raw/openalex data/forecast/graph-findings.json
python3 -I scripts/forecast/graph/build_layer.py subset data/forecast/raw/graph/sp_findings.json <full studies.tsv> data/forecast/raw/graph/dataverse-studies-subset.tsv
```

## Source 3: OpenAlex (publication metadata)

- https://api.openalex.org/works, filtered by PubMed ID, 2 requests, 69 distinct PMIDs, all 69 resolved, so all 150 findings have a title, publication date and year (1994 to 2023). Titles are verbatim from OpenAlex, including its spacing artefacts. OpenAlex data is CC0.

## Source 4: PubMed papers that mention K540E (papers layer)

- From the Alert tab's data pack, `k540e-data-pack/k540e-literature.json` on branch `david/alert-tab`, commit a1cc503. Its `_meta`: source "PubMed (NCBI E-utilities), searched 2026-11-14"; licence "Bibliographic metadata from PubMed; quotes are short excerpts from abstracts, shown with attribution and a link to the source."; the query and method are copied verbatim into `source.notes`.
- 372 papers (1997 to 2026), every one kept. 334 name at least one country; 38 name none. 10 are read by the Graph (pack field `in_graph`: the paper's PubMed ID is in the Graph's CSV snapshot). 41 have no publication month (`month: null`).
- Countries were machine-read from abstracts by the pack's pipeline and have not been checked by a human. Abstracts only; definitions differ between papers.
- The clock is publication date, unlike the genome layer (collection year). `MIN_YEAR`/`MAX_YEAR` in `lib/forecast/data.ts` span every clock (currently 1966 to 2026: genome 1966-2022, papers 1997-2026, Graph papers 1994-2023); `GENOME_MIN_YEAR`/`GENOME_MAX_YEAR` keep the genome range. After 2022 the genome layer simply has no newer samples; 88 papers were published after 2022.
- Regenerate (after the branch merges): `python3 -I scripts/forecast/build_papers.py k540e-data-pack/k540e-literature.json data/forecast/papers.json a1cc503`

## Vetted release membership (`inVettedCsv`)

System publishes a vetted bulk snapshot of the Graph on Harvard Dataverse (doi:10.7910/DVN/7V6JDO, version 2.1, released 2026-07-22). Its associations file is `system-public-graph-v1-associations.csv` (442,463,948 bytes, 1,999,877 rows per the dataset MANIFEST; SHA-256 `a9c8ba3db760efec0d08c65c17c36f0066073062d8e1ff8ea40cc71679daddf9`, MD5 `c884dd1132957f69ffea45404f29db61`; id column `system_id`). The live API serves more associations than that file; System's documentation says about 20% of API associations are known-bad extractions.

- `inVettedCsv: true`: the finding's `system_id` is in the vetted associations file. `false`: served by the API only. `null`: not determined.
- Source used for the current flags: the PRIMARY file. Downloaded from https://dataverse.harvard.edu/api/access/datafile/14061020 on 2026-11-14 (16:58:43Z to 17:03:11Z), complete: 442,463,948 bytes, SHA-256 equal to the MANIFEST value above, 1,999,877 data rows scanned. Not committed. 107 of our 498 pulled records are in it.
- Cross-check with the Alert tab pack's `vetted_association_ids` (4,912 ids, commit a1cc503): it agrees on 496 of our 498 records. Two records are in the CSV but missing from the pack's list: `CJSUyFiyCF` (SP, Burkina Faso, displayed) and `8H-_xZF5xZ` (other dhps, not displayed). All 26 ids the pack lists as `haplotype_findings` and `stakes_sp` are in the CSV.
- None of the 11 `codon540` findings is in the vetted list.

### The three haplotype findings are shown as not country-specific
The Alert tab's pack treats `o23pQ-icgn`, `gD0V6goixf` and `489sn1mPQa` as the marker's own Graph findings (K540E-containing quintuple or sextuple haplotypes), and all three are in System's vetted CSV. By our country rule (a country only from the Graph's population text or a variable name) none of them names a country, so they carry `countries: []`. To keep both tabs consistent without breaking that rule, they are listed in every country panel (`graphFindingsFor(...).haplotype`, `globalHaplotypeFindings()`) and labelled as not country-specific. They are left out of every per-country and headline count (`graphCountsByCountry`, `GRAPH_VETTED.counts`, `GRAPH_VERIFICATION.counts`, `totals.spNamingCountry`); `GRAPH_VETTED.globalHaplotype` counts them separately. Their papers were resolved through OpenAlex like the others (`raw/openalex/works_pmid_02.json`).
- Regenerate from the primary file: `python3 -I scripts/forecast/graph/vetted_membership.py csv <associations.csv> <checkedAt> data/forecast/raw/graph/sp_findings.json data/forecast/graph-vetted.json`, then rerun `build_layer.py build ... data/forecast/graph-vetted.json`. Fallback: same command with `pack <k540e-graph.json>`.

## Spot-check against the papers

`graph-verification.json` (written by another agent; this layer only reads it) compares Graph findings with their source papers: the PubMed abstract and, where Europe PMC serves it, the open full text. It is "AI-assisted spot-check (Claude subagent); not reviewed by a human" (its `checkedBy`). Its `method`, `scope` and `checkedAt` are carried into `GRAPH_VERIFICATION` in `lib/forecast/data.ts`. Each displayed finding gets `verification` (by `systemId`), or `null` if it was not checked.

| Status | Meaning |
|---|---|
| `supported` | The paper reports the same comparison with the same value. |
| `partly_supported` | The comparison is in the paper, but a label, subgroup or interval differs. |
| `contradicted` | The paper reports something materially different for that comparison. |
| `not_verifiable` | Could not be found in the abstract or open full text. This is not a judgement that the finding is wrong. |
| unchecked (`null`) | Not checked against the paper. |

The status counts change as the file is extended; `node scripts/forecast/check-data.mjs` prints the current counts over the displayed findings.

## Checks
```sh
node scripts/forecast/check-data.mjs
```
Asserts the counting invariants, ISO3 format, ascending unique years, and that every finding has a `systemId`, a `pubmedId` or `doi`, and at least one country; prints the spot checks.
