"""Go/no-go check: how much medication x heat evidence does the System Public Graph hold?

Two modes:
  API  (needs a beta key):  set SYSTEM_API_KEY, then  py -3 scripts/graph_check.py api
  CSV  (no key, ~450 MB):    py -3 scripts/graph_check.py csv path/to/system-public-graph-v1-associations.csv

Both modes match drug terms in one variable name and heat-outcome terms in the
other variable name of each association (finding), then count findings and
distinct studies per drug x outcome. Output: data/graph_coverage.csv

Text matching on variable names is deliberate: concept grounding is incomplete
(see the graph's Limitations page), so name matching catches more. Expect some
false positives; hand-check a sample before quoting numbers.
"""
import csv, os, re, sys, time
from collections import defaultdict

DRUGS = {
    "lithium": ["lithium"],
    "loop diuretics": ["furosemide", "bumetanide", "torsemide", "loop diuretic"],
    "thiazides": ["thiazide", "hydrochlorothiazide", "chlorthalidone", "indapamide"],
    "diuretics (any)": ["diuretic"],
    "ACEi/ARB": ["ace inhibitor", "angiotensin-converting", "angiotensin receptor", "lisinopril", "ramipril", "enalapril", "losartan", "valsartan", "candesartan", "renin-angiotensin"],
    "beta blockers": ["beta blocker", "beta-blocker", "β-blocker", "metoprolol", "propranolol", "atenolol", "carvedilol", "bisoprolol"],
    "insulin": ["insulin"],
    "SGLT2 inhibitors": ["sglt2", "sglt-2", "empagliflozin", "dapagliflozin", "canagliflozin", "gliflozin"],
    "anticholinergics": ["anticholinergic", "antimuscarinic", "oxybutynin", "benztropine", "diphenhydramine", "tolterodine"],
    "antipsychotics": ["antipsychotic", "neuroleptic", "olanzapine", "quetiapine", "risperidone", "haloperidol", "clozapine", "aripiprazole"],
    "antidepressants/SSRIs": ["ssri", "antidepressant", "sertraline", "fluoxetine", "citalopram", "escitalopram", "paroxetine"],
    "topiramate/zonisamide": ["topiramate", "zonisamide"],
    "stimulants": ["methylphenidate", "amphetamine", "stimulant medication", "adhd medication"],
    "NSAIDs": ["nsaid", "non-steroidal anti-inflammatory", "ibuprofen", "naproxen"],
    "opioids/fentanyl": ["opioid", "fentanyl", "buprenorphine"],
    "benzodiazepines": ["benzodiazepine", "lorazepam", "diazepam", "alprazolam"],
    "metformin": ["metformin"],
    "sulfonylureas": ["sulfonylurea", "glipizide", "glyburide", "glibenclamide", "gliclazide"],
}

OUTCOMES = {
    "heat illness/stroke": ["heat stroke", "heatstroke", "heat illness", "heat-related illness", "heat exhaustion", "exertional heat"],
    "hyperthermia/body temp": ["hyperthermia", "core temperature", "body temperature", "thermoregulation"],
    "ambient heat/heat wave": ["heat wave", "heatwave", "ambient temperature", "high temperature", "extreme heat", "hot weather", "heat exposure"],
    "sweating": ["sweat", "anhidrosis", "hypohidrosis", "oligohidrosis"],
    "dehydration/volume": ["dehydration", "volume depletion", "hypovolemia"],
    "hyponatremia": ["hyponatremia", "hyponatraemia", "serum sodium"],
    "acute kidney injury": ["acute kidney injury", "acute renal failure"],
}

HEAT_CORE = {"heat illness/stroke", "hyperthermia/body temp", "ambient heat/heat wave", "sweating"}


def compile_terms(d):
    return {k: re.compile("|".join(re.escape(t) for t in v), re.I) for k, v in d.items()}

DRUG_RE, OUT_RE = compile_terms(DRUGS), compile_terms(OUTCOMES)


def classify(n1, n2):
    """Yield (drug, outcome) pairs where one variable names a drug and the other an outcome."""
    n1, n2 = n1 or "", n2 or ""
    for a, b in ((n1, n2), (n2, n1)):
        for drug, dre in DRUG_RE.items():
            if dre.search(a):
                for out, ore in OUT_RE.items():
                    if ore.search(b):
                        yield drug, out


def tally(rows):
    """rows: iterable of (var1_name, var2_name, study_id, assoc_id)."""
    findings = defaultdict(set)
    studies = defaultdict(set)
    examples = defaultdict(list)
    for v1, v2, sid, aid in rows:
        for pair in set(classify(v1, v2)):
            findings[pair].add(aid)
            studies[pair].add(sid)
            if len(examples[pair]) < 3:
                examples[pair].append(f"{v1} <-> {v2}")
    return findings, studies, examples


def write_out(findings, studies, examples, path="data/graph_coverage.csv"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["drug", "outcome", "heat_core_outcome", "findings", "distinct_studies", "example_variable_pairs"])
        for drug in DRUGS:
            for out in OUTCOMES:
                k = (drug, out)
                w.writerow([drug, out, out in HEAT_CORE, len(findings[k]), len(studies[k]), " | ".join(examples[k])])
    total_f = sum(len(findings[(d, o)]) for d in DRUGS for o in HEAT_CORE)
    total_s = len(set().union(*[studies[(d, o)] for d in DRUGS for o in HEAT_CORE]) or [])
    print(f"\nWrote {path}")
    print(f"Drug x core-heat outcome findings: {total_f}   distinct studies: {total_s}")
    print("Rule of thumb from the plan: hundreds = go; a few dozen = go, but make thinness a finding; near zero = switch ideas.")
    for drug in DRUGS:
        n = sum(len(findings[(drug, o)]) for o in HEAT_CORE)
        print(f"  {drug:24s} core-heat findings: {n}")


