"""Reproducible first-pass cleaning. Python standard library only; no paper linking.

Raw files are immutable. Lexical candidates remain unverified research evidence.
Run: python3 scripts/clean_data.py
"""
from pathlib import Path
from collections import Counter, defaultdict
import csv
import gzip
import hashlib
import itertools
import json
import math
import re

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data/raw'
OUT = ROOT / 'data/processed'
REPORT = ROOT / 'reports'
VERSION = '1.1.0'
MISSING = {'', 'na', 'n/a', 'nan', 'null', 'none'}
COUNTRIES = dict(zip(
    ['Bangladesh','Benin','Burkina Faso','Cambodia','Cameroon','Colombia',"Côte d'Ivoire",'Democratic Republic of the Congo','Ethiopia','Gabon','Gambia','Ghana','Guinea','Honduras','India','Indonesia','Kenya','Laos','Madagascar','Malawi','Mali','Mauritania','Mozambique','Myanmar','Nigeria','Papua New Guinea','Peru','Senegal','Sudan','Tanzania','Thailand','Uganda','Venezuela','Vietnam'],
    ['BGD','BEN','BFA','KHM','CMR','COL','CIV','COD','ETH','GAB','GMB','GHA','GIN','HND','IND','IDN','KEN','LAO','MDG','MWI','MLI','MRT','MOZ','MMR','NGA','PNG','PER','SEN','SDN','TZA','THA','UGA','VEN','VNM']))
PATTERNS = {
    'nets': r'insecticide[ -]treated (?:bed[ -]?)?nets?|long[ -]lasting insecticid\w* nets?|\b(?:bed[ -]?nets?|llins?|interceptor g2|royal guard|permanet|olyset)\b|(?:chlorfenapyr|pyriproxyfen|piperonyl butoxide)',
    'smc': r'seasonal malaria chemoprevention|\bsmc\b|sulfadoxine[ -]pyrimethamine.{0,35}amodiaquine|\bsp[ +/\-]+aq\b',
    'vaccines': r'\brts\s*[,/\-]?\s*s\b|\br21(?:/matrix[ -]?m)?\b|malaria vaccin\w*|vaccin\w*.{0,30}malaria',
}
RX = {k: re.compile(v, re.I) for k,v in PATTERNS.items()}
MALARIA = re.compile(r'malaria|plasmodium|anopheles|mosquito|\b(?:itns?|llins?)\b', re.I)
RATIOS = {'odds_ratio','adjusted_odds_ratio','hazard_ratio','adjusted_hazard_ratio',
          'relative_risk_ratio','incident_rate_ratio','prevalence_ratio','rate_ratio','risk_ratio'}
NUMERIC = ['statistic_value','ci_lower','ci_upper','ci_level','p_value']
QA = {}

def norm(value):
    if value is None: return None
    text = re.sub(r'\s+', ' ', str(value)).strip()
    return None if text.lower() in MISSING else text

def number(value):
    text = norm(value)
    if text is None: return None
    try:
        n = float(text)
        return n if math.isfinite(n) else None
    except (TypeError, ValueError): return None

def integer(value):
    n = number(value)
    return int(n) if n is not None and n.is_integer() else None

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def save(name, rows, fields=None):
    path = OUT / (name+'.csv')
    fields = fields or list(rows[0]) if rows else fields
    if not fields: raise ValueError(f'No schema: {name}')
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for row in rows:
            w.writerow({k:json.dumps(v,ensure_ascii=False,sort_keys=True) if isinstance(v,(list,dict)) else v for k,v in row.items()})
    (OUT/(name+'.json')).write_text(json.dumps(rows,ensure_ascii=False,indent=2,allow_nan=False)+'\n')

def read_tsv(name):
    with (RAW/'pf8'/name).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f,delimiter='\t'))

def system_path(name):
    return ROOT/'data/restored/system'/('system-public-graph-v1-'+name+'.csv')

