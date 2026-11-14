"""Classify graph candidates: intervention subtype, outcome tier, statistic family, direction and QC flags.

Nothing here is a verdict on study quality. It sorts raw graph associations so a human can review
them, and it flags rows that cannot be plotted honestly (e.g. a percentage stored as a ratio).
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

from common import INTERIM

C = pd.read_csv(INTERIM / "candidates.csv", dtype=str, keep_default_na=False)

RX = lambda p: re.compile(p, re.I)  # noqa: E731

NET_SUBTYPE = [
    ("chlorfenapyr-pyrethroid net", RX(r"chlorfenapyr|interceptor\s*g2|\big2\b|pronet|permanet dual")),
    ("pyriproxyfen-pyrethroid net", RX(r"pyriproxyfen|royal ?guard|olyset duo")),
    ("PBO-pyrethroid net", RX(r"piperonyl|\bpbo\b|olyset plus|permanet 3")),
    ("insecticide-treated net (standard / unspecified)", RX(r".")),
]

# Uptake/behaviour: the net or vaccine is the *outcome* being explained (ownership, use, acceptance).
UPTAKE = RX(r"\buse\b|\busage\b|\busing\b|ownership|\bown(ed|ing)?\b|access|possess|slept|sleep|knowledge|aware"
            r"|attitude|willing|accept|hesitan|hang|adherence|coverage|uptake|retention|utili[sz]")

INTERVENTION_WORD = RX(r"\bnets?\b|\bitns?\b|\bllins?\b|bednet|vaccin|chemopreven|\bsmc\b|spray|\birs\b")
MALARIA_OUTCOME = RX(r"malaria|parasit|infect|mortal|death|anaem|anem|incidence|clinical|fever|hospital"
                     r"|plasmodium|mosquito|vector|wasting|haemoglobin|hemoglobin|birth")
NEGATED = RX(r"^\s*(no|non|not|without|lack of|never)\b|\bnon[- ]?use|\bnot (using|sleeping|owning)")

OUTCOME_TIERS = [
    ("mortality", RX(r"mortality|death|died|surviv")),
    ("severe / hospital", RX(r"severe|hospital|admission|cerebral")),
    ("anaemia & growth", RX(r"anaemi|anemi|haemoglobin|hemoglobin|\bhb\b|wasting|stunting|growth")),
    ("clinical malaria", RX(r"clinical|incidence|episode|cases?\b|uncomplicated|fever|outpatient")),
    ("infection", RX(r"infection|parasit|prevalence|rdt|microscop|carriage|positiv|pcr|plasmodium|malaria")),
    ("vector / entomological", RX(r"mosquito|anophel|vector|biting|eir\b|entomolog|knock ?down|blood[- ]?fe")),
]

RATIO_TYPES = {"odds_ratio", "adjusted_odds_ratio", "relative_risk_ratio", "hazard_ratio",
               "adjusted_hazard_ratio", "incident_rate_ratio", "prevalence_ratio"}
DIFF_TYPES = {"mean_difference_unstandardized", "mean_difference_standardized", "risk_difference"}
CORR_TYPES = {"pearson_r", "spearman_correlation"}


def intervention_side(row) -> tuple[str, str]:
    """Return (intervention_text, other_text) — the side that names the intervention."""
    rx = {"nets": NET_SUBTYPE[0][1], "smc": RX(r"chemopreven|smc|spaq|amodiaquine|iptc"),
          "vaccines": RX(r"rts|r21|vaccin|mosquirix")}
    cls = row["class"].split(";")[0]
    pat = rx[cls] if cls != "nets" else RX(r"net|itn|llin|interceptor|olyset|permanet|guard|pbo|piperonyl"
                                            r"|chlorfenapyr|pyriproxyfen")
    a, b = row["variable_1_name"], row["variable_2_name"]
    return (a, b) if pat.search(a) or not pat.search(b) else (b, a)


def classify(row) -> pd.Series:
    cls = row["class"].split(";")
    primary = "smc" if "smc" in cls and "vaccines" not in cls else cls[0]
    if "smc" in cls and "vaccines" in cls:
        primary = "combination"
    iv, other = intervention_side(row)
    if primary == "nets":
        subtype = next(name for name, rx in NET_SUBTYPE if rx.search(iv + " " + other))
    elif primary == "smc":
        subtype = "SMC (SP+AQ / IPTc)"
    elif primary == "vaccines":
        subtype = "R21/Matrix-M" if re.search(r"\br21\b", iv, re.I) else (
            "RTS,S/AS01" if re.search(r"rts", iv, re.I) else "malaria vaccine (unspecified)")
    else:
        subtype = "RTS,S + SMC"

    # Roles: is the intervention the exposure (effect evidence) or the thing being explained (uptake)?
    if UPTAKE.search(other) and INTERVENTION_WORD.search(other):
        role = "uptake / behaviour"            # e.g. education -> net ownership, knowledge -> vaccine acceptance
    elif UPTAKE.search(iv) and not MALARIA_OUTCOME.search(other):
        role = "uptake / behaviour"            # e.g. awareness of vaccine <- employment
    elif UPTAKE.search(iv):
        role = "use or coverage as exposure (observational)"   # e.g. ITN use -> parasitaemia in a survey
    else:
        role = "effect on outcome"
    tier = next((name for name, rx in OUTCOME_TIERS if rx.search(other)), "other")

    st = row["system_statistic_type"]
    fam = ("ratio" if st in RATIO_TYPES else "difference" if st in DIFF_TYPES
           else "correlation" if st in CORR_TYPES else "other")
    v, lo, hi = (pd.to_numeric(row[k], errors="coerce") for k in ("statistic_value", "ci_lower", "ci_upper"))
    p = pd.to_numeric(row["p_value"], errors="coerce")

    flags = []
    if NEGATED.search(iv):
        flags.append("exposure is the absence of the intervention (direction inverted)")
    if fam == "ratio":
        if not np.isnan(v) and v <= 0:
            flags.append("non-positive ratio")
        if not np.isnan(v) and v > 20:
            flags.append("ratio > 20: possibly a percentage stored as a ratio")
        if not np.isnan(lo) and lo <= 0:
            flags.append("non-positive CI bound")
    if not np.isnan(lo) and not np.isnan(hi):
        if lo > hi:
            flags.append("CI bounds reversed")
        elif not np.isnan(v) and not (lo <= v <= hi):
            flags.append("estimate outside its CI")
    else:
        flags.append("no CI")
    cil = pd.to_numeric(row["ci_level"], errors="coerce")
    if not np.isnan(cil) and cil not in (0.9, 0.95, 0.99):
        flags.append(f"ci_level={row['ci_level']}")

    plottable = fam == "ratio" and not np.isnan(v) and not np.isnan(lo) and not np.isnan(hi) \
        and v > 0 and lo > 0 and lo <= v <= hi and v <= 20

    null = 1.0 if fam == "ratio" else 0.0
    if np.isnan(v) or fam in ("other",):
        direction = "unclassified"
    elif v < null:
        direction = "lower with intervention"
    elif v > null:
        direction = "higher with intervention"
    else:
        direction = "no difference"
    if not np.isnan(lo) and not np.isnan(hi) and lo <= hi:
        ci_excludes_null = bool(hi < null or lo > null)
    elif not np.isnan(p):
        ci_excludes_null = bool(p < 0.05)
    else:
        ci_excludes_null = None

    return pd.Series({
        "intervention_class": primary, "intervention_subtype": subtype,
        "intervention_text": iv, "outcome_text": other, "role": role, "outcome_tier": tier,
        "stat_family": fam, "plottable_ratio": plottable, "direction": direction,
        "ci_excludes_null": ci_excludes_null, "qc_flags": "; ".join(flags),
    })


TEAM_RATIOS = RATIO_TYPES | {"rate_ratio", "risk_ratio"}


def teammate_flags(row) -> str:
    """Recompute the teammate's QC flags (scripts/clean_data.py v1.1.0) under their names."""
    num = lambda k: pd.to_numeric(row[k], errors="coerce")  # noqa: E731
    v, lo, hi, lvl, p = (num(k) for k in ("statistic_value", "ci_lower", "ci_upper", "ci_level", "p_value"))
    f = []
    if int(row.get("exact_duplicate_rows") or 0) > 0:
        f.append("exact_duplicate_rows")
    if str(row.get("conflicting_association_id")) == "True":
        f.append("conflicting_association_id")
    if np.isnan(v):
        f.append("missing_estimate")
    if np.isnan(lo) != np.isnan(hi):
        f.append("partial_ci")
    if not np.isnan(lo) and not np.isnan(hi):
        if lo > hi:
            f.append("reversed_ci")
        elif not np.isnan(v) and not lo <= v <= hi:
            f.append("estimate_outside_ci")
    if row["system_statistic_type"] in TEAM_RATIOS and any(not np.isnan(x) and x <= 0 for x in (lo, hi, v)):
        f.append("nonpositive_ratio")
    if not np.isnan(lvl) and not 0 < lvl < 1:
        f.append("ci_level_out_of_range")
    if not np.isnan(p) and not 0 <= p <= 1:
        f.append("p_value_out_of_range")
    if not np.isnan(p) and not row["p_value_equality"]:
        f.append("p_operator_unspecified")
    return "; ".join(f)


def main() -> None:
    out = pd.concat([C, C.apply(classify, axis=1)], axis=1)
    out["teammate_flags"] = C.apply(teammate_flags, axis=1)
    out.to_csv(INTERIM / "candidates_classified.csv", index=False)
    print(out.groupby(["intervention_class", "role"]).size().to_string())
    print(out[out.role == "effect on outcome"].groupby(["intervention_subtype", "outcome_tier"]).size().to_string())
    print("teammate flags:", out.teammate_flags.str.split("; ").explode().value_counts().to_dict())
    print("plottable:", int(out.plottable_ratio.sum()), "flagged >20:",
          int(out.qc_flags.str.contains("percentage").sum()))


if __name__ == "__main__":
    main()
