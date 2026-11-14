# Batch 1/2 — EHDP challenge measures vs SPG concepts

For every NYC row below, decide whether an SPG concept maps to it.
Match types: `equivalent` (same construct), `broader-narrower` (construct covers the
measure or vice versa — e.g. 'asthma' vs 'Asthma ED visits, Number'), `related-component`
(same topic, different construct — e.g. 'heat wave' vs 'Heat ED visits'), `no-match`.
Confidence: high / medium / low. Do NOT write no-match rows — every NYC id absent from
your output is treated as no-match. Only emit rows with a match.
SPG concepts here are the 473 challenge-domain ones; the supplement lists add lexical
candidates from the wider 45,721-concept set (outside the 473). You may also name any
other SPG concept you believe exists — only supplement-listed and table-listed ids are
guaranteed real.

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


## NYC family: Commercial insecticide use  (9 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:966 | Commercial insecticide use, Best practice products | Best practice products | Pest control services provided by a professional exterminator in the individual' | Sum of pounds (lb) of solid pesticide applications that meet | Housing & indoor | 1999-2022 |
| ehdp:measure:959 | Commercial insecticide use, Pyrethroid/pyrethrin liquids | Pyrethroid/pyrethrin liquids | Pest control services provided by a professional exterminator in the individual' | Sum of gallons (gal) of liquid pesticide applications that m | Housing & indoor | 1999-2022 |
| ehdp:measure:958 | Commercial insecticide use, Organophosphate solids | Organophosphate solids | Pest control services provided by a professional exterminator in the individual' | Sum of pounds (lb) of solid pesticide applications that meet | Housing & indoor | 1999-2022 |
| ehdp:measure:957 | Commercial insecticide use, Organophosphate liquids | Organophosphate liquids | Pest control services provided by a professional exterminator in the individual' | Sum of gallons (gal) of liquid pesticide applications that m | Housing & indoor | 1999-2022 |
| ehdp:measure:956 | Commercial insecticide use, Carbamate solids | Carbamate solids | Pest control services provided by a professional exterminator in the individual' | Sum of pounds (lb) of solid pesticide applications that meet | Housing & indoor | 1999-2022 |
| ehdp:measure:955 | Commercial insecticide use, Carbamate liquids | Carbamate liquids | Pest control services provided by a professional exterminator in the individual' | Sum of gallons (gal) of liquid pesticide applications that m | Housing & indoor | 1999-2022 |
| ehdp:measure:953 | Commercial insecticide use, All liquids | All liquids | Pest control services provided by a professional exterminator in the individual' | Sum of gallons (gal) of liquid pesticide applications that m | Housing & indoor | 1999-2022 |
| ehdp:measure:954 | Commercial insecticide use, All solids | All solids | Pest control services provided by a professional exterminator in the individual' | Sum of pounds (lb) of solid pesticide applications that meet | Housing & indoor | 1999-2022 |
| ehdp:measure:960 | Commercial insecticide use, Pyrethroid/pyrethrin solids | Pyrethroid/pyrethrin solids | Pest control services provided by a professional exterminator in the individual' | Sum of pounds (lb) of solid pesticide applications that meet | Housing & indoor | 1999-2022 |

Supplement candidates (wider SPG, not in table above):
- `W3DRcIxD47` insecticide — pesticide used against insects (cos 0.59)
- `AG5EdenPcm` insecticide resistance — development by insects of resistance to insecticides (cos 0.49)
- `Go5d1nTk86` Catalogs, Commercial —  (cos 0.46)

## NYC family: NYC agency use of insecticides  (9 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:1153 | NYC agency use of insecticides, DOE (liquids) | DOE (liquids) | Pesticides targeting insects, applied by NYC agency-contracted exterminators or  | Sum of gallons of liquid pesticide applications made by the  | Housing & indoor | 2008-2023 |
| ehdp:measure:1154 | NYC agency use of insecticides, DOE (solids) | DOE (solids) | Pesticides targeting insects, applied by NYC agency-contracted exterminators or  | Sum of pounds of solid pesticide applications made by the De | Housing & indoor | 2008-2023 |
| ehdp:measure:1156 | NYC agency use of insecticides, NYCHA (liquids) | NYCHA (liquids) | Pesticides targeting insects, applied by NYC agency-contracted exterminators or  | Sum of gallons of liquid pesticide applications made by the  | Housing & indoor | 2008-2023 |
| ehdp:measure:1157 | NYC agency use of insecticides, NYCHA (solids) | NYCHA (solids) | Pesticides targeting insects, applied by NYC agency-contracted exterminators or  | Sum of pounds of solid pesticide applications made by the NY | Housing & indoor | 2008-2023 |
| ehdp:measure:1148 | NYC agency use of insecticides, All agency application count | All agency application count | Pesticides targeting insects, applied by NYC agency-contracted exterminators or  | Total count of pesticide applications made by NYC agencies o | Housing & indoor | 2008-2023 |
| ehdp:measure:1150 | NYC agency use of insecticides, All agency (liquids) | All agency (liquids) | Pesticides targeting insects, applied by NYC agency-contracted exterminators or  | Sum of gallons of liquid pesticide applications made by NYC  | Housing & indoor | 2008-2023 |
| ehdp:measure:1151 | NYC agency use of insecticides, All agency (solids) | All agency (solids) | Pesticides targeting insects, applied by NYC agency-contracted exterminators or  | Sum of pounds of solid pesticide applications made by NYC ag | Housing & indoor | 2008-2023 |
| ehdp:measure:1152 | NYC agency use of insecticides, DOE application count | DOE application count | Pesticides targeting insects, applied by NYC agency-contracted exterminators or  | Total count of pesticide applications made by the Department | Housing & indoor | 2008-2023 |
| ehdp:measure:1155 | NYC agency use of insecticides, NYCHA application count | NYCHA application count | Pesticides targeting insects, applied by NYC agency-contracted exterminators or  | Total count of pesticide applications made by the NYC Housin | Housing & indoor | 2008-2023 |

Supplement candidates (wider SPG, not in table above):
- `W3DRcIxD47` insecticide — pesticide used against insects (cos 0.64)
- `AG5EdenPcm` insecticide resistance — development by insects of resistance to insecticides (cos 0.55)
- `qODaxGmiJk` insecticide-treated bednet — meshwork fabric impregnated with insecticide, having openings too smal (cos 0.35)

## NYC family: NYC agency use of fungicides  (9 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:1118 | NYC agency use of fungicides, All agency application count | All agency application count | Pesticides targeting fungus such as mold or plant blight, applied by NYC agency- | Total count of pesticide applications made by NYC agencies o | Housing & indoor | 2008-2023 |
| ehdp:measure:1119 | NYC agency use of fungicides, All agency (liquids) | All agency (liquids) | Pesticides targeting fungus such as mold or plant blight, applied by NYC agency- | Sum of gallons of liquid pesticide applications made by NYC  | Housing & indoor | 2008-2023 |
| ehdp:measure:1124 | NYC agency use of fungicides, Golf course application count | Golf course application count | Pesticides targeting fungus such as mold or plant blight, applied by NYC agency- | Total count of pesticide applications made on NYC public gol | Housing & indoor | 2008-2023 |
| ehdp:measure:1125 | NYC agency use of fungicides, Golf course (liquids) | Golf course (liquids) | Pesticides targeting fungus such as mold or plant blight, applied by NYC agency- | Sum of gallons of liquid pesticide applications made on NYC  | Housing & indoor | 2008-2023 |
| ehdp:measure:1120 | NYC agency use of fungicides, All agency (solids) | All agency (solids) | Pesticides targeting fungus such as mold or plant blight, applied by NYC agency- | Sum of pounds of solid pesticide applications made by NYC ag | Housing & indoor | 2008-2023 |
| ehdp:measure:1121 | NYC agency use of fungicides, Parks application count | Parks application count | Pesticides targeting fungus such as mold or plant blight, applied by NYC agency- | Total count of pesticide applications made by the Departmant | Housing & indoor | 2008-2023 |
| ehdp:measure:1122 | NYC agency use of fungicides, Parks (liquids) | Parks (liquids) | Pesticides targeting fungus such as mold or plant blight, applied by NYC agency- | Sum of gallons of liquid pesticide applications made by the  | Housing & indoor | 2008-2023 |
| ehdp:measure:1126 | NYC agency use of fungicides, Golf course (solids) | Golf course (solids) | Pesticides targeting fungus such as mold or plant blight, applied by NYC agency- | Sum of pounds of solid pesticide applications made on NYC pu | Housing & indoor | 2008-2023 |
| ehdp:measure:1123 | NYC agency use of fungicides, Parks (solids) | Parks (solids) | Pesticides targeting fungus such as mold or plant blight, applied by NYC agency- | Sum of pounds of solid pesticide applications made by the De | Housing & indoor | 2008-2023 |

Supplement candidates (wider SPG, not in table above):
- `TBsyBcNA1b` fungicide — pesticide used to kill fungi (cos 0.64)
- `XGryu0RaQ9` industrial fungicides — chemicals that kill or inhibit the growth of fungi in agricultural, in (cos 0.43)
- `of3Jfb6LlS` antifungal — pharmaceutical or chemical fungicide or fungistatic used to treat and  (cos 0.4)

## NYC family: NYC agency use of herbicides  (9 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:1139 | NYC agency use of herbicides, All agency application count | All agency application count | Pesticides targeting unwanted weeds, grasses, vines and trees, applied by NYC ag | Total count of pesticide applications made by NYC agencies o | Housing & indoor;Green & built | 2008-2023 |
| ehdp:measure:1140 | NYC agency use of herbicides, All agency (liquids) | All agency (liquids) | Pesticides targeting unwanted weeds, grasses, vines and trees, applied by NYC ag | Sum of gallons of liquid pesticide applications made by NYC  | Housing & indoor;Green & built | 2008-2023 |
| ehdp:measure:1141 | NYC agency use of herbicides, All agency (solids) | All agency (solids) | Pesticides targeting unwanted weeds, grasses, vines and trees, applied by NYC ag | Sum of pounds of solid pesticide applications made by NYC ag | Housing & indoor;Green & built | 2008-2023 |
| ehdp:measure:1142 | NYC agency use of herbicides, Parks application count | Parks application count | Pesticides targeting unwanted weeds, grasses, vines and trees, applied by NYC ag | Total count of pesticide applications made by the Departmant | Housing & indoor;Green & built | 2008-2023 |
| ehdp:measure:1143 | NYC agency use of herbicides, Parks (liquids) | Parks (liquids) | Pesticides targeting unwanted weeds, grasses, vines and trees, applied by NYC ag | Sum of gallons of liquid pesticide applications made by the  | Housing & indoor;Green & built | 2008-2023 |
| ehdp:measure:1144 | NYC agency use of herbicides, Parks (solids) | Parks (solids) | Pesticides targeting unwanted weeds, grasses, vines and trees, applied by NYC ag | Sum of pounds of solid pesticide applications made by the De | Housing & indoor;Green & built | 2008-2023 |
| ehdp:measure:1145 | NYC agency use of herbicides, Golf course application count | Golf course application count | Pesticides targeting unwanted weeds, grasses, vines and trees, applied by NYC ag | Total count of pesticide applications made on NYC public gol | Housing & indoor;Green & built | 2008-2023 |
| ehdp:measure:1146 | NYC agency use of herbicides, Golf course (liquids) | Golf course (liquids) | Pesticides targeting unwanted weeds, grasses, vines and trees, applied by NYC ag | Sum of gallons of liquid pesticide applications made on NYC  | Housing & indoor;Green & built | 2008-2023 |
| ehdp:measure:1147 | NYC agency use of herbicides, Golf course (solids) | Golf course (solids) | Pesticides targeting unwanted weeds, grasses, vines and trees, applied by NYC ag | Sum of pounds of solid pesticide applications made on NYC pu | Housing & indoor;Green & built | 2008-2023 |

Supplement candidates (wider SPG, not in table above):
- `RsRHLzVNE9` herbicide — chemical used to kill unwanted plants (cos 0.62)
- `xLtZvaVlIi` diquat — ion, active substance of a herbicide (cos 0.46)
- `0zSSEilYig` Defoliants, Chemical — Herbicides that remove leaves from trees and growing plants. They may  (cos 0.26)

## NYC family: Disinfection by-products (TTHM)  (8 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:862 | Disinfection by-products (TTHM), Quarterly average concentration | Quarterly average concentration | Concentration of TTHM in drinking water. Disinfection by-products form when a di | Samples are collected from the drinking water distribution s | Housing & indoor | 1999-2023 |
| ehdp:measure:863 | Disinfection by-products (TTHM), Quarterly maximum concentration | Quarterly maximum concentration | Concentration of TTHM in drinking water. Disinfection by-products form when a di | Samples are collected from the drinking water distribution s | Housing & indoor | 1999-2023 |
| ehdp:measure:861 | Disinfection by-products (TTHM), Qtr maximum allowable contaminant level (MCL) | Qtr maximum allowable contaminant level (MCL) | Concentration of TTHM in drinking water. Disinfection by-products form when a di | The highest level of TTHM that is allowed in drinking water  | Housing & indoor | 1999-2021 |
| ehdp:measure:866 | Disinfection by-products (TTHM), Number (samples) | Number (samples) | Concentration of TTHM in drinking water. Disinfection by-products form when a di | The number of total trihalomethanes (TTHM) samples taken thr | Housing & indoor | 1999-2023 |
| ehdp:measure:865 | Disinfection by-products (TTHM), Maximum concentration | Maximum concentration | Concentration of TTHM in drinking water. Disinfection by-products form when a di | Samples are collected from the drinking water distribution s | Housing & indoor | 1999-2023 |
| ehdp:measure:867 | Disinfection by-products (TTHM), Annual average concentration | Annual average concentration | Concentration of TTHM in drinking water. Disinfection by-products form when a di | Samples are collected from the drinking water distribution s | Housing & indoor | 1999-2023 |
| ehdp:measure:868 | Disinfection by-products (TTHM), Number (sample locations) | Number (sample locations) | Concentration of TTHM in drinking water. Disinfection by-products form when a di | The number of total trihalomethanes (TTHM) samples taken thr | Housing & indoor | 1999-2023 |
| ehdp:measure:864 | Disinfection by-products (TTHM), Maximum allowable contaminant level (MCL) | Maximum allowable contaminant level (MCL) | Concentration of TTHM in drinking water. Disinfection by-products form when a di | The highest level of total trihalomethanes (TTHM) that is al | Housing & indoor | 1999-2021 |

Supplement candidates (wider SPG, not in table above):
- `OFf_hr91iP` reproductive tract infection — infection of the genital tract (cos 0.32)
- `BRm9tt6jy4` hand disinfection — cleansing the hands to destroy infectious microorganism (cos 0.3)
- `DUv5LOi5fD` urine — liquid by-product of metabolism in the bodies of many animals, produce (cos 0.3)

## NYC family: Disinfection by-products (HAA5)  (8 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:858 | Disinfection by-products (HAA5), Quarterly maximum concentration | Quarterly maximum concentration | Concentration of total trihalomethane in drinking water. Disinfection by-product | Samples are collected from the drinking water distribution s | Housing & indoor | 2017-2023 |
| ehdp:measure:860 | Disinfection by-products (HAA5), Quarterly average concentration | Quarterly average concentration | Concentration of total trihalomethane in drinking water. Disinfection by-product | Samples are collected from the drinking water distribution s | Housing & indoor | 2017-2023 |
| ehdp:measure:433 | Disinfection by-products (HAA5), Number (samples) | Number (samples) | Concentration of total trihalomethane in drinking water. Disinfection by-product | The number of total haloacetic acids (five) (HAA5) samples t | Housing & indoor | 1999-2023 |
| ehdp:measure:434 | Disinfection by-products (HAA5), Number (sample locations) | Number (sample locations) | Concentration of total trihalomethane in drinking water. Disinfection by-product | Number of sampling total haloacetic acids (five) (HAA5) loca | Housing & indoor | 1999-2023 |
| ehdp:measure:432 | Disinfection by-products (HAA5), Maximum concentration | Maximum concentration | Concentration of total trihalomethane in drinking water. Disinfection by-product | Samples are collected from the drinking water distribution s | Housing & indoor | 1999-2023 |
| ehdp:measure:431 | Disinfection by-products (HAA5), Annual average concentration | Annual average concentration | Concentration of total trihalomethane in drinking water. Disinfection by-product | Samples are collected from the drinking water distribution s | Housing & indoor | 1999-2023 |
| ehdp:measure:529 | Disinfection by-products (HAA5), Maximum allowable contaminant level (MCL) | Maximum allowable contaminant level (MCL) | Concentration of total trihalomethane in drinking water. Disinfection by-product | The highest level of total haloacetic acids (five) (HAA5) th | Housing & indoor | 1999-2021 |
| ehdp:measure:859 | Disinfection by-products (HAA5), Qtr maximum allowable contaminant level (MCL) | Qtr maximum allowable contaminant level (MCL) | Concentration of total trihalomethane in drinking water. Disinfection by-product | The highest level of total haloacetic acids (five) (HAA5) th | Housing & indoor | 2017-2021 |

Supplement candidates (wider SPG, not in table above):
- `OFf_hr91iP` reproductive tract infection — infection of the genital tract (cos 0.3)
- `BRm9tt6jy4` hand disinfection — cleansing the hands to destroy infectious microorganism (cos 0.29)
- `DUv5LOi5fD` urine — liquid by-product of metabolism in the bodies of many animals, produce (cos 0.28)

## NYC family: Race/ethnicity  (6 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:989 | Race/ethnicity, Hispanic alone (percent) | Hispanic alone (percent) | Population by Census race/ethnicity category. Past and present structural racism | Estimated Percent Hispanic | Housing & indoor;Social & economic | 2007-2017 |
| ehdp:measure:990 | Race/ethnicity, White alone (percent) | White alone (percent) | Population by Census race/ethnicity category. Past and present structural racism | Estimated Percent White | Housing & indoor;Social & economic | 2007-2017 |
| ehdp:measure:1192 | Race/ethnicity, Non-white (percent) | Non-white (percent) | Population by Census race/ethnicity category. Past and present structural racism | Estiamted percent of people who are not White. | Housing & indoor;Social & economic | 2007-2017 |
| ehdp:measure:987 | Race/ethnicity, Asian alone (percent) | Asian alone (percent) | Population by Census race/ethnicity category. Past and present structural racism | Estimated percent of people who are only Asian. | Housing & indoor;Social & economic | 2007-2017 |
| ehdp:measure:988 | Race/ethnicity, Black alone (percent) | Black alone (percent) | Population by Census race/ethnicity category. Past and present structural racism | Estimated percent of people who are only Black. | Housing & indoor;Social & economic | 2007-2017 |
| ehdp:measure:992 | Race/ethnicity, Total population | Total population | Population by Census race/ethnicity category. Past and present structural racism | Estimated total population. | Housing & indoor;Social & economic | 2007-2017 |

