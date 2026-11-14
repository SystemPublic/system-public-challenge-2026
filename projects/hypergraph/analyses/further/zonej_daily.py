"""Aggregate PAL 5-minute files to zone-day energy, peak and coverage for N.Y.C. and LONGIL."""
import zipfile, io, pandas as pd
from pathlib import Path
SRC = Path.home()/"opt/nyc-concordance/nyiso/pal"
ROOT = Path(__file__).resolve().parents[2]
rows = []
for z in sorted(SRC.glob("*.zip")):
    with zipfile.ZipFile(z) as zf:
        for n in zf.namelist():
            if not n.endswith(".csv"): continue
            d = pd.read_csv(zf.open(n), usecols=["Time Stamp","Name","Load"])
            d = d[d.Name.isin(["N.Y.C.","LONGIL"])]
            d["ts"] = pd.to_datetime(d["Time Stamp"], format="%m/%d/%Y %H:%M:%S")
            rows.append(d[["ts","Name","Load"]])
a = pd.concat(rows)
a = a.groupby(["Name","ts"], as_index=False).Load.mean()   # duplicate stamps (fall-back hour) averaged
a["date"] = a.ts.dt.normalize()
g = a.groupby(["Name","date"]).Load.agg(n="count", mean="mean", peak="max", mn="min").reset_index()
g["energy_mwh"] = g["mean"]*24   # mean MW x 24 h (robust to missing intervals; DST days nominal 24h)
g = g.rename(columns={"Name":"zone"})
out = ROOT/"data/derived/further/zonej_daily.csv"; g.to_csv(out, index=False)
print(g.groupby("zone").n.describe()); print(len(g))
