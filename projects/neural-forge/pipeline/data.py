"""Fetch pinned inputs (Underlay collections + Dataverse graph) and load them into one DuckDB file.

Called by `python -m pipeline.run`; downloads only what is missing, so it is safe to re-run.
"""
import hashlib
import json
import shutil
import sys

import duckdb
import requests

from . import config as C

TABLES = {"eh": "eh", "geo": "geo", "trees": "trees", "complaints": "complaints", "weather": "weather"}


def _dir(slug):
    return C.UNDERLAY_RAW / slug.replace("/", "_", 1)


def _get_json(url):
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    return r.json()


def _download(url, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    with requests.get(url, stream=True, timeout=600) as r:
        r.raise_for_status()
        with open(tmp, "wb") as f:
            shutil.copyfileobj(r.raw, f, length=1 << 20)
    tmp.rename(dest)


def fetch_underlay(alias_or_slug, records=True):
    slug, semver, expected = C.COLLECTIONS.get(alias_or_slug) or C.GRAPH
    d = _dir(slug)
    d.mkdir(parents=True, exist_ok=True)
    if not (d / "version.json").exists():
        v = _get_json(f"{C.UNDERLAY_API}/collections/{slug}/versions/{semver}")
        (d / "version.json").write_text(json.dumps(v))
    if not (d / "collection.json").exists():
        c = _get_json(f"{C.UNDERLAY_API}/collections/{slug}")
        (d / "collection.json").write_text(json.dumps(c))
    got = json.loads((d / "version.json").read_text())["hash"]
    if got != expected:
        sys.exit(f"{slug}@{semver} is {got}, expected {expected}. Refusing to run on an unpinned version.")
    if records and not (d / "records.ndjson.gz").exists():
        print(f"downloading {slug}@{semver} …", flush=True)
        _download(f"{C.UNDERLAY_API}/collections/{slug}/versions/{semver}/records.ndjson.gz", d / "records.ndjson.gz")


def _md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_graph():
    C.GRAPH_PARQUET.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    for fid, (name, md5, table) in C.DATAVERSE_FILES.items():
        pq = C.GRAPH_PARQUET / f"{table}.parquet"
        if pq.exists():
            continue
        raw = C.GRAPH_RAW / name
        if not raw.exists():
            print(f"downloading {name} from Dataverse …", flush=True)
            _download(f"https://dataverse.harvard.edu/api/access/datafile/{fid}?format=original", raw)
        if _md5(raw) != md5:
            sys.exit(f"{name}: checksum mismatch")
        con.execute(f"COPY (SELECT * FROM read_csv_auto('{raw}', sample_size=-1)) "
                    f"TO '{pq}' (FORMAT parquet, COMPRESSION zstd)")
    fetch_underlay("graph", records=False)


def fetch_all():
    for alias in C.COLLECTIONS:
        fetch_underlay(alias)
    fetch_graph()


def connect(rebuild=False):
    """One DuckDB connection with Underlay tables (id, type, data JSON) and graph views."""
    C.CACHE_DB.parent.mkdir(parents=True, exist_ok=True)
    if rebuild and C.CACHE_DB.exists():
        C.CACHE_DB.unlink()
    con = duckdb.connect(str(C.CACHE_DB))
    have = {r[0] for r in con.execute("select table_name from information_schema.tables").fetchall()}
    for alias, (slug, _, _) in C.COLLECTIONS.items():
        if alias in have:
            continue
        src = _dir(slug) / "records.ndjson.gz"
        if not src.exists():
            fetch_underlay(alias)
        print(f"loading {slug} into cache …", flush=True)
        con.execute(f"""create table {alias} as select * from read_json('{src}', format='newline_delimited',
                        columns={{'id':'VARCHAR','type':'VARCHAR','data':'JSON'}})""")
    for t in ("associations", "relationships", "concepts", "studies", "variables"):
        con.execute(f"create or replace temp view {t} as select * from '{C.GRAPH_PARQUET / (t + '.parquet')}'")
    return con


def version_info(alias):
    slug, semver, expected = C.COLLECTIONS.get(alias) or C.GRAPH
    d = _dir(slug)
    coll = json.loads((d / "collection.json").read_text()) if (d / "collection.json").exists() else {}
    return {"collection": slug, "collection_id": coll.get("id"), "semver": semver, "hash": expected,
            "url": f"{C.UNDERLAY_WEB}/{slug}/v/{semver.lstrip('v')}"}


if __name__ == "__main__":
    fetch_all()
    connect()
    print("ok")
