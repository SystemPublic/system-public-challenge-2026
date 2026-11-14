"""Cohen's kappa between pass 1 and pass 2 per field; lists disagreements.
Run: python3 -I scripts/guidance_kappa.py  -> data/processed/guidance_kappa.json (+ disagreements csv in data/raw/guidance)"""
import csv, json, os, sys
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from guidance_common import PROC, ROOT, SOURCES, load_lines, norm

FIELDS = ["mentioned", "mention_level", "action_type", "specificity", "evidence_cited"]

def kappa(a, b):
    n = len(a); po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0, po

def load(p):
    return {(r["source_id"], r["drug_id"]): r for r in csv.DictReader(open(p, encoding="utf-8"))}

def main():
    p1 = load(os.path.join(PROC, "guidance_coding_pass1.csv"))
    p2 = load(os.path.join(PROC, "guidance_coding_pass2.csv"))
    assert set(p1) == set(p2), "cell sets differ"
    full = {sid: norm(" ".join(" ".join(load_lines(fn)) for fn, _ in f)) for sid, f in SOURCES.items()}
    # pass-1 quotes use " / " to mark source line breaks; compare with slashes removed on both sides
    def ok(q, sid):
        return norm(q.replace("/", " ")) in norm(full[sid].replace("/", " "))
    p1_bad = [k for k, r in p1.items() if r["quote"] and not ok(r["quote"], k[0])]
    res = {"method": "Cohen's kappa (unweighted), pass1 keyword-then-read vs pass2 read-whole-section", "n_pass1_quotes_not_verbatim": len(p1_bad)}
    dis = []
    for scope in ["core", "all"]:
        keys = sorted(k for k in p1 if scope == "all" or p2[k]["drug_group"] == "core")
        res[scope] = {"n_cells": len(keys)}
        for f in FIELDS:
            a = [p1[k][f].strip() or "none" for k in keys]; b = [p2[k][f].strip() or "none" for k in keys]
            kp, po = kappa(a, b)
            res[scope][f] = {"kappa": round(kp, 3), "percent_agreement": round(100 * po, 1), "n_disagree": sum(x != y for x, y in zip(a, b))}
    for k in sorted(p1):
        diffs = [f for f in FIELDS if (p1[k][f].strip() or "none") != (p2[k][f].strip() or "none")]
        if diffs:
            dis.append(dict(source_id=k[0], drug_id=k[1], drug_group=p2[k]["drug_group"], fields=";".join(diffs),
                            **{f"p1_{f}": p1[k][f] for f in FIELDS}, **{f"p2_{f}": p2[k][f] for f in FIELDS},
                            p1_quote=p1[k]["quote"], p2_quote=p2[k]["quote"]))
    json.dump(res, open(os.path.join(PROC, "guidance_kappa.json"), "w"), indent=2)
    out = os.path.join(ROOT, "data", "raw", "guidance", "pass_disagreements.csv")
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(dis[0].keys())); w.writeheader(); w.writerows(dis)
    print(json.dumps(res, indent=1)); print(len(dis), "disagreeing cells ->", out)
    if p1_bad: print("pass1 non-verbatim:", p1_bad)

if __name__ == "__main__":
    main()
