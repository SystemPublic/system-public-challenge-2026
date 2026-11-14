"""Step 2 (graph side only): the literature's sign for every indicator pair that has findings.

For each relationship between mapped concepts (both orders) the associations are read from the API and
normalised with tools/graph_evidence.normalise. A finding is "signed" when it has a direction and its
statistic is not a group difference (mean difference, risk difference, t-test: the sign depends on which
group was subtracted). The sign is then expressed between the two INDICATORS: multiplied by both
polarities, and flipped once for each variable whose name carries a negation word that is not part of its
concept's label. Rules fixed before any city correlation was computed.
"""
import csv
import json
import re

import common as C
from graph_evidence import GROUP_ORDER, normalise
from indicators import BY_KEY, KEYS

g = C.g
NEG = re.compile(r"\b(lack of|lacking|no|not|non|without|absence of|absent|low|lower|lowest|less|least|never|poor|poorer|unemployed|uninsured|unhealthy|inadequate|insufficient|inactive|inactivity|reduced|decreas\w+|former|quit\w*|cessation)\b", re.I)
NEG_EXEMPT = {"bIwjlkmcHV": {"poor", "poorer", "low", "lower", "lowest"}, "ADplkYjn2k": {"poor", "poorer", "low", "lower", "lowest"},
              "hupL32mZNu": {"unemployed"}, "3x-TeF7nX4": {"unemployed"}}


def negated(name, cid, label):
    toks = {m.group(1).lower() for m in NEG.finditer(name or "") if m.group(1) != "NO"}
    toks = {t for t in toks if t not in (label or "").lower().split() and t not in NEG_EXEMPT.get(cid, set())}
    if cid in ("PtQBvGm5CM", "rYCo7LTyzN", "VM_BejazFq"):
        toks -= {"low"}
    return bool(toks)


def main():
    P = json.loads((C.OUT / "pairs_relationships.json").read_text())["pairs"]
    c2k, lab = {}, {}
    for k in KEYS:
        for cid, l in BY_KEY[k]["concepts"]:
            c2k[cid], lab[cid] = k, l
    rows, summ = [], []
    for p in P:
        a, b = p["a"], p["b"]
        s = {"a": a, "b": b, "mappable": p["mappable"], "n_relationships": len(p["relationships"]), "n_findings": 0, "n_signed": 0,
             "pos": 0, "neg": 0, "n_studies": 0, "n_studies_signed": 0, "sig_pos": 0, "sig_neg": 0}
        st_all, st_signed, seen, study_votes = set(), set(), set(), {}
        for rid in p["relationships"]:
            for x in g.page_all(f"/v1/relationships/{g.enc(rid)}/associations", limit=1000, max_items=4000):
                if x["system_id"] in seen:
                    continue
                seen.add(x["system_id"])
                n = normalise(x)
                c1, c2 = x.get("variable_1_concept_id"), x.get("variable_2_concept_id")
                k1, k2 = c2k.get(c1), c2k.get(c2)
                if not k1 or not k2 or {k1, k2} != {a, b}:
                    continue
                s["n_findings"] += 1
                st_all.add(x.get("study_id"))
                signed = n["direction"] is not None and x.get("system_statistic_type") not in GROUP_ORDER and not [f for f in n["flags"] if f != "sign_depends_on_group_order"]
                sgn = None
                if signed:
                    sgn = 1 if n["direction"] == "+" else -1
                    sgn *= BY_KEY[k1]["polarity"] * BY_KEY[k2]["polarity"]
                    if negated(x.get("variable_1_name"), c1, lab[c1]):
                        sgn = -sgn
                    if negated(x.get("variable_2_name"), c2, lab[c2]):
                        sgn = -sgn
                    s["n_signed"] += 1
                    s["pos" if sgn > 0 else "neg"] += 1
                    if n["significant"]:
                        s["sig_pos" if sgn > 0 else "sig_neg"] += 1
                    st_signed.add(x.get("study_id"))
                    study_votes[x.get("study_id")] = study_votes.get(x.get("study_id"), 0) + sgn
                rows.append({"a": a, "b": b, "relationship_id": rid, "association_id": x["system_id"], "pubmed_id": x.get("pubmed_id"),
                             "study_id": x.get("study_id"), "variable_1": x.get("variable_1_name"), "variable_2": x.get("variable_2_name"),
                             "concept_1": lab.get(c1), "concept_2": lab.get(c2), "statistic": x.get("system_statistic_type"),
                             "value": x.get("statistic_value"), "ci_lower": x.get("ci_lower"), "ci_upper": x.get("ci_upper"),
                             "p_value": x.get("p_value"), "raw_direction": n["direction"], "significant": n["significant"],
                             "indicator_sign": sgn, "flags": ";".join(n["flags"])})
        s["n_studies"], s["n_studies_signed"] = len(st_all), len(st_signed)
        s["studies_pos"] = sum(v > 0 for v in study_votes.values())
        s["studies_neg"] = sum(v < 0 for v in study_votes.values())
        if s["n_signed"]:
            s["share_pos"] = round(s["pos"] / s["n_signed"], 4)
            s["lit_sign"] = 1 if s["pos"] > s["neg"] else -1 if s["neg"] > s["pos"] else 0
            s["consistency"] = round(max(s["pos"], s["neg"]) / s["n_signed"], 4)
        else:
            s["share_pos"], s["lit_sign"], s["consistency"] = None, None, None
        s["qualifies"] = bool(s["n_studies_signed"] >= 3 and (s["consistency"] or 0) >= 0.8)
        summ.append(s)
    with open(C.OUT / "graph_findings.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    with open(C.OUT / "literature_signs.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(summ[0].keys()))
        w.writeheader()
        w.writerows(summ)
    q = [s for s in summ if s["qualifies"]]
    print("pairs", len(summ), "with findings", sum(s["n_findings"] > 0 for s in summ), "with signed", sum(s["n_signed"] > 0 for s in summ),
          "qualifying", len(q), "of which positive", sum(s["lit_sign"] > 0 for s in q), "findings", len(rows))
    print(">=3 signed studies", sum(s["n_studies_signed"] >= 3 for s in summ))
    print("uncached so far", C.used())


if __name__ == "__main__":
    main()
