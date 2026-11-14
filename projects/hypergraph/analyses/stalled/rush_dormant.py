"""EXPLORATORY (decides nothing). Of the foundation starts in the six months before 15 June 2022 that have no CO by
November 2026, how many show no DOB permit activity (DOB NOW permit issued, or legacy permit issued) on the BBL after
1 November 2025? These are candidate dormant foundation sites. Also borough and flood-zone counts."""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
B = ROOT / "data/big/construction"
D = ROOT / "data/derived/stalled"
s = pd.read_csv(D / "vesting_jobs_union.csv", dtype={"bbl": str})
s = s[(s.window == 2022) & s.co_any.isna()]
f = pd.read_csv(D / "flood_jobs.csv", dtype={"bbl": str})[["job", "borough", "flood"]]
s = s.merge(f, on="job", how="left")
dn = pd.read_parquet(B / "dobnow_permits_2022on.parquet", columns=["bbl", "issued_date"])
dn["d"] = pd.to_datetime(dn.issued_date, errors="coerce")
lg = pd.read_parquet(B / "permits_nb_legacy.parquet", columns=["bbl", "issuance_date"])
lg["d"] = pd.to_datetime(lg.issuance_date, format="%m/%d/%Y", errors="coerce")
allp = pd.concat([dn[["bbl", "d"]], lg[["bbl", "d"]]])
allp["bbl"] = allp.bbl.astype(str).str.replace(r"\.0+$", "", regex=True)
last = allp.groupby("bbl").d.max()
s["last_permit"] = s.bbl.map(last)
s["dormant"] = ~(s.last_permit >= pd.Timestamp("2025-11-01"))
res = dict(no_co=int(len(s)), dormant_no_permit_since_nov2025=int(s.dormant.sum()),
           by_borough=s.groupby("borough").dormant.agg(["sum", "size"]).astype(int).to_dict("index"),
           dormant_in_flood_zone=int(s[s.dormant].flood.fillna(0).sum()),
           note="DOB NOW permits in the cache are those expiring 2022 or later; legacy permits are NB-job permits only.")
print(json.dumps(res, indent=1))
(D / "rush_dormant.json").write_text(json.dumps(res, indent=1))
s[["job", "bbl", "system", "start", "borough", "flood", "last_permit", "dormant"]].to_csv(D / "rush_no_co_jobs.csv", index=False)
