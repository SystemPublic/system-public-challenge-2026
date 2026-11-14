# Replication package: rlc-expansion-rearend

This folder lets a reader check one claim from the NYC concordance project without the repository. The claim is: At the intersections where New York City switched on red-light cameras in January-August 2026, rear-end crashes rose relative to matched signalized intersections, as the meta-analyses predict and contrary to NYC DOT's report of fewer rear-end injury crashes at its camera sites.

It was registered at 2026-11-13T12:39:17-0500 with sha256 `a0d11a850d2da5029a3ae583a3ce37a4ff36a4b4846df639fa569276879ace9e`, in commit `3e747066e417`. The branch `prereg/rlc-expansion-rearend` on the project's GitHub remote points at `3e747066e417`. The outcome is `unsettled`, decided at 2026-11-13T13:11:25-0500.

## The deciding number

The deciding number is the city_effect: ratio of ratios for rear-end proxy crashes within 50 m, 283 camera intersections against matched controls, cluster bootstrap 95% interval (B=2000, seed 20261113). The recorded value is estimate = 1.3266, lo = 1.061, hi = 1.6499, n = 283, placebo_estimate = 1.2496, placebo_lo = 1.0519, placebo_hi = 1.488. The registered condition that decides the verdict is "support_if: 95% interval above 1.00 and rule 8 D >= 4 against 1.33". `verify.py` accepts a rerun when each value lies within its tolerance: estimate within 0.0001, lo within 0.0001, hi within 0.0001, n within 0, placebo_estimate within 0.0001, placebo_lo within 0.0001, placebo_hi within 0.0001.

Smallest wrapper: rlc_did.py needs 120.7 MB of crash pages and writes into the repository. code/prepare.py keeps the crashes within 50.5 m of a camera or control intersection, the only ones build() counts, and code/rerun.py calls load_sites(), control_pool(), crash_arrays(), build(), placebo(), rr_from() and boot() unchanged (B=2000, seed 20261113) for the rear-end outcome. rlc_did.py rounds the ratio and the interval to four decimals, as the outcome records them. The placebo is the registered one (the same sites and windows one year earlier, before any camera).

The rerun also recomputes the claim's placebo, and `verify.py` compares it with the recorded value in the same way: placebo_estimate = 1.2496 (within 0.0001), registered placebo: the same sites and windows one year earlier, before any camera, recorded in outcome notes and data/derived/street_safety/rlc_did_results.json (placebo_one_year_earlier.rear_end.rr); placebo_lo = 1.0519 (within 0.0001), its lower 95% limit, recorded in rlc_did_results.json placebo_one_year_earlier.rear_end.lo; placebo_hi = 1.488 (within 0.0001), its upper 95% limit, recorded in rlc_did_results.json placebo_one_year_earlier.rear_end.hi.

## How to run it

Install Python 3.12.10, the version the package was recorded under, and the pinned packages, then run the check. With uv, which can install that Python itself:

```
uv venv --python 3.12.10 .venv
uv pip install --python .venv/bin/python -r requirements.txt
PYTHON=.venv/bin/python ./run.sh
```

Without uv, use a Python 3.12.10 interpreter from python.org or a package manager: `python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt`. Do not rely on whichever `python3` is first on the PATH; on some machines it is an Anaconda build of another version.

The packages were recorded under Python 3.12.10 on Darwin 27.2.0 (arm64). The full `uv pip freeze` of the project's environment is in `manifest.json` under `environment`. The check prints MATCH when every copied input has its recorded sha256 and the rerun reproduces the deciding number within tolerance, DRIFT when an input differs from its pin, and MISMATCH when the inputs are intact but the number differs, which points to a change in code or environment. `./run.sh --refetch` also re-runs each pinned query and reports whether the live sources still match their pins. No key is needed for these. With `--refetch` the deciding number is not recomputed from live data, because the derived tables it reads come from upstream stages that are not packaged; DRIFT then says only that a pinned source has changed. A run writes `verify_result.json`, and `--refetch` writes `refetched/`, inside the package; the rerun may also write `work/` and `code/data/`. These are listed in `.gitignore`.

## What is pinned

