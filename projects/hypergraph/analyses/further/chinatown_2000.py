"""Pre-specified secondary (Question 2): northern edge of the majority-Asian area in 2000 with 2000 tracts, from the 2000 PL 94-171 file.
Writes data/derived/further/chinatown_2000.json"""
import json, re, math
from pathlib import Path
EXT = Path.home() / "opt/nyc-concordance/chinatown/data/pl2000"; ROOT = Path(__file__).resolve().parents[2]
geo = {}
for l in open(EXT / "nygeo.upl", encoding="latin1"):
    if l[8:11] == "140" and l[29:31] == "36" and l[31:34] == "061":
        m = re.search(r"([+-]\d{8})([+-]\d{9})", l[200:])
        geo[l[18:25]] = ("36061" + l[55:61], int(m.group(1)) / 1e6, int(m.group(2)) / 1e6)
rows = {}
for l in open(EXT / "ny00001.upl", encoding="latin1"):
    f = l.rstrip("\n").split(",")
    if f[4] in geo:
        c = [int(x) for x in f[5:]]
        rows[geo[f[4]][0]] = dict(total=c[0], asian=c[5], lat=geo[f[4]][1], lon=geo[f[4]][2])
south = {g: v for g, v in rows.items() if v["lat"] < 40.7365}
maj = {g: v for g, v in south.items() if v["total"] > 0 and v["asian"] / v["total"] >= .5}
ix = max(maj, key=lambda g: maj[g]["lat"])
w = sum(v["asian"] for v in south.values())
out = dict(n_manhattan_tracts=len(rows), n_south_14th=len(south), asian_south_14th=w, majority_tracts=len(maj), majority_pop=sum(v["asian"] for v in maj.values()),
           northern_edge_lat=maj[ix]["lat"], northern_edge_tract=ix, centroid=[sum(v["lat"] * v["asian"] for v in south.values()) / w, sum(v["lon"] * v["asian"] for v in south.values()) / w],
           manhattan_asian_alone=sum(v["asian"] for v in rows.values()), source="2000 PL 94-171 New York (ny00001.upl, nygeo.upl), see data_sources.json / downloads log")
json.dump(out, open(ROOT / "data/derived/further/chinatown_2000.json", "w"), indent=1)
print(out)
