"""Build an Underlay collection of the live DOHMH Restaurant Inspection Results
(NYC Open Data 43nn-pn8j), all five boroughs, plus the restaurants that have
dropped off the city's list. Nothing is sent to the Underlay; push.py does that.

Record types (the first three keep the keys of nyc/restaurant-inspections v1.0.0):
  Restaurant         id = CAMIS
  Inspection         id = CAMIS-YYYY-MM-DD-<inspection type slug>
  Violation          id = <inspection id>-<violation code>; a code repeated within one
                     inspection gets -2, -3 ... on its second and later occurrences
  RemovedRestaurant  id = CAMIS, for restaurants in an earlier copy of the table and
                     absent from the live table

Inputs
  live table, fetched through concord.socrata (cache in ~/opt, outside Dropbox)
  ~/opt/nyc-concordance/underlay/records_v1.0.0.ndjson        (fetch_underlay.py)
  ~/opt/nyc-concordance/restaurants_wayback/20260403010027.csv (Internet Archive copy)
Outputs
  ~/opt/nyc-concordance/underlay_publish/  records.ndjson, record_hashes.tsv, schemas.json,
      readme.md, collection.json, source.json, live_43nn-pn8j_all.csv.gz
  data/derived/underlay_publish/  manifest.json, schemas.json, readme.md,
      removed_restaurants.csv

Run:  python analyses/underlay_publish/build.py [--refresh] [--allow-dirty]
The readme names the git commit of this folder, so the folder must be committed first.
"""
import argparse
import gzip
import hashlib
import json
import re
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

import jsonschema
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from concord import socrata  # noqa: E402

HERE = Path(__file__).resolve().parent
BIG = Path.home() / "opt" / "nyc-concordance" / "underlay_publish"
OUT = ROOT / "data" / "derived" / "underlay_publish"
SNAP = Path.home() / "opt" / "nyc-concordance" / "underlay" / "records_v1.0.0.ndjson"
SNAP_HASH = "ulv2:07a7f08a0d5c85649920f8adc6946d27c17f5e2d75e9ee07c0ad4ae0fcc6739c"
SNAP_NAME = "nyc/restaurant-inspections v1.0.0"
IA_CAPTURE = "20260403010027"
IA_FILE = Path.home() / "opt" / "nyc-concordance" / "restaurants_wayback" / f"{IA_CAPTURE}.csv"
IA_URL = (f"https://web.archive.org/web/{IA_CAPTURE}id_/https://data.cityofnewyork.us/"
          "api/views/43nn-pn8j/rows.csv?accessType=DOWNLOAD")
DATASET = "43nn-pn8j"
COLS = ("camis,dba,boro,building,street,zipcode,phone,cuisine_description,inspection_date,action,"
        "violation_code,violation_description,critical_flag,score,grade,grade_date,record_date,"
        "inspection_type,latitude,longitude,community_board,council_district,census_tract,bin,bbl,nta")
SLUG = "nyc-restaurant-inspections-2026-11"
TERMS_URL = "https://www.nyc.gov/main/terms-of-use"
OPEN_DATA_LAW = "https://codelibrary.amlegal.com/codes/newyorkcity/latest/NYCadmin/0-0-0-216807"


# ---------- helpers ----------

