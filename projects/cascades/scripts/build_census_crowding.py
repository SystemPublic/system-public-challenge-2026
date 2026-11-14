"""Census 2021 TS052 -> % households overcrowded (occupancy rating bedrooms <= -1) by lower-tier LA and LSOA; joins onto la_context / lsoa_context.
RM099 (occupancy x tenure) -> % overcrowded among private and social renters by LA, if the file is present."""
import zipfile, io, re, os, pandas as pd
def read_zip(path, level):
    z=zipfile.ZipFile(path); n=[x for x in z.namelist() if x.lower().endswith(f'-{level}.csv')]
    if not n: print(path,'levels:',[x for x in z.namelist() if x.endswith('.csv')]); return None
    return pd.read_csv(io.BytesIO(z.read(n[0])))
def pct_overcrowded(d):
    code=[c for c in d.columns if c.lower().strip() in ('geography code','geography_code')][0]
    tot=[c for c in d.columns if re.search(r'total', c, re.I)][0]
    m1=[c for c in d.columns if re.search(r'rating of bedrooms: -1\b', c)]; m2=[c for c in d.columns if re.search(r'-2 or less', c)]
    o=pd.DataFrame({'code':d[code],'households_census':d[tot],'overcrowded_households':d[m1[0]]+d[m2[0]]})
    o['overcrowded_pct_census2021']=(o.overcrowded_households/o.households_census*100).round(2); return o
ts='external/raw3/census2021_ts052.zip'
if os.path.exists(ts):
    la=pct_overcrowded(read_zip(ts,'ltla')); ls=pct_overcrowded(read_zip(ts,'lsoa'))
    lc=pd.read_csv('data/la_context.csv'); lc=lc.drop(columns=[c for c in lc.columns if 'overcrowd' in c])
    lc=lc.merge(la[['code','overcrowded_pct_census2021']].rename(columns={'code':'lad_code'}),on='lad_code',how='left')
    lc.to_csv('data/la_context.csv',index=False); print('la matched', lc.overcrowded_pct_census2021.notna().sum(), '/', len(lc))
    so=pd.read_csv('data/lsoa_context.csv'); key=[c for c in so.columns if 'lsoa' in c.lower() and 'code' in c.lower()][0]
    so=so.drop(columns=[c for c in so.columns if 'overcrowd' in c]).merge(ls[['code','overcrowded_pct_census2021']].rename(columns={'code':key}),on=key,how='left')
    so.to_csv('data/lsoa_context.csv',index=False); print('lsoa matched', so.overcrowded_pct_census2021.notna().sum(), '/', len(so))
    print(lc[['overcrowded_pct_census2021','damp_pct_ehs2023','imd_score_popweighted','asthma_adm_u19_per100k']].corr(method='spearman').round(2))
else: print('missing', ts, '- run ./external/fetch_external3.sh')
