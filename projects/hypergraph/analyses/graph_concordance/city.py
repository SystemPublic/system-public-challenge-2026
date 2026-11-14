"""Step 3 (after registration): assemble the UHF42 indicator table. Computes no correlation."""
import json
import subprocess
import sys

import geopandas as gpd
import pandas as pd

import common as C
from indicators import INDICATORS

sys.path.insert(0, str(C.ROOT))
from analyses.mobility import ehdp  # noqa: E402

DER = C.ROOT / "data" / "derived"
GEO_URL = f"https://raw.githubusercontent.com/nychealth/EHDP-data/{ehdp.SHA}/geography/UHF42.geojson"


def latest(ind, mid):
    """Latest period (by end date, shortest span on ties) with at least 40 of the 42 UHF42 areas non-missing."""
    d = pd.DataFrame(json.load(open(ehdp._get(f"data/{ind}.json", f"{ind}.json"))))
    d = d[(d["MeasureID"] == mid) & (d["GeoType"] == "UHF42")].copy()
    d["Value"] = pd.to_numeric(d["Value"], errors="coerce")
    d["GeoID"] = d["GeoID"].astype(int)
    d = d.dropna(subset=["Value"])
    tp = pd.DataFrame(json.load(open(ehdp._get("metadata/TimePeriods.json", "TimePeriods.json")))).drop_duplicates("TimePeriodID").set_index("TimePeriodID")
    n = d.groupby("TimePeriodID")["Value"].count()
    ok = [p for p in n.index if n[p] >= 40]
    if not ok:
        return None, None
    p = max(ok, key=lambda x: (tp.loc[x, "end_period"], -(tp.loc[x, "end_period"] - tp.loc[x, "start_period"])))
    return d[d["TimePeriodID"] == p].groupby("GeoID")["Value"].mean(), str(tp.loc[p, "TimePeriod"])


def tract_to_uhf():
    f = ehdp.DIR + "/UHF42.geojson"
    import os
    if not os.path.exists(f):
        subprocess.run(["curl", "-s", "-f", "-m", "120", "-A", "python-client", "-o", f, GEO_URL], check=True)
    u = gpd.read_file(f)
    idc = [c for c in u.columns if c.lower() in ("geocode", "id", "uhfcode", "uhf", "geoid")][0]
    u = u[[idc, "geometry"]].rename(columns={idc: "uhf"}).to_crs(2263)
    t = gpd.read_file(DER / "neighbourhood" / "tracts.geojson").to_crs(2263)
    gid = [c for c in t.columns if c.upper() == "GEOID"][0]
    t["geometry"] = t.geometry.representative_point()
    j = gpd.sjoin(t[[gid, "geometry"]], u, how="left", predicate="within")
    return j.set_index(gid)["uhf"].dropna().astype(int)


def main():
    cols, src = {}, []
    x = tract_to_uhf()
    for key, role, label, s, pol, concepts, note in INDICATORS:
        if s[0] == "ehdp":
            v, p = latest(s[1], s[2])
            if v is None:
                src.append({"indicator": key, "dropped": "fewer than 40 areas in every period"})
                continue
            cols[key] = v
            src.append({"indicator": key, **ehdp.source(s[1], s[2], label, [p])})
        else:
            _, f, col, how = s
            d = pd.read_csv(DER / f)
            if how == "uhf":
                cols[key] = d.set_index("GeoID")[col]
            else:
                d["GEOID"] = d["GEOID"].astype(str)
                d["uhf"] = d["GEOID"].map(x.rename(index=str))
                d = d.dropna(subset=["uhf"])
                d["uhf"] = d["uhf"].astype(int)
                if how == "popmean":
                    pop = pd.read_csv(DER / "neighbourhood" / "tracts_acs.csv", dtype={"GEOID": str}).set_index("GEOID")["pop"]
                    d["w"] = d["GEOID"].map(pop).fillna(0)
                    d = d.dropna(subset=[col])
                    cols[key] = d.groupby("uhf").apply(lambda q: (q[col] * q["w"]).sum() / max(q["w"].sum(), 1))
                elif how == "rate_per_pop":
                    gq = d.groupby("uhf")[[col, "pop"]].sum()
                    cols[key] = gq[col] / gq["pop"] * 1000
                elif how == "ratio_of_sums":
                    a, b = col.split("/")
                    gq = d.groupby("uhf")[[a, b]].sum()
                    cols[key] = gq[a] / gq[b]
            src.append({"indicator": key, "kind": "project-derived", "file": "data/derived/" + f, "column": col, "aggregation": how,
                        "crosswalk": "tract representative point within UHF42 polygon (EHDP geography/UHF42.geojson at the pinned commit)"})
    t = pd.DataFrame(cols)
    t.index.name = "uhf42"
    t = t[t.index.isin(range(101, 600))]
    t.to_csv(C.OUT / "city_indicators_uhf42.csv")
    (C.OUT / "city_sources.json").write_text(json.dumps(src, indent=1))
    print(t.shape, t.notna().sum().to_dict())


if __name__ == "__main__":
    main()