def clean_system():
    counts=Counter(); missing=Counter(); types=Counter(); flags_count=Counter()
    seen={}; conflict_ids=set(); candidates=[]; sid=set(); vid=set()
    with system_path('associations').open(newline='') as f:
        for line,raw in enumerate(csv.DictReader(f),2):
            counts['input_rows']+=1
            for k in NUMERIC:
                if norm(raw.get(k)) is None:missing[k]+=1
            types[norm(raw.get('system_statistic_type')) or 'missing']+=1
            ident=raw['system_id']; signature=hashlib.sha256(json.dumps(raw,sort_keys=True).encode()).digest()
            duplicate=False
            if ident in seen:
                duplicate=seen[ident]==signature
                counts['exact_duplicate_rows' if duplicate else 'conflicting_id_rows']+=1
                if not duplicate:conflict_ids.add(ident)
            else: seen[ident]=signature
            text=' '.join([raw['variable_1_name'],raw['variable_2_name']])
            groups=[k for k,r in RX.items() if r.search(text)]
            if not groups or not MALARIA.search(text):continue
            counts['lexical_candidate_rows']+=1
            if duplicate:continue
            row={k:norm(v) for k,v in raw.items()}; flags=[]
            row['source_row']=line
            if seen[ident]!=signature:flags.append('conflicting_association_id')
            for k in NUMERIC:
                row[k+'_raw']=raw.get(k,''); row[k]=number(raw.get(k))
                if norm(raw.get(k)) is not None and row[k] is None:flags.append(k+'_not_numeric')
            if row['statistic_value'] is None:flags.append('missing_estimate')
            lo,hi,value=row['ci_lower'],row['ci_upper'],row['statistic_value']
            if (lo is None)!=(hi is None):flags.append('partial_ci')
            if lo is not None and hi is not None:
                if lo>hi:flags.append('reversed_ci')
                elif value is not None and not lo<=value<=hi:flags.append('estimate_outside_ci')
            if row['system_statistic_type'] in RATIOS:
                if any(x is not None and x<=0 for x in [lo,hi,value]):flags.append('nonpositive_ratio')
            level=row['ci_level']
            if level is not None and not 0<level<1:flags.append('ci_level_out_of_range')
            if row['p_value'] is not None and not 0<=row['p_value']<=1:flags.append('p_value_out_of_range')
            if row['p_value'] is not None and not row['p_value_equality']:flags.append('p_operator_unspecified')
            row.update(candidate_classes=groups,match_terms=sorted(set(m.group(0).lower() for k in groups for m in RX[k].finditer(text))),
                       origin='system_csv',verification_status='pending_source_review',
                       country_iso3=None,publication_year=None,followup_months=None,comparator=None,
                       intervention_verified=None,outcome_verified=None,trial_family_id=None)
            hints=[]
            for label,pattern in {
                'behaviour_or_acceptance':r'acceptance|willing|intention|knowledge|awareness|attitude|ownership|adheren|utili[sz]|net use|use of.{0,30}nets|sleeping under|slept under',
                'immunological':r'antibod|immunogen|antigen|anti.circumsporozoite|immune response',
                'entomological':r'mosquito|anopheles|entomolog|blood.feed|biting|vector mortality|knock.down',
                'human_infection_or_disease':r'infection|parasitem|parasitaem|malaria (?:incidence|case|episode|mortality)|clinical malaria|risk of malaria|anemia|anaemia|hospital|death|deaths|mortality',
            }.items():
                if re.search(pattern,text,re.I):hints.append(label)
            row['content_hints']=hints or ['unclassified']
            row['effect_display_eligible']=False
            row['flags']=flags;row['numeric_check_status']='review' if any(x!='p_operator_unspecified' for x in flags) else 'passed'
            candidates.append(row);sid.add(raw['study_id']);vid.update([raw['variable_1_id'],raw['variable_2_id']])
    studies={}; study_counts=Counter()
    with system_path('studies').open(newline='') as f:
        for raw in csv.DictReader(f):
            study_counts['all_study_rows']+=1
            if raw['study_id'] in sid:
                if raw['study_id'] in studies:raise ValueError('Nonunique study lookup')
                studies[raw['study_id']]={k:norm(v) for k,v in raw.items()}
    variables={}
    with system_path('variables').open(newline='') as f:
        for raw in csv.DictReader(f):
            if raw['system_id'] in vid:
                if raw['system_id'] in variables:raise ValueError('Nonunique variable lookup')
                variables[raw['system_id']]={k:norm(v) for k,v in raw.items()}
    for row in candidates:
        if row['system_id'] in conflict_ids and 'conflicting_association_id' not in row['flags']:
            row['flags'].append('conflicting_association_id')
        study=studies.get(row['study_id']);row['study_population_raw']=study.get('population_string') if study else None
        row['study_type_raw']=study.get('study_type') if study else None
        row['study_pmid_raw']=study.get('pubmed_id') if study else None
        if not study:row['flags'].append('study_lookup_missing')
        if study and study['pubmed_id'] and row['pubmed_id'] and study['pubmed_id']!=row['pubmed_id']:row['flags'].append('study_pmid_mismatch')
        pop=row['study_population_raw'] or ''
        row['country_hints']=[code for name,code in COUNTRIES.items() if re.search(r'\b'+re.escape(name)+r'\b',pop,re.I)]
        for i in [1,2]:
            variable=variables.get(row[f'variable_{i}_id'])
            if not variable:row['flags'].append(f'variable_{i}_lookup_missing')
            elif norm(variable['name'])!=norm(row[f'variable_{i}_name']):row['flags'].append(f'variable_{i}_name_mismatch')
        row['numeric_check_status']='review' if any(x!='p_operator_unspecified' for x in row['flags']) else 'passed'
        flags_count.update(row['flags'])
    candidates.sort(key=lambda x:(x['study_id'],x['system_id'],x['source_row']))
    save('system_candidates',candidates)
    class_summary=[]
    for group in RX:
        rows=[x for x in candidates if group in x['candidate_classes']]
        class_summary.append({'candidate_class':group,'association_count':len(rows),'study_record_count':len({x['study_id'] for x in rows}),
                              'with_complete_ci':sum(x['ci_lower'] is not None and x['ci_upper'] is not None for x in rows),
                              'numeric_checks_passed':sum(x['numeric_check_status']=='passed' for x in rows),
                              'source_verified_count':0})
    save('system_candidate_summary',class_summary)
    save('system_study_lookup',sorted(studies.values(),key=lambda x:x['study_id']),['study_id','doi','pubmed_id','population_string','study_type'])
    review=[{'system_id':r['system_id'],'study_id':r['study_id'],'candidate_classes':r['candidate_classes'],
             'flags':r['flags'],'verification_status':r['verification_status'],'missing_context':['intervention','comparator','outcome','country','followup','trial_family']} for r in candidates]
    save('system_review_queue',review)
    QA['system']={**counts,**study_counts,'output_candidates':len(candidates),'unique_study_records':len(sid),'study_lookup_matched':len(studies),
                  'source_verified_count':0,'global_missing':dict(missing),'global_statistic_types':dict(types),'candidate_flags':dict(flags_count),'class_summary':class_summary,
                  'search_patterns':PATTERNS,'context_pattern':MALARIA.pattern,'scope':'lexical candidate search, not exhaustive; study records are not independent trials'}
    QA['system']['content_hints']=dict(Counter(h for r in candidates for h in r['content_hints']))

