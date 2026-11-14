"""Download the raw files for the exploration note (docs/explore.md).

Large files go to ~/opt/nyc-concordance/explore/ (outside Dropbox). A record of every
source (dataset id, update time, query or URL, fetch time, rows) is written to
data/derived/explore/sources.json. Run from the repo root; safe to re-run (existing
files are kept).

Sources
  Film Permits, NYC Open Data tg4x-b46p (holds 2023 onward only), plus two Internet
    Archive copies of the same table's CSV export (4 Feb 2022 and 24 Sep 2022) for 2012 to June 2022.
  PLUTO: current table 64uk-42ks, and DCP archive versions 02a, 06c, 10v1, 14v2, 18v2.1, 24v4.
  DOHMH restaurant inspections 43nn-pn8j; DCWP issued licences w7w3-xahh; Dining Out NYC fpeh-f7ci;
    NYS Liquor Authority active licences (data.ny.gov 9s3h-dpkz).
  DCLA cultural organisations u35m-9t32; DCP Facilities Database ji82-xba5.
  Census ZIP Code Business Patterns detail files, 1998 to 2023.
  Zillow Observed Rent Index by ZIP code.
  OpenStreetMap galleries through the Overpass API (current, and as of 1 January 2014, 2018, 2022).
  ACS 2018-2022 tables B19013, B15003, B01001, C24010 (table-based summary file) and
    ACS 2008-2012 sequence files for C24010 (New York and New Jersey).
"""
from __future__ import annotations

import csv
import io
import json
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from concord import socrata  # noqa: E402

RAW = Path.home() / "opt" / "nyc-concordance" / "explore"
OUT = ROOT / "data" / "derived" / "explore"
UA = {"User-Agent": "Mozilla/5.0 (research script)"}
SOURCES: dict[str, dict] = {}
SRC_FILE = OUT / "sources.json"
if SRC_FILE.exists():
    SOURCES.update(json.loads(SRC_FILE.read_text()))


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def save_sources():
    OUT.mkdir(parents=True, exist_ok=True)
    if SRC_FILE.exists():  # merge, so that two runs at once do not drop each other's records
        disk = json.loads(SRC_FILE.read_text())
        disk.update(SOURCES)
        SOURCES.update(disk)
    SRC_FILE.write_text(json.dumps(SOURCES, indent=1, sort_keys=True))


def download(url: str, rel: str, key: str, kind: str = "file", note: str = "") -> Path:
    f = RAW / rel
    f.parent.mkdir(parents=True, exist_ok=True)
    if not f.exists():
        print("get", url, flush=True)
        r = requests.get(url, headers=UA, timeout=900, stream=True)
        r.raise_for_status()
        tmp = f.with_suffix(f.suffix + ".part")
        with open(tmp, "wb") as fh:
            for chunk in r.iter_content(1 << 20):
                fh.write(chunk)
        tmp.rename(f)
        SOURCES[key] = {"kind": kind, "url": url, "file": f"~/opt/nyc-concordance/explore/{rel}",
                        "bytes": f.stat().st_size, "fetched": now(), "note": note}
        save_sources()
    return f


def socrata_csv(dataset: str, rel: str, key: str, domain: str = socrata.DOMAIN, page: int = 50000, **soql) -> Path:
    """Page a SoQL query to one CSV file in RAW and record the dataset version."""
    f = RAW / rel
    f.parent.mkdir(parents=True, exist_ok=True)
    if f.exists():
        return f
    params = {"$" + k: v for k, v in soql.items()}
    params.setdefault("$order", ":id")
    n, off, header = 0, 0, None
    tmp = f.with_suffix(".part")
    with open(tmp, "w", newline="") as fh:
        w = csv.writer(fh)
        while True:
            p = dict(params, **{"$limit": page, "$offset": off})
            r = socrata._req(f"{domain}/resource/{dataset}.csv", p, timeout=600)
            rows = list(csv.reader(io.StringIO(r.text)))
            if header is None:
                header = rows[0]
                w.writerow(header)
            w.writerows(rows[1:])
            n += len(rows) - 1
            print(dataset, n, flush=True)
            if len(rows) - 1 < page:
                break
            off += page
    tmp.rename(f)
    if domain == socrata.DOMAIN:
        src = socrata.source_record(dataset, params)
    else:
        m = requests.get(f"{domain}/api/views/{dataset}.json", headers=UA, timeout=120).json()
        ts = m.get("rowsUpdatedAt")
        src = {"kind": "ny-open-data", "dataset": dataset, "name": m.get("name"), "url": f"{domain}/d/{dataset}",
               "rows_updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts)) if ts else None,
               "query": params, "fetched": now()}
    src["n_rows"] = n
    src["file"] = f"~/opt/nyc-concordance/explore/{rel}"
    SOURCES[key] = src
    save_sources()
    return f


