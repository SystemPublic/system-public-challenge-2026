"""311 flooding complaint counts for further-tidal-flooding-trend (run after registration).
The registered patterns are applied together with agency = 'DEP': without it the Socrata server did not answer the
upper(...) like '%STREET FLOOD%' query over the 2010-2019 file within the client's timeout. The agency split of the
patterns is reported below to show what the filter excludes."""
import json
from pathlib import Path
from concord import socrata
ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "data" / "derived" / "round2" / "tidal_trend"
PAT = {
 "C3": "(upper(descriptor) like 'STREET FLOODING%' or upper(descriptor) like 'CATCH BASIN CLOGGED%' or upper(complaint_type) like '%STREET FLOOD%')",
 "C1": "(upper(descriptor) like 'STREET FLOODING%' or upper(complaint_type) like '%STREET FLOOD%')",
 "C4": "(upper(descriptor) like 'STREET FLOODING%' or upper(descriptor) like 'CATCH BASIN CLOGGED%' or upper(complaint_type) like '%STREET FLOOD%' or upper(descriptor) like 'SEWER BACKUP%')",
}
out, srcs = {}, []
# which agencies hold records matching the case-sensitive descriptor patterns (fast query), 2010-2019
rows, src = socrata.query("76ig-c548", select="agency, count(*) as n",
    where="created_date between '2010-01-01T00:00:00' and '2019-12-31T23:59:59' and (descriptor like 'Street Flooding%' or descriptor like 'Catch Basin Clogged%' or descriptor like 'Sewer Backup%')",
    group="agency", order="n desc")
out["agency_split_2010_2019"] = rows; srcs.append(src); print(rows, flush=True)
from concurrent.futures import ThreadPoolExecutor
def one(args):
    ds, y, k, group = args
    rows, src = socrata.query_all(ds, select="date_trunc_ymd(created_date) as d, incident_zip as zip, " + ("descriptor, complaint_type, " if group else "") + "count(*) as n",
        where=f"created_date between '{y}-01-01T00:00:00' and '{y}-12-31T23:59:59' and agency='DEP' and {PAT[k]}",
        group="d, zip" + (", descriptor, complaint_type" if group else ""), order="d, zip")
    return y, rows, src
jobs = [("76ig-c548", y, "C4", True) for y in range(2010, 2020)] + [("erm2-nwe9", y, "C3", False) for y in range(2020, 2026)]
with ThreadPoolExecutor(4) as ex:
    res = list(ex.map(one, jobs))
A = [r for (y, rows, s_) in res[:10] for r in rows]; B = [r for (y, rows, s_) in res[10:] for r in rows]
srcs += [s_ for (_, _, s_) in res]
out["C4desc_A"] = A; out["C3_B"] = B
print(len(A), len(B), flush=True)
from collections import Counter
cnt = Counter()
for r in A: cnt[(r.get("complaint_type"), r.get("descriptor"))] += int(r["n"])
out["descriptors_2010_2019"] = [{"complaint_type": a_, "descriptor": b_, "n": n} for (a_, b_), n in cnt.most_common()]
print(out["descriptors_2010_2019"], flush=True)
out["sources"] = srcs
(D / "complaints_by_day_zip.json").write_text(json.dumps(out))
