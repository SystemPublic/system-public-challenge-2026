"""HeatRx v2: merge the teammate's evidence grid, guidance coding, label patterns and timed actions
(branch stella/heat-med-guide, commit d2188ae, copied into reference/stella/) with our bundle, and add the
patient-level risk factors and NYC heat-vulnerability lookup for the heat check.

Usage (from the repo root), after merge_outside.py:
  python3 -I scripts/merge_v2.py bundle/evidence.json reference
"""
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bundle_io  # noqa: E402

bundle_path, ref = sys.argv[1:3]
b = json.load(open(bundle_path))
S = os.path.join(ref, "stella")
grid = json.load(open(os.path.join(S, "grid_data.json")))
guid = json.load(open(os.path.join(S, "guidance.json")))
lens = json.load(open(os.path.join(S, "lenses_data.json")))

# her class rows -> our class ids (for the body map and our evidence links); None = no equivalent
CLASS_MAP = {
    "Diuretics": "diuretics", "ACE inhibitors / ARBs": "acei_arb", "Beta blockers": "beta_blockers",
    "Calcium channel blockers": "ccb", "Anticholinergics": "anticholinergics", "Antipsychotics": "antipsychotics",
    "Lithium": "lithium", "Antidepressants": "antidepressants", "Benzodiazepines / sedatives": "opioids_sedatives",
    "Opioids": "opioids_sedatives", "Insulin": "insulin", "SGLT2 inhibitors": "sglt2",
    "Metformin and sulfonylureas": "other_diabetes", "NSAIDs": "nsaids", "Topiramate / zonisamide": "anticonvulsants",
    "Stimulants": "stimulants", "GLP-1 agonists": "other_diabetes",
}
# generic names for the medication picker, per her class rows
NAMES = {
    "Diuretics": ["furosemide", "bumetanide", "torsemide", "hydrochlorothiazide", "chlorthalidone", "indapamide", "spironolactone", "amiloride", "acetazolamide"],
    "ACE inhibitors / ARBs": ["lisinopril", "enalapril", "ramipril", "perindopril", "captopril", "benazepril", "losartan", "valsartan", "candesartan", "telmisartan", "irbesartan", "olmesartan", "sacubitril/valsartan"],
    "Beta blockers": ["metoprolol", "atenolol", "propranolol", "bisoprolol", "carvedilol", "nebivolol"],
    "Calcium channel blockers": ["amlodipine", "nifedipine", "felodipine", "diltiazem", "verapamil"],
    "Anticholinergics": ["oxybutynin", "tolterodine", "solifenacin", "trospium", "benztropine", "trihexyphenidyl", "scopolamine", "glycopyrrolate", "diphenhydramine", "hydroxyzine", "promethazine"],
    "Antipsychotics": ["haloperidol", "olanzapine", "clozapine", "risperidone", "quetiapine", "aripiprazole", "chlorpromazine"],
    "Lithium": ["lithium carbonate"],
    "Antidepressants": ["sertraline", "fluoxetine", "paroxetine", "citalopram", "escitalopram", "venlafaxine", "duloxetine", "amitriptyline", "nortriptyline", "mirtazapine", "bupropion", "trazodone"],
    "Benzodiazepines / sedatives": ["diazepam", "lorazepam", "alprazolam", "clonazepam", "temazepam", "zolpidem", "zopiclone"],
    "Opioids": ["morphine", "oxycodone", "hydrocodone", "tramadol", "fentanyl patch", "methadone", "buprenorphine"],
    "Insulin": ["insulin glargine", "insulin lispro", "insulin aspart", "insulin degludec", "NPH insulin", "regular insulin"],
    "SGLT2 inhibitors": ["empagliflozin", "dapagliflozin", "canagliflozin"],
    "Metformin and sulfonylureas": ["metformin", "glipizide", "gliclazide", "glimepiride", "glyburide"],
    "NSAIDs": ["ibuprofen", "naproxen", "diclofenac", "meloxicam", "celecoxib", "aspirin (pain dose)"],
    "Topiramate / zonisamide": ["topiramate", "zonisamide"],
    "Stimulants": ["methylphenidate", "amphetamine", "lisdexamfetamine"],
    "GLP-1 agonists": ["semaglutide", "liraglutide", "dulaglutide", "tirzepatide"],
    "Parkinson / dopaminergic": ["levodopa/carbidopa", "pramipexole", "ropinirole"],
    "Cholinesterase inhibitors": ["donepezil", "rivastigmine", "galantamine"],
    "Heat-labile emergency products": ["epinephrine auto-injector", "salbutamol inhaler", "albuterol inhaler", "nitroglycerin"],
}
# Corrections from our abstract checks to her direct entries
OVERRIDES = {
    "16911573": {"effect": "null", "summary": "Thiazide-induced low sodium: no correlation of monthly cases with air temperature (r = -0.056, p = 0.65); 201 cases, Hong Kong",
                 "correction": "Our abstract check: the paper reports no correlation with air temperature (C-ref F33)."},
    "37280056": {"effect": "unclear", "correction": "The ratio is per unit of serum potassium, not a heat effect; the paper shows potassium peaking in winter (C16)."},
    "31205291": {"effect": "null", "correction": "A cold-weather finding labelled as ambient temperature (C22)."},
}

