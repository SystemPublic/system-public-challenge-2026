"""Shared definitions for guidance coding (sources, drug list, text loading).
Used by guidance_pass1.py, guidance_pass2.py and guidance_kappa.py."""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT_DIR = os.path.join(ROOT, "data", "raw", "guidance", "text")
PROC = os.path.join(ROOT, "data", "processed")

# source_id -> list of (text file, short doc label)
SOURCES = {
    "CDC": [("cdc.txt", "CDC clinicians page")],
    "NYC": [("nyc_dohmh.txt", "NYC provider page"), ("nyc_han23_2026.txt", "NYC HAN 2026 #23")],
    "UKHSA": [("ukhsa.txt", "UKHSA healthcare professionals page")],
    "HC": [("health_canada.txt", "Health Canada 2011 technical guide")],
    "ANSM": [("ansm_map2017.txt", "ANSM mise au point 2017"), ("ansm_glyc.txt", "ANSM glycaemic Q&A 2017")],
    "WHO_EUR": [("who_2011_public_health_advice.txt", "WHO/Europe 2011 public health advice"),
                ("who_2026_hhap_2ed.txt", "WHO/Europe 2026 HHAP guidance 2nd ed")],
    "VIC": [("victoria_clinicians.txt", "Victoria DH clinicians page")],
    "GER_BMG": [("bmg_muster_apotheken.txt", "BMG Musterhitzeschutzplan Apotheken 2025"),
                ("bmg_muster_krankenhaeuser.txt", "BMG Musterhitzeschutzplan Krankenhaeuser 2024")],
    "GER_HEID": [("germany_heidelberg_hitzetabelle.txt", "Heidelberger Hitze-Tabelle (Stand 07.07.2026)")],
}

CORE = [
    "lithium", "loop_diuretics", "thiazides", "acei_arb", "sglt2", "insulin", "metformin",
    "anticholinergics_oxybutynin", "antipsychotics_clozapine", "ssri", "topiramate_zonisamide",
    "adhd_stimulants", "beta_blockers", "opioid_patches_fentanyl", "epinephrine_autoinjector",
]
OTHER = [
    "ccb", "nitrates", "nsaids", "acetaminophen", "tca", "antihistamines_1stgen", "antiparkinson",
    "benzodiazepines_anxiolytics", "carbamazepine_oxcarbazepine", "digoxin", "levothyroxine",
    "laxatives", "snri", "glp1_dpp4", "sulfonylureas", "cholinesterase_inhibitors",
    "photosensitizing_antimicrobials", "inhalers", "transdermal_other",
]
DRUG_LABEL = {
    "lithium": "Lithium", "loop_diuretics": "Loop diuretics", "thiazides": "Thiazides",
    "acei_arb": "ACE inhibitors / ARBs", "sglt2": "SGLT2 inhibitors", "insulin": "Insulin (incl. pumps)",
    "metformin": "Metformin", "anticholinergics_oxybutynin": "Anticholinergics (oxybutynin)",
    "antipsychotics_clozapine": "Antipsychotics (incl. clozapine)", "ssri": "SSRIs",
    "topiramate_zonisamide": "Topiramate / zonisamide", "adhd_stimulants": "ADHD stimulants",
    "beta_blockers": "Beta blockers", "opioid_patches_fentanyl": "Fentanyl / opioid patches",
    "epinephrine_autoinjector": "Epinephrine auto-injectors",
    "ccb": "Calcium channel blockers", "nitrates": "Nitrates / antianginals", "nsaids": "NSAIDs",
    "acetaminophen": "Acetaminophen / paracetamol", "tca": "Tricyclic antidepressants",
    "antihistamines_1stgen": "First-generation antihistamines", "antiparkinson": "Anti-Parkinson agents",
    "benzodiazepines_anxiolytics": "Benzodiazepines / anxiolytics / hypnotics",
    "carbamazepine_oxcarbazepine": "Carbamazepine / oxcarbazepine", "digoxin": "Digoxin",
    "levothyroxine": "Levothyroxine / thyroid hormone", "laxatives": "Laxatives", "snri": "SNRIs",
    "glp1_dpp4": "GLP-1 agonists / DPP-4 inhibitors", "sulfonylureas": "Sulfonylureas",
    "cholinesterase_inhibitors": "Cholinesterase inhibitors",
    "photosensitizing_antimicrobials": "Photosensitizing antimicrobials", "inhalers": "Inhalers",
    "transdermal_other": "Other transdermal patches (non-opioid)",
}

ACTIONS = ["monitor", "adjust_dose", "hold_or_substitute", "storage", "general_caution", "none"]
# Precedence used when several actions apply: the most concrete wins for the single "primary" field.
ACTION_RANK = {"hold_or_substitute": 5, "adjust_dose": 4, "monitor": 3, "storage": 2, "general_caution": 1, "none": 0}


def load_lines(fname):
    with open(os.path.join(TEXT_DIR, fname), encoding="utf-8") as f:
        return f.read().splitlines()


def norm(s):
    return re.sub(r"\s+", " ", s).strip()


def page_of(lines, idx):
    for j in range(idx, -1, -1):
        m = re.match(r"=== \[page (\d+)\] ===", lines[j])
        if m:
            return int(m.group(1))
    return None
