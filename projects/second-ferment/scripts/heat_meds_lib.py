"""Shared matching rules for heat terms and medication classes."""
import collections
import re

I = re.IGNORECASE
# Direct heat exposure / heat illness terms
HEAT_DIRECT = re.compile(
    r"heat[\s-]?waves?|heat[\s-]?stroke|heat[\s-]?(related|illness|stress|strain|exhaustion|exposure|injur|disorder|index|"
    r"toleran|intoleran|acclimat|event|day|season|warning|alert|vulnerab|mortality|death|morbidity)|extreme heat|"
    r"\bhot (weather|day|climate|temperature|environment|season|condition|spell|night|ambient|summer|humid)|"
    r"(ambient|air|outdoor|high|higher|extreme|daily|mean|maximum|apparent|environmental|wet[\s-]?bulb)[\w\s-]{0,20}temperature|"
    r"temperature (increase|rise|above|exposure|variab)|\bsummer|heat exposure|exertional heat|\bin the heat\b|"
    r"passive heat|heat load|thermal stress|hyperthermi|global warming|climate change|urban heat",
    I,
)
HEAT_EXCLUDE = re.compile(
    r"heat[\s-]?shock|heat pain|heated tobacco|heat[\s-]?map|wheat|heat therapy|heat treat|heat[\s-]?inactivat|"
    r"malignant hyperthermia|hyperthermic|hyperthermia (therapy|treatment)|hipec|heat capacity|"
    r"heat[\s-]?not[\s-]?burn|heat sensitiv|heat applic|heat wrap|heat pack|moist heat|heating|heat pad",
    I,
)
# Physiological proxies for heat vulnerability
HEAT_PROXY = re.compile(
    r"dehydrat|hypohydrat|\bsweat|thermoregulat|(core|body|rectal|skin|tympanic|oesophageal|esophageal)[\s-]?temperature|"
    r"hyponatr|volume depletion|hypovol",
    I,
)

DRUGS = collections.OrderedDict(
    [
        ("Diuretics", r"diuretic|furosemide|frusemide|thiazide|spironolactone|bumetanide|torsemide|torasemide|chlort?halidone|indapamide|amiloride"),
        ("Beta blockers", r"beta[\s-]?(adrenergic )?(receptor )?block|β[\s-]?block|metoprolol|atenolol|propranolol|bisoprolol|carvedilol|nebivolol"),
        ("ACE inhibitors / ARBs", r"ace[\s-]?inhibitor|angiotensin[\s-]converting enzyme inhib|angiotensin (ii )?receptor (block|antag)|\barbs?\b|\bacei\b|lisinopril|enalapril|ramipril|perindopril|captopril|losartan|valsartan|candesartan|telmisartan|irbesartan|renin[\s-]angiotensin[\w\s-]*(inhib|block)|raas inhib|ras inhib"),
        ("Calcium channel blockers", r"calcium[\s-]channel block|calcium antagonist|amlodipine|nifedipine|diltiazem|verapamil"),
        ("Antihypertensives (unspecified)", r"antihypertensive|anti-hypertensive|blood pressure (medication|lowering drug|drug)|cardiovascular (medication|drug)"),
        ("Anticholinergics", r"anticholinergic|antimuscarinic|oxybutynin|atropine|scopolamine|hyoscine|tolterodine|solifenacin|benz?tropine|trihexyphenidyl|glycopyrr"),
        ("Antipsychotics", r"antipsychotic|neuroleptic|haloperidol|olanzapine|clozapine|risperidone|quetiapine|aripiprazole|chlorpromazine|phenothiazine"),
        ("Antidepressants", r"antidepressant|\bssris?\b|\bsnris?\b|serotonin reuptake|tricyclic|sertraline|fluoxetine|paroxetine|citalopram|venlafaxine|duloxetine|amitriptyline|mirtazapine|bupropion"),
        ("Lithium", r"\blithium"),
        ("Psychotropics (unspecified)", r"psychotropic|psychiatric (medication|drug)|psychoactive (medication|drug)"),
        ("Insulin (as therapy)", r"insulin"),
        ("SGLT2 inhibitors", r"sglt[\s-]?2|gliflozin|sodium[\s-]glucose co"),
        ("Other diabetes drugs", r"metformin|sulfonylurea|glipizide|gliclazide|glimepiride|glp[\s-]?1|antidiabetic|hypoglycemic agent|diabetes medication"),
        ("Stimulants", r"stimulant|methylphenidate|amphetamine|mdma|ecstasy|cocaine|ephedrine|pseudoephedrine"),
        ("Antihistamines", r"antihistamine|diphenhydramine|promethazine|cetirizine|loratadine|chlorphen"),
        ("Opioids / sedatives", r"opioid|benzodiazepine|sedative|hypnotic|morphine|fentanyl|oxycodone|tramadol|diazepam|lorazepam|zolpidem"),
        ("NSAIDs / analgesics", r"\bnsaids?\b|non-?steroidal anti|ibuprofen|naproxen|diclofenac|aspirin|acetaminophen|paracetamol"),
        ("Anticonvulsants", r"anticonvulsant|antiepileptic|anti-epileptic|topiramate|zonisamide|carbamazepine|oxcarbazepine|valproate|valproic"),
        ("Antiparkinson / dementia drugs", r"levodopa|dopamine agonist|antiparkinson|cholinesterase inhib|donepezil|rivastigmine|memantine"),
        ("Statins", r"\bstatins?\b|atorvastatin|simvastatin|rosuvastatin|pravastatin"),
        ("Anticoagulants / antiplatelets", r"anticoagulant|warfarin|antiplatelet|clopidogrel|\bdoacs?\b|apixaban|rivaroxaban"),
        ("Inhalers / epinephrine", r"inhaler|salbutamol|albuterol|epinephrine|adrenaline|bronchodilator|\bepipen"),
        ("Laxatives / PPIs / other", r"laxative|proton pump|\bppis?\b|thyroxine|levothyroxine|alcohol"),
        ("Medication use (generic)", r"polypharmacy|\bmedications?\b|\bdrugs?\b|prescri|pharmac"),
    ]
)
DRUG_RE = collections.OrderedDict((k, re.compile(v, I)) for k, v in DRUGS.items())
INSULIN_BIOMARKER = re.compile(
    r"insulin[\s-]?(resist|sensitiv|like|level|concentrat|secret|respon|receptor|signal|growth|index|auc|clearance|action)|"
    r"(fasting|serum|plasma|circulating|basal|postprandial|hyper|hypo|pro|endogenous|blood)[\s-]?insulin|homa|igf|"
    r"non[\s-]?insulin|insulinemi|insulin[\s-]?depend",
    I,
)
STORAGE = re.compile(r"storage|stored|stabilit|shelf|degrad|potency|refriger|room temperature|freez|cold chain", I)


