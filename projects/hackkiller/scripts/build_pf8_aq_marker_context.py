"""Observed crt K76T / mdr1 N86Y carrier shares, not inferred AQ resistance."""
from pathlib import Path
from collections import defaultdict, Counter
import csv,gzip,json

ROOT=Path(__file__).resolve().parents[1]
COUNTRIES={'BFA','MLI','NGA','GHA','GMB','TZA','BEN','KEN'}
MARKERS={'crt_76[K]':('crt_K76T','T'),'mdr1_86[N]':('mdr1_N86Y','Y')}

def main():
 samples=json.loads((ROOT/'data/processed/pf8_samples.json').read_text())
 eligible={r['sample_id']:r for r in samples if r['aggregation_eligible'] and r['country_iso3'] in COUNTRIES}
 counts=defaultdict(Counter)
 with gzip.open(ROOT/'data/processed/pf8_marker_calls.csv.gz','rt') as f:
  for r in csv.DictReader(f):
   if r['sample_id'] not in eligible or r['marker'] not in MARKERS:continue
   sample=eligible[r['sample_id']];label,variant=MARKERS[r['marker']]
   c=counts[(sample['country_iso3'],sample['year'],label)];c['n_total']+=1
   call=r['call_raw'].strip();alleles={x.strip() for x in call.split(',') if x.strip()}
   if not alleles or '-' in alleles or not all(len(x)==1 and x in 'ACDEFGHIKLMNPQRSTVWY' for x in alleles):
    c['n_missing_or_invalid']+=1;continue
   c['n_determined']+=1;c['n_mixed']+=len(alleles)>1
   c['n_variant_carrier']+=variant in alleles;c['n_variant_only']+=alleles=={variant}
 rows=[]
 for (iso,year,marker),c in sorted(counts.items()):
  rows.append({'iso3':iso,'year':year,'marker':marker,**{k:c[k] for k in ['n_total','n_determined','n_missing_or_invalid','n_variant_carrier','n_variant_only','n_mixed']},
   'variant_carrier_share':c['n_variant_carrier']/c['n_determined'] if c['n_determined'] else None,
   'scope':'sampled_cases_not_prevalence','interpretation':'marker_carriage_not_AQ_resistance_classification'})
 out=ROOT/'what-works-where/data/context/pf8_aq_markers_country_year.csv'
 with out.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 print('Marker context rows:',len(rows))

if __name__=='__main__':main()
