"""Graph findings linking food access (food desert, store access, supermarket) to diabetes or obesity.
Writes data/derived/health_gaps/graph_food.json."""
from __future__ import annotations
import json, re
from concord import sysgraph as g
from analyses.health_gaps.common import DER

TERMS = ["food desert", "food access", "supermarket", "grocery store", "food environment", "food retail",
         "food swamp", "healthy food retailer", "convenience store"]
OUT_RE = re.compile(r"diabet|HbA1c|glyc|obes|BMI|body mass|weight", re.I)


def main():
    seen, rows = set(), []
    for t in TERMS:
        for v in g.variables(t, limit=50):
            vid = v["system_id"]
            if vid in seen:
                continue
            seen.add(vid)
            for a in g.variable_associations(vid, max_items=200):
                txt = (a.get("variable_1_name") or "") + " " + (a.get("variable_2_name") or "")
                if OUT_RE.search(txt) and not OUT_RE.search(v.get("name") or ""):
                    rows.append({"term": t, "exposure_var": v.get("name"), "assoc": a})
    (DER / "graph_food.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False))
    print(len(seen), "variables;", len(rows), "associations with a diabetes/obesity outcome")


if __name__ == "__main__":
    main()
