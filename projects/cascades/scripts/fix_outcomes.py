"""Fix outcome precedence: cancer terms win over 'lung'/'respiratory' (e.g. 'lung cancer' was landing in Other respiratory)."""
import re, pandas as pd
ev=pd.read_csv('data/evidence.csv',low_memory=False)
canc=ev.other_variable.fillna('').str.lower().str.contains(r'cancer|neoplasm|carcinoma|tumou?r|malignan|mesothelioma')
before=(canc & ev.outcome_group.ne('Cancer')).sum()
ev.loc[canc,'outcome_group']='Cancer'
ev.to_csv('data/evidence.csv',index=False); print('reclassified to Cancer:',before)
