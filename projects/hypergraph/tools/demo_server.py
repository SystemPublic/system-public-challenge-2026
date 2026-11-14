"""Local server for the live demo: serves the pages and compares two versions of an Underlay collection.

Written on 14 November 2026, during the event.

Usage:
  ~/.venvs/nyc-concordance/bin/python tools/demo_server.py [port]      (default 8000)
then open http://localhost:8000/viz/compare.html

A browser page cannot call the Underlay directly (the API sends no cross-origin header), so this server makes
the calls. /api/versions lists a collection's versions. /api/compare returns strips for a pair of versions,
built by tools/compare_versions.py. /api/inspections/compare returns the inspections whose score differs between
the June and November copies of the city's restaurant table, and /api/inspections/record fetches one inspection
from both copies on the Underlay. The server listens on localhost only.
"""
from __future__ import annotations

import json
import re
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compare_versions as cv  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SLUG = re.compile(r"^[A-Za-z0-9_.-]{1,80}$")
SEMVER = re.compile(r"^v\d+\.\d+\.\d+$")


STARTED = __import__("time").strftime("%Y-%m-%d %H:%M:%S")


def status(page: str) -> dict:
    """The server is up; when the page file was last changed; which commit the folder is at (if it is a git checkout)."""
    import subprocess
    import time
    out = {"ok": True, "server_started": STARTED, "now": time.strftime("%Y-%m-%d %H:%M:%S")}
    f = ROOT / "viz" / page if re.match(r"^[a-z_]+\.html$", page or "") else None
    if f and f.exists():
        out["page"] = page
        out["page_changed"] = time.strftime("%Y-%m-%d %H:%M", time.localtime(f.stat().st_mtime))
    try:
        r = subprocess.run(["git", "-C", str(ROOT), "log", "-1", "--format=%h %cd", "--date=format:%Y-%m-%d %H:%M"], capture_output=True, text=True, timeout=5)
        if r.returncode == 0 and r.stdout.strip():
            out["commit"], out["commit_time"] = r.stdout.strip().split(" ", 1)
    except Exception:
        pass
    return out


def lookup(term: str) -> dict:
    """Live: ask the city's table (today) for a Manhattan restaurant by name, then fetch each of its inspections
    from the June version on the Underlay and compare the scores."""
    import time
    from concurrent.futures import ThreadPoolExecutor

    import requests
    term = re.sub(r"[^A-Za-z0-9 &'.-]", "", term).strip().upper()[:40]
    if len(term) < 3:
        return {"error": "type at least three letters of a restaurant's name"}
    t0 = time.time()
    r = requests.get("https://data.cityofnewyork.us/resource/43nn-pn8j.json", timeout=40, params={
        "$select": "camis,dba,building,street,zipcode,inspection_date,inspection_type,max(score) as score,max(grade) as grade",
        "$where": "boro='Manhattan' AND upper(dba) like '%" + term.replace("'", "''") + "%' AND inspection_date between '2024-01-01T00:00:00' and '2026-06-11T23:59:59'",
        "$group": "camis,dba,building,street,zipcode,inspection_date,inspection_type", "$order": "inspection_date DESC", "$limit": "40"})
    if r.status_code != 200:
        return {"error": f"the city's data portal answered {r.status_code}"}
    rows, t_city = r.json(), time.time() - t0
    slug = lambda x: re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", x.lower())).strip("-")  # noqa: E731

    def june(x):
        rid = f"{x['camis']}-{x['inspection_date'][:10]}-{slug(x.get('inspection_type') or '')}"
        rec = cv.record("nyc", "restaurant-inspections", "v1.0.0", "Inspection", rid)
        now = int(float(x["score"])) if x.get("score") not in (None, "") else None
        then = (rec or {}).get("data", {}).get("score") if rec else None
        return {"id": rid, "name": x.get("dba"), "address": f"{x.get('building', '')} {x.get('street', '')}, {x.get('zipcode', '')}".strip(), "date": x["inspection_date"][:10],
                "type": x.get("inspection_type"), "now": now, "june": then, "in_june_copy": rec is not None,
                "changed": rec is not None and then is not None and now is not None and then != now}
    t1 = time.time()
    with ThreadPoolExecutor(max_workers=12) as ex:
        out = list(ex.map(june, rows))
    found = [o for o in out if o["in_june_copy"]]
    return {"term": term, "inspections_today": len(out), "found_in_june": len(found), "changed": sum(o["changed"] for o in out), "rows": out,
            "seconds_city": round(t_city, 1), "seconds_underlay": round(time.time() - t1, 1),
            "sources": {"today": "NYC Open Data 43nn-pn8j, queried now", "june": "Underlay nyc/restaurant-inspections v1.0.0"}}


