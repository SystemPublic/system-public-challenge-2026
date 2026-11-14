"""Shared helpers for the openFDA scripts (faers_heat_signals.py, fda_label_heat_audit.py).

- Cached GET against api.fda.gov: every response is stored gzip-compressed in
  data/raw/openfda/cache/<sha1 of URL>.json.gz, so reruns cost zero API calls.
- Polite rate limiting (no API key: 240 req/min, 1,000 req/day; with a key: 240 req/min,
  120,000 req/day). Call use_api_key_from_env() to send OPENFDA_API_KEY (read from the
  environment or .env.local). The key is added only to the outgoing request: cache keys,
  cache files, the call log and error messages always use the key-free URL, so keyed and
  keyless runs share the same cache.
- Ingredient list (generic names) for the 15 heat-risk drug classes plus
  positive and negative controls.

Responses from openFDA are untrusted data; they are parsed as JSON only.
"""
import gzip, hashlib, json, os, time, urllib.error, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw", "openfda")
CACHE = os.path.join(RAW, "cache")
PROCESSED = os.path.join(ROOT, "data", "processed")
CALL_LOG = os.path.join(RAW, "call_log.tsv")

# (class, ingredient search term, role). role: study | positive_control | negative_control
INGREDIENTS = [
    ("lithium", "lithium", "study"),
    ("loop diuretics", "furosemide", "study"),
    ("loop diuretics", "bumetanide", "study"),
    ("loop diuretics", "torsemide", "study"),
    ("thiazides", "hydrochlorothiazide", "study"),
    ("thiazides", "chlorthalidone", "study"),
    ("thiazides", "indapamide", "study"),
    ("ACE inhibitors/ARBs", "lisinopril", "study"),
    ("ACE inhibitors/ARBs", "enalapril", "study"),
    ("ACE inhibitors/ARBs", "ramipril", "study"),
    ("ACE inhibitors/ARBs", "losartan", "study"),
    ("ACE inhibitors/ARBs", "valsartan", "study"),
    ("ACE inhibitors/ARBs", "olmesartan", "study"),
    ("SGLT2 inhibitors", "empagliflozin", "study"),
    ("SGLT2 inhibitors", "dapagliflozin", "study"),
    ("SGLT2 inhibitors", "canagliflozin", "study"),
    ("insulin (incl. pumps)", "insulin", "study"),
    ("metformin", "metformin", "study"),
    ("anticholinergics", "oxybutynin", "positive_control"),
    ("anticholinergics", "benztropine", "positive_control"),
    ("anticholinergics", "trihexyphenidyl", "positive_control"),
    ("anticholinergics", "tolterodine", "positive_control"),
    ("antipsychotics", "olanzapine", "positive_control"),
    ("antipsychotics", "clozapine", "positive_control"),
    ("antipsychotics", "haloperidol", "positive_control"),
    ("antipsychotics", "risperidone", "positive_control"),
    ("antipsychotics", "quetiapine", "positive_control"),
    ("antipsychotics", "aripiprazole", "positive_control"),
    ("SSRIs", "sertraline", "study"),
    ("SSRIs", "fluoxetine", "study"),
    ("SSRIs", "citalopram", "study"),
    ("SSRIs", "escitalopram", "study"),
    ("SSRIs", "paroxetine", "study"),
    ("topiramate/zonisamide", "topiramate", "positive_control"),
    ("topiramate/zonisamide", "zonisamide", "positive_control"),
    ("ADHD stimulants", "amphetamine", "study"),
    ("ADHD stimulants", "lisdexamfetamine", "study"),
    ("ADHD stimulants", "methylphenidate", "study"),
    ("beta blockers", "metoprolol", "study"),
    ("beta blockers", "propranolol", "study"),
    ("beta blockers", "atenolol", "study"),
    ("beta blockers", "carvedilol", "study"),
    ("fentanyl/opioid patches", "fentanyl", "study"),
    ("fentanyl/opioid patches", "buprenorphine", "study"),
    ("epinephrine auto-injectors", "epinephrine", "study"),
    ("negative control", "amoxicillin", "negative_control"),
    ("negative control", "levothyroxine", "negative_control"),
    ("negative control", "atorvastatin", "negative_control"),
]

_last = [0.0]
net_calls = [0]
_api_key = [None]


def use_api_key_from_env(var="OPENFDA_API_KEY"):
    """Enable the openFDA API key from the environment (or ROOT/.env.local). Returns True if found.
    The key is never written to disk or printed."""
    key = os.environ.get(var, "").strip()
    env_file = os.path.join(ROOT, ".env.local")
    if not key and os.path.exists(env_file):
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line.startswith(var + "="):
                    # value up to an inline '#' comment; internal whitespace removed
                    key = "".join(line.split("=", 1)[1].split("#", 1)[0].split()).strip('"').strip("'")
    _api_key[0] = key or None
    return bool(key)


def _log(url, status):
    os.makedirs(RAW, exist_ok=True)
    with open(CALL_LOG, "a") as f:
        f.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S')}\t{status}\t{url}\n")


def get(base, params, max_calls=None, compact=None, compact_tag=""):
    """GET base?params with disk cache. Returns parsed JSON (dict). 404 => {'results': [], 'not_found': True}.

    compact: optional function applied to the response before it is cached (used for large label
    pages so the cache stays small); compact_tag is appended to the cache key so compacted and
    full responses never collide."""
    safe = ':()"*[]'
    qs = "&".join(k + "=" + urllib.parse.quote(str(v), safe=safe) for k, v in params.items())
    url = f"{base}?{qs}"
    key = hashlib.sha1((url + compact_tag).encode()).hexdigest()
    path = os.path.join(CACHE, key + ".json.gz")
    if os.path.exists(path):
        with gzip.open(path, "rt") as f:
            return json.load(f)["response"]
    if max_calls is not None and net_calls[0] >= max_calls:
        raise RuntimeError("call budget exhausted")
    os.makedirs(CACHE, exist_ok=True)
    for attempt in range(5):
        wait = (0.27 if _api_key[0] else 0.35) - (time.time() - _last[0])
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.time()
        net_calls[0] += 1
        try:
            req_url = url + ("&api_key=" + _api_key[0] if _api_key[0] else "")
            try:
                with urllib.request.urlopen(req_url, timeout=90) as r:
                    data = json.loads(r.read().decode())
            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
                raise
            except Exception as e:  # never let a keyed URL reach a traceback
                raise RuntimeError(f"request failed ({type(e).__name__}) for {url}") from None
            _log(url, 200)
            break
        except urllib.error.HTTPError as e:
            _log(url, e.code)
            if e.code == 404:
                data = {"results": [], "not_found": True}
                break
            if e.code == 429 or e.code >= 500:
                time.sleep(10 * (attempt + 1))
                continue
            raise RuntimeError(f"HTTP {e.code} for {url}") from None
        except (urllib.error.URLError, TimeoutError):
            time.sleep(5 * (attempt + 1))
    else:
        raise RuntimeError(f"failed: {url}")
    if compact is not None:
        data = compact(data)
    with gzip.open(path, "wt") as f:
        json.dump({"url": url, "compact": compact_tag or None, "fetched": time.strftime("%Y-%m-%dT%H:%M:%S"), "response": data}, f)
    return data
