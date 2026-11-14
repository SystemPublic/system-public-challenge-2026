#!/usr/bin/env python
"""Shared neighbours in the System Public Graph for the three confounded pairs and for
control pairs. Writes data/derived/graph/confounders/shared_<pair>.json and specificity.json.
Run: ~/.venvs/nyc-concordance/bin/python analyses/graph_confounders/shared.py
All API responses are cached by concord/sysgraph.py."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "tools"))
import graph_paths as gp  # noqa: E402

OUT = ROOT / "data/derived/graph/confounders"
GREEN = ["I2CN3brExA", "lHLIKbfnYp", "hsryqxdFzE", "6DTj2ennMm"]      # tree, green space, NDVI, park
TEMP = ["sSuplgYnDQ", "mUxSLRMwIy", "UbF0-c8zHb", "k9BAffdSqv", "dINFs04idR"]  # surface temp, air temp, UHI, heat wave, hot
HEATILL = ["rYCo7LTyzN", "PtQBvGm5CM", "2M0TDlEdLk", "FDJ4Gulj_Q"]   # heat stroke, heat illness, heat exhaustion, hyperthermia
ACTIVE = ["_2dhcsFISl", "nB_DNapip8", "iSnN_TnuWd"]                  # walking, public transport, motor car
OBES = ["cj7G775u_Q", "slXbabUYMb", "YtQ5lW8obL"]                    # obesity, overweight, BMI
VACANT = ["IFcQ3j86qe", "NSSHqnR5tw", "QC5uxyjQb5", "2gR7THM-gS"]    # housing, housing quality, urban renewal, neighbourhood characteristics
SHOOT = ["X7hfhwez9f", "5-tHcH0EjT", "14UOQBVakG", "Sb3zGs-d5I", "YZku29igbl", "2qLKgaxkm_", "V7ImOTxbql"]

TARGET = {
    "green__temperature": (GREEN, TEMP),
    "temperature__heat-illness": (TEMP, HEATILL),
    "green__heat-illness": (GREEN, HEATILL),
    "active-travel__obesity": (ACTIVE, OBES),
    "housing-vacancy__gun-violence": (VACANT, SHOOT),
}
# Control pairs: unrelated to the targets, resolved by exact label. Five further pairs were tried and
# dropped because whole-word concept search did not resolve one end (educational attainment, depression,
# loneliness, alcoholic beverage, fracture).
CONTROL = {
    "smoking__lung-cancer": ("smoking", "lung cancer"),
    "breastfeeding__asthma": ("breastfeeding", "asthma"),
    "coffee__stroke": ("coffee", "stroke"),
    "air-pollution__preterm-birth": ("air pollution", "preterm birth"),
    "noise__hypertension": ("noise", "hypertension"),
}


def exact(term):
    r = gp.resolve(term, expand=False)
    ex = [c for c in r if c["label"].lower() == term.lower()]
    return [c["system_id"] for c in (ex or r[:1])]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    res = {}
    for name, (a, b) in TARGET.items():
        res[name] = gp.between(a, b, 1)
    for name, (a, b) in CONTROL.items():
        ia, ib = exact(a), exact(b)
        if not ia or not ib:
            print("unresolved", name, ia, ib); continue
        res[name] = gp.between(ia, ib, 1)
    for name, r in res.items():
        (OUT / f"shared_{name}.json").write_text(json.dumps(r, indent=1))
        print(f"{name}: a={[c['label'] for c in r['a']]} b={[c['label'] for c in r['b']]} direct={r['direct_findings']} "
              f"nA={r['neighbours_a']} nB={r['neighbours_b']} shared={len(r['shared'])}")
    # specificity
    K = 20
    top = {n: [s["label"] for s in r["shared"][:K]] for n, r in res.items()}
    ctrl = [n for n in res if n in CONTROL]
    spec = {"K": K, "controls": ctrl, "targets": {}}
    for n in TARGET:
        rows = []
        for lab in top[n]:
            hits = [c for c in ctrl if lab in top[c]]
            anyrank = [c for c in ctrl if lab in [s["label"] for s in res[c]["shared"]]]
            rows.append({"label": lab, "in_top20_of_controls": len(hits), "shared_at_all_in_controls": len(anyrank)})
        spec["targets"][n] = {
            "top": rows,
            "share_top20_in_any_control_top20": sum(r["in_top20_of_controls"] > 0 for r in rows) / max(len(rows), 1),
            "share_top20_in_3plus_control_top20": sum(r["in_top20_of_controls"] >= 3 for r in rows) / max(len(rows), 1),
            "mean_jaccard_with_controls": sum(len(set(top[n]) & set(top[c])) / len(set(top[n]) | set(top[c])) for c in ctrl) / len(ctrl),
        }
    cc = [len(set(top[a]) & set(top[b])) / len(set(top[a]) | set(top[b])) for i, a in enumerate(ctrl) for b in ctrl[i + 1:]]
    spec["mean_jaccard_control_vs_control"] = sum(cc) / len(cc)
    (OUT / "specificity.json").write_text(json.dumps(spec, indent=1))
    for n, d in spec["targets"].items():
        print(n, {k: round(v, 3) for k, v in d.items() if k != "top"})
        for r in d["top"]:
            print(f"    {r['in_top20_of_controls']:2d}/{len(ctrl)} top20  {r['shared_at_all_in_controls']:2d}/{len(ctrl)} any   {r['label']}")
    print("control-control jaccard", round(spec["mean_jaccard_control_vs_control"], 3))


if __name__ == "__main__":
    main()