def clean_who():
    units={'MALARIA_ITN_USE':'percent_population','MALARIA_ITN_COVERAGE':'percent_population',
           'MALARIA_IRS_COVERAGE':'people','MALARIA_EST_INCIDENCE':'cases_per_1000_population_at_risk'}
    rows=[];seen=set();duplicates=0
    for path in sorted((RAW/'who').glob('*.json')):
        doc=json.loads(path.read_text())
        if doc.get('@odata.nextLink'):raise ValueError('WHO pagination incomplete')
        for raw in doc['value']:
            signature=json.dumps(raw,sort_keys=True)
            if signature in seen:duplicates+=1;continue
            seen.add(signature)
            code=raw['IndicatorCode'];value=number(raw.get('NumericValue'));lo=number(raw.get('Low'));hi=number(raw.get('High'));flags=[]
            if value is None:flags.append('missing_value')
            if value is not None and value<0:flags.append('negative_value')
            if units[code]=='percent_population' and value is not None and value>100:flags.append('percentage_above_100')
            if lo is not None and hi is not None and (lo>hi or value is not None and not lo<=value<=hi):flags.append('invalid_interval')
            rows.append({'source':'WHO','source_file':str(path.relative_to(ROOT)),'source_id':raw['Id'],
                         'country_iso3':raw['SpatialDim'],'year':integer(raw['TimeDim']),'indicator':code,
                         'value':value,'lower':lo,'upper':hi,'unit':units[code],'estimate_type':'modelled' if code!='MALARIA_IRS_COVERAGE' else 'reported_programme',
                         'dim1':raw.get('Dim1'),'dim2':raw.get('Dim2'),'dim3':raw.get('Dim3'),
                         'value_raw':raw.get('Value'),'source_updated':raw.get('Date'),'flags':flags})
    keys=Counter((r['country_iso3'],r['year'],r['indicator'],r['dim1'],r['dim2'],r['dim3']) for r in rows)
    for r in rows:
        if keys[(r['country_iso3'],r['year'],r['indicator'],r['dim1'],r['dim2'],r['dim3'])]>1:r['flags'].append('duplicate_dimension_key')
    rows.sort(key=lambda r:(r['country_iso3'],r['indicator'],r['year'],r['source_id']))
    save('who_context',rows)
    QA['who']={'output_rows':len(rows),'exact_duplicates_removed':duplicates,'by_indicator':dict(Counter(r['indicator'] for r in rows)),
               'flags':dict(Counter(f for r in rows for f in r['flags'])),'countries':sorted({r['country_iso3'] for r in rows})}

