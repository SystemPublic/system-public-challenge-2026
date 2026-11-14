# Replication package: levers-vacant-lot-trial-match

This folder lets a reader check one claim from the NYC concordance project without the repository. The claim is: Of New York's tax lots recorded as vacant land (MapPLUTO 26v2 land use 11) in the census tracts with the most shootings, about three in ten resemble the lots of the Philadelphia vacant-lot trial (small, unpaved, not under development, not a garden or buyout parcel), and greening them would prevent on the order of 20 shootings a year.

It was registered at 2026-11-13T13:31:12-0500 with sha256 `31d31f4114ae025178cede169e4da36d9648c5c5dd6438c6eab15c73b7ee90f6`, in commit `2a7c4b4f2124`. The branch `prereg/levers-vacant-lot-trial-match` on the project's GitHub remote points at `2a7c4b4f2124`. The outcome is `confirmed`, decided at 2026-11-13T13:58:27-0500.

## The deciding number

The deciding number is the trial-like share of land use 11 lots in high-shooting tracts (a count ratio; no sampling interval). The recorded value is estimate = 0.417, n = 2678, trial_like_n = 1116. The registered condition that decides the verdict is "support_if: share in 0.18-0.45 and number in 400-1,500". `verify.py` accepts a rerun when each value lies within its tolerance: estimate within 0.0005, n within 0, trial_like_n within 0.

Smallest wrapper: lot_test.py reads and writes data/derived/levers/ inside the repository, so code/rerun.py copies its three input tables to work/levers/ and sets lot_test.D there. The registration's statement says 'about three in ten' and 'on the order of 20 shootings a year'; those are its central guesses. The verdict turns on the registered range of the share (0.18 to 0.45) and of the count (400 to 1,500). The rerun also prints the shootings a year within 300 m of the trial-like lots (388.0), from which the outcome derives 26.4 prevented a year at the trial's 6.8% effect; that figure decides nothing.

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

