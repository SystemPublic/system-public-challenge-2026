"""Case study (exploratory, not a registered test): the assemblage at Van Brunt and King Streets, Red Hook,
Brooklyn block 545, lots 23-27 (330, 332, 334, 336 Van Brunt St and 142 King St), owner NY 336 Van Brunt LLC.
Fetches every city record for the five lots and writes data/derived/stalled/lot_334/records.json and sources.json."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from concord import socrata as so

OUT = ROOT / "data/derived/stalled/lot_334"
OUT.mkdir(parents=True, exist_ok=True)
BLOCK = 545
LOTS = {23: ("330", "VAN BRUNT"), 24: ("332", "VAN BRUNT"), 25: ("334", "VAN BRUNT"),
        26: ("336", "VAN BRUNT"), 27: ("142", "KING")}
res, srcs = {}, []


def q(name, ds, **soql):
    rows, src = so.query(ds, limit=5000, **soql)
    srcs.append({**src, "query_name": name})
    return rows


for lot, (num, street) in LOTS.items():
    bbl = f"3{BLOCK:05d}{lot:04d}"
    d = {}
    d["pluto"] = q(f"pluto_{lot}", "64uk-42ks", where=f"bbl='{bbl}'")
    legals = q(f"acris_legals_{lot}", "8h5j-fqxa", where=f"borough='3' and block='{BLOCK}' and lot='{lot}'")
    ids = sorted({x["document_id"] for x in legals})
    inn = ",".join(f"'{i}'" for i in ids)
    d["acris_legals"] = legals
    d["acris_master"] = q(f"acris_master_{lot}", "bnx9-e6tj", where=f"document_id in ({inn})") if ids else []
    d["acris_parties"] = q(f"acris_parties_{lot}", "636b-3b5g", where=f"document_id in ({inn})") if ids else []
    d["dob_job_filings_legacy"] = q(f"dob_jobs_legacy_{lot}", "ic3t-wcy2", where=f"borough='BROOKLYN' and block='{BLOCK:05d}' and lot='{lot:05d}'")
    d["dob_permits_legacy"] = q(f"dob_permits_legacy_{lot}", "ipu4-2q9a", where=f"borough='BROOKLYN' and block='{BLOCK:05d}' and lot='{lot:05d}'")
    d["dobnow_job_filings"] = q(f"dobnow_jobs_{lot}", "w9ak-ipjd", where=f"bbl='{bbl}' or (borough='BROOKLYN' and block='{BLOCK}' and lot='{lot}')")
    d["dobnow_permits"] = q(f"dobnow_permits_{lot}", "rbx6-tga4", where=f"bbl='{bbl}' or (borough='BROOKLYN' and block='{BLOCK}' and lot='{lot}')")
    d["co_legacy"] = q(f"co_legacy_{lot}", "bs8b-p36w", where=f"bbl='{bbl}'")
    d["co_dobnow"] = q(f"co_dobnow_{lot}", "pkdm-hqz6", where=f"bbl='{bbl}'")
    d["dob_violations"] = q(f"dob_violations_{lot}", "3h2n-5cm9", where=f"boro='3' and block='{BLOCK:05d}' and lot='{lot:05d}'")
    d["ecb_violations"] = q(f"ecb_violations_{lot}", "6bgk-3dad", where=f"boro='3' and block='{BLOCK:05d}' and lot='{lot:05d}'")
    d["dob_complaints"] = q(f"dob_complaints_{lot}", "eabe-havv",
                            where=f"house_number='{num}' and upper(house_street) like '{street}%' and complaint_number like '3%'")
    d["complaints_311"] = q(f"c311_{lot}", "erm2-nwe9",
                            select="unique_key,created_date,closed_date,agency,complaint_type,descriptor,incident_address,status,resolution_description",
                            where=f"bbl='{bbl}' or (borough='BROOKLYN' and upper(incident_address) like '{num} {street}%')")
    res[lot] = {"bbl": bbl, **d}
    print(lot, {k: len(v) for k, v in d.items()})

# BINs found on the DOB filings, for the stalled-sites table, which has no BBL
bins = sorted({r.get("bin__") or r.get("bin") for lot in res.values() for k in ("dob_job_filings_legacy", "dobnow_job_filings", "dobnow_permits", "dob_permits_legacy")
               for r in lot[k] if (r.get("bin__") or r.get("bin"))})
inb = ",".join(f"'{b}'" for b in bins)
stalled = q("stalled_bins", "i296-73x5", where=f"bin in ({inb})") if bins else []
stalled_addr = q("stalled_addr", "i296-73x5", where="borough_name='BROOKLYN' and upper(street_name) like 'VAN BRUNT%'")
res["bins"] = bins
res["stalled_by_bin"] = stalled
res["stalled_van_brunt"] = stalled_addr
print("bins", bins, "stalled", len(stalled), "stalled on Van Brunt", len(stalled_addr))
(OUT / "records.json").write_text(json.dumps(res, indent=1))
(OUT / "sources.json").write_text(json.dumps(srcs, indent=1))
