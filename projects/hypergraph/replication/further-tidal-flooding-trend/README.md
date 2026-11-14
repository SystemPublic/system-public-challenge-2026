# Replication package: further-tidal-flooding-trend

This folder lets a reader check one claim from the NYC concordance project without the repository. The claim is: In a held-out period (2010 to 2019), on dry days 311 street-flooding and catch-basin complaints from the low-lying coastal ZIP codes rise with the daily maximum water level at the Battery above a knot of 0.35 m above MHHW, and the rise is larger there than in other ZIP codes; and the annual count of dry days with a Battery maximum above that knot rose over 2010 to 2025 at about the rate that the Battery sea-level trend implies.

It was registered at 2026-11-12T23:44:06-0500 with sha256 `517759937d19637def545614ad12b6602797658a915567e7ab6799e9575efe78`, in commit `5fd01ba768e8`. The branch `prereg/further-tidal-flooding-trend` on the project's GitHub remote points at `9ff568d395bb`. The outcome is `confirmed`, decided at 2026-11-13T00:35:27-0500.

## The deciding number

The deciding number is the city_effect: rate ratio of dry-day street-flooding and catch-basin complaints (C3) in the tidal ZIP set per 10 cm of Battery daily maximum above 0.35 m over MHHW, 2010-2019, negative binomial, 14-day moving-block bootstrap 95% interval (seed 20261113, 1,000 replicates); and the tidal-over-placebo-ZIP ratio of rate ratios. The recorded value is estimate = 2.000694591935365, lo = 1.6436462504789693, hi = 2.3843478152869113, n = 1882, ratio_lo = 1.4348997719663479, placebo_zip_rr = 1.1530935101354036, shift7_tidal_rr = 0.9926041049820505, shift7_tidal_hi = 1.0704564224491058, shift100_tidal_rr = 0.9713548847095617, shift100_tidal_hi = 1.0450819569777863. The registered condition that decides the verdict is "support_if: tidal-set interval lower limit above 1.00 and tidal-over-placebo ratio interval lower limit above 1.00; shifted-tide placebos not above 1". `verify.py` accepts a rerun when each value lies within its tolerance: estimate within 0.0001, lo within 0.0001, hi within 0.0001, n within 0, ratio_lo within 0.0001, placebo_zip_rr within 0.0001, shift7_tidal_rr within 0.0001, shift7_tidal_hi within 0.0001, shift100_tidal_rr within 0.0001, shift100_tidal_hi within 0.0001.

Smallest wrapper: analyse.py is a flat script that runs eighteen bootstrapped models on import and writes into the repository. code/rerun.py executes the script's own source with four asserted textual changes (inputs path; the complaint series read from daily_panel.csv instead of aggregated from the 27.8 MB complaints_by_day_zip.json; no results.json write; stop after the primary model and the two shifted-tide placebos). The block bootstrap uses the registered seed 20261113 and 1,000 replicates, drawn in the same order as the full script, so the intervals reproduce exactly. The rerun takes several minutes.

The rerun also recomputes the claim's placebo, and `verify.py` compares it with the recorded value in the same way: placebo_zip_rr = 1.1530935101354036 (within 0.0001), the same model on the placebo ZIP set (every ZIP outside the broad tidal set), recorded in data/derived/round2/tidal_trend/results.json primary.placebo.rr (outcome: 1.15); shift7_tidal_rr = 0.9926041049820505 (within 0.0001), tidal-set rate ratio with the tide shifted 7 days (registered placebo), recorded in data/derived/round2/tidal_trend/results.json placebo_shift7.tidal.rr; shift7_tidal_hi = 1.0704564224491058 (within 0.0001), upper bootstrap limit of the 7-day shifted-tide placebo, recorded in data/derived/round2/tidal_trend/results.json placebo_shift7.tidal.hi; shift100_tidal_rr = 0.9713548847095617 (within 0.0001), tidal-set rate ratio with the tide shifted 100 days (registered placebo), recorded in data/derived/round2/tidal_trend/results.json placebo_shift100.tidal.rr; shift100_tidal_hi = 1.0450819569777863 (within 0.0001), upper bootstrap limit of the 100-day shifted-tide placebo, recorded in data/derived/round2/tidal_trend/results.json placebo_shift100.tidal.hi.

## How to run it

Install Python 3.12.10, the version the package was recorded under, and the pinned packages, then run the check. With uv, which can install that Python itself:

```
uv venv --python 3.12.10 .venv
uv pip install --python .venv/bin/python -r requirements.txt
PYTHON=.venv/bin/python ./run.sh
```

