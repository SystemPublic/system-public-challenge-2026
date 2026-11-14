"""Treatment data: left-turn traffic calming installations from NYC DOT 'VZV Turn Traffic Calming'
(sm2x-35i7). Keeps left-turn treatments (drops labels naming right turns, bike islands, and the 1899 date
placeholder). Writes data/derived/turn_restrictions/sites.json with a source record."""
import json, math, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from concord import socrata as s

OUT = ROOT / "data/derived/turn_restrictions"


def xy(lat, lon):  # local metres, equirectangular about NYC
    return (lon + 73.95) * 111320 * math.cos(math.radians(40.72)), (lat - 40.72) * 110574


def main():
    rows, src = s.query("sm2x-35i7", limit=50000)
    keep, dropped = [], {}
    for i, r in enumerate(rows):
        t = (r.get("treatment_") or "").strip()
        d = (r.get("completion") or "")[:10]
        tl = t.lower()
        why = None
        if "right" in tl:
            why = "right turn"
        elif "bike island" in tl:
            why = "bike island"
        elif not d or d < "2010":
            why = "no date"
        elif not r.get("lat"):
            why = "no location"
        if why:
            dropped[why] = dropped.get(why, 0) + 1
            continue
        keep.append({"i": i, "treatment": t, "date": d, "lat": float(r["lat"]), "lon": float(r["long"])})
    # merge records within 40 m (two approaches of one intersection): keep the earliest date
    keep.sort(key=lambda k: k["date"])
    sites = []
    for k in keep:
        x, y = xy(k["lat"], k["lon"])
        hit = None
        for sx in sites:
            if (sx["x"] - x) ** 2 + (sx["y"] - y) ** 2 < 40 ** 2:
                hit = sx
                break
        if hit:
            hit["n_records"] += 1
            hit["later_dates"].append(k["date"])
            continue
        sites.append({**k, "x": x, "y": y, "n_records": 1, "later_dates": []})
    src["n_rows"] = len(rows)
    out = {"source": src, "n_records": len(rows), "dropped": dropped, "n_left_records": len(keep),
           "n_sites": len(sites), "sites": sites}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "sites.json").write_text(json.dumps(out, indent=1))
    from collections import Counter
    print(len(rows), dropped, len(keep), len(sites), sorted(Counter(x["date"][:4] for x in sites).items()))


if __name__ == "__main__":
    main()