def jsonstat(doc):
    dimensions=doc['id'];sizes=doc['size'];categories=[]
    for dim in dimensions:
        index=doc['dimension'][dim]['category']['index']
        categories.append(index if isinstance(index,list) else [k for k,v in sorted(index.items(),key=lambda x:x[1])])
    if [len(x) for x in categories]!=sizes:raise ValueError('JSON-stat category sizes mismatch')
    for i,coords in enumerate(itertools.product(*categories)):
        v=doc['value']; value=v[i] if isinstance(v,list) else v.get(str(i))
        yield dict(zip(dimensions,coords)),number(value)

def clean_map():
    groups={};source_files=defaultdict(list)
    for path in sorted((RAW/'map').glob('*.json')):
        match=re.fullmatch(r'([A-Z]{3})_(.+)_(mean|lci|uci)_(\d+)',path.stem)
        if not match:raise ValueError('Unexpected MAP filename')
        country,metric,stat,version=match.groups()
        for coords,value in jsonstat(json.loads(path.read_text())):
            if coords['ISO']!=country:raise ValueError('MAP geography mismatch')
            key=(country,integer(coords['Year']),metric,version)
            if stat in groups.setdefault(key,{}):raise ValueError('Duplicate MAP stat')
            groups[key][stat]=value;source_files[key].append(str(path.relative_to(ROOT)))
    rows=[]
    for (country,year,metric,version),v in sorted(groups.items()):
        flags=[];raw_mean=v.get('mean');lo=v.get('lci');hi=v.get('uci')
        if set(v)!={'mean','lci','uci'}:flags.append('incomplete_interval_files')
        if raw_mean is None:flags.append('missing_value')
        if any(x==0 for x in v.values()):flags.append('zero_may_mean_missing')
        if raw_mean is not None and (raw_mean<0 or metric!='Pf_incidence-rate' and raw_mean>1):flags.append('value_out_of_range')
        if lo is not None and hi is not None and (lo>hi or raw_mean is not None and not lo<=raw_mean<=hi):flags.append('invalid_interval')
        rows.append({'source':'MAP','country_iso3':country,'year':year,'metric':metric,'release':version,
                     'value':None if 'zero_may_mean_missing' in flags else raw_mean,'lower':None if lo==0 else lo,'upper':None if hi==0 else hi,
                     'value_raw':raw_mean,'lower_raw':lo,'upper_raw':hi,
                     'unit':'cases_per_1000_population_per_year' if metric=='Pf_incidence-rate' else 'proportion',
                     'population':'children_age_2_10' if metric=='Pf_PR-rate' else 'all_ages',
                     'estimate_type':'modelled','source_files':source_files[(country,year,metric,version)],'flags':flags})
    save('map_context',rows)
    QA['map']={'output_rows':len(rows),'release':'202608','countries':sorted({r['country_iso3'] for r in rows}),'flags':dict(Counter(f for r in rows for f in r['flags'])),'years':[min(r['year'] for r in rows),max(r['year'] for r in rows)]}

