"""Build tract tables for further-chinatown-shift from official Census bulk files kept in ~/opt/nyc-concordance/chinatown/data
(the Census API now needs a key, so the keyless bulk files are used):
  2010 PL 94-171 (ny2010.pl.zip), 2020 PL 94-171 (ny2020.pl.zip), ACS 2022 5-year table-based summary file B03002, B02015.
Output: data/derived/further/tracts_2010.csv, tracts_2020.csv, acs2022_tracts.csv, data_sources.json"""
import csv, json
from pathlib import Path
EXT = Path.home() / "opt/nyc-concordance/chinatown/data"
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/derived/further"
CTY = {"36005", "36047", "36061", "36081", "36085"}

def pl(year):
    d = EXT / f"pl{year}"
    geo = {}
    for l in open(d / f"nygeo{year}.pl", encoding="latin1"):
        if year == 2010:
            if l[8:11] == "140": geo[l[18:25]] = l[27:29] + l[29:32] + l[54:60]
        else:
            f = l.split("|")
            if f[2] == "140": geo[f[7]] = f[9][-11:]
    rows = {}
    f1 = d / f"ny00001{year}.pl"
    for l in open(f1, encoding="latin1"):
        f = l.rstrip("\n").split("|" if year == 2020 else ",")
        lr = f[4] if year == 2020 else f[4]
        if lr in geo and geo[lr][:5] in CTY:
            c = [int(x) for x in f[5:]]
            p1, p2 = c[:71], c[71:71+73]
            rows[geo[lr]] = dict(geoid=geo[lr], total=p1[0], asian_alone=p1[5], nhpi_alone=p1[6],
                                 hisp=p2[1], nh_white=p2[4], nh_black=p2[5], nh_asian=p2[7], nh_nhpi=p2[8])
    return rows

def acs(table, cols):
    out = {}
    with open(EXT / f"acsdt5y2022-{table}.dat") as f:
        rd = csv.reader(f, delimiter="|"); h = next(rd); ix = {k: i for i, k in enumerate(h)}
        for r in rd:
            g = r[0]
            if g.startswith("1400000US") and g[9:14] in CTY:
                out[g[9:]] = {c: (float(r[ix[c]]) if r[ix[c]] not in ("", ".") else None) for c in cols}
    return out

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for y in (2010, 2020):
        r = pl(y)
        with open(OUT / f"tracts_{y}.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(next(iter(r.values())).keys())); w.writeheader(); w.writerows(r.values())
        print(y, len(r))
    cols = ["B03002_E001", "B03002_M001", "B03002_E003", "B03002_M003", "B03002_E004", "B03002_M004", "B03002_E006", "B03002_M006",
            "B03002_E007", "B03002_M007", "B03002_E012", "B03002_M012"]
    a = acs("b03002", cols); c = acs("b02015", ["B02015_E001", "B02015_M001", "B02015_E002", "B02015_M002"])
    with open(OUT / "acs2022_tracts.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["geoid"] + cols + ["B02015_E002", "B02015_M002"])
        for g, v in a.items(): w.writerow([g] + [v[k] for k in cols] + [c.get(g, {}).get("B02015_E002"), c.get(g, {}).get("B02015_M002")])
    print("acs", len(a))
    src = [dict(l.split(" | ")[i] for i in range(0)) for l in []]
    json.dump({"downloads_log": (EXT / "downloads.log").read_text().splitlines(),
               "note": "Census API requires a key since late 2026 (HTML 'Missing Key' returned); keyless bulk files used instead. Files kept outside Dropbox."},
              open(OUT / "data_sources.json", "w"), indent=1)
