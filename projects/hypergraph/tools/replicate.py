#!/usr/bin/env python
"""Build a replication package for one registered claim.

    ~/.venvs/nyc-concordance/bin/python tools/replicate.py <claim-id> [--underlay] [--cap-mb 15]

Writes replication/<claim-id>/:

  manifest.json   claim (registration, its sha256, the commit that added it, the pushed prereg/<id> branch,
                  the outcome, its revision history, referee reports), code (scripts with git blob hashes and
                  commits, the repo commit, seeds and draw counts named in the registration), data (one entry
                  per source with the version information that exists for it and the sha256 of each cached
                  response), environment (Python, `uv pip freeze`, platform), inputs (every copied file with
                  its sha256) and the deciding number with its tolerance.
  inputs/         copies of the cached responses and derived tables the deciding number is computed from,
                  up to a total of --cap-mb; larger inputs are listed in the manifest by pointer only.
  code/           copies of the analysis code the rerun imports, and code/rerun.py, a wrapper that reruns the
                  deciding number from inputs/ without network access.
  run.sh          runs verify.py with the package's own Python (PYTHON=... to choose another).
  verify.py       checks every input hash, reruns the deciding number, compares it with the recorded outcome
                  within the stated tolerance and prints MATCH, DRIFT or MISMATCH. With --refetch it re-runs
                  the pinned Socrata queries and NOAA downloads and reports drift in the live sources.
  requirements.txt  pinned versions of the packages the rerun imports (full freeze in manifest.json).
  README.md       what is pinned, what is only pointed to, and what a stranger needs.
  underlay/       with --underlay: schemas.json, records.jsonl and manifest.json for an Underlay push.
                  Nothing is pushed.

Paths in every generated file are relative to the repo, to the package, or (for big files kept outside
Dropbox) to ~/opt/nyc-concordance. No API key is read, printed or written: the System graph cache holds
responses keyed by request path without the key.

Claims need a rerun recipe (RECIPES below) for code/rerun.py to exist. Without one the package still pins
the claim, the code and the inputs, and verify.py checks hashes only and says that no rerun is packaged.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
REG = ROOT / "claims" / "registered"
OUTC = ROOT / "claims" / "outcomes"
OPT = Path.home() / "opt" / "nyc-concordance"
VENV = Path.home() / ".venvs" / "nyc-concordance"
SYSGRAPH_RELEASE = "July 1, 2026 release (as named in the challenge brief; the API returns no version id)"
SOCRATA_DOMAINS = {"nyc-open-data": "https://data.cityofnewyork.us"}
DEFAULT_CAP_MB = 15

# --------------------------------------------------------------------------- per-claim rerun recipes
# Each recipe names the code the rerun imports (copied into code/), the derived tables it reads (copied into
# inputs/ as required inputs), pointers to upstream files it does not rerun, the wrapper, and the deciding
# number with its tolerance. Recorded values come from the outcome file unless stated.

HEAT_WRAPPER = r'''"""Rerun the deciding number of heat-shootings from the package's inputs.

The claim's script, analyses/heat/shootings.py, runs the primary model and every sensitivity analysis and
writes its results into the repository's data/derived/heat/. This wrapper is the smallest change that reruns
only the deciding number: it points the Socrata and NOAA caches at the package's inputs, blocks network access,
calls shootings.build() and shootings.nb_fit() unchanged, and prints the IRR per 5 C of Central Park TMAX.
"""
import argparse, json, sys
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser()
ap.add_argument("--inputs", default=str(PKG / "inputs"))
INP = Path(ap.parse_args().inputs).resolve()
sys.path.insert(0, str(PKG / "code"))

import requests  # noqa: E402


def _offline(*a, **k):
    raise RuntimeError(f"offline rerun: a pinned input is missing and the code tried to fetch {a[:1]}")


requests.get = _offline
from concord import noaa, socrata  # noqa: E402

socrata.CACHE = INP / "data" / "cache" / "socrata"
noaa.CACHE = INP / "data" / "cache" / "noaa"
from analyses.heat import shootings  # noqa: E402

df, _ = shootings.build()
d = df.dropna(subset=["TMAX"])
res, alpha = shootings.nb_fit(shootings.FORM.format(x="t5"), d)
r = shootings.irr(res, "t5")
print(json.dumps({"estimate": r["estimate"], "lo": r["lo"], "hi": r["hi"], "n": int(len(d)),
                  "n_incidents": int(d["n"].sum()), "alpha": alpha}))
'''

LEVERS_WRAPPER = r'''"""Rerun the deciding number of levers-vacant-lot-trial-match from the package's inputs.

The claim's script, analyses/levers/lot_test.py, reads three derived tables from data/derived/levers/ and
writes its results there. This wrapper copies the three tables from the package's inputs into work/, points
lot_test.D at that folder, calls lot_test.main() unchanged and prints the trial-like share and counts.
The upstream stages (lots_fetch.py, Socrata records; lot_ndvi.py, NAIP imagery) are not rerun.
"""
import argparse, contextlib, json, shutil, sys
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser()
ap.add_argument("--inputs", default=str(PKG / "inputs"))
INP = Path(ap.parse_args().inputs).resolve()
sys.path.insert(0, str(PKG / "code"))

import requests  # noqa: E402


def _offline(*a, **k):
    raise RuntimeError(f"offline rerun tried to fetch {a[:1]}")


requests.get = _offline
from analyses.levers import lot_test  # noqa: E402

work = PKG / "work" / "levers"
work.mkdir(parents=True, exist_ok=True)
for f in ("lots_records.csv", "lots_naip.csv", "shootings_2023_2025.csv"):
    shutil.copyfile(INP / "data" / "derived" / "levers" / f, work / f)
lot_test.D = work
with contextlib.redirect_stdout(sys.stderr):
    lot_test.main()
res = json.loads((work / "lot_test_results.json").read_text())
print(json.dumps({"estimate": res["trial_like_share"], "n": res["n_lu11_in_high_shooting_tracts"],
                  "trial_like_n": res["trial_like_n"],
                  "shootings_within_300m_per_year": res["shootings_within_300m_trial_like_per_year"]}))
'''

RECIPES = {
    "heat-shootings": {
        "code": ["concord/__init__.py", "concord/socrata.py", "concord/noaa.py", "analyses/__init__.py",
                 "analyses/heat/common.py", "analyses/heat/shootings.py"],
        "derived": [],
        "upstream_pointers": [],
        "wrapper": HEAT_WRAPPER,
        "wrapper_note": "Smallest wrapper: shootings.py main() also runs eight sensitivity models and writes into the "
                        "repository, so code/rerun.py calls its build() and nb_fit() for the primary model only.",
        "imports": ["numpy", "pandas", "statsmodels", "patsy", "scipy", "requests"],
        "deciding": {
            "what": "city_effect: IRR per 5 C of Central Park TMAX (lag 0), negative binomial GLM, robust HC0 95% CI",
            "keys": {"estimate": 1e-4, "lo": 1e-4, "hi": 1e-4, "n": 0},
            "extra_recorded": {},
            "decides": "support_if: lower 95% limit above 1.00",
        },
        "refetch_rerun": True,
        "trace": False,
    },
    "levers-vacant-lot-trial-match": {
        "code": ["analyses/__init__.py", "analyses/levers/lot_test.py"],
        "derived": ["data/derived/levers/lots_records.csv", "data/derived/levers/lots_naip.csv",
                    "data/derived/levers/shootings_2023_2025.csv"],
        "upstream_code": ["analyses/levers/lots_fetch.py", "analyses/levers/lot_ndvi.py", "analyses/levers/lot_polygons.py",
                          "analyses/levers/city_metrics.py"],
        "upstream_pointers": [
            {"path": "data/derived/levers/lots_sources.json", "role": "source records of lots_records.csv"},
            {"path": "data/derived/levers/lot_polygons_source.json", "role": "source record of the MapPLUTO polygons"},
            {"path": "data/derived/neighbourhood/vacant_shootings_tracts.csv", "role": "tract shooting counts read by lots_fetch.py"},
            {"opt": "levers/lu11_polygons.geojson", "role": "MapPLUTO 26v2 lot polygons read by lot_ndvi.py",
             "recorded": {"bytes": 13581012, "sha256": "a4b924f65193473ee9abe1bd9d4539831c3986220063a19e9469e790a998ced8",
                          "when": "package build of 13 November 2026, with the drive attached"}},
        ],
        "not_rebuilt": [
            {"table": "data/derived/levers/lots_records.csv", "built_by": "analyses/levers/lots_fetch.py",
             "built_from": ["socrata:64uk-42ks", "socrata:p78i-pat6", "socrata:ipu4-2q9a", "socrata:rbx6-tga4",
                            "socrata:ic3t-wcy2", "socrata:w9ak-ipjd", "socrata:i296-73x5",
                            "data/derived/neighbourhood/vacant_shootings_tracts.csv"],
             "why": "the DOB BIS permit pages (63.7 MB) and the two DOB job-filing queries (26.2 MB) are over the cap"},
            {"table": "data/derived/levers/shootings_2023_2025.csv", "built_by": "analyses/levers/lots_fetch.py",
             "built_from": ["socrata:5ucz-vwe8"],
             "why": "it is built by the same upstream stage as lots_records.csv, which is not rerun"},
            {"table": "data/derived/levers/lots_naip.csv", "built_by": "analyses/levers/lot_ndvi.py",
             "built_from": ["opt:levers/lu11_polygons.geojson",
                            "external:USDA NAIP 2022 imagery, Microsoft Planetary Computer STAC collection naip"],
             "why": "it needs the NAIP image tiles and the MapPLUTO polygons, which are kept outside the repository"},
        ],
        "wrapper": LEVERS_WRAPPER,
        "wrapper_note": "Smallest wrapper: lot_test.py reads and writes data/derived/levers/ inside the repository, so "
                        "code/rerun.py copies its three input tables to work/levers/ and sets lot_test.D there. "
                        "The registration's statement says 'about three in ten' and 'on the order of 20 shootings a year'; "
                        "those are its central guesses. The verdict turns on the registered range of the share (0.18 to 0.45) "
                        "and of the count (400 to 1,500). The rerun also prints the shootings a year within 300 m of the "
                        "trial-like lots (388.0), from which the outcome derives 26.4 prevented a year at the trial's 6.8% effect; "
                        "that figure decides nothing.",
        "imports": ["numpy", "pandas", "geopandas", "shapely", "pyproj", "pyogrio", "requests"],
        "deciding": {
            "what": "trial-like share of land use 11 lots in high-shooting tracts (a count ratio; no sampling interval)",
            "keys": {"estimate": 5e-4, "n": 0},
            "extra_recorded": {"trial_like_n": {"value": 1116, "tol": 0,
                                                "from": "outcome prediction_scored ('the number 1,116')"}},
            "decides": "support_if: share in 0.18-0.45 and number in 400-1,500",
        },
        "refetch_rerun": False,
        "trace": False,
    },
}


# Recipes added on 13 November 2026 (headline claims). Each wrapper is the smallest change that reruns the deciding
# number (and the claim's placebo where one is registered or named by the referee) from the package's inputs.

_W_HEAT_ED_SYNDROMIC = r'''"""Rerun the deciding number of heat-ed-syndromic from the package's inputs.

The claim's script, analyses/heat/ed_syndromic.py, fits the primary model, a spline curve, a piecewise model and a
yearly correlation, and writes five files into data/derived/heat/. This wrapper points its EHDP cache and the NOAA
cache at the package's inputs, blocks network access, calls load() and nb_fit() unchanged and repeats only the
lines of main() that build the model frame and fit the primary model.
"""
import argparse, json, sys
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser()
ap.add_argument("--inputs", default=str(PKG / "inputs"))
INP = Path(ap.parse_args().inputs).resolve()
sys.path.insert(0, str(PKG / "code"))

import requests  # noqa: E402


def _offline(*a, **k):
    raise RuntimeError(f"offline rerun: a pinned input is missing and the code tried to fetch {a[:1]}")


requests.get = _offline
from concord import noaa  # noqa: E402

noaa.CACHE = INP / "data" / "cache" / "noaa"
from analyses.heat import ed_syndromic as E  # noqa: E402
from analyses.heat.common import holidays  # noqa: E402

E.CACHE = INP / "data" / "derived" / "heat" / "ehdp"
ed, supp = E.load()
w, _ = noaa.daily("central_park")
d = ed.join(w[["TMAX", "TMIN", "PRCP"]], how="left")
d = d[d.index.month.isin([5, 6, 7, 8, 9])].dropna(subset=["TMAX", "HEAT_ED_VISIT_COUNT"]).copy()
d["n"] = d["HEAT_ED_VISIT_COUNT"].astype(int)
d["dow"] = d.index.day_of_week
d["month"] = d.index.month
d["year"] = d.index.year
d["hol"] = d.index.isin(holidays(str(d.index.min().date()), str(d.index.max().date()))).astype(int)
d["t5"] = d["TMAX"] / 5.0
res, alpha = E.nb_fit("n ~ t5 + C(dow) + C(month) + C(year) + hol", d)
r = E.irr(res, "t5")
print(json.dumps({"estimate": r["estimate"], "lo": r["lo"], "hi": r["hi"], "n": int(len(d)),
                  "n_visits": int(d["n"].sum()), "alpha": alpha}))
'''

RECIPES['heat-ed-syndromic'] = {'code': ['concord/__init__.py',
          'concord/noaa.py',
          'analyses/__init__.py',
          'analyses/heat/common.py',
          'analyses/heat/ed_syndromic.py'],
 'derived': [],
 'upstream_pointers': [],
 'wrapper': _W_HEAT_ED_SYNDROMIC,
 'wrapper_note': 'Smallest wrapper: ed_syndromic.py main() also fits a spline curve, a piecewise model and a yearly '
                 'correlation and writes five files into the repository, so code/rerun.py calls its load(), nb_fit() '
                 'and irr() unchanged and repeats the lines of main() that build the May-September model frame.',
 'imports': ['numpy', 'pandas', 'statsmodels', 'patsy', 'scipy', 'requests'],
 'deciding': {'what': 'city_effect: IRR per 5 C of Central Park TMAX (lag 0) for daily heat-syndrome ED visits, '
                      'May-September, negative binomial GLM with day of week, month, year and holiday, robust HC0 '
                      '95% CI',
              'keys': {'estimate': 0.0001, 'lo': 0.0001, 'hi': 0.0001, 'n': 0},
              'extra_recorded': {},
              'decides': 'prediction magnitude: IRR per 5 C between 1.5 and 5'},
 'slices': [{'path': 'data/cache/noaa/USW00094728.csv', 'columns': ['DATE', 'TMAX', 'TMIN', 'TAVG', 'PRCP', 'SNOW']}],
 'refetch_rerun': True}


_W_MOB_CRZ_TRAFFIC = r'''"""Rerun the deciding number of mob-crz-traffic, and its registered 2024 placebo, from the package's inputs.

