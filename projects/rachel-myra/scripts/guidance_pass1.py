"""PASS 1 (automated keyword-then-classify coder).

Approach: for every source text, find lines that contain a drug term (EN/FR/DE regex
dictionary). The coded quote is the matched line verbatim. Action type, specificity
and evidence are assigned by fixed keyword rules applied ONLY to a small window
(matched line + next 2 lines). No human/LLM judgement is used in this pass.

Run: python3 -I scripts/guidance_pass1.py
Output: data/processed/guidance_coding_pass1.csv
"""
import csv
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from guidance_common import (SOURCES, CORE, OTHER, DRUG_LABEL, ACTION_RANK, PROC,
                             load_lines, norm, page_of)

I = re.IGNORECASE
# specific terms = the drug or its own class named; umbrella = a broader parent class only
TERMS = {
    "lithium": (r"\blithium\b", None),
    "loop_diuretics": (r"loop diuretic|furosemide|frusemide|bumetanide|diur[ée]tiques de l.anse|\bLasix\b",
                       r"\bdiuretic|diur[ée]tique|\bDiuretika"),
    "thiazides": (r"thiazid|hydrochlorothiazide", r"\bdiuretic|diur[ée]tique|\bDiuretika"),
    "acei_arb": (r"\bACE\b|ACEi|angiotensin|enalapril|lisinopril|ramipril|perindopril|valsartan|losartan|\bIEC\b|ARA ?II|ACE-Hemmer|AT1-Rezeptor|sartans?\b",
                 r"antihypertens|anti-hypertens|Antihypertenseurs"),
    "sglt2": (r"SGLT|gliflozin", r"antidiab|hypoglyc[ée]miant|Antidiabetika"),
    "insulin": (r"insulin|insuline", r"\bdiabet"),
    "metformin": (r"metformin|biguanide", r"hypoglyc[ée]miants oraux|antidiab"),
    "anticholinergics_oxybutynin": (r"oxybutynin|anti-?cholinerg|atropiniques|Anticholinerg|urinary incontinence drugs|antispasmodiques",
                                    None),
    "antipsychotics_clozapine": (r"antipsychoti|neurolepti|clozapin|olanzapin|quetiapin|haloperidol|risperidon|Antipsychotika|phenothiazin",
                                 r"psychotrop"),
    "ssri": (r"\bSSRI|serotonin reuptake|recapture de la s[ée]rotonine|\bIRS\b|fluoxetine|sertraline|Prozac|Zoloft",
             r"antidepress|antid[ée]presseur|seroton|s[ée]rotoninergique|psychotrop"),
    "topiramate_zonisamide": (r"topiramat|zonisamid", r"antiepilep|anti-?[ée]pileptique|antiseizure|anticonvuls|Antiepileptika"),
    "adhd_stimulants": (r"methylphenidat|amphetamin|amph[ée]taminique|\bADHD\b|Sympathomimetika, zentral",
                        r"\bstimulant"),
    "beta_blockers": (r"beta.?block|β-?block|b[êe]ta-bloquant|Betablocker|atenolol|metoprolol|propranolol",
                      r"antihypertens|anti-hypertens|Antihypertenseurs"),
    "opioid_patches_fentanyl": (r"fentanyl|transderm|Pflaster|\bpatch", r"\bopiat|\bopioid|opiac|Opioide"),
    "epinephrine_autoinjector": (r"epipen|epinephrine|adrenalin|auto-?inject", r"adrenergic drugs"),
    # other classes (specific only)
    "ccb": (r"calcium channel|calcium blocker|antagonistes calciques|amlodipin|felodipin|nifedipin|Calciumkanal", None),
    "nitrates": (r"nitrate|antiangin|anti-angoreux|glyceryl trinitrate|isosorbide", None),
    "nsaids": (r"NSAID|non-steroidal anti|AINS|anti-inflammatoires non st|COX-2|ibuprofen", None),
    "acetaminophen": (r"acetaminophen|paracetamol|parac[ée]tamol|antipyretic", None),
    "tca": (r"tricyclic|\bTCAs?\b|imipraminiques|Trizyklika|amitriptylin|clomipramin", None),
    "antihistamines_1stgen": (r"antihistamin|H1|diphenhydramin|promethazin|doxylamin", None),
    "antiparkinson": (r"parkinson|benztropin|trihex|Antiparkinsonika", None),
    "benzodiazepines_anxiolytics": (r"benzodiazepin|anxiolytic|hypnotic|Benzodiazepine", None),
    "carbamazepine_oxcarbazepine": (r"carbamazepin|oxcarbazepin", None),
    "digoxin": (r"digoxin", None),
    "levothyroxine": (r"levothyrox|thyroxin|thyroid|thyro[ïi]d|Levothyroxin", None),
    "laxatives": (r"laxati|Laxanzien", None),
    "snri": (r"\bSNRI|norepinephrine reuptake|IRSNA|venlafaxin|duloxetin|duloxatine", None),
    "glp1_dpp4": (r"GLP-1|gliptin|liraglutid|DPP-4", None),
    "sulfonylureas": (r"sulfonylur|sulfamides hypoglyc", None),
    "cholinesterase_inhibitors": (r"cholinesterase", None),
    "photosensitizing_antimicrobials": (r"sun sensitivity|photosensit|voriconazole|griseofulvin|tetracycline|fluoroquinolone", None),
    "inhalers": (r"inhaler", None),
    "transdermal_other": (r"transderm|Pflaster", None),
}

