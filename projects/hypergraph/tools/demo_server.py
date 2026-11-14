"""Local server for the live demo: serves the pages and compares two versions of an Underlay collection.

Written on 14 November 2026, during the event.

Usage:
  ~/.venvs/nyc-concordance/bin/python tools/demo_server.py [port]      (default 8000)
then open http://localhost:8000/viz/compare.html

A browser page cannot call the Underlay directly (the API sends no cross-origin header), so this server makes
the calls. /api/versions lists a collection's versions. /api/compare returns strips for a pair of versions,
built by tools/compare_versions.py. The server listens on localhost only.
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
