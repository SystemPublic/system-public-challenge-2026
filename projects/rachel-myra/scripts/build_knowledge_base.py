#!/usr/bin/env python3
"""Build the Missing Label knowledge base (v0).

    ~/.local/bin/uv run python scripts/build_knowledge_base.py            # full build
    ~/.local/bin/uv run python scripts/build_knowledge_base.py --offline  # no RxNav calls (cache only)

Outputs (all in data/kb/):
    knowledge_base.json       one record per drug/class (schema: schemas/knowledge_base.schema.json)
    mock_knowledge_base.json  the same records for lithium, loop diuretics, oxybutynin (UI work)
    kb_build_report.md        inputs present, counts, scoring formula and weights, what's missing
    rxnorm_cache.json         RxNav ingredient lookups (reruns make no network calls)

Rerunnable and deterministic: no timestamps; build_id is a hash of the inputs present.
Later inputs from other agents are merged automatically when they appear:
    data/processed/system_api_verification.csv, system_api_*.csv   (System API pull + badges)
    data/processed/faers_heat_signals_v2.csv, fda_label_heat_audit*_v2.csv
    data/processed/literature_screen*.csv                          (LLM screening/extraction)
They are read with tolerant column detection; anything they add is re-verified here
(abstract grounding) before it can become public.

Rules enforced by the build (it fails loudly if broken):
    - no dose instructions or dose numbers in any public text
    - claims badged "?" are never public and never used in labels or patient messages
    - graph pathways and FAERS are kept in their own layers, never in the literature score
Standard library only (plus urllib for RxNav). Curated clinical content lives in DRUGS below;
every number shown publicly comes from an input file listed in kb_build_report.md.
"""
from __future__ import annotations

import csv
import glob
import hashlib
import json
import math
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)  # noqa: E731
OUT = P("data", "kb")
SCHEMA_VERSION = "0.1.0"
OFFLINE = "--offline" in sys.argv
# Auto-extracted (LLM, unreviewed) literature rows are opt-in: they shift meters a lot and storage/lab
# studies can inflate patient-risk ratings. With the flag, output goes to *_with_screened_lit.* files.
MERGE_LIT = "--merge-literature" in sys.argv

DISCLAIMER = (
    "Prototype. Considerations for clinicians, not instructions. Not a replacement for clinical "
    "guidance. No dose advice. Patients: do not stop or change any medicine on your own; talk to "
    "your doctor or pharmacist."
)
ES_STATUS = "machine-translated, needs review"
TALK_EN = "Talk to your doctor or pharmacist."
TALK_ES = "Hable con su médico o farmacéutico."

# ----------------------------------------------------------------------------- inputs
INPUTS = {
    "master_list": "data/Drug heat risk master list.csv",
    "citation_verification": "data/processed/citation_verification.csv",
    "abstracts": "data/raw/literature/abstracts.jsonl",
    "guidance_matrix": "data/processed/guidance_matrix.csv",
    "guidance_sources": "data/processed/guidance_sources.csv",
    "faers": "data/processed/faers_heat_signals.csv",
    "faers_v2": "data/processed/faers_heat_signals_v2.csv",
    "label_summary": "data/processed/fda_label_heat_audit_summary.csv",
    "label_summary_v2": "data/processed/fda_label_heat_audit_summary_v2.csv",
    "label_audit_v2": "data/processed/fda_label_heat_audit_v2.csv",
    "system_pathways": "data/processed/system_pathways.csv",
    "system_pathway_summary": "data/processed/system_pathway_drug_summary.csv",
    "system_direct": "data/processed/system_drug_heat_direct_findings.csv",
    "system_untested": "data/processed/system_untested_links.csv",
    "system_master_findings": "data/processed/system_master_list_study_findings.csv",
    "system_api_verification": "data/processed/system_api_verification.csv",
    "storage_profiles": "data/processed/drug_storage_profiles.json",
    "acb": "data/kb/anticholinergic_burden.csv",
    "rxnorm_seed": "data/processed/synthetic/rxnorm_cache.json",
}
GLOB_INPUTS = {
    "system_api_extra": "data/processed/system_api_*.csv",
    # Extraction rows (one per included study finding); literature_screen.csv holds only decisions.
    "literature_screen": "data/processed/literature_extraction*.csv",
}

# literature_extraction.csv uses its own class names; map them to KB drug ids.
LIT_CLASS_TO_KB = {
    "lithium": "lithium", "loop_diuretics": "loop_diuretics", "anticholinergics": "anticholinergics_oxybutynin",
    "thiazides": "thiazides", "ace_arb": "acei_arb", "sglt2": "sglt2", "insulin": "insulin",
    "metformin": "metformin", "antipsychotics": "antipsychotics_clozapine", "ssris": "ssri",
    "topiramate_zonisamide": "topiramate_zonisamide", "adhd_stimulants": "adhd_stimulants",
    "beta_blockers": "beta_blockers", "opioids_fentanyl": "opioid_patches_fentanyl",
    "epinephrine": "epinephrine_autoinjector",
}
LIT_DIRECTION = {"harm": "supports_harm", "null": "null", "mixed": "conflicting", "protective": "protective"}


def exists(key):
    return os.path.exists(P(INPUTS[key]))


def read_csv(key_or_path):
    path = P(INPUTS[key_or_path]) if key_or_path in INPUTS else key_or_path
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def sha1_file(path):
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fnum(x):
    try:
        if x is None or str(x).strip() == "":
            return None
        return float(x)
    except ValueError:
        return None


# ----------------------------------------------------------------------------- evidence model
TIER_LABELS = {
    1: "RCT / meta-analysis",
    2: "Population study",
    3: "Small clinical / PK study",
    4: "Case series",
    5: "Case report",
    6: "Lab / bench / field test",
    7: "Label or guidance only",
    8: "Mechanism only / no study found",
}
DESIGN_W = {1: 1.0, 2: 0.8, 3: 0.6, 4: 0.45, 5: 0.3, 6: 0.25, 7: 0.15, 8: 0.05}
POP_MATCH = {
    "patients_in_heat": 1.0,  # people taking the drug, real heat exposure, clinical outcome
    "subgroup_in_heat": 0.85,  # real heat but narrow/other population (e.g. single case, veterans)
    "lab_heat_healthy": 0.6,  # controlled heat stress in healthy volunteers
    "indirect": 0.5,  # dehydration/AKI without heat, or heat without the drug's users
    "mechanism": 0.3,
}
STUDIES_SATURATE = 5
METER_T = {"strong": 0.45, "some": 0.2}
FLAG_T = {"high": 0.6, "moderate": 0.3}
CHANGE_T = {"high": 0.45, "moderate": 0.2}
FAERS_NEG_CUTOFF_DEFAULT = 1.734
SPECIFIC_COMPOSITE = "HEAT COMPOSITE SPECIFIC"

FORMULA = (
    "literature_score = design_weight x study_factor x consistency x population_match, where "
    "design_weight and population_match come from the public literature HARM claim with the highest "
    "design_weight x population_match (all claims if none shows harm, so a strong null study never "
    "inflates the harm meter); study_factor = min(1, log2(1+n)/log2(1+5)) with n = distinct "
    "public literature sources; consistency = share of directional public literature claims in the "
    "majority direction (harm vs null), 0.5 if none. Meter: Strong >= 0.45, Some >= 0.2, else Early "
    "signs. Only layer=literature claims with badge != '?' count. System graph pathways and FAERS "
    "are reported in their own fields and are never multiplied in."
)
FLAG_RULE = (
    "FLAG ('Check on this person') = association strength, causal or not: max over public "
    "literature harm claims of design_weight x population_match x severity (1.0 High, 0.75 "
    "Moderate) + 0.15 if FAERS specific-composite signal clears the negative-control band + 0.10 "
    "if any FDA label carries a heat warning + 0.10 if >= 6 of 8 jurisdictions mention it. "
    "High >= 0.6, Moderate >= 0.3. CHANGE ('Rethink the medicine') = literature_score x "
    "causal_factor + 0.10 if a cited lower-heat-risk alternative exists. causal_factor = 1.0 when "
    "the drug's own mechanism is shown in humans, 0.5 when within-person or adjusted studies show "
    "no added drug effect (confounding by indication), 0.75 otherwise; for storage/absorption "
    "drugs CHANGE concerns handling, not the molecule. High >= 0.45, Moderate >= 0.2; CHANGE is capped "
    "at Moderate when causal_factor <= 0.5. "
    "Strong within-person studies showing no added drug effect -> high FLAG, lower CHANGE (spec §9)."
)


def level(score, t):
    return "high" if score >= t["high"] else "moderate" if score >= t["moderate"] else "low"


def plain_ratio(v):
    """'OR 2.43' -> 'About 2½ times the odds' style text (spec §3.4)."""
    if v is None:
        return ""
    if v < 1.0:
        return "lower than without the medicine in this study"
    if v < 1.1:
        return "about the same as without the medicine"
    if v < 1.5:
        return f"about {round((v - 1) * 100)}% higher"
    halves = round(v * 2) / 2
    whole = int(halves)
    frac = "½" if halves - whole else ""
    return f"about {whole}{frac} times as high"


# ----------------------------------------------------------------------------- loaders
def load_abstracts():
    idx = {}
    if exists("abstracts"):
        with open(P(INPUTS["abstracts"]), encoding="utf-8") as f:
            for line in f:
                try:
                    d = json.loads(line)
                except json.JSONDecodeError:
                    continue
                text = (d.get("title") or "") + " " + (d.get("abstract") or "")
                for k in ("pmid", "doi", "pmcid"):
                    v = (d.get(k) or "").strip().lower()
                    if v:
                        idx[v] = {"text": text, "title": d.get("title") or "", "has_abstract": bool(d.get("abstract"))}
    return idx


def load_citation_verification():
    by_id = defaultdict(list)
    for r in read_csv("citation_verification"):
        for k in ("id_value", "pmid", "doi", "pmcid"):
            v = (r.get(k) or "").strip().lower()
            if v:
                by_id[v].append(r)
    return by_id


def norm_num_variants(v):
    s = f"{v}"
    out = {s}
    if s.endswith(".0"):
        out.add(s[:-2])
    out.add(s.replace(".", "·"))  # some abstracts use a middle dot (e.g. 2·79)
    return out


def number_in_text(v, text):
    if v is None:
        return True
    for s in norm_num_variants(v):
        if re.search(r"(?<![\d.])" + re.escape(s) + r"(?![\d])", text):
            return True
    return False


# ----------------------------------------------------------------------------- RxNorm
def rxnorm_lookup(names):
    cache_path = os.path.join(OUT, "rxnorm_cache.json")
    cache = {}
    if os.path.exists(cache_path):
        cache = json.load(open(cache_path))
    seed = {}
    if exists("rxnorm_seed"):
        seed = json.load(open(P(INPUTS["rxnorm_seed"]))).get("drugs", {})
    calls = 0
    for n in sorted(set(names)):
        if n in cache:
            continue
        if OFFLINE:
            s = seed.get(n)
            cache[n] = (
                {"rxcui": s["rxcui"], "rxnorm_name": s["rxnorm_name"], "tty": s["tty"], "via": "synthetic rxnorm_cache seed"}
                if s
                else {"rxcui": None, "rxnorm_name": None, "tty": None, "via": "offline, not looked up"}
            )
            continue
        try:
            url = "https://rxnav.nlm.nih.gov/REST/rxcui.json?" + urllib.parse.urlencode({"name": n, "search": 0})
            d = json.load(urllib.request.urlopen(url, timeout=20))
            ids = (d.get("idGroup") or {}).get("rxnormId") or []
            calls += 1
            rec = {"rxcui": None, "rxnorm_name": None, "tty": None, "via": url}
            if ids:
                pu = f"https://rxnav.nlm.nih.gov/REST/rxcui/{ids[0]}/properties.json"
                pr = json.load(urllib.request.urlopen(pu, timeout=20)).get("properties") or {}
                calls += 1
                rec.update(rxcui=ids[0], rxnorm_name=pr.get("name"), tty=pr.get("tty"))
            cache[n] = rec
            time.sleep(0.06)
        except Exception as e:  # network failure: fall back to seed, record why
            s = seed.get(n)
            cache[n] = (
                {"rxcui": s["rxcui"], "rxnorm_name": s["rxnorm_name"], "tty": s["tty"], "via": f"seed (RxNav failed: {e.__class__.__name__})"}
                if s
                else {"rxcui": None, "rxnorm_name": None, "tty": None, "via": f"RxNav failed: {e.__class__.__name__}"}
            )
    with open(cache_path, "w") as f:
        json.dump(dict(sorted(cache.items())), f, indent=1, ensure_ascii=False)
        f.write("\n")
    return cache, calls


# ----------------------------------------------------------------------------- curated content
# Claim spec keys: id (PMID:/DOI:/GUIDANCE:/LABEL:), label, text, plain, num (value), ntype,
# ci (lo, hi), tier, direction, pop (POP_MATCH key), population, layer (default literature).
# Numbers are re-checked against the abstract text (abstracts.jsonl / citation_verification.csv).

C = dict  # shorthand

MARTIN_LATRY = "PMID:17513091"
LAYTON = "DOI:10.1371/journal.pone.0243665"
HOSPERS = "PMID:39513185"
KALISCH = "DOI:10.1111/jcpt.12418"
MANGONI = "PMID:29116624"
WONG = "PMID:39648665"  # Wong et al., Psychol Med 2024 (PMC11769904)
CHEN = "PMID:41044101"
HARLEY = "DOI:10.1002/pds.70447"
VANAKOSKI = "PMID:9571303"

