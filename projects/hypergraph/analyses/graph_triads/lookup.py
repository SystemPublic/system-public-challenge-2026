"""Helper: for an exposure family and an outcome label, the direct findings and every intermediate (open or not)."""
import json, collections, sys
from common import OUT
from triads import FAMILIES, load

def table(ex, inter, c_labels, min_ab=3, min_bc=3):
    out = []
    for fam, members in FAMILIES.items():
        mem = [m for m in members if m in ex]
        direct = collections.defaultdict(lambda: [0, 0]); ab = {}
        for m in mem:
            for oid, d in ex[m]["neighbours"].items():
                direct[d["label"]][0] += d["f"]; direct[d["label"]][1] += d["s"]
                a = ab.setdefault(oid, {"label": d["label"], "s": 0}); a["s"] += d["s"]
        for c in c_labels:
            via = []
            for bid, a in ab.items():
                if a["s"] >= min_ab and bid in inter:
                    for cid, d in inter[bid]["neighbours"].items():
                        if d["label"] == c and d["s"] >= min_bc:
                            via.append((min(a["s"], d["s"]), a["label"], a["s"], d["s"]))
            via.sort(reverse=True)
            out.append((fam, c, direct[c][0], direct[c][1], via))
    return out

if __name__ == "__main__":
    ex, inter = load()
    for fam, c, f, s, via in table(ex, inter, sys.argv[1:]):
        if via or f:
            print(f"{fam[:22]:22s} -> {c[:26]:26s} direct f={f} s={s} | " + "; ".join(f"{b}({x}/{y})" for _, b, x, y in via[:7]))