PLUTO_COLS = ("bbl,borough,block,lot,address,zipcode,landuse,bldgclass,ownertype,ownername,lotarea,bldgarea,"
              "numfloors,unitsres,unitstotal,yearbuilt,zonedist1,spdist1,histdist,latitude,longitude,bct2020,version")
PLUTO_OLD = {"02a": "nyc_pluto_02a.zip", "06c": "nyc_pluto_06c.zip", "10v1": "nyc_pluto_10v1.zip",
             "14v2": "nyc_pluto_14v2.zip", "18v2_1": "nyc_pluto_18v2_1_csv.zip", "24v4": "nyc_pluto_24v4_csv.zip"}
PLUTO_BASE = "https://s-media.nyc.gov/agencies/dcp/assets/files/zip/data-tools/bytes/pluto/"
ZBP = "https://www2.census.gov/programs-surveys/cbp/datasets/{y}/zbp{yy}detail.zip"
ZORI = "https://files.zillowstatic.com/research/public_csvs/zori/Zip_zori_uc_sfrcondomfr_sm_month.csv"
TB = "https://www2.census.gov/programs-surveys/acs/summary_file/2022/table-based-SF/data/5YRData/acsdt5y2022-{t}.dat"
SEQ = ("https://www2.census.gov/acs2012_5yr/summaryfile/2008-2012_ACSSF_By_State_By_Sequence_Table_Subset/"
       "{state}/Tracts_Block_Groups_Only/{f}")
OVERPASS = "https://overpass-api.de/api/interpreter"
# bounding box: the five boroughs and Hudson County, New Jersey
BBOX = "40.48,-74.27,40.93,-73.68"


def overpass(date: str | None, rel: str, key: str):
    f = RAW / rel
    f.parent.mkdir(parents=True, exist_ok=True)
    if f.exists():
        return f
    head = "[out:json][timeout:300]" + (f'[date:"{date}T00:00:00Z"]' if date else "") + ";"
    q = head + f'(nwr["tourism"="gallery"]({BBOX});nwr["shop"="art"]({BBOX});nwr["amenity"="arts_centre"]({BBOX});nwr["craft"="artist"]({BBOX});nwr["amenity"="studio"]["studio"="art"]({BBOX}););out center tags;'
    for i in range(4):
        r = requests.post(OVERPASS, data={"data": q}, headers={"User-Agent": "research-script/1.0"}, timeout=400)
        if r.status_code == 200:
            break
        time.sleep(20 * (i + 1))
    r.raise_for_status()
    f.write_text(r.text)
    SOURCES[key] = {"kind": "openstreetmap-overpass", "url": OVERPASS, "query": q, "as_of": date or "current",
                    "n_elements": len(r.json().get("elements", [])), "fetched": now(),
                    "file": f"~/opt/nyc-concordance/explore/{rel}"}
    save_sources()
    return f


