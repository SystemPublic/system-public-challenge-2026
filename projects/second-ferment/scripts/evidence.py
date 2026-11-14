"""Build the HeatRx evidence bundle (PRD phase 1).

Three routes from a drug class to heat:
  1. Direct by name     a finding with a drug variable on one side and a heat variable on the other
  2. Shared pathway     drug class -> effect (drug arm) and environmental heat -> same effect (heat arm)
  3. Population         a heat finding whose study population is defined by a medication
Routes 1 and 3 are hand-curated in reference/direct_evidence.csv; this script lists the candidates
for that curation and attaches the matching graph rows. Route 2 is computed here.

Usage (from the repo root):
  python3 -I scripts/evidence.py data/graph.db data/api reference data/derived/evidence bundle/evidence.json

Optional input: data/pubmed/summaries.json (written by scripts/pubmed_meta.py) adds title, journal and year.
"""
import collections
import csv
import datetime
import json
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heat_meds_lib as L  # noqa: E402

db_path, api_dir, ref_dir, derived_dir, bundle_path = sys.argv[1:6]
os.makedirs(derived_dir, exist_ok=True)
os.makedirs(os.path.dirname(bundle_path), exist_ok=True)

MIN_DRUG_RAISED = 3   # studies with a significantly raised ratio needed on the drug arm
MIN_HEAT_STUDIES = 2  # studies needed on the heat arm
EXTRA_EFFECTS = {     # effects that only appear in curated direct evidence
    "drug_level": ("Drug levels", "kidney"),
    "storage": ("Storage and stability", None),
    "overdose": ("Overdose (drug use)", None),
}

db = sqlite3.connect("file:%s?mode=ro" % db_path, uri=True)
cols = ("system_id, pubmed_id, study_id, system_statistic_type, statistic_value, ci_lower, ci_upper, p_value, "
        "variable_1_name, variable_2_name")

findings = {}                                  # id -> row dict
drug_arm = collections.defaultdict(list)       # (class, effect) -> [finding id]
heat_arm = collections.defaultdict(list)       # effect -> [finding id]
direct_cand = []                               # finding ids with a drug and a heat-tier variable
heat_rows_by_study = collections.defaultdict(list)


def keep(r, src):
    sid, pmid, study, stat, val, lo, hi, p, n1, n2 = r
    if sid not in findings:
        findings[sid] = {"id": sid, "pmid": pmid or "", "study": study, "stat": stat or "", "value": val,
                         "lo": lo, "hi": hi, "p": p, "v1": n1, "v2": n2, "src": src,
                         "dir": L.direction(stat, lo, hi)}
    return sid


def scan(r, src):
    n1, n2 = r[8] or "", r[9] or ""
    f = (L.focus_classes(n1), L.focus_classes(n2))
    anydrug = (bool(L.drug_classes(n1)), bool(L.drug_classes(n2)))
    t = (L.heat_tier(n1), L.heat_tier(n2))
    names = (n1, n2)
    for i in (0, 1):
        j = 1 - i
        # drug arm: drug variable on side i, an effect on side j, side j not itself a drug or heat variable
        if f[i] and not anydrug[j] and t[j] != "direct":
            if not L.effects(names[i]):  # skip "thiazide-induced hyponatremia" -> fracture
                for e in L.effects(names[j]):
                    sid = keep(r, src)
                    for c in f[i]:
                        drug_arm[(c, e)].append(sid)
        # heat arm: environmental heat exposure on side i, an effect on side j, no drug on either side
        if L.env_heat(names[i]) and not L.effects(names[i]) and not anydrug[0] and not anydrug[1]:
            for e in L.effects(names[j]):
                heat_arm[e].append(keep(r, src))
        # direct candidates for curation
        if f[i] and t[j] == "direct":
            direct_cand.append(keep(r, src))
    if L.env_heat(n1) or L.env_heat(n2):
        heat_rows_by_study[r[2]].append(r)


n = 0
for r in db.execute("SELECT %s FROM associations" % cols):
    n += 1
    scan(r, "in_csv")
print("CSV findings scanned:", n)

# API rows that are not in the CSV (heat side only; see docs/DATA.md "Live API")
api_n = 0
with open(os.path.join(api_dir, "heat_associations.csv"), newline="") as fh:
    for a in csv.DictReader(fh):
        if a["api_status"] == "in_csv" or a["system_id"] in findings:
            continue
        api_n += 1
        r = (a["system_id"], a["pubmed_id"], a["study_id"], a["system_statistic_type"], a["statistic_value"],
             a["ci_lower"] or None, a["ci_upper"] or None, a["p_value"] or None, a["variable_1_name"], a["variable_2_name"])
        scan(r, a["api_status"])
print("API-only heat findings scanned:", api_n)

# study details for every kept finding (CSV studies only; API-only studies have none locally)
study_ids = list({f["study"] for f in findings.values()} | set(heat_rows_by_study))
studies = {}
for i in range(0, len(study_ids), 500):
    ch = study_ids[i:i + 500]
    q = "SELECT study_id, doi, pubmed_id, population_string FROM studies WHERE study_id IN (%s)" % ",".join("?" * len(ch))
    for sid, doi, pmid, pop in db.execute(q, ch):
        studies[sid] = (doi or "", pmid or "", pop or "")
