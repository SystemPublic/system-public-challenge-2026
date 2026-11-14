"""Evidence-strength proxy, per System Public Graph methods docs:
- null value from system_statistic_type (ratios -> 1, differences/coefficients/correlations -> 0)
- significance from the CI at its own ci_level (fallback 95%), else p-value with its equality qualifier
- trials from studies.study_type == 'Experimental Trial' (System's own flag)
- effect-size vs group-comparison split from system_statistic_type
Outputs per group x role (node) and per group x role x health group (edge). Associations, not causal estimates."""
import pandas as pd, numpy as np, json, duckdb
e=pd.read_csv('data/evidence.csv',low_memory=False); k=e[e.relevance=='keep'].copy()
c=duckdb.connect('retrofit.duckdb',read_only=True)
a=c.execute("select system_id, system_statistic_type sst, ci_level from associations").df()
stt=c.execute("select study_id, study_type from studies").df()
k=k.merge(a,left_on='association_id',right_on='system_id',how='left').merge(stt,on='study_id',how='left',suffixes=('','_sys'))
HO={'Asthma & wheeze':'resp','Other respiratory':'resp','Infection':'inf','Allergy & skin':'allergy','Cancer':'cancer','Cardiovascular':'heart','Mental health & sleep':'mental','Mortality & hospital use':'hosp'}
k=k[k.outcome_group.isin(HO)].copy(); k['ho']=k.outcome_group.map(HO)
sst=k.sst.fillna('').str.lower()
ratio=sst.str.contains('ratio')
k['effect_size']=sst.str.contains('ratio|coefficient|correlation|pearson|spearman|beta|risk_difference')
k['group_comp']=sst.str.contains('mean_difference|median|proportion|percent') & ~k.effect_size
null=np.where(ratio,1.0,0.0)
lo=pd.to_numeric(k.ci_lower,errors='coerce'); hi=pd.to_numeric(k.ci_upper,errors='coerce'); p=pd.to_numeric(k.p_value,errors='coerce')
peq=k.p_value_equality.fillna('').astype(str)
has_ci=lo.notna()&hi.notna()
k['testable']=has_ci|p.notna()
k['sig']=(has_ci&((lo>null)|(hi<null)))|((~has_ci)&p.notna()&(p<0.05)&~peq.str.contains('>'))
k['trial']=k.study_type_sys.fillna('').eq('Experimental Trial')
k['ci90']=pd.to_numeric(k.ci_level,errors='coerce').eq(0.9)
def summ(s,role):
    t=s[s.testable]; studies=s.study_id.nunique(); ts=t.study_id.nunique(); sg=t[t.sig].study_id.nunique()
    pct=round(100*sg/ts) if ts else None; trials=s[s.trial].study_id.nunique()
    findings=len(s); fs=int(s.effect_size.sum()); fg=int(s.group_comp.sum())
    if studies==0: lvl='None'
    elif role=='exposure': lvl='Strong' if studies>=20 and (pct or 0)>=60 else 'Moderate' if studies>=5 and (pct or 0)>=40 else 'Limited'
    else: lvl='Strong' if trials>=5 and (pct or 0)>=50 else 'Moderate' if studies>=5 and (pct or 0)>=40 else 'Limited'
    cons='consistent' if pct is not None and pct>=60 else ('mixed' if pct is not None and pct>=40 else ('mostly null' if pct is not None else 'untestable'))
    return {'studies':int(studies),'tested':int(ts),'significant':int(sg),'pct_sig':pct,'trials':int(trials),'findings':int(findings),'effect_size':fs,'group_comparison':fg,'level':lvl,'consistency':cons}
out={}
for (g,r),s in k.groupby(['group','role']):
    out.setdefault(g,{})[r]=summ(s,r)
    out[g][r]['by_outcome']={ho:summ(ss,r) for ho,ss in s.groupby('ho')}
json.dump(out,open('data/evidence_strength.json','w'),indent=1)
for g,v in out.items():
    print(g[:30].ljust(30), {r:(x['level'],x['studies'],x['pct_sig'],x['trials']) for r,x in v.items()})
d=out['Moisture & mould remediation']['exposure']['by_outcome']; print('damp exp by outcome', {h:(x['studies'],x['pct_sig'],x['consistency']) for h,x in d.items()})