def unique_index(rows,key):
    result={}
    for row in rows:
        ident=row[key]
        if ident in result:raise ValueError(f'Duplicate join key: {key} {ident}')
        result[ident]=row
    return result

def clean_pf8():
    meta=read_tsv('Pf8_samples.txt');gen=unique_index(read_tsv('Pf8_drug_resistance_marker_genotypes.tsv'),'Sample')
    drug_rows=read_tsv('Pf8_inferred_resistance_status_classification.tsv');drugs=unique_index(drug_rows,'sample')
    unique_index(meta,'Sample')
    # Canonicalize same-case membership including transitive overlap. Keep all samples.
    parent={r['Sample']:r['Sample'] for r in meta}
    def find(x):
        parent.setdefault(x,x)
        if parent[x]!=x:parent[x]=find(parent[x])
        return parent[x]
    def union(a,b):
        a,b=find(a),find(b)
        if a!=b:parent[max(a,b)]=min(a,b)
    for r in meta:
        for member in (r['All samples same case'] or r['Sample']).split(','):union(r['Sample'],member.strip())
    prepared=[];groups=defaultdict(list)
    for raw in meta:
        flags=[];year=integer(raw['Year']);qc={'true':True,'false':False}.get(raw['QC pass'].lower())
        country=COUNTRIES.get(raw['Country']);callable_=number(raw['% callable'])
        if country is None:flags.append('missing_or_unmapped_country')
        if year is None:flags.append('missing_or_invalid_year')
        if qc is None:flags.append('invalid_qc_boolean')
        if callable_ is not None and not 0<=callable_<=100:flags.append('callable_percentage_out_of_range')
        if qc and raw['Sample'] not in gen:flags.append('qc_pass_missing_genotypes')
        if qc and raw['Sample'] not in drugs:flags.append('qc_pass_missing_drug_classification')
        r={'sample_id':raw['Sample'],'study_id':norm(raw['Study']),'country_raw':norm(raw['Country']),'country_iso3':country,
           'admin1':norm(raw['Admin level 1']),'year':year,'qc_pass':qc,'callable_percent':callable_,
           'case_group_id':find(raw['Sample']),'same_case_raw':raw['All samples same case'],
           'exclusion_reason_raw':raw['Exclusion reason'],'sample_type':norm(raw['Sample type']),
           'country_latitude':number(raw['Country latitude']),'country_longitude':number(raw['Country longitude']),
           'admin1_latitude':number(raw['Admin level 1 latitude']),'admin1_longitude':number(raw['Admin level 1 longitude']),
           'has_genotypes':raw['Sample'] in gen,'has_drug_classification':raw['Sample'] in drugs,'selected_case_representative':False,'aggregation_eligible':False,'flags':flags}
        prepared.append(r)
        if qc:groups[r['case_group_id']].append(r)
    for group in groups.values():
        contexts={(r['country_iso3'],r['admin1'],r['year']) for r in group}
        chosen=sorted(group,key=lambda r:(-(r['callable_percent'] if r['callable_percent'] is not None else -1),r['sample_id']))[0]
        chosen['selected_case_representative']=True
        if len(contexts)>1:
            for r in group:r['flags'].append('same_case_conflicting_context')
        for r in group:
            if len(group)>1 and r is not chosen:r['flags'].append('same_case_secondary_sample')
        chosen['aggregation_eligible']=len(contexts)==1 and chosen['country_iso3'] is not None and chosen['year'] is not None
    prepared.sort(key=lambda r:r['sample_id']);save('pf8_samples',prepared)
    drug_names=[x for x in drug_rows[0] if x!='sample'];long=[];counts=defaultdict(Counter)
    for r in prepared:
        source=drugs.get(r['sample_id'])
        if source is None:continue
        for drug in drug_names:
            status=norm(source[drug]);flags=[]
            if status not in {'Resistant','Sensitive','Undetermined'}:flags.append('unexpected_status')
            long.append({'sample_id':r['sample_id'],'drug_or_combination':drug,'status':status,'flags':flags})
            if r['aggregation_eligible']:
                key=(r['country_iso3'],r['admin1'],r['year'],drug)
                counts[key][status or 'Missing']+=1
    save('pf8_drug_classifications',long)
    summaries=[]
    for (country,admin,year,drug),c in sorted(counts.items(),key=lambda x:str(x[0])):
        known=c['Resistant']+c['Sensitive'];total=sum(c.values())
        summaries.append({'country_iso3':country,'admin1':admin,'year':year,'drug_or_combination':drug,'n_total':total,
                          'n_resistant':c['Resistant'],'n_sensitive':c['Sensitive'],'n_undetermined':c['Undetermined'],
                          'n_missing_or_invalid':total-known-c['Undetermined'],'n_determined':known,
                          'resistant_proportion_among_determined':c['Resistant']/known if known else None,
                          'scope':'sampled_cases_not_national_prevalence','classification_source':'publisher_Pf8_not_SMC_efficacy'})
    save('pf8_resistance_context',summaries)
    national_counts=defaultdict(Counter)
    for r in summaries:
        c=national_counts[(r['country_iso3'],r['year'],r['drug_or_combination'])]
        for k in ['n_total','n_resistant','n_sensitive','n_undetermined','n_missing_or_invalid','n_determined']:c[k]+=r[k]
    national=[]
    for (country,year,drug),c in sorted(national_counts.items()):
        national.append({'country_iso3':country,'year':year,'drug_or_combination':drug,**c,
                         'resistant_proportion_among_determined':c['n_resistant']/c['n_determined'] if c['n_determined'] else None,
                         'scope':'sampled_cases_not_national_prevalence','classification_source':'publisher_Pf8_not_SMC_efficacy'})
    save('pf8_country_year_resistance',national)
    # Normalize all available raw marker strings, without inventing resistance rules.
    markers=[]
    for sample,source in sorted(gen.items()):
        for marker,call in source.items():
            if marker=='Sample':continue
            markers.append({'sample_id':sample,'marker':marker,'call_raw':call,'call':norm(call),
                            'is_missing':norm(call) is None or call.strip()=='-',
                            'is_mixed':',' in call,'interpretation':'not_inferred'})
    # Wide raw calls are already compact; long normalized output is gzip to avoid large Git files.
    marker_path=OUT/'pf8_marker_calls.csv.gz'
    with gzip.open(marker_path,'wt',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(markers[0]));w.writeheader();w.writerows(markers)
    QA['pf8']={'input_samples':len(meta),'qc_pass_samples':sum(r['qc_pass'] is True for r in prepared),
               'genotype_rows':len(gen),'classification_rows':len(drugs),'qc_pass_case_groups':len(groups),
               'aggregation_eligible_cases':sum(r['aggregation_eligible'] for r in prepared),'resistance_context_rows':len(summaries),
               'country_year_resistance_rows':len(national),
               'marker_call_rows':len(markers),'metadata_without_genotypes':sum(not r['has_genotypes'] for r in prepared),
               'orphan_genotype_samples':len(set(gen)-set(parent)),'orphan_classification_samples':len(set(drugs)-set(parent)),
               'flags':dict(Counter(f for r in prepared for f in r['flags'])),'countries':len({r['country_iso3'] for r in prepared if r['country_iso3']})}

