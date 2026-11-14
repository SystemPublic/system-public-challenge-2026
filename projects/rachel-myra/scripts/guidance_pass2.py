"""PASS 2 (read-whole-section coder).

Approach: the coder read each source's complete medication section(s) end to end
(CDC page; NYC page + HAN #23; UKHSA 'Medications with increased risk' + heatstroke
first aid; Health Canada ch. 3 diabetes, ch. 4, Table 4.2 and Table 7.1; ANSM mise au
point incl. annexes 1-3 + glycaemic Q&A; WHO/Europe 2011 medication info sheets and all
medication passages of the 2026 HHAP guidance; Victoria clinicians page; BMG model plans;
Heidelberger Hitze-Tabelle) and coded each drug from that reading, using the same
codebook as pass 1 (see data/raw/guidance/README.md). Cells not listed = not mentioned.
Every quote is checked verbatim (whitespace-normalised) against the source text.

Run: python3 -I scripts/guidance_pass2.py  -> data/processed/guidance_coding_pass2.csv
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from guidance_common import SOURCES, CORE, OTHER, DRUG_LABEL, PROC, load_lines, norm

S, U = "specific", "umbrella"
GC, MON, ADJ, HOLD, STO = "general_caution", "monitor", "adjust_dose", "hold_or_substitute", "storage"

CDCT = "CDC clinicians page, table 'Medications that may increase risk of harm on hot days'"
CDCN = "CDC clinicians page, 'Heat and Medications' narrative"
CDCA = "CDC clinicians page, 'What Clinicians Can Do'"
NYCT = "NYC provider page, 'Drugs That May Increase Risk of Harm on Hot Days'"
NYCN = "NYC provider page, intro mechanisms list"
NYCS = "NYC provider page, 'Safe Storage'"
UKM = "UKHSA page, 'Medications with increased risk during hot weather'"
HC4 = "Health Canada 2011, ch. 4 §4.4"
HCT = "Health Canada 2011, Table 4.2 'Hazardous Drugs and Recommendations'"
HC7 = "Health Canada 2011, Table 7.1"
AN = "ANSM mise au point 2017"
W11 = "WHO/Europe 2011, 'For medical professionals: adverse effects of medication during hot weather' (PDF p. 13-14)"
W26 = "WHO/Europe 2026 HHAP guidance 2nd ed"
VIC2 = "Victoria clinicians page, Table 2 'Mechanisms for medicine increasing the risk of heat-related illness'"
HEI = "Heidelberger Hitze-Tabelle (Stand 07.07.2026)"

# (level, primary action, all actions, specificity, evidence_cited, quote, location)
P2 = {
 # ---------------- CDC ----------------
 ("CDC", "lithium"): (S, GC, GC, "generic", "no", "Lithium Diabetes insipidus induced water loss and risk for fainting, falls Electrolyte imbalance Risk for toxicity in setting of dehydration because of narrow therapeutic index", CDCT),
 ("CDC", "loop_diuretics"): (S, GC, GC, "generic", "no", "Diuretics Furosemide Hydrochlorothiazide Acetazolamide Electrolyte imbalance Volume depletion, dehydration and increased risk of fainting and falls", CDCT),
 ("CDC", "thiazides"): (S, GC, GC, "generic", "no", "Diuretics Furosemide Hydrochlorothiazide Acetazolamide Electrolyte imbalance Volume depletion, dehydration and increased risk of fainting and falls", CDCT),
 ("CDC", "acei_arb"): (S, GC, GC, "generic", "no", "Certain combinations of medications, such as an angiotensin converting enzyme (ACE) inhibitor or an angiotensin II receptor blocker (ARB) with a diuretic, may significantly increase risk of harm from heat exposure.", CDCN),
 ("CDC", "insulin"): (S, STO, STO, "specific", "no", "Remind patients that insulin can be degraded by heat and should be refrigerated.", CDCA),
 ("CDC", "anticholinergics_oxybutynin"): (S, GC, GC, "generic", "no", "Commonly prescribed medications that increase risk from heat include diuretics, anticholinergic agents, and some psychotropic medications.", CDCN),
 ("CDC", "antipsychotics_clozapine"): (S, GC, GC, "generic", "no", "Antipsychotics Haloperidol, Olanzapine, Quetiapine, Risperidone Impaired sweating Impaired temperature", CDCT),
 ("CDC", "ssri"): (S, GC, GC, "generic", "no", "Impaired sweating and therefore impaired cooling (increased with Selective Serotonin Reuptake Inhibitors (SSRIs)", CDCN),
 ("CDC", "topiramate_zonisamide"): (S, GC, GC, "generic", "no", "Antiseizure medications Topiramate Decreased sweating", CDCT),
 ("CDC", "adhd_stimulants"): (S, GC, GC, "generic", "no", "stimulants like methylphenidate for attention-deficit/hyperactivity disorder (ADHD)", CDCN),
 ("CDC", "beta_blockers"): (S, GC, GC, "generic", "no", "Beta blockers Atenolol Metoprolol Propranolol Reduced superficial vasodilation Decreased sweating", CDCT),
 ("CDC", "opioid_patches_fentanyl"): (U, "none", "", "none", "no", "Sedation or cognitive impairment with increased risk of falls and reduced thirst sensation (e.g., opiates, benzodiazepines", CDCN),
 ("CDC", "epinephrine_autoinjector"): (S, STO, STO, "generic", "no", "EpiPens may malfunction or deliver less epinephrine when exposed to heat.", CDCN),
 ("CDC", "ccb"): (S, GC, GC, "generic", "no", "Calcium channel blocker Amlodipine Felodipine Nifedipine Decreased blood pressure, increased risk of fainting and falls", CDCT),
 ("CDC", "nitrates"): (S, GC, GC, "generic", "no", "Nitrates Glyceryl Trinitrate, Isosorbide Mononitrate Worsened hypotension", CDCT),
 ("CDC", "nsaids"): (S, GC, GC, "generic", "no", "Nonsteroidal anti-inflammatory drugs (NSAIDS) Kidney injury with dehydration", CDCT),
 ("CDC", "acetaminophen"): (S, GC, GC, "generic", "no", "Acetaminophen Heat related liver injury increase risk for acetaminophen hepatoxicity", CDCT),
 ("CDC", "tca"): (S, GC, GC, "generic", "no", "Tricyclic antidepressants (TCAs) Amitriptyline, Clomipramine Decreased sweating", CDCT),
 ("CDC", "antihistamines_1stgen"): (S, GC, GC, "generic", "no", "Antihistamines with anticholinergic properties Promethazine, Doxylamine, Diphenhydramine Decreased sweating", CDCT),
 ("CDC", "benzodiazepines_anxiolytics"): (S, GC, GC, "generic", "no", "Sedation or cognitive impairment with increased risk of falls and reduced thirst sensation (e.g., opiates, benzodiazepines", CDCN),
 ("CDC", "carbamazepine_oxcarbazepine"): (S, GC, GC, "generic", "no", "Carbamazepine Dizziness and weakness, especially after increased dose", CDCT),
 ("CDC", "levothyroxine"): (S, GC, GC, "generic", "no", "Thyroid replacement Levothyroxine Excessive sweating", CDCT),
 ("CDC", "laxatives"): (S, GC, GC, "generic", "no", "Electrolyte imbalance (e.g., diuretics, beta blockers, calcium channel blockers, antacids, laxatives, lithium, and trimethoprim-sulfamethoxazole)", CDCN),
 ("CDC", "snri"): (S, GC, GC, "generic", "no", "SNRI: Duloxatine Venlafaxine Increased sweating", CDCT),
 ("CDC", "photosensitizing_antimicrobials"): (S, GC, GC, "specific", "no", "Counsel patients taking medications that increase sun sensitivity to limit sun exposure and apply sunscreen when they need to be outside in the sun.", CDCA),
 ("CDC", "inhalers"): (S, STO, STO, "specific", "no", "Remind patients that inhalers can malfunction or burst from extreme heat.", CDCA),
 # ---------------- NYC ----------------
 ("NYC", "lithium"): (S, GC, GC, "generic", "no", "Drug toxicity from reduced clearance of medications in people who are dehydrated, especially for medications with a narrow therapeutic index (for example, apixaban, carbamazepine, and lithium)", NYCN),
 ("NYC", "loop_diuretics"): (S, GC, GC, "generic", "no", "Examples: Furosemide, Hydrochlorothiazide, Acetazolamide", NYCT),
 ("NYC", "thiazides"): (S, GC, GC, "generic", "no", "Examples: Furosemide, Hydrochlorothiazide, Acetazolamide", NYCT),
 ("NYC", "acei_arb"): (S, GC, GC, "generic", "no", "Examples: ACEi: Enalapril, Lisinopril, Ramipril; ARB: Valsartan, Losartan", NYCT),
 ("NYC", "insulin"): (S, MON, "monitor;storage", "specific", "no", "High temperatures can change how the body uses insulin. People with diabetes should check their blood sugar more frequently.", "NYC HAN 2026 #23 (Aug 5, 2026), PDF p. 2; storage also in NYC provider page 'Safe Storage'"),
 ("NYC", "anticholinergics_oxybutynin"): (S, GC, GC, "generic", "no", "Interference with central thermoregulation (for example, antipsychotics, anticholinergics, stimulants)", NYCN),
 ("NYC", "antipsychotics_clozapine"): (S, GC, GC, "generic", "no", "Examples: Haloperidol, Olanzapine, Quetiapine, Risperidone", NYCT),
 ("NYC", "ssri"): (S, GC, GC, "generic", "no", "Examples: SSRI: Fluoxetine, Sertraline; SNRI: Duloxatine, Venlafaxine", NYCT),
 ("NYC", "topiramate_zonisamide"): (S, GC, GC, "generic", "no", "Example: Topiramate May cause: Decreased sweating", NYCT),
 ("NYC", "adhd_stimulants"): (S, GC, GC, "generic", "no", "Examples: Amphetamine, Methylphenidate May cause: Increased body temperature", NYCT),
 ("NYC", "beta_blockers"): (S, GC, GC, "generic", "no", "Examples: Atenolol, Metoprolol, Propranolol", NYCT),
 ("NYC", "opioid_patches_fentanyl"): (U, "none", "", "none", "no", "Sedation or cognitive impairment with increased risk of falls and reduced thirst sensation (for example, opiates, benzodiazepines", NYCN),
 ("NYC", "epinephrine_autoinjector"): (S, STO, STO, "specific", "no", "EpiPens may malfunction or deliver less epinephrine when exposed to heat.", NYCS),
 ("NYC", "ccb"): (S, GC, GC, "generic", "no", "Examples: Amlodipine, Felodipine, Nifedipine", NYCT),
 ("NYC", "nitrates"): (S, GC, GC, "generic", "no", "Examples: Glyceryl Trinitrate, Isosorbide Mononitrate May cause: Worsened hypotension", NYCT),
 ("NYC", "nsaids"): (S, GC, GC, "generic", "no", "Nonsteroidal anti-inflammatory drugs (NSAIDS) May cause: Kidney injury with dehydration", NYCT),
 ("NYC", "acetaminophen"): (S, GC, GC, "generic", "no", "Heat related liver injury increase risk for acetaminophen hepatoxicity", NYCT),
 ("NYC", "tca"): (S, GC, GC, "generic", "no", "Examples: Amitriptyline, Clomipramine May cause: Decreased sweating", NYCT),
 ("NYC", "antihistamines_1stgen"): (S, GC, GC, "generic", "no", "Examples: Diphenhydramine, Doxylamine, Promethazine", NYCT),
 ("NYC", "benzodiazepines_anxiolytics"): (S, GC, GC, "generic", "no", "Sedation or cognitive impairment with increased risk of falls and reduced thirst sensation (for example, opiates, benzodiazepines", NYCN),
 ("NYC", "carbamazepine_oxcarbazepine"): (S, GC, GC, "generic", "no", "Example: Carbamazepine May cause: Dizziness and weakness, especially after increased dose", NYCT),
 ("NYC", "levothyroxine"): (S, GC, GC, "generic", "no", "Example: Levothyroxine May cause: Excessive sweating", NYCT),
 ("NYC", "laxatives"): (S, GC, GC, "generic", "no", "Electrolyte imbalance (for example, diuretics, beta blockers, calcium channel blockers, antacids, laxatives, lithium, and trimethoprim-sulfamethoxazole)", NYCN),
 ("NYC", "snri"): (S, GC, GC, "generic", "no", "Examples: SSRI: Fluoxetine, Sertraline; SNRI: Duloxatine, Venlafaxine", NYCT),
 ("NYC", "photosensitizing_antimicrobials"): (S, GC, GC, "specific", "no", "For patients on these medications, sun avoidance, protective clothing and hats, and broad-spectrum sunscreen that filters out UVA and UVB rays, with an SPF of 30 or higher, are recommended.", "NYC provider page, 'Medication Use'"),
 ("NYC", "inhalers"): (S, STO, STO, "specific", "no", "Inhalers, for example, can burst in hot environments, such as car trunks on hot days.", NYCS),
 # ---------------- UKHSA ----------------
 ("UKHSA", "lithium"): (S, GC, GC, "generic", "no", "agents with levels affected by dehydration, such as lithium, digoxin, antiepileptics", UKM),
 ("UKHSA", "loop_diuretics"): (S, GC, GC, "generic", "no", "diuretics, especially loop diuretics, which can lead to dehydration and electrolyte abnormalities", UKM),
 ("UKHSA", "thiazides"): (U, "none", "", "none", "no", "diuretics, especially loop diuretics, which can lead to dehydration and electrolyte abnormalities", UKM),
 ("UKHSA", "acei_arb"): (U, "none", "", "none", "no", "medications that interfere with cardiovascular responses such as antihypertensives and antianginal drugs", UKM),
 ("UKHSA", "anticholinergics_oxybutynin"): (S, GC, GC, "generic", "no", "medications that interfere with sweating, such as anticholinergics or beta blockers", UKM),
 ("UKHSA", "antipsychotics_clozapine"): (S, GC, GC, "generic", "no", "medications that can interfere with central nervous system thermoregulation, such as neuroleptics and serotoninergic agonists", UKM),
 ("UKHSA", "ssri"): (U, "none", "", "none", "no", "medications that can interfere with central nervous system thermoregulation, such as neuroleptics and serotoninergic agonists", UKM),
 ("UKHSA", "topiramate_zonisamide"): (U, "none", "", "none", "no", "agents with levels affected by dehydration, such as lithium, digoxin, antiepileptics", UKM),
 ("UKHSA", "beta_blockers"): (S, GC, GC, "generic", "no", "medications that interfere with sweating, such as anticholinergics or beta blockers", UKM),
 ("UKHSA", "opioid_patches_fentanyl"): (U, "none", "", "none", "no", "medications that cause diarrhoea or vomiting, such as colchicine, antibiotics and opiates, which can lead to dehydration", UKM),
 ("UKHSA", "ccb"): (U, "none", "", "none", "no", "medications that interfere with cardiovascular responses such as antihypertensives and antianginal drugs", UKM),
 ("UKHSA", "nitrates"): (U, "none", "", "none", "no", "medications that interfere with cardiovascular responses such as antihypertensives and antianginal drugs", UKM),
 ("UKHSA", "nsaids"): (S, GC, GC, "generic", "no", "medications that can impair renal function, such as certain antimicrobials, immunosuppressants, non-steroidal anti-inflammatories, anti-ulcer agents and chemotherapies", UKM),
 ("UKHSA", "acetaminophen"): (S, HOLD, HOLD, "specific", "no", "do not give them aspirin or paracetamol", "UKHSA page, 'Emergency treatment of heatstroke' (first aid, not chronic medication)"),
 ("UKHSA", "benzodiazepines_anxiolytics"): (S, GC, GC, "generic", "no", "drugs that alter states of alertness, such as hypnotics, anxiolytics and analgesics", UKM),
 ("UKHSA", "carbamazepine_oxcarbazepine"): (U, "none", "", "none", "no", "agents with levels affected by dehydration, such as lithium, digoxin, antiepileptics", UKM),
 ("UKHSA", "digoxin"): (S, GC, GC, "generic", "no", "agents with levels affected by dehydration, such as lithium, digoxin, antiepileptics", UKM),
 ("UKHSA", "levothyroxine"): (S, GC, GC, "generic", "no", "drugs that increase the basal metabolic rate such as thyroxine", UKM),
 ("UKHSA", "snri"): (U, "none", "", "none", "no", "medications that can interfere with central nervous system thermoregulation, such as neuroleptics and serotoninergic agonists", UKM),
 # ---------------- Health Canada ----------------
 ("HC", "lithium"): (S, MON, "monitor;general_caution", "specific", "yes", "A retrospective study on adverse reactions associated with lithium showed that 11.5% of lithium poisonings requiring hospitalization were due to summer heat exposure and consequent dehydration.Reference 191 Hydrate with water rather than an electrolyte solution to minimize potential hypernatremic complications.", HC4 + " 'Lithium'; Table 4.2 row 'Lithium'"),
 ("HC", "loop_diuretics"): (S, GC, GC, "generic", "no", "Diuretics (e.g. Lasix) Can lead to dehydration and hyponatremia is a common side effect", HC7),
 ("HC", "thiazides"): (U, "none", "", "none", "no", "Diuretics Hyperhydration Hyponatremia Electrolyte imbalance Hyperthermia Heat intolerance Drink water or electrolyte solutions throughout the day Protect yourself from the heat No specific recommendations", HCT),
 ("HC", "acei_arb"): (S, MON, "monitor", "generic", "yes", "With ACE-II inhibitors, hyponatremia is also a side effect: OR 12.2 (CI95 1.26-21.2).Reference 209", HC4 + " 'Antiarrhythmics'; Table 4.2 row 'ACE-II inhibitors' (Monitor patient hydration; No specific recommendations)"),
 ("HC", "insulin"): (S, STO, STO, "specific", "yes", "It is especially important to be aware of the proper storage of insulin during EHEs. Studies have shown that insulin vials stored at 32°C can lose 14-18% of their potency after 28 days, compromising the reduction of blood glucose levels.Reference 134", "Health Canada 2011, ch. 3 §3.1 'Diabetes'"),
 ("HC", "anticholinergics_oxybutynin"): (S, GC, GC, "generic", "yes", "Anticholinergic 6.0 1.8-19.6", "Health Canada 2011, Table 4.1; Table 7.1 'Anticholinergics (e.g. Scopolamine)'"),
 ("HC", "antipsychotics_clozapine"): (S, GC, GC, "generic", "yes", "Antipsychotics 4.6 1.9-11.2", "Health Canada 2011, Table 4.1; Table 4.2 row 'Antipsychotics/Neuroleptics' (No specific recommendations)"),
 ("HC", "ssri"): (S, MON, "monitor;general_caution", "specific", "yes", "Especially in individuals taking selective serotonin reuptake inhibitors.", HCT + " row 'Antidepressants' (side effects to monitor: hyponatremia); §4.4.1 SSRIs OR 13.5 with diuretics"),
 ("HC", "topiramate_zonisamide"): (S, MON, MON, "specific", "yes", "Topiramate: watch for hyperthermia and heat intolerance.", HCT + " row 'Antiepileptics'; §4.4.1 (11% of children hypohidrosis, Reference 139)"),
 ("HC", "adhd_stimulants"): (U, "none", "", "none", "no", "An 11-year-old girl who was taking two amphetamines (phentermine and propylhexedrine hydrochloride) for weight loss", "Health Canada 2011, §4.3 case study (weight-loss amphetamines, not ADHD medication)"),
 ("HC", "beta_blockers"): (S, GC, GC, "generic", "no", "Antiadrenergics and β-Blockers (e.g. Atenolol, Metoprolol) Can decrease cardiac output", HC7),
 ("HC", "ccb"): (S, MON, MON, "generic", "yes", "The side effects of calcium channel blockers should also be monitored during the summer months. Diarrhea is the most frequently cited side effect,Reference 210", HC4 + " 'Calcium channel blockers'"),
 ("HC", "nitrates"): (S, MON, MON, "generic", "yes", "With nitrate vasodilators, vomiting can affect 24% of the study population,Reference 207", HC4 + "; Table 4.2 row 'Nitrate vasodilators' (Monitor patient hydration; No specific recommendations)"),
 ("HC", "tca"): (S, GC, GC, "generic", "yes", "with tricyclic antidepressants featuring most prominently (OR 2.2, CI95 1.80-2.69)", HC4 + " 'Antidepressants'"),
 ("HC", "antihistamines_1stgen"): (S, GC, GC, "generic", "no", "Antihistamines (e.g. Brompheniramine) Can inhibit the sweating mechanism", HC7),
 ("HC", "antiparkinson"): (S, GC, GC, "generic", "yes", "anti-Parkinson's agents: OR 6.02 (CI95 0.72-50.37) for older adults living in their own homes", HC4 + " 'Anti-Parkinson's agents'"),
 ("HC", "benzodiazepines_anxiolytics"): (S, GC, GC, "generic", "yes", "Anxiolytics 2.4 1.3-4.4", "Health Canada 2011, Table 4.1"),
 ("HC", "carbamazepine_oxcarbazepine"): (S, GC, GC, "specific", "yes", "Oxcarbazepine and carbamazepine: take precautions against hyponatremia and hyperhydration.", HCT + " row 'Antiepileptics'"),
 ("HC", "snri"): (U, "none", "", "none", "no", "Antidepressants Hyperhydration Hyponatremia Electrolyte imbalance", HCT),
 ("HC", "cholinesterase_inhibitors"): (S, MON, MON, "specific", "yes", "Carefully monitor patients who are starting the medication in the summer.", HCT + " row 'Anti-Alzheimer's agents (Cholinesterase inhibitors)'; §4.4.1 OR 4.82 vomiting"),
 # ---------------- ANSM ----------------
 ("ANSM", "lithium"): (S, GC, GC, "generic", "no", "Sels de lithium Profil cinétique affecté par la déshydratation", AN + ", Annexe 2 (PDF p. 8)"),
 ("ANSM", "loop_diuretics"): (S, MON, "monitor;general_caution", "specific", "no", "en cas de prescription d’un diurétique, vérifier que les apports hydriques et sodés sont adaptés", AN + ", §4 Recommandations (PDF p. 6); list 'diurétiques de l’anse (furosémide, bumétanide)' PDF p. 3"),
 ("ANSM", "thiazides"): (S, MON, "monitor;general_caution", "specific", "no", "en cas de prescription d’un diurétique, vérifier que les apports hydriques et sodés sont adaptés", AN + ", §4 Recommandations (PDF p. 6); list 'diurétiques thiazidiques et distaux au long cours' PDF p. 3"),
 ("ANSM", "acei_arb"): (S, GC, GC, "generic", "yes", "les inhibiteurs de l’enzyme de conversion de l’angiotensine, les antidépresseurs sérotoninergiques, les inhibiteurs de la pompe à proton, la digoxine, les benzodiazépines, les hypoglycémiants oraux, les sartans, les antagonistes calciques et les β-bloquants10", AN + ", §2 (PDF p. 3), Sommet et al. 2012 pharmacovigilance study"),
 ("ANSM", "sglt2"): (U, "none", "", "none", "no", "les hypoglycémiants oraux", AN + ", §2 (PDF p. 3)"),
 ("ANSM", "insulin"): (S, STO, STO, "specific", "no", "Médicaments biologiques (insuline, somatropine...) en présentation multidose qui se conservent hors du réfrigérateur après ouverture à des températures ne dépassant pas 25°C ou 30°C En cas d'exposition à des températures supérieures, il est recommandé de se rapprocher, éventuellement avec l'aide d'un pharmacien, du laboratoire", AN + ", Annexe 3 'Conservation' (PDF p. 9)"),
 ("ANSM", "metformin"): (S, GC, GC, "generic", "no", "Biguanides et sulfamides hypoglycémiants Profil cinétique affecté par la déshydratation", AN + ", Annexe 2 (PDF p. 8)"),
 ("ANSM", "anticholinergics_oxybutynin"): (S, GC, GC, "generic", "no", "certains antispasmodiques, en particulier ceux à visée urinaire (oxybutynine, toltérodine,", AN + ", §3 (PDF p. 4)"),
 ("ANSM", "antipsychotics_clozapine"): (S, GC, GC, "generic", "yes", "la prise d’un psychotrope, en particulier antidépresseur ou neuroleptique, est associée à une augmentation du risque de décès chez le sujet âgé pendant une vague de chaleur", AN + ", §2 (PDF p. 3), Nordon et al. 2009"),
 ("ANSM", "ssri"): (S, GC, GC, "generic", "yes", "les antidépresseurs sérotoninergiques", AN + ", §2 (PDF p. 3) Sommet 2012; IRS listed Annexe 1-2"),
 ("ANSM", "topiramate_zonisamide"): (U, "none", "", "none", "no", "Anti-épileptiques Profil cinétique affecté par la déshydratation", AN + ", Annexe 2 (PDF p. 8)"),
 ("ANSM", "adhd_stimulants"): (U, "none", "", "none", "no", "l’usage de certaines drogues, en particulier les substances amphétaminiques et la cocaïne", AN + ", §3 (PDF p. 5): recreational drugs only"),
 ("ANSM", "beta_blockers"): (S, GC, GC, "generic", "yes", "les antagonistes calciques et les β-bloquants10", AN + ", §2 (PDF p. 3); Annexe 2 'Bêta-bloquants'"),
 ("ANSM", "opioid_patches_fentanyl"): (U, "none", "", "none", "no", "la pharmacocinétique des dispositifs transdermiques peut être modifiée en raison de la vasodilatation sous-cutanée, et de l’hypersudation susceptible d’entrainer un décollement.", AN + ", §3 (PDF p. 4): transdermal systems in general, no opioid named"),
 ("ANSM", "ccb"): (S, GC, GC, "generic", "yes", "les antagonistes calciques et les β-bloquants10", AN + ", §2 (PDF p. 3)"),
 ("ANSM", "nitrates"): (S, GC, GC, "generic", "no", "Anti-angoreux Diminution de la pression artérielle", AN + ", Annexe 2 (PDF p. 8)"),
 ("ANSM", "nsaids"): (S, HOLD, "hold_or_substitute", "specific", "no", "éviter la prescription d’anti-inflammatoires non stéroïdiens, particulièrement néphrotoxiques en cas de déshydratation", AN + ", §4 Recommandations (PDF p. 6)"),
 ("ANSM", "acetaminophen"): (S, HOLD, HOLD, "specific", "no", "en cas de fièvre, éviter aussi la prescription de paracétamol en raison de son inefficacité pour traiter le coup de chaleur et d’une possible aggravation de l’atteinte hépatique souvent présente", AN + ", §4 Recommandations (PDF p. 6)"),
 ("ANSM", "tca"): (S, GC, GC, "generic", "no", "Antidépresseurs imipraminiques Diminution de la perte calorique", AN + ", Annexe 2 (PDF p. 8)"),
 ("ANSM", "antihistamines_1stgen"): (S, GC, GC, "generic", "no", "Antihistaminiques de première génération Diminution de la perte calorique (propriétés atropiniques)", AN + ", Annexe 2 (PDF p. 8)"),
 ("ANSM", "antiparkinson"): (S, GC, GC, "generic", "no", "antiparkinsoniens atropiniques (trihexyphénidyle, tropatépine, bipéridène…)", AN + ", §3 (PDF p. 4)"),
 ("ANSM", "benzodiazepines_anxiolytics"): (S, GC, GC, "generic", "yes", "Benzodiazépines Altération de la vigilance donc des facultés de défense contre la chaleur", AN + ", Annexe 2 (PDF p. 8); Sommet 2012 list PDF p. 3"),
 ("ANSM", "carbamazepine_oxcarbazepine"): (U, "none", "", "none", "no", "Anti-épileptiques Profil cinétique affecté par la déshydratation", AN + ", Annexe 2 (PDF p. 8)"),
 ("ANSM", "digoxin"): (S, GC, GC, "generic", "yes", "Digitaliques : digoxine Profil cinétique affecté par la déshydratation", AN + ", Annexe 2 (PDF p. 8); Sommet 2012 list PDF p. 3"),
 ("ANSM", "levothyroxine"): (S, GC, GC, "generic", "no", "Un traitement non équilibré avec un apport trop élevé d’hormones thyroïdiennes expose à un risque d’hyperthermie.", AN + ", §3 (PDF p. 5)"),
 ("ANSM", "snri"): (S, GC, GC, "generic", "no", "IRS, IRSNA, IMAO sélectifs (moclobémide, sélégiline, rasagiline) Hyperthermie", AN + ", Annexe 2 (PDF p. 8)"),
 ("ANSM", "glp1_dpp4"): (S, GC, GC, "generic", "no", "Gliptines et agonistes récepteur GLP-1 (liraglutide, exenatine) Altération de la fonction rénale", AN + ", Annexe 2 (PDF p. 8)"),
 ("ANSM", "sulfonylureas"): (S, GC, GC, "generic", "no", "Biguanides et sulfamides hypoglycémiants Profil cinétique affecté par la déshydratation", AN + ", Annexe 2 (PDF p. 8)"),
 ("ANSM", "transdermal_other"): (S, GC, GC, "generic", "no", "la pharmacocinétique des dispositifs transdermiques peut être modifiée en raison de la vasodilatation sous-cutanée, et de l’hypersudation susceptible d’entrainer un décollement.", AN + ", §3 (PDF p. 4)"),
 # ---------------- WHO Europe ----------------
 ("WHO_EUR", "lithium"): (S, GC, GC, "generic", "no", "increase toxicity and/or decrease the efficacy of drugs, particularly those with a narrow therapeutic index, such as digoxin or lithium.", W11 + "; also 2026 HHAP Box UAB1 pre-season medication reviews (PDF p. 214)"),
 ("WHO_EUR", "loop_diuretics"): (U, "none", "", "none", "no", "Some medicines – including diuretics, anticholinergics and neuroleptics – may further affect sweating, hydration, renal function or cardiovascular response", W26 + ", Core element 3 (PDF p. 86)"),
 ("WHO_EUR", "thiazides"): (U, "none", "", "none", "no", "Some medicines – including diuretics, anticholinergics and neuroleptics – may further affect sweating, hydration, renal function or cardiovascular response", W26 + ", Core element 3 (PDF p. 86)"),
 ("WHO_EUR", "acei_arb"): (U, "none", "", "none", "no", "Antihypertensives and diuretics", W11),
 ("WHO_EUR", "insulin"): (S, STO, STO, "specific", "no", "This is particularly important for emergency drugs, including antibiotics, adrenergic drugs, insulin, analgesics and sedatives.", W11 + " (PDF p. 14)"),
 ("WHO_EUR", "anticholinergics_oxybutynin"): (S, GC, GC, "generic", "no", "Some medicines – including diuretics, anticholinergics and neuroleptics – may further affect sweating, hydration, renal function or cardiovascular response", W26 + ", Core element 3 (PDF p. 86); 2011 table rows 'Anti-cholinergics', 'urinary incontinence drugs'"),
 ("WHO_EUR", "antipsychotics_clozapine"): (S, STO, "storage;general_caution", "specific", "yes", "sensitive pharmaceuticals such as antipsychotics during transportation and storage (16)", W26 + ", Core element 5 (PDF p. 128)"),
 ("WHO_EUR", "ssri"): (U, "none", "", "none", "no", "Run pre-season medication reviews for and with patients on medications that affect thermoregulation or fluid balance (such as diuretics, antihypertensives, anticholinergics, antipsychotics, antidepressants and lithium), and document adjustments and counselling.", W26 + ", User action brief 1 (PDF p. 214)"),
 ("WHO_EUR", "topiramate_zonisamide"): (U, "none", "", "none", "no", "Antiepileptics", W11),
 ("WHO_EUR", "adhd_stimulants"): (U, "none", "", "none", "no", "Sympathomimetics", W11),
 ("WHO_EUR", "beta_blockers"): (S, GC, GC, "generic", "no", "Antiadrenergics and beta-blockers", W11),
 ("WHO_EUR", "epinephrine_autoinjector"): (U, "none", "", "none", "no", "This is particularly important for emergency drugs, including antibiotics, adrenergic drugs, insulin, analgesics and sedatives.", W11 + " (PDF p. 14)"),
 ("WHO_EUR", "ccb"): (S, GC, GC, "generic", "no", "Vasodilators, including nitrates and calcium channel blockers, can worsen hypotension in vulnerable patients", W11),
 ("WHO_EUR", "nitrates"): (S, GC, GC, "generic", "no", "Vasodilators, including nitrates and calcium channel blockers, can worsen hypotension in vulnerable patients", W11),
 ("WHO_EUR", "acetaminophen"): (S, HOLD, HOLD, "specific", "no", "Antipyretics such as acetylsalicylic acid and acetaminophen should be avoided because of their potential to aggravate the coagulopathy and liver injury of heatstroke.", "WHO/Europe 2011, 'management of life-threatening heatstroke' (treatment of heatstroke, not chronic medication)"),
 ("WHO_EUR", "antihistamines_1stgen"): (S, GC, GC, "generic", "no", "Antihistamines", W11),
 ("WHO_EUR", "antiparkinson"): (S, GC, GC, "generic", "no", "Anti-Parkinson agents", W11),
 ("WHO_EUR", "benzodiazepines_anxiolytics"): (S, GC, GC, "generic", "no", "Anxiolytics and muscle relaxants", W11),
 ("WHO_EUR", "carbamazepine_oxcarbazepine"): (U, "none", "", "none", "no", "Antiepileptics", W11),
 ("WHO_EUR", "digoxin"): (S, GC, GC, "generic", "no", "increase toxicity and/or decrease the efficacy of drugs, particularly those with a narrow therapeutic index, such as digoxin or lithium.", W11),
 ("WHO_EUR", "snri"): (U, "none", "", "none", "no", "Antidepressants", W11),
 ("WHO_EUR", "tca"): (U, "none", "", "none", "no", "Antidepressants", W11),
 # ---------------- Victoria ----------------
 ("VIC", "lithium"): (S, GC, GC, "generic", "no", "Increased toxicity for drugs with a narrow therapeutic index in dehydration Various Digoxin, immunosuppressants, lithium, metformin, warfarin", VIC2),
 ("VIC", "loop_diuretics"): (S, GC, GC, "generic", "no", "Frusemide, hydrochlorothiazide, acetazolamide, aldosterone", VIC2),
 ("VIC", "thiazides"): (S, GC, GC, "generic", "no", "Frusemide, hydrochlorothiazide, acetazolamide, aldosterone", VIC2),
 ("VIC", "acei_arb"): (S, GC, GC, "generic", "no", "Angiotensin-converting enzyme (ACE) inhibitors Enalapril, perindopril, ramipril", VIC2),
 ("VIC", "metformin"): (S, GC, GC, "generic", "no", "Increased toxicity for drugs with a narrow therapeutic index in dehydration Various Digoxin, immunosuppressants, lithium, metformin, warfarin", VIC2),
 ("VIC", "anticholinergics_oxybutynin"): (S, GC, GC, "generic", "no", "Other anticholinergics Benztropine, hyoscine, clozapine, olanzapine, quetiapine, oxybutynin, solifenacin", VIC2),
 ("VIC", "antipsychotics_clozapine"): (S, GC, GC, "generic", "no", "Antipsychotic drugs Clozapine, olanzapine, quetiapine, risperidone", VIC2),
 ("VIC", "adhd_stimulants"): (S, GC, GC, "generic", "no", "Stimulants Amphetamines, cocaine, thyroxine", VIC2),
 ("VIC", "beta_blockers"): (S, GC, GC, "generic", "no", "Beta-blockers Atenolol, metoprolol, propranolol", VIC2),
 ("VIC", "ccb"): (S, GC, GC, "generic", "no", "Calcium channel blockers: Amlodipine, felodipine, nifedipine", VIC2),
 ("VIC", "nitrates"): (S, GC, GC, "generic", "no", "Nitrates: glyceryl trinitrate, isosorbide mononitrate", VIC2),
 ("VIC", "tca"): (S, GC, GC, "generic", "no", "Anticholinergics – tricyclic antidepressants Amitriptyline, clomipramine, dothiepin", VIC2),
 ("VIC", "antihistamines_1stgen"): (S, GC, GC, "generic", "no", "Anticholinergics – sedating antihistamines Promethazine, doxylamine, diphenhydramine", VIC2),
 ("VIC", "antiparkinson"): (S, GC, GC, "generic", "no", "Other anticholinergics Benztropine, hyoscine, clozapine, olanzapine, quetiapine, oxybutynin, solifenacin", VIC2),
 ("VIC", "digoxin"): (S, GC, GC, "generic", "no", "Increased toxicity for drugs with a narrow therapeutic index in dehydration Various Digoxin, immunosuppressants, lithium, metformin, warfarin", VIC2),
 ("VIC", "levothyroxine"): (S, GC, GC, "generic", "no", "Stimulants Amphetamines, cocaine, thyroxine", VIC2),
 ("VIC", "laxatives"): (S, GC, GC, "generic", "no", "Stimulant laxatives Senna extract, bisacodyl", VIC2),
 # ---------------- Germany: Heidelberger Hitze-Tabelle (referenced by BMG) ----------------
 ("GER_HEID", "lithium"): (S, MON, MON, "specific", "yes", "Lithium Spiegelkontrolle. Besondere Vorsicht bei Polyurie / Diabetes insipidus", HEI),
 ("GER_HEID", "loop_diuretics"): (U, "none", "", "none", "no", "Diuretika Gewichtsmonitoring, ausreichende Flüssigkeits- und ggf. Elektrolytzufuhr", HEI),
 ("GER_HEID", "thiazides"): (U, "none", "", "none", "no", "Diuretika Gewichtsmonitoring, ausreichende Flüssigkeits- und ggf. Elektrolytzufuhr", HEI),
 ("GER_HEID", "acei_arb"): (S, MON, MON, "specific", "yes", "ACE-Hemmer, AT1-Rezeptor-Antagonisten Trinkprotokoll führen um adäquate Flüssigkeitszufuhr zu überwachen.", HEI),
 ("GER_HEID", "insulin"): (S, ADJ, "monitor;adjust_dose", "specific", "yes", "Subcutan applizierte Arzneimittel (schnell wirksames Insulin) Intensivierte Überwachung, ggf. Dosisanpassung", HEI + ", 'Beeinflussung der Pharmakokinetik durch Hitze'"),
 ("GER_HEID", "anticholinergics_oxybutynin"): (S, HOLD, HOLD, "specific", "yes", "Urologische anticholinerge Spasmolytika (z. B. Oxybutynin, Solifenacin, Tolterodin) Therapiewechsel auf weniger anticholinerge Vertreter erwägen", HEI),
 ("GER_HEID", "antipsychotics_clozapine"): (S, ADJ, "monitor;adjust_dose", "specific", "yes", "Enges UAW-Monitoring und ggf. Dosisanpassung", HEI + ", row 'Antipsychotika (... Clozapin ...)'"),
 ("GER_HEID", "ssri"): (S, GC, GC, "generic", "yes", "SSRI, SNRI (insb. auch in Kombination mit Lithium), NDRI (Bupropion)", HEI),
 ("GER_HEID", "topiramate_zonisamide"): (S, GC, GC, "generic", "yes", "Topiramat, Zonisamid 11-14", HEI),
 ("GER_HEID", "adhd_stimulants"): (S, MON, MON, "specific", "yes", "Sympathomimetika, zentral wirkend (z. B. Methylphenidat, Modafinil) Enges UAW-Monitoring", HEI),
 ("GER_HEID", "beta_blockers"): (S, GC, GC, "generic", "yes", "Betablocker 4, 58, 59", HEI),
 ("GER_HEID", "opioid_patches_fentanyl"): (S, ADJ, "monitor;adjust_dose", "specific", "yes", "Opioide als transdermale therapeutische Systeme (Pflaster) Enges UAW-Monitoring und ggf. Dosisanpassung", HEI),
 ("GER_HEID", "nsaids"): (S, GC, GC, "generic", "yes", "NSAID (inkl. COX-2 Hemmer) ? 41, 42, 57, 60", HEI),
 ("GER_HEID", "tca"): (S, HOLD, HOLD, "specific", "yes", "Möglichst vermeiden, Therapiewechsel auf weniger anticholinerge Vertreter erwägen", HEI + ", row 'Trizyklika'"),
 ("GER_HEID", "antihistamines_1stgen"): (S, HOLD, HOLD, "specific", "yes", "Wechsel auf H1-Antagonisten höherer Generationen erwägen", HEI + ", row 'Histamin-H1-Antagonisten der ersten Generation'"),
 ("GER_HEID", "antiparkinson"): (S, GC, GC, "generic", "yes", "Anticholinerge Antiparkinsonika (z. B. Trihexiphenidyl, Procyclidin) 8, 25, 58, 59", HEI),
 ("GER_HEID", "benzodiazepines_anxiolytics"): (S, ADJ, "monitor;adjust_dose", "specific", "yes", "Benzodiazepine Enges UAW-Monitoring und ggf. Dosisanpassung 45, 59", HEI),
 ("GER_HEID", "carbamazepine_oxcarbazepine"): (S, GC, GC, "generic", "yes", "Carbamazepin, Oxcarbazepin, Eslicarbazepin 7,19, 59", HEI),
 ("GER_HEID", "levothyroxine"): (S, MON, MON, "specific", "yes", "Levothyroxin (bei arzneimittelinduzierter Hyperthyreose) TSH-Kontrolle 51", HEI),
 ("GER_HEID", "laxatives"): (S, MON, MON, "specific", "yes", "Gewichtsmonitoring, ausreichende Flüssigkeits- und ggf. Elektrolytzufuhr ? 2", HEI + ", row 'Laxanzien'"),
 ("GER_HEID", "snri"): (S, GC, GC, "generic", "yes", "SSRI, SNRI (insb. auch in Kombination mit Lithium), NDRI (Bupropion)", HEI),
 ("GER_HEID", "transdermal_other"): (S, GC, GC, "generic", "yes", "Transdermale therapeutische Systeme (Pflaster, z. B. organische Nitrate, Testosteron, Nicotin)", HEI),
 ("GER_HEID", "nitrates"): (S, GC, GC, "generic", "yes", "Transdermale therapeutische Systeme (Pflaster, z. B. organische Nitrate, Testosteron, Nicotin)", HEI),
}


def main():
    full = {sid: norm(" ".join(" ".join(load_lines(fn)) for fn, _ in files)) for sid, files in SOURCES.items()}
    bad = []
    rows = []
    for sid in SOURCES:
        for drug in CORE + OTHER:
            v = P2.get((sid, drug))
            if v is None:
                v = ("none", "none", "", "none", "no", "", "")
            lvl, act, alls, spec, ev, q, loc = v
            if q and norm(q) not in full[sid]:
                bad.append((sid, drug, q[:80]))
            rows.append(dict(source_id=sid, drug_id=drug, drug_label=DRUG_LABEL[drug],
                             drug_group="core" if drug in CORE else "other",
                             mentioned="yes" if lvl == "specific" else "no", mention_level=lvl,
                             action_type=act, all_actions=alls, specificity=spec,
                             evidence_cited=ev, quote=q, location=loc,
                             coder="pass2_read_whole_section"))
    if bad:
        for b in bad:
            print("QUOTE NOT FOUND:", b)
        sys.exit(1)
    out = os.path.join(PROC, "guidance_coding_pass2.csv")
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("wrote", out, len(rows), "rows; all quotes verified verbatim")


if __name__ == "__main__":
    main()
