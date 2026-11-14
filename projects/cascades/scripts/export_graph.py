"""Export data/graph.json for the technical/graph view (and Christina's frontend).
nodes: intervention:<group>, exposure:<group>, outcome:<outcome>
edges: acts_on (intervention->exposure), worsens (crowding->ventilation/moisture exposure),
       evidence (intervention|exposure -> outcome) with study counts, UK counts, status, and up to N findings.
Gap edges (0 studies) are included for intervention->outcome with status 'no match under this search' so the view can draw them dashed."""
import json, math, pandas as pd, numpy as np
N_FIND = 30
ev = pd.read_csv('data/evidence.csv', low_memory=False)
gaps = pd.read_csv('data/gaps.csv')
src = pd.read_csv('data/sources.csv', dtype=str).fillna('')
GROUPS = ["Ventilation & source capture","Particle filtration","Clean cooking","Moisture & mould remediation","Radon mitigation",
          "Allergen & pest control (household)","Building fabric (insulation, airtightness)","Indoor temperature (heating & cooling)"]
CROWD = "Crowding (exposure)"
OUTCOMES = ["Infection","Asthma & wheeze","Other respiratory","Allergy & skin","Mental health & sleep","Cardiovascular","Cancer","Mortality & hospital use","Indoor exposure measured"]
COLORS = {"Ventilation & source capture":"#2E86AB","Particle filtration":"#6C5B7B","Clean cooking":"#E07A5F","Moisture & mould remediation":"#3D9970",
          "Radon mitigation":"#B8860B","Allergen & pest control (household)":"#C06C84","Building fabric (insulation, airtightness)":"#7F8C8D",
          "Indoor temperature (heating & cooling)":"#D35400",CROWD:"#34495E"}
PRI = gaps.drop_duplicates('group').set_index('group').air_quality_priority.to_dict()
def status(n): return "no match under this search" if n==0 else "thin (1-4 studies)" if n<5 else "moderate (5-19 studies)" if n<20 else "well studied (20+ studies)"
def clean(v):
    if v is None or (isinstance(v,float) and (math.isnan(v) or math.isinf(v))): return None
    if isinstance(v,(np.integer,)): return int(v)
    if isinstance(v,(np.floating,)): return float(v)
    if isinstance(v,(np.bool_,)): return bool(v)
    return v
k = ev[ev.relevance=='keep']; ctx = ev[ev.relevance=='context']
def short(g): return g.split(' (')[0]
def sources_for(g):
    key = short(g).split(' &')[0].lower()
    return src[src.groups_informed.str.lower().str.contains(key, regex=False) | src.groups_informed.str.lower().eq('all')].source_id.tolist()
cert = gaps[gaps.gap_type=='evidence: low certainty or null result'].groupby('group').note.apply(list).to_dict()
datag = gaps[gaps.gap_type=='data: no open linked dataset'].groupby('group').note.apply(list).to_dict()

CO = {
"Moisture & mould remediation":[("co_benefit","NHS cost of damp homes ~GBP 38m/yr","BRE"),("co_benefit","Fixing worst 65k Cat 1 damp homes ~GBP 250m","BRE")],
"Ventilation & source capture":[("co_benefit","School illness absence -1.6% per +1 L/s/person (observational)","MENDELL_VENT"),("trade_off","Heat loss / energy use (unquantified)","")],
"Particle filtration":[("co_benefit","Indoor PM2.5 -60% in HEPA trial","HAPI_HEPA"),("data_gap","No cost data","")],
"Clean cooking":[("co_benefit","Removes gas-hob methane leaks","CLASP_GAS_EU"),("data_gap","No cost data","")],
"Radon mitigation":[("co_benefit","New-build prevention ~GBP 11.4k/QALY","GRAY_RADON"),("trade_off","Retrofit ~GBP 36.8k/QALY (above NICE threshold)","GRAY_RADON")],
"Allergen & pest control (household)":[("trade_off","Single dust-mite measures: no benefit (Cochrane)","COCHRANE_HDM"),("data_gap","No cost data","")],
"Building fabric (insulation, airtightness)":[("co_benefit","Observed gas use -3.9% (loft) to -13.2% (solid wall)","NEED"),("co_benefit","Cold homes cost NHS ~GBP 540m/yr","BRE"),("trade_off","Damp risk if poorly installed: 98% EWI with major issues","NAO_ECO")],
"Indoor temperature (heating & cooling)":[("co_benefit","US weatherization ~USD 14k health/household benefit per home","WAP_ORNL"),("trade_off","Untargeted measures >GBP 100k/QALY; targeted favourable","NICE_NG6")]}
INTLABEL={"Moisture & mould remediation":"Fix damp & mould","Ventilation & source capture":"Improve ventilation","Particle filtration":"Filter the air (HEPA)",
"Clean cooking":"Clean cooking & heating","Radon mitigation":"Mitigate radon","Allergen & pest control (household)":"Control allergens & pests",
"Building fabric (insulation, airtightness)":"Insulate & seal","Indoor temperature (heating & cooling)":"Heat & cool adequately"}
nodes=[]; edges=[]
for g in GROUPS+[CROWD]:
    for role in (['exposure'] if g==CROWD else ['intervention','exposure']):
        s=k[(k.group==g)&(k.role==role)]
        nodes.append({'id':f'{role}:{g}','type':role,'label':short(g) if role=='intervention' else f'{short(g)} (exposure)','group':g,
            'color':COLORS[g],'air_quality_priority':PRI.get(g,''),'studies':int(s.study_id.nunique()),'uk_studies':int(s[s.is_uk==True].study_id.nunique()),
            'findings':int(len(s)),'context_studies':int(ctx[(ctx.group==g)&(ctx.role==role)].study_id.nunique()),
            'regions':{r:int(n) for r,n in s.drop_duplicates('study_id').study_region.value_counts().items()},
            'settings':{r:int(n) for r,n in s.drop_duplicates('study_id').setting.value_counts().items()},
            'certainty_notes':cert.get(g,[]) if role=='intervention' else [],'data_gaps':datag.get(g,[]) if role=='intervention' else [],
            'source_ids':sources_for(g),
            'action_label':INTLABEL.get(g,'') if role=='intervention' else '',
            'co_benefits':[{'kind':k_,'text':t_,'source_id':s_} for k_,t_,s_ in CO.get(g,[])] if role=='intervention' else []})
