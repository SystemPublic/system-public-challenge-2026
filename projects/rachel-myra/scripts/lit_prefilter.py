"""Rule-based prefilter before LLM screening (spec §8.4 step 4; rules in
data/raw/literature/screening_rules.md).

Drops only *obvious* exclusions, in this order (first matching rule wins):
  P1 no abstract                                   (rule E1)
  P2 animal-only MeSH: "Animals" without "Humans",
     unless it looks like a medicine-stability study (rule E2)
  P3 materials science / chemistry keywords, no clinical words, and no drug
     other than lithium named (rule E3)
  P4 storage-query record naming none of the 15 drugs/classes (or inhaler /
     glucose strip) in title/abstract/MeSH         (rule E6)
  P5 no heat / temperature word in title/abstract/MeSH (rule E7)
  P6 NMS / serotonin syndrome / malignant hyperthermia in the title and
     no environmental-heat word anywhere            (rule E5)
Everything else goes to LLM screening. Records are written to chunk files
(~120 records) ordered by priority: drug x heat records first, smaller drug
classes first (SGLT2, epinephrine, topiramate, fentanyl, insulin, loop
diuretics, lithium, then the rest), storage-only records last.

Outputs:
  data/raw/literature/screen_prefilter.csv   record_id, prefilter_decision, prefilter_rule, drug_classes, group, priority
  data/raw/literature/screen_chunks/chunk_NNN.jsonl
  data/raw/literature/screen_prefilter_counts.json

Usage: ~/.local/bin/uv run --with pandas python -I scripts/lit_prefilter.py
"""
import json, os, re
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIT = os.path.join(ROOT, "data", "raw", "literature")
REC = os.path.join(ROOT, "data", "processed", "literature_records.csv")
CHUNK_DIR = os.path.join(LIT, "screen_chunks")
CHUNK = 120
ABS_MAX = 2500  # characters of abstract passed to the screener

DRUGS = {
    "sglt2": r"sglt-?2|sodium[- ]glucose co-?transporter|gliflozin",
    "epinephrine": r"epinephrine|adrenaline|epipen|auto-?injector",
    "topiramate_zonisamide": r"topiramate|zonisamide",
    "opioids_fentanyl": r"fentanyl|opioid|opiate|morphine|oxycodone|hydromorphone|methadone|buprenorphine|tramadol|transdermal",
    "insulin": r"insulin",
    "loop_diuretics": r"loop diuretic|furosemide|frusemide|bumetanide|torsemide|torasemide|ethacrynic",
    "lithium": r"lithium",
    "thiazides": r"thiazide|chlorthalidone|chlortalidone|indapamide|metolazone",
    "metformin": r"metformin|biguanide",
    "adhd_stimulants": r"amphetamine|methylphenidate|lisdexamfetamine|dexamfetamine|dextroamphetamine|adhd|psychostimulant|stimulant medication|atomoxetine",
    "ace_arb": r"\bace inhibitor|angiotensin|\bacei\b|\barbs?\b|pril\b|sartan\b|enalapril|lisinopril|ramipril|captopril|losartan|valsartan|candesartan|irbesartan|telmisartan|olmesartan|renin",
    "beta_blockers": r"beta[- ]?block|β[- ]?block|adrenergic beta|propranolol|metoprolol|atenolol|bisoprolol|carvedilol|nebivolol|labetalol|timolol|olol\b",
    "anticholinergics": r"anticholinergic|antimuscarinic|cholinergic antagonist|muscarinic antagonist|oxybutynin|benztropine|trihexyphenidyl|atropine|scopolamine|hyoscine|glycopyrr|tolterodine|solifenacin|tricyclic|amitriptyline|imipramine|nortriptyline|clomipramine|doxepin|diphenhydramine|antihistamine|promethazine|hydroxyzine|chlorpheniramine",
    "ssris": r"ssri|serotonin reuptake|fluoxetine|sertraline|paroxetine|citalopram|escitalopram|fluvoxamine|antidepressant",
    "antipsychotics": r"antipsychotic|neuroleptic|clozapine|olanzapine|quetiapine|risperidone|haloperidol|chlorpromazine|aripiprazole|ziprasidone|phenothiazine|thioridazine|fluphenazine|paliperidone|lurasidone",
}
STORAGE_OTHER = r"inhaler|metered[- ]dose|salbutamol|albuterol|nebuli[sz]|glucose (test )?strip|test strip|glucometer|glucose meter|blood glucose monitor|continuous glucose monitor"
PRIORITY = ["sglt2", "epinephrine", "topiramate_zonisamide", "opioids_fentanyl", "insulin",
            "loop_diuretics", "lithium", "thiazides", "metformin", "adhd_stimulants", "ace_arb",
            "beta_blockers", "anticholinergics", "ssris", "antipsychotics"]
