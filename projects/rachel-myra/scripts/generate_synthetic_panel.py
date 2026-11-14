"""Generate the SYNTHETIC patient panel for "The Missing Label" (spec §6.8, §4.3-4.5a, §6.1).

Run:
    ~/.local/bin/uv run --with certifi python scripts/generate_synthetic_panel.py            # uses cached sources
    ~/.local/bin/uv run --with certifi python scripts/generate_synthetic_panel.py --refresh  # re-download sources

Stdlib only, plus certifi for TLS roots (optional). Output goes to data/processed/synthetic/.

WHY NOT SYNTHEA
    The build plan (Step 1/2) planned Synthea, which needs Java. The build machine has no Java and
    ~4 GB free disk, so this is a small deterministic Python generator instead (fixed seed
    SEED=20261114). Same seed + same cached source files => byte-identical output.

EVERYTHING HERE IS SYNTHETIC
    * Every row/resource carries synthetic=true (CSV column; FHIR extension + meta.tag HTEST).
    * Names are Synthea-style (letters + 3 digits, e.g. "Rosa412 Quintero877") so no record can be
      mistaken for a real person. Phone numbers use the fictional 555-01xx block.
    * Home locations are random points inside the Census ZCTA polygon of the ZIP (rejecting large
      parks and the Jerome Park Reservoir), never a street address. Patient.address has no line.
    * No dose numbers are written (spec §10.1 guardrail: no dose numbers); only ingredient, route
      and dose form.

DATA SOURCES (fetched once, cached in data/processed/synthetic/sources/, access date 2026-11-14)
    1. CDC PLACES ZCTA, 2025 release (data.cdc.gov dataset kee5-23sr): crude adult prevalence of
       high BP, diabetes, CHD, current asthma, depression, arthritis, mobility disability etc.
       Used to (a) weight ZIPs by population and (b) as the reference the panel is compared to.
    2. CDC PLACES ZCTA, 2023 release (c7b2-4ecy): chronic kidney disease (dropped from the 2025
       GIS release).
    3. US Census TIGERweb, 2020 ZCTA polygons (PUMA_TAD_TAZ_UGA_ZCTA MapServer layer 7).
    4. CDC/ATSDR SVI 2022, Bronx County (ACS 2018-2022): % age 65+, % age <=17, % limited English,
       % housing in 10+ unit structures. (The Census API itself now requires a key, so SVI is used
       as the ACS proxy.)
    5. NYC Parks Properties (NYC Open Data enfh-gkve): Bronx parks > 2 acres, to avoid placing a
       home inside Crotona Park, Bronx Park (zoo/botanical garden) etc.
    6. NIH RxNav (rxnav.nlm.nih.gov) for RxNorm RxCUIs of every generic ingredient -> rxnorm_cache.json.
    7. NLM Clinical Tables ICD-10-CM API to confirm every condition code -> sources/icd10cm_cache.json.

ASSUMPTIONS (explicit; none of these come from a single authoritative source)
    A1 Panel age mix: a clinic panel of people ON MEDICINES, deliberately enriched for heat-relevant
       drugs, so it is older and sicker than the ZIP population (Bronx SVI: 13.3% age 65+,
       24.7% age <=17). Bands: 2-5 2%, 6-11 5%, 12-17 6%, 18-29 8%, 30-44 16%, 45-64 35%,
       65-74 16%, 75-94 12%.
    A2 Sex: adults 56% female (primary-care panels skew female); children 50/50, ADHD male 2:1.
    A3 ZIP weights: PLACES total population x 1.0 for demo ZIPs (10453, 10457, 10458, 10460) and
       x 0.5 for nearby ZIPs (10452, 10456, 10468).
    A4 Condition probabilities are age-banded (see COND_P), anchored so that the panel's adult
       prevalence sits at or above PLACES crude prevalence (enrichment). Behavioural-health
       conditions (schizophrenia, bipolar) are enriched ~3x over population (~1-2%) because SBH
       runs a large behavioural-health service (spec §6.3). README compares panel vs PLACES.
    A5 Children in the panel are children on a medicine: asthma, ADHD (teens), epilepsy (incl.
       topiramate), food/insect allergy with epinephrine, rare type 1 diabetes.
    A6 Drug choice within condition follows common US first-line practice (ACC/AHA HTN 2017,
       ADA Standards of Care, APA guidelines); weights are illustrative, not measured.
       Antipsychotic polypharmacy ~20% of schizophrenia (Gallego et al. 2012, international median
       19.6%). Lithium in ~30% of bipolar. NSAID use from arthritis/chronic pain/migraine, which
       produces "triple whammy" combinations naturally rather than by force.
    A7 Working AC: 84% yes (minus 6 points for people 65+ living alone). NYC Housing & Vacancy
       Survey via DOHMH EHDP indicator 2185 (data/processed/ac_households_nyc.csv, written by the
       place agent): 2023 households WITH AC in the SBH sub-boroughs = 84.9% University
       Heights/Fordham, 87.0% Morrisania/East Tremont, 88.1% Highbridge/South Concourse (2017:
       79.7-84.6%). "Working AC" is stricter than "has AC" and the panel is older/lower income,
       so we sit slightly below. 15% of those with AC say cost limits use (assumption; NYC DOHMH
       heat data story cites cost as a reason AC goes unused).
    A8 Lives alone: 10% (18-44), 20% (45-64), 33% (65+) - assumption informed by NYC aging
       reports (~1/3 of older New Yorkers live alone).
    A9 Mobility / step-free need: 5% / 20% / 38% by the same bands (PLACES mobility disability
       ~20-24% of adults in these ZCTAs), raised for heart failure and chronic pain.
    A10 Building: 67.5% of Bronx housing units are in 10+ unit structures (SVI EP_MUNIT); those
       are elevator buildings 70% of the time (assumption) up to floor 20; walk-ups floors 1-6;
       small buildings floors 1-3.
    A11 Preferred language: Spanish 30% (18-44), 40% (45-64), 50% (65+), 35% for children's
       parents; ~3% other (French, Bengali, Arabic); rest English (assumption; these ZIPs are
       majority Hispanic and SVI shows 14.5% of Bronx residents speak English less than well).
    A12 Trusted contacts: 0 (20%), 1 (55%), 2 (25%). Location type: same building 10%, walkable
       same ZIP 0.2-1.5 km 30%, elsewhere in the Bronx 1.5-6 km 30%, elsewhere in NYC 6-20 km 20%,
       out of area 30-150 km 10%. Contact positions are bearing+distance offsets, not addresses.
    A13 Mail order: 18% of adults, 30% of 65+ with 3+ chronic meds, 5% of children (assumption;
       US mail-order share of maintenance prescriptions is roughly 10-20%). Controlled
       substances and clozapine (REMS, lab-linked dispensing) are never mail-order here.
    A14 naive_travel_min / naive_qualifies_60min in contacts.csv are PLACEHOLDERS for the routed
       travel time of spec §4.4a: straight-line km x 1.3 detour, walking 0.8 m/s (older walker,
       Western et al. 2025) if <=1.5 km, else transit 10 min + 15 km/h, else driving 30 km/h.
       Qualifies if travel <= 60 - 15 (patient p90) - 15 (contact p90) = 30 min (high risk), or
       <= 90 - 30 = 60 min (medium risk). Step 4 must
       replace these with OpenRouteService/GTFS routing and published p90s.
    A15 Mechanism tags and Anticholinergic Burden (ACB) scores per drug are provisional
       convenience fields (ACB per Boustani et al. 2008 / 2012 update, as recalled - verify).
       The Step-3 knowledge base is authoritative; these are NOT a risk score.
    A16 Background non-heat medicines so lists look real: omeprazole 15% of 40+, levothyroxine 9%
       of 30+, low-dose aspirin 35% of 50+ with diabetes/HF/CKD, vitamin D 15% of 50+, statin 70%
       of 40+ with diabetes and 40% with other cardio-renal disease (assumptions).
    A17 Coverage top-up: with only 300 patients, rare drugs (lithium, fentanyl patches) can come
       out at 1-2 patients by chance. After the random draw, trailing random patients are replaced
       by patients whose condition and drug are forced (TOPUP table) until each of the 15 spec §8.7
       classes has >= 5 patients. These rows have coverage_topup=true, so analyses that need
       "natural" rates can drop them.
"""
import argparse
import csv
import datetime as dt
import json
import math
import random
import ssl
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "processed" / "synthetic"
SRC = OUT / "sources"
SEED = 20261114
REF_DATE = dt.date(2026, 11, 14)
UA = {"User-Agent": "synthetic-panel-generator/1.0"}
try:  # some hosts (NYC Open Data) fail with uv's bundled CA store; certifi fixes it if present
    import certifi
    SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    SSL_CTX = ssl.create_default_context()

DEMO_ZIPS = ["10453", "10457", "10458", "10460"]
NEARBY_ZIPS = ["10452", "10456", "10468"]
ALL_ZIPS = DEMO_ZIPS + NEARBY_ZIPS
N_TOTAL = 300

# Approximate box around Jerome Park Reservoir (10468) - homes are not placed in water.
RESERVOIR_BOX = (-73.8935, 40.8745, -73.8845, 40.8865)  # lon_min, lat_min, lon_max, lat_max


# ----------------------------------------------------------------------------- network + cache
def get_json(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=60, context=SSL_CTX) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception:  # noqa: BLE001
            if i == tries - 1:
                raise
            time.sleep(2 * (i + 1))


def cached(name, url, refresh):
    p = SRC / name
    if p.exists() and not refresh:
        return json.loads(p.read_text())
    data = get_json(url)
    p.write_text(json.dumps(data, indent=1))
    return data


def zip_in(field):
    return "%20in(" + ",".join("'%s'" % z for z in ALL_ZIPS) + ")"


def load_sources(refresh):
    SRC.mkdir(parents=True, exist_ok=True)
    zin = zip_in("zcta5")
    places = cached("cdc_places_zcta_2025.json",
                    "https://data.cdc.gov/resource/kee5-23sr.json?$where=zcta5" + zin, refresh)
    kidney = cached("cdc_places_zcta_2023_kidney.json",
                    "https://data.cdc.gov/resource/c7b2-4ecy.json?$select=zcta5,kidney_crudeprev"
                    "&$where=zcta5" + zin, refresh)
    q = urllib.parse.quote("ZCTA5 IN (" + ",".join("'%s'" % z for z in ALL_ZIPS) + ")")
    zcta = cached("census_tigerweb_zcta2020.geojson",
                  "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/"
                  "PUMA_TAD_TAZ_UGA_ZCTA/MapServer/7/query?where=" + q +
                  "&outFields=ZCTA5,AREALAND&outSR=4326&f=geojson", refresh)
    svi = cached("cdc_svi2022_bronx_county.json",
                 "https://onemap.cdc.gov/OneMapServices/rest/services/SVI/"
                 "CDC_ATSDR_Social_Vulnerability_Index_2022_USA/FeatureServer/1/query?"
                 "where=FIPS%3D'36005'&outFields=FIPS,LOCATION,E_TOTPOP,EP_AGE65,EP_AGE17,"
                 "EP_LIMENG,EP_DISABL,EP_NOVEH,EP_MUNIT&returnGeometry=false&f=json", refresh)
    parks = cached("nyc_parks_bronx_gt2acres.json",
                   "https://data.cityofnewyork.us/resource/enfh-gkve.json?$select=signname,acres,"
                   "zipcode,multipolygon&$where=borough='X'%20AND%20acres>2&$limit=1000", refresh)
    return places, kidney, zcta, svi, parks


