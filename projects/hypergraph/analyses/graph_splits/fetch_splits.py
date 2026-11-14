"""Step 2: sign split of each candidate relationship, from the API's associations.

Candidates come from two listings, because the API's concept listing returns nothing
for some concepts (school, unemployment, urban population, rural population, migrant,
cold, tree) whose relationships the Dataverse CSV holds and whose associations the API
still serves by relationship id:
  (a) data/derived/graph/splits/candidates.json (API listing, >= 8 findings, >= 5 studies)
  (b) data/derived/graph_audit/sign_mixing.csv rows whose source or target label is an
      exposure label (CSV, >= 8 signed findings).
To save requests, a relationship that the CSV table shows with a minority sign share
below 0.15 is not fetched from (a), and only rows with a share >= 0.25 are fetched from (b).
Signs and significance come from tools/graph_evidence.normalise.
Output: data/derived/graph/splits/findings.json, splits.csv.
"""
import csv, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "tools")); sys.path.insert(0, str(Path(__file__).parent))
from concord import sysgraph as g
from graph_evidence import normalise
import enumerate as en
import pandas as pd

OUT = ROOT / "data/derived/graph/splits"

def assocs(rid):
    out, seen, off = [], set(), 0
    while True:
        rows = g.get(f"/v1/relationships/{g.enc(rid)}/associations", {"limit": 1000, "offset": off}).get("data", [])
        for a in rows:
            k = a.get("system_id") or json.dumps(a, sort_keys=True)
            if k not in seen:
                seen.add(k); out.append(a)
        if len(rows) < 1000: break
        off += 1000
    return out

def main():
    c = json.loads((OUT / "candidates.json").read_text())
    sm = pd.read_csv(ROOT / "data/derived/graph_audit/sign_mixing.csv")
    sm["minor"] = sm[["pos", "neg"]].min(axis=1) / sm.n_signed
    smi = sm.set_index("rid")
    lab2fam = {l.lower(): f for f, ls in en.FAMILIES.items() for l in ls}
    todo = {}
    skipped = 0
    for x in c["candidates"]:
        rid = x["relationship_id"]
        if rid in smi.index and smi.loc[rid, "minor"] < 0.15:
            skipped += 1; continue
        todo[rid] = {"family": x["family"], "exposure": x["exposure"], "source": x["source"], "target": x["target"], "listing": "api"}
    for _, r in sm[(sm.n_signed >= 8) & (sm.minor >= 0.25)].iterrows():
        for side in ("src", "tgt"):
            l = str(r[side]).lower()
            if l in lab2fam and r.rid not in todo:
                todo[r.rid] = {"family": lab2fam[l], "exposure": r[side], "source": r.src, "target": r.tgt, "listing": "csv"}
    print(len(todo), "to fetch; skipped as one-sided in CSV:", skipped)
    findings, rows = {}, []
    for rid, meta in todo.items():
        fs = []
        for a in assocs(rid):
            n = normalise(a)
            fs.append({"id": a.get("system_id"), "v1": a.get("variable_1_name"), "v2": a.get("variable_2_name"),
                       "stat": a.get("system_statistic_type"), "value": a.get("statistic_value"),
                       "lo": a.get("ci_lower"), "hi": a.get("ci_upper"), "p": a.get("p_value"),
                       "direction": n["direction"], "significant": bool(n["significant"]), "flags": n["flags"],
                       "study_id": a.get("study_id"), "pmid": a.get("pubmed_id")})
        signed = [f for f in fs if f["direction"] in ("+", "-")]
        pos = [f for f in signed if f["direction"] == "+"]; neg = [f for f in signed if f["direction"] == "-"]
        st = {f["study_id"] for f in signed}
        row = {**meta, "relationship_id": rid, "n_findings": len(fs), "n_signed": len(signed), "n_studies": len(st),
               "pos": len(pos), "neg": len(neg), "sig_pos": sum(f["significant"] for f in pos), "sig_neg": sum(f["significant"] for f in neg),
               "studies_pos": len({f["study_id"] for f in pos}), "studies_neg": len({f["study_id"] for f in neg}),
               "studies_sig_pos": len({f["study_id"] for f in pos if f["significant"]}),
               "studies_sig_neg": len({f["study_id"] for f in neg if f["significant"]}),
               "minority_share": round(min(len(pos), len(neg)) / len(signed), 3) if signed else None}
        rows.append(row); findings[rid] = fs
    (OUT / "findings.json").write_text(json.dumps(findings))
    rows.sort(key=lambda r: -(r["minority_share"] or 0))
    with open(OUT / "splits.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    ok = [r for r in rows if r["n_signed"] >= 8 and r["n_studies"] >= 5 and (r["minority_share"] or 0) >= 0.25]
    print("fetched", len(rows), "; meeting 8 signed / 5 studies:", sum(r["n_signed"] >= 8 and r["n_studies"] >= 5 for r in rows), "; split:", len(ok))

if __name__ == "__main__":
    main()