Supplement candidates (wider SPG, not in table above):
- `0p4AO5M1ph` racism — race or ethnic-based discrimination (cos 0.35)
- `PxWsf7d5Ds` minority group — group of people by practices, race, religion, ethnicity, or other char (cos 0.26)

## NYC family: Asthma hospitalizations (adults)  (6 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:1202 | Asthma hospitalizations (adults), Number | Number | Hospitalizations for asthma. These more severe asthma outcomes are often cluster | Number of asthma-related hospitalizations among NYC resident | Asthma & respiratory;Housing & indoor;Social & economic | 2005-2023 |
| ehdp:measure:1204 | Asthma hospitalizations (adults), Age-adjusted rate | Age-adjusted rate | Hospitalizations for asthma. These more severe asthma outcomes are often cluster | Number of asthma-related hospitalizations among NYC resident | Asthma & respiratory;Housing & indoor;Social & economic | 2005-2023 |
| ehdp:measure:1203 | Asthma hospitalizations (adults), Estimated annual rate | Estimated annual rate | Hospitalizations for asthma. These more severe asthma outcomes are often cluster | Number of asthma-related hospitalizations among NYC resident | Asthma & respiratory;Housing & indoor;Social & economic | 2005-2023 |
| ehdp:measure:1215 | Asthma hospitalizations (adults), by NTA, Average annual rate | Average annual rate | Hospitalizations for asthma. These more severe asthma outcomes are often cluster | Average annual number of asthma-related hospitalizations amo | Asthma & respiratory;Housing & indoor;Social & economic | 2012-2012 |
| ehdp:measure:1216 | Asthma hospitalizations (adults), by NTA, Average annual age-adjusted rate | Average annual age-adjusted rate | Hospitalizations for asthma. These more severe asthma outcomes are often cluster | Average annual number of asthma-related hospitalizations amo | Asthma & respiratory;Housing & indoor;Social & economic | 2012-2012 |
| ehdp:measure:1220 | Asthma hospitalizations (adults), by NTA, Average annual number | Average annual number | Hospitalizations for asthma. These more severe asthma outcomes are often cluster | Average annual number of asthma-related hospitalizations amo | Asthma & respiratory;Housing & indoor;Social & economic | 2012-2012 |

Supplement candidates (wider SPG, not in table above):
- `Jx2R43aZ7W` status asthmaticus — type of asthma (cos 0.37)
- `M6F-TJO4S3` hospitalized child — child hospitalized for short term care (cos 0.37)
- `HqtWmsegwf` rural hospital — hospital (cos 0.35)

## NYC family: Heat hospitalizations  (6 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:538 | Heat hospitalizations, Number | Number | Hospitalizations due to heat stress. These are part of the public health burden  | The number of NYC residents admitted to a NYC hospital durin | Heat & temperature | 2000-2022 |
| ehdp:measure:539 | Heat hospitalizations, Estimated annual rate | Estimated annual rate | Hospitalizations due to heat stress. These are part of the public health burden  | The number of NYC residents admitted to a NYC hospital durin | Heat & temperature | 2000-2022 |
| ehdp:measure:540 | Heat hospitalizations, Age-adjusted rate | Age-adjusted rate | Hospitalizations due to heat stress. These are part of the public health burden  | The number of NYC residents admitted to a NYC hospital durin | Heat & temperature | 2000-2022 |
| ehdp:measure:1285 | Heat hospitalizations, Number | Number | Hospitalizations due to hot weather. These are part of the public health burden  | The number of NYC residents admitted to a NYC hospital durin | Heat & temperature | 2013-2013 |
| ehdp:measure:1284 | Heat hospitalizations, Average annual rate | Average annual rate | Hospitalizations due to hot weather. These are part of the public health burden  | The number of NYC residents admitted to a NYC hospital durin | Heat & temperature | 2013-2013 |
| ehdp:measure:1283 | Heat hospitalizations, Average annual age-adjusted rate | Average annual age-adjusted rate | Hospitalizations due to hot weather. These are part of the public health burden  | The number of NYC residents admitted to a NYC hospital durin | Heat & temperature | 2013-2013 |

Supplement candidates (wider SPG, not in table above):
- `M6F-TJO4S3` hospitalized child — child hospitalized for short term care (cos 0.51)
- `HqtWmsegwf` rural hospital — hospital (cos 0.49)
- `kCxzkek5LN` State hospital —  (cos 0.47)

## NYC family: Secondhand smoke (from outside)  (6 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:1035 | Secondhand smoke (from outside), Never (number) | Never (number) | Adults reporting secondhand smoke at home, from outside sources. Secondhand smok | Estimated number of people who reported never smelling cigar | Housing & indoor | 2013-2017 |
| ehdp:measure:1033 | Secondhand smoke (from outside), Everyday (number) | Everyday (number) | Adults reporting secondhand smoke at home, from outside sources. Secondhand smok | Estimated number of people who reported smelling cigarette s | Housing & indoor | 2013-2017 |
| ehdp:measure:1038 | Secondhand smoke (from outside), Sometimes (percent) | Sometimes (percent) | Adults reporting secondhand smoke at home, from outside sources. Secondhand smok | Estimated number of people who reported sometimes smelling c | Housing & indoor | 2013-2017 |
| ehdp:measure:1037 | Secondhand smoke (from outside), Sometimes (number) | Sometimes (number) | Adults reporting secondhand smoke at home, from outside sources. Secondhand smok | Estimated number of people who reported sometimes smelling c | Housing & indoor | 2013-2017 |
| ehdp:measure:1036 | Secondhand smoke (from outside), Never (percent) | Never (percent) | Adults reporting secondhand smoke at home, from outside sources. Secondhand smok | Estimated number of people who reported never smelling cigar | Housing & indoor | 2013-2017 |
| ehdp:measure:1034 | Secondhand smoke (from outside), Everyday (percent) | Everyday (percent) | Adults reporting secondhand smoke at home, from outside sources. Secondhand smok | Estimated number of people who reported smelling cigarette s | Housing & indoor | 2013-2017 |

Supplement candidates (wider SPG, not in table above):
- `PDDW6UukdU` smoker — person who smokes (cos 0.29)
- `qsn9G63cwk` tobacco smoke pollution — contamination of the air by tobacco smoke (cos 0.25)
- `Bgy96PVCs9` tobacco smoke — aerosol produced by the incomplete combustion of tobacco (cos 0.24)

## NYC family: Carbon monoxide hospitalizations  (6 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:1268 | Carbon monoxide hospitalizations, Number (not fire-related) | Number (not fire-related) | Hospitalizations s due to carbon monoxide. Carbon monoxide (CO) exposure can be  | The number of NYC residents hospitalized. Prior to October 1 | Air quality | 2000-2018 |
| ehdp:measure:1271 | Carbon monoxide hospitalizations, Rate | Rate | Hospitalizations s due to carbon monoxide. Carbon monoxide (CO) exposure can be  | The number of NYC residents treated in an emergency departme | Air quality | 2000-2018 |
| ehdp:measure:1270 | Carbon monoxide hospitalizations, Number | Number | Hospitalizations s due to carbon monoxide. Carbon monoxide (CO) exposure can be  | The number of NYC residents hospitalized. Prior to October 1 | Air quality | 2000-2018 |
| ehdp:measure:1269 | Carbon monoxide hospitalizations, Rate (not fire-related) | Rate (not fire-related) | Hospitalizations s due to carbon monoxide. Carbon monoxide (CO) exposure can be  | The number of NYC residents hospitalized. Prior to October 1 | Air quality | 2000-2018 |
| ehdp:measure:1267 | Carbon monoxide hospitalizations, Number (fire-related) | Number (fire-related) | Hospitalizations s due to carbon monoxide. Carbon monoxide (CO) exposure can be  | The number of NYC residents hospitalized. Prior to October 1 | Air quality | 2000-2018 |
| ehdp:measure:1266 | Carbon monoxide hospitalizations, Rate (fire-related) | Rate (fire-related) | Hospitalizations s due to carbon monoxide. Carbon monoxide (CO) exposure can be  | The number of NYC residents hospitalized. Prior to October 1 | Air quality | 2000-2018 |

Supplement candidates (wider SPG, not in table above):
- `M6F-TJO4S3` hospitalized child — child hospitalized for short term care (cos 0.41)
- `HqtWmsegwf` rural hospital — hospital (cos 0.38)
- `kCxzkek5LN` State hospital —  (cos 0.37)

## NYC family: Carbon monoxide emergency department visits  (6 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:1265 | Carbon monoxide emergency department visits, Rate | Rate | Emergency department visits due to carbon monoxide. Carbon monoxide (CO) exposur | The number of NYC residents treated in an emergency departme | Air quality | 2005-2018 |
| ehdp:measure:1260 | Carbon monoxide emergency department visits, Number (fire-related) | Number (fire-related) | Emergency department visits due to carbon monoxide. Carbon monoxide (CO) exposur | The number of NYC residents treated in an emergency departme | Air quality | 2005-2018 |
| ehdp:measure:1261 | Carbon monoxide emergency department visits, Rate (fire-related) | Rate (fire-related) | Emergency department visits due to carbon monoxide. Carbon monoxide (CO) exposur | The number of NYC residents treated in an emergency departme | Air quality | 2005-2018 |
| ehdp:measure:1262 | Carbon monoxide emergency department visits, Number (not fire-related) | Number (not fire-related) | Emergency department visits due to carbon monoxide. Carbon monoxide (CO) exposur | The number of NYC residents treated in an emergency departme | Air quality | 2005-2018 |
| ehdp:measure:1263 | Carbon monoxide emergency department visits, Rate (not fire-related) | Rate (not fire-related) | Emergency department visits due to carbon monoxide. Carbon monoxide (CO) exposur | The number of NYC residents treated in an emergency departme | Air quality | 2005-2018 |
| ehdp:measure:1264 | Carbon monoxide emergency department visits, Number | Number | Emergency department visits due to carbon monoxide. Carbon monoxide (CO) exposur | The number of NYC residents treated in an emergency departme | Air quality | 2005-2018 |

Supplement candidates (wider SPG, not in table above):
- `cExGz1bOoS` Emergency Treatment —  (cos 0.45)
- `yy20Kl8PjT` pediatric emergency medicine — branch of emergency medicine dealing with the emergency care of childr (cos 0.32)
- `mHe_Y_w5EU` emergency medicine — medical specialty concerned with care for patients who require immedia (cos 0.3)

## NYC family: Personal pesticide use  (6 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:936 | Personal pesticide use, Percent (Spray/Bomb only) | Percent (Spray/Bomb only) | Adults reporting pesticide use in the home. This does not include pesticide appl | Estimated number of adults who reported using any ineffectiv | Housing & indoor | 2015-2015 |
| ehdp:measure:940 | Personal pesticide use, Percent (Safer methods only) | Percent (Safer methods only) | Adults reporting pesticide use in the home. This does not include pesticide appl | Estimated number of adults who reported using only safe meth | Housing & indoor | 2015-2015 |
| ehdp:measure:942 | Personal pesticide use, Percent (any use) | Percent (any use) | Adults reporting pesticide use in the home. This does not include pesticide appl | Estimated number of adults who reported using any pesticide  | Housing & indoor | 2015-2015 |
| ehdp:measure:934 | Personal pesticide use, Percent (Tempo or Chinese Chalk) | Percent (Tempo or Chinese Chalk) | Adults reporting pesticide use in the home. This does not include pesticide appl | Estimated number of adults who reported using any illegal me | Housing & indoor | 2015-2015 |
| ehdp:measure:939 | Personal pesticide use, Number (Safer methods only) | Number (Safer methods only) | Adults reporting pesticide use in the home. This does not include pesticide appl | Estimated number of adults who reported using only safe meth | Housing & indoor | 2015-2015 |
| ehdp:measure:941 | Personal pesticide use, Number (any use) | Number (any use) | Adults reporting pesticide use in the home. This does not include pesticide appl | Estimated number of adults who reported using any pesticide  | Housing & indoor | 2015-2015 |

Supplement candidates (wider SPG, not in table above):
- `z5gUrT2Y3H` pesticide — substance used to destroy pests (cos 0.6)
- `ENKCyVKtaU` pesticide residue — pesticide applied to food crops remaining on or in food (cos 0.51)
- `NaqXdIgUsj` pesticide poisoning — poisoning of humans from pesticide exposure (cos 0.51)

## NYC family: NYC agency use of rodenticides  (6 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:1158 | NYC agency use of rodenticides, All agency application count | All agency application count | Pesticides targeting rats and mice, applied by NYC agency-contracted exterminato | Total count of pesticide applications made by NYC agencies o | Housing & indoor | 2008-2023 |
| ehdp:measure:1159 | NYC agency use of rodenticides, All agency (solids) | All agency (solids) | Pesticides targeting rats and mice, applied by NYC agency-contracted exterminato | Sum of pounds of solid pesticide applications made by NYC ag | Housing & indoor | 2008-2023 |
| ehdp:measure:1162 | NYC agency use of rodenticides, DOHMH application count | DOHMH application count | Pesticides targeting rats and mice, applied by NYC agency-contracted exterminato | Total count of pesticide applications made by the Department | Housing & indoor | 2008-2023 |
| ehdp:measure:1160 | NYC agency use of rodenticides, DOE application count | DOE application count | Pesticides targeting rats and mice, applied by NYC agency-contracted exterminato | Total count of pesticide applications made by the Department | Housing & indoor | 2008-2023 |
| ehdp:measure:1163 | NYC agency use of rodenticides, DOHMH (solids) | DOHMH (solids) | Pesticides targeting rats and mice, applied by NYC agency-contracted exterminato | Sum of pounds of solid pesticide applications made by the De | Housing & indoor | 2008-2023 |
| ehdp:measure:1161 | NYC agency use of rodenticides, DOE (solids) | DOE (solids) | Pesticides targeting rats and mice, applied by NYC agency-contracted exterminato | Sum of pounds of solid pesticide applications made by the De | Housing & indoor | 2008-2023 |

Supplement candidates (wider SPG, not in table above):
- `ilXDKtVKMy` rodenticide — chemicals selected for killing rodents (cos 0.59)
- `zZkCL2jHfh` Rodentia — order of mammals (cos 0.42)
- `cbmie_ypX1` rodent disease — diseases of rodents of the order Rodentia (cos 0.39)

## NYC family: NYC agency use of "Best Practice" products  (6 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:1132 | NYC agency use of "Best Practice" products, DOE (solids) | DOE (solids) | Pesticides targeting insects that are effective, but have low toxicity or low po | Sum of pounds of solid pesticide applications made by the De | Housing & indoor | 2008-2023 |
| ehdp:measure:1134 | NYC agency use of "Best Practice" products, NYCHA (solids) | NYCHA (solids) | Pesticides targeting insects that are effective, but have low toxicity or low po | Sum of pounds of solid pesticide applications made by the NY | Housing & indoor | 2008-2023 |
| ehdp:measure:1133 | NYC agency use of "Best Practice" products, NYCHA application count | NYCHA application count | Pesticides targeting insects that are effective, but have low toxicity or low po | Total count of pesticide applications made by the NYC Housin | Housing & indoor | 2008-2023 |
| ehdp:measure:1130 | NYC agency use of "Best Practice" products, All agency (solids) | All agency (solids) | Pesticides targeting insects that are effective, but have low toxicity or low po | Sum of pounds of solid pesticide applications made by NYC ag | Housing & indoor | 2008-2023 |
| ehdp:measure:1129 | NYC agency use of "Best Practice" products, All agency application count | All agency application count | Pesticides targeting insects that are effective, but have low toxicity or low po | Total count of pesticide applications made by NYC agencies o | Housing & indoor | 2008-2023 |
| ehdp:measure:1131 | NYC agency use of "Best Practice" products, DOE application count | DOE application count | Pesticides targeting insects that are effective, but have low toxicity or low po | Total count of pesticide applications made by the Department | Housing & indoor | 2008-2023 |

Supplement candidates (wider SPG, not in table above):
- `j0A1zcxTqg` general dental practice —  (cos 0.28)
- `uiHfq-yGGD` tat gene products — trans-acting transcription factors produced by retroviruse (cos 0.27)
- `jn93N6PlWV` nef gene product — products of the retroviral nef gene (cos 0.27)

