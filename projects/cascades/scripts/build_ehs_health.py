"""Tidy the EHS 2023-24 Health & Housing annex tables (AT4-AT16) into long form.
Blocks are separated by blank rows; each block's last row is its subtotal (e.g. 'owner occupiers'), used as the block name."""
import pandas as pd, numpy as np, sys
F = sys.argv[1] if len(sys.argv)>1 else 'external/raw2/ehs_2023_24_health_housing_annex.ods'
x = pd.read_excel(F, sheet_name=None, header=None, engine='odf')
toc = x['List_of_contents']; titles = {str(r[1]).strip(): str(r[2]).strip() for _,r in toc.iterrows() if str(r[1]).startswith('AT')}
out=[]
for sh in [f'AT{i}' for i in range(4,17)]:
    v = x[sh]
    # header row = row containing 'sample size'
    cand=[i for i in range(len(v)) if v.iloc[i].astype(str).str.contains('sample size',case=False).any()]
    if cand: hr=cand[0]
    else:
        first=next(i for i in range(len(v)) if sum(isinstance(c,(int,float)) and pd.notna(c) for c in v.iloc[i,2:])>=2)
        hr=max(i for i in range(first) if sum(isinstance(c,str) and c.strip()!='' for c in v.iloc[i,2:])>=2)
    headers = [str(h).strip() if pd.notna(h) else '' for h in v.iloc[hr]]
    units = ' '.join(str(u) for u in v.iloc[hr+1:hr+4].stack().dropna().tolist() if str(u).strip())
    block=[]; 
    def flush(block):
        if not block: return
        name = block[-1][0]
        for lab,vals in block:
            for h,val in zip(headers[2:],vals):
                if h and pd.notna(val) and isinstance(val,(int,float,np.floating)):
                    out.append({'table':sh,'title':titles.get(sh,''),'units':units,'block':name,'row':lab,'column':h,'value':float(val)})
    for i in range(hr+2,len(v)):
        r=v.iloc[i]; lab=r.iloc[1]
        nums=[c for c in r.iloc[2:] if isinstance(c,(int,float,np.floating)) and pd.notna(c)]
        if pd.isna(lab) or str(lab).strip()=='' :
            flush(block); block=[]; continue
        if nums: block.append((str(lab).strip(), list(r.iloc[2:])))
        elif str(lab).lower().startswith(('note','source','base')): flush(block); block=[]
    flush(block)
d=pd.DataFrame(out); d.to_csv('data/ehs_health_housing_long.csv',index=False)
print(len(d), d.table.value_counts().sort_index().to_dict())
# headline: share of households with long-term illness/disability, damp vs no damp, by tenure (AT7) and overcrowding (AT10)
for t,cond in [('AT7','damp present'),('AT10','overcrowded')]:
    s=d[d.table==t]; p=s.pivot_table(index=['block','row'],columns='column',values='value',aggfunc='first')
    ill=[c for c in p.columns if c.startswith('long-term')][0]; allc=[c for c in p.columns if c.replace(' ','').startswith('allhouseholds')][0]
    p['pct_ill']=(p[ill]/p[allc]*100).round(1); print(t); print(p[['pct_ill',allc]].to_string())
