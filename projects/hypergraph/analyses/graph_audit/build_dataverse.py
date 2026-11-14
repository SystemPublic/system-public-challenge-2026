"""Download the System Public Graph Dataverse deposit and load it into DuckDB.

Deposit: doi:10.7910/DVN/7V6JDO (Harvard Dataverse), the version is read from
the Dataverse API at run time (2.1 on 12 November 2026).

Files go to ~/opt/nyc-concordance/dataverse/ (outside Dropbox):
  raw/<original filename>     the files as deposited (original CSV format)
  dataset_meta.json           the Dataverse API record for the dataset version
  graph.duckdb                tables associations, concepts, relationships,
                              studies, variables, and provenance

Each file's MD5 is checked against Dataverse and its SHA-256 against the
deposit's MANIFEST.json. The check results are written to
data/derived/graph_audit/dataverse_files.json (repo-relative, small).

Usage:
  ~/.venvs/nyc-concordance/bin/python analyses/graph_audit/build_dataverse.py [--skip-download]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import duckdb
import requests

DOI = "doi:10.7910/DVN/7V6JDO"
API = "https://dataverse.harvard.edu/api"
HOME = Path.home() / "opt" / "nyc-concordance" / "dataverse"
RAW = HOME / "raw"
# Dataverse answers 403 to the default python-requests User-Agent.
UA = {"User-Agent": "nyc-concordance/0.1 (research script)"}
DB = HOME / "graph.duckdb"
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "derived" / "graph_audit" / "dataverse_files.json"

TABLES = {
    "associations": "system-public-graph-v1-associations.csv",
    "concepts": "system-public-graph-v1-concepts.csv",
    "relationships": "system-public-graph-v1-relationships.csv",
    "studies": "system-public-graph-v1-studies.csv",
    "variables": "system-public-graph-v1-variables.csv",
}


def digest(p: Path, algo: str) -> str:
    h = hashlib.new(algo)
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_meta() -> dict:
    r = requests.get(f"{API}/datasets/:persistentId/", params={"persistentId": DOI}, headers=UA, timeout=60)
    r.raise_for_status()
    HOME.mkdir(parents=True, exist_ok=True)
    (HOME / "dataset_meta.json").write_text(r.text)
    return r.json()["data"]


def download(files: list[dict]) -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    for f in files:
        df = f["dataFile"]
        # Dataverse turns ingested CSVs into .tab; ?format=original returns the deposited CSV.
        name = df["filename"].replace(".tab", ".csv") if df.get("originalFileFormat") else df["filename"]
        dest = RAW / name
        size = df.get("originalFileSize") or df["filesize"]
        if dest.exists() and dest.stat().st_size == size:
            continue
        url = f"{API}/access/datafile/{df['id']}" + ("?format=original" if df.get("originalFileFormat") else "")
        with requests.get(url, stream=True, headers=UA, timeout=600) as r:
            r.raise_for_status()
            with dest.open("wb") as out:
                for chunk in r.iter_content(1 << 22):
                    out.write(chunk)


def verify(meta: dict) -> list[dict]:
    v = meta["latestVersion"]
    manifest = json.loads((RAW / "MANIFEST.json").read_text())
    man = {m["filename"]: m for m in manifest["files"]}
    rows = []
    for f in v["files"]:
        df = f["dataFile"]
        orig = bool(df.get("originalFileFormat"))
        name = df["filename"].replace(".tab", ".csv") if orig else df["filename"]
        p = RAW / name
        md5 = digest(p, "md5")
        sha = digest(p, "sha256")
        m = man.get(name, {})
        rows.append({
            "filename": name,
            "dataverse_file_id": df["id"],
            "dataverse_filename": df["filename"],
            "bytes": p.stat().st_size,
            "md5": md5,
            "sha256": sha,
            # Dataverse's MD5 of an ingested file is of the original upload
            "md5_matches_dataverse": md5 == df.get("checksum", {}).get("value"),
            "sha256_matches_manifest": (sha == m["checksums"]["sha256"]) if m else None,
            "manifest_rows": m.get("rows"),
            "url": f"https://dataverse.harvard.edu/api/access/datafile/{df['id']}" + ("?format=original" if orig else ""),
        })
    return rows


def load(rows: list[dict], meta: dict) -> dict:
    con = duckdb.connect(str(DB))
    counts = {}
    for t, fn in TABLES.items():
        con.execute(f"DROP TABLE IF EXISTS {t}")
        con.execute(
            f"CREATE TABLE {t} AS SELECT * FROM read_csv('{RAW / fn}', header=true, all_varchar=false, "
            f"sample_size=-1, quote='\"', escape='\"', max_line_size=10000000)"
        )
        counts[t] = con.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
    v = meta["latestVersion"]
    con.execute("DROP TABLE IF EXISTS provenance")
    con.execute("CREATE TABLE provenance (key VARCHAR, value VARCHAR)")
    prov = {
        "doi": DOI,
        "version": f"{v['versionNumber']}.{v['versionMinorNumber']}",
        "release_time": v.get("releaseTime"),
        "license": (v.get("license") or {}).get("name"),
        "loaded_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "files": json.dumps(rows),
        "row_counts": json.dumps(counts),
    }
    con.executemany("INSERT INTO provenance VALUES (?, ?)", list(prov.items()))
    con.execute("CREATE INDEX IF NOT EXISTS ix_assoc_id ON associations(system_id)")
    con.close()
    return counts


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--skip-download", action="store_true")
    a = ap.parse_args()
    meta = fetch_meta()
    v = meta["latestVersion"]
    if not a.skip_download:
        download(v["files"])
    rows = verify(meta)
    counts = load(rows, meta)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "doi": DOI,
        "version": f"{v['versionNumber']}.{v['versionMinorNumber']}",
        "release_time": v.get("releaseTime"),
        "license": (v.get("license") or {}).get("name"),
        "local_db": "~/opt/nyc-concordance/dataverse/graph.duckdb",
        "files": rows,
        "row_counts": counts,
    }, indent=1))
    for r in rows:
        print(f"{r['filename']:45s} {r['bytes']:>11,d}  md5 {'ok' if r['md5_matches_dataverse'] else 'MISMATCH'}"
              f"  sha256 {'ok' if r['sha256_matches_manifest'] else r['sha256_matches_manifest']}")
    print(counts)


if __name__ == "__main__":
    main()
