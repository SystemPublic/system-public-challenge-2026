"""Reproduce curated independent checks against supplied open-access XMLs.

Selection locators are explicit; numerical occurrence alone is not treated as
confirmation of intervention/comparator/outcome/follow-up context.
"""
from pathlib import Path
import csv
import datetime
import hashlib
import json
import re
from decimal import Decimal
from xml.etree import ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'data/raw/literature'
OUT=ROOT/'what-works-where/data/verified/fulltext_checks.csv'
FIELDS='result_id,pmid,pmcid,location,quoted_text,value_found,ci_found,matches_our_value,discrepancy_note,checked_by,checked_at'.split(',')

def text(e):
 return re.sub(r'\s+',' ',''.join(e.itertext())).replace('·','.').replace('–','-').replace('−','-').strip()
def table_row(root,table_id,index):
 table=next(t for t in root.iter('table-wrap') if t.get('id')==table_id)
 row=list(table.iter('tr'))[index]
 return ' | '.join(text(cell) for cell in row)
def body_paragraph(root,needle):
 return next(text(p) for p in root.findall('.//body//p') if needle in text(p))
def excerpt(value,start,end=None):
 i=value.index(start);j=value.index(end,i)+len(end) if end else min(len(value),i+300)
 result=value[i:j]
 if len(result)>300:raise ValueError('Quote exceeds contract length')
 return result