def run_csv(path):
    import pandas as pd
    cols = ["system_id", "study_id", "variable_1_name", "variable_2_name"]
    def gen():
        for chunk in pd.read_csv(path, usecols=cols, chunksize=200_000, dtype=str):
            yield from zip(chunk.variable_1_name, chunk.variable_2_name, chunk.study_id, chunk.system_id)
    write_out(*tally(gen()))


def load_dotenv(path=os.path.join(os.path.dirname(__file__), "..", ".env")):
    """Read KEY=value lines from the project .env without overriding real env vars."""
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def run_api():
    import requests
    load_dotenv()
    key = os.environ.get("SYSTEM_API_KEY")
    if not key:
        sys.exit("Set SYSTEM_API_KEY first (the key from the beta portal / organizers).")
    base = "https://public-api.system.com/v1"
    s = requests.Session(); s.headers["x-api-key"] = key
    calls = 0

    def get(path, **params):
        nonlocal calls
        for attempt in range(4):
            r = s.get(base + path, params=params, timeout=60); calls += 1
            if r.status_code == 429:
                time.sleep(5 * (attempt + 1)); continue
            r.raise_for_status(); return r.json()
        r.raise_for_status()

    def paged(path, page=100, cap=2000, **params):
        out, off = [], 0
        while off < cap:
            data = get(path, offset=off, limit=page, **params).get("data", [])
            out += data
            if len(data) < page: break
            off += page
        return out

    # Variable-name search is fuzzy (millions of hits), so start from the heat side:
    # find each heat-outcome concept, pull all of its concept-to-concept relationships,
    # and keep the ones whose other end is a drug.
    HEAT_CONCEPTS = {
        "heat illness/stroke": ["heat stroke", "heat illness", "heat exhaustion", "heat-related illness", "hot"],
        "hyperthermia/body temp": ["hyperthermia", "body temperature", "thermoregulation", "fever"],
        "ambient heat/heat wave": ["heat wave", "ambient temperature", "extreme heat", "temperature"],
        "sweating": ["sweating", "anhidrosis", "hypohidrosis", "hyperhidrosis"],
        "dehydration/volume": ["dehydration", "hypovolemia"],
        "hyponatremia": ["hyponatremia"],
        "acute kidney injury": ["acute kidney injury"],
    }
    out_rows, seen = [], set()
    for outcome, labels in HEAT_CONCEPTS.items():
        for label in labels:
            hits = get("/concepts", search=f"wikidata_label:{label}", limit=5).get("data", [])
            hits = [c for c in hits if c["wikidata_label"].lower() == label] or hits[:1]
            for c in hits:
                rels = paged(f"/concepts/{c['system_id']}/relationships", page=1000, cap=20000)
                for rel in rels:
                    other = rel["target_concept"] if rel["source_concept"]["system_id"] == c["system_id"] else rel["source_concept"]
                    text_label = other.get("wikidata_label") or ""
                    for drug, dre in DRUG_RE.items():
                        if dre.search(text_label):
                            key = (rel["relationship_id"], drug, outcome)
                            if key in seen: continue
                            seen.add(key)
                            out_rows.append([drug, outcome, c["wikidata_label"], text_label,
                                             rel["source_concept"]["wikidata_label"] + " -> " + rel["target_concept"]["wikidata_label"],
                                             rel["num_findings"], rel["num_studies"], rel.get("last_published_date"), rel["relationship_id"]])
                print(f"{outcome:24s} {c['wikidata_label']!r}: {len(rels)} relationships ({calls} calls)")

    os.makedirs("data", exist_ok=True)
    with open("data/graph_heat_relationships.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["drug_group", "outcome_group", "heat_concept", "drug_concept", "relationship", "num_findings", "num_studies", "last_published_date", "relationship_id"])
        w.writerows(sorted(out_rows, key=lambda r: (r[0], r[1], -r[6])))
    with open("data/graph_coverage.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["drug", "outcome", "heat_core_outcome", "relationships", "findings", "studies_summed"])
        for drug in DRUGS:
            for out in HEAT_CONCEPTS:
                rs = [r for r in out_rows if r[0] == drug and r[1] == out]
                w.writerow([drug, out, out in HEAT_CORE, len(rs), sum(r[5] for r in rs), sum(r[6] for r in rs)])
    print("\nWrote data/graph_heat_relationships.csv and data/graph_coverage.csv")
    for drug in DRUGS:
        core = [r for r in out_rows if r[0] == drug and r[1] in HEAT_CORE]
        other = [r for r in out_rows if r[0] == drug and r[1] not in HEAT_CORE]
        print(f"  {drug:24s} core-heat findings {sum(r[5] for r in core):5d} (rels {len(core):3d}) | dehydration/Na/AKI findings {sum(r[5] for r in other):5d}")
    print(f"API calls used: {calls} (daily limit 10,000)")
    print("Note: drug matching uses concept labels; check drug_concept in the CSV for false matches (e.g. 'insulin resistance').")


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "api":
        run_api()
    elif len(sys.argv) >= 3 and sys.argv[1] == "csv":
        run_csv(sys.argv[2])
    else:
        sys.exit(__doc__)