# ----------------------------------------------------------------------------- code catalogs
# key: (rxnav lookup name, drug class, spec §8.7 heat class or "", mechanism tags, ACB score,
#       dose form, route, mail-order eligible, fridge/temperature-sensitive)
DRUGS = {
    "lisinopril": ("lisinopril", "ACE inhibitor", "ACE inhibitors/ARBs", ["bp_drop", "kidney_stress"], 0, "oral tablet", "oral", True, False),
    "losartan": ("losartan", "ARB", "ACE inhibitors/ARBs", ["bp_drop", "kidney_stress"], 0, "oral tablet", "oral", True, False),
    "sacubitril/valsartan": ("sacubitril / valsartan", "ARNI (contains ARB)", "ACE inhibitors/ARBs", ["bp_drop", "kidney_stress"], 0, "oral tablet", "oral", True, False),
    "amlodipine": ("amlodipine", "calcium channel blocker", "", ["bp_drop"], 0, "oral tablet", "oral", True, False),
    "hydrochlorothiazide": ("hydrochlorothiazide", "thiazide diuretic", "thiazides", ["fluid_salt_loss", "low_sodium"], 0, "oral tablet", "oral", True, False),
    "chlorthalidone": ("chlorthalidone", "thiazide-like diuretic", "thiazides", ["fluid_salt_loss", "low_sodium"], 1, "oral tablet", "oral", True, False),
    "metoprolol": ("metoprolol", "beta blocker", "beta blockers", ["bp_drop", "less_skin_blood_flow"], 1, "oral extended-release tablet", "oral", True, False),
    "carvedilol": ("carvedilol", "beta blocker", "beta blockers", ["bp_drop", "less_skin_blood_flow"], 1, "oral tablet", "oral", True, False),
    "propranolol": ("propranolol", "beta blocker", "beta blockers", ["bp_drop", "less_skin_blood_flow"], 0, "oral tablet", "oral", True, False),
    "furosemide": ("furosemide", "loop diuretic", "loop diuretics", ["fluid_salt_loss"], 1, "oral tablet", "oral", True, False),
    "torsemide": ("torsemide", "loop diuretic", "loop diuretics", ["fluid_salt_loss"], 0, "oral tablet", "oral", True, False),
    "bumetanide": ("bumetanide", "loop diuretic", "loop diuretics", ["fluid_salt_loss"], 0, "oral tablet", "oral", True, False),
    "spironolactone": ("spironolactone", "potassium-sparing diuretic", "", ["fluid_salt_loss"], 0, "oral tablet", "oral", True, False),
    "digoxin": ("digoxin", "cardiac glycoside", "", ["kidney_cleared_buildup"], 1, "oral tablet", "oral", True, False),
    "empagliflozin": ("empagliflozin", "SGLT2 inhibitor", "SGLT2 inhibitors", ["fluid_salt_loss"], 0, "oral tablet", "oral", True, False),
    "dapagliflozin": ("dapagliflozin", "SGLT2 inhibitor", "SGLT2 inhibitors", ["fluid_salt_loss"], 0, "oral tablet", "oral", True, False),
    "metformin": ("metformin", "biguanide", "metformin", ["kidney_cleared_buildup"], 0, "oral tablet", "oral", True, False),
    "insulin glargine": ("insulin glargine", "basal insulin", "insulin", ["faster_absorption", "storage_sensitive"], 0, "injectable pen", "subcutaneous", True, True),
    "insulin lispro": ("insulin lispro", "rapid-acting insulin", "insulin", ["faster_absorption", "storage_sensitive"], 0, "injectable pen", "subcutaneous", True, True),
    "glipizide": ("glipizide", "sulfonylurea", "", ["low_glucose"], 0, "oral tablet", "oral", True, False),
    "semaglutide": ("semaglutide", "GLP-1 receptor agonist", "", ["fluid_salt_loss", "storage_sensitive"], 0, "injectable pen", "subcutaneous", True, True),
    "atorvastatin": ("atorvastatin", "statin", "", [], 0, "oral tablet", "oral", True, False),
    "lithium": ("lithium carbonate", "mood stabilizer (lithium)", "lithium", ["kidney_cleared_buildup"], 0, "oral capsule", "oral", True, False),
    "divalproex": ("divalproex sodium", "mood stabilizer / anticonvulsant", "", ["sedation"], 0, "oral delayed-release tablet", "oral", True, False),
    "lamotrigine": ("lamotrigine", "anticonvulsant / mood stabilizer", "", [], 0, "oral tablet", "oral", True, False),
    "risperidone": ("risperidone", "antipsychotic (2nd gen)", "antipsychotics", ["impaired_thermoregulation", "sedation"], 1, "oral tablet", "oral", True, False),
    "olanzapine": ("olanzapine", "antipsychotic (2nd gen)", "antipsychotics", ["impaired_thermoregulation", "sedation", "sweat_blocked"], 3, "oral tablet", "oral", True, False),
    "aripiprazole": ("aripiprazole", "antipsychotic (2nd gen)", "antipsychotics", ["impaired_thermoregulation"], 1, "oral tablet", "oral", True, False),
    "quetiapine": ("quetiapine", "antipsychotic (2nd gen)", "antipsychotics", ["impaired_thermoregulation", "sedation", "sweat_blocked"], 3, "oral tablet", "oral", True, False),
    "haloperidol": ("haloperidol", "antipsychotic (1st gen)", "antipsychotics", ["impaired_thermoregulation", "sedation"], 1, "oral tablet", "oral", True, False),
    "paliperidone": ("paliperidone", "antipsychotic (2nd gen)", "antipsychotics", ["impaired_thermoregulation"], 1, "long-acting injection", "intramuscular", False, False),
    "clozapine": ("clozapine", "antipsychotic (2nd gen)", "antipsychotics", ["impaired_thermoregulation", "sedation", "sweat_blocked"], 3, "oral tablet", "oral", False, False),
    "ziprasidone": ("ziprasidone", "antipsychotic (2nd gen)", "antipsychotics", ["impaired_thermoregulation"], 1, "oral capsule", "oral", True, False),
    "lurasidone": ("lurasidone", "antipsychotic (2nd gen)", "antipsychotics", ["impaired_thermoregulation"], 0, "oral tablet", "oral", True, False),
    "benztropine": ("benztropine", "anticholinergic (antiparkinson)", "anticholinergics", ["sweat_blocked"], 3, "oral tablet", "oral", True, False),
    "sertraline": ("sertraline", "SSRI", "SSRIs", ["low_sodium", "more_sweating"], 0, "oral tablet", "oral", True, False),
    "escitalopram": ("escitalopram", "SSRI", "SSRIs", ["low_sodium", "more_sweating"], 0, "oral tablet", "oral", True, False),
    "fluoxetine": ("fluoxetine", "SSRI", "SSRIs", ["low_sodium", "more_sweating"], 0, "oral capsule", "oral", True, False),
    "citalopram": ("citalopram", "SSRI", "SSRIs", ["low_sodium", "more_sweating"], 0, "oral tablet", "oral", True, False),
    "paroxetine": ("paroxetine", "SSRI", "SSRIs", ["low_sodium", "sweat_blocked"], 3, "oral tablet", "oral", True, False),
    "bupropion": ("bupropion", "antidepressant (NDRI)", "", [], 1, "oral extended-release tablet", "oral", True, False),
    "mirtazapine": ("mirtazapine", "antidepressant", "", ["sedation"], 1, "oral tablet", "oral", True, False),
    "trazodone": ("trazodone", "antidepressant / sleep", "", ["sedation"], 1, "oral tablet", "oral", True, False),
    "amitriptyline": ("amitriptyline", "tricyclic antidepressant", "anticholinergics", ["sweat_blocked", "sedation"], 3, "oral tablet", "oral", True, False),
    "duloxetine": ("duloxetine", "SNRI", "", ["low_sodium"], 0, "oral capsule", "oral", True, False),
    "venlafaxine": ("venlafaxine", "SNRI", "", ["low_sodium"], 1, "oral extended-release capsule", "oral", True, False),
    "levetiracetam": ("levetiracetam", "anticonvulsant", "", [], 0, "oral tablet", "oral", True, False),
    "topiramate": ("topiramate", "anticonvulsant (carbonic anhydrase)", "topiramate/zonisamide", ["sweat_blocked"], 0, "oral tablet", "oral", True, False),
    "zonisamide": ("zonisamide", "anticonvulsant (carbonic anhydrase)", "topiramate/zonisamide", ["sweat_blocked"], 0, "oral capsule", "oral", True, False),
    "carbamazepine": ("carbamazepine", "anticonvulsant", "", ["low_sodium"], 2, "oral tablet", "oral", True, False),
    "oxcarbazepine": ("oxcarbazepine", "anticonvulsant", "", ["low_sodium"], 0, "oral tablet", "oral", True, False),
    "sumatriptan": ("sumatriptan", "triptan", "", [], 0, "oral tablet", "oral", True, False),
    "methylphenidate": ("methylphenidate", "ADHD stimulant", "ADHD stimulants", ["heat_production"], 0, "oral extended-release tablet", "oral", False, False),
    "amphetamine mixed salts": ("amphetamine aspartate / amphetamine sulfate / dextroamphetamine saccharate / dextroamphetamine sulfate", "ADHD stimulant", "ADHD stimulants", ["heat_production"], 0, "oral extended-release capsule", "oral", False, False),
    "lisdexamfetamine": ("lisdexamfetamine", "ADHD stimulant", "ADHD stimulants", ["heat_production"], 0, "oral capsule", "oral", False, False),
    "guanfacine": ("guanfacine", "alpha-2 agonist (ADHD)", "", ["bp_drop", "sedation"], 0, "oral extended-release tablet", "oral", True, False),
    "oxybutynin": ("oxybutynin", "bladder antimuscarinic", "anticholinergics", ["sweat_blocked"], 3, "oral extended-release tablet", "oral", True, False),
    "tolterodine": ("tolterodine", "bladder antimuscarinic", "anticholinergics", ["sweat_blocked"], 3, "oral tablet", "oral", True, False),
    "solifenacin": ("solifenacin", "bladder antimuscarinic", "anticholinergics", ["sweat_blocked"], 3, "oral tablet", "oral", True, False),
    "trospium": ("trospium", "bladder antimuscarinic", "anticholinergics", ["sweat_blocked"], 3, "oral tablet", "oral", True, False),
    "mirabegron": ("mirabegron", "beta-3 agonist (bladder)", "", [], 0, "oral extended-release tablet", "oral", True, False),
    "epinephrine": ("epinephrine", "epinephrine auto-injector", "epinephrine auto-injectors", ["storage_sensitive"], 0, "auto-injector", "intramuscular", True, True),
    "fentanyl": ("fentanyl", "opioid (transdermal)", "fentanyl/opioid patches", ["faster_absorption", "sedation"], 1, "transdermal patch", "transdermal", False, False),
    "oxycodone": ("oxycodone", "opioid", "", ["sedation"], 1, "oral tablet", "oral", False, False),
    "gabapentin": ("gabapentin", "gabapentinoid", "", ["sedation"], 0, "oral capsule", "oral", True, False),
    "ibuprofen": ("ibuprofen", "NSAID", "", ["kidney_stress"], 0, "oral tablet", "oral", True, False),
    "naproxen": ("naproxen", "NSAID", "", ["kidney_stress"], 0, "oral tablet", "oral", True, False),
    "meloxicam": ("meloxicam", "NSAID", "", ["kidney_stress"], 0, "oral tablet", "oral", True, False),
    "diclofenac": ("diclofenac", "NSAID", "", ["kidney_stress"], 0, "oral tablet", "oral", True, False),
    "omeprazole": ("omeprazole", "proton pump inhibitor", "", [], 0, "oral delayed-release capsule", "oral", True, False),
    "levothyroxine": ("levothyroxine", "thyroid hormone", "", [], 0, "oral tablet", "oral", True, False),
    "aspirin": ("aspirin", "antiplatelet (low dose)", "", [], 0, "oral tablet", "oral", True, False),
    "cholecalciferol": ("cholecalciferol", "vitamin D", "", [], 0, "oral capsule", "oral", True, False),
    "acetaminophen": ("acetaminophen", "analgesic", "", [], 0, "oral tablet", "oral", True, False),
    "albuterol": ("albuterol", "short-acting beta agonist", "", ["storage_sensitive"], 0, "metered-dose inhaler", "inhalation", True, False),
    "fluticasone": ("fluticasone", "inhaled corticosteroid", "", [], 0, "metered-dose inhaler", "inhalation", True, False),
    "budesonide/formoterol": ("budesonide / formoterol", "ICS/LABA", "", [], 0, "metered-dose inhaler", "inhalation", True, False),
    "montelukast": ("montelukast", "leukotriene antagonist", "", [], 0, "oral tablet", "oral", True, False),
    "cetirizine": ("cetirizine", "antihistamine (2nd gen)", "", [], 1, "oral tablet", "oral", True, False),
    "diphenhydramine": ("diphenhydramine", "antihistamine (1st gen)", "anticholinergics", ["sweat_blocked", "sedation"], 3, "oral capsule", "oral", True, False),
    "hydroxyzine": ("hydroxyzine", "antihistamine (1st gen)", "anticholinergics", ["sweat_blocked", "sedation"], 3, "oral tablet", "oral", True, False),
}
ANTIPSYCHOTICS = {"risperidone", "olanzapine", "aripiprazole", "quetiapine", "haloperidol",
                  "paliperidone", "clozapine", "ziprasidone", "lurasidone"}
