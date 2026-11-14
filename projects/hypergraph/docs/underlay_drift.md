# Drift between the Underlay snapshot and the live restaurant inspection table

This note compares two copies of the same city data. The first is the Underlay collection `nyc/restaurant-inspections`, version v1.0.0, hash `ulv2:07a7f08a0d5c85649920f8adc6946d27c17f5e2d75e9ee07c0ad4ae0fcc6739c`, pushed on 12 June 2026 at 06:06 UTC. The second is the live DOHMH table "New York City Restaurant Inspection Results" on NYC Open Data (43nn-pn8j), fetched on 13 November 2026 with `rowsUpdatedAt` 2026-11-12T23:06:40Z.

This is a descriptive audit. No hypothesis was registered. The results are in `data/derived/underlay_drift/summary.json`, `by_month.csv` and `example_zip_share_A.csv`. The figure is `figures/underlay_drift/underlay_drift.png`.


## Correction (13 November, evening)

The 543 restaurants counted here as gone compare Manhattan rows only. Against the whole live table, 519 are absent; the other 24 are still listed under another borough, 18 of them in Brooklyn (`docs/underlay_publish.md`). The 1,310 inspections and the other counts are for Manhattan rows and are unchanged.

## How the snapshot was built

The collection has one version. Its log entry gives the app id `nyc-restaurant-inspections/1.0` and the message "Push 112747 records". It holds 10,536 Restaurant, 25,341 Inspection and 76,870 Violation records, all public, with no files. All 112,747 record hashes were checked on download. Each hash is the SHA-256 of the line `{"id","type","data"}`, with the keys inside `data` sorted.

The readme names the source as "NYC Open Data — DOHMH New York City Restaurant Inspection Results". It gives no dataset id, no query and no fetch time. It says the collection is "Scoped to Manhattan restaurants inspected since January 2023" and was "Last imported: 2025-06". The records contradict both statements: inspection dates run from 2024-01-02 to 2026-06-09, so the data cannot date from June 2025 and do not start in 2023. The live table still holds 5,004 Manhattan inspections dated 2023, and none of them are in the snapshot. The data were therefore fetched between 9 June 2026 (the last inspection date) and 12 June 2026 (the push), and filtered to inspections dated 2024 or later. The importer's code is not public; the Underlay repository on GitHub holds no importer for this collection. The source query can only be inferred: Manhattan rows with a real inspection date from 1 January 2024 onward. Restaurants that the city lists with the placeholder date 1900-01-01 (not yet inspected) were left out.

The records are keyed as follows, which was checked against the ids.

| Type | Id | Fields kept |
|---|---|---|
| Restaurant | CAMIS | name, building, street, zipcode, phone, cuisine, latitude, longitude, boro |
| Inspection | CAMIS, inspection date and inspection type in slug form, e.g. `30191841-2024-11-20-cycle-inspection-initial-inspection` | action, score, grade, grade date, inspection type, date |
| Violation | inspection id plus violation code | code, description, critical flag |

The violation key collapses repeated codes. In the live table 58 inspections cite the same code twice; the snapshot keeps one record for each. The snapshot drops the city's NTA, community board, BBL and BIN columns. A blank grade is stored as an empty string, and a blank score is left out of the record.

## Matching

Inspections were matched on CAMIS, inspection date and inspection type, violations on the inspection key plus violation code, and restaurants on CAMIS. The comparison covers inspections dated 1 January 2024 to 11 June 2026, the day before the push.

| Inspections dated 2024-01-01 to 2026-06-11 | Count |
|---|---|
| In the snapshot | 25,341 |
| In the live table | 24,217 |
| In both | 24,030 |
| In both, with at least one field different | 903 |
| Only in the snapshot | 1,311 |
| Only in the live table | 187 |

Of the 1,311 inspections found only in the snapshot, 1,310 belong to restaurants that are no longer in the live table at all. One belongs to a restaurant that is still listed. No snapshot-only inspection reappears in the live table under a different inspection type with the same CAMIS and date.

Of the 187 inspections found only in the live table, 94 belong to 41 restaurants that are not in the snapshot, and 93 belong to restaurants that are. Of the 187, 109 are dated 1 to 11 June 2026. These 109 took place before the push but were not in the snapshot, so most were probably entered in the city table after the snapshot's data were fetched. The other 78 are spread across earlier months at 0 to 8 a month, and were added to the table late.

