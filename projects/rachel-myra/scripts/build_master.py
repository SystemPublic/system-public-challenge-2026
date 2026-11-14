import csv, sys
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

OUT_XLSX = sys.argv[1]
OUT_CSV = sys.argv[2]

T1 = "1 RCT / meta-analysis"
T2 = "2 Population study"
T3 = "3 Small clinical / PK study"
T4 = "4 Case series"
T5 = "5 Case report"
T6 = "6 Lab / bench / field test"
T7 = "7 Label or guidance only"
T8 = "8 Mechanism only / no study found"
TIERS = [T1, T2, T3, T4, T5, T6, T7, T8]

DOSE, HOLD, MON, STORE, CROSS = "Dose adjustment", "Hold or substitute", "Closer monitoring", "Storage and devices", "Cross-cutting"
BUCKETS = [DOSE, HOLD, MON, STORE, CROSS]

SUP, NULL, CONF, MECH, GAP = "Supports harm", "Null / no added risk", "Conflicting", "Plausible, untested", "Evidence gap"

V, P, U, N = "Verified ID", "Partly verified", "Unverified - check before use", "No citation yet"

# (depth, mechanism, drug/class, examples, harm, bucket, severity, tier, direction, groups, prescribers, guidance, citations, status, notes)
R = [
# ---- Cooling / thermoregulation
("Basic","Cooling: less sweating","Anticholinergics","Oxybutynin, benztropine, tricyclic antidepressants, older antihistamines","Reduced sweating; heat illness and heat-related admission","Hold or substitute","High",T2,SUP,"Older adults, polypharmacy","Urology, psychiatry, neurology, primary care","Common class lists (CDC, NYC, UKHSA, Health Canada, ANSM, Germany)","PMID 17513091 (OR 6.0); DOI 10.1371/journal.pone.0243665 (RR 1.16); PMID 39513185 (+0.42 C, strong anticholinergics)",V,"Strong anticholinergic effect in trials is essentially atropine data"),
("Tail","Cooling: less sweating","Oxybutynin","Oxybutynin","Heat stroke recurring in consecutive summers in the same patient","Hold or substitute","High",T5,SUP,"Older adults; Parkinson's disease","Urology, primary care, geriatrics","Covered only under the anticholinergic class","PMID 8835047; PMID 34055543",V,"Bladder drugs are rarely thought of as dangerous"),
("Tail","Cooling: less sweating","Diphenhydramine","Diphenhydramine 50 mg","No effect on sweating, core temperature or heart rate in heat","Hold or substitute","Low",T1,NULL,"Healthy young adults only (tested)","OTC, primary care","Antihistamines listed by CDC/NYC","PMID 39140777",V,"Contradicts guidance; one dose, healthy adults, so not proof of safety in older people"),
("Tail","Cooling: less sweating","Topiramate, zonisamide (children)","Topiramate, zonisamide","Reduced sweating (oligohidrosis) leading to hyperthermia and heat stroke; often silent until heat/exertion","Hold or substitute","High",T4,SUP,"Children (all US zonisamide cases age 18 or under)","Neurology, pediatrics","Health Canada (pediatric detail); CDC/NYC list topiramate sweating","PMID 12770670; PMID 15519129; PMID 12760427",V,"About 1 case per 4,600-10,000 patient-years; 9 of 14 had abnormal sweat tests but only 3 had symptoms"),
("Tail","Cooling: less sweating","Topiramate (adults)","Topiramate for epilepsy, migraine, tremor, weight loss","Fatal heat stroke at normal drug levels; permanent neurologic injury","Hold or substitute","High",T5,SUP,"Adults; outdoor exertion","Neurology, headache medicine, obesity medicine","No adult-specific guidance found","PMID 23993866; PMID 15795554; DOI 10.1186/s13256-016-0835-5",V,"Blood-level monitoring does not protect"),
("Tail","Cooling: less sweating","Acetazolamide","Acetazolamide","Assumed reduced sweating (same mechanism as topiramate)","Hold or substitute","Unknown",T8,MECH,"Altitude, glaucoma, IIH patients","Ophthalmology, neurology, altitude medicine","Listed by CDC","None - no human case found",N,"Listing rests on inference"),
("Basic","Cooling: brain thermostat","Antipsychotics","Haloperidol, olanzapine, quetiapine, risperidone","Heat-related hospitalization and death","Closer monitoring","High",T2,CONF,"Severe mental illness, older adults","Psychiatry","Common class lists","PMID 17513091 (OR 4.6); DOI 10.1371/journal.pone.0243665 (RR 1.37); DOI 10.1017/S0033291724002824 (Japan, null interaction)",V,"Within-person studies suggest risk tracks the illness, not the drug (confounding by indication)"),
("Tail","Cooling: combined","Antipsychotic + anticholinergic in outdoor workers","Zuclopenthixol, quetiapine, benztropine","Fatal exertional heat stroke; repeat admissions despite advice","Hold or substitute","High",T5,SUP,"Outdoor workers on psychiatric meds","Psychiatry, occupational health","Not addressed","PMID 18025545; DOI 10.1345/aph.1G130",P,"PMID 18025545 link built from ID, not opened"),
("Tail","Cooling: brain thermostat","Antipsychotics (hypothermia)","Olanzapine and other strong 5-HT2 blockers","Severe hypothermia, mostly in first days after starting or raising dose","Closer monitoring","High",T4,SUP,"Schizophrenia; new starts","Psychiatry","Not addressed","PMID 21956608; DOI 10.1177/0091270011409233",V,"Drug-temperature harm runs both directions"),
("Tail","Masked warning signs","Clozapine","Clozapine","Fever may be benign or an early sign of a serious reaction; heat stroke confused with drug reactions","Cross-cutting","High",T7,MECH,"Clozapine users","Psychiatry","Not addressed","PMID 31378552; DOI 10.1016/j.schres.2019.07.040",V,"Narrative review"),
("Tail","Masked warning signs","Antipsychotics / serotonergic drugs","Antipsychotics, SSRIs","Heat stroke looks like neuroleptic malignant or serotonin syndrome","Cross-cutting","High",T7,GAP,"Psychiatric patients","Psychiatry, emergency medicine","Not addressed","DOI 10.1017/neu.2015.29",V,"No study shows ambient heat triggers NMS or serotonin syndrome"),
("Basic","Cooling: less skin blood flow","Beta blockers","Propranolol, metoprolol, atenolol","Limits heart-rate and skin blood-flow response; small core-temperature rise","Closer monitoring","Moderate",T1,CONF,"Older adults, heart disease","Cardiology, primary care","Common class lists","PMID 39513185 (+0.11 C non-selective); DOI 10.1371/journal.pone.0243665 (null for hospitalization)",V,""),
("Basic","Masked warning signs","Beta blockers","Propranolol, metoprolol","Blunt racing heart that signals heat stress or low blood sugar; break heart-rate-based wearable estimates","Cross-cutting","Moderate",T8,MECH,"Beta-blocker users","Cardiology","Not addressed","None for heat-specific masking",N,"Wearable estimators never validated in these patients"),
("Basic","Cooling: more heat production","ADHD stimulants","Methylphenidate, amphetamines","Mild exertional heat illness; rare fatal exertional heat stroke in athletes","Closer monitoring","High",T2,CONF,"Teen athletes, military recruits","Pediatrics, psychiatry, sports medicine","Generic class mention","PMID 29613996 (recruits, mild only); PMID 25469604 (fatal case); Layton 2020 null",V,"Stimulant labels do not mention heat stroke"),
("Tail","Cooling: more heat production","Prescribed appetite suppressants","(1982 case)","Child died of heat stroke on a hike 107 other children completed unharmed","Hold or substitute","High",T5,SUP,"Children","Pediatrics","Not addressed","PMID 6128802",P,"Link built from ID, not opened"),
("Tail","Cooling: less skin blood flow","Aspirin, clopidogrel","Low-dose aspirin, clopidogrel","Reduced skin blood flow; core-temperature rise in middle age but not over 65","Closer monitoring","Low",T1,CONF,"Middle-aged adults","Cardiology, primary care","Not addressed","PMID 23135368; PMID 40350968",V,""),
("Basic","Cooling: brain thermostat","SSRIs / antidepressants","Sertraline, fluoxetine, citalopram","Heat-related death signal; sweating effects disputed","Closer monitoring","Moderate",T2,CONF,"Depression, older adults","Psychiatry, primary care","Common class lists; CDC table contradicts itself on sweating","France aOR 1.71 (Nordon 2009, ID unverified); DOI 10.1017/S0033291724002824 (Japan null)",P,""),
("Tail","Cooling: brain thermostat","Serotonergic drugs","SSRIs, tramadol, triptans","Serotonin syndrome causes overheating","Closer monitoring","High",T8,GAP,"Multiple serotonergic drugs","Psychiatry, pain, neurology","Not addressed","None - no study links ambient heat to serotonin syndrome",N,""),
("Basic","Cooling: less sweating","Anti-Parkinson drugs","Trihexyphenidyl, levodopa combinations","Small core-temperature rise in trials","Closer monitoring","Moderate",T1,SUP,"Parkinson's disease","Neurology","Some class lists","PMID 39513185 (+0.13 C)",V,""),
("Tail","Harm from holding","Anti-Parkinson drugs (stopping)","Levodopa; deep brain stimulator","Abrupt stopping, missed doses or stimulator battery failure causes parkinsonism-hyperpyrexia syndrome","Cross-cutting","High",T4,SUP,"Elderly with long-standing Parkinson's","Neurology","General 'do not stop abruptly' only","DOI 10.3233/JPD-223362 (56 cases); DOI 10.1136/bcr-2018-229122; DOI 10.1002/ncp.11297",V,"Heat not shown as trigger"),
("Basic","Cooling: more heat production","Thyroid hormone (excess)","Levothyroxine","Over-replacement raises heat production","Closer monitoring","Moderate",T7,MECH,"Over-replaced patients","Endocrinology, primary care","CDC, UKHSA list thyroxine","CDC guidance",N,""),
("Basic","Awareness and behavior","Benzodiazepines, hypnotics","Lorazepam, diazepam, zolpidem","Sedation dulls awareness of overheating","Closer monitoring","Moderate",T2,CONF,"Older adults","Psychiatry, primary care","Common class lists","PMID 17513091 (OR 2.4 harm); Nordon 2009 aOR 0.85 'protective' (ID unverified); Kalisch Ellett 2016 null",P,"Apparent protection likely reflects healthier users"),
("Basic","Awareness and behavior","Opioids","Oxycodone, morphine, methadone","Sedation; mild heat illness signal in recruits","Closer monitoring","Moderate",T2,SUP,"Chronic pain, older adults","Pain medicine, primary care","Some class lists","PMID 29613996",V,"No population heat-mortality data for opioids"),
("Basic","Awareness and behavior","Polypharmacy / anticholinergic burden","Multiple drugs","Linked to heat-wave hospital admission but not death","Closer monitoring","Moderate",T2,SUP,"Older adults","Primary care, geriatrics, pharmacy","Not addressed as a score","See epidemiology notes",P,""),
# ---- Fluid, salt and kidneys
("Basic","Fluid and kidneys","Loop diuretics","Furosemide, bumetanide","Volume depletion; heat hospitalization in heart failure, MI, dementia","Dose adjustment","High",T2,SUP,"Heart failure, dementia","Cardiology, primary care","Common class lists","DOI 10.1371/journal.pone.0243665 (RR 1.54-1.84)",V,""),
("Basic","Fluid and kidneys","Non-loop diuretics","Thiazides, spironolactone","Counter-signal: no heat-wave interaction; no core-temperature effect","Dose adjustment","Low",T2,NULL,"","Primary care","Common class lists","PMID 42710533; PMID 39513185",V,""),
("Basic","Fluid and kidneys","ACE inhibitors / ARBs (+ diuretic)","Lisinopril, losartan, ramipril","Dehydration and heat-illness admission; rising creatinine","Dose adjustment","High",T2,SUP,"Older adults","Primary care, cardiology, nephrology","Common class lists","DOI 10.1111/jcpt.12418 (ratio 2.79 for combo); PMID 42710533; PMID 27992525",V,""),
("Basic","Fluid and kidneys","'Triple whammy'","Diuretic + NSAID + ACEi/ARB","Kidney injury feared, but null for in-hospital AKI in heat","Hold or substitute","Moderate",T2,NULL,"Older inpatients","Primary care, geriatrics","Some lists","PMID 29116624 (OR 1.02)",V,""),
("Basic","Fluid and kidneys","NSAIDs","Ibuprofen, naproxen","Reduced kidney blood flow; dehydration admission; mild heat illness in recruits","Hold or substitute","Moderate",T2,SUP,"Older adults, recruits","Primary care, OTC","Common class lists","DOI 10.1111/jcpt.12418; PMID 29613996",V,""),
("Basic","Salt balance","Thiazides + SSRIs","Hydrochlorothiazide, SSRIs","Low sodium (hyponatremia), worst in age 80+ and in heat waves; made worse by drinking lots of plain water","Closer monitoring","High",T2,SUP,"Age 80+, low body weight","Primary care, psychiatry","Conflict: CDC/NYC relax fluids; Health Canada warns of overdrinking","DOI 10.1210/clinem/dgac103; DOI 10.3390/ijerph14070827",V,"Thiazides + SSRIs may cause ~30% of hyponatremia admissions (thesis)"),
("Basic","Salt balance","Other low-sodium drugs","Carbamazepine, oxcarbazepine, desmopressin","Hyponatremia; no heat-specific data","Closer monitoring","Moderate",T8,GAP,"","Neurology, urology","NYC lists carbamazepine","None heat-specific",N,""),
("Basic","Drug buildup","Lithium","Lithium","Dehydration concentrates lithium into the toxic range","Closer monitoring","High",T2,SUP,"Bipolar disorder","Psychiatry","NYC narrow-margin list; Health Canada: avoid electrolyte drinks","Arizona poison-center study; Wilting (Dutch, PMID unconfirmed); Japanese congress abstract",U,"No population heat-mortality estimate for lithium"),
("Tail","Drug buildup","Dabigatran","Dabigatran","Fatal accumulation linked to summer diarrhea and low fluid intake","Closer monitoring","High",T5,SUP,"Older adults, kidney impairment","Cardiology","Not addressed","PMID 25534224",V,""),
("Tail","Drug buildup","Apixaban","Apixaban","Listed as narrow-margin drug in heat","Closer monitoring","Unknown",T7,MECH,"","Cardiology","NYC only","NYC DOHMH provider page",N,""),
("Basic","Drug buildup","Metformin","Metformin","Lactic acidosis after dehydration-related kidney injury","Hold or substitute","High",T5,MECH,"Kidney impairment","Endocrinology, primary care","Not addressed","PMC6424540 (not heat-specific)",P,""),
("Basic","Drug buildup","Digoxin","Digoxin","Toxicity when kidney function falls","Closer monitoring","High",T5,MECH,"Older adults","Cardiology","UKHSA lists","Cureus case (not heat-specific)",P,""),
("Tail","Fluid and kidneys","SGLT2 inhibitors","Empagliflozin, dapagliflozin","Volume depletion; euglycemic diabetic ketoacidosis","Hold or substitute","High",T8,MECH,"Diabetes, heart failure","Endocrinology, cardiology, nephrology","None of 8 guidance sources reviewed","Thieme Ramadan review; PMC11588271",P,"No study combines heat, SGLT2 inhibitors and DKA"),
("Basic","Fluid and kidneys","Laxatives","Senna, bisacodyl","Extra fluid and salt loss","Closer monitoring","Low",T7,MECH,"Older adults","Primary care","NYC lists","NYC DOHMH provider page",N,""),
("Basic","Drug buildup","Colchicine","Colchicine","Listed as heat-risk drug; no heat data","Closer monitoring","Unknown",T7,MECH,"","Rheumatology, primary care","UKHSA lists","UKHSA guidance",N,""),
# ---- Blood pressure and heart
("Basic","Blood pressure","Vasodilators","Tamsulosin, doxazosin, nitrates, sildenafil, calcium-channel blockers","Heat widens blood vessels too; low blood pressure, fainting, falls","Closer monitoring","Moderate",T2,MECH,"Older adults","Urology, cardiology, primary care","NYC mentions falls","PMID 42710533 (CCB heat-wave interaction, Japan); others mechanism only",P,"No heat study for alpha blockers, nitrates or PDE5 inhibitors found"),
("Basic","Heart rhythm","QT-prolonging drugs","Some antibiotics, antipsychotics, antiarrhythmics","Low potassium/magnesium from sweating raises torsades risk","Closer monitoring","High",T8,GAP,"","Cardiology, psychiatry","Not addressed","None - no heat study found",N,""),
("Basic","Blood clotting","Warfarin","Warfarin","INR drift in summer (inconsistent)","Closer monitoring","Moderate",T2,CONF,"","Cardiology, anticoagulation clinics","Not addressed","PMID 33903173",V,""),
("Tail","Blood clotting","Anticoagulants (as class)","Warfarin, DOACs","Unexpected raised dehydration/heat-illness admission after starting","Closer monitoring","Moderate",T2,SUP,"Older veterans","Cardiology","Not addressed","DOI 10.1111/jcpt.12418",V,""),
# ---- Blood sugar
("Basic","Absorption","Insulin (injected)","All insulins","Heat speeds absorption, so blood sugar can drop","Dose adjustment","High",T3,SUP,"Type 1 and type 2 diabetes","Endocrinology, primary care","Glucose checks (NYC HAN #23, unverified); not dosing","PMC1601709 (n=8 sauna study); PMC3230259",V,"Effect likely differs by formulation"),
("Basic","Blood sugar","Sulfonylureas","Glipizide, glyburide","Low blood sugar when eating less in heat","Dose adjustment","High",T8,GAP,"Older adults","Endocrinology, primary care","Not addressed","None heat-specific",N,""),
("Tail","Devices","Glucose meters and strips","Glucose meters, test strips, sensors","20-30% reading errors after brief heat and humidity; direction depends on chemistry","Storage and devices","High",T6,SUP,"Diabetes","Endocrinology, pharmacy","ANSM (France) only","PMC2717087; PMC5032940; Louie 2014 (PMID unconfirmed)",P,"'Check glucose more often' may yield unreliable numbers"),
("Tail","Storage","Insulin pens in use","Glargine and others","Counter-signal: stable at 37 C (99 F) for 3-4 weeks","Storage and devices","Low",T1,NULL,"","Endocrinology, pharmacy","CDC/NYC warn on insulin storage","PMID 36585035 (RCT); PMID 33534816",V,"Insulin more robust than labeling implies"),
("Basic","Storage","Insulin above 37 C","Insulin in cars, direct sun","Loss of potency","Storage and devices","High",T6,CONF,"","Endocrinology, pharmacy","CDC/NYC","PMID 19797814 (rabbit, potency loss at 32-37 C)",V,""),
("Tail","Devices","Insulin pumps","Pump reservoirs, tubing","Reservoir overheating; diabetic ketoacidosis after pump exposed to heat and sun","Storage and devices","High",T6,SUP,"Pump users","Endocrinology, diabetes educators","Not addressed","PMID 27789976 (industry-sponsored); PMID 19424950",V,"1999 sauna-pump DKA case could not be verified"),
("Tail","Storage","GLP-1 pens","Semaglutide, liraglutide, tirzepatide","No heat-stability or heat-absorption data found","Storage and devices","Unknown",T8,GAP,"","Endocrinology, obesity medicine","Not addressed","None found",N,""),
("Tail","Storage","Glucagon kits","Glucagon","No heat-stability data found","Storage and devices","Unknown",T8,GAP,"","Endocrinology","Not addressed","None found",N,""),
# ---- Patches
("Tail","Absorption","Opioid patches","Fentanyl, buprenorphine","Heat or fever increases absorption; fatal overdose; effect can outlast the heat","Storage and devices","High",T7,SUP,"Chronic pain, palliative care, older adults","Pain, palliative care, oncology, geriatrics","None of 8 guidance sources reviewed","FDA boxed warning; DOI 10.1097/PAF.0000000000000565; DOI 10.1186/1752-1947-6-220; Fimea warning",V,"Clearest omission in heat guidance"),
("Tail","Absorption","Other drug patches","Rivastigmine, nicotine, rotigotine","Label heat cautions","Storage and devices","Moderate",T7,SUP,"Dementia, Parkinson's, smokers","Neurology, geriatrics, primary care","Not addressed","Health Canada rivastigmine monograph; PMC3175749",P,""),
("Tail","Absorption","Patches without heat data","Clonidine, estradiol, scopolamine","No primary heat-harm studies","Storage and devices","Unknown",T8,GAP,"","Cardiology, gynecology, primary care","Not addressed","None found",N,""),
("Basic","Devices","Patches and sensors (adhesion)","Any patch, CGM sensors","Sweat loosens adhesive, so less drug or lost readings","Storage and devices","Moderate",T8,GAP,"","All","Not addressed","None - no heat study found (PMID 24876416 does not measure heat)",N,""),
# ---- Storage and emergency drugs
("Basic","Storage","Epinephrine auto-injectors","EpiPen and generics","Reduced dose after prolonged extreme heat; devices still fired","Storage and devices","High",T6,CONF,"Allergy patients","Allergy, pediatrics, primary care","CDC/NYC","PMID 25997362 (~78% dose at 70 C for 10 days); PMID 27221065",V,""),
("Basic","Devices","Metered-dose inhalers","Albuterol","Canister pressure; dose changes when used outside temperature range","Storage and devices","Moderate",T6,CONF,"Asthma, COPD","Pulmonology, primary care","CDC/NYC (bursting)","University of Arizona study (ID unverified)",U,"Storage in a hot car for 6 months did not change delivery at room temperature"),
("Tail","Storage","EMS drug kits","Lorazepam, succinylcholine, dilute epinephrine, tenecteplase","Potency loss in hot ambulances and response cars","Storage and devices","High",T6,SUP,"Emergency patients","EMS medical directors","Not addressed","PMID 24548058; PMID 23711878; PMID 8179739; PMID 32686630; PMID 40596924",V,"Midazolam held up in field studies"),
("Tail","Storage","Ketamine (EMS)","Ketamine","Conflict: large loss in South Africa vs none in US","Storage and devices","Moderate",T6,CONF,"","EMS","Not addressed","PMID 38173689; PMID 34028315",V,"South African controls looked analytically suspect"),
("Tail","Storage","Degraded tetracycline","Old tetracycline","Breakdown product injures kidneys (Fanconi syndrome)","Storage and devices","High",T5,SUP,"Hot, humid climates (historical)","Primary care, dermatology","Victoria council material only","PMID 14258922; PMID 5547594",V,"Only verified case of heat-degraded drug becoming toxic"),
("Basic","Storage","Suppositories, creams, softgels","Various","Melting, separating, capsules sticking","Storage and devices","Low",T8,GAP,"","Pharmacy","Generic storage advice","None verified",N,""),
("Basic","Storage","Levothyroxine","Levothyroxine","Possible heat instability; no data found","Storage and devices","Unknown",T8,GAP,"","Endocrinology","CDC lists","None found",N,""),
("Tail","Storage","Biologics, vaccines, eye drops","Monoclonal antibodies, vaccines, ophthalmic drops","No verified heat-stability data found in this search","Storage and devices","Unknown",T8,GAP,"","Rheumatology, ophthalmology, pharmacy","Generic storage advice","None verified",N,""),
("Tail","Supply","Mail-order medicines","Any shipped drug","About 68% of transit time outside controlled room temperature; clinical impact unknown","Storage and devices","Moderate",T6,MECH,"Mail-order users","Pharmacists, PBMs","Not addressed","Chowdhury 2023 (PMID unconfirmed); PMID 18463345",P,""),
("Tail","Supply","Oxytocin (low-income settings)","Oxytocin","Out-of-spec product from unrefrigerated storage","Storage and devices","High",T6,SUP,"Postpartum women in LMICs","Obstetrics, supply chains","Not addressed","PMC4168628",P,""),
("Tail","Supply","Insulin on Hajj","Insulin","62% of surveyed pilgrims had nowhere to store insulin","Storage and devices","Moderate",T2,SUP,"Pilgrims","Endocrinology","Not addressed","Survey (see notes)",U,""),
# ---- Systems
("Basic","Systems: power outages","Power-dependent devices","Oxygen concentrators, CPAP, nebulizers, ventilators, home dialysis","Equipment failure; ED surges; excess deaths","Cross-cutting","High",T2,SUP,"Home oxygen, nursing homes","Pulmonology, nephrology, home health, emergency planners","CDC/NYC only","PMID 16263671 (2003 NYC blackout: 52% of respiratory EMS calls); PMID 37219950; PMID 35977265; PMID 40692025",V,"Strong NYC hook"),
("Basic","Systems: power outages","Refrigerated drugs","Insulin, biologics","Spoilage when refrigeration fails","Cross-cutting","Moderate",T2,SUP,"","Pharmacy, primary care","CDC/NYC","PMID 36380330 (Puerto Rico interviews)",V,""),
("Basic","Systems: access","Missed refills","Any chronic drug","ED visits for refills and dialysis surge after outages","Cross-cutting","Moderate",T2,SUP,"","Pharmacy, primary care","Not addressed","PMID 40545799 (Houston, Hurricane Beryl)",V,""),
("Basic","Harm from holding","Drugs with withdrawal or rebound","Beta blockers, clonidine, benzodiazepines, antidepressants","Stopping abruptly causes rebound or withdrawal","Cross-cutting","High",T8,MECH,"Patients self-adjusting","All","General 'do not stop abruptly'","None heat-specific",N,""),
("Tail","Harm from holding","Diuretics in heart failure (holding)","Loop diuretics","Cutting diuretics in heat can cause fluid buildup","Cross-cutting","High",T8,GAP,"Heart failure","Cardiology","No titration guidance anywhere","None found",N,""),
("Basic","Wrong treatment","Acetaminophen, NSAIDs for heat stroke","Paracetamol, ibuprofen","Don't work for heat stroke; liver or kidney stress","Cross-cutting","Moderate",T7,SUP,"","Emergency medicine, primary care","ANSM (avoid paracetamol); CDC (liver injury)","ANSM guidance; CDC guidance",N,""),
("Tail","Masked warning signs","Wearable heat-strain estimates","Heart-rate-based core-temperature algorithms","Validated only in healthy soldiers, athletes, firefighters; miss many readings above 39 C","Cross-cutting","Moderate",T3,GAP,"Medicated, older, pregnant users","Digital health","Not addressed","Front Sports Act Living 2022; MIT Lincoln Lab report",P,"Never validated in people on beta blockers, stimulants or anticholinergics"),
# ---- Skin and sun
("Basic","Skin and sun","Photosensitizing drugs","Doxycycline, fluoroquinolones, amiodarone, sulfonamides, retinoids, St John's wort","Severe sunburn or phototoxic reaction; burned skin sweats less","Closer monitoring","Moderate",T7,SUP,"Outdoor workers","Dermatology, primary care, cardiology","CDC/NYC only (six named drugs)","CDC guidance; individual drug citations not verified in this research",N,""),
("Tail","Skin and sun","Voriconazole","Voriconazole","Raised squamous-cell skin cancer risk with long-term use","Closer monitoring","High",T1,SUP,"Lung-transplant patients","Transplant, infectious disease","Not addressed","PMID 30130598 (meta-analysis RR 1.72); PMID 22484291",V,""),
("Tail","Skin and sun","Hydrochlorothiazide","Hydrochlorothiazide","Dose-dependent non-melanoma skin cancer","Closer monitoring","Moderate",T2,SUP,"Long-term users","Primary care, cardiology","UK MHRA drug safety update (not heat guidance)","PMID 29217346",V,"Same drug appears in dehydration and sun columns"),
# ---- Populations
("Tail","Population: pregnancy","Low-dose aspirin in pregnancy","Aspirin","Appeared to blunt heat-related preterm birth rise, but heat still linked to perinatal deaths","Closer monitoring","High",T1,CONF,"Pregnant people, malaria-endemic areas","Obstetrics","Not addressed","JAMA Netw Open 2026 (via press release)",U,"Secondary analysis of RCT"),
("Tail","Population: pregnancy","Thermoregulation-affecting medicines in pregnancy","Various","Amplified effect of extreme heat on congenital heart defects (US Southwest)","Closer monitoring","High",T2,SUP,"Pregnant people","Obstetrics","Not addressed","National Birth Defects Prevention Study (ID not verified)",U,""),
("Tail","Population: dialysis","Dialysis patients","All","Heat raises same-day admission (RR 1.27) and death (RR 1.31); no drug breakdown","Closer monitoring","High",T2,GAP,"Dialysis","Nephrology","Not addressed","PMID 31397862",V,""),
("Tail","Population: MS","Dalfampridine (protective)","4-aminopyridine","May widen heat tolerance in MS; seizure risk at higher doses","Dose adjustment","Low",T3,NULL,"Multiple sclerosis","Neurology","Not addressed","Small crossover trials (see notes)",P,"Rare protective signal"),
("Tail","Population: prisons","Psychotropics in prisons","Antipsychotics, antidepressants","Heat deaths in non-air-conditioned prisons; psychotropics cited as vulnerability","Closer monitoring","High",T2,SUP,"Incarcerated people","Correctional health, psychiatry","Not addressed","JAMA Netw Open 2022 (Texas); PLoS One (US prisons)",P,"No drug-level breakdown"),
("Tail","Population: workers","Medications in new outdoor workers","Various predisposing drugs","73% of fatal heat illnesses in OSHA investigations were in the first week on the job","Closer monitoring","High",T2,SUP,"New outdoor workers","Occupational health, primary care","Not addressed","DOI 10.1097/JOM.0000000000001365",V,"First weeks of heat exposure matter most"),
("Tail","Population: gaps","Transplant (tacrolimus)","Tacrolimus, cyclosporine","No heat study found","Closer monitoring","Unknown",T8,GAP,"Transplant recipients","Transplant","Not addressed","None found",N,""),
("Tail","Population: gaps","Methadone / buprenorphine patients","Methadone, buprenorphine","No heat-wave study found","Closer monitoring","Unknown",T8,GAP,"People in opioid treatment","Addiction medicine","Not addressed","None found",N,""),
("Tail","Population: gaps","Unhoused people","Any","Nowhere cool to store medicines; no study found","Storage and devices","Unknown",T8,GAP,"Unhoused people","Street medicine, public health","Not addressed","None found",N,""),
("Tail","Population: gaps","HIV, sickle cell, cystic fibrosis, spinal cord injury","Antiretrovirals, CFTR modulators, others","No drug-by-heat studies found","Closer monitoring","Unknown",T8,GAP,"","Various","Not addressed","None found",N,""),
]

