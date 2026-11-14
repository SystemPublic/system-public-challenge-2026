"""Shared helpers for the routing scripts (routing_contacts.py, routing_cooling.py, routing_story.py).

- Road-network matrix client with an on-disk cache: every response is stored as
  data/raw/routing/cache/<engine>_<profile>_<sha1 of engine + profile + request body>.json,
  so reruns cost zero network calls. No API key is ever written to disk or printed.
- Engine 1 (preferred): OpenRouteService Matrix API (profiles foot-walking, driving-car),
  key ORS_API_KEY from the environment or .env.local. Free plan: 40 req/min (we sleep 1.6 s),
  <=3,500 source x destination pairs per request; back off 65 s on HTTP 429.
- Engine 2 (fallback, used automatically when no usable ORS key is available): the public
  FOSSGIS OSRM servers at routing.openstreetmap.de (routed-foot, routed-car; OpenStreetMap
  data), table service, <=100 locations per request, 1.5 s between requests (their policy
  asks for <=1 req/s). Force an engine with ROUTING_ENGINE=ors|osrm-fossgis.
- Every network call is appended to data/raw/routing/call_log.tsv (time, engine, profile,
  pair count, HTTP status, cache file). No key in the log.
- Geometry helpers (haversine) and the shared constants for the spec §4.4a time budget.

Routing responses are untrusted data; they are parsed as JSON only.
"""
import csv, datetime as dt, hashlib, json, math, os, time, urllib.error, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw", "routing")
CACHE = os.path.join(RAW, "cache")
SYN = os.path.join(ROOT, "data", "processed", "synthetic")
PROCESSED = os.path.join(ROOT, "data", "processed")
CALL_LOG = os.path.join(RAW, "call_log.tsv")
ORS_BASE = "https://api.openrouteservice.org/v2/matrix/"

# Spec §4.4a starting time budgets (min) and the default response-time assumption from
# contacts.csv generator A14: p90(patient) = 15 min, p90(contact) = 15 min.
BUDGETS = {45: "very high risk", 60: "high", 90: "medium"}
P90_PATIENT_MIN = 15
P90_CONTACT_MIN = 15
OLDER_WALK_MPS = 0.8  # Western et al. 2025 (PMC12682371): older walkers ~0.77-0.9 m/s
MAX_PAIRS = 3500       # ORS free plan: sources x destinations per matrix request

STATS = {"network": 0, "cached": 0, "errors": 0}


def _key():
    """Return the ORS key, or None when it is missing or not a usable HTTP header value."""
    k = os.environ.get("ORS_API_KEY")
    if not k:
        p = os.path.join(ROOT, ".env.local")
        if os.path.exists(p):
            with open(p) as fh:
                for line in fh:
                    if line.startswith("ORS_API_KEY="):
                        k = line.split("=", 1)[1].strip().strip('"').strip("'")
    if not k or not k.isascii() or any(ch.isspace() for ch in k):
        return None
    return k


ENGINE_NOTE = {}
_last = [0.0]


def _throttle(gap):
    wait = gap - (time.time() - _last[0])
    if wait > 0:
        time.sleep(wait)


def _log(engine, profile, n, status, fname):
    with open(CALL_LOG, "a") as fh:
        fh.write("\t".join([dt.datetime.now().isoformat(timespec="seconds"), engine, profile,
                            str(n), str(status), fname]) + "\n")


def _http(req, timeout=120):
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, None
    except Exception as e:
        return f"exc:{type(e).__name__}", None


def _ors(profile, body, path):
    key = _key()
    raw = json.dumps(body, sort_keys=True, separators=(",", ":"))
    for _ in range(6):
        _throttle(1.6)  # ORS free plan: 40 req/min
        req = urllib.request.Request(ORS_BASE + profile, data=raw.encode(), method="POST", headers={
            "Authorization": key, "Content-Type": "application/json",
            "Accept": "application/json", "User-Agent": "hackathon-routing-script"})
        status, resp = _http(req)
        _last[0] = time.time()
        STATS["network"] += 1
        _log("ors", profile, len(body["sources"]) * len(body["destinations"]), status, os.path.basename(path))
        if status == 200 and resp is not None:
            return {"durations": resp["durations"], "distances": resp["distances"],
                    "sources": [{"snapped_distance": s.get("snapped_distance")} if s else {} for s in resp.get("sources", [])],
                    "destinations": [{"snapped_distance": s.get("snapped_distance")} if s else {} for s in resp.get("destinations", [])]}
        if status == 429 or isinstance(status, str):
            time.sleep(65)
            continue
        STATS["errors"] += 1
        raise RuntimeError(f"ORS matrix {profile} failed: HTTP {status}: {str(resp)[:300]}")
    raise RuntimeError("ORS matrix: retries exhausted")


