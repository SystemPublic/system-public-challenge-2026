"""Validate the single-file handoff, its provenance and frontend-safe separation."""
import csv,hashlib,json,math
from pathlib import Path
from build_frontend_bundle import ROOT,OUTPUT,CORE,build

def main():
 data=json.loads(OUTPUT.read_text(),parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)))
 assert data['schema_version']=='1.0.0'
 rows=data['results'];candidates=data['candidates'];ctx=data['context']
 assert len({r['id'] for r in rows})==len(rows)==53
 assert len({r['system_id'] for r in candidates})==len(candidates)==481
 team=json.loads((ROOT/'data/processed/system_candidates.json').read_text())
 assert {r['system_id'] for r in team}<={r['system_id'] for r in candidates}
 registry={r['iso3'] for r in data['countries']}
 assert CORE<=registry
 for r in rows+candidates:
  assert isinstance(r['iso3'],list) and set(r['iso3'])<=registry
  for k in ['estimate','ci_lower','ci_upper','ci_level','followup_months','publication_year','year','p_value','statistic_value']:
   if k in r and r[k] is not None:assert isinstance(r[k],(int,float)) and not isinstance(r[k],bool) and math.isfinite(r[k])
 for r in rows:
  if r['display']['plot_eligible']:
   assert 0<r['ci_lower']<=r['estimate']<=r['ci_upper']
   assert not r['verification_status'].startswith('excluded')
  if r['evidence_kind']=='systematic_review_summary':assert r['display']['source_summary_only']
 assert sum(not r['display']['plot_eligible'] for r in rows)==1
 for r in candidates:
  assert r['effect_display_eligible'] is False
  assert isinstance(r['qc_flags'],list) and isinstance(r['teammate_flags'],list)
  assert 'plottable_ratio' not in r
  assert set(r['linked_result_ids'])<={x['id'] for x in rows}
 by_id={r['result_id']:r for r in rows}
 for key,country in [('R21-SEAS',{'BFA','MLI'}),('R21-STD',{'BFA','KEN','TZA'}),('ACCESS-SMC-CC',{'BFA','TCD','GMB','MLI','NGA'})]:
  r=by_id[key];assert set(r['iso3'])==country
  assert r['fulltext_check']['historical_matches_our_value'] is False
  assert r['fulltext_check']['numerical_match'] is True
  assert r['fulltext_check']['current_resolution']=='resolved_in_current_evidence'
  assert r['display']['plot_eligible']
 assert '42 days' in by_id['ACCESS-SMC-CC']['comparator']
 assert len(ctx['country_year'])==721 and len(ctx['pf8_sp'])==332 and len(ctx['pf8_aq_markers'])==166
 assert len({(r['iso3'],r['year'],r['source'],r['indicator']) for r in ctx['country_year']})==721
 for r in ctx['country_year']:
  assert r['iso3'] in CORE and isinstance(r['year'],int) and isinstance(r['flags'],list)
  if r['source']=='MAP':assert r['release']=='202608'
  if r['indicator']=='MALARIA_IRS_COVERAGE':assert r['unit']=='people'
 for r in ctx['pf8_sp']:
  n=r['n_determined'];assert n==r['n_resistant']+r['n_sensitive']
  if n:assert math.isclose(r['resistant_share'],r['n_resistant']/n)
  else:assert r['resistant_share'] is None
 assert {r['year'] for r in ctx['pf8_sp'] if r['iso3']=='BFA'}=={2008}
 for source in data['meta']['inputs']:
  assert hashlib.sha256((ROOT/source['path']).read_bytes()).hexdigest()==source['sha256']
 first=OUTPUT.read_bytes();build();assert OUTPUT.read_bytes()==first,'Build is not deterministic within the same input revision'
 print('PASS: counts, union coverage, distinct review levels, excluded-row guard, typed fields, corrected context/historical audit, joins, units, denominators, input hashes and deterministic build.')

if __name__=='__main__':main()