HEAD = ["ID","Risk depth","Mechanism category","Drug or class","Example drugs","What can go wrong","Action bucket","Severity","Evidence tier","Evidence direction","Higher-risk groups","Main prescribers","Guidance coverage","Key citations","Citation status","Notes"]

for r in R:
    assert len(r) == 15, r
    assert r[5] in BUCKETS, r[5]
    assert r[7] in TIERS, r[7]

rows = [[f"R{i:02d}", *r] for i, r in enumerate(R, 1)]

with open(OUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f); w.writerow(HEAD); w.writerows(rows)

wb = Workbook()
F = "Arial"
hdr_font = Font(name=F, bold=True, color="FFFFFF")
hdr_fill = PatternFill("solid", fgColor="1F4E78")
body = Font(name=F, size=10)
thin = Side(style="thin", color="BFBFBF")
wrap = Alignment(wrap_text=True, vertical="top")

# README
rd = wb.active; rd.title = "README"
lines = [
 ("Drug and heat risk master list", True),
 ("Built 13 Nov 2026 for Visualize Challenge 3. One row per drug and risk, combining the basic risk list with the deep-research report 'Prescribed drug heat risks'.", False),
 ("Not clinical advice. Rows marked 'Unverified' or 'No citation yet' must be checked before they appear in a public visual.", False),
 ("", False),
 ("Sheets", True),
 ("Risks: the master table (also saved as a CSV for the visual).", False),
 ("Summary: counts by action bucket and evidence tier (formulas update if you edit Risks).", False),
 ("Guidance: what each of the 8 reviewed guidance sources covers.", False),
 ("", False),
 ("Columns", True),
 ("Risk depth: Basic = widely known; Tail = rare, extreme or less-known.", False),
 ("Severity: High = can be fatal or permanent; Moderate = hospitalization or significant harm; Low = minor or no harm shown; Unknown = no data. This is a judgment call by the compiler, not a published grade.", False),
 ("Evidence direction: Supports harm / Null (no added risk) / Conflicting / Plausible, untested / Evidence gap.", False),
 ("Guidance coverage: based on 8 sources reviewed (CDC, NYC DOHMH, UKHSA, Health Canada, ANSM, WHO Europe, Victoria, Germany). 'Common class lists' means the class appears on most drug lists; not every source was checked row by row.", False),
 ("Citation status: Verified ID = identifier confirmed during research; Partly verified = some IDs confirmed; Unverified = check before use; No citation yet = from general knowledge or guidance only.", False),
 ("", False),
 ("Evidence tiers (strongest to weakest)", True),
 *[(t, False) for t in TIERS],
 ("", False),
 ("Key caveat: controlled trials mostly enrolled healthy young men (mean age under 30, 4.5% women), while heat-wave deaths happen in frail, older, multi-medicated people. Within-person population studies suggest many drug signals reflect the underlying illness (confounding by indication).", False),
 ("Out of scope: recreational/illicit drugs.", False),
]
for i,(t,b) in enumerate(lines,1):
    c = rd.cell(row=i, column=1, value=t); c.font = Font(name=F, bold=b, size=14 if i==1 else 10); c.alignment = Alignment(wrap_text=True, vertical="top")