RAAS = {"lisinopril", "losartan", "sacubitril/valsartan"}
DIURETICS = {"furosemide", "torsemide", "bumetanide", "hydrochlorothiazide", "chlorthalidone",
             "spironolactone"}
THIAZIDES = {"hydrochlorothiazide", "chlorthalidone"}
LOOPS = {"furosemide", "torsemide", "bumetanide"}
NSAIDS = {"ibuprofen", "naproxen", "meloxicam", "diclofenac"}
SSRIS = {"sertraline", "escitalopram", "fluoxetine", "citalopram", "paroxetine"}
SGLT2 = {"empagliflozin", "dapagliflozin"}
NARROW_KIDNEY = {"lithium", "digoxin"}
OTC_POSSIBLE = {"ibuprofen", "naproxen", "acetaminophen", "diphenhydramine", "cetirizine", "aspirin",
                "cholecalciferol", "omeprazole"}

CONDITIONS = {  # key: (ICD-10-CM, display)
    "hypertension": ("I10", "Essential (primary) hypertension"),
    "type2_diabetes": ("E11.9", "Type 2 diabetes mellitus without complications"),
    "type1_diabetes": ("E10.9", "Type 1 diabetes mellitus without complications"),
    "heart_failure": ("I50.9", "Heart failure, unspecified"),
    "ckd": ("N18.9", "Chronic kidney disease, unspecified"),
    "schizophrenia": ("F20.9", "Schizophrenia, unspecified"),
    "bipolar": ("F31.9", "Bipolar disorder, unspecified"),
    "depression": ("F32.A", "Depression, unspecified"),
    "epilepsy": ("G40.909", "Epilepsy, unspecified, not intractable, without status epilepticus"),
    "migraine": ("G43.909", "Migraine, unspecified, not intractable, without status migrainosus"),
    "adhd": ("F90.9", "Attention-deficit hyperactivity disorder, unspecified type"),
    "overactive_bladder": ("N32.81", "Overactive bladder"),
    "anaphylaxis_risk_food": ("Z91.010", "Allergy to peanuts"),
    "anaphylaxis_risk_insect": ("Z91.030", "Bee allergy status"),
    "chronic_pain": ("G89.29", "Other chronic pain"),
    "osteoarthritis": ("M19.90", "Unspecified osteoarthritis, unspecified site"),
    "asthma": ("J45.909", "Unspecified asthma, uncomplicated"),
    "hyperlipidemia": ("E78.5", "Hyperlipidemia, unspecified"),
    "insomnia": ("G47.00", "Insomnia, unspecified"),
    "anxiety": ("F41.9", "Anxiety disorder, unspecified"),
    "gerd": ("K21.9", "Gastro-esophageal reflux disease without esophagitis"),
    "hypothyroidism": ("E03.9", "Hypothyroidism, unspecified"),
}


def load_rxnorm(refresh):
    path = OUT / "rxnorm_cache.json"
    cache = {} if (refresh or not path.exists()) else json.loads(path.read_text()).get("drugs", {})
    for key, spec in DRUGS.items():
        if key in cache:
            continue
        name = spec[0]
        url = "https://rxnav.nlm.nih.gov/REST/rxcui.json?name=" + urllib.parse.quote(name)
        ids = get_json(url).get("idGroup", {}).get("rxnormId", [])
        if not ids:
            ids = get_json(url + "&search=2").get("idGroup", {}).get("rxnormId", [])
        rxcui = ids[0] if ids else None
        props = {}
        if rxcui:
            props = get_json("https://rxnav.nlm.nih.gov/REST/rxcui/%s/properties.json" % rxcui
                             ).get("properties", {}) or {}
        cache[key] = {"lookup_name": name, "rxcui": rxcui, "rxnorm_name": props.get("name"),
                      "tty": props.get("tty")}
        time.sleep(0.07)  # RxNav asks for <= 20 requests/second
    path.write_text(json.dumps({
        "source": "NIH NLM RxNav REST API, https://rxnav.nlm.nih.gov/REST/rxcui.json?name=...",
        "accessed": REF_DATE.isoformat(), "drugs": cache}, indent=1, sort_keys=True))
    return cache


def verify_icd(refresh):
    path = SRC / "icd10cm_cache.json"
    cache = {} if (refresh or not path.exists()) else json.loads(path.read_text())
    for key, (code, _) in CONDITIONS.items():
        if code in cache:
            continue
        r = get_json("https://clinicaltables.nlm.nih.gov/api/icd10cm/v3/search?sf=code&terms="
                     + urllib.parse.quote(code))
        hit = [d for c, d in (r[3] or []) if c == code]
        cache[code] = hit[0] if hit else None
    path.write_text(json.dumps(cache, indent=1, sort_keys=True))
    bad = [c for c, d in cache.items() if not d]
    if bad:
        raise SystemExit("ICD-10-CM codes not found: %s" % bad)
    return cache


# ----------------------------------------------------------------------------- geometry
def ring_contains(ring, x, y):
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-15) + xi:
            inside = not inside
        j = i
    return inside


def geom_contains(geom, x, y):
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    for poly in polys:
        if ring_contains(poly[0], x, y) and not any(ring_contains(h, x, y) for h in poly[1:]):
            return True
    return False


def bbox(geom):
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    xs = [p[0] for poly in polys for p in poly[0]]
    ys = [p[1] for poly in polys for p in poly[0]]
    return min(xs), min(ys), max(xs), max(ys)


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def offset(lat, lon, km, bearing_deg):
    b = math.radians(bearing_deg)
    dlat = km * math.cos(b) / 111.32
    dlon = km * math.sin(b) / (111.32 * math.cos(math.radians(lat)))
    return round(lat + dlat, 6), round(lon + dlon, 6)


class Geo:
    def __init__(self, zcta, parks):
        self.zips = {f["properties"]["ZCTA5"]: f["geometry"] for f in zcta["features"]}
        self.parks = [p["multipolygon"] for p in parks if p.get("multipolygon")]
        self.park_boxes = [bbox(g) for g in self.parks]

    def in_excluded(self, x, y):
        lx, ly, hx, hy = RESERVOIR_BOX
        if lx <= x <= hx and ly <= y <= hy:
            return True
        for g, (a, b, c, d) in zip(self.parks, self.park_boxes):
            if a <= x <= c and b <= y <= d and geom_contains(g, x, y):
                return True
        return False

    def random_home(self, rng, z):
        g = self.zips[z]
        a, b, c, d = bbox(g)
        for _ in range(5000):
            x, y = rng.uniform(a, c), rng.uniform(b, d)
            if geom_contains(g, x, y) and not self.in_excluded(x, y):
                return round(y, 6), round(x, 6)
        raise RuntimeError("could not place point in " + z)


# ----------------------------------------------------------------------------- names
FIRST_F = ["Rosa", "Maria", "Carmen", "Ana", "Luz", "Yesenia", "Dolores", "Gladys", "Keisha",
           "Tanisha", "Aaliyah", "Fatoumata", "Aminata", "Mariama", "Esperanza", "Milagros",
           "Daisy", "Yolanda", "Brenda", "Josefina", "Altagracia", "Nayeli", "Camila", "Valeria",
           "Jasmine", "Imani", "Nia", "Sofia", "Ruth", "Gloria", "Denise", "Marisol", "Ivelisse",
           "Ama", "Hawa", "Nasrin", "Layla", "Kiara", "Paola", "Evelyn"]
