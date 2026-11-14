#!/usr/bin/env bash
# Rebuild every derived data file from scratch.
# Needs SYSTEM_API_KEY in ../.env (or the environment) for steps 03-04.
set -euo pipefail
cd "$(dirname "$0")"
# Prefer the teammate's restored tables (repo root: python3 scripts/restore_system.py);
# fall back to downloading the association snapshot from Dataverse.
if [ ! -f ../../data/restored/system/system-public-graph-v1-associations.csv ]; then
  python3 ../../scripts/restore_system.py || python3 00_download_snapshot.py
fi
python3 01_extract_candidates.py    # 2M associations -> malaria-prevention candidates
python3 02_classify.py              # subtype, outcome tier, statistic family, QC flags
python3 03_enrich.py                # PubMed metadata + System study population/type
python3 04_graph_context.py         # malaria neighbourhood + anchor coverage (System API)
python3 05_build_site_data.py       # site/data/*.json (+ WHO country context)
python3 06_review_queue.py          # data/review/review_queue.csv
python3 07_abstract_check.py        # Europe PMC abstracts: is the number in the abstract? + quote
python3 08_graph_checked.py         # human-reviewed graph rows -> data/verified/evidence_graph_checked.csv
python3 05_build_site_data.py       # rebuild site data with the reviewed rows
python3 validate.py                 # fails loudly on any rule break
echo "done"
