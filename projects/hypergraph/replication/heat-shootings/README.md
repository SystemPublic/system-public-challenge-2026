# Replication package: heat-shootings

This folder lets a reader check one claim from the NYC concordance project without the repository. The claim is: In New York City, the daily number of shooting incidents rises with the day's maximum temperature at Central Park, within month and year, by about 5 to 20 percent per 5 C.

It was registered at 2026-11-12T15:19:38-0500 with sha256 `b2a1bd8ecec550da1e1e07d368d2e5f1b7d108b07ce6f51ef658bbb197ebb762`, in commit `67507946fe78`. No `prereg/` branch was found on the remote. The outcome is `confirmed`, decided at 2026-11-12T15:39:52-0500.

## The deciding number

The deciding number is the city_effect: IRR per 5 C of Central Park TMAX (lag 0), negative binomial GLM, robust HC0 95% CI. The recorded value is estimate = 1.1462159704993367, lo = 1.1297421298925683, hi = 1.162930031787583, n = 7548. The registered condition that decides the verdict is "support_if: lower 95% limit above 1.00". `verify.py` accepts a rerun when each value lies within its tolerance: estimate within 0.0001, lo within 0.0001, hi within 0.0001, n within 0.

Smallest wrapper: shootings.py main() also runs eight sensitivity models and writes into the repository, so code/rerun.py calls its build() and nb_fit() for the primary model only.

## How to run it

Install Python 3.12.10, the version the package was recorded under, and the pinned packages, then run the check. With uv, which can install that Python itself:

```
uv venv --python 3.12.10 .venv
uv pip install --python .venv/bin/python -r requirements.txt
PYTHON=.venv/bin/python ./run.sh
```

Without uv, use a Python 3.12.10 interpreter from python.org or a package manager: `python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt`. Do not rely on whichever `python3` is first on the PATH; on some machines it is an Anaconda build of another version.

The packages were recorded under Python 3.12.10 on Darwin 27.2.0 (arm64). The full `uv pip freeze` of the project's environment is in `manifest.json` under `environment`. The check prints MATCH when every copied input has its recorded sha256 and the rerun reproduces the deciding number within tolerance, DRIFT when an input differs from its pin, and MISMATCH when the inputs are intact but the number differs, which points to a change in code or environment. `./run.sh --refetch` also re-runs each pinned query and the NOAA download and reports whether the live sources still match their pins. No key is needed for these. With `--refetch` the deciding number is also recomputed from the live data, and `live_number_within_tolerance` says whether it still agrees; DRIFT with that flag true means the sources changed but the number did not. NCEI rewrites the NOAA station file every day, so `--refetch` will report DRIFT for it whenever a day has passed. A run writes `verify_result.json`, and `--refetch` writes `refetched/`, inside the package; the rerun may also write `work/` and `code/data/`. These are listed in `.gitignore`.

## What is pinned

The folder `inputs/` holds 19 files (18.1 MB), each with its sha256 in `manifest.json`. They keep the paths they have in the repository. 
For each NYC Open Data source the manifest gives the dataset id, its `rowsUpdatedAt` at fetch time, the exact SoQL query, the fetch time and the sha256 of the cached response (and of its rows alone, which is what `--refetch` compares). The city rewrites these tables in place (see the project's audit `docs/underlay_drift.md`), so the cached response is the only copy of the data as they were used. 
The NOAA station file is copied whole with its Last-Modified header. NCEI updates it daily. 
The analysis code the rerun imports is copied into `code/`, with the git blob hash and last commit of each file in the manifest. The repository commit at packaging time was `47e2f54ff97e`. The registration names no seed and no resampling draw count; the deciding number is deterministic given the inputs.

## What is only pointed to

- The System Public Graph (July 1, 2026 release (as named in the challenge brief; the API returns no version id)): 12 cached API responses for the relationships named in the registration are copied, but the graph itself is only pointed to. Fetching more needs your own API key, which you supply in `~/.config/system/token`; no key is included here.

## Tables this package cannot rebuild

None. The rerun starts from the copied source responses and computes every intermediate table itself.

## What a stranger needs

A stranger needs Python 3.12.10 with the packages in `requirements.txt` and this folder. The check reads only files inside the folder and makes no network request unless `--refetch` is given. Re-fetching the pinned sources needs network access but no key. Anything that touches the System graph beyond the copied responses needs the reader's own System API key, supplied by the reader; no key is included. The registration, outcome, revision history and referee report paths are in `manifest.json` under `claim`; the referee reports themselves are in the project repository.
