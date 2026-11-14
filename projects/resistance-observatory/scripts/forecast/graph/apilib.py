"""Tiny cached client for the System Public Graph API v1.0.
Key read from env SYSTEM_API_KEY only; never printed or written.
Every response is saved to raw/<sanitized path>.json; a cached file is reused
instead of re-requesting (so re-runs cost nothing)."""
import json, os, re, sys, time, urllib.request, urllib.error, urllib.parse
from concurrent.futures import ThreadPoolExecutor

BASE = "https://public-api.system.com/v1"
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
RAW = os.path.join(REPO, "data", "forecast", "raw", "graph")
os.makedirs(RAW, exist_ok=True)
KEY = os.environ.get("SYSTEM_API_KEY")
COUNT = {"net": 0, "cache": 0}


def fname(path):
    s = re.sub(r"[^A-Za-z0-9._=-]+", "_", path.strip("/"))
    return os.path.join(RAW, s[:200] + ".json")


def get(path):
    f = fname(path)
    if os.path.exists(f):
        COUNT["cache"] += 1
        with open(f) as fh:
            return json.load(fh)
    if not KEY:
        sys.exit("SYSTEM_API_KEY not set")
    for attempt in range(5):
        COUNT["net"] += 1
        req = urllib.request.Request(BASE + path, headers={"x-api-key": KEY, "User-Agent": "graph-recon/0.1"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                body = json.loads(r.read().decode())
            break
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < 4:
                time.sleep(1.5 * 2 ** attempt)
                continue
            body = {"_error": e.code, "_body": e.read().decode()[:500]}
            break
    with open(f, "w") as fh:
        json.dump({"_request": "GET " + path, "response": body}, fh, indent=1)
    return {"_request": "GET " + path, "response": body}


def resp(path):
    return get(path)["response"]


def paged(path, page=200, maxrows=2000):
    sep = "&" if "?" in path else "?"
    rows, total = [], None
    off = 0
    while off < maxrows:
        r = resp(f"{path}{sep}limit={page}&offset={off}&include_total=true")
        if "_error" in r:
            return rows, total, r
        data = r.get("data", [])
        if isinstance(r.get("total"), int):
            total = r["total"]
        rows += data
        if len(data) < page or (total is not None and len(rows) >= total):
            break
        off += page
    return rows, total, None


def pmap(fn, items, n=6):
    with ThreadPoolExecutor(n) as ex:
        return list(ex.map(fn, items))
