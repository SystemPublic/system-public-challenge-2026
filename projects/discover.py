"""Reproduce the first, deliberately broad candidate search. Python standard library only.
Usage: python discover.py --raw /path/to/raw --out /path/to/results
Download sources listed in SOURCE_FILES when raw files are absent.
"""
import argparse,csv,hashlib,json,re,urllib.request
from pathlib import Path
from datetime import datetime,timezone
SOURCE_FILES={'associations.csv':(14061020,'c884dd1132957f69ffea45404f29db61'), 'concepts.tsv':(14061021,'c902b288797545dcc801edd3a55a4f0d'), 'studies.tsv':(14061022,'558e7529ee5545c7504bf412288694cc')}
ATTRIBUTES={
 'Wages / earnings':r'\b(wages?|salary|salaries|pay insecurity|low pay|hourly pay)\b',
 'Job security':r'\b(job insecurity|job security|employment insecurity|employment security|precarious employment|precarious work|temporary employment|temporary contract|fixed.term contract)\b',
 'Working hours / shifts':r'\b(working hours|work hours|long hours|overtime|shift work|night shift|night work|work schedule|working time)\b',
 'Working conditions':r'\b(working conditions|work conditions|job strain|job demands|job control|effort.reward imbalance|occupational stress|workplace bullying)\b',
 'Occupational safety':r'\b(occupational exposure|occupational noise|occupational dust|workplace safety|safety training|fall protection|occupational health and safety)\b',
 'Insurance / benefits':r'\b(health insurance|insurance benefits|paid leave|sick leave|employment benefits)\b',
 'Pensions / protection':r'\b(pension|social protection|social insurance)\b',
 'Job satisfaction':r'\bjob satisfaction\b',
 'Formal / informal employment':r'\b(informal employment|informal work|formal employment|employment formality|informal sector)\b'}
OUTCOMES={
 'Mental health':r'\b(mental health|psychological health|mental disorder)\b',
 'Depression / anxiety':r'\b(depression|depressive|anxiety)\b',
 'Psychological distress':r'\b(psychological distress|mental distress|emotional distress)\b',
 'Physical / self-rated health':r'\b(physical health|self.rated health|self.reported health|general health|coronary heart disease|cardiovascular disease|stroke|musculoskeletal|lung function)\b',
 'Life satisfaction / well-being':r'\b(life satisfaction|well.being|wellbeing)\b',
 'Occupational injury':r'\b(occupational injury|occupational injuries|work.related injur|work injury|work injuries)'}
def write_rows(path,rows,fields=None):
 rows=list(rows)
 with path.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields or list(rows[0]));w.writeheader();w.writerows(rows)
def matches(text,patterns):return [k for k,v in patterns.items() if re.search(v,text,re.I)]
def run(raw,out):
 raw.mkdir(parents=True,exist_ok=True);out.mkdir(parents=True,exist_ok=True)
 checks={}
 for name,(fid,expected) in SOURCE_FILES.items():
  p=raw/name
  if not p.exists():urllib.request.urlretrieve(f'https://dataverse.harvard.edu/api/access/datafile/{fid}',p)
  h=hashlib.md5()
  with p.open('rb') as f:
   for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
  if name.endswith('.csv') and h.hexdigest()!=expected:raise ValueError('Checksum mismatch: '+name)
  checks[name]={'file_id':fid,'md5':h.hexdigest(),'bytes':p.stat().st_size,'metadata_md5':expected,'checksum_status':'matched' if h.hexdigest()==expected else 'tabular export differs from original-file checksum'}
 with (raw/'concepts.tsv').open() as f:concepts={r['system_id']:r for r in csv.DictReader(f,delimiter='\t')}
 candidates=[];pair_rows=[];scanned=0
 with (raw/'associations.csv').open() as f:
  for r in csv.DictReader(f):
   scanned+=1
   texts=[r[f'variable_{i}_name']+' '+concepts.get(r[f'variable_{i}_concept_id'],{}).get('wikidata_label','') for i in (1,2)]
   pairs=[]
   for a,b in [(0,1),(1,0)]:
    for attr in matches(texts[a],ATTRIBUTES):
     for outcome in matches(texts[b],OUTCOMES):pairs.append((attr,outcome,a+1))
   if not pairs:continue
   r['review_status']='candidate: not paper validated'
   candidates.append(r)
   for attr,outcome,side in sorted(set(pairs)):
    pair_rows.append({'association_id':r['system_id'],'study_id':r['study_id'],'attribute':attr,'outcome':outcome,'exposure_variable_side':side})
 ids={r['study_id'] for r in candidates if r['study_id']}
 with (raw/'studies.tsv').open() as f:studies=[r for r in csv.DictReader(f,delimiter='\t') if r['study_id'] in ids]
 write_rows(out/'candidate_associations.csv',candidates)
 write_rows(out/'candidate_pairs.csv',pair_rows)
 write_rows(out/'candidate_studies.csv',studies)
 counts=[]
 for a in ATTRIBUTES:
  for o in OUTCOMES:
   rs=[r for r in pair_rows if r['attribute']==a and r['outcome']==o]
   counts.append({'attribute':a,'outcome':o,'candidate_associations':len({r['association_id'] for r in rs}),'distinct_study_ids':len({r['study_id'] for r in rs if r['study_id']})})
 write_rows(out/'discovery_counts.csv',counts)
 selected={r[f'variable_{i}_concept_id'] for r in candidates for i in (1,2)}
 write_rows(out/'candidate_concepts.csv',[c for k,c in concepts.items() if k in selected])
 manifest={'retrieved_utc':datetime.now(timezone.utc).isoformat(),'dataset_doi':'10.7910/DVN/7V6JDO','dataset_version':'2.1','source_files':checks,'association_rows_scanned':scanned,'candidate_associations':len(candidates),'candidate_study_ids':len(ids),'matched_study_metadata':len(studies),'attribute_patterns':ATTRIBUTES,'outcome_patterns':OUTCOMES,'limitations':['Purposive vocabulary; not exhaustive literature coverage','Pattern matches require exposure/outcome/population screening','Publication IDs are not independent cohorts','No paper-validated effect estimates or causal conclusions in discovery counts']}
 (out/'manifest.json').write_text(json.dumps(manifest,indent=2))
 print(json.dumps({k:v for k,v in manifest.items() if k not in ['source_files','attribute_patterns','outcome_patterns','limitations']},indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--raw',type=Path,default=Path('raw'));p.add_argument('--out',type=Path,default=Path('data'));a=p.parse_args();run(a.raw,a.out)