for f in findings.values():
    doi, pmid, pop = studies.get(f["study"], ("", "", ""))
    f["doi"] = doi
    f["pmid"] = f["pmid"] or pmid
    f["pop"] = pop[:240]

# drop animal studies from both arms
animal = {i for i, f in findings.items() if L.ANIMAL.search(" ".join([f["v1"] or "", f["v2"] or "", f["pop"]]))}
for d in (drug_arm, heat_arm):
    for k in list(d):
        d[k] = [i for i in d[k] if i not in animal]
print("animal findings dropped:", len(animal))

# route 3 candidates: heat findings whose population names a focus class
pop_cand = []
for study, rows in heat_rows_by_study.items():
    pop = studies.get(study, ("", "", ""))[2]
    cls = L.focus_classes(pop)
    if cls:
        for r in rows:
            sid = keep(r, "in_csv")
            findings[sid].update(doi=studies[study][0], pop=pop[:240])
            pop_cand.append((sid, ";".join(cls)))


def explicit_heat_studies(ids):
    """Heat-arm studies whose exposure is explicitly high heat and whose result does not point the protective way."""
    out = set()
    for i in ids:
        f = findings[i]
        expo = f["v1"] if L.env_heat(f["v1"] or "") and not L.effects(f["v1"] or "") else f["v2"]
        if L.HIGH.search(expo or "") and f["dir"] != "lowered":
            out.add(f["study"])
    return len(out)


def study_direction(ids):
    """Collapse rows to studies; a study counts as raised if any row is raised, else lowered, else unclear."""
    by = collections.defaultdict(set)
    for i in ids:
        by[findings[i]["study"]].add(findings[i]["dir"])
    out = collections.Counter()
    for dirs in by.values():
        for d in ("raised", "lowered", "unclear", "not_ratio"):
            if d in dirs:
                out[d] += 1
                break
    return {"studies": len(by), "raised": out["raised"], "lowered": out["lowered"],
            "unclear": out["unclear"], "not_ratio": out["not_ratio"]}


# curated direct evidence
direct = []
cand_by_pmid = collections.defaultdict(set)
for sid in direct_cand + [p[0] for p in pop_cand]:
    cand_by_pmid[findings[sid]["pmid"]].add(sid)
with open(os.path.join(api_dir, "heat_med_api.csv"), newline="") as fh:
    for a in csv.DictReader(fh):
        if a["system_id"] not in findings:
            r = (a["system_id"], a["pubmed_id"], a["study_id"], a["system_statistic_type"], a["statistic_value"],
                 a["ci_lower"] or None, a["ci_upper"] or None, a["p_value"] or None, a["variable_1_name"], a["variable_2_name"])
            keep(r, a["api_status"])
            findings[a["system_id"]].update(doi="", pop="")
        cand_by_pmid[a["pubmed_id"]].add(a["system_id"])
levels = json.load(open(os.path.join(ref_dir, "direct_levels.json")))
corrections = {}
with open(os.path.join(ref_dir, "corrections.csv"), newline="") as fh:
    for c in csv.DictReader(fh):
        corrections[c["pmid"]] = {"text": c["correction"], "caveat": c["caveat"]}
with open(os.path.join(ref_dir, "direct_evidence.csv"), newline="") as fh:
    for d in csv.DictReader(fh):
        if d["include"] != "yes":
            continue
        d["classes"] = [c for c in d["classes"].split(";") if c]
        d["finding_ids"] = sorted(cand_by_pmid.get(d["pmid"], ()))
        d["levels"] = levels.get(d["id"])
        del d["include"]
        direct.append(d)

# links: every class x effect with any drug-arm study
effect_meta = {e: (lab, hub) for e, lab, hub, _ in L.EFFECTS}
effect_meta.update(EXTRA_EFFECTS)
heat_summary = {e: dict(study_direction(ids), explicit_high=explicit_heat_studies(ids)) for e, ids in heat_arm.items()}
links = []
for c, _, _, _ in L.FOCUS:
    for e in list(effect_meta):
        ids = sorted(set(drug_arm.get((c, e), [])))
        dirs = [x for x in direct if c in x["classes"] and x["effect"] == e]
        if not ids and not dirs:
            continue
        arm = study_direction(ids)
        heat = heat_summary.get(e, {"studies": 0, "explicit_high": 0})
        if any(x["context"] != "misuse" for x in dirs):
            tier = "direct"
        elif (arm["raised"] >= MIN_DRUG_RAISED and arm["raised"] > arm["lowered"]
              and heat["studies"] >= MIN_HEAT_STUDIES and heat["explicit_high"] >= 1):
            tier = "shared"
        elif dirs:
            tier = "direct_misuse"
        else:
            tier = "weak"
        links.append({"class": c, "effect": e, "tier": tier,
                      "direct_scope": sorted({x["scope"] for x in dirs if x["context"] != "misuse"}),
                      "direct_ids": [x["id"] for x in dirs], "drug_arm": arm, "drug_arm_ids": ids,
                      "heat_arm_studies": heat["studies"]})

