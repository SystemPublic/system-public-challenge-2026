"""FDA label audit: does each heat-risk drug's current label mention heat?

Source: openFDA drug/label.json (SPL label text). For each ingredient in
openfda_common.INGREDIENTS, one API call fetches the 25 most recently updated
prescription labels (sort=effective_time:desc), single-ingredient labels are
preferred (combination products used only if no single-ingredient label exists),
duplicate texts are collapsed, and up to 10 labels are audited.

Sections scanned: boxed_warning, warnings_and_cautions, warnings, precautions,
adverse_reactions, patient_counseling_information, information_for_patients,
spl_patient_package_insert, spl_medguide, instructions_for_use,
storage_and_handling, how_supplied.

Each sentence that matches a pattern is classified:
  env_heat      explicit heat / hot-weather / heat-stroke / reduced-sweating / heat-source
                warning in a clinical (non-storage) sentence      -> "heat warning"
  hyperthermia  incidental only: 'hyperthermia' / raised body temperature as a sign of NMS,
                serotonin syndrome or overdose; heat stroke in an NMS differential diagnosis;
                heat terms only inside adverse_reactions listings; 'heat intolerance' as a symptom
                (product-protection lines like "keep away from heat" count as storage)
  sweat_fluid   sweating, dehydration, fluid/volume loss only     -> indirect
  storage       storage-temperature language (Store at / degrees / avoid excessive heat
                in storage or how-supplied text)                   -> storage only
Per-ingredient tier = best tier on ANY audited label (generous to the label).

Usage:  uv run python scripts/fda_label_heat_audit.py
Outputs: data/processed/fda_label_heat_audit.csv (one row per label x category hit, plus
         'none' rows), data/processed/fda_label_heat_audit_summary.csv (one row per
         ingredient), data/raw/openfda/label_audit_summary.txt (headline).
"""
import csv, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from openfda_common import INGREDIENTS, PROCESSED, RAW, get, net_calls  # noqa: E402

LABEL = "https://api.fda.gov/drug/label.json"
SECTIONS = ["boxed_warning", "warnings_and_cautions", "warnings", "precautions", "adverse_reactions",
            "patient_counseling_information", "information_for_patients", "spl_patient_package_insert",
            "spl_medguide", "instructions_for_use", "storage_and_handling", "how_supplied"]
STORAGE_SECTIONS = {"storage_and_handling", "how_supplied"}

# Label search overrides: product form matters for these classes.
SEARCH_OVERRIDE = {
    "fentanyl": 'openfda.generic_name:"fentanyl" AND openfda.route:"TRANSDERMAL"',
    "buprenorphine": 'openfda.generic_name:"buprenorphine" AND openfda.route:"TRANSDERMAL"',
    "epinephrine": 'openfda.generic_name.exact:"EPINEPHRINE" AND openfda.route:"INTRAMUSCULAR"',
}

ENV_HEAT = re.compile(
    r"heat\s*stroke|heatstroke|heat exhaustion|heat[- ]related|heat illness|hot weather|hot climate|"
    r"hot environment|hot temperatures|warm weather|warm climate|high (?:environmental|ambient|outside|external) temperature|"
    r"(?:elevated|high) (?:environmental|ambient) temperature|exposure to (?:extreme |excessive )?heat|extreme heat|"
    r"excessive heat|heat exposure|external heat|heat sources?|heating pads?|electric blankets?|heated water ?beds?|"
    r"heat lamps?|saunas?|hot tubs?|sunbath|hot baths?|body temperature regulation|regulat\w* (?:of )?(?:core )?body temperature|"
    r"reduce core body temperature|anhidrosis|oligohidrosis|hypohidrosis|decreased sweating|reduced sweating|"
    r"(?:inability|unable|ability) to sweat|lack of sweating|not sweating|sweat less|\bheat\b", re.I)