rd.column_dimensions["A"].width = 120

# Risks
ws = wb.create_sheet("Risks")
ws.append(HEAD)
for r in rows: ws.append(r)
widths = [6,9,22,28,30,45,18,10,24,18,22,28,30,45,18,35]
for i,wd in enumerate(widths,1): ws.column_dimensions[get_column_letter(i)].width = wd
for c in ws[1]: c.font = hdr_font; c.fill = hdr_fill; c.alignment = Alignment(wrap_text=True, vertical="center")
sev_fill = {"High":"F8CBAD","Moderate":"FFE699","Low":"E2EFDA","Unknown":"EDEDED"}
for row in ws.iter_rows(min_row=2):
    for c in row: c.font = body; c.alignment = wrap; c.border = Border(bottom=thin)
    s = row[7].value
    if s in sev_fill: row[7].fill = PatternFill("solid", fgColor=sev_fill[s])
ws.freeze_panes = "E2"
n = len(rows) + 1
tab = Table(displayName="Risks", ref=f"A1:P{n}")
tab.tableStyleInfo = TableStyleInfo(name="TableStyleLight1", showRowStripes=True)
ws.add_table(tab)

# Summary with formulas
sm = wb.create_sheet("Summary")
sm["A1"] = "Rows by action bucket and evidence tier"; sm["A1"].font = Font(name=F, bold=True, size=12)
sm.cell(row=3, column=1, value="Evidence tier")
for j,b in enumerate(BUCKETS,2): sm.cell(row=3, column=j, value=b)
sm.cell(row=3, column=len(BUCKETS)+2, value="Total")
for i,t in enumerate(TIERS,4):
    sm.cell(row=i, column=1, value=t)
    for j,b in enumerate(BUCKETS,2):
        sm.cell(row=i, column=j, value=f'=COUNTIFS(Risks!$I$2:$I${n},$A{i},Risks!$G$2:$G${n},{get_column_letter(j)}$3)')
    sm.cell(row=i, column=len(BUCKETS)+2, value=f"=SUM(B{i}:{get_column_letter(len(BUCKETS)+1)}{i})")