Without uv, use a Python 3.12.10 interpreter from python.org or a package manager: `python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt`. Do not rely on whichever `python3` is first on the PATH; on some machines it is an Anaconda build of another version.

The packages were recorded under Python 3.12.10 on Darwin 27.2.0 (arm64). The full `uv pip freeze` of the project's environment is in `manifest.json` under `environment`. The check prints MATCH when every copied input has its recorded sha256 and the rerun reproduces the deciding number within tolerance, DRIFT when an input differs from its pin, and MISMATCH when the inputs are intact but the number differs, which points to a change in code or environment. `./run.sh --refetch` also re-runs each pinned query and the NOAA download and reports whether the live sources still match their pins. No key is needed for these. With `--refetch` the deciding number is not recomputed from live data, because the derived tables it reads come from upstream stages that are not packaged; DRIFT then says only that a pinned source has changed. NCEI rewrites the NOAA station file every day, so `--refetch` will report DRIFT for it whenever a day has passed. A run writes `verify_result.json`, and `--refetch` writes `refetched/`, inside the package; the rerun may also write `work/` and `code/data/`. These are listed in `.gitignore`.

## What is pinned

The folder `inputs/` holds 4 files (2.4 MB), each with its sha256 in `manifest.json`. They keep the paths they have in the repository. 
For each NYC Open Data source the manifest gives the dataset id, its `rowsUpdatedAt` at fetch time, the exact SoQL query, the fetch time and the sha256 of the cached response (and of its rows alone, which is what `--refetch` compares). The city rewrites these tables in place (see the project's audit `docs/underlay_drift.md`), so the cached response is the only copy of the data as they were used. 
The NOAA station file is copied whole with its Last-Modified header. NCEI updates it daily. 
The analysis code the rerun imports is copied into `code/`, with the git blob hash and last commit of each file in the manifest. The repository commit at packaging time was `47e2f54ff97e`. Seeds and draw counts above are quoted from the registration text.

## What is only pointed to

- `data/cache/socrata/76ig-c548-a55b37766d07b0951c8f9b51.json` (0.0 MB, sha256 `dd7dad94129cb7c9...`): cached Socrata response, 76ig-c548; not read by the rerun; pointed to by hash.
- `data/cache/socrata/erm2-nwe9-a8e80fda807bcee86ab51dd6.json` (0.3 MB, sha256 `f3d2bbdd98a5452e...`): cached Socrata response, erm2-nwe9; not read by the rerun; pointed to by hash.
- `data/derived/round2/tidal_trend/complaints_by_day_zip.json` (26.5 MB, sha256 `00bcf097b2d93a20...`): input of analyses/round2_tidal/analyse.py (not rerun); not read by the rerun; pointed to by hash.
- noaa-co-ops: recorded in the outcome as a noaa-co-ops source; no file is pinned.
- noaa-co-ops: recorded in the outcome as a noaa-co-ops source; no file is pinned.

## Tables this package cannot rebuild

The rerun starts from intermediate tables that it reads but cannot rebuild from what the package carries. Each is copied with its sha256; the inputs it was built from are listed with the place in `manifest.json` (under `not_rebuilt`) where each is pointed to by hash.

- `data/derived/round2/tidal_trend/daily_panel.csv` (sha256 `1a3782dc2bec1aa9...`) was built by `analyses/round2_tidal/analyse.py` from: `data/derived/round2/tidal_trend/complaints_by_day_zip.json` (26.5 MB, sha256 `00bcf097b2d93a20...`), pointed to by hash; `data/derived/round2/tidal_trend/battery_daily_max_mhhw.json` (0.2 MB, sha256 `86a5914ca476ee5e...`), copied; `data/derived/round2/tidal_trend/prcp_central_park.csv` (0.8 MB, sha256 `c9013459e870210c...`), copied; `data/derived/round2/tidal_trend/prcp_jfk.csv` (0.4 MB, sha256 `b0368bfb8ae5f61e...`), copied. It cannot be rebuilt here because its complaint columns are aggregated from complaints_by_day_zip.json (27.8 MB, over the cap; written by analyses/round2_tidal/fetch_311.py from 311 queries of 76ig-c548 and erm2-nwe9); the rerun takes only the columns C3_t, C3_p, C1_t and C4_t from it and rebuilds the tide and dry-day columns itself.

## What a stranger needs

A stranger needs Python 3.12.10 with the packages in `requirements.txt` and this folder. The check reads only files inside the folder and makes no network request unless `--refetch` is given. Re-fetching the pinned sources needs network access but no key. The registration, outcome, revision history and referee report paths are in `manifest.json` under `claim`; the referee reports themselves are in the project repository.
