"""Client for the System Public Graph API (v1.0, closed beta).

The key is read from $SYSTEM_API_KEY, a .env file at the root, or ~/.config/system/token. It is never
written into the repo, the cache, or any output. Responses are cached on disk
under data/cache/sysgraph/, keyed by the request path and query (without the
key), so the cache is the same on every machine.

Data model (docs.system.com, read 12 Nov 2026):
  concept      Wikidata-grounded node (system_id, wikidata_id, wikidata_label)
  variable     a study's measured variable, grounded to a concept
  association  one finding: variable_1 -- variable_2, statistic_type/value,
               ci_lower/ci_upper, p_value, study_id, pubmed_id
  relationship concept|concept aggregate: num_findings, num_studies
  study        study_id, doi, pubmed_id, population, study_type

The docs warn that about 20% of API associations may be mis-extracted and
recommend dropping those absent from the Dataverse CSV (see concord/dataverse.py).
"""
from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.parse
from pathlib import Path

import requests

BASE = "https://public-api.system.com"
API_VERSION = "v1.0"
DATASET_VERSION = "Dataverse v2.1, doi:10.7910/DVN/7V6JDO"
ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "data" / "cache" / "sysgraph"


def _key() -> str:
    """The key comes from $SYSTEM_API_KEY, then a `.env` file at the repository
    root (a line SYSTEM_API_KEY=...), then ~/.config/system/token."""
    k = os.environ.get("SYSTEM_API_KEY")
    if k:
        return k.strip()
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            name, sep, value = line.strip().partition("=")
            if sep and name.strip().removeprefix("export ").strip() == "SYSTEM_API_KEY" and value.strip():
                return value.strip().strip("\"'")
    p = Path.home() / ".config" / "system" / "token"
    if not p.exists():
        raise SystemExit("No System API key: set SYSTEM_API_KEY in .env or put the key in ~/.config/system/token")
    return p.read_text().strip()


def get(path: str, params: dict | None = None, *, refresh: bool = False, retries: int = 4) -> dict:
    """GET a v1 path such as '/v1/concepts'. Returns parsed JSON (cached)."""
    params = {k: v for k, v in (params or {}).items() if v is not None}
    q = urllib.parse.urlencode(sorted(params.items()), doseq=True)
    sig = hashlib.sha256(f"{path}?{q}".encode()).hexdigest()[:24]
    f = CACHE / f"{sig}.json"
    if f.exists() and not refresh:
        return json.loads(f.read_text())["response"]
    url = BASE + path
    last = None
    for i in range(retries):
        try:
            r = requests.get(url, params=params, headers={"x-api-key": _key()}, timeout=60)
            if r.status_code == 404:
                out = {"error": 404, "data": []}
                break
            if r.status_code in (429, 500, 502, 503, 504):
                last = r.status_code
                time.sleep(2 * (i + 1))
                continue
            r.raise_for_status()
            out = r.json()
            break
        except requests.RequestException as e:  # network
            last = e
            time.sleep(2 * (i + 1))
    else:
        raise RuntimeError(f"System API failed for {path} {params}: {last}")
    CACHE.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps({"path": path, "params": params, "fetched": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                             "api_version": API_VERSION, "response": out}))
    return out


def page_all(path: str, params: dict | None = None, *, limit: int = 100, max_items: int = 5000) -> list[dict]:
    """Follow offset pagination until exhausted or max_items reached."""
    params = dict(params or {})
    out, offset, seen = [], 0, set()
    while len(out) < max_items:
        d = get(path, {**params, "limit": limit, "offset": offset})
        rows = d.get("data", [])
        # The API's offset paging repeats some rows (graph audit, 12 Nov 2026); keep the first copy.
        for r in rows:
            k = r.get("system_id") or r.get("relationship_id") or r.get("study_id") or json.dumps(r, sort_keys=True)
            if k not in seen:
                seen.add(k)
                out.append(r)
        if len(rows) < limit:
            break
        offset += limit
    return out[:max_items]


def enc(rel_id: str) -> str:
    return urllib.parse.quote(rel_id, safe="")


# --- convenience wrappers -------------------------------------------------

def concepts(search: str, limit: int = 20) -> list[dict]:
    """Search concepts by label. The search matches whole words; multi-word
    phrases often return nothing, so try single distinctive words too."""
    return get("/v1/concepts", {"search": f"wikidata_label:{search}", "limit": limit}).get("data", [])


def variables(search: str, limit: int = 50) -> list[dict]:
    return get("/v1/variables", {"search": f"name:{search}", "limit": limit}).get("data", [])


def concept(cid: str) -> dict:
    return get(f"/v1/concepts/{cid}")


def concept_relationships(cid: str, max_items: int = 2000) -> list[dict]:
    return page_all(f"/v1/concepts/{cid}/relationships", max_items=max_items)


def concept_variables(cid: str, max_items: int = 2000) -> list[dict]:
    return page_all(f"/v1/concepts/{cid}/variables", max_items=max_items)


def relationship(rel_id: str) -> dict:
    return get(f"/v1/relationships/{enc(rel_id)}")


def relationship_associations(rel_id: str, max_items: int = 2000) -> list[dict]:
    return page_all(f"/v1/relationships/{enc(rel_id)}/associations", max_items=max_items)


def relationship_studies(rel_id: str, max_items: int = 500) -> list[dict]:
    return page_all(f"/v1/relationships/{enc(rel_id)}/studies", max_items=max_items)


def variable_associations(vid: str, max_items: int = 2000) -> list[dict]:
    return page_all(f"/v1/variables/{vid}/associations", max_items=max_items)


def study(sid: str) -> dict:
    return get(f"/v1/studies/{sid}")


def relationships_between(a: str, b: str) -> list[dict]:
    """Both directions of a concept pair (ids are source|target)."""
    out = []
    for rid in (f"{a}|{b}", f"{b}|{a}"):
        d = relationship(rid)
        if d and not d.get("error") and d.get("relationship_id"):
            out.append(d)
    return out


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "/v1/concepts"
    params = dict(a.split("=", 1) for a in sys.argv[2:])
    print(json.dumps(get(path, params), indent=1)[:6000])
