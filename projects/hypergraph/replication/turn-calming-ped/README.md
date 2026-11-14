# Replication package: turn-calming-ped

This folder lets a reader check one claim from the NYC concordance project without the repository. The claim is: NYC DOT left-turn traffic calming (hardened centerlines, slow-turn wedges and related treatments) reduced pedestrians injured or killed within 40 m of treated intersections in the two years after installation, relative to intersections DOT treated later.

It was registered at 2026-11-13T13:18:40-0500 with sha256 `5941844b4bc2fd346ebb469eafa51c0dc44fca0f1ff247bc0086f3fba10debc2`, in commit `85b40afe3055`. The branch `prereg/turn-calming-ped` on the project's GitHub remote points at `85b40afe3055`. The outcome is `confirmed`, decided at 2026-11-13T14:04:20-0500.

## The deciding number

The deciding number is the city_effect: ratio of ratios of pedestrians injured or killed within 40 m, 24 months after against 24 months before installation, treated against later-treated sites, stacked cohorts 2016Q3-2023Q2, conditional Poisson (binomial GLM), SE clustered by site. The recorded value is estimate = 0.8482, lo = 0.7787, hi = 0.924, n = 712, placebo_12m_ror = 0.9119, placebo_12m_lo = 0.8252, placebo_12m_hi = 1.0078. The registered condition that decides the verdict is "support_if: upper bound of the 95% interval of the ratio of ratios below 1.00". `verify.py` accepts a rerun when each value lies within its tolerance: estimate within 0.0001, lo within 0.0001, hi within 0.0001, n within 0, placebo_12m_ror within 0.0001, placebo_12m_lo within 0.0001, placebo_12m_hi within 0.0001.

Smallest wrapper: did.py reads 174 MB of crash records from ~/opt and writes into the repository. code/prepare.py keeps the crashes within 40.5 m of a calming site with at least one pedestrian injured or killed, the only crashes that add to the pedestrian count within 40 m, and code/rerun.py calls load_crashes(), site_monthly(), stack() and fit() unchanged for that outcome. The left-turn and ring outcomes are not reproduced from this cut. The recorded n (712) is the number of treated sites. The placebo is the referee's exploratory check, not a registered one.

The rerun also recomputes the claim's placebo, and `verify.py` compares it with the recorded value in the same way: placebo_12m_ror = 0.9119 (within 0.0001), UNREGISTERED exploratory placebo named by the referee: installation moved 12 months early (months -24..-13 against -12..-1), recorded in outcome notes and data/derived/turn_restrictions/did_explore.json (ped.placebo_12m_early); placebo_12m_lo = 0.8252 (within 0.0001), its lower 95% limit, recorded in data/derived/turn_restrictions/did_explore.json; placebo_12m_hi = 1.0078 (within 0.0001), its upper 95% limit, recorded in data/derived/turn_restrictions/did_explore.json.

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

The folder `inputs/` holds 3 files (2.0 MB), each with its sha256 in `manifest.json`. They keep the paths they have in the repository. 
For each NYC Open Data source the manifest gives the dataset id, its `rowsUpdatedAt` at fetch time, the exact SoQL query, the fetch time and the sha256 of the cached response (and of its rows alone, which is what `--refetch` compares). The city rewrites these tables in place (see the project's audit `docs/underlay_drift.md`), so the cached response is the only copy of the data as they were used. 
Some inputs are cut from files too large to carry: `prepared/turn_restrictions/crashes.csv` (1.5 MB), the crash records (h9gi-nx95, fetched by analyses/turn_restrictions/fetch_crashes.py) with a pedestrian injured or killed within 40.5 m of a left-turn calming site, and the left-turn vehicle records (bm4k-52h4) of those crashes; `prepared/turn_restrictions/left_vehicles.csv` (0.2 MB), the crash records (h9gi-nx95, fetched by analyses/turn_restrictions/fetch_crashes.py) with a pedestrian injured or killed within 40.5 m of a left-turn calming site, and the left-turn vehicle records (bm4k-52h4) of those crashes. `code/prepare.py` is the code that cut them; the files it reads are listed with their sha256 under `inputs.files[].prepared_from` in the manifest: `~/opt/nyc-concordance/turn_restrictions/crashes.csv` (173.9 MB, sha256 `0348a9eeee336881...`); `~/opt/nyc-concordance/turn_restrictions/left_vehicles.csv` (17.4 MB, sha256 `4ceb4850aedbf88b...`); `data/derived/turn_restrictions/sites.json` (0.3 MB, sha256 `d877a2a9cf5e211b...`). 
The analysis code the rerun imports is copied into `code/`, with the git blob hash and last commit of each file in the manifest. The repository commit at packaging time was `a9efe822a26e`. The registration names no seed and no resampling draw count; the deciding number is deterministic given the inputs.

## What is only pointed to

- `data/cache/socrata/sm2x-35i7-28298048f09e2906e26154a7.json` (0.4 MB, sha256 `197157eec5d6250e...`): cached Socrata response, sm2x-35i7; not read by the rerun; pointed to by hash.
- NYC Open Data `h9gi-nx95` (Motor Vehicle Collisions - Crashes): no cached response was found, so only the query and `rowsUpdatedAt` are recorded.
- NYC Open Data `bm4k-52h4` (Motor Vehicle Collisions - Vehicles): no cached response was found, so only the query and `rowsUpdatedAt` are recorded.
- `~/opt/nyc-concordance/turn_restrictions/crashes.csv` (173.9 MB, sha256 `0348a9eeee336881...`): all geocoded crashes, 2014-2026, read by did.py. It is kept outside the repository and is not included.
- `~/opt/nyc-concordance/turn_restrictions/left_vehicles.csv` (17.4 MB, sha256 `4ceb4850aedbf88b...`): vehicles making a left turn, read by did.py. It is kept outside the repository and is not included.

## Tables this package cannot rebuild

None. The rerun starts from the copied source responses and computes every intermediate table itself.

## What a stranger needs

A stranger needs Python 3.12.10 with the packages in `requirements.txt` and this folder. The check reads only files inside the folder and makes no network request unless `--refetch` is given. Re-fetching the pinned sources needs network access but no key. The registration, outcome, revision history and referee report paths are in `manifest.json` under `claim`; the referee reports themselves are in the project repository.