FIRST_M = ["Luis", "Jose", "Juan", "Carlos", "Miguel", "Rafael", "Angel", "Hector", "Wilfredo",
           "Darnell", "Marcus", "Andre", "Tyrone", "Mamadou", "Ibrahima", "Kwame", "Kofi",
           "Ramon", "Julio", "Victor", "Edwin", "Nelson", "Dante", "Jayden", "Elijah", "Mateo",
           "Santiago", "Javier", "Reginald", "Malik", "Omar", "Rahim", "Samuel", "Felix",
           "Isaiah", "Kevin", "Pedro", "Ernesto", "Moussa", "Anthony"]
LAST = ["Quintero", "Rivera", "Santiago", "Batista", "Almonte", "Peralta", "Feliz", "Cruz",
        "Ortiz", "Delgado", "Washington", "Jefferson", "Brooks", "Coleman", "Diallo", "Bah",
        "Toure", "Mensah", "Owusu", "Rahman", "Uddin", "Morales", "Reyes", "Vargas", "Castillo",
        "Guzman", "Polanco", "Tavarez", "Mercado", "Holloway", "Simmons", "Grant", "Fofana",
        "Camara", "Asante", "Nunez", "Rosario", "Pagan", "Velez", "Medina", "Acevedo", "Lugo"]


def synth_name(rng, sex):
    first = rng.choice(FIRST_F if sex == "female" else FIRST_M)
    return "%s%d" % (first, rng.randint(100, 999)), "%s%d" % (rng.choice(LAST), rng.randint(100, 999))


def fake_phone(rng):
    return "+1-718-555-01%02d" % rng.randint(0, 99)


# ----------------------------------------------------------------------------- sampling helpers
def wchoice(rng, items):
    """items: list of (value, weight)."""
    tot = sum(w for _, w in items)
    r = rng.uniform(0, tot)
    acc = 0.0
    for v, w in items:
        acc += w
        if r <= acc:
            return v
    return items[-1][0]


AGE_BANDS = [((2, 5), .02), ((6, 11), .05), ((12, 17), .06), ((18, 29), .08), ((30, 44), .16),
             ((45, 64), .35), ((65, 74), .16), ((75, 94), .12)]


def band(age):
    if age < 18:
        return "child"
    if age < 45:
        return "18-44"
    if age < 65:
        return "45-64"
    return "65+"


# Adult condition probabilities by band (18-44, 45-64, 65+); see assumption A4.
COND_P = {
    "hypertension": (.12, .48, .72),
    "type2_diabetes": (.05, .22, .32),
    "heart_failure": (.0, .03, .10),
    "ckd": (.01, .05, .13),
    "asthma": (.13, .12, .10),
    "depression": (.17, .18, .15),
    "schizophrenia": (.05, .04, .015),
    "bipolar": (.045, .035, .015),
    "epilepsy": (.012, .012, .012),
    "migraine": (.06, .05, .015),
    "adhd": (.03, .01, .0),
    "overactive_bladder": (.01, .06, .14),
    "anaphylaxis_risk": (.03, .02, .015),
    "chronic_pain": (.02, .08, .10),
    "osteoarthritis": (.05, .22, .38),
}
BI = {"18-44": 0, "45-64": 1, "65+": 2}


def sample_conditions(rng, age, sex):
    c = set()
    b = band(age)
    if b == "child":
        if rng.random() < .35:
            c.add("asthma")
        if age >= 6 and rng.random() < (.30 if age >= 12 else .22) * (1.3 if sex == "male" else .7):
            c.add("adhd")
        if rng.random() < .09:
            c.add("epilepsy")
        if age >= 10 and rng.random() < .04:
            c.add("migraine")
        if rng.random() < .13:
            c.add("anaphylaxis_risk")
        if age >= 4 and rng.random() < .03:
            c.add("type1_diabetes")
        if not c:
            c.add(wchoice(rng, [("asthma", 4), ("adhd" if age >= 6 else "asthma", 3),
                                ("anaphylaxis_risk", 2), ("epilepsy", 1)]))
        return c
    i = BI[b]
    p = lambda k: COND_P[k][i]  # noqa: E731
    if rng.random() < p("hypertension"):
        c.add("hypertension")
    if rng.random() < .006:
        c.add("type1_diabetes")
    elif rng.random() < p("type2_diabetes") * (1.3 if "hypertension" in c else .8):
        c.add("type2_diabetes")
    if rng.random() < p("heart_failure") * (1.5 if "hypertension" in c else .5):
        c.add("heart_failure")
    if rng.random() < p("ckd") * (1.6 if c & {"hypertension", "type2_diabetes"} else .5):
        c.add("ckd")
    sexf = 1.3 if sex == "female" else .7
    for k, mult in [("asthma", 1), ("depression", sexf), ("schizophrenia", 1.3 if sex == "male" else .7),
                    ("bipolar", 1), ("epilepsy", 1), ("migraine", 1.6 if sex == "female" else .4),
                    ("adhd", 1), ("overactive_bladder", sexf), ("anaphylaxis_risk", 1),
                    ("chronic_pain", 1), ("osteoarthritis", sexf)]:
        if rng.random() < p(k) * mult:
            c.add(k)
    if "schizophrenia" in c:
        c.discard("bipolar")
    if not c:
        c.add(wchoice(rng, [("hypertension", 5), ("depression", 3), ("asthma", 2),
                            ("osteoarthritis", 2), ("type2_diabetes", 2)]))
    return c


# ----------------------------------------------------------------------------- medications
def build_meds(rng, age, conds):
    meds = {}  # generic -> indication

    def add(g, why):
        meds.setdefault(g, why)

    def has(*gs):
        return any(g in meds for g in gs)

    adult = age >= 18
    # Cardio-renal-metabolic
    if "heart_failure" in conds:
        if rng.random() < .85:
            add(wchoice(rng, [("furosemide", 70), ("torsemide", 20), ("bumetanide", 10)]), "heart_failure")
        if rng.random() < .80:
            add(rng.choice(["carvedilol", "metoprolol"]), "heart_failure")
        r = rng.random()
        if r < .30:
            add("sacubitril/valsartan", "heart_failure")
        elif r < .85:
            add(rng.choice(["lisinopril", "losartan"]), "heart_failure")
        if rng.random() < .35:
            add("spironolactone", "heart_failure")
        if rng.random() < .40:
            add(rng.choice(["empagliflozin", "dapagliflozin"]), "heart_failure")
        if rng.random() < .06:
            add("digoxin", "heart_failure")
    if "hypertension" in conds:
        # total number of BP-lowering agents (1: 45%, 2: 35%, 3: 20%); HF agents count toward it
        k = wchoice(rng, [(1, 45), (2, 35), (3, 20)])
        already = sum(1 for g in meds if g in RAAS | DIURETICS | {"carvedilol", "metoprolol"})
        cands = []
        if not has(*RAAS) and rng.random() < .70:
            cands.append(wchoice(rng, [("lisinopril", 55), ("losartan", 45)]))
        rest = ["amlodipine"]
        if not has(*LOOPS):
            rest.append(wchoice(rng, [("hydrochlorothiazide", 65), ("chlorthalidone", 35)]))
        if not has("carvedilol", "metoprolol"):
            rest.append("metoprolol")
        rest = rest[:1] + rng.sample(rest[1:], len(rest) - 1)
        if rng.random() < .35:  # thiazide before CCB in ~1/3 (common in Black/Hispanic patients)
            rest = rest[1:2] + rest[:1] + rest[2:]
        cands += rest
        for g in cands[:max(k - already, 0)]:
            add(g, "hypertension")
        if not already and not any(v == "hypertension" for v in meds.values()):
            add("amlodipine", "hypertension")
    if "type2_diabetes" in conds:
        if rng.random() < (.55 if "ckd" in conds else .78):
            add("metformin", "type2_diabetes")
        if rng.random() < .22:
            if not has(*SGLT2):
                add(rng.choice(["empagliflozin", "dapagliflozin"]), "type2_diabetes")
        if rng.random() < .25:
            add("insulin glargine", "type2_diabetes")
            if rng.random() < .4:
                add("insulin lispro", "type2_diabetes")
        if rng.random() < .15:
            add("glipizide", "type2_diabetes")
        if rng.random() < .12:
            add("semaglutide", "type2_diabetes")
        if not any(meds.get(g) == "type2_diabetes" for g in meds):
            add("metformin", "type2_diabetes")
        if rng.random() < .55 and not has(*RAAS):
            add(rng.choice(["lisinopril", "losartan"]), "type2_diabetes")
    pump = False
    if "type1_diabetes" in conds:
        add("insulin lispro", "type1_diabetes")
        pump = rng.random() < .35
        if not pump:
            add("insulin glargine", "type1_diabetes")
    if "ckd" in conds:
        if not has(*RAAS) and rng.random() < .6:
            add(rng.choice(["lisinopril", "losartan"]), "ckd")
        if not has(*LOOPS) and rng.random() < .2:
            add("furosemide", "ckd")
    if adult and age >= 40 and conds & {"type2_diabetes", "hypertension", "heart_failure", "ckd"}:
        if rng.random() < (.70 if "type2_diabetes" in conds else .40):
            add("atorvastatin", "hyperlipidemia")
    # Behavioural health
    if "schizophrenia" in conds:
        n = wchoice(rng, [(1, 80), (2, 18), (3, 2)])
        pool = [("risperidone", 20), ("olanzapine", 18), ("aripiprazole", 20), ("quetiapine", 12),
                ("haloperidol", 10), ("paliperidone", 8), ("clozapine", 7), ("ziprasidone", 5)]
        while sum(1 for g in meds if g in ANTIPSYCHOTICS) < n:
            add(wchoice(rng, pool), "schizophrenia")
        if rng.random() < (.5 if has("haloperidol", "paliperidone") else .1):
            add("benztropine", "schizophrenia")
    if "bipolar" in conds:
        if rng.random() < .35:
            add("lithium", "bipolar")
        r = rng.random()
        if r < .25:
            add("divalproex", "bipolar")
        elif r < .45:
            add("lamotrigine", "bipolar")
        if rng.random() < .5 or not any(v == "bipolar" for v in meds.values()):
            add(wchoice(rng, [("quetiapine", 35), ("aripiprazole", 30), ("olanzapine", 20),
                              ("lurasidone", 15)]), "bipolar")
    if "depression" in conds:
        r = rng.random()
        if r < .65:
            add(wchoice(rng, [("sertraline", 35), ("escitalopram", 25), ("fluoxetine", 20),
                              ("citalopram", 12), ("paroxetine", 8)]), "depression")
        elif r < .77:
            add("bupropion", "depression")
        elif r < .87:
            add(rng.choice(["duloxetine", "venlafaxine"]), "depression")
        elif r < .94:
            add("mirtazapine", "depression")
        else:
            add("amitriptyline", "depression")
        if rng.random() < .15:
            add("trazodone", "insomnia")
    # Neuro
    if "epilepsy" in conds:
        pool = ([("levetiracetam", 40), ("topiramate", 30), ("oxcarbazepine", 15), ("lamotrigine", 10),
                 ("zonisamide", 5)] if not adult else
                [("levetiracetam", 45), ("lamotrigine", 20), ("topiramate", 15), ("carbamazepine", 8),
                 ("oxcarbazepine", 7), ("zonisamide", 5)])
        add(wchoice(rng, pool), "epilepsy")
    if "migraine" in conds:
        if rng.random() < .45:
            add(wchoice(rng, [("topiramate", 45), ("propranolol", 30), ("amitriptyline", 25)]), "migraine")
        if age >= 12 and rng.random() < .6:
            add("sumatriptan", "migraine")
        if rng.random() < .5:
            add(rng.choice(["ibuprofen", "naproxen"]), "migraine")
        if not any(v == "migraine" for v in meds.values()):
            add("ibuprofen", "migraine")
    if "adhd" in conds:
        if rng.random() < .85:
            add(wchoice(rng, [("methylphenidate", 50), ("amphetamine mixed salts", 30),
                              ("lisdexamfetamine", 20)]), "adhd")
        if rng.random() < .15 or not any(v == "adhd" for v in meds.values()):
            add("guanfacine", "adhd")
    # Bladder, allergy, pain, airway
    if "overactive_bladder" in conds:
        add(wchoice(rng, [("oxybutynin", 50), ("tolterodine", 12), ("solifenacin", 15),
                          ("trospium", 5), ("mirabegron", 18)]), "overactive_bladder")
    if "anaphylaxis_risk" in conds:
        add("epinephrine", "anaphylaxis_risk")
        if rng.random() < .3:
            add("cetirizine", "anaphylaxis_risk")
    if "chronic_pain" in conds:
        if rng.random() < .45:
            add(rng.choice(["ibuprofen", "naproxen", "meloxicam"]), "chronic_pain")
        if rng.random() < .30:
            add("gabapentin", "chronic_pain")
        if rng.random() < .12 and not has(*SSRIS):
            add("duloxetine", "chronic_pain")
        if rng.random() < .10:
            add("oxycodone", "chronic_pain")
        if rng.random() < .20:
            add("fentanyl", "chronic_pain")
        if not any(v == "chronic_pain" for v in meds.values()):
            add("acetaminophen", "chronic_pain")
    if "osteoarthritis" in conds:
        if rng.random() < .35:
            add(wchoice(rng, [("ibuprofen", 35), ("naproxen", 30), ("meloxicam", 25), ("diclofenac", 10)]),
                "osteoarthritis")
        if rng.random() < .45:
            add("acetaminophen", "osteoarthritis")
        if not any(v == "osteoarthritis" for v in meds.values()):
            add("acetaminophen", "osteoarthritis")
    if "asthma" in conds:
        if rng.random() < .95:
            add("albuterol", "asthma")
        if rng.random() < .55:
            add(wchoice(rng, [("fluticasone", 50), ("budesonide/formoterol", 50)]), "asthma")
        if rng.random() < .2:
            add("montelukast", "asthma")
        if not any(v == "asthma" for v in meds.values()):
            add("albuterol", "asthma")
    # Common non-heat background medicines (assumption A16) so med lists look like real lists
    if age >= 40 and rng.random() < .15:
        add("omeprazole", "gerd")
    if age >= 30 and rng.random() < (.09 if len(meds) and age >= 18 else 0) * 1:
        add("levothyroxine", "hypothyroidism")
    if age >= 50 and conds & {"type2_diabetes", "heart_failure", "ckd"} and rng.random() < .35:
        add("aspirin", "cardiovascular_prevention")
    if age >= 50 and rng.random() < .15:
        add("cholecalciferol", "vitamin_d_supplement")
    # OTC / sleep anticholinergics in adults (assumption: 5% of 45+, 3% hydroxyzine for anxiety)
    if age >= 45 and rng.random() < .05:
        add("diphenhydramine", "insomnia")
    if adult and rng.random() < .03:
        add("hydroxyzine", "anxiety")
    return meds, pump


