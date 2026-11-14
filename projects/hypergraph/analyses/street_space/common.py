"""Shared definitions for the 14th Street busway tests (fixed before registration).

The 14th Street Transit and Truck Priority pilot (the busway) began on Thursday 3 October 2019,
06:00 to 22:00 every day, on 14th Street between 3rd and 9th Avenues (NYC DOT; Sam Schwartz
Engineering preliminary report, fall 2019). Through traffic other than buses and trucks must
turn off at the next avenue. The M14 Select Bus Service began on 1 July 2019. The L train
weeknight and weekend slowdown ran from 27 April 2019 to 26 April 2020. The Manhattan
congestion surcharge on taxi trips began on 2 February 2019 and applies to every pair below.

Zones are TLC taxi zones. A directed pair is (pickup zone, drop-off zone).
Treated pairs cross Fifth Avenue between a zone west of it that touches 14th Street and a
zone east of it that touches 14th Street. Control pairs make a comparable east-west crossing
of Fifth Avenue (or of Broadway/Lafayette downtown) far from 14th Street.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DER = ROOT / "data" / "derived" / "street_space"
FIG = ROOT / "figures" / "street_space"
TLC = Path.home() / "opt" / "nyc-concordance" / "tlc_yellow_1720"
PAIRS = Path.home() / "opt" / "nyc-concordance" / "street_space"  # pair aggregates (50 MB each), outside Dropbox
TLC_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_{m}.parquet"

GROUPS = {
    # 14th Street crosstown: west side <-> east side
    "t14": ({158: "Meatpacking/West Village West", 249: "West Village", 68: "East Chelsea", 113: "Greenwich Village North"},
            {79: "East Village", 224: "Stuy Town/Peter Cooper Village", 4: "Alphabet City", 107: "Gramercy"}),
    # Midtown crosstown (34th to 57th Streets)
    "c_mid": ({48: "Clinton East", 50: "Clinton West", 100: "Garment District", 230: "Times Sq/Theatre District"},
              {170: "Murray Hill", 162: "Midtown East", 233: "UN/Turtle Bay South", 229: "Sutton Place/Turtle Bay North"}),
    # Downtown crosstown (Canal, Houston, Delancey)
    "c_down": ({231: "TriBeCa/Civic Center", 125: "Hudson Sq", 211: "SoHo"},
               {148: "Lower East Side", 232: "Two Bridges/Seward Park", 144: "Little Italy/NoLiTa", 45: "Chinatown"}),
}

START = "2019-10-03"
# Windows: same calendar months a year apart, ending before the pandemic.
PRE = ("2018-10-03", "2019-02-28")
POST = ("2019-10-03", "2020-02-29")
PLACEBO_PRE = ("2017-10-03", "2018-02-28")
PLACEBO_POST = PRE

SEED = 20261113
DRAWS = 2000
MIN_TRIPS = 200  # a directed pair is used only with at least this many trips in each window


def all_zones():
    z = set()
    for w, e in GROUPS.values():
        z |= set(w) | set(e)
    return sorted(z)


def pair_group(pu: int, do: int):
    for g, (w, e) in GROUPS.items():
        if (pu in w and do in e) or (pu in e and do in w):
            return g
    return None
