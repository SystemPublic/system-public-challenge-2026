# Referee report: levers-vacant-lot-trial-match

Verdict recorded: confirmed (1,116 of 2,678 lots, share 0.417). Recommendation: keep "confirmed" under rule 1, because the registered screen passes under every variant I ran. The outcome, `docs/levers.md` and `viz/levers.html` should stop saying that the screened lots resemble the trial's lots. In a random sample of 40 screened lots that I checked against NAIP, 28 (70%, Wilson 95% interval 55% to 82%) are not vacant blighted land. On that evidence the number of lots like the trial's is nearer 330 than 1,100.

I rebuilt the count with my own code before reading `docs/levers.md` or the page. My scripts are in the scratchpad and are not committed. They query Socrata and the DCP MapPLUTO feature service directly, build BBLs from borough, block and lot, and read NAIP 2022 from the Planetary Computer with my own masks.

## (a) Order of registration and data, and rule 9

The registration was committed at 13:31:12 on 13 November in 2a7c4b4, and that commit is also the remote branch `prereg/levers-vacant-lot-trial-match`. The first lot-level fetch recorded in the outcome is PLUTO at 13:31:44. The DOB, GreenThumb, stalled-site and shooting fetches came between 13:38 and 13:48. The registration therefore precedes the deciding data. One part of the prediction was knowable beforehand. The `vac_lots` column of `data/derived/neighbourhood/vacant_shootings_tracts.csv`, committed on 12 November, sums to exactly 2,678 over the tracts with 10 or more shootings. That number is not in `support_if`, so this does not matter for the verdict.

Rule 9 was committed at 01:12 on 13 November (d11132b), twelve hours before this registration, so its last sentence binds this claim. The registration commit holds `register_lots.py` and `pubmed.py` only. `lots_fetch.py`, `lot_polygons.py`, `lot_ndvi.py` and `lot_test.py` were first committed with the outcome in f09bc0c, and the registration names no analysis commit. The claim therefore does not meet rule 9. The plan text fixes the 510 m² limit, the NDVI cut of 0.2, the vegetated-share cut of 0.2, the type order and the definition of trial-like (types 5 and 6, small, vegetated share at least 0.2), and the outcome applies them as written. The plan left four choices open: the tie at the top-decile cut, polygons or centroid disks, how BBLs are joined, and how the stalled list is read. Under rule 9 the verdict must not turn on these. It does not, as the next section shows.

## (b) Independent rebuild

| Quantity | Registrant | Referee |
|---|---|---|
| Land use 11 lots, PLUTO 26v2 | 24,663 | 24,663 |
| Lots in tracts with ≥ 10 shootings 2019-2024 (235 tracts) | 2,678 | 2,678 |
| Private idle / city interim / stalled / active | 1,471 / 668 / 281 / 258 | 1,433 / 656 / 285 / 304 |
| Small (≤ 510 m²) private idle or city interim | 1,705 | 1,666 |
| Trial-like (registered rule) | 1,116 | 1,087 |
| Share | 0.417 | 0.406 |
| Shootings a year within 300 m (union), 2023-2025 | 388.0 | 387.3 |
| Prevented by greening, −6.8% (−2.7 to −10.6) | 26.4 (10.5-41.1) | 26.3 (10.5-41.1) |

The types differ on 69 lots. In 42 of them I find a recent permit or filing that the registrant's code missed: 29 have a DOB NOW new-building filing and others have foundation, earthwork or excavation permits dated after 13 November 2024. I build BBLs from borough, block and lot, but `lots_fetch.py` joins on each dataset's `bbl` column, which is missing or different on some recent rows. I also count General Construction permits on new-building jobs, which the plan calls "a DOB permit of job type NB". DOB NOW has no work type "New Building", so the registrant's permit filter found none.

These are the variants for the choices the plan left open. The share stays inside 0.18 to 0.45 in every one.

- Strict top decile (more than 10 shootings, 193 tracts, 2,229 lots): 912 lots, share 0.409.
- Lot polygon eroded inward by 1 m, against centroid and edge error: 962 lots, share 0.359.
- Pixel NDVI cut of 0.3 instead of 0.2: 829 lots, share 0.310.
- Without the imagery filter: 1,666 lots, share 0.622, which is above the range. The imagery filter therefore decides the verdict.

My NDVI agrees with the registrant's. The correlation of vegetated share over 2,109 lots is 0.991, and the two classifications agree at the 0.2 cut on 99.5% of lots.

### Errors in the data handling that change no verdict

1. The shootings coordinates are swapped, as the registrant says. In all 7,731 rows for 2019-2025 the `latitude` column holds values near −74. After the swap, every point lies within 0.93 m of the point given by the state-plane columns `x_coord_cd` and `y_coord_cd`. The swap is uniform, so the fix in `lot_test.py` is correct.
2. The BIS filter `work_type in ('FO','EW')` matches no rows. In ipu4-2q9a, FO and EW are permit types, and EW means equipment work, not earthwork. Foundation permits are on new-building jobs, so the `job_type` clause catches them anyway.
3. The stalled-sites view i296-73x5 has 1,460,450 rows and 866 distinct BINs. One 50,000-row page holds about 450 to 650 of those BINs; I counted this in the registrant's cached pages. Grouping by BIN returns all 866. The full list matches 86 land use 11 lots, of which 13 are in the top tracts.
4. The outcome says that "BIS permits for new buildings end in May 2020", and this is wrong. BIS issued 2,113 permits on new-building jobs in 2025 and 1,245 in 2026. The BIS new-building job filings (ic3t-wcy2) end in November 2023.
5. 28 of the 2,678 lots have no polygon in the MapPLUTO feature service. 15 of them are small private-idle or city-interim lots, which the rule cannot classify.