HYPERTHERMIA = re.compile(r"hyperthermi\w*|elevated (?:body )?temperature|increased body temperature|body temperature increase", re.I)
SWEAT_FLUID = re.compile(r"sweat\w*|perspir\w*|diaphoresis|dehydrat\w*|fluid loss|loss of fluid|volume depletion|hypovolemi\w*|salt depletion", re.I)
STORAGE_SENT = re.compile(r"\bstor(?:e|ed|age|ing)\b|°|º|degrees|\bdeg\b|room temperature|refrigerat|excursions?|freez", re.I)
SENT_SPLIT = re.compile(r"(?<=[.;!?])\s+")
TIER_ORDER = ["env_heat", "hyperthermia", "sweat_fluid", "storage", "none"]
TIER_LABEL = {"env_heat": "heat warning", "hyperthermia": "incidental mention only (hyperthermia/heat as a sign, differential or side-effect listing)",
              "sweat_fluid": "sweating/dehydration only (indirect)", "storage": "storage temperature only", "none": "nothing"}


PRODUCT_PROTECT = re.compile(
    r"keep (?:\w+ )*?away from (?:direct )?heat|do not expose (?:\w+ )*?to (?:extreme |excessive |direct )?(?:heat|cold)|"
    r"protect(?:ed)? from (?:excessive )?heat|heat (?:and|or) (?:direct )?(?:sun)?light|sunlight or (?:radiant|direct) heat|"
    r"extreme (?:heat|cold) or (?:heat|cold)|out of direct light|do not (?:leave|store) .{0,40}(?:car|vehicle)", re.I)
INCIDENTAL_CONTEXT = re.compile(r"differential diagnosis|other serious medical conditions", re.I)


def _snip(s, m):
    a = max(0, m.start() - 110)
    return ("..." if a else "") + s[a:m.end() + 140] + ("..." if m.end() + 140 < len(s) else "")


def classify_label(lab):
    """Return {category: (section, snippet)}, first hit per category.

    env_heat is downgraded to 'storage' for product-protection sentences ("keep away from heat")
    and to 'hyperthermia' (incidental) when the only heat term is in an adverse-reaction listing,
    an NMS differential diagnosis, or 'heat intolerance' as a symptom.
    """
    hits = {}
    for sec in SECTIONS:
        for block in lab.get(sec, []) or []:
            for sent in SENT_SPLIT.split(block):
                s = " ".join(sent.split())
                is_storage = sec in STORAGE_SECTIONS or bool(STORAGE_SENT.search(s)) or bool(PRODUCT_PROTECT.search(s))
                for cat, rx in (("env_heat", ENV_HEAT), ("hyperthermia", HYPERTHERMIA), ("sweat_fluid", SWEAT_FLUID)):
                    m = rx.search(s)
                    if not m:
                        continue
                    if is_storage:
                        if cat == "env_heat" or STORAGE_SENT.search(s):
                            cat = "storage"
                        else:
                            continue
                    elif cat == "env_heat" and (sec == "adverse_reactions" or INCIDENTAL_CONTEXT.search(s)
                                                or not ENV_HEAT.search(re.sub(r"heat intolerance", "", s, flags=re.I))):
                        cat = "hyperthermia"
                    if cat not in hits:
                        hits[cat] = (sec, _snip(s, m))
                if is_storage and "storage" not in hits and re.search(r"°|º|degrees|room temperature|heat|cold", s, re.I):
                    hits["storage"] = (sec, s[:250])
    return hits