OSRM_BASE = "https://routing.openstreetmap.de/routed-{}/table/v1/driving/"
OSRM_PROFILE = {"foot-walking": "foot", "driving-car": "car"}


def _osrm(profile, body, path):
    coords = ";".join(f"{lon},{lat}" for lon, lat in body["locations"])
    url = (OSRM_BASE.format(OSRM_PROFILE[profile]) + coords + "?annotations=duration,distance"
           + "&sources=" + ";".join(map(str, body["sources"]))
           + "&destinations=" + ";".join(map(str, body["destinations"])))
    for _ in range(6):
        _throttle(1.5)  # FOSSGIS usage policy: at most 1 request/s
        req = urllib.request.Request(url, headers={"User-Agent": "hackathon-routing-script (synthetic data)",
                                                   "Accept": "application/json"})
        status, resp = _http(req)
        _last[0] = time.time()
        STATS["network"] += 1
        _log("osrm-fossgis", profile, len(body["sources"]) * len(body["destinations"]), status,
             os.path.basename(path))
        if status == 200 and resp and resp.get("code") == "Ok":
            return {"durations": resp["durations"], "distances": resp["distances"],
                    "sources": [{"snapped_distance": s.get("distance")} for s in resp["sources"]],
                    "destinations": [{"snapped_distance": s.get("distance")} for s in resp["destinations"]]}
        if status in (429, 502, 503, 504) or isinstance(status, str):
            time.sleep(30)
            continue
        STATS["errors"] += 1
        raise RuntimeError(f"OSRM table {profile} failed: HTTP {status}: {str(resp)[:300]}")
    raise RuntimeError("OSRM table: retries exhausted")


def engine():
    """'ors' when a usable ORS key exists, else 'osrm-fossgis' (public OSRM at routing.openstreetmap.de)."""
    if os.environ.get("ROUTING_ENGINE"):
        return os.environ["ROUTING_ENGINE"]
    return "ors" if _key() else "osrm-fossgis"


def ors_matrix(profile, locations, sources, destinations):
    """Road-network matrix (ORS Matrix API, or the OSRM fallback). locations are [lon, lat].

    Returns {"durations": [[s]], "distances": [[m]], "sources"/"destinations": [{"snapped_distance": m}]}
    (cached on disk; the cache file is keyed by engine + profile + request body).
    """
    os.makedirs(CACHE, exist_ok=True)
    eng = engine()
    body = {"locations": [[round(a, 6), round(b, 6)] for a, b in locations],
            "sources": sources, "destinations": destinations,
            "metrics": ["duration", "distance"], "units": "m"}
    raw = json.dumps(body, sort_keys=True, separators=(",", ":"))
    h = hashlib.sha1((eng + "|" + profile + "|" + raw).encode()).hexdigest()
    path = os.path.join(CACHE, f"{eng}_{profile}_{h}.json")
    ENGINE_NOTE[eng] = ENGINE_NOTE.get(eng, 0) + 1
    if os.path.exists(path):
        STATS["cached"] += 1
        with open(path) as fh:
            return json.load(fh)["response"]
    if eng == "osrm-fossgis" and len(locations) > 100:
        raise ValueError("keep OSRM table requests at <=100 locations")
    resp = _ors(profile, body, path) if eng == "ors" else _osrm(profile, body, path)
    with open(path, "w") as fh:
        json.dump({"engine": eng, "profile": profile, "request": body, "response": resp}, fh)
    return resp


def haversine_m(lat1, lon1, lat2, lon2):
    r = 6371008.8
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def read_csv(name):
    with open(os.path.join(SYN, name), newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(path, rows, fields):
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def fmt(x, nd=1):
    return "" if x is None else round(x, nd)
