"""Term lists for matching System Public Graph variable names / concept labels.

Shared by scripts/system_dataverse_scan.py, system_relationships_filter.py and
system_build_outputs.py. Drug lists start from scripts/graph_check.py DRUGS and
are extended for the 15-drug scope in spec.md section 8.7. Each group has
`include` terms (regex-escaped substrings, case-insensitive) and optional
`exclude` regexes that veto a match (e.g. "insulin resistance" is not insulin
therapy). Matching is on free-text names, so expect some false positives.
"""
import re

# The 15 in-scope drug groups (spec 8.7). Keys are stable ids used in outputs.
DRUGS15 = {
    "lithium": {"label": "Lithium", "include": ["lithium"],
                "exclude": [r"lithium[- ]ion", r"lithium batter"]},
    "loop_diuretics": {"label": "Loop diuretics",
                       "include": ["furosemide", "frusemide", "bumetanide", "torsemide", "torasemide", "loop diuretic",
                                    "sodium potassium chloride symporter inhibitor", "na-k-cl cotransporter inhibitor"]},
    "thiazides": {"label": "Thiazides",
                  "include": ["thiazide", "hydrochlorothiazide", "chlorthalidone", "chlortalidone", "indapamide", "metolazone", "hctz",
                              "sodium chloride symporter inhibitor"]},
    "acei_arb": {"label": "ACE inhibitors / ARBs",
                 "include": ["ace inhibitor", "ace-inhibitor", "angiotensin-converting enzyme inhibitor",
                             "angiotensin converting enzyme inhibitor", "angiotensin receptor blocker",
                             "angiotensin ii receptor blocker", "angiotensin receptor antagonist",
                             "angiotensin ii receptor antagonist", "lisinopril", "ramipril", "enalapril",
                             "captopril", "perindopril", "benazepril", "quinapril", "losartan", "valsartan",
                             "candesartan", "irbesartan", "trandolapril", "fosinopril", "moexipril", "imidapril", "azilsartan", "eprosartan", "olmesartan", "telmisartan", "renin-angiotensin system inhibitor",
                             "raas inhibitor", "ras inhibitor", "ras blockade", "raas blockade", "acei", "arb"],
                 },
    "sglt2": {"label": "SGLT2 inhibitors",
              "include": ["sglt2", "sglt-2", "sodium-glucose cotransporter 2", "sodium-glucose co-transporter 2",
                          "sodium glucose cotransporter 2", "gliflozin"]},
    "insulin": {"label": "Insulin (incl. pumps)",
                "include": ["insulin"],
                "exclude": [r"resistan", r"sensitiv", r"secret", r"fasting", r"serum insulin", r"plasma insulin",
                            r"insulin level", r"insulin concentration", r"homa", r"insulin-like", r"igf", r"insulinoma",
                            r"clearance", r"insulin response", r"insulin action", r"signal", r"receptor", r"proinsulin",
                            r"insulin index", r"auc", r"c-peptide", r"insulin(ogenic)? index", r"autoantib", r"insulin antib",
                            r"insulin release", r"insulin degrad", r"hyperinsulin", r"insulinemi", r"insulin tolerance",
                            r"disposition index", r"insulin gene", r"\bins\b", r"dietary insulin", r"insulin load",
                            r"circulating", r"endogenous insulin", r"insulin demand", r"insulin need"]},
    "metformin": {"label": "Metformin", "include": ["metformin"]},
    "anticholinergics": {"label": "Anticholinergics (oxybutynin)",
                         "include": ["anticholinergic", "antimuscarinic", "oxybutynin", "benztropine", "diphenhydramine",
                                     "tolterodine", "solifenacin", "trospium", "darifenacin", "fesoterodine", "trihexyphenidyl",
                                     "scopolamine", "hyoscine"]},
    "antipsychotics": {"label": "Antipsychotics (incl. clozapine)",
                       "include": ["antipsychotic", "neuroleptic", "olanzapine", "quetiapine", "risperidone", "haloperidol",
                                   "clozapine", "aripiprazole", "ziprasidone", "paliperidone", "lurasidone", "chlorpromazine",
                                   "asenapine", "cariprazine", "brexpiprazole", "fluphenazine", "perphenazine"],
                       "exclude": [r"neuroleptic malignant"]},
    "ssris": {"label": "SSRIs",
              "include": ["ssri", "selective serotonin reuptake", "selective serotonin re-uptake", "sertraline", "fluoxetine",
                          "citalopram", "escitalopram", "paroxetine", "fluvoxamine", "antidepressant"]},
    "topiramate_zonisamide": {"label": "Topiramate / zonisamide", "include": ["topiramate", "zonisamide"]},
    "adhd_stimulants": {"label": "ADHD stimulants",
                        "include": ["methylphenidate", "amphetamine", "lisdexamfetamine", "dexamfetamine", "dextroamphetamine",
                                    "dexmethylphenidate", "stimulant medication", "adhd medication", "psychostimulant",
                                    "stimulant treatment", "stimulant use"],
                        "exclude": [r"methamphetamine", r"\bmeth\b"]},
    "beta_blockers": {"label": "Beta blockers",
                      "include": ["beta blocker", "beta-blocker", "β-blocker", "β blocker", "beta-adrenergic blocker",
                                  "beta adrenergic blocker", "beta-adrenergic blocking", "metoprolol", "propranolol", "atenolol",
                                  "carvedilol", "bisoprolol", "nebivolol", "labetalol"]},
    "opioids_fentanyl": {"label": "Fentanyl / opioid patches",
                         "include": ["opioid", "fentanyl", "buprenorphine", "morphine", "oxycodone", "hydromorphone",
                                     "opiate"],
                         "exclude": [r"receptor", r"endogenous opioid", r"opioid peptide"]},
    "epinephrine_ai": {"label": "Epinephrine auto-injectors",
                       "include": ["epinephrine auto", "epinephrine autoinjector", "adrenaline auto", "autoinjector",
                                   "auto-injector", "epipen", "intramuscular epinephrine", "epinephrine administration",
                                   "epinephrine use", "epinephrine treatment", "epinephrine prescription"]},
}