class Handler(SimpleHTTPRequestHandler):
    def _json(self, code: int, obj) -> None:
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802
        u = urlparse(self.path)
        if not u.path.startswith("/api/"):
            return super().do_GET()
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        owner, slug = q.get("owner", "system-community"), q.get("slug", "nyc-concordance-claims")
        if not (SLUG.match(owner) and SLUG.match(slug)):
            return self._json(400, {"error": "bad owner or slug"})
        try:
            if u.path == "/api/versions":
                return self._json(200, {"owner": owner, "slug": slug, "versions": cv.versions(owner, slug)})
            if u.path == "/api/compare":
                frm, to = q.get("from") or None, q.get("to", "")
                if not SEMVER.match(to) or (frm and not SEMVER.match(frm)):
                    return self._json(400, {"error": "versions look like v1.2.0"})
                return self._json(200, cv.build(owner, slug, frm, to))
            if u.path == "/api/inspections/compare":
                d = json.loads((ROOT / "viz/data/inspections_changed_scores.json").read_text())
                for side in ("june", "november"):  # one live call each: the version the numbers rest on
                    v = cv.get(f"{cv.API}/collections/{d[side]['owner']}/{d[side]['slug']}/versions/{d[side]['version']}") or {}
                    d[side].update(hash=v.get("hash"), recordCount=v.get("recordCount"), createdAt=v.get("createdAt"))
                return self._json(200, d)
            if u.path == "/api/status":
                return self._json(200, status(q.get("page", "")))
            if u.path == "/api/inspections/lookup":
                return self._json(200, lookup(q.get("q", "")))
            if u.path == "/api/inspections/history":
                return self._json(200, json.loads((ROOT / "viz/data/inspections_history.json").read_text()))
            if u.path == "/api/inspections/record":
                rid = q.get("id", "")
                if not re.match(r"^[0-9]{6,10}-[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z0-9-]{1,80}$", rid):
                    return self._json(400, {"error": "bad inspection id"})
                out = {"id": rid}
                for side, (o, sl) in (("june", ("nyc", "restaurant-inspections")), ("november", ("system-community", "nyc-restaurant-inspections-2026-11"))):
                    r = cv.record(o, sl, "v1.0.0", "Inspection", rid)
                    out[side] = {"record": r, "url": f"https://www.underlay.org/api/collections/{o}/{sl}/versions/v1.0.0/records/Inspection/{rid}", "collection": f"{o}/{sl} v1.0.0"}
                rest = cv.record("system-community", "nyc-restaurant-inspections-2026-11", "v1.0.0", "Restaurant", rid.split("-")[0])
                out["restaurant"] = (rest or {}).get("data")
                return self._json(200, out)
            return self._json(404, {"error": "unknown endpoint"})
        except Exception as exc:
            return self._json(502, {"error": str(exc)[:300]})

    def log_message(self, fmt, *args):  # quiet, except for the API
        if "/api/" in (args[0] if args else ""):
            sys.stderr.write("%s\n" % (fmt % args))


def main() -> int:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    srv = ThreadingHTTPServer(("127.0.0.1", port), partial(Handler, directory=str(ROOT)))
    print(f"http://localhost:{port}/viz/compare.html")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