def combination_flags(meds):
    g = set(meds)
    f = []
    if g & DIURETICS and g & RAAS and g & NSAIDS:
        f.append("triple_whammy")
    if len(g & ANTIPSYCHOTICS) >= 2:
        f.append("antipsychotic_polypharmacy")
    if "lithium" in g:
        if g & THIAZIDES:
            f.append("lithium_plus_thiazide")
        if g & NSAIDS:
            f.append("lithium_plus_nsaid")
        if g & RAAS:
            f.append("lithium_plus_acei_arb")
        if g & LOOPS:
            f.append("lithium_plus_loop")
    ac = [x for x in g if DRUGS[x][4] >= 1]
    if len(ac) >= 2 and sum(DRUGS[x][4] for x in g) >= 3:
        f.append("anticholinergic_stack")
    if g & RAAS and g & DIURETICS:
        f.append("acei_arb_plus_diuretic")
    if g & THIAZIDES and g & SSRIS:
        f.append("thiazide_plus_ssri")
    if (g & (DIURETICS | SGLT2)) and (g & NARROW_KIDNEY):
        f.append("fluid_loss_plus_narrow_margin_drug")
    if len(g) >= 5:
        f.append("polypharmacy_5plus")
    return f


# ----------------------------------------------------------------------------- questionnaire
CHECKIN_OPTIONS = [("10:00;16:00", 55), ("09:00;14:00;18:00", 15), ("08:00;13:00;17:00", 10),
                   ("11:00;17:00", 12), ("10:00;14:00;16:00;18:00", 8)]


def make_questionnaire(rng, p, meds, pump):
    age, b = p["age"], band(p["age"])
    conds = p["conditions"]
    child = age < 18
    lives_alone = False if child else rng.random() < {"18-44": .10, "45-64": .20, "65+": .33}[b]
    r = rng.random()
    ac_yes = .84 - (.06 if (b == "65+" and lives_alone) else 0)
    ac = "no" if r > ac_yes else ("yes_but_cost_limits_use" if rng.random() < .15 else "yes")
    if child:
        day = wchoice(rng, [("home", 35), ("indoors_ac", 30), ("outdoors_or_physical_work", 35)])
    elif b == "65+":
        day = wchoice(rng, [("home", 65), ("indoors_ac", 30), ("outdoors_or_physical_work", 5)])
    else:
        hw = 55 if conds & {"schizophrenia", "bipolar"} else 40
        day = wchoice(rng, [("home", hw), ("indoors_ac", 45), ("outdoors_or_physical_work", 15)])
    btype = wchoice(rng, [("10plus_units", 67.5), ("small_building", 32.5)])
    if btype == "10plus_units":
        elevator = rng.random() < .70
        floor = (wchoice(rng, [(f, 1.0 / (1 + .12 * f)) for f in range(1, 21)]) if elevator
                 else rng.randint(1, 6))
    else:
        elevator, floor = False, rng.randint(1, 3)
    mob_p = {"child": .02, "18-44": .05, "45-64": .20, "65+": .38}[b]
    if conds & {"heart_failure", "chronic_pain"}:
        mob_p += .2
    step_free = rng.random() < mob_p
    if step_free:
        reach = wchoice(rng, [("yes", 35), ("with_help", 45), ("no", 20)])
    else:
        reach = wchoice(rng, [("yes", 80), ("with_help", 15), ("no", 5)])
    if "heart_failure" in conds:
        fluid = rng.random() < .6
    elif "ckd" in conds:
        fluid = rng.random() < .15
    else:
        fluid = False
    smartphone = rng.random() < (.70 if b == "65+" else .92)
    if not smartphone:
        channel = wchoice(rng, [("sms_only", 60), ("voice_call", 40)])
    else:
        channel = wchoice(rng, [("app_and_sms", 75), ("sms_only", 20), ("voice_call", 5)])
    equip = []
    if pump:
        equip.append("insulin_pump")
    if age >= 45 and rng.random() < .06:
        equip.append("cpap")
    if age >= 65 and rng.random() < (.12 if "heart_failure" in conds else .03):
        equip.append("home_oxygen")
    if "asthma" in conds and rng.random() < .15:
        equip.append("nebulizer")
    fridge = sorted(g for g in meds if DRUGS[g][8] and g != "epinephrine")
    hot_p = (.6 if ac == "no" else .25 if ac.startswith("yes_but") else .1) + (.15 if floor >= 5 else 0)
    home_hot = "often" if rng.random() < hot_p else wchoice(rng, [("sometimes", 50), ("rarely", 50)])
    outdoor = day == "outdoors_or_physical_work" or (child and rng.random() < .3)
    return {
        "respondent": "parent_or_caregiver" if child or (age >= 80 and rng.random() < .2) else "self",
        "q1_working_ac": ac,
        "q2_day_location": day,
        "q3_floor": floor,
        "building_type": btype,
        "building_has_elevator": elevator,
        "q4_lives_alone": lives_alone,
        "q5_can_reach_cool_place": reach,
        "mobility_step_free_needed": step_free,
        "fluid_restricted": fluid,
        "fluid_restriction_set_by": "clinician" if fluid else "",
        "preferred_language": p["language"],
        "alert_opt_in": rng.random() < .88,
        "alert_channel": channel,
        "has_smartphone": smartphone,
        "checkin_times": wchoice(rng, CHECKIN_OPTIONS),
        "power_dependent_equipment": ";".join(equip),
        "fridge_medicines": ";".join(fridge),
        "mail_order_drop_location": "",  # filled after mail-order sampling
        "outdoor_work_or_sports": outdoor,
        "windows_open": rng.random() < .9,
        "home_gets_hot": home_hot,
        "someone_checks_on_them": (rng.random() < .55) if lives_alone else True,
        "leaves_home_most_days": rng.random() < (.45 if step_free else .8),
        "knows_heat_illness_signs": rng.random() < .45,
        "stable_housing": rng.random() < .9,
        "answered_on": (REF_DATE - dt.timedelta(days=rng.randint(10, 400))).isoformat(),
    }


# ----------------------------------------------------------------------------- contacts
LOC_TYPES = [("same_building", 10, (0.0, 0.05)), ("walkable_same_area", 30, (0.2, 1.5)),
             ("elsewhere_bronx", 30, (1.5, 6.0)), ("elsewhere_nyc", 20, (6.0, 20.0)),
             ("out_of_area", 10, (30.0, 150.0))]
BEARINGS = {"same_building": (0, 360), "walkable_same_area": (0, 360), "elsewhere_bronx": (20, 200),
            "elsewhere_nyc": (100, 260), "out_of_area": (200, 440)}


def naive_travel(km):
    d = km * 1.3
    if km <= 1.5:
        return round(d * 1000 / 0.8 / 60, 1), "walk"
    if km <= 20:
        return round(10 + d / 15 * 60, 1), "transit"
    return round(d / 30 * 60, 1), "drive"