def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def canonical(rec):
    """Underlay protocol v2 canonical form: fixed envelope, data in JCS (keys sorted)."""
    data = json.dumps(rec["data"], sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return ('{"id":' + json.dumps(rec["id"], ensure_ascii=False) + ',"type":'
            + json.dumps(rec["type"], ensure_ascii=False) + ',"data":' + data + "}")


def rhash(rec):
    return hashlib.sha256(canonical(rec).encode("utf-8")).hexdigest()


def s(v):
    """City string field: missing becomes ''."""
    return "" if v is None or pd.isna(v) else str(v)


def git_commit():
    rel = HERE.relative_to(ROOT)
    dirty = subprocess.run(["git", "status", "--porcelain", "--", str(rel)], cwd=ROOT,
                           capture_output=True, text=True).stdout.strip()
    commit = subprocess.run(["git", "log", "-1", "--format=%H", "--", str(rel)], cwd=ROOT,
                            capture_output=True, text=True).stdout.strip()
    return commit, dirty


# ---------- schemas ----------

def schemas():
    st = {"type": "string"}
    base = {"$schema": "http://json-schema.org/draft-07/schema#", "type": "object",
            "additionalProperties": False}
    restaurant = dict(base, title="Restaurant",
                      description="A food service establishment in New York City listed in the DOHMH "
                                  "Restaurant Inspection Results (43nn-pn8j), keyed by CAMIS.",
                      required=["name", "boro"],
                      properties={
                          "name": dict(st, description="Business name (DBA)"),
                          "boro": dict(st, description="Borough"),
                          "building": dict(st, description="Building number"),
                          "street": dict(st, description="Street name as the city gives it"),
                          "zipcode": dict(st, description="ZIP code"),
                          "phone": dict(st, description="Phone number"),
                          "cuisineDescription": dict(st, description="Cuisine as the city codes it"),
                          "latitude": {"type": "number", "description": "Latitude; 0 where the city has not geocoded the address"},
                          "longitude": {"type": "number", "description": "Longitude; 0 where the city has not geocoded the address"},
                          "nta": dict(st, description="Neighborhood Tabulation Area code"),
                          "communityBoard": dict(st, description="Community board (borough digit and board number)"),
                          "bbl": dict(st, description="Borough-Block-Lot tax lot identifier"),
                          "bin": dict(st, description="Building Identification Number"),
                          "inspected": {"type": "boolean", "description": "False when the city lists the restaurant with only the placeholder inspection date 1900-01-01"},
                      })
    inspection = dict(base, title="Inspection",
                      description="One inspection of one restaurant: a CAMIS, an inspection date and an "
                                  "inspection type. Same key and fields as nyc/restaurant-inspections v1.0.0.",
                      required=["restaurantId", "inspectionDate", "inspectionType", "action", "grade", "gradeDate"],
                      properties={
                          "restaurantId": dict(st, description="CAMIS of the restaurant", **{"x-ref-type": "Restaurant"}),
                          "inspectionDate": dict(st, pattern=r"^\d{4}-\d{2}-\d{2}$", description="Inspection date"),
                          "inspectionType": dict(st, description="Inspection type as the city gives it"),
                          "action": dict(st, description="Action taken"),
                          "score": {"type": "integer", "description": "Score (lower is better); absent when the city gives none"},
                          "grade": dict(st, description="Letter grade; empty when the city gives none"),
                          "gradeDate": dict(st, pattern=r"^(\d{4}-\d{2}-\d{2})?$", description="Grade date; empty when none"),
                      })
    violation = dict(base, title="Violation",
                     description="One violation cited at one inspection. The key is the inspection id plus the "
                                 "violation code; a code cited more than once in one inspection gets -2, -3 ... "
                                 "on its later occurrences and carries an occurrence number.",
                     required=["inspectionId", "violationCode", "violationDescription", "criticalFlag"],
                     properties={
                         "inspectionId": dict(st, description="Id of the inspection", **{"x-ref-type": "Inspection"}),
                         "violationCode": dict(st, description="Violation code"),
                         "violationDescription": dict(st, description="Violation text"),
                         "criticalFlag": dict(st, description="Critical, Not Critical or Not Applicable"),
                         "occurrence": {"type": "integer", "minimum": 2,
                                        "description": "Present only on the second and later citations of the same code in one inspection"},
                     })
    last = {"type": "object", "additionalProperties": False,
            "required": ["inspectionDate", "inspectionType"],
            "properties": {
                "inspectionId": st, "inspectionDate": dict(st, pattern=r"^\d{4}-\d{2}-\d{2}$"),
                "inspectionType": st, "action": st, "grade": st,
                "score": {"type": "integer"}}}
    removed = dict(base, title="RemovedRestaurant",
                   description="A restaurant listed in an earlier copy of 43nn-pn8j and absent from the live "
                               "table at the fetch recorded in absentFrom. The city does not say why a "
                               "restaurant leaves the table; most closed or lost their permit.",
                   required=["name", "boro", "shownBy", "source", "absentFrom", "evidence"],
                   properties={
                       "name": st, "boro": st, "building": st, "street": st, "zipcode": st,
                       "cuisineDescription": st,
                       "lastInspection": dict(last, description="The restaurant's latest inspection in the source copy; absent when the source lists only the placeholder date 1900-01-01"),
                       "source": {"type": "string", "enum": ["underlay-snapshot", "internet-archive"],
                                  "description": "Copy the name, address, cuisine and last inspection come from"},
                       "shownBy": {"type": "array", "minItems": 1, "uniqueItems": True,
                                   "items": {"type": "string", "enum": ["underlay-snapshot", "internet-archive"]},
                                   "description": "Every earlier copy that lists this CAMIS"},
                       "snapshotVersion": dict(st, pattern=r"^ulv2:[0-9a-f]{64}$",
                                               description="Version hash of nyc/restaurant-inspections v1.0.0, when the snapshot lists it"),
                       "snapshotRecordHash": dict(st, pattern=r"^[0-9a-f]{64}$",
                                                  description="Hash of the Restaurant record in that version"),
                       "archiveCopy": {"type": "object", "additionalProperties": False,
                                       "required": ["url", "captured"],
                                       "properties": {"url": st, "captured": st},
                                       "description": "Internet Archive copy of the full table that lists this CAMIS"},
                       "absentFrom": {"type": "object", "additionalProperties": False,
                                      "required": ["dataset", "rowsUpdatedAt", "fetched"],
                                      "properties": {"dataset": st, "rowsUpdatedAt": st, "fetched": st}},
                       "evidence": dict(st, description="How the removal was shown, in one sentence"),
                   })
    return {"Restaurant": restaurant, "Inspection": inspection, "Violation": violation,
            "RemovedRestaurant": removed}


# ---------- fetch ----------

def fetch(refresh):
    BIG.mkdir(parents=True, exist_ok=True)
    socrata.CACHE = BIG / "socrata_cache"           # keep the 300k-row cache out of Dropbox
    before = socrata.metadata(DATASET, refresh=True)["rowsUpdatedAt"]
    rows, src = socrata.query_all(DATASET, select=COLS, refresh=refresh)
    after = socrata.metadata(DATASET, refresh=True)["rowsUpdatedAt"]
    if refresh and before != after:
        sys.exit(f"table rewritten during the fetch ({before} -> {after}); run again")
    checks = {}
    for name, q in {"rows": {"select": "count(*)"},
                    "restaurants": {"select": "count(distinct camis)"},
                    "violation_rows": {"select": "count(*)",
                                       "where": "inspection_date > '1901-01-01' and violation_code is not null"},
                    "inspections": {"select": "count(distinct camis || '|' || inspection_date || '|' || inspection_type)",
                                    "where": "inspection_date > '1901-01-01'"}}.items():
        r, _ = socrata.query(DATASET, refresh=refresh, **q)
        checks[name] = int(list(r[0].values())[0])
    src["server_counts"] = checks
    src["rows_updated_at_after_fetch"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(after))
    df = pd.DataFrame(rows, columns=COLS.split(","))
    df.to_csv(BIG / "live_43nn-pn8j_all.csv.gz", index=False)
    src["local_copy"] = "~/opt/nyc-concordance/underlay_publish/live_43nn-pn8j_all.csv.gz"
    return df.astype(object).where(df.notna(), None), src


# ---------- build ----------

def build_live(L):
    L = L.copy()
    L["date"] = L.inspection_date.str[:10]
    real = L.date > "1901"
    problems = Counter()

    # Restaurants: one per CAMIS; attributes from the row of the latest inspection
    R = {}
    order = L.sort_values(["camis", "date"], ascending=[True, False], kind="stable")
    inspected = set(L.loc[real, "camis"])
    varies = (L.groupby("camis")[["dba", "building", "street", "nta", "bbl", "bin"]].nunique(dropna=False) > 1).sum()
    for col, n in varies.items():
        if n:
            problems[f"restaurants_where_{col}_varies_across_rows"] = int(n)
    for r in order.drop_duplicates("camis").sort_values("camis").itertuples(index=False):
        camis = r.camis
        d = {"name": s(r.dba), "boro": s(r.boro), "building": s(r.building), "street": s(r.street),
             "zipcode": s(r.zipcode), "phone": s(r.phone), "cuisineDescription": s(r.cuisine_description),
             "nta": s(r.nta), "communityBoard": s(r.community_board), "bbl": s(r.bbl), "bin": s(r.bin),
             "inspected": camis in inspected}
        for k in ("latitude", "longitude"):
            if s(getattr(r, k)) != "":
                d[k] = float(getattr(r, k))
        R[camis] = d

    # Inspections
    I = {}
    li = L[real].copy()
    if li.inspection_type.isna().any():
        problems["inspection_type_missing_on_dated_rows"] = int(li.inspection_type.isna().sum())
    li["iid"] = li.camis + "-" + li.date + "-" + li.inspection_type.fillna("").map(slug)
    varies = (li.groupby("iid")[["action", "score", "grade", "grade_date"]].nunique(dropna=False) > 1).sum()
    for col, n in varies.items():
        if n:
            problems[f"inspections_where_{col}_varies_across_rows"] = int(n)
    for r in li.drop_duplicates("iid").sort_values("iid").itertuples(index=False):
        iid = r.iid
        d = {"restaurantId": r.camis, "inspectionDate": r.date, "inspectionType": s(r.inspection_type),
             "action": s(r.action), "grade": s(r.grade), "gradeDate": s(r.grade_date)[:10]}
        if s(r.score) != "":
            d["score"] = int(r.score)
        I[iid] = d

    # Violations
    V = {}
    lv = li[li.violation_code.notna()].copy()
    lv["desc"] = lv.violation_description.fillna("")
    lv = lv.sort_values(["iid", "violation_code", "desc", "critical_flag"], kind="stable")
    lv["occ"] = lv.groupby(["iid", "violation_code"]).cumcount() + 1
    for r in lv.itertuples(index=False):
        vid = f"{r.iid}-{r.violation_code}" + (f"-{r.occ}" if r.occ > 1 else "")
        d = {"inspectionId": r.iid, "violationCode": r.violation_code,
             "violationDescription": r.desc, "criticalFlag": s(r.critical_flag)}
        if r.occ > 1:
            d["occurrence"] = int(r.occ)
        V[vid] = d
    repeats = int((lv.occ > 1).sum())
    return R, I, V, problems, repeats, len(lv)


def load_snapshot():
    R, I, hashes = {}, {}, {}
    for line in open(SNAP):
        r = json.loads(line)
        if r["type"] == "Restaurant":
            R[r["id"]] = r["data"]
            hashes[("Restaurant", r["id"])] = r["hash"]
        elif r["type"] == "Inspection":
            I[r["id"]] = r["data"]
        hashes[(r["type"], r["id"])] = r["hash"]
    return R, I, hashes


def last_of(insps):
    """Latest inspection by (date, id)."""
    iid, d = max(insps, key=lambda x: (x[1]["inspectionDate"], x[0]))
    out = {"inspectionId": iid, "inspectionDate": d["inspectionDate"],
           "inspectionType": d.get("inspectionType", ""), "action": d.get("action", ""),
           "grade": d.get("grade", "")}
    if d.get("score") is not None:
        out["score"] = int(d["score"])
    return out


def build_removed(live_camis, live_boro, src):
    absent = {"dataset": DATASET, "rowsUpdatedAt": src["rows_updated_at"], "fetched": src["fetched"]}
    sR, sI, shash = load_snapshot()
    by_rest = {}
    for iid, d in sI.items():
        by_rest.setdefault(d["restaurantId"], []).append((iid, d))
    snap_gone = sorted(set(sR) - live_camis)
    moved = sorted(c for c in sR if c in live_camis and live_boro[c] != "Manhattan")

    A = pd.read_csv(IA_FILE, dtype=str, usecols=["CAMIS", "DBA", "BORO", "BUILDING", "STREET", "ZIPCODE",
                                                  "CUISINE DESCRIPTION", "INSPECTION DATE", "ACTION",
                                                  "SCORE", "GRADE", "INSPECTION TYPE"])
    A["date"] = pd.to_datetime(A["INSPECTION DATE"], format="%m/%d/%Y").dt.strftime("%Y-%m-%d").fillna("1900-01-01")
    ia_gone = sorted(set(A.CAMIS) - live_camis)
    A = A[A.CAMIS.isin(ia_gone)].sort_values(["CAMIS", "date"], ascending=[True, False], kind="stable")
    ia = {}
    for camis, g in A.groupby("CAMIS", sort=True):
        r = g.iloc[0]
        d = {"name": s(r.DBA), "boro": s(r.BORO), "building": s(r.BUILDING), "street": s(r.STREET),
             "zipcode": s(r.ZIPCODE), "cuisineDescription": s(r["CUISINE DESCRIPTION"])}
        if r.date > "1901":
            t = s(r["INSPECTION TYPE"])
            li = {"inspectionId": f"{camis}-{r.date}-{slug(t)}", "inspectionDate": r.date,
                  "inspectionType": t, "action": s(r.ACTION), "grade": s(r.GRADE)}
            if s(r.SCORE) != "":
                li["score"] = int(float(r.SCORE))
            d["lastInspection"] = li
        ia[camis] = d

    out = {}
    live_note = (f"absent from the live table {DATASET} (rowsUpdatedAt {absent['rowsUpdatedAt']}, "
                 f"fetched {absent['fetched']})")
    for camis in sorted(set(snap_gone) | set(ia)):
        shown = []
        if camis in sR:
            shown.append("underlay-snapshot")
        if camis in ia:
            shown.append("internet-archive")
        if camis in sR:
            d0 = sR[camis]
            d = {"name": d0.get("name", ""), "boro": d0.get("boro", ""), "building": d0.get("building", ""),
                 "street": d0.get("street", ""), "zipcode": d0.get("zipcode", ""),
                 "cuisineDescription": d0.get("cuisineDescription", ""), "source": "underlay-snapshot"}
            if camis in by_rest:
                d["lastInspection"] = last_of(by_rest[camis])
            d["snapshotVersion"] = SNAP_HASH
            d["snapshotRecordHash"] = shash[("Restaurant", camis)]
        else:
            d = dict(ia[camis], source="internet-archive")
        if camis in ia:
            d["archiveCopy"] = {"url": IA_URL, "captured": IA_CAPTURE}
        parts = []
        if camis in sR:
            parts.append(f"listed in the Underlay collection {SNAP_NAME} ({SNAP_HASH})")
        if camis in ia:
            parts.append(f"listed in the Internet Archive copy of the full table captured {IA_CAPTURE}")
        d["shownBy"] = shown
        d["absentFrom"] = absent
        d["evidence"] = "CAMIS " + camis + " is " + " and ".join(parts) + ", and " + live_note + "."
        out[camis] = d
    stats = {"snapshot_restaurants": len(sR), "snapshot_gone": len(snap_gone),
             "snapshot_moved_borough": [{"camis": c, "snapshot_boro": sR[c].get("boro"),
                                         "live_boro": live_boro[c]} for c in moved],
             "snapshot_gone_inspections": sum(len(by_rest.get(c, [])) for c in snap_gone),
             "archive_capture": IA_CAPTURE, "archive_restaurants": int(pd.read_csv(IA_FILE, dtype=str, usecols=["CAMIS"]).CAMIS.nunique()),
             "archive_gone": len(ia), "both": len(set(snap_gone) & set(ia)),
             "snapshot_only": len(set(snap_gone) - set(ia)), "archive_only": len(set(ia) - set(snap_gone)),
             "archive_gone_never_inspected": sum(1 for c, d in ia.items() if "lastInspection" not in d),
             "snapshot_gone_by_last_year": dict(sorted(Counter(out[c]["lastInspection"]["inspectionDate"][:4]
                                                               for c in snap_gone if "lastInspection" in out[c]).items())),
             "archive_gone_by_boro": dict(sorted(Counter(ia[c]["boro"] for c in ia).items()))}
    return out, stats, shash


# ---------- readme ----------

def readme(src, commit, counts, rstats, fstats):
    q = src["query"]
    soql = "&".join(f"{k}={v}" for k, v in q.items())
    def and_join(xs):
        return ", ".join(xs[:-1]) + " and " + xs[-1] if len(xs) > 1 else "".join(xs)
    by_year = and_join([f"in {y} for {n:,}" for y, n in rstats["snapshot_gone_by_last_year"].items()])
    by_boro = and_join([f"{n:,} in {b}" if b != "0" else f"{n:,} with the borough code 0"
                        for b, n in rstats["archive_gone_by_boro"].items()])
    return f"""# NYC Restaurant Inspections, November 2026

This collection holds the New York City Department of Health and Mental Hygiene (DOHMH) Restaurant Inspection Results for all five boroughs, as the city published them on 12 November 2026. It also holds the restaurants that appear in earlier copies of the same table and have since been removed from it.

## Source

The source is the NYC Open Data dataset "DOHMH New York City Restaurant Inspection Results", dataset id `{DATASET}` (https://data.cityofnewyork.us/d/{DATASET}). The dataset's `rowsUpdatedAt` was {src['rows_updated_at']} when the rows were fetched, and it was unchanged when the fetch ended. The rows were fetched at {src['fetched']} through the Socrata API (`https://data.cityofnewyork.us/resource/{DATASET}.json`) with this query, paged by `$offset` in steps of 50,000:

```
{soql}
```

The fetch returned {src['n_rows']:,} rows. The city's own counts, queried by SoQL aggregation at the same time, were {src['server_counts']['rows']:,} rows, {src['server_counts']['restaurants']:,} distinct CAMIS numbers, {src['server_counts']['inspections']:,} distinct inspections (CAMIS, date and type, dated after 1901) and {src['server_counts']['violation_rows']:,} rows that cite a violation code on a dated inspection.

The collection was built by `analyses/underlay_publish/build.py` in the repository nyc-concordance, at git commit `{commit}`.

## Record types

| Type | Records | Id |
|---|---|---|
| Restaurant | {counts['Restaurant']:,} | CAMIS |
| Inspection | {counts['Inspection']:,} | CAMIS, inspection date and inspection type in slug form, for example `30191841-2024-11-20-cycle-inspection-initial-inspection` |
| Violation | {counts['Violation']:,} | inspection id plus violation code |
| RemovedRestaurant | {counts['RemovedRestaurant']:,} | CAMIS |

Restaurant, Inspection and Violation use the same ids and the same field names as the Underlay collection `nyc/restaurant-inspections` v1.0.0 (version hash `{SNAP_HASH}`). A record in the two collections with the same type and id describes the same restaurant, inspection or violation, so the two versions can be compared record by record. Where the city has not changed an inspection or a violation since June 2026, the record is identical and has the same hash in both collections.

This collection differs from v1.0.0 in four ways. It covers all five boroughs and every inspection the city lists, not only Manhattan inspections from 2024 onward. Restaurant records keep the city's NTA, community board, BBL and BIN fields, which v1.0.0 dropped, and an `inspected` flag. Restaurants that the city lists only with the placeholder date 1900-01-01 are included as Restaurant records with `inspected` set to false and no inspections; there are {fstats['never_inspected']:,} of them. A violation code that the city cites more than once in one inspection keeps a record for each citation. The first citation has the id used in v1.0.0, and later ones add `-2`, `-3` and an `occurrence` field. There are {fstats['repeated_violations']:,} such later citations; v1.0.0 kept one record for each code.

As in v1.0.0, a blank grade or grade date is an empty string and a blank score is left out. Dates are YYYY-MM-DD. Latitude and longitude are 0 where the city has not geocoded the address, and are left out where the city gives no value.

## Removed restaurants

The live table holds only restaurants in active status on the day it is written. A RemovedRestaurant record is a CAMIS listed in an earlier copy of the table and absent from the live table at the fetch above. Each record says which copies show it (`shownBy`), takes its name, address, cuisine and last inspection from one of them (`source`), and states the evidence in one sentence.

Two earlier copies were used. The first is `nyc/restaurant-inspections` v1.0.0, pushed on 12 June 2026, which covers Manhattan. Of its {rstats['snapshot_restaurants']:,} restaurants, {rstats['snapshot_gone']:,} are absent from the live table. A further {len(rstats['snapshot_moved_borough'])} are missing from the live Manhattan rows but are still listed under another borough, so they are not counted as removed; the earlier audit's figure of 543 included them. For the {rstats['snapshot_gone']:,} removed restaurants, the last inspection in the snapshot was {by_year}. These records give the snapshot's version hash and the hash of the snapshot's Restaurant record. The second is the copy of the full table that the Internet Archive captured at {IA_CAPTURE} (UTC, 3 April 2026), at {IA_URL}. Of its {rstats['archive_restaurants']:,} restaurants, {rstats['archive_gone']:,} are absent from the live table: {by_boro}. Of these, {rstats['archive_gone_never_inspected']:,} were listed only with the placeholder date and have no last inspection. Both copies show {rstats['both']:,} of the removed restaurants, the snapshot alone shows {rstats['snapshot_only']:,} and the archive copy alone shows {rstats['archive_only']:,}. Where both copies list a restaurant, the details come from the snapshot, which is the later copy.

The city does not say why a restaurant leaves the table. Most of these restaurants probably closed or lost their permit, and the data cannot separate the two.

## How the city changes this table

A comparison of v1.0.0 with the live table (docs/underlay_drift.md in the repository) found three things. First, the city rewrites the whole table every day: every row of the November fetch carries the same `record_date`, {fstats['record_dates']}, and `rowsUpdatedAt` records when the table was last written, not which rows changed. A citation of the dataset id and its update time therefore cannot be checked after the next day's rewrite. Second, the city lowers scores when violations are dismissed on adjudication. Of 24,030 Manhattan inspections present in both copies, 485 had a different score in November, and every one of the 485 was lower (median change −8 points). In 302 inspections violation codes were removed and none were added, and 202 grades of Z (grade pending) became final grades. Third, the city deletes a restaurant from the table, with all of its inspections, when the restaurant leaves active status. The {rstats['snapshot_gone']:,} Manhattan restaurants described above had {rstats['snapshot_gone_inspections']:,} inspections in the snapshot, and none of them is in the live table.

## Licence

The data are public records of the City of New York, published through NYC Open Data under the Open Data Law (Local Law 11 of 2012, now Title 23, Chapter 5 of the NYC Administrative Code, {OPEN_DATA_LAW}). The city attaches no licence to the dataset and states no restriction on the use of the data. The NYC Open Data site refers its users to the City of New York Terms of Use ({TERMS_URL}), which govern the city's websites. This collection is not published or endorsed by the City of New York.
"""


# ---------- main ----------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true", help="fetch the live table again instead of using the cache")
    ap.add_argument("--allow-dirty", action="store_true")
    a = ap.parse_args()
    commit, dirty = git_commit()
    if (dirty or not commit) and not a.allow_dirty:
        sys.exit(f"commit analyses/underlay_publish/ first (uncommitted: {dirty or 'never committed'})")
    BIG.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)

    L, src = fetch(a.refresh)
    R, I, V, problems, repeats, vrows = build_live(L)
    removed, rstats, shash = build_removed(set(R), {k: v["boro"] for k, v in R.items()}, src)
    sch = schemas()

    records = ([{"id": k, "type": "Restaurant", "data": v} for k, v in R.items()]
               + [{"id": k, "type": "Inspection", "data": v} for k, v in I.items()]
               + [{"id": k, "type": "Violation", "data": v} for k, v in V.items()]
               + [{"id": k, "type": "RemovedRestaurant", "data": v} for k, v in removed.items()])
    counts = dict(Counter(r["type"] for r in records))

    # validate every record against its schema, and the input rules that apply
    errs = Counter()
    validators = {t: jsonschema.Draft7Validator(x) for t, x in sch.items()}
    for x in sch.values():
        jsonschema.Draft7Validator.check_schema(x)
    examples = []
    for r in records:
        for e in validators[r["type"]].iter_errors(r["data"]):
            errs[r["type"]] += 1
            if len(examples) < 10:
                examples.append([r["type"], r["id"], e.message])
        if not r["id"] or len(r["id"].encode()) > 1024:
            errs["bad_id"] += 1
    ids = Counter((r["type"], r["id"]) for r in records)
    dup_ids = sum(1 for v in ids.values() if v > 1)
    refs_ok = (all(d["restaurantId"] in R for d in I.values()) and all(d["inspectionId"] in I for d in V.values()))

    sc = src["server_counts"]
    count_checks = {
        "rows_fetched == server rows": src["n_rows"] == sc["rows"],
        "Restaurant == distinct CAMIS": counts["Restaurant"] == sc["restaurants"],
        "Inspection == distinct (CAMIS, date, type)": counts["Inspection"] == sc["inspections"],
        "Violation == rows citing a code": counts["Violation"] == sc["violation_rows"] == vrows,
        # docs/underlay_drift.md found 543 snapshot restaurants missing from the live Manhattan rows;
        # 24 of them are still listed under another borough, so 519 are missing from the whole table
        "snapshot-derived removals == 543 - moved": rstats["snapshot_gone"] == 543 - len(rstats["snapshot_moved_borough"]),
    }

    # records identical to nyc/restaurant-inspections v1.0.0
    hashes = []
    same = Counter()
    for r in records:
        h = rhash(r)
        hashes.append((r["type"], r["id"], h))
        if shash.get((r["type"], r["id"])) == h:
            same[r["type"]] += 1

    lines = [json.dumps(r, ensure_ascii=False, separators=(",", ":")) for r in records]
    body = "\n".join(lines) + "\n"
    (BIG / "records.ndjson").write_text(body, encoding="utf-8")
    with open(BIG / "record_hashes.tsv", "w") as f:
        f.write("type\tid\thash\n")
        for t, i, h in hashes:
            f.write(f"{t}\t{i}\t{h}\n")
    src_out = dict(src)
    text = readme(src_out, commit, counts, rstats,
                  {"never_inspected": sum(1 for d in R.values() if not d["inspected"]),
                   "repeated_violations": repeats,
                   "record_dates": ", ".join(sorted(set(L.record_date.dropna().str[:10])))})
    collection = {"slug": SLUG, "name": "NYC Restaurant Inspections, November 2026", "public": True,
                  "description": ("DOHMH Restaurant Inspection Results (NYC Open Data 43nn-pn8j), all five "
                                  f"boroughs, rowsUpdatedAt {src['rows_updated_at']}, with the restaurants "
                                  "removed from the table since earlier copies."),
                  "message": f"43nn-pn8j rowsUpdatedAt {src['rows_updated_at']}, fetched {src['fetched']}; build {commit[:12]}",
                  "app_id": "nyc-concordance/underlay_publish",
                  "metadata": {"license": "City of New York open data (Admin. Code Title 23 ch. 5); no licence and no stated restriction on use; City of New York Terms of Use, " + TERMS_URL,
                               "tags": ["Food & Drink", "Government"],
                               "source": {k: src[k] for k in ("dataset", "name", "url", "rows_updated_at", "query", "fetched", "n_rows")},
                               "buildCommit": commit, "relatedVersion": f"{SNAP_NAME} {SNAP_HASH}"}}
    collection["metadata"]["description"] = collection["description"]
    for d in (BIG, OUT):
        (d / "schemas.json").write_text(json.dumps(sch, indent=1))
        (d / "readme.md").write_text(text)
    (BIG / "collection.json").write_text(json.dumps(collection, indent=1))
    (BIG / "source.json").write_text(json.dumps(src_out, indent=1))

    rows = [dict(camis=k, name=v["name"], boro=v["boro"], building=v["building"], street=v["street"],
                 zipcode=v["zipcode"], cuisine=v["cuisineDescription"], source=v["source"],
                 shown_by="+".join(v["shownBy"]),
                 last_inspection_date=v.get("lastInspection", {}).get("inspectionDate", ""),
                 last_inspection_type=v.get("lastInspection", {}).get("inspectionType", ""))
            for k, v in removed.items()]
    pd.DataFrame(rows).to_csv(OUT / "removed_restaurants.csv", index=False)

    sample = [h for h in hashes if h[0] == "RemovedRestaurant"][:3] + \
             [h for h in hashes if h[0] == "Restaurant"][:3] + \
             [h for h in hashes if h[0] == "Inspection" and shash.get((h[0], h[1])) != h[2]][:2] + \
             [h for h in hashes if h[0] == "Violation" and "occurrence" in V[h[1]]][:2]
    manifest = {
        "collection_slug": SLUG, "build_commit": commit, "built": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "source": src_out, "counts": counts, "total_records": len(records),
        "records_file": "~/opt/nyc-concordance/underlay_publish/records.ndjson",
        "records_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
        "records_bytes": len(body.encode("utf-8")),
        "schema_hashes": {t: hashlib.sha256(json.dumps(x, sort_keys=True, separators=(",", ":"),
                                                       ensure_ascii=False).encode()).hexdigest()
                          for t, x in sch.items()},
        "validation": {"schema_errors": dict(errs), "examples": examples, "duplicate_ids": dup_ids,
                       "references_resolve": refs_ok},
        "count_checks": count_checks, "consistency_notes": dict(problems),
        "repeated_violation_citations": repeats,
        "removed": rstats,
        "identical_to_nyc_v1.0.0": dict(same),
        "sample_hashes": [{"type": t, "id": i, "hash": h} for t, i, h in sample],
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=1))
    print(json.dumps({k: manifest[k] for k in ("counts", "validation", "count_checks", "consistency_notes",
                                                "removed", "identical_to_nyc_v1.0.0")}, indent=1))
    if errs or dup_ids or not refs_ok or not all(count_checks.values()):
        sys.exit("validation or count check failed; see manifest.json")


if __name__ == "__main__":
    main()
