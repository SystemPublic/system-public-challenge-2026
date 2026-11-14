"""Export AI-2 context contracts from first-pass processed files. No unit conversion."""
from pathlib import Path
import csv
import json

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'what-works-where/data/context'
CORE={'TZA','BEN','BFA','MLI','NGA'}
PF={'BFA','MLI','NGA','GHA','GMB','TZA','BEN','KEN'}
DRUGS={'Sulfadoxine','Pyrimethamine','SP (uncomplicated)','SP (IPTp)'}
HEADERS={
 'countries':'iso3,name,region,seasonality,showcase,in_who,in_map,in_pf8,notes',
 'context_country_year':'iso3,year,source,indicator,value,lower,upper,unit,estimate_type,release,flags',
 'pf8_sp_country_year':'iso3,year,drug,n_determined,n_resistant,n_sensitive,n_undetermined,resistant_share,scope',
}

def read(name):return json.loads((ROOT/'data/processed'/f'{name}.json').read_text())
def write(name,rows):
 with (OUT/f'{name}.csv').open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=HEADERS[name].split(','));w.writeheader();w.writerows(rows)

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 who,mp,pf=read('who_context'),read('map_context'),read('pf8_country_year_resistance')
 context=[]
 units={'percent_population':'percent','proportion':'proportion','people':'people',
        'cases_per_1000_population_at_risk':'per_1000_at_risk','cases_per_1000_population_per_year':'per_1000_per_year'}
 for r in who+mp:
  if r['country_iso3'] not in CORE:continue
  context.append({'iso3':r['country_iso3'],'year':r['year'],'source':r['source'],
    'indicator':r.get('indicator',r.get('metric')),'value':r['value'],'lower':r['lower'],'upper':r['upper'],
    'unit':units[r['unit']],'estimate_type':r['estimate_type'],'release':r.get('release',''),'flags':';'.join(r['flags'])})
 context.sort(key=lambda r:(r['iso3'],r['source'],r['indicator'],r['year']))
 keys=[(r['iso3'],r['year'],r['source'],r['indicator']) for r in context]
 assert len(keys)==len(set(keys)),'Conflicting context dimensions require review, not first-match selection'
 write('context_country_year',context)
 resistance=[{'iso3':r['country_iso3'],'year':r['year'],'drug':r['drug_or_combination'],
   'n_determined':r['n_determined'],'n_resistant':r['n_resistant'],'n_sensitive':r['n_sensitive'],
   'n_undetermined':r['n_undetermined'],'resistant_share':r['resistant_proportion_among_determined'],
   'scope':'sampled_cases_not_prevalence'} for r in pf if r['country_iso3'] in PF and r['drug_or_combination'] in DRUGS]
 resistance.sort(key=lambda r:(r['iso3'],r['year'],r['drug']))
 write('pf8_sp_country_year',resistance)
 specs=[('TZA','Tanzania','east_africa_perennial','perennial'),('BEN','Benin','west_africa_coastal','mixed'),
        ('BFA','Burkina Faso','sahel_seasonal','seasonal'),('MLI','Mali','sahel_seasonal','seasonal'),
        ('NGA','Nigeria','sahel_seasonal','mixed'),('GHA','Ghana','west_africa_coastal','mixed'),
        ('GMB','The Gambia','sahel_seasonal','seasonal'),('TCD','Chad','sahel_seasonal','seasonal'),
        ('UGA','Uganda','east_africa_perennial','perennial'),('KEN','Kenya','east_africa_perennial','perennial'),
        ('SEN','Senegal','sahel_seasonal','seasonal')]
 countries=[]
 for iso,name,region,seasonality in specs:
  notes=['coarse national grouping labels, not study-site facts; Pf8 has no amodiaquine classification (SP side only)']
  if iso=='NGA':notes.append('north seasonal, south perennial')
  years=sorted({r['year'] for r in pf if r['country_iso3']==iso})
  if iso=='BFA':notes.append('Pf8 sampled-case years: '+', '.join(map(str,years)))
  countries.append({'iso3':iso,'name':name,'region':region,'seasonality':seasonality,
    'showcase':'core' if iso in CORE else 'supporting',
    'in_who':str(any(r['country_iso3']==iso for r in who)).lower(),
    'in_map':str(any(r['country_iso3']==iso for r in mp)).lower(),
    'in_pf8':str(any(r['country_iso3']==iso for r in pf)).lower(),'notes':'; '.join(notes)})
 write('countries',countries)
 stats={'countries':len(countries),'context_rows':len(context),'who_rows':sum(r['source']=='WHO' for r in context),
        'map_rows':sum(r['source']=='MAP' for r in context),'pf8_sp_rows':len(resistance),
        'pf8_years':{iso:sorted({r['year'] for r in resistance if r['iso3']==iso}) for iso in sorted(PF)}}
 (ROOT/'reports/context_contract_summary.json').write_text(json.dumps(stats,indent=2)+'\n')
 print(json.dumps(stats,indent=2))

if __name__=='__main__':main()
