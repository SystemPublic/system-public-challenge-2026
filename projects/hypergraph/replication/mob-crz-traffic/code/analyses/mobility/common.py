"""Shared helpers for the mobility analyses."""
from __future__ import annotations

import contextlib
import subprocess
from pathlib import Path

from concord import socrata

ROOT = Path(__file__).resolve().parents[2]
DER = ROOT / "data" / "derived" / "mobility"
FIG = ROOT / "figures" / "mobility"
DER.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)
SRGB = "/System/Library/ColorSync/Profiles/sRGB Profile.icc"


@contextlib.contextmanager
def domain(d: str):
    """Point concord.socrata at another Socrata domain (e.g. data.ny.gov) for a block."""
    old = socrata.DOMAIN
    socrata.DOMAIN = f"https://{d}"
    try:
        yield
    finally:
        socrata.DOMAIN = old


def nys(dataset: str, **soql):
    """Query data.ny.gov through concord.socrata, so results carry the same source record."""
    with domain("data.ny.gov"):
        rows, src = socrata.query(dataset, **soql)
    src = dict(src)
    src["url"] = f"https://data.ny.gov/d/{dataset}"
    return rows, src


def savefig(fig, name: str) -> str:
    p = FIG / name
    fig.savefig(p, dpi=160, bbox_inches="tight")
    subprocess.run(["sips", "--embedProfile", SRGB, str(p)], capture_output=True)
    return str(p.relative_to(ROOT))