def make_contact(rng, p, idx, loc_type=None, km=None, relationship=None, bearing=None):
    if loc_type is None:
        loc_type = wchoice(rng, [(t, w) for t, w, _ in LOC_TYPES])
    rng_km = dict((t, r) for t, _, r in LOC_TYPES)[loc_type]
    if km is None:
        km = rng.uniform(*rng_km)
    if bearing is None:
        bearing = rng.uniform(*BEARINGS[loc_type]) % 360
    lat, lon = offset(p["home_lat"], p["home_lon"], km, bearing)
    if relationship is None:
        if p["age"] < 18:
            relationship = wchoice(rng, [("grandparent", 35), ("aunt_or_uncle", 25),
                                         ("other_parent", 20), ("family_friend", 10), ("neighbor", 10)])
        elif loc_type == "same_building":
            relationship = wchoice(rng, [("neighbor", 60), ("friend", 25), ("relative", 15)])
        else:
            relationship = wchoice(rng, [("daughter", 22), ("son", 16), ("sibling", 18), ("friend", 16),
                                         ("niece_or_nephew", 8), ("partner", 6), ("case_manager", 4),
                                         ("neighbor", 10)])
    sex = "female" if rng.random() < .62 else "male"
    gn, fn = synth_name(rng, sex)
    km_real = haversine_km(p["home_lat"], p["home_lon"], lat, lon)
    tmin, mode = naive_travel(km_real)
    return {
        "contact_id": "%s-C%d" % (p["patient_id"], idx), "patient_id": p["patient_id"],
        "synthetic": True, "priority": idx, "given_name": gn, "family_name": fn,
        "relationship": relationship, "phone": fake_phone(rng),
        "preferred_language": p["language"] if rng.random() < .8 else "en",
        "location_type": loc_type, "lat": lat, "lon": lon,
        "straight_line_km": round(km_real, 3), "naive_travel_mode": mode,
        "naive_travel_min": tmin, "naive_qualifies_60min": tmin <= 30,
        "naive_qualifies_90min": tmin <= 60,
    }


# ----------------------------------------------------------------------------- patients
def base_patient(pid, rng, age, sex, zip_, geo, language=None):
    gn, fn = synth_name(rng, sex)
    lat, lon = geo.random_home(rng, zip_)
    if language is None:
        b = band(age)
        es = {"child": .35, "18-44": .30, "45-64": .40, "65+": .50}[b]
        r = rng.random()
        language = "es" if r < es else ("other" if r < es + .03 else "en")
    other_lang = rng.choice(["fr", "bn", "ar"]) if language == "other" else ""
    bday = REF_DATE.replace(year=REF_DATE.year - age) - dt.timedelta(days=rng.randint(1, 364))
    return {"patient_id": pid, "synthetic": True, "story_patient": False, "story_label": "",
            "given_name": gn, "family_name": fn, "sex": sex, "birth_date": bday.isoformat(),
            "age": age, "zip": zip_, "home_lat": lat, "home_lon": lon,
            "language": other_lang or language,
            "interpreter_needed": language != "en" and (language == "other" or rng.random() < .55),
            "phone": fake_phone(rng), "coverage_topup": False}


STORIES = [
    # id, label, age, sex, zip, lang, conditions, meds{generic: indication}, q overrides, mail meds, contacts
    ("S01", "78F on a loop diuretic + oxybutynin, no AC, lives alone, 6th-floor walk-up; only contact is out of state",
     78, "female", "10457", "es", ["heart_failure", "hypertension", "overactive_bladder"],
     {"furosemide": "heart_failure", "oxybutynin": "overactive_bladder", "lisinopril": "hypertension",
      "metoprolol": "heart_failure"},
     {"q1_working_ac": "no", "q4_lives_alone": True, "q3_floor": 6, "building_has_elevator": False,
      "building_type": "10plus_units", "q2_day_location": "home", "mobility_step_free_needed": True,
      "q5_can_reach_cool_place": "with_help", "fluid_restricted": True, "fluid_restriction_set_by": "clinician",
      "has_smartphone": False, "alert_channel": "voice_call", "someone_checks_on_them": False,
      "home_gets_hot": "often", "alert_opt_in": True},
     [], [("out_of_area", 95.0, "daughter", 250)]),
    ("S02", "16M on a stimulant who plays outdoor summer soccer; also has asthma",
     16, "male", "10458", "en", ["adhd", "asthma"],
     {"amphetamine mixed salts": "adhd", "albuterol": "asthma"},
     {"q2_day_location": "outdoors_or_physical_work", "outdoor_work_or_sports": True, "q1_working_ac": "yes",
      "q3_floor": 3, "alert_channel": "app_and_sms", "has_smartphone": True},
     [], [("elsewhere_bronx", 2.4, "aunt_or_uncle", 90)]),
    ("S03", "9F on topiramate for epilepsy; Spanish-speaking parent; outdoor summer day camp",
     9, "female", "10453", "es", ["epilepsy"], {"topiramate": "epilepsy"},
     {"q2_day_location": "outdoors_or_physical_work", "outdoor_work_or_sports": True, "q1_working_ac": "yes_but_cost_limits_use",
      "q3_floor": 4, "respondent": "parent_or_caregiver"},
     [], [("walkable_same_area", 0.6, "grandparent", 40)]),
    ("S04", "44M with schizophrenia on clozapine + haloperidol + benztropine (2 antipsychotics, anticholinergic stack); lives alone",
     44, "male", "10460", "en", ["schizophrenia"],
     {"clozapine": "schizophrenia", "haloperidol": "schizophrenia", "benztropine": "schizophrenia"},
     {"q1_working_ac": "no", "q4_lives_alone": True, "q2_day_location": "home", "q3_floor": 5,
      "building_has_elevator": True, "knows_heat_illness_signs": False, "home_gets_hot": "often"},
     [], [("walkable_same_area", 0.9, "sibling", 10), ("elsewhere_bronx", 3.5, "case_manager", 150)]),
    ("S05", "34F with type 1 diabetes on an insulin pump; insulin and pump supplies by mail, left in the building lobby",
     34, "female", "10458", "en", ["type1_diabetes"], {"insulin lispro": "type1_diabetes"},
     {"power_dependent_equipment": "insulin_pump", "fridge_medicines": "insulin lispro",
      "q2_day_location": "outdoors_or_physical_work", "outdoor_work_or_sports": True, "q1_working_ac": "yes",
      "mail_order_drop_location": "building_lobby"},
     ["insulin lispro"], [("elsewhere_nyc", 9.0, "partner", 200)]),
    ("S06", "58F with bipolar disorder on lithium + hydrochlorothiazide + lisinopril + OTC ibuprofen",
     58, "female", "10452", "es", ["bipolar", "hypertension", "osteoarthritis"],
     {"lithium": "bipolar", "hydrochlorothiazide": "hypertension", "lisinopril": "hypertension",
      "ibuprofen": "osteoarthritis"},
     {"q1_working_ac": "yes_but_cost_limits_use", "q4_lives_alone": True, "q3_floor": 2},
     ["lithium", "hydrochlorothiazide", "lisinopril"], [("elsewhere_bronx", 4.2, "son", 60)]),
    ("S07", "72M with hypertension, type 2 diabetes and CKD: losartan + chlorthalidone + OTC naproxen (triple whammy) + empagliflozin + metformin",
     72, "male", "10456", "es", ["hypertension", "type2_diabetes", "ckd", "osteoarthritis"],
     {"losartan": "hypertension", "chlorthalidone": "hypertension", "naproxen": "osteoarthritis",
      "empagliflozin": "type2_diabetes", "metformin": "type2_diabetes", "atorvastatin": "hyperlipidemia"},
     {"q4_lives_alone": False, "q3_floor": 3, "q1_working_ac": "yes"},
     ["losartan", "chlorthalidone", "empagliflozin", "metformin", "atorvastatin"],
     [("same_building", 0.02, "neighbor", 0)]),
    ("S08", "66F with heart failure (fluid restricted) and chronic pain on a fentanyl patch; lives alone",
     66, "female", "10457", "en", ["heart_failure", "chronic_pain", "hypertension"],
     {"fentanyl": "chronic_pain", "furosemide": "heart_failure", "spironolactone": "heart_failure",
      "sacubitril/valsartan": "heart_failure", "carvedilol": "heart_failure", "gabapentin": "chronic_pain"},
     {"q1_working_ac": "yes_but_cost_limits_use", "q4_lives_alone": True, "fluid_restricted": True,
      "fluid_restriction_set_by": "clinician", "mobility_step_free_needed": True, "q3_floor": 9,
      "building_has_elevator": True, "q5_can_reach_cool_place": "with_help"},
     [], [("elsewhere_nyc", 12.0, "daughter", 205), ("walkable_same_area", 1.1, "friend", 300)]),
    ("S09", "29F with peanut allergy and asthma, works as a bike delivery courier; carries an epinephrine auto-injector all day",
     29, "female", "10468", "en", ["anaphylaxis_risk", "asthma"],
     {"epinephrine": "anaphylaxis_risk", "albuterol": "asthma", "budesonide/formoterol": "asthma"},
     {"q2_day_location": "outdoors_or_physical_work", "outdoor_work_or_sports": True, "q1_working_ac": "no",
      "q4_lives_alone": True, "q3_floor": 5, "mail_order_drop_location": "doorstep_or_hallway"},
     ["epinephrine", "budesonide/formoterol"], [("elsewhere_bronx", 2.0, "sibling", 30)]),
    ("S10", "81M on sertraline + hydrochlorothiazide (low-sodium risk), tolterodine + diphenhydramine (anticholinergic stack); walker, lives alone",
     81, "male", "10453", "es", ["depression", "hypertension", "overactive_bladder", "insomnia"],
     {"sertraline": "depression", "hydrochlorothiazide": "hypertension", "amlodipine": "hypertension",
      "tolterodine": "overactive_bladder", "diphenhydramine": "insomnia"},
     {"q4_lives_alone": True, "mobility_step_free_needed": True, "q5_can_reach_cool_place": "no",
      "q3_floor": 2, "building_has_elevator": False, "q1_working_ac": "yes", "has_smartphone": False,
      "alert_channel": "voice_call", "leaves_home_most_days": False},
     [], [("same_building", 0.03, "neighbor", 0)]),
]


def condition_key_for(rng, c, story=False):
    if c == "anaphylaxis_risk":
        return "anaphylaxis_risk_food" if (story or rng.random() < .75) else "anaphylaxis_risk_insect"
    return c


def finalize(rng, p, meds, pump, q, mail_meds, contacts):
    conds = set(p["conditions"])
    if "atorvastatin" in meds:
        conds.add("hyperlipidemia")
    for g, why in meds.items():
        if why in ("insomnia", "anxiety", "gerd", "hypothyroidism"):
            conds.add(why)
    p["conditions"] = conds
    p["condition_codes"] = sorted(condition_key_for(rng, c, p["story_patient"]) for c in sorted(conds))
    p["meds"] = meds
    p["pump"] = pump
    p["q"] = q
    p["mail_meds"] = mail_meds
    p["contacts"] = contacts
    p["flags"] = combination_flags(meds)
    return p


