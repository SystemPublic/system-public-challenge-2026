"""Pupil illness absence by LA (England) and RECS 2020 US gas/wood/induction shares."""
import pandas as pd, numpy as np
# --- pupil absence: LA level, all phases, all pupils
cols=['time_period','geographic_level','new_la_code','la_name','education_phase','characteristic','characteristic_breakdown','enrolments','sess_possible','sess_overall','sess_auth_illness','sess_overall_percent']
d=pd.read_csv('external/raw2/pupil_absence_by_characteristics.csv',usecols=cols,low_memory=False)
la=d[(d.geographic_level=='Local authority')&(d.education_phase=='Total')]
tot=la[la.characteristic.str.lower().eq('total')|la.characteristic_breakdown.str.lower().eq('total')]
if tot.empty: print('no total rows; characteristics:', la.characteristic.unique()[:20])
for c in ['sess_possible','sess_auth_illness','sess_overall','enrolments']: tot[c]=pd.to_numeric(tot[c],errors='coerce')
tot=tot.drop_duplicates(['time_period','new_la_code'])
tot['illness_absence_pct']=(tot.sess_auth_illness/tot.sess_possible*100).round(3)
tot['overall_absence_pct']=pd.to_numeric(tot.sess_overall_percent,errors='coerce')
out=tot[['time_period','new_la_code','la_name','enrolments','illness_absence_pct','overall_absence_pct']].rename(columns={'new_la_code':'la_code_edu'})
out.to_csv('data/pupil_absence_la.csv',index=False)
print('pupil absence rows', len(out), out.time_period.value_counts().sort_index().to_dict())
print(out[out.time_period==out.time_period.max()].illness_absence_pct.describe().round(2).to_dict())
# --- RECS 2020
r=pd.read_csv('external/raw2/recs2020_public_v7.csv',usecols=lambda c:c in ['DOEID','NWEIGHT','state_name','DIVISION','UGCOOK','LPCOOK','ELFOOD','WDWARM','RANGEINDT','COOKTOPINDT','RANGEFUEL','FUELHEAT','TYPEHUQ'])
w=r.NWEIGHT
def share(mask): return round(float((w*mask).sum()/w.sum()*100),1)
nat={'gas_cooking_pct':share(r.UGCOOK==1),'propane_cooking_pct':share(r.LPCOOK==1),'wood_heating_any_pct':share(r.WDWARM==1),
     'induction_pct':share((r.RANGEINDT==1)|(r.COOKTOPINDT==1))}
print('RECS national', nat)
g=r.groupby('state_name').apply(lambda s: pd.Series({'households_weighted':s.NWEIGHT.sum(),
   'gas_cooking_pct':(s.NWEIGHT*(s.UGCOOK==1)).sum()/s.NWEIGHT.sum()*100,
   'wood_heating_any_pct':(s.NWEIGHT*(s.WDWARM==1)).sum()/s.NWEIGHT.sum()*100})).round(1).reset_index()
g.to_csv('data/recs2020_state_cooking_heating.csv',index=False)
print(g.sort_values('gas_cooking_pct',ascending=False).head(5).to_string())
