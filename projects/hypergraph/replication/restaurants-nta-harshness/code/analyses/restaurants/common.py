"""Shared loaders for the restaurant analyses (43nn-pn8j inspections, erm2-nwe9 311 complaints).

Inspections are fetched one row per (camis, inspection_date, inspection_type) with the score,
grade and number of critical violations, by SoQL aggregation, so that a violation-level table of
some 300,000 rows is not downloaded.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from concord import socrata  # noqa: E402

DER = ROOT / "data" / "derived" / "restaurants"
FIG = ROOT / "figures" / "restaurants"
INSP = "43nn-pn8j"
SR311 = "erm2-nwe9"
SRGB = "/System/Library/ColorSync/Profiles/sRGB Profile.icc"


def inspections(where: str = "inspection_date > '2000-01-02'", tag: str = "all") -> tuple[pd.DataFrame, dict]:
    """One row per inspection visit: camis, dba, boro, bbl, nta, cuisine, date, type, score, grade,
    n_viol (violation rows), n_crit (critical violation rows)."""
    sel = ("camis, dba, boro, bbl, nta, zipcode, cuisine_description, inspection_date, inspection_type, "
           "max(score) as score, max(grade) as grade, count(violation_code) as n_viol, "
           "sum(case(critical_flag='Critical', 1, true, 0)) as n_crit, max(latitude) as lat, max(longitude) as lon")
    grp = "camis, dba, boro, bbl, nta, zipcode, cuisine_description, inspection_date, inspection_type"
    rows, src = socrata.query_all(INSP, select=sel, where=where, group=grp, order=grp)
    df = pd.DataFrame(rows)
    for c in ("score", "n_viol", "n_crit", "lat", "lon"):
        df[c] = pd.to_numeric(df.get(c), errors="coerce")
    df["inspection_date"] = pd.to_datetime(df["inspection_date"].str[:10])
    df["itype"] = df["inspection_type"].fillna("")
    df["program"] = df["itype"].str.split(" / ").str[0]
    df["stage"] = df["itype"].str.split(" / ").str[1]
    src["tag"] = tag
    return df, src


CHAIN_MIN = 10  # a dba with at least this many CAMIS citywide in the live data is a chain


def norm_dba(s: pd.Series) -> pd.Series:
    return s.fillna("").str.upper().str.replace(r"[^A-Z0-9 ]", "", regex=True).str.replace(r"\s+", " ", regex=True).str.strip()


def chain_flag(df: pd.DataFrame) -> pd.Series:
    d = norm_dba(df["dba"])
    n = df.assign(_d=d).groupby("_d")["camis"].nunique()
    return d.map(n).fillna(1) >= CHAIN_MIN


def cuisine_group(s: pd.Series, top: int = 20) -> pd.Series:
    vc = s.fillna("Unknown").value_counts()
    keep = set(vc.index[:top])
    return s.fillna("Unknown").where(s.fillna("Unknown").isin(keep), "Other")


def save_fig(fig, name: str):
    import subprocess
    FIG.mkdir(parents=True, exist_ok=True)
    p = FIG / name
    fig.savefig(p, dpi=150, bbox_inches="tight")
    subprocess.run(["sips", "--embedProfile", SRGB, str(p)], check=True, capture_output=True)
    return p.relative_to(ROOT).as_posix()


def write_json(name: str, obj):
    DER.mkdir(parents=True, exist_ok=True)
    (DER / name).write_text(json.dumps(obj, indent=1, default=str))
