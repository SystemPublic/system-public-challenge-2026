"""Parallel prefetch for system_api_evidence.py stage D (variable-name route).

The server takes ~10 s per batched /associations call, so running the remaining batches
one at a time takes ~30 min. This fills the same cache (data/raw/system/api/cache/) with
N parallel workers; then system_api_evidence.py reruns entirely from cache.

  EVID_D_CACHED_ONLY=1 EVID_DUMP_SKIPPED=skipped.json python scripts/system_api_evidence.py
  python scripts/system_api_prefetch.py skipped.json [workers=6]
  python scripts/system_api_evidence.py

Batches that return HTTP 500 are left uncached; the evidence script then splits them itself.
Every live call is logged to request_log.csv and counts toward the daily budget.
"""
import json, os, sys, threading, time, datetime as dt
from concurrent.futures import ThreadPoolExecutor
import requests

sys.path.insert(0, os.path.dirname(__file__))
from system_api_client import _cache_name, _load_key, BASE, LOG_PATH, CACHE_DIR  # noqa: E402

lock = threading.Lock()
key = _load_key()
done = {"ok": 0, "err": 0, "calls": 0}


def log(ident, status, ms):
    with lock:
        new = not os.path.exists(LOG_PATH)
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            if new:
                f.write("utc_time,request,status,latency_ms\n")
            f.write(f"{dt.datetime.utcnow().isoformat(timespec='seconds')},{ident},{status},{ms}\n")
        done["calls"] += 1


def fetch(batch):
    side, chunk = batch
    flt = f"{side}:" + "||".join(chunk)
    off = 0
    while off < 3000:
        params = {"filter": flt, "offset": off, "limit": 100}
        ident, fn = _cache_name("/associations", params)
        if os.path.exists(fn):
            body = json.load(open(fn, encoding="utf-8"))["body"]
        else:
            t0 = time.time()
            try:
                r = requests.get(BASE + "/associations", params=params, headers={"x-api-key": key}, timeout=120)
                status = r.status_code
            except Exception as e:
                status, r = f"ERR:{type(e).__name__}", None
            ms = int((time.time() - t0) * 1000)
            log(ident, status, ms)
            if status != 200:
                with lock:
                    done["err"] += 1
                return
            body = r.json()
            with open(fn, "w", encoding="utf-8") as f:
                json.dump({"request": ident, "status": status, "fetched_utc": dt.datetime.utcnow().isoformat(timespec="seconds"),
                           "latency_ms": ms, "body": body}, f)
        if len((body or {}).get("data", [])) < 100:
            break
        off += 100
    with lock:
        done["ok"] += 1
        if done["ok"] % 20 == 0:
            print(f"  {done['ok']} batches done, {done['err']} errors, {done['calls']} live calls", flush=True)


if __name__ == "__main__":
    batches = json.load(open(sys.argv[1]))
    workers = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    os.makedirs(CACHE_DIR, exist_ok=True)
    print(f"prefetching {len(batches)} batches with {workers} workers", flush=True)
    with ThreadPoolExecutor(workers) as ex:
        list(ex.map(fetch, batches))
    print(f"done: {done['ok']} ok, {done['err']} left for the evidence script to split, {done['calls']} live calls")
