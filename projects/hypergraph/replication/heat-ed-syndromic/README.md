# Replication package: heat-ed-syndromic

This folder lets a reader check one claim from the NYC concordance project without the repository. The claim is: In New York City, daily emergency department visits for heat-related illness (DOHMH syndromic surveillance) rise steeply with the day's maximum temperature in the warm season.

It was registered at 2026-11-12T15:19:38-0500 with sha256 `8d15c930565b1a7fe3f75990127c08ae83c4a6a92ed1f84624d75cc2413422ec`, in commit `176ef40c48e8`. No `prereg/` branch was found on the remote. The outcome is `confirmed`, decided at 2026-11-12T15:39:52-0500.

## The deciding number

The deciding number is the city_effect: IRR per 5 C of Central Park TMAX (lag 0) for daily heat-syndrome ED visits, May-September, negative binomial GLM with day of week, month, year and holiday, robust HC0 95% CI. The recorded value is estimate = 4.092242632189716, lo = 3.7615528042599875, hi = 4.452004433314224, n = 1522. The registered condition that decides the verdict is "prediction magnitude: IRR per 5 C between 1.5 and 5". `verify.py` accepts a rerun when each value lies within its tolerance: estimate within 0.0001, lo within 0.0001, hi within 0.0001, n within 0.

Smallest wrapper: ed_syndromic.py main() also fits a spline curve, a piecewise model and a yearly correlation and writes five files into the repository, so code/rerun.py calls its load(), nb_fit() and irr() unchanged and repeats the lines of main() that build the May-September model frame.

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

The folder `inputs/` holds 10 files (2.7 MB), each with its sha256 in `manifest.json`. They keep the paths they have in the repository. 
The NOAA station file is too large to copy whole, so `inputs/` holds a slice of it (the columns the code reads, all rows), with the Last-Modified header. The manifest gives the sha256 of the slice and of the whole file, and the rule that makes one from the other (`inputs.files[].sliced_from`). NCEI updates the file daily. 
The analysis code the rerun imports is copied into `code/`, with the git blob hash and last commit of each file in the manifest. The repository commit at packaging time was `47e2f54ff97e`. The registration names no seed and no resampling draw count; the deciding number is deterministic given the inputs.

## What is only pointed to

- `data/derived/heat/graph_evidence.json` (0.1 MB, sha256 `461e6aaf79039a2a...`): graph evidence (file); not read by the rerun; pointed to by hash.
- `data/derived/heat/graph_audit_heat.json` (0.0 MB, sha256 `f034e3df5749c39f...`): graph evidence (audit); not read by the rerun; pointed to by hash.
- `data/cache/sysgraph/27a670cce81c7f8e43cd7449.json` (0.0 MB, sha256 `feeac7a73f0fc802...`): cached System graph response; not read by the rerun; pointed to by hash.
- `data/cache/sysgraph/4308ee2d43dd6892ea46a94f.json` (0.0 MB, sha256 `fdd95b3a5e328566...`): cached System graph response; not read by the rerun; pointed to by hash.
- `data/cache/sysgraph/aeae68093ec96addc5a0640d.json` (0.0 MB, sha256 `1c073987db085d00...`): cached System graph response; not read by the rerun; pointed to by hash.
- `data/cache/sysgraph/ce67d30f80e589699565db76.json` (0.0 MB, sha256 `87380cf3a37ed2c2...`): cached System graph response; not read by the rerun; pointed to by hash.
- https://raw.githubusercontent.com/nychealth/EHDP-data/547482b9df589006543e13e8cdf6546e00ed9998/key-topics/heat-syndrome/previous_years.csv: recorded in the outcome as a github source; no file is pinned.
- https://raw.githubusercontent.com/nychealth/EHDP-data/547482b9df589006543e13e8cdf6546e00ed9998/key-topics/heat-syndrome/edheat1720_supp.csv: recorded in the outcome as a github source; no file is pinned.
- https://raw.githubusercontent.com/nychealth/EHDP-data/547482b9df589006543e13e8cdf6546e00ed9998/key-topics/heat-syndrome/edheat2021_live.csv: recorded in the outcome as a github source; no file is pinned.
- https://raw.githubusercontent.com/nychealth/EHDP-data/547482b9df589006543e13e8cdf6546e00ed9998/key-topics/heat-syndrome/edheat2022_live.csv: recorded in the outcome as a github source; no file is pinned.
- https://raw.githubusercontent.com/nychealth/EHDP-data/547482b9df589006543e13e8cdf6546e00ed9998/key-topics/heat-syndrome/edheat2023_live.csv: recorded in the outcome as a github source; no file is pinned.
- https://raw.githubusercontent.com/nychealth/EHDP-data/547482b9df589006543e13e8cdf6546e00ed9998/key-topics/heat-syndrome/edheat2024_live.csv: recorded in the outcome as a github source; no file is pinned.
- https://raw.githubusercontent.com/nychealth/EHDP-data/547482b9df589006543e13e8cdf6546e00ed9998/key-topics/heat-syndrome/edheat2025_live.csv: recorded in the outcome as a github source; no file is pinned.
- https://raw.githubusercontent.com/nychealth/EHDP-data/547482b9df589006543e13e8cdf6546e00ed9998/key-topics/heat-syndrome/edheat2026_live.csv: recorded in the outcome as a github source; no file is pinned.
- https://raw.githubusercontent.com/nychealth/EHDP-data/547482b9df589006543e13e8cdf6546e00ed9998/indicators/data/2074.json: recorded in the outcome as a github source; no file is pinned.
- https://raw.githubusercontent.com/nychealth/EHDP-data/547482b9df589006543e13e8cdf6546e00ed9998/indicators/data/2075.json: recorded in the outcome as a github source; no file is pinned.
- The System Public Graph (July 1, 2026 release (as named in the challenge brief; the API returns no version id)): 4 cached API responses for the relationships named in the registration are copied, but the graph itself is only pointed to. Fetching more needs your own API key, which you supply in `~/.config/system/token`; no key is included here.

## Tables this package cannot rebuild

None. The rerun starts from the copied source responses and computes every intermediate table itself.

## What a stranger needs

A stranger needs Python 3.12.10 with the packages in `requirements.txt` and this folder. The check reads only files inside the folder and makes no network request unless `--refetch` is given. Re-fetching the pinned sources needs network access but no key. Anything that touches the System graph beyond the copied responses needs the reader's own System API key, supplied by the reader; no key is included. The registration, outcome, revision history and referee report paths are in `manifest.json` under `claim`; the referee reports themselves are in the project repository.
