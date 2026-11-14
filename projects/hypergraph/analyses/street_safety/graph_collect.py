"""Collect System Public Graph variables and associations on street-safety interventions.
Writes data/derived/street_safety/graph_evidence.json. Re-runs from cache."""
import json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from concord import sysgraph as sg

TERMS = {
    "red_light_camera": ["red light camera", "red-light camera", "red light", "red-light", "traffic light camera", "signal violation"],
    "speed_camera": ["speed camera", "automated speed", "speed enforcement"],
    "lpi": ["leading pedestrian", "pedestrian interval", "pedestrian signal"],
    "road_diet": ["road diet", "lane reduction", "rechannelization"],
    "daylighting": ["daylighting", "sight distance", "parking near intersection"],
    "ped_bridge": ["pedestrian bridge", "overpass", "footbridge", "pedestrian overpass"],
    "rear_end": ["rear-end", "rear end"],
    "right_angle": ["right-angle", "angle crash", "angle collision"],
    "pedestrian_injury": ["pedestrian injur", "pedestrian collision", "pedestrian crash", "pedestrian fatal"],
    "traffic_calming": ["traffic calming", "speed hump", "20 mph", "speed limit"],
}
out = {}
for k, terms in TERMS.items():
    vs = {}
    for t in terms:
        for v in sg.variables(t, limit=50):
            vs[v.get("system_id") or v.get("id")] = v
    pat = re.compile("|".join(re.escape(t.split()[0] if k in ("ped_bridge",) else t) for t in terms), re.I)
    vs = {i: v for i, v in vs.items() if pat.search(v.get("name", ""))}
    recs = []
    for vid, v in list(vs.items())[:25]:
        try:
            assoc = sg.variable_associations(vid, max_items=50)
        except Exception as e:
            assoc = [{"error": str(e)}]
        recs.append({"variable": v, "associations": assoc})
    out[k] = recs
    print(k, len(vs), sum(len(r["associations"]) for r in recs))
(ROOT / "data/derived/street_safety").mkdir(parents=True, exist_ok=True)
(ROOT / "data/derived/street_safety/graph_raw.json").write_text(json.dumps(out, indent=1))
