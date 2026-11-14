# A new Underlay collection of NYC restaurant inspections (built, not published)

The collection `nyc-restaurant-inspections-2026-11` is built and validated locally. It has not been published. Publishing needs an Underlay organization to own the collection, and the account behind `~/.config/underlay/token` has none (see "Blocker" below).

## What is ready

`analyses/underlay_publish/build.py`, committed at `7b50945f05a82177e14e3331f07d1dfa2ef94753`, fetched the live DOHMH Restaurant Inspection Results (NYC Open Data `43nn-pn8j`, all five boroughs) through `concord/socrata.py`. The table's `rowsUpdatedAt` was 2026-11-12T23:06:40Z before and after the fetch, and the last page was fetched at 2026-11-13T14:51:05-0500. The query was `$select=` (26 city columns), `$order=:id`, paged by `$offset` in steps of 50,000. The fetch returned 294,845 rows.

| Type | Records | Checked against |
|---|---|---|
| Restaurant | 31,482 | SoQL `count(distinct camis)` = 31,482 |
| Inspection | 92,745 | SoQL distinct (CAMIS, date, type) after 1901 = 92,745 |
| Violation | 287,728 | SoQL rows citing a code on a dated inspection = 287,728 |
| RemovedRestaurant | 2,388 | see below |

All 414,343 records pass their JSON Schemas (draft-07, `additionalProperties: false`), with no duplicate ids. Every Inspection points to a Restaurant, and every Violation points to an Inspection. Restaurant, Inspection and Violation keep the ids and field names of `nyc/restaurant-inspections` v1.0.0. Restaurant also keeps NTA, community board, BBL and BIN, and has an `inspected` flag. A violation code cited twice in one inspection keeps both records, with ids `…-CODE` and `…-CODE-2`; there are 225 such second or later citations. Of the snapshot's records, 23,180 Inspection and 72,228 Violation records are byte-identical in the new build and therefore have the same hash.

The RemovedRestaurant count differs from the brief. Of the 543 Manhattan restaurants that `docs/underlay_drift.md` found missing from the live Manhattan rows, 24 are still in the live table under another borough. Eighteen are in Brooklyn, for example DOKEBI GRILL at 199 Grand Street, which the city now lists in 11211. So 519 snapshot restaurants are absent from the whole table. The build adds restaurants that the Internet Archive copy of the full table (captured 2026-04-03 01:00:27 UTC) lists and the live table does not: 2,388 in all. These include all 519 from the snapshot, and 327 of them were never inspected. Each record names the copies that show it and gives the evidence in one sentence. Snapshot-derived records carry the version hash `ulv2:07a7f08a…` and the snapshot's Restaurant record hash.

The files are:

- `~/opt/nyc-concordance/underlay_publish/`: `records.ndjson` (161 MB, SHA-256 `58f84528…01437`), `record_hashes.tsv`, `schemas.json`, `readme.md`, `collection.json`, `source.json` and the raw rows `live_43nn-pn8j_all.csv.gz`.
- `data/derived/underlay_publish/`: `manifest.json` (counts, checks, source record, schema hashes and sample record hashes), `schemas.json`, `readme.md` and `removed_restaurants.csv`.

The readme states the source, `rowsUpdatedAt`, query, fetch time, build commit, relation to v1.0.0, the three findings from the drift audit and the licence position. The city attaches no licence to the dataset and states no restriction on use. The readme names the City of New York Terms of Use and the Open Data Law (Administrative Code Title 23, Chapter 5).

## How push.py will publish it

Run `python analyses/underlay_publish/push.py --owner <org slug> --yes`. Without both flags the script prints the plan and makes no request. It reads the key from `~/.config/underlay/token` and never prints it. It makes these calls in order:

1. `GET /api/collections/<owner>/nyc-restaurant-inspections-2026-11`, which must return 404.
2. `POST /api/accounts/<owner>/collections` with `{slug, name, description, public: true}`, which must return 201.
3. `POST /api/collections/<owner>/<slug>/push` with `{base: null, message, app_id, metadata (description, readme, license, tags, source, buildCommit), schemas}`. This returns the session id and limits.
4. `POST …/push/<sid>/records`, NDJSON in batches within `limits.batch_lines` (10,000) and 90 percent of `limits.batch_bytes`. That is about 42 batches.
5. `POST …/push/<sid>/commit` with `{"async": true}`. The script then polls `GET …/push/<sid>` until the status is `committed`, and writes `data/derived/underlay_publish/push_result.json`.
6. Read back without authentication: the collection and `…/versions/<hash>`, giving the version hash, ARK and `typeCounts` against the manifest counts. It then pages `…/manifest` to compare every record hash with `record_hashes.tsv`, and calls `/api/records/<hash>/first` for the ten sample hashes. The results go to `readback.json`.

Any non-success response stops the script and prints the status and body. Only the poll is retried. The collection is new, so this is version v1.0.0, and the build is fixed at commit `7b50945`.

## Blocker

Collections on the Underlay belong to organizations. `GET /api/accounts/me` with the key returns `"orgs": []` and no handle. `GET /api/collections?mine=true` returns no collections. According to the Underlay's llms.txt, an organization is created with `POST /api/auth/organization/create`, which needs a Knowledge Futures org id and answers 403 without one. The alternative is to email help@underlay.org. The account is also named "Jeff Nickerson", which should be confirmed as Jeff's. No organization was created and no write call was made.