def main():
 evidence=list(csv.DictReader((ROOT/'what-works-where/data/verified/evidence_verified.csv').open()))
 indexed={r['result_id']:r for r in evidence}
 roots={k:ET.parse(RAW/(k+'.xml')).getroot() for k in ['PMC8971961','PMC7618965','PMC7718580','PMC9871299','PMC6418392','PMC8457484']}
 # Explicit table rows, independently inspected in supplied XML.
 specs={
  'TZ24-CFP':('PMC8971961','Table 2, chlorfenapyr, 24 months, intention-to-treat',table_row(roots['PMC8971961'],'tbl2',13),(Decimal('.45'),Decimal('.30'),Decimal('.67')),''),
  'TZ24-PBO':('PMC8971961','Table 2, piperonyl butoxide, 24 months, intention-to-treat',table_row(roots['PMC8971961'],'tbl2',17),(Decimal('.99'),Decimal('.67'),Decimal('1.45')),''),
  'TZ24-PPF':('PMC8971961','Table 2, pyriproxyfen, 24 months, intention-to-treat',table_row(roots['PMC8971961'],'tbl2',9),(Decimal('.79'),Decimal('.54'),Decimal('1.17')),''),
  'R21-SEAS':('PMC7618965','Table 2, first clinical episode, seasonal sites, adjusted VE',table_row(roots['PMC7618965'],'T2',7),(Decimal('.75'),Decimal('.71'),Decimal('.79')),
    'Numeric HR=1-VE matches. Context mismatch: row lists all four trial countries, but seasonal sites are Nanoro (BFA) and Bougouni (MLI); use iso3 BFA;MLI. Table adjusted VE, 12 months after dose 3; outcome first clinical episode.'),
  'R21-STD':('PMC7618965','Table 2, first clinical episode, standard sites, adjusted VE',table_row(roots['PMC7618965'],'T2',10),(Decimal('.68'),Decimal('.61'),Decimal('.74')),
    'Numeric HR=1-VE matches. Context mismatch: row lists all four trial countries, but standard sites are Dande (BFA), Kilifi (KEN), Bagamoyo (TZA); use iso3 BFA;KEN;TZA. Table adjusted VE; first clinical episode, 12 months.'),
  'MALI-SMC5':('PMC9871299','Table 4, SMC group, fifth round (December)',table_row(roots['PMC9871299'],'t0020',4),(Decimal('.49'),Decimal('.26'),Decimal('.94')),''),
 }
 r=roots['PMC7718580']
 cc=body_paragraph(r,'The pooled estimate of the protective effectiveness')
 ccquote=excerpt(cc,'The pooled estimate','figure 2A).')
 specs['ACCESS-SMC-CC']=('PMC7718580','Results, Effectiveness of SMC paragraph; Figure 2A caption',ccquote,(Decimal('88.2'),Decimal('78.7'),Decimal('93.4')),
   'Numeric 1-PE conversion matches. Comparator mismatch: Figure 2A specifies no SMC within the last 42 days, not no SMC in previous 28 days. 28 days is the protection window. Case-control data cover five countries within the seven-country programme.')
 table=next(t for t in r.iter('table-wrap') if t.get('id')=='tbl2')
 for ident,country,source_values in [('ACCESS-SMC-NG','Nigeria',(Decimal('25.5'),Decimal('6.1'),Decimal('40.9'))),('ACCESS-SMC-GM','The Gambia',(Decimal('55.2'),Decimal('42.0'),Decimal('65.3')))]:
  line=next(' | '.join(text(c) for c in row) for row in table.iter('tr') if text(row).startswith(country) and str(source_values[0]) in text(row))
  specs[ident]=('PMC7718580','Table 2, malaria outpatients, '+country+', Overall',line,source_values,'')
 r=roots['PMC6418392']
 for ident,start,end,values in [
   ('COCH-ITN-MORT','Pooled analysis of five trials showed','Analysis 1.1).',(Decimal('.83'),Decimal('.77'),Decimal('.89'))),
   ('COCH-ITN-CLIN','Overall, the reduction in the rate','Analysis 1.2).',(Decimal('.55'),Decimal('.48'),Decimal('.64')))]:
  para=body_paragraph(r,start)
  specs[ident]=('PMC6418392','Effects of interventions, '+('child mortality' if 'MORT' in ident else 'P. falciparum uncomplicated episodes'),excerpt(para,start,end),values,'')
 checks=[];audit=[];now=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
 for ident in ['TZ24-CFP','TZ24-PBO','TZ24-PPF','R21-SEAS','R21-STD','ACCESS-SMC-CC','ACCESS-SMC-NG','ACCESS-SMC-GM','MALI-SMC5','COCH-ITN-MORT','COCH-ITN-CLIN']:
  row=indexed[ident];pmc,location,quote,source,note=specs[ident]
  expected=tuple(Decimal(row[k]) for k in ['estimate','ci_lower','ci_upper'])
  if ident.startswith('R21'):
   converted=(1-source[0],1-source[2],1-source[1]);normalization='HR = 1 - adjusted VE; reverse interval endpoints'
  elif ident.startswith('ACCESS'):
   converted=(1-source[0]/100,1-source[2]/100,1-source[1]/100);normalization='ratio = 1 - published percentage/100; reverse interval endpoints'
  else:converted=source;normalization='original ratio retained'
  numeric_match=all(abs(a-b)<=Decimal('.000001') for a,b in zip(expected,converted))
  # Tables can contain trailing zeros and percentages; match parsed decimals.
  observed={Decimal(x) for x in re.findall(r'(?<![\w.])(?:\d*\.\d+|\d+)(?![\w.])',quote)}
  value_found=source[0] in observed;ci_found=source[1] in observed and source[2] in observed
  if not note:note='Numbers, intervention, comparator, outcome and follow-up checked in supplied XML. '+normalization+'.'
  numeric_note='Numeric match; context correction required.' if ident in ['R21-SEAS','R21-STD','ACCESS-SMC-CC'] else ''
  check={'result_id':ident,'pmid':row['pmid'],'pmcid':pmc,'location':location,'quoted_text':quote,
    'value_found':'Y' if value_found else 'N','ci_found':'Y' if ci_found else 'N',
    'matches_our_value':'Y' if value_found and ci_found and numeric_match and not numeric_note else 'N',
    'discrepancy_note':note,'checked_by':'AI-2','checked_at':now}
  checks.append(check)
  audit.append({'result_id':ident,'source_scale_values':list(map(str,source)),'transformed_values':list(map(str,converted)),
    'stored_values':list(map(str,expected)),'numerical_match':numeric_match,'normalization':normalization,
    'context_correction_required':bool(numeric_note),'xml_sha256':hashlib.sha256((RAW/(pmc+'.xml')).read_bytes()).hexdigest()})
 OUT.parent.mkdir(parents=True,exist_ok=True)
 with OUT.open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(checks)
 identifier=roots['PMC8457484']
 identification={'title':text(identifier.find('.//article-title')),
  'pmid':next(e.text for e in identifier.findall('.//article-meta/article-id') if e.get('pub-id-type')=='pmid'),
  'doi':next(e.text for e in identifier.findall('.//article-meta/article-id') if e.get('pub-id-type')=='doi')}
 (ROOT/'reports/fulltext_check_audit.json').write_text(json.dumps({'checks':audit,'identified_PMC8457484':identification,
  'additional_27875528_34894221_rows_in_graph_checked':sum(r['pmid'] in ['27875528','34894221'] for r in csv.DictReader((ROOT/'what-works-where/data/verified/evidence_graph_checked.csv').open()))},indent=2)+'\n')
 assert all(r['value_found']=='Y' and r['ci_found']=='Y' for r in checks)
 assert all(r['numerical_match'] for r in audit)
 print('11 numeric matches; 3 context corrections requested; no evidence table silently changed.')
 print(identification)

if __name__=='__main__':main()
