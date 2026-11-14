"""Build one typed, offline frontend data file from both contributors' results.

Never edits source evidence or context tables. Requires only Python stdlib.
"""
from pathlib import Path
from collections import Counter, defaultdict
import csv, hashlib, json, math, re, subprocess

ROOT=Path(__file__).resolve().parents[1]
PROJECT=ROOT/'what-works-where'
OUTPUT=PROJECT/'site/data/frontend-data.json'
NUMBERS={'estimate','ci_lower','ci_upper','ci_level','followup_months','publication_year','year','statistic_value','p_value'}
INTEGER={'publication_year','year','followup_months','n_determined','n_resistant','n_sensitive','n_undetermined','n_total','n_missing_or_invalid','n_variant_carrier','n_variant_only','n_mixed'}
CORE={'TZA','BEN','BFA','MLI','NGA'}

def csv_rows(path):
 with path.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def num(value):
 if value in ('',None):return None
 n=float(value)
 if not math.isfinite(n):raise ValueError('Nonfinite number')
 return int(n) if n.is_integer() else n
def codes(value):
 if not value:return []
 if isinstance(value,list):return sorted(set(value))
 values=sorted({x.strip() for x in value.split(';') if x.strip()})
 if any(not re.fullmatch('[A-Z]{3}',x) for x in values):raise ValueError(f'Invalid ISO3 list {value}')
 return values
def flags(value):
 if not value:return []
 if isinstance(value,list):return value
 return [x.strip() for x in value.split(';') if x.strip()]
def nullable(row):return {k:(None if v=='' else v) for k,v in row.items()}
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def check_resolution(result,check,audit):
 if check['matches_our_value']=='Y':return 'matched_at_fulltext_check'
 if not audit.get('numerical_match'):return 'unresolved'
 if result['result_id']=='R21-SEAS' and set(result['iso3'])=={'BFA','MLI'}:return 'resolved_in_current_evidence'
 if result['result_id']=='R21-STD' and set(result['iso3'])=={'BFA','KEN','TZA'}:return 'resolved_in_current_evidence'
 if result['result_id']=='ACCESS-SMC-CC' and '42 days' in result['comparator']:
  return 'resolved_in_current_evidence'
 return 'unresolved'

