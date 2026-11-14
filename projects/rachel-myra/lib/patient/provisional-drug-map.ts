// PROVISIONAL drug → heat-mechanism table. Swappable: the knowledge base
// (data/kb/knowledge_base.json, built by the Step-3 knowledge-base agent) is authoritative,
// and lib/patient/drug-profiles.ts prefers it whenever it is loaded. This table only covers
// the 72 drugs in the synthetic panel and was generated from the panel generator's
// convenience fields (data/processed/synthetic/medications.csv `mechanism_tags`, `acb_score`;
// generator assumption A15: "provisional; ACB scores recalled from the scale, check them").
// Every profile built from it is labeled source = "provisional" in all outputs.

export interface ProvisionalDrugRow {
  rxcui: string;
  drugClass: string;
  heatClass: string;
  tags: string[];
  acb: number;
}

export const PROVISIONAL_DRUG_MAP: Record<string, ProvisionalDrugRow> = {
  "acetaminophen": { rxcui: "161", drugClass: "analgesic", heatClass: "", tags: [], acb: 0 },
  "albuterol": { rxcui: "435", drugClass: "short-acting beta agonist", heatClass: "", tags: ["storage_sensitive"], acb: 0 },
  "amitriptyline": { rxcui: "704", drugClass: "tricyclic antidepressant", heatClass: "anticholinergics", tags: ["sweat_blocked", "sedation"], acb: 3 },
  "amlodipine": { rxcui: "17767", drugClass: "calcium channel blocker", heatClass: "", tags: ["bp_drop"], acb: 0 },
  "amphetamine mixed salts": { rxcui: "822929", drugClass: "ADHD stimulant", heatClass: "ADHD stimulants", tags: ["heat_production"], acb: 0 },
  "aripiprazole": { rxcui: "89013", drugClass: "antipsychotic (2nd gen)", heatClass: "antipsychotics", tags: ["impaired_thermoregulation"], acb: 1 },
  "aspirin": { rxcui: "1191", drugClass: "antiplatelet (low dose)", heatClass: "", tags: [], acb: 0 },
  "atorvastatin": { rxcui: "83367", drugClass: "statin", heatClass: "", tags: [], acb: 0 },
  "benztropine": { rxcui: "1424", drugClass: "anticholinergic (antiparkinson)", heatClass: "anticholinergics", tags: ["sweat_blocked"], acb: 3 },
  "budesonide/formoterol": { rxcui: "389132", drugClass: "ICS/LABA", heatClass: "", tags: [], acb: 0 },
  "bumetanide": { rxcui: "1808", drugClass: "loop diuretic", heatClass: "loop diuretics", tags: ["fluid_salt_loss"], acb: 0 },
  "bupropion": { rxcui: "42347", drugClass: "antidepressant (NDRI)", heatClass: "", tags: [], acb: 1 },
  "carvedilol": { rxcui: "20352", drugClass: "beta blocker", heatClass: "beta blockers", tags: ["bp_drop", "less_skin_blood_flow"], acb: 1 },
  "cetirizine": { rxcui: "20610", drugClass: "antihistamine (2nd gen)", heatClass: "", tags: [], acb: 1 },
  "chlorthalidone": { rxcui: "2409", drugClass: "thiazide-like diuretic", heatClass: "thiazides", tags: ["fluid_salt_loss", "low_sodium"], acb: 1 },
  "cholecalciferol": { rxcui: "2418", drugClass: "vitamin D", heatClass: "", tags: [], acb: 0 },
  "citalopram": { rxcui: "2556", drugClass: "SSRI", heatClass: "SSRIs", tags: ["low_sodium", "more_sweating"], acb: 0 },
  "clozapine": { rxcui: "2626", drugClass: "antipsychotic (2nd gen)", heatClass: "antipsychotics", tags: ["impaired_thermoregulation", "sedation", "sweat_blocked"], acb: 3 },
  "dapagliflozin": { rxcui: "1488564", drugClass: "SGLT2 inhibitor", heatClass: "SGLT2 inhibitors", tags: ["fluid_salt_loss"], acb: 0 },
  "diclofenac": { rxcui: "3355", drugClass: "NSAID", heatClass: "", tags: ["kidney_stress"], acb: 0 },
  "diphenhydramine": { rxcui: "3498", drugClass: "antihistamine (1st gen)", heatClass: "anticholinergics", tags: ["sweat_blocked", "sedation"], acb: 3 },
  "divalproex": { rxcui: "266856", drugClass: "mood stabilizer / anticonvulsant", heatClass: "", tags: ["sedation"], acb: 0 },
  "duloxetine": { rxcui: "72625", drugClass: "SNRI", heatClass: "", tags: ["low_sodium"], acb: 0 },
  "empagliflozin": { rxcui: "1545653", drugClass: "SGLT2 inhibitor", heatClass: "SGLT2 inhibitors", tags: ["fluid_salt_loss"], acb: 0 },
  "epinephrine": { rxcui: "3992", drugClass: "epinephrine auto-injector", heatClass: "epinephrine auto-injectors", tags: ["storage_sensitive"], acb: 0 },
  "escitalopram": { rxcui: "321988", drugClass: "SSRI", heatClass: "SSRIs", tags: ["low_sodium", "more_sweating"], acb: 0 },
  "fentanyl": { rxcui: "4337", drugClass: "opioid (transdermal)", heatClass: "fentanyl/opioid patches", tags: ["faster_absorption", "sedation"], acb: 1 },
  "fluoxetine": { rxcui: "4493", drugClass: "SSRI", heatClass: "SSRIs", tags: ["low_sodium", "more_sweating"], acb: 0 },
  "fluticasone": { rxcui: "41126", drugClass: "inhaled corticosteroid", heatClass: "", tags: [], acb: 0 },
  "furosemide": { rxcui: "4603", drugClass: "loop diuretic", heatClass: "loop diuretics", tags: ["fluid_salt_loss"], acb: 1 },
  "gabapentin": { rxcui: "25480", drugClass: "gabapentinoid", heatClass: "", tags: ["sedation"], acb: 0 },
  "glipizide": { rxcui: "4821", drugClass: "sulfonylurea", heatClass: "", tags: ["low_glucose"], acb: 0 },
  "guanfacine": { rxcui: "40114", drugClass: "alpha-2 agonist (ADHD)", heatClass: "", tags: ["bp_drop", "sedation"], acb: 0 },
  "haloperidol": { rxcui: "5093", drugClass: "antipsychotic (1st gen)", heatClass: "antipsychotics", tags: ["impaired_thermoregulation", "sedation"], acb: 1 },
  "hydrochlorothiazide": { rxcui: "5487", drugClass: "thiazide diuretic", heatClass: "thiazides", tags: ["fluid_salt_loss", "low_sodium"], acb: 0 },
  "hydroxyzine": { rxcui: "5553", drugClass: "antihistamine (1st gen)", heatClass: "anticholinergics", tags: ["sweat_blocked", "sedation"], acb: 3 },
  "ibuprofen": { rxcui: "5640", drugClass: "NSAID", heatClass: "", tags: ["kidney_stress"], acb: 0 },
  "insulin glargine": { rxcui: "274783", drugClass: "basal insulin", heatClass: "insulin", tags: ["faster_absorption", "storage_sensitive"], acb: 0 },
  "insulin lispro": { rxcui: "86009", drugClass: "rapid-acting insulin", heatClass: "insulin", tags: ["faster_absorption", "storage_sensitive"], acb: 0 },
  "lamotrigine": { rxcui: "28439", drugClass: "anticonvulsant / mood stabilizer", heatClass: "", tags: [], acb: 0 },
  "levetiracetam": { rxcui: "114477", drugClass: "anticonvulsant", heatClass: "", tags: [], acb: 0 },
  "levothyroxine": { rxcui: "10582", drugClass: "thyroid hormone", heatClass: "", tags: [], acb: 0 },
  "lisdexamfetamine": { rxcui: "700810", drugClass: "ADHD stimulant", heatClass: "ADHD stimulants", tags: ["heat_production"], acb: 0 },
  "lisinopril": { rxcui: "29046", drugClass: "ACE inhibitor", heatClass: "ACE inhibitors/ARBs", tags: ["bp_drop", "kidney_stress"], acb: 0 },
  "lithium": { rxcui: "42351", drugClass: "mood stabilizer (lithium)", heatClass: "lithium", tags: ["kidney_cleared_buildup"], acb: 0 },
  "losartan": { rxcui: "52175", drugClass: "ARB", heatClass: "ACE inhibitors/ARBs", tags: ["bp_drop", "kidney_stress"], acb: 0 },
  "meloxicam": { rxcui: "41493", drugClass: "NSAID", heatClass: "", tags: ["kidney_stress"], acb: 0 },
  "metformin": { rxcui: "6809", drugClass: "biguanide", heatClass: "metformin", tags: ["kidney_cleared_buildup"], acb: 0 },
  "methylphenidate": { rxcui: "6901", drugClass: "ADHD stimulant", heatClass: "ADHD stimulants", tags: ["heat_production"], acb: 0 },
  "metoprolol": { rxcui: "6918", drugClass: "beta blocker", heatClass: "beta blockers", tags: ["bp_drop", "less_skin_blood_flow"], acb: 1 },
  "mirabegron": { rxcui: "1300786", drugClass: "beta-3 agonist (bladder)", heatClass: "", tags: [], acb: 0 },
  "mirtazapine": { rxcui: "15996", drugClass: "antidepressant", heatClass: "", tags: ["sedation"], acb: 1 },
  "montelukast": { rxcui: "88249", drugClass: "leukotriene antagonist", heatClass: "", tags: [], acb: 0 },
  "naproxen": { rxcui: "7258", drugClass: "NSAID", heatClass: "", tags: ["kidney_stress"], acb: 0 },
  "olanzapine": { rxcui: "61381", drugClass: "antipsychotic (2nd gen)", heatClass: "antipsychotics", tags: ["impaired_thermoregulation", "sedation", "sweat_blocked"], acb: 3 },
  "omeprazole": { rxcui: "7646", drugClass: "proton pump inhibitor", heatClass: "", tags: [], acb: 0 },
  "oxcarbazepine": { rxcui: "32624", drugClass: "anticonvulsant", heatClass: "", tags: ["low_sodium"], acb: 0 },
  "oxybutynin": { rxcui: "32675", drugClass: "bladder antimuscarinic", heatClass: "anticholinergics", tags: ["sweat_blocked"], acb: 3 },
  "oxycodone": { rxcui: "7804", drugClass: "opioid", heatClass: "", tags: ["sedation"], acb: 1 },
  "paroxetine": { rxcui: "32937", drugClass: "SSRI", heatClass: "SSRIs", tags: ["low_sodium", "sweat_blocked"], acb: 3 },
  "quetiapine": { rxcui: "51272", drugClass: "antipsychotic (2nd gen)", heatClass: "antipsychotics", tags: ["impaired_thermoregulation", "sedation", "sweat_blocked"], acb: 3 },
  "risperidone": { rxcui: "35636", drugClass: "antipsychotic (2nd gen)", heatClass: "antipsychotics", tags: ["impaired_thermoregulation", "sedation"], acb: 1 },
  "sacubitril/valsartan": { rxcui: "1656339", drugClass: "ARNI (contains ARB)", heatClass: "ACE inhibitors/ARBs", tags: ["bp_drop", "kidney_stress"], acb: 0 },
  "semaglutide": { rxcui: "1991302", drugClass: "GLP-1 receptor agonist", heatClass: "", tags: ["fluid_salt_loss", "storage_sensitive"], acb: 0 },
  "sertraline": { rxcui: "36437", drugClass: "SSRI", heatClass: "SSRIs", tags: ["low_sodium", "more_sweating"], acb: 0 },
  "spironolactone": { rxcui: "9997", drugClass: "potassium-sparing diuretic", heatClass: "", tags: ["fluid_salt_loss"], acb: 0 },
  "sumatriptan": { rxcui: "37418", drugClass: "triptan", heatClass: "", tags: [], acb: 0 },
  "tolterodine": { rxcui: "119565", drugClass: "bladder antimuscarinic", heatClass: "anticholinergics", tags: ["sweat_blocked"], acb: 3 },
  "topiramate": { rxcui: "38404", drugClass: "anticonvulsant (carbonic anhydrase)", heatClass: "topiramate/zonisamide", tags: ["sweat_blocked"], acb: 0 },
  "torsemide": { rxcui: "38413", drugClass: "loop diuretic", heatClass: "loop diuretics", tags: ["fluid_salt_loss"], acb: 0 },
  "trazodone": { rxcui: "10737", drugClass: "antidepressant / sleep", heatClass: "", tags: ["sedation"], acb: 1 },
  "venlafaxine": { rxcui: "39786", drugClass: "SNRI", heatClass: "", tags: ["low_sodium"], acb: 1 },
};

/** Narrow-margin drugs cleared by the kidney (spec §6.1 cross-mechanism combos). */
export const NARROW_MARGIN_KIDNEY_CLEARED = ["lithium", "digoxin", "dabigatran"];