DRUGS = [
    # ------------------------------------------------------------------ lithium
    C(
        id="lithium",
        display="Lithium",
        plain="Lithium",
        class_label="Mood stabilizer",
        examples=["lithium carbonate", "lithium citrate"],
        ingredients=["lithium", "lithium carbonate"],
        master_rows=["R32"],
        faers_class="lithium",
        label_class="lithium",
        system_group="lithium",
        storage_profile=None,
        severity="High",
        buckets=[("monitor", True, "Dehydration can push lithium into the toxic range; levels and symptoms are what to watch (Heidelberg table: level check)."),
                 ("adjust_dose", False, "Any change is a prescriber decision after a level check; the knowledge base never gives dose numbers.")],
        mechanism_groups=["kidney_cleared_buildup", "fluid_salt_loss"],
        heat_stack=C(
            sweating=("no", "Lithium does not block sweating; heavy sweating loses water and salt."),
            water_salt=("yes", "Lithium can cause the body to lose extra water (diabetes-insipidus-like); salt and water loss raises levels."),
            kidney_clearance=("yes", "Kidneys clear lithium; dehydration lowers clearance so it builds up."),
            blood_pressure=("no", "No direct blood-pressure effect at usual use."),
            other=[("awareness", "Early toxicity (confusion, unsteadiness) can look like heat illness.")],
        ),
        compass=C(arrow="up", meaning="Acts stronger in heat: dehydration concentrates lithium.",
                  mechanism="Water and salt loss -> less kidney clearance -> lithium builds up toward the toxic range (narrow margin).",
                  triggers=["forecast heat", "heavy sweating or exertion", "vomiting/diarrhea or fever", "starting a water pill, ACE inhibitor/ARB or NSAID"],
                  monitor=["lithium level (prescriber decides timing)", "kidney function and sodium", "tremor, unsteadiness, confusion, vomiting"]),
        prescribers=["psychiatry", "primary care"],
        higher_risk=["older adults", "kidney disease", "people also taking diuretics, ACE inhibitors/ARBs or NSAIDs"],
        pediatric=None,
        causal_factor=1.0,
        causal_note="Mechanism (renal clearance falls with dehydration) is direct; heat-specific human data are case reports and one guidance-cited series.",
        claims=[
            C(id="PMID:747906", label="Severe neurotoxicity and lithium therapy, Clin Toxicol 1978",
              text="Case report: lithium neurotoxicity in a long-term user, which the author attributes to hot weather with excessive sweating and reduced water and salt intake.",
              plain="One patient became seriously ill from lithium after hot weather and heavy sweating.",
              tier=5, direction="supports_harm", pop="subgroup_in_heat", population="single adult on long-term lithium"),
            C(id="PMID:24615", label="Heat illness syndrome and lithium intoxication, J Clin Psychiatry 1978",
              text="Review: heat illness and lithium intoxication share symptoms, predisposing factors and physiology.",
              plain="Lithium poisoning and heat illness look alike and share causes.",
              tier=8, direction="plausible_untested", pop="mechanism", population="narrative review"),
            C(id="GUIDANCE:HC", label="Health Canada, Extreme Heat Events Guidelines (2011)", layer="guidance", guidance_drug="lithium",
              text="Health Canada cites a retrospective study in which 11.5% of lithium poisonings requiring hospitalization were due to summer heat exposure and dehydration, and advises hydrating with water rather than electrolyte solutions.",
              plain="In one study cited by Health Canada, about 1 in 9 lithium poisonings needing hospital care came from summer heat and dehydration.",
              num=11.5, ntype="%", tier=7, direction="supports_harm", pop="patients_in_heat", population="hospitalized lithium poisonings (study cited by Health Canada)"),
        ],
        alternatives=[],
        timeline=[
            ("before_summer", "Review the medication list for lithium plus diuretic, ACE inhibitor/ARB or NSAID; agree a heat-day plan and who checks levels.", ["prescriber", "pharmacist"], "early_signs", "mechanism; Heidelberg table (level check); NYC/CDC narrow-margin lists"),
            ("72h_before", "Remind the patient of early toxicity signs and the clinic number; check they have a cool place to go.", ["care_coordinator", "pharmacist"], "early_signs", "guidance only"),
            ("during", "Check in by phone; ask about vomiting, diarrhea, unsteadiness or confusion; a prescriber decides whether a level is needed.", ["care_coordinator", "prescriber"], "early_signs", "GER_HEID quote; case reports"),
            ("after", "Consider a lithium level and kidney/sodium check after a heat wave for flagged patients (clinician-approved).", ["prescriber"], "early_signs", "GER_HEID (Spiegelkontrolle); spec §4.4 item 9"),
        ],
        messages=[
            ("heat_forecast",
             "Heat warning for lithium: in hot weather your body can lose water, and lithium can build up to a harmful level. Watch for shaking hands, feeling unsteady, confusion, vomiting or diarrhea. Keep taking your medicine unless your doctor tells you otherwise, and stay somewhere cool. " + TALK_EN,
             "Aviso de calor por el litio: con el calor su cuerpo puede perder agua y el litio puede acumularse hasta un nivel dañino. Fíjese si tiene temblor en las manos, inestabilidad, confusión, vómitos o diarrea. Siga tomando su medicina a menos que su médico le diga otra cosa, y quédese en un lugar fresco. " + TALK_ES),
            ("after_heat",
             "The heat wave is over. Your care team may want to check your lithium level. " + TALK_EN,
             "La ola de calor terminó. Su equipo médico quizás quiera revisar su nivel de litio. " + TALK_ES),
        ],
        label_line="During a heat wave, think about lithium levels: dehydration can push them into the toxic range.",
        gaps=["No population heat-mortality or heat-admission estimate for lithium users was found.",
              "Dutch serum-level vs temperature data (Wilting) and the Arizona poison-center study have no confirmed PMID; kept internal (?)."],
        extra_unverified=[
            C(id="NOID:wilting", label="Wilting et al., Utrecht thesis chapter (PMID unconfirmed)",
              text="41,102 lithium levels from 3,054 patients differed by season and temperature category.",
              plain="Lithium levels varied with outdoor temperature.", num=41102, ntype="n", tier=2, direction="supports_harm", pop="patients_in_heat",
              population="Dutch lithium users", url="https://dspace.library.uu.nl/bitstream/handle/1874/27401/wilting_07_theimpactofenvironmentaltemperature.pdf?sequence=2"),
        ],
    ),
    # ------------------------------------------------------------------ loop diuretics
    C(
        id="loop_diuretics",
        display="Loop diuretics",
        plain="Water pills (loop diuretics)",
        class_label="Diuretic",
        examples=["furosemide", "bumetanide", "torsemide"],
        ingredients=["furosemide", "bumetanide", "torsemide"],
        master_rows=["R25", "R71"],
        faers_class="loop diuretics",
        label_class="loop diuretics",
        system_group="loop_diuretics",
        storage_profile=None,
        severity="High",
        buckets=[("adjust_dose", True, "Fluid loss in heat adds to the drug's effect; whether to change anything is a prescriber decision, balanced against fluid build-up in heart failure."),
                 ("monitor", False, "Weight, dizziness, kidney function and sodium during and after heat (ANSM: check fluid and salt intake).")],
        mechanism_groups=["fluid_salt_loss", "kidney_stress", "bp_drop", "low_sodium"],
        heat_stack=C(
            sweating=("no", "Does not block sweating; sweating adds to the water the drug removes."),
            water_salt=("yes", "Removes water and salt; heat sweating adds to the loss (volume depletion, low sodium)."),
            kidney_clearance=("yes", "Low blood volume strains the kidneys and slows clearance of other drugs (e.g. lithium)."),
            blood_pressure=("yes", "Less blood volume plus heat-widened blood vessels -> dizziness, fainting, falls."),
            other=[],
        ),
        compass=C(arrow="up", meaning="Acts stronger in heat: the water and salt loss adds to heat sweating.",
                  mechanism="Diuresis + sweat loss -> volume depletion -> low blood pressure and kidney strain.",
                  triggers=["forecast heat", "exertion", "vomiting/diarrhea", "low fluid intake"],
                  monitor=["daily weight", "dizziness on standing", "kidney function and sodium (clinician decides)", "swelling or breathlessness (fluid build-up if held)"]),
        prescribers=["cardiology", "primary care", "nephrology"],
        higher_risk=["heart failure", "dementia", "older adults", "chronic kidney disease"],
        pediatric=None,
        causal_factor=0.75,
        causal_note="Mechanism is direct, but loop-specific heat estimates are not abstract-verifiable and holding the drug carries its own risk in heart failure.",
        claims=[
            C(id=KALISCH, label="Kalisch Ellett et al., J Clin Pharm Ther 2016",
              text="Sequence symmetry analysis of 6,700 veterans: starting an ACE inhibitor plus diuretic combination product had the highest risk of admission for dehydration or heat-related illness (ratio 2.79).",
              plain="Starting an ACE inhibitor together with a water pill was linked to about 3 times the risk of a dehydration or heat-illness admission.",
              num=2.79, ntype="ratio", tier=2, direction="supports_harm", pop="subgroup_in_heat", population="Australian veterans"),
            C(id=LAYTON, label="Layton et al., PLoS One 2020",
              text="Medicare SCCS: loop diuretics raised heat-related hospitalization (RR 1.54-1.84).",
              plain="Loop diuretics were linked to more heat-related hospital stays.",
              num=1.54, ntype="RR", tier=2, direction="supports_harm", pop="patients_in_heat", population="US Medicare, age 65+"),
            C(id=HOSPERS, label="Hospers et al., eClinicalMedicine 2024 (meta-analysis)",
              text="Meta-analysis of heat-stress trials: diuretics did not alter core temperature responses (mostly healthy young men, short exposures).",
              plain="In short lab heat tests on healthy young people, water pills did not raise body temperature.",
              tier=1, direction="null", pop="lab_heat_healthy", population="healthy young adults, lab heat stress"),
            C(id=MANGONI, label="Mangoni et al. 2017 (triple whammy)",
              text="Diuretic + NSAID + ACEi/ARB ('triple whammy') did not predict in-hospital AKI during heat waves (OR 1.02, 95% CI 0.21-2.97).",
              plain="In one hospital study, the water pill + NSAID + ACE inhibitor combination did not predict kidney injury during heat waves.",
              num=1.02, ntype="OR", ci=(0.21, 2.97), tier=2, direction="null", pop="subgroup_in_heat", population="older medical inpatients, Australia"),
        ],
        alternatives=[],
        timeline=[
            ("before_summer", "Review indication and combinations (ACE inhibitor/ARB, NSAID, SGLT2 inhibitor, lithium); write a heat-day plan with weight and symptom thresholds set by the prescriber.", ["prescriber", "pharmacist"], "some", "Kalisch Ellett 2016; ANSM"),
            ("72h_before", "Remind about daily weights and dizziness; fluid advice only within the limits the clinician set (no blanket 'drink more' for heart failure).", ["care_coordinator"], "some", "ANSM; spec §4.4 item 10"),
            ("during", "Check in about dizziness, falls, low urine, confusion; prescriber decides any change.", ["care_coordinator", "prescriber"], "some", "guidance; mechanism"),
            ("after", "Kidney function and sodium check for flagged patients; watch for fluid build-up if anything was held.", ["prescriber"], "early_signs", "R71: holding risk in heart failure, no study"),
        ],
        messages=[
            ("heat_forecast",
             "Heat warning for your water pill: in hot weather it can leave you low on water and salt because you also lose fluid by sweating. Watch for dizziness when you stand, very little urine, confusion or a fall. Do not stop it on your own; follow the fluid plan your doctor gave you and stay somewhere cool. " + TALK_EN,
             "Aviso de calor por su pastilla para orinar (diurético): con el calor puede quedarse sin suficiente agua y sal porque también pierde líquido al sudar. Fíjese si se marea al pararse, orina muy poco, está confundido o se cae. No la deje por su cuenta; siga el plan de líquidos que le dio su médico y quédese en un lugar fresco. " + TALK_ES),
            ("after_heat",
             "The heat wave is over. Your care team may check your kidneys and salt levels. Tell them if your ankles are swelling or you are short of breath. " + TALK_EN,
             "La ola de calor terminó. Su equipo médico quizás revise sus riñones y su nivel de sal. Avíseles si se le hinchan los tobillos o le falta el aire. " + TALK_ES),
        ],
        label_line="During a heat wave, water pills add to the water and salt lost by sweating: watch for dizziness, falls and kidney strain.",
        gaps=["Loop-diuretic-specific heat estimates (Layton RR 1.54-1.84) are not in the abstract; kept internal until checked in full text.",
              "No study gives titration guidance for diuretics in heart failure during heat (holding can cause fluid build-up)."],
        extra_unverified=[],
    ),
    # ------------------------------------------------------------------ anticholinergics (oxybutynin)
    C(
        id="anticholinergics_oxybutynin",
        display="Anticholinergics (oxybutynin)",
        plain="Medicines that reduce sweating (e.g. oxybutynin for bladder)",
        class_label="Anticholinergic / bladder antimuscarinic",
        examples=["oxybutynin", "tolterodine", "solifenacin", "trospium", "benztropine", "trihexyphenidyl"],
        ingredients=["oxybutynin", "tolterodine", "solifenacin", "trospium", "benztropine", "trihexyphenidyl"],
        master_rows=["R01", "R02", "R24"],
        faers_class="anticholinergics",
        label_class="anticholinergics",
        system_group="anticholinergics",
        storage_profile=None,
        severity="High",
        buckets=[("hold_or_substitute", True, "Blocks sweating, the body's main cooling route; consider a less anticholinergic option at the spring review (Heidelberg table)."),
                 ("monitor", False, "Hot dry skin, confusion and rising temperature during heat.")],
        mechanism_groups=["sweat_blocked", "sedation_awareness"],
        heat_stack=C(
            sweating=("yes", "Blocks the nerve signal to sweat glands, so the body cannot cool by sweating."),
            water_salt=("no", "No direct effect."),
            kidney_clearance=("no", "No direct effect."),
            blood_pressure=("no", "No direct effect."),
            other=[("awareness", "Can cause confusion in older adults, which hides early heat illness.")],
        ),
        compass=C(arrow="up", meaning="Effect matters more in heat: blocked sweating means the body heats up faster.",
                  mechanism="Muscarinic blockade at sweat glands -> less sweating -> core temperature rises under heat stress.",
                  triggers=["forecast heat", "exertion", "fever", "adding another anticholinergic (stacking)"],
                  monitor=["hot, dry, flushed skin", "confusion", "body temperature", "total anticholinergic burden (ACB score)"]),
        prescribers=["urology", "primary care", "geriatrics", "neurology", "psychiatry"],
        higher_risk=["older adults", "Parkinson's disease", "polypharmacy / high anticholinergic burden"],
        pediatric=None,
        causal_factor=1.0,
        causal_note="Mechanism shown in humans: strong anticholinergics raise core temperature with reduced sweating in heat-stress trials.",
        claims=[
            C(id=MARTIN_LATRY, label="Martin-Latry et al., Eur Psychiatry 2007",
              text="2003 French heat wave case-control: people admitted with heat-related illness were more likely to be on anticholinergic drugs (OR 6.0, 95% CI 1.8-19.6).",
              plain="In the 2003 French heat wave, people hospitalized for heat illness had about 6 times the odds of taking these medicines.",
              num=6.0, ntype="OR", ci=(1.8, 19.6), tier=2, direction="supports_harm", pop="patients_in_heat", population="older adults (mean age 83), Bordeaux"),
            C(id=LAYTON, label="Layton et al., PLoS One 2020",
              text="Medicare self-controlled case series: anticholinergics raised heat-related hospitalization across the summer (RR 1.16).",
              plain="Older adults had about 16% more heat-related hospital stays while taking these medicines.",
              num=1.16, ntype="RR", tier=2, direction="supports_harm", pop="patients_in_heat", population="US Medicare, age 65+"),
            C(id=HOSPERS, label="Hospers et al., eClinicalMedicine 2024 (meta-analysis)",
              text="Meta-analysis of randomized heat-stress trials: drugs with high anticholinergic properties raised core temperature by 0.42 C at air temperatures of 30 C or more, with reduced sweating (evidence limited to atropine).",
              plain="In lab heat tests, strong sweat-blocking medicines raised body temperature.",
              num=0.42, ntype="degC", ci=(0.04, 0.79), tier=1, direction="supports_harm", pop="lab_heat_healthy", population="healthy young adults (atropine)"),
            C(id="PMID:8835047", label="Adubofour et al., Ann Pharmacother 1996",
              text="Case report: an older man on oxybutynin admitted with heat stroke on the hottest day of summer, after a similar admission the previous summer; the drug was stopped.",
              plain="An older man on oxybutynin had heat stroke two summers in a row.",
              tier=5, direction="supports_harm", pop="subgroup_in_heat", population="older adult"),
            C(id="PMID:34055543", label="Ahmad et al., Cureus 2021",
              text="Case report: oxybutynin-induced heat stroke in an older patient with Parkinson's disease.",
              plain="A person with Parkinson's disease had heat stroke while on oxybutynin.",
              tier=5, direction="supports_harm", pop="subgroup_in_heat", population="older adult with Parkinson's disease"),
            C(id=KALISCH, label="Kalisch Ellett et al., J Clin Pharm Ther 2016",
              text="Starting anticholinergic agents was associated with a higher risk of admission for dehydration or heat-related illness (sequence symmetry analysis, 6,700 veterans).",
              plain="Starting these medicines was linked to more dehydration or heat-illness admissions.",
              tier=2, direction="supports_harm", pop="subgroup_in_heat", population="Australian veterans"),
        ],
        alternatives=[
            C(name="A less anticholinergic bladder option (e.g. mirabegron, a beta-3 agonist)",
              why="Oxybutynin scores 3 (highest) on the Anticholinergic Cognitive Burden scale; mirabegron is not on the scale. The Heidelberg heat table advises considering a switch to a less anticholinergic agent.",
              lost="Different side-effect profile (e.g. blood pressure) and cost; efficacy differs by patient.",
              heat_studied=False,
              source_id="GUIDANCE:GER_HEID", source_label="Heidelberger Hitze-Tabelle (2026): 'Therapiewechsel auf weniger anticholinerge Vertreter erwägen'",
              source_url="https://dosing.de/Hitze/Medikamentenmanagement_bei_Hitzewellen.pdf"),
        ],
        timeline=[
            ("before_summer", "Count total anticholinergic burden (ACB); at the spring review consider a less anticholinergic option, especially for older adults and Parkinson's disease.", ["prescriber", "pharmacist"], "strong", "Martin-Latry 2007; Hospers 2024; Heidelberg table; ACB scale"),
            ("72h_before", "Tell the patient and caregiver the warning signs (hot dry skin, confusion) and line up a cool place to spend the day.", ["care_coordinator", "caregiver"], "some", "case reports; guidance"),
            ("during", "Check in; skin that is hot and dry with confusion is an emergency: cool the person and call 911.", ["care_coordinator", "caregiver", "patient"], "some", "case reports"),
            ("after", "Review any heat-illness episode and the bladder treatment plan.", ["prescriber"], "early_signs", "case reports (recurrence in consecutive summers)"),
        ],
        messages=[
            ("heat_forecast",
             "Heat warning for oxybutynin: in hot weather it can stop you from sweating, so your body heats up faster. Watch for hot, dry skin, feeling confused or very weak. Do not stop it on your own; stay somewhere cool and ask your doctor at your next visit whether another bladder medicine would suit you. " + TALK_EN,
             "Aviso de calor por la oxibutinina: con el calor puede impedir que usted sude, y su cuerpo se calienta más rápido. Fíjese si tiene la piel caliente y seca, confusión o mucha debilidad. No la deje por su cuenta; quédese en un lugar fresco y pregunte a su médico en su próxima cita si otra medicina para la vejiga le convendría. " + TALK_ES),
            ("heat_day",
             "Heat danger today. Your bladder medicine makes it harder to sweat. Go somewhere cool with other people around, early in the day. " + TALK_EN,
             "Peligro por calor hoy. Su medicina para la vejiga le hace más difícil sudar. Vaya temprano a un lugar fresco donde haya otras personas. " + TALK_ES),
        ],
        label_line="Blocks sweating: during a heat wave, watch for hot dry skin and confusion; consider a less anticholinergic option at the spring review.",
        gaps=["Trial evidence for core temperature is atropine in healthy young men; oxybutynin itself has only case reports in heat.",
              "No heat study of mirabegron or other non-anticholinergic bladder options (alternative is 'not studied in heat')."],
        extra_unverified=[],
    ),
]

# Additional drugs are appended from DRUGS_MORE (defined below) so the mock trio stays first.

# ----------------------------------------------------------------------------- build helpers
GUIDANCE_JURIS = {"CDC": "USA (CDC)", "NYC": "USA (NYC DOHMH)", "UKHSA": "England (UKHSA)", "HC": "Canada (Health Canada)",
                  "ANSM": "France (ANSM)", "WHO_EUR": "WHO Europe", "VIC": "Australia (Victoria)",
                  "GER_BMG": "Germany (federal BMG)", "GER_HEID": "Germany (Heidelberg table)"}
JURIS_OF = {k: ("Germany" if k.startswith("GER") else k) for k in GUIDANCE_JURIS}

DOSE_RE = re.compile(
    r"\b\d+(\.\d+)?\s*(mg|mcg|µg|microgram|milligram|units?|ml|mL|tablets?|pills?|puffs?)\b|"
    r"\b(double|halve|half) (the|your) dose\b|\bskip (a|your|the) dose\b|\bincrease (the|your) dose\b|\breduce (the|your) dose\b",
    re.I,
)


def check_no_dose(text, where):
    if DOSE_RE.search(text or ""):
        raise SystemExit(f"DOSE GUARD: dose-like text in {where}: {text!r}")


def source_url(sid):
    kind, _, val = sid.partition(":")
    if kind == "PMID":
        return f"https://pubmed.ncbi.nlm.nih.gov/{val}/"
    if kind == "DOI":
        return f"https://doi.org/{val}"
    if kind == "PMCID":
        return f"https://pmc.ncbi.nlm.nih.gov/articles/{val}/"
    return None


class Ctx:
    pass


