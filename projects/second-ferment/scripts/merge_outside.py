"""Add the outside sources (PRD phase 2) to the HeatRx bundle: coded heat-health guidance, the effect-to-action
mapping, Medicare prescriber specialty shares and the NYC heat-wave scenarios. Nothing here comes from the graph;
everything added is tagged as outside the graph.

Usage (from the repo root), after evidence.py and merge_papers.py:
  python3 -I scripts/merge_outside.py bundle/evidence.json reference
"""
import collections
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bundle_io  # noqa: E402

bundle_path, ref = sys.argv[1:3]
b = json.load(open(bundle_path))
rd = lambda p: list(csv.DictReader(open(os.path.join(ref, p), newline="")))  # noqa: E731

docs = rd("guidance/documents.csv")
mentions = rd("guidance/class_mentions.csv")
actions = rd("guidance/actions.csv")
for a in actions:
    a["classes"] = [c for c in a["classes"].split(";") if c]
eff_actions = rd("effect_actions.csv")
for e in eff_actions:
    e["basis"] = [d for d in e["basis"].split(";") if d]
BUCKETS = {"hold_swap": "Hold or swap", "adjust_dose": "Adjust dose", "monitor": "Monitor closely",
           "storage": "Storage", "counsel": "Counsel"}

b["guidance"] = {
    "documents": docs,
    "mentions": mentions,
    "actions": actions,
    "not_included": [{"title": "WHO Regional Office for Europe, Public health advice on preventing health effects of heat (2011), "
                               "sheet 4: adverse effects of medications during hot weather",
                      "reason": "The PDF could not be retrieved (the server refuses automated downloads)."}],
    "buckets": BUCKETS,
}
b["effect_actions"] = eff_actions

# guidance on each class x effect link; add guidance-only links
by_ce = collections.defaultdict(set)
docs_by_class = collections.defaultdict(set)
for m in mentions:
    docs_by_class[m["class"]].add(m["doc"])
    if m["effect"]:
        by_ce[(m["class"], m["effect"])].add(m["doc"])
links = {(l["class"], l["effect"]): l for l in b["links"]}
added = 0
for (c, e), ds in by_ce.items():
    l = links.get((c, e))
    if l is None:
        l = {"class": c, "effect": e, "tier": "guidance_only", "direct_scope": [], "direct_ids": [],
             "drug_arm": {"studies": 0, "raised": 0, "lowered": 0, "unclear": 0, "not_ratio": 0}, "drug_arm_ids": [],
             "heat_arm_studies": next((h["studies"] for h in b["heat_arms"] if h["effect"] == e), 0)}
        b["links"].append(l)
        links[(c, e)] = l
        added += 1
    elif l["tier"] == "weak":
        l["tier"] = "guidance_only"
        l["weak_evidence"] = True
    l["guidance_docs"] = sorted(ds)
for l in b["links"]:
    l.setdefault("guidance_docs", [])

# actions per class: from class-specific guidance, and from the effects of its drawn links
spec = json.load(open(os.path.join(ref, "medicare_specialty.json"))) if os.path.exists(os.path.join(ref, "medicare_specialty.json")) else None
for cl in b["classes"]:
    c = cl["id"]
    cl["guidance_docs"] = sorted(docs_by_class.get(c, ()))
    acts = []
    for a in actions:
        if c in a["classes"]:
            acts.append({"bucket": a["bucket"], "text": a["text"], "docs": [a["doc"]], "basis": "class", "timing": a["timing"]})
    drawn = [l for l in b["links"] if l["class"] == c and l["tier"] in ("direct", "shared")]
    for l in drawn:
        for ea in eff_actions:
            if ea["effect"] == l["effect"] and ea["bucket"]:
                acts.append({"bucket": ea["bucket"], "text": ea["note"], "docs": ea["basis"], "basis": "effect:" + l["effect"],
                             "inferred": not ea["basis"]})
    cl["actions"] = acts
    cl["buckets"] = sorted({a["bucket"] for a in acts}, key=list(BUCKETS).index)
    if spec and c in spec["classes"]:
        cl["specialties"] = spec["classes"][c]["by_type"]

# gap view: one row per class
def strength(c):
    ls = [l for l in b["links"] if l["class"] == c]
    if any(l["tier"] == "direct" and "class" in l["direct_scope"] for l in ls):
        return "direct"
    if any(l["tier"] == "direct" for l in ls):
        return "direct_group"
    if any(l["tier"] == "shared" for l in ls):
        return "shared"
    return "none"


gaps = []
for cl in b["classes"]:
    s, g = strength(cl["id"]), len(cl["guidance_docs"])
    backed = s in ("direct", "direct_group", "shared")
    quad = ("backed_and_covered" if backed and g >= 3 else "backed_not_covered" if backed else
            "covered_not_backed" if g >= 3 else "neither")
    gaps.append({"class": cl["id"], "evidence": s, "guidance_docs": g, "quadrant": quad,
                 "effects_backed_not_in_guidance": sorted(l["effect"] for l in b["links"] if l["class"] == cl["id"]
                                                          and l["tier"] in ("direct", "shared") and not l["guidance_docs"]),
                 "effects_in_guidance_not_backed": sorted(l["effect"] for l in b["links"] if l["class"] == cl["id"]
                                                          and l["tier"] == "guidance_only")})
b["gaps"] = {"rule": "backed = at least one direct or shared link; covered = named by 3 or more of the guidance documents",
             "classes": gaps,
             "missing_studies": [
                 {"topic": "Beta blockers and heat illness", "detail": "No class-specific study in the graph; only studies of antihypertensives as a group."},
                 {"topic": "SGLT2 inhibitors in heat", "detail": "Drug side links them to ketoacidosis and fluid loss; no study in heat."},
                 {"topic": "Lithium in hot climates", "detail": "One near-null study in a temperate climate; its authors call for study above 40 °C. No guidance document says to check levels."},
                 {"topic": "Wearables for people on these medicines", "detail": "Lab studies of heart rate, skin temperature and sweat in heat exist in the graph; none involves a medication. No guidance document mentions wearables."},
             ]}

if spec:
    b["specialties"] = {"source": spec["source"], "measure": spec["measure"], "sample": spec["sample"]}
b["scenarios"] = json.load(open(os.path.join(ref, "nyc_heat_scenarios.json")))
b["meta"]["counts"].update(guidance_documents=len(docs), guidance_mentions=len(mentions), guidance_actions=len(actions),
                           guidance_only_links=sum(1 for l in b["links"] if l["tier"] == "guidance_only"))
b["meta"]["outside_sources"] = "guidance, effect_actions, specialties, scenarios and gaps come from outside the graph"
bundle_io.write(b, bundle_path)
print("links added:", added, "| tiers:", dict(collections.Counter(l["tier"] for l in b["links"])))
print("quadrants:", dict(collections.Counter(g["quadrant"] for g in gaps)))
for g in gaps:
    print(f'{g["class"]:18} {g["evidence"]:13} docs={g["guidance_docs"]} {g["quadrant"]:20} backed-not-in-guidance={g["effects_backed_not_in_guidance"]}')
print("specialties:", "yes" if spec else "not yet")
