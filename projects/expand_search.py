import sys,re,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import discover as d
old_a=d.ATTRIBUTES.copy();old_o=d.OUTCOMES.copy()
d.ATTRIBUTES['Wages / earnings']+=r'|\b(labou?r income|employee earnings|hourly earnings|monthly earnings|work income|low.wage)\b'
d.ATTRIBUTES['Job security']+=r'|\b(insecure employment|employment precarity|precariousness|non.standard employment|nonstandard employment|casual employment|casual work|contract insecurity|employment instability)\b'
d.ATTRIBUTES['Working hours / shifts']+=r'|\b(workhours|work hours|long work|weekly hours|daily hours|rotating shift|rotational shift|shiftwork|nightshift|night.work|irregular schedule)\b'
d.ATTRIBUTES['Formal / informal employment']+=r'|\b(informal job|informal worker|informal wage|informality|unregistered employment|undeclared work|unregistered worker|formal sector)\b'
d.OUTCOMES['Physical / self-rated health']+=r'|\b(self.assessed health|perceived health|poor health|somatic health|physical functioning|physical functioning|bodily pain|back pain|low.back pain|hypertension|ischemic heart|ischaemic heart|myocardial infarction|diabetes|cardiometabolic|cardiovascular mortality|all.cause mortality)\b'
d.OUTCOMES['Life satisfaction / well-being']+=r'|\b(satisfaction with life|subjective well.being|psychological well.being|quality of life|happiness|flourishing)\b'
d.OUTCOMES['Psychological distress']+=r'|\b(psychiatric distress|GHQ.12|Kessler|K6|K10)\b'
# Compile once; skip outcome checks for rows without employment-pattern matches.
compiled={}
def matches(text,patterns):
 key=id(patterns)
 if key not in compiled:compiled[key]=[(k,re.compile(v,re.I)) for k,v in patterns.items()]
 return [k for k,v in compiled[key] if v.search(text)]
d.matches=matches
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--raw',type=Path,default=Path('raw'));p.add_argument('--out',type=Path,default=Path('data/expanded'));a=p.parse_args();d.run(a.raw,a.out)
