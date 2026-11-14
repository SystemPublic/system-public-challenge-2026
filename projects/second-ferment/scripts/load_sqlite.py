"""Load the System Public Graph CSVs into a local SQLite database.

Usage: python3 -I load_sqlite.py <raw_dir> <db_path>
"""
import csv
import os
import sqlite3
import sys

raw, db_path = sys.argv[1], sys.argv[2]
csv.field_size_limit(10**9)
if os.path.exists(db_path):
    os.remove(db_path)
db = sqlite3.connect(db_path)
db.execute("PRAGMA journal_mode=OFF")
db.execute("PRAGMA synchronous=OFF")

FILES = {
    "associations": "associations.csv",
    "concepts": "concepts.tsv",
    "relationships": "relationships.csv",
    "studies": "studies.tsv",
    "variables": "variables.tsv",
}
for table, fname in FILES.items():
    with open(os.path.join(raw, fname), newline="", encoding="utf-8") as f:
        r = csv.reader(f)
        cols = [c.replace(".", "_") for c in next(r)]
        db.execute(f"CREATE TABLE {table} ({', '.join(c + ' TEXT' for c in cols)})")
        q = f"INSERT INTO {table} VALUES ({','.join('?' * len(cols))})"
        n, batch = 0, []
        for row in r:
            if len(row) != len(cols):
                continue
            batch.append([v if v != "" else None for v in row])
            if len(batch) >= 50000:
                db.executemany(q, batch)
                n += len(batch)
                batch = []
        db.executemany(q, batch)
        n += len(batch)
        print(table, n, "rows")
    db.commit()

for stmt in [
    "CREATE INDEX a_v1c ON associations(variable_1_concept_id)",
    "CREATE INDEX a_v2c ON associations(variable_2_concept_id)",
    "CREATE INDEX a_study ON associations(study_id)",
    "CREATE INDEX s_id ON studies(study_id)",
    "CREATE INDEX c_id ON concepts(system_id)",
    "CREATE INDEX v_c ON variables(concept_id)",
    "CREATE INDEX r_s ON relationships(source_concept_system_id)",
    "CREATE INDEX r_t ON relationships(target_concept_system_id)",
]:
    db.execute(stmt)
db.commit()
print("done")