The claim's script, analyses/mobility/crz_traffic.py, fits the speed and trip difference-in-differences, the
by-industry models and two descriptive series, writes five tables and a figure into the repository. This wrapper
points the Socrata cache at the package's inputs, blocks network access, and repeats only the lines of main()
that build the speed and trip frames, calling did() and placebo() unchanged.
"""
import argparse, json, sys
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser()
ap.add_argument("--inputs", default=str(PKG / "inputs"))
INP = Path(ap.parse_args().inputs).resolve()
sys.path.insert(0, str(PKG / "code"))

import requests  # noqa: E402


def _offline(*a, **k):
    raise RuntimeError(f"offline rerun: a pinned input is missing and the code tried to fetch {a[:1]}")


requests.get = _offline
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from concord import socrata  # noqa: E402

socrata.CACHE = INP / "data" / "cache" / "socrata"
from analyses.mobility import crz_traffic as C  # noqa: E402
from analyses.mobility.common import nys  # noqa: E402

rows, _ = nys("6p29-6xqn", select="month, zone, zonal_speed", order="month")
sp = pd.DataFrame(rows)
sp["month"] = pd.to_datetime(sp["month"])
sp["speed"] = sp["zonal_speed"].astype(float)
sp = sp.rename(columns={"zone": "area"})
w = sp[sp["month"] >= "2023-01-01"]
g = w[w["area"].isin(["CBD", "Greater NYC"])]
s = C.did(g, "CBD", "speed")
sp_pl = C.placebo(g, "CBD", "speed")

zrows, _ = nys("yfdc-w5jh", select="taxi_zone")
cbd = {int(r["taxi_zone"]) for r in zrows}
rows, _ = socrata.query("c5iv-bn4s", select="metric_month, industry, locationid, sum(trip_count) as n",
                        where="metric_month >= '2023-01-01'", group="metric_month, industry, locationid")
t = pd.DataFrame(rows)
t["n"] = t["n"].astype(float)
t["locationid"] = pd.to_numeric(t["locationid"], errors="coerce")
t["month"] = pd.to_datetime(t["metric_month"])
t["area"] = np.where(t["locationid"].isin(cbd), "CBD", "Outside CBD")
tm = t.groupby(["month", "area"], as_index=False)["n"].sum()
tr = C.did(tm, "CBD", "n")
tr_pl = C.placebo(tm, "CBD", "n")
print(json.dumps({"estimate": s["pct"], "lo": s["lo_pct"], "hi": s["hi_pct"], "n": s["n"],
                  "trips_pct": tr["pct"], "trips_n": tr["n"],
                  "placebo2024_speed_pct": sp_pl["pct"], "placebo2024_trips_pct": tr_pl["pct"]}))
'''

RECIPES['mob-crz-traffic'] = {'code': ['concord/__init__.py',
          'concord/socrata.py',
          'analyses/__init__.py',
          'analyses/mobility/__init__.py',
          'analyses/mobility/common.py',
          'analyses/mobility/crz_traffic.py'],
 'derived': [],
 'upstream_pointers': [],
 'wrapper': _W_MOB_CRZ_TRAFFIC,
 'wrapper_note': 'Smallest wrapper: crz_traffic.py main() also fits by-industry models, summarises two descriptive '
                 'series (VMT, CRZ entries) and writes tables and a figure into the repository, so code/rerun.py '
                 'repeats the lines of main() that build the speed and trip frames and calls did() and placebo() '
                 'unchanged. The outcome records the city effect to two decimals, so the tolerance is 0.005 '
                 'percentage points. The trip estimate is printed and checked too, because the registered prediction '
                 'covers it.',
 'imports': ['numpy', 'pandas', 'statsmodels', 'patsy', 'scipy', 'requests', 'matplotlib'],
 'deciding': {'what': 'city_effect: percent change in CBD taxi and FHV speed relative to Greater NYC, 2025 against '
                      '2023-24, OLS difference-in-differences on log monthly speed with area, calendar month and '
                      'year, HAC (3 lags) 95% CI',
              'keys': {'estimate': 0.005, 'lo': 0.005, 'hi': 0.005, 'n': 0},
              'extra_recorded': {'trips_pct': {'value': -9.8,
                                               'tol': 0.05,
                                               'from': "outcome prediction_scored ('the estimate is -9.8%')"},
                                 'trips_n': {'value': 90,
                                             'tol': 0,
                                             'from': 'data/derived/mobility/crz_traffic_results.json, '
                                                     'trips_CBD_vs_outside.n'}},
              'placebo': {'placebo2024_speed_pct': {'value': -0.8,
                                                    'tol': 0.05,
                                                    'from': "outcome notes ('the 2024 placebo for speed is null "
                                                            "(-0.8%)')",
                                                    'what': 'registered pre-trend check: the same speed model with '
                                                            'post = Jan 2024 on 2023-2024 only'},
                          'placebo2024_trips_pct': {'value': -4.5,
                                                    'tol': 0.05,
                                                    'from': "outcome prediction_scored ('the 2024 placebo also shows "
                                                            "a CBD decline (-4.5%')",
                                                    'what': 'registered pre-trend check for trips, post = Jan 2024 '
                                                            'on 2023-2024 only'}},
              'decides': 'prediction magnitude: speed +5% to +15% and trips -3% to -12%'},
 'refetch_rerun': True}


_W_STREET_BUSWAY14_M14_SPEED = r'''"""Rerun the deciding number of street-busway14-m14-speed, and its 119 placebo DiDs, from the package's inputs.

The claim's script, analyses/street_space/bus.py, has two stages: design() computes the placebo DiDs (each other
Manhattan route as if treated, seasons 2021-2023) and writes bus_design.json; final() reads it, computes the M14
DiD with the placebo standard deviation as its standard error and writes bus_final.json. This wrapper points the
Socrata cache at the package's inputs, blocks network access, sets bus.DER to work/street_space inside the
package, and calls design() and final() unchanged.
"""
import argparse, contextlib, json, sys
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser()
ap.add_argument("--inputs", default=str(PKG / "inputs"))
INP = Path(ap.parse_args().inputs).resolve()
sys.path.insert(0, str(PKG / "code"))

import requests  # noqa: E402


def _offline(*a, **k):
    raise RuntimeError(f"offline rerun: a pinned input is missing and the code tried to fetch {a[:1]}")


requests.get = _offline
from concord import socrata  # noqa: E402

socrata.CACHE = INP / "data" / "cache" / "socrata"
from analyses.street_space import bus  # noqa: E402

work = PKG / "work" / "street_space"
work.mkdir(parents=True, exist_ok=True)
bus.DER = work
with contextlib.redirect_stdout(sys.stderr):
    bus.design()
    bus.final()
d = json.loads((work / "bus_design.json").read_text())
f = json.loads((work / "bus_final.json").read_text())
import numpy as np  # noqa: E402
m14_log = float(np.log(1 + f["did_pct"] / 100))
print(json.dumps({"estimate": f["did_pct"], "lo": f["lo_pct"], "hi": f["hi_pct"], "n": f["n_controls"],
                  "se_log": f["se_log"], "placebo_sd_log": d["sd_log"], "placebo_n": d["n"],
                  "placebo_n_as_large": int(sum(p["did_log"] >= m14_log for p in d["placebo"]))}))
'''

RECIPES['street-busway14-m14-speed'] = {'code': ['concord/__init__.py',
          'concord/socrata.py',
          'analyses/__init__.py',
          'analyses/mobility/__init__.py',
          'analyses/mobility/common.py',
          'analyses/street_space/common.py',
          'analyses/street_space/bus.py'],
 'derived': [],
 'upstream_pointers': [],
 'wrapper': _W_STREET_BUSWAY14_M14_SPEED,
 'wrapper_note': 'Smallest wrapper: bus.py reads and writes data/derived/street_space/ inside the repository, so '
                 'code/rerun.py sets bus.DER to work/street_space inside the package and calls design() and final() '
                 'unchanged. The standard error of the M14 DiD is the standard deviation of the 119 placebo DiDs, so '
                 'the placebo stage is part of the deciding number.',
 'imports': ['numpy', 'pandas', 'requests', 'matplotlib'],
 'deciding': {'what': 'city_effect: percent change in M14A+M14D weekday speed, Oct 2019-Feb 2020 against Jul-Sep '
                      '2019, minus the mean change of 39 other Manhattan routes (DiD on log speed), with the 95% '
                      'interval from the placebo SD',
              'keys': {'estimate': 0.0005, 'lo': 0.0005, 'hi': 0.0005, 'n': 0, 'se_log': 1e-09},
              'extra_recorded': {},
              'placebo': {'placebo_sd_log': {'value': 0.0185421743139463,
                                             'tol': 1e-09,
                                             'from': 'outcome city_effect.se_log (= sd of the placebo DiDs)',
                                             'what': 'registered null distribution: SD of the 119 placebo DiDs (each '
                                                     'other Manhattan route as if treated, seasons 2021-2023)'},
                          'placebo_n': {'value': 119,
                                        'tol': 0,
                                        'from': "registration plan ('119 placebo DiDs')",
                                        'what': 'number of placebo DiDs'},
                          'placebo_n_as_large': {'value': 2,
                                                 'tol': 0,
                                                 'from': 'outcome notes_referee and '
                                                         "critique/street-busway14-m14-speed.md ('2 of 119')",
                                                 'what': 'placebo DiDs at least as large as the M14 estimate '
                                                         '(signed, as the referee counted them)'}},
              'decides': 'support_if: DiD >= 4% and lower 95% limit above 0'},
 'refetch_rerun': True}


_W_EMS_TRAFFIC_SHARE_2019_2026 = r'''"""Rerun the deciding number of ems-traffic-share-2019-2026 from the package's inputs.

The claim's script, analyses/ems_response/run_tests.py, runs three registered tests and writes results.json. The
deciding number is T2's S1, from lib.traffic_share(): the share of the January-September 2019 to 2026 rise in
Manhattan life-threatening EMS travel time that the change in taxi pace accounts for at an elasticity of 1. This
wrapper points lib.DER and lib.CONG at the package's inputs, replaces lib.taxi_hourly() by a copy that reads the
named files in the order the original's globs give (it reads every taxi table in two folders, 29 MB, but only the
files below hold rows in the two windows, and the first-occurrence rule of drop_duplicates picks the same rows),
and calls lib.traffic_share() unchanged (400 day-block bootstrap draws, seed 20261113). S1 and its interval do not
depend on the elasticity argument, because the bootstrap draws are taken before the elasticity draws.
"""
import argparse, json, sys
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser()
ap.add_argument("--inputs", default=str(PKG / "inputs"))
INP = Path(ap.parse_args().inputs).resolve()
sys.path.insert(0, str(PKG / "code"))

import requests  # noqa: E402


def _offline(*a, **k):
    raise RuntimeError(f"offline rerun: a pinned input is missing and the code tried to fetch {a[:1]}")


requests.get = _offline
import pandas as pd  # noqa: E402
from analyses.ems_response import lib  # noqa: E402

lib.DER = INP / "data" / "derived" / "ems_response"
lib.CONG = INP / "data" / "derived" / "congestion"
TAXI = ['data/derived/ems_response/taxi_hourly_2019-01_2020-02.csv', 'data/derived/ems_response/taxi_hourly_2026-01_2026-06.csv', 'data/derived/ems_response/taxi_hourly_2026-07_2026-09.csv', 'data/derived/ems_response/taxi_parts/2019-01.csv', 'data/derived/ems_response/taxi_parts/2019-02.csv', 'data/derived/ems_response/taxi_parts/2019-03.csv', 'data/derived/ems_response/taxi_parts/2019-04.csv', 'data/derived/ems_response/taxi_parts/2019-05.csv', 'data/derived/ems_response/taxi_parts/2019-06.csv', 'data/derived/ems_response/taxi_parts/2019-07.csv', 'data/derived/ems_response/taxi_parts/2019-08.csv', 'data/derived/ems_response/taxi_parts/2019-09.csv', 'data/derived/ems_response/taxi_parts/2026-01.csv', 'data/derived/ems_response/taxi_parts/2026-02.csv', 'data/derived/ems_response/taxi_parts/2026-03.csv', 'data/derived/ems_response/taxi_parts/2026-04.csv', 'data/derived/ems_response/taxi_parts/2026-05.csv', 'data/derived/ems_response/taxi_parts/2026-06.csv', 'data/derived/ems_response/taxi_parts/2026-07.csv', 'data/derived/ems_response/taxi_parts/2026-08.csv', 'data/derived/ems_response/taxi_parts/2026-09.csv', 'data/derived/congestion/taxi_speed_2025-01_2026-06.csv']


def taxi_hourly():
    t = pd.concat([pd.read_csv(INP / f) for f in TAXI])
    t["d"] = pd.to_datetime(t["d"])
    return t.drop_duplicates(["d", "hh", "area"]).reset_index(drop=True)


lib.taxi_hourly = taxi_hourly
r = lib.traffic_share(1.0, 0.0)
print(json.dumps({"estimate": r["S1"], "lo": r["S1_ci"][0], "hi": r["S1_ci"][1], "n": 2,
                  "D_pct": r["D_pct"], "pace_change_pct": r["pace_change_pct"]}))
'''

RECIPES['ems-traffic-share-2019-2026'] = {'code': ['analyses/__init__.py',
          'analyses/ems_response/__init__.py',
          'analyses/ems_response/common.py',
          'analyses/ems_response/lib.py'],
 'derived': [],
 'slices': [{'path': 'data/derived/congestion/ems_2019.csv',
             'date_column': 'd',
             'from': '2019-01-01',
             'to': '2019-09-30'},
            {'path': 'data/derived/ems_response/taxi_hourly_2019-01_2020-02.csv',
             'date_column': 'd',
             'from': '2019-01-01',
             'to': '2019-09-30'},
            {'path': 'data/derived/congestion/taxi_speed_2025-01_2026-06.csv',
             'date_column': 'd',
             'from': '2026-01-01',
             'to': '2026-09-30'}],
 'upstream_code': ['analyses/ems_response/run_tests.py',
                   'analyses/ems_response/taxi_hourly.py',
                   'analyses/congestion/ems_fetch.py',
                   'analyses/congestion/taxi_speed.py'],
 'upstream_pointers': [{'path': 'data/derived/congestion/ems_sources.json',
                        'role': 'SoQL and rowsUpdatedAt of the EMS hourly tables'},
                       {'path': 'data/derived/ems_response/taxi_files_2019-01_2020-02.json',
                        'role': 'TLC file versions of taxi_hourly_2019-01_2020-02.csv'},
                       {'path': 'data/derived/ems_response/taxi_files_2026-01_2026-06.json',
                        'role': 'TLC file versions of taxi_hourly_2026-01_2026-06.csv'},
                       {'path': 'data/derived/ems_response/taxi_files_2026-07_2026-09.json',
                        'role': 'TLC file versions of taxi_hourly_2026-07_2026-09.csv'},
                       {'path': 'data/derived/reproduction/mmr_cbd_speed_files.json',
                        'role': 'TLC file versions of the congestion taxi_speed tables'}],
 'not_rebuilt': [{'table': 'data/derived/congestion/ems_2019.csv and ems_2026.csv',
                  'built_by': 'analyses/congestion/ems_fetch.py',
                  'built_from': ['socrata:76xm-jjuj', 'data/derived/congestion/ems_sources.json'],
                  'why': 'the hourly EMS sums were aggregated by SoQL queries whose responses are not cached under '
                         "the outcome's query; the queries and rowsUpdatedAt are in ems_sources.json"},
                 {'table': 'data/derived/ems_response/taxi_hourly_*.csv and taxi_parts/*.csv (2019 and 2026 months)',
                  'built_by': 'analyses/ems_response/taxi_hourly.py',
                  'built_from': ['external:TLC yellow taxi trip record parquet files for 2019-01 to 2019-09 and '
                                 '2026-01 to 2026-09 (about 50 to 140 MB each), kept in ~/opt/nyc-concordance; URLs, '
                                 "ETags and Last-Modified are in the outcome's sources and in the taxi_files_*.json "
                                 'records',
                                 'data/derived/ems_response/taxi_files_2019-01_2020-02.json',
                                 'data/derived/ems_response/taxi_files_2026-01_2026-06.json',
                                 'data/derived/ems_response/taxi_files_2026-07_2026-09.json'],
                  'why': 'the TLC trip files total several GB and the drive that holds them was detached at this '
                         'build'},
                 {'table': 'data/derived/congestion/taxi_speed_2025-01_2026-06.csv',
                  'built_by': 'analyses/congestion/taxi_speed.py',
                  'built_from': ['external:TLC yellow taxi trip record parquet files, 2025-01 to 2026-06',
                                 'data/derived/reproduction/mmr_cbd_speed_files.json'],
                  'why': 'it is built from TLC trip files that are not carried'}],
 'wrapper': _W_EMS_TRAFFIC_SHARE_2019_2026,
 'wrapper_note': 'Smallest wrapper: run_tests.py runs three tests and writes results.json, so code/rerun.py calls '
                 'lib.traffic_share() unchanged for T2 only. lib.taxi_hourly() globs every taxi table in two folders '
                 "(29 MB); the wrapper's copy reads, in the same order, only the files that hold rows in "
                 'January-September 2019 and 2026, three of them sliced to those months. The rows the rerun uses are '
                 'the same, because drop_duplicates keeps the first occurrence and the omitted files hold no rows in '
                 'the windows.',
 'imports': ['numpy', 'pandas', 'requests'],
 'deciding': {'what': 'city_effect: S1, share of the January-September 2019 to 2026 rise in Manhattan '
                      'life-threatening EMS travel time accounted for by the taxi pace change at elasticity 1, with '
                      'a day-block bootstrap 95% interval (400 draws, seed 20261113)',
              'keys': {'estimate': 0.0001, 'lo': 0.0001, 'hi': 0.0001, 'n': 0},
              'extra_recorded': {},
              'decides': 'support_if: upper 95% limit of S1 below 0.5 and estimate within 0.05 to 0.45'},
 'refetch_rerun': False}


_W_FOOD_SUPERMARKET_DIABETES_ZCTA = r'''"""Rerun the deciding number of food-supermarket-diabetes-zcta from the package's inputs.