def heat_tier(name):
    if HEAT_DIRECT.search(name) and not HEAT_EXCLUDE.search(name):
        return "direct"
    if HEAT_PROXY.search(name):
        return "proxy"
    return None


def drug_classes(name):
    hits = []
    for k, rx in DRUG_RE.items():
        if rx.search(name):
            if k == "Insulin (as therapy)" and INSULIN_BIOMARKER.search(name):
                continue
            hits.append(k)
    # only keep the generic bucket if nothing specific matched
    if len(hits) > 1 and "Medication use (generic)" in hits:
        hits.remove("Medication use (generic)")
    return hits


# ---------------------------------------------------------------------------
# HeatRx evidence base (added 2026-11-14, phase 1). Documented in docs/MAPPINGS.md.
# ---------------------------------------------------------------------------

# The 16 drug classes HeatRx covers: (id, key in DRUGS, display label, named in the brief)
FOCUS = [
    ("diuretics", "Diuretics", "Diuretics", True),
    ("beta_blockers", "Beta blockers", "Beta blockers", True),
    ("acei_arb", "ACE inhibitors / ARBs", "ACE inhibitors / ARBs", False),
    ("ccb", "Calcium channel blockers", "Calcium channel blockers", False),
    ("anticholinergics", "Anticholinergics", "Anticholinergics", True),
    ("antipsychotics", "Antipsychotics", "Antipsychotics", True),
    ("antidepressants", "Antidepressants", "Antidepressants", False),
    ("lithium", "Lithium", "Lithium", True),
    ("insulin", "Insulin (as therapy)", "Insulin", True),
    ("sglt2", "SGLT2 inhibitors", "SGLT2 inhibitors", True),
    ("other_diabetes", "Other diabetes drugs", "Other diabetes drugs", False),
    ("anticonvulsants", "Anticonvulsants", "Anticonvulsants", False),
    ("nsaids", "NSAIDs / analgesics", "NSAIDs and other painkillers", False),
    ("opioids_sedatives", "Opioids / sedatives", "Opioids and sedatives", False),
    ("stimulants", "Stimulants", "Stimulants", False),
    ("antihistamines", "Antihistamines", "Antihistamines", False),
]
FOCUS_BY_KEY = {k: i for i, k, _, _ in FOCUS}