QUERY2CLASS = {
    "drug_sglt2_inhibitors": "sglt2", "drug_epinephrine_auto_injectors": "epinephrine",
    "drug_topiramate_zonisamide": "topiramate_zonisamide", "drug_fentanyl_opioid_patches": "opioids_fentanyl",
    "drug_insulin_incl_pumps": "insulin", "drug_loop_diuretics": "loop_diuretics", "drug_lithium": "lithium",
    "drug_thiazides": "thiazides", "drug_metformin": "metformin", "drug_adhd_stimulants": "adhd_stimulants",
    "drug_ace_inhibitors_arbs": "ace_arb", "drug_beta_blockers": "beta_blockers",
    "drug_anticholinergics_oxybutynin": "anticholinergics", "drug_ssris": "ssris",
    "drug_antipsychotics_incl_clozapine": "antipsychotics",
}
HEAT = r"heat|hot\b|temperature|thermal|thermo|summer|hyperthermi|sweat|hidrosis|warm|climat|°c|degrees? c|\d ?º ?c|tropic|season|weather|excursion"
ENV_HEAT = r"heat ?wave|heat stroke|heatstroke|heat illness|heat-related|heat exhaustion|ambient|environmental|weather|summer|climat|hot (day|environment|season|climate)|exertion|exercis|outdoor|sauna|heat exposure|heat stress"
NMS_TITLE = r"neuroleptic malignant|serotonin syndrome|serotonin toxicity|malignant hyperthermia|\bnms\b"
MATERIALS = r"batter(y|ies)|cathode|anode|electrode|lithium[- ]ion|li-ion|niobate|tantalate|ceramic|alloy|crystal structure|crystalline|thin film|nanoparticle|nanostructur|superconduct|lattice|solid[- ]state electrolyte|ionic conductivity|electrochemi|sintering|glass(es)?\b|spectroscop|polymer electrolyte|molten salt|catalys|lithium (hydride|niobate|fluoride|borate|silicate|aluminate|titanate|carbonate powder)|doped|annealing|phase transition|x-ray diffraction|dielectric|luminescen|reactor|zeolite"
CLINICAL = r"patient|serum|plasma|bipolar|psychiatr|mania|depress|clinical|hospital|human|volunteer|toxicity|therapy|treatment|mood|renal|kidney|thyroid"
STAB_HINT = r"stabilit|potency|degrad|storage|stored|shelf"


def rx(p):
    return re.compile(p, re.I)


DRX = {k: rx(v) for k, v in DRUGS.items()}
SORX, HRX, ENVRX, NMSRX, MATRX, CLINRX, STABRX = map(rx, [STORAGE_OTHER, HEAT, ENV_HEAT, NMS_TITLE, MATERIALS, CLINICAL, STAB_HINT])


def s(x):
    return "" if pd.isna(x) else str(x)


def main():
    d = pd.read_csv(REC, dtype=str)
    rows, keep = [], []
    for _, r in d.iterrows():
        title, ab, mesh, fb = s(r.title), s(r.abstract), s(r.mesh), s(r.found_by)
        text = f"{title} {ab} {mesh}"
        qids = {q.split(":", 1)[1] for q in fb.split("; ") if ":" in q}
        q_classes = sorted({QUERY2CLASS[q] for q in qids if q in QUERY2CLASS})
        group = "drug_x_heat" if q_classes else "storage"
        t_classes = [k for k, v in DRX.items() if v.search(text)]
        storage_other = bool(SORX.search(text))
        classes = sorted(set(q_classes) & set(t_classes)) or t_classes
        mesh_terms = {m.split("/")[0].strip() for m in mesh.split(";")}
        rule = ""
        if s(r.has_abstract) != "yes" or len(ab) < 50:
            rule = "P1 no abstract"
        elif "Animals" in mesh_terms and "Humans" not in mesh_terms and not STABRX.search(title + " " + ab):
            rule = "P2 animal-only MeSH"
        elif MATRX.search(title + " " + ab) and not CLINRX.search(title + " " + ab) \
                and set(t_classes) <= {"lithium"} and not storage_other:
            rule = "P3 materials/chemistry"
        elif group == "storage" and not classes and not storage_other:
            rule = "P4 none of the 15 drugs (or inhaler/glucose strip) named"
        elif not HRX.search(text):
            rule = "P5 no heat/temperature term"
        elif NMSRX.search(title) and not ENVRX.search(title + " " + ab):
            rule = "P6 NMS/serotonin syndrome/MH, no environmental heat"
        cls_list = classes if classes else ["storage_other"]
        pri = min((PRIORITY.index(c) for c in cls_list if c in PRIORITY), default=len(PRIORITY))
        if group == "storage":
            pri += 100
        rows.append(dict(record_id=r.record_id, prefilter_decision="exclude" if rule else "screen",
                         prefilter_rule=rule, drug_classes="|".join(cls_list), query_classes="|".join(q_classes),
                         group=group, priority=pri))
        if not rule:
            keep.append(dict(record_id=r.record_id, year=s(r.year), title=title, journal=s(r.journal),
                             pub_types=s(r.publication_types), mesh=mesh[:400], abstract=ab[:ABS_MAX],
                             query_classes="|".join(q_classes) or "storage", text_drug_classes="|".join(cls_list),
                             _pri=pri))
    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(LIT, "screen_prefilter.csv"), index=False)
    keep.sort(key=lambda k: (k["_pri"], k["record_id"]))
    os.makedirs(CHUNK_DIR, exist_ok=True)
    for f in os.listdir(CHUNK_DIR):
        os.remove(os.path.join(CHUNK_DIR, f))
    n_chunks = 0
    for i in range(0, len(keep), CHUNK):
        n_chunks += 1
        with open(os.path.join(CHUNK_DIR, f"chunk_{n_chunks:03d}.jsonl"), "w") as fh:
            for k in keep[i:i + CHUNK]:
                k = {kk: vv for kk, vv in k.items() if kk != "_pri"}
                fh.write(json.dumps(k, ensure_ascii=False) + "\n")
    counts = {
        "records": len(out),
        "by_rule": out.prefilter_rule.replace("", "to LLM screening").value_counts().to_dict(),
        "by_group_decision": out.groupby(["group", "prefilter_decision"]).size().rename(lambda x: x).to_dict() and
        {f"{g}|{dcs}": int(n) for (g, dcs), n in out.groupby(["group", "prefilter_decision"]).size().items()},
        "to_screen": len(keep), "chunks": n_chunks, "chunk_size": CHUNK,
    }
    json.dump(counts, open(os.path.join(LIT, "screen_prefilter_counts.json"), "w"), indent=1)
    print(json.dumps(counts, indent=1))


if __name__ == "__main__":
    main()