The claim's script, analyses/health_gaps/food_access.py, builds a ZCTA table from Census files kept in
~/opt/nyc-concordance/census (zctas()), the Retail Food Stores query (stores()) and the SPARCS PQI query (pqi()),
fits ten models and writes into data/derived/health_gaps/. This wrapper reruns stores() and pqi() unchanged from the
cached Socrata responses, takes the Census columns that zctas() produced from the derived table food_zcta.csv
(the Census files are not carried), repeats the merge and filter of main() and fits the primary model with fit()
and coef() unchanged. It also prints the unadjusted ratio.
"""
import argparse, json, sys
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser()
ap.add_argument("--inputs", default=str(PKG / "inputs"))
INP = Path(ap.parse_args().inputs).resolve()
sys.path.insert(0, str(PKG / "code"))

import requests  # noqa: E402


def _offline(*a, **k):
    raise RuntimeError(f"offline rerun: a pinned input is missing and the code tried to fetch {a[:1]}")


requests.get = _offline
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from concord import socrata  # noqa: E402

socrata.CACHE = INP / "data" / "cache" / "socrata"
from analyses.health_gaps import food_access as F  # noqa: E402

CENSUS = ["zcta", "county", "ALAND", "pop", "adults", "density", "poverty", "income", "med_age", "black", "hisp",
          "nocar", "land_km2"]
z = pd.read_csv(INP / "data" / "derived" / "health_gaps" / "food_zcta.csv", dtype={"zcta": str})[CENSUS]
st, _ = F.stores()
pq, _, years, pqis = F.pqi()
d = z.merge(st, on="zcta", how="left").merge(pq, on="zcta", how="inner")
for c in ("stores_all", "super6k", "super10k"):
    d[c] = d[c].fillna(0)
d = d[(d.adults >= 5000) & (d.obs > 0) & (d.exp > 0)].dropna(subset=["poverty", "income", "med_age"])
d["y"] = np.log(d.obs / d.exp)
d["x"] = np.log2((d.super6k + 0.5) / d["pop"] * 1e4)
d["ldens"] = np.log2(d.density)
d["linc"] = np.log2(d.income)
base = "ldens + poverty + linc + med_age"
p = F.coef(F.fit(d, f"x + {base}"), "x")
u = F.coef(F.fit(d, "x"), "x")
print(json.dumps({"estimate": p["ratio"], "lo": p["lo"], "hi": p["hi"], "n": p["n"], "years": years,
                  "unadjusted": u["ratio"], "unadjusted_lo": u["lo"], "unadjusted_hi": u["hi"]}))
'''

RECIPES['food-supermarket-diabetes-zcta'] = {'code': ['concord/__init__.py',
          'concord/socrata.py',
          'analyses/__init__.py',
          'analyses/health_gaps/__init__.py',
          'analyses/health_gaps/common.py',
          'analyses/health_gaps/food_access.py'],
 'derived': ['data/derived/health_gaps/food_zcta.csv'],
 'upstream_pointers': [{'opt': 'census/zcta_county_rel.txt', 'role': 'Census or ACS file read by food_access.zctas() to build food_zcta.csv'}, {'opt': 'census/gaz_zcta_2020.zip', 'role': 'Census or ACS file read by food_access.zctas() to build food_zcta.csv'}, {'opt': 'census/acsdt5y2023-b01003.dat', 'role': 'Census or ACS file read by food_access.zctas() to build food_zcta.csv'}, {'opt': 'census/acsdt5y2023-b19013.dat', 'role': 'Census or ACS file read by food_access.zctas() to build food_zcta.csv'}, {'opt': 'census/acsdt5y2023-b17001.dat', 'role': 'Census or ACS file read by food_access.zctas() to build food_zcta.csv'}, {'opt': 'census/acsdt5y2023-b01002.dat', 'role': 'Census or ACS file read by food_access.zctas() to build food_zcta.csv'}, {'opt': 'census/acsdt5y2023-b03002.dat', 'role': 'Census or ACS file read by food_access.zctas() to build food_zcta.csv'}, {'opt': 'census/acsdt5y2023-b08201.dat', 'role': 'Census or ACS file read by food_access.zctas() to build food_zcta.csv'}, {'opt': 'census/acsdt5y2023-b09021.dat', 'role': 'Census or ACS file read by food_access.zctas() to build food_zcta.csv'}],
 'wrapper': _W_FOOD_SUPERMARKET_DIABETES_ZCTA,
 'wrapper_note': 'Smallest wrapper: food_access.py main() downloads Census files into ~/opt/nyc-concordance/census, '
                 'fits ten models and writes into the repository. code/rerun.py reruns stores() and pqi() unchanged '
                 'from the cached Socrata responses, takes the Census columns from the derived table food_zcta.csv, '
                 'repeats the merge and filter of main() and calls fit() and coef() unchanged for the primary model. '
                 "The referee's negative control (critique/food-supermarket-diabetes-zcta.md) uses other admission "
                 'measures and is not rerun here.',
 'imports': ['numpy', 'pandas', 'statsmodels', 'patsy', 'scipy', 'requests'],
 'deciding': {'what': 'city_effect: ratio of the diabetes admission O/E (SPARCS PQI 01, 03, 14, 16, 2021-2023) per '
                      'doubling of supermarkets >= 6,000 sq ft per 10,000 residents, adjusted, 168 ZCTAs, WLS by '
                      'population, HC3 95% CI',
              'keys': {'estimate': 0.0001, 'lo': 0.0001, 'hi': 0.0001, 'n': 0},
              'extra_recorded': {},
              'decides': 'support_if: primary ratio with 95% interval inside (0.90, 1.10) and estimate at or above '
                         '0.95'},
 'not_rebuilt': [{'table': 'data/derived/health_gaps/food_zcta.csv',
                  'built_by': 'analyses/health_gaps/food_access.py',
                  'built_from': ['opt:census/zcta_county_rel.txt', 'opt:census/gaz_zcta_2020.zip', 'opt:census/acsdt5y2023-b01003.dat', 'opt:census/acsdt5y2023-b19013.dat', 'opt:census/acsdt5y2023-b17001.dat', 'opt:census/acsdt5y2023-b01002.dat', 'opt:census/acsdt5y2023-b03002.dat', 'opt:census/acsdt5y2023-b08201.dat', 'opt:census/acsdt5y2023-b09021.dat'],
                  'why': 'its Census columns come from national Census and ACS files kept in '
                         '~/opt/nyc-concordance/census (about 400 MB together), outside the repository; the rerun '
                         'uses only those columns of the table and recomputes the store and PQI columns'}],
 'refetch_rerun': False}


_W_BRIDGE_HEAT_SHOOTINGS_EMS = r'''"""Rerun the deciding number of bridge-heat-shootings-ems from the package's inputs.

The claim's script, analyses/bridges/ems_shot.py, builds the heat-shootings daily frame (analyses/heat/shootings.py
build()), adds daily FDNY EMS dispatch counts (ems_daily()), fits a link model, the endpoint model and four
sensitivity models, and writes into data/derived/bridges/. It reads the composed prediction from
composed_predictions.json, written by analyses/bridges/compose.py. This wrapper points the Socrata and NOAA caches at
the package's inputs, blocks network access, reruns compose.py's bridge1() and bridge2() with its seed and draw count
(bridge1 first, as in compose.main(), since both draw from one generator), calls build(), ems_daily(), nb_fit(), irr()
and compat() unchanged, and prints the endpoint IRR, its compatibility with the composed prediction, and the STAB
contrast that the registration names as a check outside the causal chain.
"""
import argparse, json, sys
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser()
ap.add_argument("--inputs", default=str(PKG / "inputs"))
INP = Path(ap.parse_args().inputs).resolve()
sys.path.insert(0, str(PKG / "code"))

import requests  # noqa: E402


def _offline(*a, **k):
    raise RuntimeError(f"offline rerun: a pinned input is missing and the code tried to fetch {a[:1]}")


requests.get = _offline
import numpy as np  # noqa: E402
from concord import noaa, socrata  # noqa: E402

socrata.CACHE = INP / "data" / "cache" / "socrata"
noaa.CACHE = INP / "data" / "cache" / "noaa"
from analyses.bridges import compose, ems_shot as B  # noqa: E402
from analyses.bridges.common import SEED  # noqa: E402

rng = np.random.default_rng(SEED)
compose.bridge1(rng)
comp = compose.bridge2(rng)["composed_irr_per5C"]

df, _ = B.build()
w, _ = B.ems_daily()
for c in ("SHOT", "T-SHOT", "STAB"):
    df[c] = w[c].reindex(df.index).fillna(0).astype(int) if c in w else 0
df = df.dropna(subset=["TMAX"])
r, alpha = B.nb_fit(B.FORM.format(x="t5").replace("n ~", "SHOT ~"), df)
e = B.irr(r, "t5")
c = B.compat(float(r.params["t5"]), float(r.bse["t5"]), comp["mean_log"], comp["sd_log"])
s = B.irr(B.nb_fit(B.FORM.format(x="t5").replace("n ~", "STAB ~"), df)[0], "t5")
print(json.dumps({"estimate": e["estimate"], "lo": e["lo"], "hi": e["hi"], "n": int(len(df)), "alpha": alpha,
                  "composed_median": comp["median"], "compat_z": c["z"], "stab_contrast": s["estimate"],
                  "stab_contrast_lo": s["lo"], "stab_contrast_hi": s["hi"]}))
'''

RECIPES['bridge-heat-shootings-ems'] = {'code': ['concord/__init__.py',
          'concord/socrata.py',
          'concord/noaa.py',
          'analyses/__init__.py',
          'analyses/heat/common.py',
          'analyses/heat/shootings.py',
          'analyses/bridges/__init__.py',
          'analyses/bridges/common.py',
          'analyses/bridges/compose.py',
          'analyses/bridges/ems_shot.py'],
 'derived': [],
 'upstream_pointers': [],
 'wrapper': _W_BRIDGE_HEAT_SHOOTINGS_EMS,
 'wrapper_note': 'Smallest wrapper: ems_shot.py main() also fits a link model and four sensitivity models and writes '
                 'into the repository, and it reads the composed prediction from a file written by compose.py. '
                 "code/rerun.py recomputes the composed prediction with compose.py's own functions, seed (20261112) "
                 'and draw count (200,000), then calls build(), ems_daily(), nb_fit(), irr() and compat() unchanged '
                 'for the endpoint and for the STAB contrast. The verdict turns on whether the endpoint IRR is '
                 'compatible with the composed prediction (|z| < 1.96); the recorded z is 0.41.',
 'imports': ['numpy', 'pandas', 'statsmodels', 'patsy', 'scipy', 'requests'],
 'deciding': {'what': 'city_effect: IRR per 5 C of Central Park TMAX (lag 0) for daily FDNY EMS SHOT dispatches, '
                      '2006 to August 2026, negative binomial GLM as in heat-shootings, robust HC0 95% CI; and its '
                      'compatibility z with the composed prediction',
              'keys': {'estimate': 0.0001, 'lo': 0.0001, 'hi': 0.0001, 'n': 0},
              'extra_recorded': {'compat_z': {'value': 0.4149437146358164,
                                              'tol': 0.01,
                                              'from': 'outcome endpoint_test.z'}},
              'placebo': {'stab_contrast': {'value': 1.0759499384976088,
                                            'tol': 0.0001,
                                            'from': 'outcome notes (1.076) and data/derived/bridges/ems_results.json '
                                                    'sensitivity.STAB_contrast',
                                            'what': 'IRR per 5 C for STAB dispatches, the registered contrast '
                                                    'outside the heat-shooting chain'}},
              'decides': 'endpoint IRR compatible with the composed prediction 1.099 (1.049 to 1.148), |z| < 1.96'},
 'slices': [{'path': 'data/cache/noaa/USW00094728.csv', 'columns': ['DATE', 'TMAX', 'TMIN', 'TAVG', 'PRCP', 'SNOW']}],
 'refetch_rerun': True}


_W_FURTHER_TIDAL_FLOODING_TREND = r'''"""Rerun the deciding number of further-tidal-flooding-trend from the package's inputs.

The claim's script, analyses/round2_tidal/analyse.py, is a flat script with no functions to import: on import it
builds a daily panel, runs the primary model, two shifted-tide placebos and fifteen checks with block bootstraps,
and writes results.json and daily_panel.csv into data/derived/round2/tidal_trend/. This wrapper executes the
script's own source with four textual changes, each asserted to match exactly once:

1. D points at the package's inputs.
2. The block that aggregates complaints_by_day_zip.json (27.8 MB, not carried) into daily series is replaced by
   reading the complaint series the deciding models and the sample counts use (C3_t, C3_p, C1_t, C4_t) from
   daily_panel.csv, the panel the script wrote.
   The tide, precipitation, dry-day and knot columns are rebuilt from the carried tide and precipitation files.
3. run() does not write results.json.
4. The script stops after the primary model and the two registered shifted-tide placebos. The random generator
   (seed 20261113) is drawn in the same order as in the full script up to that point, so the bootstrap intervals
   are those of the full run.
