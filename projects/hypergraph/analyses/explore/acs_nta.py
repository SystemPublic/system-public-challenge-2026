"""ACS measures per NTA (and for Hudson County, New Jersey) for the exploration note.

2018-2022: median household income (B19013), share of adults 25+ with a bachelor's degree (B15003),
share of residents aged 25 to 34 and 65 and over (B01001), share of employed residents in arts, design,
entertainment, sports and media occupations (C24010, cells 15 and 51).
2008-2012: the same occupation share from sequence file 79 (cells 15 and 51 of C24010, which starts at
position 43), moved to 2020 tracts with the Census land-area relationship file.
Medians are population-weighted means of tract medians. Output data/derived/explore/acs_nta.csv, arts_occ.json.
"""
from __future__ import annotations

import json
import zipfile

import numpy as np
import pandas as pd
import requests

from common import OUT, RAW, ROOT, nta_pop, tract_table

COUNTIES = ("36005", "36047", "36061", "36081", "36085", "34017")
SEQ = ("https://www2.census.gov/acs2012_5yr/summaryfile/2008-2012_ACSSF_By_State_By_Sequence_Table_Subset/"
       "{state}/Tracts_Block_Groups_Only/{f}")
UA = {"User-Agent": "Mozilla/5.0 (research script)"}


def acs2022(table: str, cols: list[int]) -> pd.DataFrame:
    f = RAW / "acs" / f"acsdt5y2022-{table}.dat"
    keep = []
    with open(f) as fh:
        header = fh.readline().rstrip("\n").split("|")
        for line in fh:
            if line.startswith("1400000US") and line[9:14] in COUNTIES:
                keep.append(line.rstrip("\n").split("|"))
    d = pd.DataFrame(keep, columns=header)
    out = pd.DataFrame({"GEOID": d.GEO_ID.str[-11:]})
    for c in cols:
        out[f"e{c}"] = pd.to_numeric(d[f"{table.upper()}_E{c:03d}"], errors="coerce")
    return out


def arts2012(state: str, ab: str) -> pd.DataFrame:
    geo = pd.read_csv(RAW / "acs" / f"g20125{ab}.csv", header=None, dtype=str, encoding="latin-1")
    geo = geo[geo[2] == "140"][[4, 48]].rename(columns={4: "LOGRECNO", 48: "GEO"})
    geo["GEOID"] = geo.GEO.str[-11:]
    name = f"20125{ab}0079000.zip"
    f = RAW / "acs" / name
    if not f.exists():
        r = requests.get(SEQ.format(state=state, f=name), headers=UA, timeout=600)
        r.raise_for_status()
        f.write_bytes(r.content)
    with zipfile.ZipFile(f) as zf:
        e = [n for n in zf.namelist() if n.startswith("e")][0]
        d = pd.read_csv(zf.open(e), header=None, dtype=str)
    d = d.rename(columns={5: "LOGRECNO"})
    sub = d[["LOGRECNO", 42, 56, 92]].copy()
    sub.columns = ["LOGRECNO", "emp12", "am", "af"]
    for c in ("emp12", "am", "af"):
        sub[c] = pd.to_numeric(sub[c], errors="coerce")
    sub["arts12"] = sub.am + sub.af
    return geo.merge(sub, on="LOGRECNO")[["GEOID", "emp12", "arts12"]]