The folder `inputs/` holds 3 files (3.9 MB), each with its sha256 in `manifest.json`. They keep the paths they have in the repository. 
For each NYC Open Data source the manifest gives the dataset id, its `rowsUpdatedAt` at fetch time, the exact SoQL query, the fetch time and the sha256 of the cached response (and of its rows alone, which is what `--refetch` compares). The city rewrites these tables in place (see the project's audit `docs/underlay_drift.md`), so the cached response is the only copy of the data as they were used. 
Some inputs are cut from files too large to carry: `prepared/street_safety/crashes_near_sites.json.gzip` (2.6 MB), the crash records (h9gi-nx95, with the rear-end flag from bm4k-52h4) within 50.5 m of a camera intersection or a control-pool intersection, as returned by rlc_did.fetch_crashes(), gzipped. `code/prepare.py` is the code that cut them; the files it reads are listed with their sha256 under `inputs.files[].prepared_from` in the manifest: `data/cache/socrata/h9gi-nx95-d84a3a3634c73147b31621a7.json` (18.6 MB, sha256 `fa64e70b35c4b7a8...`); `data/cache/socrata/h9gi-nx95-6689db4216bb39668a0d5e23.json` (18.6 MB, sha256 `fe9b3db8dbaf1427...`); `data/cache/socrata/h9gi-nx95-8f57948c311e587e8fc34b1c.json` (18.6 MB, sha256 `169f8f9e2fbb53d7...`); `data/cache/socrata/h9gi-nx95-969416e69c86c5044fc85a1b.json` (18.6 MB, sha256 `dc5166671c97befa...`); `data/cache/socrata/h9gi-nx95-a1ada602969f6cf789d991b2.json` (18.7 MB, sha256 `3f51c29ff5060b03...`); `data/cache/socrata/h9gi-nx95-60cab1a79bd7b49bf9f7b688.json` (18.6 MB, sha256 `6c3f21f7d7323997...`); `data/cache/socrata/h9gi-nx95-64e49fa4d92902d1aaf51cee.json` (8.8 MB, sha256 `fba41f098c5a2e7d...`); `data/cache/socrata/bm4k-52h4-d9aed0d6a7c5d127ad60851a.json` (2.2 MB, sha256 `33ab4b469070f024...`); `data/derived/street_safety/rlc_sites_geo.json` (0.3 MB, sha256 `c5dfe14c6f0cd631...`); `data/derived/street_safety/lpi_gazetteer.json` (1.1 MB, sha256 `4ab2c425ded4cd77...`). 
The analysis code the rerun imports is copied into `code/`, with the git blob hash and last commit of each file in the manifest. The repository commit at packaging time was `f9660de2d17f`. Seeds and draw counts above are quoted from the registration text.

## What is only pointed to

- `data/cache/socrata/h9gi-nx95-d84a3a3634c73147b31621a7.json` (18.6 MB, sha256 `fa64e70b35c4b7a8...`): cached Socrata response, h9gi-nx95; not read by the rerun; pointed to by hash.
- `data/cache/socrata/h9gi-nx95-6689db4216bb39668a0d5e23.json` (18.6 MB, sha256 `fe9b3db8dbaf1427...`): cached Socrata response, h9gi-nx95; not read by the rerun; pointed to by hash.
- `data/cache/socrata/h9gi-nx95-8f57948c311e587e8fc34b1c.json` (18.6 MB, sha256 `169f8f9e2fbb53d7...`): cached Socrata response, h9gi-nx95; not read by the rerun; pointed to by hash.
- `data/cache/socrata/h9gi-nx95-969416e69c86c5044fc85a1b.json` (18.6 MB, sha256 `dc5166671c97befa...`): cached Socrata response, h9gi-nx95; not read by the rerun; pointed to by hash.
- `data/cache/socrata/h9gi-nx95-a1ada602969f6cf789d991b2.json` (18.7 MB, sha256 `3f51c29ff5060b03...`): cached Socrata response, h9gi-nx95; not read by the rerun; pointed to by hash.
- `data/cache/socrata/h9gi-nx95-60cab1a79bd7b49bf9f7b688.json` (18.6 MB, sha256 `6c3f21f7d7323997...`): cached Socrata response, h9gi-nx95; not read by the rerun; pointed to by hash.
- `data/cache/socrata/h9gi-nx95-64e49fa4d92902d1aaf51cee.json` (8.8 MB, sha256 `fba41f098c5a2e7d...`): cached Socrata response, h9gi-nx95; not read by the rerun; pointed to by hash.
- `data/cache/socrata/bm4k-52h4-d9aed0d6a7c5d127ad60851a.json` (2.2 MB, sha256 `33ab4b469070f024...`): cached Socrata response, bm4k-52h4; not read by the rerun; pointed to by hash.
- `data/derived/street_safety/graph_check.json` (0.0 MB, sha256 `2e05fdbe0e1bb707...`): graph evidence (file); not read by the rerun; pointed to by hash.
- Parking Violations Issued FY2024-FY2027, violation code 7: recorded in the outcome as a nyc-open-data source; no file is pinned.
- NYC Open Data `xc4v-ntf4` (VZV Leading Pedestrian Interval Signals (control pool)): no cached response was found, so only the query and `rowsUpdatedAt` are recorded.
- NYC Open Data `shr7-eqdc` (VZV Street Improvement Projects (SIP) Intersections): no cached response was found, so only the query and `rowsUpdatedAt` are recorded.
- OpenStreetMap intersections via Overpass API, OSM base 2026-07-24: recorded in the outcome as a other source; no file is pinned.

## Tables this package cannot rebuild

None. The rerun starts from the copied source responses and computes every intermediate table itself.

## What a stranger needs

A stranger needs Python 3.12.10 with the packages in `requirements.txt` and this folder. The check reads only files inside the folder and makes no network request unless `--refetch` is given. Re-fetching the pinned sources needs network access but no key. Anything that touches the System graph beyond the copied responses needs the reader's own System API key, supplied by the reader; no key is included. The registration, outcome, revision history and referee report paths are in `manifest.json` under `claim`; the referee reports themselves are in the project repository.
