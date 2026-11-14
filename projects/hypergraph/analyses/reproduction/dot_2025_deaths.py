"""Reproduction of NYC DOT's 2 Jan 2026 press release (claim repro-dot-2025-deaths).

Recomputes 2025 and 2024 traffic deaths, pedestrian deaths, deaths by borough and
injuries from the NYPD collision tables under the readings registered in
claims/registered/repro-dot-2025-deaths.json. Writes
data/derived/reproduction/dot_2025_deaths.json. Run from the repo root:
  ~/.venvs/nyc-concordance/bin/python -m analyses.reproduction.dot_2025_deaths
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

from shapely.geometry import Point, shape
from shapely.ops import nearest_points  # noqa: F401

from concord import socrata

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "derived" / "reproduction" / "dot_2025_deaths.json"
CR, PE, BB = "h9gi-nx95", "f55k-p6yu", "gthc-hcne"
W = "crash_date between '2023-12-01T00:00:00' and '2025-12-31T23:59:59'"

STATED = {
    "deaths": {"2025": 205, "2024": 253},
    "ped": {"2025": 111, "2024": 122},
    "boro": {"2025": {"BRONX": 33, "QUEENS": 57, "MANHATTAN": 39, "BROOKLYN": 63, "STATEN ISLAND": 13},
             "2024": {"BRONX": 54, "QUEENS": 74, "MANHATTAN": 44, "BROOKLYN": 69, "STATEN ISLAND": 12}},
    "inj": {"2025": 47557, "2024": 51540},
}
BOROS = ["BRONX", "BROOKLYN", "MANHATTAN", "QUEENS", "STATEN ISLAND"]


def tol_count(stated, pct=0.05, floor=3):
    return max(stated * pct, floor)


def main():
    sources = []

    # Persons table: killed persons by month and type (D1, P1, D3 bound)
    rows, s = socrata.query(PE, select="date_trunc_ym(crash_date) as m, person_type, count(*) as n",
                            where=W + " and person_injury = 'Killed'", group="m, person_type", order="m")
    sources.append(s)
    pk = defaultdict(Counter)
    for r in rows:
        pk[r["m"][:7]][r["person_type"]] += int(r["n"])

    # Persons killed, row level, for borough join
    pkill, s = socrata.query_all(PE, select="collision_id, crash_date, person_type",
                                 where="crash_date between '2024-01-01T00:00:00' and '2025-12-31T23:59:59' and person_injury = 'Killed'",
                                 order="unique_id")
    sources.append(s)

    # Crash table: killed crashes, row level (D2, P2, B1, B2)
    ck, s = socrata.query_all(CR, select="collision_id, crash_date, borough, latitude, longitude, number_of_persons_killed, number_of_pedestrians_killed",
                              where="crash_date between '2024-01-01T00:00:00' and '2025-12-31T23:59:59' and number_of_persons_killed > 0",
                              order="collision_id")
    sources.append(s)

    # Crash rows for collisions with a killed person but number_of_persons_killed = 0
    have = {r["collision_id"] for r in ck}
    missing = sorted({r["collision_id"] for r in pkill} - have)
    extra = []
    for i in range(0, len(missing), 100):
        ids = ",".join(missing[i:i + 100])
        rr, s = socrata.query(CR, select="collision_id, crash_date, borough, latitude, longitude, number_of_persons_killed, number_of_pedestrians_killed",
                              where=f"collision_id in ({ids})")
        extra.extend(rr)
        sources.append(s)

    # Injuries by day (I1-I4): crash table sum, persons table count
    ci, s = socrata.query(CR, select="date_trunc_ymd(crash_date) as d, sum(number_of_persons_injured) as inj",
                          where="crash_date between '2024-01-01T00:00:00' and '2025-12-31T23:59:59'", group="d", order="d")
    sources.append(s)
    pi, s = socrata.query(PE, select="date_trunc_ymd(crash_date) as d, count(*) as inj",
                          where="crash_date between '2024-01-01T00:00:00' and '2025-12-31T23:59:59' and person_injury = 'Injured'",
                          group="d", order="d")
    sources.append(s)

    # Borough boundaries
    bb, s = socrata.query(BB, select="boroname, the_geom")
    sources.append(s)
    polys = {r["boroname"].upper(): shape(r["the_geom"]) for r in bb}

    res = {"stated": STATED}

    # D1 / P1 by year, D3 bound
    def ysum(y, types=None):
        return sum(n for m, c in pk.items() if m.startswith(y) for t, n in c.items() if types is None or t in types)
    res["D1"] = {y: ysum(y) for y in ("2024", "2025")}
    res["P1"] = {y: ysum(y, {"Pedestrian"}) for y in ("2024", "2025")}
    res["D1_by_type"] = {y: dict(sum((pk[m] for m in pk if m.startswith(y)), Counter())) for y in ("2024", "2025")}
    res["D1_monthly"] = {m: sum(c.values()) for m, c in sorted(pk.items())}
    res["D3_bound"] = {"dec_2023_crash_deaths": res["D1_monthly"].get("2023-12", 0),
                       "dec_2024_crash_deaths": res["D1_monthly"].get("2024-12", 0),
                       "dec_2025_crash_deaths": res["D1_monthly"].get("2025-12", 0),
                       "note": "Deaths recorded for December crashes; under a date-of-death reading some of these move to the next year. The open tables carry no date of death."}

    # D2 / P2 / B1
    allc = ck + extra
    byid = {r["collision_id"]: r for r in allc}
    d2, p2 = Counter(), Counter()
    b1 = defaultdict(Counter)
    for r in ck:
        y = r["crash_date"][:4]
        k = int(r.get("number_of_persons_killed") or 0)
        d2[y] += k
        p2[y] += int(r.get("number_of_pedestrians_killed") or 0)
        b1[y][(r.get("borough") or "UNASSIGNED").upper()] += k
    res["D2"] = dict(d2)
    res["P2"] = dict(p2)
    res["B1"] = {y: dict(b1[y]) for y in b1}

    # B2: borough from coordinates (crash-table killed counts)
    def from_coords(r):
        try:
            la, lo = float(r["latitude"]), float(r["longitude"])
        except (KeyError, TypeError, ValueError):
            la = lo = 0.0
        if not la or not lo:
            return (r.get("borough") or "UNASSIGNED").upper(), "no_coords"
        p = Point(lo, la)
        for b, g in polys.items():
            if g.contains(p):
                return b, "inside"
        b, g = min(polys.items(), key=lambda kv: kv[1].distance(p))
        # degrees to metres at NYC latitude, roughly 85 km per degree longitude, 111 per latitude; use 100 km
        if g.distance(p) * 100_000 <= 500:
            return b, "nearest"
        return (r.get("borough") or "UNASSIGNED").upper(), "outside_kept_field"
    b2 = defaultdict(Counter)
    how = defaultdict(Counter)
    moved = defaultdict(Counter)
    for r in ck:
        y = r["crash_date"][:4]
        k = int(r.get("number_of_persons_killed") or 0)
        b, h = from_coords(r)
        b2[y][b] += k
        how[y][h] += k
        f = (r.get("borough") or "UNASSIGNED").upper()
        if f != b:
            moved[y][f"{f}->{b}"] += k
    res["B2"] = {y: dict(b2[y]) for y in b2}
    res["B2_method"] = {y: dict(how[y]) for y in how}
    res["B1_to_B2_moves"] = {y: dict(moved[y]) for y in moved}

    # Exploratory: D1 persons by borough via join (field, then coordinates)
    d1b, d1b2 = defaultdict(Counter), defaultdict(Counter)
    unmatched = Counter()
    for r in pkill:
        y = r["crash_date"][:4]
        c = byid.get(r["collision_id"])
        if c is None:
            unmatched[y] += 1
            continue
        d1b[y][(c.get("borough") or "UNASSIGNED").upper()] += 1
        d1b2[y][from_coords(c)[0]] += 1
    res["D1_by_borough_field_exploratory"] = {y: dict(d1b[y]) for y in d1b}
    res["D1_by_borough_coords_exploratory"] = {y: dict(d1b2[y]) for y in d1b2}
    res["D1_unmatched_collisions"] = dict(unmatched)
    res["persons_killed_in_crashes_with_zero_killed"] = len(missing)

    # Injuries
    cid = {r["d"][:10]: int(float(r["inj"])) for r in ci}
    pid = {r["d"][:10]: int(r["inj"]) for r in pi}
    def win(dct, y, end):
        return sum(v for d, v in dct.items() if d.startswith(y) and d[5:] <= end)
    res["I1"] = {y: win(cid, y, "12-15") for y in ("2024", "2025")}
    res["I2"] = {y: win(pid, y, "12-15") for y in ("2024", "2025")}
    res["I3"] = {"2025": win(cid, "2025", "12-15"), "2024": win(cid, "2024", "12-31")}
    res["I4"] = {y: win(cid, y, "12-14") for y in ("2024", "2025")}
    res["I_fullyear_crash"] = {y: win(cid, y, "12-31") for y in ("2024", "2025")}
    res["I_fullyear_person"] = {y: win(pid, y, "12-31") for y in ("2024", "2025")}

    # Scoring against tolerances
    def score(val, stated, pct, floor=0):
        t = max(stated * pct, floor)
        return {"value": val, "stated": stated, "gap": val - stated, "gap_pct": round(100 * (val - stated) / stated, 1),
                "tol": round(t, 1), "within": abs(val - stated) <= t}
    sc = {}
    for rd in ("D1", "D2"):
        for y in ("2025", "2024"):
            sc[f"{rd}_{y}"] = score(res[rd][y], STATED["deaths"][y], 0.05)
    for rd in ("P1", "P2"):
        for y in ("2025", "2024"):
            sc[f"{rd}_{y}"] = score(res[rd][y], STATED["ped"][y], 0.05, 3)
    for rd in ("B1", "B2"):
        for y in ("2025", "2024"):
            for b in BOROS:
                sc[f"{rd}_{y}_{b}"] = score(res[rd][y].get(b, 0), STATED["boro"][y][b], 0.05, 3)
    for rd in ("I1", "I2", "I3", "I4"):
        for y in ("2025", "2024"):
            sc[f"{rd}_{y}"] = score(res[rd][y], STATED["inj"][y], 0.03)
    res["scores"] = sc
    res["sources"] = sources
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=1))
    return res


if __name__ == "__main__":
    r = main()
    print(json.dumps({k: v for k, v in r.items() if k not in ("sources", "scores", "D1_monthly")}, indent=1))
    for k, v in r["scores"].items():
        print(f"{k:28s} {v['value']:>7} vs {v['stated']:>7}  gap {v['gap']:>+6} ({v['gap_pct']:+.1f}%)  {'IN' if v['within'] else 'out'}")