def main():
    inc = acs2022("b19013", [1]).rename(columns={"e1": "income"})
    inc.loc[inc.income < 0, "income"] = np.nan
    edu = acs2022("b15003", [1, 22, 23, 24, 25])
    edu["ba"] = edu[["e22", "e23", "e24", "e25"]].sum(axis=1)
    edu = edu.rename(columns={"e1": "pop25"})[["GEOID", "pop25", "ba"]]
    age = acs2022("b01001", [1, 11, 12, 35, 36] + list(range(20, 26)) + list(range(44, 50)))
    age["a2534"] = age[["e11", "e12", "e35", "e36"]].sum(axis=1)
    age["a65"] = age[[f"e{i}" for i in list(range(20, 26)) + list(range(44, 50))]].sum(axis=1)
    age = age.rename(columns={"e1": "agepop"})[["GEOID", "agepop", "a2534", "a65"]]
    occ = acs2022("c24010", [1, 15, 51])
    occ["arts22"] = occ.e15 + occ.e51
    occ = occ.rename(columns={"e1": "emp22"})[["GEOID", "emp22", "arts22"]]
    t22 = inc.merge(edu, on="GEOID").merge(age, on="GEOID").merge(occ, on="GEOID")

    # 2012 arts occupations on 2010 tracts -> 2020 tracts (New York) by land-area weights
    a12 = pd.concat([arts2012("NewYork", "ny"), arts2012("NewJersey", "nj")])
    a12 = a12[a12.GEOID.str[:5].isin(COUNTIES)]
    rel = pd.read_csv(ROOT / "data" / "raw" / "acs" / "tab20_tract20_tract10_st36.txt", sep="|", dtype=str, encoding="utf-8-sig")
    for c in ("AREALAND_PART", "AREALAND_TRACT_10"):
        rel[c] = pd.to_numeric(rel[c])
    rel["w"] = rel.AREALAND_PART / rel.AREALAND_TRACT_10.replace(0, np.nan)
    m = rel.merge(a12, left_on="GEOID_TRACT_10", right_on="GEOID")
    m["emp12"] *= m.w
    m["arts12"] *= m.w
    x12 = m.groupby("GEOID_TRACT_20")[["emp12", "arts12"]].sum().reset_index().rename(columns={"GEOID_TRACT_20": "GEOID"})

    tt = tract_table()[["GEOID", "nta2020", "pop"]].rename(columns={"nta2020": "nta"})
    d = tt.merge(t22, on="GEOID", how="left").merge(x12, on="GEOID", how="left")
    d["inc_w"] = d.income * d["pop"]
    d["inc_n"] = d["pop"].where(d.income.notna())
    g = d.groupby("nta").agg(pop25=("pop25", "sum"), ba=("ba", "sum"), agepop=("agepop", "sum"), a2534=("a2534", "sum"),
                             a65=("a65", "sum"), emp22=("emp22", "sum"), arts22=("arts22", "sum"), emp12=("emp12", "sum"),
                             arts12=("arts12", "sum"), inc_w=("inc_w", "sum"), inc_n=("inc_n", "sum"))
    out = pd.DataFrame({"income": g.inc_w / g.inc_n.replace(0, np.nan), "ba_share": g.ba / g.pop25.replace(0, np.nan),
                        "share_25_34": g.a2534 / g.agepop.replace(0, np.nan), "share_65": g.a65 / g.agepop.replace(0, np.nan),
                        "arts_workers22": g.arts22, "employed22": g.emp22, "arts_share22": g.arts22 / g.emp22.replace(0, np.nan),
                        "arts_workers12": g.arts12, "employed12": g.emp12, "arts_share12": g.arts12 / g.emp12.replace(0, np.nan)})
    out = nta_pop().set_index("nta").join(out)
    out.to_csv(OUT / "acs_nta.csv")

    # city, borough and Hudson County totals of the arts occupation group
    tot = {}
    for lab, pre in (("New York City", ("36005", "36047", "36061", "36081", "36085")), ("Manhattan", ("36061",)),
                     ("Brooklyn", ("36047",)), ("Queens", ("36081",)), ("Bronx", ("36005",)), ("Staten Island", ("36085",)),
                     ("Hudson County NJ", ("34017",))):
        a = occ[occ.GEOID.str[:5].isin(pre)]
        b = a12[a12.GEOID.str[:5].isin(pre)]
        tot[lab] = {"arts_2008_12": float(b.arts12.sum()), "employed_2008_12": float(b.emp12.sum()),
                    "arts_2018_22": float(a.arts22.sum()), "employed_2018_22": float(a.emp22.sum())}
        tot[lab]["share_2008_12"] = tot[lab]["arts_2008_12"] / tot[lab]["employed_2008_12"]
        tot[lab]["share_2018_22"] = tot[lab]["arts_2018_22"] / tot[lab]["employed_2018_22"]
    # Jersey City tracts are not separable from the county without a place file; Hudson County is reported whole
    (OUT / "arts_occ.json").write_text(json.dumps(tot, indent=1))
    print(json.dumps(tot, indent=1))
    names = tract_table().drop_duplicates("nta2020").set_index("nta2020").ntaname
    o = out[out["pop"] > 5000].copy()
    o["name"] = names.reindex(o.index)
    o["d_arts"] = o.arts_workers22 - o.arts_workers12
    pd.set_option("display.width", 200)
    print(o.sort_values("arts_share22", ascending=False).head(15)[["name", "arts_workers12", "arts_workers22", "arts_share12", "arts_share22"]])
    print(o.sort_values("d_arts", ascending=False).head(15)[["name", "arts_workers12", "arts_workers22", "arts_share12", "arts_share22"]])
    print(o.sort_values("d_arts").head(10)[["name", "arts_workers12", "arts_workers22", "arts_share12", "arts_share22"]])
    print(out.describe().T[["count", "50%"]])


if __name__ == "__main__":
    main()
