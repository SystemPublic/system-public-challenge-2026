"""Step 2 (after registration): fetch the Chicago indicators by community area.

For each topic the period is the latest (by end year, the longer window on a tie) with a value for at least
MIN_AREAS of the 77 community areas; a topic with no such period is dropped. Raw responses are cached in
data/cache/chicago_atlas/. Writes chicago_indicators_ca77.csv and chicago_sources.json.
"""
import json
import time
from pathlib import Path

import pandas as pd
import requests

from chicago_indicators import CHICAGO, MIN_AREAS, N_AREAS

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "derived" / "round5" / "chicago_matrix"
CACHE = ROOT / "data" / "cache" / "chicago_atlas"
API = "https://chicagohealthatlas.org/api/v1"
UA = {"User-Agent": "research-script/1.0"}


def get(name, url, params=None):
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / f"{name}.json"
    if f.exists():
        return json.loads(f.read_text())
    for i in range(5):
        r = requests.get(url, params=params, headers=UA, timeout=120)
        if r.status_code == 200:
            d = r.json()
            d["_fetched"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
            f.write_text(json.dumps(d))
            time.sleep(0.4)
            return d
        time.sleep(3 * (i + 1))
    raise RuntimeError(f"{url} {params}: {r.status_code}")


def order(p):
    y = [int(x) for x in p.split("-")]
    return (-y[-1], y[0])


def values(topic, period):
    d = get(f"data-{topic}-{period}", f"{API}/data/", {"topic": topic, "population": "", "period": period, "layer": "neighborhood", "limit": 1000})
    v = {}
    for r in d["results"]:
        g = r["g"]
        if g.startswith("1714000-") and r.get("v") is not None:
            v[int(g.split("-")[1])] = float(r["v"])
    return {k: x for k, x in v.items() if 1 <= k <= N_AREAS}, d["_fetched"]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cols, src = {}, []
    for key, topic, tr, note in CHICAGO:
        cov = get(f"coverage-{topic}", f"{API}/coverage/{topic}/")["coverages"].get("neighborhood", [])
        periods = sorted({c["period"] for c in cov if c["population"] == ""}, key=order)
        rec = {"indicator": key, "kind": "chicago-health-atlas", "topic": topic, "transform": tr, "note": note, "tried": []}
        for p in periods:
            v, when = values(topic, p)
            rec["tried"].append({"period": p, "n_areas": len(v)})
            if len(v) >= MIN_AREAS:
                s = pd.Series(v)
                cols[key] = 100 - s if tr == "100-x" else s
                rec.update(period=p, n_areas=len(v), fetched=when,
                           url=f"{API}/data/?topic={topic}&population=&period={p}&layer=neighborhood")
                break
        else:
            rec["dropped"] = f"no period with {MIN_AREAS} areas"
        src.append(rec)
        print(key, topic, rec.get("period"), rec.get("n_areas"), rec.get("dropped", ""))
    t = pd.DataFrame(cols).reindex(range(1, N_AREAS + 1))
    t.index.name = "community_area"
    t.to_csv(OUT / "chicago_indicators_ca77.csv")
    (OUT / "chicago_sources.json").write_text(json.dumps(src, indent=1))
    print(t.shape)


if __name__ == "__main__":
    main()
