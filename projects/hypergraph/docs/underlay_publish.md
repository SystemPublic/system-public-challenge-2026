# Two Underlay collections published under `system-community`

Two public collections were published on 13 November 2026 (local time; 14 November UTC) to the Underlay at `https://www.underlay.org`, under the organization `system-community` (System Inc. Community). Travis Rich of Knowledge Futures invited the account to that organization for the System Public Challenge. The page `https://demo-system-hackathon.kfutures.org` is an information page for the event and uses the same host; it is not a separate Underlay instance.

| | Restaurant inspections | Claims |
|---|---|---|
| Collection | `system-community/nyc-restaurant-inspections-2026-11` | `system-community/nyc-concordance-claims` |
| Page | https://www.underlay.org/system-community/nyc-restaurant-inspections-2026-11 | https://www.underlay.org/system-community/nyc-concordance-claims |
| API | https://www.underlay.org/api/collections/system-community/nyc-restaurant-inspections-2026-11 | https://www.underlay.org/api/collections/system-community/nyc-concordance-claims |
| Version | v1.0.0 | v1.0.0 |
| Version hash | `ulv3:75f19225fc60e9d18c7ece50c4f3b02dc61077c580ae083f9776d0209075f42b` | `ulv3:39269fcb2e3c3ab88a3d15cf7a2c45492165a4b3091d4fd57c47adfc3ec41143` |
| Version ARK | https://underlay.org/ark:12345/ulcb4v9t8nfrhs62.v1.0.0 | https://underlay.org/ark:12345/ulcb4ksbc7h2v96n.v1.0.0 |
| Collection ARK | https://underlay.org/ark:12345/ulcb4v9t8nfrhs62 | https://underlay.org/ark:12345/ulcb4ksbc7h2v96n |
| Created (UTC) | 2026-11-14T04:42:04Z | 2026-11-14T04:46:18Z |
| Records | 414,343 | 275 |
| Counts by type | Restaurant 31,482; Inspection 92,745; Violation 287,728; RemovedRestaurant 2,388 | Claim 94; Outcome 93; Revision 88 |
| Visibility | public | public |
| Build commit | records `7b50945`; readme and push at `d3f39e5` | `7a86412` |

The ARKs carry the name-assigner number 12345 because the organization has not set its own; the Underlay issued them in that form.

## Read-back

Each version was read back without authentication after its push (`readback.json` beside each `push_result.json`). For both collections the version hash equals the hash the commit returned, the collection is public, and `typeCounts` equals the local counts. Every record hash in the version's manifest equals the local hash: 414,343 of 414,343 and 275 of 275. Ten sample restaurant records and nine sample claim records were fetched through `.../versions/<hash>/records/<type>/<id>`, and each had the expected hash and the same data as the local file. The published readme of each version names the organization and the pull request.

The lookup `GET /api/records/<hash>/first`, which the plan named, answers 404. The Underlay's llms.txt lists lookups by record hash as not available yet, so `push.py` resolves records through the collection.

The first read-back of the restaurant collection reported 438 hash mismatches. They were in the local table, not on the server. `build.py` wrote the float 0.0 as `0.0` where the Underlay's rule (RFC 8785) writes `0`, which affected 438 Restaurant records with latitude 0.0. `build.py` now uses the same function as `tools/underlay_export.py`, `record_hashes.tsv` was recomputed from the unchanged `records.ndjson`, and the second read-back found no mismatch.

## The claims collection

`tools/underlay_export.py` builds it from the register and writes `data/derived/underlay_publish/claims/` (`records.ndjson`, `record_hashes.tsv`, `schemas.json`, `readme.md`, `collection.json`, `manifest.json`). The tool stopped with a TypeError on the current register because some registrations give a list of relationship ids; that is fixed, and the older five-type export is kept under `--graph-audit`.

| Type | Records | Content |
|---|---|---|
| Claim | 94 | the registration as parsed and as exact file text, its sha256 (recomputed for all 94), the commit that added it, the `prereg/<id>` branch and its commit (64 claims have one), the lineage-audit class, and the replication package with its status (12 claims, all MATCH) |
| Outcome | 93 | verdict, `city_effect`, `graph_effect`, stance, sources with dataset versions, `notes_referee`, the referee report's path and sha256 (87), the placebo estimate (14) and the referee's value (22) from `viz/data/annotations.json` |
| Revision | 88 | each `history` entry: the outcome before the revision, the reason, the critique path and whether the verdict changed (12 did) |

An outcome file keeps the reason of its latest revision only. For the seven earlier revisions of the six outcomes revised more than once, the reason was read from the git history of the outcome file, and the record names the commit. Every record passes its JSON Schema (draft-07, no undeclared top-level fields), ids are unique, every Outcome and Revision points to a Claim, and each Outcome's `registration_sha256` equals its Claim's. The lineage classes are 2 d, 1 e, 10 c, 20 a, 10 b, 3 f and 48 with no early fetch. The readme explains registration before data, the verdict rules (`PRECEDENCE` in `concord/claims.py` at commit `3b42e04`), the lineage audit with the two class d claims (afford-gentrification-prevalence and heat-extremes-downturn), and where the code is: pull request https://github.com/SystemPublic/system-public-challenge-2026/pull/3 under `projects/hypergraph/`, with the working repository private for now.

## The restaurant collection

The readme pushed with the version names `system-community` as owner, names the collection Knowledge Futures seeded for the event (`nyc/restaurant-inspections` v1.0.0: Manhattan restaurants inspected since January 2024; 10,536 restaurants, 25,341 inspections and 76,870 violations) and says how this one differs, and names the pull request. The records are those built on 13 November and described below.

### The build

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

## How push.py publishes

Run `python analyses/underlay_publish/push.py --owner <org slug> --yes`, adding `--collection claims` for the claims collection and `--verify-only` to repeat the read-back. Without both flags the script prints the plan and makes no request. It reads the key from `~/.config/underlay/token` and never prints it. It makes these calls in order:

1. `GET /api/collections/<owner>/nyc-restaurant-inspections-2026-11`, which must return 404.
2. `POST /api/accounts/<owner>/collections` with `{slug, name, description, public: true}`, which must return 201.
3. `POST /api/collections/<owner>/<slug>/push` with `{base: null, message, app_id, metadata (description, readme, license, tags, source, buildCommit), schemas}`. This returns the session id and limits.
4. `POST …/push/<sid>/records`, NDJSON in batches within `limits.batch_lines` (10,000) and 90 percent of `limits.batch_bytes`. That is about 42 batches.
5. `POST …/push/<sid>/commit` with `{"async": true}`. The script then polls `GET …/push/<sid>` until the status is `committed`, and writes `data/derived/underlay_publish/push_result.json`.
6. Read back without authentication: the collection and `…/versions/<hash>`, giving the version hash, ARK and `typeCounts` against the manifest counts. It then pages `…/manifest` to compare every record hash with `record_hashes.tsv`, and fetches each sample record through the version. The results go to `readback.json`.

Any non-success response stops the script and prints the status and body. Only the poll is retried. Each collection was new, so each version is v1.0.0. Collections are created public, because only the organization's administrators can change visibility later; the key acts as a plain member.

## Earlier blocker (resolved)

Until the evening of 13 November the account belonged to no organization, and `GET /api/accounts/me` returned `"orgs": []`. Later that evening `GET /api/accounts/me` listed `system-community` with the role member, and the key in `~/.config/underlay/token` then created both collections. No other write was made on the Underlay.