The folder `inputs/` holds 11 files (20.0 MB), each with its sha256 in `manifest.json`. They keep the paths they have in the repository. 
For each NYC Open Data source the manifest gives the dataset id, its `rowsUpdatedAt` at fetch time, the exact SoQL query, the fetch time and the sha256 of the cached response (and of its rows alone, which is what `--refetch` compares). The city rewrites these tables in place (see the project's audit `docs/underlay_drift.md`), so the cached response is the only copy of the data as they were used. 
The analysis code the rerun imports is copied into `code/`, with the git blob hash and last commit of each file in the manifest. The repository commit at packaging time was `47e2f54ff97e`. The registration names no seed and no resampling draw count; the deciding number is deterministic given the inputs.

## What is only pointed to

- `data/cache/socrata/ipu4-2q9a-c6868813a9236c5306426819.json` (4.5 MB, sha256 `330ad9654f054fca...`): cached Socrata response, ipu4-2q9a; the pages of this query total 63.7 MB, over the remaining cap.
- `data/cache/socrata/ipu4-2q9a-1a445c79476c26075a5803cc.json` (4.8 MB, sha256 `677af1fbc0f03c5b...`): cached Socrata response, ipu4-2q9a; the pages of this query total 63.7 MB, over the remaining cap.
- `data/cache/socrata/ipu4-2q9a-248fa6b4855775b192679ed7.json` (4.8 MB, sha256 `1164a71a1e0e0c9a...`): cached Socrata response, ipu4-2q9a; the pages of this query total 63.7 MB, over the remaining cap.
- `data/cache/socrata/ipu4-2q9a-1325dcfe5fd142b0d59ff7bf.json` (4.8 MB, sha256 `3516a42471abf754...`): cached Socrata response, ipu4-2q9a; the pages of this query total 63.7 MB, over the remaining cap.
- `data/cache/socrata/ipu4-2q9a-38a3e078f3f17f04f741098e.json` (4.8 MB, sha256 `5a89ff70406f527b...`): cached Socrata response, ipu4-2q9a; the pages of this query total 63.7 MB, over the remaining cap.
- `data/cache/socrata/ipu4-2q9a-cd8b1ffcc9abd4adbd2602be.json` (4.8 MB, sha256 `9837c21001723641...`): cached Socrata response, ipu4-2q9a; the pages of this query total 63.7 MB, over the remaining cap.
- `data/cache/socrata/ipu4-2q9a-b650cf65a56fc70d55429633.json` (4.8 MB, sha256 `7767796c855fcc57...`): cached Socrata response, ipu4-2q9a; the pages of this query total 63.7 MB, over the remaining cap.
- `data/cache/socrata/ipu4-2q9a-21e4e075710b29d342877cde.json` (4.8 MB, sha256 `0890bcea4d73a74a...`): cached Socrata response, ipu4-2q9a; the pages of this query total 63.7 MB, over the remaining cap.
- `data/cache/socrata/ipu4-2q9a-47bfe23209e828a3afe8af80.json` (4.7 MB, sha256 `35312eb3fca26d28...`): cached Socrata response, ipu4-2q9a; the pages of this query total 63.7 MB, over the remaining cap.
- `data/cache/socrata/ipu4-2q9a-b2c5e0ef17eb307f3e11e68f.json` (4.7 MB, sha256 `40d68f34cfe87804...`): cached Socrata response, ipu4-2q9a; the pages of this query total 63.7 MB, over the remaining cap.
- `data/cache/socrata/ipu4-2q9a-eddb33a7380e36c4a0755d49.json` (4.6 MB, sha256 `4c677448fb3d3de4...`): cached Socrata response, ipu4-2q9a; the pages of this query total 63.7 MB, over the remaining cap.
- `data/cache/socrata/ipu4-2q9a-86eaaa188b4936958b5797dc.json` (4.7 MB, sha256 `fc0a30cd4a28faed...`): cached Socrata response, ipu4-2q9a; the pages of this query total 63.7 MB, over the remaining cap.
- `data/cache/socrata/ipu4-2q9a-37118a4844ce6c8229080a01.json` (4.8 MB, sha256 `f5324d4aedc1e84a...`): cached Socrata response, ipu4-2q9a; the pages of this query total 63.7 MB, over the remaining cap.
- `data/cache/socrata/ipu4-2q9a-e0fc20cbf637a6e6dde04c9c.json` (2.0 MB, sha256 `defcbf7d7f494923...`): cached Socrata response, ipu4-2q9a; the pages of this query total 63.7 MB, over the remaining cap.
- `data/cache/socrata/ic3t-wcy2-1f77ab4f4e24a6b409001ca3.json` (4.4 MB, sha256 `6e6fbdb0b24fb044...`): cached Socrata response, ic3t-wcy2; the pages of this query total 20.1 MB, over the remaining cap.
- `data/cache/socrata/ic3t-wcy2-e0418a024bebfde8d4b2c8c5.json` (4.5 MB, sha256 `1caf630ea1d0f20c...`): cached Socrata response, ic3t-wcy2; the pages of this query total 20.1 MB, over the remaining cap.
- `data/cache/socrata/ic3t-wcy2-32957b9071f6708fdd03fcbf.json` (4.4 MB, sha256 `a50367f97f1c4a92...`): cached Socrata response, ic3t-wcy2; the pages of this query total 20.1 MB, over the remaining cap.
- `data/cache/socrata/ic3t-wcy2-0144e6dee087f28430dfe15a.json` (4.5 MB, sha256 `89fab5b0485da564...`): cached Socrata response, ic3t-wcy2; the pages of this query total 20.1 MB, over the remaining cap.
- `data/cache/socrata/ic3t-wcy2-5fcbeb4b623a0ad184b55fe5.json` (2.3 MB, sha256 `cf06a291f69dcb1b...`): cached Socrata response, ic3t-wcy2; the pages of this query total 20.1 MB, over the remaining cap.
- `data/cache/socrata/w9ak-ipjd-955f8b932e7ff4281a1c858b.json` (5.1 MB, sha256 `36f67fe587b5fc62...`): cached Socrata response, w9ak-ipjd; the pages of this query total 6.1 MB, over the remaining cap.
- `data/cache/socrata/w9ak-ipjd-c54ce1170aac9d7b0f8ccebd.json` (0.9 MB, sha256 `af375908005729f2...`): cached Socrata response, w9ak-ipjd; the pages of this query total 6.1 MB, over the remaining cap.
- `data/derived/neighbourhood/vacant_shootings_tracts.csv` (1.1 MB, sha256 `9963a7ed2287d7a9...`): tract shooting counts read by lots_fetch.py; over the 20 MB cap (1.1 MB).
- MapPLUTO lot polygons, DCP ArcGIS feature service: recorded in the outcome as a other source; no file is pinned.
- USDA NAIP 2022, New York flight, via Microsoft Planetary Computer STAC (collection naip): recorded in the outcome as a other source; no file is pinned.
- Moyer et al. 2019 AJPH, PMID 30496003: recorded in the outcome as a literature source; no file is pinned.
- `~/opt/nyc-concordance/levers/lu11_polygons.geojson` (13.0 MB, sha256 `a4b924f65193473e...`): MapPLUTO 26v2 lot polygons read by lot_ndvi.py. It is kept outside the repository and is not included.

## Tables this package cannot rebuild

The rerun starts from intermediate tables that it reads but cannot rebuild from what the package carries. Each is copied with its sha256; the inputs it was built from are listed with the place in `manifest.json` (under `not_rebuilt`) where each is pointed to by hash.

- `data/derived/levers/lots_records.csv` (sha256 `9f693f7793e255b0...`) was built by `analyses/levers/lots_fetch.py` from: NYC Open Data `64uk-42ks` (Primary Land Use Tax Lot Output (PLUTO)), 1 cached page(s), 6.5 MB, copied; NYC Open Data `p78i-pat6` (GreenThumb Garden Info), 1 cached page(s), 0.1 MB, copied; NYC Open Data `ipu4-2q9a` (DOB Permit Issuance), 14 cached page(s), 63.7 MB, pointed to by sha256 in `data[]`; NYC Open Data `rbx6-tga4` (DOB NOW: Build – Approved Permits), 2 cached page(s), 5.8 MB, copied; NYC Open Data `ic3t-wcy2` (DOB Job Application Filings), 5 cached page(s), 20.1 MB, pointed to by sha256 in `data[]`; NYC Open Data `w9ak-ipjd` (DOB NOW: Build – Job Application Filings), 2 cached page(s), 6.1 MB, pointed to by sha256 in `data[]`; NYC Open Data `i296-73x5` (DOB Stalled Construction Sites), 1 cached page(s), 3.5 MB, copied; `data/derived/neighbourhood/vacant_shootings_tracts.csv` (1.1 MB, sha256 `9963a7ed2287d7a9...`), pointed to by hash. It cannot be rebuilt here because the DOB BIS permit pages (63.7 MB) and the two DOB job-filing queries (26.2 MB) are over the cap.
- `data/derived/levers/shootings_2023_2025.csv` (sha256 `40060096e10dda1f...`) was built by `analyses/levers/lots_fetch.py` from: NYC Open Data `5ucz-vwe8` (Shootings (2006-Present)), 1 cached page(s), 0.5 MB, copied. It cannot be rebuilt here because it is built by the same upstream stage as lots_records.csv, which is not rerun.
- `data/derived/levers/lots_naip.csv` (sha256 `cf50d3308ced91a3...`) was built by `analyses/levers/lot_ndvi.py` from: `~/opt/nyc-concordance/levers/lu11_polygons.geojson` (13.0 MB, sha256 `a4b924f65193473e...`), pointed to by hash; USDA NAIP 2022 imagery, Microsoft Planetary Computer STAC collection naip (an external service; no file is pinned). It cannot be rebuilt here because it needs the NAIP image tiles and the MapPLUTO polygons, which are kept outside the repository.

## What a stranger needs

A stranger needs Python 3.12.10 with the packages in `requirements.txt` and this folder. The check reads only files inside the folder and makes no network request unless `--refetch` is given. Re-fetching the pinned sources needs network access but no key. The registration, outcome, revision history and referee report paths are in `manifest.json` under `claim`; the referee reports themselves are in the project repository.