"""
import argparse, contextlib, json, sys
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser()
ap.add_argument("--inputs", default=str(PKG / "inputs"))
ap.add_argument("--nboot", type=int, default=1000, help="block-bootstrap replicates (registered: 1,000)")
a = ap.parse_args()
INP = Path(a.inputs).resolve()
sys.path.insert(0, str(PKG / "code"))

import requests  # noqa: E402


def _offline(*a, **k):
    raise RuntimeError(f"offline rerun: a pinned input is missing and the code tried to fetch {a[:1]}")


requests.get = _offline

src = (PKG / "code" / "analyses" / "round2_tidal" / "analyse.py").read_text()


def sub(s, old, new):
    assert s.count(old) == 1, f"analyse.py has changed: {old[:60]!r} found {s.count(old)} times"
    return s.replace(old, new)


src = sub(src, 'D = ROOT / "data" / "derived" / "round2" / "tidal_trend"', 'D = INP / "data" / "derived" / "round2" / "tidal_trend"')
i = src.index('C = json.load(open(D / "complaints_by_day_zip.json"))')
j = src.index('df.loc[df.year >= 2020, "C3_t"] = b3t[df.year >= 2020]; df.loc[df.year >= 2020, "C3_p"] = b3p[df.year >= 2020]\n')
j += len('df.loc[df.year >= 2020, "C3_t"] = b3t[df.year >= 2020]; df.loc[df.year >= 2020, "C3_p"] = b3p[df.year >= 2020]\n')
src = src[:i] + ('_P = pd.read_csv(D / "daily_panel.csv", index_col=0, parse_dates=True)\n'
                 'for _c in ("C3_t", "C3_p", "C1_t", "C4_t"): df[_c] = _P[_c].reindex(days)\n') + src[j:]
src = sub(src, '    json.dump(res, open(D / "results.json", "w"), indent=1, default=float)\n', '    pass\n')
src = src[:src.index('    for k in (30, 40, 45): run(')]
g = {"__name__": "analyse_rerun", "__file__": str(PKG / "code" / "analyses" / "round2_tidal" / "analyse.py"), "INP": INP}
sys.argv = [sys.argv[0], str(a.nboot), "0"]
with contextlib.redirect_stdout(sys.stderr):
    exec(compile(src, "analyses/round2_tidal/analyse.py (rerun)", "exec"), g)
res = g["res"]
p, s7, s100 = res["primary"], res["placebo_shift7"], res["placebo_shift100"]
print(json.dumps({"estimate": p["tidal"]["rr"], "lo": p["tidal"]["lo"], "hi": p["tidal"]["hi"], "n": p["n_days"],
                  "ratio_tidal_over_placebo": p["ratio"]["rr"], "ratio_lo": p["ratio"]["lo"], "ratio_hi": p["ratio"]["hi"],
                  "placebo_zip_rr": p["placebo"]["rr"],
                  "shift7_tidal_rr": s7["tidal"]["rr"], "shift7_tidal_hi": s7["tidal"]["hi"],
                  "shift100_tidal_rr": s100["tidal"]["rr"], "shift100_tidal_hi": s100["tidal"]["hi"],
                  "complaints_tidal": p["complaints_tidal"], "n_boot": p["tidal"]["n_boot"]}))
'''

RECIPES['further-tidal-flooding-trend'] = {'code': ['analyses/__init__.py', 'analyses/round2_tidal/analyse.py'],
 'derived': ['data/derived/round2/tidal_trend/battery_daily_max_mhhw.json',
             'data/derived/round2/tidal_trend/prcp_central_park.csv',
             'data/derived/round2/tidal_trend/prcp_jfk.csv',
             'data/derived/round2/tidal_trend/daily_panel.csv'],
 'upstream_pointers': [],
 'wrapper': _W_FURTHER_TIDAL_FLOODING_TREND,
 'wrapper_note': 'Smallest wrapper: analyse.py is a flat script that runs eighteen bootstrapped models on import and '
                 "writes into the repository. code/rerun.py executes the script's own source with four asserted "
                 'textual changes (inputs path; the complaint series read from daily_panel.csv instead of aggregated '
                 'from the 27.8 MB complaints_by_day_zip.json; no results.json write; stop after the primary model '
                 'and the two shifted-tide placebos). The block bootstrap uses the registered seed 20261113 and '
                 '1,000 replicates, drawn in the same order as the full script, so the intervals reproduce exactly. '
                 'The rerun takes several minutes.',
 'imports': ['numpy', 'pandas', 'statsmodels', 'patsy', 'scipy', 'requests'],
 'deciding': {'what': 'city_effect: rate ratio of dry-day street-flooding and catch-basin complaints (C3) in the '
                      'tidal ZIP set per 10 cm of Battery daily maximum above 0.35 m over MHHW, 2010-2019, negative '
                      'binomial, 14-day moving-block bootstrap 95% interval (seed 20261113, 1,000 replicates); and '
                      'the tidal-over-placebo-ZIP ratio of rate ratios',
              'keys': {'estimate': 0.0001, 'lo': 0.0001, 'hi': 0.0001, 'n': 0},
              'extra_recorded': {'ratio_lo': {'value': 1.4348997719663479,
                                              'tol': 0.0001,
                                              'from': 'data/derived/round2/tidal_trend/results.json primary.ratio.lo '
                                                      '(outcome: 1.43 to 2.09)'}},
              'placebo': {'placebo_zip_rr': {'value': 1.1530935101354036,
                                             'tol': 0.0001,
                                             'from': 'data/derived/round2/tidal_trend/results.json '
                                                     'primary.placebo.rr (outcome: 1.15)',
                                             'what': 'the same model on the placebo ZIP set (every ZIP outside the '
                                                     'broad tidal set)'},
                          'shift7_tidal_rr': {'value': 0.9926041049820505,
                                              'tol': 0.0001,
                                              'from': 'data/derived/round2/tidal_trend/results.json '
                                                      'placebo_shift7.tidal.rr',
                                              'what': 'tidal-set rate ratio with the tide shifted 7 days (registered '
                                                      'placebo)'},
                          'shift7_tidal_hi': {'value': 1.0704564224491058,
                                              'tol': 0.0001,
                                              'from': 'data/derived/round2/tidal_trend/results.json '
                                                      'placebo_shift7.tidal.hi',
                                              'what': 'upper bootstrap limit of the 7-day shifted-tide placebo'},
                          'shift100_tidal_rr': {'value': 0.9713548847095617,
                                                'tol': 0.0001,
                                                'from': 'data/derived/round2/tidal_trend/results.json '
                                                        'placebo_shift100.tidal.rr',
                                                'what': 'tidal-set rate ratio with the tide shifted 100 days '
                                                        '(registered placebo)'},
                          'shift100_tidal_hi': {'value': 1.0450819569777863,
                                                'tol': 0.0001,
                                                'from': 'data/derived/round2/tidal_trend/results.json '
                                                        'placebo_shift100.tidal.hi',
                                                'what': 'upper bootstrap limit of the 100-day shifted-tide placebo'}},
              'decides': 'support_if: tidal-set interval lower limit above 1.00 and tidal-over-placebo ratio '
                         'interval lower limit above 1.00; shifted-tide placebos not above 1'},
 'not_rebuilt': [{'table': 'data/derived/round2/tidal_trend/daily_panel.csv',
                  'built_by': 'analyses/round2_tidal/analyse.py',
                  'built_from': ['data/derived/round2/tidal_trend/complaints_by_day_zip.json',
                                 'data/derived/round2/tidal_trend/battery_daily_max_mhhw.json',
                                 'data/derived/round2/tidal_trend/prcp_central_park.csv',
                                 'data/derived/round2/tidal_trend/prcp_jfk.csv'],
                  'why': 'its complaint columns are aggregated from complaints_by_day_zip.json (27.8 MB, over the '
                         'cap; written by analyses/round2_tidal/fetch_311.py from 311 queries of 76ig-c548 and '
                         'erm2-nwe9); the rerun takes only the columns C3_t, C3_p, C1_t and C4_t from it and '
                         'rebuilds the tide and dry-day columns itself'}],
 'refetch_rerun': False}


# Recipes added on 13 November 2026 (late evening), with the drive attached. Each cuts the rows its rerun needs
# from files too large to carry with a prepare step (code/prepare.py in the package).

_P_RLC_EXPANSION_REAREND = r'''
# Read the crash and vehicle records with rlc_did.fetch_crashes() from the repository's Socrata cache (the seven
# h9gi-nx95 pages and the bm4k-52h4 page), and keep the crashes within 50.5 m of a camera intersection or of an
# intersection in the control pool. rlc_did.build() sums crashes within 50 m of these points only, so the matched
# sets, the deciding ratio and the placebo are the same on this cut. Written as gzipped JSON with a fixed timestamp.
import gzip, json
import numpy as np
from concord import socrata
socrata.requests.get = None  # the cache must answer every query; a missing page fails here
sys.path.insert(0, str(ROOT / "analyses" / "street_safety"))
import rlc_did as R
from scipy.spatial import cKDTree
treated, all_cam, _ = R.load_sites()
pool = R.control_pool(all_cam)
pts = [R.xy(s["lat"], s["lon"]) for s in treated] + [R.xy(r["lat"], r["lon"]) for r in pool]
tree = cKDTree(np.array([[float(x), float(y)] for x, y in pts]))
rows, _ = R.fetch_crashes()
cx, cy, _, _ = R.crash_arrays(rows)
d, _ = tree.query(np.c_[cx, cy], k=1)
keep = [r for r, di in zip(rows, d) if di <= 50.5]
dst = OUT / "prepared" / "street_safety"
dst.mkdir(parents=True, exist_ok=True)
with open(dst / "crashes_near_sites.json.gzip", "wb") as raw:
    with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0, compresslevel=9) as fo:
        fo.write(json.dumps(keep, sort_keys=True, separators=(",", ":")).encode())
print(json.dumps({"crashes_read": len(rows), "crashes_kept": len(keep)}))
'''

_W_RLC_EXPANSION_REAREND = r'''"""Rerun the deciding number of rlc-expansion-rearend, and its registered placebo, from the package's inputs.

The claim's script, analyses/street_safety/rlc_did.py, reads 323,685 crash records (h9gi-nx95, seven cached pages,
120.7 MB) and the rear-end vehicle records (bm4k-52h4), matches each camera intersection to three control
intersections, and writes its results into the repository. The package carries the crashes within 50.5 m of a
camera or control intersection (inputs/prepared/, cut by code/prepare.py from the cached pages, which are pointed
to by sha256); build() sums crashes within 50 m of these points only. This wrapper replaces fetch_crashes() with a
reader of that cut, and calls load_sites(), control_pool(), crash_arrays(), build(), placebo(), rr_from() and boot()
unchanged (B=2000, seed 20261113) for the rear-end outcome and for the registered placebo year.
"""
import argparse, gzip, json, sys
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser()
ap.add_argument("--inputs", default=str(PKG / "inputs"))
INP = Path(ap.parse_args().inputs).resolve()
sys.path.insert(0, str(PKG / "code"))

import requests  # noqa: E402


def _offline(*a, **k):
    raise RuntimeError(f"offline rerun: a pinned input is missing and the code tried to fetch {a[:1]}")


requests.get = _offline
from analyses.street_safety import rlc_did as R  # noqa: E402

R.DER = INP / "data" / "derived" / "street_safety"
with gzip.open(INP / "prepared" / "street_safety" / "crashes_near_sites.json.gzip", "rb") as f:
    rows = json.loads(f.read())
treated, all_cam, _ = R.load_sites()
pool = R.control_pool(all_cam)
cx, cy, cym, vals = R.crash_arrays(rows)
out = {}
for tag, sets in (("", R.build(treated, pool, cx, cy, cym, vals)), ("placebo_", R.placebo(treated, pool, cx, cy, cym, vals))):
    rr, parts = R.rr_from(sets, "rear_end")
    lo, hi, se = R.boot(sets, "rear_end")
    out.update({f"{tag}estimate": round(rr, 4), f"{tag}lo": round(lo, 4), f"{tag}hi": round(hi, 4), f"{tag}n": len(sets)})

print(json.dumps(out))
'''

RECIPES['rlc-expansion-rearend'] = {'code': ['concord/__init__.py', 'concord/socrata.py', 'analyses/__init__.py', 'analyses/street_safety/rlc_did.py'],
 'derived': ['data/derived/street_safety/rlc_sites_geo.json', 'data/derived/street_safety/lpi_gazetteer.json'],
 'upstream_code': ['analyses/street_safety/rlc_sites.py'],
 'prepare': {'code': _P_RLC_EXPANSION_REAREND,
             'sources': ['file:data/cache/socrata/h9gi-nx95-d84a3a3634c73147b31621a7.json',
                         'file:data/cache/socrata/h9gi-nx95-6689db4216bb39668a0d5e23.json',
                         'file:data/cache/socrata/h9gi-nx95-8f57948c311e587e8fc34b1c.json',
                         'file:data/cache/socrata/h9gi-nx95-969416e69c86c5044fc85a1b.json',
                         'file:data/cache/socrata/h9gi-nx95-a1ada602969f6cf789d991b2.json',
                         'file:data/cache/socrata/h9gi-nx95-60cab1a79bd7b49bf9f7b688.json',
                         'file:data/cache/socrata/h9gi-nx95-64e49fa4d92902d1aaf51cee.json',
                         'file:data/cache/socrata/bm4k-52h4-d9aed0d6a7c5d127ad60851a.json',
                         'file:data/derived/street_safety/rlc_sites_geo.json',
                         'file:data/derived/street_safety/lpi_gazetteer.json'],
             'outputs': ['prepared/street_safety/crashes_near_sites.json.gzip'],
             'what': 'the crash records (h9gi-nx95, with the rear-end flag from bm4k-52h4) within 50.5 m of a camera '
                     'intersection or a control-pool intersection, as returned by rlc_did.fetch_crashes(), gzipped'},
 'upstream_pointers': [],
 'wrapper': _W_RLC_EXPANSION_REAREND,
 'wrapper_note': 'Smallest wrapper: rlc_did.py needs 120.7 MB of crash pages and writes into the repository. '
                 'code/prepare.py keeps the crashes within 50.5 m of a camera or control intersection, the only ones '
                 'build() counts, and code/rerun.py calls load_sites(), control_pool(), crash_arrays(), build(), '
                 'placebo(), rr_from() and boot() unchanged (B=2000, seed 20261113) for the rear-end outcome. '
                 'rlc_did.py rounds the ratio and the interval to four decimals, as the outcome records them. The '
                 'placebo is the registered one (the same sites and windows one year earlier, before any camera).',
 'imports': ['numpy', 'scipy', 'requests'],
 'deciding': {'what': 'city_effect: ratio of ratios for rear-end proxy crashes within 50 m, 283 camera intersections '
                      'against matched controls, cluster bootstrap 95% interval (B=2000, seed 20261113)',
              'keys': {'estimate': 0.0001, 'lo': 0.0001, 'hi': 0.0001, 'n': 0},
              'extra_recorded': {},
              'placebo': {'placebo_estimate': {'value': 1.2496,
                                               'tol': 0.0001,
                                               'registered': True,
                                               'from': 'outcome notes and '
                                                       'data/derived/street_safety/rlc_did_results.json '
                                                       '(placebo_one_year_earlier.rear_end.rr)',
                                               'what': 'registered placebo: the same sites and windows one year '
                                                       'earlier, before any camera'},
                          'placebo_lo': {'value': 1.0519,
                                         'tol': 0.0001,
                                         'registered': True,
                                         'from': 'rlc_did_results.json placebo_one_year_earlier.rear_end.lo',
                                         'what': 'its lower 95% limit'},
                          'placebo_hi': {'value': 1.488,
                                         'tol': 0.0001,
                                         'registered': True,
                                         'from': 'rlc_did_results.json placebo_one_year_earlier.rear_end.hi',
                                         'what': 'its upper 95% limit'}},
              'decides': 'support_if: 95% interval above 1.00 and rule 8 D >= 4 against 1.33'},
 'trace': True,
 'refetch_rerun': False}


_P_TURN_CALMING_PED = r'''
# Keep the crashes with at least one pedestrian injured or killed that lie within 40.5 m of a left-turn calming
# site, after the same coordinate filter that did.load_crashes() applies. The pedestrian count within 40 m of a
# site (the deciding outcome and the placebo) is a sum over these crashes only; the others add zero. The rings (50-200 m) are not reproduced from this cut.
import csv, json, math
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, str(ROOT / "analyses" / "turn_restrictions"))
from sites import xy
src = OPT / "turn_restrictions"
sites = json.loads((ROOT / "data/derived/turn_restrictions/sites.json").read_text())["sites"]
tree = cKDTree(np.array([[s["x"], s["y"]] for s in sites]))
dst = OUT / "prepared" / "turn_restrictions"
dst.mkdir(parents=True, exist_ok=True)
keep_ids, n_in, n_out = set(), 0, 0
with open(src / "crashes.csv", newline="") as fi, open(dst / "crashes.csv", "w", newline="") as fo:
    rd = csv.DictReader(fi)
    cols = ["collision_id", "crash_date", "latitude", "longitude", "number_of_pedestrians_injured",
            "number_of_pedestrians_killed"]
    wr = csv.DictWriter(fo, fieldnames=cols, quoting=csv.QUOTE_ALL, lineterminator="\n", extrasaction="ignore")
    wr.writeheader()
    for r in rd:
        n_in += 1
        try:
            lat, lon = float(r["latitude"]), float(r["longitude"])
        except (TypeError, ValueError):
            continue
        if not (40.45 < lat < 40.95 and -74.3 < lon < -73.65):
            continue
        if int(r["number_of_pedestrians_injured"] or 0) + int(r["number_of_pedestrians_killed"] or 0) == 0:
            continue
        x, y = xy(lat, lon)
        if tree.query_ball_point([x, y], 40.5):
            wr.writerow(r)
            keep_ids.add(r["collision_id"])
            n_out += 1
with open(src / "left_vehicles.csv", newline="") as fi, open(dst / "left_vehicles.csv", "w", newline="") as fo:
    rd = csv.DictReader(fi)
    wr = csv.DictWriter(fo, fieldnames=["collision_id"], quoting=csv.QUOTE_ALL, lineterminator="\n", extrasaction="ignore")
    wr.writeheader()
    for r in rd:
        if r["collision_id"] in keep_ids:
            wr.writerow(r)
print(json.dumps({"crashes_read": n_in, "crashes_kept": n_out}))
'''

_W_TURN_CALMING_PED = r'''"""Rerun the deciding number of turn-calming-ped, and the referee's placebo, from the package's inputs.

