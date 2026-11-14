#!/usr/bin/env bash
# Builds a local DuckDB copy of the System Public Graph (Dataverse v2.1).
# Usage: ./setup.sh   (needs curl + duckdb: `brew install duckdb`)
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p raw
B="https://dataverse.harvard.edu/api/access/datafile"
fetch() { [ -s "raw/$1" ] && echo "have raw/$1" || { echo "downloading $1"; curl -fL --retry 3 -o "raw/$1" "$B/$2"; }; }
fetch concepts.csv      "14061021?format=original"
fetch studies.csv       "14061022?format=original"
fetch relationships.csv "14061025"
fetch associations.csv  "14061020"

echo "building retrofit.duckdb ..."
duckdb retrofit.duckdb <<'SQL'
CREATE OR REPLACE TABLE concepts      AS SELECT * FROM read_csv('raw/concepts.csv',      header=true);
CREATE OR REPLACE TABLE studies       AS SELECT * FROM read_csv('raw/studies.csv',       header=true);
CREATE OR REPLACE TABLE relationships AS SELECT * FROM read_csv('raw/relationships.csv', header=true);
CREATE OR REPLACE TABLE associations  AS SELECT * FROM read_csv('raw/associations.csv',  header=true);
SELECT 'associations' AS t, count(*) AS n FROM associations UNION ALL
SELECT 'relationships', count(*) FROM relationships UNION ALL
SELECT 'concepts', count(*) FROM concepts UNION ALL
SELECT 'studies', count(*) FROM studies;
SQL
echo "done: open with  duckdb retrofit.duckdb"