# paper metadata, if fetched
meta_path = os.path.join(os.path.dirname(os.path.dirname(bundle_path)), "data", "pubmed", "summaries.json")
papers = {}
used = set()
for l in links:
    used.update(l["drug_arm_ids"])
for ids in heat_arm.values():
    used.update(ids)
for d in direct:
    used.update(d["finding_ids"])
pmids = sorted({findings[i]["pmid"] for i in used if findings[i]["pmid"]} | {d["pmid"] for d in direct})
if os.path.exists(meta_path):
    allmeta = json.load(open(meta_path))
    papers = {p: allmeta[p] for p in pmids if p in allmeta}
with open(os.path.join(derived_dir, "pmids.txt"), "w") as fh:
    fh.write("\n".join(pmids) + "\n")

# class totals for dot sizes
class_totals = {}
for c, _, _, _ in L.FOCUS:
    ls = [l for l in links if l["class"] == c]
    class_totals[c] = {"links_shown": sum(1 for l in ls if l["tier"] in ("direct", "shared")),
                       "raised_studies": sum(l["drug_arm"]["raised"] for l in ls if l["tier"] in ("direct", "shared")),
                       "direct_findings": sum(len(l["direct_ids"]) for l in ls if l["tier"] == "direct")}

for i in used:
    if findings[i]["pmid"] in corrections:
        findings[i]["correction"] = corrections[findings[i]["pmid"]]

bundle = {
    "meta": {
        "generated": datetime.date.today().isoformat(),
        "source": "System Public Graph, Dataverse snapshot v2.1 (doi:10.7910/DVN/7V6JDO) and live API; CC BY-NC 4.0",
        "rules": {"min_drug_raised_studies": MIN_DRUG_RAISED, "min_heat_studies": MIN_HEAT_STUDIES,
                  "shared_requires": "drug arm: at least %d studies with a significantly raised ratio, and more raised than lowered; heat arm: at least %d studies, at least one with explicitly high heat that does not point the protective way" % (MIN_DRUG_RAISED, MIN_HEAT_STUDIES),
                  "tiers": {"direct": "drug and heat studied together (curated, abstract-checked)",
                            "shared": "drug linked to the effect and heat linked to the same effect, in different studies",
                            "direct_misuse": "drug and heat studied together, but for drug use or overdose",
                            "weak": "drug arm below threshold or no heat arm; not drawn by default",
                            "guidance_only": "added in phase 2 from guidance documents"}},
        "counts": {"findings": len(findings), "links": len(links), "direct": len(direct), "papers_with_metadata": len(papers)},
    },
    "classes": [{"id": c, "label": lab, "named_in_brief": brief, "members": L.MEMBERS[c], **class_totals[c]}
                for c, _, lab, brief in L.FOCUS],
    "hubs": [{"id": h, "label": lab} for h, lab in L.HUBS],
    "effects": [{"id": e, "label": effect_meta[e][0], "hub": effect_meta[e][1]} for e in effect_meta],
    "links": links,
    "heat_arms": [{"effect": e, **heat_summary[e], "ids": sorted(set(ids))} for e, ids in heat_arm.items()],
    "direct": direct,
    "findings": {i: findings[i] for i in sorted(used)},
    "papers": papers,
}
with open(bundle_path, "w") as fh:
    json.dump(bundle, fh, separators=(",", ":"))
print("bundle:", bundle_path, round(os.path.getsize(bundle_path) / 1e6, 2), "MB", json.dumps(bundle["meta"]["counts"]))

# row-level exports for reading
def dump(name, ids, extra=None):
    with open(os.path.join(derived_dir, name), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["key", "id", "pmid", "src", "dir", "stat", "value", "lo", "hi", "v1", "v2", "pop"])
        for key, i in ids:
            f = findings[i]
            w.writerow([key, i, f["pmid"], f["src"], f["dir"], f["stat"], f["value"], f["lo"], f["hi"], f["v1"], f["v2"], f.get("pop", "")])


dump("drug_arm_rows.csv", [("%s|%s" % k, i) for k, ids in sorted(drug_arm.items()) for i in sorted(set(ids))])
dump("heat_arm_rows.csv", [(e, i) for e, ids in sorted(heat_arm.items()) for i in sorted(set(ids))])
dump("direct_candidates.csv", [("direct", i) for i in sorted(set(direct_cand))] + [("population:" + c, i) for i, c in pop_cand])
with open(os.path.join(derived_dir, "links.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["class", "effect", "tier", "drug_studies", "raised", "lowered", "unclear", "not_ratio", "heat_studies", "direct_ids"])
    for l in links:
        a = l["drug_arm"]
        w.writerow([l["class"], l["effect"], l["tier"], a["studies"], a["raised"], a["lowered"], a["unclear"], a["not_ratio"],
                    l["heat_arm_studies"], ";".join(l["direct_ids"])])
print("heat arms:", {e: (s["studies"], s["raised"]) for e, s in heat_summary.items()})