def verify_claim(spec, ctx, drug_id):
    """Return (badge, badge_code, verification, citation_status, input_file)."""
    sid = spec["id"]
    kind, _, val = sid.partition(":")
    num = spec.get("num")
    if kind == "GUIDANCE":
        g = ctx.guidance.get((val, spec.get("guidance_drug", drug_id)))
        if g and (num is None or number_in_text(num, g["quote"])):
            return "✓", "verified", f"verbatim quote in {val} source text (guidance pass-2 verbatim check); number found in quote", "guidance quote", INPUTS["guidance_matrix"]
        return "?", "unverified", "quote or number not found in guidance_matrix.csv", "unverified", INPUTS["guidance_matrix"]
    if kind not in ("PMID", "DOI", "PMCID"):
        return "?", "unverified", "no PMID/DOI; not machine-checkable", "no citation id", INPUTS["master_list"]
    key = val.lower()
    cv_rows = ctx.cv.get(key, [])
    absrec = ctx.abstracts.get(key)
    if absrec is None:
        for r in cv_rows:
            for k in ("pmid", "doi", "pmcid"):
                a = ctx.abstracts.get((r.get(k) or "").lower())
                if a:
                    absrec = a
                    break
    exists_ok = bool(cv_rows) and any(r.get("exists") == "yes" for r in cv_rows) or absrec is not None
    cstatus = ";".join(sorted({r.get("verdict", "") for r in cv_rows if r.get("verdict")})) or ("abstract in literature corpus" if absrec else "not checked")
    infile = INPUTS["citation_verification"] if cv_rows else INPUTS["abstracts"]
    if not exists_ok:
        return "?", "unverified", "citation not found in citation_verification.csv or the abstract corpus", cstatus, infile
    text = absrec["text"] if absrec else ""
    nums = [num] + list(spec.get("ci") or [])
    nums = [n for n in nums if n is not None]
    if nums:
        if not text:
            found = all(any(number_in_text(n, (r.get("numbers_found") or "").replace("|", " ")) for r in cv_rows) for n in nums)
        else:
            found = all(number_in_text(n, text) for n in nums)
        if not found:
            return "?", "unverified", "citation exists but the number(s) were not found verbatim in the abstract", cstatus, infile
    elif absrec is not None and not absrec.get("has_abstract") and not cv_rows:
        return "?", "unverified", "no abstract available", cstatus, infile
    # System second extractor (✓✓ / ⚠)
    pmid = val if kind == "PMID" else next((r.get("pmid") for r in cv_rows if r.get("pmid")), "")
    sysrows = ctx.sys_findings.get(pmid, [])
    keys = {f"pmid:{pmid}".lower(), f"{kind}:{val}".lower()} | {f"doi:{r.get('doi','')}".lower() for r in cv_rows if r.get("doi")}
    for n_ in nums:
        for k in keys:
            hit = ctx.api_num.get((k, round(n_, 4)))
            if hit and hit["badge"].startswith("✓✓"):
                return "✓✓", "double_verified", f"number in abstract AND System extracted the same value ({hit['system_result']}; {hit['file']})", cstatus, hit["file"]
            if hit and "⚠" in hit["badge"]:
                if "mislabel" in hit["system_result"]:
                    # Our number is in the abstract; System's label for it is wrong. That's System's error, not
                    # ours: keep ✓ and record it for the graph-audit fix list.
                    return "✓", "verified", f"citation exists, number(s) found verbatim in abstract; {SYS_AUDIT_NOTE} ({hit['file']})", cstatus, infile
                return "⚠", "conflict", f"System check flags a conflict ({hit['system_result']}; {hit['file']})", cstatus, hit["file"]
    for k in keys:
        for a in ctx.api_verif.get(k, []):
            if "⚠" in a["badge"] and a.get("mislabel_only"):
                return "✓", "verified", ("citation exists, number(s) found verbatim in abstract; " if nums else "citation exists; ") + f"{SYS_AUDIT_NOTE} ({a['note']})", cstatus, infile
            if "⚠" in a["badge"]:
                return "⚠", "conflict", f"System verification flags a conflict or mislabel ({a['note']})", cstatus, "data/processed/" + a["note"]
    if num is not None and sysrows:
        vals = [fnum(r.get("statistic_value")) for r in sysrows]
        if any(v is not None and abs(v - num) < 0.006 for v in vals):
            return "✓✓", "double_verified", "number in abstract AND System (Dataverse v2.1) extracted the same value for this paper", cstatus, INPUTS["system_master_findings"]
    return "✓", "verified", ("citation exists, number(s) found verbatim in abstract" if nums else "citation exists, title matched; no number claimed"), cstatus, infile


def paper_aliases(sid, ctx):
    """All ids (lowercase, prefixed) that refer to the same paper, via citation_verification.csv."""
    kind, _, val = sid.partition(":")
    out = {sid.lower()}
    for r in ctx.cv.get(val.lower(), []):
        for k, pfx in (("pmid", "pmid:"), ("doi", "doi:"), ("pmcid", "pmcid:")):
            if r.get(k):
                out.add(pfx + r[k].lower())
    return out


def paper_key(sid, ctx):
    al = paper_aliases(sid, ctx)
    pm = sorted(a for a in al if a.startswith("pmid:"))
    return pm[0] if pm else sorted(al)[0]


def make_claim(spec, idx, ctx, drug_id):
    badge, code, how, cstatus, infile = verify_claim(spec, ctx, drug_id)
    tier = spec.get("tier")
    num = spec.get("num")
    number = None
    if num is not None:
        ntype = spec.get("ntype", "")
        ci = spec.get("ci") or (None, None)
        special = {"%": f"{num:g}%", "n": f"n = {num:,.0f}", "degC": f"+{num:g} °C", "degC_rise": f"+{num:g} °C",
                   "degC_storage": f"{num:g} °C storage", "age": f"age {num:g}", "% of control sweat": f"{num:g}% of normal sweat",
                   "patient-years per case": f"1 per {num:,.0f} patient-years", "% of labeled amount": f"{num:g}% of labeled amount"}
        disp = special.get(ntype, f"{ntype} {num:g}".strip())
        if ci[0] is not None:
            disp += f" (95% CI {ci[0]:g}–{ci[1]:g})"
        pl = ""
        if ntype in ("OR", "RR", "ratio", "IRR", "ROR"):
            pl = plain_ratio(num).capitalize()
        elif ntype == "degC":
            pl = f"Body temperature about {num:g} °C higher"
        number = {"value": num, "type": ntype, "ci_low": ci[0], "ci_high": ci[1], "display": disp, "plain": pl}
    sid = spec["id"]
    c = {
        "id": f"{drug_id}.c{idx}",
        "text": spec["text"],
        "plain": spec["plain"],
        "number": number,
        "source": {"id": sid, "label": spec["label"], "url": spec.get("url") or source_url(sid)},
        "paper_key": paper_key(sid, ctx),
        "layer": spec.get("layer", "literature"),
        "tier": {"code": tier, "label": TIER_LABELS[tier]} if tier else None,
        "direction": spec["direction"],
        "population": spec.get("population", ""),
        "population_match": spec.get("pop", "indirect"),
        "badge": badge,
        "badge_code": code,
        "verification": how,
        "citation_status": cstatus,
        "public": badge != "?",
        "input_file": infile,
    }
    if c["public"]:
        check_no_dose(c["text"] + " " + c["plain"], c["id"])
    return c


def score_evidence(claims, d):
    lit = [c for c in claims if c["layer"] == "literature" and c["public"] and c["tier"]]
    harm_lit = [c for c in lit if c["direction"] == "supports_harm"]
    best = max(harm_lit or lit, key=lambda c: DESIGN_W[c["tier"]["code"]] * POP_MATCH[c["population_match"]], default=None)
    if best:
        dw, pm, tier = DESIGN_W[best["tier"]["code"]], POP_MATCH[best["population_match"]], best["tier"]
    else:  # fall back to label/guidance or mechanism
        anyc = [c for c in claims if c["public"] and c["tier"]]
        t = min((c["tier"]["code"] for c in anyc), default=8)
        dw, pm, tier = DESIGN_W[t], POP_MATCH["mechanism"], {"code": t, "label": TIER_LABELS[t]}
    n = len({c.get("paper_key") or c["source"]["id"] for c in lit})
    sf = min(1.0, math.log2(1 + n) / math.log2(1 + STUDIES_SATURATE)) if n else 0.0
    h = sum(1 for c in lit if c["direction"] == "supports_harm")
    z = sum(1 for c in lit if c["direction"] in ("null", "protective"))
    cons = max(h, z) / (h + z) if (h + z) else 0.5
    score = round(dw * sf * cons * pm, 3) if n else 0.0
    meter = "strong" if score >= METER_T["strong"] else "some" if score >= METER_T["some"] else "early_signs"
    if h and z:
        direction = "conflicting"
    elif h:
        direction = "supports_harm"
    elif z:
        direction = "null"
    else:
        direction = "plausible_untested"
    nulls = [c["id"] for c in claims if c["direction"] in ("null", "conflicting", "protective")]
    mlabel = {"strong": "Strong", "some": "Some", "early_signs": "Early signs"}[meter]
    summ = f"{mlabel} evidence from {n} verified literature source{'s' if n != 1 else ''}"
    if z:
        summ += f"; {z} null finding{'s' if z != 1 else ''} shown, not hidden"
    return {
        "meter": meter, "meter_label": mlabel, "tier": tier, "literature_score": score,
        "components": {"design_weight": dw, "independent_studies": n, "study_factor": round(sf, 3),
                       "consistency": round(cons, 3), "population_match": pm},
        "direction": direction, "null_or_conflicting": nulls, "plain_summary": summ + ".",
    }


def faers_block(d, ctx):
    rows = [r for r in ctx.faers if r["drug_class"] == d["faers_class"] and r["event"].startswith(SPECIFIC_COMPOSITE)]
    if not rows:
        return None
    out = []
    for r in rows:
        out.append({"ingredient": r["ingredient"], "level": r["level"], "n_cases": int(fnum(r["n_cases"]) or 0),
                    "ror": fnum(r["ror"]), "ror_ci_low": fnum(r["ror_ci_low"]), "ror_ci_high": fnum(r["ror_ci_high"]),
                    "signal": r["signal"] == "yes", "above_neg_control_band": r["above_neg_control_band"] == "yes"})
    head = next((x for x in out if x["level"] == "class"), None) or out[0]
    cutoff = fnum(rows[0].get("neg_control_band_max")) or FAERS_NEG_CUTOFF_DEFAULT
    verdict = "above negative-control band" if head["above_neg_control_band"] else "signal (within noise band)" if head["signal"] else "no signal"
    if head["ror"] is not None and head["ror"] >= 1.1:
        rp = f"heat-illness reports were {plain_ratio(head['ror'])} as often as for other drugs"
    else:
        rp = "heat-illness reports were not more common than for other drugs"
    plain = f"FDA reports: {rp} ({verdict}). Warning signal, not proof."
    if verdict == "no signal":
        plain += " No signal does not mean safe."
    return {"composite": rows[0]["event"], "headline": head, "rows": out, "neg_control_cutoff": cutoff, "verdict": verdict,
            "plain": plain, "caveat": "warning signal, not proof", "input_file": ctx.faers_file}


def label_block(d, ctx):
    rows = [r for r in ctx.labels if r["drug_class"] == d["label_class"]]
    ing = []
    for r in rows:
        ing.append({"ingredient": r["ingredient"], "best_tier": r["best_tier"], "three_way": r.get("three_way") or r.get("coverage_class") or "",
                    "pct_heat_warning": fnum(r.get("pct_heat_warning")),
                    "n_labels_audited": int(fnum(r["n_labels_audited"]) or 0), "n_heat_warning": int(fnum(r["n_heat_warning"]) or 0),
                    "example_set_id": r["example_set_id"], "example_section": r["example_section"], "example_snippet": r["example_snippet"]})
    if not ing:
        st, pl = "not audited", "FDA label not audited for this drug."
    elif any(i["best_tier"] == "heat warning" for i in ing):
        n = sum(1 for i in ing if i["best_tier"] == "heat warning")
        st, pl = "heat warning", f"FDA label: {n} of {len(ing)} audited ingredients carry a heat warning."
    elif any(i["best_tier"].startswith("sweating") for i in ing):
        st, pl = "indirect only", "FDA label: mentions dehydration or sweating, but no heat warning (the missing label)."
    else:
        st, pl = "incidental or storage only", "FDA label: no heat warning; heat appears only as storage temperature or a side-effect listing (the missing label)."
    return {"class_status": st, "plain": pl, "ingredients": ing, "input_file": ctx.label_file}


def guidance_block(gid, ctx):
    rows = [r for r in ctx.guidance_rows if r["drug_id"] == gid]
    by = []
    mention_j, action_j = set(), set()
    for r in sorted(rows, key=lambda r: list(GUIDANCE_JURIS).index(r["source_id"]) if r["source_id"] in GUIDANCE_JURIS else 99):
        sa = r["specific_action"] == "yes"
        by.append({"source_id": r["source_id"], "jurisdiction": GUIDANCE_JURIS.get(r["source_id"], r["source_id"]),
                   "mention_level": r["mention_level"], "action_type": r["action_type"], "specific_action": sa,
                   "evidence_cited": r["evidence_cited"] == "yes", "quote": r["quote"], "location": r["location"]})
        if r["mention_level"] == "specific":
            mention_j.add(JURIS_OF.get(r["source_id"], r["source_id"]))
        if sa:
            action_j.add(JURIS_OF.get(r["source_id"], r["source_id"]))
    gap = len(action_j) == 0
    if not rows:
        reason = "Not coded in guidance_matrix.csv."
    elif gap and not mention_j:
        reason = "None of the 8 jurisdictions names this drug."
    elif gap:
        reason = f"Named by {len(mention_j)} of 8 jurisdictions, but none gives a drug-specific action."
    else:
        reason = f"Only {len(action_j)} of 8 jurisdictions give a drug-specific action."
    return {"n_jurisdictions": 8, "jurisdictions_mentioning": len(mention_j), "jurisdictions_specific_action": len(action_j),
            "gap": gap, "gap_reason": reason, "by_source": by, "input_file": INPUTS["guidance_matrix"]}


def graph_block(d, ctx):
    g = d["system_group"]
    paths = []
    for r in ctx.pathways:
        if r["drug_group"] != g:
            continue
        paths.append({"mediator": r["mediator"], "mediator_label": r["mediator_label"],
                      "drug_leg_studies": int(fnum(r["drug_leg_studies"]) or 0), "heat_leg_studies": int(fnum(r["heat_leg_studies"]) or 0),
                      "direct_drug_heat_studies": int(fnum(r["direct_drug_heat_studies"]) or 0),
                      "pathway_score_sqrt_studies": fnum(r["pathway_score_sqrt_studies"]) or 0.0,
                      "pathway_present": r["pathway_present"] == "True"})
    direct = []
    for r in ctx.direct:
        if r["drug_group"] == g:
            direct.append({"pmid": r["pubmed_id"], "drug_variable": r["drug_variable"], "heat_variable": r["heat_variable"],
                           "statistic_type": r["statistic_type"], "statistic_value": fnum(r["statistic_value"]),
                           "title": r["title_pubmed"], "flagged": bool(r["auto_flags_heuristic"].strip())})
    untested = sorted({r["mediator"] for r in ctx.untested if r["source"] == "drug_group" and r["entity"] == g and r["untested"] == "True"})
    rank = next((int(r["rank_share_nonbp"]) for r in ctx.pw_summary if r["drug_group"] == g), None)
    api = ctx.api_by_group.get(g) or ctx.api_by_group.get(d["id"])
    files = [INPUTS["system_pathways"], INPUTS["system_direct"], INPUTS["system_untested"], INPUTS["system_pathway_summary"]]
    if api:
        files.append(api.get("_file", "data/processed/system_api_*.csv"))
    return {"source": "System Public Graph, Harvard Dataverse v2.1 bulk release" + (" + System API" if api else ""),
            "pathways": paths, "direct_findings": direct, "untested_links": untested,
            "validation_rank_nonbp": rank, "api": api, "input_files": files}


def graph_claims(d, graph, start_idx):
    """Graph-layer claims (↗ corroborated), kept out of the literature score."""
    out = []
    i = start_idx
    for p in sorted(graph["pathways"], key=lambda p: -p["drug_leg_studies"]):
        if not p["pathway_present"] or p["mediator"] == "bp_hypotension" or p["drug_leg_studies"] < 3:
            continue
        out.append({
            "id": f"{d['id']}.c{i}",
            "text": f"System graph: {p['drug_leg_studies']} studies link {d['display'].lower()} to {p['mediator_label'].lower()}, and {p['heat_leg_studies']} studies link heat to it (two-hop pathway; direct drug x heat studies: {p['direct_drug_heat_studies']}).",
            "plain": f"Research links this medicine to {p['mediator_label'].lower()}, and heat to the same problem.",
            "number": {"value": p["drug_leg_studies"], "type": "n_studies", "ci_low": None, "ci_high": None,
                       "display": f"{p['drug_leg_studies']} + {p['heat_leg_studies']} studies", "plain": ""},
            "source": {"id": "SYSTEM:dataverse_v2.1", "label": "System Public Graph (Dataverse v2.1)", "url": "https://doi.org/10.7910/DVN/7V6JDO"},
            "layer": "graph", "tier": None, "direction": "plausible_untested", "population": "mixed (graph associations)",
            "population_match": "indirect", "badge": "↗", "badge_code": "corroborated",
            "verification": "pathway present in System associations (name-matched variables; not checked against abstracts)",
            "citation_status": "graph", "public": True, "input_file": INPUTS["system_pathways"],
        })
        i += 1
    return out


def faers_claim(d, fb, idx):
    if not fb or not fb["headline"] or fb["headline"]["ror"] is None:
        return []
    h = fb["headline"]
    return [{
        "id": f"{d['id']}.c{idx}",
        "text": f"FAERS (openFDA) specific heat composite: reporting odds ratio {h['ror']:g} (95% CI {h['ror_ci_low']:g}–{h['ror_ci_high']:g}), n = {h['n_cases']} reports, {h['ingredient']}; {fb['verdict']} (negative-control cut-off {fb['neg_control_cutoff']:g}).",
        "plain": fb["plain"],
        "number": {"value": h["ror"], "type": "ROR", "ci_low": h["ror_ci_low"], "ci_high": h["ror_ci_high"],
                   "display": f"ROR {h['ror']:g} ({h['ror_ci_low']:g}–{h['ror_ci_high']:g})", "plain": plain_ratio(h["ror"]).capitalize()},
        "source": {"id": "FAERS:openFDA", "label": "FDA Adverse Event Reporting System via openFDA (accessed 2026-11-14)", "url": "https://open.fda.gov/apis/drug/event/"},
        "layer": "fda_reports", "tier": None,
        "direction": "supports_harm" if h["signal"] else "null",
        "population": "spontaneous reports, any role", "population_match": "indirect",
        "badge": "✓", "badge_code": "verified", "verification": "computed from cached openFDA counts; warning signal, not proof",
        "citation_status": "computed", "public": True, "input_file": fb["input_file"],
    }]


