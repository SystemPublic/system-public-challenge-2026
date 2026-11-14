"""Collect System Public Graph variables and associations on turning vehicles, turn bans and turn calming.
Writes data/derived/turn_restrictions/graph_raw.json and prints a compact list. Re-runs from cache."""
import json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from concord import sysgraph as sg

TERMS = ["left turn", "left-turn", "turning vehicle", "turning movement", "turn restriction", "turn ban",
         "intersection", "hardened centerline", "traffic calming", "pedestrian crash", "pedestrian collision",
         "failure to yield", "protected left", "signal phasing", "displacement", "crash migration"]
PAT = re.compile(r"turn|intersection|calming|yield|phas|displac|migrat", re.I)
out = {}
for t in TERMS:
    vs = sg.variables(t, limit=50)
    recs = []
    for v in vs:
        if not PAT.search(v.get("name", "")):
            continue
        vid = v.get("system_id") or v.get("id")
        try:
            assoc = sg.variable_associations(vid, max_items=50)
        except Exception as e:
            assoc = [{"error": str(e)}]
        recs.append({"variable": v, "associations": assoc})
    out[t] = recs
    print(t, len(vs), len(recs), sum(len(r["associations"]) for r in recs))
(ROOT / "data/derived/turn_restrictions/graph_raw.json").write_text(json.dumps(out, indent=1))
