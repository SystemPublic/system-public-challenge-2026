# Replication package: street-busway14-m14-speed

This folder lets a reader check one claim from the NYC concordance project without the repository. The claim is: On weekdays in October 2019 to February 2020 the M14A and M14D Select Bus Service ran at least 4% faster, relative to the other Manhattan bus routes, than in July to September 2019, when the SBS ran without the busway.

It was registered at 2026-11-13T13:12:22-0500 with sha256 `3a9ed05a54f81f1f92c8303f8aacbc11f9db8818bd5cd3d41c7e9ea99af36b37`, in commit `f26cd61cc178`. The branch `prereg/street-busway14-m14-speed` on the project's GitHub remote points at `f26cd61cc178`. The outcome is `confirmed`, decided at 2026-11-13T13:21:51-0500.

## The deciding number

The deciding number is the city_effect: percent change in M14A+M14D weekday speed, Oct 2019-Feb 2020 against Jul-Sep 2019, minus the mean change of 39 other Manhattan routes (DiD on log speed), with the 95% interval from the placebo SD. The recorded value is estimate = 5.457, lo = 1.693, hi = 9.36, n = 39, se_log = 0.0185421743139463, placebo_sd_log = 0.0185421743139463, placebo_n = 119, placebo_n_as_large = 2. The registered condition that decides the verdict is "support_if: DiD >= 4% and lower 95% limit above 0". `verify.py` accepts a rerun when each value lies within its tolerance: estimate within 0.0005, lo within 0.0005, hi within 0.0005, n within 0, se_log within 1e-09, placebo_sd_log within 1e-09, placebo_n within 0, placebo_n_as_large within 0.

Smallest wrapper: bus.py reads and writes data/derived/street_space/ inside the repository, so code/rerun.py sets bus.DER to work/street_space inside the package and calls design() and final() unchanged. The standard error of the M14 DiD is the standard deviation of the 119 placebo DiDs, so the placebo stage is part of the deciding number.

The rerun also recomputes the claim's placebo, and `verify.py` compares it with the recorded value in the same way: placebo_sd_log = 0.0185421743139463 (within 1e-09), registered null distribution: SD of the 119 placebo DiDs (each other Manhattan route as if treated, seasons 2021-2023), recorded in outcome city_effect.se_log (= sd of the placebo DiDs); placebo_n = 119 (within 0), number of placebo DiDs, recorded in registration plan ('119 placebo DiDs'); placebo_n_as_large = 2 (within 0), placebo DiDs at least as large as the M14 estimate (signed, as the referee counted them), recorded in outcome notes_referee and critique/street-busway14-m14-speed.md ('2 of 119').

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

The folder `inputs/` holds 2 files (0.2 MB), each with its sha256 in `manifest.json`. They keep the paths they have in the repository. 
For each NYC Open Data source the manifest gives the dataset id, its `rowsUpdatedAt` at fetch time, the exact SoQL query, the fetch time and the sha256 of the cached response (and of its rows alone, which is what `--refetch` compares). The city rewrites these tables in place (see the project's audit `docs/underlay_drift.md`), so the cached response is the only copy of the data as they were used. 
The analysis code the rerun imports is copied into `code/`, with the git blob hash and last commit of each file in the manifest. The repository commit at packaging time was `47e2f54ff97e`. The registration names no seed and no resampling draw count; the deciding number is deterministic given the inputs.

## What is only pointed to

Nothing.

## Tables this package cannot rebuild

None. The rerun starts from the copied source responses and computes every intermediate table itself.

## What a stranger needs

A stranger needs Python 3.12.10 with the packages in `requirements.txt` and this folder. The check reads only files inside the folder and makes no network request unless `--refetch` is given. Re-fetching the pinned sources needs network access but no key. The registration, outcome, revision history and referee report paths are in `manifest.json` under `claim`; the referee reports themselves are in the project repository.