## NYC family: Asthma ED visits (age 5 to 17)  (5 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:1195 | Asthma ED visits (age 5 to 17), Number | Number | Emergency department visits for asthma. Things like smoke, air pollution, dust m | Number of asthma-related emergency department (ED) visits am | Asthma & respiratory;Housing & indoor | 2005-2023 |
| ehdp:measure:1196 | Asthma ED visits (age 5 to 17), Estimated annual rate | Estimated annual rate | Emergency department visits for asthma. Things like smoke, air pollution, dust m | Number of asthma-related emergency department (ED) visits am | Asthma & respiratory;Housing & indoor | 2005-2023 |
| ehdp:measure:1217 | Asthma ED visits (age 5 to 17), by NTA, Average annual number | Average annual number | Emergency department visits for asthma. Things like smoke, air pollution, dust m | Average annual number of asthma-related emergency department | Asthma & respiratory;Housing & indoor | 2014-2017 |
| ehdp:measure:1206 | Asthma ED visits (age 5 to 17), by NTA, Average annual rate | Average annual rate | Emergency department visits for asthma. Things like smoke, air pollution, dust m | Average annual number of asthma-related emergency department | Asthma & respiratory;Housing & indoor | 2014-2017 |
| ehdp:measure:1205 | Asthma ED visits (age 5 to 17), by NTA, Number | Number | Emergency department visits for asthma. Things like smoke, air pollution, dust m | Aggregated number of asthma-related emergency department (ED | Asthma & respiratory;Housing & indoor | 2017-2017 |

Supplement candidates (wider SPG, not in table above):
- `Jx2R43aZ7W` status asthmaticus — type of asthma (cos 0.4)
- `ICZJq4kU5i` anti-asthmatic agents — drugs used to treat asthma (cos 0.3)
- `90fz4aqYPE` Office Visits — Visits made by patients to health service providers' offices for diagn (cos 0.25)

## NYC family: Arsenic  (5 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:436 | Arsenic, Maximum concentration | Maximum concentration | Concentration of arsenic in drinking water. Arsenic occurrs naturally in some gr | Samples are collected from entry points to the drinking wate | Housing & indoor | 1999-2021 |
| ehdp:measure:437 | Arsenic, Number (samples) | Number (samples) | Concentration of arsenic in drinking water. Arsenic occurrs naturally in some gr | Number of samples collected from entry points to the distrib | Housing & indoor | 1999-2021 |
| ehdp:measure:528 | Arsenic, Maximum allowable contaminant level (MCL) | Maximum allowable contaminant level (MCL) | Concentration of arsenic in drinking water. Arsenic occurrs naturally in some gr | The highest level of arsenic that is allowed in drinking wat | Housing & indoor | 1999-2021 |
| ehdp:measure:438 | Arsenic, Number (sample locations) | Number (sample locations) | Concentration of arsenic in drinking water. Arsenic occurrs naturally in some gr | Number of sampling locations. | Housing & indoor | 1999-2021 |
| ehdp:measure:435 | Arsenic, Annual average concentration | Annual average concentration | Concentration of arsenic in drinking water. Arsenic occurrs naturally in some gr | Samples are collected from entry points to the drinking wate | Housing & indoor | 1999-2021 |

Supplement candidates (wider SPG, not in table above):
- `g95gvaIuB8` arsenic compound — class of chemical compounds (cos 0.79)
- `_z7MHvIz4t` arsenic poisoning — arsenic affecting human life (cos 0.75)
- `xDWJMegNBz` arsenate — salt or ester of arsenic acid (cos 0.67)

## NYC family: Heat events  (5 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:549 | Heat events, 90 degree days | 90 degree days | Days over 90 degrees. More people die due to extreme heat than all other extreme | Number of days per year with a maximum temperature or heat i | Heat & temperature;Climate & weather | 2000-2018 |
| ehdp:measure:550 | Heat events, 95 degree days | 95 degree days | Days over 90 degrees. More people die due to extreme heat than all other extreme | Number of days per year with a maximum temperature or heat i | Heat & temperature;Climate & weather | 2000-2018 |
| ehdp:measure:551 | Heat events, 100 degree days | 100 degree days | Days over 90 degrees. More people die due to extreme heat than all other extreme | Number of days per year with a maximum temperature or heat i | Heat & temperature;Climate & weather | 2000-2018 |
| ehdp:measure:553 | Heat events, 2+ 95 degree days | 2+ 95 degree days | Days over 90 degrees. More people die due to extreme heat than all other extreme | Number of events per year with a maximum daily temperature o | Heat & temperature;Climate & weather | 2000-2018 |
| ehdp:measure:554 | Heat events, Maximum consecutive 90 degree days | Maximum consecutive 90 degree days | Days over 90 degrees. More people die due to extreme heat than all other extreme | Duration in consecutive days of longest event per year with  | Heat & temperature;Climate & weather | 2000-2018 |

Supplement candidates (wider SPG, not in table above):
- `6t2_El9p-a` HEATR3 — protein-coding gene in the species Homo sapiens (cos 0.31)
- `yBTH6Nv35k` history — past events and their tracks or records (cos 0.3)
- `AuowoaaCsz` HEATR6 — protein-coding gene in the species Homo sapiens (cos 0.29)

## NYC family: NYC agency use of mosquito control  (5 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:1170 | NYC agency use of mosquito control, DOHMH adulticides application count | DOHMH adulticides application count | Pesticides targeting mosquitoes, applied by NYC agency-contracted exterminators  | Total count of pesticides applied by the Department of Healt | Housing & indoor | 2008-2023 |
| ehdp:measure:1172 | NYC agency use of mosquito control, All agency larvicides application count | All agency larvicides application count | Pesticides targeting mosquitoes, applied by NYC agency-contracted exterminators  | Total count of pesticides applied by NYC agencies and their  | Housing & indoor | 2008-2023 |
| ehdp:measure:1173 | NYC agency use of mosquito control, All agency larvicides | All agency larvicides | Pesticides targeting mosquitoes, applied by NYC agency-contracted exterminators  | Sum of pounds of solid pesticides applied by NYC agencies an | Housing & indoor | 2008-2023 |
| ehdp:measure:1171 | NYC agency use of mosquito control, DOHMH adulticides (solids) | DOHMH adulticides (solids) | Pesticides targeting mosquitoes, applied by NYC agency-contracted exterminators  | Sum of pounds of solid pesticides applied by the Department  | Housing & indoor | 2008-2021 |
| ehdp:measure:1377 | NYC agency use of mosquito control, DOHMH adulticides (liquids) | DOHMH adulticides (liquids) | Pesticides targeting mosquitoes, applied by NYC agency-contracted exterminators  | Sum of gallons of liquid pesticides applied by the Departmen | Housing & indoor | 2020-2023 |

Supplement candidates (wider SPG, not in table above):
- `qG8bpAf84m` mosquito control — efforts to reduce health risks from mosquitoes (cos 0.57)
- `_o1feEPxJM` Culicidae — family of nematoceran flies (cos 0.51)
- `MvZaix-FRr` mosquito net — fine net used to exclude mosquitos and other biting insects (cos 0.49)

## NYC family: Asthma hospitalizations (age 4 and under)  (4 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:155 | Asthma hospitalizations (age 4 and under), Estimated annual rate | Estimated annual rate | Asthma hospitalizations are more severe asthma outcomes. They're often clustered | Number of asthma-related hospitalizations among NYC resident | Asthma & respiratory;Housing & indoor;Social & economic | 1998-2023 |
| ehdp:measure:154 | Asthma hospitalizations (age 4 and under), Number | Number | Asthma hospitalizations are more severe asthma outcomes. They're often clustered | Number of asthma-related hospitalizations among NYC resident | Asthma & respiratory;Housing & indoor;Social & economic | 1998-2023 |
| ehdp:measure:1210 | Asthma hospitalizations (age 4 and under), by NTA, Average annual rate | Average annual rate | Hospitalizations for asthma. These more severe asthma outcomes are often cluster | Average annual number of asthma-related hospitalizations amo | Asthma & respiratory;Housing & indoor;Social & economic | 2014-2014 |
| ehdp:measure:1211 | Asthma hospitalizations (age 4 and under), by NTA, Number | Number | Hospitalizations for asthma. These more severe asthma outcomes are often cluster | Aggregated number of asthma-related hospitalizations among N | Asthma & respiratory;Housing & indoor;Social & economic | 2014-2014 |

Supplement candidates (wider SPG, not in table above):
- `Jx2R43aZ7W` status asthmaticus — type of asthma (cos 0.39)
- `M6F-TJO4S3` hospitalized child — child hospitalized for short term care (cos 0.37)
- `HqtWmsegwf` rural hospital — hospital (cos 0.35)

## NYC family: Asthma ED visits (age 4 and under)  (4 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:460 | Asthma ED visits (age 4 and under), Estimated annual rate | Estimated annual rate | Severe asthma attacks can result in a visit to the ED. Things like smoke, air po | Number of asthma-related emergency department (ED) visits am | Asthma & respiratory;Housing & indoor | 2005-2023 |
| ehdp:measure:459 | Asthma ED visits (age 4 and under), Number | Number | Severe asthma attacks can result in a visit to the ED. Things like smoke, air po | Number of asthma-related emergency department (ED) visits am | Asthma & respiratory;Housing & indoor | 2005-2023 |
| ehdp:measure:1194 | Asthma ED visits (age 4 and under), by NTA, Number | Number | Emergency department visits for asthma. Things like smoke, air pollution, dust m | Aggregated number of asthma-related emergency department (ED | Asthma & respiratory;Housing & indoor | 2014-2014 |
| ehdp:measure:1193 | Asthma ED visits (age 4 and under), by NTA, Average annual rate | Average annual rate | Emergency department visits for asthma. Things like smoke, air pollution, dust m | Average annual number of asthma-related emergency department | Asthma & respiratory;Housing & indoor | 2014-2014 |

Supplement candidates (wider SPG, not in table above):
- `Jx2R43aZ7W` status asthmaticus — type of asthma (cos 0.43)
- `ICZJq4kU5i` anti-asthmatic agents — drugs used to treat asthma (cos 0.3)
- `90fz4aqYPE` Office Visits — Visits made by patients to health service providers' offices for diagn (cos 0.25)

## NYC family: Asthma hospitalizations (age 5 to 17)  (4 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:1200 | Asthma hospitalizations (age 5 to 17), Number | Number | Hospitalizations for asthma. These more severe asthma outcomes are often cluster | Number of asthma-related hospitalizations among NYC resident | Asthma & respiratory;Housing & indoor;Social & economic | 2005-2023 |
| ehdp:measure:1201 | Asthma hospitalizations (age 5 to 17), Estimated annual rate | Estimated annual rate | Hospitalizations for asthma. These more severe asthma outcomes are often cluster | Number of asthma-related hospitalizations among NYC resident | Asthma & respiratory;Housing & indoor;Social & economic | 2005-2023 |
| ehdp:measure:1213 | Asthma hospitalizations (age 5 to 17), by NTA, Average annual rate | Average annual rate | Hospitalizations for asthma. These more severe asthma outcomes are often cluster | Average annual number of asthma-related hospitalizations amo | Asthma & respiratory;Housing & indoor;Social & economic | 2014-2014 |
| ehdp:measure:1219 | Asthma hospitalizations (age 5 to 17), by NTA, Average annual number | Average annual number | Hospitalizations for asthma. These more severe asthma outcomes are often cluster | Average annual number of asthma-related hospitalizations amo | Asthma & respiratory;Housing & indoor;Social & economic | 2014-2014 |

Supplement candidates (wider SPG, not in table above):
- `Jx2R43aZ7W` status asthmaticus — type of asthma (cos 0.37)
- `M6F-TJO4S3` hospitalized child — child hospitalized for short term care (cos 0.37)
- `HqtWmsegwf` rural hospital — hospital (cos 0.35)

## NYC family: Cockroaches  (4 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:245 | Cockroaches, Percent | Percent | The presence of cockroaches in the home is often associated with poor housing ma | Estimated number of households in an area that reported seei | Asthma & respiratory;Housing & indoor | 2008-2023 |
| ehdp:measure:631 | Cockroaches, Number | Number | The presence of cockroaches in the home is often associated with poor housing ma | Estimated number of households that reported seeing at least | Asthma & respiratory;Housing & indoor | 2011-2017 |
| ehdp:measure:41 | Cockroaches, Percent | Percent | Adults reporting cockroaches in the past 30 days (from when they were surveyed). | Estimated number of respondents in an area that reported coc | Asthma & respiratory;Housing & indoor | 2003-2012 |
| ehdp:measure:40 | Cockroaches, Number | Number | Adults reporting cockroaches in the past 30 days (from when they were surveyed). | Estimated number of respondents in an area that reported coc | Asthma & respiratory;Housing & indoor | 2003-2012 |

Supplement candidates (wider SPG, not in table above):
- `cL7f0l1roH` Blattellidae — cockroaches family (cos 0.77)
- `JgRYwtm5Zx` cockroach — paraphyletic group of winged insects of the order Blattodea (cos 0.73)

## NYC family: Asthma ED visits (adults  (4 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:1218 | Asthma ED visits (adults, NTA), Average annual number | Average annual number | Emergency department visits for asthma. Things like smoke, air pollution, dust m | Average annual number of asthma-related emergency department | Asthma & respiratory;Housing & indoor | 2012-2017 |
| ehdp:measure:1208 | Asthma ED visits (adults, NTA), Average annual rate | Average annual rate | Emergency department visits for asthma. Things like smoke, air pollution, dust m | Average annual number of asthma-related emergency department | Asthma & respiratory;Housing & indoor | 2012-2017 |
| ehdp:measure:1209 | Asthma ED visits (adults, NTA), Average annual age-adjusted rate | Average annual age-adjusted rate | Emergency department visits for asthma. Things like smoke, air pollution, dust m | Average annual number of asthma-related emergency department | Asthma & respiratory;Housing & indoor | 2012-2017 |
| ehdp:measure:1207 | Asthma ED visits (adults, NTA), Number | Number | Emergency department visits for asthma. Things like smoke, air pollution, dust m | Aggregated number of asthma-related emergency department (ED | Asthma & respiratory;Housing & indoor | 2017-2017 |

Supplement candidates (wider SPG, not in table above):
- `Jx2R43aZ7W` status asthmaticus — type of asthma (cos 0.41)
- `ICZJq4kU5i` anti-asthmatic agents — drugs used to treat asthma (cos 0.3)
- `90fz4aqYPE` Office Visits — Visits made by patients to health service providers' offices for diagn (cos 0.25)

## NYC family: Citi Bike stations  (4 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:1350 | Citi Bike stations, Number | Number | Biking bridges gaps in existing public transportation systems and is a great way | The number of Citi Bike stations per geographic area. | Green & built | 2023-2023 |
| ehdp:measure:1351 | Citi Bike stations, Density | Density | Biking bridges gaps in existing public transportation systems and is a great way | The number of Citi Bike stations per geographic area, divide | Green & built | 2023-2023 |
| ehdp:measure:1352 | Citi Bike stations, Docks per station | Docks per station | Biking bridges gaps in existing public transportation systems and is a great way | The total dock capacity of Citi Bike stations per geographic | Green & built | 2023-2023 |
| ehdp:measure:1372 | Citi Bike stations, Docks per 1000 people | Docks per 1000 people | Biking bridges gaps in existing public transportation systems and is a great way | The total dock capacity of Citi Bike stations per geographic | Green & built | 2023-2023 |

Supplement candidates (wider SPG, not in table above):
- `bCExxZr1ew` motorcycle — two- or three-wheeled motor vehicle (cos 0.31)
- `3K3gx13Fco` BMP2K — protein-coding gene in the species Homo sapiens (cos 0.22)

## NYC family: Ozone asthma hospitalizations  (4 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:661 | Ozone asthma hospitalizations, Estimated annual rate (age 18+) | Estimated annual rate (age 18+) | Hospitalizations for asthma due to ozone. These are part of the health burden of | Estimate is based on the number of hospitalizations for urge | Air quality;Asthma & respiratory | 2005-2017 |
| ehdp:measure:655 | Ozone asthma hospitalizations, Estimated annual rate (under age 18) | Estimated annual rate (under age 18) | Hospitalizations for asthma due to ozone. These are part of the health burden of | Estimate is based on the number of hospitalizations for urge | Air quality;Asthma & respiratory | 2005-2017 |
| ehdp:measure:1182 | Ozone asthma hospitalizations, Estimated annual number (age 18+) | Estimated annual number (age 18+) | Hospitalizations for asthma due to ozone. These are part of the health burden of | Estimate is based on the number of hospitalizations for urge | Air quality;Asthma & respiratory | 2005-2017 |
| ehdp:measure:1181 | Ozone asthma hospitalizations, Estimated annual number (under age 18) | Estimated annual number (under age 18) | Hospitalizations for asthma due to ozone. These are part of the health burden of | Estimate is based on the number of hospitalizations for urge | Air quality;Asthma & respiratory | 2005-2017 |

Supplement candidates (wider SPG, not in table above):
- `Jx2R43aZ7W` status asthmaticus — type of asthma (cos 0.38)
- `M6F-TJO4S3` hospitalized child — child hospitalized for short term care (cos 0.38)
- `HqtWmsegwf` rural hospital — hospital (cos 0.36)

## NYC family: PM2.5 asthma ED visits  (4 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:1174 | PM2.5 asthma ED visits, Estimated annual number (under age 18) | Estimated annual number (under age 18) | ED visits for asthma due to PM2.5 air pollution. These represent part of the hea | Estimate is based on the number of emergency department (ED) | Air quality;Asthma & respiratory | 2005-2017 |
| ehdp:measure:657 | PM2.5 asthma ED visits, Estimated annual rate (age 18+) | Estimated annual rate (age 18+) | ED visits for asthma due to PM2.5 air pollution. These represent part of the hea | Estimate is based on the number of emergency department (ED) | Air quality;Asthma & respiratory | 2005-2017 |
| ehdp:measure:648 | PM2.5 asthma ED visits, Estimated annual rate (under age 18) | Estimated annual rate (under age 18) | ED visits for asthma due to PM2.5 air pollution. These represent part of the hea | Estimate is based on the number of emergency department (ED) | Air quality;Asthma & respiratory | 2005-2017 |
| ehdp:measure:1175 | PM2.5 asthma ED visits, Estimated annual number (age 18+) | Estimated annual number (age 18+) | ED visits for asthma due to PM2.5 air pollution. These represent part of the hea | Estimate is based on the number of emergency department (ED) | Air quality;Asthma & respiratory | 2005-2017 |

Supplement candidates (wider SPG, not in table above):
- `Jx2R43aZ7W` status asthmaticus — type of asthma (cos 0.41)
- `ICZJq4kU5i` anti-asthmatic agents — drugs used to treat asthma (cos 0.29)
- `90fz4aqYPE` Office Visits — Visits made by patients to health service providers' offices for diagn (cos 0.24)

## NYC family: Ozone asthma ED visits  (4 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:659 | Ozone asthma ED visits, Estimated annual rate (age 18+) | Estimated annual rate (age 18+) | ED visits for asthma due to ozone. These are part of the health burden of air po | Estimate is based on the number of emergency department (ED) | Air quality;Asthma & respiratory | 2005-2017 |
| ehdp:measure:653 | Ozone asthma ED visits, Estimated annual rate (under age 18) | Estimated annual rate (under age 18) | ED visits for asthma due to ozone. These are part of the health burden of air po | Estimate is based on the number of emergency department (ED) | Air quality;Asthma & respiratory | 2005-2017 |
| ehdp:measure:1180 | Ozone asthma ED visits, Estimated annual number (age 18+) | Estimated annual number (age 18+) | ED visits for asthma due to ozone. These are part of the health burden of air po | Estimate is based on the number of emergency department (ED) | Air quality;Asthma & respiratory | 2005-2017 |
| ehdp:measure:1179 | Ozone asthma ED visits, Estimated annual number (under age 18) | Estimated annual number (under age 18) | ED visits for asthma due to ozone. These are part of the health burden of air po | Estimate is based on the number of emergency department (ED) | Air quality;Asthma & respiratory | 2005-2017 |

Supplement candidates (wider SPG, not in table above):
- `Jx2R43aZ7W` status asthmaticus — type of asthma (cos 0.41)
- `ICZJq4kU5i` anti-asthmatic agents — drugs used to treat asthma (cos 0.3)
- `90fz4aqYPE` Office Visits — Visits made by patients to health service providers' offices for diagn (cos 0.25)

## NYC family: Elevated blood lead levels (age 16+)  (4 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:878 | Elevated blood lead levels (age 16+), Number (25+ mcg/dL) | Number (25+ mcg/dL) | Blood lead levels over 10 mg/dL among people age 16+. In New York City, the most | Number of NYC residents aged 16 years or older with blood le | Housing & indoor | 2001-2016 |
| ehdp:measure:880 | Elevated blood lead levels (age 16+), Average annual rate (10+ mcg/dL) | Average annual rate (10+ mcg/dL) | Blood lead levels over 10 mg/dL among people age 16+. In New York City, the most | Number of NYC residents aged 16 years and older with blood l | Housing & indoor | 2001-2016 |
| ehdp:measure:872 | Elevated blood lead levels (age 16+), Number (10+ mcg/dL) | Number (10+ mcg/dL) | Blood lead levels over 10 mg/dL among people age 16+. In New York City, the most | Number of NYC residents aged 16 years or older with blood le | Housing & indoor | 2001-2016 |
| ehdp:measure:873 | Elevated blood lead levels (age 16+), Average annual rate (25+ mcg/dL) | Average annual rate (25+ mcg/dL) | Blood lead levels over 10 mg/dL among people age 16+. In New York City, the most | Number of NYC residents aged 16 years and older with blood l | Housing & indoor | 2001-2016 |

Supplement candidates (wider SPG, not in table above):
- `Z1DkcC8Exg` Blood lead level — level of lead in blood (cos 0.61)
- `AdMnm7d5wZ` elevated transaminases — elevations of the levels of transaminases in the serum (cos 0.42)
- `19GI2cQ6gq` hyperkalemia — elevated level of potassium (K+) in the blood serum. (cos 0.41)

## NYC family: NYC agency use of glyphosate  (4 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:1135 | NYC agency use of glyphosate, All agency application count | All agency application count | Herbicide containing the chemical glyphosate, targeting unwanted weeds, grasses, | Total count of pesticide applications made by NYC agencies o | Housing & indoor;Green & built | 2008-2023 |
| ehdp:measure:1136 | NYC agency use of glyphosate, All agency (liquids) | All agency (liquids) | Herbicide containing the chemical glyphosate, targeting unwanted weeds, grasses, | Sum of gallons of liquid pesticide applications made by NYC  | Housing & indoor;Green & built | 2008-2023 |
| ehdp:measure:1137 | NYC agency use of glyphosate, Parks application count | Parks application count | Herbicide containing the chemical glyphosate, targeting unwanted weeds, grasses, | Total count of pesticide applications made by the Department | Housing & indoor;Green & built | 2008-2023 |
| ehdp:measure:1138 | NYC agency use of glyphosate, Parks (liquids) | Parks (liquids) | Herbicide containing the chemical glyphosate, targeting unwanted weeds, grasses, | Sum of gallons of liquid pesticide applications made by the  | Housing & indoor;Green & built | 2008-2023 |

Supplement candidates (wider SPG, not in table above):
- `7P8u0wR1ts` glyphosate — chemical compound (cos 0.47)
- `8ddk_0YfvJ` polyphosphate — class of chemical compounds (cos 0.24)
- `fQxrVIQSoi` tin polyphosphate — class of chemical compounds (cos 0.22)

## NYC family: Poverty  (3 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:233 | Poverty, Number | Number | Households with incomes below the federal poverty level. Households without suff | Estimated number of people for whom poverty status is determ | Housing & indoor;Social & economic | 2007-2019 |
| ehdp:measure:221 | Poverty, Percent | Percent | Households with incomes below the federal poverty level. Households without suff | Estimated number of people for whom poverty status is determ | Housing & indoor;Social & economic | 2007-2019 |
| ehdp:measure:870 | Poverty, Rank | Rank | Households with incomes below the federal poverty level. Households without suff | test | Housing & indoor;Social & economic | 2009-2011 |

## NYC family: Child poverty  (3 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:755 | Child poverty, Percent | Percent | Children living in households in poverty. Poverty deprives people of access to h | Estimated number of children in a household whose annual inc | Social & economic | 2007-2017 |
| ehdp:measure:754 | Child poverty, Number | Number | Children living in households in poverty. Poverty deprives people of access to h | Estimated number of children who live in a household for who | Social & economic | 2007-2017 |
| ehdp:measure:869 | Child poverty, Rank | Rank | Children living in households in poverty. Poverty deprives people of access to h | Neighborhoods are ranked citywide in 3 groups (tertiles), so | Social & economic | 2009-2009 |

Supplement candidates (wider SPG, not in table above):
- `du4LooAe8F` child — human between birth and puberty (cos 0.41)
- `d0rwMIvA5n` parenting — process of raising a child (cos 0.35)
- `vSn5OHbgCI` child sexual abuse — form of child abuse (cos 0.31)

## NYC family: Nitrogen dioxide  (3 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:1431 | Nitrogen dioxide, Annual mean | Annual mean | Concentration of nitrogen dioxide in the air. Nitrogen dioxide is a pollutant fo | Air samples collected at specific NYCCAS monitoring sites al | Air quality | 2009-2025 |
| ehdp:measure:1432 | Nitrogen dioxide, Summer mean | Summer mean | Concentration of nitrogen dioxide in the air. Nitrogen dioxide is a pollutant fo | Air samples collected at specific NYCCAS monitoring sites al | Air quality | 2009-2025 |
| ehdp:measure:1433 | Nitrogen dioxide, Winter mean | Winter mean | Concentration of nitrogen dioxide in the air. Nitrogen dioxide is a pollutant fo | Air samples collected at specific NYCCAS monitoring sites al | Air quality | 2009-2025 |

Supplement candidates (wider SPG, not in table above):
- `CGI_WiqbDZ` nitrogen oxide — any chemical compound consisting of nitrogen and oxygen only (cos 0.6)
- `UuFOyqZncv` nitrite ion — anion (cos 0.55)
- `aZtUF3LVtt` hydrogen peroxide — chemical compound (cos 0.54)

## NYC family: PM2.5 (Fine particles)  (3 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:1425 | PM2.5 (Fine particles), Annual mean | Annual mean | Concentration of fine particles in the air. Fine particles are emitted by vehicl | Air samples collected at specific NYCCAS monitoring sites al | Air quality;Green & built | 2009-2025 |
| ehdp:measure:1426 | PM2.5 (Fine particles), Summer mean | Summer mean | Concentration of fine particles in the air. Fine particles are emitted by vehicl | Air samples collected at specific NYCCAS monitoring sites al | Air quality;Green & built | 2009-2025 |
| ehdp:measure:1427 | PM2.5 (Fine particles), Winter mean | Winter mean | Concentration of fine particles in the air. Fine particles are emitted by vehicl | Air samples collected at specific NYCCAS monitoring sites al | Air quality;Green & built | 2009-2025 |

Supplement candidates (wider SPG, not in table above):
- `jtzZPZ8DQh` PM 2.5 — particulates of 2.5 micrometers or less (cos 0.44)
- `Fwwu1s3wZA` dust — small particles in the air (cos 0.33)
- `vY3QsbDZaz` nanoparticle — particle with size less than 100 nm (cos 0.31)

## NYC family: Black carbon  (3 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:1429 | Black carbon, Summer mean | Summer mean | Concentration of black carbon in the air. Black carbon is a major component of f | Air samples collected at specific NYCCAS monitoring sites al | Air quality | 2009-2025 |
| ehdp:measure:1430 | Black carbon, Winter mean | Winter mean | Concentration of black carbon in the air. Black carbon is a major component of f | Air samples collected at specific NYCCAS monitoring sites al | Air quality | 2009-2025 |
| ehdp:measure:1428 | Black carbon, Annual mean | Annual mean | Concentration of black carbon in the air. Black carbon is a major component of f | Air samples collected at specific NYCCAS monitoring sites al | Air quality | 2009-2025 |

Supplement candidates (wider SPG, not in table above):
- `LwoQztgGk8` Simuliidae — family of flies (cos 0.44)
- `XG_c_pj85V` Black people — a racialized classification of people, usually a political and skin co (cos 0.4)
- `RkxzIxYe6M` Total organic carbon — concentration of organic carbon in a sample (cos 0.36)

## NYC family: Asthma (adults)  (3 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:363 | Asthma (adults), Percent | Percent | Adults reporting an asthma diagnosis, and symptoms, in the last 12 months (from  | Estimated number of adults aged 18 years and older who repor | Air quality;Asthma & respiratory;Housing & indoor | 2003-2022 |
| ehdp:measure:31 | Asthma (adults), Age-adjusted percent | Age-adjusted percent | Adults reporting an asthma diagnosis, and symptoms, in the last 12 months (from  | Estimated number of adults aged 18 years and older who repor | Air quality;Asthma & respiratory;Housing & indoor | 2003-2022 |
| ehdp:measure:30 | Asthma (adults), Number | Number | Adults reporting an asthma diagnosis, and symptoms, in the last 12 months (from  | Estimated number of adults aged 18 years and older who repor | Air quality;Asthma & respiratory;Housing & indoor | 2003-2022 |

Supplement candidates (wider SPG, not in table above):
- `Jx2R43aZ7W` status asthmaticus — type of asthma (cos 0.5)
- `ICZJq4kU5i` anti-asthmatic agents — drugs used to treat asthma (cos 0.36)

## NYC family: Asthma ED visits (adults)  (3 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:1197 | Asthma ED visits (adults), Number | Number | Emergency department visits for asthma. Things like smoke, air pollution, dust m | Number of asthma-related emergency department (ED) visits am | Asthma & respiratory;Housing & indoor | 2005-2023 |
| ehdp:measure:1198 | Asthma ED visits (adults), Estimated annual rate | Estimated annual rate | Emergency department visits for asthma. Things like smoke, air pollution, dust m | Number of asthma-related emergency department (ED) visits am | Asthma & respiratory;Housing & indoor | 2005-2023 |
| ehdp:measure:1199 | Asthma ED visits (adults), Age-adjusted rate | Age-adjusted rate | Emergency department visits for asthma. Things like smoke, air pollution, dust m | Number of asthma-related emergency department (ED) visits am | Asthma & respiratory;Housing & indoor | 2005-2023 |

Supplement candidates (wider SPG, not in table above):
- `Jx2R43aZ7W` status asthmaticus — type of asthma (cos 0.4)
- `ICZJq4kU5i` anti-asthmatic agents — drugs used to treat asthma (cos 0.29)
- `90fz4aqYPE` Office Visits — Visits made by patients to health service providers' offices for diagn (cos 0.24)

## NYC family: Diabetes (adults)  (3 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:717 | Diabetes (adults), Age-adjusted percent | Age-adjusted percent | Diabetes is a metabolic disorder that affects how well your body can get energy  | Estimated number of adults aged 18 years and older who have  | Cardiovascular | 2007-2022 |
| ehdp:measure:719 | Diabetes (adults), Percent | Percent | Diabetes is a metabolic disorder that affects how well your body can get energy  | Estimated number of adults aged 18 years and older who have  | Cardiovascular | 2007-2022 |
| ehdp:measure:718 | Diabetes (adults), Number | Number | Diabetes is a metabolic disorder that affects how well your body can get energy  | Estimated number of adults aged 18 years and older who have  | Cardiovascular | 2007-2022 |

Supplement candidates (wider SPG, not in table above):
- `PAiZIeG9pe` Diabetic coma — medical condition due to diabetes (cos 0.52)
- `7tbk11vFEK` Latent autoimmune diabetes — medical condition (cos 0.51)
- `BHJmU_6tIk` prediabetes syndrome — a predisease state of hyperglycemia with high risk for diabetes (cos 0.45)

## NYC family: Heat ED visits  (3 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:537 | Heat ED visits, Age-adjusted rate | Age-adjusted rate | ED visits due to heat-related illnesses, such as heat stroke and heat exhaustion | The number of NYC residents treated in a NYC emergency depar | Heat & temperature;Cardiovascular | 2005-2022 |
| ehdp:measure:535 | Heat ED visits, Number | Number | ED visits due to heat-related illnesses, such as heat stroke and heat exhaustion | The number of NYC residents treated in a NYC emergency depar | Heat & temperature;Cardiovascular | 2005-2022 |
| ehdp:measure:536 | Heat ED visits, Estimated annual rate | Estimated annual rate | ED visits due to heat-related illnesses, such as heat stroke and heat exhaustion | The number of NYC residents treated in a NYC emergency depar | Heat & temperature;Cardiovascular | 2005-2022 |

Supplement candidates (wider SPG, not in table above):
- `90fz4aqYPE` Office Visits — Visits made by patients to health service providers' offices for diagn (cos 0.39)
- `3HvZT1of0h` Visitors to Patients — Patients' guests and rules for visiting. (cos 0.27)
- `GuufEaGtME` appointments and schedules — the various different methods of scheduling healthcase visits (cos 0.26)

## NYC family: Households with AC  (3 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:781 | Households with AC, Percent (with AC) | Percent (with AC) | Households reporting functioning air conditioning (AC). AC is an important way t | Estimated number of households in an area reporting having f | Heat & temperature | 2014-2023 |
| ehdp:measure:1045 | Households with AC, Percent (without AC) | Percent (without AC) | Households reporting functioning air conditioning (AC). AC is an important way t | Estimated number of households in an area reporting not havi | Heat & temperature | 2014-2023 |
| ehdp:measure:782 | Households with AC, Number (with AC) | Number (with AC) | Households reporting functioning air conditioning (AC). AC is an important way t | Estimated number of households reporting having functioning  | Heat & temperature | 2014-2017 |

Supplement candidates (wider SPG, not in table above):
- `-Z5-JHJW2U` household products — substances or materials used in the course of housekeeping or personal (cos 0.52)
- `lmHcY3gDld` housekeeping — management of household chores (cos 0.48)
- `WLDbx54V-S` linens — household textiles and (historically) personal clothing (cos 0.4)

## NYC family: Average Citi Bike availability  (3 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:1353 | Average Citi Bike availability, Number | Number | The average number of Citi Bikes available to rent per each area between 7am-7pm | Yearly bike availability is calculated by totaling average d | Housing & indoor;Green & built | 2022-2022 |
| ehdp:measure:1365 | Average Citi Bike availability, Bikes per station | Bikes per station | The average number of Citi Bikes available to rent per each area between 7am-7pm | Yearly bike availability is calculated by totaling average d | Housing & indoor;Green & built | 2022-2022 |
| ehdp:measure:1354 | Average Citi Bike availability, Density | Density | The average number of Citi Bikes available to rent per each area between 7am-7pm | Yearly bike availability is calculated by totaling average d | Housing & indoor;Green & built | 2022-2022 |

Supplement candidates (wider SPG, not in table above):
- `Gn-Jm_L8Gr` bioavailability — type of absorption (cos 0.55)
- `3X9JydAzHk` food security — condition related to the supply and availability of food, and individu (cos 0.33)
- `ONf6ct5iQ3` insurance coverage — amount of protection available and the kind of loss which would be pai (cos 0.26)

## NYC family: Lyme disease  (3 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:1400 | Lyme disease, Number | Number | Cases of Lyme disease. Lyme disease is transmitted through the bite of an infect | Number of cases meeting the?national case definition. | Cardiovascular | 2000-2020 |
| ehdp:measure:1402 | Lyme disease, Age-adjusted rate | Age-adjusted rate | Cases of Lyme disease. Lyme disease is transmitted through the bite of an infect | Age-adjusted rates were calculated per 100,000 population us | Cardiovascular | 2000-2020 |
| ehdp:measure:1401 | Lyme disease, Rate | Rate | Cases of Lyme disease. Lyme disease is transmitted through the bite of an infect | Crude Rate per 100,000 Population | Cardiovascular | 2000-2020 |

Supplement candidates (wider SPG, not in table above):
- `OfQcxYwdhM` Post-Treatment Lyme Disease — Lyme disease symptoms persisting after treatment (cos 0.5)
- `o-M9CG9kk9` Bowen's disease — disease (cos 0.39)
- `_VkP5asl6A` anal disease — human disease (cos 0.39)

## NYC family: Heat stress: 5-year emergency department visits  (3 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:1405 | Heat stress: 5-year emergency department visits, Average annual age-adjusted rate | Average annual age-adjusted rate | ED visits due to heat-related illnesses, such as heat stroke and heat exhaustion | The number of NYC residents treated in a NYC emergency depar | Heat & temperature;Cardiovascular | 2018-2018 |
| ehdp:measure:1403 | Heat stress: 5-year emergency department visits, Number | Number | ED visits due to heat-related illnesses, such as heat stroke and heat exhaustion | The number of NYC residents treated in a NYC emergency depar | Heat & temperature;Cardiovascular | 2018-2018 |
| ehdp:measure:1404 | Heat stress: 5-year emergency department visits, Estimated annual rate | Estimated annual rate | ED visits due to heat-related illnesses, such as heat stroke and heat exhaustion | The number of NYC residents treated in a NYC emergency depar | Heat & temperature;Cardiovascular | 2018-2018 |

Supplement candidates (wider SPG, not in table above):
- `cExGz1bOoS` Emergency Treatment —  (cos 0.46)
- `xfCkI7BH9S` United States Department of Health and Human Services — department of the US federal government (cos 0.31)
- `yy20Kl8PjT` pediatric emergency medicine — branch of emergency medicine dealing with the emergency care of childr (cos 0.31)

## NYC family: Work-related deaths (construction industry)  (3 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:885 | Work-related deaths (construction industry), Citywide, Annual rate | Annual rate | Construction is the most dangerous industry in NYC, with nearly a third of work- | Number of fatal construction injuries occurring in NYC and r | Mortality | 1992-2014 |
| ehdp:measure:884 | Work-related deaths (construction industry), Citywide, Number | Number | Construction is the most dangerous industry in NYC, with nearly a third of work- | Number of fatal construction injuries occurring in NYC and r | Mortality | 1992-2014 |
| ehdp:measure:904 | Work-related deaths (construction industry), by borough, Number | Number | Construction is the most dangerous industry in NYC, with nearly a third of work- | Number of fatal construction injuries occurring in NYC by bo | Mortality | 2007-2012 |

Supplement candidates (wider SPG, not in table above):
- `3tietCkdPo` industrial production — totality of all goods that are generated by industry (cos 0.28)
- `mqvHlstCrC` health care industry — industry dedicated to providing health care services and products (cos 0.27)
- `oLaVpFCU4Z` tourism industry — economic sector related to tourism (cos 0.25)

## NYC family: Adults with asthma  (3 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:1297 | Adults with asthma, Number | Number | Adults age 18 and older who have ever been diagnosed with asthma. | Estimated number of adults aged 18 years and older who repor | Asthma & respiratory | 2020-2020 |
| ehdp:measure:1298 | Adults with asthma, Percent | Percent | Adults age 18 and older who have ever been diagnosed with asthma. | Estimated number of adults aged 18 years and older who repor | Asthma & respiratory | 2020-2020 |
| ehdp:measure:1299 | Adults with asthma, Age-adjusted percent | Age-adjusted percent | Adults age 18 and older who have ever been diagnosed with asthma. | Estimated number of adults aged 18 years and older who repor | Asthma & respiratory | 2020-2020 |

Supplement candidates (wider SPG, not in table above):
- `Jx2R43aZ7W` status asthmaticus — type of asthma (cos 0.54)
- `ICZJq4kU5i` anti-asthmatic agents — drugs used to treat asthma (cos 0.36)
- `zx_u-G7usE` adult — living organism that has reached sexual maturity (cos 0.3)

## NYC family: Carbon monoxide deaths  (3 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:1245 | Carbon monoxide deaths, Number (not fire-related) | Number (not fire-related) | Deaths due to carbon monoxide. These may be fire-related or non-fire-related. | Number of deaths with an underlying or contributing cause th | Air quality;Mortality | 2000-2017 |
| ehdp:measure:1244 | Carbon monoxide deaths, Number (fire-related) | Number (fire-related) | Deaths due to carbon monoxide. These may be fire-related or non-fire-related. | Number of deaths with an underlying or contributing cause th | Air quality;Mortality | 2000-2017 |
| ehdp:measure:1246 | Carbon monoxide deaths, Number (unknown cause) | Number (unknown cause) | Deaths due to carbon monoxide. These may be fire-related or non-fire-related. | Number of deaths with an underlying or contributing cause th | Air quality;Mortality | 2000-2017 |

Supplement candidates (wider SPG, not in table above):
- `XMVYV9chc_` iron carbonyl — any coordination compound with iron as a central atom and at least one (cos 0.35)
- `YRLawYAEXy` carboxyhemoglobin — complex of haemoglobin and carbon monoxide (cos 0.33)
- `gk67KSD-DC` PCO2 — partial pressure of carbon dioxide often used in reference to blood (cos 0.27)

## NYC family: Very old homes  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:27 | Very old homes, Percent | Percent | Homes built before 1950. Older housing can put residents at risk of lead poisoni | Number of housing units built before 1950, divided by all ho | Housing & indoor | 2000-2019 |
| ehdp:measure:26 | Very old homes, Number | Number | Homes built before 1950. Older housing can put residents at risk of lead poisoni | Number of housing units built before 1950. | Housing & indoor | 2000-2019 |

Supplement candidates (wider SPG, not in table above):
- `pWsHDC6odL` group home — home for multiple people with special needs (cos 0.29)
- `DwJ_rpoi1H` retirement home — housing facility intended for senior citizens (cos 0.26)

## NYC family: Owner-occupied homes  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:29 | Owner-occupied homes, Percent | Percent | Housing units occupied by their owner. | Estimated number of housing units occupied by the owner, div | Housing & indoor | 2007-2019 |
| ehdp:measure:232 | Owner-occupied homes, Number | Number | Housing units occupied by their owner. | Estimated number of housing units occupied by the owner. | Housing & indoor | 2007-2019 |

Supplement candidates (wider SPG, not in table above):
- `xKpz1v0hRQ` Bed Occupancy — A measure of inpatient health facility use based upon the average numb (cos 0.25)
- `pTS2fe-CmZ` partial pressure — hypothetical pressure of gas if it alone occupied the volume of the mi (cos 0.24)

## NYC family: Difficulty walking  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:1460 | Difficulty walking, Percent | Percent | People with disabilities or access needs that make it difficult to walk or climb | Percentage of all New Yorkers who have difficulty walking or | Housing & indoor | 2008-2019 |
| ehdp:measure:1459 | Difficulty walking, Number | Number | People with disabilities or access needs that make it difficult to walk or climb | Number of New Yorkers who have difficulty walking or climbin | Housing & indoor | 2008-2019 |

Supplement candidates (wider SPG, not in table above):
- `pLOxqX8Jnn` mobility disability — difficulty in walking (cos 0.51)
- `g3FMvCkMD4` difficulty concentrating — clinical symptom (cos 0.47)
- `C36RqDZlqe` six minute walking test —  (cos 0.39)

## NYC family: Rent burden  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:1029 | Rent burden, Percent | Percent | Renter households spending 30% of their income or more on rent. | Estimated number of renter households whose gross rent (rent | Housing & indoor;Social & economic | 2007-2017 |
| ehdp:measure:1028 | Rent burden, Number | Number | Renter households spending 30% of their income or more on rent. | Estimated number of renter households whose gross rent (rent | Housing & indoor;Social & economic | 2007-2017 |

Supplement candidates (wider SPG, not in table above):
- `LKpNtSYZwa` tumor burden — quantified total measure of tumor cells or tissue in the body (cos 0.52)
- `kDS5O8SPet` Global Burden of Disease — large recurring global health study (cos 0.44)
- `oqSNcJ1Eq6` viral load — amount of virus found in host tissue or a given volume of fluid (cos 0.34)

## NYC family: Limited English  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:1026 | Limited English, Number | Number | People who do not speak English at home and/or are not English proficient. | Estimated number of people who do not speak English at home  | Housing & indoor | 2007-2017 |
| ehdp:measure:1027 | Limited English, Percent | Percent | People who do not speak English at home and/or are not English proficient. | Estimated number of people who do not speak English at home  | Housing & indoor | 2007-2017 |

Supplement candidates (wider SPG, not in table above):
- `Ic3j2gkecR` limited English proficiency — term used in the United States for a person who is not fluent in the E (cos 0.66)
- `Iv1HUK5wgp` English — West Germanic language (cos 0.51)
- `Og3ui1WxaP` Channel Islands — archipelago in the English Channel (cos 0.36)

## NYC family: Older adults living alone (65+)  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:1060 | Older adults living alone (65+), Number | Number | People age 65+ living alone. People living alone may have more difficulty gettin | Estimated number of people aged 65 and older living alone. | Heat & temperature;Cardiovascular | 2007-2017 |
| ehdp:measure:693 | Older adults living alone (65+), Percent | Percent | People age 65+ living alone. People living alone may have more difficulty gettin | Percent of people aged 65 and older living alone | Heat & temperature;Cardiovascular | 2007-2017 |

Supplement candidates (wider SPG, not in table above):
- `zx_u-G7usE` adult — living organism that has reached sexual maturity (cos 0.39)
- `6EOtagmzeP` retirement community — town or housing complex for older adults who are generally able to car (cos 0.33)
- `VoeTkOuUYK` Elder Nutritional Physiological Phenomena — Nutritional physiology of adults aged 65 years of age and older. (cos 0.28)

## NYC family: Evictions  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:1128 | Evictions, Estimated annual rate | Estimated annual rate | Court-ordered evictions. Eviction often leads to residential instability, moving | Rate of executed evictions ordered by the New York City Hous | Housing & indoor | 2017-2022 |
| ehdp:measure:1127 | Evictions, Number | Number | Court-ordered evictions. Eviction often leads to residential instability, moving | Count of executed evictions ordered by the New York City Hou | Housing & indoor | 2017-2022 |

Supplement candidates (wider SPG, not in table above):
- `5tj83J2IMF` crime victim — victim of a crime (cos 0.29)
- `pfxSTacMAD` Restriction map —  (cos 0.24)

## NYC family: Commercial use of herbicides  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:209 | Commercial use of herbicides, Liquid products | Liquid products | Pesticides targeting unwanted weeds, grasses, vines and trees applied by profess | Sum of gallons of liquid pesticide applications that meet th | Housing & indoor;Green & built | 1999-2022 |
| ehdp:measure:210 | Commercial use of herbicides, Solid products | Solid products | Pesticides targeting unwanted weeds, grasses, vines and trees applied by profess | Sum of pounds of solid pesticide applications that meet the  | Housing & indoor;Green & built | 1999-2022 |

Supplement candidates (wider SPG, not in table above):
- `RsRHLzVNE9` herbicide — chemical used to kill unwanted plants (cos 0.57)
- `Go5d1nTk86` Catalogs, Commercial —  (cos 0.44)
- `xLtZvaVlIi` diquat — ion, active substance of a herbicide (cos 0.42)

## NYC family: Commercial use of insecticides (Pyrethroid/Pyrethrin)  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:214 | Commercial use of insecticides (Pyrethroid/Pyrethrin), Liquid products | Liquid products | Pyrethroids and Pyrethrins are less acutely toxic than some other insecticide cl | Sum of gallons of liquid pesticide applications that meet th | Asthma & respiratory | 1999-2022 |
| ehdp:measure:215 | Commercial use of insecticides (Pyrethroid/Pyrethrin), Solid products | Solid products | Pyrethroids and Pyrethrins are less acutely toxic than some other insecticide cl | Sum of pounds of solid pesticide applications that meet the  | Asthma & respiratory | 1999-2022 |

Supplement candidates (wider SPG, not in table above):
- `2NaEtunqCy` pyrethrin — group of chemical compounds (cos 0.47)
- `W3DRcIxD47` insecticide — pesticide used against insects (cos 0.38)
- `AG5EdenPcm` insecticide resistance — development by insects of resistance to insecticides (cos 0.33)

## NYC family: Commercial use of insecticides  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:207 | Commercial use of insecticides, Solid products | Solid products | Pesticides targeting insects, applied by professional exterminators or licensed  | Sum of pounds of solid pesticide applications that meet the  | Housing & indoor | 1999-2022 |
| ehdp:measure:206 | Commercial use of insecticides, Liquid products | Liquid products | Pesticides targeting insects, applied by professional exterminators or licensed  | Sum of gallons of liquid pesticide applications that meet th | Housing & indoor | 1999-2022 |

Supplement candidates (wider SPG, not in table above):
- `W3DRcIxD47` insecticide — pesticide used against insects (cos 0.59)
- `AG5EdenPcm` insecticide resistance — development by insects of resistance to insecticides (cos 0.51)
- `Go5d1nTk86` Catalogs, Commercial —  (cos 0.45)

## NYC family: Commercial use of insecticides (Organophosphate)  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:212 | Commercial use of insecticides (Organophosphate), Liquid products | Liquid products | Pesticides of this chemical class used to target insects, applied by professiona | Sum of gallons of liquid pesticide applications that meet th | Housing & indoor | 1999-2022 |
| ehdp:measure:213 | Commercial use of insecticides (Organophosphate), Solid products | Solid products | Pesticides of this chemical class used to target insects, applied by professiona | Sum of pounds of solid pesticide applications that meet the  | Housing & indoor | 1999-2022 |

Supplement candidates (wider SPG, not in table above):
- `W3DRcIxD47` insecticide — pesticide used against insects (cos 0.44)
- `AG5EdenPcm` insecticide resistance — development by insects of resistance to insecticides (cos 0.38)
- `N8rNwcUSHO` mevinphos — organophosphate insecticide (cos 0.36)

## NYC family: Commercial use of fungicides  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:686 | Commercial use of fungicides, Liquid products | Liquid products | Pesticides targeting type of fungus such as mold or plant blight applied by prof | Sum of gallons of liquid pesticide applications that meet th | Housing & indoor | 1999-2022 |
| ehdp:measure:211 | Commercial use of fungicides, Solid products | Solid products | Pesticides targeting type of fungus such as mold or plant blight applied by prof | Sum of pounds of solid pesticide applications that meet the  | Housing & indoor | 1999-2022 |

Supplement candidates (wider SPG, not in table above):
- `TBsyBcNA1b` fungicide — pesticide used to kill fungi (cos 0.59)
- `Go5d1nTk86` Catalogs, Commercial —  (cos 0.45)
- `XGryu0RaQ9` industrial fungicides — chemicals that kill or inhibit the growth of fungi in agricultural, in (cos 0.41)

## NYC family: Cigarette smoking (adults)  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:307 | Cigarette smoking (adults), Percent | Percent | Adults who are current smokers. Cigarette smoking is the leading cause of preven | Estimated number of adults in an area who report current, ac | Housing & indoor;Mortality | 2002-2022 |
| ehdp:measure:306 | Cigarette smoking (adults), Number | Number | Adults who are current smokers. Cigarette smoking is the leading cause of preven | Estimated number of adults who report current, active smokin | Housing & indoor;Mortality | 2002-2022 |

Supplement candidates (wider SPG, not in table above):
- `2Cgoxznk46` cigarette smoking — smoking of cigarettes (cos 0.81)
- `-A8uEoFnym` cigar smoking — smoking of cigars (cos 0.61)
- `Ffb62RPpp2` cigarette — small roll of cut drug (typically tobacco) designed to be smoked (cos 0.54)

## NYC family: Overweight  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:502 | Overweight, Percent | Percent | Adults reporting a Body Mass Index over 25. People who are overweight or obese a | Estimated number of adults classified as overweight or obese | Cardiovascular;Green & built | 2003-2022 |
| ehdp:measure:501 | Overweight, Number | Number | Adults reporting a Body Mass Index over 25. People who are overweight or obese a | Estimated number of adults classified as overweight or obese | Cardiovascular;Green & built | 2003-2022 |

Supplement candidates (wider SPG, not in table above):
- `slXbabUYMb` overweight — having a body mass index of 25.0–29.9 kg/m2 (cos 0.65)
- `6nzvcUJAdt` weight reduction programs — services providing counseling and activities that help overweight indi (cos 0.47)
- `ZrYY68i4Ow` underweight — classification of human body weight (cos 0.43)

## NYC family: Obesity  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:506 | Obesity, Percent | Percent | Adults reporting a Body Mass Index over 30. People who are overweight or obese a | Estimated number of adults classified as obese; based on the | Cardiovascular;Green & built | 2003-2022 |
| ehdp:measure:505 | Obesity, Number | Number | Adults reporting a Body Mass Index over 30. People who are overweight or obese a | Estimated number of adults classified as obese; based on the | Cardiovascular;Green & built | 2003-2022 |

Supplement candidates (wider SPG, not in table above):
- `1T_5mI3LDp` morbid obesity — human disease (cos 0.68)
- `G431f9lOWh` epidemiology of obesity — recognization of obesity as an epidemic (cos 0.61)
- `_Wi90i069L` childhood obesity — condition where excess body fat negatively affects a child's health or (cos 0.54)

## NYC family: Death (postneonatal)  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:16 | Death (postneonatal), Estimated annual rate | Estimated annual rate | Deaths from 28 days old to 1 year old. | Number of deaths occurring from 28 days to less than 1 year  | Mortality | 1998-2020 |
| ehdp:measure:15 | Death (postneonatal), Number | Number | Deaths from 28 days old to 1 year old. | Number of deaths occurring from 28 days to less than 1 year  | Mortality | 1998-2020 |

Supplement candidates (wider SPG, not in table above):
- `J-pNffWQLF` neonatal nursing —  (cos 0.36)
- `s9AiIn8qjW` neonatal anemia — Human disease (cos 0.35)
- `9kQTOQ7fam` neonatology — medical care of newborns, especially the ill or premature (cos 0.3)

## NYC family: Death (neonatal)  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:12 | Death (neonatal), Estimated annual rate | Estimated annual rate | Deaths among children less than 28 days old. | Number of deaths occurring at less than 28 days of age in an | Mortality | 1998-2020 |
| ehdp:measure:11 | Death (neonatal), Number | Number | Deaths among children less than 28 days old. | Number of deaths occurring at less than 28 days of age in an | Mortality | 1998-2020 |

Supplement candidates (wider SPG, not in table above):
- `J-pNffWQLF` neonatal nursing —  (cos 0.42)
- `s9AiIn8qjW` neonatal anemia — Human disease (cos 0.4)
- `9kQTOQ7fam` neonatology — medical care of newborns, especially the ill or premature (cos 0.35)

## NYC family: Death (infants)  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:9 | Death (infants), Number | Number | Death among children under 1 year old. | Number of deaths occurring at less than 1 year of age. Infan | Mortality | 1998-2020 |
| ehdp:measure:10 | Death (infants), Estimated annual rate | Estimated annual rate | Death among children under 1 year old. | Number of deaths occurring at less than 1 year of age in an  | Mortality | 1998-2020 |

Supplement candidates (wider SPG, not in table above):
- `Mi0ZeHbA57` infant health — physical and mental conditions of infants (cos 0.31)
- `qTaSECLkor` Infant Care — Care of infants in the home or institution. (cos 0.3)
- `jN1Lwro8uq` DAP — protein-coding gene in the species Homo sapiens (cos 0.24)

## NYC family: Carbon monoxide incidents  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:73 | Carbon monoxide incidents, Estimated annual rate | Estimated annual rate | A leak where the Fire Department measures at least 1 ppm of carbon monixide at t | Number of carbon monoxide incidents in an area, where FDNY m | Air quality | 2004-2016 |
| ehdp:measure:72 | Carbon monoxide incidents, Number | Number | A leak where the Fire Department measures at least 1 ppm of carbon monixide at t | Number of carbon monoxide incidents where FDNY measured at l | Air quality | 2004-2016 |

Supplement candidates (wider SPG, not in table above):
- `XMVYV9chc_` iron carbonyl — any coordination compound with iron as a central atom and at least one (cos 0.34)
- `YRLawYAEXy` carboxyhemoglobin — complex of haemoglobin and carbon monoxide (cos 0.32)
- `3W3jdc7kg1` mass-casualty incident — incident which results in medical care systems becoming overwhelmed (cos 0.3)

## NYC family: Supplemental heat  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:90 | Supplemental heat, Percent | Percent | Households using supplemental heat, like a space heater. This may mean a buildin | Estimated number of households in an area that needed to use | Heat & temperature;Housing & indoor | 1999-2023 |
| ehdp:measure:89 | Supplemental heat, Number | Number | Households using supplemental heat, like a space heater. This may mean a buildin | Estimated number of households that needed to use a secondar | Heat & temperature;Housing & indoor | 2002-2017 |

Supplement candidates (wider SPG, not in table above):
- `zZdL5r2-BH` dietary supplement — product that provides additional source of nutrients (cos 0.51)
- `R1e5KF9DNa` calcium supplement — calcium compounds used as food supplements or in food to supply the bo (cos 0.4)
- `9OkXcCXwNn` whey protein — protein supplement from milk (cos 0.4)

## NYC family: Leaks  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:80 | Leaks, Percent | Percent | Households reporting leaks from outside the unit. This maintenance problem can i | Estimated number of households in an area that reported leak | Asthma & respiratory;Housing & indoor | 1999-2023 |
| ehdp:measure:79 | Leaks, Number | Number | Households reporting leaks from outside the unit. This maintenance problem can i | Estimated number of households in an area that reported leak | Asthma & respiratory;Housing & indoor | 2002-2017 |

Supplement candidates (wider SPG, not in table above):
- `e-N5ftg08W` angioid streaks — Human disease (cos 0.39)

## NYC family: Cracks  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:76 | Cracks, Percent | Percent | Households reporting cracks or holes in the home. This maintenance problem is li | Estimated number of households in an area that reported crac | Housing & indoor | 1999-2023 |
| ehdp:measure:75 | Cracks, Number | Number | Households reporting cracks or holes in the home. This maintenance problem is li | Estimated number of households that reported cracks or holes | Housing & indoor | 2002-2017 |

Supplement candidates (wider SPG, not in table above):
- `uIUPbdxnRe` crack cocaine — smokable preparation of freebase cocaine (cos 0.35)
- `Lk___iP3Vl` Cracked tooth syndrome — medical condition (cos 0.33)
- `rGzDgyFqkH` crackles — respiratory condition (cos 0.27)

## NYC family: Homes with 3+ housing problems  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:86 | Homes with 3+ housing problems, Percent | Percent | Households reporting 3 or more housing problems. These can threaten the health o | Estimated number of households in an area reporting three or | Housing & indoor | 1999-2021 |
| ehdp:measure:85 | Homes with 3+ housing problems, Number | Number | Households reporting 3 or more housing problems. These can threaten the health o | Estimated number of households reporting three or more housi | Housing & indoor | 2002-2017 |

Supplement candidates (wider SPG, not in table above):
- `KDOTeHf7Mt` problem solving — using generic or ad hoc methods in an orderly manner to find solutions (cos 0.33)
- `uSECT_2bz9` social issue — problem that influences a considerable number of individuals within a  (cos 0.33)
- `DwJ_rpoi1H` retirement home — housing facility intended for senior citizens (cos 0.3)

## NYC family: Health insurance (adults)  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:672 | Health insurance (adults), Percent | Percent | Adults with any kind of health insurance. People with health insurance are more  | Estimated number of adults who reported having any kind of h | Mortality | 2012-2022 |
| ehdp:measure:671 | Health insurance (adults), Number | Number | Adults with any kind of health insurance. People with health insurance are more  | Estimated number of adults who reported having any kind of h | Mortality | 2012-2022 |

Supplement candidates (wider SPG, not in table above):
- `0xDFgJAfrX` private health insurance — type of organization (cos 0.59)
- `1r25L-2lSx` Value-Based Insurance Design — type of health insurance (cos 0.55)
- `dgw4-XU6sq` long-term care insurance — type of insurance (cos 0.51)

## NYC family: Renter-occupied homes with no housing problems  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:759 | Renter-occupied homes with no housing problems, Percent | Percent | Renter-occupied homes reporting no housing problems. Healthy homes are free of h | Estimated number of renter-occupied households reporting no  | Housing & indoor | 2002-2023 |
| ehdp:measure:758 | Renter-occupied homes with no housing problems, Number | Number | Renter-occupied homes reporting no housing problems. Healthy homes are free of h | Estimated number of renter-occupied households reporting no  | Housing & indoor | 2002-2017 |

Supplement candidates (wider SPG, not in table above):
- `KDOTeHf7Mt` problem solving — using generic or ad hoc methods in an orderly manner to find solutions (cos 0.23)
- `uSECT_2bz9` social issue — problem that influences a considerable number of individuals within a  (cos 0.23)
- `DwJ_rpoi1H` retirement home — housing facility intended for senior citizens (cos 0.22)

## NYC family: Mice or rats (in the building)  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:94 | Mice or rats (in the building), Percent | Percent | Households reporting mice or rats in their building in the past 90 days (from wh | Estimated number of households in an area that reported mice | Asthma & respiratory;Housing & indoor | 1999-2017 |
| ehdp:measure:93 | Mice or rats (in the building), Number | Number | Households reporting mice or rats in their building in the past 90 days (from wh | Estimated number of households that reported mice or rats in | Asthma & respiratory;Housing & indoor | 2002-2017 |

Supplement candidates (wider SPG, not in table above):
- `COEFxSZVXO` construction — economic activity that consists of the building or assembling of a bui (cos 0.39)
- `jCrN64TC75` building — structure, typically with a roof and walls, standing more or less perm (cos 0.35)
- `xkijW_XwI2` building material — material used for construction purposes (cos 0.31)

## NYC family: Neighborhood building quality  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:88 | Neighborhood building quality, Percent | Percent | Building quality predicts the number of housing maintenance problems in a reside | Estimated number of households in an area that rated their n | Housing & indoor | 1999-2017 |
| ehdp:measure:87 | Neighborhood building quality, Number | Number | Building quality predicts the number of housing maintenance problems in a reside | Estimated number of households that rated their neighborhood | Housing & indoor | 2002-2017 |

Supplement candidates (wider SPG, not in table above):
- `1eDAwPTGNu` neighborhood — geographically localised community within a larger city, town or subur (cos 0.44)
- `2gR7THM-gS` neighborhood characteristics — characteristics of a residential area influencing the lift of its resi (cos 0.44)
- `beUHqr6So5` MIATNB — non-coding RNA in the species Homo sapiens (cos 0.36)

## NYC family: Death before 65  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:983 | Death before 65, Age-adjusted rate | Age-adjusted rate | Deaths before age 65. This can indicate the overall health of a population. | Average annual rate of premature deaths (death before age 65 | Mortality | 2014-2020 |
| ehdp:measure:1230 | Death before 65, Number | Number | Deaths before age 65. This can indicate the overall health of a population. | Number of deaths occurring before age 65. | Mortality | 2014-2020 |

Supplement candidates (wider SPG, not in table above):
- `X-jqh6j95g` stillbirth — death of a fetus before or during delivery, resulting in delivery of a (cos 0.39)
- `dKCoscHHI_` controlled before-after study — study in which observations are made before and after an intervention, (cos 0.28)
- `jN1Lwro8uq` DAP — protein-coding gene in the species Homo sapiens (cos 0.28)

## NYC family: Smoke-free homes  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:292 | Smoke-free homes, Percent | Percent | Adults without a smoke-free home policy. A smoke-free home policy can limit peop | Estimated number of adults in an area without a policy that  | Housing & indoor | 2002-2013 |
| ehdp:measure:298 | Smoke-free homes, Number | Number | Adults without a smoke-free home policy. A smoke-free home policy can limit peop | Estimated number of adults without a policy that prohibits s | Housing & indoor | 2002-2013 |

Supplement candidates (wider SPG, not in table above):
- `JPVciSoX7p` smoking ban — public policies, including criminal laws and occupational safety and h (cos 0.49)
- `PDDW6UukdU` smoker — person who smokes (cos 0.39)
- `8Xv5d6HSQV` ex-smokers — persons who do not smoke but have a history of smoking (cos 0.27)

## NYC family: Housing problems  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:1248 | Housing problems, Percent | Percent | Renter-occupied homes with any health-related housing problems. Homes with housi | Estimated number of renter-occupied households reporting any | Housing & indoor | 2014-2023 |
| ehdp:measure:1247 | Housing problems, Number | Number | Renter-occupied homes with any health-related housing problems. Homes with housi | Estimated number of renter-occupied households reporting any | Housing & indoor | 2014-2017 |

Supplement candidates (wider SPG, not in table above):
- `KDOTeHf7Mt` problem solving — using generic or ad hoc methods in an orderly manner to find solutions (cos 0.38)
- `uSECT_2bz9` social issue — problem that influences a considerable number of individuals within a  (cos 0.36)
- `u3fn84wwCW` oral hygiene — practice of keeping the mouth and teeth clean to prevent dental proble (cos 0.28)

## NYC family: Death (perinatal)  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:13 | Death (perinatal), Number | Number | Deaths from 28 weeks of pregnancy to 6 days old. | Number of fetal deaths occurring at 28 or more weeks gestati | Mortality | 1998-2011 |
| ehdp:measure:14 | Death (perinatal), Estimated annual rate | Estimated annual rate | Deaths from 28 weeks of pregnancy to 6 days old. | Number of fetal deaths occurring at 28 or more weeks gestati | Mortality | 1998-2011 |

Supplement candidates (wider SPG, not in table above):
- `aJYOA5y3UG` perinatal disease — type of human disease (cos 0.29)
- `nnQGb5_DMK` perinatal care — care of women and a fetus or newborn given before, during, and after d (cos 0.25)
- `jN1Lwro8uq` DAP — protein-coding gene in the species Homo sapiens (cos 0.23)

## NYC family: Secondhand smoke  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:47 | Secondhand smoke, Percent | Percent | Adults reporting secondhand smoke at home. Secondhand smoke, especially indoors, | Estimated number of adults in an area exposed to second-hand | Housing & indoor | 2004-2012 |
| ehdp:measure:46 | Secondhand smoke, Number | Number | Adults reporting secondhand smoke at home. Secondhand smoke, especially indoors, | Estimated number of adults exposed to second-hand smoke at h | Housing & indoor | 2004-2012 |

Supplement candidates (wider SPG, not in table above):
- `PDDW6UukdU` smoker — person who smokes (cos 0.44)
- `qsn9G63cwk` tobacco smoke pollution — contamination of the air by tobacco smoke (cos 0.38)
- `Bgy96PVCs9` tobacco smoke — aerosol produced by the incomplete combustion of tobacco (cos 0.37)

## NYC family: Peeling paint  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:78 | Peeling paint, Percent | Percent | Housing built before 1960 with peeling paint. This can put residents at risk of  | Estimated number of households in an area that were built be | Housing & indoor | 2011-2017 |
| ehdp:measure:77 | Peeling paint, Number | Number | Housing built before 1960 with peeling paint. This can put residents at risk of  | Estimated number of households in an area that were built be | Housing & indoor | 2011-2017 |

Supplement candidates (wider SPG, not in table above):
- `cygOlHQiSF` chemexfoliation —  (cos 0.45)
- `jxmpUa6P2f` pain — type of unpleasant feeling (cos 0.28)
- `ClQuazVonb` painting — visual artwork, surface artistically covered with paint (cos 0.27)

## NYC family: Home fall ED visits  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:1281 | Home fall ED visits, Rate | Rate | Emergency department visits due to home falls (age 65+). Falls are a leading cau | Because of slight variations between datasets, results might | Housing & indoor | 2018-2023 |
| ehdp:measure:1282 | Home fall ED visits, Number | Number | Emergency department visits due to home falls (age 65+). Falls are a leading cau | Because of slight variations between datasets, results might | Housing & indoor | 2018-2023 |

Supplement candidates (wider SPG, not in table above):
- `90fz4aqYPE` Office Visits — Visits made by patients to health service providers' offices for diagn (cos 0.32)
- `gcZd__sJci` home health nursing — nursing specialty (cos 0.29)
- `3HvZT1of0h` Visitors to Patients — Patients' guests and rules for visiting. (cos 0.23)

## NYC family: Home fall hospitalizations  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:1280 | Home fall hospitalizations, Number | Number | Hospitalizations due to home falls (age 65+). Falls are a leading cause of injur | Because of slight variations between datasets, results might | Housing & indoor | 2018-2023 |
| ehdp:measure:1279 | Home fall hospitalizations, Rate | Rate | Hospitalizations due to home falls (age 65+). Falls are a leading cause of injur | Because of slight variations between datasets, results might | Housing & indoor | 2018-2023 |

Supplement candidates (wider SPG, not in table above):
- `M6F-TJO4S3` hospitalized child — child hospitalized for short term care (cos 0.46)
- `HqtWmsegwf` rural hospital — hospital (cos 0.44)
- `kCxzkek5LN` State hospital —  (cos 0.43)

## NYC family: Coastal flood risk  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:1410 | Coastal flood risk, Number | Number | Hurricane Evacuation Zones are determined by New York City Emergency Management  | Number of neighborhood residents living within 2024 NYC Emer | Climate & weather | 2024-2024 |
| ehdp:measure:687 | Coastal flood risk, Percent | Percent | Hurricane Evacuation Zones are determined by New York City Emergency Management  | Percent of neighborhood residents living within 2024 NYC Eme | Climate & weather | 2024-2024 |

Supplement candidates (wider SPG, not in table above):
- `2UUx_s45iv` relative risk — in statistics and epidemiology (cos 0.28)
- `Lkorx-4hNq` risk assessment — analysis with risk acceptance criteria or other decision parameters (cos 0.24)
- `61q4sykRmH` risk factor — variable or factor associated with an increased risk of disease or inf (cos 0.23)

## NYC family: Secondhand smoke at work  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:309 | Secondhand smoke at work, Percent | Percent | Adults reporting secondhand smoke at work. Secondhand smoke, especially indoors, | Estimated number of adults in an area exposed to second-hand | Housing & indoor | 2002-2007 |
| ehdp:measure:308 | Secondhand smoke at work, Number | Number | Adults reporting secondhand smoke at work. Secondhand smoke, especially indoors, | Estimated number of adults exposed to second-hand smoke at w | Housing & indoor | 2002-2007 |

Supplement candidates (wider SPG, not in table above):
- `PDDW6UukdU` smoker — person who smokes (cos 0.38)
- `qsn9G63cwk` tobacco smoke pollution — contamination of the air by tobacco smoke (cos 0.33)
- `Bgy96PVCs9` tobacco smoke — aerosol produced by the incomplete combustion of tobacco (cos 0.32)

## NYC family: Adults with air conditioners  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:636 | Adults with air conditioners, Percent | Percent | Adults reporting having an air conditioner. Air conditioning reduces the risk of | Estimated number of adults who reported having a functioning | Heat & temperature;Cardiovascular | 2007-2022 |
| ehdp:measure:635 | Adults with air conditioners, Number | Number | Adults reporting having an air conditioner. Air conditioning reduces the risk of | Estimated number of adults who reported having a functioning | Heat & temperature;Cardiovascular | 2007-2022 |

Supplement candidates (wider SPG, not in table above):
- `zx_u-G7usE` adult — living organism that has reached sexual maturity (cos 0.28)
- `A_WS5HdQs5` nurse practitioner — profession (cos 0.27)
- `7tbk11vFEK` Latent autoimmune diabetes — medical condition (cos 0.26)

## NYC family: Mice or rats (outside)  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:45 | Mice or rats (outside), Percent | Percent | Mice and rats are a source of household allergens connected to developing or wor | Estimated number of adults reporting mice or rats outside th | Asthma & respiratory | 2004-2020 |
| ehdp:measure:44 | Mice or rats (outside), Number | Number | Mice and rats are a source of household allergens connected to developing or wor | Estimated number of adults reporting mice or rats outside th | Asthma & respiratory | 2004-2020 |

Supplement candidates (wider SPG, not in table above):
- `3a7WLWUQj1` Murinae — subfamily of rodents (cos 0.23)

## NYC family: Deaths from PM2.5  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:1176 | Deaths from PM2.5, Estimated annual number (age 30+) | Estimated annual number (age 30+) | Estimated annual deaths due to PM2.5 air pollution. Estimating these deaths is a | Estimated annual number of all-cause deaths associated with  | Air quality;Mortality | 2005-2017 |
| ehdp:measure:639 | Deaths from PM2.5, Estimated annual rate (age 30+) | Estimated annual rate (age 30+) | Estimated annual deaths due to PM2.5 air pollution. Estimating these deaths is a | Estimated annual number of all-cause deaths associated with  | Air quality;Mortality | 2005-2017 |

Supplement candidates (wider SPG, not in table above):
- `jtzZPZ8DQh` PM 2.5 — particulates of 2.5 micrometers or less (cos 0.26)
- `jK9LiCuxDQ` vital statistics — statistics on live births, deaths, fetal deaths, marriages and divorce (cos 0.23)
- `uqRI_-RaDr` opioid epidemic — deaths due to abuse of opioid drugs (cos 0.22)

## NYC family: Deaths from ozone  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:652 | Deaths from ozone, Estimated annual rate | Estimated annual rate | Deaths due to cardiac or respiratory issues linked to ozone. These show how air  | Estimate is based on the number of cardiovascular and respir | Air quality;Asthma & respiratory;Mortality | 2005-2017 |
| ehdp:measure:1183 | Deaths from ozone, Estimated annual number | Estimated annual number | Deaths due to cardiac or respiratory issues linked to ozone. These show how air  | Estimate is based on the number of cardiovascular and respir | Air quality;Asthma & respiratory;Mortality | 2005-2017 |

Supplement candidates (wider SPG, not in table above):
- `JVHcy7JsEZ` thioacetazone — chemical compound (cos 0.24)
- `jK9LiCuxDQ` vital statistics — statistics on live births, deaths, fetal deaths, marriages and divorce (cos 0.23)
- `uqRI_-RaDr` opioid epidemic — deaths due to abuse of opioid drugs (cos 0.23)

## NYC family: PM2.5 health burden (heart)  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:651 | PM2.5 health burden (heart), Estimated annual rate | Estimated annual rate | Hospitalizations for cardiovascular issues due to PM2.5 (among people over age 4 | Estimate is based on the number of hospitalizations for card | Air quality;Cardiovascular | 2005-2017 |
| ehdp:measure:1177 | PM2.5 health burden (heart), Estimated annual number | Estimated annual number | Hospitalizations for cardiovascular issues due to PM2.5 (among people over age 4 | Estimate is based on the number of hospitalizations for card | Air quality;Cardiovascular | 2005-2017 |

Supplement candidates (wider SPG, not in table above):
- `kDS5O8SPet` Global Burden of Disease — large recurring global health study (cos 0.34)
- `LKpNtSYZwa` tumor burden — quantified total measure of tumor cells or tissue in the body (cos 0.32)
- `atmwEK1Z8M` family health — health status of the family as a unit (cos 0.25)

## NYC family: PM2.5 health burden (lungs)  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:650 | PM2.5 health burden (lungs), Estimated annual rate | Estimated annual rate | Hospitalizations for respiratory issues due to PM2.5 pollution (among people ove | Estimate is based on the number of hospitalizations for resp | Air quality;Asthma & respiratory | 2005-2017 |
| ehdp:measure:1178 | PM2.5 health burden (lungs), Estimated annual number | Estimated annual number | Hospitalizations for respiratory issues due to PM2.5 pollution (among people ove | Estimate is based on the number of hospitalizations for resp | Air quality;Asthma & respiratory | 2005-2017 |

Supplement candidates (wider SPG, not in table above):
- `kDS5O8SPet` Global Burden of Disease — large recurring global health study (cos 0.33)
- `LKpNtSYZwa` tumor burden — quantified total measure of tumor cells or tissue in the body (cos 0.32)
- `atmwEK1Z8M` family health — health status of the family as a unit (cos 0.23)

## NYC family: Carbon monoxide  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:716 | Carbon monoxide, Average annual rate | Average annual rate | Carbon monoxide incidents when there was no alarm. Carbon monoxide detectors are | A 3-year Average annual rate of carbon monoxide incidents wh | Air quality;Housing & indoor;Mortality | 2011-2014 |
| ehdp:measure:715 | Carbon monoxide, Average annual number | Average annual number | Carbon monoxide incidents when there was no alarm. Carbon monoxide detectors are | A 3-year Average annual number of carbon monoxide incidents  | Air quality;Housing & indoor;Mortality | 2011-2014 |

Supplement candidates (wider SPG, not in table above):
- `XMVYV9chc_` iron carbonyl — any coordination compound with iron as a central atom and at least one (cos 0.44)
- `YRLawYAEXy` carboxyhemoglobin — complex of haemoglobin and carbon monoxide (cos 0.42)
- `gk67KSD-DC` PCO2 — partial pressure of carbon dioxide often used in reference to blood (cos 0.34)

## NYC family: Heat Vulnerability Index  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:1288 | Heat Vulnerability Index, Score | Score | The risk of community-level heat impacts, like deaths, due to extreme heat event | Each neighborhood receives a score from 1 (lowest risk) to 5 | Heat & temperature;Mortality;Green & built;Social & economic | 2023-2023 |
| ehdp:measure:822 | Heat Vulnerability Index, Score | Score | The risk of community-level heat impacts like deaths due to extreme heat events. | Each neighborhood receives a score from 1 (lowest risk) to 5 | Heat & temperature;Mortality;Green & built;Social & economic | 2023-2023 |

Supplement candidates (wider SPG, not in table above):
- `s8NLcc5cT6` vulnerable population — persons whose range of options is severely limited, are subjected to c (cos 0.43)
- `zcDFTr3tu6` health disparity, minority and vulnerable populations — groups of persons recognsed as vulnerable and possibly having limited  (cos 0.38)
- `jW7bSg_lln` social vulnerability — inability of people, organizations, and societies to withstand adverse (cos 0.37)

## NYC family: Neighborhood safety  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:1058 | Neighborhood safety, Percent | Percent | Adults reporting their neighborhood is safe from crime. Whether people perceive  | Estimated number of adults who reported living in a neighbor | Green & built | 2015-2016 |
| ehdp:measure:892 | Neighborhood safety, Number | Number | Adults reporting their neighborhood is safe from crime. Whether people perceive  | Estimated number of adults who reported living in a neighbor | Green & built | 2015-2016 |

Supplement candidates (wider SPG, not in table above):
- `2gR7THM-gS` neighborhood characteristics — characteristics of a residential area influencing the lift of its resi (cos 0.49)
- `1eDAwPTGNu` neighborhood — geographically localised community within a larger city, town or subur (cos 0.47)
- `beUHqr6So5` MIATNB — non-coding RNA in the species Homo sapiens (cos 0.4)

## NYC family: Pneumoconiosis hospitalizations  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:877 | Pneumoconiosis hospitalizations, Number (age 15+) | Number (age 15+) | Hospitalizations for pneumoconiosis, a lung disease caused by breathing in certa | Number of hospitalizations with a pneumoconiosis ICD-9-CM di | Asthma & respiratory | 2001-2016 |
| ehdp:measure:874 | Pneumoconiosis hospitalizations, Average annual rate | Average annual rate | Hospitalizations for pneumoconiosis, a lung disease caused by breathing in certa | Number of hospitalizations with a pneumoconiosis ICD-9-CM di | Asthma & respiratory | 2001-2016 |

Supplement candidates (wider SPG, not in table above):
- `WA9Jud8NKo` silicosis — pneumoconiosis that is an inflammation and scarring of the upper lobes (cos 0.48)
- `xU4qBZM3Je` pneumoconiosis — interstitial lung disease that is caused by the inhalation of dust (cos 0.47)
- `Rbalp6imET` asbestosis — pneumoconiosis caused by inhalation and retention of asbestos fibers (cos 0.44)

## NYC family: Asbestosis hospitalizations  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:879 | Asbestosis hospitalizations, Number (age 15+) | Number (age 15+) | Hospitalizations for asbestosis. Asbestos is a naturally-occurring mineral which | Number of hospitalizations with an asbestosis ICD-9-CM diagn | Asthma & respiratory | 2001-2016 |
| ehdp:measure:871 | Asbestosis hospitalizations, Average annual rate | Average annual rate | Hospitalizations for asbestosis. Asbestos is a naturally-occurring mineral which | Number of hospitalizations with an asbestosis ICD-9-CM diagn | Asthma & respiratory | 2001-2016 |

Supplement candidates (wider SPG, not in table above):
- `Rbalp6imET` asbestosis — pneumoconiosis caused by inhalation and retention of asbestos fibers (cos 0.47)
- `wNj4j7Xq_b` amosite asbestos — substance (cos 0.45)
- `jmOp_fN53S` serpentine asbestos — type of asbestos that occurs in nature as the dihydrate of magnesium s (cos 0.41)

## NYC family: Older adults with AC  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:706 | Older adults with AC, Percent | Percent | Older adults (over 65) are more vulnerable to hot weather and heat stress. Air c | Estimated number of adults age 65 years or older who reporte | Heat & temperature;Cardiovascular | 2013-2013 |
| ehdp:measure:705 | Older adults with AC, Number | Number | Older adults (over 65) are more vulnerable to hot weather and heat stress. Air c | Estimated number of adults age 65 years or older who reporte | Heat & temperature;Cardiovascular | 2013-2013 |

Supplement candidates (wider SPG, not in table above):
- `VoeTkOuUYK` Elder Nutritional Physiological Phenomena — Nutritional physiology of adults aged 65 years of age and older. (cos 0.34)
- `zx_u-G7usE` adult — living organism that has reached sexual maturity (cos 0.33)
- `JX1K3nvW41` geriatric nursing — specialty of nursing pertaining to older adults (cos 0.33)

## NYC family: Mice or rats (inside)  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:634 | Mice or rats (inside), Percent | Percent | Mice and rats are a source of household allergens connected to developing or wor | Estimated number of adults reporting mice or rats inside the | Asthma & respiratory;Housing & indoor | 2012-2012 |
| ehdp:measure:633 | Mice or rats (inside), Number | Number | Mice and rats are a source of household allergens connected to developing or wor | Estimated number of adults reporting mice or rats inside the | Asthma & respiratory;Housing & indoor | 2012-2012 |

Supplement candidates (wider SPG, not in table above):
- `3a7WLWUQj1` Murinae — subfamily of rodents (cos 0.26)

## NYC family: Tetralogy of Fallot  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:812 | Tetralogy of Fallot, Number | Number | Tetralogy of Fallot is a congenital heart defect that affects how blood flows th | Number of live births diagnosed with Tetralogy of Fallot and | Cardiovascular | 2000-2010 |
| ehdp:measure:813 | Tetralogy of Fallot, Prevalence | Prevalence | Tetralogy of Fallot is a congenital heart defect that affects how blood flows th | Number of live births diagnosed with Tetralogy of Fallot and | Cardiovascular | 2000-2010 |

Supplement candidates (wider SPG, not in table above):
- `Eg5BCw9XOJ` tetralogy of Fallot — congenital heart defect, whose symptoms include episodes of bluish ski (cos 0.55)
- `ajNkjVBuxd` tetralone — any organic compound with a tetraline (tetrahydronaphthalene) backbone (cos 0.29)
- `q-RWqpqBFK` fallopian tube disease — Human disease (cos 0.24)

## NYC family: Hypoplastic left heart syndrome  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:796 | Hypoplastic left heart syndrome, Number | Number | A rare birth defect where part of the heart is underdeveloped. | Number of live births diagnosed with hypoplastic left heart  | Cardiovascular | 2000-2010 |
| ehdp:measure:797 | Hypoplastic left heart syndrome, Prevalence | Prevalence | A rare birth defect where part of the heart is underdeveloped. | Number of live births diagnosed with hypoplastic left heart  | Cardiovascular | 2000-2010 |

Supplement candidates (wider SPG, not in table above):
- `O3v2HT2Eth` left ear —  (cos 0.38)
- `GGsan7hN1y` paraneoplastic syndrome — Medical effects of tumors besides mass effect (cos 0.36)
- `hkwCregFT7` Verloove Vanhorick-Brubakk syndrome —  (cos 0.35)

## NYC family: TGA  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:814 | TGA, Number | Number | A congenital heart defect that involves abnormal arrangement of parts of the hea | Number of live births diagnosed with transposition of the gr | Cardiovascular | 2000-2010 |
| ehdp:measure:815 | TGA, Prevalence | Prevalence | A congenital heart defect that involves abnormal arrangement of parts of the hea | Number of live births diagnosed with transposition of the gr | Cardiovascular | 2000-2010 |

## NYC family: Cigarette smoking (youth)  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:310 | Cigarette smoking (youth), Number | Number | High school students who smoked in the past 30 days (from when they were surveye | Estimated number of high school students who smoked cigarett | Housing & indoor;Mortality | 1997-2017 |
| ehdp:measure:311 | Cigarette smoking (youth), Percent | Percent | High school students who smoked in the past 30 days (from when they were surveye | Estimated number of high school students who smoked cigarett | Housing & indoor;Mortality | 1997-2017 |

Supplement candidates (wider SPG, not in table above):
- `2Cgoxznk46` cigarette smoking — smoking of cigarettes (cos 0.78)
- `-A8uEoFnym` cigar smoking — smoking of cigars (cos 0.59)
- `Ffb62RPpp2` cigarette — small roll of cut drug (typically tobacco) designed to be smoked (cos 0.52)

## NYC family: Obesity (youth)  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:507 | Obesity (youth), Number | Number | Youths reporting a Body Mass Index over 30. People who are overweight or obese a | Estimated number of high school students classified as obese | Cardiovascular;Green & built | 2003-2017 |
| ehdp:measure:508 | Obesity (youth), Percent | Percent | Youths reporting a Body Mass Index over 30. People who are overweight or obese a | Estimated number of high school students classified as obese | Cardiovascular;Green & built | 2003-2017 |

Supplement candidates (wider SPG, not in table above):
- `1T_5mI3LDp` morbid obesity — human disease (cos 0.45)
- `G431f9lOWh` epidemiology of obesity — recognization of obesity as an epidemic (cos 0.41)
- `_Wi90i069L` childhood obesity — condition where excess body fat negatively affects a child's health or (cos 0.36)

## NYC family: Overweight or obesity (youth)  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:503 | Overweight or obesity (youth), Number | Number | Youths reporting a Body Mass Index over 25. People who are overweight or obese a | Estimated number of high school students classified as overw | Cardiovascular;Green & built | 2003-2017 |
| ehdp:measure:504 | Overweight or obesity (youth), Percent | Percent | Youths reporting a Body Mass Index over 25. People who are overweight or obese a | Estimated number of high school students classified as overw | Cardiovascular;Green & built | 2003-2017 |

Supplement candidates (wider SPG, not in table above):
- `slXbabUYMb` overweight — having a body mass index of 25.0–29.9 kg/m2 (cos 0.43)
- `b-digE4fD_` weight loss treatment — medical intervention to counter obesity (cos 0.39)
- `eCNV2eYZAg` Obesity hypoventilation syndrome — condition in which severely overweight people fail to breathe rapidly  (cos 0.37)

## NYC family: Work-related deaths (all industries)  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:883 | Work-related deaths (all industries), Estimated annual rate | Estimated annual rate | Fatal, work-related injuries. These include deaths resulting from unintentional  | Number of fatal work-related injuries occurring in NYC and r | Mortality | 1992-2014 |
| ehdp:measure:882 | Work-related deaths (all industries), Number | Number | Fatal, work-related injuries. These include deaths resulting from unintentional  | Number of fatal work-related injuries occurring in NYC and r | Mortality | 1992-2014 |

Supplement candidates (wider SPG, not in table above):
- `qArJF-9vso` industrial development — planning and building of industries (cos 0.32)
- `3tietCkdPo` industrial production — totality of all goods that are generated by industry (cos 0.27)
- `HqxTpbak_m` industrial oils — oils used for industrial or commercial applications (cos 0.25)

## NYC family: Children living with cockroaches  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:1232 | Children living with cockroaches, Percent | Percent | Children living in homes with reported cockroaches. The saliva, feces, and shedd | Estimated number of children ages 0-13 years living in a hom | Asthma & respiratory;Housing & indoor | 2017-2023 |
| ehdp:measure:1242 | Children living with cockroaches, Number | Number | Children living in homes with reported cockroaches. The saliva, feces, and shedd | Estimated number of children ages 0-13 years living in a hom | Asthma & respiratory;Housing & indoor | 2017-2023 |

Supplement candidates (wider SPG, not in table above):
- `cL7f0l1roH` Blattellidae — cockroaches family (cos 0.58)
- `JgRYwtm5Zx` cockroach — paraphyletic group of winged insects of the order Blattodea (cos 0.56)
- `vZsgUBQ-3d` disabled child — child with mental or physical disabilities that interfere with usual a (cos 0.33)

## NYC family: Children ever diagnosed with asthma  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:1228 | Children ever diagnosed with asthma, Percent | Percent | Children ages 1 to 13 that have ever received an asthma diagnosis. | Estimated number of children ages 1-13 years who were ever d | Asthma & respiratory | 2017-2023 |
| ehdp:measure:1229 | Children ever diagnosed with asthma, Number | Number | Children ages 1 to 13 that have ever received an asthma diagnosis. | Estimated number of children ages 1-13 years who were ever d | Asthma & respiratory | 2017-2023 |

Supplement candidates (wider SPG, not in table above):
- `Jx2R43aZ7W` status asthmaticus — type of asthma (cos 0.41)
- `SXX22KGNRb` undiagnosed diseases — rare and common diseases lacking a diagnosis (cos 0.35)
- `piFEP9lptK` child health — concept of wellbeing (cos 0.31)

## NYC family: Children in homes with visible mold or mildew (age 1-13)  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:1369 | Children in homes with visible mold or mildew (age 1-13), Percent | Percent | Children who live in homes with visible mold/mildew. Mold and mildew can trigger | Estimated number of children ages 1-13 years living in priva | Asthma & respiratory;Housing & indoor | 2019-2023 |
| ehdp:measure:1368 | Children in homes with visible mold or mildew (age 1-13), Number | Number | Children who live in homes with visible mold/mildew. Mold and mildew can trigger | Estimated number of children ages 1-13 years living in priva | Asthma & respiratory;Housing & indoor | 2019-2023 |

Supplement candidates (wider SPG, not in table above):
- `piFEP9lptK` child health — concept of wellbeing (cos 0.29)
- `du4LooAe8F` child — human between birth and puberty (cos 0.28)
- `kS7V3937tL` only child — child without siblings (cos 0.28)

## NYC family: Children with a recent asthma attack  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:1367 | Children with a recent asthma attack, Percent | Percent | Children ages 1 to 13 who have had an asthma attack in the past 12 months from w | Estimated number of children ages 1-13 years who reported ha | Asthma & respiratory | 2017-2023 |
| ehdp:measure:1366 | Children with a recent asthma attack, Number | Number | Children ages 1 to 13 who have had an asthma attack in the past 12 months from w | Estimated number of children ages 1-13 years who reported ha | Asthma & respiratory | 2017-2023 |

Supplement candidates (wider SPG, not in table above):
- `Jx2R43aZ7W` status asthmaticus — type of asthma (cos 0.5)
- `piFEP9lptK` child health — concept of wellbeing (cos 0.32)
- `ZivTPiXSKN` suicide attack — attack in which the attacker knows they will die (cos 0.3)

## NYC family: Mold  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:624 | Mold, Number | Number | Adults reporting mold in the home. Mold can worsen respiratory conditions like a | Estimated number of adults reporting mold or mildew on their | Asthma & respiratory;Housing & indoor | 2019-2019 |
| ehdp:measure:625 | Mold, Percent | Percent | Adults reporting mold in the home. Mold can worsen respiratory conditions like a | Estimated number of adults reporting mold or mildew on their | Asthma & respiratory;Housing & indoor | 2019-2019 |

Supplement candidates (wider SPG, not in table above):
- `lfUHCEVpVQ` Mucorales — order of fungi (cos 0.51)

## NYC family: Asthma (youth)  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:1040 | Asthma (youth), Percent | Percent | Public high school students who reported having an asthma attack in the past 12  | Estimated number of public high school students who reported | Asthma & respiratory | 2007-2017 |
| ehdp:measure:1039 | Asthma (youth), Number | Number | Public high school students who reported having an asthma attack in the past 12  | Estimated number of public high school students who reported | Asthma & respiratory | 2007-2017 |

Supplement candidates (wider SPG, not in table above):
- `Jx2R43aZ7W` status asthmaticus — type of asthma (cos 0.47)
- `ICZJq4kU5i` anti-asthmatic agents — drugs used to treat asthma (cos 0.34)
- `rKXFwqBwxv` youth sports — sport practiced by youth (cos 0.22)

## NYC family: Children in homes with mice (age 1-13)  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:1234 | Children in homes with mice (age 1-13), Percent | Percent | Children living in homes with reported mice. The presence of mice is associated  | Estimated number of children ages 0-13 years living in a hom | Asthma & respiratory;Housing & indoor | 2017-2021 |
| ehdp:measure:1233 | Children in homes with mice (age 1-13), Number | Number | Children living in homes with reported mice. The presence of mice is associated  | Estimated number of children ages 0-13 years living in a hom | Asthma & respiratory;Housing & indoor | 2017-2021 |

Supplement candidates (wider SPG, not in table above):
- `piFEP9lptK` child health — concept of wellbeing (cos 0.34)
- `du4LooAe8F` child — human between birth and puberty (cos 0.33)
- `nHt-mj7d-7` child psychiatry — medical science concerned with mental disorders in children (cos 0.32)

## NYC family: Secondhand smoke exposure at home (children)  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:1259 | Secondhand smoke exposure at home (children), Percent | Percent | The number of children aged 1-13 years exposed to tobacco smoke at home. Secondh | Estimated number of children aged 1-13 years living in a hom | Asthma & respiratory;Housing & indoor | 2019-2023 |
| ehdp:measure:1258 | Secondhand smoke exposure at home (children), Number | Number | The number of children aged 1-13 years exposed to tobacco smoke at home. Secondh | Estimated number of children aged 1-13 years living in a hom | Asthma & respiratory;Housing & indoor | 2019-2023 |

Supplement candidates (wider SPG, not in table above):
- `Qh_S6WHgEN` war exposure —  (cos 0.39)
- `BTY-9NoskE` toxin exposure — concept in toxicology (cos 0.34)
- `VllUJmqrNV` exposure to violence — experience of and exposure to violence (cos 0.3)

## NYC family: Children still with asthma  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:1370 | Children still with asthma, Number | Number | Children ages 1 to 13 that currently have asthma. Not every asthma diagnosis is  | Estimated number of children ages 1-13 years who reported st | Asthma & respiratory;Housing & indoor | 2019-2023 |
| ehdp:measure:1371 | Children still with asthma, Percent | Percent | Children ages 1 to 13 that currently have asthma. Not every asthma diagnosis is  | Estimated number of children ages 1-13 years who reported st | Asthma & respiratory;Housing & indoor | 2019-2023 |

Supplement candidates (wider SPG, not in table above):
- `Jx2R43aZ7W` status asthmaticus — type of asthma (cos 0.46)
- `piFEP9lptK` child health — concept of wellbeing (cos 0.35)
- `du4LooAe8F` child — human between birth and puberty (cos 0.33)

## NYC family: Citywide PM2.5  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:111 | Citywide PM2.5, PM2.5 annual average | PM2.5 annual average | Concentration of fine particles in the air. Fine particles are emitted by vehicl | This measure is calculated by averaging PM2.5 levels at each | Air quality | 2001-2024 |
| ehdp:measure:788 | Citywide PM2.5, PM2.5 98th percentile | PM2.5 98th percentile | Concentration of fine particles in the air. Fine particles are emitted by vehicl | 98% of PM2.5 measurements taken at New York City's EPA Air Q | Air quality | 2001-2024 |

Supplement candidates (wider SPG, not in table above):
- `jtzZPZ8DQh` PM 2.5 — particulates of 2.5 micrometers or less (cos 0.29)

## NYC family: Air quality action days  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:201 | Air quality action days, Days (sensitive groups) | Days (sensitive groups) | Days when air quality is unhealthy. Action days for sensitive groups are counted | An AQI value of 100 corresponds to the current U.S. standard | Air quality | 2003-2024 |
| ehdp:measure:200 | Air quality action days, Days (general population) | Days (general population) | Days when air quality is unhealthy. Action days for sensitive groups are counted | An AQI value of 100 corresponds to the current U.S. standard | Air quality | 2003-2024 |

Supplement candidates (wider SPG, not in table above):
- `xYmg9GfDNw` information quality — term to describe the quality of the content of information systems (cos 0.37)
- `ffqA-4i8HR` health care quality — level of quality and value provided by a health care resource (cos 0.37)
- `od3IfNnHB-` quality control — process or activity to ensure the quality of products and services pro (cos 0.35)

## NYC family: PM2.5 (Fine particles) action days  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:786 | PM2.5 (Fine particles) action days, Days (general population) | Days (general population) | Days when PM2.5 is at an unhealthy level. PM2.5 is emitted by combustion and are | When the daily average PM2.5 levels are above 150 on EPA's A | Air quality | 2003-2024 |
| ehdp:measure:785 | PM2.5 (Fine particles) action days, Days (sensitive groups) | Days (sensitive groups) | Days when PM2.5 is at an unhealthy level. PM2.5 is emitted by combustion and are | When the daily average PM2.5 levels are between 101 and 150  | Air quality | 2003-2024 |

Supplement candidates (wider SPG, not in table above):
- `jtzZPZ8DQh` PM 2.5 — particulates of 2.5 micrometers or less (cos 0.38)
- `Fwwu1s3wZA` dust — small particles in the air (cos 0.28)
- `MvDhgA79KG` beta particle — ionizing radiation (cos 0.27)

## NYC family: Ozone action days  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:787 | Ozone action days, Days (sensitive groups) | Days (sensitive groups) | Days when ozone levels are at unhealthy levels. Ozone is a common air pollutant  | When the daily average ozone levels are between 101 and 150  | Air quality;Asthma & respiratory | 2003-2024 |
| ehdp:measure:107 | Ozone action days, Days (general population) | Days (general population) | Days when ozone levels are at unhealthy levels. Ozone is a common air pollutant  | When the daily average ozone levels are above 150 on EPA's A | Air quality;Asthma & respiratory | 2003-2024 |

Supplement candidates (wider SPG, not in table above):
- `KAY3A9sT8A` snow day — day on which fall of snow is observed (cos 0.26)
- `JVHcy7JsEZ` thioacetazone — chemical compound (cos 0.25)
- `QfjLLuFwok` day — unit of time lasting 24 hours, derived from the period of Earth's rota (cos 0.22)

## NYC family: Children in homes with supplemental heat (age 13 and under)  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:1238 | Children in homes with supplemental heat (age 13 and under), Number | Number | Children living in homes that use supplemental heat. This housing problem can in | Estimated number of children ages 0-13 years living in a hom | Heat & temperature;Housing & indoor | 2017-2017 |
| ehdp:measure:1239 | Children in homes with supplemental heat (age 13 and under), Percent | Percent | Children living in homes that use supplemental heat. This housing problem can in | Estimated number of children ages 0-13 years living in a hom | Heat & temperature;Housing & indoor | 2017-2017 |

Supplement candidates (wider SPG, not in table above):
- `nHt-mj7d-7` child psychiatry — medical science concerned with mental disorders in children (cos 0.33)
- `piFEP9lptK` child health — concept of wellbeing (cos 0.32)
- `XKiaYPePt4` dental care for children — attention to the dental needs of children, including the prevention of (cos 0.31)

## NYC family: E-cigarette vapor exposure at home (children)  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:1336 | E-cigarette vapor exposure at home (children), Number | Number | The number of children aged 1-13 years exposed to e-cigarette smoke at home all  | Estimated number of children aged 1-13 years living in a hom | Housing & indoor | 2021-2021 |
| ehdp:measure:1337 | E-cigarette vapor exposure at home (children), Percent | Percent | The number of children aged 1-13 years exposed to e-cigarette smoke at home all  | Estimated number of children aged 1-13 years living in a hom | Housing & indoor | 2021-2021 |

Supplement candidates (wider SPG, not in table above):
- `59SJNq_Hne` e-cigarette vapor — complex mixture of vaporized chemicals emitted during the smoking of e (cos 0.58)
- `iO5hPrebfP` vape — device usually used to quit or be an alternative to tobacco (cos 0.44)
- `5Gts9oTP6V` vaping — practice of inhaling and exhaling the vapor produced by an electronic  (cos 0.38)

## NYC family: Children in homes with cracks or holes (age 1-13)  (2 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:1235 | Children in homes with cracks or holes (age 1-13), Number | Number | Children living in homes with cracks or holes in walls, ceilings, or floors. Thi | Estimated number of children ages 0-13 years living in homes | Asthma & respiratory;Housing & indoor | 2017-2017 |
| ehdp:measure:1236 | Children in homes with cracks or holes (age 1-13), Percent | Percent | Children living in homes with cracks or holes in walls, ceilings, or floors. Thi | Estimated number of children ages 0-13 years living in homes | Asthma & respiratory;Housing & indoor | 2017-2017 |

Supplement candidates (wider SPG, not in table above):
- `piFEP9lptK` child health — concept of wellbeing (cos 0.3)
- `du4LooAe8F` child — human between birth and puberty (cos 0.28)
- `nHt-mj7d-7` child psychiatry — medical science concerned with mental disorders in children (cos 0.28)

## NYC family: Ozone  (1 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:1435 | Ozone, Summer mean | Summer mean | Concentration of ozone in the air. Ozone is a common air pollutant that can harm | Air samples collected at specific NYCCAS monitoring sites al | Air quality;Asthma & respiratory | 2009-2025 |

Supplement candidates (wider SPG, not in table above):
- `JVHcy7JsEZ` thioacetazone — chemical compound (cos 0.37)
- `TLg8cq-b30` Ozolinone — chemical compound (cos 0.27)

## NYC family: Commercial use of rodenticides  (1 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:208 | Commercial use of rodenticides, Solid products | Solid products | Pesticides targeting rats and mice, applied by professional exterminators or lic | Sum of pounds of solid pesticide applications that are class | Housing & indoor | 1999-2022 |

Supplement candidates (wider SPG, not in table above):
- `ilXDKtVKMy` rodenticide — chemicals selected for killing rodents (cos 0.55)
- `Go5d1nTk86` Catalogs, Commercial —  (cos 0.43)
- `zZkCL2jHfh` Rodentia — order of mammals (cos 0.39)

## NYC family: Commercial use of "Best Practice" products  (1 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:218 | Commercial use of "Best Practice" products, Solid products | Solid products | Pesticides targeting insects, but have low toxicity or low potential for human e | Sum of pounds of solid pesticide applications that meet the  | Housing & indoor | 1999-2022 |

Supplement candidates (wider SPG, not in table above):
- `Go5d1nTk86` Catalogs, Commercial —  (cos 0.42)
- `j0A1zcxTqg` general dental practice —  (cos 0.27)
- `XNRDwCAAyj` defensive medicine — practice of recommending a diagnostic test or medical treatment that i (cos 0.26)

## NYC family: Sulfur dioxide  (1 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:1434 | Sulfur dioxide, Winter mean | Winter mean | Concentration of sulfur dioxide in the air. Sulfur dioxide comes from burning so | Data collected at specific NYCCAS monitoring sites along wit | Air quality | 2009-2016 |

Supplement candidates (wider SPG, not in table above):
- `dqIh31-nYb` sulfur oxide — any binary compound of sulfur and oxygen (cos 0.57)
- `l9sxMrfijd` sulfur compound — any chemical compound having at least one sulfur atom (cos 0.5)
- `zdgjHGsZ7J` isotope of sulfur —  (cos 0.47)

## NYC family: Park access  (1 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:1224 | Park access, Percent | Percent | The percentage of the population who live within walking distance to a park: a q | A map of "walk-to-a-park service areas" from the NYC Parks D | Green & built | 2017-2023 |

Supplement candidates (wider SPG, not in table above):
- `rer3OSuuIl` Patient record access —  (cos 0.4)
- `0L49tgF49-` health services accessibility — ease of individual access to care and services from the health care sy (cos 0.34)
- `uJyFp5TSE6` open-access publishing — open access publishing (cos 0.32)

## NYC family: Grass and tree cover  (1 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:690 | Grass and tree cover, Percent | Percent | Land covered by trees, grass, or other plants. Vegetative cover reduces temperat | Spatial information classifying ground cover is used to calc | Heat & temperature;Air quality;Green & built | 2010-2017 |

Supplement candidates (wider SPG, not in table above):
- `jDkmqz-8HD` snow cover — coverage of snow (cos 0.31)
- `9hCJVZmmGc` Eragrostis — genus of plants (cos 0.29)
- `cX8EqLrC9o` grassland — area with vegetation dominated by grasses (cos 0.28)

## NYC family: Surface temperature  (1 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:688 | Surface temperature, Degrees Fahrenheit | Degrees Fahrenheit | Spatial average of surface temperature, measured by satellite. Surface temperatu | Daytime landsat thermal data on surface, July 17, 2018, aver | Heat & temperature;Mortality | 2018-2018 |

Supplement candidates (wider SPG, not in table above):
- `dINFs04idR` hot — state of high relative temperature, often said about body temperature, (cos 0.55)
- `y8owuMrsFx` cold — relative or subjective state of low temperature (cos 0.53)
- `h0Aryv0NjW` hypothermia — human body core temperature below 35.0 °C (95.0 °F) (cos 0.5)

## NYC family: Homes with mold  (1 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:1422 | Homes with mold, Percent | Percent | Households reporting visible mold in the home. Mold can worsen respiratory condi | Estimated number of households that reported visible mold in | Asthma & respiratory;Housing & indoor | 2021-2023 |

Supplement candidates (wider SPG, not in table above):
- `pWsHDC6odL` group home — home for multiple people with special needs (cos 0.37)
- `lfUHCEVpVQ` Mucorales — order of fungi (cos 0.34)

## NYC family: Homes with mice or rats in the unit or building  (1 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:1424 | Homes with mice or rats in the unit or building, Percent | Percent | Households reporting mice or rats in their unit or building. The presence of mic | Estimated number of households that reported mice or rats in | Asthma & respiratory;Housing & indoor | 2021-2023 |

Supplement candidates (wider SPG, not in table above):
- `COEFxSZVXO` construction — economic activity that consists of the building or assembling of a bui (cos 0.38)
- `jCrN64TC75` building — structure, typically with a roof and walls, standing more or less perm (cos 0.38)
- `veYJYBMo_h` sick building syndrome — a medical condition where people in a building suffer from symptoms of (cos 0.3)

## NYC family: Bike lanes  (1 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:1226 | Bike lanes, Percent | Percent | Percent of street milage with bike lanes. Bike lanes can improve bicyclist and p | Percentage of street mileage with conventional and protected | Green & built | 2017-2017 |

Supplement candidates (wider SPG, not in table above):
- `bCExxZr1ew` motorcycle — two- or three-wheeled motor vehicle (cos 0.36)
- `3K3gx13Fco` BMP2K — protein-coding gene in the species Homo sapiens (cos 0.26)

## NYC family: Tree shade  (1 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:708 | Tree shade, Percent | Percent | The percent of a neighborhood that is shaded by trees. Tree shade can lower a ne | Tree canopy cover represents a 'top down' mapping perspectiv | Heat & temperature;Green & built | 2014-2014 |

Supplement candidates (wider SPG, not in table above):
- `SBPo9TJ8u9` Solanum — genus of plants (cos 0.26)
- `3C-u7cS1bu` biliary tract disease — disease involving the biliary tree (cos 0.24)
- `jF4gbq4H9F` Taxus — genus of plants or tree (cos 0.24)

## NYC family: Walkability  (1 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:673 | Walkability, Score | Score | A score that summarizes features that promote walking. These include density of  | Z-scores were calculated and summed across indicators of res | Housing & indoor;Green & built | 2011-2011 |

Supplement candidates (wider SPG, not in table above):
- `pLOxqX8Jnn` mobility disability — difficulty in walking (cos 0.38)
- `4Spq_PvliQ` Drug Stability —  (cos 0.37)
- `ioU1ls5KMB` Walk Test —  (cos 0.35)

## NYC family: Cold deaths  (1 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:1189 | Cold deaths, Number | Number | Deaths due to cold weather. These are part of the health burden of cold weather. | Number of deaths during cold season months of October-April  | Mortality | 1999-2022 |

Supplement candidates (wider SPG, not in table above):
- `VbhaEHYy0f` cold weather — weather cold enough to cause freezing (cos 0.35)
- `jK9LiCuxDQ` vital statistics — statistics on live births, deaths, fetal deaths, marriages and divorce (cos 0.28)
- `uqRI_-RaDr` opioid epidemic — deaths due to abuse of opioid drugs (cos 0.27)

## NYC family: Heat deaths  (1 measures)

| nyc_id | label | measurementType | indicator description | howCalculated | themes | years |
|---|---|---|---|---|---|---|
| ehdp:measure:534 | Heat deaths, Number | Number | Deaths directly attributed to heat, according to death certificates. Hot weather | Number of deaths during warm season months of May-September  | Heat & temperature;Mortality | 1999-2020 |

Supplement candidates (wider SPG, not in table above):
- `jK9LiCuxDQ` vital statistics — statistics on live births, deaths, fetal deaths, marriages and divorce (cos 0.3)
- `uqRI_-RaDr` opioid epidemic — deaths due to abuse of opioid drugs (cos 0.3)
- `6t2_El9p-a` HEATR3 — protein-coding gene in the species Homo sapiens (cos 0.28)