# Individual drugs per class, for search and the medication review. Generic names only.
MEMBERS = {
    "diuretics": ["furosemide", "bumetanide", "torsemide", "hydrochlorothiazide", "chlorthalidone", "indapamide", "spironolactone", "amiloride"],
    "beta_blockers": ["metoprolol", "atenolol", "propranolol", "bisoprolol", "carvedilol", "nebivolol"],
    "acei_arb": ["lisinopril", "enalapril", "ramipril", "perindopril", "captopril", "losartan", "valsartan", "candesartan", "telmisartan", "irbesartan"],
    "ccb": ["amlodipine", "nifedipine", "diltiazem", "verapamil"],
    "anticholinergics": ["oxybutynin", "tolterodine", "solifenacin", "benztropine", "trihexyphenidyl", "scopolamine", "glycopyrrolate", "atropine"],
    "antipsychotics": ["haloperidol", "olanzapine", "clozapine", "risperidone", "quetiapine", "aripiprazole", "chlorpromazine"],
    "antidepressants": ["sertraline", "fluoxetine", "paroxetine", "citalopram", "escitalopram", "venlafaxine", "duloxetine", "amitriptyline", "mirtazapine", "bupropion"],
    "lithium": ["lithium carbonate"],
    "insulin": ["insulin glargine", "insulin lispro", "insulin aspart", "NPH insulin", "regular insulin"],
    "sglt2": ["empagliflozin", "dapagliflozin", "canagliflozin"],
    "other_diabetes": ["metformin", "glipizide", "gliclazide", "glimepiride", "semaglutide", "liraglutide"],
    "anticonvulsants": ["topiramate", "zonisamide", "carbamazepine", "oxcarbazepine", "valproate"],
    "nsaids": ["ibuprofen", "naproxen", "diclofenac", "aspirin", "acetaminophen"],
    "opioids_sedatives": ["morphine", "oxycodone", "tramadol", "fentanyl", "diazepam", "lorazepam", "zolpidem"],
    "stimulants": ["methylphenidate", "amphetamine", "pseudoephedrine"],
    "antihistamines": ["diphenhydramine", "promethazine", "chlorpheniramine", "cetirizine", "loratadine"],
}

# Body systems (hubs of the body-system map) and the finer effects (nodes of the ribbon map).
HUBS = [
    ("heat", "Heat illness"),
    ("brain", "Brain"),
    ("heart", "Heart and blood pressure"),
    ("kidney", "Kidney"),
    ("salts", "Sodium and potassium"),
    ("sugar", "Blood sugar"),
    ("fluid", "Fluid loss"),
    ("falls", "Falls"),
]
# (id, label, hub, pattern matched against the variable on the other side)
EFFECTS = [
    ("heat_illness", "Heat illness", "heat",
     r"heat[\s-]?(stroke|illness|exhaustion|cramp|syncope)|heat[\s-]related (illness|patholog|disorder|admission|death|mortality|emergenc)|"
     r"hyperthermi|neuroleptic malignant|serotonin syndrome"),
    ("confusion", "Confusion and delirium", "brain", r"delirium|confus|cognitive (impair|decline|dysfunction)|altered mental"),
    ("low_bp", "Low blood pressure and fainting", "heart", r"hypotens|syncope|orthostat|faint"),
    ("heart_rhythm", "Heart rhythm problems", "heart",
     r"arrhythm|\bqtc?\b|torsade|atrial fibrillation|ventricular (fibrillation|tachy)|cardiac arrest|sudden (cardiac )?death"),
    ("kidney", "Kidney injury", "kidney", r"acute kidney injury|kidney injury|acute renal (failure|injury)|\baki\b|nephrotox|renal failure"),
    ("sodium", "Low sodium", "salts", r"hyponatr"),
    ("potassium", "Potassium imbalance", "salts", r"hyperkal|hypokal|serum potassium|plasma potassium|potassium (level|concentration)"),
    ("low_sugar", "Low blood sugar", "sugar", r"hypoglyc"),
    ("ketoacidosis", "Ketoacidosis and high blood sugar crises", "sugar", r"ketoacidosis|\bdka\b|hyperglyc\w* (emergenc|crisis|crises)|hyperosmolar"),
    ("fluid_loss", "Dehydration and fluid loss", "fluid", r"dehydrat|hypovol|volume depletion|hypohydrat|fluid (loss|depletion)"),
    ("falls", "Falls and fractures", "falls", r"\bfalls?\b|\bfalling\b|hip fracture"),
]
EFFECT_RE = [(e, re.compile(p, I)) for e, _, _, p in EFFECTS]

