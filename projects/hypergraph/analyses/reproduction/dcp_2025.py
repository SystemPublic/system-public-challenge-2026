"""repro-dcp-2025-completions: recompute DCP's 2025 Housing Production Snapshot numbers
from the portal copy of the Housing Database (br6q-ssj3). Registered in commit 308dd84
(pushed as bc791bc on prereg/repro-dcp-2025-completions) before any query here."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from concord import socrata

D = "br6q-ssj3"
OUTDIR = Path(__file__).resolve().parents[2] / "data" / "derived" / "reproduction"
OUTDIR.mkdir(parents=True, exist_ok=True)
NB = "job_type='New Building'"
sources = []

def q(ds, **k):
    rows, src = socrata.query(ds, **k)
    sources.append(src)
    return rows

def num(x):
    return float(x) if x not in (None, "") else 0.0

res = {}
# (a) completions in 2025 by status and borough
a = q(D, select="job_status, boro, count(*) as n, sum(classaprop) as classaprop, sum(units_co) as units_co",
      where=f"{NB} AND compltyear='2025'", group="job_status, boro")
res["completions_2025_by_status_boro"] = a
R1 = sum(num(r.get("classaprop")) for r in a)
R2 = sum(num(r.get("units_co")) for r in a)
R3 = sum(num(r.get("classaprop")) for r in a if r["job_status"].startswith("5"))
boro = {}
for r in a:
    boro[r["boro"]] = boro.get(r["boro"], 0) + num(r.get("classaprop"))
res["readings"] = {"R1": R1, "R2": R2, "R3": R3, "jobs": sum(int(r["n"]) for r in a)}
res["boro_R1"] = boro
boro2 = {}
for r in a:
    boro2[r["boro"]] = boro2.get(r["boro"], 0) + num(r.get("units_co"))
res["boro_R2"] = boro2
# (b) which permit cohorts completed in 2025 (exploratory)
res["completions_2025_by_permityear"] = q(D, select="permityear, count(*) as n, sum(classaprop) as units",
                                          where=f"{NB} AND compltyear='2025'", group="permityear", order="permityear")
# (c) permits issued 2025
c = q(D, select="job_status, count(*) as n, sum(classaprop) as units", where=f"{NB} AND permityear='2025'", group="job_status")
res["permits_2025_by_status"] = c
res["P1"] = sum(num(r.get("units")) for r in c if not r["job_status"].startswith("9"))
res["P2"] = sum(num(r.get("units")) for r in c)
# (d) version values
res["versions"] = q(D, select="version, count(*) as n", group="version")
# R1 for 2024 and other years, against DCP's published 2024 counts (33,974 then 33,859)
res["R1_by_year"] = q(D, select="compltyear, count(*) as n, sum(classaprop) as units, sum(units_co) as units_co",
                      where=f"{NB} AND compltyear >= '2015'", group="compltyear", order="compltyear")
# (e) aggregate cross-check
e = q("dbdt-5s7j", select="sum(comp2025) as c25, sum(comp2024) as c24, count(*) as n")
res["aggregate_cd"] = e

(OUTDIR / "dcp_2025_results.json").write_text(json.dumps(res, indent=1))
(OUTDIR / "dcp_2025_sources.json").write_text(json.dumps(sources, indent=1))
print(json.dumps({k: res[k] for k in ("readings", "boro_R1", "boro_R2", "P1", "P2", "versions", "aggregate_cd")}, indent=1))
print(json.dumps(res["R1_by_year"], indent=0))
print(json.dumps(res["completions_2025_by_status_boro"], indent=0))
print(json.dumps(res["permits_2025_by_status"], indent=0))
print(json.dumps(res["completions_2025_by_permityear"], indent=0))