# Coverage top-up (assumption A17): spec §8.7 class -> (condition, drug, age range)
TOPUP = {
    "lithium": ("bipolar", "lithium", (25, 72)),
    "fentanyl/opioid patches": ("chronic_pain", "fentanyl", (50, 88)),
    "antipsychotics": ("schizophrenia", "risperidone", (20, 65)),
    "loop diuretics": ("heart_failure", "furosemide", (60, 90)),
    "SGLT2 inhibitors": ("type2_diabetes", "empagliflozin", (45, 80)),
    "insulin": ("type2_diabetes", "insulin glargine", (45, 80)),
    "topiramate/zonisamide": ("migraine", "topiramate", (18, 50)),
    "ADHD stimulants": ("adhd", "methylphenidate", (8, 17)),
    "epinephrine auto-injectors": ("anaphylaxis_risk", "epinephrine", (4, 40)),
    "anticholinergics": ("overactive_bladder", "oxybutynin", (60, 90)),
    "SSRIs": ("depression", "sertraline", (25, 75)),
    "thiazides": ("hypertension", "hydrochlorothiazide", (40, 80)),
    "beta blockers": ("hypertension", "metoprolol", (40, 80)),
    "metformin": ("type2_diabetes", "metformin", (40, 80)),
    "ACE inhibitors/ARBs": ("hypertension", "lisinopril", (40, 80)),
}
MIN_PER_CLASS = 5


def make_random_patient(i, rng, geo, zip_weights, force=None):
    pid = "P%04d" % i
    (lo, hi) = force[2] if force else wchoice(rng, AGE_BANDS)
    age = rng.randint(lo, hi)
    sex = ("female" if rng.random() < .56 else "male") if age >= 18 else rng.choice(["female", "male"])
    zip_ = wchoice(rng, zip_weights)
    p = base_patient(pid, rng, age, sex, zip_, geo)
    conds = sample_conditions(rng, age, sex)
    if force:
        conds.add(force[0])
        if force[0] == "schizophrenia":
            conds.discard("bipolar")
    p["conditions"] = conds
    meds, pump = build_meds(rng, age, conds)
    if force and force[1] not in meds:
        if force[0] == "schizophrenia" and set(meds) & ANTIPSYCHOTICS:
            pass
        else:
            meds[force[1]] = force[0]
    p["coverage_topup"] = bool(force)
    q = make_questionnaire(rng, p, meds, pump)
    chronic = [g for g in meds if DRUGS[g][7] and g not in OTC_POSSIBLE]
    mp = .05 if age < 18 else (.30 if age >= 65 and len(chronic) >= 3 else .18)
    mail_meds = []
    if chronic and rng.random() < mp:
        mail_meds = [g for g in chronic if rng.random() < .85] or chronic[:1]
        q["mail_order_drop_location"] = wchoice(rng, [("building_lobby_or_mailroom", 45),
                                                      ("doorstep_or_hallway", 25),
                                                      ("handed_to_patient", 20),
                                                      ("left_with_neighbor_or_super", 10)])
    if pump and not mail_meds and rng.random() < .7:
        mail_meds = ["insulin lispro"]
        q["mail_order_drop_location"] = "building_lobby_or_mailroom"
    n = wchoice(rng, [(0, 20), (1, 55), (2, 25)]) if age >= 18 else wchoice(rng, [(1, 60), (2, 40)])
    contacts = [make_contact(rng, p, k + 1) for k in range(n)]
    return finalize(rng, p, meds, pump, q, mail_meds, contacts)


def make_story_patient(rng, geo, s):
    sid, label, age, sex, zip_, lang, conds, meds, qo, mail, cts = s
    p = base_patient(sid, rng, age, sex, zip_, geo, language=lang)
    p["story_patient"] = True
    p["story_label"] = label
    p["conditions"] = set(conds)
    pump = sid == "S05"
    q = make_questionnaire(rng, p, meds, pump)
    q.update(qo)
    q["preferred_language"] = p["language"]
    if mail and not q["mail_order_drop_location"]:
        q["mail_order_drop_location"] = "building_lobby_or_mailroom"
    contacts = [make_contact(rng, p, k + 1, loc_type=t, km=km, relationship=rel, bearing=br)
                for k, (t, km, rel, br) in enumerate(cts)]
    return finalize(rng, p, dict(meds), pump, q, list(mail), contacts)


# ----------------------------------------------------------------------------- FHIR
SYN_EXT = {"url": "https://example.org/fhir/StructureDefinition/synthetic", "valueBoolean": True}
SYN_TAG = {"system": "http://terminology.hl7.org/CodeSystem/v3-ActReason", "code": "HTEST",
           "display": "test health records"}
LANG_DISPLAY = {"en": "English", "es": "Spanish", "fr": "French", "bn": "Bengali", "ar": "Arabic"}


def meta():
    return {"tag": [SYN_TAG]}


def fhir_for(p, rx):
    pid = p["patient_id"]
    res = []
    patient = {
        "resourceType": "Patient", "id": pid, "meta": meta(), "extension": [SYN_EXT],
        "identifier": [{"system": "https://example.org/synthetic-panel", "value": pid}],
        "name": [{"use": "official", "family": p["family_name"], "given": [p["given_name"]]}],
        "gender": p["sex"], "birthDate": p["birth_date"],
        "telecom": [{"system": "phone", "value": p["phone"], "use": "mobile"}],
        "address": [{"use": "home", "city": "Bronx", "state": "NY", "postalCode": p["zip"],
                     "country": "US", "extension": [{
                         "url": "http://hl7.org/fhir/StructureDefinition/geolocation",
                         "extension": [{"url": "latitude", "valueDecimal": p["home_lat"]},
                                       {"url": "longitude", "valueDecimal": p["home_lon"]}]}]}],
        "communication": [{"language": {"coding": [{"system": "urn:ietf:bcp:47", "code": p["language"],
                                                    "display": LANG_DISPLAY[p["language"]]}]},
                           "preferred": True}],
    }
    if p["story_patient"]:
        patient["extension"].append({"url": "https://example.org/fhir/StructureDefinition/story-patient",
                                     "valueString": p["story_label"]})
    res.append(patient)
    for k, ck in enumerate(p["condition_codes"]):
        code, disp = CONDITIONS[ck]
        res.append({"resourceType": "Condition", "id": "%s-cond%d" % (pid, k + 1), "meta": meta(),
                    "extension": [SYN_EXT],
                    "clinicalStatus": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                                                   "code": "active"}]},
                    "code": {"coding": [{"system": "http://hl7.org/fhir/sid/icd-10-cm", "code": code,
                                         "display": disp}], "text": ck.replace("_", " ")},
                    "subject": {"reference": "Patient/" + pid}})
    for k, (g, why) in enumerate(sorted(p["meds"].items())):
        d = DRUGS[g]
        r = rx[g]
        mr = {"resourceType": "MedicationRequest", "id": "%s-med%d" % (pid, k + 1), "meta": meta(),
              "extension": [SYN_EXT, {"url": "https://example.org/fhir/StructureDefinition/mail-order",
                                      "valueBoolean": g in p["mail_meds"]}],
              "status": "active", "intent": "order",
              "medicationCodeableConcept": {
                  "coding": [{"system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                              "code": r["rxcui"], "display": r["rxnorm_name"]}],
                  "text": "%s %s" % (g, d[5])},
              "subject": {"reference": "Patient/" + pid},
              "authoredOn": p["authored"][g],
              "reasonCode": [{"text": why.replace("_", " ")}],
              "dosageInstruction": [{"route": {"text": d[6]},
                                     "text": "dose intentionally omitted (synthetic demo; spec 10.1)"}]}
        if p["mail_meds"] and g in p["mail_meds"]:
            mr["dispenseRequest"] = {"extension": [{
                "url": "https://example.org/fhir/StructureDefinition/delivery-location",
                "valueString": p["q"]["mail_order_drop_location"]}]}
        res.append(mr)
    for c in p["contacts"]:
        res.append({"resourceType": "RelatedPerson", "id": c["contact_id"], "meta": meta(),
                    "extension": [SYN_EXT, {"url": "http://hl7.org/fhir/StructureDefinition/geolocation",
                                            "extension": [{"url": "latitude", "valueDecimal": c["lat"]},
                                                          {"url": "longitude", "valueDecimal": c["lon"]}]}],
                    "patient": {"reference": "Patient/" + pid}, "active": True,
                    "relationship": [{"text": c["relationship"]}, {"coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/v2-0131", "code": "C",
                        "display": "Emergency Contact"}]}],
                    "name": [{"family": c["family_name"], "given": [c["given_name"]]}],
                    "telecom": [{"system": "phone", "value": c["phone"], "rank": c["priority"]}]})
    items = []
    for k, v in p["q"].items():
        if k == "answered_on":
            continue
        if isinstance(v, bool):
            ans = {"valueBoolean": v}
        elif isinstance(v, int):
            ans = {"valueInteger": v}
        else:
            ans = {"valueString": v}
        items.append({"linkId": k, "answer": [ans]})
    res.append({"resourceType": "QuestionnaireResponse", "id": pid + "-signup", "meta": meta(),
                "extension": [SYN_EXT], "status": "completed",
                "questionnaire": "https://example.org/fhir/Questionnaire/heat-signup-spec-4-5a",
                "subject": {"reference": "Patient/" + pid}, "authored": p["q"]["answered_on"],
                "item": items})
    return res