tr = 4+len(TIERS)
sm.cell(row=tr, column=1, value="Total")
for j in range(2, len(BUCKETS)+3):
    L = get_column_letter(j); sm.cell(row=tr, column=j, value=f"=SUM({L}4:{L}{tr-1})")

sm.cell(row=tr+2, column=1, value="Rows by evidence direction")
dirs = [SUP, NULL, CONF, MECH, GAP]
for k,d in enumerate(dirs):
    r_ = tr+3+k
    sm.cell(row=r_, column=1, value=d)
    sm.cell(row=r_, column=2, value=f'=COUNTIF(Risks!$J$2:$J${n},A{r_})')
r0 = tr+3+len(dirs)+1
sm.cell(row=r0, column=1, value="Rows by risk depth")
for k,d in enumerate(["Basic","Tail"]):
    sm.cell(row=r0+1+k, column=1, value=d)
    sm.cell(row=r0+1+k, column=2, value=f'=COUNTIF(Risks!$B$2:$B${n},A{r0+1+k})')
r1 = r0+4
sm.cell(row=r1, column=1, value="High-severity rows with no guidance ('Not addressed' or 'None of 8')")
sm.cell(row=r1, column=2, value=f'=COUNTIFS(Risks!$H$2:$H${n},"High",Risks!$M$2:$M${n},"Not addressed")+COUNTIFS(Risks!$H$2:$H${n},"High",Risks!$M$2:$M${n},"None of 8*")')
for row in sm.iter_rows():
    for c in row:
        c.font = Font(name=F, size=10, bold=(c.row in (tr, tr+2, r0)))
