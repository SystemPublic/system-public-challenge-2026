"""Loader for the NYC DOHMH Environment and Health Data Portal (EHDP) at a fixed commit."""
from __future__ import annotations

import json
import os
import subprocess

import pandas as pd

SHA = "547482b9df589006543e13e8cdf6546e00ed9998"
RAW = "https://raw.githubusercontent.com/nychealth/EHDP-data/{sha}/indicators/{path}"
DIR = os.path.expanduser("~/opt/nyc-concordance/ehdp")


def _get(path: str, name: str) -> str:
    os.makedirs(DIR, exist_ok=True)
    f = os.path.join(DIR, name)
    if not os.path.exists(f):
        subprocess.run(["curl", "-s", "-f", "-m", "120", "-o", f, RAW.format(sha=SHA, path=path)], check=True)
    return f


def periods() -> pd.Series:
    return pd.DataFrame(json.load(open(_get("metadata/TimePeriods.json", "TimePeriods.json")))).set_index(
        "TimePeriodID")["TimePeriod"]


def measure(indicator: int, measure_id: int, geotype: str = "UHF42") -> pd.DataFrame:
    """Rows of one measure at one geography, with the period label in 'period'."""
    d = pd.DataFrame(json.load(open(_get(f"data/{indicator}.json", f"{indicator}.json"))))
    d = d[(d["MeasureID"] == measure_id) & (d["GeoType"] == geotype)].copy()
    d["period"] = d["TimePeriodID"].map(periods())
    d["Value"] = pd.to_numeric(d["Value"], errors="coerce")
    d["GeoID"] = d["GeoID"].astype(int)
    return d[["GeoID", "period", "Value", "CI", "Note"]]


def wide(indicator, measure_id, periods_wanted, geotype="UHF42") -> pd.Series:
    d = measure(indicator, measure_id, geotype)
    d = d[d["period"].isin(periods_wanted)]
    return d.groupby("GeoID")["Value"].mean()


def source(indicator: int, measure_id: int, label: str, periods_used) -> dict:
    return {"kind": "ehdp-github", "repo": "github.com/nychealth/EHDP-data", "commit": SHA,
            "file": f"indicators/data/{indicator}.json", "indicator": indicator, "measure": measure_id,
            "label": label, "geotype": "UHF42", "periods": list(periods_used),
            "url": RAW.format(sha=SHA, path=f"data/{indicator}.json")}


BORO = {1: "Bronx", 2: "Brooklyn", 3: "Manhattan", 4: "Queens", 5: "Staten Island"}