def main(which: set[str]):
    if "film" in which:
        socrata_csv("tg4x-b46p", "film/film_current.csv", "film_current")
        for ts, q in (("20220204105500", "?accessType=DOWNLOAD"), ("20220924230956", "?accessType=DOWNLOAD")):
            rel = f"film_wayback/film_{ts}.csv"
            if not (RAW / rel).exists():
                download(f"http://web.archive.org/web/{ts}id_/https://data.cityofnewyork.us/api/views/tg4x-b46p/rows.csv{q}",
                         rel, f"film_wayback_{ts}", "internet-archive")
            elif f"film_wayback_{ts}" not in SOURCES:
                SOURCES[f"film_wayback_{ts}"] = {
                    "kind": "internet-archive",
                    "url": f"http://web.archive.org/web/{ts}id_/https://data.cityofnewyork.us/api/views/tg4x-b46p/rows.csv{q}",
                    "file": f"~/opt/nyc-concordance/explore/{rel}", "bytes": (RAW / rel).stat().st_size,
                    "fetched": "2026-11-13", "note": "Archived CSV export of tg4x-b46p; the 24 Sep 2022 copy was served gzipped and was unpacked."}
                save_sources()
    if "pluto" in which:
        socrata_csv("64uk-42ks", "pluto/pluto_current.csv", "pluto_current", select=PLUTO_COLS, order="bbl")
        for v, name in PLUTO_OLD.items():
            download(PLUTO_BASE + name, f"pluto/{name}", f"pluto_{v}", "dcp-bytes-archive")
    if "shops" in which:
        socrata_csv("43nn-pn8j", "shops/restaurant_dates.csv", "restaurant_dates",
                    select="camis, inspection_date, count(*) as n", group="camis, inspection_date", order="camis, inspection_date")
        socrata_csv("43nn-pn8j", "shops/restaurants.csv", "restaurants",
                    select="camis, dba, boro, building, street, zipcode, cuisine_description, latitude, longitude, bbl, count(*) as n",
                    group="camis, dba, boro, building, street, zipcode, cuisine_description, latitude, longitude, bbl", order="camis")
        socrata_csv("w7w3-xahh", "shops/dcwp_licences.csv", "dcwp_licences",
                    select="license_nbr, business_name, dba_trade_name, business_unique_id, business_category, license_type, license_status, "
                           "license_creation_date, lic_expir_dd, address_zip, address_borough, latitude, longitude",
                    order="license_nbr")
        socrata_csv("fpeh-f7ci", "shops/dining_out.csv", "dining_out")
        socrata_csv("9s3h-dpkz", "shops/liquor.csv", "liquor", domain="https://data.ny.gov",
                    select="licensepermitid, description, legalname, dba, zipcode, originalissuedate, effectivedate, georeference",
                    where="premisescounty in ('New York','Kings','Queens','Bronx','Richmond')", order="licensepermitid")
    if "art" in which:
        socrata_csv("u35m-9t32", "art/dcla.csv", "dcla")
        socrata_csv("ji82-xba5", "art/facdb_cultural.csv", "facdb_cultural",
                    select="uid, facname, address, zipcode, latitude, longitude, facgroup, facsubgrp, factype, opname, datasource",
                    where="facgroup='CULTURAL INSTITUTIONS'", order="uid")
        for d in (None, "2014-01-01", "2018-01-01", "2022-01-01"):
            try:
                overpass(d, f"art/osm_{d or 'current'}.json", f"osm_{d or 'current'}")
            except Exception as e:  # noqa: BLE001
                print("overpass failed", d, e)
            time.sleep(5)
    if "zbp" in which:
        for y in range(1998, 2024):
            try:
                download(ZBP.format(y=y, yy=str(y)[2:]), f"zbp/zbp{str(y)[2:]}detail.zip", f"zbp_{y}", "census-zbp")
            except Exception as e:  # noqa: BLE001
                print("zbp failed", y, e)
        download(ZORI, "zori/zip_zori.csv", "zori", "zillow-research")
    if "acs" in which:
        for t in ("b19013", "b15003", "b01001", "c24010"):
            download(TB.format(t=t), f"acs/acsdt5y2022-{t}.dat", f"acs2022_{t}", "census-acs")
        for st, ab in (("NewYork", "ny"), ("NewJersey", "nj")):
            download(SEQ.format(state=st, f=f"g20125{ab}.csv"), f"acs/g20125{ab}.csv", f"acs2012_geo_{ab}", "census-acs")
    save_sources()


if __name__ == "__main__":
    main(set(sys.argv[1:]) or {"film", "pluto", "shops", "art", "zbp", "acs"})