The claim's script, analyses/turn_restrictions/did.py, reads 1.8 million crash records from
~/opt/nyc-concordance/turn_restrictions/, fits four outcomes and three checks, and writes did_results.json into
the repository. The crash file is 174 MB, so the package carries the crashes within 40.5 m of a calming site
with at least one pedestrian injured or killed (inputs/prepared/, cut by code/prepare.py); the pedestrian
count within 40 m is a sum over these crashes only. This wrapper
points did.OPT at that folder, calls load_crashes(), site_monthly(), stack() and fit() unchanged for the
pedestrian outcome, and then reruns the exploratory placebo of did_explore.py (installation moved 12 months
early) with its window_factory() unchanged.
"""
import argparse, contextlib, json, sys
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser()
ap.add_argument("--inputs", default=str(PKG / "inputs"))
INP = Path(ap.parse_args().inputs).resolve()
sys.path.insert(0, str(PKG / "code"))
sys.path.insert(0, str(PKG / "code" / "analyses" / "turn_restrictions"))

import requests  # noqa: E402


def _offline(*a, **k):
    raise RuntimeError(f"offline rerun: a pinned input is missing and the code tried to fetch {a[:1]}")


requests.get = _offline
import did as D  # noqa: E402
import did_explore as E  # noqa: E402

D.OPT = INP / "prepared" / "turn_restrictions"
D.OUT = INP / "data" / "derived" / "turn_restrictions"
sites = json.loads((D.OUT / "sites.json").read_text())["sites"]
X, Y, M, PED, LT, _ = D.load_crashes()
counts = D.site_monthly(sites, X, Y, M, PED, LT)
r = D.fit(D.stack(sites, counts, "ped"))
orig = D.window
D.window = E.window_factory(-24, -13, -12, -1)
pl = D.fit(D.stack(sites, counts, "ped"))
D.window = orig
print(json.dumps({"estimate": r["ror"], "lo": r["lo"], "hi": r["hi"], "n": r["n_treated_sites"],
                  "treated_pre": r["treated_pre"], "treated_post": r["treated_post"],
                  "placebo_12m_ror": pl["ror"], "placebo_12m_lo": pl["lo"], "placebo_12m_hi": pl["hi"]}))
'''

RECIPES['turn-calming-ped'] = {'code': ['concord/__init__.py',
          'concord/socrata.py',
          'analyses/__init__.py',
          'analyses/turn_restrictions/sites.py',
          'analyses/turn_restrictions/did.py',
          'analyses/turn_restrictions/did_explore.py'],
 'derived': ['data/derived/turn_restrictions/sites.json'],
 'prepare': {'code': _P_TURN_CALMING_PED,
             'sources': ['opt:turn_restrictions/crashes.csv',
                         'opt:turn_restrictions/left_vehicles.csv',
                         'file:data/derived/turn_restrictions/sites.json'],
             'outputs': ['prepared/turn_restrictions/crashes.csv', 'prepared/turn_restrictions/left_vehicles.csv'],
             'what': 'the crash records (h9gi-nx95, fetched by analyses/turn_restrictions/fetch_crashes.py) with a '
                     'pedestrian injured or killed within 40.5 m of a left-turn calming site, and the left-turn '
                     'vehicle records (bm4k-52h4) of those crashes'},
 'upstream_pointers': [{'opt': 'turn_restrictions/crashes.csv',
                        'role': 'all geocoded crashes, 2014-2026, read by did.py'},
                       {'opt': 'turn_restrictions/left_vehicles.csv',
                        'role': 'vehicles making a left turn, read by did.py'}],
 'wrapper': _W_TURN_CALMING_PED,
 'wrapper_note': 'Smallest wrapper: did.py reads 174 MB of crash records from ~/opt and writes into the repository. '
                 'code/prepare.py keeps the crashes within 40.5 m of a calming site with at least one pedestrian '
                 'injured or killed, the only crashes that add to the pedestrian count within 40 m, and '
                 'code/rerun.py calls load_crashes(), site_monthly(), stack() and fit() unchanged for that outcome. '
                 'The left-turn and ring outcomes are not reproduced from this cut. The recorded n (712) is the '
                 "number of treated sites. The placebo is the referee's exploratory check, not a registered one.",
 'imports': ['numpy', 'pandas', 'statsmodels', 'patsy', 'scipy', 'requests'],
 'deciding': {'what': 'city_effect: ratio of ratios of pedestrians injured or killed within 40 m, 24 months after '
                      'against 24 months before installation, treated against later-treated sites, stacked cohorts '
                      '2016Q3-2023Q2, conditional Poisson (binomial GLM), SE clustered by site',
              'keys': {'estimate': 0.0001, 'lo': 0.0001, 'hi': 0.0001, 'n': 0},
              'extra_recorded': {},
              'placebo': {'placebo_12m_ror': {'value': 0.9119,
                                              'tol': 0.0001,
                                              'registered': False,
                                              'from': 'outcome notes and '
                                                      'data/derived/turn_restrictions/did_explore.json '
                                                      '(ped.placebo_12m_early)',
                                              'what': 'UNREGISTERED exploratory placebo named by the referee: '
                                                      'installation moved 12 months early (months -24..-13 against '
                                                      '-12..-1)'},
                          'placebo_12m_lo': {'value': 0.8252,
                                             'tol': 0.0001,
                                             'registered': False,
                                             'from': 'data/derived/turn_restrictions/did_explore.json',
                                             'what': 'its lower 95% limit'},
                          'placebo_12m_hi': {'value': 1.0078,
                                             'tol': 0.0001,
                                             'registered': False,
                                             'from': 'data/derived/turn_restrictions/did_explore.json',
                                             'what': 'its upper 95% limit'}},
              'decides': 'support_if: upper bound of the 95% interval of the ratio of ratios below 1.00'},
 'trace': True,
 'refetch_rerun': False}


_P_RESTAURANTS_NTA_HARSHNESS = r'''
# Keep, for every record of the Underlay snapshot, the type, the id and the data fields that
# evenness_test.load_snapshot() reads, in the snapshot's own order; drop the other fields and the record hashes.
# Write it gzipped with a fixed timestamp, so the same snapshot always gives the same bytes.
import gzip, json
KEEP = {"Restaurant": ("name", "cuisineDescription", "latitude", "longitude"),
        "Inspection": ("restaurantId", "inspectionDate", "inspectionType", "score", "grade"),
        "Violation": ("inspectionId", "criticalFlag")}
dst = OUT / "prepared" / "underlay"
dst.mkdir(parents=True, exist_ok=True)
n = 0
with open(OPT / "underlay" / "records_v1.0.0.ndjson") as fi, open(dst / "records_v1.0.0_min.ndjson.gzip", "wb") as raw:
    with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0, compresslevel=9) as fo:
        for line in fi:
            r = json.loads(line)
            d = r["data"]
            k = KEEP.get(r["type"], KEEP["Violation"])
            fo.write((json.dumps({"id": r["id"], "type": r["type"], "data": {x: d[x] for x in k if x in d}},
                                 separators=(",", ":"), ensure_ascii=False) + "\n").encode())
            n += 1
print(json.dumps({"records": n}))
'''

_W_RESTAURANTS_NTA_HARSHNESS = r'''"""Rerun the deciding number of restaurants-nta-harshness from the package's inputs.

The claim's script, analyses/restaurants/evenness_test.py, reads the Underlay snapshot nyc/restaurant-inspections
v1.0.0 (51 MB) from ~/opt/nyc-concordance/underlay/, runs the harshness and frequency tests, and writes into the
repository. The package carries the snapshot with only the fields load_snapshot() reads (inputs/prepared/, cut by
code/prepare.py). This wrapper unpacks it into work/, points evenness_test.SNAP and common.DER at the package,
calls load_snapshot(), assign_nta(), design(), permutation() (10,000 draws, seed 20261113) and nta_effects()
unchanged, and repeats the lines of main() that build the harshness frame.
"""
import argparse, gzip, json, shutil, sys
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser()
ap.add_argument("--inputs", default=str(PKG / "inputs"))
INP = Path(ap.parse_args().inputs).resolve()
sys.path.insert(0, str(PKG / "code"))
sys.path.insert(0, str(PKG / "code" / "analyses" / "restaurants"))

import requests  # noqa: E402


def _offline(*a, **k):
    raise RuntimeError(f"offline rerun: a pinned input is missing and the code tried to fetch {a[:1]}")


requests.get = _offline
import numpy as np  # noqa: E402
import common as c  # noqa: E402
import evenness_test as E  # noqa: E402

work = PKG / "work"
work.mkdir(exist_ok=True)
snap = work / "records_v1.0.0_min.ndjson"
with gzip.open(INP / "prepared" / "underlay" / "records_v1.0.0_min.ndjson.gzip", "rb") as fi, open(snap, "wb") as fo:
    shutil.copyfileobj(fi, fo)
E.SNAP = snap
c.DER = INP / "data" / "derived" / "restaurants"

R, I = E.load_snapshot()
Rn = E.assign_nta(R)
counts = Rn.groupby("nta2020").size()
keep = counts[counts >= E.MIN_REST].index
Rn = Rn[Rn.nta2020.isin(keep)].copy()
Rn["log_nta_rest"] = np.log(Rn.nta2020.map(counts))
Rn["cuis"] = c.cuisine_group(Rn.cuisine)
nm = c.norm_dba(Rn.name)
Rn["chain"] = nm.map(nm.value_counts()).ge(5).astype(float)
I = I.sort_values("date")
first = I.groupby("camis").head(1).set_index("camis")
Rn["new"] = Rn.camis.map(first.itype.str.startswith("Pre-permit")).fillna(False).astype(float)
work_n = I.groupby("date").size()
ci = I[I.itype == "Cycle Inspection / Initial Inspection"].merge(Rn, on="camis")
ci["log_work"] = np.log(ci.date.map(work_n))
ci["q"] = ci.date.dt.to_period("Q").astype(str)
ci["dow"] = ci.date.dt.dayofweek.astype(str)
Xh = E.design(ci, ["cuis", "chain", "q", "dow", "log_work", "log_nta_rest", "new"], ["cuis", "q", "dow"])
harsh, _ = E.permutation(ci, "n_crit", Xh)
_, _, tau = E.nta_effects(ci, "n_crit", Xh)
print(json.dumps({"estimate": tau, "n": int(len(ci)), "permutation_p": harsh["p"], "n_ntas": harsh["n_ntas"],
                  "n_restaurants": int(ci.camis.nunique()), "S_over_null_mean": harsh["S_ratio"]}))
'''

RECIPES['restaurants-nta-harshness'] = {'code': ['concord/__init__.py',
          'concord/socrata.py',
          'analyses/__init__.py',
          'analyses/restaurants/common.py',
          'analyses/restaurants/evenness_test.py'],
 'derived': ['data/derived/restaurants/nta2020.geojson'],
 'prepare': {'code': _P_RESTAURANTS_NTA_HARSHNESS,
             'sources': ['opt:underlay/records_v1.0.0.ndjson'],
             'outputs': ['prepared/underlay/records_v1.0.0_min.ndjson.gzip'],
             'what': 'every record of the Underlay snapshot nyc/restaurant-inspections v1.0.0 (hash '
                     'ulv2:07a7f08a0d5c85649920f8adc6946d27c17f5e2d75e9ee07c0ad4ae0fcc6739c) with only the fields '
                     'evenness_test.load_snapshot() reads, gzipped'},
 'upstream_pointers': [{'opt': 'underlay/records_v1.0.0.ndjson',
                        'role': 'Underlay snapshot nyc/restaurant-inspections v1.0.0, read by evenness_test.py'}],
 'wrapper': _W_RESTAURANTS_NTA_HARSHNESS,
 'wrapper_note': 'Smallest wrapper: evenness_test.py reads the 51 MB Underlay snapshot from ~/opt, runs two tests '
                 'and writes into the repository. code/prepare.py keeps only the fields load_snapshot() reads, and '
                 'code/rerun.py calls load_snapshot(), assign_nta(), design(), permutation() and nta_effects() '
                 'unchanged for the harshness test, with the registered 10,000 draws and seed 20261113. The rerun '
                 'takes about a minute. The claim has no placebo; the permutation null is part of the deciding test.',
 'imports': ['numpy',
             'pandas',
             'statsmodels',
             'patsy',
             'scipy',
             'geopandas',
             'shapely',
             'pyproj',
             'pyogrio',
             'requests'],
 'deciding': {'what': 'city_effect: between-NTA SD (tau) of the adjusted log rate ratio of critical violations per '
                      'routine initial inspection, with the permutation p of the NTA score statistic (10,000 draws, '
                      'seed 20261113)',
              'keys': {'estimate': 0.0001, 'n': 0, 'permutation_p': 0.0001, 'n_ntas': 0, 'n_restaurants': 0},
              'extra_recorded': {},
              'decides': 'support_if: permutation p <= 0.01 and tau >= 0.05; refute_if: permutation p > 0.10'},
 'trace': True,
 'refetch_rerun': False}


if os.environ.get("REPLICATE_EXTRA_RECIPES"):  # development only: <dir>/*.py, each defining RECIPE_ID and RECIPE
    for _f in sorted(Path(os.environ["REPLICATE_EXTRA_RECIPES"]).glob("*.py")):
        _ns: dict = {}
        exec(compile(_f.read_text(), str(_f), "exec"), _ns)
        RECIPES[_ns["RECIPE_ID"]] = _ns["RECIPE"]


# --------------------------------------------------------------------------- helpers

def sha256_file(p: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while b := f.read(chunk):
            h.update(b)
    return h.hexdigest()


def rows_sha256(rows) -> str:
    return hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def git(*args, check=False) -> str:
    r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=60)
    if check and r.returncode:
        raise RuntimeError(r.stderr)
    return r.stdout.strip()


def rel(p: Path) -> str:
    return str(Path(p).resolve().relative_to(ROOT))


def opt_rel(p: Path) -> str:
    return "~/opt/nyc-concordance/" + str(Path(p).resolve().relative_to(OPT.resolve()))


# --------------------------------------------------------------------------- claim section

def claim_section(cid: str) -> dict:
    from concord.claims import _hash
    rf, of = REG / f"{cid}.json", OUTC / f"{cid}.json"
    reg = json.loads(rf.read_text())
    out = json.loads(of.read_text()) if of.exists() else None
    added = git("log", "--diff-filter=A", "--format=%H %cI %s", "--", rel(rf)).splitlines()
    branch = {"name": f"prereg/{cid}", "sha": None, "reachable": False}
    try:
        ls = subprocess.run(["git", "ls-remote", "origin", f"refs/heads/prereg/{cid}"], cwd=ROOT, capture_output=True,
                            text=True, timeout=30)
        branch["reachable"] = ls.returncode == 0
        if ls.stdout.strip():
            branch["sha"] = ls.stdout.split()[0]
            branch["contains_registration_commit"] = bool(added) and subprocess.run(
                ["git", "merge-base", "--is-ancestor", added[-1].split()[0], branch["sha"]], cwd=ROOT).returncode == 0
        elif branch["reachable"]:
            branch["note"] = "origin is reachable but has no such branch"
    except Exception as e:  # noqa: BLE001
        branch["note"] = f"git ls-remote failed: {type(e).__name__}"
    hist = []
    if out:
        for line in git("log", "--format=%H %cI %s", "--", rel(of)).splitlines():
            h, t, s = line.split(" ", 2)
            hist.append({"commit": h, "committed_at": t, "subject": s})
    referee = []
    seen = set()
    if out and isinstance(out.get("critique"), dict) and out["critique"].get("report"):
        referee.append({"path": out["critique"]["report"], "role": "named in the outcome", "answer": out["critique"].get("answer")})
        seen.add(out["critique"]["report"])
    own = ROOT / "critique" / f"{cid}.md"
    if own.exists() and rel(own) not in seen:
        referee.append({"path": rel(own), "role": "referee report for this claim"})
        seen.add(rel(own))
    for f in sorted((ROOT / "critique").glob("*.md")):
        if rel(f) not in seen and re.search(r"(?<![\w-])" + re.escape(cid) + r"(?![\w-])", f.read_text(errors="ignore")):
            referee.append({"path": rel(f), "role": "mentions the claim id"})
    for r in referee:
        p = ROOT / r["path"]
        if p.exists():
            r["sha256"] = sha256_file(p)
    return {
        "id": cid,
        "registration": reg,
        "registration_path": rel(rf),
        "registration_sha256": reg.get("sha256"),
        "registration_hash_ok": reg.get("sha256") == _hash(reg),
        "registration_file_sha256": sha256_file(rf),
        "registration_commit": ({"commit": added[-1].split()[0], "committed_at": added[-1].split()[1],
                                 "subject": added[-1].split(" ", 2)[2]} if added else None),
        "prereg_branch": branch,
        "outcome": out,
        "outcome_path": rel(of) if out else None,
        "outcome_file_sha256": sha256_file(of) if out else None,
        "revision_history": {"in_file": (out or {}).get("history", []), "last_revision": (out or {}).get("revision"),
                             "outcome_commits": hist},
        "referee_reports": referee,
    }


# --------------------------------------------------------------------------- code section

SCRIPT_RE = re.compile(r"\b((?:analyses|tools|concord)/[\w./-]+\.py)\b")
SEED_RE = re.compile(r"seeds?\s*(?:=|:|of|is)?\s*(\d{3,})", re.I)
DRAWS_RE = re.compile(r"(\d[\d,]*)\s+(draws|permutations|bootstrap(?:\s+(?:draws|replicates|samples))?|replicates|resamples|simulations)", re.I)
COMMIT_RE = re.compile(r"(?:commit|script)\s+([0-9a-f]{7,40})\b")


def code_entry(path: str, how: str) -> dict:
    p = ROOT / path
    e = {"path": path, "found_by": how, "exists": p.exists()}
    if p.exists():
        e["blob"] = git("hash-object", path)
        e["blob_at_HEAD"] = git("rev-parse", f"HEAD:{path}") or None
        e["clean"] = e["blob"] == e["blob_at_HEAD"]
        e["last_commit"] = git("log", "-1", "--format=%H", "--", path) or None
        e["first_commit"] = (git("log", "--diff-filter=A", "--format=%H", "--", path).splitlines() or [None])[-1]
        e["sha256"] = sha256_file(p)
    return e


def code_section(cid: str, claim: dict, recipe: dict | None) -> dict:
    found: dict[str, str] = {}
    if recipe:
        for p in recipe["code"]:
            found[p] = "rerun recipe (imported by code/rerun.py)"
        for p in recipe.get("upstream_code", []):
            found.setdefault(p, "rerun recipe (upstream stage, not rerun)")
    texts = json.dumps(claim["outcome"] or {}) + json.dumps(claim["registration"])
    for m in SCRIPT_RE.findall(texts):
        if (ROOT / m).exists():
            found.setdefault(m, "named in the registration or outcome")
    id_re = re.compile(r"(?<![\w-])" + re.escape(cid) + r"(?![\w-])")
    for f in sorted((ROOT / "analyses").rglob("*.py")):
        try:
            if id_re.search(f.read_text(errors="ignore")):
                found.setdefault(rel(f), "contains the claim id (search of analyses/)")
        except OSError:
            pass
    reg_txt = json.dumps(claim["registration"])
    return {
        "repo_commit": git("rev-parse", "HEAD"),
        "repo_dirty_paths": len([x for x in git("status", "--porcelain").splitlines() if x.strip()]),
        "scripts": [code_entry(p, how) for p, how in found.items()],
        "seeds": sorted(set(SEED_RE.findall(reg_txt))),
        "draw_counts": sorted({f"{n} {w}" for n, w in DRAWS_RE.findall(reg_txt)}),
        "commits_named_in_registration": sorted(set(COMMIT_RE.findall(reg_txt))),
        "procedure_note": ("The registration names no seed and no resampling draw count; the deciding number is "
                           "deterministic given the inputs." if not SEED_RE.findall(reg_txt) and not DRAWS_RE.findall(reg_txt)
                           else "Seeds and draw counts above are quoted from the registration text."),
    }


# --------------------------------------------------------------------------- data section

def socrata_cache_files(dataset: str, query: dict) -> list[Path]:
    cache = ROOT / "data" / "cache" / "socrata"
    q = dict(query)
    sig = lambda params: hashlib.sha256((dataset + json.dumps(params, sort_keys=True)).encode()).hexdigest()[:24]  # noqa: E731
    f = cache / f"{dataset}-{sig(q)}.json"
    if f.exists():
        return [f]
    out, off = [], 0
    page = int(q.get("$limit", 50000))
    while True:
        f = cache / f"{dataset}-{sig({**q, '$offset': off})}.json"
        if not f.exists():
            break
        out.append(f)
        off += page
    return out


def sysgraph_cached_requests(reg: dict) -> list[Path]:
    """Cached System graph responses for the relationships and concepts named in the registration's graph_evidence."""
    toks = set()
    for g in reg.get("graph_evidence", []) or []:
        rid = g.get("relationship_id") or ""
        if "|" in rid and " " not in rid:
            toks.add(rid)
            toks.add(urllib.parse.quote(rid, safe=""))
        for m in re.findall(r"concept ([A-Za-z0-9_-]{10})", rid):
            toks.add(f"/v1/concepts/{m}")
    if not toks:
        return []
    hits = []
    for f in sorted((ROOT / "data" / "cache" / "sysgraph").glob("*.json")):
        with open(f, "rb") as fh:
            head = fh.read(600).decode("utf-8", "ignore")
        m = re.search(r'"path":\s*"([^"]*)"', head)
        if m and any(t in m.group(1) for t in toks):
            hits.append(f)
    return hits


