"""Cached, rate-limited client for the System Public Graph API (https://public-api.system.com/v1).

Shared by the scripts/system_api_*.py scripts.

- The key is read from SYSTEM_API_KEY in the environment, or from .env.local / .env
  in the repo root. It is only ever sent as the `x-api-key` header. It is never
  printed, logged or written to disk (cache files hold the request path + params only).
- Every response (2xx and 404) is cached to data/raw/system/api/cache/ keyed by
  the request path + sorted query params, so reruns are free.
- Every live request is appended to data/raw/system/api/request_log.csv
  (UTC time, path, params, HTTP status, latency ms). Cache hits are not logged.
- Sleeps between live calls and backs off on 429 / 5xx.
- A hard budget (default 6,000 live requests per day, override SYSTEM_API_BUDGET)
  is enforced from the request log.
"""
import csv, datetime as dt, hashlib, json, os, re, time, urllib.parse

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
API_DIR = os.path.join(ROOT, "data", "raw", "system", "api")
CACHE_DIR = os.path.join(API_DIR, "cache")
LOG_PATH = os.path.join(API_DIR, "request_log.csv")
BASE = "https://public-api.system.com/v1"
SLEEP = float(os.environ.get("SYSTEM_API_SLEEP", "0.25"))
BUDGET = int(os.environ.get("SYSTEM_API_BUDGET", "6000"))


class BudgetExceeded(RuntimeError):
    pass


def _load_key():
    k = os.environ.get("SYSTEM_API_KEY")
    if k:
        return k
    for name in (".env.local", ".env"):
        p = os.path.join(ROOT, name)
        if os.path.exists(p):
            for line in open(p, encoding="utf-8"):
                line = line.strip()
                if line.startswith("SYSTEM_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def _cache_name(path, params):
    q = urllib.parse.urlencode(sorted((k, str(v)) for k, v in (params or {}).items()))
    ident = path + ("?" + q if q else "")
    slug = re.sub(r"[^A-Za-z0-9]+", "_", path).strip("_")[:60]
    return ident, os.path.join(CACHE_DIR, f"{slug}__{hashlib.sha1(ident.encode()).hexdigest()[:16]}.json")


def live_calls_today():
    if not os.path.exists(LOG_PATH):
        return 0
    today = dt.datetime.utcnow().strftime("%Y-%m-%d")
    with open(LOG_PATH, encoding="utf-8") as f:
        return sum(1 for r in csv.DictReader(f) if r["utc_time"].startswith(today))


def _drop(o, keys):
    if isinstance(o, dict):
        return {k: _drop(v, keys) for k, v in o.items() if k not in keys}
    if isinstance(o, list):
        return [_drop(v, keys) for v in o]
    return o


class Client:
    def __init__(self, sleep=SLEEP, budget=BUDGET):
        import requests
        os.makedirs(CACHE_DIR, exist_ok=True)
        self._key = _load_key()
        self.s = requests.Session()
        if self._key:
            self.s.headers["x-api-key"] = self._key
        self.sleep = sleep
        self.budget = budget
        self.live = 0
        self.hits = 0
        self.used_today = live_calls_today()
        self._last = 0.0

    def _log(self, ident, status, ms):
        new = not os.path.exists(LOG_PATH)
        with open(LOG_PATH, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if new:
                w.writerow(["utc_time", "request", "status", "latency_ms"])
            w.writerow([dt.datetime.utcnow().isoformat(timespec="seconds"), ident, status, ms])

    def get(self, path, use_cache=True, drop_keys=(), **params):
        """GET path with params. Returns parsed JSON dict, or None for 404. Cached.
        drop_keys: key names removed (recursively) before caching, to keep the cache small
        (e.g. the long wikidata_aliases lists inside relationship pages)."""
        ident, fn = _cache_name(path, params)
        if use_cache and os.path.exists(fn):
            self.hits += 1
            rec = json.load(open(fn, encoding="utf-8"))
            return rec["body"]
        if not self._key:
            raise RuntimeError("SYSTEM_API_KEY not set (looked in env, .env.local, .env)")
        url = BASE + path
        for attempt in range(getattr(self, "max_attempts", 6)):
            if self.used_today + self.live >= self.budget:
                raise BudgetExceeded(f"live request budget {self.budget} reached")
            wait = self.sleep - (time.time() - self._last)
            if wait > 0:
                time.sleep(wait)
            t0 = time.time()
            try:
                r = self.s.get(url, params=params, timeout=90)
                status = r.status_code
            except Exception as e:  # network error
                status, r = f"ERR:{type(e).__name__}", None
            ms = int((time.time() - t0) * 1000)
            self._last = time.time()
            self.live += 1
            self._log(ident, status, ms)
            if r is not None and status == 200:
                body = _drop(r.json(), set(drop_keys)) if drop_keys else r.json()
                break
            if r is not None and status == 404:
                body = None
                break
            if r is not None and status in (400, 401, 403, 422):
                raise RuntimeError(f"HTTP {status} for {ident}: {r.text[:300]}")
            time.sleep(min(60, 3 * 2 ** attempt))
        else:
            raise RuntimeError(f"giving up on {ident} after retries (last status {status})")
        with open(fn, "w", encoding="utf-8") as f:
            json.dump({"request": ident, "status": status, "fetched_utc": dt.datetime.utcnow().isoformat(timespec="seconds"),
                       "latency_ms": ms, "body": body}, f)
        return body

    def paged(self, path, page=100, cap=5000, drop_keys=(), **params):
        """Collect `data` across offset pages until a short page or cap."""
        out, off = [], 0
        while off < cap:
            body = self.get(path, drop_keys=drop_keys, offset=off, limit=page, **params)
            data = (body or {}).get("data", [])
            out += data
            if len(data) < page:
                break
            off += page
        return out

    def stats(self):
        return f"live={self.live} cache_hits={self.hits} live_today_total={self.used_today + self.live}"
