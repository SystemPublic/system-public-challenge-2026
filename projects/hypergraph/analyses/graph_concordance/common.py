"""Shared helpers for the concordance-matrix study: a System API wrapper that counts uncached requests."""
from __future__ import annotations

import hashlib
import json
import sys
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
from concord import sysgraph as g  # noqa: E402

OUT = ROOT / "data" / "derived" / "graph" / "concordance"
COUNT = OUT / "requests.json"
_orig = g.get


def _counted(path, params=None, **kw):
    p = {k: v for k, v in (params or {}).items() if v is not None}
    q = urllib.parse.urlencode(sorted(p.items()), doseq=True)
    sig = hashlib.sha256(f"{path}?{q}".encode()).hexdigest()[:24]
    miss = not (g.CACHE / f"{sig}.json").exists()
    out = _orig(path, params, **kw)
    if miss:
        d = json.loads(COUNT.read_text()) if COUNT.exists() else {"uncached_requests": 0}
        d["uncached_requests"] += 1
        COUNT.write_text(json.dumps(d))
    return out


g.get = _counted


def used() -> int:
    return json.loads(COUNT.read_text())["uncached_requests"] if COUNT.exists() else 0
