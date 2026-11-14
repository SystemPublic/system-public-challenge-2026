"""What the System graph holds on temperature and violence, by variable-name search.

Searches study variables on the violence side and on the temperature side, fetches each
variable's associations, and keeps associations whose two variables pair a temperature
term with a violence term. Stops at a fixed cap of uncached requests.

Run: ~/.venvs/nyc-concordance/bin/python -m analyses.heat_extremes.graph_shape
Writes data/derived/heat_extremes/graph_temp_violence_variables.json
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import analyses.transfer.gcount as gc  # noqa: E402
from concord import sysgraph as g  # noqa: E402

OUT = ROOT / "data" / "derived" / "heat_extremes"
CAP = 900
VTERMS = ["assault", "homicide", "violent crime", "shooting", "shootings", "aggression", "violence", "crime", "firearm",
          "gun violence", "murder", "aggressive behavior"]
TTERMS = ["ambient temperature", "heat wave", "heatwave", "air temperature", "maximum temperature", "daily temperature",
          "mean temperature", "apparent temperature", "heat index", "extreme heat", "hot days", "temperature", "heat",
          "weather", "season", "summer"]
T_RE = re.compile(r"temperatur|heat ?wave|\bheat\b|\bhot\b|weather|season|summer|winter|humid|climat|warm", re.I)
T_NOT = re.compile(r"body|rectal|skin|core|water|oral|tympan|fever|heat shock|storage|cook|pain|thermal sens|stimul|incubat|anneal|"
                   r"sinter|calcin|react|melting|transition|heat treat|tolerance|heart", re.I)
V_RE = re.compile(r"assault|homicid|violen|shoot|aggress|crime|firearm|murder|gun\b|robber|batter", re.I)


def main():
    hits, seen = {}, set()
    def scan(v, own_re, other_re):
        vid = v["system_id"]
        if vid in seen or gc.N["uncached"] >= CAP:
            return
        seen.add(vid)
        for a in g.variable_associations(vid, max_items=300):
            side = "2" if a.get("variable_1_id") == vid else "1"
            other = a.get(f"variable_{side}_name") or ""
            if other_re.search(other):
                k = a.get("system_id") or json.dumps([a.get("variable_1_id"), a.get("variable_2_id"), a.get("study_id")])
                hits[k] = {x: a.get(x) for x in ("variable_1_name", "variable_2_name", "system_statistic_type", "statistic_value",
                                                 "ci_lower", "ci_upper", "p_value", "pubmed_id", "doi", "study_id", "population")}
    nv = nt = 0
    for term in VTERMS:
        for v in g.variables(term, limit=100):
            if V_RE.search(v.get("name") or ""):
                nv += 1
                scan(v, V_RE, T_RE)
    for term in TTERMS:
        for v in g.variables(term, limit=100):
            n = v.get("name") or ""
            if T_RE.search(n) and not T_NOT.search(n):
                nt += 1
                scan(v, T_RE, V_RE)
    rows = [h for h in hits.values() if not T_NOT.search((h["variable_1_name"] or "") + " " + (h["variable_2_name"] or ""))]
    out = {"violence_variables": nv, "temperature_variables": nt, "variables_scanned": len(seen), "uncached_requests": gc.N["uncached"],
           "cap": CAP, "associations": rows}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "graph_temp_violence_variables.json").write_text(json.dumps(out, indent=1))
    print(nv, nt, len(seen), gc.N, len(rows))
    for h in rows:
        print(h["pubmed_id"], "|", h["variable_1_name"], "|", h["variable_2_name"], "|", h["system_statistic_type"], h["statistic_value"], h["ci_lower"], h["ci_upper"])


if __name__ == "__main__":
    main()
