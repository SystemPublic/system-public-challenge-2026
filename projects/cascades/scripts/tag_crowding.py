"""Add household crowding as an EXPOSURE linked to Ventilation and Moisture & mould (team decision Nov 14).
Strict crowding terms -> relevance 'keep'; household-size proxies (no room denominator) -> 'context'.
Appends to data/evidence.csv (idempotent: removes earlier Crowding rows first)."""
import re, duckdb, pandas as pd, warnings
warnings.filterwarnings('ignore')
import importlib.util, sys
sys.path.insert(0,'scripts')
from build_evidence import OUTCOMES
OUT = dict(OUTCOMES); OUT = {"Infection": r"tubercul|\btb\b|infect|pylori|haemophilus|meningoc|otitis|diarrh|syncytial|\brsv\b|covid|sars|influenza|scabies|rheumatic|carriage|pneumococ|measles", **OUT}
STRICT = r"overcrowd|crowding|crowded|persons? per room|people per room|occupants? per|household density$|higher household density|sharing a bedroom|level of crowding"
PROXY  = r"household size|number of (people|persons|occupants|family members|household members)|large household|small household|larger household|greater number of occupants"
EXC = (r"dental|teeth|tooth|molar|incisor|maxillary|labial|malocclus|fossa|pedicle|hospital|\bward\b|emergency|triage|icu|prison|jail|cafeteria|"
       r"nursing home|bed occupancy|private room|shared room|crowded places|crowded or chaotic|neighbou?rhood crowding|per square kilomet|sexual abuse|"
       r"cannabin|bed net|village|farm|sharing a bed|cell|molecul|visual|reading|stadium|transit|\bbus\b")
c = duckdb.connect('retrofit.duckdb', read_only=True)
a = c.execute("select * from associations").df()
st = c.execute("select study_id, doi, population_string, study_type from studies").df()
rows=[]
for _,r in a.iterrows():
    for side,other in [(r.variable_1_name, r.variable_2_name),(r.variable_2_name, r.variable_1_name)]:
        s=str(side or '').lower()
        if re.search(EXC, s+' '+str(other or '').lower()): continue
        strict = bool(re.search(STRICT, s)); proxy = bool(re.search(PROXY, s))
        if not (strict or proxy): continue
        o=str(other or '').lower()
        og = next((k for k,rx in OUT.items() if re.search(rx,o)), 'Other')
        rows.append({'group':'Crowding (exposure)','role':'exposure','matched_variable':side,'other_variable':other,'outcome_group':og,
            'association_id':r.system_id,'study_id':r.study_id,'pubmed_id':r.pubmed_id,'statistic_type':r.statistic_type,'statistic_value':r.statistic_value,
            'ci_lower':r.ci_lower,'ci_upper':r.ci_upper,'p_value':r.p_value,'p_value_equality':r.p_value_equality,
            'variable_1_name':r.variable_1_name,'variable_2_name':r.variable_2_name,'review_status':'candidate','match_method':'keyword',
            'name_key':s,'relevance':'keep' if strict else 'context',
            'linked_groups':'Ventilation & source capture; Moisture & mould remediation',
            'notes':'crowding = occupancy relative to space' if strict else 'household-size proxy (no room denominator)'})
        break
cr = pd.DataFrame(rows).merge(st, on='study_id', how='left').rename(columns={'population_string':'population'})
cr['is_trial'] = cr.study_type.fillna('').str.contains('trial', case=False)
ev = pd.read_csv('data/evidence.csv', low_memory=False)
ev = ev[ev.group!='Crowding (exposure)']
if 'linked_groups' not in ev: ev['linked_groups']=''
ev = pd.concat([ev, cr[[c for c in cr.columns if c in ev.columns or c=='linked_groups']]], ignore_index=True)
ev['population']=ev.population.fillna('')
ev.to_csv('data/evidence.csv', index=False)
k=cr[cr.relevance=='keep']
print('crowding rows', len(cr), 'keep', len(k), 'studies keep', k.study_id.nunique(), 'context studies', cr[cr.relevance=='context'].study_id.nunique())
print(k.drop_duplicates(['study_id','outcome_group']).outcome_group.value_counts().to_dict())
