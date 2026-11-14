#!/bin/sh
# Download the System Public Graph snapshot (Dataverse doi:10.7910/DVN/7V6JDO, v2.1) into data/raw
# and load it into data/graph.db. About 1.1 GB download, 1.4 GB database.
# Usage: sh scripts/fetch_data.sh   (run from the repo root)
set -e
mkdir -p data/raw
dl() { [ -s "data/raw/$2" ] || curl -sL --fail -o "data/raw/$2" "https://dataverse.harvard.edu/api/access/datafile/$1?format=original"; }
dl 14061024 MANIFEST.json
dl 14061021 concepts.tsv
dl 14061020 associations.csv
dl 14061023 variables.tsv
dl 14061022 studies.tsv
dl 14061025 relationships.csv
python3 -I scripts/load_sqlite.py data/raw data/graph.db
