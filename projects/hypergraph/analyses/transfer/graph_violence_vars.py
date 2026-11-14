"""Violence-side study variables (named, often ungrounded) whose associations name temperature or weather.
Run: ~/.venvs/nyc-concordance/bin/python -u -m analyses.transfer.graph_violence_vars
"""
import json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import analyses.transfer.gcount as gc  # noqa
from concord import sysgraph as g  # noqa

OUT = ROOT / "data" / "derived" / "graph" / "transfer_chicago"
SEARCH = ["shootings", "firearm violence", "gun violence", "assaults", "violent crime", "homicide", "crime rate", "murder"]
good = re.compile(r"gun|firearm|assault|homicide|murder|violent crime|shooting incident|shootings|crime rate|violent|violence|crime", re.I)
bad = re.compile(r"sandy hook|shoot dry|shoots|shoot |shooters|shooting (accuracy|performance|zone)|true shooting|three-point|jump shoot|gallery|galleries|sexual|bullying|cyber|dating|school|police|victim|witness|exposure|exposed|perpetrat|restraining|advocacy|public health|agreeing|mention", re.I)
tp = re.compile(r"temperature|heat|weather|\bhot\b|warm|degree|climate|season|summer", re.I)
seen = {}
for t in SEARCH:
    for r in g.variables(t, limit=100):
        seen[r["system_id"]] = r
v = [r for r in seen.values() if good.search(r["name"] or "") and not bad.search(r["name"] or "")]
print(len(seen), "variables found;", len(v), "kept", flush=True)
hits, done = [], 0
for r in v:
    try:
        rows = g.variable_associations(r["system_id"], max_items=100)
    except Exception as e:
        print("fail", r["name"][:50], e, flush=True); continue
    done += 1
    for a in rows:
        o1, o2 = a.get("variable_1_name") or "", a.get("variable_2_name") or ""
        other = o2 if a.get("variable_1_id") == r["system_id"] else o1
        if tp.search(other):
            hits.append({"violence_var": r["name"], "other": other, "study_id": a.get("study_id"), "pubmed": a.get("pubmed_id"),
                         "stat": a.get("system_statistic_type"), "val": a.get("statistic_value"), "ci": [a.get("ci_lower"), a.get("ci_upper")]})
    if done % 10 == 0:
        print(done, len(hits), gc.N, flush=True)
(OUT / "violence_variable_temperature_hits.json").write_text(json.dumps({"n_variables_checked": done, "hits": hits, "uncached_requests": gc.N["uncached"]}, indent=1))
print("DONE", done, len(hits), gc.N, flush=True)
