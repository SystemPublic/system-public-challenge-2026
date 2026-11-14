"""NYC Open Data (Socrata) client that records the dataset version it used.

Every query result carries a `source` record: dataset id, name, the
dataset's rowsUpdatedAt / dataUpdatedAt timestamps from the metadata API at
fetch time, the exact SoQL, and the fetch time. Claims cite these records,
which is how the challenge's "each citing the dataset versions it rests on"
is met for NYC data (Socrata has no immutable versions; the update timestamp
plus the query is the nearest thing, and the cached result file is the copy).

Results are cached in data/cache/socrata/ keyed by dataset+query.
"""
from __future__ import annotations

import hashlib
import io
import json
import time
from pathlib import Path

import requests

DOMAIN = "https://data.cityofnewyork.us"
ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "data" / "cache" / "socrata"


def _req(url, params=None, retries=6, timeout=180):
    last = None
    for i in range(retries):
        try:
            r = requests.get(url, params=params, timeout=timeout)
            if r.status_code in (429, 500, 502, 503, 504):
                last = r.status_code
                time.sleep(3 * (i + 1))
                continue
            r.raise_for_status()
            return r
        except requests.RequestException as e:
            last = e
            time.sleep(3 * (i + 1))
    raise RuntimeError(f"Socrata failed {url} {params}: {last}")


def metadata(dataset: str, refresh: bool = False) -> dict:
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / f"meta-{dataset}.json"
    if f.exists() and not refresh and time.time() - f.stat().st_mtime < 86400:
        return json.loads(f.read_text())
    m = _req(f"{DOMAIN}/api/views/{dataset}.json").json()
    keep = {k: m.get(k) for k in ("id", "name", "attribution", "rowsUpdatedAt", "viewLastModified",
                                  "publicationDate", "createdAt")}
    keep["columns"] = [c.get("fieldName") for c in m.get("columns", [])]
    keep["url"] = f"{DOMAIN}/d/{dataset}"
    f.write_text(json.dumps(keep, indent=1))
    return keep


def source_record(dataset: str, soql: dict) -> dict:
    m = metadata(dataset)
    ts = m.get("rowsUpdatedAt")
    return {
        "kind": "nyc-open-data",
        "dataset": dataset,
        "name": m.get("name"),
        "url": m.get("url"),
        "rows_updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts)) if ts else None,
        "query": soql,
        "fetched": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }


def query(dataset: str, refresh: bool = False, **soql) -> tuple[list[dict], dict]:
    """Run a SoQL query ($select, $where, $group, $order, $limit ...).
    Pass keys without the '$', e.g. query('ipu4-2q9a', select='count(*)', where="...").
    Returns (rows, source_record)."""
    params = {("$" + k if not k.startswith("$") else k): v for k, v in soql.items()}
    params.setdefault("$limit", 50000)
    sig = hashlib.sha256((dataset + json.dumps(params, sort_keys=True)).encode()).hexdigest()[:24]
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / f"{dataset}-{sig}.json"
    if f.exists() and not refresh:
        d = json.loads(f.read_text())
        return d["rows"], d["source"]
    rows = _req(f"{DOMAIN}/resource/{dataset}.json", params).json()
    src = source_record(dataset, params)
    src["n_rows"] = len(rows)
    f.write_text(json.dumps({"source": src, "rows": rows}))
    return rows, src


def query_all(dataset: str, page: int = 50000, max_rows: int = 2_000_000, **soql) -> tuple[list[dict], dict]:
    """Page through a query with $offset (requires a stable $order)."""
    soql.setdefault("order", ":id")
    out, off, src = [], 0, None
    while len(out) < max_rows:
        rows, src = query(dataset, limit=page, offset=off, **soql)
        out.extend(rows)
        if len(rows) < page:
            break
        off += page
    src = dict(src or {})
    src["n_rows"] = len(out)
    src["query"] = {k: v for k, v in src.get("query", {}).items() if k != "$offset"}
    return out, src


def frame(dataset: str, **soql):
    import pandas as pd
    rows, src = query(dataset, **soql)
    return pd.DataFrame(rows), src