class Inputs:
    """Collects files to copy, in priority order, under a total size cap."""

    def __init__(self, cap_bytes: int, only_required: bool = False):
        self.cap, self.used, self.files = cap_bytes, 0, []
        self.only_required = only_required  # copy only the files the rerun reads; point to the rest by hash

    def add_slice(self, p: Path, rule: dict, tmpdir: Path) -> dict:
        """Copy a column or row subset of a large file in place of the whole file. The entry carries the sha256 of
        the slice (what verify.py checks) and of the whole file (what --refetch compares), and the rule that makes one
        from the other."""
        import csv
        p = Path(p)
        out = tmpdir / (rel(p).replace("/", "__"))
        with open(p, newline="") as fi, open(out, "w", newline="") as fo:
            rd, wr = csv.reader(fi), csv.writer(fo, quoting=csv.QUOTE_ALL, lineterminator="\n")
            head = next(rd)
            keep = [i for i, c in enumerate(head) if c in rule["columns"]] if rule.get("columns") else list(range(len(head)))
            wr.writerow([head[i] for i in keep])
            dcol = head.index(rule["date_column"]) if rule.get("date_column") else None
            for row in rd:
                if dcol is not None and not (rule["from"] <= row[dcol][:10] <= rule["to"]):
                    continue
                wr.writerow([row[i] for i in keep])
        size = out.stat().st_size
        e = {"path": rel(p), "bytes": size, "sha256": sha256_file(out), "role": "slice of a large input, read by the rerun",
             "sliced_from": {"bytes": p.stat().st_size, "sha256": sha256_file(p),
                             "rule": {k: v for k, v in rule.items() if k != "path"},
                             "how": "csv.reader over the whole file; keep the named columns (and rows whose date column "
                                    "lies in the range, if one is given); csv.writer with QUOTE_ALL and newline line ends"},
             "copied": True, "required_for_rerun": True, "_src": str(out)}
        self.used += size
        self.files.append(e)
        return e

    def add(self, p: Path, role: str, required: bool, group_bytes: int | None = None, **extra) -> dict:
        """group_bytes: total size of the set of pages this file belongs to; the pages are copied all or none."""
        p = Path(p)
        for old in self.files:  # a file already listed (for example, found by the trace) keeps its first entry
            if old["path"] == rel(p):
                for k, v in extra.items():
                    old.setdefault(k, v)
                return old
        size = p.stat().st_size
        e = {"path": rel(p), "bytes": size, "sha256": sha256_file(p), "role": role, **extra}
        if self.only_required and not required:
            e["copied"] = False
            e["why_not_copied"] = "not read by the rerun; pointed to by hash"
        elif group_bytes is not None and not getattr(self, "_group_ok", True):
            e["copied"] = False
            e["why_not_copied"] = f"the pages of this query total {group_bytes / 2**20:.1f} MB, over the remaining cap"
        elif self.used + size <= self.cap:
            e["copied"] = True
            self.used += size
        else:
            e["copied"] = False
            e["why_not_copied"] = f"over the {self.cap // 2**20} MB cap ({size / 2**20:.1f} MB)"
        e["required_for_rerun"] = required and e["copied"]
        if required and not e["copied"]:
            e["required_for_rerun_but_missing"] = True
        self.files.append(e)
        return e


def data_section(claim: dict, recipe: dict | None, inputs: Inputs) -> list[dict]:
    out = claim["outcome"] or {}
    entries = []
    # derived tables first, so the deciding rerun gets its inputs inside the cap
    for path in (recipe or {}).get("derived", []):
        inputs.add(ROOT / path, "derived table read by the rerun", True)
    for path in (recipe or {}).get("_traced", []):
        inputs.add(ROOT / path, "read by code/rerun.py (found by tracing a run in the repository)", True)
    for s in out.get("sources", []) or []:
        if not isinstance(s, dict):
            continue
        k = (s.get("kind") or "").lower()
        e = {"kind": s.get("kind"), "record": s}
        if isinstance(s.get("dataset"), str) and (k in SOCRATA_DOMAINS or (s.get("query") and re.match(r"^[a-z0-9]{4}-[a-z0-9]{4}$", s["dataset"]))):
            # the host comes from the source's own URL when it has one (data.ny.gov and health.data.ny.gov are Socrata too)
            host = urllib.parse.urlparse(s.get("url") or "").netloc
            dom = ("https://" + host) if host else SOCRATA_DOMAINS.get(k, "https://data.cityofnewyork.us")
            e.update({"type": "socrata", "domain": dom, "dataset": s.get("dataset"), "rows_updated_at": s.get("rows_updated_at"),
                      "soql": s.get("query"), "fetched": s.get("fetched"), "n_rows": s.get("n_rows")})
            files = socrata_cache_files(s["dataset"], s.get("query") or {})
            e["cache_files"] = []
            gb = sum(f.stat().st_size for f in files)
            inputs._group_ok = inputs.used + gb <= inputs.cap
            for f in files:
                rows = json.loads(f.read_text()).get("rows", [])
                fe = inputs.add(f, f"cached Socrata response, {s['dataset']}", recipe is not None and recipe.get("refetch_rerun", False),
                                group_bytes=gb, rows_sha256=rows_sha256(rows), n_rows=len(rows))
                e["cache_files"].append({k2: fe[k2] for k2 in ("path", "sha256", "rows_sha256", "bytes", "copied")})
            inputs._group_ok = True
            if not files:
                e["cache_files_note"] = "no cached response found in data/cache/socrata/ for this query"
        elif k == "noaa-ghcnd":
            f = ROOT / "data" / "cache" / "noaa" / f"{s.get('station')}.csv"
            e.update({"type": "noaa", "url": s.get("url"), "station": s.get("station"), "last_modified": s.get("last_modified")})
            if f.exists():
                fe = inputs.add(f, "NOAA GHCN-Daily station file", recipe is not None and recipe.get("refetch_rerun", False))
                meta = f.with_suffix(".meta")
                if meta.exists():
                    inputs.add(meta, "NOAA cache metadata (Last-Modified, fetch time)", fe["copied"])
                e["file"] = {k2: fe[k2] for k2 in ("path", "sha256", "bytes", "copied")}
                if fe.get("sliced_from"):
                    e["file"]["full_sha256"] = fe["sliced_from"]["sha256"]
                    e["file"]["full_bytes"] = fe["sliced_from"]["bytes"]
                lm = (meta.read_text().split("\n")[0] if meta.exists() else None)
                if lm and s.get("last_modified") and lm != s.get("last_modified"):
                    e["warning"] = f"cached file Last-Modified {lm!r} differs from the outcome's {s.get('last_modified')!r}"
        elif k.startswith("sysgraph") or k == "system-public-graph":
            e.update({"type": "sysgraph", "release": SYSGRAPH_RELEASE, "api": s.get("api") or "v1.0",
                      "dataset_version": s.get("dataset"), "key": "not included; supply your own in ~/.config/system/token"})
            e["derived_files"] = []
            for fld in ("file", "audit"):
                if s.get(fld) and (ROOT / s[fld]).exists():
                    fe = inputs.add(ROOT / s[fld], f"graph evidence ({fld})", False)
                    e["derived_files"].append({k2: fe[k2] for k2 in ("path", "sha256", "bytes", "copied")})
            e["cached_requests"] = []
            for f in sysgraph_cached_requests(claim["registration"]):
                d = json.loads(f.read_text())
                q = urllib.parse.urlencode(sorted((d.get("params") or {}).items()), doseq=True)
                fe = inputs.add(f, "cached System graph response", False)
                e["cached_requests"].append({"request": d.get("path") + (f"?{q}" if q else ""), "fetched": d.get("fetched"),
                                             "path": fe["path"], "sha256": fe["sha256"],
                                             "response_sha256": rows_sha256(d.get("response")), "copied": fe["copied"]})
        elif k.startswith("tlc"):
            e.update({"type": "tlc", "url": s.get("url"), "etag": s.get("etag"), "last_modified": s.get("last_modified")})
            for fs in (s.get("files") or [s]):
                lc = fs.get("local_copy")
                if lc:
                    p = Path(os.path.expanduser(lc))
                    if p.exists():
                        e.setdefault("big_files", []).append({"url": fs.get("url"), "path": opt_rel(p), "bytes": p.stat().st_size,
                                                              "sha256": sha256_file(p)})
        elif k == "underlay":
            e.update({"type": "underlay", "collection": s.get("collection"), "version": s.get("version"), "hash": s.get("hash")})
            col = OPT / "underlay" / "collection.json"
            if col.exists():
                arks = re.findall(r'"ark":"([^"]+)"', col.read_text())
                e["ark"] = next((a for a in arks if a.endswith("." + str(s.get("version")))), arks[0] if arks else None)
        else:
            e["type"] = "pointer"
            for fld in ("file", "path"):
                v = s.get(fld)
                if isinstance(v, str) and (ROOT / v).is_file():
                    fe = inputs.add(ROOT / v, f"file named by a {s.get('kind')} source", False)
                    e["file"] = {k2: fe[k2] for k2 in ("path", "sha256", "bytes", "copied")}
        entries.append(e)
    # upstream files named by the recipe
    for u in (recipe or {}).get("upstream_pointers", []):
        if "opt" in u:
            p = OPT / u["opt"]
            e = {"type": "big-file", "role": u["role"], "path": f"~/opt/nyc-concordance/{u['opt']}"}
            if p.exists():
                e.update({"bytes": p.stat().st_size, "sha256": sha256_file(p)})
            elif u.get("recorded"):
                e.update({"bytes": u["recorded"]["bytes"], "sha256": u["recorded"]["sha256"],
                          "note": f"the drive was not attached at this build; size and sha256 are from the {u['recorded']['when']}"})
            else:
                e["note"] = "not present on this machine when the package was built; no hash recorded"
            entries.append(e)
        else:
            p = ROOT / u["path"]
            if p.exists():
                fe = inputs.add(p, u["role"], False)
                entries.append({"type": "upstream-file", "role": u["role"], **{k2: fe[k2] for k2 in ("path", "sha256", "bytes", "copied")}})
    return entries


def not_rebuilt_section(recipe: dict | None, data: list[dict], inputs: Inputs) -> list[dict]:
    """Intermediate tables the package carries but cannot rebuild, each with what it was built from and where
    those inputs are pointed to by hash (a manifest path, or a recorded sha256)."""
    out = []
    by_ds = {}
    for e in data:
        if e.get("type") == "socrata":
            by_ds.setdefault(e["dataset"], []).append(e)
    files = {f["path"]: f for f in inputs.files}
    for t in (recipe or {}).get("not_rebuilt", []):
        ent = {"table": t["table"], "built_by": t["built_by"], "why_not_rebuilt": t["why"], "built_from": []}
        tf = files.get(t["table"])
        if tf:
            ent["table_sha256"], ent["table_copied"] = tf["sha256"], tf["copied"]
        for src in t["built_from"]:
            kind, _, val = src.partition(":") if ":" in src and not src.startswith("data/") else ("file", "", src)
            b = {"source": src}
            if kind == "socrata":
                es = by_ds.get(val, [])
                pages = [cf for e in es for cf in e.get("cache_files", [])]
                b.update({"dataset": val, "name": (es[0]["record"].get("name") if es else None),
                          "pages": len(pages), "bytes": sum(cf["bytes"] for cf in pages),
                          "copied": bool(pages) and all(cf["copied"] for cf in pages),
                          "pointed_to_at": "manifest.json data[] (type socrata, dataset " + val + ") cache_files[].sha256",
                          "sha256": [cf["sha256"] for cf in pages]})
                if not pages:
                    b["note"] = "no cached response found; only the query and rowsUpdatedAt are recorded"
            elif kind == "opt":
                e = next((x for x in data if x.get("type") == "big-file" and x["path"].endswith(val)), None)
                b.update({"path": f"~/opt/nyc-concordance/{val}", "copied": False,
                          "bytes": (e or {}).get("bytes"), "sha256": (e or {}).get("sha256"),
                          "pointed_to_at": "manifest.json data[] (type big-file)"})
            elif kind == "external":
                b.update({"copied": False, "sha256": None, "note": "an external service; no file is pinned"})
            else:
                f = files.get(val)
                if f is None and (ROOT / val).exists():
                    f = inputs.add(ROOT / val, f"input of {t['built_by']} (not rerun)", False)
                b.update({"path": val, "copied": (f or {}).get("copied", False), "bytes": (f or {}).get("bytes"),
                          "sha256": (f or {}).get("sha256"), "pointed_to_at": "manifest.json inputs.files[]"})
            ent["built_from"].append(b)
        out.append(ent)
    return out


# --------------------------------------------------------------------------- environment

def environment(recipe: dict | None) -> dict:
    py = VENV / "bin" / "python"
    pyv = subprocess.run([str(py), "-c", "import sys;print(sys.version)"], capture_output=True, text=True).stdout.strip()
    fr = subprocess.run(["uv", "pip", "freeze", "--python", str(py)], capture_output=True, text=True)
    freeze = [x for x in fr.stdout.splitlines() if x.strip()]
    env = {"python": pyv, "venv": "~/.venvs/nyc-concordance", "uv_pip_freeze": freeze,
           "platform": platform.platform(), "machine": platform.machine(), "os": f"{platform.system()} {platform.release()}",
           "mac_ver": platform.mac_ver()[0] or None}
    if recipe:
        want = {w.lower() for w in recipe["imports"]}
        env["requirements"] = [x for x in freeze if re.split(r"[=<>@ ]", x)[0].lower().replace("_", "-") in want]
    return env


# --------------------------------------------------------------------------- generated files