def main():
    OUT.mkdir(parents=True,exist_ok=True);REPORT.mkdir(exist_ok=True)
    # Validate raw packaged inputs before cleaning. All changes stay in processed/.
    manifest=json.loads((ROOT/'metadata/download_manifest.json').read_text())
    for item in manifest['files']:
        path=ROOT/item['path']
        if digest(path)!=item['sha256']:raise ValueError(f'Raw file changed: {path}')
    if not all(system_path(x).exists() for x in ['associations','studies','variables','concepts']):
        from restore_system import main as restore
        restore()
    publisher=json.loads((RAW/'system/MANIFEST.json').read_text())
    for item in publisher['files']:
        path=ROOT/'data/restored/system'/item['filename']
        if path.exists() and digest(path)!=item['checksums']['sha256']:raise ValueError('Restored CSV changed')
    for name,job in [('System',clean_system),('WHO',clean_who),('MAP',clean_map),('Pf8',clean_pf8)]:
        print(f'Cleaning {name}...',flush=True);job();print(f'Finished {name}',flush=True)
    QA['pipeline_version']=VERSION;QA['paper_linking_performed']=False
    (REPORT/'quality_report.json').write_text(json.dumps(QA,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    files=[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':digest(p)} for p in sorted(OUT.glob('*')) if p.is_file()]
    (REPORT/'processed_manifest.json').write_text(json.dumps({'pipeline_version':VERSION,'files':files},indent=2)+'\n')
    s=QA['system'];p=QA['pf8']
    lines=['# 第一轮数据清洗结果','',
           '论文链接及原文核验尚未执行。System 的结果都是候选关联，不能直接解释成干预效力。',
           '',f"- System 全量扫描：{s['input_rows']:,} 行；候选 {s['output_candidates']:,} 行，来自 {s['unique_study_records']} 个 study 记录。",
           f"- WHO：{QA['who']['output_rows']} 条国家—年份—指标记录。",
           f"- MAP：{QA['map']['output_rows']} 条国家—年份—指标记录，版本 202608。",
           f"- Pf8：{p['input_samples']:,} 个样本；QC通过 {p['qc_pass_samples']:,}；可汇总病例 {p['aggregation_eligible_cases']:,}。",'',
           '## 候选证据覆盖','', '|类别|关联数|study记录数|完整区间|数值检查通过|原文核验通过|','|---|---:|---:|---:|---:|---:|']
    for r in s['class_summary']:lines.append('|'+ '|'.join(str(r[k]) for k in ['candidate_class','association_count','study_record_count','with_complete_ci','numeric_checks_passed','source_verified_count'])+'|')
    lines+=['','类别允许重叠。study记录数不等于独立试验数。数值检查通过不等于临床解释已核验。',
            '', '## 处理规则','',
            '- 原始文件及其校验值保持不变。空值写为CSV空单元格或JSON null；不以0填补。',
            '- System：仅去除内容完全相同的重复ID记录；冲突保留并标记。保留原始统计类型，不统一转换HR/OR/RR，不计算效果排名。',
            '- 国家提示仅取自原始population文本，不能作为已确认研究国家。对照组、随访和试验家族留空待核验。',
            '- WHO：保留单位和各维度；IRS人数不当成覆盖率。完整重复记录去重，维度冲突保留标记。',
            '- MAP：按JSON-stat维度顺序展开，并按国家/年/指标/版本连接mean/lci/uci。零值可能缺失，保留raw值，清洗值暂留空并标记。',
            '- Pf8：保留全部样本。仅QC通过病例进入汇总；同病例优先最高callable比例，平局按样本ID排序。地点/年份冲突的病例不进入汇总。',
            '- 耐药比例分母为Resistant + Sensitive，Undetermined和缺失另列。数据描述采样病例，不代表全国耐药率，不代表SMC失效。',
            '- 基因标记保留混合调用和缺失；未重新推断生物学耐药含义。',
            '', '## 下一步','',
            '查看 system_review_queue.csv，按原文确认干预、对照、结局、国家、时间与试验家族，再生成可解释的效果图。WHO/MAP/Pf8背景保持分表。',
            '', '运行命令：`python3 scripts/clean_data.py`。详细问题计数见 quality_report.json。']
    (REPORT/'cleaning_report_zh.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({k:v for k,v in QA.items() if k!='system'},ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':main()
