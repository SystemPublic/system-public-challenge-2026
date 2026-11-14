"""Census API fetch with a source record (URL without key, vintage metadata, fetch time) and a cache.
Official open source. Generic User-Agent."""
import hashlib, json, time
from pathlib import Path
import requests
ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "data" / "cache" / "census"
HDR = {"User-Agent": "research-client/1.0"}

def get(url, params=None):
    CACHE.mkdir(parents=True, exist_ok=True)
    sig = hashlib.sha256((url + json.dumps(params, sort_keys=True)).encode()).hexdigest()[:20]
    f = CACHE / f"{sig}.json"
    if f.exists():
        d = json.loads(f.read_text()); return d["data"], d["source"]
    for i in range(5):
        r = requests.get(url, params=params, headers=HDR, timeout=120)
        if r.status_code == 200: break
        time.sleep(3 * (i + 1))
    r.raise_for_status()
    src = {"kind": "census-api", "url": r.url, "last_modified": r.headers.get("Last-Modified"),
           "date": r.headers.get("Date"), "fetched": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "n_rows": None}
    data = r.json(); src["n_rows"] = len(data) - 1
    f.write_text(json.dumps({"data": data, "source": src}))
    return data, src

def table(dataset, variables, county, state="36"):
    """tract rows for one county -> (dict geoid -> {var: value}, source)"""
    url = f"https://api.census.gov/data/{dataset}"
    data, src = get(url, {"get": ",".join(variables), "for": "tract:*", "in": f"state:{state} county:{county}"})
    h = data[0]; out = {}
    for row in data[1:]:
        d = dict(zip(h, row)); out[d["state"] + d["county"] + d["tract"]] = {k: (float(v) if v not in (None, "") and k in variables else None) for k, v in d.items() if k in variables}
    return out, src