sm["A1"].font = Font(name=F, bold=True, size=12)
for c in sm[3]: c.font = hdr_font; c.fill = hdr_fill; c.alignment = Alignment(wrap_text=True)
sm.column_dimensions["A"].width = 40
for j in range(2, len(BUCKETS)+3): sm.column_dimensions[get_column_letter(j)].width = 16

# Guidance
g = wb.create_sheet("Guidance")
GH = ["Source","Drug content","Actions","Storage / devices / outages","Evidence basis stated","Notable omissions"]
G = [
("CDC 'Heat and Medications - Guidance for Clinicians' (Sept 2025)","Broadest class table; acetaminophen liver injury, levothyroxine, indinavir, topiramate sweating, pediatric drugs","Medication review; individualized dose changes; relax fluid restriction; HeatRisk-day plan","Insulin, EpiPen, inhaler bursting, cars; outage plan for refrigerated drugs, nebulizers, ventilators, oxygen; photosensitizers","Expert opinion, ungraded","Fentanyl patches, SGLT2 inhibitors, glucose meters; SSRI sweating contradicts itself"),
("NYC DOHMH provider page (2025) + 2026 HAN alerts","Mirrors CDC; adds apixaban, carbamazepine, lithium as narrow-margin; laxatives, antacids, TMP-SMX; falls","Same as CDC; AC at 78 F; HEAP cooling assistance; HAN #23 reportedly more glucose checks","Inhalers, EpiPens, insulin, outage plan","No primary studies cited","Patches; meter errors; insulin dosing"),
("UKHSA healthcare professionals page (Dec 2024)","Class list incl. colchicine, digoxin, chemotherapy, thyroxine","Assess risk-benefit; adapt care plans; fluid monitoring","Store below 25 C","None stated","Patches, photosensitivity, insulin, devices, power"),
("Health Canada Technical Guide Ch. 4 (2011)","Class table; topiramate pediatric hypohidrosis","Hydrate/protect/monitor; lithium: avoid electrolyte drinks; overdrinking causes hyponatremia","Insulin storage only","Only source citing odds ratios and non-significant results","Patches, photosensitivity, outages; 15 years old"),
("France ANSM 'Canicule et produits de sante' (2017)","Diuretics, nephrotoxics, neuroleptics, serotonergics, antihypertensives, sedatives","No systematic dose cuts; avoid paracetamol for heat stroke","Only source on glucose strip/sensor heat errors","Not graded","Patches; SGLT2 inhibitors"),
("WHO Europe heat-health action plan guidance (2008; 2nd ed. reported 2026, unverified)","No medication-specific clinical content found","Planning framework","Unclear","Systematic reviews for planning","Drug-level content"),
("Victoria, Australia CHO advisory (Jan 2026)","Generic statements","Clinician roles; cool-box for medicines","Council material notes degraded drugs can be toxic","None stated","Drug-specific actions"),
("Germany Hitzeschutzplan (2023) + 2024 model plans","Practice lists: diuretics, ACEi, ARBs, antidepressants, anticonvulsants, antipsychotics","Medication review; storage","Heat-sensitive storage","None stated","No federal drug-by-drug list"),
]
g.append(GH)
for r in G: g.append(list(r))
for c in g[1]: c.font = hdr_font; c.fill = hdr_fill; c.alignment = Alignment(wrap_text=True)
for row in g.iter_rows(min_row=2):
    for c in row: c.font = body; c.alignment = wrap
for i,wd in enumerate([38,40,40,40,26,36],1): g.column_dimensions[get_column_letter(i)].width = wd
g.freeze_panes = "B2"

wb.active = 0
wb.save(OUT_XLSX)
print(len(rows), "rows")
