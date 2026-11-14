#!/usr/bin/env python
"""Stage 2: coverage.csv, coverage_summary.json and figures/graph/coverage.png from the stage-1 JSON.
No API calls and no city data. Run from the repo root after collect.py."""
import csv, glob, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from termmap import ENDS, CLAIMS

D = ROOT / "data" / "derived" / "graph" / "coverage"
ends = json.load(open(D / "ends.json"))
pairs = json.load(open(D / "pairs.json"))

# Judgement, made by reading the sampled variable names in ends.json (and the supplementary queries noted in
# docs/graph_experiments.md). relevant = variables about this exposure/outcome exist with associations;
# thin = a few variables, mostly about something else; none = no usable variable.
REL = {
 "congestion pricing": ("none", "no variable names contain it"),
 "traffic speed": ("relevant", "13 variables; ungrounded or grounded to traffic-related pollution"),
 "speed cameras": ("relevant", "9 variables; ungrounded"),
 "travel time to work": ("relevant", "100+ commuting variables; ungrounded"),
 "311 noise complaints": ("relevant", "4 variables; grounded to the concept noise, not to complaints"),
 "mice or rats in home": ("relevant", "43 mouse-allergen and 7 rodent-infestation variables; ungrounded or grounded to rodent disease"),
 "vacant land": ("relevant", "21 variables; ungrounded or grounded to population density"),
 "for-hire vehicle trips": ("thin", "5 ride-hailing variables, mostly about drivers' health"),
 "FHV and taxi price": ("none", "no variable names contain it"),
 "loss of subway service": ("thin", "one subway-ridership variable among restaurant and driver variables"),
 "data centres": ("none", "matches are 'Centers for Disease Control'"),
 "electrification": ("thin", "5 electricity-demand variables grounded to electricity; none about electrification"),
 "hour of day": ("none", "no variable names contain it"),
 "rat sightings": ("relevant", "7 variables; grounded to the laboratory-animal concept rats, or ungrounded"),
 "building permits": ("none", "no variable names contain it"),
 "sidewalk sheds": ("none", "no variable names contain it"),
 "aerial photography": ("none", "3 remote-sensing variables, none about buildings"),
 "residential displacement": ("relevant", "17 gentrification variables; ungrounded"),
}
TOPIC = {
 "heat-shootings": "heat and health", "bridge-shot-ems-link": "violence", "bridge-heat-shootings-ems": "heat and health",
 "heat-ed-syndromic": "heat and health", "heat-surftemp-ed": "heat and health", "heat-trees-surftemp": "heat and green space",
 "heat-trees-airtemp-hyperlocal": "heat and green space", "heat-trees-canopy-within-nta": "heat and green space",
 "heat-trees-ed-chain": "heat and green space", "mob-crz-traffic": "traffic and congestion pricing",
 "bridge-crz-crash-link": "traffic and congestion pricing", "bridge-crz-injury-crashes": "traffic and congestion pricing",
 "bridge-crz-injury-crashes-v2": "traffic and congestion pricing", "mob-crz-air": "air quality", "mob-crz-air-nyccas": "air quality",
 "mob-speedcam-247": "traffic and congestion pricing", "mob-asthma-pollution": "air quality",
 "mob-active-commute-obesity": "commuting and health", "commute-time-depression": "commuting and health",
 "commute-fhv-subway-distance": "transit operations", "nbhd-noise311-exposure": "noise", "nbhd-rodents-asthma": "pests",
 "nbhd-vacant-shootings": "violence", "transit-fhv-price-subway": "transit operations", "transit-gtrain-substitution": "transit operations",
 "transit-weekday-pattern": "transit operations", "further-containers-rats-cd9": "pests", "further-datacentre-share-manhattan": "electricity",
 "further-zonej-demand-growth": "electricity", "further-subway-crime-per-ride-by-hour": "violence", "further-tidal-flooding-311": "flooding",
 "further-repro-dsny-rat-sightings": "pests", "further-subway-crime-per-million-repro": "violence", "further-chinatown-shift": "demography",
 "construction-2022-rush-units-2027": "permits and construction", "construction-aerial-triangulation": "permits and construction",
 "construction-four-year-completion": "permits and construction", "construction-permit-funnel": "permits and construction",
 "construction-sheds-outnumber-nb": "permits and construction", "construction2-rows-per-job-dobnow": "permits and construction",
 "construction2-rows-per-job-legacy-2000s": "permits and construction", "repro-dcp-2025-completions": "permits and construction",
 "repro-dot-2025-deaths": "traffic and congestion pricing", "repro-mmr-cbd-speed": "traffic and congestion pricing",
}

