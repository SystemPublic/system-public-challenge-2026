# Replication package: ems-traffic-share-2019-2026

This folder lets a reader check one claim from the NYC concordance project without the repository. The claim is: Slower traffic accounts for less than half of the rise in Manhattan life-threatening ambulance travel time from January-September 2019 to January-September 2026, even if ambulance pace moved one for one with taxi pace.

It was registered at 2026-11-13T13:27:12-0500 with sha256 `d5ae4bc880e81dbf1075d0d6df0963bb730aa71f31a494104950158198bfe180`, in commit `d75fa5e45a37`. The branch `prereg/ems-traffic-share-2019-2026` on the project's GitHub remote points at `d75fa5e45a37`. The outcome is `confirmed`, decided at 2026-11-13T13:43:30-0500.

## The deciding number

The deciding number is the city_effect: S1, share of the January-September 2019 to 2026 rise in Manhattan life-threatening EMS travel time accounted for by the taxi pace change at elasticity 1, with a day-block bootstrap 95% interval (400 draws, seed 20261113). The recorded value is estimate = 0.331097434751018, lo = 0.29459485491962767, hi = 0.3674869733328879, n = 2. The registered condition that decides the verdict is "support_if: upper 95% limit of S1 below 0.5 and estimate within 0.05 to 0.45". `verify.py` accepts a rerun when each value lies within its tolerance: estimate within 0.0001, lo within 0.0001, hi within 0.0001, n within 0.

Smallest wrapper: run_tests.py runs three tests and writes results.json, so code/rerun.py calls lib.traffic_share() unchanged for T2 only. lib.taxi_hourly() globs every taxi table in two folders (29 MB); the wrapper's copy reads, in the same order, only the files that hold rows in January-September 2019 and 2026, three of them sliced to those months. The rows the rerun uses are the same, because drop_duplicates keeps the first occurrence and the omitted files hold no rows in the windows.

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

The folder `inputs/` holds 24 files (14.4 MB), each with its sha256 in `manifest.json`. They keep the paths they have in the repository. 
For each NYC Open Data source the manifest gives the dataset id, its `rowsUpdatedAt` at fetch time, the exact SoQL query, the fetch time and the sha256 of the cached response (and of its rows alone, which is what `--refetch` compares). The city rewrites these tables in place (see the project's audit `docs/underlay_drift.md`), so the cached response is the only copy of the data as they were used. 
These inputs are slices of larger files, with the sha256 of both and the rule in the manifest: `data/derived/congestion/ems_2019.csv` (3.1 MB of 3.2 MB); `data/derived/ems_response/taxi_hourly_2019-01_2020-02.csv` (2.4 MB of 3.1 MB); `data/derived/congestion/taxi_speed_2025-01_2026-06.csv` (0.6 MB of 1.4 MB). 
The analysis code the rerun imports is copied into `code/`, with the git blob hash and last commit of each file in the manifest. The repository commit at packaging time was `47e2f54ff97e`. Seeds and draw counts above are quoted from the registration text.

## What is only pointed to

- `data/derived/congestion/ems_sources.json` (0.0 MB, sha256 `0943e5f21e562f23...`): SoQL and rowsUpdatedAt of the EMS hourly tables; not read by the rerun; pointed to by hash.
- `data/derived/ems_response/taxi_files_2019-01_2020-02.json` (0.0 MB, sha256 `34dcb45f37f71054...`): TLC file versions of taxi_hourly_2019-01_2020-02.csv; not read by the rerun; pointed to by hash.
- `data/derived/ems_response/taxi_files_2026-01_2026-06.json` (0.0 MB, sha256 `f693f7887e7c0823...`): TLC file versions of taxi_hourly_2026-01_2026-06.csv; not read by the rerun; pointed to by hash.
- `data/derived/ems_response/taxi_files_2026-07_2026-09.json` (0.0 MB, sha256 `1163fa3edd8fac47...`): TLC file versions of taxi_hourly_2026-07_2026-09.csv; not read by the rerun; pointed to by hash.
- `data/derived/reproduction/mmr_cbd_speed_files.json` (0.0 MB, sha256 `f83e304510000d76...`): TLC file versions of the congestion taxi_speed tables; not read by the rerun; pointed to by hash.
- NYC Open Data `76xm-jjuj` (EMS Incident Dispatch Data): no cached response was found, so only the query and `rowsUpdatedAt` are recorded.

## Tables this package cannot rebuild

The rerun starts from intermediate tables that it reads but cannot rebuild from what the package carries. Each is copied with its sha256; the inputs it was built from are listed with the place in `manifest.json` (under `not_rebuilt`) where each is pointed to by hash.

- `data/derived/congestion/ems_2019.csv and ems_2026.csv` was built by `analyses/congestion/ems_fetch.py` from: NYC Open Data `76xm-jjuj` (EMS Incident Dispatch Data), 0 cached page(s), 0.0 MB, pointed to by sha256 in `data[]`; `data/derived/congestion/ems_sources.json` (0.0 MB, sha256 `0943e5f21e562f23...`), pointed to by hash. It cannot be rebuilt here because the hourly EMS sums were aggregated by SoQL queries whose responses are not cached under the outcome's query; the queries and rowsUpdatedAt are in ems_sources.json.
- `data/derived/ems_response/taxi_hourly_*.csv and taxi_parts/*.csv (2019 and 2026 months)` was built by `analyses/ems_response/taxi_hourly.py` from: TLC yellow taxi trip record parquet files for 2019-01 to 2019-09 and 2026-01 to 2026-09 (about 50 to 140 MB each), kept in ~/opt/nyc-concordance; URLs, ETags and Last-Modified are in the outcome's sources and in the taxi_files_*.json records (an external service; no file is pinned); `data/derived/ems_response/taxi_files_2019-01_2020-02.json` (0.0 MB, sha256 `34dcb45f37f71054...`), pointed to by hash; `data/derived/ems_response/taxi_files_2026-01_2026-06.json` (0.0 MB, sha256 `f693f7887e7c0823...`), pointed to by hash; `data/derived/ems_response/taxi_files_2026-07_2026-09.json` (0.0 MB, sha256 `1163fa3edd8fac47...`), pointed to by hash. It cannot be rebuilt here because the TLC trip files total several GB and the drive that holds them was detached at this build.
- `data/derived/congestion/taxi_speed_2025-01_2026-06.csv` (sha256 `729cfd966eefd2e1...`) was built by `analyses/congestion/taxi_speed.py` from: TLC yellow taxi trip record parquet files, 2025-01 to 2026-06 (an external service; no file is pinned); `data/derived/reproduction/mmr_cbd_speed_files.json` (0.0 MB, sha256 `f83e304510000d76...`), pointed to by hash. It cannot be rebuilt here because it is built from TLC trip files that are not carried.

## What a stranger needs

A stranger needs Python 3.12.10 with the packages in `requirements.txt` and this folder. The check reads only files inside the folder and makes no network request unless `--refetch` is given. Re-fetching the pinned sources needs network access but no key. The registration, outcome, revision history and referee report paths are in `manifest.json` under `claim`; the referee reports themselves are in the project repository.
