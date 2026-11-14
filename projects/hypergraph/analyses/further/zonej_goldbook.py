"""Extract Zone J / K baseline annual energy (GWh) and summer coincident peak (MW) from Gold Book editions 2021-2026 (Tables I-2, I-3a)."""
import re, subprocess, json
import pandas as pd
from pathlib import Path
GB = Path.home()/"opt/nyc-concordance/nyiso/gb"
ROOT = Path(__file__).resolve().parents[2]
rows = []
def page_text(y, p): return subprocess.run(["pdftotext","-layout","-f",str(p),"-l",str(p),str(GB/f"{y}.pdf"),"-"],capture_output=True,text=True).stdout
for y in range(2021, 2027):
    for tab, key in (("I-2","energy_gwh"),("I-3a","summer_peak_mw")):
        found = None
        for p in range(20, 36):
            t = page_text(y, p)
            if f"Table {tab}:" in t.split("\n")[0] + t[:300] and "......" not in t and re.search(r"Year\s+A\s+B", t):
                found = (p, t); break
        if not found: print("NOT FOUND", y, tab); continue
        p, t = found
        hdr = [l for l in t.split("\n") if re.match(r"\s*Year\s+A\s+B", l)][0].split()[1:]
        n = 0
        for l in t.split("\n"):
            m = re.match(r"\s*(20\d\d)\s+([\d,\s]+)$", l)
            if m:
                vals = [int(v.replace(",","")) for v in l.split()[1:]]
                if len(vals) == len(hdr):
                    d = dict(zip(hdr, vals)); rows.append(dict(edition=y, table=tab, page=p, year=int(m.group(1)), J=d["J"], K=d["K"])); n += 1
        print(y, tab, "page", p, "rows", n, "hdr", hdr[-3:])
df = pd.DataFrame(rows); df["measure"] = df.table.map({"I-2":"energy_gwh","I-3a":"summer_peak_mw"})
df.to_csv(ROOT/"data/derived/further/zonej_goldbook.csv", index=False)
print(df.groupby(["edition","measure"]).year.agg(["min","max","count"]))
