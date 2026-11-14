"""Shared definitions for the congestion-pricing tradeoff analyses.

Areas are sets of ZIP codes, because the EMS, fire, restaurant and licence data all carry a ZIP.
  crz    Manhattan south of 60th Street (the Congestion Relief Zone). ZIP boundaries follow
         59th/60th Street closely; small building ZIPs inside the zone are included by range.
  north  Manhattan from 60th Street to about 110th Street (Upper East and Upper West Side).
  bklic  Downtown Brooklyn (11201, 11217) and Long Island City (11101, 11109).
  rest   every other New York City ZIP.
Toll periods (MTA toll schedule, phase 1): peak 05:00-20:59 on weekdays and 09:00-20:59 at
weekends; overnight otherwise. The toll began at 00:00 on Sunday 5 January 2025.
"""
from __future__ import annotations

import contextlib
import subprocess
from pathlib import Path

from concord import socrata

ROOT = Path(__file__).resolve().parents[2]
DER = ROOT / "data" / "derived" / "congestion"
FIG = ROOT / "figures" / "congestion"
DER.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)
SRGB = "/System/Library/ColorSync/Profiles/sRGB Profile.icc"
TOLL_START = "2025-01-05"

_crz = [str(z) for z in list(range(10001, 10021)) + [10022, 10036, 10038] + list(range(10041, 10049))
        + [10055, 10060, 10080, 10081, 10087, 10090, 10095, 10098, 10099]
        + list(range(10101, 10124)) + list(range(10150, 10180)) + [10199]
        + list(range(10256, 10287))]
CRZ_ZIPS = sorted(set(_crz) - {"10008", "10015"} | {"10008", "10015"})
NORTH_ZIPS = ["10021", "10023", "10024", "10025", "10028", "10065", "10069", "10075", "10128"]
BKLIC_ZIPS = ["11201", "11217", "11101", "11109"]


def area_of_zip(z) -> str:
    z = str(z)[:5]
    if z in CRZ_ZIPS:
        return "crz"
    if z in NORTH_ZIPS:
        return "north"
    if z in BKLIC_ZIPS:
        return "bklic"
    return "rest"


def area_case(col: str = "zipcode") -> str:
    q = lambda zs: ",".join(f"'{z}'" for z in zs)
    return (f"case({col} in ({q(CRZ_ZIPS)}), 'crz', {col} in ({q(NORTH_ZIPS)}), 'north', "
            f"{col} in ({q(BKLIC_ZIPS)}), 'bklic', true, 'rest')")


def is_peak(dow, hour):
    """dow: Monday=0. Vectorised over pandas Series."""
    wk = dow < 5
    return (wk & (hour >= 5) & (hour < 21)) | (~wk & (hour >= 9) & (hour < 21))


@contextlib.contextmanager
def domain(d: str):
    old = socrata.DOMAIN
    socrata.DOMAIN = f"https://{d}"
    try:
        yield
    finally:
        socrata.DOMAIN = old


def nys(dataset: str, all_pages: bool = False, **soql):
    with domain("data.ny.gov"):
        rows, src = (socrata.query_all if all_pages else socrata.query)(dataset, **soql)
    src = dict(src)
    src["url"] = f"https://data.ny.gov/d/{dataset}"
    return rows, src


def savefig(fig, name: str) -> str:
    p = FIG / name
    fig.savefig(p, dpi=160, bbox_inches="tight")
    subprocess.run(["sips", "--embedProfile", SRGB, str(p)], capture_output=True)
    return str(p.relative_to(ROOT))