def label_claim(d, lb, idx):
    hw = [i for i in lb["ingredients"] if i["best_tier"] == "heat warning"]
    if not hw:
        return []
    i0 = hw[0]
    return [{
        "id": f"{d['id']}.c{idx}",
        "text": f"FDA label ({i0['ingredient']}, set {i0['example_set_id']}, {i0['example_section']}): \"{i0['example_snippet']}\"",
        "plain": "The official FDA label warns about heat.",
        "number": None,
        "source": {"id": f"LABEL:{i0['example_set_id']}", "label": f"FDA label, {i0['ingredient']}", "url": f"https://dailymed.nlm.nih.gov/dailymed/lookup.cfm?setid={i0['example_set_id']}"},
        "layer": "label", "tier": {"code": 7, "label": TIER_LABELS[7]}, "direction": "supports_harm",
        "population": "label", "population_match": "mechanism", "badge": "✓", "badge_code": "verified",
        "verification": "verbatim snippet from openFDA label text", "citation_status": "label", "public": True,
        "input_file": INPUTS["label_summary"],
    }]


def build_drug(d, ctx):
    rid = d["id"]
    # names / ingredients
    ingredients = []
    for n in d["ingredients"]:
        rx = ctx.rx.get(n, {})
        acb = ctx.acb.get(n)
        ingredients.append({"name": n, "rxcui": rx.get("rxcui"), "rxnorm_name": rx.get("rxnorm_name"), "tty": rx.get("tty"),
                            "acb_score": acb})
    claims = [make_claim(s, i + 1, ctx, rid) for i, s in enumerate(d["claims"] + d.get("extra_unverified", []))]
    # merge literature screening/extraction (other agent) when present
    for s in ctx.lit_extra.get(rid, []):
        claims.append(make_claim(s, len(claims) + 1, ctx, rid))
    seen_ids = set()
    for c in claims:
        seen_ids |= paper_aliases(c["source"]["id"], ctx)
    # auto-harvest master-list citations not already curated (kept internal unless verified)
    for row in d["master_rows"]:
        for r in ctx.cv_by_loc.get(row, []):
            sid = ("PMID:" + r["id_value"]) if r["id_type"] == "pmid" else ("DOI:" + r["id_value"]) if r["id_type"] == "doi" else None
            if not sid:
                continue
            al = paper_aliases(sid, ctx)
            if al & seen_ids:
                continue
            seen_ids |= al
            mrow = ctx.master.get(row, {})
            spec = {"id": sid, "label": r.get("cited_label") or (r.get("fetched_first_author", "") + " " + r.get("fetched_year", "")).strip(),
                    "text": f"{mrow.get('Drug or class','')}: {mrow.get('What can go wrong','')} ({r.get('claim_text') or 'cited in master list'}).",
                    "plain": mrow.get("What can go wrong", ""), "tier": int(mrow.get("Evidence tier", "8")[0]) if mrow.get("Evidence tier") else None,
                    "direction": {"Supports harm": "supports_harm", "Null / no added risk": "null", "Conflicting": "conflicting"}.get(mrow.get("Evidence direction"), "plausible_untested"),
                    "pop": "indirect", "population": mrow.get("Higher-risk groups", "")}
            nums = [fnum(x) for x in (r.get("numbers_claimed") or "").split("|")]
            nums = [x for x in nums if x is not None]
            if nums:
                spec["num"], spec["ntype"] = nums[0], ""
            c = make_claim(spec, len(claims) + 1, ctx, rid)
            c["text"] = "[auto from master list] " + c["text"]
            claims.append(c)
    evidence = score_evidence(claims, d)
    fb = faers_block(d, ctx)
    lb = label_block(d, ctx)
    gb = graph_block(d, ctx)
    claims += graph_claims(d, gb, len(claims) + 1)
    claims += faers_claim(d, fb, len(claims) + 1)
    claims += label_claim(d, lb, len(claims) + 1)
    gv = guidance_block(rid, ctx)
    # FLAG / CHANGE
    sev = 1.0 if d["severity"] == "High" else 0.75
    harm = [c for c in claims if c["layer"] == "literature" and c["public"] and c["tier"] and c["direction"] == "supports_harm"]
    assoc = max((DESIGN_W[c["tier"]["code"]] * POP_MATCH[c["population_match"]] for c in harm), default=0.0)
    drivers = [f"association strength {assoc:.2f} x severity {sev}"]
    fs = assoc * sev
    if fb and fb["headline"]["above_neg_control_band"]:
        fs += 0.15
        drivers.append("FAERS above negative-control band (+0.15)")
    if lb["class_status"] == "heat warning":
        fs += 0.10
        drivers.append("FDA label heat warning (+0.10)")
    if gv["jurisdictions_mentioning"] >= 6:
        fs += 0.10
        drivers.append(f"{gv['jurisdictions_mentioning']}/8 jurisdictions list it (+0.10)")
    fs = round(fs, 3)
    has_alt = any(a.get("source_id") for a in d["alternatives"])
    cs = round(evidence["literature_score"] * d["causal_factor"] + (0.10 if has_alt else 0.0), 3)
    cdrivers = [f"literature score {evidence['literature_score']} x causal factor {d['causal_factor']}"] + (["cited alternative exists (+0.10)"] if has_alt else [])
    flag = {"level": level(fs, FLAG_T), "plain_label": "Check on this person", "score": fs,
            "rationale": d.get("flag_note") or f"Score {fs}: " + "; ".join(drivers) + ".", "drivers": drivers}
    clevel = level(cs, CHANGE_T)
    if d["causal_factor"] <= 0.5 and clevel == "high":
        clevel = "moderate"
        cdrivers.append("capped at moderate: within-person/adjusted evidence shows no added drug effect")
    change = {"level": clevel, "plain_label": "Rethink the medicine", "score": cs,
              "rationale": f"Score {cs}: " + "; ".join(cdrivers) + ". " + d["causal_note"], "drivers": cdrivers}
    if d.get("flag_note"):
        flag["rationale"] = f"Score {fs}: " + "; ".join(drivers) + ". " + d["flag_note"]
    cp = d["compass"]
    sym = {"up": "↑", "down": "↓", "depends": "↕"}[cp["arrow"]]
    compass = {"arrow": cp["arrow"], "symbol": sym, "meaning": cp["meaning"], "mechanism": cp["mechanism"],
               "triggers": cp["triggers"], "monitor": cp["monitor"], "evidence_meter": cp.get("meter", evidence["meter"]),
               "source_claim_ids": [c["id"] for c in claims if c["public"] and c["layer"] in ("literature", "label", "guidance")][:6],
               "note": "Direction only, not doses: no validated calibration exists (spec §6.2; Vanakoski & Seppälä 1998, PMID 9571303)."}
    hs = {k: {"affected": v[0], "how": v[1]} for k, v in d["heat_stack"].items() if k != "other"}
    hs["other"] = [{"defense": a, "how": b} for a, b in d["heat_stack"]["other"]]
    alts = []
    for a in d["alternatives"]:
        alts.append({"name": a["name"], "why": a["why"], "what_is_lost": a["lost"], "heat_studied": a["heat_studied"],
                     "heat_evidence_label": a.get("heat_label") or ("studied in heat" if a["heat_studied"] else "not studied in heat"),
                     "source": {"id": a["source_id"], "label": a["source_label"], "url": a.get("source_url")} if a.get("source_id") else None,
                     "caution": "A spring-review consideration, never an automatic switch. Never stop abruptly; any change is the prescriber's decision."})
    combos = [dict(c) for c in ctx.combos_by_drug.get(rid, [])]
    tl = [{"phase": p, "action": a, "who": w, "evidence_meter": m, "basis": b} for p, a, w, m, b in d["timeline"]]
    public_ids = [c["id"] for c in claims if c["public"] and c["layer"] in ("literature", "guidance", "label")]
    msgs = [{"situation": s, "en": en, "es": es, "es_status": ES_STATUS,
             "reading_level_note": "Plain language; no dose advice; ends with 'talk to your doctor or pharmacist'.",
             "uses_claim_ids": public_ids[:3]} for s, en, es in d["messages"]]
    for m in msgs:
        check_no_dose(m["en"], f"{rid} message"), check_no_dose(m["es"], f"{rid} message es")
        assert m["en"].endswith(TALK_EN) and m["es"].endswith(TALK_ES), f"{rid}: message must end with talk-to-doctor"
    check_no_dose(d["label_line"], f"{rid} label_line")
    storage = None
    if d.get("storage_profile"):
        prof = ctx.storage.get(d["storage_profile"])
        storage = {"profile_id": d["storage_profile"], "summary": (prof or {}).get("label", {}).get("summary", "profile not found"),
                   "input_file": INPUTS["storage_profiles"] if prof else None}
    return {
        "id": rid, "scope": d.get("scope", "core15"),
        "names": {"display": d["display"], "plain": d["plain"], "class_label": d["class_label"], "examples": d["examples"],
                  "ingredients": ingredients, "master_list_rows": d["master_rows"]},
        "buckets": [{"bucket": b, "primary": p, "rationale": r} for b, p, r in d["buckets"]],
        "mechanism_groups": d["mechanism_groups"],
        "label_line": d["label_line"],
        "evidence": evidence, "flag": flag, "change": change, "compass": compass, "heat_stack": hs,
        "prescribers": d["prescribers"], "higher_risk_groups": d["higher_risk"], "pediatric_note": d.get("pediatric"),
        "guidance": gv, "fda_label": lb, "faers": fb, "graph": gb, "claims": claims,
        "alternatives": alts, "combinations": combos, "timeline": tl, "patient_messages": msgs, "storage": storage,
        "gaps": d["gaps"], "disclaimer": DISCLAIMER,
    }


# ----------------------------------------------------------------------------- combination rules
COMBINATION_RULES = [
    C(id="cr_diuretic_raas", label="Diuretic + ACE inhibitor/ARB (+/- NSAID: 'triple whammy')", rule="direct_evidence",
      members=["loop_diuretics", "thiazides", "acei_arb", "nsaids"], groups=["fluid_salt_loss", "kidney_stress", "bp_drop"],
      description="Fluid loss plus blunted kidney blood-flow regulation. Starting an ACE inhibitor + diuretic product had the highest dehydration/heat-illness admission ratio (2.79). The full triple whammy was null for in-hospital AKI in heat waves (OR 1.02): shown honestly.",
      evidence="Kalisch Ellett 2016 (harm); Mangoni 2017 (null)", claim_refs=[KALISCH, MANGONI], direction="conflicting",
      plain="A water pill together with a blood-pressure medicine like lisinopril (and especially with ibuprofen-type painkillers) can strain the kidneys when you are low on fluids."),
    C(id="cr_two_antipsychotics", label="Two or more antipsychotics", rule="direct_evidence",
      members=["antipsychotics_clozapine"], groups=["thermostat", "sweat_blocked"],
      description="In the 2021 BC heat dome, dispensation of two or more antipsychotics had OR 4.05 for death among people with schizophrenia (any antipsychotic OR 2.43).",
      evidence="Chen et al., Sci Rep 2025", claim_refs=[CHEN], direction="supports_harm",
      plain="Taking two medicines of this kind together was linked to a higher risk during an extreme heat event."),
    C(id="cr_lithium_fluid", label="Lithium + fluid-losing or kidney-flow drug (diuretic, ACE inhibitor/ARB, NSAID, SGLT2 inhibitor)", rule="cross_mechanism",
      members=["lithium", "loop_diuretics", "thiazides", "acei_arb", "nsaids", "sglt2"], groups=["kidney_cleared_buildup", "fluid_salt_loss"],
      description="Fluid-losing drug + kidney-cleared narrow-margin drug: dehydration lowers lithium clearance. Not studied in heat; mechanism and known interaction only.",
      evidence="mechanism only / no heat study", claim_refs=[], direction="plausible_untested",
      plain="Lithium plus a water pill or some blood-pressure or pain medicines can let lithium build up when you lose fluid in the heat."),
    C(id="cr_thiazide_ssri_sodium", label="Thiazide + SSRI (low sodium)", rule="direct_evidence",
      members=["thiazides", "ssri"], groups=["low_sodium"],
      description="Both lower sodium; drug-induced hyponatremia rises in hot periods. The '~30% of hyponatremia admissions' figure is from a thesis and is not machine-verified (kept internal).",
      evidence="IJERPH 2017; JCEM 2022 (exist; no numbers verified)", claim_refs=["DOI:10.3390/ijerph14070827", "DOI:10.1210/clinem/dgac103"], direction="supports_harm",
      plain="A water pill like hydrochlorothiazide plus an antidepressant like sertraline can lower the salt in your blood, more so in hot weather. Drinking large amounts of plain water can make it worse."),
    C(id="cr_anticholinergic_stack", label="Anticholinergic stacking (sum of ACB scores >= 3)", rule="same_mechanism_stack",
      members=["anticholinergics_oxybutynin", "antipsychotics_clozapine"], groups=["sweat_blocked"],
      description="Sweat blockers add up. Sum Anticholinergic Cognitive Burden (2012) scores across all medicines; >= 3 is the scale's clinically relevant threshold. Other drugs on the scale count too (e.g. paroxetine 3, furosemide 1); see data/kb/anticholinergic_burden.csv. Antipsychotic + anticholinergic in outdoor workers has fatal case reports.",
      evidence="ACB scale 2012 (Boustani 2008); Kao & Kelly 2007 (case)", claim_refs=["PMID:18025545"], direction="supports_harm",
      plain="Several medicines that each reduce sweating add up, and together make it harder for your body to cool down."),
    C(id="cr_sglt2_diuretic", label="SGLT2 inhibitor + diuretic", rule="same_mechanism_stack",
      members=["sglt2", "loop_diuretics", "thiazides"], groups=["fluid_salt_loss"],
      description="Both remove water and salt through the urine. Not studied in heat; no guidance names SGLT2 inhibitors.",
      evidence="mechanism only / no heat study", claim_refs=[], direction="plausible_untested",
      plain="Two medicines that both make you pass more water can leave you dehydrated in hot weather."),
]


def combos_for(ctx, all_ids):
    out = defaultdict(list)
    for r in COMBINATION_RULES:
        for m in r["members"]:
            if m not in all_ids:
                continue
            partners = [x for x in r["members"] if x != m]
            claim_ids = []
            out[m].append({"id": r["id"], "partners": partners or [m], "label": r["label"], "rule": r["rule"],
                           "mechanism_groups": r["groups"], "finding": r["description"], "direction": r["direction"],
                           "claim_ids": claim_ids, "plain": r["plain"], "_refs": r["claim_refs"]})
    return out


# ----------------------------------------------------------------------------- tolerant merges
def first_col(row, names):
    for n in names:
        for k in row:
            if k.lower() == n:
                return row[k]
    return None


SYS_AUDIT_NOTE = "System audit: System's extraction of this paper mislabels or drops the drug (graph-audit fix list)"


def prefer_api(paths):
    """Drop a *_dataverse_fallback file when the live-API file with the same name exists (no double counting)."""
    s = set(paths)
    return [p for p in paths if not (p.endswith("_dataverse_fallback.csv")
                                     and p.replace("_dataverse_fallback.csv", ".csv") in s)]


def load_api_verification(ctx):
    """System API verification (other agent). Accepts system_api_verification.csv or *_dataverse_fallback variants;
    when both exist the live-API file wins."""
    ctx.api_verif, ctx.api_num = {}, {}
    ctx.api_files = []
    vfiles = prefer_api(sorted(glob.glob(P("data/processed/system_api_verification*.csv"))))
    vclaim = [f for f in vfiles if "numbers" not in os.path.basename(f)]
    vnum = [f for f in vfiles if "numbers" in os.path.basename(f)]
    n = 0
    for path in vclaim:
        ctx.api_files.append(os.path.relpath(path, ROOT))
        for r in read_csv(path):
            n += 1
            badge = (first_col(r, ["badge", "verification_badge"]) or "").strip()
            for k in (first_col(r, ["paper_key"]), (first_col(r, ["id_type"]) or "") + ":" + (first_col(r, ["id_value", "pmid"]) or "")):
                if k and ":" in k and k.split(":", 1)[1]:
                    ctx.api_verif.setdefault(k.lower(), []).append({
                        "badge": badge, "note": os.path.basename(path),
                        "mislabel_only": (fnum(r.get("numbers_direction_conflict")) or 0) == 0 and (fnum(r.get("numbers_mislabel")) or 0) > 0})
    for path in vnum:
        ctx.api_files.append(os.path.relpath(path, ROOT))
        for r in read_csv(path):
            v = fnum(first_col(r, ["number"]))
            pk = (first_col(r, ["paper_key"]) or "").lower()
            if v is not None and pk:
                ctx.api_num[(pk, round(v, 4))] = {"badge": (first_col(r, ["badge"]) or "").strip(),
                                                  "system_result": first_col(r, ["system_result"]) or "", "file": os.path.relpath(path, ROOT)}
    ctx.api_by_group = {}
    for path in prefer_api(sorted(glob.glob(P(GLOB_INPUTS["system_api_extra"])))):
        if os.path.basename(path).startswith("system_api_verification"):
            continue
        for r in read_csv(path):
            g = first_col(r, ["drug_group", "drug_id", "group"])
            if not g:
                continue
            rec = ctx.api_by_group.setdefault(g, {"_file": os.path.relpath(path, ROOT), "rows": 0})
            rec["rows"] += 1
            for k in ("num_studies", "num_findings", "n_studies"):
                fv = fnum(first_col(r, [k]))
                if fv is not None:
                    rec[k] = rec.get(k, 0) + fv
    return n


