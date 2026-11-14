"""Stage 7: score the triads with fetched signs and write the ranked table."""
import json, csv
from common import OUT
res = json.loads((OUT / "triad_signs.json").read_text())
by = {(r["family"], r["C"]): r for r in csv.DictReader(open(OUT / "open_triads_by_outcome.csv"))}
rows = []
for key, t in res.items():
    c1, c2 = t["AB"]["consistency"], t["BC"]["consistency"]
    weaker = min(t["studies_AB"], t["studies_BC"])
    cons = min(c1 or 0, c2 or 0)
    b = by.get((t["family"], t["C"]), {})
    rows.append({"family": t["family"], "B": t["B"], "C": t["C"], "studies_AB": t["studies_AB"], "studies_BC": t["studies_BC"],
                 "direct_AC_findings": b.get("direct_AC_findings", ""), "n_intermediates": b.get("n_intermediates", ""),
                 "AB_plus": t["AB"]["plus"], "AB_minus": t["AB"]["minus"], "AB_returned": t["AB"]["n_returned"],
                 "BC_plus": t["BC"]["plus"], "BC_minus": t["BC"]["minus"], "BC_returned": t["BC"]["n_returned"],
                 "AB_consistency": round(c1, 3) if c1 else "", "BC_consistency": round(c2, 3) if c2 else "",
                 "weaker_link_studies": weaker, "score": round(weaker * cons, 1),
                 "composed_sign": ("+" if t["AB"]["majority"] == t["BC"]["majority"] else "-") if c1 and c2 else ""})
rows.sort(key=lambda r: -r["score"])
with open(OUT / "triads_scored.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
for i, r in enumerate(rows):
    print(f"{i+1:2d} {r['score']:5.1f} {r['family'][:16]:16s} {r['B'][:22]:22s} {r['C'][:30]:30s} AB {r['studies_AB']}st {r['AB_consistency']} BC {r['studies_BC']}st {r['BC_consistency']} d={r['direct_AC_findings']}")
