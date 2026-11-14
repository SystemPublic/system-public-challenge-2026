# Replication package: food-supermarket-diabetes-zcta

This folder lets a reader check one claim from the NYC concordance project without the repository. The claim is: Across New York City ZIP code areas, the number of supermarkets per resident does not predict adult hospital admissions for diabetes (age-sex standardised) once residential density, poverty, income and median age are held, against the graph's cross-sectional findings that distance to or scarcity of supermarkets goes with more diabetes.

It was registered at 2026-11-13T12:00:23-0500 with sha256 `7af9b8f8298e72630678ce3e796d6338e4a27db4a3fd984b8af08f9a605c8d36`, in commit `d97489780d32`. The branch `prereg/food-supermarket-diabetes-zcta` on the project's GitHub remote points at `d97489780d32`. The outcome is `confirmed`, decided at 2026-11-13T12:08:35-0500.

## The deciding number

The deciding number is the city_effect: ratio of the diabetes admission O/E (SPARCS PQI 01, 03, 14, 16, 2021-2023) per doubling of supermarkets >= 6,000 sq ft per 10,000 residents, adjusted, 168 ZCTAs, WLS by population, HC3 95% CI. The recorded value is estimate = 0.995099767922046, lo = 0.9463921955555745, hi = 1.0463141525984418, n = 168. The registered condition that decides the verdict is "support_if: primary ratio with 95% interval inside (0.90, 1.10) and estimate at or above 0.95". `verify.py` accepts a rerun when each value lies within its tolerance: estimate within 0.0001, lo within 0.0001, hi within 0.0001, n within 0.

Smallest wrapper: food_access.py main() downloads Census files into ~/opt/nyc-concordance/census, fits ten models and writes into the repository. code/rerun.py reruns stores() and pqi() unchanged from the cached Socrata responses, takes the Census columns from the derived table food_zcta.csv, repeats the merge and filter of main() and calls fit() and coef() unchanged for the primary model. The referee's negative control (critique/food-supermarket-diabetes-zcta.md) uses other admission measures and is not rerun here.

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

