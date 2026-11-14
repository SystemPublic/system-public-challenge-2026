"""Replay collect.py with a counter on sysgraph.get to list the distinct requests this experiment needs,
and compare with cache files written after the experiment started (argument: start time, epoch seconds)."""
import sys, hashlib, urllib.parse, os, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "tools"), str(Path(__file__).parent)]
from concord import sysgraph as g
start = float(sys.argv[1])
seen = set()
orig = g.get
def get(path, params=None, **kw):
    p = {k: v for k, v in (params or {}).items() if v is not None}
    q = urllib.parse.urlencode(sorted(p.items()), doseq=True)
    seen.add(hashlib.sha256(f"{path}?{q}".encode()).hexdigest()[:24])
    return orig(path, params, **kw)
g.get = get
import collect
collect.main()
new = [s for s in seen if (g.CACHE / f"{s}.json").exists() and (g.CACHE / f"{s}.json").stat().st_mtime >= start]
print("distinct requests used:", len(seen), "of which written after start (uncached at start):", len(new))
