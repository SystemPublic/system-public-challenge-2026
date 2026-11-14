"""Shared paths and helpers for the bridge analyses."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
DER = ROOT / "data" / "derived" / "bridges"
FIG = ROOT / "figures" / "bridges"
DER.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)
SRGB = "/System/Library/ColorSync/Profiles/sRGB Profile.icc"
SEED = 20261112
NDRAW = 200_000


def savefig(fig, name: str) -> str:
    p = FIG / name
    fig.savefig(p, dpi=160, bbox_inches="tight")
    subprocess.run(["sips", "--embedProfile", SRGB, str(p)], capture_output=True)
    return str(p.relative_to(ROOT))
