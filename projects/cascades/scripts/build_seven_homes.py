"""Summarise the 'seven homes' (England) multi-sensor monitors into per-home, per-transmitter air-quality stats.
Reads only the raw K0*.csv monitor files from the zip (does NOT unpickle the processed .pkl files)."""
import zipfile, io, sys, pandas as pd, numpy as np
Z = sys.argv[1] if len(sys.argv)>1 else 'external/raw2/seven_homes_england.zip'
P = 'Longitudinal environmental and ventilation practic/data/'
VARS = ['temp_c','rh_pct','co2_ppm','pm1_ugm3','pm25_ugm3','pm10_ugm3','airflow_mls','no2_ppm','co_ppm','voc_ppm']
z = zipfile.ZipFile(Z)
rows = []
for n in z.namelist():
    if not n.startswith(P) or '/data_unprocessed/' not in n: continue
    fn = n.split('/')[-1]
    if not (fn.startswith('K0') and fn.endswith('.csv')): continue
    home = n[len(P):].split('/')[0]
    raw = z.read(n).decode(errors='replace').splitlines()
    hdr = [l.split(',') for l in raw[:6]]
    serial = [x.strip() for x in hdr[4][1:]]; chan = [x.strip() for x in hdr[5][1:]]
    df = pd.read_csv(io.StringIO('\n'.join(raw[6:])), header=None, low_memory=False, dtype=str)
    del raw
    ts = pd.to_datetime(df[0], format='mixed', dayfirst=True, errors='coerce')
    for s_ in sorted(set(serial)):
        cols = {VARS['ABCDEFGHIJ'.index(c)]: j for j,(s2,c) in enumerate(zip(serial,chan), start=1) if s2==s_ and c and c in 'ABCDEFGHIJ'}
        g = pd.DataFrame({v: pd.to_numeric(df[j], errors='coerce').astype('float32') for v,j in cols.items() if j in df})
        g['ts'] = ts; g = g.dropna(subset=['ts'])
        if 'co2_ppm' in g: g = g[g.co2_ppm.notna()]
        if len(g)==0: continue
        d = {'home':home,'file':fn,'transmitter':s_,'start':g.ts.min().date(),'end':g.ts.max().date(),'n_readings':len(g)}
        for v in ['co2_ppm','pm25_ugm3','pm10_ugm3','no2_ppm','rh_pct','temp_c']:
            if v in g: d[v+'_median']=round(float(g[v].median()),3); d[v+'_p95']=round(float(g[v].quantile(.95)),3)
        if 'co2_ppm' in g:
            d['pct_time_co2_gt1000']=round(float((g.co2_ppm>1000).mean()*100),1); d['pct_time_co2_gt1500']=round(float((g.co2_ppm>1500).mean()*100),1)
        if 'pm25_ugm3' in g:
            daily=g.set_index('ts').pm25_ugm3.resample('D').mean().dropna()
            d['pct_days_pm25_gt_who15']=round(float((daily>15).mean()*100),1) if len(daily) else np.nan
        if 'rh_pct' in g: d['pct_time_rh_gt70']=round(float((g.rh_pct>70).mean()*100),1)
        rows.append(d)
    del df
out = pd.DataFrame(rows)
out['likely_outdoor'] = out.groupby('home').co2_ppm_median.transform('min').eq(out.co2_ppm_median) & (out.co2_ppm_median<550)
out.to_csv('data/seven_homes_summary.csv', index=False)
print(out[['home','transmitter','start','end','co2_ppm_median','pct_time_co2_gt1000','pm25_ugm3_median','pct_days_pm25_gt_who15','pct_time_rh_gt70','no2_ppm_median','likely_outdoor']].to_string())