def load_literature_screen(ctx, ids):
    """Map extraction rows to claim specs. Every number is re-grounded against the abstract here."""
    ctx.lit_extra = defaultdict(list)
    files = sorted(glob.glob(P(GLOB_INPUTS["literature_screen"])))
    n = 0
    if not MERGE_LIT:
        return files, 0
    for path in files:
        for r in read_csv(path):
            raw_cls = (r.get("drug_class") or "").strip()
            drug = LIT_CLASS_TO_KB.get(raw_cls) or (first_col(r, ["drug_id", "drug_group", "kb_id"]) or "").strip()
            if drug not in ids:
                continue
            # Skip doubtful includes and narrative reviews (tier 8) so they can't inflate evidence scores.
            if (r.get("uncertain_include") or "").strip().lower() in ("true", "1", "yes"):
                continue
            if (r.get("evidence_tier") or "").strip()[:1] == "8":
                continue
            if (r.get("direction") or "").strip().lower() in ("not_stated", ""):
                continue
            dec = (first_col(r, ["include", "decision", "screen_decision", "included"]) or "include").strip().lower()
            if dec not in ("include", "included", "yes", "true", "1"):
                continue
            pmid = (first_col(r, ["pmid"]) or "").strip()
            doi = (first_col(r, ["doi"]) or "").strip()
            sid = f"PMID:{pmid}" if pmid else f"DOI:{doi}" if doi else None
            text = first_col(r, ["claim", "finding", "effect_text", "summary", "result"]) or ""
            if not sid or not text:
                continue
            # Auto-extracted text is uncurated: drop any row with dose-like text instead of failing the build.
            if DOSE_RE.search(text):
                ctx.lit_dose_skipped = getattr(ctx, "lit_dose_skipped", 0) + 1
                continue
            design = (first_col(r, ["tier", "design_tier", "evidence_tier"]) or "").strip()
            tier = int(design[0]) if design[:1].isdigit() else 2
            dirn = (first_col(r, ["direction"]) or "supports_harm").strip().lower().replace(" ", "_")
            dirn = LIT_DIRECTION.get(dirn, dirn)
            dirn = dirn if dirn in ("supports_harm", "null", "conflicting", "protective") else "supports_harm"
            spec = {"id": sid, "label": first_col(r, ["citation", "label", "title"]) or sid, "text": text, "plain": text,
                    "tier": tier, "direction": dirn, "pop": "subgroup_in_heat", "population": first_col(r, ["population"]) or ""}
            v = fnum(first_col(r, ["statistic_value", "effect_size", "value"]))
            if v is not None:
                spec["num"], spec["ntype"] = v, first_col(r, ["statistic_type", "effect_type"]) or ""
            ctx.lit_extra[drug].append(spec)
            n += 1
    return files, n


# ----------------------------------------------------------------------------- main
def main():
    os.makedirs(OUT, exist_ok=True)
    ctx = Ctx()
    ctx.abstracts = load_abstracts()
    ctx.cv = load_citation_verification()
    ctx.cv_by_loc = defaultdict(list)
    for r in read_csv("citation_verification"):
        if r["source"] == "master_list":
            ctx.cv_by_loc[r["location"]].append(r)
    ctx.master = {r["ID"]: r for r in read_csv("master_list")}
    ctx.guidance_rows = read_csv("guidance_matrix")
    ctx.guidance = {(r["source_id"], r["drug_id"]): r for r in ctx.guidance_rows}
    ctx.faers_file = INPUTS["faers_v2"] if exists("faers_v2") else INPUTS["faers"]
    ctx.faers = read_csv(ctx.faers_file)
    ctx.label_file = INPUTS["label_summary_v2"] if exists("label_summary_v2") else INPUTS["label_summary"]
    ctx.labels = read_csv(ctx.label_file)
    ctx.pathways = read_csv("system_pathways")
    ctx.pw_summary = read_csv("system_pathway_summary")
    ctx.direct = read_csv("system_direct")
    ctx.untested = read_csv("system_untested")
    ctx.sys_findings = defaultdict(list)
    for r in read_csv("system_master_findings"):
        if r.get("id_type") == "pmid" and r.get("statistic_value"):
            ctx.sys_findings[r["id"]].append(r)
    ctx.storage = {}
    if exists("storage_profiles"):
        ctx.storage = {p["id"]: p for p in json.load(open(P(INPUTS["storage_profiles"]))).get("profiles", [])}
    ctx.acb = {}
    for r in read_csv("acb"):
        if r.get("acb_score", "").strip():
            ctx.acb[r["drug_generic"].strip().lower()] = int(r["acb_score"])
    n_api = load_api_verification(ctx)
    drugs_spec = DRUGS + DRUGS_MORE
    ids = [d["id"] for d in drugs_spec]
    lit_files, n_lit = load_literature_screen(ctx, set(ids))
    ctx.rx, rx_calls = rxnorm_lookup([n for d in drugs_spec for n in d["ingredients"]])
    ctx.combos_by_drug = combos_for(ctx, set(ids) | {"nsaids"})

    records = [build_drug(d, ctx) for d in drugs_spec]
    # resolve combination claim references to claim ids (any drug's public claim with that source id)
    src_to_claims = defaultdict(list)
    for rec in records:
        for c in rec["claims"]:
            if c["public"]:
                src_to_claims[c.get("paper_key") or c["source"]["id"].lower()].append(c["id"])
    def rule_claims(refs, members):
        return sorted({cid for ref in refs for cid in src_to_claims.get(paper_key(ref, ctx), []) if cid.split(".")[0] in members})
    for rec in records:
        for cb in rec["combinations"]:
            cb["claim_ids"] = rule_claims(cb.pop("_refs"), set(cb["partners"]) | {rec["id"]})
    rules_out = []
    for r in COMBINATION_RULES:
        rules_out.append({"id": r["id"], "label": r["label"], "rule": r["rule"], "members": r["members"], "description": r["description"],
                          "evidence": r["evidence"], "claim_ids": rule_claims(r["claim_refs"], set(r["members"]))})

    # inputs manifest (deterministic)
    manifest = []
    for k, rel in sorted(INPUTS.items()):
        path = P(rel)
        pres = os.path.exists(path)
        rows = None
        if pres and rel.endswith(".csv"):
            rows = len(read_csv(path))
        elif pres and rel.endswith(".jsonl"):
            rows = sum(1 for _ in open(path, encoding="utf-8"))
        manifest.append({"path": rel, "present": pres, "rows": rows, "sha1": sha1_file(path) if pres else None})
    for k, pat in sorted(GLOB_INPUTS.items()):
        hits = sorted(glob.glob(P(pat)))
        hits = [h for h in hits if not h.endswith("system_api_verification.csv")]
        if not hits:
            manifest.append({"path": pat, "present": False, "rows": None, "sha1": None})
        for h in hits:
            manifest.append({"path": os.path.relpath(h, ROOT), "present": True, "rows": len(read_csv(h)), "sha1": sha1_file(h)})
    build_id = hashlib.sha1((json.dumps(manifest, sort_keys=True) + open(__file__, "rb").read().decode("utf-8")).encode()).hexdigest()[:12]

    kb = {
        "schema_version": SCHEMA_VERSION, "build_id": build_id, "disclaimer": DISCLAIMER, "inputs": manifest,
        "evidence_model": {"formula": FORMULA, "design_weights": {f"{k} {TIER_LABELS[k]}": v for k, v in DESIGN_W.items()},
                           "population_match": POP_MATCH, "meter_thresholds": METER_T, "flag_change_rules": FLAG_RULE},
        "anticholinergic_scale": {"name": "Anticholinergic Cognitive Burden (ACB) Scale, 2012 update",
                                  "source": "Boustani M et al. Aging Health 2008;4(3):311-320; 2012 update, Aging Brain Care / Regenstrief Institute",
                                  "url": "https://www.hii.iu.edu/resources/anticholinergic-cognitive-burden-scale.pdf",
                                  "input_file": INPUTS["acb"]},
        "combination_rules": rules_out,
        "drugs": records,
    }
    def dump(obj, name):
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=1, ensure_ascii=False)
            f.write("\n")
    if MERGE_LIT:
        dump(kb, "knowledge_base_with_screened_lit.json")
    else:
        dump(kb, "knowledge_base.json")
        mock = dict(kb)
        mock["drugs"] = [r for r in records if r["id"] in ("lithium", "loop_diuretics", "anticholinergics_oxybutynin")]
        mock["combination_rules"] = rules_out
        dump(mock, "mock_knowledge_base.json")
    write_report(kb, manifest, rx_calls, n_api, lit_files, n_lit, ctx)
    print(f"built {len(records)} drugs, build_id {build_id}; RxNav calls {rx_calls}")


def write_report(kb, manifest, rx_calls, n_api, lit_files, n_lit, ctx):
    L = []
    a = L.append
    a("# Knowledge base v0: build report\n")
    a(f"Generated by `scripts/build_knowledge_base.py` (deterministic; build_id `{kb['build_id']}`, schema {kb['schema_version']}).")
    a("Rerun after other agents finish: `~/.local/bin/uv run python scripts/build_knowledge_base.py` (add `--offline` to skip RxNav).\n")
    a(f"> {DISCLAIMER}\n")
    a("## Inputs\n")
    a("| Input | Present | Rows |")
    a("|---|---|---|")
    for m in manifest:
        a(f"| `{m['path']}` | {'yes' if m['present'] else '**no (merged automatically when it appears)**'} | {m['rows'] if m['rows'] is not None else ''} |")
    a("")
    a(f"- FAERS file used: `{ctx.faers_file}`; label summary used: `{ctx.label_file}`.")
    a(f"- System API verification files: {', '.join('`'+f+'`' for f in ctx.api_files) or 'none'} ({n_api} claim rows). Literature screening files: {len(lit_files)} ({n_lit} included extraction rows merged).")
    a(f"- RxNav network calls this run: {rx_calls} (cache: `data/kb/rxnorm_cache.json`).\n")
    a("## Counts\n")
    drugs = kb["drugs"]
    allc = [c for d in drugs for c in d["claims"]]
    a(f"- Drugs/classes: {len(drugs)}")
    a(f"- Claims: {len(allc)} total; public {sum(c['public'] for c in allc)}; hidden as unverified (?) {sum(not c['public'] for c in allc)}")
    a("- Badges: " + ", ".join(f"{k} {v}" for k, v in sorted(Counter(c['badge'] for c in allc).items())))
    a("- Layers: " + ", ".join(f"{k} {v}" for k, v in sorted(Counter(c['layer'] for c in allc).items())))
    a("")
    a("| Drug | Buckets | Meter (score) | Tier | FLAG | CHANGE | Compass | Guidance mention / action (of 8) | FDA label | FAERS | Public / hidden claims |")
    a("|---|---|---|---|---|---|---|---|---|---|---|")
    for d in drugs:
        e = d["evidence"]
        fa = d["faers"]["verdict"] if d["faers"] else "n/a"
        pub = sum(c["public"] for c in d["claims"])
        a(f"| {d['names']['display']} | {', '.join(b['bucket'] for b in d['buckets'])} | {e['meter_label']} ({e['literature_score']}) | {e['tier']['code']} | "
          f"{d['flag']['level']} ({d['flag']['score']}) | {d['change']['level']} ({d['change']['score']}) | {d['compass']['symbol']} | "
          f"{d['guidance']['jurisdictions_mentioning']} / {d['guidance']['jurisdictions_specific_action']} | {d['fda_label']['class_status']} | {fa} | {pub} / {len(d['claims']) - pub} |")
    a("")
    a("## Evidence scoring (spec §9)\n")
    a(FORMULA + "\n")
    a("Design weights (8-step tier):\n")
    for k, v in DESIGN_W.items():
        a(f"- {k} {TIER_LABELS[k]}: {v}")
    a("\nPopulation match:\n")
    for k, v in POP_MATCH.items():
        a(f"- `{k}`: {v}")
    a(f"\nStudy factor saturates at {STUDIES_SATURATE} independent sources. Meter thresholds: Strong >= {METER_T['strong']}, Some >= {METER_T['some']}.\n")
    a("### FLAG vs CHANGE\n")
    a(FLAG_RULE + "\n")
    a("### Badges\n")
    a("- ✓✓ number found verbatim in the abstract AND System (Dataverse v2.1 `system_master_list_study_findings.csv`, or System API verification when present) has the same value.")
    a("- ✓ citation exists (PubMed/Crossref check in `citation_verification.csv` or abstract in `abstracts.jsonl`) and every claimed number is verbatim in the abstract; or a guidance quote verbatim in the coded source; or a computed FAERS/label value from cached openFDA data.")
    a("- ↗ System graph two-hop pathway (drug -> mediator <- heat) with >= 3 drug-leg studies, non-BP mediators only. Graph layer; never in the literature score.")
    a("- ⚠ System value or API check conflicts with ours.")
    a("- ? no citation id, citation not found, or number not in abstract. **Never public**: excluded from label lines, patient messages, the meter and FLAG/CHANGE.\n")
    a("## Anticholinergic burden\n")
    acb_rows = read_csv("acb")
    a(f"`{INPUTS['acb']}`: {len(acb_rows)} drugs from the Anticholinergic Cognitive Burden Scale, 2012 update "
      "(Boustani et al., Aging Health 2008; Aging Brain Care / Regenstrief), PDF https://www.hii.iu.edu/resources/anticholinergic-cognitive-burden-scale.pdf, "
      "read from the official PDF (copy in `data/kb/sources/`). Counts by score: "
      + ", ".join(f"{k}: {v}" for k, v in sorted(Counter(r['acb_score'] for r in acb_rows).items())) + ". "
      "Drugs not on the scale get `acb_score: null` (never 0 and never invented). This replaces the provisional, from-memory scores in the synthetic panel "
      "(the panel script itself was not edited; re-generate it against this CSV).\n")
    kb_ing = sorted({(i["name"], i["acb_score"]) for d in drugs for i in d["names"]["ingredients"]})
    a("KB ingredients on the scale: " + ", ".join(f"{n} {s}" for n, s in kb_ing if s is not None) + ".")
    a("KB ingredients not on the scale: " + ", ".join(n for n, s in kb_ing if s is None) + ".\n")
    a("## Featured case check (spec §6.3)\n")
    for d in drugs:
        if d["id"] == "antipsychotics_clozapine":
            a(f"Antipsychotics: FLAG {d['flag']['level']}, CHANGE {d['change']['level']} (spec target: FLAG high, CHANGE moderate).\n")
    a("## Hidden (?) claims: what to check next\n")
    for d in drugs:
        for c in d["claims"]:
            if not c["public"]:
                a(f"- `{c['id']}` {c['source']['label']}: {c['verification']}")
    a("\n## Guardrails enforced at build time\n")
    a("- Dose guard regex over all public text (claims, label lines, patient messages); the build fails on a match.")
    a("- Every patient message ends with 'Talk to your doctor or pharmacist.' / 'Hable con su médico o farmacéutico.'")
    a(f"- Spanish text is marked '{ES_STATUS}'.")
    a("- Heat Dose Compass is an arrow plus mechanism, triggers and monitoring; no numbers.\n")
    a("## What's missing / caveats\n")
    for m in manifest:
        if not m["present"]:
            a(f"- `{m['path']}` not present at build time.")
    a("- Literature claims are curated in the script from verified citations (citation_verification.csv / abstracts.jsonl); the LLM screening/extraction outputs are merged when present and re-grounded against abstracts.")
    a("- No human review of claims, scores or translations (spec §8.2a).")
    a("- Graph pathways rely on name-matched variables (System Dataverse v2.1); about 20% of System extractions are wrong by System's own estimate.")
    a("- FAERS: any-role drug matching, no exposure denominator; warning signal, not proof.")
    report_name = "kb_build_report_with_screened_lit.md" if MERGE_LIT else "kb_build_report.md"
    with open(os.path.join(OUT, report_name), "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")


def _hs(sw, ws, kc, bp, other=()):
    return C(sweating=sw, water_salt=ws, kidney_clearance=kc, blood_pressure=bp, other=list(other))


NO = ("no", "No direct effect.")

