"""Count uncached System API requests made by this study (wraps concord.sysgraph.get)."""
import json
from concord import sysgraph as g

_orig = g.get
N = {"uncached": 0}


def _counting(path, params=None, *, refresh=False, retries=4):
    import hashlib, urllib.parse
    p = {k: v for k, v in (params or {}).items() if v is not None}
    q = urllib.parse.urlencode(sorted(p.items()), doseq=True)
    f = g.CACHE / (hashlib.sha256(f"{path}?{q}".encode()).hexdigest()[:24] + ".json")
    if refresh or not f.exists():
        N["uncached"] += 1
    return _orig(path, params, refresh=refresh, retries=retries)


g.get = _counting