def verdict(cid):
    f = ROOT / "claims" / "outcomes" / f"{cid}.json"
    return json.load(open(f)).get("verdict") if f.exists() else "no outcome"

def kind(cid):
    return json.load(open(ROOT / "claims" / "registered" / f"{cid}.json"))["kind"]

def vm(end):
    """variable-name matches for an end with no concept: (n variables, associations in sample, sample size)"""
    qs = ends[end]["variable_queries"]
    if not qs:
        return None
    best = max(qs.values(), key=lambda d: d["n_variables"])
    return best["n_variables"], sum(d["associations_in_sample"] for d in qs.values()), sum(d["sampled"] for d in qs.values()), best["capped"]

rows = []
for cid, (c, f, causal) in CLAIMS.items():
    P = pairs[cid]
    cc, fc = ends[c]["concept_labels"], ends[f]["concept_labels"]
    missing = [e for e in (c, f) if not ENDS[e]["concepts"]]
    if not missing:
        cls = "linked" if P["direct_findings"] else "concepts exist, no findings link them"
    elif all(REL[e][0] == "relevant" for e in missing):
        cls = "variable names only"
    else:
        cls = "silent"
    s = P["signs"] or {}
    def vcol(e):
        if ENDS[e]["concepts"]:
            return ""
        m = vm(e)
        return f"{m[0]}{'+' if m[3] else ''} variables; {m[1]} associations in first {m[2]} [{REL[e][0]}]"
    rows.append({
        "claim_id": cid, "kind": kind(cid), "verdict": verdict(cid), "topic": TOPIC[cid], "causal_edge": causal,
        "cause_term": c, "effect_term": f,
        "cause_concepts": "; ".join(cc), "effect_concepts": "; ".join(fc),
        "direct_findings": "" if P["direct_findings"] is None else P["direct_findings"],
        "direct_studies": "" if P["direct_studies"] is None else P["direct_studies"],
        "findings_positive": s.get("+", ""), "findings_negative": s.get("-", ""), "findings_unsigned": s.get("none", ""),
        "significant_positive": s.get("sig+", ""), "significant_negative": s.get("sig-", ""),
        "shared_neighbours": "" if P["shared_neighbours"] is None else P["shared_neighbours"],
        "cause_variable_matches": vcol(c), "effect_variable_matches": vcol(f),
        "coverage_class": cls,
        "top_shared": "; ".join(f"{x['label']} ({x['with_cause']}/{x['with_effect']})" for x in P["shared_top"][:4]),
    })