ACT = [
    ("storage", r"refrigerat|stor(e|age|ed)|fridge|\bcool box|conserv|Lagerung|aufbewahr|below 25|temperature"),
    ("hold_or_substitute", r"\bavoid|\bvermeiden|Wechsel|switch|substitut|[ée]viter|supprimer|do not give|stop"),
    ("adjust_dose", r"\bdose|dosage|Dosis|posolog|adjust"),
    ("monitor", r"monitor|check|watch|Kontrolle|Monitoring|surveill|[Üü]berwachung|contr[ôo]ler|blood sugar|Spiegel"),
    ("general_caution", r"caution|careful|risk|vigilan|Vorsicht|prudence|attention|consider|review"),
]
BIBLIO = r"\(\d{4}\)\.|\d{4};\s?\d+|doi\.org|https?://|\d{4}, \d+, \d+-\d+"
EVID = r"Reference \d|\bOR \d|CI ?95|\d+(\.\d+)? ?%|\(\d{4}\)|\d{2}, \d{2}|et al"


def code_window(text):
    acts = [a for a, rx in ACT if re.search(rx, text, I)]
    return acts


def main():
    rows = []
    for sid, files in SOURCES.items():
        docs = [(lab, load_lines(fn)) for fn, lab in files]
        for drug in CORE + OTHER:
            spec_rx, umb_rx = TERMS[drug]
            hits_spec, hits_umb = [], []
            for lab, lines in docs:
                for i, ln in enumerate(lines):
                    if re.search(BIBLIO, ln):
                        continue  # skip bibliography / reference-list lines
                    if re.search(spec_rx, ln, I):
                        hits_spec.append((lab, lines, i))
                    elif umb_rx and re.search(umb_rx, ln, I):
                        hits_umb.append((lab, lines, i))
            hits = hits_spec or hits_umb
            level = "specific" if hits_spec else ("umbrella" if hits_umb else "none")
            if not hits:
                rows.append(dict(source_id=sid, drug_id=drug, drug_label=DRUG_LABEL[drug],
                                 drug_group="core" if drug in CORE else "other",
                                 mentioned="no", mention_level="none", action_type="none",
                                 all_actions="", specificity="none", evidence_cited="no",
                                 quote="", location="", n_hits=0))
                continue
            # choose best hit: the one with the highest-ranked action in its window
            best = None
            all_acts = set()
            evid = False
            for lab, lines, i in hits:
                own = lines[i]
                window = " ".join(lines[i:i + 3])
                acts = code_window(window)
                all_acts.update(acts)
                if re.search(EVID, window):
                    evid = True
                score = max([ACTION_RANK[a] for a in acts] or [0])
                own_specific = bool(code_window(own)) and level == "specific"
                key = (own_specific, score)
                if best is None or key > best[0]:
                    best = (key, lab, lines, i, acts)
            key, lab, lines, i, acts = best
            primary = max(acts, key=lambda a: ACTION_RANK[a]) if acts else "general_caution"
            specificity = "specific" if key[0] and primary != "general_caution" else "generic"
            pg = page_of(lines, i)
            loc = f"{lab}, PDF p. {pg}" if pg else f"{lab}, line {i + 1}"
            rows.append(dict(source_id=sid, drug_id=drug, drug_label=DRUG_LABEL[drug],
                             drug_group="core" if drug in CORE else "other",
                             mentioned="yes" if level == "specific" else "no",
                             mention_level=level, action_type=primary if level == "specific" else "none",
                             all_actions=";".join(sorted(all_acts)),
                             specificity=specificity if level == "specific" else "none",
                             evidence_cited="yes" if (evid and level == "specific") else "no",
                             quote=norm(lines[i]), location=loc, n_hits=len(hits)))
    os.makedirs(PROC, exist_ok=True)
    out = os.path.join(PROC, "guidance_coding_pass1.csv")
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) + ["coder"])
        w.writeheader()
        for r in rows:
            r["coder"] = "pass1_keyword_rules"
            w.writerow(r)
    print("wrote", out, len(rows))


if __name__ == "__main__":
    main()
