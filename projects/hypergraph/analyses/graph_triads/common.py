"""Shared helpers for the open-triad study: a request counter around the graph client."""
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "tools"))
from concord import sysgraph as g  # noqa: E402
OUT = ROOT / "data" / "derived" / "graph" / "triads"
OUT.mkdir(parents=True, exist_ok=True)
COUNT = OUT / "request_count.json"
_orig = g.get
import hashlib, urllib.parse

def _counted(path, params=None, **kw):
    p = {k: v for k, v in (params or {}).items() if v is not None}
    q = urllib.parse.urlencode(sorted(p.items()), doseq=True)
    f = g.CACHE / (hashlib.sha256(f"{path}?{q}".encode()).hexdigest()[:24] + ".json")
    miss = not f.exists()
    out = _orig(path, params, **kw)
    if miss:
        d = json.loads(COUNT.read_text()) if COUNT.exists() else {"uncached_requests": 0}
        d["uncached_requests"] += 1
        COUNT.write_text(json.dumps(d))
    return out
g.get = _counted

def used():
    return json.loads(COUNT.read_text())["uncached_requests"] if COUNT.exists() else 0

def rels(cid, lim=1000, max_items=20000):
    """All relationships of a concept, 1000 per page, de-duplicated."""
    return g.page_all(f"/v1/concepts/{cid}/relationships", limit=lim, max_items=max_items)