## (c) Does the registered rule pick lots like the trial's?

Moyer et al. (2019) and Branas et al. (2018) drew lots from Philadelphia's vacant-lot inventory. They admitted only lots that a field visit found blighted, with trash, dumping or overgrowth. They excluded lots larger than about 5,500 sq ft (510 m²) and paved parking lots. The treated lots were mostly street-facing gaps in rowhouse blocks. Moyer's full text is not in the open PMC XML, so for the exact exclusion list I rely on the registrant's reading. The PNAS methods defer to its supplement.

The registered rule copies the size limit and the paving exclusion. Records stand in for "not under development". The rule does not copy the blight condition, and NDVI cannot measure it. A vegetated share of at least 20% admits mown lawns, rear gardens, tree-covered rear yards and woodland, all of which score higher than a trash-strewn dirt lot. The rule also has no test for street frontage, for slivers, or for a lot that is part of a neighbour's yard. GreenThumb gardens are not the problem. I overlaid all 635 GreenThumb polygons on the lot polygons, and none covers more than half of any land use 11 lot in these tracts.

For the visual check I drew 60 lots at random (seed 20261113) from the small lots in the top tracts with a vegetated share of at least 0.2. I kept the first 40 that my rebuild calls trial-like. Each image is 60 m by 60 m of NAIP 2022 with the lot outlined, so the neighbouring buildings and the street are visible. I put each lot in one of three classes:

- Plausibly vacant blighted land (overgrown or bare gap lot, or open field): 6 lots.
- Uncertain (vacant grass or trees with no visible trash, or partly shaded): 6 lots.
- Not vacant blighted land: 28 lots. Ten are rear yards or side yards of houses, including a mown lawn and a pool. Six are mostly covered by roofs in 2022. Five are slivers or traffic triangles. Two are wooded natural areas and two are paved parking or driveways. One is landscaped building grounds, one is a courtyard and one is a working storage yard.

So 28 of 40 (0.70; 0.55 to 0.82) are not the kind of lot the trial treated. If every uncertain lot counts as blighted, the trial-like share of the 2,678 lots becomes about 0.12 (0.07 to 0.18), which is below the registered lower limit of 0.18. Under rule 4 this check was chosen after the data were seen and decides nothing. It does show that the confirmed quantity counts lots that pass a records-and-NDVI screen. It does not count lots like the trial's.

The outcome's own check ("4 of the 18 lots the rule calls trial-like") used chips padded by 3 m. At that size a yard cannot be told from a gap lot. It also counted only roofs and ball fields as failures. The 70% figure replaces it.

## (d) Prevented shootings

The arithmetic is correct. 388 × 0.068 = 26.4, and the interval is 10.5 to 41.1. The union of buffers does not double count. A shooting within 300 m of several lots is counted once. Summing over lots would give 1,573 shootings a year, 4.1 times the union, and 107 prevented. A median shooting near any screened lot lies within 300 m of 3 of them, and 31% lie within 300 m of 5 or more. The trial's clusters averaged about 5 lots (541 lots in 110 clusters), so applying one cluster-level percentage to the union is a fair reading of the trial.

Two problems remain. First, the figure assumes that every one of the lots is blighted. If 30% of them are, the union falls to about 239 shootings a year and greening prevents about 16. If 15% are, it prevents about 11. Second, the trial measured kernel density at the lot with a 500 m bandwidth, which weights near shootings more heavily. Applying the percentage to a flat 300 m count treats a shooting 290 m away the same as one beside the lot. The intervals shown are the trial's only. Neither the transfer doubt nor the uncertainty in the lot count is included.

## (e) docs/levers.md and viz/levers.html

The five components are kept apart, as the note says. Three of them are presented unfairly to the reader, and the prose claims more than the numbers support.

1. Reach. The table and the page give 24,663 vacant lots as the reach of greening, and the page sorts the reach column on that number. On the registrant's own test, at most 1,116 lots are eligible, and on the visual check about 330. Sorting reach across lots, buildings, vacate orders and hump locations compares counts in different units.
2. The note says that the vegetated-share filter "excludes paved, built-over and excavated lots". Nine of my 40 screened lots were mostly roofed in 2022 or were paved driveways or parking.
3. The headline "1,116 lots resemble the trial's lots" appears in the note, the page's fact panel and `trial_like_lots.csv`. The note then proposes the list, including the 304 city-owned lots, for a greening programme. The note does advise a street-level survey first. The list should be described as screened candidates, of which most are not blighted lots.
4. The fact panel gives "26.4 (10.5–41.1)" prevented shootings, to one decimal. The interval leaves out both the lot-count doubt and the transfer doubt. A rounded figure, about 10 to 25 a year under the visual check, with both doubts stated, would match the evidence.
5. The note says that housing repair "acts on the largest measured burden". That compares 68,746 asthma visits with 855 shootings by count alone, across outcomes that differ in severity. The comparison should be removed or qualified.
6. The note repeats the wrong statement about BIS new-building permits, item 4 in (b).

The rest of the ranking table (designs, intervals, breadth, cost sources) matches `levers.json`. I found no other misstatement.

## Recommendation

Keep "confirmed" under rule 1. The share is between 0.31 and 0.41 under every variant of the open choices, and the count is between 800 and 1,120. Add to the notes that rule 9 was not met, because the scripts were committed after the data, and that the verdict does not depend on the open choices. Add the referee's visual check (28 of 40 not vacant blighted land) as exploratory, and state that the confirmed quantity is the screen, not resemblance to the trial. Correct the BIS statement. Change "reach" and the headline figures in the note and the page as described in (e). A successor claim should register a two-coder visual or street-level coding of a random sample before the coding is done, with the trial's blight criteria written out.
