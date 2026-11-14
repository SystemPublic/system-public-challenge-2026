"""Collect System graph evidence for the neighbourhood claims.

Searches variables by keyword, keeps the ones relevant to each topic, and
writes their associations to data/derived/neighbourhood/graph_<topic>.json.
Re-runnable; every request is cached by concord.sysgraph.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from concord import sysgraph as s  # noqa: E402

OUT = ROOT / "data" / "derived" / "neighbourhood"
OUT.mkdir(parents=True, exist_ok=True)

TOPICS = {
    "vacant": {"searches": ["vacant", "blighted", "abandoned"],
               "keep": r"vacant|blight|abandon"},
    "noise": {"searches": ["noise"],
              "keep": r"traffic noise|road noise|aircraft noise|railway noise|environmental noise|noise annoyance|noise exposure|noise pollution|residential.*noise|night.*noise|noise.*night|transportation noise|community noise|noise complaint|neighbou?r noise"},
    "rodent": {"searches": ["rodent", "mouse allergen", "allergen"],
               "keep": r"rodent|mouse allergen|mus m|rat allergen|rattus|mice|rats within|cockroach"},
}


def collect(topic):
    cfg = TOPICS[topic]
    seen = {}
    for q in cfg["searches"]:
        for v in s.variables(q, limit=100):
            if re.search(cfg["keep"], v["name"], re.I):
                seen[v["system_id"]] = v["name"]
    out = []
    for vid, name in seen.items():
        assoc = s.variable_associations(vid, max_items=200)
        out.append({"variable_id": vid, "name": name, "associations": assoc})
    (OUT / f"graph_{topic}.json").write_text(json.dumps(out, indent=1))
    return out


if __name__ == "__main__":
    for t in sys.argv[1:] or TOPICS:
        res = collect(t)
        print(t, len(res), "variables", sum(len(r["associations"]) for r in res), "associations")
