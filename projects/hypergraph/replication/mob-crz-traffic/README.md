# Replication package: mob-crz-traffic

This folder lets a reader check one claim from the NYC concordance project without the repository. The claim is: Congestion pricing in Manhattan's Central Business District (from 5 January 2025) raised taxi and for-hire vehicle speeds and reduced TLC trip counts in the CBD relative to the rest of New York City.

It was registered at 2026-11-12T15:15:19-0500 with sha256 `7e080860acc4dff2c0ecba9b77628be759c0f9681c9daa5a3e815eabdb578b26`, in commit `f2d4f724d505`. No `prereg/` branch was found on the remote. The outcome is `confirmed`, decided at 2026-11-12T15:19:20-0500.

## The deciding number

The deciding number is the city_effect: percent change in CBD taxi and FHV speed relative to Greater NYC, 2025 against 2023-24, OLS difference-in-differences on log monthly speed with area, calendar month and year, HAC (3 lags) 95% CI. The recorded value is estimate = 5.75, lo = 2.95, hi = 8.62, n = 64, trips_pct = -9.8, trips_n = 90, placebo2024_speed_pct = -0.8, placebo2024_trips_pct = -4.5. The registered condition that decides the verdict is "prediction magnitude: speed +5% to +15% and trips -3% to -12%". `verify.py` accepts a rerun when each value lies within its tolerance: estimate within 0.005, lo within 0.005, hi within 0.005, n within 0, trips_pct within 0.05, trips_n within 0, placebo2024_speed_pct within 0.05, placebo2024_trips_pct within 0.05.

Smallest wrapper: crz_traffic.py main() also fits by-industry models, summarises two descriptive series (VMT, CRZ entries) and writes tables and a figure into the repository, so code/rerun.py repeats the lines of main() that build the speed and trip frames and calls did() and placebo() unchanged. The outcome records the city effect to two decimals, so the tolerance is 0.005 percentage points. The trip estimate is printed and checked too, because the registered prediction covers it.

The rerun also recomputes the claim's placebo, and `verify.py` compares it with the recorded value in the same way: placebo2024_speed_pct = -0.8 (within 0.05), registered pre-trend check: the same speed model with post = Jan 2024 on 2023-2024 only, recorded in outcome notes ('the 2024 placebo for speed is null (-0.8%)'); placebo2024_trips_pct = -4.5 (within 0.05), registered pre-trend check for trips, post = Jan 2024 on 2023-2024 only, recorded in outcome prediction_scored ('the 2024 placebo also shows a CBD decline (-4.5%').

## How to run it

Install Python 3.12.10, the version the package was recorded under, and the pinned packages, then run the check. With uv, which can install that Python itself:

```
uv venv --python 3.12.10 .venv
uv pip install --python .venv/bin/python -r requirements.txt
PYTHON=.venv/bin/python ./run.sh
```

Without uv, use a Python 3.12.10 interpreter from python.org or a package manager: `python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt`. Do not rely on whichever `python3` is first on the PATH; on some machines it is an Anaconda build of another version.

The packages were recorded under Python 3.12.10 on Darwin 27.2.0 (arm64). The full `uv pip freeze` of the project's environment is in `manifest.json` under `environment`. The check prints MATCH when every copied input has its recorded sha256 and the rerun reproduces the deciding number within tolerance, DRIFT when an input differs from its pin, and MISMATCH when the inputs are intact but the number differs, which points to a change in code or environment. `./run.sh --refetch` also re-runs each pinned query and reports whether the live sources still match their pins. No key is needed for these. With `--refetch` the deciding number is also recomputed from the live data, and `live_number_within_tolerance` says whether it still agrees; DRIFT with that flag true means the sources changed but the number did not. A run writes `verify_result.json`, and `--refetch` writes `refetched/`, inside the package; the rerun may also write `work/` and `code/data/`. These are listed in `.gitignore`.

## What is pinned

The folder `inputs/` holds 5 files (3.1 MB), each with its sha256 in `manifest.json`. They keep the paths they have in the repository. 
For each NYC Open Data source the manifest gives the dataset id, its `rowsUpdatedAt` at fetch time, the exact SoQL query, the fetch time and the sha256 of the cached response (and of its rows alone, which is what `--refetch` compares). The city rewrites these tables in place (see the project's audit `docs/underlay_drift.md`), so the cached response is the only copy of the data as they were used. 
The analysis code the rerun imports is copied into `code/`, with the git blob hash and last commit of each file in the manifest. The repository commit at packaging time was `47e2f54ff97e`. The registration names no seed and no resampling draw count; the deciding number is deterministic given the inputs.

## What is only pointed to

- `data/derived/mobility/graph_evidence.json` (0.0 MB, sha256 `8bdfe0dbce7a9c1e...`): graph evidence (file); not read by the rerun; pointed to by hash.

## Tables this package cannot rebuild

None. The rerun starts from the copied source responses and computes every intermediate table itself.

## What a stranger needs

A stranger needs Python 3.12.10 with the packages in `requirements.txt` and this folder. The check reads only files inside the folder and makes no network request unless `--refetch` is given. Re-fetching the pinned sources needs network access but no key. Anything that touches the System graph beyond the copied responses needs the reader's own System API key, supplied by the reader; no key is included. The registration, outcome, revision history and referee report paths are in `manifest.json` under `claim`; the referee reports themselves are in the project repository.
