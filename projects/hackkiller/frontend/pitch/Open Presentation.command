#!/bin/zsh
cd -- "$(dirname -- "$0")" || exit 1
exec python3 - <<'PY'
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import webbrowser

root = Path.cwd()
handler = partial(SimpleHTTPRequestHandler, directory=str(root))
server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
url = f"http://127.0.0.1:{server.server_port}/pitch.html"
print(f"Malaria Atlas presentation is running at {url}", flush=True)
print("Keep this window open while presenting. Press Control-C to stop.", flush=True)
webbrowser.open(url)
try:
    server.serve_forever()
except KeyboardInterrupt:
    pass
finally:
    server.server_close()
PY