with open(D / "coverage.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader(); w.writerows(rows)

# ---- end-level gap table
gap_rows = []
for e, info in ENDS.items():
    used = [cid for cid, (c, f, _) in CLAIMS.items() if e in (c, f)]
    if info["concepts"]:
        gap_rows.append({"end": e, "state": "concept", "claims": len(used)})
    else:
        gap_rows.append({"end": e, "state": "grounding failure" if REL[e][0] == "relevant" else "real gap" + (" (thin)" if REL[e][0] == "thin" else ""),
                         "note": REL[e][1], "claims": len(used)})
json.dump(gap_rows, open(D / "end_gaps.json", "w"), indent=1)

from collections import Counter
summ = {"classes": Counter(r["coverage_class"] for r in rows),
        "topics": {}}
for r in rows:
    summ["topics"].setdefault(r["topic"], Counter())[r["coverage_class"]] += 1
summ["classes"] = dict(summ["classes"]); summ["topics"] = {k: dict(v) for k, v in summ["topics"].items()}
summ["ends"] = dict(Counter(g["state"] for g in gap_rows))
json.dump(summ, open(D / "coverage_summary.json", "w"), indent=1)
print(json.dumps(summ, indent=1))

# ---- figure
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
COL = {"confirmed": "#1b7837", "contested": "#d95f02", "unsettled": "#7570b3", "bridged": "#1f78b4", "no_test": "#999999", "no outcome": "#cccccc"}
LAB = {"confirmed": "confirmed", "contested": "contested", "unsettled": "unsettled", "bridged": "bridged", "no_test": "no test possible", "no outcome": "no outcome yet"}
order_cls = {"linked": 0, "concepts exist, no findings link them": 1, "variable names only": 2, "silent": 3}
def key(r):
    d = r["direct_findings"]
    return (order_cls[r["coverage_class"]], -(d if d != "" else 0), r["claim_id"])
rs = sorted(rows, key=key)
fig, ax = plt.subplots(figsize=(11, 12.5), dpi=200)
ypos, y, prev = {}, 0, None
for r in rs:
    if prev is not None and r["coverage_class"] != prev:
        y += 0.8
    prev = r["coverage_class"]; ypos[r["claim_id"]] = y; y += 1
import numpy as np
for r in rs:
    yy = ypos[r["claim_id"]]; col = COL[r["verdict"]]
    d = r["direct_findings"]
    if r["coverage_class"] == "linked":
        ax.barh(yy, d, color=col, height=0.7)
        ax.text(d * 1.12, yy, f"{d} findings, {r['direct_studies']} studies; {r['findings_positive']} +, {r['findings_negative']} -", va="center", fontsize=7.5)
    elif r["coverage_class"].startswith("concepts exist"):
        ax.plot([0.55], [yy], "o", mfc="white", mec=col, mew=1.6, ms=7)
        ax.text(0.75, yy, "both concepts exist, 0 findings link them", va="center", fontsize=7.5, color="#444")
    elif r["coverage_class"] == "variable names only":
        ax.plot([0.55], [yy], "s", mfc=col, mec=col, ms=6, alpha=0.55)
        miss = [e for e in (r["cause_term"], r["effect_term"]) if not ENDS[e]["concepts"]]
        ax.text(0.75, yy, "no concept for " + ", ".join(miss) + "; variables exist", va="center", fontsize=7.5, color="#444")
    else:
        ax.plot([0.55], [yy], "x", color=col, ms=7, mew=1.8)
        miss = [e for e in (r["cause_term"], r["effect_term"]) if not ENDS[e]["concepts"] and REL[e][0] != "relevant"]
        ax.text(0.75, yy, "silent: nothing usable for " + ", ".join(miss), va="center", fontsize=7.5, color="#444")
ax.set_xscale("log"); ax.set_xlim(0.5, 20000)
ax.set_xticks([1, 3, 10, 30, 100, 300, 1000]); ax.set_xticklabels(["1", "3", "10", "30", "100", "300", "1000"]); ax.set_xlim(0.5, 20000)
ax.set_yticks([ypos[r["claim_id"]] for r in rs])
ax.set_yticklabels([f"{r['claim_id']}  ({r['cause_term']} > {r['effect_term']})" for r in rs], fontsize=7.5)
ax.invert_yaxis()
ax.set_xlabel("Findings linking the cause and effect concepts (log scale)")
ax.set_title("What the System Public Graph holds on each of the 44 registered claims", loc="right", fontsize=12)
for s in ("top", "right"): ax.spines[s].set_visible(False)
ax.grid(axis="x", alpha=0.25)
h = [Line2D([0], [0], marker="s", ls="", color=COL[k], label=LAB[k]) for k in COL if any(r["verdict"] == k for r in rows)]
h += [Line2D([0], [0], marker="o", ls="", mfc="white", mec="#444", label="concepts exist, no link"),
      Line2D([0], [0], marker="s", ls="", color="#888", alpha=0.55, label="variable names only"),
      Line2D([0], [0], marker="x", ls="", color="#444", label="silent")]
ax.legend(handles=h, loc="lower right", fontsize=8, title="Colour: team verdict", title_fontsize=8, frameon=False)
fig.tight_layout()
out = ROOT / "figures" / "graph" / "coverage.png"
out.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(out)
from PIL import Image, ImageCms
im = Image.open(out).convert("RGB")
prof = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
im.save(out, icc_profile=prof, dpi=(200, 200))
print("wrote", out.relative_to(ROOT))
