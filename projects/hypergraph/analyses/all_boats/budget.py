"""Counts uncached requests to the System API across runs of this task (limit 1,200)."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "tools"))
from concord import sysgraph as g
F = ROOT / "data" / "derived" / "all_boats" / "api_requests.json"
LIMIT = 1150
_orig = g.requests.get
def _counted(*a, **k):
    n = json.loads(F.read_text())["n"] if F.exists() else 0
    if n >= LIMIT:
        raise SystemExit(f"API budget reached ({n})")
    F.parent.mkdir(parents=True, exist_ok=True)
    F.write_text(json.dumps({"n": n + 1}))
    return _orig(*a, **k)
g.requests.get = _counted
def used():
    return json.loads(F.read_text())["n"] if F.exists() else 0