The folder `inputs/` holds 4 files (3.9 MB), each with its sha256 in `manifest.json`. They keep the paths they have in the repository. 
For each NYC Open Data source the manifest gives the dataset id, its `rowsUpdatedAt` at fetch time, the exact SoQL query, the fetch time and the sha256 of the cached response (and of its rows alone, which is what `--refetch` compares). The city rewrites these tables in place (see the project's audit `docs/underlay_drift.md`), so the cached response is the only copy of the data as they were used. 
The analysis code the rerun imports is copied into `code/`, with the git blob hash and last commit of each file in the manifest. The repository commit at packaging time was `a9efe822a26e`. The registration names no seed and no resampling draw count; the deciding number is deterministic given the inputs.

## What is only pointed to

- https://www2.census.gov/geo/docs/maps-data/data/rel2020/zcta520/tab20_zcta520_county20_natl.txt: recorded in the outcome as a census source; no file is pinned.
- https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2020_Gazetteer/2020_Gaz_zcta_national.zip: recorded in the outcome as a census source; no file is pinned.
- https://www2.census.gov/programs-surveys/acs/summary_file/2023/table-based-SF/data/5YRData/acsdt5y2023-<table>.dat: recorded in the outcome as a census-acs source; no file is pinned.
- `~/opt/nyc-concordance/census/zcta_county_rel.txt` (6.5 MB, sha256 `3ed41278d637dc24...`): Census or ACS file read by food_access.zctas() to build food_zcta.csv. It is kept outside the repository and is not included.
- `~/opt/nyc-concordance/census/gaz_zcta_2020.zip` (1.0 MB, sha256 `335402fb16b41303...`): Census or ACS file read by food_access.zctas() to build food_zcta.csv. It is kept outside the repository and is not included.
- `~/opt/nyc-concordance/census/acsdt5y2023-b01003.dat` (17.5 MB, sha256 `24ae3f523b4c5433...`): Census or ACS file read by food_access.zctas() to build food_zcta.csv. It is kept outside the repository and is not included.
- `~/opt/nyc-concordance/census/acsdt5y2023-b19013.dat` (17.1 MB, sha256 `c9007017b7bb29ba...`): Census or ACS file read by food_access.zctas() to build food_zcta.csv. It is kept outside the repository and is not included.
- `~/opt/nyc-concordance/census/acsdt5y2023-b17001.dat` (112.9 MB, sha256 `578e998daf0823a1...`): Census or ACS file read by food_access.zctas() to build food_zcta.csv. It is kept outside the repository and is not included.
- `~/opt/nyc-concordance/census/acsdt5y2023-b01002.dat` (25.4 MB, sha256 `270cb55fea151fde...`): Census or ACS file read by food_access.zctas() to build food_zcta.csv. It is kept outside the repository and is not included.
- `~/opt/nyc-concordance/census/acsdt5y2023-b03002.dat` (79.0 MB, sha256 `cae53cb92e7ca446...`): Census or ACS file read by food_access.zctas() to build food_zcta.csv. It is kept outside the repository and is not included.
- `~/opt/nyc-concordance/census/acsdt5y2023-b08201.dat` (61.9 MB, sha256 `71e502d0d2b456cb...`): Census or ACS file read by food_access.zctas() to build food_zcta.csv. It is kept outside the repository and is not included.
- `~/opt/nyc-concordance/census/acsdt5y2023-b09021.dat` (61.6 MB, sha256 `c313a828919e44ac...`): Census or ACS file read by food_access.zctas() to build food_zcta.csv. It is kept outside the repository and is not included.

## Tables this package cannot rebuild

The rerun starts from intermediate tables that it reads but cannot rebuild from what the package carries. Each is copied with its sha256; the inputs it was built from are listed with the place in `manifest.json` (under `not_rebuilt`) where each is pointed to by hash.

- `data/derived/health_gaps/food_zcta.csv` (sha256 `7f2732d7e11958cd...`) was built by `analyses/health_gaps/food_access.py` from: `~/opt/nyc-concordance/census/zcta_county_rel.txt` (6.5 MB, sha256 `3ed41278d637dc24...`), pointed to by hash; `~/opt/nyc-concordance/census/gaz_zcta_2020.zip` (1.0 MB, sha256 `335402fb16b41303...`), pointed to by hash; `~/opt/nyc-concordance/census/acsdt5y2023-b01003.dat` (17.5 MB, sha256 `24ae3f523b4c5433...`), pointed to by hash; `~/opt/nyc-concordance/census/acsdt5y2023-b19013.dat` (17.1 MB, sha256 `c9007017b7bb29ba...`), pointed to by hash; `~/opt/nyc-concordance/census/acsdt5y2023-b17001.dat` (112.9 MB, sha256 `578e998daf0823a1...`), pointed to by hash; `~/opt/nyc-concordance/census/acsdt5y2023-b01002.dat` (25.4 MB, sha256 `270cb55fea151fde...`), pointed to by hash; `~/opt/nyc-concordance/census/acsdt5y2023-b03002.dat` (79.0 MB, sha256 `cae53cb92e7ca446...`), pointed to by hash; `~/opt/nyc-concordance/census/acsdt5y2023-b08201.dat` (61.9 MB, sha256 `71e502d0d2b456cb...`), pointed to by hash; `~/opt/nyc-concordance/census/acsdt5y2023-b09021.dat` (61.6 MB, sha256 `c313a828919e44ac...`), pointed to by hash. It cannot be rebuilt here because its Census columns come from national Census and ACS files kept in ~/opt/nyc-concordance/census (about 400 MB together), outside the repository; the rerun uses only those columns of the table and recomputes the store and PQI columns.

## What a stranger needs

A stranger needs Python 3.12.10 with the packages in `requirements.txt` and this folder. The check reads only files inside the folder and makes no network request unless `--refetch` is given. Re-fetching the pinned sources needs network access but no key. The registration, outcome, revision history and referee report paths are in `manifest.json` under `claim`; the referee reports themselves are in the project repository.
