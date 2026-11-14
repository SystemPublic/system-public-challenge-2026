"""Validate exact handoff schemas, conservation and published-value transformations."""
import csv,json,math
from pathlib import Path
from build_context_contracts import ROOT,OUT,HEADERS,CORE,PF,DRUGS
from check_context_fulltexts import FIELDS

def load(path):
 with path.open(newline='') as f:return list(csv.DictReader(f))

def main():
 tables={name:load(OUT/(name+'.csv')) for name in HEADERS}
 for name,header in HEADERS.items():
  assert list(tables[name][0])==header.split(','),name
 countries=tables['countries'];iso={r['iso3'] for r in countries};assert len(iso)==11
 context=tables['context_country_year'];assert {r['iso3'] for r in context}==CORE
 assert len({tuple(r[k] for k in ['iso3','year','source','indicator']) for r in context})==len(context)
 assert len(context)==len(json.loads((ROOT/'data/processed/who_context.json').read_text()))+len(json.loads((ROOT/'data/processed/map_context.json').read_text()))
 for r in context:
  assert r['unit'] in {'percent','proportion','per_1000_at_risk','per_1000_per_year','people'}
  assert r['estimate_type'] in {'modelled','reported_programme','survey_observed','sampled_cases'}
  assert r['source'] in {'WHO','MAP'}
  assert r['iso3'] in iso
  if r['source']=='MAP':assert r['release']=='202608'
  if r['indicator']=='MALARIA_IRS_COVERAGE':assert r['unit']=='people'
  for key in ['value','lower','upper']:
   if r[key]:assert math.isfinite(float(r[key]))
 resistance=tables['pf8_sp_country_year'];assert {r['iso3'] for r in resistance}==PF
 assert {r['drug'] for r in resistance}==DRUGS
 assert {r['year'] for r in resistance if r['iso3']=='BFA'}=={'2008'}
 assert len({(r['iso3'],r['year'],r['drug']) for r in resistance})==len(resistance)
 for r in resistance:
  assert r['scope']=='sampled_cases_not_prevalence'
  n=int(r['n_determined']);assert n==int(r['n_resistant'])+int(r['n_sensitive'])
  assert all(int(r[k])>=0 for k in ['n_resistant','n_sensitive','n_undetermined'])
  assert r['resistant_share']=='' if n==0 else math.isclose(float(r['resistant_share']),int(r['n_resistant'])/n)
 for r in countries:
  assert len(r['iso3'])==3 and r['iso3'].isupper()
  assert r['in_who']==str(any(x['iso3']==r['iso3'] and x['source']=='WHO' for x in context)).lower()
  assert r['in_map']==str(any(x['iso3']==r['iso3'] and x['source']=='MAP' for x in context)).lower()
 checks=load(ROOT/'what-works-where/data/verified/fulltext_checks.csv');assert list(checks[0])==FIELDS
 assert len(checks)==len({r['result_id'] for r in checks})==11
 for r in checks:
  assert len(r['quoted_text'])<=300
  assert r['value_found']=='Y' and r['ci_found']=='Y'
  assert r['matches_our_value'] in {'Y','N'} and r['checked_by']=='AI-2'
  if r['matches_our_value']=='N':assert r['discrepancy_note']
 audit=json.loads((ROOT/'reports/fulltext_check_audit.json').read_text())
 assert all(r['numerical_match'] for r in audit['checks'])
 assert sum(r['context_correction_required'] for r in audit['checks'])==3
 optional=load(OUT/'pf8_aq_markers_country_year.csv')
 for r in optional:
  n=int(r['n_determined']);assert n+int(r['n_missing_or_invalid'])==int(r['n_total'])
  assert 0<=int(r['n_variant_only'])<=int(r['n_variant_carrier'])<=n
  assert 0<=int(r['n_mixed'])<=n
  assert r['scope']=='sampled_cases_not_prevalence'
  if n:assert math.isclose(float(r['variant_carrier_share']),int(r['n_variant_carrier'])/n)
 print('PASS: exact schemas, five-country context, source units, unique keys, Pf8 denominator/BFA year, 11 full-text checks, 3 contextual discrepancies, marker summaries.')

if __name__=='__main__':main()
