# Replication package: bridge-heat-shootings-ems

This folder lets a reader check one claim from the NYC concordance project without the repository. The claim is: Composed from heat and shootings (heat-shootings, NYPD) and the share of EMS gunshot dispatches that are shooting victims (bridge-shot-ems-link), daily FDNY EMS dispatches for gunshot wounds rise with the day's maximum temperature by the composed rate ratio.

It was registered at 2026-11-12T16:04:50-0500 with sha256 `bda255d3ebffd6189ea84b6060c0e85675e809fee6bcbdbb17a4a6281ff11099`, in commit `e783221b5d7c`. No `prereg/` branch was found on the remote. The outcome is `bridged`, decided at 2026-11-12T16:10:34-0500.

## The deciding number

The deciding number is the city_effect: IRR per 5 C of Central Park TMAX (lag 0) for daily FDNY EMS SHOT dispatches, 2006 to August 2026, negative binomial GLM as in heat-shootings, robust HC0 95% CI; and its compatibility z with the composed prediction. The recorded value is estimate = 1.1105984346713746, lo = 1.100129319081887, hi = 1.1211671770768419, n = 7548, compat_z = 0.4149437146358164, stab_contrast = 1.0759499384976088. The registered condition that decides the verdict is "endpoint IRR compatible with the composed prediction 1.099 (1.049 to 1.148), |z| < 1.96". `verify.py` accepts a rerun when each value lies within its tolerance: estimate within 0.0001, lo within 0.0001, hi within 0.0001, n within 0, compat_z within 0.01, stab_contrast within 0.0001.

Smallest wrapper: ems_shot.py main() also fits a link model and four sensitivity models and writes into the repository, and it reads the composed prediction from a file written by compose.py. code/rerun.py recomputes the composed prediction with compose.py's own functions, seed (20261112) and draw count (200,000), then calls build(), ems_daily(), nb_fit(), irr() and compat() unchanged for the endpoint and for the STAB contrast. The verdict turns on whether the endpoint IRR is compatible with the composed prediction (|z| < 1.96); the recorded z is 0.41.

The rerun also recomputes the claim's placebo, and `verify.py` compares it with the recorded value in the same way: stab_contrast = 1.0759499384976088 (within 0.0001), IRR per 5 C for STAB dispatches, the registered contrast outside the heat-shooting chain, recorded in outcome notes (1.076) and data/derived/bridges/ems_results.json sensitivity.STAB_contrast.

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

The folder `inputs/` holds 6 files (4.6 MB), each with its sha256 in `manifest.json`. They keep the paths they have in the repository. 
For each NYC Open Data source the manifest gives the dataset id, its `rowsUpdatedAt` at fetch time, the exact SoQL query, the fetch time and the sha256 of the cached response (and of its rows alone, which is what `--refetch` compares). The city rewrites these tables in place (see the project's audit `docs/underlay_drift.md`), so the cached response is the only copy of the data as they were used. 
The NOAA station file is too large to copy whole, so `inputs/` holds a slice of it (the columns the code reads, all rows), with the Last-Modified header. The manifest gives the sha256 of the slice and of the whole file, and the rule that makes one from the other (`inputs.files[].sliced_from`). NCEI updates the file daily. 
The analysis code the rerun imports is copied into `code/`, with the git blob hash and last commit of each file in the manifest. The repository commit at packaging time was `47e2f54ff97e`. The registration names no seed and no resampling draw count; the deciding number is deterministic given the inputs.

## What is only pointed to

Nothing.

## Tables this package cannot rebuild

None. The rerun starts from the copied source responses and computes every intermediate table itself.

## What a stranger needs

A stranger needs Python 3.12.10 with the packages in `requirements.txt` and this folder. The check reads only files inside the folder and makes no network request unless `--refetch` is given. Re-fetching the pinned sources needs network access but no key. The registration, outcome, revision history and referee report paths are in `manifest.json` under `claim`; the referee reports themselves are in the project repository.