def build():
 inputs=[]
 def load_csv(relative):
  p=ROOT/relative;inputs.append(p);return csv_rows(p)
 def load_json(relative):
  p=ROOT/relative;inputs.append(p);return json.loads(p.read_text())
 ver=load_csv('what-works-where/data/verified/evidence_verified.csv')
 reviewed=load_csv('what-works-where/data/verified/evidence_graph_checked.csv')
 site_verified=load_json('what-works-where/site/data/verified.json')
 site_reviewed=load_json('what-works-where/site/data/graph_checked.json')
 enriched={r['result_id']:r for r in site_verified+site_reviewed}
 ft=load_csv('what-works-where/data/verified/fulltext_checks.csv')
 audits=load_json('reports/fulltext_check_audit.json')['checks']
 audit_by_id={r['result_id']:r for r in audits};ft_by_id={r['result_id']:r for r in ft}
 countries=load_csv('what-works-where/data/context/countries.csv')
 context=load_csv('what-works-where/data/context/context_country_year.csv')
 resistance=load_csv('what-works-where/data/context/pf8_sp_country_year.csv')
 markers=load_csv('what-works-where/data/context/pf8_aq_markers_country_year.csv')
 graph=load_json('what-works-where/site/data/graph.json')
 network=load_json('what-works-where/site/data/context.json')
 results=[];linked=defaultdict(list)
 for source_set,rows in [('paper_anchors',ver),('abstract_reviewed',reviewed)]:
  for raw in rows:
   r=nullable(raw)
   r['id']=source_set+':'+raw['result_id'];r['source_set']=source_set
   for k in NUMBERS:
    if k in r:r[k]=num(r[k])
   r['iso3_raw']=raw.get('iso3','');r['iso3']=codes(raw.get('iso3') or enriched.get(raw['result_id'],{}).get('iso3'))
   r['provenance']={'input_file':'what-works-where/data/verified/'+('evidence_verified.csv' if source_set=='paper_anchors' else 'evidence_graph_checked.csv'),
                    'result_id':raw['result_id'],'pmid':raw['pmid']}
   # The corrected evidence omits explicit countries for this five-country component.
   # Source: supplied PMC7718580 XML Results (the case-control component), not the 7-country programme.
   if raw['result_id']=='ACCESS-SMC-CC' and not r['iso3']:
    r['iso3']=['BFA','TCD','GMB','MLI','NGA']
    r['provenance']['country_codes_note']='Restored from PMC7718580 Results: case-control studies in five countries, not all seven programme countries.'
   excluded=str(r.get('verification_status','')).startswith('excluded')
   reasons=[]
   if excluded:reasons.append('excluded_by_evidence_review')
   values=[r.get(k) for k in ['estimate','ci_lower','ci_upper']]
   valid=all(isinstance(v,(int,float)) and v>0 for v in values)
   if not valid or not values[1]<=values[0]<=values[2]:reasons.append('invalid_or_missing_positive_ratio_interval')
   r['fulltext_check']=None
   if raw['result_id'] in ft_by_id:
    check=ft_by_id[raw['result_id']];audit=audit_by_id[raw['result_id']]
    resolution=check_resolution(r,check,audit)
    r['fulltext_check']={**check,'value_found':check['value_found']=='Y','ci_found':check['ci_found']=='Y',
      'historical_matches_our_value':check['matches_our_value']=='Y',
      'numerical_match':audit['numerical_match'],'current_resolution':resolution}
    # Preserve historical mismatch and note; never silently replace its result.
    del r['fulltext_check']['matches_our_value']
    if resolution=='unresolved':reasons.append('unresolved_fulltext_discrepancy')
   is_summary='cochrane' in str(r.get('trial_family_id','')).lower()
   r['evidence_kind']='systematic_review_summary' if is_summary else 'source_reported_result'
   r['display']={'plot_eligible':not reasons,'exclusion_reasons':reasons,
     'verification_level':'full_text' if r['fulltext_check'] and r['fulltext_check']['current_resolution']!='unresolved' else 'paper_reported' if source_set=='paper_anchors' else 'abstract',
     'panel_key':str(r.get('outcome_tier'))+' | '+str(r.get('effect_measure')),
     'source_summary_only':is_summary}
   if r.get('graph_association_id'):linked[r['graph_association_id']].append(r['id'])
   results.append(r)
 # Preserve potentially overlapping comparisons, but expose them for deduplication.
 groups=defaultdict(list)
 for r in results:
  signature=(r['pmid'],r['estimate'],r['ci_lower'],r['ci_upper'],r.get('followup_months'))
  groups[signature].append(r['id'])
 overlaps=[{'result_ids':ids,'reason':'same paper, estimate, interval and follow-up; compare definitions before combining'} for ids in groups.values() if len(ids)>1]
 candidates=[]
 for raw in graph:
  r=nullable(raw)
  for k in NUMBERS:
   if k in r:r[k]=num(r[k])
  r['iso3_raw']=raw.get('iso3','');r['iso3']=codes(raw.get('iso3'))
  for k in ['qc_flags','teammate_flags','study_flags']:r[k]=flags(raw.get(k))
  r['numeric_plot_eligible']=bool(r.pop('plottable_ratio',False))
  old=r.get('ci_excludes_null')
  r['ci_excludes_null']=True if old is True or old=='True' else False if old is False or old=='False' else None
  r['verification_status']='pending_source_review';r['effect_display_eligible']=False
  r['linked_result_ids']=linked.get(r['system_id'],[])
  candidates.append(r)
 for r in context:
  for k in ['value','lower','upper','year']:r[k]=num(r[k])
  r['release']=r['release'] or None;r['flags']=flags(r['flags'])
 for collection in [resistance,markers]:
  for r in collection:
   for k in r:
    if k in INTEGER or k in ['resistant_share','variant_carrier_share']:r[k]=num(r[k])
 for r in countries:
  for k in ['in_who','in_map','in_pf8']:r[k]=r[k]=='true'
 registry={r['iso3']:r for r in countries}
 observed=set(registry)
 observed.update(c for r in results+candidates for c in r['iso3'])
 for c in observed-registry.keys():
  registry[c]={'iso3':c,'name':c,'region':'other','seasonality':None,'showcase':'index_only',
    'notes':'No curated national metadata in the eleven-country showcase table; name falls back to ISO3.'}
 for c,r in registry.items():
  r['bundle_availability']={'country_year':any(x['iso3']==c for x in context),
    'pf8_sp':any(x['iso3']==c for x in resistance),'pf8_aq_markers':any(x['iso3']==c for x in markers),
    'reviewed_results':any(c in x['iso3'] for x in results)}
 summary={'snapshot_associations':network['summary']['snapshot_rows'],'candidate_associations':len(candidates),
  'candidate_papers':len({r['pubmed_id'] for r in candidates}),'paper_anchor_results':len(ver),
  'abstract_reviewed_records':len(reviewed),'reviewed_results_total':len(results),
  'displayable_reviewed_results':sum(r['display']['plot_eligible'] for r in results),
  'excluded_reviewed_records':sum(not r['display']['plot_eligible'] for r in results),
  'fulltext_checks':len(ft),'resolved_historical_context_discrepancies':sum(r['fulltext_check'] is not None and r['fulltext_check']['current_resolution']=='resolved_in_current_evidence' for r in results),
  'country_year_records':len(context),'who_records':sum(r['source']=='WHO' for r in context),
  'map_records':sum(r['source']=='MAP' for r in context),'pf8_sp_records':len(resistance),'pf8_aq_marker_records':len(markers),
  'core_countries':sorted(CORE),'country_registry_entries':len(registry),
  'counting_note':'Results are comparisons, not independent trials. Candidate and reviewed collections overlap; do not add their counts.'}
 bundle={'schema_version':'1.0.0','meta':{'title':'Malaria: What Works Where — frontend data',
  'data_as_of':'2026-11-14','source_integration_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
  'inputs':[{'path':str(p.relative_to(ROOT)),'sha256':sha(p)} for p in inputs],
  'licenses':[{'source':'System Public Graph','license':'CC BY-NC 4.0'},{'source':'MalariaGEN Pf8','license':'CC BY 4.0'},
    {'source':'WHO / MAP / articles','license':'Source-specific terms and attribution retained; no blanket relicensing.'}],
  'warnings':['Do not pool or rank studies with different outcomes, measures or comparators.',
    'Candidates are unverified associations; numerical plottability does not establish an intervention effect.',
    'WHO/MAP are national context, not trial-site measurements or causal explanations.',
    'Pf8 describes sampled cases, not national prevalence or SMC efficacy; no AQ classification is provided.',
    'Burkina Faso Pf8 data are from 2008 only; do not carry forward to later years.']},
  'summary':summary,'countries':sorted(registry.values(),key=lambda r:r['iso3']),
  'filters':{'intervention_classes':sorted({r['intervention_class'] for r in results}),
    'outcome_tiers':sorted({r['outcome_tier'] for r in results}),
    'effect_measures':sorted({r['effect_measure'] for r in results}),
    'country_codes':sorted(registry),'core_country_codes':sorted(CORE)},
  'results':results,'candidates':candidates,'possible_result_overlaps':overlaps,
  'context':{'country_year':context,'pf8_sp':resistance,'pf8_aq_markers':markers},
  'graph_context':{k:network[k] for k in ['malaria_neighbourhood','intervention_neighbourhoods','concepts','anchor_coverage']},
  'frontend_rules':{'effect_chart_collection':'results','effect_chart_filter':'display.plot_eligible === true',
    'candidate_collection':'candidates','candidate_use':'Search/index and source drill-down only',
    'country_membership':'iso3 is an array; use includes(countryCode). Multi-country results remain one result.',
    'context_join':'Match iso3 explicitly; select source/indicator/year. Do not automatically match publication_year to context year.',
    'default_panels':'Separate by outcome_tier and effect_measure; use display.panel_key.',
    'missing_values':'null means unavailable; preserve valid zeros.',
    'historical_checks':'Historical fulltext mismatch flags remain; current_resolution distinguishes corrected current records.'}}
 OUTPUT.parent.mkdir(parents=True,exist_ok=True)
 OUTPUT.write_text(json.dumps(bundle,ensure_ascii=False,separators=(',',':'),allow_nan=False)+'\n')
 print(json.dumps(summary,ensure_ascii=False,indent=2));print('Output bytes:',OUTPUT.stat().st_size)
 return bundle

if __name__=='__main__':build()
