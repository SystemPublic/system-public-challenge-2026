"""Shared definitions for the EMS response-time decomposition (docs/ems_response.md)."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DER = ROOT / "data" / "derived" / "ems_response"
FIG = ROOT / "figures" / "ems_response"
DER.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)
OPT = Path.home() / "opt" / "nyc-concordance"
TLC_LOCAL = [OPT / "tlc_yellow_1720", OPT / "tlc_yellow", OPT / "ems_response" / "tlc"]
TLC_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data/"
SRGB = "/System/Library/ColorSync/Profiles/sRGB Profile.icc"
EMS = "76xm-jjuj"
SEED = 20261113