for o in OUTCOMES:
    nodes.append({'id':f'outcome:{o}','type':'outcome' if o!='Indoor exposure measured' else 'exposure_measure','label':o,'color':'#95A5A6'})
for g in GROUPS:
    edges.append({'id':f'acts_on:{g}','source':f'intervention:{g}','target':f'exposure:{g}','type':'acts_on'})
for t in ["Ventilation & source capture","Moisture & mould remediation"]:
    edges.append({'id':f'worsens:{t}','source':f'exposure:{CROWD}','target':f'exposure:{t}','type':'worsens','note':'team decision: crowding is an exposure that makes this worse'})
FCOLS=['association_id','study_id','pubmed_id','doi','variable_1_name','variable_2_name','statistic_type','statistic_value','ci_lower','ci_upper','p_value','p_value_equality','population','study_country','study_region','setting','is_trial']
for g in GROUPS+[CROWD]:
    for role in (['exposure'] if g==CROWD else ['intervention','exposure']):
        for o in OUTCOMES:
            s=k[(k.group==g)&(k.role==role)&(k.outcome_group==o)]
            n=int(s.study_id.nunique())
            if n==0 and role=='exposure': continue
            s2=s.assign(_uk=s.is_uk.astype(bool)).sort_values(['_uk','is_trial'],ascending=False)
            f=[{c:clean(r[c]) for c in FCOLS} for _,r in s2.head(N_FIND).iterrows()]
            for x in f:
                if isinstance(x.get('population'),str): x['population']=x['population'][:240]
            edges.append({'id':f'evidence:{role}:{g}->{o}','source':f'{role}:{g}','target':f'outcome:{o}','type':'evidence','role':role,
                'studies':n,'uk_studies':int(s[s.is_uk==True].study_id.nunique()),'findings_total':int(len(s)),'status':status(n),
                'is_gap':n==0,'findings':f,
                'expected_via_exposure_studies': int(k[(k.group==g)&(k.role=='exposure')&(k.outcome_group==o)].study_id.nunique()) if role=='intervention' else None})
meta={'title':'Indoor air interventions -> exposures -> health outcomes (System Public Graph v2.1 subset)',
      'source':'System Public Graph v2.1, Harvard Dataverse doi:10.7910/DVN/7V6JDO (CC BY-NC 4.0); labelled 14 Nov 2026',
      'counts_rule':'studies = distinct study_id with relevance=keep; findings = associations; UK = study population tagged UK',
      'status_labels':['no match under this search','thin (1-4 studies)','moderate (5-19 studies)','well studied (20+ studies)'],
      'caveats':['correlational findings, not causal effects','"no match" means none found by this search, not proven absence','~28% of studies have unknown country']}
json.dump({'meta':meta,'nodes':nodes,'edges':edges}, open('data/graph.json','w'), indent=1, default=str)
e=pd.DataFrame(edges)
print('nodes',len(nodes),'edges',len(edges),e.type.value_counts().to_dict(),'gap edges',int(e.is_gap.fillna(False).sum()))
import os; print('size KB', os.path.getsize('data/graph.json')//1024)
