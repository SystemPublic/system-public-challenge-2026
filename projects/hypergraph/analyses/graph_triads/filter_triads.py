"""Stage 5: drop outcomes C that are treatments, tests, chemicals or genes (by Wikidata description),
and collapse to one row per exposure family and outcome, keeping every intermediate that reaches it."""
import json, csv, re, collections
from common import OUT
DROP = re.compile(r"\b(chemical|compound|protein|gene|medication|drug|drugs|pharmaceutical|surgical|surgery|procedure|treatment|treat|therapy|technique|"
                  r"test|measurement|method|species|genus|hormone|element|vaccine|removal|device|enzyme|antibiotic|operation|agent|agents|"
                  r"medicine|imaging|scale|questionnaire|examination|screening|specialty|profession|occupation|taxon|bacteri\w*|virus|"
                  r"index|ratio|unit|stent|implant|prosthesis|replacement|transplantation|anesthesia|intervention|molecule|acid|vitamin|mineral|steroid|inhibitor|class of)\b", re.I)
DROP_LABEL = re.compile(r"(therapy|surgery|ectomy|plasty|ostomy|test$|scale$|score$|index$|level$|vaccin|inhibitor|blocker|agonist|statin|care$|"
                        r"length of stay|hospital|intensive care|insurance|^maternal age|family relation|rural area|employment|marital|religio|adolescent father|"
                        r"pregnancy$|parity|gestational age|menopause|puberty|childbirth|^infant$|^child$|adolescen|^elderly|pet$)", re.I)

def keep(label, desc):
    return not DROP.search(desc or "") and not DROP_LABEL.search(label or "")

if __name__ == "__main__":
    desc = json.loads((OUT / "concept_descriptions.json").read_text())
    rows = list(csv.DictReader(open(OUT / "open_triads.csv")))
    kept = [r for r in rows if keep(r["C"], desc.get(r["C_id"], ["", ""])[1]) and keep(r["B"], desc.get(r["B_id"], ["", ""])[1])]
    print(len(rows), "->", len(kept), "after dropping treatments, tests, chemicals, genes")
    grp = collections.defaultdict(list)
    for r in kept:
        grp[(r["family"], r["C_id"])].append(r)
    out = []
    for (fam, cid), rs in grp.items():
        rs.sort(key=lambda r: -int(r["weaker_link_studies"]))
        b = rs[0]
        out.append({"family": fam, "C": b["C"], "C_id": cid, "C_description": desc.get(cid, ["", ""])[1][:80], "direct_AC_findings": b["direct_AC_findings"],
                    "best_B": b["B"], "best_B_id": b["B_id"], "studies_AB": b["studies_AB"], "studies_BC": b["studies_BC"],
                    "weaker_link_studies": int(b["weaker_link_studies"]), "n_intermediates": len(rs),
                    "sum_weaker": sum(int(r["weaker_link_studies"]) for r in rs),
                    "intermediates": "; ".join(f"{r['B']}({r['studies_AB']}/{r['studies_BC']})" for r in rs[:8])})
    out.sort(key=lambda r: (-r["weaker_link_studies"], -r["n_intermediates"]))
    with open(OUT / "open_triads_by_outcome.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
    print(len(out), "family-outcome pairs")
    fams = collections.defaultdict(list)
    for r in out:
        fams[r["family"]].append(r)
    for fam, rs in fams.items():
        print(f"\n== {fam} ({len(rs)})")
        for r in rs[:22]:
            print(f"  {r['weaker_link_studies']:3d} nB={r['n_intermediates']:2d} d={r['direct_AC_findings']} {r['C'][:36]:36s} via {r['intermediates'][:110]}")