VERIFY = r'''#!/usr/bin/env python
"""Verify this replication package. Usage: python verify.py [--refetch] [--python PATH]

1. Checks the sha256 of every file copied into inputs/ against manifest.json.
2. Reruns the deciding number with code/rerun.py on inputs/ (no network) and compares it with the recorded
   outcome within the tolerance stated in manifest.json.
3. With --refetch, re-runs each pinned Socrata query and NOAA download (no key needed), writes the responses to
   refetched/ in the same layout, compares them with the pinned hashes, and, where the recipe allows, reruns the
   deciding number on the live data.

Result: MATCH (inputs intact, number within tolerance), DRIFT (an input differs from its pin: a copy was altered,
or with --refetch a live source has changed), MISMATCH (inputs intact, number outside tolerance: the code or the
environment differs). Only files inside this folder are read.
"""
import argparse, hashlib, json, shutil, subprocess, sys, time, urllib.parse, urllib.request
from pathlib import Path

PKG = Path(__file__).resolve().parent
M = json.loads((PKG / "manifest.json").read_text())


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while b := f.read(1 << 20):
            h.update(b)
    return h.hexdigest()


def rows_sha(rows):
    return hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def rerun(py, inputs):
    r = subprocess.run([py, str(PKG / "code" / "rerun.py"), "--inputs", str(inputs)], cwd=PKG, capture_output=True, text=True)
    if r.returncode:
        return None, r.stderr[-3000:]
    try:
        return json.loads(r.stdout.strip().splitlines()[-1]), None
    except Exception as e:  # noqa: BLE001
        return None, f"could not parse rerun output: {e}: {r.stdout[-500:]}"


def compare(got):
    d = M["deciding"]
    rows, ok = [], True
    for k, tol in d["tolerance"].items():
        rec, new = d["recorded"].get(k), got.get(k)
        good = rec is not None and new is not None and abs(float(new) - float(rec)) <= tol
        ok &= good
        rows.append({"key": k, "recorded": rec, "rerun": new, "tolerance": tol, "within": good})
    return ok, rows


def get(url, params=None, timeout=300):
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "replication-package-verify"})
    ctx = None
    try:  # some Python builds have no CA bundle for urllib; certifi (installed with requests) supplies one
        import certifi, ssl
        ctx = ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        pass
    for i in range(5):
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
                return r.read(), dict(r.headers)
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(3 * (i + 1))
    raise RuntimeError(f"fetch failed {url}: {last}")


def refetch():
    out = PKG / "refetched"
    report = []
    for f in M["inputs"]["files"]:  # start from the copies, so derived tables are present
        if f["copied"]:
            dst = out / f["path"]
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(PKG / "inputs" / f["path"], dst)
    for e in M["data"]:
        if e.get("type") == "socrata":
            ds, dom = e["dataset"], e["domain"]
            try:
                meta = json.loads(get(f"{dom}/api/views/{ds}.json")[0])
                ts = meta.get("rowsUpdatedAt")
                live_ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts)) if ts else None
            except Exception as ex:  # noqa: BLE001
                live_ts = f"error: {ex}"
            r = {"source": f"socrata {ds}", "pinned_rows_updated_at": e.get("rows_updated_at"), "live_rows_updated_at": live_ts}
            changed_ts = live_ts != e.get("rows_updated_at")
            for cf in e.get("cache_files", []):
                if not cf["copied"]:
                    r.setdefault("not_refetched", []).append(cf["path"])
                    continue
                pinned = json.loads((PKG / "inputs" / cf["path"]).read_text())
                params = pinned["source"]["query"]
                # the cached page may carry $offset; the source record in the file is the page's own query
                body, _ = get(f"{dom}/resource/{ds}.json", params)
                rows = json.loads(body)
                new = rows_sha(rows)
                r.setdefault("pages", []).append({"path": cf["path"], "pinned_rows_sha256": cf["rows_sha256"],
                                                  "live_rows_sha256": new, "same": new == cf["rows_sha256"],
                                                  "pinned_n": len(pinned["rows"]), "live_n": len(rows)})
                (out / cf["path"]).write_text(json.dumps({"source": {**pinned["source"], "fetched": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                                                                     "n_rows": len(rows)}, "rows": rows}))
            r["drift"] = changed_ts or any(not p["same"] for p in r.get("pages", []))
            report.append(r)
        elif e.get("type") == "noaa" and e.get("file", {}).get("copied"):
            body, hdr = get(e["url"])
            p = out / e["file"]["path"]
            p.write_bytes(body)
            p.with_suffix(".meta").write_text(hdr.get("Last-Modified", "") + "\n" + time.strftime("%Y-%m-%dT%H:%M:%S%z"))
            new = hashlib.sha256(body).hexdigest()
            pin = e["file"].get("full_sha256", e["file"]["sha256"])
            report.append({"source": f"noaa {e['station']}", "pinned_last_modified": e.get("last_modified"),
                           "live_last_modified": hdr.get("Last-Modified"), "pinned_sha256": pin,
                           "live_sha256": new, "drift": new != pin})
    return out, report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refetch", action="store_true")
    ap.add_argument("--python", default=sys.executable)
    a = ap.parse_args()
    res = {"claim": M["claim"]["id"], "checked_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    bad = []
    for f in M["inputs"]["files"]:
        if f["copied"]:
            p = PKG / "inputs" / f["path"]
            if not p.exists() or sha(p) != f["sha256"]:
                bad.append(f["path"])
    missing = [f["path"] for f in M["inputs"]["files"] if f.get("required_for_rerun_but_missing")]
    res["inputs"] = {"copied": sum(f["copied"] for f in M["inputs"]["files"]), "hash_failures": bad,
                     "required_but_pointer_only": missing}
    if not (PKG / "code" / "rerun.py").exists():
        res["status"] = "DRIFT" if bad else "NO_RERUN"
        res["note"] = "No rerun recipe is packaged for this claim; only the input hashes were checked."
        print(json.dumps(res, indent=1))
        return
    got, err = rerun(a.python, PKG / "inputs")
    res["rerun"] = got if got else {"error": err}
    ok, rows = compare(got) if got else (False, [])
    res["comparison"] = rows
    if a.refetch:
        try:
            rdir, rep = refetch()
        except Exception as ex:  # noqa: BLE001
            rdir, rep = None, [{"source": "refetch", "error": str(ex)[:500], "drift": None}]
        res["refetch"] = rep
        drift = any(r.get("drift") for r in rep)
        if rdir is None:
            res["rerun_on_live_inputs"] = "not run: the refetch failed"
        elif M["deciding"].get("refetch_rerun"):
            got2, err2 = rerun(a.python, rdir)
            res["rerun_on_live_inputs"] = got2 if got2 else {"error": err2}
            if got2:
                ok2, res["comparison_live"] = compare(got2)
                res["live_number_within_tolerance"] = ok2
        else:
            res["rerun_on_live_inputs"] = ("not run: the deciding number is computed from derived tables whose upstream "
                                           "stages are not packaged; the live check covers the pinned sources only")
    else:
        drift = False
    if bad:
        res["status"] = "DRIFT"
    elif got is None or not ok:
        res["status"] = "MISMATCH"
    elif drift:
        res["status"] = "DRIFT"
    else:
        res["status"] = "MATCH"
    print(json.dumps(res, indent=1, default=str))
    (PKG / "verify_result.json").write_text(json.dumps(res, indent=1, default=str))
    sys.exit(0 if res["status"] == "MATCH" else 1)


if __name__ == "__main__":
    main()
'''

RUN_SH = """#!/bin/sh
# Verify this replication package. Set PYTHON to an interpreter that has the packages in requirements.txt.
# The Python version the package was recorded under is on the first line of requirements.txt. With uv:
#   uv venv --python <that version> .venv && uv pip install --python .venv/bin/python -r requirements.txt
#   PYTHON=.venv/bin/python ./run.sh
# Pass --refetch to compare the pinned sources with the live ones.
set -e
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
exec "$PY" verify.py --python "$PY" "$@"
"""


def readme(m: dict) -> str:
    c, d, code, env = m["claim"], m["data"], m["code"], m["environment"]
    reg, out = c["registration"], c["outcome"] or {}
    dec = m["deciding"]
    copied = [f for f in m["inputs"]["files"] if f["copied"]]
    pointer = [f for f in m["inputs"]["files"] if not f["copied"]]
    L = []
    L.append(f"# Replication package: {c['id']}\n")
    L.append(f"This folder lets a reader check one claim from the NYC concordance project without the repository. "
             f"The claim is: {reg['statement']}\n")
    L.append(f"It was registered at {reg.get('registered_at')} with sha256 `{c['registration_sha256']}`"
             + (f", in commit `{c['registration_commit']['commit'][:12]}`" if c.get("registration_commit") else "")
             + (f". The branch `{c['prereg_branch']['name']}` on the project's GitHub remote points at `{c['prereg_branch']['sha'][:12]}`."
                if c["prereg_branch"].get("sha") else ". No `prereg/` branch was found on the remote.")
             + f" The outcome is `{out.get('verdict')}`, decided at {out.get('decided_at')}.\n")
    if dec.get("available"):
        rec = dec["recorded"]
        L.append("## The deciding number\n")
        L.append(f"The deciding number is the {dec['what']}. The recorded value is "
                 + ", ".join(f"{k} = {v}" for k, v in rec.items())
                 + f". The registered condition that decides the verdict is \"{dec['decides']}\". "
                 f"`verify.py` accepts a rerun when each value lies within its tolerance: "
                 + ", ".join(f"{k} within {t}" for k, t in dec["tolerance"].items()) + ".\n")
        L.append(f"{dec['wrapper_note']}\n")
        if dec.get("placebo"):
            L.append("The rerun also recomputes the claim's placebo, and `verify.py` compares it with the recorded value in the "
                     "same way: " + "; ".join(f"{k} = {v['value']} (within {v['tol']}), {v['what']}, recorded in {v['from']}"
                                               for k, v in dec["placebo"].items()) + ".\n")
    pyv = env["python"].split()[0]
    L.append("## How to run it\n")
    L.append(f"Install Python {pyv}, the version the package was recorded under, and the pinned packages, then run the check. "
             f"With uv, which can install that Python itself:\n")
    L.append(f"```\nuv venv --python {pyv} .venv\nuv pip install --python .venv/bin/python -r requirements.txt\n"
             "PYTHON=.venv/bin/python ./run.sh\n```\n")
    L.append(f"Without uv, use a Python {pyv} interpreter from python.org or a package manager: "
             f"`python{'.'.join(pyv.split('.')[:2])} -m venv .venv && .venv/bin/pip install -r requirements.txt`. "
             "Do not rely on whichever `python3` is first on the PATH; on some machines it is an Anaconda build of another version.\n")
    L.append(f"The packages were recorded under Python {pyv} on {env['os']} ({env['machine']}). "
             "The full `uv pip freeze` of the project's environment is in `manifest.json` under `environment`. "
             "The check prints MATCH when every copied input has its recorded sha256 and the rerun reproduces the deciding "
             "number within tolerance, DRIFT when an input differs from its pin, and MISMATCH when the inputs are intact "
             "but the number differs, which points to a change in code or environment. "
             "`./run.sh --refetch` also re-runs each pinned query" + (" and the NOAA download" if any(e.get("type") == "noaa" for e in d) else "")
             + " and reports whether the live sources still match their pins. No key is needed for these. "
             + ("With `--refetch` the deciding number is also recomputed from the live data, and `live_number_within_tolerance` "
                "says whether it still agrees; DRIFT with that flag true means the sources changed but the number did not. "
                if dec.get("refetch_rerun") else
                "With `--refetch` the deciding number is not recomputed from live data, because the derived tables it reads "
                "come from upstream stages that are not packaged; DRIFT then says only that a pinned source has changed. ")
             + ("NCEI rewrites the NOAA station file every day, so `--refetch` will report DRIFT for it whenever a day has passed. "
                if any(e.get("type") == "noaa" for e in d) else "")
             + "A run writes `verify_result.json`, and `--refetch` writes `refetched/`, inside the package; the rerun may also "
             "write `work/` and `code/data/`. These are listed in `.gitignore`.\n")
    L.append("## What is pinned\n")
    L.append(f"The folder `inputs/` holds {len(copied)} files ({sum(f['bytes'] for f in copied) / 2**20:.1f} MB), each with "
             "its sha256 in `manifest.json`. They keep the paths they have in the repository. ")
    socs = [e for e in d if e.get("type") == "socrata"]
    if socs:
        L.append("For each NYC Open Data source the manifest gives the dataset id, its `rowsUpdatedAt` at fetch time, the exact "
                 "SoQL query, the fetch time and the sha256 of the cached response (and of its rows alone, which is what "
                 "`--refetch` compares). The city rewrites these tables in place (see the project's audit "
                 "`docs/underlay_drift.md`), so the cached response is the only copy of the data as they were used. ")
    if any(e.get("type") == "noaa" for e in d):
        if any(e.get("file", {}).get("full_sha256") for e in d):
            L.append("The NOAA station file is too large to copy whole, so `inputs/` holds a slice of it (the columns the code "
                     "reads, all rows), with the Last-Modified header. The manifest gives the sha256 of the slice and of the "
                     "whole file, and the rule that makes one from the other (`inputs.files[].sliced_from`). NCEI updates "
                     "the file daily. ")
        else:
            L.append("The NOAA station file is copied whole with its Last-Modified header. NCEI updates it daily. ")
    pr = [f for f in m["inputs"]["files"] if f.get("prepared_from")]
    if pr:
        L.append("Some inputs are cut from files too large to carry: " + "; ".join(
            f"`{f['path']}` ({f['bytes'] / 2**20:.1f} MB), {f['what']}" for f in pr)
            + ". `code/prepare.py` is the code that cut them; the files it reads are listed with their sha256 under "
            "`inputs.files[].prepared_from` in the manifest: " + "; ".join(
            f"`{x['source']}`" + (f" ({x['bytes'] / 2**20:.1f} MB, sha256 `{x['sha256'][:16]}...`)" if x.get("sha256") else "")
            for x in pr[0]["prepared_from"]) + ". ")
    sl = [f for f in m["inputs"]["files"] if f.get("sliced_from") and "noaa" not in f["path"]]
    if sl:
        L.append("These inputs are slices of larger files, with the sha256 of both and the rule in the manifest: "
                 + "; ".join(f"`{f['path']}` ({f['bytes'] / 2**20:.1f} MB of {f['sliced_from']['bytes'] / 2**20:.1f} MB)" for f in sl) + ". ")
    L.append(f"The analysis code the rerun imports is copied into `code/`, with the git blob hash and last commit of each "
             f"file in the manifest. The repository commit at packaging time was `{code['repo_commit'][:12]}`. "
             f"{code['procedure_note']}\n")
    L.append("## What is only pointed to\n")
    pl = []
    for f in pointer:
        pl.append(f"- `{f['path']}` ({f['bytes'] / 2**20:.1f} MB, sha256 `{f['sha256'][:16]}...`): {f['role']}; {f.get('why_not_copied', '')}.")
    for e in d:
        if e.get("type") == "big-file":
            pl.append(f"- `{e['path']}`" + (f" ({e['bytes'] / 2**20:.1f} MB, sha256 `{e['sha256'][:16]}...`)" if e.get("sha256") else "")
                      + f": {e['role']}. It is kept outside the repository and is not included.")
        elif e.get("type") == "socrata" and not e.get("cache_files"):
            pl.append(f"- NYC Open Data `{e['dataset']}` ({e['record'].get('name')}): no cached response was found, so only the "
                      "query and `rowsUpdatedAt` are recorded.")
        elif e.get("type") in ("pointer",) and not e.get("file"):
            nm = e["record"].get("name") or e["record"].get("url") or e.get("kind")
            pl.append(f"- {nm}: recorded in the outcome as a {e.get('kind')} source; no file is pinned.")
        elif e.get("type") == "sysgraph" and e.get("cached_requests"):
            pl.append(f"- The System Public Graph ({e['release']}): {len(e.get('cached_requests', []))} cached API responses for "
                      "the relationships named in the registration are copied, but the graph itself is only pointed to. "
                      "Fetching more needs your own API key, which you supply in `~/.config/system/token`; no key is included here.")
        elif e.get("type") == "underlay":
            pl.append(f"- Underlay collection `{e['collection']}` version {e['version']}, hash `{e['hash']}`, ARK {e.get('ark')}.")
    L.append("\n".join(pl) + "\n" if pl else "Nothing.\n")
    nr = m.get("not_rebuilt") or []
    L.append("## Tables this package cannot rebuild\n")
    if not nr:
        L.append("None. The rerun starts from the copied source responses and computes every intermediate table itself.\n")
    else:
        L.append("The rerun starts from intermediate tables that it reads but cannot rebuild from what the package carries. "
                 "Each is copied with its sha256; the inputs it was built from are listed with the place in `manifest.json` "
                 "(under `not_rebuilt`) where each is pointed to by hash.\n")
        for t in nr:
            parts = []
            for b in t["built_from"]:
                if b.get("dataset"):
                    parts.append(f"NYC Open Data `{b['dataset']}` ({b.get('name')}), {b['pages']} cached page(s), "
                                 f"{(b['bytes'] or 0) / 2**20:.1f} MB, " + ("copied" if b["copied"] else "pointed to by sha256 in `data[]`"))
                elif b.get("path"):
                    parts.append(f"`{b['path']}`" + (f" ({b['bytes'] / 2**20:.1f} MB, sha256 `{b['sha256'][:16]}...`)" if b.get("sha256") else " (no hash recorded)")
                                 + (", copied" if b.get("copied") else ", pointed to by hash"))
                else:
                    parts.append(f"{b['source'].split(':', 1)[1]} ({b.get('note')})")
            L.append(f"- `{t['table']}`" + (f" (sha256 `{t['table_sha256'][:16]}...`)" if t.get("table_sha256") else "")
                     + f" was built by `{t['built_by']}` from: " + "; ".join(parts)
                     + f". It cannot be rebuilt here because {t['why_not_rebuilt']}.")
        L.append("")
    if dec.get("available") and dec.get("upstream_note"):
        L.append(dec["upstream_note"] + "\n")
    L.append("## What a stranger needs\n")
    L.append(f"A stranger needs Python {env['python'].split()[0]} with the packages in `requirements.txt` and this folder. The check reads only files "
             "inside the folder and makes no network request unless `--refetch` is given. Re-fetching the pinned sources "
             "needs network access but no key. "
             + ("Anything that touches the System graph beyond the copied responses needs the reader's own System API key, "
                "supplied by the reader; no key is included. " if any(e.get("type") == "sysgraph" for e in d) else "")
             + "The registration, outcome, revision history and referee report paths are in "
             "`manifest.json` under `claim`; the referee reports themselves are in the project repository.\n")
    return "\n".join(L)