lens_rows = {r["class"]: r for r in lens["rows"]}
actions = lens["actions"]
classes = []
for r in grid["rows"]:
    name = r["class"]
    cells = {}
    for bk, c in r["cells"].items():
        d = []
        for x in c.get("direct", []):
            x = dict(x)
            if x["pmid"] in OVERRIDES:
                x.update(OVERRIDES[x["pmid"]])
            d.append(x)
        cells[bk] = {k: c.get(k) for k in ("tier", "strength", "vetted", "signal", "action", "note")}
        cells[bk]["direct"] = d
        cells[bk]["mechanisms"] = [{k: m.get(k) for k in ("mechanism", "primary", "drug_studies", "drug_unvetted", "heat_studies", "heat_unvetted")}
                                   for m in c.get("mechanisms", [])]
    lr = lens_rows.get(name, {})
    classes.append({
        "name": name, "our_id": CLASS_MAP.get(name), "examples": r.get("examples", ""), "specialties": r.get("specialties", []),
        "names": NAMES.get(name, []), "cells": cells, "guidance": guid["classes"].get(name, {}),
        "pattern": lr.get("pattern"), "finding": lr.get("finding"),
        "label": {k: lr.get(k) for k in lr if k.startswith("label")} or None,
        "research": lr.get("research"),
    })

hvi = {}
with open(os.path.join(S, "nyc_zcta_lookup.csv"), newline="") as fh:
    for row in csv.DictReader(fh):
        if row["hvi"]:
            hvi[row["zcta"]] = {"hvi": int(row["hvi"]), "neighbourhood": row["neighbourhood"], "borough": row["borough"]}
rfs = list(csv.DictReader(open(os.path.join(ref, "risk_factors.csv"), newline="")))

b["v2"] = {
    "source_note": "Evidence grid, guidance coding, label patterns and timed actions from the teammate's pipeline "
                   "(branch stella/heat-med-guide, d2188ae); corrections from our abstract checks applied.",
    "buckets": grid["buckets"],
    "classes": classes,
    "general_direct": grid.get("general", []),
    "guidance_sources": guid["sources"],
    "alignment_checks": guid.get("alignment_checks", []),
    "patterns": lens["patterns"],
    "scorecard": lens.get("scorecard", []),
    "timing": actions.get("timing", {}),
    "actions": actions.get("items", []),
    "actions_all_classes": actions.get("all_classes", []),
    "risk_factors": rfs,
    "hvi": hvi,
    "hvi_source": "NYC Heat Vulnerability Index by ZIP (NYC Environment and Health Data Portal), via the teammate's lookup",
}
# paper titles for the teammate's studies, action citations and risk factors (cached by pubmed_meta.py)
meta_path = os.path.join(os.path.dirname(os.path.dirname(bundle_path)), "data", "pubmed", "summaries.json")
if os.path.exists(meta_path):
    meta = json.load(open(meta_path))
    want = {d["pmid"] for c in classes for cell in c["cells"].values() for d in cell["direct"]}
    want |= {p for a in b["v2"]["actions"] for p in a.get("pmids", [])} | {r["pmid"] for r in rfs}
    for p in want:
        if p in meta:
            b["papers"][p] = meta[p]
bundle_io.write(b, bundle_path)
print("classes:", len(classes), "| mapped to our ids:", sum(1 for c in classes if c["our_id"]),
      "| actions:", len(b["v2"]["actions"]), "| risk factors:", len(rfs), "| HVI ZIPs:", len(hvi))
print("label keys sample:", list((classes[0]["label"] or {}).keys()), "| research keys:", list((classes[0]["research"] or {}).keys()))
print("lens row keys:", list(lens["rows"][0].keys()))