DRUGS_MORE: list = [
    # ------------------------------------------------------------------ thiazides
    C(
        id="thiazides", display="Thiazide diuretics", plain="Water pills (thiazides)", class_label="Diuretic",
        examples=["hydrochlorothiazide", "chlorthalidone", "indapamide"],
        ingredients=["hydrochlorothiazide", "chlorthalidone", "indapamide"],
        master_rows=["R26", "R30"], faers_class="thiazides", label_class="thiazides", system_group="thiazides",
        storage_profile=None, severity="High",
        buckets=[("monitor", True, "Low sodium is the main heat risk; it is worst in the very old and is made worse by drinking large amounts of plain water."),
                 ("adjust_dose", False, "A prescriber may review the need for a thiazide before summer; no dose numbers are given here.")],
        mechanism_groups=["fluid_salt_loss", "low_sodium", "bp_drop"],
        heat_stack=_hs(("no", "Does not block sweating."), ("yes", "Loses salt and water; low blood sodium (hyponatremia) is the classic thiazide problem."),
                       ("possible", "Volume loss can strain the kidneys."), ("yes", "Lower blood volume adds to heat-related blood-pressure drop."),
                       [("skin", "Hydrochlorothiazide makes skin more sun-sensitive.")]),
        compass=C(arrow="up", meaning="Acts stronger in heat: salt and water loss adds to sweating.",
                  mechanism="Salt loss in urine + sweat loss -> low sodium and low blood volume.",
                  triggers=["forecast heat", "drinking large amounts of plain water", "starting an SSRI"],
                  monitor=["sodium (clinician decides timing)", "confusion, headache, nausea, falls", "dizziness on standing"]),
        prescribers=["primary care", "cardiology"], higher_risk=["age 80+", "low body weight", "people also taking SSRIs"], pediatric=None,
        causal_factor=0.75, causal_note="Low-sodium mechanism is direct; heat-wave studies of non-loop diuretics found no added heat-illness risk.",
        claims=[
            C(id=HARLEY, label="Harley et al., Pharmacoepidemiol Drug Saf 2026",
              text="Japanese self-controlled case series: ACE inhibitors/ARBs and CCBs were associated with increased heat-related illness during heatwaves, whereas there was no evidence of an effect with (non-loop) diuretics.",
              plain="In one careful Japanese study, these water pills did not add heat-illness risk during heat waves.",
              tier=2, direction="null", pop="patients_in_heat", population="adults with hypertension, Japan"),
            C(id=HOSPERS, label="Hospers et al., eClinicalMedicine 2024 (meta-analysis)",
              text="Heat-stress trials: diuretics did not alter core temperature responses.",
              plain="In lab heat tests, water pills did not raise body temperature.",
              tier=1, direction="null", pop="lab_heat_healthy", population="healthy young adults"),
            C(id="PMID:27992525", label="PLoS One 2016 (Israel)",
              text="Older inpatients on thiazide and/or ACE inhibitor/ARB: a 5 °C higher daily temperature on admission was associated with a creatinine increase, significant in the dual-treatment group (% change 3.440).",
              plain="In older adults on these blood-pressure medicines, hotter days were linked to worse kidney tests.",
              tier=2, direction="supports_harm", pop="subgroup_in_heat", population="hospitalized adults 65+, Israel"),
            C(id="DOI:10.3390/ijerph14070827", label="IJERPH 2017",
              text="Drug-induced hyponatremia risk increased during high temperatures.",
              plain="Low blood salt caused by medicines became more common in hot weather.",
              tier=2, direction="supports_harm", pop="subgroup_in_heat", population="hyponatremia cases"),
        ],
        alternatives=[],
        timeline=[
            ("before_summer", "Review thiazide + SSRI combinations and low-sodium history; give individual fluid advice (not blanket 'drink more').", ["prescriber", "pharmacist"], "some", "IJERPH 2017; Health Canada (overdrinking warning)"),
            ("during", "Check in about confusion, nausea, headache or falls.", ["care_coordinator"], "some", "guidance; mechanism"),
            ("after", "Sodium check for flagged older patients (clinician-approved).", ["prescriber"], "early_signs", "spec §4.4 item 9"),
        ],
        messages=[("heat_forecast",
                   "Heat warning for your water pill: in hot weather it can make the salt in your blood too low, especially if you drink a lot of plain water. Watch for confusion, headache, feeling sick or falling. Follow the drinking advice your care team gave you and stay somewhere cool. " + TALK_EN,
                   "Aviso de calor por su pastilla para orinar: con el calor puede bajarle demasiado la sal en la sangre, sobre todo si toma mucha agua sola. Fíjese si tiene confusión, dolor de cabeza, náuseas o se cae. Siga los consejos sobre líquidos que le dio su equipo médico y quédese en un lugar fresco. " + TALK_ES)],
        label_line="In heat, thiazides can drive sodium too low, especially in the very old and with SSRIs: give individual fluid advice.",
        gaps=["Sun sensitivity / skin cancer with hydrochlorothiazide (master list R76, Pedersen 2018) is a sun risk, not a heat risk; kept out of the heat evidence score.",
              "The '~30% of hyponatremia admissions from thiazide + SSRI' figure comes from a thesis and is not machine-verified.",
              "Heat-wave studies show no added heat-illness risk for non-loop diuretics; the low-sodium risk is the concern."],
        extra_unverified=[],
    ),
    # ------------------------------------------------------------------ ACEi / ARB
    C(
        id="acei_arb", display="ACE inhibitors / ARBs", plain="Blood-pressure medicines (ACE inhibitors and ARBs)", class_label="Renin-angiotensin blocker",
        examples=["lisinopril", "enalapril", "ramipril", "losartan", "valsartan", "olmesartan"],
        ingredients=["lisinopril", "enalapril", "ramipril", "losartan", "valsartan", "olmesartan"],
        master_rows=["R27", "R28"], faers_class="ACE inhibitors/ARBs", label_class="ACE inhibitors/ARBs", system_group="acei_arb",
        storage_profile=None, severity="High",
        buckets=[("adjust_dose", True, "When someone is dehydrated these drugs stop the kidneys protecting their own blood flow; a prescriber decides any change (Heidelberg: fluid diary)."),
                 ("monitor", False, "Kidney function, potassium and dizziness during and after heat.")],
        mechanism_groups=["kidney_stress", "bp_drop"],
        heat_stack=_hs(NO, ("possible", "Dehydration plus these drugs lowers kidney filtration."), ("yes", "Kidneys cannot keep up filtration when low on fluid; other drugs build up."),
                       ("yes", "Adds to heat-related blood-pressure drop.")),
        compass=C(arrow="up", meaning="Acts stronger in heat: blood-pressure and kidney effects grow when you are low on fluid.",
                  mechanism="Blocked angiotensin + volume loss -> lower kidney filtration and blood pressure.",
                  triggers=["forecast heat", "vomiting/diarrhea", "adding a diuretic or NSAID"],
                  monitor=["creatinine and potassium (clinician decides)", "dizziness, fainting, falls"]),
        prescribers=["primary care", "cardiology", "nephrology"], higher_risk=["older adults", "chronic kidney disease", "people also on diuretics or NSAIDs"], pediatric=None,
        causal_factor=0.75, causal_note="Within-person Japanese data show a drug-temperature interaction, but the authors could not exclude confounding.",
        claims=[
            C(id=HARLEY, label="Harley et al., Pharmacoepidemiol Drug Saf 2026",
              text="Self-controlled case series: heat-related illness rose more during heatwaves in person-time prescribed antihypertensives (IRR 1.64, 95% CI 1.53-1.75) than not prescribed (IRR 1.42); ACE inhibitors/ARBs were associated with increased risk.",
              plain="During heat waves, people on blood-pressure medicines had a bigger rise in heat illness than people not on them.",
              num=1.64, ntype="IRR", ci=(1.53, 1.75), tier=2, direction="supports_harm", pop="patients_in_heat", population="adults with hypertension, Japan"),
            C(id=KALISCH, label="Kalisch Ellett et al., J Clin Pharm Ther 2016",
              text="Starting an ACE inhibitor plus diuretic combination product had the highest risk of dehydration or heat-illness admission (ratio 2.79).",
              plain="Starting an ACE inhibitor with a water pill was linked to about 3 times the risk of a dehydration or heat-illness admission.",
              num=2.79, ntype="ratio", tier=2, direction="supports_harm", pop="subgroup_in_heat", population="Australian veterans"),
            C(id="PMID:27992525", label="PLoS One 2016 (Israel)",
              text="Older inpatients on thiazide and/or ACE inhibitor/ARB: higher daily temperature was associated with a creatinine increase, significant in the dual-treatment group.",
              plain="Hotter days were linked to worse kidney tests in older adults on these medicines.",
              tier=2, direction="supports_harm", pop="subgroup_in_heat", population="hospitalized adults 65+"),
            C(id=MANGONI, label="Mangoni et al. 2017 (triple whammy)",
              text="Diuretic + NSAID + ACEi/ARB did not predict in-hospital AKI during heat waves (OR 1.02, 95% CI 0.21-2.97).",
              plain="In one hospital study, this three-medicine combination did not predict kidney injury during heat waves.",
              num=1.02, ntype="OR", ci=(0.21, 2.97), tier=2, direction="null", pop="subgroup_in_heat", population="older medical inpatients"),
        ],
        alternatives=[],
        timeline=[
            ("before_summer", "Review combinations with diuretics and NSAIDs; agree a sick-day / heat-day plan and who to call.", ["prescriber", "pharmacist"], "some", "Kalisch Ellett 2016; Harley 2026"),
            ("during", "Check in about dizziness, falls, low urine, vomiting or diarrhea.", ["care_coordinator"], "some", "guidance; mechanism"),
            ("after", "Kidney function and potassium check for flagged patients (clinician-approved).", ["prescriber"], "some", "PLoS One 2016 (creatinine)"),
        ],
        messages=[("heat_forecast",
                   "Heat warning for your blood-pressure medicine: in hot weather, if you lose a lot of fluid, it can lower your blood pressure and strain your kidneys. Watch for dizziness when you stand, fainting, very little urine, vomiting or diarrhea. Do not stop it on your own; stay somewhere cool. " + TALK_EN,
                   "Aviso de calor por su medicina para la presión: con el calor, si pierde mucho líquido, puede bajarle la presión y forzar sus riñones. Fíjese si se marea al pararse, se desmaya, orina muy poco, o tiene vómitos o diarrea. No la deje por su cuenta; quédese en un lugar fresco. " + TALK_ES)],
        label_line="With dehydration in heat, ACE inhibitors/ARBs can drop blood pressure and kidney function, especially with a diuretic or NSAID.",
        gaps=["Whether the drug itself causes the extra risk, or the people who take it differ, is not settled (Harley 2026)."],
        extra_unverified=[],
    ),
    # ------------------------------------------------------------------ SGLT2
    C(
        id="sglt2", display="SGLT2 inhibitors", plain="Diabetes/heart medicines that make you pass sugar in urine (SGLT2 inhibitors)", class_label="SGLT2 inhibitor",
        examples=["empagliflozin", "dapagliflozin", "canagliflozin"], ingredients=["empagliflozin", "dapagliflozin", "canagliflozin"],
        master_rows=["R37"], faers_class="SGLT2 inhibitors", label_class="SGLT2 inhibitors", system_group="sglt2",
        storage_profile=None, severity="High",
        buckets=[("hold_or_substitute", True, "Sick-day rules already pause these drugs when people cannot keep fluids up; whether heat days count is untested (no guidance names them)."),
                 ("monitor", False, "Dehydration, dizziness and ketoacidosis symptoms.")],
        mechanism_groups=["fluid_salt_loss", "kidney_stress", "blood_sugar"],
        heat_stack=_hs(NO, ("yes", "Sugar in the urine pulls water and salt with it."), ("possible", "Volume loss can strain the kidneys."), ("possible", "Lower blood volume can lower blood pressure."),
                       [("blood sugar", "Ketoacidosis can occur even with normal blood sugar (euglycemic DKA) when dehydrated or ill.")]),
        compass=C(arrow="up", meaning="Acts stronger in heat: urine water loss adds to sweating.",
                  mechanism="Glucose in the urine drags water and salt -> volume depletion; dehydration raises ketoacidosis risk.",
                  triggers=["forecast heat", "not eating or drinking", "vomiting/diarrhea", "adding a diuretic"],
                  monitor=["dizziness, thirst, low urine", "nausea, vomiting, abdominal pain, fast breathing (ketoacidosis)"]),
        prescribers=["endocrinology", "cardiology", "nephrology", "primary care"], higher_risk=["older adults", "people also on diuretics", "heart failure"], pediatric=None,
        causal_factor=0.75, causal_note="Mechanism only: no heat study of SGLT2 inhibitors was found.",
        claims=[],
        alternatives=[],
        timeline=[
            ("before_summer", "Teach sick-day rules and ask the prescriber whether they apply on extreme-heat days; review diuretic co-prescription.", ["prescriber", "pharmacist"], "early_signs", "mechanism only; no guidance names SGLT2 inhibitors"),
            ("during", "Check in about vomiting, not drinking, dizziness or abdominal pain.", ["care_coordinator"], "early_signs", "mechanism only"),
        ],
        messages=[("heat_forecast",
                   "Heat warning for your diabetes or heart medicine: in hot weather it can make you lose extra water through your urine. Watch for dizziness, being very thirsty, passing little urine, stomach pain or vomiting. If you cannot eat or drink, call your care team. " + TALK_EN,
                   "Aviso de calor por su medicina para la diabetes o el corazón: con el calor puede hacerle perder más agua por la orina. Fíjese si se marea, tiene mucha sed, orina poco, le duele el estómago o vomita. Si no puede comer ni beber, llame a su equipo médico. " + TALK_ES)],
        label_line="SGLT2 inhibitors add urine water loss to sweating; no heat guidance anywhere names them.",
        gaps=["None of the 13 guidance documents names SGLT2 inhibitors.", "No study combines heat, SGLT2 inhibitors and ketoacidosis."],
        extra_unverified=[],
    ),
    # ------------------------------------------------------------------ insulin
    C(
        id="insulin", display="Insulin (incl. pumps)", plain="Insulin", class_label="Insulin",
        examples=["insulin glargine", "insulin lispro", "insulin pumps"], ingredients=["insulin glargine", "insulin lispro", "insulin aspart", "insulin human"],
        master_rows=["R44", "R47", "R48", "R49"], faers_class="insulin (incl. pumps)", label_class="insulin (incl. pumps)", system_group="insulin",
        storage_profile="insulin_pen", severity="High",
        buckets=[("storage", True, "Keep in-use insulin out of hot cars and direct sun; pens tolerated 37 °C for weeks in trials, but higher heat and pumps in sun are a problem."),
                 ("monitor", False, "Heat speeds absorption from the skin, so blood sugar can drop; check glucose more often on hot days (NYC HAN #23)."),
                 ("adjust_dose", False, "Any change is decided with the diabetes team; no dose numbers are given here.")],
        mechanism_groups=["faster_absorption", "blood_sugar", "storage_sensitive"],
        heat_stack=_hs(NO, NO, NO, NO, [("absorption", "Warm skin absorbs injected insulin faster -> low blood sugar."), ("drug integrity", "Very hot storage can reduce potency; pumps in sun can overheat.")]),
        compass=C(arrow="depends", meaning="Depends: heat on the skin makes insulin act faster (↑); insulin left in extreme heat can weaken (↓).",
                  mechanism="Skin blood flow rises in heat -> faster absorption from the injection site; prolonged high storage temperature degrades insulin.",
                  triggers=["hot bath/sauna or sun on the injection site", "exercise in heat", "insulin left in a hot car or pump in direct sun"],
                  monitor=["glucose more often on hot days", "signs of low blood sugar", "unexplained high sugars (possible heat-damaged insulin)"]),
        prescribers=["endocrinology", "primary care", "pediatrics"], higher_risk=["type 1 diabetes", "pump users", "people without a fridge or power"],
        pediatric="Children with type 1 diabetes: caregivers manage storage and hypoglycemia checks on hot days.",
        causal_factor=1.0, causal_note="Absorption change is shown in human PK studies; CHANGE here concerns handling and monitoring, not the molecule.",
        claims=[
            C(id=VANAKOSKI, label="Vanakoski & Seppälä, Clin Pharmacokinet 1998 (review)",
              text="Review: external heating enhances systemic absorption of transdermally and subcutaneously given drugs including insulin; oral drugs change little.",
              plain="Heat on the skin makes injected insulin get into the blood faster.",
              tier=3, direction="supports_harm", pop="lab_heat_healthy", population="small PK studies"),
            C(id="PMCID:PMC1601709", label="Koivisto, BMJ 1980",
              text="Sauna-induced acceleration in insulin absorption from a subcutaneous injection site (small study).",
              plain="A sauna made injected insulin absorb faster.", tier=3, direction="supports_harm", pop="lab_heat_healthy", population="people with insulin-treated diabetes (small study)"),
            C(id="PMID:36585035", label="Kongmalai et al., BMJ Open Diabetes Res Care 2022 (RCT)",
              text="Randomized crossover trial: glargine pens kept at 37 °C for 21 days gave the same glucose control as refrigerated pens.",
              plain="Insulin pens kept at body temperature for 3 weeks still worked the same.",
              num=37, ntype="degC_storage", tier=1, direction="null", pop="patients_in_heat", population="adults with type 2 diabetes"),
            C(id="PMID:19797814", label="Vimalavathini & Gitanjali 2009",
              text="Insulin stored at 32 and 37 °C lost 14-18% potency by day 28 (rabbit bioassay).",
              plain="Insulin kept warm for 4 weeks lost some strength in an animal test.",
              tier=6, direction="supports_harm", pop="mechanism", population="laboratory / rabbit"),
            C(id="PMID:27789976", label="Vereshchetin et al., Med Devices 2016 (industry-sponsored)",
              text="A rechargeable insulin pump in a 35 °C chamber rose 4.4 °C, above the 37 °C insulin storage limit.",
              plain="An insulin pump can heat up above the safe limit for insulin in a hot room.",
              num=4.4, ntype="degC_rise", tier=6, direction="supports_harm", pop="mechanism", population="bench test"),
        ],
        alternatives=[],
        timeline=[
            ("before_summer", "Teach heat storage (no hot cars, no direct sun on pumps); plan for power outages and a cool bag.", ["pharmacist", "prescriber"], "some", "storage studies; CDC/NYC/HC/ANSM/WHO storage guidance"),
            ("72h_before", "Remind to check glucose more often and carry fast sugar.", ["care_coordinator"], "some", "NYC HAN #23; PK studies"),
            ("during", "Check glucose more often; keep insulin cool; watch for lows after heat on the injection site.", ["patient", "caregiver"], "some", "Vanakoski 1998; Koivisto 1980"),
            ("after", "Replace insulin that was exposed to extreme heat; review lows.", ["pharmacist"], "some", "drug_storage_profiles.json advice tiers"),
        ],
        messages=[("heat_forecast",
                   "Heat warning for insulin: in hot weather insulin can work faster when your skin is hot, so your sugar can drop. Check your sugar more often, keep fast sugar with you, and keep your insulin out of hot cars and direct sun. " + TALK_EN,
                   "Aviso de calor por la insulina: con el calor la insulina puede actuar más rápido cuando su piel está caliente, y su azúcar puede bajar. Mídase el azúcar más seguido, lleve azúcar rápida con usted y no deje la insulina en un carro caliente ni al sol. " + TALK_ES),
                  ("storage",
                   "Keep your insulin cool: not in a hot car, not in direct sun. If it got very hot, ask your pharmacist whether to replace it. " + TALK_EN,
                   "Guarde su insulina en un lugar fresco: no en un carro caliente ni al sol. Si se calentó mucho, pregunte a su farmacéutico si debe reemplazarla. " + TALK_ES)],
        label_line="Heat speeds insulin absorption (lows) and extreme heat can weaken stored insulin: check glucose more often and store cool.",
        gaps=["Absorption studies are small and older; the effect likely differs by formulation.", "Pens tolerate 37 °C for weeks; data above 37 °C are animal or bench only."],
        extra_unverified=[],
    ),
    # ------------------------------------------------------------------ metformin
    C(
        id="metformin", display="Metformin", plain="Metformin", class_label="Biguanide (diabetes)",
        examples=["metformin"], ingredients=["metformin"],
        master_rows=["R35"], faers_class="metformin", label_class="metformin", system_group="metformin",
        storage_profile=None, severity="High",
        buckets=[("hold_or_substitute", True, "Sick-day guidance pauses metformin when dehydrated; dehydration-related kidney injury can lead to lactic acidosis. Not studied in heat."),
                 ("monitor", False, "Vomiting, diarrhea, not drinking, kidney function.")],
        mechanism_groups=["kidney_cleared_buildup"],
        heat_stack=_hs(NO, ("possible", "Indirect: dehydration matters because of the kidneys."), ("yes", "Kidney-cleared; builds up if dehydration injures the kidneys."), NO),
        compass=C(arrow="up", meaning="Can act stronger in heat: builds up if dehydration injures the kidneys.",
                  mechanism="Dehydration -> acute kidney injury -> metformin accumulation -> lactic acidosis (rare).",
                  triggers=["severe dehydration", "vomiting/diarrhea", "acute illness in heat"],
                  monitor=["vomiting, not drinking", "kidney function (clinician decides)", "unusual tiredness, fast breathing, stomach pain"]),
        prescribers=["primary care", "endocrinology"], higher_risk=["chronic kidney disease", "older adults"], pediatric=None,
        causal_factor=0.75, causal_note="Pathway is extrapolated from dehydration/AKI case reports; no heat-specific study.",
        claims=[
            C(id="PMCID:PMC6424540", label="Case report (PMC6424540)",
              text="Case report: metformin-associated severe lactic acidosis in the setting of acute kidney injury (not heat-specific).",
              plain="A person had a rare serious reaction to metformin after kidney injury.",
              tier=5, direction="supports_harm", pop="indirect", population="single case, not in heat"),
            C(id="GUIDANCE:VIC", guidance_drug="metformin", layer="guidance", label="Victoria Department of Health, information for clinicians (2024)",
              text="Victoria lists metformin among drugs with increased toxicity in dehydration because of a narrow therapeutic index.",
              plain="Australian heat guidance lists metformin as riskier when dehydrated.", tier=7, direction="supports_harm", pop="mechanism", population="guidance"),
        ],
        alternatives=[],
        timeline=[
            ("before_summer", "Teach sick-day rules; check kidney function is recent.", ["prescriber", "pharmacist"], "early_signs", "case reports; Victoria guidance"),
            ("during", "Ask about vomiting, diarrhea or not drinking.", ["care_coordinator"], "early_signs", "mechanism"),
        ],
        messages=[("heat_forecast",
                   "Heat warning for metformin: if you get very dehydrated in hot weather, your kidneys can be strained and metformin can build up. If you are vomiting, have diarrhea or cannot drink, call your care team. " + TALK_EN,
                   "Aviso de calor por la metformina: si se deshidrata mucho con el calor, sus riñones pueden forzarse y la metformina puede acumularse. Si vomita, tiene diarrea o no puede beber, llame a su equipo médico. " + TALK_ES)],
        label_line="Metformin can build up if heat dehydration injures the kidneys: follow sick-day rules.",
        gaps=["No heat-specific study; only dehydration/AKI case reports.", "Only 2 of 8 jurisdictions name metformin."],
        extra_unverified=[],
    ),
    # ------------------------------------------------------------------ antipsychotics
    C(
        id="antipsychotics_clozapine", display="Antipsychotics (incl. clozapine)", plain="Antipsychotic medicines", class_label="Antipsychotic",
        examples=["haloperidol", "clozapine", "olanzapine", "quetiapine", "risperidone", "aripiprazole"],
        ingredients=["haloperidol", "clozapine", "olanzapine", "quetiapine", "risperidone", "aripiprazole"],
        master_rows=["R07", "R08", "R09", "R10"], faers_class="antipsychotics", label_class="antipsychotics", system_group="antipsychotics",
        storage_profile=None, severity="High",
        buckets=[("monitor", True, "The illness, poverty and isolation carry much of the risk: check-ins and cooling access during heat (FLAG high)."),
                 ("hold_or_substitute", False, "Review combination therapy (2+ antipsychotics) in spring; never stop abruptly (CHANGE moderate).")],
        mechanism_groups=["thermostat", "sweat_blocked", "sedation_awareness"],
        heat_stack=_hs(("possible", "Some (e.g. clozapine, olanzapine, quetiapine) are anticholinergic and reduce sweating."), NO, NO,
                       ("possible", "Some lower blood pressure on standing."),
                       [("thermostat", "Dopamine blockade disturbs the brain's temperature control (overheating in heat, also hypothermia)."),
                        ("awareness", "Sedation and illness reduce thirst and awareness of heat.")]),
        compass=C(arrow="depends", meaning="Depends: the drug blunts temperature control, so the body can overheat in heat (and cool too much in cold).",
                  mechanism="Central thermoregulation impaired (dopamine blockade) plus anticholinergic sweat reduction for some agents.",
                  triggers=["forecast heat", "outdoor work or exertion", "adding an anticholinergic (e.g. benztropine)", "combination therapy"],
                  monitor=["confusion, very high temperature, hot dry skin", "fever on clozapine (can be benign or serious)", "whether the person has cooling and someone checking"]),
        prescribers=["psychiatry", "primary care"], higher_risk=["schizophrenia", "older adults", "income assistance / poverty", "living alone", "2+ antipsychotics"], pediatric=None,
        causal_factor=0.5, causal_note="A within-person Japanese study found heat-illness risk tracked the illness, not the prescription (confounding by indication); specific agents and combinations still stand out in BC.",
        flag_note="Spec §6.3: FLAG high, CHANGE moderate. Strong evidence that these patients are at risk; weaker evidence that changing the drug lowers it.",
        claims=[
            C(id=CHEN, label="Chen et al., Sci Rep 2025 (2021 BC heat dome)",
              text="Among people with schizophrenia, dispensation of any antipsychotic was associated with death during the 2021 extreme heat event (OR 2.43, 95% CI 1.52-4.01), driven by haloperidol, clozapine and zuclopenthixol.",
              plain="During the 2021 BC heat dome, people with schizophrenia taking an antipsychotic had about 2½ times the odds of dying.",
              num=2.43, ntype="OR", ci=(1.52, 4.01), tier=2, direction="supports_harm", pop="patients_in_heat", population="people with schizophrenia, British Columbia"),
            C(id=CHEN, label="Chen et al., Sci Rep 2025 (2021 BC heat dome)",
              text="Two or more antipsychotics in combination: OR 4.05 (95% CI 2.41-6.98) for death during the extreme heat event.",
              plain="Taking two or more antipsychotics was linked to about 4 times the odds of dying in the heat dome.",
              num=4.05, ntype="OR", ci=(2.41, 6.98), tier=2, direction="supports_harm", pop="patients_in_heat", population="people with schizophrenia, British Columbia"),
            C(id=MARTIN_LATRY, label="Martin-Latry et al., Eur Psychiatry 2007",
              text="2003 French heat wave case-control: antipsychotics OR 4.6 (95% CI 1.9-11.2) for heat-related admission.",
              plain="In the 2003 French heat wave, people hospitalized for heat illness had about 4½ times the odds of taking antipsychotics.",
              num=4.6, ntype="OR", ci=(1.9, 11.2), tier=2, direction="supports_harm", pop="patients_in_heat", population="older adults, Bordeaux"),
            C(id=LAYTON, label="Layton et al., PLoS One 2020",
              text="Medicare SCCS: antipsychotics raised heat-related hospitalization across the summer (RR 1.37).",
              plain="Older adults had about 37% more heat-related hospital stays while on antipsychotics.",
              num=1.37, ntype="RR", tier=2, direction="supports_harm", pop="patients_in_heat", population="US Medicare 65+"),
            C(id=WONG, label="Wong et al., Psychol Med 2024 (Japan, within-person)",
              text="Self-controlled case series in severe mental illness: heatwave heat-illness IRR 1.48 when prescribed antipsychotics vs 1.45 when not (p interaction 0.53): no added drug effect.",
              plain="In one careful Japanese study, heat risk was about the same whether or not people were taking antipsychotics: the illness, not the drug, carried the risk.",
              num=1.48, ntype="IRR", tier=2, direction="null", pop="patients_in_heat", population="people with severe mental illness, Japan"),
            C(id="PMID:18025545", label="Kao & Kelly, Can J Clin Pharmacol 2007",
              text="Case report: fatal exertional heat stroke in a 36-year-old outdoor worker taking zuclopenthixol, quetiapine and benztropine.",
              plain="A young outdoor worker on several of these medicines died of heat stroke.",
              tier=5, direction="supports_harm", pop="subgroup_in_heat", population="outdoor worker"),
            C(id="DOI:10.1345/aph.1G130", label="Kwok & Chan, Ann Pharmacother 2005",
              text="Case report: recurrent heat-related illnesses during antipsychotic treatment.",
              plain="One person had heat illness more than once while on antipsychotics.", tier=5, direction="supports_harm", pop="subgroup_in_heat", population="single case"),
        ],
        alternatives=[
            C(name="Reduce combination therapy toward a single antipsychotic where clinically possible (spring review)",
              why="Two or more antipsychotics: OR 4.05 vs any antipsychotic OR 2.43 for heat-dome death (Chen 2025).",
              lost="Symptom control; relapse risk. Only psychiatry can weigh this.",
              heat_studied=True, heat_label="studied in heat (one population study)",
              source_id=CHEN, source_label="Chen et al., Sci Rep 2025", source_url="https://doi.org/10.1038/s41598-025-17591-0"),
            C(name="Agents without the BC excess (e.g. aripiprazole) when switching is already being considered",
              why="In the BC heat dome, the excess was driven by haloperidol, clozapine and zuclopenthixol; aripiprazole was not elevated (per-drug estimate in full text, not abstract-verified).",
              lost="Efficacy and tolerability differ; clozapine is often irreplaceable for treatment-resistant illness.",
              heat_studied=True, heat_label="one study; per-drug finding from full text, not machine-verified",
              source_id=CHEN, source_label="Chen et al., Sci Rep 2025", source_url="https://doi.org/10.1038/s41598-025-17591-0"),
        ],
        timeline=[
            ("before_summer", "Review combination therapy and anticholinergic add-ons; check AC at home; enroll in check-ins and name a trusted contact; HEAP cooling assistance if no AC.", ["prescriber", "care_coordinator", "health_system"], "strong", "Chen 2025; Martin-Latry 2007; Cincinnati 1999 (AC protective)"),
            ("72h_before", "Call high-FLAG patients; confirm a cooling place and check-in times.", ["care_coordinator"], "strong", "FLAG: Chen 2025; Bark 1998 (prevention worked)"),
            ("during", "Daily check-ins; silence escalates to the trusted contact, then a human decides on a wellness check.", ["care_coordinator", "caregiver"], "some", "spec §4.4"),
            ("after", "Follow up anyone who missed check-ins; review the medication plan for the next summer.", ["prescriber", "care_coordinator"], "some", "spec §4.0"),
        ],
        messages=[("heat_forecast",
                   "Heat warning for your medicine: in hot weather some medicines like yours can make it harder for your body to control its temperature. Watch for feeling confused, very hot, or not sweating. Keep taking your medicine, go somewhere cool with other people around, and answer our check-in. " + TALK_EN,
                   "Aviso de calor por su medicina: con el calor algunas medicinas como la suya pueden hacer más difícil que su cuerpo controle la temperatura. Fíjese si se siente confundido, muy caliente o no suda. Siga tomando su medicina, vaya a un lugar fresco donde haya otras personas y responda a nuestro mensaje. " + TALK_ES)],
        label_line="Check on this person during heat: illness, isolation and some antipsychotics raise risk; review combination therapy in spring; never stop abruptly.",
        gaps=["Per-drug estimates (haloperidol, clozapine, aripiprazole) are in full text only; not machine-verified.",
              "No study shows heat triggers NMS."],
        extra_unverified=[],
    ),
    # ------------------------------------------------------------------ SSRIs
    C(
        id="ssri", display="SSRIs", plain="Antidepressants (SSRIs)", class_label="Selective serotonin reuptake inhibitor",
        examples=["sertraline", "citalopram", "escitalopram", "fluoxetine", "paroxetine"], ingredients=["sertraline", "citalopram", "escitalopram", "fluoxetine", "paroxetine"],
        master_rows=["R17", "R30"], faers_class="SSRIs", label_class="SSRIs", system_group="ssris",
        storage_profile=None, severity="Moderate",
        buckets=[("monitor", True, "Low sodium (especially with a thiazide) and possible effects on sweating; risk tracks the illness in within-person data.")],
        mechanism_groups=["low_sodium", "thermostat"],
        heat_stack=_hs(("possible", "Effect on sweating is disputed (CDC's own narrative and table disagree)."), ("yes", "Can lower blood sodium (SIADH), worse with thiazides and heavy water intake."), NO, NO,
                       [("thermostat", "Serotonergic drugs act on central temperature control.")]),
        compass=C(arrow="depends", meaning="Depends: mainly a low-sodium risk; effect on cooling is uncertain.",
                  mechanism="SIADH-type low sodium + possible central thermoregulation effects.",
                  triggers=["forecast heat", "drinking large amounts of plain water", "thiazide co-prescription"],
                  monitor=["sodium in older adults (clinician decides)", "confusion, headache, falls"]),
        prescribers=["primary care", "psychiatry"], higher_risk=["older adults", "people also on thiazides"], pediatric=None,
        causal_factor=0.5, causal_note="Within-person Japanese data: heat risk in depression was similar whether or not antidepressants were prescribed.",
        claims=[
            C(id=KALISCH, label="Kalisch Ellett et al., J Clin Pharm Ther 2016",
              text="Starting SSRIs: ratio 1.17 for admission with dehydration or heat-related illness (lowest of the significant classes).",
              plain="Starting an SSRI was linked to slightly more dehydration or heat-illness admissions.",
              num=1.17, ntype="ratio", tier=2, direction="supports_harm", pop="subgroup_in_heat", population="Australian veterans"),
            C(id=WONG, label="Wong et al., Psychol Med 2024 (Japan, within-person)",
              text="Depression cohort: heatwave heat-illness IRR 1.54 when prescribed antidepressants vs 1.64 when not (p interaction 0.33): no added drug effect.",
              plain="In one careful study, heat risk was about the same with or without antidepressants.",
              num=1.54, ntype="IRR", tier=2, direction="null", pop="patients_in_heat", population="people with depression, Japan"),
            C(id=HOSPERS, label="Hospers et al., eClinicalMedicine 2024",
              text="Heat-stress trials: antidepressants did not alter core temperature responses.",
              plain="In lab heat tests, antidepressants did not raise body temperature.", tier=1, direction="null", pop="lab_heat_healthy", population="healthy young adults"),
            C(id="DOI:10.3390/ijerph14070827", label="IJERPH 2017",
              text="Drug-induced hyponatremia risk increased during high temperatures.",
              plain="Low blood salt from medicines became more common in hot weather.", tier=2, direction="supports_harm", pop="subgroup_in_heat", population="hyponatremia cases"),
        ],
        alternatives=[],
        timeline=[
            ("before_summer", "Flag SSRI + thiazide combinations in older adults; individual fluid advice.", ["prescriber", "pharmacist"], "some", "IJERPH 2017; Health Canada"),
            ("during", "Check in about confusion or falls.", ["care_coordinator"], "early_signs", "mechanism"),
        ],
        messages=[("heat_forecast",
                   "Heat warning for your antidepressant: in hot weather it can lower the salt in your blood, especially with a water pill or if you drink a lot of plain water. Watch for confusion, headache or falls. Keep taking it and stay somewhere cool. " + TALK_EN,
                   "Aviso de calor por su antidepresivo: con el calor puede bajarle la sal en la sangre, sobre todo si también toma una pastilla para orinar o mucha agua sola. Fíjese si tiene confusión, dolor de cabeza o se cae. Siga tomándolo y quédese en un lugar fresco. " + TALK_ES)],
        label_line="SSRIs: watch sodium in older adults during heat, especially with a thiazide; the drug itself adds little heat-illness risk in within-person data.",
        gaps=["French aOR 1.71 for heat death (Nordon 2009) has no verified ID.", "Guidance disagrees on whether SSRIs increase or decrease sweating."],
        extra_unverified=[],
    ),
    # ------------------------------------------------------------------ topiramate / zonisamide
    C(
        id="topiramate_zonisamide", display="Topiramate / zonisamide", plain="Seizure and migraine medicines that reduce sweating (topiramate, zonisamide)", class_label="Antiepileptic (carbonic anhydrase inhibition)",
        examples=["topiramate", "zonisamide"], ingredients=["topiramate", "zonisamide"],
        master_rows=["R04", "R05"], faers_class="topiramate/zonisamide", label_class="topiramate/zonisamide", system_group="topiramate_zonisamide",
        storage_profile=None, severity="High",
        buckets=[("hold_or_substitute", True, "Reduced sweating is often silent until heat or exertion; neurology may review the choice before summer, especially for children and athletes."),
                 ("monitor", False, "Fever or overheating with exertion; decreased sweating.")],
        mechanism_groups=["sweat_blocked"],
        heat_stack=_hs(("yes", "Reduces sweating (oligohidrosis), often without symptoms until heat or exercise."), NO, NO, NO),
        compass=C(arrow="up", meaning="Effect matters more in heat: the body cannot sweat enough to cool.",
                  mechanism="Carbonic-anhydrase inhibition in sweat glands -> oligohidrosis -> hyperthermia with heat or exertion.",
                  triggers=["forecast heat", "sports or outdoor exertion", "children in summer"],
                  monitor=["not sweating during exercise", "flushed hot skin, fever with exertion", "confusion"]),
        prescribers=["neurology", "pediatrics", "headache medicine", "obesity medicine"], higher_risk=["children", "athletes and outdoor workers"],
        pediatric="All US zonisamide oligohidrosis/fever cases in the FDA series were age 18 or under; topiramate pilot study found low sweat output in children.",
        causal_factor=1.0, causal_note="Mechanism shown: sweat tests normalized after stopping topiramate in a child.",
        claims=[
            C(id="PMID:12760427", label="Ben-Zeev et al., J Child Neurol 2003",
              text="A child on topiramate had recurrent hyperthermia with heat and activity; sweat output was 5% of age-matched controls and normalized after stopping the drug; a pilot study followed.",
              plain="A child on topiramate could barely sweat; sweating came back after the medicine was stopped.",
              num=5, ntype="% of control sweat", tier=4, direction="supports_harm", pop="subgroup_in_heat", population="children and young adults"),
            C(id="PMID:12770670", label="Knudsen et al., 2003 (FDA AERS series)",
              text="Six US cases of zonisamide-associated oligohydrosis and/or fever, all in patients 18 or younger.",
              plain="In the US, every reported case of zonisamide stopping sweating was in a child or teen.",
              tier=4, direction="supports_harm", pop="subgroup_in_heat", population="children"),
            C(id="PMID:15519129", label="Low et al., 2004",
              text="Zonisamide: 13 US oligohidrosis/hyperthermia events in 3 years, an estimated 1 case per 4590 patient-years, mostly in children, typically in summer.",
              plain="Rare, but most cases happen in children in the summer.",
              num=4590, ntype="patient-years per case", tier=4, direction="supports_harm", pop="subgroup_in_heat", population="mostly children"),
            C(id="PMID:23993866", label="Fatal heat stroke associated with topiramate therapy",
              text="Case report: a 40-year-old man on topiramate found unresponsive with rectal temperature 43.2 °C, hot dry skin; fatal heat stroke.",
              plain="An adult on topiramate died of heat stroke.", tier=5, direction="supports_harm", pop="subgroup_in_heat", population="adult"),
            C(id="PMID:15795554", label="Severe topiramate-associated hyperthermia",
              text="Case report: severe topiramate-associated hyperthermia resulting in persistent neurological dysfunction.",
              plain="An adult on topiramate had lasting brain injury from overheating.", tier=5, direction="supports_harm", pop="subgroup_in_heat", population="adult"),
        ],
        alternatives=[],
        timeline=[
            ("before_summer", "Neurology reviews the choice for children and athletes; teach families to watch for not sweating with exercise.", ["prescriber", "caregiver"], "some", "case series; Health Canada pediatric detail"),
            ("during", "Limit exertion in heat; cool down early; check for flushed dry skin.", ["patient", "caregiver"], "some", "case series"),
        ],
        messages=[("heat_forecast",
                   "Heat warning for topiramate or zonisamide: in hot weather these medicines can stop you or your child from sweating enough, so the body overheats, especially during sports. Watch for hot, red, dry skin or fever after activity. Keep taking it, take breaks in the shade or indoors, and stay cool. " + TALK_EN,
                   "Aviso de calor por el topiramato o la zonisamida: con el calor estas medicinas pueden hacer que usted o su hijo no suden lo suficiente y el cuerpo se sobrecaliente, sobre todo al hacer deporte. Fíjese si la piel está caliente, roja y seca o si hay fiebre después de la actividad. Siga tomándola, descanse a la sombra o adentro y manténgase fresco. " + TALK_ES)],
        label_line="Topiramate and zonisamide can silently stop sweating, especially in children: limit exertion in heat and watch for hot dry skin.",
        gaps=["No adult-specific heat guidance found.", "No cited source names a specific lower-heat-risk anticonvulsant; alternatives left to neurology."],
        extra_unverified=[],
    ),
    # ------------------------------------------------------------------ ADHD stimulants
    C(
        id="adhd_stimulants", display="ADHD stimulants", plain="ADHD stimulant medicines", class_label="Central nervous system stimulant",
        examples=["methylphenidate", "amphetamine", "lisdexamfetamine"], ingredients=["methylphenidate", "amphetamine", "lisdexamfetamine"],
        master_rows=["R14"], faers_class="ADHD stimulants", label_class="ADHD stimulants", system_group="adhd_stimulants",
        storage_profile=None, severity="High",
        buckets=[("monitor", True, "Extra heat production and blunted fatigue cues during exertion in heat, especially teen athletes and new recruits.")],
        mechanism_groups=["heat_production"],
        heat_stack=_hs(NO, NO, NO, ("possible", "Raises heart rate and blood pressure."), [("heat production", "Increases metabolic heat and may mask fatigue during exertion.")]),
        compass=C(arrow="up", meaning="Effect matters more in heat: more body heat and less sense of fatigue during exertion.",
                  mechanism="Sympathomimetic: increased heat production, vasoconstriction, masked fatigue.",
                  triggers=["sports or training in heat", "outdoor work"],
                  monitor=["dizziness, headache, confusion during exertion", "very high temperature"]),
        prescribers=["pediatrics", "psychiatry", "primary care"], higher_risk=["teen athletes", "military recruits"],
        pediatric="Teen athletes on stimulants: coaches and parents should plan breaks, shade and fluids on hot practice days.",
        causal_factor=0.75, causal_note="Population signal for mild heat illness only (recruits); severe outcomes are case reports.",
        claims=[
            C(id="PMID:29613996", label="Nelson et al., Med Sci Sports Exerc 2018 (US Army enlistees)",
              text="In 238,168 new soldiers, the odds of mild heat illness increased with methylphenidate stimulants (also NSAIDs and opioids).",
              plain="New soldiers taking stimulant medicine had more mild heat illness.",
              tier=2, direction="supports_harm", pop="subgroup_in_heat", population="US Army enlistees"),
            C(id="PMID:25469604", label="Case report (fatal heat shock)",
              text="Case report: fatal complications of exertional heat stroke in a stimulant user.",
              plain="A rare fatal case of heat stroke in someone on a stimulant.", tier=5, direction="supports_harm", pop="subgroup_in_heat", population="single case"),
        ],
        alternatives=[],
        timeline=[
            ("before_summer", "Talk with families and athletes about training in heat (breaks, shade, cooling).", ["prescriber", "caregiver"], "early_signs", "Nelson 2018"),
            ("during", "On hot practice days, plan breaks and stop if dizzy or confused.", ["patient", "caregiver"], "early_signs", "Nelson 2018"),
        ],
        messages=[("heat_forecast",
                   "Heat warning for your ADHD medicine: in hot weather it can make your body make more heat and make it harder to notice you are overheating during sports. Take breaks in the shade, cool down, and stop if you feel dizzy or confused. " + TALK_EN,
                   "Aviso de calor por su medicina para el TDAH: con el calor puede hacer que su cuerpo produzca más calor y que le cueste notar que se está sobrecalentando al hacer deporte. Descanse a la sombra, refrésquese y pare si se marea o se siente confundido. " + TALK_ES)],
        label_line="Stimulants add body heat and mask fatigue: plan breaks for athletes and outdoor workers on hot days.",
        gaps=["Stimulant labels do not mention heat stroke.", "No pediatric cohort of stimulants and heat illness."],
        extra_unverified=[],
    ),
    # ------------------------------------------------------------------ beta blockers
    C(
        id="beta_blockers", display="Beta blockers", plain="Heart and blood-pressure medicines (beta blockers)", class_label="Beta-adrenergic blocker",
        examples=["metoprolol", "propranolol", "atenolol", "carvedilol"], ingredients=["metoprolol", "propranolol", "atenolol", "carvedilol"],
        master_rows=["R12", "R13"], faers_class="beta blockers", label_class="beta blockers", system_group="beta_blockers",
        storage_profile=None, severity="Moderate",
        buckets=[("monitor", True, "Small core-temperature rise with non-selective agents; blunted racing-heart warning sign; listed everywhere but no guidance gives an action.")],
        mechanism_groups=["bp_drop", "sedation_awareness"],
        heat_stack=_hs(("possible", "Limits skin blood flow and the heart-rate response that carries heat to the skin."), NO, NO,
                       ("yes", "Limits the heart's ability to keep blood pressure up when blood vessels widen in heat."),
                       [("awareness", "Blunts the racing heart that signals heat stress or low blood sugar; breaks heart-rate-based wearable estimates.")]),
        compass=C(arrow="depends", meaning="Depends: small effect on cooling; mainly hides warning signs.",
                  mechanism="Reduced cardiac output and skin blood flow response; masked tachycardia.",
                  triggers=["forecast heat", "exertion"],
                  monitor=["dizziness, fainting", "do not rely on heart rate alone as a warning sign"]),
        prescribers=["cardiology", "primary care", "neurology"], higher_risk=["older adults", "heart failure"], pediatric=None,
        causal_factor=0.75, causal_note="Trial effect is small (+0.11 °C, non-selective); population data are null for hospitalization.",
        claims=[
            C(id=HOSPERS, label="Hospers et al., eClinicalMedicine 2024 (meta-analysis)",
              text="Heat-stress trials: non-selective beta-blockers raised core temperature by 0.11 °C (95% CI 0.02-0.19).",
              plain="In lab heat tests, some beta blockers raised body temperature a little.",
              num=0.11, ntype="degC", ci=(0.02, 0.19), tier=1, direction="supports_harm", pop="lab_heat_healthy", population="healthy young adults"),
            C(id=LAYTON, label="Layton et al., PLoS One 2020",
              text="Medicare SCCS: beta blockers were not meaningfully associated with heat-related hospitalization (null).",
              plain="In older adults, beta blockers were not linked to more heat-related hospital stays.",
              tier=2, direction="null", pop="patients_in_heat", population="US Medicare 65+"),
        ],
        alternatives=[],
        timeline=[
            ("before_summer", "No change suggested by evidence; teach that heart rate may not rise as a warning sign.", ["prescriber"], "early_signs", "Hospers 2024; Layton 2020"),
            ("during", "Ask about dizziness and fainting.", ["care_coordinator"], "early_signs", "mechanism"),
        ],
        messages=[("heat_forecast",
                   "Heat note for your beta blocker: in hot weather it can make dizziness more likely and can hide a racing heart, one of the body's warning signs. Stand up slowly, stay somewhere cool, and watch for dizziness or confusion. " + TALK_EN,
                   "Nota de calor por su betabloqueador: con el calor puede aumentar el mareo y ocultar el corazón acelerado, una de las señales de alarma del cuerpo. Levántese despacio, quédese en un lugar fresco y fíjese si se marea o se confunde. " + TALK_ES)],
        label_line="Beta blockers hide the racing-heart warning sign; their own effect on cooling is small.",
        gaps=["Listed by all 8 jurisdictions; none gives an action.", "Heart-rate-based wearables were never validated in these patients."],
        extra_unverified=[],
    ),
    # ------------------------------------------------------------------ opioid patches
    C(
        id="opioid_patches_fentanyl", display="Fentanyl / opioid patches", plain="Pain patches (fentanyl, buprenorphine)", class_label="Transdermal opioid",
        examples=["fentanyl patch", "buprenorphine patch"], ingredients=["fentanyl", "buprenorphine"],
        master_rows=["R52"], faers_class="fentanyl/opioid patches", label_class="fentanyl/opioid patches", system_group="opioids_fentanyl",
        storage_profile=None, severity="High",
        buckets=[("monitor", True, "Heat on the skin or fever increases absorption; watch for sleepiness and slow breathing (FDA boxed warning)."),
                 ("storage", False, "Keep the patch away from heat sources: heating pads, hot baths, saunas, direct sun."),
                 ("adjust_dose", False, "Heidelberg table: close monitoring and dose adjustment if needed, decided by the prescriber.")],
        mechanism_groups=["faster_absorption", "sedation_awareness"],
        heat_stack=_hs(NO, NO, NO, NO, [("absorption", "Warm skin releases more drug from the patch; the effect can outlast the heat."), ("awareness", "Sedation dulls awareness of overheating.")]),
        compass=C(arrow="up", meaning="Acts stronger in heat: warm skin releases more medicine from the patch.",
                  mechanism="Skin heating raises blood flow and patch release -> higher blood levels (dose dumping).",
                  triggers=["heat on the patch (sun, heating pad, sauna, hot bath)", "fever", "heat wave"],
                  monitor=["unusual sleepiness, slow or shallow breathing", "confusion", "patches peeling off with sweat"]),
        prescribers=["pain medicine", "palliative care", "primary care"], higher_risk=["older adults", "people living alone"], pediatric=None,
        causal_factor=1.0, causal_note="Mechanism shown in PK studies and in the FDA boxed warning; human heat cases are reports.",
        claims=[
            C(id=VANAKOSKI, label="Vanakoski & Seppälä, Clin Pharmacokinet 1998 (review)",
              text="External heating enhances systemic absorption of transdermally administered drugs, leading to higher plasma concentrations.",
              plain="Heat on the skin makes patches release more medicine.", tier=3, direction="supports_harm", pop="lab_heat_healthy", population="small PK studies"),
            C(id="DOI:10.1186/1752-1947-6-220", label="J Med Case Rep 2012",
              text="Case report: a 77-year-old woman developed severe opioid toxicity while sun tanning, likely from altered fentanyl patch function in heat, then hyperthermia and burns.",
              plain="An older woman on a fentanyl patch became unconscious after lying in the sun.",
              num=77, ntype="age", tier=5, direction="supports_harm", pop="subgroup_in_heat", population="older adult"),
            C(id="DOI:10.1097/PAF.0000000000000565", label="Am J Forensic Med Pathol 2020",
              text="Case report: death in a sauna associated with a transdermal fentanyl patch.",
              plain="A person with a fentanyl patch died in a sauna.", tier=5, direction="supports_harm", pop="subgroup_in_heat", population="single case"),
        ],
        alternatives=[],
        timeline=[
            ("before_summer", "Teach patch heat rules (no heating pads, saunas, hot baths, sun on the patch).", ["prescriber", "pharmacist"], "some", "FDA boxed warning; case reports"),
            ("during", "Check in about sleepiness and breathing; a caregiver should know the signs.", ["care_coordinator", "caregiver"], "some", "FDA boxed warning"),
        ],
        messages=[("heat_forecast",
                   "Heat warning for your pain patch: heat on your skin can make the patch release more medicine than usual. Keep the patch out of the sun and away from heating pads and hot baths. Watch for unusual sleepiness or slow breathing, and call 911 if someone cannot wake you. " + TALK_EN,
                   "Aviso de calor por su parche para el dolor: el calor en la piel puede hacer que el parche suelte más medicina de lo normal. No deje el parche al sol y aléjelo de almohadillas eléctricas y baños calientes. Fíjese si tiene mucho sueño o respira despacio, y que alguien llame al 911 si no lo pueden despertar. " + TALK_ES)],
        label_line="Heat on the skin makes opioid patches release more drug: keep patches away from heat and watch breathing.",
        gaps=["Only the Heidelberg table names opioid patches; no government heat guidance does.", "FAERS shows no heat-PT signal because harm is reported as overdose, not heat illness."],
        extra_unverified=[],
    ),
    # ------------------------------------------------------------------ epinephrine
    C(
        id="epinephrine_autoinjector", display="Epinephrine auto-injectors", plain="Epinephrine auto-injectors (for severe allergy)", class_label="Emergency adrenaline",
        examples=["epinephrine auto-injector"], ingredients=["epinephrine"],
        master_rows=["R56"], faers_class="epinephrine auto-injectors", label_class="epinephrine auto-injectors", system_group="epinephrine_ai",
        storage_profile="epinephrine_autoinjector", severity="High",
        buckets=[("storage", True, "Prolonged extreme heat lowers the delivered medicine; keep the injector with you but out of hot cars and direct sun.")],
        mechanism_groups=["storage_sensitive"],
        heat_stack=_hs(NO, NO, NO, NO, [("drug integrity", "Epinephrine degrades with prolonged high heat.")]),
        compass=C(arrow="down", meaning="Weaker after heat: an injector left in extreme heat may deliver less medicine.",
                  mechanism="Thermal degradation of epinephrine in the device after prolonged extreme heat.",
                  triggers=["left in a hot car", "carried in direct sun for long periods"],
                  monitor=["discolored solution or past expiry", "replace if exposed to extreme heat"]),
        prescribers=["allergy", "pediatrics", "primary care"], higher_risk=["children and teens carrying injectors", "outdoor workers"],
        pediatric="Children carry auto-injectors to school, camp and sports; caregivers should keep them out of hot cars.",
        causal_factor=1.0, causal_note="Degradation shown in lab studies; real-world fluctuations caused little loss.",
        claims=[
            C(id="PMID:25997362", label="Rachid et al., Drug Dev Ind Pharm 2016",
              text="Auto-injectors stored constantly at 70 °C for 10 days ejected 77.7% of the labeled amount; the authors advise they cannot be relied on after excessive heat.",
              plain="Injectors kept extremely hot for 10 days gave only about three quarters of the medicine.",
              num=77.7, ntype="% of labeled amount", tier=6, direction="supports_harm", pop="mechanism", population="laboratory"),
            C(id="PMID:27221065", label="Parish et al., Ann Allergy Asthma Immunol 2016 (systematic review)",
              text="Systematic review of 9 studies: heat caused epinephrine degradation only with prolonged exposure; real-world temperature fluctuations caused no significant degradation; all 40 auto-injectors tested fired.",
              plain="Short hot spells did little harm; long extreme heat did.",
              tier=6, direction="conflicting", pop="mechanism", population="laboratory studies"),
        ],
        alternatives=[],
        timeline=[
            ("before_summer", "Check expiry; teach heat storage (insulated pouch, not in hot cars); consider a spare.", ["pharmacist", "prescriber"], "some", "lab studies; NYC Safe Storage"),
            ("after", "Replace an injector that was left in extreme heat.", ["pharmacist", "patient"], "some", "Rachid 2016; storage profile advice tiers"),
        ],
        messages=[("storage",
                   "Heat warning for your epinephrine injector: if it is left in extreme heat for a long time, it can give less medicine when you need it. Keep it with you, but not in a hot car or in direct sun. If it got very hot, ask your pharmacist about a replacement. " + TALK_EN,
                   "Aviso de calor por su inyector de epinefrina: si se queda mucho tiempo en calor extremo, puede dar menos medicina cuando la necesite. Llévelo con usted, pero no en un carro caliente ni al sol. Si se calentó mucho, pregunte a su farmacéutico por un reemplazo. " + TALK_ES)],
        label_line="Keep epinephrine injectors out of hot cars and sun: prolonged extreme heat lowers the medicine delivered.",
        gaps=["Only small device studies; clinically relevant heat with limited exposure is understudied."],
        extra_unverified=[],
    ),
]

if __name__ == "__main__":
    main()