# --------------------------------------------------------------------------- Underlay JSONL

def underlay_records(m: dict, pkg: Path) -> None:
    from tools.underlay_export import _clean, record_hash
    cid = m["claim"]["id"]
    pid = f"replication/{cid}"
    recs = []
    for i, f in enumerate(m["inputs"]["files"]):
        recs.append({"id": f"{pid}/input/{i}", "type": "PackageInput", "data": _clean({
            "package": pid, "path": f["path"], "sha256": f["sha256"], "bytes": f["bytes"], "role": f["role"],
            "copied": f["copied"], "rows_sha256": f.get("rows_sha256")})})
    for i, s in enumerate(m["code"]["scripts"]):
        recs.append({"id": f"{pid}/code/{i}", "type": "PackageCode", "data": _clean({
            "package": pid, "path": s["path"], "blob": s.get("blob"), "last_commit": s.get("last_commit"),
            "found_by": s["found_by"], "sha256": s.get("sha256")})})
    for i, e in enumerate(m["data"]):
        d = {k: v for k, v in e.items() if k != "record"}
        recs.append({"id": f"{pid}/source/{i}", "type": "PackageSource", "data": _clean({"package": pid, **json.loads(json.dumps(d))})})
    c = m["claim"]
    recs.append({"id": pid, "type": "ReplicationPackage", "data": _clean({
        "claim": cid, "registration_sha256": c["registration_sha256"], "registration_commit": c.get("registration_commit"),
        "prereg_branch": c["prereg_branch"], "outcome_file_sha256": c.get("outcome_file_sha256"),
        "verdict": (c["outcome"] or {}).get("verdict"), "repo_commit": m["code"]["repo_commit"],
        "deciding": {k: v for k, v in m["deciding"].items() if k in ("what", "recorded", "tolerance", "decides")},
        "python": m["environment"]["python"].split()[0], "platform": m["environment"]["platform"],
        "manifest_sha256": sha256_file(pkg / "manifest.json"),
        "inputs": [r["id"] for r in recs if r["type"] == "PackageInput"],
        "code": [r["id"] for r in recs if r["type"] == "PackageCode"],
        "sources": [r["id"] for r in recs if r["type"] == "PackageSource"]})})
    schemas = {
        "ReplicationPackage": {"$schema": "http://json-schema.org/draft-07/schema#", "type": "object",
                               "description": "A replication package for one registered claim (tools/replicate.py).",
                               "properties": {"claim": {"type": "string", "x-ref-type": "Claim"}, "registration_sha256": {"type": "string"},
                                              "manifest_sha256": {"type": "string"},
                                              "inputs": {"type": "array", "items": {"type": "string", "x-ref-type": "PackageInput"}},
                                              "code": {"type": "array", "items": {"type": "string", "x-ref-type": "PackageCode"}},
                                              "sources": {"type": "array", "items": {"type": "string", "x-ref-type": "PackageSource"}}},
                               "required": ["claim", "registration_sha256", "inputs"]},
        "PackageInput": {"$schema": "http://json-schema.org/draft-07/schema#", "type": "object",
                         "properties": {"package": {"type": "string", "x-ref-type": "ReplicationPackage"}, "path": {"type": "string"},
                                        "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"}, "bytes": {"type": "integer"},
                                        "copied": {"type": "boolean"}}, "required": ["package", "path", "sha256"]},
        "PackageCode": {"$schema": "http://json-schema.org/draft-07/schema#", "type": "object",
                        "properties": {"package": {"type": "string", "x-ref-type": "ReplicationPackage"}, "path": {"type": "string"},
                                       "blob": {"type": "string"}}, "required": ["package", "path"]},
        "PackageSource": {"$schema": "http://json-schema.org/draft-07/schema#", "type": "object",
                          "properties": {"package": {"type": "string", "x-ref-type": "ReplicationPackage"}, "type": {"type": "string"}},
                          "required": ["package"]},
    }
    ud = pkg / "underlay"
    ud.mkdir(exist_ok=True)
    (ud / "schemas.json").write_text(json.dumps(schemas, indent=1))
    with open(ud / "records.jsonl", "w") as fh:
        for r in recs:
            fh.write(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n")
    counts = {}
    for r in recs:
        counts[r["type"]] = counts.get(r["type"], 0) + 1
    (ud / "manifest.json").write_text(json.dumps({
        "note": "Written for an Underlay push; nothing has been pushed. Hashes follow tools/underlay_export.record_hash (RFC 8785).",
        "collection_suggestion": "nyc-concordance/replication", "counts": counts,
        "records": {r["id"]: record_hash(r["id"], r["type"], r["data"]) for r in recs}}, indent=1))


# --------------------------------------------------------------------------- trace

TRACER = r'''
import json, os, runpy, sys
reads, writes = set(), set()
W = os.O_WRONLY | os.O_RDWR | os.O_APPEND | os.O_CREAT
def hook(ev, args):
    if ev != "open" or not args or not isinstance(args[0], (str, bytes, os.PathLike)):
        return
    path = os.path.abspath(os.fsdecode(args[0]))
    mode = args[1] if len(args) > 1 else None
    flags = args[2] if len(args) > 2 else 0
    w = (isinstance(mode, str) and any(c in mode for c in "wax+")) or (isinstance(flags, int) and flags & W)
    (writes if w else reads).add(path)
sys.addaudithook(hook)
out = os.environ["TRACE_OUT"]
sys.argv = sys.argv[1:]
try:
    runpy.run_path(sys.argv[0], run_name="__main__")
finally:
    with open(out, "w") as fh:
        json.dump({"reads": sorted(reads), "writes": sorted(writes)}, fh)
'''


PREPARE_HEAD = '''"""Build the prepared inputs of this package from the files they are cut from.

The builder ran this file once, with ROOT the repository, OPT ~/opt/nyc-concordance and OUT the folder whose
contents became inputs/prepared/. A reader who has the source files (pointed to by sha256 in manifest.json,
inputs.files[].prepared_from) can run it the same way and compare the sha256 of each output.
    python code/prepare.py ROOT OPT OUT
"""
import sys
from pathlib import Path
ROOT, OPT, OUT = (Path(a) for a in sys.argv[1:4])
sys.path.insert(0, str(ROOT))
'''


def run_prepare(prep: dict, pkg: Path) -> dict:
    """Run a recipe's prepare code with the project's Python. It cuts the rows the rerun needs from inputs too
    large to carry and writes them under OUT/prepared/. Returns the folder and the source hashes."""
    import tempfile
    out = Path(tempfile.mkdtemp(prefix=f"replicate-prepare-{pkg.name}-"))
    code = PREPARE_HEAD + prep["code"]
    (pkg / "code").mkdir(parents=True, exist_ok=True)
    (pkg / "code" / "prepare.py").write_text(code)
    r = subprocess.run([str(VENV / "bin" / "python"), str(pkg / "code" / "prepare.py"), str(ROOT), str(OPT), str(out)],
                       capture_output=True, text=True, timeout=3600)
    if r.returncode:
        raise SystemExit(f"prepare failed:\n{r.stderr[-2000:]}")
    sources = []
    for src in prep["sources"]:
        kind, _, val = src.partition(":")
        if kind == "opt":
            f = OPT / val
            sources.append({"source": f"~/opt/nyc-concordance/{val}", "bytes": f.stat().st_size, "sha256": sha256_file(f)})
        elif kind == "file":
            f = ROOT / val
            sources.append({"source": val, "bytes": f.stat().st_size, "sha256": sha256_file(f)})
        elif kind == "socrata":
            sources.append({"source": f"socrata:{val}", "note": "the cached pages are listed with their sha256 in data[]"})
        else:
            sources.append({"source": src})
    return {"dir": out, "outputs": prep["outputs"], "sources": sources, "what": prep["what"],
            "stdout_tail": r.stdout[-1000:]}


def trace_rerun(pkg: Path, prepared_dir: Path | None = None) -> dict:
    """Run code/rerun.py against the repository itself (--inputs ROOT) with an audit hook, and return the data
    files it opened for reading, the files it wrote inside the repository, and its printed result. Reads made
    by C libraries (GDAL, Arrow) do not pass the hook, so recipes list such files under "derived"."""
    import tempfile
    tmp = Path(tempfile.mkdtemp(prefix=f"replicate-trace-{pkg.name}-"))  # outside the repository; left for the OS to clear
    shutil.copytree(pkg / "code", tmp / "code")
    inp = ROOT
    if prepared_dir is not None:  # the repository plus the prepared files, as the package will see them
        inp = tmp / "overlay"
        inp.mkdir()
        for child in ROOT.iterdir():
            (inp / child.name).symlink_to(child)
        (inp / "prepared").symlink_to(prepared_dir / "prepared")
    tf = tmp / "trace.json"
    env = {**os.environ, "TRACE_OUT": str(tf)}
    r = subprocess.run([str(VENV / "bin" / "python"), "-c", TRACER, str(tmp / "code" / "rerun.py"), "--inputs", str(inp)],
                       cwd=tmp, capture_output=True, text=True, env=env, timeout=3600)
    t = json.loads(tf.read_text()) if tf.exists() else {"reads": [], "writes": []}
    res = {"returncode": r.returncode, "stderr_tail": r.stderr[-1500:] if r.returncode else None}
    try:
        res["printed"] = json.loads(r.stdout.strip().splitlines()[-1])
    except Exception:  # noqa: BLE001
        res["printed"] = None
    keep, wrote = [], []
    rootr = ROOT.resolve()
    for f in t["reads"]:
        fp = Path(f)
        try:
            rp = fp.resolve().relative_to(rootr)
        except ValueError:
            continue
        if rp.parts[0] in ("replication", "_trash", ".git") or fp.suffix in (".py", ".pyc") or not fp.is_file():
            continue
        keep.append(str(rp))
    for f in t["writes"]:
        try:
            rp = Path(f).resolve().relative_to(rootr)
        except ValueError:
            continue
        if rp.parts[0] != "replication":
            wrote.append(str(rp))
    res["reads"], res["writes_in_repo"] = sorted(set(keep)), sorted(set(wrote))
    return res


# --------------------------------------------------------------------------- main

def build(cid: str, cap_mb: float, underlay: bool) -> Path:
    recipe = RECIPES.get(cid)
    pkg = ROOT / "replication" / cid
    if pkg.exists():
        # keep earlier packages: move rather than delete
        stamp = time.strftime("%Y-%m-%dT%H%M%S")
        dest = ROOT / "_trash" / time.strftime("%Y-%m-%d") / f"replication-{cid}-{stamp}"
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(pkg), str(dest))
    pkg.mkdir(parents=True)
    claim = claim_section(cid)
    trace = None
    prepared = None
    if recipe and recipe.get("prepare"):
        prepared = run_prepare(recipe["prepare"], pkg)
    if recipe:
        for p in recipe["code"]:
            dst = pkg / "code" / p
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / p, dst)
        (pkg / "code" / "rerun.py").write_text(recipe["wrapper"])
        if recipe.get("trace", True):
            trace = trace_rerun(pkg, prepared["dir"] if prepared else None)
            if trace["returncode"]:
                raise SystemExit(f"the wrapper failed in the repository:\n{trace['stderr_tail']}")
            if trace["writes_in_repo"]:
                raise SystemExit(f"the wrapper wrote inside the repository: {trace['writes_in_repo']}")
            recipe = {**recipe, "_traced": trace["reads"]}
    inputs = Inputs(int(cap_mb * 2**20), only_required=bool(recipe and recipe.get("trace", True)))
    if prepared:
        for o in prepared["outputs"]:
            f = prepared["dir"] / o
            inputs.files.append({"path": o, "bytes": f.stat().st_size, "sha256": sha256_file(f),
                                 "role": "prepared input, read by the rerun", "copied": True, "required_for_rerun": True,
                                 "prepared_from": prepared["sources"], "prepared_by": "code/prepare.py",
                                 "what": prepared["what"], "_src": str(f)})
            inputs.used += f.stat().st_size
    if recipe and recipe.get("slices"):
        import tempfile
        stmp = Path(tempfile.mkdtemp(prefix="replicate-slice-"))
        for sl in recipe["slices"]:
            inputs.add_slice(ROOT / sl["path"], sl, stmp)
    data = data_section(claim, recipe, inputs)
    not_rebuilt = not_rebuilt_section(recipe, data, inputs)
    code = code_section(cid, claim, recipe)
    env = environment(recipe)
    out = claim["outcome"] or {}
    deciding = {"available": recipe is not None}
    if recipe:
        ce = out.get("city_effect") or {}
        dd = recipe["deciding"]
        recorded = {k: ce.get(k) for k in dd["keys"]}
        tol = dict(dd["keys"])
        for k, v in {**dd["extra_recorded"], **dd.get("placebo", {})}.items():
            recorded[k] = v["value"]
            tol[k] = v["tol"]
        deciding.update({"what": dd["what"], "recorded": recorded, "tolerance": tol, "decides": dd["decides"],
                         "recorded_from": {"city_effect": "claims/outcomes/" + cid + ".json",
                                           **{k: v["from"] for k, v in {**dd["extra_recorded"], **dd.get("placebo", {})}.items()}},
                         "wrapper": "code/rerun.py", "wrapper_note": recipe["wrapper_note"],
                         "refetch_rerun": recipe["refetch_rerun"]})
        if dd.get("placebo"):
            deciding["placebo"] = {k: {kk: vv for kk, vv in v.items()} for k, v in dd["placebo"].items()}
        if trace:
            deciding["trace_run_in_repository"] = {"printed": trace["printed"], "files_read": len(trace["reads"])}
    # copy inputs
    for f in inputs.files:
        if f["copied"]:
            dst = pkg / "inputs" / f["path"]
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(f.pop("_src", None) or (ROOT / f["path"]), dst)
    if recipe:
        (pkg / "requirements.txt").write_text(f"# Python {env['python'].split()[0]}\n" + "\n".join(env["requirements"]) + "\n")
    m = {"package": {"claim": cid, "built_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "tool": "tools/replicate.py",
                     "tool_blob": git("hash-object", "tools/replicate.py"),
                     "paths": "relative to the repository (inputs keep their repo paths under inputs/) or to ~/opt/nyc-concordance"},
         "claim": claim, "code": code, "data": data, "environment": env,
         "inputs": {"cap_bytes": inputs.cap, "copied_bytes": inputs.used, "files": inputs.files},
         "deciding": deciding, "not_rebuilt": not_rebuilt}
    if trace:
        m["inputs"]["traced"] = True
    (pkg / "manifest.json").write_text(json.dumps(m, indent=1, ensure_ascii=False, default=str))
    (pkg / "verify.py").write_text(VERIFY)
    (pkg / "run.sh").write_text(RUN_SH)
    os.chmod(pkg / "run.sh", 0o755)
    (pkg / "README.md").write_text(readme(m))
    (pkg / ".gitignore").write_text("# written by verify.py and code/rerun.py\nrefetched/\nwork/\nverify_result.json\n"
                                    "code/data/\ncode/figures/\n__pycache__/\n.venv/\n")
    if underlay:
        underlay_records(m, pkg)
    return pkg


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("claim")
    ap.add_argument("--cap-mb", type=float, default=DEFAULT_CAP_MB)
    ap.add_argument("--underlay", action="store_true", help="also write underlay/ JSONL records (nothing is pushed)")
    a = ap.parse_args(argv)
    if not (REG / f"{a.claim}.json").exists():
        raise SystemExit(f"no registration claims/registered/{a.claim}.json")
    pkg = build(a.claim, a.cap_mb, a.underlay)
    m = json.loads((pkg / "manifest.json").read_text())
    print(json.dumps({"package": rel(pkg), "inputs_copied": sum(f["copied"] for f in m["inputs"]["files"]),
                      "inputs_pointer_only": sum(not f["copied"] for f in m["inputs"]["files"]),
                      "copied_mb": round(m["inputs"]["copied_bytes"] / 2**20, 1), "scripts": len(m["code"]["scripts"]),
                      "rerun": m["deciding"]["available"]}, indent=1))


if __name__ == "__main__":
    main()