def main():
    rows, summary = [], []
    for cls, term, role in INGREDIENTS:
        q = SEARCH_OVERRIDE.get(term, f'openfda.generic_name:"{term}"') + ' AND openfda.product_type:"HUMAN PRESCRIPTION DRUG"'
        try:
            d = get(LABEL, {"search": q, "sort": "effective_time:desc", "limit": 25})
        except RuntimeError as e:
            print("stopping:", e, file=sys.stderr)
            break
        labs = d.get("results", [])
        single = [l for l in labs if all(" AND " not in g.upper() for g in l.get("openfda", {}).get("generic_name", [""]))]
        pool = single or labs
        seen, audited = set(), []
        for l in pool:
            key = tuple((l.get(s) or [""])[0][:400] for s in ("warnings_and_cautions", "warnings", "how_supplied"))
            if key in seen:
                continue
            seen.add(key)
            audited.append(l)
            if len(audited) == 10:
                break
        tier_counts = {t: 0 for t in TIER_ORDER}
        any_storage = False
        best, best_ex = "none", None
        for l in audited:
            of = l.get("openfda", {})
            hits = classify_label(l)
            any_storage = any_storage or "storage" in hits
            tier = next((t for t in TIER_ORDER if t in hits), "none")
            tier_counts[tier] += 1
            base = {"drug_class": cls, "ingredient": term, "role": role, "set_id": l.get("set_id", ""),
                    "effective_time": l.get("effective_time", ""), "generic_name": "; ".join(of.get("generic_name", [])),
                    "brand_name": "; ".join(of.get("brand_name", [])), "manufacturer": "; ".join(of.get("manufacturer_name", [])),
                    "label_tier": TIER_LABEL[tier]}
            for cat in TIER_ORDER[:-1]:
                if cat in hits:
                    rows.append(dict(base, category=TIER_LABEL[cat], section=hits[cat][0], snippet=hits[cat][1]))
            if not hits:
                rows.append(dict(base, category="nothing", section="", snippet=""))
            if best_ex is None or TIER_ORDER.index(tier) < TIER_ORDER.index(best):
                best = tier
                best_ex = (l.get("set_id", ""), hits.get(tier, ("", "")))
        summary.append({"drug_class": cls, "ingredient": term, "role": role, "label_query": q,
                        "n_labels_found": d.get("meta", {}).get("results", {}).get("total", 0) if not d.get("not_found") else 0,
                        "n_labels_audited": len(audited), "combination_labels_used": "yes" if not single and labs else "no",
                        "n_heat_warning": tier_counts["env_heat"], "n_hyperthermia_only": tier_counts["hyperthermia"],
                        "n_sweat_fluid_only": tier_counts["sweat_fluid"], "n_storage_only": tier_counts["storage"],
                        "n_nothing": tier_counts["none"],
                        "best_tier": TIER_LABEL[best] if audited else "no label found",
                        "three_way": ("heat warning" if best == "env_heat" else
                                      "storage temperature only" if any_storage else "nothing") if audited else "no label found",
                        "example_set_id": best_ex[0] if best_ex else "", "example_section": best_ex[1][0] if best_ex else "",
                        "example_snippet": best_ex[1][1] if best_ex else ""})
        print(f"{term:20s} labels={len(audited):2d} best={best:12s} {tier_counts}  calls={net_calls[0]}", file=sys.stderr)

    os.makedirs(PROCESSED, exist_ok=True)
    for name, data in [("fda_label_heat_audit.csv", rows), ("fda_label_heat_audit_summary.csv", summary)]:
        with open(os.path.join(PROCESSED, name), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(data[0].keys()))
            w.writeheader()
            w.writerows(data)

    lines = []
    for scope, keep in [("heat-risk ingredients (study + positive controls)", ("study", "positive_control")),
                        ("negative-control ingredients", ("negative_control",))]:
        s = [r for r in summary if r["role"] in keep and r["n_labels_audited"]]
        nw = [r for r in s if r["best_tier"] != TIER_LABEL["env_heat"]]
        lines.append(f"{len(nw)} of {len(s)} {scope} carry no explicit heat warning on any audited label.")
        for t in ("heat warning", "storage temperature only", "nothing"):
            names = [r["ingredient"] for r in s if r["three_way"] == t]
            lines.append(f"  [3-way] {t}: {len(names)}  {', '.join(names)}")
        lines.append("  [detail by best tier]")
        for t in TIER_ORDER:
            names = [r["ingredient"] for r in s if r["best_tier"] == TIER_LABEL[t]]
            lines.append(f"  {TIER_LABEL[t]}: {len(names)}  {', '.join(names)}")
    classes = {}
    for r in summary:
        if r["role"] in ("study", "positive_control") and r["n_labels_audited"]:
            t = TIER_ORDER.index(next(k for k, v in TIER_LABEL.items() if v == r["best_tier"]))
            classes[r["drug_class"]] = min(classes.get(r["drug_class"], 9), t)
    lines.append(f"By class (best ingredient): {sum(1 for t in classes.values() if t != 0)} of {len(classes)} classes have no ingredient with a heat warning.")
    for t in TIER_ORDER:
        lines.append(f"  {TIER_LABEL[t]}: {', '.join(c for c, v in classes.items() if v == TIER_ORDER.index(t))}")
    txt = "\n".join(lines)
    print(txt)
    with open(os.path.join(RAW, "label_audit_summary.txt"), "w") as f:
        f.write("openFDA drug/label.json audit, accessed 2026-11-14. Label text check, not a legal review.\n" + txt + "\n")


if __name__ == "__main__":
    main()
