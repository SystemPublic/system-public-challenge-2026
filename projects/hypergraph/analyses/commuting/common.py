"""Shared helpers for the commuting analyses."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DER = ROOT / "data" / "derived" / "commuting"
FIG = ROOT / "figures" / "commuting"
OPT = Path(os.path.expanduser("~/opt/nyc-concordance/commuting"))
for p in (DER, FIG, OPT):
    p.mkdir(parents=True, exist_ok=True)
SRGB = "/System/Library/ColorSync/Profiles/sRGB Profile.icc"
REGISTRANT = "commuting agent (Claude Opus 5.5), 12 Nov 2026"


def fetch(url: str, name: str) -> Path:
    """Download once into ~/opt/nyc-concordance/commuting/ and return the path."""
    f = OPT / name
    if not f.exists():
        subprocess.run(["curl", "-s", "-f", "-L", "-m", "600", "-o", str(f), url], check=True)
    return f


def savefig(fig, name: str) -> str:
    p = FIG / name
    fig.savefig(p, dpi=160, bbox_inches="tight")
    subprocess.run(["sips", "--embedProfile", SRGB, str(p)], capture_output=True)
    return str(p.relative_to(ROOT))
