# Batch 2/2 — death causes, complaint conditions, tree species vs SPG

Same rules as batch 1. Death causes already carry Tier-0 Wikidata anchors
(ICD-10 verified) — accept them into your output with method=anchor unless you
believe an anchor is wrong; add any additional SPG concept matches as method=llm.
For tree species, expect mostly no-match: only match where an SPG concept clearly
refers to the species or to species-level health concepts.

## SPG-473 concepts (the matching universe)

| system_id | wikidata_id | label | description | aliases | domains |
|---|---|---|---|---|---|
| cxcREl4-U9 | Q1517140 | long-term depression | activity-dependent reduction in the efficacy of neuronal synapses lasting hours or longer  | LTD; long-term synaptic depression; long term synaptic depre | Mental health |
| e_lhH9g8QC | Q18975599 | bovine respiratory disease complex | bovine disease |  | Respiratory |
| _zLVUxvG7F | Q1515895 | socioeconomic status | economic and social measure of a person's affluence and/or influence | socioeconomic factor; socioeconomic factors; socio-economic  | Socioeconomic |
| _kKg1dUMhP | Q5558337 | giant-cell carcinoma of the lung | lung carcinoma that is located in large undifferentiated cells | lung giant cell carcinoma; Giant cell carcinoma; Giant cell  | Respiratory |
| de70POr9Rk | Q461576 | Cortical spreading depression | type of evoked potential | spreading depolarization; Leão's spreading depression; Leão' | Mental health |
| 9_1ct5QGco | Q54928431 | Masked Hypertension | Phenomenon where increased BLOOD PRESSURE readings taken in non-clinical settings (e.g., H |  | Cardiovascular |
| RF7tCwCaa5 | Q105217314 | vegetation cover | biogeographic feature of a landscape |  | Green space |
| 2M0TDlEdLk | Q12643772 | heat exhaustion | caused by the loss of water and electrolytes through sweating |  | Heat & temperature |
| 09dv6lYllX | Q5055020 | income inequality | divergence in economic well-being within a group | economic inequality | Socioeconomic |
| mz6SXR841t | Q54974207 | out-of-hospital cardiac arrest | heart arrest in an individual when there is no immediate access to medical personnel or eq |  | Cardiovascular |
| wYrczD56jV | Q18975749 | cardiovascular tuberculosis | human disease | Tuberculosis, Cardiovascular | Cardiovascular |
| f5PgkT0rn4 | Q2914583 | psychotic depression | major depressive episode that is accompanied by psychotic symptoms | psychogenic depressive psychosis; Depressive type psychosis; | Mental health |
| -8Mo0o-1cl | Q126888 | artificial heart | medical device |  | Cardiovascular |
| q2oC2WLTZe | Q28163641 | pulmonary surfactant | medication | Lung surfactant; Pulmonary Surfactants; Surfactant, Pulmonar | Respiratory |
| 0dV5FQbqSS | Q169994 | smog | severe air pollution |  | Air pollution |
| RSZEdA6qW6 | Q98840270 | Excess mortality | statistical figure |  | Mortality |
| YNbCxuCgg4 | Q1329925 | sudden cardiac death | sudden stop in effective blood flow due to the failure of the heart to contract effectivel | Death, Sudden, Cardiac | Cardiovascular; Mortality |
| 9qDOoWLHQf | Q67264434 | cardiac valve annuloplasty | type of heart valve surgery that involves the repair, replacement, or reconstruction of th |  | Cardiovascular |
| gOD3TnGSb1 | Q25304032 | management of hypertension |  |  | Cardiovascular |
| 3d7r8xp8QA | Q16934669 | heart septal defect | Human disease | Cardiac septal defects; Cardiac septal defects (disorder); C | Cardiovascular |
| 2PIXy-gC1s | Q922640 | bronchopulmonary dysplasia | Human disease of premature infants | Bronchopulmonary dysplasia of newborn (disorder); Perinatal  | Respiratory |
| fSlFv-kHLH | Q70373813 | Mental Health Associations | Voluntary organizations which support educational programs and research in psychiatry with |  | Mental health |
| 4ixfP1w8VB | Q190259 | thermoregulation | ability of an organism to keep its body temperature within certain boundaries | body temperature regulation | Heat & temperature |
| AuVqsRwhO8 | Q6947899 | blunt cardiac injury | injury to the heart as the result of blunt trauma | myocardial contusion | Cardiovascular |
| Es_Qsswv-8 | Q1615191 | cardiac catheterization | insertion of a catheter into a chamber or vessel of the heart | Cardiac Catheterization | Cardiovascular |
| VbfmvyKDDY | Q7663898 | systolic heart murmur | medical condition | systolic murmur | Cardiovascular |
| CLmVRAXLtF | Q4778774 | Aortopulmonary septal defect | medical condition | A-P window | Respiratory |
| RAmiNpUHBd | Q944333 | sensory deprivation | the act of deliberately removing or reducing stimuli |  | Socioeconomic |
| MF1dnPBumx | Q108858651 | chronic heart disease | type of heart disease |  | Cardiovascular |
| lWpMfc7aO5 | Q72393122 | heart rate determination |  |  | Cardiovascular |
| 7GaoH7ZDjR | Q3519556 | death anxiety | anxiety caused by thoughts of death | thanatophobia; Death anxiety | Mental health; Mortality |
| V4aKFMKpdE | Q7886 | lung | essential respiration organ in many air-breathing animals | lungs; Borders of the lung; Lung | Respiratory |
| LbPlJM7Hm- | Q1060911 | heart murmur | heart sound produced when blood flows across one of the heart valves that are loud enough  | cardiac murmur; heart murmurs | Cardiovascular |
| V0mQQRvr7_ | Q124604 | portal hypertension | hypertension in the hepatic portal system | Hypertension, Portal | Cardiovascular |
| _yOrB5cg3O | Q2299606 | psychiatric somatotherapy | treatment of mental illness by physical means rather than psychotherapy | somatic therapy; Psychiatric Somatic Therapies | Mental health |
| 5ylKZnx6I6 | Q9390268 | community mental health service |  | CMHS; community mental health teams; CMHT | Mental health |
| yPfH_YBxUJ | Q16847090 | income | United States legal definitions of income |  | Socioeconomic |
| cieZvNi89D | Q54911848 | cardiovascular abnormality | congenital, inherited, or acquired anomalies of the cardiovascular system, including the h | cardiovascular abnormalities | Cardiovascular |
| UVPqnwWRzp | Q282454 | artificial heart valve | device implanted in the heart of a patient with valvular heart disease | Heart Valve Prosthesis | Cardiovascular |
| rYCo7LTyzN | Q69032838 | heat stroke | failure of the body to dissipate heat in an excessively hot environment, or during physica | heatstroke | Cardiovascular; Heat & temperature |
| FmwmmCV7hu | Q418939 | heat shock proteins | proteins synthesized in response to hyperthermia and other environmental stresses | Heat-Shock Proteins; heat shock protein | Heat & temperature |
| UCOLbfj4o6 | Q38112 | forestry | science and craft of creating, managing, using, conserving and repairing forests, woodland | Forestry | Green space |
| suGihS8vGs | Q11821184 | total lungs capacity |  |  | Respiratory |
| tzuQSi4YbE | Q3658562 | non-small-cell lung carcinoma | any type of epithelial lung cancer other than small-cell lung carcinoma | NSCLC; non-small cell lung carcinoma; Non-small cell lung ca | Respiratory |
| 0qX3yizFGr | Q2290446 | idiopathic pulmonary fibrosis | chronic, irreversible and ultimately fatal disease characterized by a progressive decline  | FIBROCYSTIC PULMONARY DYSPLASIA; IDIOPATHIC PULMONARY FIBROS | Respiratory |
| jQx2Q-ElPQ | Q189331 | heart arrhythmia | group of conditions in which the heartbeat is irregular, too fast, or too slow | cardiac arrhythmia; cardiac irregularities; arrhythmia; disr | Cardiovascular |
| 7aDmtHlI06 | Q54944094 | pulmonary echinococcosis | helminth infection of the lung caused by Echinococcus granulosus or Echinococcus multilocu |  | Respiratory |
| 17spa7Z89f | Q55999785 | choanal atresia-hearing loss-cardiac defects-craniofacial dysmorphism syndrome | human disease | BURN-MCKEOWN SYNDROME; Oculootofacial Dysplasia; Choanal atr | Cardiovascular |
| nyF_qLUsoJ | Q21116494 | Heat shock protein family A (Hsp70) member 5 | mammalian protein found in Homo sapiens | immunoglobulin heavy chain-binding protein; BiP; 78 kDa gluc | Heat & temperature |
| OmSPyYqNuD | Q1073121 | heart rate | number of contractions (beats) of the heart per minute (bpm) | heart pulse; HR; cardiac rate; pulse rate; heartbeat rate | Cardiovascular |
| CPu3fKZt34 | Q751803 | body temperature | temperature, vital sign, measurement | BT; Body temperature, BT | Heat & temperature |
| UbF0-c8zHb | Q215712 | urban heat island | urban area that is significantly warmer than its surrounding rural areas due to human acti | UHI; heat island | Heat & temperature |
| zDwqMsbSzn | Q70339465 | pulmonary ventilation flow | volume of gas inspired or expired per unit of time, usual units liters/minute. | pulmonary ventilation | Respiratory |
| 2x6XloVEJw | Q1963724 | food deprivation | withholding of food in a structured experimental situation | Food Deprivation | Socioeconomic |
| i_Fdvs4tkJ | Q840646 | premature heart beat | Heart rhythm disorder | premature cardiac complex; extrasystole; premature beat; Pre | Cardiovascular |
| FKa6mvT7u0 | Q5374276 | Employee Retirement Income Security Act of 1974 | U.S. tax and labor law | Employee Retirement Income Security Act; ERISA | Socioeconomic |
| EhpdS79G1u | Q5404323 | ethnicity | a person's ethnic background |  | Socioeconomic |
| bmiCmSbxHY | Q110775399 | radio immunoprecipitation assay | analytic technique | RIPA; radioimmunoprecipitation assay; radioimmunoprecipitati | Flooding & storms |
| 0CU4MZJc47 | Q7170591 | personal income | individual's total earnings | income; person's income; income of a person | Socioeconomic |
| bIwjlkmcHV | Q10294 | poverty | lack of a certain amount of material possessions or money | Poverty | Socioeconomic |
| R9aAWmx82G | Q4430231 | social deprivation | limited access to society's resources caused by poverty, discrimination or other disadvant | psychosocial deprivation; socioeconomic deprivation | Socioeconomic |
| dR8IKnoGAz | Q7259529 | pulmonary hemorrhage | medical condition | pulmonary haemorrhage | Respiratory |
| XXXYGKTOxM | Q967103 | heart sound | noise generated by the beating heart and the resultant flow of blood through it | cardiac sound; sound of heartbeat; heartbeat sound; heart so | Cardiovascular |
| bjjYIW180T | Q1426787 | test anxiety | physiological condition |  | Mental health |
| RGkWJeCzQ9 | Q18553330 | extrapulmonary tuberculosis | respiratory disease | Extrapulmonary tuberculosis; Tuberculosis, Extrapulmonary | Respiratory |
| EfqHrtO0Sb | Q20679883 | psychological theory | theory to explain psychological phenomena |  | Mental health |
| b62duiavCn | Q75083620 | involuntary psychiatric treatment | treatment of persons with mental disorders without their consent | Involuntary Treatment, Psychiatric | Mental health |
| GXPo2ZlO9e | Q3324547 | neonatal mortality | type of mortality | neonatal death | Mortality |
| Ji_2iMcJrJ | Q1507383 | sea surface temperature | water temperature close to the ocean's surface | SST | Heat & temperature |
| sntHhAqkI0 | Q1877473 | lung metastasis | Human disease | metastasis to lung; metastatic tumor to the lung; secondary  | Respiratory |
| 2a0iSAxMzH | Q18554296 | chronic pulmonary heart disease | Human disease |  | Cardiovascular; Respiratory |
| 5DCMaxArTC | Q464880 | American Heart Association | US nonprofit funding cardiovascular medical research, educating consumers on healthy livin | AHA; Association for the Prevention and Relief of Heart Dise | Cardiovascular |
| SQuBf6o2Te | Q188638 | mood disorder | any of various disorders characterised primarily by disturbance in an individual's mood | episodic mood disorder; affective psychosis; affective disor | Mental health |
| K2UoargABY | Q821508 | sudden unexpected death in epilepsy | fatal complication of epilepsy | SUDEP | Mortality |
| PWqr_kRuwW | Q11788761 | renal hypertension | human disease | hypertensive renal disease; hypertensive nephropathy | Cardiovascular |
| NBYWLjvqUq | Q107538662 | embolic stroke | ischemic stroke by blockage somewhere other than the brain that subsequently restricts blo | embolic strokes | Cardiovascular |
| dWZL1SSLLt | Q6537255 | Lewis lung carcinoma | mouse tumour that happened in 1951 and is still used in research |  | Respiratory |
| a_vrrgthrs | Q5832696 | idiopathic pulmonary arterial hypertension |  | Ayerza's disease; IPAH; Ayerza's syndrome; Primary pulmonary | Cardiovascular; Respiratory |
| ccvd2b5sNn | Q3020720 | total anomalous pulmonary venous connection |  | total anomalous pulmonary venous return; TAPVR | Respiratory |
| yGcHpujgBi | Q3064207 | cardiovascular disease risk factor |  | Cardiovascular risk | Cardiovascular |
| M_o91ghaOq | Q5038325 | cardiac magnetic resonance imaging | biomedical imaging technology | CMR; cardiac MRI | Cardiovascular |
| of1GEB2i2t | Q181754 | heart failure | failure of the heart to provide sufficient blood flow | HF; congestive heart failure; congestive cardiac failure; ca | Cardiovascular |
| bPmIoJSEb9 | Q215620 | heart valve | flap of tissue that prevent backflow of blood around the heart | cardiac valve; heart valves; cardiac valves | Cardiovascular |
| 1w7NpJrycz | Q188605 | pulmonary emphysema | human disease | emphysema | Respiratory |
| hetipX0cZf | Q19000661 | congestive heart failure | human disease | CHF; Cardiac Failure Congestive; congestive heart disease; w | Cardiovascular |
| rTbYdlAa-H | Q18558122 | acute myocardial infarction | human disease | AMI; myocardial infarction (disease), acute | Cardiovascular |
| UlwgbsVl6u | Q1072 | heart | inner organ for the circulation of blood |  | Cardiovascular |
| dUXrhKbUab | Q114397298 | school mental health services | services which focus on the mental well-being of pre-college and pre-university students | School Mental Health Service | Mental health |
| L7Z6wSp_ju | Q2869826 | pulmonary atresia with Ventricular Septal Defect | type of congenital heart defect | PA-VSD; PULMONARY ATRESIA WITH VENTRICULAR SEPTAL DEFECT; Pu | Respiratory |
| Nnr_i0oykd | Q16679262 | human body temperature | typical temperature range found in humans | normothermia; euthermia | Heat & temperature |
| AP1k1Rhl5S | Q1698533 | stroke volume | volume of blood pumped from the left ventricle per beat | SV | Cardiovascular |
| 69A6FsOr2S | Q15822797 | cardiac embolism |  |  | Cardiovascular |
| EBIUU9-fn4 | Q9363854 | aneurysm of heart | Human disease | heart aneurysm; cardiac aneurysm | Cardiovascular |
| yEqtMmLzM0 | Q76949971 | HSP72 Heat-Shock Proteins | Stress-inducible members of the heat-shock proteins 70 family. HSP72 heat shock proteins f |  | Heat & temperature |
| XL9NGuFDka | Q7834435 | Transition temperature | Temperature at which some solid substances change from one crystal structure to another |  | Heat & temperature |
| Ri3nSz9b0j | Q112206936 | psychosocial deprivation | absence of appropriate stimuli in the physical or social environment which are necessary f |  | Socioeconomic |
| JFtWgkkJ4M | Q206280 | pulmonary artery | artery in the pulmonary circulation that carries deoxygenated blood from the heart to the  | pulmonary arterial tree; pulmonary arteries | Respiratory |
| QJ7xqA4q7F | Q47912 | lung cancer | cancer in the lung | malignant lung tumor; malignant neoplasm of lung | Respiratory |
| 8PqtO_E2yO | Q881480 | anomalous left coronary artery from the pulmonary artery | coronary artery anomaly in which the left coronary artery (LCA) branches off the pulmonary | ALCAPA; Bland-White-Garland syndrome; White-Garland syndrome | Respiratory |
| q9jcq6Czei | Q30397754 | fetal death | death of the developing young in utero |  | Mortality |
| wfUNWSu4xf | Q21109885 | chronic respiratory disease | disease |  | Respiratory |
| 9mg_9464KH | Q112682357 | psychological burnout | excessive reaction to stress caused by one's environment | Burnout, Psychological | Mental health |
| QClUb6qnEq | Q12047512 | psychological phenomenon | fact studied in psychology or a psychological event that manifests itself in a particular  | psychological event; psychological effect; psychological phe | Mental health |
| e-jFghbtVp | Q1339137 | psychological abuse | form of abuse characterized by a person subjecting or exposing another to behavior that ma | emotional abuse; mental abuse; psychological violence | Mental health |
| U5-j27z_zb | Q54935113 | cardiovascular Infection | pathological condition of the cardiovascular system caused by infections | Infections of the circulatory system | Cardiovascular |
| mKz8emd6oU | Q7204815 | pleuropulmonary blastoma | pulmonary blastoma that derives from the lung or pleural cavity | Pleuropulmonary blastoma (morphologic abnormality); Pleuropu | Respiratory |
| kAkzNkpuJM | Q17045323 | Luria-Nebraska neuropsychological battery |  |  | Mental health |
| lPNBkdfh_o | Q67520723 | perinatal mortality | deaths occurring from the 28th week of gestation to the 28th day after birth in a given po |  | Mortality |
| V2VuXnbHrg | Q106880927 | psychological distance | degree of a person's detachment from emotional involvement |  | Mental health |
| AByRAdx2GF | Q1429176 | flooding | form of exposure therapy | in vivo exposure therapy; flooding therapy | Flooding & storms |
| v0YeWynnXk | Q8775887 | hypertensive heart disease | heart disease that is caused by high blood pressure | malignant hypertensive heart disease; malignant hypertensive | Cardiovascular |
| FUinUSBBJq | Q988405 | essential hypertension | hypertension with no known cause, the most common type of hypertension | idiopathic hypertension; primary hypertension | Cardiovascular |
| lUEv_RFu_j | Q2353024 | radiation-induced lung injury | medical condition | Radiation Pneumonitis | Respiratory |
| sMnMz5Z-X0 | Q2551913 | occupational asthma | medical condition caused or exacerbated by the workplace | work-related asthma; Asthma, Occupational | Respiratory |
| -5WDLc2uKT | Q1414127 | pulmonary wedge pressure | pressure measured by wedging a pulmonary catheter with an inflated balloon into a small pu | pulmonary artery wedge pressure; pulmonary artery occlusion  | Respiratory |
| 6kDSxD8B6s | Q7256373 | psychological adaptation | state of harmony between internal needs and external demands | Adaptation, Psychological | Mental health |
| vHklvCywY0 | Q552304 | cardiopulmonary bypass | technique that temporarily takes over the function of the heart and lungs during surgery | CBP | Respiratory |
| SSbC3-KBT1 | Q65559775 | psychological model | theoretical representation that simulates psychological or social processes | psychological models; Models, Psychological; psychology mode | Mental health |
| N6jEeY7uT7 | Q3491521 | psychological pain | unpleasant feeling of a psychological nature | emotional pain; mental suffering; mental pain | Mental health |
| GPvAv7fRbV | Q7239981 | prehypertension | American medical classification for cases where a person's blood pressure is elevated abov | high normal blood pressure; borderline hypertensive; BH; ele | Cardiovascular |
| OwGfeu3HeB | Q3296793 | renovascular hypertension | Human disease | Renovascular hypertension (disorder); Renovascular hypertens | Cardiovascular |
| EAshH_Ko3h | Q35869 | asthma | long-term disease involving inflamed airways | exercise-induced asthma; chronic obstructive asthma; chronic | Respiratory |
| CThjyYd_6x | Q493682 | Athletic heart syndrome | nonpathological condition commonly seen in sports medicine | AHS; athlete's heart; athletic bradycardia; exercise-induced | Cardiovascular |
| cA98nQifb1 | Q99312209 | stages of death | physiological changes that occur in bodies after death | postmortem changes | Mortality |
| RWtBGa2zmx | Q73499568 | Heart Bypass, Left |  |  | Cardiovascular |
| PqwSpEyRvq | Q30015589 | Cardiac Edema | Abnormal fluid retention by the body due to impaired cardiac function or heart failure. It | Cardiac Edemas | Cardiovascular |
| 9ODCuXMCwH | Q18966975 | cardiovascular disorder in pregnancy | Human disease | antepartum congenital cardiovascular disorder of mother; pos | Cardiovascular |
| HOwlRHgUY4 | Q20494879 | performance anxiety | anxiety related to the execution of a task |  | Mental health |
| ex8Ctqrcg- | Q2383867 | cell death | biological processes that result in permanent cessation of all vital functions of a cell | GO:0008219 | Mortality |
| j48uLZ4krh | Q18554794 | primary pulmonary hypertension | chronic pulmonary heart disease characterized by an increase of blood pressure in the pulm | Familial Primary Pulmonary Hypertension | Cardiovascular; Respiratory |
| uejMsorb_s | Q104778232 | COVID-19 mortality | death rate of COVID-19 | COVID-19 death rate; COVID-19 mortality rate; mortality of C | Mortality |
| Ajcpmb_YZZ | Q2529980 | bird fancier's lung | extrinsic allergic alveolitis which is caused by inhalation of antigens from avian excreta | Avian hypersensitivity Pneumonitis; Bird-fancier's lung NOS  | Respiratory |
| VsO_M8PMFZ | Q1153419 | interstitial lung disease | group of lung diseases affecting the interstitium (the tissue and space around the air sac | ILD; interstitial pneumonitis; Lung Diseases, Interstitial;  | Respiratory |
| FCBqAD2YzH | Q32446 | pulmonary fibrosis | human disease | Fibrosis of lung (disorder); interstitial fibrosis; Fibrosis | Respiratory |
| AOvlaewUx5 | Q570938 | net income | measure of the profitability of a business venture | bottom line; total comprehensive income; net earnings; net p | Socioeconomic |
| Yo_DxH11P_ | Q1777563 | White coat hypertension | medical condition | White coat syndrome | Cardiovascular |
| PTOzpG3Tlu | Q843799 | adenocarcinoma of the lung | non-small cell lung carcinoma that derives from epithelial cells of glandular origin | lung adenocarcinoma; nonsmall cell adenocarcinoma; adenocarc | Respiratory |
| NSSHqnR5tw | Q112207514 | housing quality | physical condition of a home, with its social and physical environment |  | Housing & energy |
| 5jSeW0wT3c | Q1637912 | lung transplant | surgical procedure in which a patient's diseased lungs are partially or totally replaced | Lung transplantation; Lung transplant; pulmonary transplanta | Respiratory |
| _jTc4NTKcD | Q73217314 | Cardiovascular Surgical Procedure |  | Cardiovascular Surgical Procedures; Cardiovascular Surgery | Cardiovascular |
| XoQ89IM23p | Q18558028 | pulmonary subvalvular stenosis | Human disease | Congenital Infundibular Stenosis; Infundibular pulmonic sten | Respiratory |
| qsovrqdaJf | Q737510 | pulmonary aspiration | entry of materials into the larynx (voice box) and lower respiratory tract | choking to death on one's own vomit; respiratory aspiration | Respiratory |
| blnho3BgEP | Q102293983 | intermittent asthma | human disease |  | Respiratory |
| zmOHHFSXfv | Q1128595 | pulmonary hypertension | medical condition | Hypertension, Pulmonary | Cardiovascular; Respiratory |
| k9BAffdSqv | Q215864 | heat wave | prolonged period of excessively hot weather | heatwave | Heat & temperature |
| yREsvjahvs | Q69904376 | psychiatric status rating scales | standardized procedures with rating scales or interviews by health personnel for evaluatin | Psychiatric Status Rating Scale | Mental health |
| kZIzSorHA_ | Q180481 | ambulance | vehicle equipped for transporting and caring for ill and wounded people | emergency ambulance; patient transport ambulance; patient tr | Emergency care |
| UlVlfx0REq | Q66560263 | fetal heart |  |  | Cardiovascular |
| 0Y9-NbbcxM | Q69906342 | Paternal Deprivation | Prolonged separation of the offspring from the father. |  | Socioeconomic |
| ebPDrSj9IR | Q6704277 | Lung cancer screening | cancer screening strategies used to identify early lung cancers |  | Respiratory |
| koij5vA3mk | Q66591230 | cardiac myoblast | cell type | cardiac myoblasts | Cardiovascular |
| 37CaVKixnc | Q191341 | pulmonary alveolus | hollow cavity found in the lungs | lung alveolus; alveolus; alveoli; pulmonary alveoli | Respiratory |
| 5TqghvALVZ | Q107538760 | thrombotic stroke | ischemic stroke caused by a blood clot obstruction in a cerebral artery |  | Cardiovascular |
| rjmOQRtwLp | Q1481109 | inbreeding depression | reduced fitness as a result of inbreeding |  | Mental health |
| YTbqIbITBX | Q7259546 | pulmonary injury | type of injury | lung toxicity; lung injury; lung injuries | Respiratory |
| mkVtWh4Xyx | Q73210964 | Electrophysiologic Techniques, Cardiac |  |  | Cardiovascular |
| GoNDdwhLIj | Q30078800 | heart auscultation |  | cardiac auscultation | Cardiovascular |
| AgplLpONjs | Q71241498 | Cardiovascular Deconditioning | A change in cardiovascular function resulting in a reduction in BLOOD VOLUME, and reflex D |  | Cardiovascular |
| S40mWtHI5O | Q24781095 | Death effector domain | InterPro Domain | DED_dom; IPR001875 | Mortality |
| naXG7INXnD | Q76723398 | Cardiac Myosins | Myosin type II isoforms found in cardiac muscle. |  | Cardiovascular |
| u-bPtQmR-M | Q15330599 | cardiac conduction | Transfer of an organized electrical impulse across the heart to coordinate the contraction | GO:0061337 | Cardiovascular |
| LvmcmY8Gys | Q5915679 | myocardial infarction with ST segment elevation | clinical syndrome defined by myocardial ischemoa symptoms, elevation in the ST segments of | ST Elevation Myocardial Infarction | Cardiovascular |
| zJA52Pnkhs | Q54911326 | parental death | death of a parent or another person in this role | death of a parent; death of mother; death of father | Mortality |
| dFNHfjsBOY | Q3710397 | asthma spacer | medical equipment |  | Respiratory |
| KL9nAV1WXN | Q54972627 | multiple pulmonary nodules | small lung lesions characterized by small round masses of 2- to 3-mm in diameter |  | Respiratory |
| k2uaVp_DyN | Q1931388 | cause of death | specific disease or injury resulting in a human's death, which may be recorded on a death  | cause-of-death; death cause | Mortality |
| FDdj35kNIa | Q3843792 | carcinoid heart disease | Cardiac manifestation of gastrointestinal CARCINOID TUMOR that metastasizes to the liver.  |  | Cardiovascular |
| z9PTYOrRrw | Q21128904 | heart injury | general or unspecified injury to the heart | heart injuries | Cardiovascular |
| 8upvfqC_S7 | Q7259520 | pulmonary artery pressure | measure of the blood pressure found in the main pulmonary artery. | PAP | Respiratory |
| -fRMDZ236S | Q25324124 | Pulmonary vein stenosis | medical condition |  | Respiratory |
| PDTWFCEP5B | Q29325697 | homeless person | person having no permanent residence despite being from a culture that normally has one | homeless persons; homeless people; homeless; street people;  | Housing & energy |
| FXkZ1H-0do | Q18658526 | place of death | place where a person died | POD; location of death; deathplace | Mortality |
| Ptzt6XUjiS | Q70696257 | cardiovascular physiological phenomena | processes and properties of the cardiovascular systems and its parts | cardiovascular physiological phenomenon | Cardiovascular |
| 1pR1MGj_du | Q4967025 | Brief Psychiatric Rating Scale | psychiatric symptom rating scale | BPRS | Mental health |
| CDJewvbYAW | Q1561657 | child poverty | state of children living in poverty | childhood poverty | Socioeconomic |
| SimY67XTIv | Q107538694 | ischemic stroke | stroke caused by brain ischemia, affecting blood flow to the brain | ischemic strokes; ischaemic stroke; ischemic cerebrovascular | Cardiovascular |
| qvM3I4ZvpU | Q161801 | sudden infant death syndrome | syndrome that is characterized by the sudden death of an infant that is not predicted by m | cot death; Cot death (context-dependent category); Crib deat | Mortality |
| 49HI2AO6xm | Q1572854 | psychiatric medication | a drug used to treat mental health disorders | psychopharmaceutical; psychiatric drug | Mental health |
| rDFF7BbT8m | Q27983244 | extravascular lung water | body fluid |  | Respiratory |
| p_qK6xwpyO | Q7552863 | sociology of race and ethnic relations | field of study | race relations | Socioeconomic |
| UYlrBpc8jJ | Q210999 | psychiatric hospital | hospital treating serious mental disorders | mental hospital; psychiatric ward; Department of Psychiatry; | Mental health |
| OvDq2AkeWs | Q1877550 | lung abscess | lung disease characterized by microbial infection which causes a type of liquefactive necr | purulent pneumonia | Respiratory |
| UROxo4ratK | Q6469117 | lacunar stroke | medical condition | lacunar infarct; Stroke, Lacunar | Cardiovascular |
| uCuMzb3iy7 | Q67639562 | cardiac-gated imaging techniques | timing the acquisition of imaging data to specific points in the cardiac cycle to minimize | Cardiac-Gated Imaging Technique | Cardiovascular |
| nmM2-pbiAR | Q11611665 | lung age |  | Spirometric lung age | Respiratory |
| -4jXesok10 | Q1591167 | household income | combined income of all people sharing a particular household or place of residence |  | Socioeconomic |
| lWecvBdria | Q7607892 | stenosis of pulmonary artery | condition where the pulmonary artery is subject to an abnormal constriction | pulmonary artery stenosis | Respiratory |
| pVE8EAcirR | Q66966038 | death-associated protein kinases | family of calcium/calmodulin-dependent protein-serine-threonine kinases | Death-Associated Protein Kinase; DAPK | Mortality |
| pmucud6ywV | Q18557042 | silent myocardial infarction | history of myocardial infarction in the absence of clinical symptoms and positive electroc | silent myocardial infarction (disorder) | Cardiovascular |
| WE4mXpefTa | Q9358981 | Neuropsychiatric systemic lupus erythematosus | medical condition | NPSLE | Mental health |
| -8dpOP3337 | Q4 | death | permanent cessation of vital functions | bereft of life; perish; oblivion; mortis; fallen; meeting th | Mortality |
| tYohIc_Gh8 | Q1552748 | pulmonary valve | semilunar valve of the heart | pulmonic valve | Respiratory |
| Iw1SGsG5Zn | Q41710 | ethnic group | socially defined category of people who identify with each other | people group; ethnic groups; ethnicity; etnické menšiny | Socioeconomic |
| dJepC0Zpgx | Q65335221 | hospital mortality | statistic measuring the rate of death in hospitalized populations | in-hospital mortalities; in-hospital mortality; in hospital  | Mortality |
| Bi924X5EXL | Q1815679 | pulmonary surgical procedure | surgery performed on the lung | Pulmonary Surgical Procedures; lung surgery; pulmonary surge | Respiratory |
| IgezF5gI_t | Q69886737 | psychiatric social work | use of all social work processes in the treatment of patients in a psychiatric or mental h |  | Mental health |
| Rz_E9HDxKM | Q55782242 | pulmonary atresia-intact ventricular septum syndrome |  | Pulmonary Valve Atresia with Intact Ventricular Septum; PULM | Respiratory |
| 9J7QjcbE7R | Q220570 | pulmonary embolism | blockage of the main artery of the lung or one of its branches by a substance that has tra | PE; pulmonary artery embolism; pulmonary embolus; pulmonary  | Respiratory |
| 2x3DVD3ReU | Q544006 | anxiety disorder | cognitive disorder with an excessive, irrational dread of everyday situations | anxiety state; anxiety neurosis; chronic anxiety; anxiety | Mental health |
| _4cNTaUYo4 | Q5692507 | Heart valve dysplasia | human disease | Congenital valvular dysplasia; Valvular Heart Disease, Conge | Cardiovascular |
| OjuGOEwQlZ | Q13538850 | lung infarction | lung disease caused by blocked artery | pulmonary infarction | Respiratory |
| CmF75oLdRI | Q3915542 | income distribution | manner in which a nation’s total GDP is distributed amongst its population |  | Socioeconomic |
| 83j6lNfQdA | Q5757641 | high output cardiac failure | medical condition |  | Cardiovascular |
| rqFj5Lvvwf | Q79995 | ozone layer | region of Earth's stratosphere that absorbs most of the Sun's UV radiation | stratospheric ozone; ozone shield; atmospheric ozone; atmosp | Air pollution |
| ziiDZrVnIJ | Q6803767 | gross national income | total domestic and foreign output claimed by residents of a country, consisting of gross d | GNI | Socioeconomic |
| 4eVmUr4Jx8 | Q564872 | hyperthermia therapy | treatment | induced hyperthermia; hyperthermia, induced | Heat & temperature |
| F_gCEqfZw_ | Q18554511 | cardiac sarcoidosis | Human disease | Cardiac sarcoidosis (disorder); Cardiac sarcoidosis | Cardiovascular |
| G3U0OkLXdv | Q24782817 | Heat shock transcription factor family | InterPro Family | HSF_fam; IPR027725; Heat shock factor; Heat Shock Transcript | Heat & temperature |
| Jv1m4iUFCb | Q2300749 | separation anxiety disorder | anxiety disorder that involves the feeling of excessive and inappropriate levels of anxiet | separation anxiety disorder of childhood | Mental health |
| dM352-wmkm | Q54913235 | attitude to death | conceptual response of the person to the various aspects of death, which are based on indi |  | Mortality |
| MZfaQzUTD5 | Q935129 | postpartum depression | endogenous depression that involves intense, sustained and sometimes disabling depression  | postnatal depression; Depressive Episode with Postpartum Ons | Mental health |
| YU8yZKAzM2 | Q430439 | cooling down | gradual decrease in physical exercise | warming down | Housing & energy |
| WvytewJeR9 | Q941796 | psychological repression | keeping out from consciousness ideas or impulses that are unacceptable to it | Repression, Psychology; control (prevention) | Mental health |
| TTLFCwX7uc | Q30104011 | cardiac septum |  | heart septum; septum; septum of heart | Cardiovascular |
| cokig6QZot | Q5433336 | Family income |  |  | Socioeconomic |
| mUxSLRMwIy | Q1160424 | air temperature |  |  | Heat & temperature |
| NEkjsJKcyj | Q70452962 | Community Mental Health Centers | Facilities which administer the delivery of psychologic and psychiatric services to people |  | Mental health |
| hoeugLl5wt | Q5938041 | right lung | anatomical structure |  | Respiratory |
| xcFHC5l065 | Q281928 | social anxiety disorder | anxiety disorder associated with social situations | sociophobia; SAD; social phobia | Mental health |
| fo-h4u_aJp | Q41861 | arterial hypertension | long term medical condition with elevated arterial blood pressure | high blood pressure; "the silent killer"; hypertension | Cardiovascular |
| fEPvZSrVRx | Q202837 | cardiac arrest | sudden stop in effective blood flow due to the failure of the heart to contract effectivel | circulatory arrest; sudden cardiac arrest; SCA; heart arrest | Cardiovascular |
| 3yWiToqGbW | Q72259833 | Isolated Heart Preparation |  |  | Cardiovascular |
| WdTYQ8MJsC | Q1519482 | gestational hypertension | Human disease | hypertension induced by pregnancy; pregnancy associated hype | Cardiovascular |
| mK0OlyUf3v | Q70437502 | Cardiac Care Facilities | Institutions specializing in the care of patients with heart disorders. |  | Cardiovascular |
| OYMdBV8G8r | Q190805 | heart disease | cardiovascular system disease that involves the heart | cardiac disease; disorder of heart; disease of heart; heart  | Cardiovascular |
| CCVZABeZcW | Q2025 | carbon monoxide | chemical compound | carbon(II) oxide; Carboneum oxygenisatum; CO; C#O; [CO]; car | Air pollution |
| FIfiMDrVR9 | Q7663896 | systolic hypertension | elevated systolic blood pressure | isolated systolic hypertension | Cardiovascular |
| PQ1nPOBjAX | Q12713657 | childhood asthma | human disease | childhood-onset asthma | Respiratory |
| WniYIQZnLw | Q3047550 | heat shock protein family D (Hsp60) member 1 | mammalian protein found in Homo sapiens | HSPD1; epididymis secretory sperm binding protein; 60 kDa he | Heat & temperature |
| 7smS8RtmND | Q69901820 | psychological techniques | methods used in the diagnosis and treatment of behavioral, personality, and mental disorde | psychological technique | Mental health |
| fbIHMd608Z | Q112206836 | psychological rejection | negative attitudes and hostility to, or excessive criticism of, an individual, which may p | rejection; Rejection, Psychology | Mental health |
| knUjuUuOxs | Q50429809 | radioactive air pollutants | pollutants present in air which exhibit radioactivity | radioactive air pollutant; Air Pollutants, Radioactive | Air pollution |
| N1d0hc5tBO | Q3247762 | Heart-lung transplant | procedure carried out to replace both heart and lungs in a single operation | Heart–lung transplant; Heart-Lung Transplantation | Cardiovascular; Respiratory |
| ELq9F8lpsq | Q78128805 | pulmonary surfactant-associated proteins | proteins found in the lung that act as pulmonary surfactants | pulmonary surfactant-associated protein | Respiratory |
| QPPiX84yv2 | Q932068 | environmental health | public health branch focused on environmental impacts on human health |  | Mental health |
| gDTwyv0tZM | Q2990558 | pulmonary compliance | ratio of volume change per pressure change in the lung | lung compliance | Respiratory |
| QSeDi--mvS | Q154278 | ethnic cleansing | systematic removal of a certain ethnic or religious group | ethnic cleaning | Socioeconomic |
| sSuplgYnDQ | Q56297886 | surface temperature | temperature at the surface of a body |  | Heat & temperature |
| hXgThWd9lb | Q55950055 | unipolar depression |  | Major Depression | Mental health |
| BC6mefIVa1 | Q579527 | pulmonary valve stenosis | Human disease | pulmonary stenosis; PS | Respiratory |
| cafO_yovFO | Q7933601 | mood swing | extreme or rapid change in mood | labile affect; affective lability; emotional lability | Mental health |
| IPV_lvgw9H | Q199804 | chronic obstructive pulmonary disease | lung disease involving long-term poor airflow | COPD; chronic obstructive airway disease; chronic obstructiv | Respiratory |
| 2f3jUDqZsL | Q1824165 | poverty reduction | measures to reduce poverty permanently | poverty alleviation; anti-poverty | Socioeconomic |
| eGt7qdAFDP | Q5038315 | cardiac amyloidosis | medical condition |  | Cardiovascular |
| mz0c3N8FeI | Q54943748 | pulmonary adenomatosis | neoplastic disease in which the alveoli and distal bronchi are filled with mucus and mucus |  | Respiratory |
| 3PHxptOwMv | Q3010837 | univentricular heart |  | Double inlet left ventricle; Common ventricle | Cardiovascular |
| KuT2LixjdD | Q26695943 | heart valve prolapse | Human disease |  | Cardiovascular |
| BXIqDiSa-n | Q18557038 | inferior myocardial infarction | Human disease | Inferior myocardial infarction NOS (disorder); Inferior myoc | Cardiovascular |
| HMN_gkSxYn | Q1130519 | heart valve disease | disease in the valves of the heart | valvular heart disorder; Valvular heart disease (disorder);  | Cardiovascular |
| Q9nwZ-nXm6 | Q1621258 | heat shock response | effect of subjecting a cell to a higher-than-optimal temperature; causes protein misfoldin | heat shock | Heat & temperature |
| 1RAPJwgLFu | Q987319 | secondary hypertension | human disease |  | Cardiovascular |
| Zh2ZTvkggH | Q873512 | psychological test | instrument designed to measure unobserved psychological constructs, also known as latent v | psychological testing; psychological scale; psychological te | Mental health |
| ultUK90419 | Q19000544 | lung small cell carcinoma | lung carcinoma that has material basis in primitive-appearing cells that are smaller than  | Oat cell carcinoma of lung (disorder); SCLC; small cell carc | Respiratory |
| nJeruaUXsN | Q21159807 | programmed cell death 1 ligand 2 | mammalian protein found in Homo sapiens | Programmed Cell Death 1 Ligand 2 Protein; B7 dendritic cell  | Mortality |
| jsQHrk3xJU | Q5038717 | cardiopulmonary rehabilitation | medical service | cardiac rehabilitation | Respiratory |
| 2J9lOXqvCS | Q2322778 | maternal deprivation | separating infants and young children from their mother | Maternal Deprivation Syndrome | Socioeconomic |
| twoiOvOZWn | Q71149323 | trigeminocardiac reflex | sudden occurrence of bradycardia or heart arrest induced by manipulations of the maxilliar | Reflex, Trigeminocardiac | Cardiovascular |
| pb-BFW1S6B | Q179222 | income tax | tax imposed on individuals or entities (taxpayers) that varies with respective income or p | income taxation; tax on income; profit tax; profit taxation | Socioeconomic |
| wU2tGNIo7u | Q5193342 | cultural deprivation |  |  | Socioeconomic |
| h1GWBVtnho | Q70453880 | Ambulance Diversion | The practice of redirecting ambulances and patients seeking urgent care from one emergency |  | Emergency care |
| 7rycwPDEmY | Q1641132 | malignant hypertension | condition of markedly elevated blood pressure with diastolic pressure typically greater th | hypertensive emergency; Hypertension, Malignant; hypertensiv | Cardiovascular |
| XW9F7OPopQ | Q12202 | stroke | death of a region of brain cells due to poor blood flow | CVA; CVI; brain attack; embolic stroke; cerebrovascular insu | Cardiovascular |
| 4YNqro40k9 | Q1478382 | heat flux density | heat transferred per area and time | thermal flux; areic heat flow rate; heat flux; density of he | Heat & temperature |
| RQtcKJybsg | Q102294453 | T2-high asthma | human disease | Th2-high | Respiratory |
| L11zkdEfRz | Q27910228 | thunderstorm asthma | human disease | thunderstorm triggered asthma | Respiratory |
| tbIjUlliUl | Q55781946 | growth delay-hydrocephaly-lung hypoplasia syndrome | medical condition | Game-Friedman-Paradice syndrome; HYDROCEPHALUS WITH ASSOCIAT | Respiratory |
| LQWjUNDY2O | Q8068 | flood | overflow of water that submerges land | flooding; floodwater | Flooding & storms |
| oJFe31eltz | Q50429808 | occupational air pollutants | toxic air-borne matter related to work performed | Air Pollutants, Occupational; occupational air pollutant | Air pollution |
| JsvFDygJCK | Q11067835 | pulmonary diffusing capacity |  | diffuxion capacity; diffusing capacity | Respiratory |
| ZByJ1i53Z6 | Q562166 | housing cooperative | Cooperative with the aim of providing its members with affordable housing | housing co-op; housing company; housing co-operative | Housing & energy |
| in4DQnGBv4 | Q2135807 | mental health recovery | approach to mental disorder or substance dependence that emphasizes and supports a person' | recovery; recovery approach; recovery-oriented practice | Mental health |
| lykXRijiaS | Q7632057 | Substance Abuse and Mental Health Services Administration | branch of the U.S. Department of Health and Human Services | Alcohol, Drug Abuse, and Mental Health Administration; SAMHS | Mental health |
| 4RFwIVS5q1 | Q116847675 | idiopathic noncirrhotic portal hypertension | portal hypertension in the absence of known risk factors | idiopathic non-cirrhotic portal hypertension | Cardiovascular |
| ET5-8-2eBO | Q125367 | carbon monoxide poisoning | toxicity due to exposure to carbon monoxide | CO poisoning; carbon monoxide toxicity; CO toxicity; carbon  | Air pollution |
| aEqv5SNtHJ | Q7920251 | ventilator-associated lung injury | type of acute lung injury | VALI; VILI; ventilator-induced lung injuries; Ventilator-Ind | Respiratory |
| YX0LjLG-s3 | Q24788167 | BH3-interacting domain death agonist | InterPro Family | BID; IPR010479 | Mortality |
| DC_F0GO0WQ | Q207895 | nitrogen dioxide | chemical compound | nitrogen peroxide; NO2; NO2(.); Nitrogen(IV) oxide; Deutoxid | Air pollution |
| 5Iq1BlvTdk | Q185325 | cardiopulmonary resuscitation | emergency procedure to maintain the blood flow to vital organs and to restore normal heart | CPR; Cardiopulmonary Resuscitation(CPR) | Respiratory |
| VUbS0APNXf | Q67006304 | racial group | group of individuals with similar physical appearances often reinforced by cultural, socia | Continental Population Groups; continental population group; | Socioeconomic |
| _Oa_0jWALE | Q317309 | mental health | level of psychological well-being |  | Mental health |
| oEWjV89s3H | Q106892235 | all-cause mortality | measure of all deaths, due to any cause, that occur during a clinical study | all cause mortality; total deaths; all deaths | Mortality |
| GQTvp_-LeQ | Q6973027 | National Heart, Lung, and Blood Institute | research institute part of U.S. National Institutes of Health (NIH) | NHLBI; National Heart, Lung, and Blood Institute (NHLBI); Na | Cardiovascular; Respiratory |
| OKbNDucuod | Q10385444 | heart neoplasm | tumor in any part of the heart, including primary cardiac tumors and also metastatic tumor | heart neoplasms; cardiac neoplasm; heart tumor; cardiac tumo | Cardiovascular |
| SNwibY-1QP | Q5038319 | cardiac imaging | visualization of the heart structure and cardiac blood flow for diagnostic evaluation or t | cardiac imaging techniques; Cardiac Imaging Technique | Cardiovascular |
| Jy2y-3RDdo | Q206120 | lung volumes | volume of air in the lungs | Lung Volume | Respiratory |
| e4llLU0K_2 | Q27891863 | resting heart rate |  |  | Cardiovascular |
| VDAUIzDRMc | Q114733078 | heart disease risk factors | aspects of lifestyle, environmental exposure, inherited conditions and characteristics ass | heart disease risk factor | Cardiovascular |
| wjKl7wOot3 | Q304484 | programmed cell death | biological process | GO:0012501; Regulated Cell Death; PCD | Mortality |
| JMeOsYIcbL | Q36933 | ozone | chemical compound | O3; [OO2]; O₃; triatomic oxygen | Air pollution |
| gEtZRFhT8z | Q4677935 | acute lung injury | condition of lung damage characterized by bilateral pulmonary infiltrates |  | Respiratory |
| Y6hqrNvoIF | Q56218018 | heart failure with reduced ejection fraction | human disease | HFrEF | Cardiovascular |
| 5VMSop2WcI | Q3500368 | psychological stress | psychological feeling of strain and pressure, that could increase the risk of strokes, hea | stress; Stress, Psychological; mental stress | Mental health |
| My4uMAzwEz | Q73483131 | one-lung ventilation | techniques for supplying artificial respiration to a single lung | single-lung ventilation | Respiratory |
| cw7BusOVlA | Q7690049 | Taylor Manifest Anxiety Scale |  |  | Mental health |
| W77fjbFKqg | Q104149893 | pulmonary function |  | respiratory function | Respiratory |
| uePwKmF8hs | Q12301086 | allergic asthma | asthma with a basis in a pathological type I hypersensitivity reaction | Extrinsic asthma with status asthmaticus (disorder); extrins | Respiratory |
| U_UfgkEZzZ | Q7259548 | pulmonary stretch receptor | cell type | pulmonary stretch receptors | Respiratory |
| PtQBvGm5CM | Q1191065 | heat illness | condition caused by the failure of the human body to dissipate heat in a hot environment | Heat Stress Disorder; Heat Stress Disorders | Heat & temperature |
| CPAIkhzpxO | Q7316336 | restrictive lung disease | medical condition | chronic restrictive respiratory failure | Respiratory |
| nS9fqJ01TW | Q1295316 | emergency department | medical treatment facility specializing in emergency medicine | accident & emergency; A&E; emergency room; ER; casualty depa | Emergency care |
| dKHKllsa1c | Q3302130 | Cardiac electrophysiology | science of elucidating, diagnosing, and treating the electrical activities of the heart |  | Cardiovascular |
| JxB_DrfKvK | Q154430 | anxiety | unpleasant complex combination of emotions that includes fear, apprehension and worry, and | uneasiness and stomach spinning; anxiety, uneasiness and wor | Mental health |
| ykiJVOKBa2 | Q757749 | atrial heart septal defect | A heart septal defect located in in the septum that separates the two atria of the heart. | atrioseptal defect; auricular septal defect; congenital atri | Cardiovascular |
| G-cA8ng8z2 | Q939364 | congenital heart disease | cardiovascular disease | CHD; congenital heart anomaly; Congenital Heart Defects; Con | Cardiovascular |
| abLtMsltWy | Q1361515 | heart conduction disease | cardiovascular system disease that involves the heart's electrical conduction system | cardiac conduction defect; heart rhythm disease; heart block | Cardiovascular |
| MyfOCvVzi7 | Q18554512 | pulmonary sarcoidosis | human disease | lung sarcoidosis | Respiratory |
| 3d9Awcw5vp | Q17105385 | psychological first aid | humane, supportive and practical help to fellow human beings suffering serious crisis even | PFA | Mental health |
| f2NLNm3eaE | Q7836891 | treatment-resistant depression | medical condition | treatment-refractory depression; TRD | Mental health |
| 8vWoXO9cFn | Q11829287 | chronic heart failure | persistent or long-lasting inability of the heart to provide sufficient pump action |  | Cardiovascular |
| 4FaXcuNJRt | Q11466 | temperature | physical property of matter that quantitatively expresses the common notions of hot and co | temp | Heat & temperature |
| 1jX8o65OKT | Q419102 | HSP70 heat-shock proteins | protein | Hsp70 | Heat & temperature |
| PV9PuPYkcO | Q47248915 | low cardiac output | state of subnormal or depressed cardiac output at rest or during stress | Cardiac Output, Low | Cardiovascular |
| TjPomHvTJ6 | Q57601280 | Targeted lung denervation |  |  | Respiratory |
| rM-gzDwfAj | Q1569573 | hepatopulmonary syndrome | Human disease | Hepatopulmonary syndrome (disorder); Hepatopulmonary syndrom | Respiratory |
| eexKsPJ1K1 | Q54973951 | sudden death | abrupt cessation of all vital bodily functions, manifested by the permanent loss of total  | D003645; Death, Sudden | Mortality |
| dr7JnamvKS | Q898280 | Nusselt number for heat transfer | characteristic number for heat transfer into a body | Nusselt number | Heat & temperature |
| BP5Hd84_NV | Q857667 | pulmonary edema | fluid accumulation in the air spaces and parenchyma of the lungs | pulmonary oedema; edema pulmonary; plicní edém | Respiratory |
| KB-3f3KXkf | Q17326470 | systolic heart failure | heart failure caused by abnormal myocardial contraction during systole | Heart Failure, Systolic | Cardiovascular |
| xqYAUO9yGl | Q102295163 | nocturnal asthma | human disease | Asthma night-time symptoms | Respiratory |
| 31gLuixqrR | Q112159693 | housing instability | hypernym for challenges in obtaining housing which is affordable by one's means |  | Housing & energy |
| qPj8S0DRc6 | Q708653 | death certificate | vital record that documents a death |  | Mortality |
| u_5_FBoksD | Q929313 | cardiac tamponade | Compression of the heart due to excessive accumulation of fluid in the pericardium (sac in | Rose's tamponade; pericardial tamponade | Cardiovascular |
| tJxGxX0KdN | Q70490040 | Insurance, Psychiatric | Insurance providing benefits to cover part or all of the psychiatric care. |  | Mental health |
| OnRtQgvIkg | Q173725 | air conditioning | cooling of air in buildings or vehicles | A/C; AC | Housing & energy |
| 9HhhdZzQYb | Q2039267 | aspirin-exacerbated respiratory disease | human disease | Asthma and Nasal Polyps; Asa Triad; ASTHMA, NASAL POLYPS, AN | Respiratory |
| ZRIVDRXDSI | Q1877474 | solitary pulmonary nodule | human disease | pulmonary coin lesion; Coin lesion lung; Coin lesion of lung | Respiratory |
| apZlYGRyxB | Q55780854 | heart-hand syndrome type 3 | medical condition | HEART-HAND SYNDROME, SPANISH TYPE; Atriodigital dysplasia ty | Cardiovascular |
| nKrKKOZKmL | Q7232210 | Portopulmonary hypertension | medical condition | POPH; PAH associated with portal hypertension | Cardiovascular; Respiratory |
| YnnxhtioLE | Q1967405 | National Institute of Mental Health | mental health research organization in the United States | NIMH | Mental health |
| TnqBv9XPzT | Q25381037 | maternal mortality ratio | number of maternal deaths in a given period per 100,000 live births (Maternal deaths/live  | MMRatio; maternal mortality | Mortality |
| PNZ6HkA4qT | Q25257 | precipitation | product of the condensation of atmospheric water vapour that falls under gravity | rain; rainfall | Flooding & storms |
| tKBti329On | Q831866 | operating income | Profit after deducting operating expenses such as wages, depreciation, and cost of goods s |  | Socioeconomic |
| rfc0Y-3LH6 | Q1430844 | allergic bronchopulmonary aspergillosis | aspergillosis that involves an allergic reaction due to the spores of Aspergillus moulds ( | pulmonary aspergillus disease; ABPA; Allergic aspergillosis; | Respiratory |
| Tzg0TxXii_ | Q22004151 | infant death | death of a child up to one year of age |  | Mortality |
| lw7_RArWhd | Q61559 | child mortality | death rate of infants and young children | child death; death of children | Mortality |
| VIfG9sCmU5 | Q618068 | Cardiac index | haemodynamic parameter that relates the cardiac output (CO) from left ventricle in one min |  | Cardiovascular |
| TM1YPafvM8 | Q55082277 | non-ST elevated myocardial infarction | myocardial infarction that does not produce elevations in the ST segments of the electroca | non-ST elevated myocardial infarctions; NSTEMI | Cardiovascular |
| syGuQJ_lry | Q69901598 | psychological feedback | route for information stimulus and response to change behavior | Feedback, Psychological | Mental health |
| FKyOHs5LVl | Q901305 | immunoprecipitation | separating components in solution by relying on antibodies to specifically bind to them |  | Flooding & storms |
| w5h_sS4gaT | Q111695166 | asthma-chronic obstructive pulmonary disease overlap syndrome | syndrome combining clinical features of  asthma and COPD | Asthma-COPD overlap; s Asthma-COPD Overlap Syndrome; Asthma- | Respiratory |
| BMe8wCbP-q | Q3428020 | cardiac resynchronization therapy | treatment for heart failure | implanted cardiac resynchronization device | Cardiovascular |
| zOGoYOSARE | Q52775754 | pulmonary arteriovenous malformations |  | PAVM; pulmonary arteriovenous fistula; pulmonary arterioveno | Respiratory |
| 0-H2z7XS3q | Q18345704 | pulmonary venoocclusive disease | Human disease | pulmonary veno-occlusive disease (disorder); pulmonary veno- | Respiratory |
| lDyLc9906y | Q845224 | generalized anxiety disorder | anxiety disorder that is characterized by long-lasting anxiety that is not focused on any  | GAD; Generalized anxiety disorder | Mental health |
| EsbQIzj8CX | Q4421 | forest | dense collection of trees covering a relatively large area | wood; woods; Forest; forests | Green space |
| FDJ4Gulj_Q | Q242165 | hyperthermia | elevated body temperature due to failed thermoregulation that occurs when a body produces  | overheating; heat stroke | Heat & temperature |
| _E2zHRt4HC | Q18553765 | hyperlucent lung | human disease | Lung, Hyperlucent | Respiratory |
| r2qagpRYm_ | Q7630973 | subcortical ischemic depression | late-life depression associated with cerebrovascular pathology | Vascular Depression | Mental health |
| fPTyqN9tuH | Q6532502 | public housing | residential properties usually owned by a government | council housing; social housing | Housing & energy |
| ap2VpwVg_- | Q3818443 | neuropsychological tests | tests to assess neurological function associated with certain behaviors | neuropsychological test | Mental health |
| EwQdct195Z | Q24772687 | heat shock protein Hsp90 family | InterPro Family | Hsp90_fam; IPR001404; Hsp90; HSP90 Heat-Shock Proteins; HSP9 | Heat & temperature |
| PCdVJWVRyS | Q264647 | thermodynamic temperature | absolute measure of temperature | absolute temperature; temperature | Heat & temperature |
| IpoZaH6HNR | Q113167716 | cardiac procedure anesthesia | anesthetic methods used during cardiac procedures | Anesthesia, Cardiac Procedures | Cardiovascular |
| Y4m9pusjjE | Q113796 | precipitation | chemical process leading to the settling of an insoluble solid from a solution | precipitating out; chemical precipitation; precipitation fro | Flooding & storms |
| gQXUoRhSjv | Q688890 | pulmonary sequestration | congenital disorder of respiratory system | congenital pulmonary sequestration; Congenital bronchopulmon | Respiratory |
| _qTp1OBVrb | Q1339474 | maternal death | death of a woman while pregnant or within 42 days of termination of pregnancy | maternal mortality | Mortality |
| 78CNd21Jd_ | Q3965303 | ST depression | finding on an electrocardiogram | ST segment depression | Mental health |
| Ah-wdkRcqy | Q11880006 | heating equipment | heating of air in buildings or vehicles | residential heating; heating (spaces); heating devices; air  | Housing & energy |
| pyj_U2xVsG | Q59679511 | low income | home with little money | low-income households; low-income household | Socioeconomic |
| vttnB9iRRH | Q70450233 | hospital psychiatric department | hospital department responsible for the organization and administration of psychiatric ser | Psychiatric Department, Hospital | Mental health |
| q5R2NvXXcK | Q54946623 | invasive pulmonary aspergillosis | lung infection with the invasive forms of Aspergillus, usually after surgery, transplantat |  | Respiratory |
| XIpFCEhBwG | Q113585438 | heart surgery | surgical operation of the heart | cardiac surgical procedures | Cardiovascular |
| EfULeaOIui | Q29513568 | heart-lung machine |  | heart–lung machine; CPB pump; the pump; cardiopulmonary bypa | Cardiovascular; Respiratory |
| HepboJi0-Y | Q9294051 | ocular hypertension | eye disease that is characterized by elevated intraocular pressure in the absence of optic | ocular hypertension (disorder) | Cardiovascular |
| H0DY9O3AHZ | Q156589 | Anacardiaceae | family of plants |  | Cardiovascular |
| _nQPetA-rl | Q645285 | National Institute of Neurological Disorders and Stroke | government agency | NINDS; U.S. National Institute of Neurological Disorders and | Cardiovascular |
| lHLIKbfnYp | Q22652 | green space | green area planned in an urban location | green area; open space reserve; open space preserve; open sp | Green space |
| epn8cUn0y3 | Q13046587 | pulmonary tuberculosis | human disease | Pulmonary TB; Lung TB; Lung Tuberculosis | Respiratory |
| ro6wY6EYLy | Q1472604 | transfusion related acute lung injury | medical condition | Transfusion-Related Acute Lung Injury | Respiratory |
| 6DTj2ennMm | Q22698 | park | permanently dedicated recreation area, often open to the public and generally characterize | park (public recreation area); garden & park; Parks, Recreat | Green space |
| Y7IAPqMIE9 | Q1137122 | tree ring | seasonal growth pattern | annual ring; growth ring; tree year ring; tree rings | Green space |
| 7rdlOXdmpC | Q18558125 | intracranial hypertension | Human disease | elevated intracranial pressure; raised intracranial pressure | Cardiovascular |
| w1T9FSwcVw | Q55227147 | post-infarction cardiac rupture | Laceration or tearing of cardiac tissues appearing after MYOCARDIAL INFARCTION. |  | Cardiovascular |
| f89miYjYGH | Q72138619 | cardiac resynchronization therapy device | artificial pacemakers with implantable leads to be placed at multiple intracardial sites | Cardiac Resynchronization Therapy Devices | Cardiovascular |
| JmZ-RoSC5o | Q3286546 | respiratory disease | disease of the respiratory system | disease of the respiratory system; disease of respiratory sy | Respiratory |
| wxgpgmEUux | Q1396859 | farmer's lung | hypersensitivity pneumonitis | Farmers lung; farmer lung | Respiratory |
| R4Zyw4LAKo | Q3141769 | Heat shock protein family B (small) member 1 | mammalian protein found in Homo sapiens | estrogen-regulated 24 kDa protein; epididymis secretory prot | Heat & temperature |
| PHTCUuEVDj | Q67216606 | anterior wall myocardial infarction | myocardial infarction in which the anterior wall of the heart is involved, subclassified a |  | Cardiovascular |
| PfzPevl_MY | Q4340209 | mental depression | state of low mood and aversion to activity, which can affect a person's thoughts, behavior | depression | Mental health |
| syPepb7sQ8 | Q60195177 | post-cardiac arrest syndrome | syndrome that is characterized by four main components: post-cardiac arrest brain injury,  | post cardiac syndrome | Cardiovascular |
| 567CGPkQXm | Q67173088 | skin temperature | the temperature at the outer surface of a living body. |  | Heat & temperature |
| 4hRwwi4C7b | Q72711 | electrical conduction system of the heart | transmits signals generated usually by the sinoatrial node to cause contraction of the hea | heart conduction system; electrical cardiac conduction syste | Cardiovascular |
| alMLXtyJaf | Q70441704 | Air Pollution, Radioactive | Contamination of air with radioactive substances. |  | Air pollution |
| Fll-ue_UyP | Q5693336 | Heat storage | Wikimedia disambiguation page |  | Heat & temperature |
| 6yoKTYSOJa | Q1527264 | income | consumption and savings opportunity gained by an entity within a specified timeframe | merit; earning; earn | Socioeconomic |
| _n3mMwVqog | Q6137239 | hantavirus pulmonary syndrome | human disease | HPS; Four Corners disease | Respiratory |
| gmP-jwpHYP | Q67076049 | mental health services | organized services to provide mental health care | mental health service | Mental health |
| 7ohbQCGNQt | Q25458308 | intra-abdominal hypertension |  |  | Cardiovascular |
| xh-q4BGKbZ | Q3508797 | obstructive lung disease | category of respiratory disease characterized by airway obstruction | respiratory airway obstruction | Respiratory |
| 0CLfeyd20U | Q67490468 | cardiac catheters | catheters inserted into the heart for diagnostic or therapeutic purposes | Cardiac Catheter | Cardiovascular |
| tr_shB_KL5 | Q422238 | cardiac glycoside | class of organic compounds that increase the output force of the heart and decrease its ra | cardiac glycosides | Cardiovascular |
| Og8UzVX-lo | Q5272105 | diastolic heart failure | heart failure caused by abnormal myocardial relaxation during diastole | Heart Failure, Diastolic | Cardiovascular |
| m1hv4homj_ | Q102296744 | near-fatal asthma | human disease |  | Respiratory |
| AroGuaoIfh | Q116847656 | sinistral portal hypertension | portal hypertension of the splenic vein, arising from occlusion caused by pancreatic patho | Left-Sided Portal Hypertension | Cardiovascular |
| 9YqpsXAD_S | Q114754301 | hemorrhagic stroke | stroke caused by the rupture of a weakened blood vessel in the brain | haemorrhagic stroke | Cardiovascular |
| z0FmiQio14 | Q1877462 | pulmonary function test | test to evaluate respiratory system | respiratory function test; respiratory function tests; pulmo | Respiratory |
| 5TzPpdv1he | Q13566222 | acute pulmonary edema |  |  | Respiratory |
| OnEwP8hPI3 | Q69904353 | Test Anxiety Scale | A self-reporting test consisting of items concerning fear and worry about taking tests and |  | Mental health |
| aw2bznU6MK | Q3658498 | rheumatic heart disease | acute inflammatory disease following an episode of Group A streptococcus pharyngitis | rheumatic carditis; RHD; Rheumatic Heart Disease; Bouillaud  | Cardiovascular |
| Cv_Ldh0HRR | Q5282 | sulfur dioxide | chemical compound | sulfurous acid anhydride; sulfurous oxide; sulfur oxide; Sul | Air pollution |
| 7dRlP44-ka | Q1364801 | sleep deprivation | condition of not having enough sleep | sleep-deprived; sleep insufficiency; sleeplessness; sleep de | Socioeconomic |
| YTKMzT1S-y | Q1641399 | hypoplastic left heart syndrome | congenital heart disease characterized by abnormal development of the left-sided structure | HLHS; Hypoplastic left heart syndrome | Cardiovascular |
| KuOsQy6Xym | Q95566669 | hypertension | elevated pressure in a specific organ of the body (arteries, lungs, head, eyes etc.) | high pressure | Cardiovascular |
| jt0p0t_A6y | Q12152 | myocardial infarction | interruption of blood supply to a part of the heart | MI; infarctus myocardii acutus; heart attack; myocardial inf | Cardiovascular |
| EsIcXQ6TCA | Q24781052 | Small heat shock protein HSP20 | protein family | HSP20; Hsp20 | Heat & temperature |
| jjeK7yyqXi | Q596579 | cardiac output | term used in cardiac physiology that describes the volume of blood being pumped by the hea | CO | Cardiovascular |
| njrXVqHWfX | Q1432397 | Kyasanur forest disease | Human disease | Kyasanur hemorrhagic fever; Monkey disease; KFD virus; Monke | Green space |
| ACCOnRBMxQ | Q24774237 | Alpha crystallin/Heat shock protein | InterPro Family | Alpha-crystallin/HSP; IPR001436; alpha-Crystallins | Heat & temperature |
| AtFfNSdizU | Q70328677 | Fetal Mortality | Number of fetal deaths with stated or presumed gestation of 20 weeks or more in a given po |  | Mortality |
| hSA-abvVAa | Q70575720 | cardiac volume | The volume of the heart, usually relating to the volume of blood contained within it at va |  | Cardiovascular |
| U2cFISqVmX | Q4105337 | psychological resilience | ability to cope with a life crisis, adapt in the face of stressors, or to adjust and retur | Resilience, Psychological; Resilience | Mental health |
| qDs5V47pxx | Q50429907 | cardiovascular agent | agent that affects the rate or intensity of cardiac contraction, blood vessel diameter, or | Cardiovascular Drugs; Cardiovascular Agents | Cardiovascular |
| 6bPmhgBHGB | Q3799243 | pulmonary valve insufficiency | disease that occurs when the pulmonary valve is not strong enough to prevent backflow into | Pulmonic insufficiency NOS; Pulmonic valve regurgitation (di | Respiratory |
| IZqp5zUQ3t | Q2090736 | pulmonary atresia | medical condition | PA; pulmonary valve atresia | Respiratory |
| WM2NlntzMA | Q73509394 | Fractional Precipitation |  |  | Flooding & storms |
| VS9viGMXLt | Q1726969 | oculocardiac reflex |  | Aschner reflex | Cardiovascular |
| iFBZoLASEM | Q7233752 | Post stroke depression |  |  | Cardiovascular; Mental health |
| P8Fii9rN3r | Q70469054 | Insurance, Hospitalization | Health insurance providing benefits to cover or partly cover hospital expenses. |  | Emergency care |
| GA2Zm4L4tp | Q18554294 | cough variant asthma | asthma that is characterized by chronic nonproductive cough without shortness of breath | Cough variant asthma (disorder) | Respiratory |
| YdX9m4rnXQ | Q2520821 | length of stay | duration of a single episode of hospitalization |  | Emergency care |
| wpUeTjUbAc | Q69044113 | extreme heat | high temperature weather exceeding the average and of several weeks duration | extreme hot weather | Heat & temperature |
| and4kaoM3Y | Q18556110 | lung carcinoma | lung cancer that has material basis in abnormally proliferating cells derives from epithel | carcinoma of lung; cancer of lung; Lung cancer, NOS; cancer  | Respiratory |
| 5q4BvnezYN | Q70188839 | heart mitochondria | mitochondria of the myocardium | Mitochondria, Heart; heart mitochondrion | Cardiovascular |
| 0CHoZ0o6r_ | Q909741 | temperature measurement | recording of temperature | thermometry | Heat & temperature |
| rNvNuxXEdo | Q835884 | infant mortality | statistical concept of infant deaths | infant mortality rate | Mortality |
| kF0-mgZADg | Q70679763 | Pulmonary Gas Exchange | The exchange of OXYGEN and CARBON DIOXIDE between alveolar air and pulmonary capillary blo |  | Respiratory |
| zRxOHnsEfh | Q3233590 | black carbon | atmospheric soot; component of fine particulate matter |  | Air pollution |
| Ce-5CCk5ZC | Q25518718 | rainfall intensity | measure of the amount of rain received in a defined area over a defined period of time | rainfall; rainfall volume; rainfall rate | Flooding & storms |
| QPxlNKv3zV | Q58702 | mortality rate | measure of the number of deaths in a population from a given cause, scaled by population,  | death rate; mortality | Mortality |
| ELRbfMDp0h | Q7104927 | Orthostatic hypertension | medical condition |  | Cardiovascular |
| sneIVep7Lr | Q913667 | pulmonary consolidation | radiologic sign |  | Respiratory |
| 3v77XvoTuC | Q10681911 | stroke habilitation | restoration of functions in a stroke victim | stroke recovery; stroke rehabilitation | Cardiovascular |
| I3L1JA5M07 | Q379607 | advanced cardiac life support | set of clinical interventions for the urgent treatment of cardiac arrest, stroke and other |  | Cardiovascular |
| jv9nUSt27I | Q183140 | ozone depletion | stratospheric phenomena of Earth | ozone destruction; ozone layer depletion; ozone hole; atmosp | Air pollution |
| IFcQ3j86qe | Q1247867 | housing | construction and assignment of houses or buildings for sheltering people | housing stock | Housing & energy |
| dnIEpQCTQ1 | Q2781245 | perinatal death | deaths of infants during late pregnancy or immediately after birth | perinatal mortality | Mortality |
| lHFynWU2q2 | Q5868917 | fetal heart rate | heart rate of fetus | FHR; Heart Rate, Fetal | Cardiovascular |
| zggHHhKfZh | Q448698 | pulmonary alveolar proteinosis | lung disease that is characterized by abnormal accumulation of surfactant occurs within th | PAP; Pulmonary Alveolar Proteinosis; Hereditary pulmonary al | Respiratory |
| GhnY7OHZYS | Q812784 | BCL2 associated agonist of cell death | mammalian protein found in Homo sapiens | BCL2-binding component 6; BCL2-antagonist of cell death prot | Mortality |
| Nnhe00hafS | Q21208025 | programmed cell death 1 | mammalian protein found in Homo sapiens | CD279; programmed cell death 1 protein; programmed cell deat | Mortality |
| P6IzhScRdx | Q131123 | air pollution | presence of dangerous substances in the atmosphere | atmospheric pollution | Air pollution |
| o_U_1mrdZd | Q223867 | brain death | Brain function stopping forever | brain dead | Mortality |
| hXsXEM2vfb | Q70330263 | Mortality, Premature | Deaths that occur before LIFE EXPECTANCY is reached within a given population. |  | Mortality |
| 0GgadM9ouC | Q389735 | cardiovascular disease | class of diseases that involve the heart or blood vessels | CV disease; cardiovascular system disease; myocardiovascular | Cardiovascular |
| UhplVarK4C | Q7259532 | pulmonary hypoplasia | congenital disorder of respiratory system |  | Respiratory |
| s_mlNM8W5q | Q15124212 | lung neoplasm | disease | lung tumor; lung neoplasms | Respiratory |
| FZU8ztWep8 | Q1585081 | malignant hyperthermia | genetic disease that is characterized by a drastic and uncontrolled increase in skeletal m | anesthesia related hyperthermia; malignant hyperpyrexia due  | Heat & temperature |
| AigsL8aMMD | Q18556999 | pulmonary sclerosing hemangioma | human disease | pneumocytoma; Pulmonary sclerosing pneumocytoma; Sclerosing  | Respiratory |
| vRX9EAE1y4 | Q2554857 | cardiac nursing | nursing specialty that works with patients who suffer from cardiovascular problems | cardiovascular nursing | Cardiovascular |
| ww0fWPGNPm | Q65617591 | artificial cardiac pacing | regulation of the rate of contraction of the heart muscles by an artificial pacemaker | Cardiac Pacing, Artificial | Cardiovascular |
| x70YsGSk8B | Q2801621 | psychiatric nursing | specialty applying psychiatric principles in caring for the mentally ill | psychiatric and mental health nursing; mental health nursing | Mental health |
| 3TbthB-Ldy | Q67270196 | heart valve prosthesis implantation | surgical insertion of synthetic material to repair injured or diseased heart valves |  | Cardiovascular |
| WarUgTS86n | Q654426 | psychological trauma | type of damage to the psyche that occurs as a result of a severely distressing event | trauma; psychic trauma; emotional scar; mental injury | Mental health |
| QIyaqCfAg5 | Q535352 | pulmonary vein | veins that transfer oxygenated blood from the lungs to the heart | pulmonary veins | Respiratory |
| jlGhG0W-c3 | Q13634374 | ethnic violence | violence expressly motivated by ethnic hatred and ethnic conflict | racial violence; racially motivated violence; ethnic terrori | Socioeconomic |
| F_sm5RQjJb | Q3055290 | psychological interview |  | Interview, Psychological | Mental health |
| Gl-I4wBZ5r | Q3140971 | hospitalization | admission of a patient to a hospital | hospital admission | Emergency care |
| ADplkYjn2k | Q5158311 | poverty area | area or settlement with severe economic deprivation and accompanying physical and social d | concentrated poverty; poverty areas | Socioeconomic |
| I2CN3brExA | Q10884 | tree | perennial woody plant | arbor; trees; Trees | Green space |
| qKaxsc3-1_ | Q112224721 | ethnic and racial minorities | socially constructed groups of people |  | Socioeconomic |
| SIkf__XHWv | Q116701699 | low socioeconomic status | socioeconomic status with relatively low income or assets and educational level |  | Socioeconomic |
| -ORsqmyw3e | Q643396 | heart transplant | surgical transplant procedure performed on patients with end-stage heart failure or severe | heart transplantation; cardiac transplant | Cardiovascular |
| r7uOms6t9F | Q16070735 | arterial pulmonary hypertension | health problem | pulmonary arterial hypertension; Pulmonary arterial hyperten | Cardiovascular; Respiratory |
| NfqwQkrVlq | Q1599758 | flood disaster | is known as the Heinrichsflut or July flood or Black Friday of Waldeck |  | Flooding & storms |
| A71KVJn6T6 | Q3392853 | lung disease | respiratory disease | non-neoplastic pulmonary disorder; non-neoplastic lung disor | Respiratory |
| BrOMMZDIIY | Q494603 | pulmonary circulation | the portion of the cardiovascular system which carries deoxygenated blood away from the he | Pulmonary circulation | Respiratory |
| dzLsRljdZJ | Q14866108 | necrotic cell death | A type of cell death that is morphologically characterized by an increasingly translucent  | cellular necrosis; GO:0070265 | Mortality |
| KV9if5ypJZ | Q71129977 | pulmonary elimination | The discharge of substances from the pulmonary capillary blood into the alveolar space to  |  | Respiratory |
| nCXMvWJBzn | Q5165683 | heart contraction | The multicellular organismal process in which the heart decreases in volume in a character | heart beating; myocardial contraction; GO:0060047 | Cardiovascular |
| KCSh6cEIRn | Q102293791 | acute asthma | human disease |  | Respiratory |
| eBBePpTiCx | Q18557034 | posterior myocardial infarction | human disease | Posterior myocardial infarction NOS (disorder); Posterior my | Cardiovascular |
| ak7lpHYuXE | Q50429805 | air pollutant | substance in the air which could, if present in high enough concentration, harm humans, an | air pollutants | Air pollution |
| Nw53jOQJ-3 | Q104885559 | indoor air pollution | the contamination of indoor air, which has a negative impact on one's health | IAP; Air Pollution, Indoor | Air pollution |

## NYC rows


### leading-causes-of-death (31)

| nyc_id | label | description | measurementType | years |
|---|---|---|---|---|
| deaths:accidents except drug poisoning | Accidents Except Drug Poisoning | ICD-10: V01-X39, X43, X45-X59, Y85-Y86 | deaths; deathRate; ageAdjustedDeathRate | 2007-2021 |
| deaths:alzheimer's disease | Alzheimer's Disease | ICD-10: G30 | deaths; deathRate; ageAdjustedDeathRate | 2007-2021 |
| deaths:anemias | Anemias | ICD-10: D50-D64 | deaths; deathRate; ageAdjustedDeathRate | 2017-2019 |
| deaths:aortic aneurysm and dissection | Aortic Aneurysm and Dissection | ICD-10: I71 | deaths; deathRate; ageAdjustedDeathRate | 2007-2019 |
| deaths:assault | Assault | ICD-10: Homicide: U01-U02, Y87.1, X85-Y09; Homicide: Y87.1, X85-Y09 (definition  | deaths; deathRate; ageAdjustedDeathRate | 2007-2021 |
| deaths:atherosclerosis | Atherosclerosis | ICD-10: I70 | deaths; deathRate; ageAdjustedDeathRate | 2007-2015 |
| deaths:cerebrovascular disease | Cerebrovascular Disease | ICD-10: Stroke: I60-I69 | deaths; deathRate; ageAdjustedDeathRate | 2007-2021 |
| deaths:certain conditions originating in the perinatal period | Certain Conditions originating in the Perinatal Period | ICD-10: P00-P96 | deaths; deathRate; ageAdjustedDeathRate | 2007-2021 |
| deaths:cholelithiasis and disorders of gallbladder | Cholelithiasis and Disorders of Gallbladder | ICD-10: K80-K82 | deaths; deathRate; ageAdjustedDeathRate | 2019-2019 |
| deaths:chronic liver disease and cirrhosis | Chronic Liver Disease and Cirrhosis | ICD-10: K70, K73; K70, K73-K74 (definition varies by year: K70, K73-K74) | deaths; deathRate; ageAdjustedDeathRate | 2007-2021 |
| deaths:chronic lower respiratory diseases | Chronic Lower Respiratory Diseases | ICD-10: J40-J47 | deaths; deathRate; ageAdjustedDeathRate | 2007-2021 |
| deaths:complications of medical and surgical care | Complications of Medical and Surgical Care | ICD-10: Y40-Y84, Y88 | deaths; deathRate; ageAdjustedDeathRate | 2019-2019 |
| deaths:congenital malformations, deformations, and chromosomal abnormalities | Congenital Malformations, Deformations, and Chromosomal Abnormalities | ICD-10: Q00-Q99 | deaths; deathRate; ageAdjustedDeathRate | 2007-2019 |
| deaths:diabetes mellitus | Diabetes Mellitus | ICD-10: E10-E14 | deaths; deathRate; ageAdjustedDeathRate | 2007-2021 |
| deaths:diseases of heart | Diseases of Heart | ICD-10: I00-I09, I11, I13, I20-I51 | deaths; deathRate; ageAdjustedDeathRate | 2007-2021 |
| deaths:essential hypertension and renal diseases | Essential Hypertension and Renal Diseases | ICD-10: I10, I12; I10, I12, I15 (definition varies by year: I10, I12, I15) | deaths; deathRate; ageAdjustedDeathRate | 2007-2021 |
| deaths:human immunodeficiency virus disease | Human Immunodeficiency Virus Disease | ICD-10: HIV: B20-B24 | deaths; deathRate; ageAdjustedDeathRate | 2007-2019 |
| deaths:influenza (flu) and pneumonia | Influenza (Flu) and Pneumonia | ICD-10: J09-J18 | deaths; deathRate; ageAdjustedDeathRate | 2007-2021 |
| deaths:insitu or benign / uncertain neoplasms | Insitu or Benign / Uncertain Neoplasms | ICD-10: D00-D48 | deaths; deathRate; ageAdjustedDeathRate | 2007-2019 |
| deaths:intentional self-harm | Intentional Self-Harm | ICD-10: Suicide: U03, X60-X84, Y87.0; Suicide: X60-X84, Y87.0 (definition varies | deaths; deathRate; ageAdjustedDeathRate | 2007-2021 |
| deaths:malignant neoplasms | Malignant Neoplasms | ICD-10: Cancer: C00-C97 | deaths; deathRate; ageAdjustedDeathRate | 2007-2021 |
| deaths:meningitis | Meningitis | ICD-10: G00, G03 | deaths; deathRate; ageAdjustedDeathRate | 2015-2015 |
| deaths:mental and behavioral disorders due to accidental poisoning and other psychoactive substance use | Mental and Behavioral Disorders due to Accidental Poisoning and Other Psychoactive Substance Use | ICD-10: F11-F16, F18-F19, X40-X42, X44 | deaths; deathRate; ageAdjustedDeathRate | 2007-2021 |
| deaths:mental and behavioral disorders due to use of alcohol | Mental and Behavioral Disorders due to Use of Alcohol | ICD-10: F10 | deaths; deathRate; ageAdjustedDeathRate | 2007-2021 |
| deaths:nephritis, nephrotic syndrome and nephrosis | Nephritis, Nephrotic Syndrome and Nephrosis | ICD-10: N00-N07, N17-N19, N25-N27 | deaths; deathRate; ageAdjustedDeathRate | 2007-2020 |
| deaths:parkinson's disease | Parkinson's Disease | ICD-10: G20 | deaths; deathRate; ageAdjustedDeathRate | 2011-2019 |
| deaths:peptic ulcer | Peptic Ulcer | ICD-10: K25-K28 | deaths; deathRate; ageAdjustedDeathRate | 2016-2019 |
| deaths:pregnancy, childbirth and the puerperium | Pregnancy, Childbirth and the Puerperium | ICD-10: O00-O09 | deaths; deathRate; ageAdjustedDeathRate | 2017-2017 |
| deaths:septicemia | Septicemia | ICD-10: A40-A41 | deaths; deathRate; ageAdjustedDeathRate | 2007-2019 |
| deaths:tuberculosis | Tuberculosis | ICD-10: A16-A19 | deaths; deathRate; ageAdjustedDeathRate | 2011-2011 |
| deaths:viral hepatitis | Viral Hepatitis | ICD-10: B15-B19 | deaths; deathRate; ageAdjustedDeathRate | 2008-2019 |

### Tier-0 anchors (ICD-10 -> Wikidata -> SPG, verified)

| nyc_id | cause | SPG system_id | SPG label | wd item | matched ICD | method | in-473 |
|---|---|---|---|---|---|---|---|
| deaths:aortic aneurysm and dissection | Aortic Aneurysm and Dissection | Y6UToUjmfn | abdominal aortic aneurysm | Q2256736 abdominal aortic aneurysm | I71.4 | sparql_p494 | False |
| deaths:aortic aneurysm and dissection | Aortic Aneurysm and Dissection | 5IuCUlfrAW | thoracic aortic aneurysm | Q3616648 thoracic aortic aneurysm | I71.2 | sparql_p494 | False |
| deaths:aortic aneurysm and dissection | Aortic Aneurysm and Dissection | wDob2uJcSH | aortic dissection | Q594660 aortic dissection | I71.0 | sparql_p494 | False |
| deaths:atherosclerosis | Atherosclerosis | sIlnXPgvIT | atheroma | Q1058276 atheroma | I70.9 | sparql_p494 | False |
| deaths:atherosclerosis | Atherosclerosis | Pfu5fwIyZx | gangrene | Q168805 gangrene | I70.2 | sparql_p494 | False |
| deaths:atherosclerosis | Atherosclerosis | xsZCyIIBRG | Monckeberg arteriosclerosis | Q938991 Monckeberg arteriosclerosis | I70.2 | sparql_p494 | False |
| deaths:certain conditions originating in the perinatal period | Certain Conditions originating in the Perinatal Period | aJYOA5y3UG | perinatal disease | Q18968218 perinatal disease | P00-P96 | sparql_p494 | False |
| deaths:chronic liver disease and cirrhosis | Chronic Liver Disease and Cirrhosis | Eem_xaD3Yw | alcoholic liver disease | Q558404 alcoholic liver disease | K70 | sparql_p494 | False |
| deaths:chronic liver disease and cirrhosis | Chronic Liver Disease and Cirrhosis | f3q5XkLWzh | alcoholic fatty liver | Q25416562 alcoholic fatty liver | K70.0 | sparql_p494 | False |
| deaths:chronic liver disease and cirrhosis | Chronic Liver Disease and Cirrhosis | BGOKSHZlNJ | alcoholic hepatitis | Q3144986 alcoholic hepatitis | K70.1 | sparql_p494 | False |
| deaths:essential hypertension and renal diseases | Essential Hypertension and Renal Diseases | PWqr_kRuwW | renal hypertension | Q11788761 renal hypertension | I12 | sparql_p494 | True |
| deaths:essential hypertension and renal diseases | Essential Hypertension and Renal Diseases | fo-h4u_aJp | arterial hypertension | Q41861 arterial hypertension | I10-I1515. | sparql_p494 | True |
| deaths:malignant neoplasms | Malignant Neoplasms | RDEImUmPgF | cancer | Q12078 cancer | C00-C97 | sparql_p494 | False |
| deaths:meningitis | Meningitis | qVCzuMt4N3 | haemophilus meningitis | Q17119372 haemophilus meningitis | G00.0 | sparql_p494 | False |
| deaths:meningitis | Meningitis | 13WuEFs-4F | aseptic meningitis | Q4804182 aseptic meningitis | G03.0 | sparql_p494 | False |
| deaths:meningitis | Meningitis | RM0YyFpVVp | nervous system disease | Q6996973 nervous system disease | G00-G99 | sparql_p494 | False |
| deaths:meningitis | Meningitis | FTcyQmGKu1 | pneumococcal meningitis | Q3854685 pneumococcal meningitis | G00.1 | sparql_p494 | False |
| deaths:mental and behavioral disorders due to use of alcohol | Mental and Behavioral Disorders due to Use of Alcohol | -ru3UMMkVB | substance-related disorder | Q4134457 substance-related disorder | F10 | sparql_p494 | False |
| deaths:mental and behavioral disorders due to use of alcohol | Mental and Behavioral Disorders due to Use of Alcohol | xsZfbnK87R | substance use disorder | Q7632070 substance use disorder | F10 | sparql_p494 | False |
| deaths:mental and behavioral disorders due to use of alcohol | Mental and Behavioral Disorders due to Use of Alcohol | d5jefjHMez | alcoholism | Q15326 alcoholism | F10 | sparql_p494 | False |
| deaths:mental and behavioral disorders due to use of alcohol | Mental and Behavioral Disorders due to Use of Alcohol | NM65CTyP3z | drug withdrawal | Q498902 drug withdrawal | F10 | sparql_p494 | False |
| deaths:mental and behavioral disorders due to use of alcohol | Mental and Behavioral Disorders due to Use of Alcohol | DU5dF5vxkA | binge drinking | Q1521260 binge drinking | F10 | sparql_p494 | False |
| deaths:mental and behavioral disorders due to use of alcohol | Mental and Behavioral Disorders due to Use of Alcohol | 2Cbi75x4kC | substance abuse | Q3184856 substance abuse | F10 | sparql_p494 | False |
| deaths:mental and behavioral disorders due to use of alcohol | Mental and Behavioral Disorders due to Use of Alcohol | W7eIQCjzy2 | alcohol and health | Q11290178 Health effects of alcohol | F10 | sparql_p494 | False |
| deaths:mental and behavioral disorders due to use of alcohol | Mental and Behavioral Disorders due to Use of Alcohol | Qqx0E1tYR6 | alcohol-induced psychotic disorder | Q4062514 alcohol-induced psychotic disorder | F10.5 | sparql_p494 | False |
| deaths:mental and behavioral disorders due to use of alcohol | Mental and Behavioral Disorders due to Use of Alcohol | uXHBnqFIrn | alcohol dependence | Q4713263 alcohol dependence | F10.2 | sparql_p494 | False |
| deaths:mental and behavioral disorders due to use of alcohol | Mental and Behavioral Disorders due to Use of Alcohol | -svrJVV3ld | intoxication | Q205972 alcohol intoxication | F10.0 | sparql_p494 | False |
| deaths:mental and behavioral disorders due to use of alcohol | Mental and Behavioral Disorders due to Use of Alcohol | ueT9zFXSHW | delirium tremens | Q209647 delirium tremens | F10.4 | sparql_p494 | False |
| deaths:mental and behavioral disorders due to use of alcohol | Mental and Behavioral Disorders due to Use of Alcohol | RCRhUqec__ | substance-induced psychosis | Q2151786 substance-induced psychosis | F10-F19 | sparql_p494 | False |
| deaths:mental and behavioral disorders due to use of alcohol | Mental and Behavioral Disorders due to Use of Alcohol | 9wRzMt2S_X | alcohol withdrawal syndrome | Q2914873 alcohol withdrawal syndrome | F10.3 | sparql_p494 | False |
| deaths:mental and behavioral disorders due to use of alcohol | Mental and Behavioral Disorders due to Use of Alcohol | cXUl0A7skU | alcohol-related disorders | Q56014553 alcohol-related disorders | F10.9 | sparql_p494 | False |

### Verified on Wikidata but NOT in SPG (context only — cannot be matches)

- Alzheimer's Disease: Q5326566 early-onset Alzheimer's disease (G30.0)
- Chronic Lower Respiratory Diseases: Q2319892 chronic lower respiratory diseases (J40-J47)
- Diseases of Heart: Q18968199 obsolete benign hypertensive heart disease (I11.9)
- Intentional Self-Harm: Q4072473 autoaggression (X60-X84)

### Causes with NO verified Wikidata candidate (need LLM matching)

- deaths:accidents except drug poisoning Accidents Except Drug Poisoning (ICD: V01-X39,X43,X45-X59,Y85-Y86)
- deaths:anemias Anemias (ICD: D50-D64)
- deaths:assault Assault (ICD: U01-U02,Y87.1,X85-Y09; Homicide: Y87.1,X85-Y09)
- deaths:cerebrovascular disease Cerebrovascular Disease (ICD: I60-I69)
- deaths:cholelithiasis and disorders of gallbladder Cholelithiasis and Disorders of Gallbladder (ICD: K80-K82)
- deaths:complications of medical and surgical care Complications of Medical and Surgical Care (ICD: Y40-Y84,Y88)
- deaths:congenital malformations, deformations, and chromosomal abnormalities Congenital Malformations, Deformations, and Chromosomal Abnormalities (ICD: Q00-Q99)
- deaths:diabetes mellitus Diabetes Mellitus (ICD: E10-E14)
- deaths:human immunodeficiency virus disease Human Immunodeficiency Virus Disease (ICD: B20-B24)
- deaths:influenza (flu) and pneumonia Influenza (Flu) and Pneumonia (ICD: J09-J18)
- deaths:insitu or benign / uncertain neoplasms Insitu or Benign / Uncertain Neoplasms (ICD: D00-D48)
- deaths:mental and behavioral disorders due to accidental poisoning and other psychoactive substance use Mental and Behavioral Disorders due to Accidental Poisoning and Other Psychoactive Substance Use (ICD: F11-F16,F18-F19,X40-X42,X44)
- deaths:nephritis, nephrotic syndrome and nephrosis Nephritis, Nephrotic Syndrome and Nephrosis (ICD: N00-N07,N17-N19,N25-N27)
- deaths:parkinson's disease Parkinson's Disease (ICD: G20)
- deaths:peptic ulcer Peptic Ulcer (ICD: K25-K28)
- deaths:pregnancy, childbirth and the puerperium Pregnancy, Childbirth and the Puerperium (ICD: O00-O09)
- deaths:septicemia Septicemia (ICD: A40-A41)
- deaths:tuberculosis Tuberculosis (ICD: A16-A19)
- deaths:viral hepatitis Viral Hepatitis (ICD: B15-B19)

Supplement candidates (wider SPG, not in table above):
- deaths:accidents except drug poisoning -> `NaqXdIgUsj` pesticide poisoning — poisoning of humans from pesticide exposure (cos 0.28)
- deaths:accidents except drug poisoning -> `v-mj7HcE0V` falling — accident (cos 0.27)
- deaths:alzheimer's disease -> `bSqtTxWXSy` Alzheimer's disease — progressive, neurodegenerative disease characterized by memory loss (cos 0.69)
- deaths:alzheimer's disease -> `nfZPLc-5CD` Alzheimer disease 4 — Alzheimer's disease that has material basis in a mutation in the prese (cos 0.69)
- deaths:anemias -> `bEBUbgyqYw` deficiency anemia — Human disease (cos 0.35)
- deaths:aortic aneurysm and dissection -> `5iNla3Myma` dissecting aortic aneurysm — Human disease (cos 0.77)
- deaths:aortic aneurysm and dissection -> `wiEYVMs74H` dissection — tear within the wall of a blood vessel (cos 0.56)
- deaths:atherosclerosis -> `h3-fHeDiWK` aortic atherosclerosis — Human disease (cos 0.69)
- deaths:atherosclerosis -> `IrVt9Z4DG8` cerebral atherosclerosis — type of atherosclerosis where build-up of plaque in the blood vessels  (cos 0.57)
- deaths:cerebrovascular disease -> `9r2mCjgLWr` basal ganglia cerebrovascular disease — Human disease (cos 0.52)
- deaths:cerebrovascular disease -> `gJXeuNMolq` cerebrovascular disease — artery disease that is characterized by dysfunction of the blood vesse (cos 0.51)
- deaths:certain conditions originating in the perinatal period -> `aJYOA5y3UG` perinatal disease — type of human disease (cos 0.63)
- deaths:certain conditions originating in the perinatal period -> `nnQGb5_DMK` perinatal care — care of women and a fetus or newborn given before, during, and after d (cos 0.28)
- deaths:cholelithiasis and disorders of gallbladder -> `3odupadx9z` cholelithiasis — Human disease (cos 0.56)
- deaths:cholelithiasis and disorders of gallbladder -> `RV1SwogTnT` gallbladder disease — gastrointestinal system disease that is located in the gallbladder (cos 0.51)
- deaths:chronic liver disease and cirrhosis -> `Z6KX9_jgVH` liver cirrhosis — chronic disease of the liver, characterized by fibrosis (cos 0.52)
- deaths:chronic liver disease and cirrhosis -> `riDOFAw0Lu` experimental liver cirrhosis — experimentally induced chronic injuries to the parenchymal cells in th (cos 0.36)
- deaths:chronic lower respiratory diseases -> `dAGu8Q7H35` lower respiratory tract disease — respiratory system disease which involves the lower respiratory tract (cos 0.55)
- deaths:chronic lower respiratory diseases -> `FQU6Y5EryN` respiratory therapy —  (cos 0.41)
- deaths:complications of medical and surgical care -> `ldqXXnek67` intraoperative complications — complications that affect patients during surgery (cos 0.37)
- deaths:complications of medical and surgical care -> `esiPwRl8Y5` complications of diabetes mellitus — medical conditions (cos 0.36)
- deaths:congenital malformations, deformations, and chromosomal abnormalities -> `pl3-mwSQN_` congenital limb deformities — human disease (cos 0.51)
- deaths:congenital malformations, deformations, and chromosomal abnormalities -> `7rlJM-K1pg` maxillofacial abnormality — congenital structural deformities, malformations, or other abnormaliti (cos 0.5)
- deaths:diabetes mellitus -> `VJC2mz4Z20` neonatal diabetes mellitus — It is a congenital form of diabetes (cos 0.57)
- deaths:diabetes mellitus -> `esiPwRl8Y5` complications of diabetes mellitus — medical conditions (cos 0.56)
- deaths:human immunodeficiency virus disease -> `26jenLNIdy` HIV protease — enzyme of the human immunodeficiency virus (cos 0.65)
- deaths:human immunodeficiency virus disease -> `udNK3lkaK0` Human Immunodeficiency Virus proteins — proteins synthesized by Human Immunodeficiency Viruses such as HIV-1 a (cos 0.62)
- deaths:influenza (flu) and pneumonia -> `byOZyZDD9F` viral pneumonia — pneumonia described as an inflammatory illness of the lung commonly ca (cos 0.48)
- deaths:influenza (flu) and pneumonia -> `ru5XrhUPnf` Influenza B virus — species of virus (cos 0.46)
- deaths:insitu or benign / uncertain neoplasms -> `wP6uQKZm9N` anus neoplasm — Human disease (cos 0.32)
- deaths:insitu or benign / uncertain neoplasms -> `J21rVG85oX` myoma — human disease (cos 0.31)
- deaths:intentional self-harm -> `QeiZjfpxr8` parasuicide — form of self-harm in which someone mimics the act of suicide without t (cos 0.43)
- deaths:intentional self-harm -> `cAz2Cd_y0K` completed suicide — successful attempt to kill oneself by an act of suicide (cos 0.36)
- deaths:malignant neoplasms -> `deNu8K34Ys` anus cancer — large intestine cancer that is located in the anus (cos 0.49)
- deaths:malignant neoplasms -> `U5tljbZubR` colon cancer — colorectal cancer that is located in the colon (cos 0.48)
- deaths:meningitis -> `XrIF80FWUs` viral meningitis — human disease (cos 0.47)
- deaths:meningitis -> `vUDhTJj55X` fungal meningitis — meningitis that has material basis in a fungal infection (cos 0.45)
- deaths:mental and behavioral disorders due to accidental poisoning and other psychoactive substance use -> `-ru3UMMkVB` substance-related disorder — group of mental and behavioural disorders, including both substance de (cos 0.33)
- deaths:mental and behavioral disorders due to accidental poisoning and other psychoactive substance use -> `2Cbi75x4kC` substance abuse — patterned use of a drug in which the user consumes the psychoactive/ch (cos 0.28)
- deaths:mental and behavioral disorders due to use of alcohol -> `cXUl0A7skU` alcohol-related disorders — disorders related to or resulting from abuse or mis-use of alcohol (cos 0.39)
- deaths:mental and behavioral disorders due to use of alcohol -> `omKDoEEBs9` internalizing disorder — type of emotional and behavioral disorder (cos 0.38)
- deaths:nephritis, nephrotic syndrome and nephrosis -> `7sGWfVGKdD` nephrotic syndrome — Human disease (cos 0.6)
- deaths:nephritis, nephrotic syndrome and nephrosis -> `W9uIkelSWJ` familial nephrotic syndrome — Human disease (cos 0.49)
- deaths:parkinson's disease -> `8jjkmUcwvr` antiparkinson — agents used in the treatment of parkinson's disease (cos 0.55)
- deaths:parkinson's disease -> `Gtjl-ppl-t` parkinsonian syndrome — symptoms that resemble Parkinson's disease (cos 0.54)
- deaths:peptic ulcer -> `EvOgTOJ4y1` active peptic ulcer disease — Human disease (cos 0.45)
- deaths:peptic ulcer -> `8iMhxcdV4v` perforated ulcer — medical condition of the gastrointestinal tract wall (cos 0.4)
- deaths:pregnancy, childbirth and the puerperium -> `ZYGt8IxIqo` anemia in pregnancy — disease of anemia during pregnancy in humans (cos 0.63)
- deaths:pregnancy, childbirth and the puerperium -> `J6Fp0YvRtO` cervical incompetence — cervix disease that is characterized by the beginning of dilation and  (cos 0.49)
- deaths:septicemia -> `IHOJeR55ma` streptococcal septicemia — human disease (cos 0.4)
- deaths:septicemia -> `_BB-Pmb9Ch` viral hemorrhagic septicemia — human disease (cos 0.39)
- deaths:tuberculosis -> `JAZxWSKlRL` Pott disease — tuberculosis of the spine (cos 0.59)
- deaths:tuberculosis -> `FH7eZPwJx2` tuberculosis vaccines — vaccines to prevent tuberculosis (cos 0.59)
- deaths:viral hepatitis -> `tpYBq3golh` hepatitis B — human viral infection (cos 0.59)
- deaths:viral hepatitis -> `W6dhmBUtPt` hepatitis A — acute infectious disease of the liver (cos 0.55)

### heat-complaints (4)

| nyc_id | label | description | measurementType | years |
|---|---|---|---|---|
| complaints:NO HEAT | NO HEAT | 311 heat-season complaint condition (408,473 complaints, Oct 2024-Nov 2026) | complaint count | 2024-2026 |
| complaints:NO HEAT AND NO HOT WATER | NO HEAT AND NO HOT WATER | 311 heat-season complaint condition (173,118 complaints, Oct 2024-Nov 2026) | complaint count | 2024-2026 |
| complaints:NO HOT WATER | NO HOT WATER | 311 heat-season complaint condition (105,683 complaints, Oct 2024-Nov 2026) | complaint count | 2024-2026 |
| complaints:HEAT ON IN SUMMER | HEAT ON IN SUMMER | 311 heat-season complaint condition (1,768 complaints, Oct 2024-Nov 2026) | complaint count | 2024-2026 |

Supplement candidates (wider SPG, not in table above):
- complaints:NO HEAT -> `Q45cha_WOu` chief complaint — principal reason for a person seeking professional assistance (cos 0.29)
- complaints:NO HEAT AND NO HOT WATER -> `Q45cha_WOu` chief complaint — principal reason for a person seeking professional assistance (cos 0.27)
- complaints:NO HOT WATER -> `Q45cha_WOu` chief complaint — principal reason for a person seeking professional assistance (cos 0.28)
- complaints:HEAT ON IN SUMMER -> `Q45cha_WOu` chief complaint — principal reason for a person seeking professional assistance (cos 0.28)

### street-trees (132)

| nyc_id | label | description | measurementType | years |
|---|---|---|---|---|
| trees:platanus-x-acerifolia | London planetree | Platanus x acerifolia (87,014 trees, 2015 census) | tree count | 2015 |
| trees:gleditsia-triacanthos-var-inermis | honeylocust | Gleditsia triacanthos var. inermis (64,264 trees, 2015 census) | tree count | 2015 |
| trees:pyrus-calleryana | Callery pear | Pyrus calleryana (58,931 trees, 2015 census) | tree count | 2015 |
| trees:quercus-palustris | pin oak | Quercus palustris (53,185 trees, 2015 census) | tree count | 2015 |
| trees:acer-platanoides | Norway maple | Acer platanoides (34,189 trees, 2015 census) | tree count | 2015 |
| trees:tilia-cordata | littleleaf linden | Tilia cordata (29,742 trees, 2015 census) | tree count | 2015 |
| trees:prunus | cherry | Prunus (29,279 trees, 2015 census) | tree count | 2015 |
| trees:zelkova-serrata | Japanese zelkova | Zelkova serrata (29,258 trees, 2015 census) | tree count | 2015 |
| trees:ginkgo-biloba | ginkgo | Ginkgo biloba (21,024 trees, 2015 census) | tree count | 2015 |
| trees:styphnolobium-japonicum | Sophora | Styphnolobium japonicum (19,338 trees, 2015 census) | tree count | 2015 |
| trees:acer-rubrum | red maple | Acer rubrum (17,246 trees, 2015 census) | tree count | 2015 |
| trees:fraxinus-pennsylvanica | green ash | Fraxinus pennsylvanica (16,251 trees, 2015 census) | tree count | 2015 |
| trees:tilia-americana | American linden | Tilia americana (13,530 trees, 2015 census) | tree count | 2015 |
| trees:acer-saccharinum | silver maple | Acer saccharinum (12,277 trees, 2015 census) | tree count | 2015 |
| trees:liquidambar-styraciflua | sweetgum | Liquidambar styraciflua (10,657 trees, 2015 census) | tree count | 2015 |
| trees:quercus-rubra | northern red oak | Quercus rubra (8,400 trees, 2015 census) | tree count | 2015 |
| trees:tilia-tomentosa | silver linden | Tilia tomentosa (7,995 trees, 2015 census) | tree count | 2015 |
| trees:ulmus-americana | American elm | Ulmus americana (7,975 trees, 2015 census) | tree count | 2015 |
| trees:acer | maple | Acer (7,080 trees, 2015 census) | tree count | 2015 |
| trees:prunus-cerasifera | purple-leaf plum | Prunus cerasifera (6,879 trees, 2015 census) | tree count | 2015 |
| trees:quercus-bicolor | swamp white oak | Quercus bicolor (6,598 trees, 2015 census) | tree count | 2015 |
| trees:acer-platanoides-crimson-king | crimson king maple | Acer platanoides 'Crimson King' (5,923 trees, 2015 census) | tree count | 2015 |
| trees:ulmus-parvifolia | Chinese elm | Ulmus parvifolia (5,345 trees, 2015 census) | tree count | 2015 |
| trees:prunus-virginiana | 'Schubert' chokecherry | Prunus virginiana (4,888 trees, 2015 census) | tree count | 2015 |
| trees:syringa-reticulata | Japanese tree lilac | Syringa reticulata (4,568 trees, 2015 census) | tree count | 2015 |
| trees:cercis-canadensis | eastern redbud | Cercis canadensis (3,801 trees, 2015 census) | tree count | 2015 |
| trees:koelreuteria-paniculata | golden raintree | Koelreuteria paniculata (3,719 trees, 2015 census) | tree count | 2015 |
| trees:malus | crab apple | Malus (3,527 trees, 2015 census) | tree count | 2015 |
| trees:gymnocladus-dioicus | Kentucky coffeetree | Gymnocladus dioicus (3,364 trees, 2015 census) | tree count | 2015 |
| trees:quercus-phellos | willow oak | Quercus phellos (3,184 trees, 2015 census) | tree count | 2015 |
| trees:metasequoia-glyptostroboides | dawn redwood | Metasequoia glyptostroboides (3,020 trees, 2015 census) | tree count | 2015 |
| trees:crataegus | hawthorn | Crataegus (2,988 trees, 2015 census) | tree count | 2015 |
| trees:acer-saccharum | sugar maple | Acer saccharum (2,844 trees, 2015 census) | tree count | 2015 |
| trees:acer-pseudoplatanus | sycamore maple | Acer pseudoplatanus (2,731 trees, 2015 census) | tree count | 2015 |
| trees:fraxinus | ash | Fraxinus (2,609 trees, 2015 census) | tree count | 2015 |
| trees:acer-campestre | hedge maple | Acer campestre (2,550 trees, 2015 census) | tree count | 2015 |
| trees:celtis-occidentalis | common hackberry | Celtis occidentalis (2,382 trees, 2015 census) | tree count | 2015 |
| trees:quercus-acutissima | sawtooth oak | Quercus acutissima (2,244 trees, 2015 census) | tree count | 2015 |
| trees:maackia-amurensis | Amur maackia | Maackia amurensis (2,197 trees, 2015 census) | tree count | 2015 |
| trees:carpinus-betulus | European hornbeam | Carpinus betulus (2,099 trees, 2015 census) | tree count | 2015 |
| trees:acer-ginnala | Amur maple | Acer ginnala (2,049 trees, 2015 census) | tree count | 2015 |
| trees:amelanchier | serviceberry | Amelanchier (2,032 trees, 2015 census) | tree count | 2015 |
| trees:robinia-pseudoacacia | black locust | Robinia pseudoacacia (1,784 trees, 2015 census) | tree count | 2015 |
| trees:quercus-alba | white oak | Quercus alba (1,686 trees, 2015 census) | tree count | 2015 |
| trees:quercus-robur | English oak | Quercus robur (1,644 trees, 2015 census) | tree count | 2015 |
| trees:ulmus-pumila | Siberian elm | Ulmus pumila (1,595 trees, 2015 census) | tree count | 2015 |
| trees:cornus-florida | flowering dogwood | Cornus florida (1,552 trees, 2015 census) | tree count | 2015 |
| trees:carpinus-caroliniana | American hornbeam | Carpinus caroliniana (1,517 trees, 2015 census) | tree count | 2015 |
| trees:quercus-shumardii | Schumard's oak | Quercus shumardii (1,487 trees, 2015 census) | tree count | 2015 |
| trees:quercus-coccinea | scarlet oak | Quercus coccinea (1,465 trees, 2015 census) | tree count | 2015 |
| trees:quercus-velutina | black oak | Quercus velutina (1,327 trees, 2015 census) | tree count | 2015 |
| trees:taxodium-distichum | bald cypress | Taxodium distichum (1,261 trees, 2015 census) | tree count | 2015 |
| trees:morus | mulberry | Morus (1,157 trees, 2015 census) | tree count | 2015 |
| trees:acer-palmatum | Japanese maple | Acer palmatum (1,130 trees, 2015 census) | tree count | 2015 |
| trees:fraxinus-americana | white ash | Fraxinus americana (1,121 trees, 2015 census) | tree count | 2015 |
| trees:juniperus-virginiana | eastern redcedar | Juniperus virginiana (1,101 trees, 2015 census) | tree count | 2015 |
| trees:aesculus-hippocastanum | horse chestnut | Aesculus hippocastanum (1,096 trees, 2015 census) | tree count | 2015 |
| trees:ostrya-virginiana | American hophornbeam | Ostrya virginiana (1,081 trees, 2015 census) | tree count | 2015 |
| trees:liriodendron-tulipifera | tulip-poplar | Liriodendron tulipifera (1,076 trees, 2015 census) | tree count | 2015 |
| trees:cornus-mas | Cornelian cherry | Cornus mas (1,066 trees, 2015 census) | tree count | 2015 |
| trees:quercus-imbricaria | shingle oak | Quercus imbricaria (1,049 trees, 2015 census) | tree count | 2015 |
| trees:eucommia-ulmoides | hardy rubber tree | Eucommia ulmoides (915 trees, 2015 census) | tree count | 2015 |
| trees:cercidiphyllum-japonicum | katsura tree | Cercidiphyllum japonicum (911 trees, 2015 census) | tree count | 2015 |
| trees:ailanthus-altissima | tree of heaven | Ailanthus altissima (756 trees, 2015 census) | tree count | 2015 |
| trees:magnolia | magnolia | Magnolia (699 trees, 2015 census) | tree count | 2015 |
| trees:prunus-serotina | black cherry | Prunus serotina (607 trees, 2015 census) | tree count | 2015 |
| trees:betula-nigra | river birch | Betula nigra (565 trees, 2015 census) | tree count | 2015 |
| trees:catalpa | catalpa | Catalpa (551 trees, 2015 census) | tree count | 2015 |
| trees:betula-papyrifera | paper birch | Betula papyrifera (535 trees, 2015 census) | tree count | 2015 |
| trees:quercus-macrocarpa | bur oak | Quercus macrocarpa (515 trees, 2015 census) | tree count | 2015 |
| trees:cladrastis-kentukea | Kentucky yellowwood | Cladrastis kentukea (479 trees, 2015 census) | tree count | 2015 |
| trees:syringa-pekinensis | Chinese tree lilac | Syringa pekinensis (462 trees, 2015 census) | tree count | 2015 |
| trees:lagerstroemia | crepe myrtle | Lagerstroemia (442 trees, 2015 census) | tree count | 2015 |
| trees:carpinus-japonica | Japanese hornbeam | Carpinus japonica (426 trees, 2015 census) | tree count | 2015 |
| trees:styrax-japonicus | Japanese snowbell | Styrax japonicus (392 trees, 2015 census) | tree count | 2015 |
| trees:chamaecyparis-thyoides | Atlantic white cedar | Chamaecyparis thyoides (355 trees, 2015 census) | tree count | 2015 |
| trees:picea-abies | Norway spruce | Picea abies (355 trees, 2015 census) | tree count | 2015 |
| trees:crataegus-crusgalli-var-inermis | cockspur hawthorn | Crataegus crusgalli var. inermis (341 trees, 2015 census) | tree count | 2015 |
| trees:thuja-occidentalis | arborvitae | Thuja occidentalis (328 trees, 2015 census) | tree count | 2015 |
| trees:corylus-colurna | Turkish hazelnut | Corylus colurna (317 trees, 2015 census) | tree count | 2015 |
| trees:cornus-kousa | kousa dogwood | Cornus kousa (302 trees, 2015 census) | tree count | 2015 |
| trees:betula-pendula | silver birch | Betula pendula (300 trees, 2015 census) | tree count | 2015 |
| trees:juglans-nigra | black walnut | Juglans nigra (295 trees, 2015 census) | tree count | 2015 |
| trees:pinus | pine | Pinus (289 trees, 2015 census) | tree count | 2015 |
| trees:nyssa-sylvatica | blackgum | Nyssa sylvatica (288 trees, 2015 census) | tree count | 2015 |
| trees:salix-babylonica | weeping willow | Salix babylonica (282 trees, 2015 census) | tree count | 2015 |
| trees:cornus-alternifolia | pagoda dogwood | Cornus alternifolia (280 trees, 2015 census) | tree count | 2015 |
| trees:parrotia-persica | Persian ironwood | Parrotia persica (277 trees, 2015 census) | tree count | 2015 |
| trees:populus-deltoides | eastern cottonwood | Populus deltoides (276 trees, 2015 census) | tree count | 2015 |
| trees:fagus-grandifolia | American beech | Fagus grandifolia (273 trees, 2015 census) | tree count | 2015 |
| trees:paulownia-tomentosa | empress tree | Paulownia tomentosa (245 trees, 2015 census) | tree count | 2015 |
| trees:chionanthus-retusus | Chinese fringetree | Chionanthus retusus (234 trees, 2015 census) | tree count | 2015 |
| trees:halesia-diptera | two-winged silverbell | Halesia diptera (221 trees, 2015 census) | tree count | 2015 |
| trees:acer-griseum | paperbark maple | Acer griseum (220 trees, 2015 census) | tree count | 2015 |
| trees:cercis-reniformis | Oklahoma redbud | Cercis reniformis (219 trees, 2015 census) | tree count | 2015 |
| trees:picea | spruce | Picea (202 trees, 2015 census) | tree count | 2015 |
| trees:pinus-strobus | white pine | Pinus strobus (202 trees, 2015 census) | tree count | 2015 |
| trees:phellodendron-amurense | Amur cork tree | Phellodendron amurense (183 trees, 2015 census) | tree count | 2015 |
| trees:taxodium-ascendens | pond cypress | Taxodium ascendens (181 trees, 2015 census) | tree count | 2015 |
| trees:castanea-mollissima | Chinese chestnut | Castanea mollissima (173 trees, 2015 census) | tree count | 2015 |
| trees:sassafras-albidum | sassafras | Sassafras albidum (171 trees, 2015 census) | tree count | 2015 |
| trees:magnolia-acuminata | cucumber magnolia | Magnolia acuminata (169 trees, 2015 census) | tree count | 2015 |
| trees:albizia-julibrissin | mimosa | Albizia julibrissin (163 trees, 2015 census) | tree count | 2015 |
| trees:acer-tataricum | tartar maple | Acer tataricum (153 trees, 2015 census) | tree count | 2015 |
| trees:ilex | holly | Ilex (138 trees, 2015 census) | tree count | 2015 |
| trees:magnolia-grandiflora | southern magnolia | Magnolia grandiflora (132 trees, 2015 census) | tree count | 2015 |
| trees:picea-pungens | blue spruce | Picea pungens (126 trees, 2015 census) | tree count | 2015 |
| trees:fagus-sylvatica | European beech | Fagus sylvatica (125 trees, 2015 census) | tree count | 2015 |
| trees:aesculus-x-carnea | red horse chestnut | Aesculus x carnea (116 trees, 2015 census) | tree count | 2015 |
| trees:acer-nigrum | black maple | Acer nigrum (114 trees, 2015 census) | tree count | 2015 |
| trees:acer-buergerianum | trident maple | Acer buergerianum (110 trees, 2015 census) | tree count | 2015 |
| trees:chamaecyparis-pisifera | false cypress | Chamaecyparis pisifera (108 trees, 2015 census) | tree count | 2015 |
| trees:pinus-resinosa | red pine | Pinus resinosa (106 trees, 2015 census) | tree count | 2015 |
| trees:carya-glabra | pignut hickory | Carya glabra (99 trees, 2015 census) | tree count | 2015 |
| trees:populus-grandidentata | bigtooth aspen | Populus grandidentata (94 trees, 2015 census) | tree count | 2015 |
| trees:tsuga-canadensis | eastern hemlock | Tsuga canadensis (88 trees, 2015 census) | tree count | 2015 |
| trees:cedrus-atlantica | Atlas cedar | Cedrus atlantica (87 trees, 2015 census) | tree count | 2015 |
| trees:pseudotsuga-menziesii | Douglas-fir | Pseudotsuga menziesii (85 trees, 2015 census) | tree count | 2015 |
| trees:populus-tremuloides | quaking aspen | Populus tremuloides (83 trees, 2015 census) | tree count | 2015 |
| trees:quercus-falcata | southern red oak | Quercus falcata (83 trees, 2015 census) | tree count | 2015 |
| trees:aesculus-glabra | Ohio buckeye | Aesculus glabra (75 trees, 2015 census) | tree count | 2015 |
| trees:cedrus-deodara | Himalayan cedar | Cedrus deodara (72 trees, 2015 census) | tree count | 2015 |
| trees:acer-negundo | boxelder | Acer negundo (64 trees, 2015 census) | tree count | 2015 |
| trees:acer-truncatum | Shantung maple | Acer truncatum (59 trees, 2015 census) | tree count | 2015 |
| trees:cotinus-coggygria | smoketree | Cotinus coggygria (58 trees, 2015 census) | tree count | 2015 |
| trees:alnus-glutinosa | European alder | Alnus glutinosa (47 trees, 2015 census) | tree count | 2015 |
| trees:larix-laricina | American larch | Larix laricina (46 trees, 2015 census) | tree count | 2015 |
| trees:pinus-nigra | black pine | Pinus nigra (37 trees, 2015 census) | tree count | 2015 |
| trees:pinus-rigida | pitch pine | Pinus rigida (33 trees, 2015 census) | tree count | 2015 |
| trees:maclura-pomifera | Osage-orange | Maclura pomifera (29 trees, 2015 census) | tree count | 2015 |
| trees:pinus-sylvestris | Scots pine | Pinus sylvestris (25 trees, 2015 census) | tree count | 2015 |
| trees:pinus-virginiana | Virginia pine | Pinus virginiana (10 trees, 2015 census) | tree count | 2015 |

Supplement candidates (wider SPG, not in table above):
- trees:gleditsia-triacanthos-var-inermis -> `NDJ2Gn__AH` Gleditsia — genus of plants (cos 0.29)
- trees:quercus-palustris -> `lEbbG9Fo83` Quercus — tree or shrub in the genus Quercus (cos 0.44)
- trees:acer-platanoides -> `eCsxTFBHr7` Acer — genus of plants (cos 0.31)
- trees:acer-platanoides -> `E0oUp41f7E` Norway — country in northern Europe (cos 0.27)
- trees:tilia-cordata -> `Hov-Qdge36` Tilia — genus of plants (cos 0.27)
- trees:prunus -> `nHS-FaTiUM` Prunus — genus of plants (cos 0.43)
- trees:prunus -> `fbdtRB3oSH` Prunus dulcis — species of plant (cos 0.34)
- trees:zelkova-serrata -> `XuzpCJ807U` Japanese encephalitis — infection of the brain caused by the Japanese encephalitis virus (cos 0.29)
- trees:zelkova-serrata -> `viOgJC0CLR` Japanese encephalitis virus — species of virus (cos 0.27)
- trees:ginkgo-biloba -> `k1a51uWALK` Ginkgo biloba — species of plant, ginkgo (cos 0.68)
- trees:ginkgo-biloba -> `50m0gv8mHo` Ginkgo biloba extract — plant extract (cos 0.55)
- trees:styphnolobium-japonicum -> `BZ81n8LuxN` Schistosoma japonicum — species of worm (cos 0.33)
- trees:styphnolobium-japonicum -> `5dUG2YZ3FR` schistosomiasis japonica —  (cos 0.26)
- trees:acer-rubrum -> `eCsxTFBHr7` Acer — genus of plants (cos 0.33)
- trees:fraxinus-pennsylvanica -> `5i45ouIeA7` Pennsylvania — state of the United States of America (cos 0.41)
- trees:fraxinus-pennsylvanica -> `ncw9JsI8Xh` Fraxinus — genus of plants (cos 0.34)
- trees:tilia-americana -> `LFtV5UUc6U` Asian Americans — Americans of Asian ancestry (cos 0.35)
- trees:tilia-americana -> `d2Qa0ojH43` Central Americans — people from Central America (cos 0.35)
- trees:acer-saccharinum -> `eCsxTFBHr7` Acer — genus of plants (cos 0.3)
- trees:acer-saccharinum -> `tjBsmCCSyh` silver stain — Using silver compounds to add colour (cos 0.28)
- trees:quercus-rubra -> `lEbbG9Fo83` Quercus — tree or shrub in the genus Quercus (cos 0.44)
- trees:quercus-rubra -> `QWGefQnZu2` Northern blot — molecular biology technique (cos 0.25)
- trees:tilia-tomentosa -> `tjBsmCCSyh` silver stain — Using silver compounds to add colour (cos 0.27)
- trees:tilia-tomentosa -> `Hov-Qdge36` Tilia — genus of plants (cos 0.26)
- trees:ulmus-americana -> `LFtV5UUc6U` Asian Americans — Americans of Asian ancestry (cos 0.37)
- trees:ulmus-americana -> `d2Qa0ojH43` Central Americans — people from Central America (cos 0.36)
- trees:acer -> `eCsxTFBHr7` Acer — genus of plants (cos 0.39)
- trees:acer -> `UIPW08nZnL` census — acquiring and recording information about the members of a given popul (cos 0.26)
- trees:prunus-cerasifera -> `fbdtRB3oSH` Prunus dulcis — species of plant (cos 0.28)
- trees:prunus-cerasifera -> `nHS-FaTiUM` Prunus — genus of plants (cos 0.25)
- trees:quercus-bicolor -> `lEbbG9Fo83` Quercus — tree or shrub in the genus Quercus (cos 0.41)
- trees:acer-platanoides-crimson-king -> `eCsxTFBHr7` Acer — genus of plants (cos 0.27)
- trees:ulmus-parvifolia -> `I0ve1O051w` Ulmus — genus of plants (cos 0.26)
- trees:prunus-virginiana -> `nHS-FaTiUM` Prunus — genus of plants (cos 0.3)
- trees:prunus-virginiana -> `fbdtRB3oSH` Prunus dulcis — species of plant (cos 0.26)
- trees:syringa-reticulata -> `qBSsUGZNrI` Syringa — genus of plants (cos 0.31)
- trees:syringa-reticulata -> `XuzpCJ807U` Japanese encephalitis — infection of the brain caused by the Japanese encephalitis virus (cos 0.28)
- trees:koelreuteria-paniculata -> `TNyAbbbUN-` Andrographis paniculata — species of plant (cos 0.27)
- trees:malus -> `lza23w8lNt` Malus — genus of plants (cos 0.44)
- trees:gymnocladus-dioicus -> `Cfu3T41k9q` Coffea — genus of flowering plants in the family Rubiaceae (cos 0.27)
- trees:quercus-phellos -> `lEbbG9Fo83` Quercus — tree or shrub in the genus Quercus (cos 0.44)
- trees:metasequoia-glyptostroboides -> `bijDg07xQ7` Sequoia — genus of plants (cos 0.35)
- trees:crataegus -> `DoatR0rW6X` Crataegus — genus of plants (cos 0.43)
- trees:acer-saccharum -> `eCsxTFBHr7` Acer — genus of plants (cos 0.33)
- trees:acer-saccharum -> `Sq00_BSIlR` sugar acid — class of chemical compounds (cos 0.26)
- trees:acer-pseudoplatanus -> `eCsxTFBHr7` Acer — genus of plants (cos 0.32)
- trees:fraxinus -> `ncw9JsI8Xh` Fraxinus — genus of plants (cos 0.46)
- trees:acer-campestre -> `eCsxTFBHr7` Acer — genus of plants (cos 0.3)
- trees:quercus-acutissima -> `lEbbG9Fo83` Quercus — tree or shrub in the genus Quercus (cos 0.42)
- trees:carpinus-betulus -> `mjR3jQLE8A` European Union — political and economic union of 27 European states (cos 0.28)
- trees:carpinus-betulus -> `KSjj3FgBPh` Eastern Europeans — people from Eastern Europe (cos 0.26)
- trees:acer-ginnala -> `eCsxTFBHr7` Acer — genus of plants (cos 0.34)
- trees:quercus-alba -> `lEbbG9Fo83` Quercus — tree or shrub in the genus Quercus (cos 0.45)
- trees:quercus-robur -> `lEbbG9Fo83` Quercus — tree or shrub in the genus Quercus (cos 0.43)
- trees:quercus-robur -> `Iv1HUK5wgp` English — West Germanic language (cos 0.29)
- trees:ulmus-pumila -> `I0ve1O051w` Ulmus — genus of plants (cos 0.26)
- trees:cornus-florida -> `XvoYmvKxlL` Cornus — genus of plants (cos 0.36)
- trees:cornus-florida -> `Ksd4ldBfYe` florigen — hypothetical plant hormone (cos 0.26)
- trees:quercus-shumardii -> `lEbbG9Fo83` Quercus — tree or shrub in the genus Quercus (cos 0.41)
- trees:quercus-coccinea -> `lEbbG9Fo83` Quercus — tree or shrub in the genus Quercus (cos 0.43)
- trees:quercus-velutina -> `lEbbG9Fo83` Quercus — tree or shrub in the genus Quercus (cos 0.43)
- trees:morus -> `IgAh_x6x1n` Morus — genus of plants (cos 0.49)
- trees:acer-palmatum -> `XuzpCJ807U` Japanese encephalitis — infection of the brain caused by the Japanese encephalitis virus (cos 0.31)
- trees:acer-palmatum -> `eCsxTFBHr7` Acer — genus of plants (cos 0.3)
- trees:fraxinus-americana -> `ncw9JsI8Xh` Fraxinus — genus of plants (cos 0.4)
- trees:juniperus-virginiana -> `Nv_t6_E4iV` Juniperus — genus of plants (cos 0.3)
- trees:juniperus-virginiana -> `yjozXllePq` Virginia — state of the United States of America (cos 0.25)
- trees:ostrya-virginiana -> `yjozXllePq` Virginia — state of the United States of America (cos 0.3)
- trees:ostrya-virginiana -> `Xnp68ezuX6` West Virginia — state of the United States of America (cos 0.27)
- trees:liriodendron-tulipifera -> `CoH67_6M_k` Tulip — genus of plants (cos 0.35)
- trees:quercus-imbricaria -> `lEbbG9Fo83` Quercus — tree or shrub in the genus Quercus (cos 0.41)
- trees:cercidiphyllum-japonicum -> `BZ81n8LuxN` Schistosoma japonicum — species of worm (cos 0.32)
- trees:prunus-serotina -> `nHS-FaTiUM` Prunus — genus of plants (cos 0.39)
- trees:prunus-serotina -> `fbdtRB3oSH` Prunus dulcis — species of plant (cos 0.3)
- trees:betula-nigra -> `qm-IOGc6Qb` Betula — genus of plants (cos 0.45)
- trees:betula-nigra -> `fQMCRiowsQ` Betulaceae — family of plants (cos 0.28)
- trees:betula-papyrifera -> `qm-IOGc6Qb` Betula — genus of plants (cos 0.42)
- trees:betula-papyrifera -> `fQMCRiowsQ` Betulaceae — family of plants (cos 0.27)
- trees:quercus-macrocarpa -> `lEbbG9Fo83` Quercus — tree or shrub in the genus Quercus (cos 0.44)
- trees:cladrastis-kentukea -> `R2SEHYYdBL` Kentucky — U.S. state (cos 0.28)
- trees:syringa-pekinensis -> `qBSsUGZNrI` Syringa — genus of plants (cos 0.33)
- trees:lagerstroemia -> `JjFxeuK6_U` Myrtus — genus of plants (cos 0.36)
- trees:lagerstroemia -> `xU7qdPuysc` Myrtaceae — family of plants (cos 0.31)
- trees:carpinus-japonica -> `XuzpCJ807U` Japanese encephalitis — infection of the brain caused by the Japanese encephalitis virus (cos 0.32)
- trees:carpinus-japonica -> `viOgJC0CLR` Japanese encephalitis virus — species of virus (cos 0.3)
- trees:styrax-japonicus -> `XuzpCJ807U` Japanese encephalitis — infection of the brain caused by the Japanese encephalitis virus (cos 0.33)
- trees:styrax-japonicus -> `viOgJC0CLR` Japanese encephalitis virus — species of virus (cos 0.31)
- trees:chamaecyparis-thyoides -> `PBIZopCmL5` Atlantic Ocean — ocean between Europe, Africa and the Americas (cos 0.25)
- trees:picea-abies -> `kcVqO-8iWb` Picea — genus of evergreen, coniferous tree (cos 0.35)
- trees:picea-abies -> `E0oUp41f7E` Norway — country in northern Europe (cos 0.29)
- trees:crataegus-crusgalli-var-inermis -> `DoatR0rW6X` Crataegus — genus of plants (cos 0.34)
- trees:corylus-colurna -> `4u7Xm3yUlx` Corylus — genus of plants (cos 0.41)
- trees:cornus-kousa -> `XvoYmvKxlL` Cornus — genus of plants (cos 0.39)
- trees:betula-pendula -> `qm-IOGc6Qb` Betula — genus of plants (cos 0.45)
- trees:betula-pendula -> `tjBsmCCSyh` silver stain — Using silver compounds to add colour (cos 0.29)
- trees:juglans-nigra -> `lOmfAsSkOR` Juglans regia — species of plant (cos 0.41)
- trees:pinus -> `pKStqXUX1V` Pinaceae — family of plants (cos 0.34)
- trees:pinus -> `DAbY8JvOZ2` Pinus — genus of plants in the conifer family Pinaceae (cos 0.29)
- trees:salix-babylonica -> `fI23LCtMXY` Salix — genus of plants (cos 0.3)
- trees:cornus-alternifolia -> `XvoYmvKxlL` Cornus — genus of plants (cos 0.36)
- trees:populus-deltoides -> `UIPW08nZnL` census — acquiring and recording information about the members of a given popul (cos 0.25)
- trees:fagus-grandifolia -> `rNnYtdwa5W` Fagus — genus of plants (cos 0.29)
- trees:halesia-diptera -> `CxncAurUvt` Diptera — order of insects (cos 0.26)
- trees:acer-griseum -> `eCsxTFBHr7` Acer — genus of plants (cos 0.31)
- trees:cercis-reniformis -> `nCHBAiQz17` Oklahoma — state of the United States of America (cos 0.25)
- trees:picea -> `kcVqO-8iWb` Picea — genus of evergreen, coniferous tree (cos 0.41)
- trees:picea -> `UIPW08nZnL` census — acquiring and recording information about the members of a given popul (cos 0.25)
- trees:pinus-strobus -> `pKStqXUX1V` Pinaceae — family of plants (cos 0.28)
- trees:sassafras-albidum -> `ve4hrqnR7T` Sassafras — genus of plants (cos 0.57)
- trees:acer-tataricum -> `eCsxTFBHr7` Acer — genus of plants (cos 0.31)
- trees:acer-tataricum -> `Q-tKZDDJE2` racemic acid — racemic mixture of tartaric acid (cos 0.26)
- trees:ilex -> `icxaVWN-wB` Ilex — genus of plants (cos 0.45)
- trees:ilex -> `UIPW08nZnL` census — acquiring and recording information about the members of a given popul (cos 0.25)
- trees:magnolia-grandiflora -> `CFJ9yt4_st` South Asia — southern region of Asia (cos 0.28)
- trees:picea-pungens -> `kcVqO-8iWb` Picea — genus of evergreen, coniferous tree (cos 0.37)
- trees:fagus-sylvatica -> `mjR3jQLE8A` European Union — political and economic union of 27 European states (cos 0.3)
- trees:fagus-sylvatica -> `rNnYtdwa5W` Fagus — genus of plants (cos 0.29)
- trees:acer-nigrum -> `eCsxTFBHr7` Acer — genus of plants (cos 0.34)
- trees:acer-buergerianum -> `eCsxTFBHr7` Acer — genus of plants (cos 0.31)
- trees:pinus-resinosa -> `pKStqXUX1V` Pinaceae — family of plants (cos 0.29)
- trees:pinus-resinosa -> `DAbY8JvOZ2` Pinus — genus of plants in the conifer family Pinaceae (cos 0.25)
- trees:populus-grandidentata -> `vlpDKQT5tf` Populus — genus of plants (cos 0.3)
- trees:populus-grandidentata -> `UIPW08nZnL` census — acquiring and recording information about the members of a given popul (cos 0.28)
- trees:tsuga-canadensis -> `CESOt8mkBD` Conium maculatum — species of plant (cos 0.34)
- trees:tsuga-canadensis -> `0ordlTAftm` Tsuga — genus of plants (cos 0.29)
- trees:cedrus-atlantica -> `rq0dhNY1eU` Cedrus — genus of plants (cos 0.46)
- trees:cedrus-atlantica -> `PBIZopCmL5` Atlantic Ocean — ocean between Europe, Africa and the Americas (cos 0.33)
- trees:pseudotsuga-menziesii -> `YuefcZ_6oF` Pseudotsuga — genus of conifers in the family Pinaceae (cos 0.33)
- trees:pseudotsuga-menziesii -> `0ordlTAftm` Tsuga — genus of plants (cos 0.25)
- trees:populus-tremuloides -> `vlpDKQT5tf` Populus — genus of plants (cos 0.3)
- trees:populus-tremuloides -> `UIPW08nZnL` census — acquiring and recording information about the members of a given popul (cos 0.28)
- trees:quercus-falcata -> `lEbbG9Fo83` Quercus — tree or shrub in the genus Quercus (cos 0.44)
- trees:quercus-falcata -> `CFJ9yt4_st` South Asia — southern region of Asia (cos 0.32)
- trees:aesculus-glabra -> `jWVDN1FFk5` Ohio — state of the United States of America (cos 0.27)
- trees:cedrus-deodara -> `rq0dhNY1eU` Cedrus — genus of plants (cos 0.47)
- trees:acer-truncatum -> `eCsxTFBHr7` Acer — genus of plants (cos 0.33)
- trees:alnus-glutinosa -> `JFa45TbJ5g` Alnus — genus of plants (cos 0.33)
- trees:alnus-glutinosa -> `mjR3jQLE8A` European Union — political and economic union of 27 European states (cos 0.3)
- trees:pinus-nigra -> `pKStqXUX1V` Pinaceae — family of plants (cos 0.3)
- trees:pinus-nigra -> `DAbY8JvOZ2` Pinus — genus of plants in the conifer family Pinaceae (cos 0.26)
- trees:pinus-rigida -> `pKStqXUX1V` Pinaceae — family of plants (cos 0.3)
- trees:pinus-rigida -> `DAbY8JvOZ2` Pinus — genus of plants in the conifer family Pinaceae (cos 0.26)
- trees:maclura-pomifera -> `0KHU4SABvx` Maclura — genus of plants (cos 0.25)
- trees:pinus-sylvestris -> `pKStqXUX1V` Pinaceae — family of plants (cos 0.28)
- trees:pinus-virginiana -> `yjozXllePq` Virginia — state of the United States of America (cos 0.45)
- trees:pinus-virginiana -> `Xnp68ezuX6` West Virginia — state of the United States of America (cos 0.39)