| Violations on inspections dated 2024-01-01 to 2026-06-11 | Count |
|---|---|
| In the snapshot | 76,870 |
| In the live table | 72,747 |
| In both | 72,122 |
| Only in the snapshot | 4,748 (509 on inspections present in both) |
| Only in the live table | 625 (8 on inspections present in both) |

## Kinds of change in the 903 matched inspections

The changes run in one direction. They are consistent with the city's adjudication process. A restaurant contests violations at a hearing. Dismissed violations are removed, the score falls, and a "grade pending" result becomes a final grade. The table's own description says it holds every violation that is "sustained or not yet adjudicated". The audit observes the changes but cannot see the hearings themselves.

- Scores changed in 485 inspections. All 485 fell; none rose and none went blank. The median change was −8 points. In 282 of them the violation codes also changed.
- Grades changed in 568 inspections. The largest group is 339 inspections graded N (Not Yet Graded) in the snapshot and blank in the live table. The next groups are grade-pending results that were resolved to a final grade: Z to B (108), Z to C (45), Z to A (35) and Z to P (14). Fifteen went the other way, from B or C to Z, and 6 from C to B.
- Violation codes changed in 303 inspections. In 302 of them codes were only removed; in 1, codes were only added. In total 509 codes were removed and 8 added. The most often removed were 10F and 06C (58 each), 08A (36), 10B (32) and 02B (28).
- The action changed in 16 inspections, in every case from "Violations were cited" to "No violations were recorded", which is what happens when every cited violation is dismissed.
- A grade date was filled in for 2 inspections where the snapshot had none.

## Change by inspection month

The two kinds of drift fall on different months (figure, left panel). For inspections from 2024, 5.3 to 8.4 percent of each month's snapshot inspections are gone from the live table, and almost none are changed. These losses come from restaurants that left the table. For inspections from February to May 2026, 1 to 2 percent are gone and 8 to 12 percent are changed. Recent inspections are still being adjudicated, so the share revised after the push is highest for the months just before the push. A further rise in early 2025 (11 to 13 percent changed or gone) combines both causes.

## Restaurants

Of the 10,536 restaurants in the snapshot, 543 are no longer in the live table. Their last inspection in the snapshot was in 2024 for 137, in 2025 for 338 and in 2026 for 68. The live table does not say why a restaurant leaves. Its description says it holds only restaurants in active status on the date of the data pull, and only inspections up to three years before a restaurant's latest one. These 543 are probably restaurants that closed or lost their permit, and the audit cannot separate the two. Only 18 of the restaurants still listed have a DOHMH closure as their latest live inspection, and 15 of those were already closed in the snapshot.

Of the 9,993 restaurants still listed, 442 have a different name, 620 a different building or street (after collapsing repeated spaces), 385 a different phone number, 227 a different cuisine and 13 a different ZIP code. Most name changes are new businesses under an old CAMIS (PERIYALI to OPTO) or small edits (H & H to H&H). The live table also lists 1,803 Manhattan restaurants with only the placeholder date 1900-01-01.

## What the drift means for analyses that cite the live table by update time

The city replaces the whole table each day: every live row has `record_date` 2026-11-12. `rowsUpdatedAt` therefore records when the table was last rewritten, not which rows changed. An analysis that cites "43nn-pn8j, rows updated at T" cannot be rerun after T, because the table at T no longer exists anywhere the city publishes. The project's `concord/socrata.py` keeps a cached copy of each result in `data/cache/socrata/`, which is git-ignored and so is not available to a reader of the repository.

The drift also changes results, and the changes are systematic. Revisions lower scores and replace pending grades with final grades, and removals drop the inspections of restaurants that closed. A figure on recent inspections computed today differs from the same figure computed in June, and the direction of the difference depends on the measure.