# For heat arms: a heat variable must describe environmental heat. These mark rows that are about cold, about
# clinical hyperthermia (fever, post-arrest rebound, therapy), or only seasonal.
COLD = re.compile(r"\bcold|low vs\.? high|\(low\b|winter|low(er)? (ambient |air |outdoor )?temperature|temperature (decrease|decline|drop)|"
                  r"(decrease|decline|drop) in (ambient |daily |mean )?temperature|hypotherm|frost|\bsnow", I)
CLINICAL_HYPERTHERMIA = re.compile(r"rebound|post[\s-]?(cardiac arrest|operative|rewarming)|fever|febrile|\bicu\b|"
                                   r"intensive care|targeted temperature|after (stroke|cardiac)|in the first 24|"
                                   r"(?<!heat )(?<!heat-)(?<!heat)(stroke|trauma|sepsis|septic) patients|cooking|"
                                   r"(body|core|rectal|skin|tympanic|oesophageal|esophageal|peripheral|patient) temperature|after maintenance|\bivf\b", I)
ENV_HEAT = re.compile(r"heat[\s-]?waves?|heat[\s-]?stroke|heat[\s-]?(related|illness|stress|strain|exhaustion|exposure|index|"
                      r"event|day|warning|alert|season)|extreme heat|\bhot (weather|day|climate|temperature|environment|season|"
                      r"spell|night|summer)|(ambient|air|outdoor|high|higher|extreme|daily|mean|maximum|apparent|environmental|"
                      r"wet[\s-]?bulb)[\w\s-]{0,20}temperature|temperature (increase|rise|above|exposure)|\bsummer|heat exposure|"
                      r"exertional heat|climate change|global warming|urban heat|\bwbgt\b", I)


QUALIFIER = re.compile(r"\([^)]*\)|\[[^\]]*\]|\b(among|in patients|patients with|in people with|in those with|of patients)\b.*$", I)
ANIMAL = re.compile(r"\b(rats?|mice|mouse|murine|pigs?|piglets?|swine|cattle|cows?|calves|broilers?|chickens?|hens|poultry|sheep|"
                    r"goats?|dogs?|canine|cats?|feline|horses?|equine|rabbits?|fish|monkeys?|primates?|frogs?)\b", I)
HIGH = re.compile(r"heat|\bhot\b|high|extreme|summer|above|increase|rise|percentile|maximum|warm|elevated|desert", I)


def effects(name):
    """Effects named in a variable, ignoring qualifiers such as '(among patients with atrial fibrillation)'."""
    core = QUALIFIER.sub("", name)
    return [e for e, rx in EFFECT_RE if rx.search(core)]


def env_heat(name):
    """True if a heat-tier name describes environmental heat (not cold, not clinical hyperthermia)."""
    if heat_tier(name) != "direct":
        return False
    if COLD.search(name) or CLINICAL_HYPERTHERMIA.search(name):
        return False
    return bool(ENV_HEAT.search(name))


def focus_classes(name):
    """Focus class ids for a variable name (subset of drug_classes())."""
    return [FOCUS_BY_KEY[k] for k in drug_classes(name) if k in FOCUS_BY_KEY]


RATIO_TYPES = {"odds_ratio", "adjusted_odds_ratio", "hazard_ratio", "adjusted_hazard_ratio", "relative_risk_ratio",
               "incident_rate_ratio", "prevalence_ratio"}


def direction(stat_type, lo, hi):
    """'raised' / 'lowered' / 'unclear' for ratio statistics with a CI; 'not_ratio' otherwise."""
    if stat_type not in RATIO_TYPES:
        return "not_ratio"
    try:
        lo = float(lo) if lo not in (None, "") else None
        hi = float(hi) if hi not in (None, "") else None
    except ValueError:
        return "unclear"
    if lo is not None and lo > 1:
        return "raised"
    if hi is not None and hi < 1:
        return "lowered"
    return "unclear"
