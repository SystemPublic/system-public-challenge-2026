"""Apply relevance labels to data/name_labels.csv.
Usage: python scripts/apply_labels.py <first_nid> <last_nid> "<drop ids>" "<context ids>"
Every nid in the range not listed as drop/context is labelled keep. Ids: space-separated, ranges a-b allowed."""
import sys, pandas as pd
def ids(s):
    out=set()
    for t in s.split():
        if '-' in t: a,b=map(int,t.split('-')); out|=set(range(a,b+1))
        elif t: out.add(int(t))
    return out
lo,hi=int(sys.argv[1]),int(sys.argv[2]); drop=ids(sys.argv[3]); ctx=ids(sys.argv[4])
g=pd.read_csv('data/name_labels.csv', keep_default_na=False)
m=(g.nid>=lo)&(g.nid<=hi)
g.loc[m,'label']='keep'
g.loc[m&g.nid.isin(drop),'label']='drop'
g.loc[m&g.nid.isin(ctx),'label']='context'
g.to_csv('data/name_labels.csv',index=False)
print(g.loc[m].label.value_counts().to_dict(), '| total labelled', (g.label!='').sum(), '/', len(g))
