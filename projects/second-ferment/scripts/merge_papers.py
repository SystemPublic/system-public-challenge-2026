"""Merge cached PubMed metadata into an existing bundle, without rescanning the graph.
Writes evidence.json, evidence.js and the self-contained check page (see bundle_io.py).

Usage (from the repo root):
  python3 -I scripts/merge_papers.py bundle/evidence.json data/pubmed/summaries.json
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bundle_io  # noqa: E402

bundle_path, meta_path = sys.argv[1:3]
b = json.load(open(bundle_path))
meta = json.load(open(meta_path))
pmids = {f["pmid"] for f in b["findings"].values() if f.get("pmid")} | {d["pmid"] for d in b["direct"]}
b["papers"] = {p: meta[p] for p in sorted(pmids) if p in meta}
b["meta"]["counts"]["papers_with_metadata"] = len(b["papers"])
b["meta"]["counts"]["papers"] = len(pmids)
bundle_io.write(b, bundle_path)
print("papers:", len(pmids), "with metadata:", len(b["papers"]))