# Comparison groups (from graph_check.py, not in the 15) used to sanity-check pathways.
COMPARATORS = {
    "nsaids": {"label": "NSAIDs (comparator)",
               "include": ["nsaid", "non-steroidal anti-inflammatory", "nonsteroidal anti-inflammatory", "ibuprofen",
                           "naproxen", "diclofenac", "celecoxib"]},
    "benzodiazepines": {"label": "Benzodiazepines (comparator)",
                        "include": ["benzodiazepine", "lorazepam", "diazepam", "alprazolam", "clonazepam"]},
    "sulfonylureas": {"label": "Sulfonylureas (comparator)",
                      "include": ["sulfonylurea", "glipizide", "glyburide", "glibenclamide", "gliclazide", "glimepiride"]},
    "diuretics_any": {"label": "Diuretics, any (comparator)", "include": ["diuretic"]},
}

MEDIATORS = {
    "dehydration": {"label": "Dehydration / volume depletion",
                    "include": ["dehydration", "volume depletion", "hypovolemia", "hypovolaemia", "hypovolemic",
                                "hypohydration", "fluid loss", "volume contraction"]},
    "hyponatremia": {"label": "Hyponatremia / serum sodium",
                     "include": ["hyponatremia", "hyponatraemia", "hyponatremic", "serum sodium", "plasma sodium",
                                 "sodium concentration", "sodium level", "blood sodium", "siadh",
                                 "inappropriate antidiuretic"]},
    "aki": {"label": "Acute kidney injury",
            "include": ["acute kidney injury", "acute kidney failure", "acute renal failure", "acute renal injury", "aki"]},
    "bp_hypotension": {"label": "Blood pressure / hypotension",
                       "include": ["hypotension", "blood pressure", "orthostatic", "systolic pressure", "diastolic pressure",
                                   "systolic bp", "diastolic bp", "sbp", "dbp"]},
    "sweating": {"label": "Sweating / anhidrosis",
                 "include": ["sweat", "anhidrosis", "hypohidrosis", "oligohidrosis", "hyperhidrosis", "diaphoresis",
                             "sudomotor", "perspiration"],
                 "exclude": [r"sweat chloride", r"sweat test", r"sweetened"]},
    "body_temp": {"label": "Body temperature / hyperthermia",
                  "include": ["hyperthermia", "body temperature", "core temperature", "core body temperature",
                              "thermoregulat", "rectal temperature", "tympanic temperature", "skin temperature"],
                  "exclude": [r"malignant hyperthermia", r"hyperthermic intraperitoneal", r"\bhipec\b", r"hyperthermia therapy",
                              r"therapeutic hyperthermia", r"hyperthermia treatment"]},
}

HEAT = {
    "heat_wave": {"label": "Heat wave", "include": ["heat wave", "heatwave", "heat-wave"]},
    "ambient_temp": {"label": "Ambient / high temperature",
                     "include": ["ambient temperature", "high temperature", "hot weather", "hot day", "hot season",
                                 "air temperature", "outdoor temperature", "outdoor heat", "temperature exposure",
                                 "heat exposure", "exposure to heat", "apparent temperature", "heat index", "wet bulb",
                                 "wbgt", "daily temperature", "mean temperature", "maximum temperature", "daily maximum temperature",
                                 "high ambient", "environmental temperature", "environmental heat", "hot environment",
                                 "temperature increase", "elevated temperature", "summer temperature"]},
    "extreme_heat": {"label": "Extreme heat",
                     "include": ["extreme heat", "extreme temperature", "excessive heat", "extremely hot", "heat event"]},
    "heat_illness": {"label": "Heat stroke / heat illness",
                     "include": ["heat stroke", "heatstroke", "heat illness", "heat-related", "heat related", "heat exhaustion",
                                 "exertional heat", "heat stress", "heat-induced", "heat injury", "heat cramps", "heat syncope"],
                     "exclude": [r"heat stress protein", r"heat shock"]},
}


def term_pattern(t):
    """Short alphanumeric terms (<=4 chars, e.g. AKI, SBP, ARB) need word boundaries; allow a plural s."""
    if len(t) <= 4 and t.isalnum():
        return r"\b" + re.escape(t) + r"s?\b"
    return re.escape(t)


def compile_groups(groups):
    """Return {key: (include_re, exclude_re_or_None)}."""
    out = {}
    for k, g in groups.items():
        inc = re.compile("|".join(term_pattern(t) for t in g["include"]), re.I)
        exc = re.compile("|".join(g["exclude"]), re.I) if g.get("exclude") else None
        out[k] = (inc, exc)
    return out


def match_groups(text, compiled):
    """Return list of group keys whose include matches and exclude does not."""
    if not text:
        return []
    hits = []
    for k, (inc, exc) in compiled.items():
        if inc.search(text) and not (exc and exc.search(text)):
            hits.append(k)
    return hits


def any_re(groups):
    """One combined prefilter regex for a dict of groups."""
    terms = [t for g in groups.values() for t in g["include"]]
    return re.compile("|".join(term_pattern(t) for t in terms), re.I)
