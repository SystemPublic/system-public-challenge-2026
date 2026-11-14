import json, sys
G=json.load(open(sys.argv[1]))
STR=json.load(open(sys.argv[3])) if len(sys.argv)>3 else {}
NONE={'studies':0,'tested':0,'significant':0,'pct_sig':None,'trials':0,'level':'None'}
nodes={n['id']:n for n in G['nodes']}; edges=G['edges']
ORDER=[("Moisture & mould remediation","Moisture & mould remediation"),("Building fabric (insulation, airtightness)","Insulation & building fabric"),
("Ventilation & source capture","Ventilation & source capture"),("Particle filtration","Particle filtration"),("Clean cooking","Combustion source control"),
("Radon mitigation","Radon testing & mitigation"),("Allergen & pest control (household)","Allergen & pest control"),("Indoor temperature (heating & cooling)","Heating, cooling & thermal comfort")]
EXPN={"Moisture & mould remediation":"damp & mould","Ventilation & source capture":"stale air / CO₂","Particle filtration":"airborne particles","Clean cooking":"combustion pollution","Radon mitigation":"radon","Allergen & pest control (household)":"allergens & pests","Building fabric (insulation, airtightness)":"cold, leaky fabric","Indoor temperature (heating & cooling)":"heat & cold exposure","Crowding (exposure)":"crowding"}
HO=[("resp","Asthma & respiratory",["Asthma & wheeze","Other respiratory"]),("inf","Infection",["Infection"]),("allergy","Allergy & skin",["Allergy & skin"]),
("cancer","Cancer",["Cancer"]),("heart","Heart & circulation",["Cardiovascular"]),("mental","Mental health & sleep",["Mental health & sleep"]),("hosp","Hospital use & deaths",["Mortality & hospital use"])]
COB=["01 · Energy & climate","02 · Affordability, equity & stability","03 · Comfort & resilience","04 · School, work & participation","05 · Outdoor air quality","06 · Healthcare & energy systems"]
CBH={
"Moisture & mould remediation":[(1,"benefit","W2","Private renters with damp: 48.9% vs 33.5% have a long-term illness (EHS 2023-24)","EHS_HH"),(2,"benefit","W1","Wetter winters raise damp risk (CCRA3)","CCC_ADAPT"),(5,"benefit","W1","Context: damp homes cost the NHS ~£38m/yr — not proven savings","BRE")],
"Ventilation & source capture":[(0,"harm","W1","Heat loss / energy use without heat recovery (unquantified)",""),(1,"benefit","W1","Matters most in overcrowded homes (Census 2021)","CENSUS_TS052"),(2,"benefit","W1","Night cooling during heatwaves (CCRA3)","CCC_ADAPT"),(3,"benefit","W1","Illness absence −1.6% per +1 L/s per pupil (162 Californian classrooms, observational)","MENDELL_VENT")],
"Particle filtration":[(0,"harm","W1","Electricity use (unquantified)","")],
"Clean cooking":[(0,"benefit","W1","Removes gas-hob methane leaks (lab tests)","CLASP_GAS_EU"),(5,"benefit","W1","Context: ~12% of EU child asthma modelled as linked to gas cooking (not peer reviewed)","CLASP_GAS_EU")],
"Radon mitigation":[(5,"mixed","W2","New build £11.4k/QALY (cost-effective); retrofit £36.8k/QALY (above NICE threshold)","GRAY_RADON")],
"Allergen & pest control (household)":[],
"Building fabric (insulation, airtightness)":[(0,"benefit","W2","Observed gas use −3.9% (loft) to −13.2% (solid wall)","NEED"),(1,"mixed","W2","Cost-effective only when targeted at at-risk households (NICE NG6)","NICE_NG6"),(2,"harm","W1","Sealed homes can overheat (CCRA3); poor installs risk damp — NAO found major issues in 98% of external wall insulation under ECO4/GBIS","NAO_ECO"),(5,"benefit","W1","Context: cold homes cost the NHS ~£540m/yr — not proven savings","BRE")],
"Indoor temperature (heating & cooling)":[(1,"benefit","W1","US weatherization: ~$14k health & household benefit per home","WAP_ORNL"),(2,"benefit","W1","Protects against heat and cold (CCRA3)","CCC_ADAPT"),(5,"mixed","W2","Untargeted >£100k/QALY; targeted at vulnerable households favourable (NICE NG6)","NICE_NG6")]}
def ekey(role,g,o): return f"evidence:{role}:{g}->{o}"
E={e['id']:e for e in edges}
def slim(f,kind):
    return {"k":kind,"a":f.get("variable_1_name"),"b":f.get("variable_2_name"),"st":f.get("statistic_type"),"v":f.get("statistic_value"),"lo":f.get("ci_lower"),"hi":f.get("ci_upper"),
            "c":f.get("study_country") or "Country not recorded","r":f.get("study_region") or "Unknown","doi":f.get("doi"),"pm":f.get("pubmed_id"),"trial":bool(f.get("is_trial"))}
