"""Stage 4: list open triads A - B - C and rank them by the weaker link.

A is an exposure family (several concepts pooled), B a concept with findings on both sides,
C a concept with at most MAX_DIRECT findings linking it to any member of A's family.
Output: data/derived/graph/triads/open_triads.csv and generic.json.
"""
import json, csv, collections
from common import g, OUT, used
from exposures import neigh
from intermediates import HAND_GENERIC

FAMILIES = {
    "noise": ["noise pollution", "traffic noise", "noise"],
    "air pollution": ["air pollution", "traffic-related pollution", "nitrogen dioxide", "particulates", "ozone", "air pollutant", "traffic"],
    "indoor air and pests": ["indoor air pollution", "cockroach", "pest control", "rodent control", "housing quality"],
    "heat": ["air temperature", "surface temperature", "urban heat island", "heat wave", "hot", "temperature"],
    "green space": ["green space", "park", "tree"],
    "urban form": ["urban area", "urbanization", "population density", "built environment", "neighborhood characteristics", "neighborhood"],
    "crowding": ["household crowding", "overcrowding"],
    "housing and homelessness": ["housing", "housing instability", "public housing", "homeless person"],
    "walking": ["walking"],
    "shift work and light at night": ["shift work", "light pollution", "artificial light"],
    "flood": ["flood", "flooding"],
    "fast food": ["fast food", "food desert", "food insecurity"],
    "poverty and unemployment": ["poverty", "poverty area", "unemployment", "unemployed"],
    "crime": ["crime", "violent crime"],
    "traffic collision": ["traffic collision"],
}
EXTRA_IDS = {"temperature": None, "air pollutant": None}
MIN_AB, MIN_BC, MAX_DIRECT = 5, 10, 1
GENERIC_SHARE = 0.25

def load():
    ex = json.loads((OUT / "exposure_neighbours.json").read_text())
    inter = json.loads((OUT / "intermediate_neighbours.json").read_text())
    lab2id = {v["label"]: k for k, v in inter.items()}
    for lab in EXTRA_IDS:
        if lab not in ex and lab in lab2id:
            n = neigh(lab2id[lab])
            ex[lab] = {"system_id": lab2id[lab], "n_neighbours": len(n), "n_findings": sum(d["f"] for d in n.values()), "neighbours": n}
    return ex, inter

def generic(ex, inter):
    """Share of the fetched concepts (exposures and intermediates) for which X is among the ten neighbours with most studies."""
    lists = {}
    for lab, v in ex.items():
        if v["n_neighbours"] >= 20:
            lists[v["system_id"]] = v["neighbours"]
    for cid, v in inter.items():
        lists[cid] = v["neighbours"]
    cnt, name = collections.Counter(), {}
    for cid, nb in lists.items():
        for oid, d in sorted(nb.items(), key=lambda kv: -kv[1]["s"])[:10]:
            cnt[oid] += 1; name[oid] = d["label"]
    n = len(lists)
    rows = [{"system_id": k, "label": name[k], "top10_share": c / n} for k, c in cnt.most_common()]
    return n, rows

if __name__ == "__main__":
    ex, inter = load()
    n, grows = generic(ex, inter)
    gen_ids = {r["system_id"] for r in grows if r["top10_share"] >= GENERIC_SHARE}
    gen_lab = {r["label"] for r in grows if r["top10_share"] >= GENERIC_SHARE} | HAND_GENERIC
    (OUT / "generic.json").write_text(json.dumps({"n_lists": n, "threshold": GENERIC_SHARE, "hand_list": sorted(HAND_GENERIC),
                                                  "computed": grows[:60]}, indent=1))
    print("generic by top-10 share (of", n, "lists):", [(r["label"], round(r["top10_share"], 2)) for r in grows[:25]])
    exid = {v["system_id"]: lab for lab, v in ex.items()}
    rows = []
    for fam, members in FAMILIES.items():
        mem = [m for m in members if m in ex]
        direct = collections.Counter(); ab = {}
        for m in mem:
            for oid, d in ex[m]["neighbours"].items():
                direct[oid] += d["f"]
                a = ab.setdefault(oid, {"label": d["label"], "s": 0, "f": 0, "via": []})
                a["s"] += d["s"]; a["f"] += d["f"]; a["via"].append((m, d["s"]))
        fam_ids = {ex[m]["system_id"] for m in mem}
        for bid, a in ab.items():
            if a["s"] < MIN_AB or bid not in inter or a["label"] in gen_lab or bid in fam_ids:
                continue
            for cid, d in inter[bid]["neighbours"].items():
                if d["s"] < MIN_BC or cid in fam_ids or d["label"] in gen_lab or cid == bid:
                    continue
                if direct.get(cid, 0) > MAX_DIRECT:
                    continue
                rows.append({"family": fam, "A_members": "; ".join(f"{m}({s})" for m, s in sorted(a["via"], key=lambda x: -x[1])),
                             "B": a["label"], "B_id": bid, "C": d["label"], "C_id": cid, "studies_AB": a["s"], "findings_AB": a["f"],
                             "studies_BC": d["s"], "findings_BC": d["f"], "direct_AC_findings": direct.get(cid, 0),
                             "weaker_link_studies": min(a["s"], d["s"]), "C_is_exposure": exid.get(cid, "")})
    rows.sort(key=lambda r: (-r["weaker_link_studies"], -(r["studies_AB"] + r["studies_BC"])))
    with open(OUT / "open_triads.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print(len(rows), "open triads;", len({(r['family'], r['C']) for r in rows}), "distinct family-outcome pairs")
    print(collections.Counter(r["family"] for r in rows).most_common())
    for r in rows[:70]:
        print(f"{r['weaker_link_studies']:3d} {r['family'][:18]:18s} -[{r['studies_AB']:3d}]- {r['B'][:28]:28s} -[{r['studies_BC']:3d}]- {r['C'][:34]:34s} direct={r['direct_AC_findings']}")
    print("uncached", used())