# ----------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true", help="re-download all cached sources")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    places, kidney, zcta, svi, parks = load_sources(args.refresh)
    rx = load_rxnorm(args.refresh)
    missing = [k for k, v in rx.items() if not v["rxcui"]]
    if missing:
        raise SystemExit("RxNorm lookup failed for: %s" % missing)
    verify_icd(args.refresh)
    geo = Geo(zcta, parks)
    pop = {r["zcta5"]: int(r["totalpopulation"]) for r in places}
    zip_weights = [(z, pop[z] * (1.0 if z in DEMO_ZIPS else 0.5)) for z in ALL_ZIPS]

    rng = random.Random(SEED)
    patients = [make_story_patient(rng, geo, s) for s in STORIES]
    n_random = N_TOTAL - len(STORIES)
    randoms = [make_random_patient(i, rng, geo, zip_weights) for i in range(1, n_random + 1)]

    def class_counts(pl):
        cc = {k: 0 for k in TOPUP}
        for p in pl:
            for k in {DRUGS[g][2] for g in p["meds"] if DRUGS[g][2]}:
                cc[k] += 1
        return cc

    # Coverage top-up: replace trailing random patients with condition-forced ones until every
    # spec §8.7 class has >= MIN_PER_CLASS patients (story patients included in the count).
    cc = class_counts(patients + randoms)
    forced = []
    for cls in TOPUP:
        forced += [cls] * max(0, MIN_PER_CLASS - cc[cls])
    for j, cls in enumerate(forced):
        idx = n_random - len(forced) + j
        randoms[idx] = make_random_patient(idx + 1, rng, geo, zip_weights, force=TOPUP[cls])
    patients += randoms
    for p in patients:
        p["authored"] = {g: (REF_DATE - dt.timedelta(days=rng.randint(14, 900))).isoformat()
                         for g in sorted(p["meds"])}

    # ---- FHIR bundle
    entries = []
    for p in patients:
        for r in fhir_for(p, rx):
            entries.append({"fullUrl": "urn:uuid:%s/%s" % (r["resourceType"], r["id"]), "resource": r})
    bundle = {"resourceType": "Bundle", "id": "missing-label-synthetic-panel", "type": "collection",
              "meta": {"tag": [SYN_TAG]}, "extension": [SYN_EXT],
              "timestamp": REF_DATE.isoformat() + "T00:00:00Z", "entry": entries}
    (OUT / "patients_fhir.json").write_text(json.dumps(bundle, indent=1))

    # ---- CSVs
    def wcsv(name, rows, cols):
        with open(OUT / name, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            for r in rows:
                w.writerow({c: (str(r[c]).lower() if isinstance(r[c], bool) else r[c]) for c in cols})

    prow, mrow, qrow, crow = [], [], [], []
    for p in patients:
        meds = p["meds"]
        heat_classes = sorted({DRUGS[g][2] for g in meds if DRUGS[g][2]})
        nearest = min((c["straight_line_km"] for c in p["contacts"]), default="")
        prow.append({
            "patient_id": p["patient_id"], "synthetic": True, "story_patient": p["story_patient"],
            "story_label": p["story_label"], "coverage_topup": p["coverage_topup"], "given_name": p["given_name"], "family_name": p["family_name"],
            "sex": p["sex"], "birth_date": p["birth_date"], "age": p["age"], "age_band": band(p["age"]),
            "zip": p["zip"], "demo_zip": p["zip"] in DEMO_ZIPS, "home_lat": p["home_lat"],
            "home_lon": p["home_lon"], "preferred_language": p["language"],
            "interpreter_needed": p["interpreter_needed"], "phone": p["phone"],
            "conditions": ";".join(sorted(p["conditions"])),
            "icd10_codes": ";".join(CONDITIONS[c][0] for c in p["condition_codes"]),
            "med_count": len(meds), "heat_class_med_count": sum(1 for g in meds if DRUGS[g][2]),
            "heat_classes": ";".join(heat_classes),
            "mechanism_tags": ";".join(sorted({t for g in meds for t in DRUGS[g][3]})),
            "acb_total": sum(DRUGS[g][4] for g in meds),
            "combination_flags": ";".join(p["flags"]),
            "mail_order": bool(p["mail_meds"]), "mail_order_med_count": len(p["mail_meds"]),
            "insulin_pump": p["pump"], "n_trusted_contacts": len(p["contacts"]),
            "nearest_contact_km": nearest,
            "has_naive_qualifying_contact_60min": any(c["naive_qualifies_60min"] for c in p["contacts"]),
            "has_naive_qualifying_contact_90min": any(c["naive_qualifies_90min"] for c in p["contacts"]),
        })
        for k, g in enumerate(sorted(meds)):
            d, r = DRUGS[g], rx[g]
            mrow.append({
                "med_id": "%s-med%d" % (p["patient_id"], k + 1), "patient_id": p["patient_id"],
                "synthetic": True, "generic_name": g, "rxnorm_rxcui": r["rxcui"], "rxnorm_tty": r["tty"],
                "rxnorm_name": r["rxnorm_name"], "drug_class": d[1], "heat_class_spec_8_7": d[2],
                "mechanism_tags": ";".join(d[3]), "acb_score": d[4], "dose_form": d[5], "route": d[6],
                "indication": meds[g], "otc_possible": g in OTC_POSSIBLE,
                "temperature_sensitive_storage": d[8], "status": "active",
                "authored_on": p["authored"][g], "mail_order": g in p["mail_meds"],
                "delivery_location": p["q"]["mail_order_drop_location"] if g in p["mail_meds"] else "",
            })
        qrow.append(dict({"patient_id": p["patient_id"], "synthetic": True}, **p["q"]))
        crow.extend(p["contacts"])

    wcsv("patients.csv", prow, list(prow[0].keys()))
    wcsv("medications.csv", mrow, list(mrow[0].keys()))
    wcsv("questionnaire.csv", qrow, list(qrow[0].keys()))
    ccols = ["contact_id", "patient_id", "synthetic", "priority", "given_name", "family_name",
             "relationship", "phone", "preferred_language", "location_type", "lat", "lon",
             "straight_line_km", "naive_travel_mode", "naive_travel_min", "naive_qualifies_60min",
             "naive_qualifies_90min"]
    wcsv("contacts.csv", crow, ccols)

    summary = summarize(patients, prow, mrow, qrow, crow, places, kidney, svi)
    (OUT / "summary.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps(summary, indent=1))


def summarize(patients, prow, mrow, qrow, crow, places, kidney, svi):
    n = len(patients)
    adults = [p for p in patients if p["age"] >= 18]
    na = len(adults)
    pct = lambda x, d: round(100.0 * x / d, 1) if d else 0  # noqa: E731
    by = lambda key, rows: {k: sum(1 for r in rows if r[key] == k)  # noqa: E731
                            for k in sorted({r[key] for r in rows}, key=str)}
    cond_counts = {}
    for p in patients:
        for c in p["conditions"]:
            cond_counts[c] = cond_counts.get(c, 0) + 1
    flag_counts = {}
    for p in patients:
        for f in p["flags"]:
            flag_counts[f] = flag_counts.get(f, 0) + 1
    hc = {}
    for m in mrow:
        if m["heat_class_spec_8_7"]:
            hc.setdefault(m["heat_class_spec_8_7"], set()).add(m["patient_id"])
    popw = {r["zcta5"]: int(r["totalpop18plus"]) for r in places}
    tot = sum(popw.values())
    wavg = lambda f: round(sum(float(r[f]) * popw[r["zcta5"]] for r in places) / tot, 1)  # noqa: E731
    kid = round(sum(float(r["kidney_crudeprev"]) * popw[r["zcta5"]] for r in kidney) / tot, 1)
    adult_prev = lambda conds: pct(sum(1 for p in adults if p["conditions"] & conds), na)  # noqa: E731
    s = svi["features"][0]["attributes"]
    contact_counts = {}
    for p in patients:
        contact_counts[len(p["contacts"])] = contact_counts.get(len(p["contacts"]), 0) + 1
    meds_per = [len(p["meds"]) for p in patients]
    return {
        "n_patients": n, "n_story_patients": sum(1 for p in patients if p["story_patient"]),
        "n_coverage_topup_patients": sum(1 for p in patients if p["coverage_topup"]),
        "n_medication_rows": len(mrow), "n_contacts": len(crow),
        "n_children": n - na,
        "age_band": by("age_band", prow), "sex": by("sex", prow), "zip": by("zip", prow),
        "language": by("preferred_language", prow),
        "meds_per_patient": {"mean": round(sum(meds_per) / n, 2), "median": sorted(meds_per)[n // 2],
                             "max": max(meds_per),
                             "pct_5plus": pct(sum(1 for x in meds_per if x >= 5), n)},
        "condition_counts": dict(sorted(cond_counts.items(), key=lambda kv: -kv[1])),
        "patients_per_heat_class": {k: len(v) for k, v in sorted(hc.items(), key=lambda kv: -len(kv[1]))},
        "combination_flag_counts": dict(sorted(flag_counts.items(), key=lambda kv: -kv[1])),
        "adult_prevalence_panel_vs_places_pct": {
            "hypertension": [adult_prev({"hypertension"}), wavg("bphigh_crudeprev")],
            "diabetes": [adult_prev({"type2_diabetes", "type1_diabetes"}), wavg("diabetes_crudeprev")],
            "asthma": [adult_prev({"asthma"}), wavg("casthma_crudeprev")],
            "depression": [adult_prev({"depression"}), wavg("depression_crudeprev")],
            "ckd": [adult_prev({"ckd"}), kid],
            "arthritis_or_chronic_pain": [adult_prev({"osteoarthritis", "chronic_pain"}), wavg("arthritis_crudeprev")],
            "_note": "[panel %, PLACES crude % (adult-population-weighted across the 7 ZCTAs)]; panel is enriched by design",
        },
        "acs_svi_bronx_reference": {"pct_age65plus": s["EP_AGE65"], "pct_age17under": s["EP_AGE17"],
                                    "pct_limited_english": s["EP_LIMENG"], "pct_10plus_unit_housing": s["EP_MUNIT"]},
        "questionnaire": {
            "q1_working_ac": by("q1_working_ac", qrow), "q2_day_location": by("q2_day_location", qrow),
            "q4_lives_alone_adults_pct": pct(sum(1 for q in qrow if q["q4_lives_alone"]), na),
            "floor_7plus_pct": pct(sum(1 for q in qrow if q["q3_floor"] >= 7), n),
            "walkup_floor_4plus": sum(1 for q in qrow if q["q3_floor"] >= 4 and not q["building_has_elevator"]),
            "step_free_needed": sum(1 for q in qrow if q["mobility_step_free_needed"]),
            "q5_can_reach_cool_place": by("q5_can_reach_cool_place", qrow),
            "fluid_restricted": sum(1 for q in qrow if q["fluid_restricted"]),
            "alert_opt_in_pct": pct(sum(1 for q in qrow if q["alert_opt_in"]), n),
            "alert_channel": by("alert_channel", qrow),
        },
        "contacts_per_patient": dict(sorted(contact_counts.items())),
        "contact_location_type": by("location_type", crow),
        "patients_without_naive_qualifying_contact_60min": sum(1 for r in prow if not r["has_naive_qualifying_contact_60min"]),
        "patients_without_naive_qualifying_contact_90min": sum(1 for r in prow if not r["has_naive_qualifying_contact_90min"]),
        "meds_per_patient_by_age_band": {b: round(sum(r["med_count"] for r in prow if r["age_band"] == b) /
                                                  max(1, sum(1 for r in prow if r["age_band"] == b)), 2)
                                         for b in ["child", "18-44", "45-64", "65+"]},
        "pct_5plus_meds_age65plus": pct(sum(1 for r in prow if r["age_band"] == "65+" and r["med_count"] >= 5),
                                        sum(1 for r in prow if r["age_band"] == "65+")),
        "mail_order_patients": sum(1 for r in prow if r["mail_order"]),
        "mail_order_temperature_sensitive_rows": sum(1 for m in mrow if m["mail_order"] and m["temperature_sensitive_storage"]),
        "high_risk_combo_example_counts": {
            "no_ac_and_lives_alone": sum(1 for q in qrow if q["q1_working_ac"] == "no" and q["q4_lives_alone"]),
        },
    }


if __name__ == "__main__":
    main()
