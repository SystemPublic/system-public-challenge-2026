"""Shared helpers for the heat analyses."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
DER = ROOT / "data" / "derived" / "heat"
FIG = ROOT / "figures" / "heat"
DER.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)


def holidays(start: str, end: str) -> pd.DatetimeIndex:
    from pandas.tseries.holiday import USFederalHolidayCalendar
    h = USFederalHolidayCalendar().holidays(start, end)
    extra = [pd.Timestamp(f"{y}-{md}") for y in range(pd.Timestamp(start).year, pd.Timestamp(end).year + 1)
             for md in ("07-04", "12-31", "01-01")]
    return h.union(pd.DatetimeIndex(extra))


def tag_srgb(path: Path):
    subprocess.run(["sips", "--embedProfile", "/System/Library/ColorSync/Profiles/sRGB Profile.icc", str(path)],
                   check=False, capture_output=True)


def rel(p: Path) -> str:
    return str(Path(p).resolve().relative_to(ROOT))


def irr_row(res, name: str, scale: float = 1.0) -> dict:
    b = res.params[name] * scale
    se = res.bse[name] * scale
    return {"estimate": float(np.exp(b)), "lo": float(np.exp(b - 1.96 * se)), "hi": float(np.exp(b + 1.96 * se)),
            "p": float(res.pvalues[name])}
