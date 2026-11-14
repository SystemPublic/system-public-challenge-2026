"""Parse the NYU Furman Center CoreData neighbourhood indicator workbook into a long panel.
Source file (kept outside Dropbox): ~/opt/nyc-concordance/affordability/furman/ni.xlsx,
downloaded from https://www.furmancenter.org/files/CoreData/Neighorhood_Indicators_CoreDataDownload_2026-05-05.xlsx
Output: data/derived/affordability/furman_panel.csv (region_id, region_name, region_type, year, indicator columns as numbers).
Prints nothing about values."""
import csv, hashlib, json, os, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import xlsx_min as X
SRC = Path(os.path.expanduser("~/opt/nyc-concordance/affordability/furman/ni.xlsx"))
OUT = ROOT / "data/derived/affordability"
KEEP = ["rent_gross_med_adj", "rent_gross_recent_med_adj", "hh_inc_med_adj", "hh_inc_rent_med_adj", "pop_edu_collp_pct",
        "pop_pov_pct", "pop_num", "pop_race_white_pct", "pop_race_black_pct", "pop_race_hisp_pct", "pop_race_asian_pct",
        "rent_burden_med", "rent_burden_mod_pct", "rent_burden_sev_pct", "rburden_mod_ami_le80", "rburden_sev_ami_le80",
        "afford_le080_rct", "afford_le030_rct", "pop_bornstate_pct", "unit_occ_own_pct", "unit_num", "hh_u18_pct",
        "unit_occ_rent_sevcrowd_pct", "priv_evic_filing_rt", "priv_evic_filings", "crime_all_rt", "crime_viol_rt",
        "serious_viol_rate", "rent_pct_nycha", "rs_unit_share", "voucher_pct", "hpi_al", "med_r_cn", "nb_permit_res_units",
        "pop_65p_pct", "pop_foreign_pct", "pct_prof_math", "units_cert"]

def num(x):
    if x is None: return ""
    if isinstance(x, float): return x
    s = str(x).replace("$", "").replace(",", "").strip()
    pct = s.endswith("%"); s = s.rstrip("%")
    try: v = float(s)
    except ValueError: return ""
    return v  # percentages stay in percent units

def main():
    it = X.rows(SRC, "Data"); h = next(it)
    keep = [k for k in KEEP if k in h]
    OUT.mkdir(parents=True, exist_ok=True)
    n = 0
    with open(OUT / "furman_panel.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["region_id", "region_name", "region_type", "year"] + keep)
        for r in it:
            r = r + [None] * (len(h) - len(r)); d = dict(zip(h, r))
            rid = d["region_id"]; rid = str(int(rid)) if isinstance(rid, float) else str(rid)
            yr = d["year"]; yr = str(int(yr)) if isinstance(yr, float) else str(yr)
            w.writerow([rid, d["region_name"], d["region_type"], yr] + [num(d[k]) for k in keep]); n += 1
    src = {"kind": "file", "publisher": "NYU Furman Center, CoreData.nyc neighbourhood indicators",
           "url": "https://www.furmancenter.org/files/CoreData/Neighorhood_Indicators_CoreDataDownload_2026-05-05.xlsx",
           "file_date": "2026-05-05", "sha256": hashlib.sha256(SRC.read_bytes()).hexdigest(), "bytes": SRC.stat().st_size,
           "fetched": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(SRC.stat().st_mtime)), "rows": n,
           "note": "Dollar amounts are inflation-adjusted by the publisher. Sub-borough areas are groups of census tracts that approximate community districts (55 areas)."}
    (OUT / "furman_source.json").write_text(json.dumps(src, indent=1))

if __name__ == "__main__":
    main()