def health_for(g, has_int=True):
    out={}
    for hk,hn,outs in HO:
        harm=harm_uk=direct=direct_uk=0; fs=[]
        for o in outs:
            ex=E.get(ekey("exposure",g,o))
            if ex: harm+=ex['studies']; harm_uk+=ex['uk_studies']; fs+= [slim(f,"exposure") for f in ex['findings'][:10]]
            if has_int:
                iv=E.get(ekey("intervention",g,o))
                if iv: direct+=iv['studies']; direct_uk+=iv['uk_studies']; fs=[slim(f,"intervention") for f in iv['findings'][:10]]+fs
        ps=STR.get(g,{}).get("exposure",{}).get("by_outcome",{}).get(hk,NONE); fs_=STR.get(g,{}).get("intervention",{}).get("by_outcome",{}).get(hk,NONE)
        out[hk]={"harm":harm,"harm_uk":harm_uk,"direct":direct,"direct_uk":direct_uk,"findings":fs[:14],"ps":ps,"fs":fs_}
    return out
ints=[]
for g,name in ORDER:
    ni=nodes[f"intervention:{g}"]; ne=nodes[f"exposure:{g}"]; h=health_for(g)
    ints.append({"key":g,"name":name,"exposure":EXPN[g],"harm_total":sum(v["harm"] for v in h.values()),"exp_studies":ne["studies"],"exp_uk":ne["uk_studies"],
      "direct":ni["studies"],"direct_uk":ni["uk_studies"],"regions":ne["regions"],"settings":ne["settings"],"int_settings":ni["settings"],"strength":{"p":STR.get(g,{}).get("exposure",NONE),"f":STR.get(g,{}).get("intervention",NONE)},"health":h,
      "cob":[{"g":j,"type":t,"w":w,"text":tx,"src":s} for j,t,w,tx,s in CBH[g]],"notes":ni.get("certainty_notes",[]),"gaps":ni.get("data_gaps",[]),"sources":ni.get("source_ids",[])})
nc=nodes["exposure:Crowding (exposure)"]; hc=health_for("Crowding (exposure)",False)
crowd={"key":"Crowding","name":"Crowding","exposure":"crowding","harm_total":sum(v["harm"] for v in hc.values()),"exp_studies":nc["studies"],"exp_uk":nc["uk_studies"],"direct":0,"direct_uk":0,"strength":{"p":STR.get("Crowding (exposure)",{}).get("exposure",NONE),"f":NONE},"regions":nc["regions"],"settings":nc["settings"],"health":hc,"worsens":["Moisture & mould remediation","Ventilation & source capture"]}
health=[{"key":hk,"name":hn,"total":sum(i["health"][hk]["harm"] for i in ints+[crowd]),"total_uk":sum(i["health"][hk]["harm_uk"] for i in ints+[crowd])} for hk,hn,_ in HO]
cobg=[{"i":j,"name":n,"n":sum(1 for i in ints if any(c["g"]==j for c in i["cob"]))} for j,n in enumerate(COB)]
DATA={"interventions":ints,"crowding":crowd,"health":health,"cob":cobg,
 "meta":{"studies":841,"unknown_country_pct":28.4,"uk_pct":2.0,"setting_unspecified_pct":37.5,"source":"System Public Graph v2.1 (Harvard Dataverse doi:10.7910/DVN/7V6JDO, CC BY-NC 4.0), curated subset labelled 14 Nov 2026; co-benefits and costs from cited reports (see sources)."}}
json.dump(DATA,open(sys.argv[2],'w'),separators=(',',':'),default=str)
import os; print('bytes',os.path.getsize(sys.argv[2]), [ (i['name'],i['harm_total'],i['direct']) for i in ints], crowd['harm_total'])
