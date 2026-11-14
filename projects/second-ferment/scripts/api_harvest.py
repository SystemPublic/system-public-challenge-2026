"""Harvest heat-related findings from the live System Public API.

The API holds about 3x more findings than the Dataverse CSV, including variables with no concept
and the ~20% of associations the provider flagged as inaccurately extracted. Every harvested row
is therefore tagged in_csv = 1/0 by checking its system_id against the local snapshot.

Usage: python3 -I api_harvest.py <repo_root>
Reads   <repo_root>/.env (SYSTEM_API_KEY) and <repo_root>/data/graph.db
Writes  <repo_root>/data/api/heat_variables.json     heat variables found by name search
        <repo_root>/data/api/cache/<variable_id>.json raw per-variable responses (re-runs cost no quota)
        <repo_root>/data/api/heat_associations.csv    every finding touching a heat variable
        <repo_root>/data/api/heat_med_api.csv         the subset with a medication on the other side
Rate limit is 10,000 requests/day; the script prints how many it made.
"""
import concurrent.futures as cf
import csv
import json
import os
import sqlite3
import sys
import threading
import urllib.parse
import urllib.request

root = sys.argv[1]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from heat_meds_lib import drug_classes, heat_tier  # noqa: E402

KEY = dict(l.strip().split("=", 1) for l in open(os.path.join(root, ".env")) if "=" in l)["SYSTEM_API_KEY"]
BASE = "https://public-api.system.com/v1/"
out = os.path.join(root, "data", "api")
cache = os.path.join(out, "cache")
os.makedirs(cache, exist_ok=True)
n_req = 0
lock = threading.Lock()


def get(path, **params):
    global n_req
    url = BASE + path + ("?" + urllib.parse.urlencode(params) if params else "")
    req = urllib.request.Request(url, headers={"x-api-key": KEY, "User-Agent": "heat-meds-hackathon"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                with lock:
                    n_req += 1
                return json.load(r)
        except Exception as e:  # noqa: BLE001
            err = e
    raise err


TERMS = [
    "heat wave", "heatwave", "heat stroke", "heatstroke", "heat illness", "heat-related", "extreme heat",
    "heat exhaustion", "heat stress", "heat strain", "hot weather", "heat exposure", "hot days", "heat index",
    "ambient temperature", "high temperature", "extreme temperature", "air temperature", "outdoor temperature",
    "apparent temperature", "summer", "hyperthermia", "heat tolerance", "heat acclimation", "hot environment",
    "heat event", "heat warning", "urban heat", "exertional heat", "passive heat", "thermal stress",
]

vpath = os.path.join(out, "heat_variables.json")
if os.path.exists(vpath):
    heat_vars = json.load(open(vpath))
else:
    heat_vars = {}
    for t in TERMS:
        off = 0
        while True:
            d = get("variables", search="name:" + t, limit=1000, offset=off).get("data", [])
            for v in d:
                if heat_tier(v.get("name", "")) == "direct":
                    heat_vars[v["system_id"]] = {"name": v["name"], "concept_id": v.get("concept_id")}
            if len(d) < 1000 or off >= 4000:
                break
            off += 1000
        print(f"{t}: running total {len(heat_vars)} heat variables", flush=True)
    json.dump(heat_vars, open(vpath, "w"))
print("heat variables:", len(heat_vars), "| ungrounded:", sum(1 for v in heat_vars.values() if not v["concept_id"]))


def fetch(vid):
    p = os.path.join(cache, urllib.parse.quote(vid, safe="") + ".json")
    if os.path.exists(p):
        return json.load(open(p))
    rows, off = [], 0
    while True:
        d = get(f"variables/{urllib.parse.quote(vid, safe='')}/associations", limit=1000, offset=off).get("data", [])
        rows += d
        if len(d) < 1000:
            break
        off += 1000
    json.dump(rows, open(p, "w"))
    return rows


assoc = {}
with cf.ThreadPoolExecutor(6) as ex:
    for i, rows in enumerate(ex.map(fetch, list(heat_vars))):
        for r in rows:
            assoc[r["system_id"]] = r
        if i % 300 == 0:
            print(f"  fetched {i}/{len(heat_vars)} variables, {len(assoc)} findings, {n_req} requests", flush=True)

db = sqlite3.connect(os.path.join(root, "data", "graph.db"))
local = {r[0] for r in db.execute("SELECT system_id FROM associations")}

cols = ["in_csv", "api_status", "drug_classes", "system_id", "study_id", "pubmed_id", "system_statistic_type", "statistic_value",
        "ci_lower", "ci_upper", "p_value", "variable_1_name", "variable_2_name", "variable_1_concept_id",
        "variable_2_concept_id", "variable_1_id", "variable_2_id"]
all_rows, med_rows = [], []
for r in assoc.values():
    n1, n2 = r.get("variable_1_name") or "", r.get("variable_2_name") or ""
    r["in_csv"] = int(r["system_id"] in local)
    grounded = bool(r.get("variable_1_concept_id") and r.get("variable_2_concept_id"))
    # in_csv: passed the provider's quality filter. api_only_ungrounded: outside the CSV's scope, unverified.
    # api_only_grounded: in scope but absent from the CSV, so probably removed for quality. Treat as suspect.
    r["api_status"] = "in_csv" if r["in_csv"] else ("api_only_ungrounded" if not grounded else "api_only_grounded_suspect")
    r["drug_classes"] = "; ".join(sorted(set(drug_classes(n1) + drug_classes(n2))))
    all_rows.append(r)
    if r["drug_classes"]:
        med_rows.append(r)
for name, rows in (("heat_associations.csv", all_rows), ("heat_med_api.csv", med_rows)):
    with open(os.path.join(out, name), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

print("requests made this run:", n_req)
print("heat findings from API:", len(all_rows), "| also in CSV:", sum(r["in_csv"] for r in all_rows),
      "| studies:", len({r["study_id"] for r in all_rows}))
print("heat x medication findings:", len(med_rows), "| also in CSV:", sum(r["in_csv"] for r in med_rows))