As an example, take the share of letter grades that are A among A, B and C grades on inspections dated 1 January 2025 to 31 May 2026. In ZIP code 10018 (the Garment District) the snapshot gives 300 of 333, or 90.1 percent. The live table as of 12 November 2026 gives 297 of 339, or 87.6 percent, a difference of −2.5 percentage points. Across the 28 Manhattan ZIP codes with at least 100 graded inspections in both copies, the difference ranges from −3.0 points (10027) to +1.0 point (10002), with a median of −0.9 points (figure, right panel). For Manhattan as a whole the share is 89.3 percent (n = 8,340) in the snapshot and 88.3 percent (n = 8,194) live. Most of the fall comes from Z grades resolved to B or C, which enter the denominator only after the change. A ranking of ZIP codes by this measure also changes: 10018 is ninth of 28 in the snapshot and seventeenth live, and 10027 moves from tenth to nineteenth. The Spearman correlation between the two rankings is 0.90.

A version hash fixes the data a figure rests on, and anyone can retrieve the same records by that hash. The snapshot does not include later corrections. For inspection results, a snapshot taken soon after the inspections holds results that were later revised, so a citation should give both the version and the inspection dates it covers.

## The same comparison over eleven years (added 14 November)

This section is exploratory and nothing in it was registered. `analyses/underlay_drift/history.py` compares each of ten Internet Archive copies of the full table (2015 to April 2026, all boroughs) with the next one, and the last with the live table of 12 November 2026. Inspections are matched on restaurant, date and inspection type.

| Earlier copy | Later copy | Inspections in both | Scores that fell | Scores that rose | Restaurants gone |
|---|---|---|---|---|---|
| 2015-09 | 2016-12 | 90,161 | 7,715 | 23 | 4,164 |
| 2016-12 | 2017-04 | 125,726 | 1,171 | 9 | 1,182 |
| 2017-04 | 2020-11 | 13,874 | 769 | 3 | 8,464 |
| 2020-11 | 2021-05 | 129,447 | 643 | 31 | 521 |
| 2021-05 | 2022-11 | 34,099 | 53 | 225 | 6,621 |
| 2022-11 | 2023-11 | 36,841 | 1,597 | 4 | 2,397 |
| 2023-11 | 2024-12 | 47,369 | 612 | 2 | 3,203 |
| 2024-12 | 2025-11 | 59,361 | 842 | 1 | 2,695 |
| 2025-11 | 2026-04 | 73,235 | 803 | 0 | 1,050 |
| 2026-04 | 2026-11 | 64,756 | 1,473 | 0 | 2,061 |

Across the ten comparisons 15,678 scores fell and 298 rose. Nine of the ten show almost no rises. The exception is 2021 to 2022, which follows the suspension of inspections in 2020 and 2021 and has almost no recent inspections in both copies; it was not investigated.

The copies record the violation codes, so the removed violations are known. Between April and November 2026, for inspections dated in the year before April, 82,066 violations were cited, 1,202 were later removed and 2 added. The codes removed most often, as a share of citations, are 03A (food from an unapproved source, 5.6%), 05C (4.9%) and 09B (improper thawing, 4.4%). The codes removed least often are evidence of pests: mice (04L), roaches (04M, 0.3%) and flies (04N, 0.2%). The same ordering appears in the two earlier comparisons.

Among inspections that scored 14 or more, 13.3% had the score reduced later (8.4% and 7.2% in the two earlier comparisons). Re-inspections are reduced more often than initial inspections in all three (17.5% against 12.2% in the latest). Differences by borough are modest: Queens and Manhattan are highest and the Bronx is lowest or second lowest in all three. By cuisine the order changes from one comparison to the next, except that Chinese restaurants are at or near the bottom in all three (9.8%, 5.7%, 6.6%). That pattern has not been tested and has many possible causes, including the mix of violations cited and whether a restaurant contests them. The outputs are in `data/derived/underlay_drift/history.json`.

## Files

- `analyses/underlay_drift/fetch_underlay.py` downloads v1.0.0 with its metadata and checks every record hash. The records (51 MB) are in `~/opt/nyc-concordance/underlay/`.
- `analyses/underlay_drift/fetch_live.py` pulls the live Manhattan rows through `concord/socrata.py` and writes the source record `data/derived/underlay_drift/live_source.json`.
- `analyses/underlay_drift/compare.py` does the matching and writes the derived tables.
- `analyses/underlay_drift/figure.py` draws the figure with an embedded sRGB profile.
