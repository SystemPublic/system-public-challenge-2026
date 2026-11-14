"""Build data-explainer.html from the derived analysis files.

Usage: python3 -I build_explainer.py <graph.db> <derived_dir> <out_html>
"""
import csv
import json
import os
import re
import sqlite3
import sys

db = sqlite3.connect(sys.argv[1])
derived, out_html = sys.argv[2], sys.argv[3]
summary = json.load(open(os.path.join(derived, "summary.json")))
path = json.load(open(os.path.join(derived, "pathways.json")))

stat_types = db.execute(
    "SELECT system_statistic_type, COUNT(*) FROM associations GROUP BY 1 ORDER BY 2 DESC"
).fetchall()
n_assoc, n_ci, n_p = db.execute(
    "SELECT COUNT(*), SUM(ci_lower IS NOT NULL), SUM(p_value IS NOT NULL) FROM associations"
).fetchone()
n_st, n_doi, n_pop, n_type = db.execute(
    "SELECT COUNT(*), SUM(doi IS NOT NULL), SUM(population_string IS NOT NULL), SUM(study_type IS NOT NULL) FROM studies"
).fetchone()
counts = {
    t: db.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    for t in ["associations", "studies", "variables", "concepts", "relationships"]
}
rel_single = db.execute("SELECT SUM(num_studies+0=1) FROM relationships").fetchone()[0]

# storage: drug-name rows that mention storage AND heat/temperature
storage_rows = list(csv.DictReader(open(os.path.join(derived, "storage_findings.csv"))))
rx_a = re.compile(r"storage|stored|refriger|shelf|degrad|cold chain", re.I)
rx_b = re.compile(r"temperature|heat|\bhot\b|refriger|cold chain", re.I)
storage_hits = [
    r for r in storage_rows
    if rx_a.search(r["variable_1_name"] + " " + r["variable_2_name"])
    and rx_b.search(r["variable_1_name"] + " " + r["variable_2_name"])
]
print("storage+temperature hits:", len(storage_hits))
for r in storage_hits:
    print("  ", r["variable_1_name"][:90], "<->", r["variable_2_name"][:90])

NOISE = {"temperature", "hot", "thermodynamic temperature", "risk", "survival rate", "death", "extreme heat",
         "heat stroke", "heat illness", "precipitation", "hypothermia", "calcifediol", "body mass index",
         "body temperature", "skin temperature", "sweat", "physical exercise", "breathing"}
heat_links = [x for x in path["heat_top_linked"] if x[0] not in NOISE][:18]

data = {
    "counts": counts,
    "stat_types": stat_types,
    "complete": {
        "Findings with a confidence interval": n_ci / n_assoc,
        "Findings with a p-value": n_p / n_assoc,
        "Studies with a DOI": n_doi / n_st,
        "Studies with a population description": n_pop / n_st,
        "Studies with a study type": n_type / n_st,
    },
    "rel_single": rel_single / counts["relationships"],
    "summary": summary,
    "path": path,
    "heat_links": heat_links,
    "storage_hits": len(storage_hits),
}

TEMPLATE = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "explainer_template.html")).read()
html = TEMPLATE.replace("/*__DATA__*/null", json.dumps(data))
open(out_html, "w").write(html)
print("wrote", out_html, len(html), "bytes")
