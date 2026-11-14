"""Turn a product-temperature trace into advice, using a drug storage profile.

Three tiers, and only three (the honesty rule):

* ``use_as_normal``          - within label
* ``check_with_pharmacist``  - beyond label, but within what studies tested
* ``request_replacement``    - beyond what studies tested (or reached a level
                                where a study found loss / malfunction)

No potency percentage is ever computed or returned.
The exact rule text lives in drug_storage_profiles.json ("rule_details").
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import numpy as np

from .metrics import mkt_c
from .params import v

REPO = Path(__file__).resolve().parents[2]
PROFILES_PATH = REPO / "data" / "processed" / "drug_storage_profiles.json"

TIER_RANK = {"use_as_normal": 0, "check_with_pharmacist": 1, "request_replacement": 2}
ACTION = {
    "use_as_normal": "Use as normal",
    "check_with_pharmacist": "Check with your pharmacist",
    "request_replacement": "Request a replacement",
}
HARM = {"loss", "device_failure", "measurement_error"}


def load_profiles(path: Path = PROFILES_PATH) -> Dict[str, dict]:
    data = json.loads(Path(path).read_text())
    return {p["id"]: p for p in data["profiles"]}


def _cite(ev: dict) -> str:
    c = ev.get("citation") or {}
    ident = f"PMID {c['pmid']}" if c.get("pmid") else (f"DOI {c['doi']}" if c.get("doi") else c.get("url", ""))
    return f"{c.get('text', '')} ({ident}; {c.get('status', '')})"


def f_of_c(c: float) -> float:
    return c * 9.0 / 5.0 + 32.0


def assess(temps_c: Sequence[float], profile: dict, dt_s: Optional[float] = None) -> dict:
    """Advice for one exposure trace (first sample = initial state)."""
    dt = dt_s if dt_s is not None else v("num", "dt_s")
    t = np.asarray(temps_c, float)
    body = t[1:] if len(t) > 1 else t
    peak = float(t.max())
    low = float(t.min())
    lab = profile["label"]

    def hours_above(thr: float) -> float:
        return float(np.sum(body > thr) * dt / 3600.0)

    def hours_at_or_above(thr: float) -> float:
        return float(np.sum(body >= thr) * dt / 3600.0)

    h_above_label = hours_above(lab["max_c"])
    reasons: List[str] = []
    matched: Optional[str] = None
    high_breach = peak > lab["max_c"]
    spike_ok = False
    if high_breach and lab.get("spike"):
        sp = lab["spike"]
        spike_ok = peak <= sp["max_c"] and h_above_label <= sp["max_hours"]
    low_breach = low < lab["min_c"]

    tier: str
    if not low_breach and (not high_breach or spike_ok):
        tier = "use_as_normal"
        if spike_ok:
            reasons.append(
                f"Peaked at {peak:.1f} C ({f_of_c(peak):.0f} F), above {lab['max_c']:.0f} C for "
                f"{h_above_label * 60:.0f} min: inside the label's allowed short spike "
                f"(up to {lab['spike']['max_c']:.0f} C for up to {lab['spike']['max_hours']:.0f} h).")
        else:
            reasons.append(
                f"Stayed between {low:.1f} and {peak:.1f} C, inside the labeled "
                f"{lab['min_c']:.0f}-{lab['max_c']:.0f} C range.")
    else:
        tier = "request_replacement"
        if low_breach:
            reasons.append(
                f"Fell to {low:.1f} C, below the label minimum of {lab['min_c']:.0f} C; "
                "no study in our evidence base tested this.")
        if high_breach:
            reasons.append(
                f"Peaked at {peak:.1f} C ({f_of_c(peak):.0f} F) and spent {h_above_label * 60:.0f} min "
                f"above the label maximum of {lab['max_c']:.0f} C.")
            if lab.get("hard_max_c") is not None and peak > lab["hard_max_c"]:
                reasons.append(f"Exceeded the label's hard limit of {lab['hard_max_c']:.0f} C.")
            harm_hit = None
            for ev in profile.get("evidence", []):
                ex = ev.get("exposure") or {}
                if not ev.get("used_in_rule") or ev.get("outcome") not in HARM:
                    continue
                if ex.get("temp_c") is None or ex.get("hours") is None:
                    continue
                if peak >= ex["temp_c"] and hours_at_or_above(ex["temp_c"]) >= ex["hours"]:
                    harm_hit = ev
                    break
            if harm_hit is not None:
                matched = harm_hit["id"]
                reasons.append(
                    f"Reached at least {harm_hit['exposure']['temp_c']:.0f} C for at least "
                    f"{harm_hit['exposure']['hours'] * 60:.0f} min, where a study found problems: "
                    f"{_cite(harm_hit)}.")
            elif not low_breach and (lab.get("hard_max_c") is None or peak <= lab["hard_max_c"]):
                for ev in profile.get("evidence", []):
                    ex = ev.get("exposure") or {}
                    if not ev.get("used_in_rule") or ev.get("outcome") != "no_meaningful_change":
                        continue
                    if ex.get("mode") != "constant" or ex.get("temp_c") is None or ex.get("hours") is None:
                        continue
                    if ex["temp_c"] <= lab["max_c"]:
                        continue
                    if peak <= ex["temp_c"] and h_above_label <= ex["hours"]:
                        tier = "check_with_pharmacist"
                        matched = ev["id"]
                        reasons.append(
                            f"Within what a study tested: held at {ex['temp_c']:.0f} C for "
                            f"{ex['hours'] / 24:.0f} days without a meaningful loss - {_cite(ev)}.")
                        break
                if tier == "request_replacement":
                    reasons.append("Beyond what any study in our evidence base tested for this product.")
        if tier != "use_as_normal":
            for cav in profile.get("caveats", []):
                reasons.append("Caveat: " + cav)

    return {
        "tier": tier,
        "action": ACTION[tier],
        "message": profile["advice_text"][tier],
        "reasons": reasons,
        "matched_evidence": matched,
        "exposure": {
            "peak_c": round(peak, 3),
            "min_c": round(low, 3),
            "hours_above_label_max": round(h_above_label, 4),
            "mkt_c": round(mkt_c(body, profile.get("mkt_delta_h_kj_mol")), 3),
        },
    }


def worse(a: str, b: str) -> str:
    return a if TIER_RANK[a] >= TIER_RANK[b] else b
