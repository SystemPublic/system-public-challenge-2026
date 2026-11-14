# Replication package: restaurants-nta-harshness

This folder lets a reader check one claim from the NYC concordance project without the repository. The claim is: Critical violations detected per routine initial inspection are not even across Manhattan's 2020 NTAs: after cuisine, chain status, quarter, day of week, daily inspection workload, new-restaurant status and the NTA's restaurant count, the between-NTA variation exceeds a permutation null, with a between-NTA standard deviation of 5 to 20 percent.

It was registered at 2026-11-13T14:18:37-0500 with sha256 `6f6e2eac57f3253c217e8cf0115e3b40ee9999caf31641c9e2e48a3ecaa53bc7`, in commit `55dabf10dd25`. The branch `prereg/restaurants-nta-harshness` on the project's GitHub remote points at `55dabf10dd25`. The outcome is `contested`, decided at 2026-11-13T14:26:29-0500.

## The deciding number

The deciding number is the city_effect: between-NTA SD (tau) of the adjusted log rate ratio of critical violations per routine initial inspection, with the permutation p of the NTA score statistic (10,000 draws, seed 20261113). The recorded value is estimate = 0.0, n = 12228, permutation_p = 0.3067, n_ntas = 31, n_restaurants = 8157. The registered condition that decides the verdict is "support_if: permutation p <= 0.01 and tau >= 0.05; refute_if: permutation p > 0.10". `verify.py` accepts a rerun when each value lies within its tolerance: estimate within 0.0001, n within 0, permutation_p within 0.0001, n_ntas within 0, n_restaurants within 0.

Smallest wrapper: evenness_test.py reads the 51 MB Underlay snapshot from ~/opt, runs two tests and writes into the repository. code/prepare.py keeps only the fields load_snapshot() reads, and code/rerun.py calls load_snapshot(), assign_nta(), design(), permutation() and nta_effects() unchanged for the harshness test, with the registered 10,000 draws and seed 20261113. The rerun takes about a minute. The claim has no placebo; the permutation null is part of the deciding test.

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

The folder `inputs/` holds 2 files (5.6 MB), each with its sha256 in `manifest.json`. They keep the paths they have in the repository. 
For each NYC Open Data source the manifest gives the dataset id, its `rowsUpdatedAt` at fetch time, the exact SoQL query, the fetch time and the sha256 of the cached response (and of its rows alone, which is what `--refetch` compares). The city rewrites these tables in place (see the project's audit `docs/underlay_drift.md`), so the cached response is the only copy of the data as they were used. 
Some inputs are cut from files too large to carry: `prepared/underlay/records_v1.0.0_min.ndjson.gzip` (1.2 MB), every record of the Underlay snapshot nyc/restaurant-inspections v1.0.0 (hash ulv2:07a7f08a0d5c85649920f8adc6946d27c17f5e2d75e9ee07c0ad4ae0fcc6739c) with only the fields evenness_test.load_snapshot() reads, gzipped. `code/prepare.py` is the code that cut them; the files it reads are listed with their sha256 under `inputs.files[].prepared_from` in the manifest: `~/opt/nyc-concordance/underlay/records_v1.0.0.ndjson` (48.6 MB, sha256 `ec6513d950a2c744...`). 
The analysis code the rerun imports is copied into `code/`, with the git blob hash and last commit of each file in the manifest. The repository commit at packaging time was `f9660de2d17f`. Seeds and draw counts above are quoted from the registration text.

## What is only pointed to

- Underlay collection `nyc/restaurant-inspections` version v1.0.0, hash `ulv2:07a7f08a0d5c85649920f8adc6946d27c17f5e2d75e9ee07c0ad4ae0fcc6739c`, ARK https://underlay.org/ark:12345/ulv0d6pnk46zsgs.v1.0.0.
- NYC Open Data `9nt8-h7nd` (2020 Neighborhood Tabulation Areas (NTAs)): no cached response was found, so only the query and `rowsUpdatedAt` are recorded.
- `~/opt/nyc-concordance/underlay/records_v1.0.0.ndjson` (48.6 MB, sha256 `ec6513d950a2c744...`): Underlay snapshot nyc/restaurant-inspections v1.0.0, read by evenness_test.py. It is kept outside the repository and is not included.

## Tables this package cannot rebuild

None. The rerun starts from the copied source responses and computes every intermediate table itself.

## What a stranger needs

A stranger needs Python 3.12.10 with the packages in `requirements.txt` and this folder. The check reads only files inside the folder and makes no network request unless `--refetch` is given. Re-fetching the pinned sources needs network access but no key. The registration, outcome, revision history and referee report paths are in `manifest.json` under `claim`; the referee reports themselves are in the project repository.
