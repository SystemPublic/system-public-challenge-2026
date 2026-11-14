"""Fetch the lot-level records for levers-vacant-lot-trial-match (after registration, commit 2a7c4b4).

Writes data/derived/levers/lots_records.csv (one row per land use 11 lot with its record-based type) and
data/derived/levers/lots_sources.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from concord import socrata  # noqa: E402

OUT = ROOT / "data" / "derived" / "levers"
START, END = "2024-11-13", "2026-11-13"
sources = {}


def q(name, ds, single=False, **soql):
    # the stalled-sites view ignores $offset and repeats its rows, so it is read in one page
    rows, src = socrata.query(ds, limit=50000, **soql) if single else socrata.query_all(ds, **soql)
    sources[name] = src
    return pd.DataFrame(rows)


def main():
    pl = q("pluto", "64uk-42ks", select="bbl,borough,block,lot,address,lotarea,ownertype,ownername,latitude,longitude,bct2020,pfirm15_flag,bldgclass",
           where="landuse='11'")
    pl["bbl"] = pl["bbl"].astype(float).astype("int64").astype(str)
    pl["lotarea"] = pd.to_numeric(pl["lotarea"], errors="coerce")
    for c in ("latitude", "longitude"):
        pl[c] = pd.to_numeric(pl[c], errors="coerce")
    bbls = set(pl["bbl"])

    gt = q("greenthumb", "p78i-pat6", select="bbl,gardenname,status")
    gt_bbl = set(gt["bbl"].dropna().astype(str).str.replace(r"\.0$", "", regex=True))

    # DOB permits, BIS: NB/DM jobs, or foundation/earthwork work types
    bis = q("dob_permits_bis", "ipu4-2q9a", select="bbl,bin__,job_type,work_type,issuance_date",
            where="(job_type in ('NB','DM') or work_type in ('FO','EW')) and issuance_date >= '01/01/2014'")
    # issuance_date is text in mm/dd/yyyy form in this dataset
    bis["date"] = pd.to_datetime(bis["issuance_date"], errors="coerce", format="mixed")
    now = q("dob_permits_now", "rbx6-tga4", select="bbl,bin,work_type,issued_date",
            where="issued_date >= '2014-01-01' and (work_type in ('New Building','Full Demolition','Foundation','Earth Work','Support of Excavation','Earthwork'))")
    now["date"] = pd.to_datetime(now["issued_date"], errors="coerce")
    nbf_bis = q("dob_jobs_bis", "ic3t-wcy2", select="bbl,bin__,job_type,pre__filing_date",
                where="job_type='NB'")
    nbf_bis["date"] = pd.to_datetime(nbf_bis["pre__filing_date"], errors="coerce", format="mixed")
    nbf_now = q("dob_jobs_now", "w9ak-ipjd", select="bbl,bin,job_type,filing_date", where="job_type='New Building'")
    nbf_now["date"] = pd.to_datetime(nbf_now["filing_date"], errors="coerce")
    stalled = q("stalled_sites", "i296-73x5", single=True, select="bin,date_complaint_received")

    def clean(s):
        return s.dropna().astype(str).str.replace(r"\.0+$", "", regex=True)

    recs = []
    for df, b in ((bis, "bbl"), (now, "bbl"), (nbf_bis, "bbl"), (nbf_now, "bbl")):
        d = df[[b, "date"]].dropna().copy()
        d["bbl"] = clean(d[b])
        recs.append(d[["bbl", "date"]])
    act = pd.concat(recs)
    act = act[act["bbl"].isin(bbls)]
    recent = set(act.loc[act["date"] >= START, "bbl"])
    older = set(act.loc[(act["date"] >= "2014-01-01") & (act["date"] < START), "bbl"])

    # stalled list BIN -> BBL through any DOB permit row
    binmap = pd.concat([
        pd.DataFrame({"bin": clean(bis["bin__"]), "bbl": clean(bis["bbl"])}) if "bin__" in bis else pd.DataFrame(),
        pd.DataFrame({"bin": clean(now["bin"]), "bbl": clean(now["bbl"])}),
        pd.DataFrame({"bin": clean(nbf_bis["bin__"]), "bbl": clean(nbf_bis["bbl"])}),
        pd.DataFrame({"bin": clean(nbf_now["bin"]), "bbl": clean(nbf_now["bbl"])}),
    ]).dropna().drop_duplicates()
    st_bbl = set(binmap.loc[binmap["bin"].isin(set(clean(stalled["bin"]))), "bbl"]) & bbls

    own = pl["ownername"].fillna("").str.upper()
    buyout = own.str.contains("HOUSING TRUST FUND|GOSR|STORM RECOVERY") | ((pl["ownertype"] == "O") & (pl["pfirm15_flag"] == "1"))

    def typ(i, r):
        if r.bbl in gt_bbl:
            return "garden"
        if buyout.iloc[i]:
            return "buyout"
        if r.bbl in recent:
            return "active_development"
        if r.bbl in st_bbl or r.bbl in older:
            return "stalled"
        if r.ownertype == "C":
            return "city_interim"
        return "private_idle"

    pl = pl.reset_index(drop=True)
    pl["type"] = [typ(i, r) for i, r in enumerate(pl.itertuples())]
    tr = pd.read_csv(ROOT / "data/derived/neighbourhood/vacant_shootings_tracts.csv", dtype={"bct2020": str})
    cut = tr["shootings"].quantile(0.9)
    top = set(tr.loc[tr["shootings"] >= cut, "bct2020"].astype(str))
    pl["bct2020"] = pl["bct2020"].astype(str).str.replace(r"\.0$", "", regex=True)
    pl["high_shooting"] = pl["bct2020"].isin(top)
    pl["small"] = pl["lotarea"] * 0.092903 <= 510
    pl.to_csv(OUT / "lots_records.csv", index=False)
    meta = {"high_shooting_cut_shootings_2019_2024": float(cut), "n_top_tracts": len(top),
            "shootings_in_top_tracts": int(tr.loc[tr["bct2020"].astype(str).isin(top), "shootings"].sum()),
            "shootings_all_tracts": int(tr["shootings"].sum()), "greenthumb_bbls": len(gt_bbl),
            "stalled_bbls_matched": len(st_bbl), "stalled_list_rows": len(stalled)}
    (OUT / "lots_sources.json").write_text(json.dumps({"sources": sources, "meta": meta}, indent=1, default=str))
    print(json.dumps(meta, indent=1))
    print(pl.groupby(["high_shooting", "type"]).size().unstack(0))
    print(pl[pl.high_shooting].groupby(["type", "small"]).size().unstack())


if __name__ == "__main__":
    main()
