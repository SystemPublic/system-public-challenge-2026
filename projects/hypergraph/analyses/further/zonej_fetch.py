"""Fetch NYISO PAL monthly zips (2015-01 to 2025-12) to ~/opt/nyc-concordance/nyiso/pal and record versions."""
import json, time, requests
from pathlib import Path
OUT = Path.home()/"opt/nyc-concordance/nyiso/pal"; OUT.mkdir(parents=True, exist_ok=True)
REC = Path(__file__).resolve().parents[2]/"data/derived/further/zonej_pal_sources.json"; REC.parent.mkdir(parents=True, exist_ok=True)
recs = json.loads(REC.read_text()) if REC.exists() else {}
for y in range(2015, 2026):
    for m in range(1, 13):
        k = f"{y}{m:02d}01pal_csv.zip"; f = OUT/k
        if k in recs and f.exists(): continue
        url = f"https://mis.nyiso.com/public/csv/pal/{k}"
        r = requests.get(url, timeout=120, headers={"User-Agent": "open-data-research-client"})
        if r.status_code != 200: recs[k] = {"url": url, "status": r.status_code}; print(k, r.status_code); continue
        f.write_bytes(r.content)
        recs[k] = {"url": url, "last_modified": r.headers.get("Last-Modified"), "bytes": len(r.content), "fetched": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
REC.write_text(json.dumps(recs, indent=1))
print(len(recs), sum(1 for v in recs.values() if v.get("status") is None))
