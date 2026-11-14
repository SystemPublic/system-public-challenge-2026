"""EXPLORATORY (not registered). Throughput proxy for the 2019 42nd Street transit project, whose turn
changes extended time-of-day left-turn bans at 6th Ave, 7th Ave and Lexington Ave: monthly M42 bus
speeds against other Manhattan crosstown local routes, MTA Bus Speeds: Beginning 2015 (data.ny.gov
cudb-vcni). Writes data/derived/turn_restrictions/bus_speeds.json."""
import json, time
from pathlib import Path
import requests
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/derived/turn_restrictions"
ROUTES = ["M42", "M50", "M57", "M66", "M72", "M96", "M31", "M23", "M34", "M86", "M79"]


def main():
    q = {"$select": "route_id, month, period, day_type, trip_type, sum(total_mileage) as mi, sum(total_operating_time) as hr",
         "$where": "month >= '2017-01-01' and month < '2021-01-01' and day_type = '1' and route_id in ("
                   + ",".join(f"'{r}'" for r in ROUTES) + ")",
         "$group": "route_id, month, period, day_type, trip_type", "$limit": 50000}
    f = OUT / "bus_speeds_raw.json"
    if not f.exists():
        r = requests.get("https://data.ny.gov/resource/cudb-vcni.json", params=q, timeout=300)
        r.raise_for_status()
        f.write_text(r.text)
    meta = requests.get("https://data.ny.gov/api/views/cudb-vcni.json", timeout=60).json()
    rows = json.loads(f.read_text())
    src = {"kind": "ny-open-data", "dataset": "cudb-vcni", "name": meta.get("name"),
           "url": "https://data.ny.gov/d/cudb-vcni",
           "rows_updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(meta.get("rowsUpdatedAt", 0))),
           "query": q, "fetched": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "n_rows": len(rows)}
    (OUT / "bus_speeds.json").write_text(json.dumps({"source": src, "rows": rows}, indent=1))
    from collections import Counter
    print(len(rows), Counter((r["route_id"], r.get("trip_type")) for r in rows).most_common(30))
    print(sorted({r.get("period") for r in rows}), sorted({r.get("day_type") for r in rows}))


if __name__ == "__main__":
    main()


def compare():
    """Jan-Feb 2019 against Jan-Feb 2020, weekday, all periods: speed = sum miles / sum operating hours."""
    import collections, statistics
    d = json.loads((OUT / "bus_speeds.json").read_text())["rows"]
    S = collections.defaultdict(lambda: [0.0, 0.0])
    for r in d:
        S[(r["route_id"], r["month"][:7])][0] += float(r["mi"])
        S[(r["route_id"], r["month"][:7])][1] += float(r["hr"])
    sp = lambda rt, ms: sum(S[(rt, m)][0] for m in ms) / sum(S[(rt, m)][1] for m in ms)
    pre, post = ["2019-01", "2019-02"], ["2020-01", "2020-02"]
    out = {rt: {"pre_mph": round(sp(rt, pre), 3), "post_mph": round(sp(rt, post), 3),
                "ratio": round(sp(rt, post) / sp(rt, pre), 4)} for rt in ["M42", "M50", "M57", "M66", "M72", "M96", "M31"]}
    comp = [v["ratio"] for k, v in out.items() if k != "M42"]
    out["comparison_mean_ratio"] = round(statistics.mean(comp), 4)
    out["comparison_range"] = [min(comp), max(comp)]
    out["m42_relative"] = round(out["M42"]["ratio"] / statistics.mean(comp), 4)
    out["monthly_m42"] = {m: round(S[("M42", m)][0] / S[("M42", m)][1], 3) for m in sorted({k[1] for k in S}) if ("M42", m) in S}
    out["monthly_comparison_mean"] = {m: round(statistics.mean(S[(rt, m)][0] / S[(rt, m)][1] for rt in ["M50", "M57", "M66", "M72", "M96", "M31"] if (rt, m) in S), 3)
                                      for m in sorted({k[1] for k in S})}
    (OUT / "bus_speeds_compare.json").write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if not k.startswith("monthly")}, indent=1))


if __name__ == "__main__" and len(__import__("sys").argv) > 1 and __import__("sys").argv[1] == "compare":
    compare()
