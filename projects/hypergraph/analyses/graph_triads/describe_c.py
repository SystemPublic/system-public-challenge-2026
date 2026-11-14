"""Collect Wikidata descriptions of every concept seen in the cached relationship pages (no new requests)."""
import json, glob
from common import g, OUT
desc = {}
for f in glob.glob(str(g.CACHE / "*.json")):
    try:
        d = json.load(open(f))
    except Exception:
        continue
    if "/relationships" not in d.get("path", "") or not d["path"].startswith("/v1/concepts/"):
        continue
    for r in d["response"].get("data", []):
        for k in ("source_concept", "target_concept"):
            c = r.get(k) or {}
            if c.get("system_id"):
                desc[c["system_id"]] = [c.get("wikidata_label"), c.get("wikidata_description") or ""]
(OUT / "concept_descriptions.json").write_text(json.dumps(desc))
print(len(desc))
