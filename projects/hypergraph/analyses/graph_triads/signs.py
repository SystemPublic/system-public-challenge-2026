"""Stage 6: sign consistency of both links for the leading open triads, and a score.

score = (studies on the weaker link) x (the lower of the two links' sign consistencies), where a link's
sign consistency is the share of its signed findings that carry the majority sign. A finding's sign is the
sign between the variables as named, so it is a property of the extracted rows, not yet of the concepts.
"""
import json, csv, hashlib, sys, collections
from common import g, OUT, used
from triads import FAMILIES, load
from graph_evidence import normalise

TOP = 45
FORCED = [("heat", "asthma", "school attendance"), ("air pollution", "mental depression", "violence"),
          ("indoor air and pests", "asthma", "school attendance"), ("flood", "post-traumatic stress disorder", "intimate partner violence"),
          ("noise", "sleep", "school attendance"), ("green space", "physical activity", "mental depression"),
          ("heat", "preterm birth", "attention deficit hyperactivity disorder"), ("shift work and light at night", "metabolic syndrome", "stroke"),
          ("noise", "arterial hypertension", "low birth weight infant"), ("walking", "physical activity", "sleep quality"),
          ("crime", "mental depression", "dementia"), ("fast food", "obesity", "sleep duration"), ("housing and homelessness", "frailty syndrome", "falling")]
BUDGET = 1000

def assocs(rid):
    q = "limit=100&offset=0"
    path = f"/v1/relationships/{g.enc(rid)}/associations"
    f = g.CACHE / (hashlib.sha256(f"{path}?{q}".encode()).hexdigest()[:24] + ".json")
    return g.page_all(path, limit=100 if f.exists() else 1000, max_items=5000)

def link(rids):
    rows, seen = [], set()
    for rid in rids:
        if used() >= BUDGET:
            raise SystemExit("budget reached")
        for a in assocs(rid):
            if a.get("system_id") in seen:
                continue
            seen.add(a.get("system_id"))
            n = normalise(a)
            rows.append({"id": a.get("system_id"), "rid": rid, "v1": a.get("variable_1_name"), "v2": a.get("variable_2_name"),
                         "type": a.get("system_statistic_type"), "value": a.get("statistic_value"), "lo": a.get("ci_lower"), "hi": a.get("ci_upper"),
                         "p": a.get("p_value"), "dir": n["direction"], "sig": n["significant"], "flags": n["flags"],
                         "pmid": a.get("pubmed_id"), "study": a.get("study_id")})
    plus = sum(r["dir"] == "+" for r in rows); minus = sum(r["dir"] == "-" for r in rows)
    sp = sum(r["dir"] == "+" and bool(r["sig"]) for r in rows); sm = sum(r["dir"] == "-" and bool(r["sig"]) for r in rows)
    cons = max(plus, minus) / (plus + minus) if plus + minus else None
    return {"n_returned": len(rows), "n_studies_returned": len({r["study"] for r in rows}), "plus": plus, "minus": minus, "sig_plus": sp, "sig_minus": sm,
            "consistency": cons, "majority": "+" if plus >= minus else "-", "findings": rows}

if __name__ == "__main__":
    ex, inter = load()
    lab2id = {v["label"]: k for k, v in inter.items()}
    by = list(csv.DictReader(open(OUT / "open_triads_by_outcome.csv")))
    chosen = [(r["family"], r["best_B"], r["C"]) for r in by[:TOP]]
    chosen += [t for t in FORCED if t not in chosen]
    f = OUT / "triad_signs.json"
    res = json.loads(f.read_text()) if f.exists() else {}
    for fam, B, C in chosen:
        key = f"{fam}|{B}|{C}"
        if key in res:
            continue
        bid = lab2id.get(B)
        if not bid:
            print("no B", B); continue
        ab_rids, s_ab = [], 0
        for m in FAMILIES[fam]:
            d = ex.get(m, {}).get("neighbours", {}).get(bid)
            if d:
                ab_rids += d["rids"]; s_ab += d["s"]
        cd = [d for d in inter[bid]["neighbours"].values() if d["label"] == C]
        if not cd or not ab_rids:
            print("no link", key); continue
        try:
            L1, L2 = link(ab_rids), link(cd[0]["rids"])
        except SystemExit as e:
            print(e); break
        res[key] = {"family": fam, "B": B, "C": C, "studies_AB": s_ab, "studies_BC": cd[0]["s"], "AB": L1, "BC": L2}
        c1, c2 = L1["consistency"], L2["consistency"]
        print(f"{fam[:16]:16s} {B[:24]:24s} {C[:28]:28s} AB +{L1['plus']}/-{L1['minus']} (ret {L1['n_returned']}) BC +{L2['plus']}/-{L2['minus']} (ret {L2['n_returned']}) used={used()}")
        f.write_text(json.dumps(res))
    print("uncached", used())
