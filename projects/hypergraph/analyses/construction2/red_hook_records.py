"""Case study of Brooklyn block 555, lot 124 (348 Van Brunt St, inferred) and lot 27 (100 Sullivan St, the alternative).
Fetches every city record for both lots and writes data/derived/construction2/red_hook/records.json with source records."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from concord import socrata as so

OUT = ROOT / "data/derived/construction2/red_hook"
OUT.mkdir(parents=True, exist_ok=True)
LOTS = {"124": ("348", "VAN BRUNT"), "27": ("100", "SULLIVAN")}
res, srcs = {}, []


def q(name, ds, **soql):
    rows, src = so.query(ds, limit=5000, **soql)
    srcs.append({**src, "query_name": name})
    return rows


for lot, (num, street) in LOTS.items():
    bbl = f"3{555:05d}{int(lot):04d}"
    d = {}
    d["pluto"] = q(f"pluto_{lot}", "64uk-42ks", where=f"bbl='{bbl}'")
    legals = q(f"acris_legals_{lot}", "8h5j-fqxa", where=f"borough='3' and block='555' and lot='{lot}'")
    ids = sorted({x["document_id"] for x in legals})
    inn = ",".join(f"'{i}'" for i in ids)
    d["acris_legals"] = legals
    d["acris_master"] = q(f"acris_master_{lot}", "bnx9-e6tj", where=f"document_id in ({inn})") if ids else []
    d["acris_parties"] = q(f"acris_parties_{lot}", "636b-3b5g", where=f"document_id in ({inn})") if ids else []
    d["dob_job_filings_legacy"] = q(f"dob_jobs_legacy_{lot}", "ic3t-wcy2", where=f"borough='BROOKLYN' and block='00555' and lot='{int(lot):05d}'")
    d["dob_permits_legacy"] = q(f"dob_permits_legacy_{lot}", "ipu4-2q9a", where=f"borough='BROOKLYN' and block='00555' and lot='{int(lot):05d}'")
    d["dobnow_job_filings"] = q(f"dobnow_jobs_{lot}", "w9ak-ipjd", where=f"bbl='{bbl}'")
    d["dobnow_permits"] = q(f"dobnow_permits_{lot}", "rbx6-tga4", where=f"bbl='{bbl}'")
    d["co_legacy"] = q(f"co_legacy_{lot}", "bs8b-p36w", where=f"bbl='{bbl}'")
    d["co_dobnow"] = q(f"co_dobnow_{lot}", "pkdm-hqz6", where=f"bbl='{bbl}'")
    d["complaints_311_bbl"] = q(f"c311_bbl_{lot}", "erm2-nwe9", select="unique_key,created_date,closed_date,agency,complaint_type,descriptor,incident_address,borough,status,resolution_description",
                                where=f"bbl='{bbl}'")
    d["complaints_311_address"] = q(f"c311_addr_{lot}", "erm2-nwe9", select="unique_key,created_date,closed_date,agency,complaint_type,descriptor,incident_address,borough,status,resolution_description",
                                    where=f"upper(incident_address) like '{num} {street}%' and borough='BROOKLYN'")
    d["dob_complaints"] = q(f"dob_complaints_{lot}", "eabe-havv", where=f"house_number='{num}' and upper(house_street) like '{street}%' and complaint_number like '3%'")  # Brooklyn complaint numbers begin with 3
    d["dob_violations"] = q(f"dob_violations_{lot}", "3h2n-5cm9", where=f"boro='3' and block='00555' and lot='{int(lot):05d}'")
    res[lot] = {"bbl": bbl, **d}
    print(lot, {k: len(v) for k, v in d.items()})

# Note: the first run (12 Nov 2026) fetched these two tables without the Brooklyn filter; the rows from other boroughs
# (100 Sullivan St and 100 Sullivan Pl, Manhattan) were then removed by red_hook_filter() below, which gives the same result.
def red_hook_filter(r):
    for lot in r:
        r[lot]["complaints_311_address"] = [c for c in r[lot]["complaints_311_address"] if c.get("unique_key") in
                                            {x["unique_key"] for x in r[lot]["complaints_311_bbl"]} or c.get("borough") == "BROOKLYN"]
        r[lot]["dob_complaints"] = [c for c in r[lot]["dob_complaints"] if str(c.get("complaint_number", "")).startswith("3")]
    return r


res = red_hook_filter(res)
(OUT / "records.json").write_text(json.dumps(res, indent=1))
(OUT / "sources.json").write_text(json.dumps(srcs, indent=1))
