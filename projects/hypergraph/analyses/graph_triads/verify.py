"""Stage 8: for the top 20 triads, pull two findings per link and print the abstract text around the stored number."""
import json, csv, sys
from common import OUT
from abstracts import fetch, snippet
res = json.loads((OUT / "triad_signs.json").read_text())
rows = list(csv.DictReader(open(OUT / "triads_scored.csv")))[:20]

def pick(L, n=2):
    fs = [f for f in L["findings"] if f["pmid"] and f["sig"] and f["lo"] is not None]
    fs = fs or [f for f in L["findings"] if f["pmid"]]
    out, seen = [], set()
    for f in fs:
        if f["pmid"] not in seen:
            seen.add(f["pmid"]); out.append(f)
        if len(out) == n:
            break
    return out

sel, seen_ab = [], set()
for i, r in enumerate(rows):
    t = res[f"{r['family']}|{r['B']}|{r['C']}"]
    if (r["family"], r["B"]) not in seen_ab:
        seen_ab.add((r["family"], r["B"]))
        sel += [(i + 1, f"{r['family']} - {r['B']}", f) for f in pick(t["AB"])]
    sel += [(i + 1, f"{r['B']} - {r['C']}", f) for f in pick(t["BC"])]
cache = fetch([f["pmid"] for _, _, f in sel])
out = []
for rank, linkname, f in sel:
    a = cache.get(str(f["pmid"]), {})
    found, snip = snippet(a.get("abstract", ""), f["value"])
    out.append({"rank": rank, "link": linkname, "pmid": f["pmid"], "v1": f["v1"], "v2": f["v2"], "type": f["type"], "value": f["value"],
                "lo": f["lo"], "hi": f["hi"], "number_in_abstract": found, "year": a.get("year"), "title": a.get("title"), "snippet": snip})
    print(f"\n#{rank} {linkname} [{f['pmid']}, {a.get('year')}] {a.get('title','')[:110]}\n   graph: {str(f['v1'])[:80]} -> {str(f['v2'])[:70]} | {f['type']} {f['value']} ({f['lo']},{f['hi']})\n   number in abstract: {found}\n   ...{snip}")
(OUT / "verification_samples.json").write_text(json.dumps(out, indent=1))
print(len(out), "findings;", sum(o["number_in_abstract"] for o in out), "with the stored number in the abstract")
