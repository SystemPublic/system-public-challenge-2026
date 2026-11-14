#!/usr/bin/env python
"""Build viz/data/annotations.json for the test cards of viz/evidence.html.

    ~/.venvs/nyc-concordance/bin/python tools/build_annotations.py

For each claim the card needs its estimate on its own scale. The estimate, its interval, its unit and its
null are copied from the outcome's city_effect (viz/data/claims.json, exported by tools/build_site.py). The
registered prediction band and the support and refute thresholds were read by hand from the registration's
prediction (magnitude, support_if, refute_if) and are listed in MANUAL below, in the units of city_effect.
Placebo estimates and referee re-estimates were read from critique/<id>.md and from the outcome's notes and
notes_referee. Every hand-copied number is checked here against the text it was copied from: the script
prints each number it cannot find in its source and exits non-zero unless the number is marked derived.

Paths written into the output are relative to the repository.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "viz" / "data"

TOPICS = [
    ("heat", "Heat and violence"),
    ("toll", "Congestion toll and mobility"),
    ("streets", "Streets and safety"),
    ("ems", "EMS"),
    ("construction", "Construction, housing and vacant land"),
    ("health", "Health and food"),
    ("drift", "Restaurants, reproductions and data drift"),
    ("graph", "The graph itself"),
    ("other", "Energy, flooding and other city questions"),
]

TOPIC_OF = {
    "heat": ["bridge-heat-shootings-ems", "bridge-shot-ems-link", "heat-", "transfer-chicago-heat-shootings",
             "transfer-chicago-hot-end"],
    "toll": ["bridge-crz-", "crz-storefront-vacancy", "mob-crz-", "sim-crz-holdout-2026", "commute-fhv-subway-distance",
             "retimed-daytime-burglary", "retimed-taxi-fhv-pickups", "transfer-chicago-weekday-pattern", "transit-"],
    "streets": ["rlc-", "turn-calming-", "street-busway14-", "mob-speedcam-247"],
    "ems": ["ems-", "retimed-ems-presence"],
    "construction": ["construction", "stalled-", "levers-", "nbhd-vacant-shootings", "afford-", "all-boats-trees-rent"],
    "health": ["food-", "commute-time-depression", "mob-active-commute-obesity", "mob-asthma-pollution",
               "nbhd-rodents-asthma", "split-temp-", "further-containers-rats-cd9"],
    "drift": ["restaurants-", "repro-", "further-chinatown-shift", "further-repro-dsny-rat-sightings",
              "further-subway-crime-per-million-repro"],
    "graph": ["graph-", "transfer-chicago-concordance-matrix"],
    "other": ["further-datacentre", "further-zonej", "further-tidal", "further-subway-crime-per-ride-by-hour",
              "nbhd-noise311-exposure"],
}


def topic_for(cid: str) -> str:
    best = None
    for t, pats in TOPIC_OF.items():
        for p in pats:
            if cid.startswith(p):
                if best is None or len(p) > best[1]:
                    best = (t, len(p))
    if best is None:
        raise SystemExit(f"no topic for {cid}")
    return best[0]


# ------------------------------------------------------------------ hand-read values, in city_effect units
# band: registered prediction range; sup / ref: thresholds from support_if / refute_if.
# derived=True marks a band computed from the registration (for example k of 22 as a share) rather than
# copied; such numbers are not looked up in the text.
# placebo: est, lo, hi, registered (named in the registration), label, src (file or "outcome").
# referee: v, label, src.
M = {
    "afford-gentrification-prevalence": dict(band=[6 / 22, 10 / 22], derived=True),
    "afford-poor-count-shift": dict(band=[-0.45, -0.10], sup=[0], ref=[0]),
    "all-boats-trees-rent": dict(band=[0.018, 0.070], sup=[0.009], ref=[0.018]),
    "bridge-crz-ems-travel": dict(band=[-3.59, -0.38]),
    "bridge-crz-injury-crashes": dict(band=[-8.2, 8.7],
        placebo=dict(est=3.8, lo=-5.4, hi=14.0, registered=True, label="2024 placebo", src="outcome")),
    "bridge-crz-injury-crashes-v2": dict(band=[-9.2, 5.5],
        placebo=dict(est=15.2, lo=4.8, hi=26.6, registered=True, label="2024 placebo", src="outcome")),
    "bridge-heat-shootings-ems": dict(band=[1.049, 1.148]),
    "bridge-shot-ems-link": dict(band=[0.6, 1.6], sup=[0.6, 1.6], ref=[0.6, 1.6]),
    "commute-fhv-subway-distance": dict(band=[0.10, 0.50], sup=[0], ref=[0]),
    "commute-time-depression": dict(band=[0.05, 0.3], sup=[0], ref=[0]),
    "construction-aerial-triangulation": dict(band=[0.65, 0.90], sup=[0.6], ref=[0.45]),
    "construction-four-year-completion": dict(band=[0.55, 0.85], sup=[0.75, 0.95], ref=[0.65]),
    "construction-permit-funnel": dict(band=[3, 10], sup=[3], ref=[2]),
    "construction-sheds-outnumber-nb": dict(band=[1.5, 6], sup=[1.2], ref=[0.8]),
    "construction2-rows-per-job-dobnow": dict(band=[4, 12], sup=[3.0], ref=[2.0]),
    "construction2-rows-per-job-legacy-2000s": dict(band=[5, 9], sup=[5.0], ref=[3.0]),
    "crz-storefront-vacancy": dict(band=[-1.5, 0.5], sup=[0.5, 1.2], ref=[0]),
    "ems-hospital-turnaround-wait": dict(band=[0.5, 3], sup=[0.2], ref=[0.2],
        placebo=dict(est=2.40, lo=1.20, hi=3.60, registered=False,
                     label="referee placebo: next day's turnaround", src="outcome"),
        referee=dict(v=4.54, label="referee reproduction", src="outcome")),
    "ems-taxi-2026-onset": dict(band=[0.3, 1.0], sup=[0.1], ref=[0.1],
        placebo=dict(est=0.690, lo=0.226, hi=1.153, registered=True, label="placebo year 2024-25",
                     src="critique/ems-taxi-2026-onset.md"),
        referee=dict(v=0.913, label="referee re-estimate", src="critique/ems-taxi-2026-onset.md")),
    "ems-traffic-hourly-elasticity": dict(band=[0.3, 0.9], sup=[0.10], ref=[0.10],
        referee=dict(v=0.636, label="referee reproduction", src="outcome")),
    "ems-traffic-share-2019-2026": dict(band=[0.05, 0.45], sup=[0.5], ref=[0.5],
        referee=dict(v=0.333, label="referee reproduction", src="outcome")),
    "food-supermarket-diabetes-zcta": dict(band=[0.95, 1.03], sup=[0.90, 1.10], ref=[0.95],
        referee=dict(v=0.995, label="referee reproduction", src="outcome")),
    "further-containers-rats-cd9": dict(band=[0.75, 0.95], sup=[1.00], ref=[0.90],
        placebo=dict(est=1.08, lo=0.89, hi=1.36, registered=True, label="placebo year 2023-24", src="outcome")),
    "further-datacentre-share-manhattan": dict(band=[1.0 - 4.4, 5.0 - 4.4], sup=[0], ref=[0], derived=True),
    "further-datacentre-share-manhattan-v2": dict(band=[1.8 - 4.4, 3.5 - 4.4], sup=[0], ref=[0], derived=True),
    "further-repro-dsny-rat-sightings": dict(band=[-21.1, -20.1], sup=[-21.1, -20.1], derived=True),
    "further-subway-crime-per-million-repro": dict(band=[1.60 / 1.65, 1.70 / 1.65], sup=[1.60 / 1.65, 1.70 / 1.65],
                                                   derived=True),
    "further-subway-crime-per-ride-by-hour": dict(band=[1.2, 2.2], sup=[1], ref=[1]),
    "further-tidal-flooding-trend": dict(band=[1.10, 2.0], sup=[1.00], ref=[1.30]),
    "further-zonej-demand-growth": dict(band=[-0.6, 0.6], sup=[0.5], ref=[0.5]),
    "graph-concordance-matrix": dict(band=[0.55, 0.75], sup=[0.60], ref=[0.40], derived=True),
    "graph-confounders-commute-obesity": dict(band=[-4.0, -1.0], sup=[-4.0, 0.5], ref=[-5.0]),
    "graph-confounders-surftemp-ed": dict(band=[-2.5, 0.5], sup=[-2.5, 0.5], ref=[-5.2, 3.4]),
    "graph-confounders-trees-surftemp": dict(band=[-1.2, -0.3], sup=[-0.30], ref=[0]),
    "graph-triad-cold-asthma-absence": dict(band=[1.0008, 1.0173], sup=[1], ref=[1]),
    "graph-triad-hot-asthma-absence": dict(band=[1.0007, 1.0055], sup=[1], ref=[1],
        placebo=dict(est=1.021, lo=0.985, hi=1.058, registered=False, label="referee placebo: heat two days later",
                     src="outcome")),
    "heat-ac-heat-calls": dict(band=[0, 0.12], sup=[0], ref=[0.112]),
    "heat-ac-shootings": dict(band=[-0.02, 0.05], sup=[0], ref=[0.042],
        referee=dict(v=0.025, label="referee, day from 06:00", src="outcome")),
    "heat-ed-syndromic": dict(band=[1.5, 5], sup=[1.00, 1.5], ref=[1.00]),
    "heat-extremes-downturn": dict(band=[0.88, 0.98], sup=[1.00], ref=[1.00]),
    "heat-mech-intox": dict(band=[-0.02, 0.08], sup=[0.10, 0.25], ref=[0.10, 0.25]),
    "heat-mech-outdoors": dict(band=[0.10, 0.35], sup=[0.10, 0.25], ref=[0.10, 0.25],
        referee=dict(v=0.529, label="after referee: night-of counts", src="outcome")),
    "heat-night-minimum": dict(band=[0.98, 1.08], sup=[1.00], ref=[1.075]),
    "heat-school-out": dict(band=[0.95, 1.08], sup=[1.00], ref=[1.10],
        referee=dict(v=1.044, label="referee, day from 06:00", src="outcome")),
    "heat-shootings": dict(band=[1.05, 1.20], sup=[1.00], ref=[1.00]),
    "heat-surftemp-ed": dict(band=[0, 8], sup=[0], ref=[0]),
    "heat-trees-airtemp-hyperlocal": dict(band=[-0.5, -0.05], sup=[0], ref=[0]),
    "heat-trees-canopy-within-nta": dict(band=[-0.25, -0.02], sup=[0], ref=[0]),
    "heat-trees-ed-chain": dict(band=[-5, -0.5], sup=[0], ref=[0]),
    "heat-trees-surftemp": dict(band=[-3, -0.5], sup=[0], ref=[0]),
    "levers-vacant-lot-trial-match": dict(band=[0.18, 0.45], sup=[0.18, 0.45], ref=[0.18, 0.45],
        referee=dict(v=0.406, label="referee rebuild", src="outcome")),
    "mob-active-commute-obesity": dict(band=[-4, -0.5], sup=[0], ref=[0]),
    "mob-asthma-pollution": dict(sup=[1], ref=[1]),
    "mob-crz-air-nyccas": dict(band=[-10, -3], sup=[0], ref=[0],
        placebo=dict(est=3.3, lo=None, hi=None, registered=True, label="placebo in time (post = 2024)",
                     src="outcome")),
    "mob-crz-traffic": dict(band=[5, 15], sup=[0], ref=[0]),
    "mob-speedcam-247": dict(band=[0.92, 1.00], sup=[1], ref=[0.97]),
    "nbhd-noise311-exposure": dict(band=[0.05, 0.30], sup=[0], ref=[0]),
    "nbhd-rodents-asthma": dict(band=[0.00, 0.20], sup=[0], ref=[0]),
    "nbhd-vacant-shootings": dict(band=[1.00, 1.10], sup=[1.00], ref=[1.00]),
    "repro-dcp-2025-completions": dict(band=[37500 / 38682 - 1, 39500 / 38682 - 1], sup=[-0.04, 0.04], derived=True),
    "repro-dot-2025-deaths": dict(band=[-5, 5], sup=[-5, 5], derived=True),
    "repro-mmr-cbd-speed": dict(band=[-0.2, 0.2], sup=[-0.2, 0.2]),
    "restaurants-nta-harshness": dict(band=[0.05, 0.20], sup=[0.05]),
    "restaurants-score-complaints": dict(band=[1.10, 1.60], sup=[1.00], ref=[1.10],
        placebo=dict(est=1.673, lo=1.111, hi=2.519, registered=True, label="placebo: Noise - Commercial complaints",
                     src="critique/restaurants-score-complaints.md"),
        referee=dict(v=1.130, label="referee re-estimate", src="outcome")),
    "retimed-daytime-burglary": dict(band=[0.905, 0.95], sup=[1], ref=[0.95, 1]),
    "retimed-ems-presence": dict(band=[0.2, 1.0], sup=[0], ref=[0.2]),
    "retimed-taxi-fhv-pickups": dict(band=[0.3, 1.0], sup=[0], ref=[0.3]),
    "rlc-expansion-injuries": dict(band=[0.70, 0.95], sup=[1.00], ref=[0.95],
        placebo=dict(est=1.263, lo=1.100, hi=1.445, registered=True, label="placebo year, before cameras",
                     src="critique/rlc-expansion-injuries.md"),
        referee=dict(v=1.038, label="referee reproduction", src="outcome")),
    "rlc-expansion-rearend": dict(band=[1.10, 1.60], sup=[1.00], ref=[1.10],
        placebo=dict(est=1.250, lo=1.052, hi=1.488, registered=True, label="placebo year, before cameras",
                     src="outcome"),
        referee=dict(v=1.327, label="referee reproduction", src="outcome")),
    "sim-crz-holdout-2026": dict(sup=[0, 1], ref=[0.5]),
    "split-temp-asthma-ems": dict(band=[0.95, 0.99], sup=[1], ref=[1]),
    "split-temp-covid-growth": dict(band=[-0.030, -0.003], sup=[0], ref=[0]),
    "stalled-421a-vesting-footings": dict(band=[0.05, 0.15], sup=[0.03], ref=[0.03],
        referee=dict(v=-0.083, label="referee, job-number matching", src="outcome")),
    "stalled-flood-zone-starts": dict(band=[0.04, 0.15], sup=[0], ref=[0],
        referee=dict(v=-0.001, label="referee, job-number matching", src="outcome")),
    "street-busway14-crosstown-detour": dict(band=[0.5, 4], sup=[0, 0.5], ref=[1.5],
        referee=dict(v=0.18, label="referee reproduction", src="outcome")),
    "street-busway14-crosstown-time": dict(band=[2, 10], sup=[0, 2.0], ref=[5.0],
        referee=dict(v=0.93, label="referee reproduction", src="outcome")),
    "street-busway14-fhv-north-south": dict(band=[3, 12], sup=[0, 3], ref=[7],
        referee=dict(v=1.56, label="referee reproduction", src="outcome")),
    "street-busway14-m14-speed": dict(band=[4, 20], sup=[4], ref=[4],
        referee=dict(v=5.46, label="referee reproduction", src="outcome")),
    "street-busway14-ped-injuries": dict(band=[0.45, 0.85], sup=[0.85, 1], ref=[0.65],
        referee=dict(v=1.319, label="referee reproduction", src="outcome")),
    "transfer-chicago-concordance-matrix": dict(band=[0.40, 0.80], sup=[0.60], ref=[0.370]),
    "transfer-chicago-heat-shootings": dict(band=[1.10, 1.20], sup=[1.110, 1.183], ref=[1.073, 1.219]),
    "transfer-chicago-hot-end": dict(band=[1.05, 1.18], ref=[1.06]),
    "transfer-chicago-weekday-pattern": dict(band=[5, 12], sup=[6.5, 10.9], ref=[4.4, 13.1]),
    "transit-gtrain-substitution": dict(band=[0.02, 0.12], sup=[0], ref=[0.02],
        placebo=dict(est=-0.002, lo=-0.031, hi=0.027, registered=True, label="2023 placebo", src="outcome")),
    "transit-weekday-pattern": dict(band=[4, 10], sup=[4], ref=[1]),
    "turn-calming-displacement": dict(band=[0.93, 1.07], sup=[0.88, 1.12], ref=[1.00],
        referee=dict(v=0.926, label="referee re-estimate", src="outcome")),
    "turn-calming-leftturn": dict(band=[0.70, 0.95], sup=[1.00], ref=[0.95],
        placebo=dict(est=0.9339, lo=0.8607, hi=1.0133, registered=False,
                     label="placebo, installation 12 months early (not registered)",
                     src="critique/turn-calming-leftturn.md"),
        referee=dict(v=0.904, label="referee reproduction", src="outcome")),
    "turn-calming-ped": dict(band=[0.80, 0.97], sup=[1.00], ref=[0.97],
        placebo=dict(est=0.9119, lo=0.8252, hi=1.0078, registered=False,
                     label="placebo, installation 12 months early (not registered)",
                     src="critique/turn-calming-ped.md"),
        referee=dict(v=0.8486, label="referee reproduction", src="critique/turn-calming-ped.md")),
}

# One line for each claim that cannot be placed on a scale.
TEXT_ONLY = {
    "bridge-crz-crash-link": "A research link (speed and volume elasticities from the literature); city data test it only through the bridge's endpoint.",
    "construction-2022-rush-units-2027": "Registered for a date not yet reached (30 June 2027); no outcome yet.",
    "further-tidal-flooding-311": "The registered minimum-data rule failed, so the rate ratio decides nothing.",
    "mob-crz-air": "No Manhattan NO2 monitor reported to EPA in 2022-2025, so the registered test could not be run.",
    "transit-fhv-price-subway": "The registered first-stage gate failed, so the subway estimate decides nothing.",
}

RATIO_WORDS = ("ratio", "irr", "rate ratio")


def short_unit(scale: str | None) -> str:
    if not scale:
        return ""
    s = scale.split(";")[0]
    s = re.sub(r"\s*\(.*$", "", s).strip()
    return s


def num_forms(v: float) -> list[str]:
    out = set()
    for f in ("{:.0f}", "{:.1f}", "{:.2f}", "{:.3f}", "{:.4f}", "{:g}"):
        s = f.format(v)
        out.add(s)
        if s.startswith("-"):
            out.add("−" + s[1:])
            out.add(s[1:])  # a range written as "-0.02 to 0.05" can list the magnitude only after a dash
        if s.startswith("0."):
            out.add(s[1:])
        if s.startswith("-0."):
            out.add("-" + s[2:])
    if v > 0:
        out |= {"+" + s for s in list(out) if not s.startswith(("-", "−", "+"))}
    if 0 < abs(v) <= 1:  # a share written as a percentage
        out |= {"{:g}%".format(round(v * 100, 1))}
    return list(out)


def found(v: float, text: str) -> bool:
    for s in num_forms(v):
        if re.search(r"(?<![0-9.])" + re.escape(s) + r"(?![0-9])", text):
            return True
    return False


def main() -> int:
    claims = json.loads((DATA / "claims.json").read_text())["claims"]
    titles = json.loads((DATA / "titles.json").read_text())
    out, problems = {}, []
    for c in claims:
        cid = c["id"]
        if cid not in titles:
            problems.append(f"{cid}: no title")
        elif len(titles[cid].split()) > 8:
            problems.append(f"{cid}: title longer than 8 words")
        o = c.get("outcome") or {}
        ce = o.get("city_effect") or {}
        m = M.get(cid, {})
        scale_txt = (ce.get("scale") or "")
        is_ratio = ce.get("null") == 1 and any(w in scale_txt.lower() for w in RATIO_WORDS)
        rec = {
            "topic": topic_for(cid),
            "verdict": o.get("verdict") or "registered",
            "label": ce.get("label"),
            "unit": short_unit(scale_txt),
            "unit_full": scale_txt or None,
            "scale": "log" if is_ratio else "linear",
            "null": ce.get("null"),
            "estimate": ce.get("estimate"),
            "lo": ce.get("lo"),
            "hi": ce.get("hi"),
            "band": m.get("band"),
            "thresholds": ([{"v": v, "role": "support"} for v in m.get("sup", [])]
                           + [{"v": v, "role": "refute"} for v in m.get("ref", [])]),
            "placebo": m.get("placebo"),
            "referee": m.get("referee"),
            "band_derived": bool(m.get("derived")),
            "text": None,
            "sources": {"estimate": f"claims/outcomes/{cid}.json (city_effect)",
                        "band_thresholds": f"claims/registered/{cid}.json (prediction)"},
        }
        if cid in TEXT_ONLY or ce.get("estimate") is None or rec["verdict"] == "no_test":
            rec["text"] = TEXT_ONLY.get(cid) or (o.get("prediction_scored") or "")[:160]
            rec["card"] = "text"
        else:
            rec["card"] = "scale"
        # ---- check hand-copied numbers against their sources
        reg_text = json.dumps(c.get("prediction") or {}, ensure_ascii=False)
        if not m.get("derived"):
            for v in (m.get("band") or []) + m.get("sup", []) + m.get("ref", []):
                if v not in (0, 1) and not found(v, reg_text):
                    problems.append(f"{cid}: band/threshold {v} not found in the registration's prediction")
        for key in ("placebo", "referee"):
            p = m.get(key)
            if not p:
                continue
            src = p["src"]
            if src == "outcome":
                text = json.dumps(o, ensure_ascii=False)
                p["src"] = f"claims/outcomes/{cid}.json"
            else:
                text = (ROOT / src).read_text()
            for k in ("est", "lo", "hi", "v"):
                if p.get(k) is not None and not found(p[k], text):
                    problems.append(f"{cid}: {key} {k}={p[k]} not found in {p['src']}")
        # the canopy claim carries a structured placebo in its outcome; copy it rather than transcribe it
        if isinstance(o.get("placebo"), dict) and o["placebo"].get("alone"):
            a = o["placebo"]["alone"]
            rec["placebo"] = {"est": a["estimate"], "lo": a["lo"], "hi": a["hi"], "registered": True,
                              "label": "placebo: " + o["placebo"].get("label", ""),
                              "src": f"claims/outcomes/{cid}.json (placebo.alone)"}
        out[cid] = rec
    for cid in M:
        if cid not in out:
            problems.append(f"{cid}: in MANUAL but not among the claims")
    doc = {"topics": [{"key": k, "name": n} for k, n in TOPICS],
           "note": "Estimates from outcome city_effect; bands and thresholds read from the registration's prediction in "
                   "city_effect units; placebos and referee values from critique/*.md and the outcome notes. Built by "
                   "tools/build_annotations.py, which checks each hand-copied number against its source text.",
           "claims": out}
    (DATA / "annotations.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
    n_scale = sum(1 for r in out.values() if r["card"] == "scale")
    print(f"annotations: {len(out)} claims, {n_scale} scale cards, {len(out) - n_scale} text cards")
    for p in problems:
        print("CHECK", p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
