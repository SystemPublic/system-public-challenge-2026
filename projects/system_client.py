"""System v1 API client; request/response schema checked against provider docs 2026-11-14.
Authenticated live behavior still requires testing with the user's key.
"""
import hashlib,json,os
from pathlib import Path
from datetime import datetime,timezone
from urllib.request import Request,urlopen
from urllib.parse import urlencode
from urllib.error import HTTPError

def get_key():
 key=os.environ.get('SYSTEM_API_KEY') or os.environ.get('SYSTEM_GRAPH_API_KEY')
 if not key:
  try:
   from google.colab import userdata
   key=userdata.get('SYSTEM_API_KEY')
  except (ImportError,KeyError):pass
 return key

class SystemClient:
 def __init__(self,key,cache='api_cache'):
  if not key:raise ValueError('Configure SYSTEM_API_KEY in Colab Secrets or the environment.')
  self._key=key;self.cache=Path(cache);self.cache.mkdir(parents=True,exist_ok=True)
 def get(self,path,params=None,refresh=False):
  if not path.startswith('/v1/') or '?' in path:raise ValueError('Use a v1 path and separate parameters.')
  url='https://public-api.system.com'+path+'?'+urlencode(params or {})
  p=self.cache/(hashlib.sha256(url.encode()).hexdigest()+'.json')
  if p.exists() and not refresh:return json.loads(p.read_text())['data']
  try:
   with urlopen(Request(url,headers={'x-api-key':self._key,'Accept':'application/json'}),timeout=45) as r:data=json.load(r)
  except HTTPError as e:raise RuntimeError(f'System HTTP {e.code}; request stopped, not counted as empty evidence.') from None
  p.write_text(json.dumps({'url':url,'retrieved_utc':datetime.now(timezone.utc).isoformat(),'data':data}))
  return data
 def paginate(self,path,params=None,cap=500,batch_size=100):
  rows=[];total=None;seen=set();reason='cap_reached'
  while len(rows)<cap:
   q=dict(params or {});q.update(limit=min(batch_size,cap-len(rows)),offset=len(rows),include_total='true')
   obj=self.get(path,q)
   if not isinstance(obj,dict) or not isinstance(obj.get('data'),list):raise ValueError('Unexpected list response schema')
   page=obj['data'];total=obj.get('total',total)
   signature=json.dumps(page,sort_keys=True)
   if page and signature in seen:raise ValueError('Repeated page; pagination cannot be trusted')
   seen.add(signature);rows.extend(page)
   if total is not None and len(rows)>=total:reason='reported_total_reached';break
   if len(page)<q['limit']:reason='short_page';break
  complete=(len(rows)>=total) if total is not None else reason=='short_page'
  return rows,{'path':path,'params':params or {},'retrieved':len(rows),'total':total,'complete':complete,'stop_reason':reason}
