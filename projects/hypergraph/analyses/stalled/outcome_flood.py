"""Write the outcome of stalled-flood-zone-starts from flood_result.json and the rule 9 check."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from concord import claims

D = ROOT / "data/derived/stalled"
r = json.loads((D / "flood_result.json").read_text())
k = json.loads((D / "flood_rule9_check.json").read_text())
vs = json.loads((D / "vesting_result.json").read_text())["sources"]
bb = r["by_borough"]
claims.outcome({
    "id": "stalled-flood-zone-starts",
    "verdict": "unsettled",
    "city_effect": {"label": "borough-stratified (Mantel-Haenszel) risk difference in the 36-month no-CO rate, flood minus non-flood",
                    "estimate": round(r["mh_rd"], 3), "lo": round(r["lo"], 3), "hi": round(r["hi"], 3),
                    "scale": "difference in proportions", "null": 0, "n": r["sizes"]["with_pluto"]},
    "graph_effect": None,
    "sources": vs + [r["source_pluto"]],
    "prediction_scored": ("miss in direction: the estimate is %.3f, opposite to the prediction. The registered refute condition (upper bound < 0) "
                          "was met with the registered seed and draws (upper bound %.4f), but under rule 9 the re-run gives %.4f with 20,000 draws "
                          "and an upper bound below 0 under 19 of 20 other seeds (range %.4f to %.4f), so the condition is neither met nor unmet "
                          "and the verdict is unsettled.") % (r["mh_rd"], r["hi"], k["draws20000"][1],
                                                               min(v[1] for v in k["other_seeds"].values()), max(v[1] for v in k["other_seeds"].values())),
    "settle": ("A larger sample (all foundation starts 2014-2023, not only the December-June windows), the flood zone at the date of the permit "
               "rather than the current PLUTO flag, and a control for project size (proposed units or floor area)."),
    "research_needed": [
        {"question": "Why do floodplain starts in Queens finish faster and those in Brooklyn and Manhattan slower than other starts in the same borough?",
         "data": "flood_jobs.csv with proposed units, building type and neighbourhood", "design": "stratify by NTA and project size", "priority": "medium"},
        {"question": "Do groundwater and dewatering problems, rather than the flood-construction rules, delay foundations near the shore?",
         "data": "DOB/ECB violations citing BC 3303.14 (drainage of excavations) by lot, joined to foundation starts", "design": "rate of dewatering violations by flood zone and the later completion of those jobs", "priority": "high"}],
    "figures": [],
    "notes": ("Crude rates: flood %.3f, other %.3f. By borough (flood vs other): " % (r["crude"]["flood"], r["crude"]["other"])
              + "; ".join(f"{b} {v['flood_rate']:.3f} (n {v['flood_n']}) vs {v['other_rate']:.3f} (n {v['other_n']})" for b, v in bb.items() if v["flood_rate"] is not None)
              + ". The pooled difference is driven by Queens, where 198 floodplain starts finished faster than other Queens starts; in Brooklyn "
              "and Manhattan the floodplain starts finished more slowly. The outcome measure (job number or BBL matching) was fixed after the "
              "result of stalled-421a-vesting-footings and before this claim was registered."),
})
print("outcome written")
